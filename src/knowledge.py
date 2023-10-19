import copy
import json
import os
from langchain import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.document_loaders.csv_loader import CSVLoader
import openai

from src.utility import get_top_combined_similarities, get_top_similarities

OPENAI_KEY = os.getenv('OPENAI_API_KEY')


class KnowledgeBase:
    def __init__(self, database):
        self.database = database


class PageJump_KB(KnowledgeBase):
    def __init__(self, database):
        super().__init__(database)
        loader = CSVLoader(file_path='src/KB/pagejump/pagejump.csv', csv_args={
            'delimiter': ',',
            'quotechar': '"',
            'fieldnames': ['Origin', 'Edge', 'Destination', "Description"]
        })
        self.data = loader.load()
        self.edge_data = copy.deepcopy(self.data)
        self.origin_data = copy.deepcopy(self.data)
        for i in range(len(self.data)):
            self.edge_data[i].page_content = self.data[i].page_content.split("Edge:")[
                1].split("Destination:")[0]
            self.origin_data[i].page_content = self.data[i].page_content.split("Origin:")[
                1].split("Edge:")[0]
        self.embeddings = OpenAIEmbeddings(
            client="GUI_LLM", openai_api_key=OPENAI_KEY)
        print(openai.api_key)
        print(openai.api_base)
        self.db = FAISS.from_documents(self.edge_data, self.embeddings)
        self.retriever = self.db.as_retriever(
            search_type="similarity_score_threshold", search_kwargs={"score_threshold": .9})

    def find_next_page(self, origin: str, edge: str) -> list[str]:
        docs = self.retriever.vectorstore.similarity_search_with_relevance_scores(
            edge, k=4, score_threshold=0.9)
        if docs == []:
            return []

        indexs = [docs[i][0].metadata["row"] for i in range(len(docs))]
        self.origin_db = FAISS.from_documents(
            [self.origin_data[i] for i in indexs], self.embeddings)
        self.origin_retriever = self.origin_db.as_retriever(
            search_type="similarity_score_threshold", search_kwargs={"score_threshold": .9})
        docs = self.origin_retriever.vectorstore.similarity_search_with_relevance_scores(
            origin, k=1, score_threshold=0.8)
        if docs == []:
            return []
        final_index = docs[0][0].metadata["row"]
        Destination = self.data[final_index].page_content.split("Destination:")[
            1].split("\n")
        return Destination


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
                *[(i["Task"], i["Trace"]) for i in result])
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
                *[(i["Task"], i["Trace"]) for i in result])
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
                *[(i["Task"], i["Trace"]) for i in result])
            return task, knowledge
        else:
            return None, None


if __name__ == "__main__":
    kb = Task_KB(None)
    kb.find_most_similar_tasks("Send an email to my boss")
