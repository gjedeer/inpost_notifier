FROM golang:alpine as builder

RUN apk add git && go get -u github.com/alufers/inpost-cli

FROM python:3-alpine

RUN apk add --no-cache gnupg 
RUN adduser -D -u 1000 inpost && mkdir -p /home/inpost/.config/alufers/inpost-cli

COPY notify_inpost.py /
COPY --from=builder /go/bin/inpost-cli /usr/bin/

COPY inpost-cli-json.json /

USER inpost
CMD python3 /notify_inpost.py
