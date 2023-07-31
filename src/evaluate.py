from concurrent.futures import ProcessPoolExecutor
import spacy
from sklearn.metrics.pairwise import cosine_similarity
from loguru import logger
import json
import math
import os
import numpy as np
import openai
openai.api_key = os.getenv("OPENAI_API_KEY")

NUM_JUDGES = 1


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

        with open("logs/log{}.log".format(self.model.index), "a") as f:
            f.write("--------------------Evaluate--------------------\n")
        log_file = logger.add("logs/log{}.log".format(self.model.index), rotation="500 MB")
        logger.debug("Evaluate for Model {}".format(self.model.index))
        logger.info("Current Page: {}".format(
            self.model.page_description))
        logger.info("Current Path: {}".format(self.model.current_path_str))
        logger.info("Task: {}".format(self.model.task))
        self.allocator = Allocator(self)
        self.judges = [LLM_Judge(self)]
        judge_scores = []
        # with ProcessPoolExecutor() as executor:
        #     # Submit the score method of each judge to the executor
        #     judge_score_futures = [executor.submit(judge.score, self.model.candidate) for judge in self.judges]
        #     # Retrieve the results from the futures
        #     judge_scores = [future.result() for future in judge_score_futures]
        weights = self.allocator.allocate()
        self.score = np.zeros(len(self.model.candidate), dtype=np.float64)  # 初始化一个长度为5的全零数组作为总得分

        for judge in self.judges:
            # 获取当前评委的打分结果，并将其转换为浮点数数组
            judge_scores = np.array(judge.score(), dtype=np.float64)
            print("judge_scores",judge_scores)
            # 将当前评委的打分结果与对应的权重相乘
            weighted_scores = judge_scores * weights[self.judges.index(judge)]

            # 将当前评委的加权打分结果累加到总得分中
            self.score += weighted_scores

            
        
        print("judge_scores",judge_scores)

        logger.info("Judge Scores: {}".format(judge_scores))
        logger.info("Weights: {}".format(weights))
        logger.warning("Score: {}".format(self.score))
        logger.debug("Evaluate for Model {} Done".format(self.model.index))
        logger.remove(log_file)
        self.node_selected = self.model.candidate_str[np.argmax(self.score)]
        self.node_selected_id = self.node_selected.split("id=")[1].split(" ")[0]
        self.model.current_path.append(self.node_selected)
        self.model.current_path_str += self.node_selected
        return self.score


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
                "content": """You are a mobile phone user interface assistant. Your task is to help the user navigate through an app by analyzing the available options and predicting which ones will assist them in accomplishing their goal. For each option, provide a confidence rating from 0-10, where 0 means 'unlikely to help' and 10 means 'highly likely to help'.
                Use the following steps to respond to user inputs. Fully restate each step before proceeding. i.e. "Step 1: Reason..."
                Step 1:Reason step-by-step about how each option contributes to the user's goal.
                Step 2:Output a JSON object structured like: {"score": []}.
                """
            },
            {
                "role": "user",
                "content": """
                    Task: "Turn on Dark mode". 
                    Current path: "HomePage".
                    Options:
                    '''HTML
                        <button id=5 class='com.whatsapp:id/menuitem_overflow' description='More options'> </button>
                        <button id=10 class='com.whatsapp:id/contact_photo' description='Wang Bowen'> </button>
                        <button id=2 class='com.whatsapp:id/home_tab_layout' description='Calls'> </button>
                        <button id=3 class='com.whatsapp:id/home_tab_layout' description='Status'> </button>
                        <button id=4 class='com.whatsapp:id/home_tab_layout' description='Community'> </button>
                    '''
                """
            },
            {
                "role": "assistant",
                "content": """
                    Step 1: 
                    1,Score: 8/10
                    Reasoning: This option is labeled as "More options" and is likely to provide additional settings and customization options. Since Dark Mode is a common feature in most apps, it is reasonable to expect that the option to enable Dark Mode may be found within the "More options" menu. Therefore, there is a high likelihood that this option will assist you in accomplishing your task.

                    2: Score: 2/10
                    Reasoning: This option appears to be related to a contact photo and is unlikely to be directly associated with enabling Dark Mode. The description "Wang Bowen" suggests that it is specific to a particular contact, rather than a system-wide setting. Therefore, the likelihood of this option assisting you in turning on Dark Mode is low.

                    3: Score: 2/10
                    Reasoning: This option represents the "Calls" tab in the home page, and it is unlikely to be directly related to enabling Dark Mode. The description "Calls" suggests that it is specific to the call-related functionality within WhatsApp. Therefore, the likelihood of this option helping you turn on Dark Mode is low.

                    4: Score: 2/10
                    Reasoning: This option represents the "Status" tab in the home page, and it is unlikely to be directly related to enabling Dark Mode. The description "Status" indicates that it is specific to the status-related functionality within WhatsApp. Therefore, the likelihood of this option assisting you in turning on Dark Mode is low.

                    5: Score: 2/10
                    Reasoning: This option represents the "Community" tab in the home page, and it is unlikely to be directly related to enabling Dark Mode. The description "Community" suggests that it is specific to community-related features, which are unlikely to include Dark Mode settings. Therefore, the likelihood of this option helping you turn on Dark Mode is low.
                    
                    Step 2:  {"score": [8, 2, 2, 2, 2]}
                """
            },
            {
                "role": "user",
                "content": """
                    Task: "{}".
                    Current path: "{}".
                    Options:
                    '''HTML
                    {}
                    '''
                """.format(self.evaluate.model.task, self.evaluate.model.current_path_str, "".join([self.evaluate.model.screen.semantic_info[i-1] for i in self.evaluate.model.candidate]))
            },
        ]
        
    def score(self):
        if self.evaluate.model.candidate == []:
            raise Exception("Please call Select function first!")
        print(self.prompt)
        response = openai.ChatCompletion.create(
            model = "gpt-3.5-turbo",
            messages = self.prompt,
            temperature=0.3,
        )
        result = response.choices[0]["message"]["content"]
        print(result)
        result = json.loads(result[result.find("{"):result.find("}")+1])
        print(result)
        result = result["score"]
        result = [int(result[i]) for i in range(len(result))]
        self.result = result
        return result

    def policy_update(self):
        # TODO:更新policy
        pass


