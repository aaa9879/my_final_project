import profile

from django.shortcuts import render

# Create your views here.
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
import secrets
import string
from line_bot_app.models import GroupTable, PersonalTable,PersonalGroupLinkingTable
from module import func
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import *

line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(settings.LINE_CHANNEL_SECRET)


@csrf_exempt
def callback(request):
    if request.method == 'POST':
        signature = request.META['HTTP_X_LINE_SIGNATURE']
        body = request.body.decode('utf-8')
        try:
            events = parser.parse(body, signature)
        except InvalidSignatureError:
            return HttpResponseForbidden()
        except LineBotApiError:
            return HttpResponseBadRequest()

        for event in events:
            if isinstance(event, MessageEvent):
                user_id = event.source.user_id  # 取得LINE ID
                profile = line_bot_api.get_profile(user_id)
                #取得用戶名稱
                user_name = profile.display_name
                if isinstance(event.message, TextMessage):
                    mtext = event.message.text
                    if mtext == '我的帳本':
                        func.MyAccount(event)
                    elif mtext[:3] == '###' and len(mtext) > 3:
                        # func.OpenAI(mtext)
                        func.Form(event, mtext, user_id)
                    elif mtext == '建立群組':
                        reply_message='請輸入您要的群組名稱(##您的群組名稱，範例:##Group1)'
                        line_bot_api.reply_message(event.reply_token,TextMessage(text=reply_message))
                    #抓取使用者建立群組所打的名稱
                    elif mtext[:2] == '##':
                        if len(mtext[2:])>200:#判斷群組名稱有沒有超過200字
                            reply_message = '群組名稱超過200字，請重新輸入(##你的群組名稱，範例:##Group1)'
                            line_bot_api.reply_message(event.reply_token, TextMessage(text=reply_message))
                        else:
                            reply_message = CreateGroup(mtext,user_id,user_name)
                            line_bot_api.reply_message(event.reply_token, TextMessage(text=reply_message))
                    elif mtext == '加入群組':
                        reply_message='請輸入您想要加入的群組代碼(####您的群組代碼，範例:#d44f7ds2ad9)'
                        line_bot_api.reply_message(event.reply_token, TextMessage(text=reply_message))
                    elif mtext[:1] == '#':
                        reply_message = JoinGroup(mtext, user_id, user_name)
                        line_bot_api.reply_message(event.reply_token, TextMessage(text=reply_message))
        return HttpResponse()
    else:
        return HttpResponseBadRequest()
#創建群組
def CreateGroup(mtext,user_id,user_name):
    temp = mtext[2:]#取得井字號的後面
    letters = string.ascii_letters#產生英文字母
    digits = string.digits#產生字串
    # 如果有和資料庫重複會重新生成
    while True:
        secure_random_string = ''.join(secrets.choice(letters) + secrets.choice(digits) for i in range(15))#數字和英文字母串接
        if not GroupTable.objects.filter(group_code=secure_random_string).exists():
            break
    group_name = temp
    group_code = secure_random_string
    try:
        #剛創建的群組加入資料庫
        unit = GroupTable(group_name=group_name, group_code=group_code)
        unit.save()
        #判斷使用者有無在personalTable裡面，沒有在裡面然後創建群組，這樣就有一個群組，但是personalTable卻沒有紀錄這個人
        user = PersonalTable.objects.filter(personal_id=user_id)
        if not user:
            #如果沒有就要加入到個人的table
            unit2 = PersonalTable(personal_id=user_id,user_name=user_name)
            unit2.save()
        #抓取群組的id且把資料加入到linking table中
        group = GroupTable.objects.get(group_id=unit.group_id)
        user_instance = PersonalTable.objects.get(personal_id=user_id)
        try:
            unit3 = PersonalGroupLinkingTable.objects.create(personal=user_instance,group=group)
            return '成功創建群組'
        except Exception as e:
            print(f"Error creating linking table record: {e}")
    except Exception as e:
        print(f"Error creating group: {e}")
#加入群組
def JoinGroup(mtext, user_id, user_name):
    code = mtext[1:]  # 取得井字號的後面
    user = PersonalTable.objects.filter(personal_id=user_id)
    # 如果沒有就要加入到personaltable
    if not user:
        unit = PersonalTable(personal_id=user_id, user_name=user_name)
        unit.save()
    #判斷使用者輸入有無此群組
    unit2 = GroupTable.objects.filter(group_code=code)
    if not unit2:
        return '查無此群組，請重新輸入'
    else:
        # 判斷使用者是否有想要重複加入群組，去linkingtable看有沒有重複加入
        group = GroupTable.objects.get(group_code=code)
        user_instance = PersonalTable.objects.get(personal_id=user_id)
        unit4 = PersonalGroupLinkingTable.objects.filter(personal=user_instance, group=group)
        if unit4:
            return '已經有加入該群組，若是要加入新群組請重新核對您的群組代碼'
        else:
            try:
                user_instance = PersonalTable.objects.get(personal_id=user_id)
                unit5 = PersonalGroupLinkingTable.objects.create(personal=user_instance,group=group)
                return '成功加入群組'
            except Exception as e:
                print(f"Error creating linking table record: {e}")
                return '加入群組時發生錯誤，請稍後再試'
