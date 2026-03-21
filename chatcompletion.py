import openai
from openai import OpenAI
from config import OPENAI_KEY, DEEPSEEK_KEY, XAI_API_KEY
from xai_sdk import Client
from xai_sdk.chat import user, system


openai_client = OpenAI(api_key=OPENAI_KEY)
ds_client = OpenAI(api_key=DEEPSEEK_KEY, base_url="https://api.deepseek.com")
xai_client = OpenAI(api_key=XAI_API_KEY, base_url="https://api.x.ai/v1")

def completion_xai(message):
    try:
        response = xai_client.chat.completions.create(
            model="grok-4-1-fast",
            messages=message
        )

        ai_output = response.choices[0].message.content

        print(ai_output)

    except Exception as e:
        print(e)
        raise e

    return ai_output


def completion_ds(message):
    try:
        response = ds_client.chat.completions.create(
            model="deepseek-chat",
            messages=message,
            max_tokens=400,
            temperature=1.5,
            stream=False
        )
        
        ai_output = response.choices[0].message.content

    except Exception as e:
        # Check the response status
        #print(response["choices"][0]["finish_reason"])
        #ai_output = response["choices"][0]["finish_reason"]
        # Extract the AI output content
        print(e)
        raise e 
    #print(ai_output)

    return ai_output


def completion(message):
    try:
        response = openai_client.chat.completions.create(
            model="gpt-5.4-nano",
            messages=message,
            max_completion_tokens=256,
            timeout=60
        )

        ai_output = response.choices[0].message.content

    except Exception as e:
        # Check the response status
        #print(response["choices"][0]["finish_reason"])
        #ai_output = response["choices"][0]["finish_reason"]
        # Extract the AI output content
        raise e 
    #print(ai_output)

    return ai_output

