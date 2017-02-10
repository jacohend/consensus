This is a starting point for a [Flask](http://flask.pocoo.org/) website + API using:

- [Flask-Restless](https://flask-restless.readthedocs.org/en/latest/) (API)
- [Flask-Security](https://pythonhosted.org/Flask-Security/) (Authentication)
- [Flask-JWT](https://pythonhosted.org/Flask-JWT/) (API authentication)
- [Flask-Admin](http://flask-admin.readthedocs.org/en/latest/) (Admin views)
- [SQLAlchemy](http://www.sqlalchemy.org/) (ORM)

Plus stubs for

- Templates
- Testing

Github user "graup" got the basic idea from Nic:
http://stackoverflow.com/a/24258886/700283

Setup
=====

- [Install docker](https://docs.docker.com/engine/installation/)
- run './rundocker.sh build' to build the sharity docker image (placing the flask app inside a virtual linux environment) and pull down the PostGres db docker image.
- run './rundocker.sh run' to run the docker images, bringing up the virtual flask and virtual postgres environments.
- run './rundocker.sh reload' to restart the flask server, which will install the schema to the database.
- run './rundocker.sh shell' to get a shell into the flask server. 
- run './rundocker.sh remove' to shutdown and remove the docker images. 

**Website**

- Access site at localhost/. Not much there, just a basic example for logging in.
- API at localhost/api/v1/<model>

**Admin**

- Access admin at /admin

**API auth**

- POST /api/v1/auth {'username': '', 'password': ''}
- Returns JSON with {'access_token':''}  
- Then request from API using header 'Authorization: JWT $token'

**Logs

- run './rundocker.sh shell' to get a shell into the flask server. 
- run 'tail -f /var/log/uwsgi/uwsgi.log' to see the output from the python subinterpreters
