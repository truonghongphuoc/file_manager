FROM ubuntu:16.04

MAINTAINER Phuoc Truong "truonghongphuoc@gmail.com"

RUN apt-get update -y && \
    apt-get install -y python3-pip python-dev
# We copy just the requirements.txt first to leverage Docker cache
COPY . /app
WORKDIR /app
RUN pip3 install -r requirements.txt
COPY ./app.py /app
EXPOSE 5000
ENTRYPOINT [ "python3" ]
CMD [ "app.py" ]
