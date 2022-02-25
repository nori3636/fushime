import hashlib
import uuid
import datetime

DIFF_JST_FROM_UTC = 9

#　アカウントの管理を行うクラス
class account_manager:

    def __init__(self,db):
        self.db = db

    def signup(self,username:str,password:str):
        users = self.db.collection(u'users').where(u'username', u'==', username)
        docs = users.stream()
        for doc in docs:
            if doc.id :
                return None
        user_id = str(uuid.uuid4())
        doc_ref = self.db.collection(u'users').document(user_id)
        hash_pass = hashlib.sha256(password.encode("utf-8")).hexdigest()
        doc_ref.set({
            u'password': hash_pass,
            u'username': username
        })
        now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
        year = now.year
        self.db.collection(u'users').document(hash_pass).collection(u'schedules').add({
            u'subject':'元旦',
            u'year': year+1,
            u'month': 1,
            u'date': 1,
            u'importance': 2,
        })
        self.db.collection(u'users').document(hash_pass).collection(u'schedules').add({
            u'subject': 'バレンタインデー',
            u'year': year+1,
            u'month': 2,
            u'date': 14,
            u'importance': 2,
        })
        self.db.collection(u'users').document(hash_pass).collection(u'schedules').add({
            u'subject': '七夕',
            u'year': year,
            u'month': 7,
            u'date': 7,
            u'importance': 2,
        })
        self.db.collection(u'users').document(hash_pass).collection(u'schedules').add({
            u'subject': 'ハロウィン',
            u'year': year,
            u'month': 10,
            u'date': 31,
            u'importance': 2,
        })
        self.db.collection(u'users').document(hash_pass).collection(u'schedules').add({
            u'subject': 'クリスマス',
            u'year': year,
            u'month': 12,
            u'date': 25,
            u'importance': 2,
        })
        return user_id

    def login(self,username:str,password:str):
        hash_pass = hashlib.sha256(password.encode("utf-8")).hexdigest()
        users = self.db.collection(u'users').where(u'username', u'==', username).where(u'password', u'==', hash_pass)
        docs = users.stream()
        for doc in docs:
            if doc.id :
                return doc.id
        return None

    def user_name(self,user_id):
        doc_ref = self.db.collection(u'users').document(user_id)
        doc = doc_ref.get()
        if doc.exists:
            dict_doc = doc.to_dict()
            return dict_doc[u'username']
    