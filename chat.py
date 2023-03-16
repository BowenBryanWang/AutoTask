import openai
openai.api_key = "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"
# # a=[1,2,3,4,5]
# # print(a.pop(-2))
# # print(a)
import pickle
import pandas as pd
from openai.embeddings_utils import (
    get_embedding,
    cosine_similarity,
    distances_from_embeddings,
    tsne_components_from_embeddings,
    chart_from_components,
    indices_of_nearest_neighbors_from_distances,
)
EMBEDDING_MODEL = "text-embedding-ada-002"

embedding_cache_path = "embeddings_cache.pkl"

# load the cache if it exists, and save a copy to disk
try:
    embedding_cache = pd.read_pickle(embedding_cache_path)
except FileNotFoundError:
    embedding_cache = {}
with open(embedding_cache_path, "wb") as embedding_cache_file:
    pickle.dump(embedding_cache, embedding_cache_file)

# define a function to retrieve embeddings from the cache if present, and otherwise request via the API
def embedding_from_string(
    string: str,
    model: str = EMBEDDING_MODEL,
    embedding_cache=embedding_cache
) -> list:
    """Return embedding of given string, using a cache to avoid recomputing."""
    if (string, model) not in embedding_cache.keys():
        embedding_cache[(string, model)] = get_embedding(string, model)
        with open(embedding_cache_path, "wb") as embedding_cache_file:
            pickle.dump(embedding_cache, embedding_cache_file)
    return embedding_cache[(string, model)]

# task = get_embedding("Turn off dark mode in WeChat",engine="text-embedding-ada-002")
# a1=get_embedding("Homepage, Weixin, Chats, Bowen",engine="text-embedding-ada-002")
# a2=get_embedding("Homepage, Me, Settings, Dark Mode",engine="text-embedding-ada-002")
# print(cosine_similarity(task,a1))
# print(cosine_similarity(task,a2))
tasks = [embedding_from_string("Check Wallet Transactions")]
strings = [['Homepage', 'Homepage->Me', 'Homepage->Me->Services', 'Homepage->Me->Services->Wallet', 'Homepage->Me->Services->Wallet->Transactions']]
tasks.append(embedding_from_string("""Enable Dark Mode in WeChat"""))
strings.append(['Homepage', 'Homepage->Me', 'Homepage->Me->Settings', 'Homepage->Me->Settings->General', 'Homepage->Me->Settings->General->Dark'])
tasks.append(embedding_from_string("""Send a 10 yuan red envelope to Bowen"""))
strings.append(['Homepage', 'Homepage->Bowen', 'Homepage->Bowen->More', 'Homepage->Bowen->More->Red Packet'])
tasks.append(embedding_from_string("""Enter Bowen's Moments"""))
strings.append(['Homepage', 'Homepage->Bowen', 'Homepage->Bowen->Chat info', 'Homepage->Bowen->Chat info->Bowen', 'Homepage->Bowen->Chat info->Bowen->Moments'])
tasks.append(embedding_from_string("""Cancel WeChat pay function"""))
strings.append(['Homepage', 'Homepage->Weixin Pay', 'Homepage->Weixin Pay->Switch to Messaging'])
tasks.append(embedding_from_string("""Don't allow people to add me as a friend by 'Mobile'"""))
strings.append(['Homepage', 'Homepage->Me', 'Homepage->Me->Friends status', 'Homepage->Me->Friends status->Set status', 'Homepage->Me->Friends status->Set status->Customize Status','Homepage->Me->Friends status->Set status->Customize Status->Done'])
tasks_i = [embedding_from_string("Check Wallet Transactions")]
strings_i = [['Homepage', 'Me', 'Services', 'Wallet', 'Transactions']]
tasks_i.append(embedding_from_string("""Enable Dark Mode in WeChat"""))
strings_i.append(['Homepage', 'Me', 'Settings', 'General', 'Dark Mode'])
tasks_i.append(embedding_from_string("""Send a 10 yuan red envelope to Bowen"""))
strings_i.append(['Homepage', 'Bowen', 'More', 'Red Packet'])
tasks_i.append(embedding_from_string("""Enter Bowen's Moments"""))
strings_i.append(['Homepage', 'Bowen', 'Chat info', 'Bowen', 'Moments'])
tasks_i.append(embedding_from_string("""Cancel WeChat pay function"""))
strings_i.append(['Homepage', 'Weixin Pay', 'Switch to Messaging'])
tasks_i.append(embedding_from_string("""Don't allow people to add me as a friend by 'Mobile'"""))
strings_i.append(['Homepage', 'Me', 'Friends status', 'Set status', 'Customize Status','Done'])

def get(i,j,a):
    embeddings = [embedding_from_string(string) for string in strings[i]]
    similarity = [cosine_similarity(tasks[j],embedding) for embedding in embeddings]
    embeddings_i = [embedding_from_string(string) for string in strings_i[i]]
    similarity_i = [cosine_similarity(tasks_i[j],embedding) for embedding in embeddings_i]
    res = []
    for k in range(len(similarity)):
        res.append(similarity[k]*a+similarity_i[k]*(1-a))
    return res

def get_mean_pooling(i,j,beta):
    embeddings_i = [embedding_from_string(string) for string in strings_i[i]]
    similarity_i = [cosine_similarity(tasks_i[j],embedding) for embedding in embeddings_i]
    res = []
    for k in range(len(similarity_i)):
        #加权平均池化
        #对于操作序列中的每个单词，计算它在序列中的位置。
        # 使用指数函数计算单词的权重，其中指数为e
        weights = [beta**(k-jj)/sum([beta**(k-jj) for jj in range(k+1)]) for jj in range(k+1)]
        print(weights)
        tmp = 0
        for jj in range(k+1):
            tmp+=similarity_i[jj]*weights[jj]
        res.append(tmp)
    return res

#遍历所有的strings和tasks对，调用get，将res画图，利用subplot，形成i*j的大图像
import matplotlib.pyplot as plt
import numpy as np
for i in range(len(strings)):
    for j in range(len(tasks)):
        res = get(i,j,0.5)
        plt.subplot(len(strings),len(tasks),i*len(tasks)+j+1)
        
        plt.subplots_adjust(wspace=1, hspace=1)
        plt.plot(res)
        plt.title("task"+str(j+1)+"_string"+str(i+1))
plt.show()




