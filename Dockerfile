FROM python:3.9.2-slim-buster

WORKDIR /usr/src

COPY . /usr/src

COPY ./requirements.txt /src/requirements.txt

EXPOSE 8000:8000

RUN pip install --no-cache-dir -r /usr/src/requirements.txt

ENV MONGODB_URL "mongodb+srv://usr:pwd@cluster0.nwtm1.mongodb.net/comics?retryWrites=true&w=majority"

CMD ["uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"]