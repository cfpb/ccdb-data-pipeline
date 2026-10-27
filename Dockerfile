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
        coreutils

# Temporary fixes only available on edge.
# certifi 2026.10.23-r0: GHSA-6q48-6c7w-9gw2
# cryptography 50.0.0-r0: CVE-2026-69249, CVE-2026-69247, GHSA-537c-gmf6-5ccf
# urllib3 2.8.0-r0: CVE-2026-97687, CVE-2026-97689
RUN echo "@edge https://dl-cdn.alpinelinux.org/alpine/edge/main" >> /etc/apk/repositories && \
    apk update && \
    apk add --no-cache py3-certifi@edge py3-cryptography@edge py3-urllib3@edge

RUN pip install --upgrade pip setuptools && \
    pip install -r ./requirements.txt

# Don't run as the root user.
ARG USER=base
RUN adduser -g ${USER} --disabled-password ${USER}
RUN chown -R ${USER}:${USER} ${HOME}

USER ${USER}
