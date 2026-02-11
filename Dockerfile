FROM python:3.13-alpine

ENV LANG=en_US.UTF-8
ENV PIP_NO_CACHE_DIR=true
ENV PYTHONUNBUFFERED=1
ENV HOME=/usr/home

WORKDIR ${HOME}

# Add Zscaler Root CA certificate, rebuild CA certificates, and both the root
# cert and the rebuilt ca-certificates cert to APP_HOME for reuse.
ADD https://raw.githubusercontent.com/cfpb/zscaler-cert/3982ebd9edf9de9267df8d1732ff5a6f88e38375/zscaler_root_ca.pem ${HOME}/zscaler-root-public.cert
RUN cp ${HOME}/zscaler-root-public.cert /usr/local/share/ca-certificates/zscaler-root-public.cert && \
    apk add ca-certificates --no-cache --no-check-certificate && \
    update-ca-certificates && \
    cp /etc/ssl/certs/ca-certificates.crt ${HOME}/ca-certificates.crt

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
