import math
import numpy as np
import openai
import pandas as pd
import scipy
from page.init import Screen

from page.init import Screen


NUM_JUDGES = 4


class Evaluate():
    """
    This class represents the evaluation process of a model.

    @attribute model:
        The model to be evaluated.
    @attribute allocator:
        The weight allocator used to allocate weights to the judges.
    @attribute judges:
        The list of judges used to evaluate the candidate items.
    @attribute scores:
        The list of scores for each candidate item.

    @method calculate_score:
        This method scores the candidate items.
        @return:
            The final scores of the candidate items.
    """

    def __init__(self, model):
        """
        Initializes the Evaluate class with an allocator, judges, and scores.

        @description:
        This function initializes the Evaluate class with the following:
        - An allocator object.
        - A list of judges, including LLM_Judge, IG_Judge, Prior_Judge, and Markov_Judge.
        - An empty list of scores.

        @return:
        None.
        """
        self.model = model
        self.allocator = Allocator(self)
        self.judges = [LLM_Judge(self), IG_Judge(self),
                       Prior_Judge(self), Markov_Judge(self)]
        self.scores = []

    def evaluate(self):
        """
        This method scores the candidate items.

        @description:
        This function works as follows:
        - Iterate over all judges and score the candidate items, storing the results in the judge_scores list.
        - Call the allocate method of the weight allocator to allocate weights to the judges, storing the weights in the weights list.
        - Use the dot function from the numpy library to calculate the product of the judge scores and weights, resulting in the final score.
        - Store the final score in self.score and return self.scores.

        @return:
        The final scores of the candidate items.
        """
        judge_scores = []
        for judge in self.judges:
            judge_scores.append(judge.score(self.model.candidate))
        weights = self.allocator.allocate()
        self.score = np.dot(judge_scores, weights)
        return self.scores


class Judge():
    """
    This class represents a judge template.
    """

    def __init__(self, evaluate: Evaluate):
        self.evaluate = evaluate


