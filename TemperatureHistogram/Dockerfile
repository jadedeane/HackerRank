#### Build container for geoipupdate ###
FROM golang:alpine as build
RUN apk add --update curl git
RUN git clone https://github.com/maxmind/geoipupdate.git /tmp/build
WORKDIR /tmp/build
RUN git checkout tags/v4.0.2
ENV GOPATH /tmp/build
WORKDIR /tmp/build/cmd/geoipupdate
RUN go get -t ./... 2> /dev/null; exit 0
RUN go build


### Runtime container ###
FROM python:3.7.3-alpine3.9

# Copy geoipupdate binary from build container
COPY --from=build /tmp/build/cmd/geoipupdate/geoipupdate /usr/bin/

# Create applications directories
RUN mkdir /TemperatureHistogram
WORKDIR /TemperatureHistogram
ENV PYTHONPATH /

# Packages to build
ARG BUILD_PACKAGES="gcc g++ tzdata"

# Copy Python requirements
COPY requirements.txt .

# Build and install packages and Python requirements
RUN set -xe &&\
    apk add --no-cache $BUILD_PACKAGES &&\
    ln -s /usr/include/locale.h /usr/include/xlocale.h &&\
    pip3 install --upgrade pip==19.0.3 &&\
    pip3 install --no-cache-dir -r requirements.txt &&\
    apk del --purge --no-cache $BUILD_PACKAGES &&\
    rm -rf /var/cache/apk/* &&\
    echo "UTC" >  /etc/timezone

# Copy applicaiton contents
COPY . .

# User configurable settings. Please do not modify things outside of here!
# <CONFIG>
# Log input file
ENV LOG_INPUT /data/input.log
# Reduce sample size. Maximum log input lines to consider
ENV REDUCE_SAMPLE_SIZE 0
#ENV MAX_SAMPLE_SIZE 100
# Histogram output file
ENV TSV_OUTPUT /data/histogram.tsv
# Histogram buckets
ENV BUCKETS 5
# Bypass OpenWeatherMap API and generate random temperature data
ENV FAUX_TEMPERATURE_DATA 0
# OpenWeatherMap API key
ENV OWM_API_KEY YOUR_KEY_HERE
# OpenWeatherMap requests-per-minute (rpm) for rate limiter
ENV OWM_RPM 60
#/CONFIG>

# Update persistent geolocation data, and start application
CMD chmod +x ./geoipupdate.sh && ./geoipupdate.sh && python __main__.py
