FROM python:3.8-slim
COPY dist/*.whl /opt/dist/
RUN pip3 install /opt/dist/*
ENTRYPOINT ["python3", "-m", "magicproxy"]