SHELL=/bin/bash

.PHONY: build build-py build-ui build-docker datastore-run datastore-stop db-apply db-apply-local db-reapply-all-local db-rollback-all db-rollback-all-local db-wipe  prepare run run-app-local run-dev run-ui-dev stop test test-integration test-ui-dev
	
build-py:
	pipenv install

build-ui:
	pushd ui && yarn install && rm -rf build && yarn build && popd 

prepare: 
	rm -rf static && cp -r ui/build static

build-docker: 
	docker compose build

build: build-py build-ui prepare build-docker

datastore-run:
	docker compose -f docker-compose-local.yml up -d

datastore-stop:
	docker compose -f docker-compose-local.yml down

db-apply:
	pipenv run yoyo apply

db-apply-local:
	PG_HOST=localhost PG_ADMIN_PWD=mypassword make db-apply

db-reapply-all-local:
	pipenv run yoyo reapply --all

db-rollback-all:
	pipenv run yoyo rollback --all

db-rollback-all-local:
	PG_HOST=localhost PG_ADMIN_PWD=mypassword make db-rollback-all

db-wipe:
	docker volume rm -f nifty_postgres-data

run:
	docker compose up -d

run-app-local:
	pipenv run flask --debug run

run-dev: datastore-run run-app-local

run-ui-dev:
	pushd ui && yarn start

stop:
	docker compose down

test: stop db-wipe run
	PG_HOST=localhost PG_ADMIN_PWD=mypassword make db-apply-local
	pushd ui && yarn cypress run ${ARGS} && popd
	make stop

test-integration: datastore-stop db-wipe datastore-run db-apply-local db-reapply-all-local
	PYTHONPATH=. pipenv run pytest tests/integration/all.py; \
        e=$$?; \
	make datastore-stop; \
        exit $$e

test-ui-dev:
	pushd ui && yarn run cypress open --env host='localhost:3000'

