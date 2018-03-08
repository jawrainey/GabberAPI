# Gabber API

> The resource endpoints for Gabber projects, sessions and discussions (annotations and comments) on specific sessions.

## Running locally

The API requires that [JWT](https://github.com/jawrainey/GabberServer/blob/master/gabber/__init__.py#L19), [MYSQL](https://github.com/jawrainey/GabberServer/blob/master/gabber/__init__.py#L18) are set, and optionally [Amazon S3](https://github.com/jawrainey/GabberServer/blob/master/gabber/utils/amazon.py#L9-L11) if you want to POST a session. These environmental variables should go into your [`.env` file](https://github.com/jawrainey/GabberServer/blob/master/docker-compose.yml#L11).

``` bash

# Launch with docker-compose.yml
docker-compose up -d --build

# Setup the database
docker-compose exec web bash

export FLASK_APP=run.py
flask db init

# Once setup leave the container
exit

# View the logs of the Flask container
docker-compose logs -f web
```
