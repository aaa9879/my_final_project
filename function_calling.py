from openai import OpenAI
import json
import os
os.environ["OPENAI_API_KEY"] = ""
client = OpenAI()
GPT_MODEL = "gpt-3.5-turbo-0613"
def chat_completion_request(messages, tools=None, tool_choice=None, model=GPT_MODEL):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
        )
        return response
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e
tools= [
        {   
            "type": "function",
            "function":{
                "name": "get_record_info",
                "description": """給了一個記帳資訊，請你幫我抓出地點、費用、項目，此外幫我預測是什麼的類別
                """,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "消費金額": {
                            "type": "integer",
                            "description": "花費紀錄的金額. e.g 200",
                        },
                        "開銷項目": {
                            "type": "string",
                            "description": "花費紀錄的開銷項目. e.g 漢堡 ",
                        },
                        "地點": {
                            "type": "string",
                            "description": "花費紀錄的項目. e.g 麥當勞",
                        },
                        "類別": {
                            "type": "string",
                            "enum": ["食","衣","住","行","育","樂","其他"]
                        },
                    },
                    'required':["金額","項目","地點","類別"]
                },
            },
        },
]
messages = []
messages.append({"role": "system", "content": "Don't make assumptions about what values to plug into functions. Ask for clarification if a user request is ambiguous."})
messages.append({"role": "user", "content": "我付房租200元"})
chat_response = chat_completion_request(
    messages, tools=tools
)
assistant_message = chat_response.choices[0].message
messages.append(assistant_message)
tool_call = assistant_message.tool_calls[0].function.arguments
print(tool_call)
