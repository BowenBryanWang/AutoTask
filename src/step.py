from src.llm import Model


class Step:
    """
    用于记录Agent操作的每一步中的信息
    """
    index = -1
    candidate = []
    decision_result = []
    evaluate_result = []
    gamma = []
    llm = Model()

    def __init__(self, index, llm: Model):
        self.index = index
        self.llm = llm
        try:
            self.candidate = llm.candidate
            self.decision_result = llm.decision_result
            self.evaluate_result = llm.evaluate_result
        except:
            raise Exception("LLM not defined!")
        self.gamma = [0 for _ in range(len(self.candidate))]
