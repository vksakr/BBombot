
import json
import os
import re
import urllib.request

from bs4 import BeautifulSoup
from slackclient import SlackClient
from flask import Flask, request, make_response, render_template
from slacker import Slacker

from datetime import datetime,timedelta



app = Flask(__name__)

#슬랙 api 키
# slack_token = "xoxp-506274278966-504714157377-506748857248-7a4d53319e9f9bf72899913f121ae80c"
# slack_client_id = "506274278966.507684340901"
# slack_client_secret = "92f9b34c479a79874eaf239822f505bf"
# slack_verification = "iYx1Pxkdm3uebtqXWEUVwevM"
# sc = SlackClient(slack_token)
# slack = Slacker('xoxp-506274278966-504714157377-506748857248-7a4d53319e9f9bf72899913f121ae80c')


outfix=[]
wordlist = ['기타','컴퓨터','디지털','먹을거리','서적','가전','육아','카메라','의류/잡화','화장품','등산/캠핑','핫딜','최신']

# 크롤링 함수
def crowling(text):
    put = text
    # URL 데이터를 가져올 사이트 url 입력
    url = "http://www.ppomppu.co.kr/zboard/zboard.php?id=ppomppu"
        
    # URL 주소에 있는 HTML 코드를 soup에 저장합니다.
    src = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(src, "html.parser")
    
    outfix.clear()
    list = []
    li0 = []
    li1 = []

    for tr_text in soup.find_all("tr", class_="list0"):
        li0.append(tr_text)

    for tr_text in soup.find_all("tr", class_="list1"):
        li1.append(tr_text)

    len0 = len(li0)
    len1 = len(li1)
    length = max([len(li0),len(li1)])

    for i in range(0,length):
        if(len(li1) != 0) : 
            list.append(li1.pop(0))
        if(len(li0) != 0) : 
            list.append(li0.pop(0))



    for i in range(0, len(list)):
        # slack.chat.post_message('#general', text= list[1].get_text())

        tmp = {}
        envspace_list = list[i].find_all("td", class_ = "eng list_vspace")

        tmp["num"] = int(envspace_list[0].get_text().strip())

        tmp["sort"] = list[i].find_all("nobr", class_ = "han4 list_vspace")[0].get_text()

        # tmp["name"] = list[i].find_all("span", class_ = "list_name")[0].get_text()

        try:
            txt = list[i].find_all("font", class_ = "list_title")[0].get_text()
            rev = txt[::-1]
            start = len(txt) - rev.find('(')
            end = len(txt) - rev.find(')') - 1

            context = list[i].find_all("font", class_ = "list_title")[0].get_text().replace("("," (").split()

            tmp["shop"] = txt[txt.find('[') + 1:txt.find(']')]

            pns = txt[start:end].split("/")
            # print(txt[start:end])

            tmp["ship"] = "Null"
            try:
                tmp["price"] = int(pns[0].replace(',','').replace('원',''))
                if(len(pns) > 1) : tmp["ship"] = pns[1]
            except:
                tmp["price"] = 0
                tmp["ship"] = "Null"

            tmp["title"] = list[i].find_all("font", class_ = "list_title")[0].get_text().replace('[' + tmp["shop"] + ']','')
        except :
            continue
            tmp["title"] = "종료된 상품"
            tmp["shop"] = ""
            tmp["price"] = 0
            tmp["ship"] = ""


        tmp["date"] = envspace_list[1].get_text()

        ratinglist = envspace_list[2].get_text().split('-')
        if (len(ratinglist) > 1) :
            tmp["rating"] = int(int(ratinglist[0]) - int(ratinglist[1]))
        else :
            tmp["rating"] = 0

        tmp["view"] = int(envspace_list[3].get_text())
        tmp["link"] = 'http://www.ppomppu.co.kr/zboard/' + list[i].find_all("a")[1]['href']

        # for k, v in tmp.items():
        #     slack.chat.post_message('#general', text= '{0} : {1}'.format(k,v))
        
        print(put)
        if tmp['sort'] in put:
            outrow = {
                "title": tmp['title'],
                'title_link' : tmp['link'],
            }
            outfix.append(outrow)
        elif put=='최신':
            outrow = {
                "title": tmp['title'],
                'title_link' : tmp['link'],
                "text": tmp['sort'],
            }
            outfix.append(outrow)


    return 0

