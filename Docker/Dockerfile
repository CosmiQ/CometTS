FROM python:3.6

MAINTAINER jshermeyer

## Install Reqs
RUN apt-get update && apt-get install -y --no-install-recommends \
        gdal && \
        pip install rasterio \
        pip install rasterstats \
        pip install numpy \
        pip install pandas \
        pip install geopandas \
        pip install shapely \
        pip install matplotlib \
        pip install tqdm \
        pip install scipy \
        pip install fnmatch \

## Install Comet
RUN pip install git+https://github.com/CosmiQ/CometTS.git
