import json, inspect, traceback, time, sys
from flask import render_template, request, redirect, make_response
from flask.ext.security import Security, logout_user, login_required, current_user
from flask.ext.security.utils import encrypt_password, verify_password
from flask.ext.restless import APIManager
from flask_jwt import JWT, jwt_required
from sqlalchemy.dialects.postgresql import Any
from celery import Celery
from flask_recaptcha import ReCaptcha
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging

from application import *
from database import db
from moderation import *
from utils import *
import models
from models import *
from admin import init_admin
from functools import wraps

security = None
jwt = None
apimanager = None

# Views  ======================================================================
@app.route('/')
def home():
	return render_template('index.html')

@app.route('/logout')
def log_out():
	logout_user()
	return redirect(request.args.get('next') or '/')

@app.route("/captcha", methods=["POST"])
def submit():
	if recaptcha.verify():
		return make_response(200)
	else:
		# FAILED
		return make_response(500)

@app.route('/tag/<string:tags>', methods=['GET'])
def get_posts(tags):
	page = request.args.get('page', type=int, default=1)
	tag_list = tags.split('+')
	tag_list.sort()
	posts = []
	for tag in tag_list:
		subject_tag = SubjectTag.query.filter(SubjectTag.name==tag).first()
		tag_posts = Post.query.filter(Post.tags.contains(str(subject_tag.id)), Post.visible==True).order_by(Post.modifier).paginate(page, 50, False)
		for psts in tag_posts.items:
			psts.user = db.session.query(User).get(psts.user_id)
		posts.extend(tag_posts.items)
	posts = uniquify(posts)
	posts.sort(key=lambda x: x.modifier, reverse=True)
	return make_response(json.dumps([post.to_dict() for post in posts]), 200)

@app.route('/tag/<string:tags>', methods=['POST'])
def post_post(tags):
	page = request.args.get('page', type=int, default=1)
	tag_list = tags.split('+')
	tag_list.append("all")
	tag_list.sort()
	print(tag_list)
	content =  request.get_json(silent=True, force=True)
	insert = {}
	insert['created'] = int(time.time())
	insert["updated"] = int(time.time())
	insert['upvote'] = 1
	insert['downvote'] = 0
	insert['sentiment'] = ''
	insert['modifier'] = 1
	insert['visible'] = True
	insert['user_id'] = current_user.id
	insert['title'] = content['title']
	if 'link' in content:
		insert['link'] = content['link']
	if 'text' in content:
		insert['text'] = content['text']
	tag_ids = []
	user = User.query.get(current_user.id)
	user.current_login_ip=request.remote_addr;
		#geo_ip = toponum_fuzzer(get_toponym(user.current_login_ip))
	if "toponym" in content and content["toponym"] and content["toponym"] != "unknown":
		user.toponym = json.dumps(get_city(content["toponym"]))
	else:
		geo_ip = get_toponym(user.current_login_ip)
		user.toponym = json.dumps(geo_ip)
	insert["toponym"] = user.toponym
	for tag in tag_list:
		print(tag)
		subject_tag = SubjectTag.query.filter(SubjectTag.name==tag).first()
		if not subject_tag:
			tag = SubjectTag(name=tag, description='blah', count=1, sentiment="NEUTRAL", trending="NEUTRAL", created=int(time.time()), updated=int(time.time()))
			db.session.add(tag)
			db.session.flush()
			tag_ids.append(tag.id)
		else:
			tag_ids.append(subject_tag.id)
			subject_tag.count = subject_tag.count + 1
			subject_tag.updated = int(time.time())
	insert['tags'] = json.dumps(tag_ids)
	post = Post(**insert)
	db.session.add(post)
	db.session.commit()
	return make_response(json.dumps({'link':'/post/{}'.format(post.id)}), 200)

