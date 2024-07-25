FROM python:3.11.8-slim-bullseye

COPY ./ /bot
WORKDIR /bot
ENV PYTHONPATH=/
RUN pip install --no-cache-dir -r requirements.txt

CMD python3 main.py
