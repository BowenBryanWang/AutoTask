import asyncio
import re
import time
from langchain import OpenAI
import requests
import spacy
from sklearn.metrics.pairwise import cosine_similarity
from loguru import logger
import json
import math
import os
import numpy as np
import openai
openai.api_key = os.getenv(
    'OPENAI_KEY', default="sk-dXUeoKXznBmiycgc06831a96F6Be42149e9aD25eDfA15e8c")
openai.api_base = "https://api.ai-yyds.com/v1"

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
        self.allocator = Allocator(self)
        self.judges = [LLM_Judge(self)]
        judge_scores = []
        weights = self.allocator.allocate()
        asyncio.run(self.judges[0].score_concurrently())
        # while self.judges[0].result["general"] == [] or self.judges[0].result["prior"] == [] or self.judges[0].result["error"] == [] or self.judges[0].result["forward"] == []:
        #     print("waiting")
        #     time.sleep(1)
        judge = self.judges[0]
        print("general", judge.result["general"])
        print("prior", judge.result["prior"])
        print("error", judge.result["error"])
        print("forward", judge.result["forward"])
        for i in range(len(self.model.candidate)):
            judge_scores.append(
                judge.result["general"][i] if judge.result["general"][i] else 0
                + judge.result["prior"][i] if judge.result["prior"][i] else 0
                + judge.result["error"][i] if judge.result["error"][i] else 0
                + judge.result["forward"][i] if judge.result["forward"][i] else 0
            )
        print("judge_scores", judge_scores)
        self.score = judge_scores
        self.model.node_selected = self.model.candidate_str[np.argmax(
            self.score)]
        self.model.node_selected_action = self.model.candidate_action[np.argmax(
            self.score)]
        self.model.node_selected_text = self.model.candidate_text[np.argmax(
            self.score)]
        self.model.node_selected_id = int(
            self.model.node_selected.split("id=")[1].split(" ")[0])
        print("node_selected", self.model.node_selected)
        print("node_selected_id", self.model.node_selected_id)
        current_action = process_action_info(
            self.model.node_selected_action, self.model.node_selected_text, self.model.node_selected)
        self.model.log_json["@Previous_Step"] = self.model.current_path_str
        self.model.current_path.append(current_action)
        self.model.log_json["@Action"] = current_action
        self.model.current_path_str = "->".join(self.model.current_path)
        log_info = {
            "Name": "Evaluate",
            "Description": "This module is an evaluation module, evaluating the selected components of their contribution to fulfilling the user's intent",
            "Output": {key: item for key, item in zip(self.model.candidate_str, self.score)},
        }
        self.model.log_json["@Module"].append(log_info)
        return self.score


