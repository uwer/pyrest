

from python:3.9.16-slim-buster

WORKDIR /app

COPY src/pyrest /app/pyrest

COPY requirements*.txt /app/
RUN pip3 install -r requirements-client.txt 
RUN pip3 install -r requirements-server.txt



ARG HANDLERPORT=9088
ENV HANDLERPORT=$HANDLERPORT

ARG HANDLERCONFIG=/app/pyrest/echo.json
ENV HANDLERCONFIG=$HANDLERCONFIG

CMD ["python3","/app/pyrest/service.py"]

