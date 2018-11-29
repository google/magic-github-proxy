FROM python:3.7.1-slim-stretch

WORKDIR /app/magicproxy

COPY . .

RUN pip install -r requirements.txt
RUN python setup.py install

CMD ["python3"]