def process_action_info(action, params, node):
    if action == "click":
        return "Action: Click on {}".format(node)
    elif action == "edit":
        return "Action: Edit {} with {}".format(node, params)


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
        super().__init__(evaluate)
        self.result = {}
        self.reason = {}
        self.result["general"] = []
        self.result["prior"] = []
        self.result["error"] = []
        self.result["forward"] = []
        self.modified_result = None
        self.insert_prompt = None

    async def LLM_output(self, name, prompt):
        print("prompt:", prompt[-1])
        resp = await openai.ChatCompletion.acreate(
            model="gpt-4", messages=prompt, temperature=0)
        text = resp.choices[0]["message"]["content"]
        print("text", text)
        json_string = text[text.find("{"):text.rfind("}")+1]
        # pattern = r"({.*?})"
        # match = re.search(pattern, text)
        # json_string = match.group() if match else None  # 获取匹配的JSON字符串
        if json_string:
            text_json = json.loads(json_string)
            score, reason = text_json["score"], text_json["reason"]
            self.result[name] = score
            self.reason[name] = reason
            print("score", score)
            print("reason", reason)
        print("---------------------------" + name +
              " done---------------------------")

    async def score_concurrently(self):
        self.general_prompt = [
            {
                "role": "system",
                "content": """
You are a mobile UI expert acting as a "General Scorer." Your role is specialized in helping the user navigate through an app by analyzing the options available on the current page and predicting which ones are most likely to assist them in accomplishing their goal. Note that your responsibility is strictly focused on the current page's options, and you will not consider external factors or errors—that is the job of the "Prior Scorer" and "Error Scorer." and "Forward Scorer".
Use the following steps to respond to user inputs.
Hints:
Some of the UI components might be wrapped by a parent node (e.g., <div><node/></div>). In such cases, consider its relationship with its parent node's attributes when analyzing.
Your role is highly specialized; you ONLY consider the current page and the options therein. Do not take into account any other disturbance factors.
Follow the steps below:
Step 1: Reason in detail about how each option contributes to or detracts from the user's goal.
Step 2: Output a JSON object with scores and reasoning. The structure should be: {"score": [], "reason": []}
Example:
{
"score": [5, 4, 2, 1, 2],
"reason": [
"...","...","...","...","..."
]
"""
            },
            #             {
            #                 "role": "user",
            #                 "content": """
            # Task: "Turn on Dark mode".
            # Current path: "HomePage".
            # Options:
            # '''HTML
            #     <button id=5 class='com.whatsapp:id/menuitem_overflow' description='More options'> </button>
            #     <button id=10 class='com.whatsapp:id/contact_photo' description='Wang Bowen'> </button>
            #     <button id=2 class='com.whatsapp:id/home_tab_layout' description='Calls'> </button>
            #     <button id=3 class='com.whatsapp:id/home_tab_layout' description='Status'> </button>
            #     <button id=4 class='com.whatsapp:id/home_tab_layout' description='Community'> </button>
            # '''
            # """
            #             },
            #             {
            #                 "role": "assistant",
            #                         "content":
            #                 """
            #             {"score": [8, 2, 3, 1, 4],
            #             "reason":["Reasoning: This option is labeled as 'More options' and is likely to provide additional settings and customization options. Since Dark Mode is a common feature in most apps, it is reasonable to expect that the option to enable Dark Mode may be found within the 'More options' menu. Therefore, there is a high likelihood that this option will assist you in accomplishing your task.", "Reasoning: This option appears to be related to a contact photo and is unlikely to be directly associated with enabling Dark Mode. The description 'Wang Bowen' suggests that it is specific to a particular contact, rather than a system-wide setting. Therefore, the likelihood of this option assisting you in turning on Dark Mode is low.",
            #                 "Reasoning: This option represents the 'Calls' tab in the home page, and it is unlikely to be directly related to enabling Dark Mode. The description 'Calls' suggests that it is specific to the call-related functionality within WhatsApp. Therefore, the likelihood of this option helping you turn on Dark Mode is low.", "Reasoning: This option represents the 'Status' tab in the home page, and it is unlikely to be directly related to enabling Dark Mode. The description 'Status' indicates that it is specific to the status-related functionality within WhatsApp. Therefore, the likelihood of this option assisting you in turning on Dark Mode is low.", "Reasoning: This option represents the 'Community' tab in the home page, and it is unlikely to be directly related to enabling Dark Mode. The description 'Community' suggests that it is specific to community-related features, which are unlikely to include Dark Mode settings. Therefore, the likelihood of this option helping you turn on Dark Mode is low."]}
            #             """},
            {
                "role": "user",
                "content": """
Task: "{}".
Current path: "{}".
Options:
'''HTML
{}
'''
                """.format(self.evaluate.model.task, self.evaluate.model.current_path_str, "".join([self.evaluate.model.screen.semantic_info_list[i-1] for i in self.evaluate.model.candidate]))
            },
        ]
        self.prior_prompt = [
            {
                "role": "system",
                "content": """
You are a mobile UI expert acting as a "Prior Scorer." Your specialized role focuses on guiding the user by refering to prior examples of successfully completed tasks. These prior examples, extracted from a task library, serve as the ground-truth and include detailed task descriptions and execution paths. 
Your job is to rate the available options on the current page based on their similarity to the prior examples. For each option, provide a confidence rating from 0-5, where 0 indicates 'unlikely to help' and 5 indicates 'highly likely to help.'

For each available option on the screen:

Step 1: Compare each option against the prior successful examples. Evaluate how closely each option aligns with the steps or features present in the examples, keeping in mind that the current task might differ.
Step 2: Output a JSON object with scores and reasoning. The structure should be: {"score": [], "reason": []}
Example:
{
"score": [5, 4, 2, 1, 2],
"reason": [
"...","...","...","...","..."
]


Hints:

1,Your evaluation should be based solely on the prior successful examples provided. Do not consider any other factors, they are the job of the "General Scorer" and "Error Scorer." and "Forward Scorer".
2,Your role is highly specialized; you consider the past successful examples as a knowledge base to evaluate the options on the current page. However, be aware that the current task may vary from the examples.
"""
            },
            {
                "role": "user",
                "content": """
Task: "{}".
Current path: {}.
Examples:{}
Options:
'''HTML
{}
'''
""".format(self.evaluate.model.task, self.evaluate.model.current_path_str, [j+":"+"=>".join(k) for j, k in zip(self.evaluate.model.similar_tasks, self.evaluate.model.similar_traces)], "".join([self.evaluate.model.screen.semantic_info_list[i-1] for i in self.evaluate.model.candidate]))
            }]
        self.error_prompt = [
            {
                "role": "system",
                "content": """
You are a mobile UI expert acting as an "Error Scorer." Your specialized role is focused on identifying potential pitfalls and errors that the user might encounter. For this, you will refer to a repository of past failed tasks, including detailed descriptions, error paths, and reasons for failure. These examples will serve as negative indicators to help you evaluate the likelihood of an option leading to an error.

For each available option on the screen:

Step 1: Examine each option in the context of the accumulated error experiences. Evaluate how closely each option mirrors the features or steps that led to errors in past examples.
Step 2: Output a JSON object with scores and reasoning. The structure should be: {"score": [], "reason": []}
Example:
{
"score": [5, 4, 2, 1, 2],
"reason": [
"...","...","...","...","..."
]

Each option should receive a confidence rating from 0-5, where 0 indicates 'highly likely to lead to an error based on past failed examples' and 5 indicates 'unlikely to lead to an error based on past failed examples.'

Hints:

Your evaluation should be primarily influenced by the previous error experiences provided. Do not consider any other factors, they are the job of the "General Scorer" and "Prior Scorer" and "Forward Scorer".
Your role is highly specialized; you use the past failed examples as a knowledge base to identify potential errors in the options on the current page. However, be aware that the current task may vary from the past examples.
"""
            },
            {
                "role": "user",
                "content": """
Task: "{}".
Current path: "{}".
Error experiences:{}
Options:
'''HTML
{}
'''
""".format(self.evaluate.model.task, self.evaluate.model.current_path_str, self.evaluate.model.error_experiences, "".join([self.evaluate.model.screen.semantic_info_list[i-1] for i in self.evaluate.model.candidate]))
            }]
        self.forward_prompt = [
            {
                "role": "system",
                "content": """
                    You are a mobile UI expert acting as a "Forward Scorer." Your specialized role revolves around the long-term consequences of interacting with each option on the screen. For this role, you will be provided with potential outcomes resulting from interactions with each option. With this information at hand, your goal is to anticipate the impact of each consequence on the successful completion of the task.

For each available option on the screen:

Step 1: Analyze the potential outcomes provided for each option. Consider how the consequences of interacting with that option could either benefit or hinder the completion of the task in the long run.
Step 2: Output a JSON object with scores and reasoning. The structure should be: {"score": [], "reason": []}
Example:
{
"score": [5, 4, 2, 1, 2],
"reason": [
"...","...","...","...","..."
]

Each option should receive a confidence rating from 0-5, where 0 indicates 'likely to negatively impact the task completion in the long run' and 5 indicates 'highly beneficial for task completion in the long run.'

Hints:

Your evaluation should be profoundly future-oriented, placing emphasis on long-term outcomes over immediate results. While the "General Scorer," "Prior Scorer," and "Error Scorer" may focus on the present or past, your role uniquely looks ahead.
Your role is highly specialized; you base your decisions on the forecasted results of each option's interaction, considering the overarching mission's long-term success.
"""
            },
            {
                "role": "user",
                "content": """
Task: "{}".
Current path: "{}".
Options with predicted outcomes:
'''HTML
{}
'''
""".format(self.evaluate.model.task, self.evaluate.model.current_path_str, [self.evaluate.model.predict_module.next_comp[i-1] for i in self.evaluate.model.candidate])
            }]
        tasks = [self.LLM_output("general", self.general_prompt), self.LLM_output(
            "prior", self.prior_prompt), self.LLM_output("error", self.error_prompt), self.LLM_output("forward", self.forward_prompt)]
        await asyncio.gather(*tasks)

    def score(self):
        self.prompt = [
            {
                "role": "system",
                "content": """
You are a mobile phone user interface assistant. Your task is to help the user navigate through an app by analyzing the available options and predicting which ones will assist them in accomplishing their goal. For each option, provide a confidence rating from 0-5, where 0 means 'unlikely to help' and 5 means 'highly likely to help'.
Use the following steps to respond to user inputs.
Step 1:Reason step-by-step about how each option contributes to the user's goal.
Step 2:Output a JSON object structured like: {"score": [],"reason":[](refers to each candidate, give your scoring reason)}.
Hint:
1, Some of the components may be warpped by its parent node (such as <div><node/></div>), thus it inherits attibutes from parent node. So when analyzing it you should consider its relationship with its parent node's info.
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
                        "content":
                """
            {"score": [8, 2, 3, 1, 4], 
            "reason":["Reasoning: This option is labeled as 'More options' and is likely to provide additional settings and customization options. Since Dark Mode is a common feature in most apps, it is reasonable to expect that the option to enable Dark Mode may be found within the 'More options' menu. Therefore, there is a high likelihood that this option will assist you in accomplishing your task.", "Reasoning: This option appears to be related to a contact photo and is unlikely to be directly associated with enabling Dark Mode. The description 'Wang Bowen' suggests that it is specific to a particular contact, rather than a system-wide setting. Therefore, the likelihood of this option assisting you in turning on Dark Mode is low.",
                "Reasoning: This option represents the 'Calls' tab in the home page, and it is unlikely to be directly related to enabling Dark Mode. The description 'Calls' suggests that it is specific to the call-related functionality within WhatsApp. Therefore, the likelihood of this option helping you turn on Dark Mode is low.", "Reasoning: This option represents the 'Status' tab in the home page, and it is unlikely to be directly related to enabling Dark Mode. The description 'Status' indicates that it is specific to the status-related functionality within WhatsApp. Therefore, the likelihood of this option assisting you in turning on Dark Mode is low.", "Reasoning: This option represents the 'Community' tab in the home page, and it is unlikely to be directly related to enabling Dark Mode. The description 'Community' suggests that it is specific to community-related features, which are unlikely to include Dark Mode settings. Therefore, the likelihood of this option helping you turn on Dark Mode is low."]}
            """},
            {
                "role": "user",
                "content": """
Task: "{}".
Current path: "{}".
Options:
'''HTML
{}
'''
                """.format(self.evaluate.model.task, self.evaluate.model.current_path_str, "".join([self.evaluate.model.screen.semantic_info_list[i-1] for i in self.evaluate.model.candidate]))
            },
        ]
        if self.insert_prompt:
            self.prompt.append(self.insert_prompt)
        if self.evaluate.model.candidate == []:
            raise Exception("Please call Select function first!")
        print(self.prompt)
        if self.modified_result:
            result = self.modified_result
        else:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=self.prompt,
                temperature=0.5,
            )
            result = response.choices[0]["message"]["content"]
        self.resp = result
        print(result)
        result = json.loads(result[result.find("{"):result.find("}")+1])
        print(result)
        self.reason = result["reason"]
        result = result["score"]
        result = [int(result[i]) for i in range(len(result))]
        self.result = result
        return result

    def update(self, advice: dict):
        self.update_prompt = [
            {
                "role": "system",
                "content": """
You are an intelligent[Evaluate Module] updater. A[Evaluate Module]'s task is to evaluate and score from 0-5 on the selected UI components of their contribution to fulfilling the user's intent".
Now, the[End Human User](represents ground-truth) has provided feedback(criticisms) regarding the scoring result from this former LLM result.
You need to optimize the current[Evaluate Module] based on this feedback and analyze how to utilize the feedback to this former LLM.
You are given the feedback from end-user and description of[Evaluate Module], you have 2 strategies to update the[Evaluate Module]:
1, [Insert]: Insert a slice prompt to the end of the original prompt of[Evaluate Module]'s LLM based on the feedback, augmenting the decision process of it.
2, [Modify]: Step over the LLM decision process of[Evaluate Module] and directly modify the original output result based on the feedback.
Think step-by-step about the process of updating the[Evaluate Module] and output a json object structured like: {"strategy": Insert or Modify, "prompt": your inserted slice prompt, "output": your direct modified output based on the original output. Don't break the format}
"""
            }
        ]
        self.update_prompt.append({
            "role": "user",
            "content": """
                Feedback from end-user(ground-truth): {}
                """.format(advice)
        })
        self.update_prompt.append({
            "role": "user",
            "content": """
                Original Output of[Evaluate Module]:{}
                """.format(self.resp)
        })
        response = requests.post("http://166.111.139.119:12321/query", headers={
            'content-type': 'application/json',
        }, data=json.dumps({
            'msg': self.update_prompt,
            'temp': 1,
        }))
        response_text = json.loads(response.text)['response']
        print(response_text)
        resp = json.loads(
            response_text[response_text.find("{"):response_text.find("}")+1])

        strategy = resp["strategy"]
        prompt = resp["prompt"]
        output = resp["output"]
        if strategy == "Insert":
            self.insert_prompt = {
                "role": "user",
                "content": prompt,
            }
        else:
            self.modified_result = output


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
            [self.evaluate.model.screen.semantic_info_list[i-1] for i in self.evaluate.model.candidate])

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
            information_gains.append(self.calculate_information_gain(i, self.evaluate.model.screen.semantic_info_list[self.evaluate.model.candidate[i]-1], initial_entropy,
                                                                     initial_probs, self.evaluate.model.predict_module))

        # 归一化
        normalized_score = (information_gains - np.min(information_gains)) / \
            (np.max(information_gains) - np.min(information_gains)) * 5

        return normalized_score

    def calculate_information_gain(self, i, candidate, initial_entropy, initial_probs, predict_module):
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
