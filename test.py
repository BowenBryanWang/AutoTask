
import openai
openai.api_key = "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"

intention = [
    {"role": "system",
     "content": """You are an assistant translating user's intention to more detailed, longer and clearer description.One sentence only!"""},
    {"role": "user",
     "content": """Don't allow others to friending me by 'search phone number' in WeChat"""},
    {"role": "assistant",
     "content": """Prevent people from finding and adding them as a friend on the WeChat app using their phone number"""},
    {"role": "user",
     "content": """Check Wallet Transactions"""},
    {"role": "assistant",
        "content": """Viewing the transaction history of their WeChat wallet"""},
    {"role": "user",
        "content": """Enter Bowen's Moments"""},
    {"role": "assistant",
        "content": """Accessing the social media feed or posts of the user named Bowen on WeChat, which is commonly referred to as 'Moments'"""},
    {"role": "user",
        "content": """Cancel WeChat pay function"""},
     
]
response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=intention,
    temperature=0.5,
)
print(response)