@app.route('/post/<int:id>', methods=['GET'])
def get_comments(id):
	page = request.args.get('page', type=int, default=1)
	comments = Comment.query.filter(Comment.post_id==id).paginate(page, 50, False)
	cmts = [{"id":comment.id, "node":comment.to_dict(), "parent":comment.parent, "children":json.loads(comment.children)} for comment in comments.items]
	nodes = dict((c["id"], c) for c in cmts)
	for c in cmts:
		if "parent" in c and c["parent"] != 0 and c["parent"] != None:
			nodes[c["parent"]]["children"] = []
	for c in cmts:
		if "parent" in c and c["parent"] != 0 and c["parent"] != None:
			nodes[c["parent"]]["children"].append(nodes[c["id"]])
	parents = [n for n in nodes.values() if n["parent"] == 0 and c["parent"] != None]
	return make_response(json.dumps([parents][0]), 200)

@app.route('/post/<int:id>/moderate', methods=['POST'])
def post_moderate(id):
	content =  request.get_json(silent=True, force=True)
	moderate = content["moderate"]
	post = Post.query.get(id)
	post_id = str(id)
	user = User.query.get(current_user.id)
	already_moderated={}
	if user.posts_moderated:
		already_moderated=json.loads(user.posts_moderated)
	else:
		user.posts_moderated=json.dumps({})
	if "upvote" in moderate and "downvote" not in moderate:
		if already_moderated!={} and post_id in already_moderated and "downvote" not in already_moderated[post_id]["action"]:
			return make_response("no", 400)
		post.upvote = post.upvote + 1
		already_moderated[post_id]={"action":"upvote"}
		user.posts_moderated=json.dumps(already_moderated)
	elif "upvote" not in moderate and "downvote" in moderate:
		if already_moderated!={} and post_id in already_moderated and "upvote" not in already_moderated[post_id]["action"]:
			return make_response("no", 400)
		post.downvote = post.downvote + 1
		already_moderated[post_id]={"action":"downvote"}
		user.posts_moderated=json.dumps(already_moderated)
	post.modifier = post.upvote - post.downvote
	db.session.commit()
	return make_response(json.dumps(already_moderated), 200)

@app.route('/comment/<int:id>', methods=['GET'])
def get_comment(id):
	comment = Comment.query.get(id)
	return make_response(json.dumps(comment.to_dict()), 200)

@app.route('/post/<int:id>', methods=['POST'])
def post_comment(id):
	comment =  request.get_json(silent=True, force=True)
	comment["created"] = int(time.time())
	comment["updated"] = int(time.time())
	comment['upvote'] = 1
	comment['downvote'] = 0
	comment["modifier"] = 1
	comment["post_id"] = id
	comment["children"] = json.dumps([])
	user = User.query.get(current_user.id)
	user.current_login_ip=request.remote_addr;
	user.toponym = json.dumps(get_toponym(user.current_login_ip))
	comment["toponym"] = user.toponym
	comment["user_id"] = current_user.id
	c = Comment(**comment)
	db.session.add(c)
	db.session.flush()
	if "parent" in comment and comment.get("parent") != 0:
		parent = Comment.query.get(comment["parent"])
		try:
			children = json.loads(parent.children)
		except:
			children = []
		children.append(c.id)
		parent.children = json.dumps(children)
	else:
		comment["parent"] = 0
	db.session.commit()
	return make_response(json.dumps({'link':'/comment/{}'.format(c.id)}), 200)

@app.route('/comment/<int:id>/moderate', methods=['POST'])
def comment_moderate():
	content =  request.get_json(silent=True, force=True)
	return make_response(200)

@app.route('/tags/trending', methods=['GET'])
def trending():
	posts = SubjectTag.query.filter(SubjectTag.trending=="POPULAR").order_by(SubjectTag.count).all()
	posts2 = SubjectTag.query.filter(SubjectTag.trending=="UP").order_by(SubjectTag.count).all()
	posts3 =SubjectTag.query.filter(SubjectTag.trending=="NEUTRAL").order_by(SubjectTag.count).all()
	posts4 =SubjectTag.query.filter(SubjectTag.trending=="DOWN").order_by(SubjectTag.count).all()
	if (posts2):
		posts.extend(posts2)
	if (posts3):
		posts.extend(posts3)
	if (posts4):
		posts.extend(posts4)
	if len(posts)==0:
		posts.append({"name":"all", "trending":"NEUTRAL", "count":0})
	posts.sort(key=lambda x: x.count, reverse=True)
	return make_response(json.dumps([post.to_dict() for post in posts]), 200)

