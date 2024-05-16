import os
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import create_sql_agent
import json
from django.conf import settings
from linebot import LineBotApi
from openai import OpenAI
from linebot.models import *
from urllib.parse import quote
import openai
line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
db = SQLDatabase.from_uri("mysql+mysqlconnector://root:0981429209@localhost:3306/my_project")
openai.api_key = os.getenv("OPENAI_API_KEY")


def MyAccount(event):
    flex_message = FlexSendMessage(
        alt_text='Flex_message',
        contents={
          "type": "bubble",
          "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
              {
                "type": "text",
                "text": "我的帳本",
                "color": "#FFFFFF",
                "weight": "bold",
                "size": "xl"
              },
              {
                "type": "text",
                "text": "請選擇要進行的操作",
                "color": "#FFFFFF",
                "weight": "regular"
              }
            ]
          },
          "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
              {
                "type": "button",
                "action": {
                  "type": "uri",
                  "uri": "https://liff.line.me/2004983305-Wxv3l2rx",
                  "label": "記帳"
                }
              },
              {
                "type": "button",
                "action": {
                  "type": "uri",
                  "label": "查詢帳本",
                  "uri": "https://liff.line.me/2004983305-2LqXBLZr"
                }
              }
            ]
          },
          "styles": {
            "header": {
              "backgroundColor": "#00B900"
            }
          }
        }
    )
    line_bot_api.reply_message(event.reply_token, flex_message)



def manageForm(event, mtext, user_id):  # 處理LIFF傳回的from資料
  try:
    flist = mtext[3:].split('/')  # 去除前三個#再分解字串
    User_imput = flist[0]  # 取得輸入資料


    text1 = User_imput
    message = TextSendMessage(
      text=text1
    )
    line_bot_api.reply_message(event.reply_token, message)

  except:
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text='發生錯誤'))


def Form(event, text,user_id):

  category = text.split(',')[0].split(':')[1].strip().strip('"')
  amount = int(text.split(',')[1].split(':')[1].strip().strip('"'))
  item = text.split(',')[2].split(':')[1].strip().strip('"')
  location = text.split(',')[3].split(':')[1].strip().strip('"')
  transaction_type = text.split(',')[4].split(':')[1].strip().strip('"')
  #print(location)
  query_params = {
    "category": category,
    "amount": amount,
    "item": item,
    "location": location,
    "transaction_type": transaction_type,
    "user_id": user_id
  }
  query_params_encoded = {key: quote(str(value)) for key, value in query_params.items()}

  query_string = "&".join([f"{key}={value}" for key, value in query_params_encoded.items()])
  url = f"https://line-lift-form.vercel.app?{query_string}"

  flex_message = FlexSendMessage(
    alt_text='Flex_message',
    contents={
      "type": "bubble",
      "header": {
        "type": "box",
        "layout": "vertical",
        "contents": [
          {
            "type": "text",
            "text": "選單",
            "color": "#FFFFFF",
            "weight": "bold",
            "size": "xl"
          },
          {
            "type": "text",
            "text": "請完成選單",
            "color": "#FFFFFF",
            "weight": "regular"
          }
        ]
      },
      "body": {
        "type": "box",
        "layout": "vertical",
        "contents": [
          {
            "type": "button",
            "action": {
              "type": "uri",
              "uri": url,
              "label": "選單內容"
            }
          },
        ]
      },
      "styles": {
        "header": {
          "backgroundColor": "#00B900"
        }
      }
    }
  )
  line_bot_api.reply_message(event.reply_token, flex_message)


def OpenAI(mtext): #判斷類別和子類別

    flist = mtext[3:].split('/')
    User_input = flist[0]
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    agent_executor = create_sql_agent(llm, db=db, agent_type="openai-tools", verbose=True)
    text1=agent_executor.invoke(

    "User_input="+User_input+"\n"+

    " ''' 不要由資料庫中{個人帳目_收入_支出_table}的來做判斷 ''' "+"\n"+

    " ''' 根據資料庫中的{類別_個人_table}，判斷 User_input 這段用者敘述屬於哪一個{類別}，例如：食、衣、住、行"+"\n"+
    "根據 User_input 判斷{金額}，{金額}是數字，不能用資料庫查詢，例如：200"+"\n"+
    "根據 User_input 判斷{項目名稱}，不能用資料庫查詢，{項目名稱}是該筆帳目的簡介，例如：買麵包" + "\n" +
    "根據 User_input 判斷{地點}，不能用資料庫查詢，{地點}是該筆帳目的發生地點，可以是地名或當地地標，例如：台南、安平古堡、師範大學"+ "\n" +
    "根據 User_input 判斷{交易類型}，不能用資料庫查詢，{交易類型}有兩種：收入(薪水)或支出(購買商品、消費等行為)，例如：支出''' " + "\n" +


    " '''輸出必須包含一個類別、項目名稱、金額、地點、時間，最後用指定格式輸出，無須任何其他輸出，範例：類別:\"類別A\",金額:\"100\",項目名稱:\"買麵包\",地點:\"中壢\",交易類型:\"收入\"，用繁體中文回答，前後不用任何文字''' "
    )
    T=text1.get('output')

    print(User_input+"\n"+T)
    return T