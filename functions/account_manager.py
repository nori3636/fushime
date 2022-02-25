import hashlib
import uuid

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
    