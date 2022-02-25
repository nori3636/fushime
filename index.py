from flask import Flask, request, redirect, url_for, render_template, flash
from flask_login import login_user, logout_user, LoginManager, UserMixin, login_required, current_user
from numpy import array

from functions.schedule_manager import schedule_manager
from functions.account_manager import account_manager

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

import datetime
import os, re, json
import calendar

DIFF_JST_FROM_UTC = 9

app = Flask(__name__,static_folder='./templates/images')

app.secret_key = os.urandom(24)

# # ログイン機能のセットアップ
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login" # ログインしてない時に飛ばされる場所

#firebaseの設定を読み込む
cred = credentials.Certificate('fushime-9ccc3-firebase-adminsdk-9vqsu-a9d6643f4e.json')
if not firebase_admin._apps:
    # api_key =json.loads(os.getenv('firestore_apikey'))
    # cred = credentials.Certificate(api_key)
    firebase_admin.initialize_app(cred)
    
db = firestore.client()
account = account_manager(db)

# むっくんの関数
def train_type(nyuuryoku:str):
    syubetu={"特急":1,"快速":2,"普通":3}
    if nyuuryoku in syubetu:
        okurisyubetu=syubetu[nyuuryoku]
        return int(okurisyubetu)    
    else:
        return False

def week_name(input:str):
    ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    ['月曜日', '火曜日', '水曜日', '木曜日', '金曜日', '土曜日', '日曜日']
    transrate={"Monday":'月曜日',"Tuesday":'火曜日',"Wednesday":'水曜日','Thursday':'木曜日','Friday':'金曜日','Saturday':'土曜日','Sunday':'日曜日'}
    if input in transrate:
        nihongo=transrate[input]
        return str(nihongo)    
    else:
        return False

def is_matched(s):
    return True if re.fullmatch('(?i:\A[a-z\d]{8,100}\Z)', s) else False


#ユーザークラスを定義
class  User(UserMixin):
    def __init__(self,uid):
        self.name = account.user_name(uid)
        self.id = uid
       
@login_manager.user_loader
def user_loader(uid):
    return User(uid)


@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET': 
        return render_template('login.html')
    check_name = str(request.form['name'])
    password = str(request.form['password'])
    if check_name == '':
        flash('ユーザー名が空欄です')
        return render_template('login.html')
    if check_name == '':
        flash('パスワードが空欄です')
        return render_template('login.html')
    uid= account.login(check_name,password)
    print(uid)
    if uid != None:
        user = User(uid)
        login_user(user)
        schedule = schedule_manager(current_user.id,db)
        now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        year = now.year
        schedule.add('元旦',year+1,1,1,3)
        schedule.add('バレンタインデー',year+1,2,14,3)
        schedule.add('七夕',year,7,7,3)
        schedule.add('ハロウィン',year,10,31,3)
        schedule.add('クリスマス',year,12,25,3)
        return redirect(url_for("calendar_page"))
    else:
        flash('パスワードかユーザー名が違います')
        return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    add_name = str(request.form['name'])
    password = str(request.form['password'])
    if add_name == '':
        flash('ユーザー名が空欄です')
        return render_template('signup.html')
    if not is_matched(password):
        flash('パスワードは半角英数字8文字以上です')
        return render_template('signup.html')
    uid = account.signup(add_name,password)
    if uid != None:
        user = User(uid)
        login_user(user)
        return redirect(url_for("calendar_page"))
    else:
        flash('すでに登録済みのユーザーです')
        return render_template('signup.html')


@app.route('/calendar_page')
@login_required
def calendar_page():
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
    weekday = week_name(calendar.day_name[now.weekday()])
    month = now.month
    day = now.day
    schedule = schedule_manager(current_user.id,db)
    schedules= schedule.get_up_to_nth(5)
    schedule1= schedules[0]
    schedule2= schedules[1]
    schedule3= schedules[2]
    schedule4= schedules[3]
    schedule5= schedules[4]
    date_array = []
    diff = []
    for i in range(5):
        date_array.append(datetime.datetime(schedules[i]['year'],schedules[i]['month'],schedules[i]['date']))
        diff.append((date_array[0]-now).days)
    schedule1['diff'] = (date_array[0] - now).days
    schedule2['diff'] = (date_array[1] - now).days
    schedule3['diff'] = (date_array[2] - now).days
    schedule4['diff'] = (date_array[3] - now).days
    schedule5['diff'] = (date_array[4] - now).days  
    
    return render_template('calender.html',user_name = current_user.name,
    schedule1=schedule1,schedule2=schedule2,schedule3=schedule3,
    schedule4=schedule4,schedule5=schedule5,
    tuki=month,hi=day,youbi= weekday
    )


@app.route('/regist', methods=['GET', 'POST'])
@login_required
def regist():
    if request.method == 'GET':
        return render_template('regist.html')
    subject = str(request.form['subject'])
    date = str(request.form['date'])
    importance = str(request.form['importance'])
    if subject == '':
        flash('予定名が入力されてません','error')
        return render_template('regist.html')
    if date == '':
        flash('予定日が入力されてません','error')
        return render_template('regist.html')
    # 日付を変数に格納
    dt = datetime.datetime.strptime(date, '%Y-%m-%d')
    year = dt.year
    month = dt.month
    day = dt.day
    level = train_type(importance)
    if not level:
        flash('重要度が不正です','error')
        return render_template('regist.html')
    schedule = schedule_manager(current_user.id,db)
    schedule.add(subject,year,month,day,level)
    return render_template('regist.html',succes ='予定の登録が完了しました' )


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for("login"))


# run the app.
if __name__ == "__main__":
    app.debug = True
    app.run(port=5000)