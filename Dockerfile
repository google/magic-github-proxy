FROM python:3.8 AS builder
WORKDIR /src
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip wheel
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY . ./
RUN pip install .

FROM python:3.8-slim
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" PYTHONUNBUFFERED=1
CMD ["python3", "-m", "magicproxy"]

