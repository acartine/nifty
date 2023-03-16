SHELL=/bin/bash

.PHONY: build build-ui datastore-run datastore-stop db-apply db-apply-local db-reapply-all-local db-rollback-all db-rollback-all-local db-wipe docker-build docker-run docker-stop prepare py-build py-clean run-app-local run-dev run-ui-dev run-trend-local stack-run stack-stop test py-test-integration test-ui-dev
	
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

db-wipe-soft:
	pipenv run python -m nifty.util.db.clean

docker-build: py-clean
	docker build -t acartine/nifty:v1 ${ARGS} .

trend-docker-build: py-clean
	docker build . -f docker/worker.dockerfile --target worker-trend -t acartine/nifty-trend:v1

trend-link-docker-build: py-clean
	docker build . -f docker/worker.dockerfile --target worker-trend-link -t acartine/nifty-trend-link:v1

docker-run: docker-build
	docker run --env-file .env -p 127.0.0.1:5000:5000 --name nifty -d acartine/nifty:v1

docker-stop:
	docker container stop nifty && docker container rm nifty

prepare: py-clean 
	rm -rf nifty/service/static && cp -r ui/build nifty/service/static

py-build:
	pipenv install

py-clean:
	pipenv run pyclean .

run-app-local:
	APP_CONTEXT_CFG=nifty PRIMARY_CFG=local pipenv run flask --debug --app nifty.service.app:app run

run-dev: datastore-run run-app-local

run-ui-dev:
	pushd ui && yarn start

run-trend-link-local:
	APP_CONTEXT_CFG=trend_link pipenv run python -m nifty.worker.trend_link

run-trend-local:
	APP_CONTEXT_CFG=trend pipenv run python -m nifty.worker.trend

stack-run: docker-build trend-docker-build trend-link-docker-build
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

py-test-integration-raw: stack-stop db-wipe datastore-run db-apply-local db-reapply-all-local
	PYTHONPATH=. APP_CONTEXT_CFG=integration_test PRIMARY_CFG=local pipenv run pytest tests_integration/all.py

py-test-integration: 
	make py-test-integration-raw; \
	e=$$?; \
	make datastore-stop; \
        exit $$e

py-test-unit: py-clean py-lint-check py-type-check
	pipenv run python -m unittest discover

py-coverage: py-clean py-lint-check py-type-check
	pipenv run coverage run -m unittest discover

test-ui-dev:
	pushd ui && yarn run cypress open --env host='localhost:3000'

py-type-check:
	pipenv run pyright

py-lint:
	pipenv run black nifty -t py311

py-lint-check:
	pipenv run black nifty -t py311 --check

py-sanity: py-lint-check py-type-check
py-sanity-full: py-sanity-fast py-test-integration

sanity-full: py-test-integration-raw
	make db-wipe-soft; \
	e=$$?; \
	make stack-base-run; \
	e=$$?; \
	pushd ui && yarn cypress run ${ARGS}; \
	e=$$?; \
	popd; \
	make stack-stop; \
	exit $$e

