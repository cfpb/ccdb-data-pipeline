FROM python:3.13-alpine

ENV LANG=en_US.UTF-8
ENV PIP_NO_CACHE_DIR=true
ENV PYTHONUNBUFFERED=1
ENV HOME=/usr/home

WORKDIR ${HOME}

COPY . .

RUN apk update --no-cache && \
    apk upgrade --no-cache --ignore alpine-baselayout && \
    apk add --no-cache \
        aws-cli \
        jq \
        make

RUN pip install --upgrade pip setuptools && \
    pip install -r ./requirements.txt

# Don't run as the root user.
ARG USER=base
RUN adduser -g ${USER} --disabled-password ${USER}
RUN chown -R ${USER}:${USER} ${HOME}

USER ${USER}
