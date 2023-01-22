Sample URL shortener meant to provide a solid foundation for a horizontally scalable web application.

## Getting Started

### Requirements

- docker (desktop OR engine+compose)
- python 3
- pip 3
- pipenv https://pipenv.pypa.io/en/latest/install/ (make sure you you add `~/.local/bin` to your PATH!)
- node >= 19.3 https://docs.npmjs.com/downloading-and-installing-node-js-and-npm
- npm >= 9.2
- yarn >= 1.22.19 (`npm install --global yarn`)

### Quick Start
For an overview of the app, run
```
make ARGS="--headed" build test
```
The first time you run this, it will take a while as it has to download all of the docker, python, and node assets used by the app.  Then you will see a browser open and quickly walk through the functionality of the app.

If you want to play with the app, you can run
```
make build run
```
and open a browser at http://localhost:8080

when you are done, run

```
make stop
```

to release the docker resources.

### Architecture
The application uses Python Flask to serve web requests in REST-ish format with JSON. The WSGI interface for hosting the application is Gunicorn, which is fronted by NGINX.  NGINX is responsible for serving the static content.

As a datastore, the appication uses Redis backed by Postgres.

The docker composition allows us to simulate production deployment for testing purposes.  In production we would likely just use load balancers in front of the stack to distribute load.  We would also likely distribute the redis cache and use cloud managed postgres (or really, any other datastore) to minimize maintenance such as upgrades, backups, and overall availability.

While the UI is written with React and Material UI, the functionality is pretty limited because of the scope of the requirements.  Realistically, we would want some kind of authentication and user management so that users can keep a list of their short urls.  Because the state is so limited, no state container is used and component definition is largely avoided.

### Local Development
For local development, you will likely want to have the databases running in docker, with flask and node running locally for hot-swapping of code and rapid development feedback.  To do this, you run

```
make run-dev
```

and in a separate terminal

```
make run-ui-dev
```

This will launch the development web app at http://localhost:3000.  Then you can change code, save it, and immediately play with it.

When you are finished, run

```
make stop-datastore
```

To release the docker resources.

### Testing
#### Integration
Integration tests are a relatively fast way of validating the backend API.

To run them you can use

```
make test-integration
```

This will wipe the datastore, launch the datastore, and execute the integration tests.

#### E2E
E2E Tests are managed/run by Cypress and located at ./ui/cypress/e2e.
This allows us to smoke test the UI and backend together in a production-like deployment.  

To develop tests, run

```
make build run
cd ui
yarn run cypress open
```

Then you can edit tests and automatically rerun them when you save them.

### Other Notes
#### Running E2E Tests Against Local UI/Backend
The Cypress tests look for a [host variable](ui/cypress/e2e/happy-path.cy.ts#L4).  This is so we can point them to other environments, such as CI/CD or production.  You can also use this to develop cypress tests when using the configuration above under local development.

With the local development configuration running, you can run

```
cd ui && yarn run cypress open --env host='localhost:3000'
```

Then you will be able to edit tests and code and immediately see the results.

#### Datastore Persistence
The datastore persists via a Docker volume.  When `make test` or `make test-integration` is executed, it wipes the datestore to ensure repeatable test results.  This is good to keep in mind if you run tests and then find all your links are gone.  If you find this behavior annoying, the make commands can be further refactored so that wiping is optional.

You can also manually wipe the datastore at any time (provided you have killed all the running containers) by running

```
make wipe-db
```

