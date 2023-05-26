from vk_api.longpoll import VkLongPoll, VkEventType
from flask_apscheduler import APScheduler
from flask import Flask
from datetime import datetime, timedelta
from config import token_vk, TOKEN, chat_id, name_group
import requests
import vk_api
import threading


app = Flask(__name__)


def check_messege_group(token_vk_group, name_group_mess):
    vk = vk_api.VkApi(token=token_vk_group)
    longpoll = VkLongPoll(vk)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            if event.to_me:
                # Сообщение от пользователя
                request = event.text
                send_message(chat_id, f'В группу {name_group_mess} пришло сообщение: {request}')
                print(request)


class Config:
    SCHEDULER_API_ENABLED = True


scheduler = APScheduler()


def send_message(chat_id, text):
    method = "sendMessage"
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    data = {"chat_id": chat_id, "text": text}
    requests.post(url, data=data)


@app.route("/", methods=["GET", "POST"])
def receive_update():
    return {"ok": True}


@scheduler.task("interval", id="daily_report", seconds=30, misfire_grace_time=30)
def send_daily_report():
    proxies = {
        'https': 'socks5://198.50.217.202:1080'
    }
    if int(datetime.now().time().hour) == 10 and int(datetime.now().time().minute) == 00:
        last_weeks_posts = {}
        date_week_later = (datetime.today() - timedelta(days=7)).strftime('%Y %m %d')
        for group in name_group.keys():
            response = requests.get('https://api.vk.com/method/wall.get', params={'access_token': token_vk,
                                                                                  'v': 5.91, 'domain': group,
                                                                                  'count': 100}, proxies=proxies)
            data = response.json()
            for post in data['response']['items']:
                date = datetime.utcfromtimestamp(int(post['date'])).strftime('%Y %m %d')
                if date > date_week_later:
                    views_count = post['views']['count']
                    if name_group[group][0] in last_weeks_posts.keys():
                        last_weeks_posts[name_group[group][0]].append(views_count)
                    else:
                        last_weeks_posts[name_group[group][0]] = [views_count]
        answer = ''
        sum_all_posts_views = []
        for group_name, list_views_count in last_weeks_posts.items():
            answer += f'Группа: {group_name} Средние просмотры за неделю:' \
                      f' {sum(list_views_count) // len(list_views_count)}\n'
            for i in list_views_count:
                sum_all_posts_views.append(i)
        answer += f'Средние просмотры за неделю всех групп: {sum(sum_all_posts_views) // len(sum_all_posts_views)}'
        send_message(chat_id, answer)
    else:
        pass


if __name__ == '__main__':
    for id, (name, token) in name_group.items():
        group_check = threading.Thread(target=check_messege_group, args=(token, name))
        group_check.start()
    app.config.from_object(Config())
    scheduler.init_app(app)
    scheduler.start()
    app.run(port=5000)
