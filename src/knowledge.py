import copy
import json
import os
from langchain import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.document_loaders.csv_loader import CSVLoader
import openai

OPENAI_KEY = os.getenv('OPENAI_API_KEY')
class KnowledgeBase:
    def __init__(self, database):
        self.database = database


class PageJump_KB(KnowledgeBase):
    def __init__(self, database):
        super().__init__(database)
        loader = CSVLoader(file_path='src/KB/pagejump.csv', csv_args={
            'delimiter': ',',
            'quotechar': '"',
            'fieldnames': ['Origin', 'Edge', 'Destination']
        })
        self.data = loader.load()
        self.edge_data = copy.deepcopy(self.data)
        self.origin_data = copy.deepcopy(self.data)
        for i in range(len(self.data)):
            self.edge_data[i].page_content = self.data[i].page_content.split("Edge:")[1].split("Destination:")[0]
            self.origin_data[i].page_content = self.data[i].page_content.split("Origin:")[1].split("Edge:")[0]
        self.embeddings = OpenAIEmbeddings(
            client="GUI_LLM", openai_api_key=OPENAI_KEY)
        print(openai.api_key)
        print(openai.api_base)
        self.db = FAISS.from_documents(self.edge_data, self.embeddings)
        self.retriever = self.db.as_retriever(search_type="similarity_score_threshold", search_kwargs={"score_threshold": .9})
        

    def find_next_page(self, origin: str, edge: str) -> list[str]:
        docs = self.retriever.vectorstore.similarity_search_with_relevance_scores(edge, k=4, score_threshold=0.9)
        if docs == []:
            return []
        print("内容", docs[0][0].page_content)
        print("分数", docs[0][1])
        indexs  = [docs[i][0].metadata["row"] for i in range(len(docs))]
        self.origin_db = FAISS.from_documents([self.origin_data[i] for i in indexs], self.embeddings)
        self.origin_retriever = self.origin_db.as_retriever(search_type="similarity_score_threshold", search_kwargs={"score_threshold": .9})
        docs = self.origin_retriever.vectorstore.similarity_search_with_relevance_scores(origin, k=1, score_threshold=0.8)
        if docs == []:
            return []
        print("内容", docs[0][0].page_content)
        final_index = docs[0][0].metadata["row"]
        print(final_index)

        Destination = self.data[final_index].page_content.split("Destination:")[1].split("\n")
        return Destination


class Task_KB(KnowledgeBase):
    def __init__(self):
        self.tasks = []
        self.similar_tasks = []
        self.similar_traces = []
        with open(os.path.join(os.path.dirname(__file__), 'KB/task.json'), 'r') as f:
            self.task_json = json.load(f)
        self.tasks = self.task_json.keys()
        self.embeddings = OpenAIEmbeddings(
            client="GUI_LLM", openai_api_key=OPENAI_KEY)
        self.db = FAISS.from_texts(self.tasks, self.embeddings)

    def update_datas(self, new_task):
        self.tasks += new_task
        self.db.add_documents(new_task)

    def find_most_similar_tasks(self, query):
        docs = self.db.similarity_search_with_score(query)
        print(docs)
        for i in range(len(docs)):
            self.similar_tasks.append(docs[i][0].page_content)
            self.similar_traces.append(self.task_json[docs[i][0].page_content])
            print("内容", docs[i][0].page_content)
            print("分数", docs[i][1])
        return self.similar_tasks, self.similar_traces
    
    
class Error_KB(KnowledgeBase):
    def __init__(self):
        self.tasks = []
        self.traces = []
        self.new_screens = []
        self.reasons = []
        with open(os.path.join(os.path.dirname(__file__), 'KB/errors.csv'), 'r') as f:
            #第一列存为task，第二列存为trace
            for line in f.readlines():
                if line.startswith("Task"):
                    continue
                self.tasks.append(line.split(",")[0])
                self.traces.append(line.split(",")[1])
                self.new_screens.append(line.split(",")[2])
                self.reasons.append(line.split(",")[3])
        
        self.embeddings = OpenAIEmbeddings(
            client="GUI_LLM", openai_api_key=OPENAI_KEY)
        self.db = FAISS.from_texts([j+"<EnS>"+k for j,k in zip(self.tasks,self.traces)], self.embeddings)

    def update_datas(self, new_task,new_trace,new_screen,new_reason):
        self.tasks += new_task
        self.traces += new_trace
        self.new_screens += new_screen
        self.reasons += new_reason
        self.db.add_documents(new_task+"<EnS>"+new_trace)

    def find_experiences(self, query):
        docs = self.db.similarity_search_with_score(query)
        print(docs)
        self.experiences = []
        for i in range(len(docs)):
            # self.similar_tasks.append(docs[i][0].page_content)
            # self.similar_traces.append(self.task_json[docs[i][0].page_content])
            # print("内容", docs[i][0].page_content)
            # print("分数", docs[i][1])
            # 综合二者找到对应的下标,根据分割得到的task和trace
            task,trace = docs[i][0].page_content.split("<EnS>")
            # 综合二者找到对应的下标
            index = self.tasks.index(task)
            self.experiences.append({"task":task,"trace":trace,"new_screen":self.new_screens[index],"reason":self.reasons[index]})
        return self.experiences
            
        return self.similar_tasks, self.similar_traces


if __name__ == "__main__":
    kb = Task_KB(None)
    kb.find_most_similar_tasks("Send an email to my boss")
