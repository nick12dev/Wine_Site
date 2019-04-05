# m3-core (draft)

### Init Dev Environment
Run:
```bash
bash init-dev-env.sh
```

### Installation
```
pipenv install --dev  # creates virutalenv and installs packages from Pipfile.lock (including dev ones)
set -a && source dev-env.list && set +a  # sets environment variables
pipenv run flask db upgrade  # upgrades db schema
```

##### Note
If you want to avoid prefixing every python related command with "pipenv run " you can activate virtualenv for your
terminal by running the following command:
```
pipenv shell
```
After that you can stop prefixing python related commands with "pipenv run ".

### Running
```
set -a && source dev-env.list && set +a
pipenv run gunicorn --bind 0.0.0.0:5000 --timeout 1000 -k gevent --workers 2 --preload wsgi:app
```

### Sanity check
- <http://localhost:5000/> should redirect to Cognito login page.
- After logging in with credentials of a user from Cognito User Pool ( for ex. teremterem / Teremterem321& ) a redirect
to GraphiQL endpoint should happen.

### Tests
Run tests:
```
pipenv run coverage run -m pytest
```
Generate coverage report:
```
pipenv run coverage html
```
Coverage report will be put into **htmlcov** folder.

### Building docker image
```
sudo docker build -t m3-core .
```

### Running docker image
```
sudo docker run --env-file ./dev-env.list -p 127.0.0.1:5000:5000 m3-core
```

# Docker Compose
To set up local dev environment with docker-compose:

- build 'alembic' image to set db and be able to run db migrations
```bash
cd core/db
docker build -t alembic .
```

- run docker-compose
```bash
cd m3-core
docker-compose up -d
```

- to init db connect to the 'alembic' and run 'init_db.sh'
```bash
docker-compose exec alembic /bin/bash
bash init_db.sh
```