class IG_Judge(Judge):
    """
    TODO：This class represents a judge that evaluates a candidate item using Information Gain.
    描述的是当点击一个控件后，任务完成的不确定性下降的程度，或者说带来的新信息有多少
    信息增益：熵-条件熵
    熵：当前任务完成的不确定性/混乱程度：所有candidate被选择的概率的熵
    条件熵：在选择了一个candidate后，任务完成的不确定性：选择candidate后带来的新页面中，每个元素被选择的概率的熵
    被选择的概率：通过语义相似度计算，计算出每个元素被选择的概率
    计算出信息增益后按照Minmax归一化到0-10分
    """

    def __init__(self, evaluate: Evaluate):
        super().__init__(evaluate)
        self.nlp = spacy.load('en_core_web_md')

    def score(self):
        # 计算初始熵
        if self.evaluate.model.candidate == []:
            raise Exception("Please call Select function first!")
        initial_entropy, initial_probs = self.calculate_entropy(
            [self.evaluate.model.screen.semantic_info[i-1] for i in self.evaluate.model.candidate])

        if self.evaluate.model.predict_module.comp_json == {}:
            raise Exception("Please call Predict function first!")
        information_gains = []

        

        # # 创建进程池
        # with ProcessPoolExecutor() as executor:
        #     # 并行计算信息增益
        #     futures = [executor.submit(self.calculate_information_gain, i, self.evaluate.model.candidate[i], initial_entropy,
        #                                initial_probs, self.evaluate.model.predict_module) for i in range(len(self.evaluate.model.candidate))]
        #     # 计算条件熵

        # 获取计算结果
        # information_gains = [future.result() for future in futures]
        for i in range(len(self.evaluate.model.candidate)):
            information_gains.append(self.calculate_information_gain(i, self.evaluate.model.screen.semantic_info[self.evaluate.model.candidate[i]-1], initial_entropy,
                                       initial_probs, self.evaluate.model.predict_module))

        # 归一化
        normalized_score = (information_gains - np.min(information_gains)) / \
            (np.max(information_gains) - np.min(information_gains)) * 10

        return normalized_score

    def calculate_information_gain(self,i, candidate, initial_entropy, initial_probs, predict_module):
            conditional_entropy, _ = self.calculate_entropy(
                predict_module.comp_json[candidate])
            return (initial_entropy - conditional_entropy) * initial_probs[i]
    def calculate_entropy(self, candidates):
        """
        计算熵
        """
        probs = []
        # 使用spacy解析字符串，得到词向量
        doc_task = self.nlp(self.evaluate.model.task)

        # 将词向量转换为矩阵
        matrix_task = np.array([token.vector for token in doc_task])

        # 计算每个元素与任务描述的语义相似度
        for candidate in candidates:
            doc_candidate = self.nlp(candidate)
            matrix_candidate = np.array(
                [token.vector for token in doc_candidate])
            similarity = cosine_similarity(matrix_task, matrix_candidate)
            probs.append(similarity[0][0])

        # 概率归一化
        probs = np.array(probs)
        probs = probs / probs.sum()

        # 计算熵
        entropy = 0
        for p in probs:
            entropy -= p * math.log2(p)

        return entropy, probs


