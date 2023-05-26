import math
import openai
from Screen.init import Screen


class LLM:
    description = ""  # 用户初始的任务意图
    screen = Screen()  # 当前界面信息的包
    prom_decision = ""  # 当前的prompt
    index = 0  # 步骤索引，表明当前是第几步
    current_path = []  # 当前的路径
    current_path_str = ""
    candidate = []  # 当前的候选项编号
    decision_result = []  # 决策输出的候选项概率
    evaluate_result = []  # 评估输出的候选项概率

    gamma = {}

    def __init__(self, screen) -> None:
        self.screen = screen
        
    def update(self,screen):
        """
        @description: 更新LLM的状态
        @param {*}
        @return {*}
        """
        self.description = ""
        self.screen = screen
        self.prom_decision = ""
        self.index = self.index+1
        self.candidate = []
        self.decision_result = []
        self.evaluate_result = []
        

    def decision(self):
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
        if len(self.prom_decision) > 7500:
            return False
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
        self.candidate = {}
        for key, value in probs.items():
            self.candidate.append(
                zip(int(key), self.screen.semantic_info[int(key)-1]))
            self.decision_result.append(math.exp(value))
        print(self.candidate)

    def generate_prompt_decision(self, semantic_info: str) -> str:
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

    def evaluate(self):
        """
        @description: 评估当前的候选项对完成任务的概率,实现机制：交给LLM判断该组件是否对完成任务有帮助
        @param {self.gamma} 惩罚因子，衡量每一个组件被惩罚的概率
        @param {self.candidate}  当前的候选项，一共有五项
        @return {*}
        在评估模块当中，可能受以下机制影响：
        1，由LLM判断各个候选项对完成任务的帮助程度；
        2，由知识库（KB，Knoeledge Base）评估候选项（TODO）
        3，由app使用经验评估候选项（TODO）
        可能有以下挑战：
        1，决策给出的top5的候选项都不对，根据先验知识应该选择另外一个top5之外的控件（待解决，不难）
        """
        if self.candidate == []:
            raise Exception("Please call decision function first!")
        self.initialize_evaluate_prompt([item[1] for item in self.candidate])
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=self.prom_evaluate,
            temperature=0.3,
            max_tokens=1024,
        )
        result = response.choices[0].text
        result = result[result.find("The score is")+13:]
        result = result.replace("[", "").replace("]", "").split(",")
        result = [int(result[i])/10*gamma[i] for i in range(len(result))]
        self.evaluate_result = result

    def initialize_evaluate_prompt(self, components):
        self.prom_evaluate = """Example:
You are a mobile phone user with the intent to [check your WeChat wallet balance]. Currently, you are on the [home page] which presents 5 options:
["Settings", "Services", "More", "Favorites", "Emoticons"]
As an AI assistant aiming to help the user accomplish their goal, analyze each of these 5 options and rate them on a scale of 0-10 for confidence in helping the user complete their intended task.
Provide reasoning and explanations for why each option receives the confidence rating you assign. Think step by step.

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
The score is [2,8,5,1,1].<END>

You are a mobile phone user with the intent to [{}]. Currently, you are on the [{}] which presents 5 options:
[{},{},{},{},{}]
As an AI assistant aiming to help the user accomplish their goal, analyze each of these 5 options and rate them on a scale of 0-10 for confidence in helping the user complete their intended task.
Provide reasoning and explanations for why each option receives the confidence rating you assign. Think step by step.""".format(self.description, self.screen.page_description, components[0], components[1], components[2], components[3], components[4])

    def predict(self):
        """
        @description: 根据当前screen的semantic_nodes预测下一个页面包含的内容，组织成html格式
        @param {*}
        @return {*}
        """
        pass

    def initialize_predict_prompt(self):
        self.prom_evaluate = """Example:
You are a mobile phone user with the intent to [check your WeChat wallet balance]. Currently, you are on the [home page] with components organized as HTML-like format:
<body>
    <List class="container">
        <ListItem class="messager">Bowen</ListItem>
        <ListItem class="group chat">OOVVCI</ListItem>
    </List>
    <TabList class="tab">
        <TabItem class="tab-item">Chats</TabItem>
        <TabItem class="tab-item">Contacts</TabItem>
        <TabItem class="tab-item">Discover</TabItem>
        <TabItem class="tab-item">Me</TabItem>
    </TabList>
</body>
As an AI assistant aiming to predict page-components after clicking each item, give the extended page HTML-like format:

"""

    def find_by_knowledge_base(self):
        """
        @description: 根据知识库中的信息，对当前的决策进行指导
        @param {*}
        @return {*}
        """
        pass
    
    def error_detection(self):
        """
        @description: 验证当前决策中是否存在错误
        @param {self.decision_result,self.screen,self.evaluate_result}
        @return {*}
        """
        pass
