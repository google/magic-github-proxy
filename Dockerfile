FROM python:3.7.1-slim-stretch

WORKDIR /app/magicproxy

RUN pip install --upgrade pip
RUN pip install wheel

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . ./

RUN pip install .

CMD ["python3", "-m", "magicproxy"]

