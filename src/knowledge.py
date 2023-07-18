from langchain import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores.redis import Redis

from langchain.document_loaders import TextLoader
from src.database import Database
import csv


EMBEDDING_DIM = OpenAIEmbeddings(openai_api_key="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")
class KnowledgeBase:
    def __init__(self,database):
        self.database = database
    

class PageJump_KB(KnowledgeBase):
    def __init__(self,database):
        super().__init__(database)
        self.pages = []
        self.embeddings = EMBEDDING_DIM
        self.db = FAISS.from_documents(self.pages, self.embeddings)

    
    def update_pages(self,page_id):
        self.pages+=TextLoader(file_path='./page/static/data/page'+str(page_id)+'.txt').load()
        self.db.add_documents(TextLoader(file_path='./page/static/data/page'+str(page_id)+'.txt').load())
        
    def find_most_similar_page(self,query):
        docs = self.db.similarity_search(query)
        print(docs[0].page_content)
        return docs[0].page_content
    
    def find_next_page(self,query,edge):
        Start = self.find_most_similar_page(query)
        return self.database.get_description(Start,edge)

class Task_KB(KnowledgeBase):
    def __init__(self, database):
        super().__init__(database)
        self.tasks = [] 
        #读取history.csv中的task列，并在此处加载到这里的tasks中
        with open("history.csv", 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                self.tasks.append(row['task'])
        self.embeddings = EMBEDDING_DIM
        self.db = FAISS.from_documents(self.tasks, self.embeddings)

    def update_datas(self,new_task):
        self.tasks+=new_task
        self.db.add_documents(new_task)
        
    def find_most_similar_tasks(self,query):
        docs = self.db.similarity_search(query)
        print(len(docs))
        print(docs)
        return docs
    
    def get_path(self,query):
        return self.database.get_path(query)
