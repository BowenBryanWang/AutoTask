from langchain.chat_models import ChatOpenAI
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)

def trans_prompt_2_openai(prompts: list):
    messages = []
    for prompt in prompts:
        if prompt.role == "system":
            messages.append(SystemMessage(content=prompt.content))
        elif prompt.role == "user":
            messages.append(HumanMessage(content=prompt.content))
        elif prompt.role == "assistant":
            messages.append(AIMessage(content=prompt.content))
    return messages

import openai
import json
from src.cache import persist_to_file

@persist_to_file("Cache.pickle")
def chat(prompt):
    print('connecting to gpt')
    response = openai.ChatCompletion.create(
        model='gpt-4',
        messages=prompt,
        temperature=0,
        stream=True  # this time, we set stream=True
    )
    collected_messages = ""
    print('start streaming...')
    for chunk in response:
        chunk_message = chunk['choices'][0]['delta'].get('content', '')
        print(chunk_message, end="")
        collected_messages += chunk_message
        
    return collected_messages

def GPT(prompt):
    while True:
        try:
            result = chat(prompt=prompt)
            result_json = json.loads(result[result.find("{"):result.rfind("}")+1])
            return result_json
        except Exception as e:
            print(e)
            continue
        