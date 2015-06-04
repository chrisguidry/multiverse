FROM ubuntu:14.04
MAINTAINER chris@theguidrys.us

ENV DEBIAN_FRONTEND noninteractive
RUN echo 'deb http://us.archive.ubuntu.com/ubuntu/ trusty multiverse' >> /etc/apt/sources.list.d/multiverse.list && \
    apt-get update && \
    apt-get install -y \
        python3.4 \
        python3-pip \
        unrar \
        uwsgi \
        uwsgi-plugin-python3 \
    && rm -rf /var/lib/apt/lists/*

ADD requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

RUN adduser --system --uid 1000 multiverse --no-create-home --disabled-login
USER multiverse

ADD . /multiverse
VOLUME /multiverse
VOLUME /library

ENTRYPOINT ["/multiverse/webserver"]

# 3333: web, 4444: uwsgi
EXPOSE 3333 4444
