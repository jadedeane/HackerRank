#!/bin/sh

echo "Updating geolocation database."
geoipupdate  -v --stack-trace -f GeoIP.conf -d /data
rm -f /data/.geoipupdate.lock
