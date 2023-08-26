import openai

response = openai.Completion.create(
    model="gpt-3.5-turbo",
    messages="hello",
    temperature=1,
)
print(response)