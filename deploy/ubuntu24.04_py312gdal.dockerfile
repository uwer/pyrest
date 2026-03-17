FROM ubuntu:24.04
# label as ubuntu/py12gdal:24.04

RUN apt update; apt install  -y python3-gdal python3-pip libgdal-dev git curl
#RUN apt install  -y python3-fiona python3-shapely  python3-pyproj  python3-geographiclib 
RUN pip3 install 'fiona<1.9.8' 'shapely>2.0.0' geographiclib pyproj --break-system-packages
RUN apt -y remove libgdal-dev ; apt -y autoremove
