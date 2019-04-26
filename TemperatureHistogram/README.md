# TemperatureHistogram

![](yes.png?raw=true "")

This application takes an input log, finds content that can be geolocated (e.g., IP addresses), and outputs a simple histogram composed of location forecast high temperatures.

No input log file is included. Please place your log file into the [data](data) directory. Filename expected is `input.log`, and can be configured within application settings. The log file must include one or more IP addresses per-line (RFC1918 or public, but must include some public IPs or no geolocation will take place).

The application's use of OpenWeatherMap's API is rate limited by default in lieu of an account permitting unrestricted access. This will cause initial processing of location temperatures to be rather time consuming. Please see the `MAX_SAMPLE_SIZE` setting for quicker testing.

## Settings

All user configurable settings can be found within the application [Dockerfile](Dockerfile).

### LOG_INPUT

Log input path and filename. Defaults to `/data/input.log`.

### REDUCE_SAMPLE_SIZE

Whether or not to reduce the log input sample size.

### MAX_SAMPLE_SIZE

Maximum log input lines to evaluate.

### TSV_OUTPUT

Histogram output path and filename. Defaults to `/data/histogram.tsv`.

### BUCKETS

Number of histogram buckets (bins). Default is `5`.

### FAUX_TEMPERATURE_DATA

Bypass OpenWeatherMap API for weather data, and populate locations with random floats.

### OWM_API_KEY

Fetching weather forecast information uses OpenWeatherMap's [API](https://openweathermap.org/api), and requires you to configure an API key. After [registering](https://home.openweathermap.org/users/sign_up) with OpenWeatherMap, an API key may be configured [here](https://home.openweathermap.org/api_keys).

### OWM_RPM

OpenWeatherMap API requests-per-minute allowed commensurate with the API key's associated account capability. Defaults to 60 queries per one minute interval.

## Usage

```shell
docker build -t historama . &&\
docker run --rm -v $DATA_FOLDER_PATH:/data historama
```

Execute above docker commands, where `$DATA_FOLDER_PATH` is the absolute path to the data folder.

## Runtime and Development Reference

The application runs in a Docker container, and bind mounts the [data](data) directory to `/data`. All files within are considered ephemeral when use of the application is complete.

### Logging

Baisc (INFO) logging is provided to the console. Granular (DEBUG) logging can be found at `/data/output.log`

### Phases

#### Container build

The image is built using a multi-stage Dockerfile. The first part of the [Dockerfile](Dockerfile) uses Golang Alpine to build MaxMind's [geoipdate](https://github.com/maxmind/geoipupdate) binary, which is copied out of this stage to the application container.

The application container uses Python 3.7.3 Alpine 3.9, and runs `geoipupdate` and the histogram application.

#### Container run

When the container first runs, it will download a MaxMind GeoIP2 GeoLite2-City database if no existing copy is found. The database will be checked, and download a newer version if availible. The process employed via [geoipupdate.sh](geoipupdate.sh) is described [here](https://dev.maxmind.com/geoip/geoipupdate). This database is the foundation for geolocation lookups, and any failure in this process will terminate the container.

#### Python application setup and run

The [entrypoint application](__main__.py) `main()` function is decorated with `app_setup` that configures basic logging, and initializes the location database. If no location database or `locations` table is found within they are created.

#### Location database

The location SQLite database and its `locations` table are where geolocated locations (IPs) are stored. The IP address (`ip` column) is the key value, and serves to represent a location.

#### Log parsing for locations

Each line of the log input file is examined for any IPv4 host addresses. Multiple (unique) IPs per line are allowed by default. This can be optionally set for single IP per line if the `LogParser` object is created with `consider_multiple_ips=False` set.

When IP(s) are found on a line, they are evaluated for geolocation consideration by ascertaining whether or not they are public (i.e., not RFC1918, or otherwise "special purpose"). The use of `ipaddress` library and its `is_global` method ensures "global" validity against IANA's [IPv4](https://www.iana.org/assignments/iana-ipv4-special-registry/iana-ipv4-special-registry.xhtml) and [IPv6](https://www.iana.org/assignments/iana-ipv6-special-registry/iana-ipv6-special-registry.xhtml) "Special-Purpose Address Registry".

All valid IPs are consolidated into an IP list, that is then used to geolocate them. If no IP list is produced the application raises an exception and terminates.

#### Geolocation

A `GeoBuilder` object is created, and its `build_locations` method is called while passing aforementioned IP list.

IPs are processed with an attempt to geolocate them against the GeoLite2-City database.

Successfully geolocated IPs are inserted into the location database, along with their respective geolocation information. Initial "placeholder" `forecast_epoch` and `forecast_temperature` columns are populated with dummy values to ensure valid values exist.

#### Weather forecast

The `update_forecast_high_temperatures` function is called, which will find all locations where the `forecast_epoch` column has a value older than the latest available for that location.

For locations found to have "stale" forecast information, a call is made against OpenWeatherMap's API to update the (next day's) forecast high temperature.

If no locations require an update the application proceeds.

#### Temperature list

The `forecast_temperature` column for all locations is queried and assembled into a temperature list. This temperature list is then modified into a NumPy array for histogram processing. If no temperature list can be constructed an exception is raised, and the application terminates.

#### Histogram

A `Histogram` object is created, and via its `build_histograms` method NumPy takes the temperature array, computes frequencies and bins, and zips them into an array. The object's `save_histogram` method uses NumPy's `savetxt`, which is called against the zipped array. The desired histogram file is produced, and displayed in the logs.

Example output:
```text
Exercise tsv content with a bucket count of 5:

bucketMin	bucketMax	count
38.00		47.60		3
48.60		58.20		25
59.20		68.80		17
69.80		79.40		42
80.40		90.00		6
```
