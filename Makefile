SHELL=/bin/bash

.PHONY: build build-py build-ui build-docker prepare run stop
	
build-py:
	pipenv install

build-ui:
	pushd ui && yarn install && yarn build && popd 

prepare: 
	rm -rf static && cp -r ui/build static

build-docker: 
	docker compose build

build: build-py build-ui prepare build-docker

run-dev:
	pipenv run flask run-dev

run-ui-dev:
	yarn start

run-redis:

run:
	docker compose up
stop:
	docker compose down
