FROM golang:alpine as builder

RUN apk add git && go install github.com/alufers/inpost-cli@latest

FROM python:3-alpine

RUN apk add --no-cache gnupg tini
RUN adduser -D -u 1000 inpost && mkdir -p /home/inpost/.config/alufers/inpost-cli

COPY --from=builder /go/bin/inpost-cli /usr/bin/
COPY refresh_keys.sh /
COPY crontab /etc/crontabs/inpost
COPY notify_inpost.py /

ENTRYPOINT ["/sbin/tini", "--"]
CMD /usr/sbin/crond -f -l 0
