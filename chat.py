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

test_task = embedding_from_string("prevent people from finding and adding them as a friend using their phone number")
# ['1{Me}-{Me}-{}-{Tab}', '2{Discover}-{Discover}-{}-{Tab}', '3{Contacts}-{Contacts}-{}-{Tab}', '4{Chats}-{Chats}-{}-{Tab}', '5{Settings}-{Settings}-{}-{}', '6{Sticker Gallery}-{Sticker Gallery}-{}-{}', '7{My Posts}-{My Posts}-{}-{}', '8{Favorites}-{Favorites}-{}-{}', '9{Services}-{Services}-{}-{}', "10{}-{}-{Friends' Status}-{}", '11{Status}-{Status}-{Add Status}-{}', '12{}-{}-{My QR Code}-{Tab}', '13{Weixin ID: saltyp0}-{Weixin ID: saltyp0}-{}-{Title}']
comps = ["Me","Discover","Contacts","Chats","Settings","Sticker Gallery","My Posts","Favorites","Services","Friends' Status","Status","Add Status","My QR Code","Weixin ID: saltyp0","Title"]
embedding_comps = [embedding_from_string(comp) for comp in comps]
distances = [cosine_similarity(test_task, comp) for comp in embedding_comps]
print(distances)
indices = indices_of_nearest_neighbors_from_distances(distances)
print(indices)
print([comps[i] for i in indices])
exit()


tasks = [embedding_from_string("Viewing the transaction history of their WeChat wallet.")]
strings = [['From the homepage, click on “Me” to access your profile or account settings.','From the homepage, click on “Me” to access your profile or account settings->Once on your profile page, navigate to the “Services” section of the website or application.','From the homepage, click on “Me” to access your profile or account settings->Once on your profile page, navigate to the “Services” section of the website or application->From the “Services” section, select “Wallet” to access your wallet settings.','From the homepage, click on “Me” to access your profile or account settings->Once on your profile page, navigate to the “Services” section of the website or application->From the “Services” section, select “Wallet” to access your wallet settings->Once in your wallet settings, click on “Transactions” to view your transaction history.']]


tasks.append(embedding_from_string("""Enabling the dark mode feature in the WeChat app interface."""))
strings.append(['Go to the homepage of the website or application.','Go to the homepage of the website or application->Once on the homepage, click on “Me” to access your user profile or account settings.','Go to the homepage of the website or application->Once on the homepage, click on “Me” to access your user profile or account settings->From there, navigate to the “Settings” section.','Go to the homepage of the website or application->Once on the homepage, click on “Me” to access your user profile or account settings->From there, navigate to the “Settings” section->In the “Settings” section, select “General”.','Go to the homepage of the website or application->Once on the homepage, click on “Me” to access your user profile or account settings->From there, navigate to the “Settings” section->In the “Settings” section, select “General”->Finally, click on “Dark Mode” to activate it and switch your interface to the dark mode.'])
tasks.append(embedding_from_string("""Sending a red packet with a value of 10¥ to the recipient named Bowen through the WeChat app."""))
strings.append(['Homepage', 'Homepage->Bowen', 'Homepage->Bowen->More', 'Homepage->Bowen->More->Red Packet'])
tasks.append(embedding_from_string("""Accessing the social media feed or posts of the user named Bowen on WeChat, which is commonly referred to as 'Moments'"""))
# strings_i.append(['Go to the homepage','Navigate to Bowen’s profile from the homepage','Click on “Chat info” while on Bowen’s profile page','From the “Chat info” page, select Bowen’s profile.','Once on Bowen’s profile, click on “Moments”'])
strings.append(['Go to the homepage','Go to the homepage->Navigate to Bowen’s profile from the homepage','Go to the homepage->Navigate to Bowen’s profile from the homepage->Click on “Chat info” while on Bowen’s profile page','Go to the homepage->Navigate to Bowen’s profile from the homepage->Click on “Chat info” while on Bowen’s profile page->From the “Chat info” page, select Bowen’s profile.','Go to the homepage->Navigate to Bowen’s profile from the homepage->Click on “Chat info” while on Bowen’s profile page->From the “Chat info” page, select Bowen’s profile->Once on Bowen’s profile, click on “Moments”'])

tasks.append(embedding_from_string("""Disabling or turning off the WeChat Pay feature in the WeChat app."""))
strings.append(['Homepage', 'Homepage->Weixin Pay', 'Homepage->Weixin Pay->Switch to Messaging'])
tasks.append(embedding_from_string("""prevent people from finding and adding them as a friend on the WeChat app using their phone number"""))
strings.append(['Go to the homepage','Go to the homepage->Navigate to Bowen’s profile from the homepage','Go to the homepage->Navigate to Bowen’s profile from the homepage->Click on “Chat info” while on Bowen’s profile page','Go to the homepage->Navigate to Bowen’s profile from the homepage->Click on “Chat info” while on Bowen’s profile page->From the “Chat info” page, select Bowen’s profile.','Go to the homepage->Navigate to Bowen’s profile from the homepage->Click on “Chat info” while on Bowen’s profile page->From the “Chat info” page, select Bowen’s profile->Once on Bowen’s profile, click on “Moments”'])

tasks_i = [embedding_from_string("Viewing the transaction history of their WeChat wallet.")]
strings_i = [['From the homepage, click on “Me” to access your profile or account settings.','Once on your profile page, navigate to the “Services” section of the website or application.','From the “Services” section, select “Wallet” to access your wallet settings.','Once in your wallet settings, click on “Transactions” to view your transaction history.']]
tasks_i.append(embedding_from_string("""Enabling the dark mode feature in the WeChat app interface."""))


strings_i.append(['Go to the homepage of the website or application.','Once on the homepage, click on “Me” to access your user profile or account settings.','From there, navigate to the “Settings” section.','In the “Settings” section, select “General”.','Finally, click on “Dark Mode” to activate it and switch your interface to the dark mode.'])
tasks_i.append(embedding_from_string("""Sending a red packet with a value of 10¥ to the recipient named Bowen through the WeChat app."""))
strings_i.append(['Homepage', 'Bowen', 'More', 'Red Packet'])
tasks_i.append(embedding_from_string("""Accessing the social media feed or posts of the user named Bowen on WeChat, which is commonly referred to as 'Moments'"""))
strings_i.append(['Go to the homepage','Navigate to Bowen’s profile from the homepage','Click on “Chat info” while on Bowen’s profile page','From the “Chat info” page, select Bowen’s profile.','Once on Bowen’s profile, click on “Moments”'])
tasks_i.append(embedding_from_string("""Disabling or turning off the WeChat Pay feature in the WeChat app."""))
strings_i.append(['Homepage', 'Weixin Pay', 'Switch to Messaging'])
tasks_i.append(embedding_from_string("""prevent people from finding and adding them as a friend on the WeChat app using their phone number"""))
strings_i.append(['Go to the homepage','Navigate to Bowen’s profile from the homepage','Click on “Chat info” while on Bowen’s profile page','From the “Chat info” page, select Bowen’s profile.','Once on Bowen’s profile, click on “Moments”'])



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




