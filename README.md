# Gabber Api / Old Web



#### Rob's Notes
``` bash
# Launch with docker-compose.yml
cd into/this/directory
docker-compose up -d

# Setup the database
docker-compose exec web bash
flask db init

# (optional) other commands you might want to do
flask db migrate
flask db upgrade

# Get out of your container
exit


```
