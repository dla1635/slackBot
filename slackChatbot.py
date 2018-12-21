# -*- coding: utf-8 -*-
import json
import os
import re
import urllib.request

from datetime import date, timedelta
import calendar
from slacker import Slacker

from bs4 import BeautifulSoup
from slackclient import SlackClient
from flask import Flask, request, make_response, render_template

app = Flask(__name__)

slack_token = 'xoxb-507380538243-507385477939-SKIdvLLs9YtclJ8B9qpoilDt'
slack_client_id = '507380538243.507320181380'
slack_client_secret = 'cdb534c31a33e33ee03d8427f04f194a'
slack_verification = 'dzBBiHE1BYO2X8r79Jh9wg6N'
sc = SlackClient(slack_token)

def data_crawling(_url):
    url = _url    
    sourcecode = urllib.request.urlopen(url).read()
    return BeautifulSoup(sourcecode, "html.parser")
    
    
# 요일별 인기 Top 10 만화 
def week_toon(text):
    soup = data_crawling('https://comic.naver.com/webtoon/weekday.nhn')
    
    slack = Slacker('xoxb-507380538243-507385477939-SKIdvLLs9YtclJ8B9qpoilDt')
 
    all_toon = soup.find_all("div", class_="col")
    days = ["월", "화", "수", "목", "금", "토", "일"]

    index = ''
    for i, day in enumerate(days):
        if day in text:
            index = i

    keywords = []
    attachments = []
    toon_list = all_toon[index].find_all("li")
    for index, toon in enumerate(toon_list):
        if index < 10:
            attachments_dict = dict()
            attachments_dict['title'] = str(index+1)+"위 "+toon.get_text().replace('\n','')
            attachments_dict['image_url'] = toon.find("img")["src"]
            attachments.append(attachments_dict)
    slack.chat.post_message(channel="#general", attachments=attachments, as_user=True)
    return u'\n'.join(keywords)
# 금일 업데이트된 웹툰
def updated_toon(text):
    # Slacker에 Bot 토큰 할당
    slack = Slacker('xoxb-507380538243-507385477939-SKIdvLLs9YtclJ8B9qpoilDt')
    # 데이터 크롤링
    soup = data_crawling('https://comic.naver.com/webtoon/weekday.nhn')
    # 요일별 웹툰 리스트 가져오기
    all_toon = soup.find_all("div", class_="col")
    # 오늘, 어제 날짜 구하기
    today = date.today().strftime("%Y.%m.%d")
    yesterday = (date.today() - timedelta(1)).strftime("%Y.%m.%d")

    # 오늘 요일 구하기
    a=calendar.weekday(date.today().year, date.today().month, date.today().day)
    days=["MON","TUE","WED","THU","FRI","SAT","SUN"]

    # 오늘 요일에 해당하는 인덱스 반환
    for i, day in enumerate(days):
        if day == days[a]:
            index = i
       
    # 해당 요일 만화 리스트의 href 추출
    list_href = []
    toon_href_list = all_toon[index].find_all("a", class_="title")
    for index, toon_href in enumerate(toon_href_list):
        if index < 10:
            list_href.append("https://comic.naver.com" + toon_href.get("href"))
   
    # 각각 만화의 최신작이 있는지 판단
    attachments = []
    for href in list_href:
        soup = data_crawling(href)
        
        latest_date = soup.find('td', class_='num').get_text()
        # 금일 웹툰이 당일 또는 전날에 업데이트 된 경우 리스트에 추가한다. 
        if(latest_date == today or latest_date == yesterday):
            detail = soup.find("div", class_="comicinfo")
            titles = detail.find("h2").get_text().split()

            title = ''
            for i in range(0, len(titles)-1):
                title += titles[i] + " "

            attachments_dict = dict()
            attachments_dict['title'] = title
            attachments_dict['image_url'] = detail.find("img")["src"]
            attachments.append(attachments_dict)

    slack.chat.post_message(channel="#general", attachments=attachments, as_user=True)

    # return u'\n'.join(update_toon_list)

# 이벤트 핸들하는 함수
def _event_handler(event_type, slack_event):

    if event_type == "app_mention" and '@UEXBBE1TM' in slack_event["event"]["text"] or 'help' in text:
        
        slack = Slacker('xoxb-507380538243-507385477939-SKIdvLLs9YtclJ8B9qpoilDt')
        channel = slack_event["event"]["channel"]
        
        attachments = []
        attachments_dict = dict()
        attachments_dict['title'] = "네이버 웹툰봇입니다.\n제공 기능\n - 요일별 Top10 웹툰 리스트 keyowrd : 월-일 \n - 금일 업데이트된 웹툰 리스트 keyowrd : 업데이트"
        attachments.append(attachments_dict)
        slack.chat.post_message(channel=channel, attachments=attachments, as_user=True)


    if event_type == "app_mention":
        channel = slack_event["event"]["channel"]
        text = slack_event["event"]["text"]
        
        if "업데이트" in text:
            updated_toon(text)
            return make_response("App mention message has been sent", 200,)
        elif "월요일" or "화요일" or "수요일" or "목요일" or "금요일" or "토요일" or "일요일"  in text:
            week_toon(text)
            return make_response("App mention message has been sent", 200,)
        
        # sc.api_call(
        #     "chat.postMessage",
        #     channel=channel,
        #     text=keywords
        # )

        return make_response("App mention message has been sent", 200,)

    # ============= Event Type Not Found! ============= #
    # If the event_type does not have a handler
    message = "You have not added an event handler for the %s" % event_type
    # Return a helpful error message
    return make_response(message, 200, {"X-Slack-No-Retry": 1})

@app.route("/listening", methods=["GET", "POST"])
def hears():
    slack_event = json.loads(request.data)

    if "challenge" in slack_event:
        return make_response(slack_event["challenge"], 200, {"content_type":
                                                             "application/json"
                                                            })

    # 토큰이 일치하지 않은 경우
    if slack_verification != slack_event.get("token"):
        message = "Invalid Slack verification token: %s" % (slack_event["token"])
        make_response(message, 403, {"X-Slack-No-Retry": 1})
    
    # 이벤트 발생
    if "event" in slack_event:
        event_type = slack_event["event"]["type"]
        return _event_handler(event_type, slack_event)

    # If our bot hears things that are not events we've subscribed to,
    # send a quirky but helpful error response
    return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids\
                         you're looking for.", 404, {"X-Slack-No-Retry": 1})

@app.route("/", methods=["GET"])
def index():
    return "<h1>Server is ready.</h1>"

if __name__ == '__main__':
    app.run('localhost', port=5000)
