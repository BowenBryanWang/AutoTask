import os


from src.utility import get_top_combined_similarities, get_top_similarities

OPENAI_KEY = os.getenv('OPENAI_API_KEY')


class KnowledgeBase:
    def __init__(self, database):
        self.database = database


class Task_KB(KnowledgeBase):
    def __init__(self):
        pass

    def find_most_similar_tasks(self, query):
        result = get_top_similarities(s=query, csv_file=os.path.join(
            os.path.dirname(__file__), 'KB/task/task.csv'), k=5, field="Task")
        if len(result) > 0:
            similar_task, similar_trace = zip(
                *[(i["Task"], i["Trace"]) for i in result])
            return similar_task, similar_trace
        return [], []


class Error_KB(KnowledgeBase):
    def __init__(self):
        pass

    def find_experiences(self, query):
        result = get_top_combined_similarities(queries=query, csv_file=os.path.join(
            os.path.dirname(__file__), 'KB/error/error.csv'), k=5, fields=["Task", "Knowledge"])
        if result:
            task, knowledge = zip(
                *[(i["Task"], i["Knowledge"]) for i in result])
            return task, knowledge
        else:
            return None, None


class Decision_KB(KnowledgeBase):
    def __init__(self):
        pass

    def find_experiences(self, query):
        result = get_top_combined_similarities(queries=query, csv_file=os.path.join(
            os.path.dirname(__file__), 'KB/decision/decision.csv'), k=5, fields=["Task", "Knowledge"])
        if result:
            task, knowledge = zip(
                *[(i["Task"], i["Knowledge"]) for i in result])
            return task, knowledge
        else:
            return None, None


class Selection_KB(KnowledgeBase):
    def __init__(self):
        pass

    def find_experiences(self, query):
        result = get_top_combined_similarities(queries=query, csv_file=os.path.join(
            os.path.dirname(__file__), 'KB/selection/selection.csv'), k=5, fields=["Task", "Knowledge"])
        if result:
            task, knowledge = zip(
                *[(i["Task"], i["Knowledge"]) for i in result])
            return task, knowledge
        else:
            return None, None
