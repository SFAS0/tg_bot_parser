from flask_apscheduler import APScheduler
from flask import Flask
from datetime import datetime, timedelta
from data import db_session
from config_my import token_vk, TOKEN, chat_id, name_group
from data.posts import Posts
import requests


app = Flask(__name__)


class Config:
    SCHEDULER_API_ENABLED = True


scheduler = APScheduler()


@scheduler.task("interval", id="check_new_post", seconds=1800, misfire_grace_time=1800)
def last_post_in_db():
    posts = [[post.id, post.post_id, post.views_count, post.id_group] for post in db.query(Posts).all()]
    for group in name_group.keys():
        response = requests.get('https://api.vk.com/method/wall.get', params={'access_token': token_vk,
                                                                          'v': 5.91, 'domain': group,
                                                                          'count': 1})
        data = response.json()
        post_id = data['response']['items'][0]['id']
        views_count = data['response']['items'][0]['views']['count']
        id_group = group
        fl = True
        fl_old_post = False
        for post in posts:
            if post_id in post:
                fl = False
            if id_group in post:
                fl_old_post = True
        if fl:
            if fl_old_post:
                # Удаление старого последнего поста
                print('delete')
                db.query(Posts).filter(Posts.id_group == id_group).delete(synchronize_session='fetch')
            # добавляем новый пост в бд (последний из группы)
            posts_class = Posts()
            posts_class.post_id = post_id
            posts_class.views_count = views_count
            posts_class.id_group = id_group
            db.add(posts_class)
            db.commit()
            print('add post')
            text = data['response']['items'][0]['text'][:30]
            send_message(chat_id, f'{name_group[id_group]}: \n {text}')
        else:
            pass


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
    if int(datetime.now().time().hour) == 10 and int(datetime.now().time().minute) == 00:
        last_weeks_posts = {}
        date_week_later = (datetime.today() - timedelta(days=7)).strftime('%Y %m %d')
        for group in name_group.keys():
            response = requests.get('https://api.vk.com/method/wall.get', params={'access_token': token_vk,
                                                                                  'v': 5.91, 'domain': group,
                                                                                  'count': 100})
            data = response.json()
            for post in data['response']['items']:
                date = datetime.utcfromtimestamp(int(post['date'])).strftime('%Y %m %d')
                if date > date_week_later:
                    views_count = post['views']['count']
                    if name_group[group] in last_weeks_posts.keys():
                        last_weeks_posts[name_group[group]].append(views_count)
                    else:
                        last_weeks_posts[name_group[group]] = [views_count]
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
    db_session.global_init('db/bot_db.sqlite')
    db = db_session.create_session()
    last_post_in_db()
    app.config.from_object(Config())
    scheduler.init_app(app)
    scheduler.start()
    app.run(port=5000)
