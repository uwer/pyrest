#ARG ARCH="aarch64"

FROM ubuntu/py12gdal:24.04
# labels pyrest/lookup-base
#
## Depending on how this wants to be run, one can mount the geometry and other potential files or 
## create a subsidary image with the relevant data included for portability  

WORKDIR /app


COPY ./requirements-geom.txt /app/requirements-geom.txt
COPY ./requirements-server.txt /app/requirements-server.txt
RUN mkdir /app/data ; pip3 install -r  /app/requirements-geom.txt --break-system-packages
##

COPY ./src/pyrest  /app/pyrest/

#
#
ARG HANDLERPORT=9088
ENV HANDLERPORT=$HANDLERPORT

ARG HANDLERCONFIG=/app/config.json
ENV HANDLERCONFIG=$HANDLERCONFIG

COPY ./deploy/lookups/exec.sh /app/exec.sh
RUN chmod 770 /app/exec.sh
CMD ["/app/exec.sh"]
