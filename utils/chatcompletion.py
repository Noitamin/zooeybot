from openai import OpenAI
from config import OPENAI_KEY, DEEPSEEK_KEY, XAI_API_KEY

openai_client = OpenAI(api_key=OPENAI_KEY)
ds_client = OpenAI(api_key=DEEPSEEK_KEY, base_url="https://api.deepseek.com")
xai_client = OpenAI(api_key=XAI_API_KEY, base_url="https://api.x.ai/v1")


def completion_xai(message):
    response = xai_client.chat.completions.create(
        model="grok-4-1-fast",
        messages=message
    )
    return response.choices[0].message.content


def completion_ds(message):
    response = ds_client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=message,
        max_tokens=1000,
        temperature=1.0,
        stream=False,
        extra_body={"thinking": {"type": "disabled"}}
    )
    return response.choices[0].message.content


def completion(message):
    response = openai_client.chat.completions.create(
        model="gpt-5.4-nano",
        messages=message,
        max_completion_tokens=256,
        timeout=60
    )
    return response.choices[0].message.content
