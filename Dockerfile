# Use base image of NGINX as it forwards logs to std
FROM nginx:1.13.0

RUN apt-get -qq update \
  && apt-get -qq install -y python-pip supervisor \
  && rm -rf /var/lib/apt/lists/* \
  && pip install uwsgi

# Use custom configuration files
RUN echo "daemon off;" >> /etc/nginx/nginx.conf
RUN rm /etc/nginx/conf.d/default.conf
COPY conf/nginx.conf /etc/nginx/conf.d/
COPY conf/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Setup the Flask application
COPY requirements.txt .
RUN pip install --quiet -r requirements.txt
COPY . /app/
WORKDIR /app

CMD ["/usr/bin/supervisord"]
