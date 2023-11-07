import csv
import json
import os


from utility import GPT, Knowledge_prompt, get_top_combined_similarities, get_top_similarities

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


def extract_knowledge(task):

    directory_path = "Shots/"+task.replace(" ", "_")+"/logs"

    def is_json_log(file_name):
        return file_name.startswith('log') and file_name.endswith('.json')

    json_data = []

    for file in os.listdir(directory_path):
        if is_json_log(file):
            with open(os.path.join(directory_path, file), 'r', encoding='utf-8') as f:
                json_data.append(json.load(f))
    with open("Shots/"+task.replace(" ", "_")+"/logs/final.json", "r") as f:
        ACTION_TRACE = json.loads(f.read())

    with open("./src/KB/task/task.csv", "a", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=',')
        writer.writerow([task, ACTION_TRACE["ACTION"]])
    response = GPT(Knowledge_prompt(
        TASK=task, ACTION_TRACE=ACTION_TRACE, log=json_data), tag="knowledge")
    selection_knowledge, decision_knowledge, error_knowledge = response.get(
        "selection"), response.get("decision"), response.get("error-handling")
    selection_path = os.path.join(os.path.dirname(
        __file__), "KB/selection/selection.csv")
    decision_path = os.path.join(os.path.dirname(
        __file__), "KB/decision/decision.csv")
    error_path = os.path.join(
        os.path.dirname(__file__), "KB/error/error.csv")

    self.write_knowledge_to_csv(selection_path, selection_knowledge)
    self.write_knowledge_to_csv(decision_path, decision_knowledge)
    self.write_knowledge_to_csv(error_path, error_knowledge)


def write_knowledge_to_csv(self, file_path, knowledge_list):
    with open(file_path, "a", newline='', encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=',')
        for knowledge in knowledge_list:
            writer.writerow([self.model.task, knowledge["knowledge"]])


extract_knowledge(task="Find my phone's Device Wifi MAC address")