@app.route('/tag/geo/<string:tags>', methods=['GET'])
def load_toponyms(tags):
	page = request.args.get('page', type=int, default=1)
	tag_list = tags.split('+')
	tag_list.sort()
	posts = []
	for tag in tag_list:
		subject_tag = SubjectTag.query.filter(SubjectTag.name==tag).first()
		tag_posts = Post.query.filter(Post.tags.contains(str(subject_tag.id)), Post.visible==True).order_by(Post.modifier).paginate(page, 50, False)
		for psts in tag_posts.items:
			psts.user = db.session.query(User).get(psts.user_id)
		posts.extend(tag_posts.items)
	posts = uniquify(posts)
	featureCollection ={
		"type": "FeatureCollection",
		"crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },
		"features": []
	}
	for post in posts:
		try:
			geo = json.loads(post.toponym)
			feature = {
				"type": "Feature",
				"geometry": {
					"type": "Point",
					"coordinates": [geo["longitude"], geo["latitude"]]
				},
				"properties": {
					"title": post.title,
					"name":geo["city"],
					"icon": "contact"
				}
			}
			featureCollection["features"].append(feature)
		except:
			pass
	return make_response(json.dumps(featureCollection), 200)


@celery.task(bind=True)
def automoderate(self):
	sys.stderr.write("starting long-running task")
	while(True):
		try:
			moderate_posts(app.config)
		except Exception as e:
			traceback.print_exc()
		try:
			db.session.remove()
		except:
			traceback.print_exc()
		time.sleep(1)






# JWT Token authentication  ===================================================
def authenticate(username, password):
	user = user_datastore.find_user(email=username)
	if user and username == user.email and verify_password(password, user.password):
		return user
	return None


def load_user(payload):
	user = user_datastore.find_user(id=payload['identity'])
	return user



# Flask-Restless API  =========================================================
@jwt_required()
def auth_func(**kw):
	pass


#try:

#except Exception as e1:
#    traceback.print_exc()
#    print(e1)


# Setup Admin  ================================================================


# Bootstrap  ==================================================================
def create_test_models():
	user_datastore.create_user(email='test', password=encrypt_password('test'))
	user_datastore.create_user(email='test2', password=encrypt_password('test2'))
	db.session.commit()


@app.before_first_request
def bootstrap_app():
	if not app.config['TESTING']:
		if db.session.query(User).count() == 0:
			create_test_models()
	automoderate.delay()

@app.teardown_request
def teardown(self):
	db.session.commit()
	db.session.remove()

def wrap_teardown_func(teardown_func):
	@wraps(teardown_func)
	def log_teardown_error(*args, **kwargs):
		try:
			teardown_func(*args, **kwargs)
		except Exception as exc:
			app.logger.exception(exc)
	return log_teardown_error

def main(app):
	global security, jwt, apimanager

	# Setup Flask-Security  =======================================================
	security = Security(app, user_datastore)
	jwt = JWT(app, authenticate, load_user)
	apimanager = APIManager(app, flask_sqlalchemy_db=db)
	init_admin()

	if app.teardown_request_funcs:
		for bp, func_list in app.teardown_request_funcs.items():
			for i, func in enumerate(func_list):
				app.teardown_request_funcs[bp][i] = wrap_teardown_func(func)
	if app.teardown_appcontext_funcs:
		for i, func in enumerate(app.teardown_appcontext_funcs):
			app.teardown_appcontext_funcs[i] = wrap_teardown_func(func)

	mail.init_app(app)
	try:
		db.init_app(app)
		with app.app_context():
			db.create_all()
	except Exception as e:
		print(e)

		# Start server  ===============================================================
		if __name__ == '__main__':
			try:
				app.run()
			except Exception as e:
				traceback.print_exc()

main(app)