class LLM_Judge(Judge):
    """
    This class represents a judge that evaluates a candidate item using the LLM algorithm.

    @attribute prompt:
        The prompt used for OpenAI's GPT-3 API to generate a score for each option.
    @attribute result:
        The LLM score result.

    @method score:
        This method generates a score for each option using OpenAI's GPT-3 API and the LLM algorithm.
        @return:
            The LLM score result.

    @method policy_update:
        This method updates the policy of the LLM algorithm.
    """

    def __init__(self, evaluate: Evaluate):
        """
        TODO:测试prompt
        """
        super().__init__(evaluate)
        self.result = []
        self.prompt = [
            {
                "role": "system",
                "content": "You are a mobile phone user interface assistant. Your task is to help the user navigate through an app by analyzing the available options and predicting which ones will assist them in accomplishing their goal. For each option, provide a confidence rating from 0-10, where 0 means 'unlikely to help' and 10 means 'highly likely to help'. Provide reasoning for each rating."
            },
            {
                "role": "user",
                "content": """
                    I need to accomplish the following task: ["check my WeChat wallet balance"]. Currently the page desription is ["Wechat Home Page"].There is the options:
                    1. "Settings"
                    2. "Services"
                    3. "More"
                    4. "Favorites"
                    5. "Emotions"
                    Please rate each option on its potential to help me complete my task and provide the reasoning behind each rating.
                """
            },
            {
                "role": "assistant",
                "content": """
                    The "Settings" option usually provides various configuration and customization options for the app. While it might contain some general account-related settings, it is unlikely to have a direct option to check your WeChat wallet balance. It may have settings related to notifications, privacy, or general app preferences, but not specifically related to financial transactions.
                    1.Settings: [2]

                    The "Services" option typically contains a range of features and functionalities offered by WeChat. It is quite likely that the WeChat wallet, including balance information, would fall under the Services section. The Services section often includes various payment-related features and account management options, making it a strong candidate for finding the wallet balance.
                    2.Services: [8]

                    The "More" option typically expands to show additional options or sub-menus. It is difficult to determine the exact content of the "More" section without further information. While it is possible that the WeChat wallet balance could be found here, there is no strong indication that it would be more likely than the other options.
                    3.More: [5]

                    The "Favorites" option generally contains saved or bookmarked items within the WeChat app, such as articles, posts, or media content. It is highly unlikely to find a direct option to check your WeChat wallet balance in this section. The Favorites section is more focused on personal preferences rather than financial transactions.
                    4.Favorites: [1]

                    The "Emoticons" option is primarily related to emojis, stickers, or other visual expressions used in messaging. It does not have any direct relevance to checking your WeChat wallet balance. It is safe to assume that this option would not provide any functionality related to financial transactions.
                    5.Emoticons: [1]
                    So the score is  [2,8,5,1,1].
                """
            },
            {
                "role": "user",
                "content": """
                    I need to accomplish the following task: [{}]. I am currently on the [{}] screen which presents the following 5 options:
                    1. [{}]
                    2. [{}]
                    3. [{}]
                    4. [{}]
                    5. [{}]
                    Please rate each option on its potential to help me complete my task and provide the reasoning behind each rating.
                """.format(self.evaluate.model.task, self.evaluate.model.screen.page_description, self.evaluate.model.candidate[0], self.evaluate.model.candidate[1], self.evaluate.model.candidate[2], self.evaluate.model.candidate[3], self.candidate[4])
            },
        ]

    def score(self):
        if self.evaluate.model.candidate == []:
            raise Exception("Please call Select function first!")
        response = openai.Completion.create(
            model="gpt-3.5-turbo",
            messages=self.prompt,
            temperature=0.3,
            max_tokens=1024,
        )
        result = response.choices[0]["message"]["content"]
        result = result[result.find("the score is")+13:]
        result = result.replace("[", "").replace("]", "").split(",")
        result = [int(result[i])/10 for i in range(len(result))]
        self.result = result
        return result

    def policy_update(self):
        #TODO:更新policy
        pass


class IG_Judge(Judge):
    """
    TODO：This class represents a judge that evaluates a candidate item using Information Gain.
    描述的是当点击一个控件后，任务完成的不确定性下降的程度，或者说带来的新信息有多少
    信息增益：熵-条件熵
    熵：在当前已完成的路径中，完成任务的概率（或者说之前讨论的覆盖率）
    条件熵：【如果选择该节点，出现的新页面中节点的匹配度】的熵
    计算出信息增益后按照Minmax归一化到0-10分
    """

    def __init__(self, evaluate: Evaluate):
        super().__init__(evaluate)


class Prior_Judge(Judge):
    """
    TODO：
    This class represents a judge that evaluates a candidate item using the Prior algorithm.
    """

    def __init__(self, evaluate: Evaluate):
        super().__init__(evaluate)

    def query(self):
        pass


class Markov_Judge(Judge):
    """
    This class represents a judge that evaluates a candidate item using the Markov algorithm.
    基于历史数据的，在已完成的路径中，选择该节点后，下一个节点被选择的频率分布，例如某个按钮点击频率次数太低，就不会被选中。 
    """

    def __init__(self, evaluate: Evaluate):
        super().__init__(evaluate)


class Allocator:
    """
    This class represents a weight allocator that allocates weights to the judeges.
    """
    weights = []  # 权重

    def __init__(self, evaluate: Evaluate):
        self.evaluate = evaluate
        for _ in range(NUM_JUDGES):
            self.weights.append(1/NUM_JUDGES)  # 初始化权重

    def allocate(self):
        """
        This method allocates weights to the candidate items.
        """
        return self.weights

    def update(self):
        """
        This method updates the weights.
        """
        pass

    def feedback(self):
        """
        This method updates the weights according to the feedback.
        """
        pass