#인기글 크롤러
def hotClick() :
    url = "http://www.ppomppu.co.kr/hot.php?id=ppomppu"

    src = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(src, "html.parser")

    outfix.clear()

    for tr_text in soup.find_all("tr", class_="line"):
        tmp = {}
        tit = tr_text.find_all("a")[1].get_text()
        li = tr_text.find_all("a")[1]['href']
        tmp['title'] = tit
        tmp['link'] = 'http://www.ppomppu.co.kr'+li
        outrow = {
                "title": tmp['title'],
                'title_link' : tmp['link'],
            }
        outfix.append(outrow)



def _out_price(text):
    if(text == '핫딜'):
        hotClick()
        if(outfix == []):
            return 0
        return outfix
    else:
        crowling(text)
        if(outfix == []):
            return 0
        return outfix
    
    return None

    

# 이벤트 핸들하는 함수
def _event_handler(event_type, slack_event):
    print(slack_event["event"])

    if event_type == "app_mention":
        channel = slack_event["event"]["channel"]
        text = slack_event["event"]["text"]

        put_msg = [
            {
                "color": "#36a64f",
                "pretext": "다음 키워드로 호출해 주세요!",
                "fields": [
                    {
                        "title": "카테고리 종류",
                        "value": "기타 컴퓨터 디지털 먹을거리 서적 ",
                    },
                    {
                        "value": "가전 육아 카메라 의류/잡화 화장품 등산/캠핑",
                    }
                ],
                "title": "핫딜 최신",
                "text": "ex) @hoju_bot 핫딜",
                "footer": "출처: 뽐뿌",
                "ts": 123456789
            }
        ]
        if text[-1:] == '>' :
            sc.api_call(
                "chat.postMessage",
                channel=channel,
                attachments=put_msg
            )
            return make_response("App mention message has been sent", 200,)
        else :
            stext = text.split(' ')[1]
            if stext in wordlist:
                # _out_price(stext)
                keywords = _out_price(stext)
                if keywords == 0:
                    sc.api_call(
                    "chat.postMessage",
                    channel=channel,
                    text='죄송합니다 찾는 정보가 없습니다 ㅜㅜ'
                )
                sc.api_call(
                    "chat.postMessage",
                    channel=channel,
                    attachments=keywords
                )
                return make_response("App mention message has been sent", 200,)


        return make_response("App mention message has been sent", 200,)

    # ============= Event Type Not Found! ============= #
    # If the event_type does not have a handler
    message = "You have not added an event handler for the %s" % event_type
    # Return a helpful error message
    return make_response(message, 200, {"X-Slack-No-Retry": 1})

#슬랙 봇이 여는 페이지
@app.route("/listening", methods=["GET", "POST"])
def hears():
    slack_event = json.loads(request.data)


    if "challenge" in slack_event:
        return make_response(slack_event["challenge"], 200, {"content_type":
                                                             "application/json"
                                                            })

    if slack_verification != slack_event.get("token"):
        message = "Invalid Slack verification token: %s" % (slack_event["token"])
        make_response(message, 403, {"X-Slack-No-Retry": 1})
    
    if "event" in slack_event:
        event_type = slack_event["event"]["type"]
        return _event_handler(event_type, slack_event)

    if slack_event['event_time'] < (datetime.now() - timedelta(seconds=1)).timestamp():
        return make_response("this message is before sent.", 200, {"X-Slack-No-Retry": 1})        

    # If our bot hears things that are not events we've subscribed to,
    # send a quirky but helpful error response
    return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids\
                         you're looking for.", 404, {"X-Slack-No-Retry": 1})

#메인 페이지, 기능 X
@app.route("/", methods=["GET"])
def index():
    return "<h1>Server is ready.</h1>"

if __name__ == '__main__':
    # app.run('0.0.0.0', port=8080)
    app.run(debug=True)