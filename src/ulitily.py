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
