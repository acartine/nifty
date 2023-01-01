Sample URL shortener meant to provide a solid foundation for a horizontally scalable web application.

## Getting Started

### Requirements

- python 3
- pip 3
- pipenv https://pipenv.pypa.io/en/latest/install/
- node >= 19.3 https://docs.npmjs.com/downloading-and-installing-node-js-and-npm
- npm >= 9.2
- yarn >= 1.22.19

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
and open a browser at http://localhost

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

Then you can change code, save it, and immediately play with it.

When you are finished, run

```
make stop-datastore
```

To release the docker resources.

