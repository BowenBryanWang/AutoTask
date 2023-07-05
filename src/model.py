import math
from typing import Optional
import numpy as np
import openai
import pandas as pd
import scipy
from evaluate import Evaluate
from page.init import Screen
from predict import Predict


class Model:

    def __init__(self, screen: Optional[Screen] = None, description: str = "", prev_model=None):
        """
        Initializes a Model object with the given screen and description.

        Args:
        - screen: A Screen object representing the current screen information.
        - description: A string representing the task description.
        - prev_model: A Model object representing the previous model.

        Returns:
        None
        """
        
        if screen is not None:
            self.screen = screen
        self.Task_description = description
        if prev_model is not None:
            self.prev_model = prev_model
            prev_model.next_model = self
            self.current_path = self.prev_model.current_path.copy().append(self.screen.page_description)
            self.current_path_str = self.prev_model.current_path_str + self.screen.page_description
            self.index = self.prev_model.index + 1
        else:
            self.index = 0
            self.current_path = [self.screen.page_description]
            self.current_path_str = self.screen.page_description
        self.next_model=None
        self.candidate = []
        self.predict_module = Predict(self)
        self.plan_module = Plan(self)
        self.evaluate_module = Evaluate(self)
        
        

    def select(self):
        """
        @description: 一步推理:将界面信息输入LLM,让LLM做出决策,只需要获得决策结果的top5的prob并更新到candidate即可
        @param {*}
        @return {*}
        """
        print("==================================================")
        # semantic_info = expand_semantic(semantic_info)
        print("semantic_info", self.screen.semantic_info)
        print("==================================================")
        self.generate_decision_prompt(
            semantic_info=str(self.screen.semantic_info))
        # if len(self.prom_decision) > 7500:
        #     return False
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=self.prom_decision,
            temperature=0.3,
            max_tokens=512,
            logprobs=5,
            stop="<EOC>",
        )
        tokens = response["choices"][0]["logprobs"]["tokens"]
        # 判断"S","OC"是否连续出现在tokens中
        index_of_choice = 0
        if "S" in tokens and "OC" in tokens:
            index_S, index_OC = tokens.index("S"), tokens.index("OC")
            if index_S == index_OC-1:
                index_of_choice = index_OC+2
        print(tokens[index_of_choice])
        probs = response["choices"][0]["logprobs"]["top_logprobs"][index_of_choice]
        self.candidate = []
        for key, value in probs.items():
            self.candidate.append(
                zip(int(key), self.screen.semantic_info[int(key)-1]))
            self.decision_result.append(math.exp(value))
        print(self.candidate)

    def generate_decision_prompt(self, semantic_info: str) -> str:
        """
        @description: 产生decision结构的prompt
        @param {semantic_info: str} 语义信息
        @return {*}
        """
        print(type(semantic_info))
        self.prom_decision = self.prom_decision+"""{},[Begin]Current page components:"[{}]".""".format(
            str(self.index+1), semantic_info
        )
        self.index += 1
        return self.prom_decision

    def initialize_descion_prompt(self, init):
        self.description = init
        self.prom_decision = """A user's intention is to 'Turn off Dark mode in WeChat'.
    1,Current page components:"['1,{}-{}-{More function buttons}-{RelativeLayout}', '2,{}-{}-{Search}-{RelativeLayout}', '3,{Me}-{Me}-{}-{RelativeLayout}', '4,{Discover}-{Discover}-{}-{RelativeLayout}', '5,{Contacts}-{Contacts}-{}-{RelativeLayout}', '6,{Chats}-{Chats}-{}-{RelativeLayout}']".The current page is:"Homepage".Expecting the next page to appear :['{Settings}-{}-{}-{LinearLayout}'].Currently choose one component :[Click on <SOC>3,Me<EOC> ].
    2,Current page components:"['1,{Settings}-{}-{}-{LinearLayout}', '2,{Sticker Gallery}-{}-{}-{LinearLayout}', '3,{My Posts}-{}-{}-{LinearLayout}', '4,{Favorites}-{}-{}-{LinearLayout}', '5,{Services}-{}-{}-{LinearLayout}']".The current page is:"Me page".Expecting the next page to appear :['{General}-{}-{}-{LinearLayout}'].Currently choose one component :[Click on <SOC>1,Settings<EOC> ].
    3,Current page components:"['1,{My Information & Authorizations}-{}-{}-{LinearLayout}', "2,{Friends' Permissions}-{}-{}-{LinearLayout}", '3,{Privacy}-{}-{}-{LinearLayout}', '4,{General}-{}-{}-{LinearLayout}', '5,{Chats}-{}-{}-{LinearLayout}', '6,{}-{}-{Back}-{LinearLayout}']".The current page is:"Settings page".Expecting the next page to appear :['{Dark Mode}-{}-{}-{LinearLayout}'].Currently choose one component :[Click on <SOC>4,General<EOC> ].
    4,Current page components:"['1,{Manage Discover}-{}-{}-{LinearLayout}', '2,{Photos, Videos, Files & Calls}-{}-{}-{LinearLayout}', '3,{Text Size}-{}-{}-{LinearLayout}','4,{Dark Mode}-{Auto}-{}-{LinearLayout}', '5,{}-{}-{Back}-{LinearLayout}']".The current page is:"Settings-General subpage".Expecting the next page to appear :["DONE!"].Currently choose one component :[Click on <SOC>4,Dark Mode, The Task is DONE!<EOC> ].

    Rules:
    1,UI components are organized as {major text}-{all text}-{description}-{android class}.
    2,Please strictly follow the answer format:"Expecting...Currently".
    3,Only one short instruction is allowed to be generated per step.
    4,Each instruction can only choose from the current components.Indicate the serial number!
    A user's intention is to """ + "["+init+"]\n"

