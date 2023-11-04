import time
import openai
import os
import pickle
import traceback
from typing import List
import numpy as np

if os.path.exists('./cache/ebd.pickle'):
    with open('./cache/ebd.pickle', 'rb') as f:
        cache = pickle.load(f)
else:
    cache = {}


def cal_embedding(text, model_name='text-embedding-ada-002'):
    if type(text) == str:
        return cal_embedding([text], model_name)[0]
    to_call_text = [x for x in text if x not in cache]
    if len(to_call_text) > 0:
        while True:
            try:
                result = openai.Embedding.create(
                    model=model_name,
                    input=to_call_text
                )
                break
            except Exception as e:
                traceback.print_exc()
                time.sleep(2)

        for idx, d in enumerate(result['data']):
            cache[to_call_text[idx]] = d['embedding']
        with open('./cache/ebd.pickle', 'wb') as f:
            pickle.dump(cache, f)
    return [cache[x] for x in text]


def cal_similarity(v1, v2):
    vec1 = np.array(v1)
    vec2 = np.array(v2)
    return vec1.dot(vec2)  # / (np.linalg.norm(vec1) * np.linalg.norm(vec2))


def sort_by_similarity(q: str, a_list: List[str]):
    q_ebd = cal_embedding(q)
    a_ebds = cal_embedding(a_list)

    extend_a = [(a, cal_similarity(q_ebd, a_ebd))
                for a, a_ebd in zip(a_list, a_ebds)]
    return extend_a


def cal_similarity_one(q: str, a: str):
    q_ebd = cal_embedding(q)
    a_ebd = cal_embedding(a)
    return cal_similarity(q_ebd, a_ebd)
