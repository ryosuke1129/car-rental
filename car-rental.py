import os
import json
import requests
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime

# Tokens
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
KANASUGI = os.getenv('KANASUGI')
MATSUSHIMA = os.getenv('MATSUSHIMA')

# DynamoDB initialize
table = boto3.resource('dynamodb').Table('car-rental')

# LINE Messaging API config
reply_url = 'https://api.line.me/v2/bot/message/reply'
push_url = 'https://api.line.me/v2/bot/message/push'
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'
}

# DB function
def db_newest(userId):
    queryData = table.query(
        KeyConditionExpression = Key('user_id').eq(userId),
        ScanIndexForward = False,
        Limit = 1
    )
    items = {}
    for key, value in queryData['Items'][0].items():
        items[key] = str(value)
    items['timestamp'] = int(items['timestamp'])
    return items

# LINE Messaging API functions
def rental_date(replyToken):
    data = {
        'replyToken': replyToken,
        'messages': [
            {
                "type": "template",
                "altText": "車の利用予約（日付選択）",
                "template": {
                    "type": "buttons",
                    "title": "車の利用予約",
                    "text": "車を利用したい日を選択してください",
                    "actions": [
                        {
                            "type": "message",
                            "label": "今日",
                            "text": "今日"
                        },
                        {
                            "type": "message",
                            "label": "明日",
                            "text": "明日"
                        },
                        {
                            "type": "datetimepicker",
                            "label": "日時を選択する",
                            "data": "rental-date",
                            "mode": "datetime"
                        }
                    ]
                }
            }
        ]
    }
    res = requests.post(reply_url, headers=headers, data=json.dumps(data))
    print(res.status_code)

def rental_time(userId, replyToken, created, r_date):
    table.put_item(
        Item={
            'user_id': userId,
            'timestamp': created,
            'rental_date': r_date
        }
    )
    data = {
        'replyToken': replyToken,
        'messages': [
            {
                "type": "template",
                "altText": "車の利用予約（時間帯選択）",
                "template": {
                    "type": "buttons",
                    "title": "車の利用予約",
                    "text": "車の利用を開始したい時間帯を選択してください",
                    "actions": [
                        {
                            "type": "message",
                            "label": "午前から",
                            "text": "午前から"
                        },
                        {
                            "type": "message",
                            "label": "昼から",
                            "text": "昼から"
                        },
                        {
                            "type": "message",
                            "label": "夕方から",
                            "text": "夕方から"
                        },
                        {
                            "type": "message",
                            "label": "夜から",
                            "text": "夜から"
                        }
                    ]
                }
            }
        ]
    }
    res = requests.post(reply_url, headers=headers, data=json.dumps(data))
    print(res.status_code)

def return_car(replyToken, r_time):
    items = db_newest(KANASUGI)
    items['rental_time'] = r_time
    table.put_item(Item=items)
    data = {
        'replyToken': replyToken,
        'messages': [
            {
                "type": "template",
                "altText": "車の利用予約（返却予定選択）",
                "template": {
                    "type": "buttons",
                    "title": "車の利用予約",
                    "text": "車の返却予定日時を選択してください",
                    "actions": [
                        {
                            "type": "message",
                            "label": "3時間以内",
                            "text": "3時間以内"
                        },
                        {
                            "type": "message",
                            "label": "当日中",
                            "text": "当日中"
                        },
                        {
                            "type": "message",
                            "label": "翌日",
                            "text": "翌日"
                        },
                        {
                            "type": "datetimepicker",
                            "label": "日時を選択する",
                            "data": "releaseß-date",
                            "mode": "datetime"
                        }
                    ]
                }
            }
        ]
    }
    res = requests.post(reply_url, headers=headers, data=json.dumps(data))
    print(res.status_code)

