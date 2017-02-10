#!/bin/bash

COMMAND="$1"
CLUSTER="consensus"

function run {
    docker run --net=$CLUSTER -e DB_USER=sharemore -e DB_PASS=consensusdev -e DB_HOST=postgres -e DB_NAME=consensus -e SERVER_ENV=Development -e APP_NAME=app -e SECRET_KEY=key -e SECURITY_PASSWORD_SALT=salt --name=server -p 80:80 -d consensus
    docker run --net=$CLUSTER --name=postgres -e POSTGRES_DB=consensus -e POSTGRES_USER=sharemore -e POSTGRES_PASSWORD=consensusdev -d postgres
    docker run --net=$CLUSTER -p 6379:6379 --name redis -d redis

}

function build {
    docker network create $CLUSTER || true
    docker build -t consensus .
    docker pull postgres
}

function reload {
    docker cp . server:/home/server/src
    docker exec -d server supervisorctl restart app-uwsgi
    docker exec -d server supervisorctl restart celery
}

function remove {
    docker kill server || true
    docker kill postgres || true
    docker kill redis || true
    docker rm server || true
    docker rm postgres || true
    docker rm redis || true
}

function shell {
    docker exec -ti server bash
}

${COMMAND}
