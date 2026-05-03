from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="not-needed" 
)

response = client.chat.completions.create(
    model="qwen2.5-coder-1.5b-instruct",
    messages=[
        {"role": "user", "content": "Hello, what are you?"}
    ]
)

print(response.choices[0].message.content)