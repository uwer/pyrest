from pyrest/lookup-base

### RUN AS
## docker build -t pyrest/lookup-netcdf:<SOME unique context> --build-arg HANDLERCONFIG=<SOME CONFIG>.json --build-arg DATAFILE=<SOME NETCDG>.nc -f ./docker/netcdf.dockerfile .

ARG HANDLERCONFIG=config.json
copy $HANDLERCONFIG /app/config.json

ARG DATAFILE=netcdf.nc

RUN mkdir -p /app/data

copy $DATAFILE /app/data/netcdf.nc
