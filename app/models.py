# -*- coding: utf-8 -*-
from database import db
from sqlalchemy.dialects.postgresql import JSON, JSONB, ARRAY
from flask_jwt import JWT, jwt_required
from flask.ext.security import UserMixin, RoleMixin, SQLAlchemyUserDatastore, current_user
from flask import abort

roles_users = db.Table('roles_users',
                       db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                       db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

def redact(dictionary, ls):
    for blackout in ls:
        if blackout in dictionary.keys():
            dictionary[blackout] = None
    return dictionary

class Serialize():
    def to_dict(self, query_instance=None):
        if hasattr(self, '__table__'):
           return {c.name: str(getattr(self, c.name)) for c in self.__table__.columns}
        else:
            cols = query_instance.column_descriptions
            return { cols[i]['name'] : self[i]  for i in range(len(cols))  }

    def from_dict(self, dict):
        for c in self.__table__.columns:
            setattr(self, c.name, dict[c.name])

    @classmethod
    def public_list(cls):
        ls = []
        if 'public_blacklist' in dir(cls):
            ls = [u.key for u in cls.__table__.columns if u.key not in cls.public_blacklist()]
        return ls

    @classmethod
    def user_list(cls):
        ls = []
        if 'user_blacklist' in dir(cls):
            ls = [u.key for u in cls.__table__.columns if u.key not in cls.user_blacklist()]
        return ls

    @classmethod
    def private_list(cls):
        ls = []
        if 'private_blacklist' in dir(cls):
            ls = [u.key for u in cls.__table__.columns if u.key not in cls.private_blacklist()]
        return ls

    def __hash__(self):
        return (self.id).__hash__()


class User(db.Model, UserMixin, Serialize):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))
    last_login_at = db.Column(db.DateTime())
    current_login_at = db.Column(db.DateTime())
    last_login_ip = db.Column(db.String(255))
    current_login_ip = db.Column(db.String(255))
    login_count = db.Column(db.Integer)
    phone = db.Column(db.String(12), unique=True)
    visible = db.Column(db.Boolean())
    created = db.Column(db.Integer())
    token = db.Column(db.String(40))
    toponym=db.Column(db.String(200))
    posts_moderated = db.Column(db.TEXT)
    comments_moderated = db.Column(db.TEXT)

    @classmethod
    def user_blacklist(cls):
        return ['password',
                'confirmed_at',
                'last_login_at',
                'last_login_ip',
                'current_login_ip',
                'login_count',
                'visible',
                'created',
                'token']

    def __repr__(self):
        return '<models.User[email=%s]>' % self.email

    @classmethod
    def public_blacklist(cls):
        return ['password', 'confirmed_at', 'last_login_ip',
                'current_login_ip', 'login_count',
                'visible', 'created', 'token']

    @classmethod
    def private_blacklist(cls):
        return ['password']

    @classmethod
    def edit_blacklist(cls):
        return ['roles',
                'password',
                'confirmed_at',
                'last_login_at',
                'last_login_ip',
                'current_login_ip',
                'login_count',
                'visible',
                'created',
                'token']

    @staticmethod
    def preGET(instance_id=None, **kw):
        pass

    @staticmethod
    def postGET(result=None, **kw):
        if result and result.get('id'):
            if 'id' not in vars(current_user).keys():
                result = redact(result, User.public_blacklist())
            else:
                if result.get('id')==current_user.id:
                    result = redact(result, User.private_blacklist())
                else:
                    result = redact(result, User.user_blacklist())

    @staticmethod
    def prePOST(data=None, **kw):
        pass

    @staticmethod
    def postPOST(result=None, **kw):
        result = redact(result, User.private_blacklist())

    @staticmethod
    def prePATCH(instance_id=None, data=None, **kw):
        if 'id' in vars(current_user).keys() and current_user.id == instance_id:
            return
        abort(401)


class Role(db.Model, RoleMixin, Serialize):
    __tablename__ = 'role'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    @classmethod
    def public_blacklist(cls):
        return []

    @classmethod
    def private_blacklist(cls):
        return []

user_datastore = SQLAlchemyUserDatastore(db, User, Role)

class SubjectTag(db.Model, Serialize):
    __tablename__ = 'tag'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.TEXT)
    count = db.Column(db.Integer)
    sentiment = db.Column(db.TEXT)
    trending = db.Column(db.TEXT)
    created = db.Column(db.Integer)
    updated = db.Column(db.Integer)
    comment = db.Column(db.Boolean())

#TODO: custom API
class Comment(db.Model, Serialize):
    __tablename__ = 'comment'
    id = db.Column(db.Integer, primary_key=True)
    user_id =  db.Column(db.Integer)
    post_id = db.Column(db.Integer)
    parent = db.Column(db.Integer)
    children=db.Column(db.TEXT)
    visible = db.Column(db.Boolean())
    text = db.Column(db.TEXT)
    tag = db.Column(db.TEXT)
    upvote = db.Column(db.Integer)
    downvote = db.Column(db.Integer)
    modifier = db.Column(db.Integer)
    toponym=db.Column(db.String(200))
    created = db.Column(db.Integer)
    updated = db.Column(db.Integer)

#TODO: custom API
class Post(db.Model, Serialize):
    __tablename__ = 'post'
    id = db.Column(db.Integer, primary_key=True)
    user_id =  db.Column(db.Integer)
    upvote = db.Column(db.Integer)
    downvote = db.Column(db.Integer)
    sentiment = db.Column(db.TEXT)
    modifier = db.Column(db.Integer)
    title = db.Column(db.String(140))
    link = db.Column(db.String(2000))
    text = db.Column(db.TEXT)
    tags = db.Column(db.TEXT)
    toponym=db.Column(db.String(200))
    created = db.Column(db.Integer)
    updated = db.Column(db.Integer)
    visible = db.Column(db.Boolean())

