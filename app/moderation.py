import json, inspect, traceback, time, sys
from cnn.eval import classify_sentiment
import redlock
from database import db
from utils import *
from application import *
from models import *
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def moderate_posts():
    lock = redlock.lock("post_query", 1000)
    if lock:
        posts = Post.query.filter(int(time.time()) - Post.updated > 300, int(time.time()) - Post.created < 432000, Post.visible==True).all()
        sys.stderr.write("examining {} posts".format(len(posts)))
        redlock.unlock(lock)
    else:
        sys.stderr.write("resource-locked, continuing")
        return
    for post in posts:
        lock = redlock.lock(str(post.id), 1000)
        if lock:
            try:
                modifier = post.upvote - post.downvote
                if (modifier - post.modifier > 10):
                    post.trending="POPULAR"
                elif (modifier - post.modifier > 0):
                    post.trending="UP"
                elif (modifier - post.modifier == 0):
                    post.trending="NEUTRAL"
                else:
                    post.trending="DOWN"
                post.updated=int(time.time())
                moderate_comments(post.id)
            except Exception as e:
                traceback.print_exc()
                sys.stderr.write("resource-locked, continuing")
            try:
                lock = redlock.lock("tensorflow", 1000)
                if lock:
                    if post.sentiment=="":
                        post.sentiment = json.dumps(classify_sentiment(post.text))
                else:
                    return
            except Exception as e:
                traceback.print_exc()
                sys.stderr.write(e)
            post.updated=int(time.time())
            db.session.commit()
            redlock.unlock(lock)
        else:
            return

def moderate_comments(post_id):
    lock = redlock.lock("comment_query", 1000)
    if lock:
        comments = Comment.query.filter(Comment.post_id==post_id, int(time.time()) - Comment.updated > 300, int(time.time()) - Comment.created < 432000, Comment.visible==True).all()
        sys.stderr.write("examining {} comments".format(len(comments)))
        redlock.unlock(lock)
    else:
        sys.stderr.write("resource-locked, continuing")
        return
    for comment in comments:
        lock = redlock.lock(str(comment.id), 1000)
        if lock:
            try:
                modifier = comment.upvote - comment.downvote
                if (modifier - comment.modifier > 10):
                    comment.trending="POPULAR"
                elif (modifier - comment.modifier > 0):
                    comment.trending="UP"
                elif (modifier - comment.modifier == 0):
                    comment.trending="NEUTRAL"
                else:
                    comment.trending="DOWN"
                comment.updated=int(time.time())
            except Exception as e:
                traceback.print_exc()
                sys.stderr.write("resource-locked, continuing")
            # try:
            #     lock = redlock.lock("tensorflow", 1000)
            #     if lock:
            #         if comment.sentiment=="":
            #             comment.sentiment = json.dumps(classify_sentiment(comment.text))
            #     else:
            #         continue
            # except Exception as e:
            #     traceback.print_exc()
            #     sys.stderr.write(e)
            comment.updated=int(time.time())
            db.session.commit()
            redlock.unlock(lock)
        else:
            return