class Prior_Judge(Judge):
    """
    TODO：
    This class represents a judge that evaluates a candidate item using the Prior knowledge.
    """

    def __init__(self, evaluate: Evaluate):
        super().__init__(evaluate)
        self.sim_tasks = []
        # self.sim_tasks = self.Task_KB.find_most similar_tasks(self.model.task)
        self.sim_paths = []
        #self.sim_paths = [self.Task_KB.get_path(task) for task in sim_tasks]
        self.result = []
        self.prompt = [
            {
                "role": "system",
                "content": "You are a mobile phone user interface assistant. Your task is to help the user navigate through an app by analyzing the available options and predicting which ones will assist them in accomplishing their goal. Some successful examples will be attached to help you evaluate the options. For each option, provide a confidence rating from 0-10, where 0 means 'unlikely to help' and 10 means 'highly likely to help'. Provide reasoning for each rating."
            },
            {
                "role": "user",
                "content": """
                    I need to accomplish the following task: "Turn on Dark mode". Currently the page desription is "HomePage".Here are the options:
                    '''HTML
                        <button id=5 class='com.whatsapp:id/menuitem_overflow' description='More options'> </button>
                        <button id=10 class='com.whatsapp:id/contact_photo' description='Wang Bowen'> </button>
                        <button id=2 class='com.whatsapp:id/home_tab_layout' description='Calls'> </button>
                        <button id=3 class='com.whatsapp:id/home_tab_layout' description='Status'> </button>
                        <button id=4 class='com.whatsapp:id/home_tab_layout' description='Community'> </button>
                    '''
                    Please rate each option on its potential to help me complete my task according to the successful examples and provide the reasoning behind each rating. Think step by step.
                    Here are some successful examples:
                    | Task | Path |
                    | ---- | ---- |
                    | Turn on Dark mode | HomePage -> More options -> Settings -> Chats -> Theme -> Dark |
                    | Turn on Light mode | HomePage -> More options -> Settings -> Chats -> Theme -> Light |
                """
            },
            {
                "role": "assistant",
                "content": """
                    1: <button id=5 class='com.whatsapp:id/menuitem_overflow' description='More options'> </button>
                    Score: 8/10
                    Reasoning: This option is labeled as "More options" and is likely to provide additional settings and customization options. Since Dark Mode is a common feature in most apps, it is reasonable to expect that the option to enable Dark Mode may be found within the "More options" menu. Therefore, there is a high likelihood that this option will assist you in accomplishing your task.

                    2: <button id=10 class='com.whatsapp:id/contact_photo' description='Wang Bowen'> </button>
                    Score: 2/10
                    Reasoning: This option appears to be related to a contact photo and is unlikely to be directly associated with enabling Dark Mode. The description "Wang Bowen" suggests that it is specific to a particular contact, rather than a system-wide setting. Therefore, the likelihood of this option assisting you in turning on Dark Mode is low.

                    3: <button id=2 class='com.whatsapp:id/home_tab_layout' description='Calls'> </button>
                    Score: 2/10
                    Reasoning: This option represents the "Calls" tab in the home page, and it is unlikely to be directly related to enabling Dark Mode. The description "Calls" suggests that it is specific to the call-related functionality within WhatsApp. Therefore, the likelihood of this option helping you turn on Dark Mode is low.

                    4: <button id=3 class='com.whatsapp:id/home_tab_layout' description='Status'> </button>
                    Score: 2/10
                    Reasoning: This option represents the "Status" tab in the home page, and it is unlikely to be directly related to enabling Dark Mode. The description "Status" indicates that it is specific to the status-related functionality within WhatsApp. Therefore, the likelihood of this option assisting you in turning on Dark Mode is low.

                    5: <button id=4 class='com.whatsapp:id/home_tab_layout' description='Community'> </button>
                    Score: 2/10
                    Reasoning: This option represents the "Community" tab in the home page, and it is unlikely to be directly related to enabling Dark Mode. The description "Community" suggests that it is specific to community-related features, which are unlikely to include Dark Mode settings. Therefore, the likelihood of this option helping you turn on Dark Mode is low.
                    
                    So the scores are <BEGIN>[8,2,2,2,2]<END>.
                """
            },
            {
                "role": "user",
                "content": """
                    I need to accomplish the following task: "{}". Currently the page desription is "{}".Here are the options:
                    '''HTML
                    {}
                    {}
                    {}
                    {}
                    {}
                    '''
                    Please rate each option on its potential to help me complete my task according to the successful examples and provide the reasoning behind each rating. Think step by step.
                """.format(self.evaluate.model.task, self.evaluate.model.screen.page_description, self.evaluate.model.candidate[0], self.evaluate.model.candidate[1], self.evaluate.model.candidate[2], self.evaluate.model.candidate[3], self.candidate[4], self.sim_tasks[0], self.sim_paths[0], self.sim_tasks[1], self.sim_paths[1], self.sim_tasks[2], self.sim_paths[2], self.sim_tasks[3], self.sim_paths[3], self.sim_tasks[4], self.sim_paths[4])
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
        result = [int(result[i]) for i in range(len(result))]
        self.result = result
        return result

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

    def __init__(self, evaluate: Evaluate):
        self.weights = []
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
