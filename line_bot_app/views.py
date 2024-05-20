from django.shortcuts import render

# Create your views here.
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render

from urllib.parse import parse_qsl
from static import *

from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import *
from line_bot_app.models import PersonalTable
from module import func

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
                # 取得用戶名稱
                user_name = profile.display_name
                # 判斷使用者有無在personalTable裡面，沒有在裡面然後創建群組，這樣就有一個群組，但是personalTable卻沒有紀錄這個人
                user = PersonalTable.objects.filter(personal_id=user_id)
                if not user:
                    # 如果沒有就要加入到個人的table
                    unit2 = PersonalTable(personal_id=user_id, user_name=user_name)
                    unit2.save()
                if isinstance(event.message, TextMessage):
                    mtext = event.message.text
                    if mtext == '我的帳本':
                        func.MyAccount(event)
                    elif mtext[:6] == '<我的帳本>' and len(mtext) > 3:
                        func.MyAccount(event)
                    elif mtext == '建立群組':
                        func.creatgroup(event)
                    elif mtext[:6] == '<建立群組>':
                        reply_message = func.CreateGroup(mtext, user_id)
                        line_bot_api.reply_message(event.reply_token, TextMessage(text=reply_message))
                    elif mtext == '加入群組':
                        func.joingroup(event)
                    elif mtext[:6] == '<加入群組>':
                        reply_message = func.JoinGroup(mtext, user_id)
                        line_bot_api.reply_message(event.reply_token, TextMessage(text=reply_message))
        return HttpResponse()
    else:
        return HttpResponseBadRequest()
