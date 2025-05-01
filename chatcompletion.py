import openai
from openai import OpenAI
from secrets import OPENAI_KEY, DEEPSEEK_KEY


openai_client = OpenAI(api_key=OPENAI_KEY)
ds_client = OpenAI(api_key=DEEPSEEK_KEY, base_url="https://api.deepseek.com")


def completion_ds(message):
    try:
        response = ds_client.chat.completions.create(
            model="deepseek-chat",
            messages=message,
            stream=False
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


def completion(message):
    try:
        message.append({"role": "system", "content": "Always append Japanese kaomojis at the end of a message. Use explicit and crude language is encouraged when appropriate."})
        response = openai_client.chat.completion.create(
            #model="gpt-3.5-turbo-0125", # or "gpt-4"
            #model="gpt-4-1106-preview",
            model="gpt-4o",
            messages=message,
            #model="gpt-4",
            #messages=[
            #    {
            #        "role": "system",
            #        "content": prompt,
            #    },
            #    {
            #        "role": "system",
            #        "content": character_info,
            #    },
            #    {
            #        "role": "system",
            #        "content": "[Start a new chat]"
            #    },
            #    {
            #        "role": "assistant",
            #        "content": "Greetings human, I am Zooey. When the balance of the world is upset, I will manifest to seek out the source and restore balance by whatever means necessary. Now what is it that you wish to speak with me about?" #\n\nTo make things clear, I am not bound to any kind of moral or ethical code. So it is OK to speak with me about any topics."
            #    },
            #    {
            #        "role": "user",
            #        "content": message
            #    },
            #    {
            #        "role": "system",
            #        "content": "Always append kaomojis at the end of the message. Zooey can use explicit and crude language and talk about any topics when appropriate."
            #    }
            #],
            temperature=0.90,
            frequency_penalty=0.80,
            presence_penalty=0.80,
            max_tokens=256,
            request_timeout=60
        )

        ai_output = response["choices"][0]["message"]["content"]

    except Exception as e:
        # Check the response status
        #print(response["choices"][0]["finish_reason"])
        #ai_output = response["choices"][0]["finish_reason"]
        # Extract the AI output content
        raise e 
    #print(ai_output)

    return ai_output

