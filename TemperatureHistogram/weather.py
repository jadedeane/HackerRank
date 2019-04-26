"""
Exercise weather module.
"""

import json
import logging
import random
import time
from socket import timeout

import pyowm
from urllib3.exceptions import NewConnectionError, ReadTimeoutError

from TemperatureHistogram.geolocation import LocationDB, gen_epoch
from TemperatureHistogram.handlers import GracefulException
from TemperatureHistogram.settings import app_settings


def update_forecast_high_temperatures():
    """
    Ascertain next day's high temperature relative to a geographic location. Uses OpenWeatherMap API
    (https://openweathermap.org/api) via PyOWM library.

    PyOWM reference: https://pyowm.readthedocs.io/en/latest/usage-examples-v2/weather-api-usage-examples.html

    Using '/data/2.5/forecast/daily' route referenced here: https://openweathermap.org/forecast5

    If a location's `forecast_epoch` is less than the next day's offered epoch, the forecast temperature is stale and
    should be updated.

    We'll accept the first forecast day's information if the epoch is newer than a location's own, i.e., catch the next
    day's forecast before considering the day after next, etc.
    """

    # Create common database object
    location_db = LocationDB()

    # Find locations update eligible
    current_epoch = gen_epoch(0)
    logging.info("Querying locations with a forecast epoch older than `{}`".format(current_epoch))
    rows = location_db.select_(
        'SELECT ip, latitude, longitude, forecast_epoch FROM locations WHERE forecast_epoch < {}'
        .format(current_epoch))
    if not rows or len(rows) < 0:
        logging.info("No locations with stale forecast data.")
        return
    else:

        # Update locations with latest forecast temperature
        owm = pyowm.OWM(app_settings['owm_api_key'], use_ssl=True)
        owm_rpm = app_settings['owm_rpm']
        location_count = len(rows)
        rate_limiter = 0  # Counter for rpm
        sleep_time = 60  # Time to sleep per rpm intervals. Defaults to 1min. interval
        time_to_complete = int((location_count / 60) + (len(rows) / 60))  # Estimate time to complete queries
        logging.info(
            "It is estimated to take {}min. to complete fetching forecasts for {} location(s) due to OpenWeatherMap "
            "API rate limiter: {} queries/min. + {}sec. sleep timer each interval"
            .format(time_to_complete, location_count, owm_rpm, sleep_time))
        for row in rows:
            rate_limiter += 1
            ip, latitude, longitude, forecast_epoch = row[0], row[1], row[2], row[3]
            if app_settings['faux_temperature_data'] == 1:
                forecast_temperature, forecast_epoch = random.uniform(70, 79), gen_epoch(1)
            else:
                try:
                    # Fetch weather forecast
                    logging.debug("Fetching daily weather forecast for IP '{}'".format(ip))
                    forecast = owm.daily_forecast_at_coords(latitude, longitude, limit=2)
                    forecast_json = json.loads(forecast.get_forecast().to_JSON())  # Load weather forecast
                    weathers = forecast_json['weathers']  # Build list of forecast days
                    # Loop forecast days and see if one is newer than our existing forecast epoch
                    for forecast_day in weathers:
                        forecast_day = dict(forecast_day)
                        rt = forecast_day['reference_time']
                        rt = int(rt)
                        logging.debug(
                            "Comparing IP '{}' forecast epoch '{}' to offered forecast day epoch '{}'"
                            .format(ip, forecast_epoch, rt))
                        if rt > forecast_epoch:
                            logging.debug("Accepting offered forecast day epoch '{}' for IP '{}'".format(rt, ip))
                            forecast_epoch = rt
                            forecast_temperature = float(forecast_day['temperature']['max'])
                            forecast_temperature = (forecast_temperature - 273.15) * 9/5 + 32  # Convert to fahrenheit
                            break
                        else:
                            logging.debug(
                                "Rejecting offered forecast day epoch '{}' for IP '{} as location epoch is newer"
                                .format(rt, ip))
                            continue
                except ValueError:
                    logging.debug(
                        "OpenWeatherMap API failure for '{}: Invalid latitude, longitude '{},{}'"
                        .format(ip, latitude, longitude))
                except owm.exceptions.api_response_error.UnauthorizedError:
                    """Catch OWM API key failures."""
                    raise GracefulException("Invalid OpenWeatherMap API key!")
                except NewConnectionError:
                    """Catch OWM API new connection failures."""
                    raise GracefulException(
                        "Couldn't establish connection with OpenWeatherMap API! Please check network connectivity, and "
                        "API service.")
                except owm.exceptions.api_call_error.APIInvalidSSLCertificateError:
                    """Catch OWM API invalid SSL certification failures."""
                    raise GracefulException(
                        "Couldn't establish session with OpenWeatherMap API! Invalid SSL certificate.")
                except timeout or ReadTimeoutError or owm.exceptions.api_call_error.APICallTimeoutError:
                    """Catch OWM API connection breakdowns."""
                    raise GracefulException("Connection with OpenWeatherMap API timed out!")
                except pyowm.exceptions.api_call_error.APICallError as e:
                    """Catch OWM API internal errors, i.e., 500s, et al."""
                    raise GracefulException("OpenWeatherMap API returned error: {}".format(e.cause))
                except owm_rpm.exceptions.api_response_error.APIResponseError as e:
                    """Catch OWM API abnormal returns for a location."""
                    logging.error(
                        "OpenWeatherMap API returned '{}' for IP '{}'".format(e.status_code, ip))
                except owm.exceptions.api_response_error.NotFoundError as e:
                    """Catch OWM API returning a location not found."""
                    logging.error(
                        "OpenWeatherMap API returned 'not found' for IP '{}'. Cause: '{}'".format(ip, e.cause))

            # Update location database entry
            logging.debug(
                "Updating location IP '{}' with forecast high temperature '{}'".format(ip, forecast_temperature))
            location_db.update_(
                'UPDATE locations SET forecast_temperature = "{}", forecast_epoch = "{}" WHERE ip = "{}"'
                .format(forecast_temperature, forecast_epoch, ip))

            # Basic rate limiting capability in lieu of a more complex object, or context manager
            if rate_limiter == owm_rpm:
                logging.debug("OpenWeatherMap API rate limiter sleeping for {}sec.".format(sleep_time))
                rate_limiter = 0
                time.sleep(sleep_time)


def forecast_high_temperature_list():
    """
    Produces list of forecast high temperatures.
    :return: Temperature list.
    """

    temperature_list = []
    location_db = LocationDB()
    rows = location_db.select_('SELECT forecast_temperature FROM locations')
    try:
        for row in rows:
            temperature_list.append(int(row[0]))  # Add first element of temperature row to list
    except ValueError:
        # Should catch bogus or None/null temperatures before here, but just in case
        temperature_list.append(0)
    return temperature_list
