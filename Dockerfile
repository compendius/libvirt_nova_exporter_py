FROM python:3.6-alpine

WORKDIR /usr/src/app
RUN apk update
RUN apk add libvirt-dev gcc musl-dev
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt
COPY ./libvirt_nova.py .
ENTRYPOINT [ "python", "./libvirt_nova.py" ]

