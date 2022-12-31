SHELL=/bin/bash

.PHONY: build build-py build-ui build-docker prepare run run-app-local run-dev run-datastore run-ui-dev stop stop-datastore test
	
build-py:
	pipenv install

build-ui:
	pushd ui && yarn install && rm -rf build && yarn build && popd 

prepare: 
	rm -rf static && cp -r ui/build static

build-docker: 
	docker compose build

build: build-py build-ui prepare build-docker

run:
	docker compose up -d

run-app-local:
	pipenv run flask run

run-datastore:
	docker compose -f docker-compose-local.yml up -d

run-dev: run-datastore run-app-local

run-ui-dev:
	yarn start

stop:
	docker compose down

stop-datastore:
	docker compose -f docker-compose-local.yml down

test: 
	make stop
	make run
	pushd ui && yarn cypress run && popd
	make stop
	
