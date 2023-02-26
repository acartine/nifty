SHELL=/bin/bash

.PHONY: build build-ui datastore-run datastore-stop db-apply db-apply-local db-reapply-all-local db-rollback-all db-rollback-all-local db-wipe docker-build docker-run docker-stop prepare py-build py-clean run-app-local run-dev run-ui-dev run-trend-worker-local stack-run stack-stop test test-integration test-ui-dev
	
build-ui:
	pushd ui && yarn install && rm -rf build && yarn build && popd 

build: py-build build-ui prepare docker-build

datastore-run:
	docker compose up --wait -d

datastore-stop:
	docker compose down

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

docker-build: py-clean
	docker build -t acartine/nifty:v1 ${ARGS} .

trend-worker-docker-build: py-clean
	docker build . -f docker/worker.dockerfile --target worker-trend -t acartine/nifty-worker-trend:v1

docker-run: docker-build
	docker run --env-file .env -p 127.0.0.1:5000:5000 --name nifty -d acartine/nifty:v1

docker-stop:
	docker container stop nifty && docker container rm nifty

prepare: py-clean 
	rm -rf src/static && cp -r ui/build src/static

py-build:
	pipenv install

py-clean:
	pipenv run pyclean .

run-app-local:
	PYTHONPATH=src pipenv run flask --debug run

run-dev: datastore-run run-app-local

run-ui-dev:
	pushd ui && yarn start

run-trend-link-worker-local:
	PYTHONPATH=src pipenv run python src/trend_link_worker/trend_link_worker.py

run-trend-worker-local:
	PYTHONPATH=src pipenv run python -m nifty_worker.trend_worker

stack-run: docker-build trend-worker-docker-build
	docker compose --profile all up --wait -d

stack-stop:
	docker compose --profile all down


stack-base-run: docker-build
	docker compose --profile base up --wait -d

stack-base-stop:
	docker compose --profile base down

test: stack-stop db-wipe stack-run db-apply-local
	pushd ui && yarn cypress run ${ARGS}; \
	e=$$?; \
	popd; \
	make stack-stop; \
	exit $$e

test-integration: datastore-stop db-wipe datastore-run db-apply-local db-reapply-all-local
	PYTHONPATH=src pipenv run pytest tests/integration/all.py; \
        e=$$?; \
	make datastore-stop; \
        exit $$e

test-unit: py-clean
	PYTHONPATH=src pipenv run pytest tests/unit

test-ui-dev:
	pushd ui && yarn run cypress open --env host='localhost:3000'