def confirmation(replyToken, return_car):
    items = db_newest(KANASUGI)
    items['return'] = return_car
    table.put_item(Item=items)
    data = {
        'replyToken': replyToken,
        'messages': [
            {
                "type": "template",
                "altText": "車の利用予約（申請内容確認）",
                "template": {
                    "type": "confirm",
                    "text": f"以下の内容で申請しますか？\n\n開始：{items['rental_date']}の{items['rental_time']}\n返却：{items['return']}",
                    "actions": [
                        {
                            "type": "message",
                            "label": "はい",
                            "text": "はい"
                        },
                        {
                            "type": "message",
                            "label": "いいえ",
                            "text": "いいえ"
                        }
                    ]
                }
            }
        ]
    }
    res = requests.post(reply_url, headers=headers, data=json.dumps(data))
    print(res.status_code)

def send_wf(replyToken):
    items = db_newest(KANASUGI)
    data = {
        'to': MATSUSHIMA,
        'messages': [
            {
                "type": "template",
                "altText": "車の利用申請がありました",
                "template": {
                    "type": "confirm",
                    "text": f"車の利用申請を承認しますか？\n\n開始：{items['rental_date']}の{items['rental_time']}\n返却：{items['return']}",
                    "actions": [
                        {
                            "type": "message",
                            "label": "はい",
                            "text": "はい"
                        },
                        {
                            "type": "message",
                            "label": "いいえ",
                            "text": "いいえ"
                        }
                    ]
                }
            }
        ]
    }
    res = requests.post(push_url, headers=headers, data=json.dumps(data))
    print(res.status_code)
    data = {
        'replyToken': replyToken,
        'messages': [
            {
                "type": "text",
                "text": "松嶋に申請を送信しました。",
            }
        ]
    }
    res = requests.post(reply_url, headers=headers, data=json.dumps(data))
    print(res.status_code)

def reply_message(replyToken, text):
    data = {
        'replyToken': replyToken,
        'messages': [
            {
                "type": "text",
                "text": text,
            }
        ]
    }
    res = requests.post(reply_url, headers=headers, data=json.dumps(data))
    print(res.status_code)

def send_message(userId, text):
    data = {
        'to': userId,
        'messages': [
            {
                "type": "text",
                "text": text,
            }
        ]
    }
    res = requests.post(push_url, headers=headers, data=json.dumps(data))
    print(res.status_code)

# Main
def lambda_handler(event, context):
    event = json.loads(event['body'])['events'][0]
    userId = event['source']['userId']
    replyToken = event['replyToken']
    if 'message' in event:
        text = event['message']['text']
    elif 'postback' in event:
        text = datetime.strptime(event['postback']['params']['date'], '%Y-%m-%d')
    print(userId, text)

    if userId == KANASUGI:
        try:
            if text == '予約':
                rental_date(replyToken)
            elif text in ['今日', '明日']:
                timestamp = event['timestamp']
                rental_time(userId, replyToken, timestamp, text)
            elif type(text) is datetime:
                text = text.strftime('%Y-%m-%d')
                timestamp = event['timestamp']
                rental_time(userId, replyToken, timestamp, text)
            elif text in ['午前から', '昼から', '夕方から', '夜から']:
                return_car(replyToken, text)
            elif text in ['3時間以内', '当日中', '翌日']:
                confirmation(replyToken, text)
            elif text == 'はい':
                send_wf(replyToken)
            elif text == 'いいえ':
                reply_message(replyToken, text='最初からやり直してください。')
        except Exception as e:
            reply_message(replyToken, text='エラーが発生しました。')
            print(userId, f'{e.__class__.__name__}: {e}')

    elif userId == MATSUSHIMA:
        try:
            if text == 'はい':
                items = db_newest(KANASUGI)
                items['approval'] = True
                table.put_item(Item=items)
                send_message(userId=KANASUGI, text='申請が承認されました。')
                reply_message(replyToken, text='金杉に承認メッセージを送信しました。')
            elif text == 'いいえ':
                items = db_newest(KANASUGI)
                items['approval'] = False
                table.put_item(Item=items)
                send_message(userId=KANASUGI, text='申請が否決されました。')
                reply_message(replyToken, text='金杉に否決メッセージを泣く泣く送信しました。')
            else:
                reply_message(replyToken, text='黙っとけ！！')
        except Exception as e:
            reply_message(replyToken, text='エラーが発生しました。')
            print(userId, f'{e.__class__.__name__}: {e}')