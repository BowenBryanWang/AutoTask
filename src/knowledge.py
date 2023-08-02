import csv
import json
import os
from langchain import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.document_loaders import TextLoader


class KnowledgeBase:
    def __init__(self, database):
        self.database = database


class PageJump_KB(KnowledgeBase):
    def __init__(self, database):
        super().__init__(database)
        self.pages = TextLoader(
            file_path='./page/static/data/page1.txt').load()
        print(self.pages)
        self.embeddings = OpenAIEmbeddings(
            client="GUI_LLM", openai_api_key="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")
        self.db = FAISS.from_documents(self.pages, self.embeddings)

    def update_pages(self, page_id):
        self.pages += TextLoader(file_path='./page/static/data/page' +
                                 str(page_id)+'.txt').load()
        self.db.add_documents(TextLoader(
            file_path='./page/static/data/page'+str(page_id)+'.txt').load())

    def find_most_similar_page(self, query: str):
        docs = self.db.similarity_search_with_score(query)
        print("内容", docs[0][0].page_content)
        print("分数", docs[0][1])
        return docs[0][0].page_content

    def find_next_page(self, query, edge):
        Start = self.find_most_similar_page(query)
        return self.database.get_destination(Start, edge)


class Task_KB(KnowledgeBase):
    def __init__(self):
        self.tasks = []
        self.similar_tasks = []
        self.task_json = json.load(open("./task.json", encoding='utf-8'))
        self.tasks = self.task_json.keys()
        self.embeddings = OpenAIEmbeddings(
            client="GUI_LLM", openai_api_key="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")
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


if __name__ == "__main__":
    kb = Task_KB(None)
    kb.find_most_similar_tasks("Send an email to my boss")
