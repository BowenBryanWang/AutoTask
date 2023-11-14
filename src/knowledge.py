import csv
import json
import os
import pickle
import random


from utility import GPT, Knowledge_prompt, get_top_combined_similarities, get_top_similarities, sort_by_similarity

OPENAI_KEY = os.getenv('OPENAI_API_KEY')
COUNT = 0


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
    global COUNT
    Log_path = "../Shots/"+task.replace(" ", "_")+"/logs"

    def is_json_log(file_name):
        return file_name.startswith('log') and file_name.endswith('.json')
    json_data = []
    for file in os.listdir(Log_path):
        if is_json_log(file):
            with open(os.path.join(Log_path, file), 'r', encoding='utf-8') as f:
                json_data.append(json.load(f))
    if not os.path.exists(os.path.join(Log_path, "final.json")):
        return
    with open(os.path.join(Log_path, "final.json"), 'r', encoding="utf-8") as f:
        ACTION_TRACE = json.load(f)

    with open(os.path.join(os.path.dirname(__file__), "KB/task/task.csv"), "a", newline='', encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=',')
        writer.writerow([task, ACTION_TRACE["ACTION"]])
    if "BACK" not in ACTION_TRACE["ACTION_DESC"]:
        return
    COUNT += 1
    print("COUNT", COUNT)
    l = process_sequences(
        ACTION_TRACE["PAGES"], ACTION_TRACE["ACTION"], ACTION_TRACE["ACTION_DESC"])
    resp = GPT(Knowledge_prompt(task, ACTION_TRACE, json_data, l))
    predict_knowledge, selection_knowledge, decision_knowledge = resp.get("prediction"), resp.get(
        "selection"), resp.get("decision")
    for i in range(len(predict_knowledge)):
        index = int(predict_knowledge[i]["index"].replace("Page_", ""))
        predict_knowledge[i]["index"] = ACTION_TRACE["PAGES"][index]
    for i in range(len(selection_knowledge)):
        index = int(selection_knowledge[i]["index"].replace("Page_", ""))
        selection_knowledge[i]["index"] = ACTION_TRACE["PAGES"][index]
    for i in range(len(decision_knowledge)):
        index = int(decision_knowledge[i]["index"].replace("Page_", ""))
        decision_knowledge[i]["index"] = ACTION_TRACE["PAGES"][index]

    if predict_knowledge:
        write_knowledge_to_csv(task, os.path.join(os.path.dirname(
            __file__), "KB/prediction/prediction.csv"), predict_knowledge)
    if selection_knowledge:
        write_knowledge_to_csv(
            task, os.path.join(os.path.dirname(__file__), "KB/selection/selection.csv"), selection_knowledge)
    if decision_knowledge:
        write_knowledge_to_csv(
            task, os.path.join(os.path.dirname(__file__), "KB/decision/decision.csv"), decision_knowledge)


def write_knowledge_to_csv(task, file_path, knowledge_list):
    with open(file_path, "a", newline='', encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=',')
        for knowledge in knowledge_list:
            writer.writerow([task, knowledge["knowledge"], knowledge["index"]])


def find_consecutive_back_sequences(action_desc):
    sequences = []
    current_sequence = []
    for i, action in enumerate(action_desc):
        if action == 'BACK':
            current_sequence.append(i)
        else:
            if current_sequence:
                sequences.append(current_sequence)
                current_sequence = []
    if current_sequence:  # Adding the last sequence if it ends with 'Back'
        sequences.append(current_sequence)
    return sequences


def process_sequences(pages, action, action_desc):
    back_sequences = find_consecutive_back_sequences(action_desc)
    l = []
    for sequence in back_sequences:
        start = sequence[0]
        end = sequence[-1]+1
        prev_pages = pages[max(0, start - len(sequence)):min(len(pages), end-len(sequence)+1)]
        actions = action[start - len(sequence):end-len(sequence)]
        l.append((prev_pages, actions))
    return l


def extract_batch_knowledge():
    for task in os.listdir("../Shots"):
        if task == ".DS_Store":
            continue
        extract_knowledge(task)


def retrivel_knowledge(task, type, page, PER):
    if type == "prediction":
        file_path = os.path.join(os.path.dirname(
            __file__), "KB/prediction/prediction.csv")
    elif type == "selection":
        file_path = os.path.join(os.path.dirname(
            __file__), "KB/selection/selection.csv")
    elif type == "decision":
        file_path = os.path.join(os.path.dirname(
            __file__), "KB/decision/decision.csv")
    else:
        return None
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        data = list(reader)

    num_rows = len(data)
    num_sample = int(num_rows * PER)

    sampled_rows = random.sample(data, num_sample)

    tasks = []
    knowledge = []
    index = []
    for row in sampled_rows:
        tasks.append(row[0]+":"+row[1])
        knowledge.append(row[1])
        index.append(row[2])
    res_task = sort_by_similarity(
        "which knowledge can be used to fulfill the task?"+task, tasks)
    res_page = sort_by_similarity(page, index)
    res = sorted([(i[0], knowledge[tasks.index(i[0])], j[0], i[1]*j[1].mean()) for i in res_task for j in res_page if i[1]*j[1].mean() > 0.75],
                 key=lambda x: x[1], reverse=True)
    knowledge = []
    for i in res:
        knowledge.append(i[1])
    return knowledge


def detect_log():
    for task in os.listdir("../Shots"):
        if task == ".DS_Store":
            continue
        Log_path = "../Shots/"+task.replace(" ", "_")+"/logs"
        if not os.path.exists(Log_path):
            Log_path = "../Shots/"+task.replace(" ", "_")+"/log"
        if not os.path.exists(os.path.join(Log_path, "final.json")):
            print(task)
            Back_steps = 0
            All_steps = len(os.listdir(Log_path))
            Ground_truth = len(os.listdir(Log_path))-2*Back_steps
            with open(os.path.join(os.path.dirname(__file__), "task.csv"), "a", newline='', encoding="utf-8") as f:
                writer = csv.writer(f, delimiter=',')
                writer.writerow([task, Back_steps, All_steps,
                                Ground_truth, 2*Back_steps/All_steps])
            print("No final.json")
            continue

        with open(os.path.join(Log_path, "final.json"), 'r', encoding="utf-8") as f:
            ACTION_TRACE = json.load(f)

        print("BACK steps count:", ACTION_TRACE["ACTION_DESC"].count("BACK"))
        print("All steps count:", len(ACTION_TRACE["ACTION_DESC"]))
        print("Ground truth count:", len(
            ACTION_TRACE["ACTION_DESC"])-2*ACTION_TRACE["ACTION_DESC"].count("BACK"))

        with open(os.path.join(os.path.dirname(__file__), "task.csv"), "a", newline='', encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=',')
            writer.writerow([task, ACTION_TRACE["ACTION_DESC"].count("BACK"), len(
                ACTION_TRACE["ACTION_DESC"]), len(ACTION_TRACE["ACTION_DESC"])-2*ACTION_TRACE["ACTION_DESC"].count("BACK"), 2*ACTION_TRACE["ACTION_DESC"].count("BACK")/len(ACTION_TRACE["ACTION_DESC"])])


if __name__ == "__main__":
    from utility import GPT, Knowledge_prompt, get_top_combined_similarities, get_top_similarities, sort_by_similarity
    # extract_batch_knowledge()
    detect_log()
