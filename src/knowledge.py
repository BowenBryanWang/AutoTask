from langchain import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores.redis import Redis

from langchain.document_loaders import TextLoader
from src.database import Database

class KnowledgeBase:
    def __init__(self,database):
        self.database = database
    

class PageJump_KB(KnowledgeBase):
    def __init__(self,database):
        super().__init__(database)
        self.pages = []
        self.embeddings = OpenAIEmbeddings(openai_api_key="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")
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



