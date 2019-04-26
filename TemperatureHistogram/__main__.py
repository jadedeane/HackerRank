"""
Exercise main application, and container entry point.
"""

import logging

from TemperatureHistogram.geolocation import GeoBuilder, LocationDB
from TemperatureHistogram.histogram import Histogram
from TemperatureHistogram.log_input import LogParser
from TemperatureHistogram.settings import app_settings
from TemperatureHistogram.weather import update_forecast_high_temperatures, forecast_high_temperature_list


def app_setup(func):  # TODO: Implement an asynchronous logging handler ala Logbook to increase DEBUG performance.
    """
    Basic application setup.
    """

    # Logging format
    formatter = "[TemperatureHistogram] %(asctime)s %(levelname)-s: " + "%(message)s"

    # File (DEBUG) logging
    logging.basicConfig(level=logging.DEBUG, format=formatter, filename='/data/output.log', filemode='w')

    # Console (INFO) handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(formatter))
    console_handler.setLevel(logging.INFO)

    # Logger and handlers
    logger = logging.getLogger()
    logger.addHandler(console_handler)

    # Initialize location database
    location_db = LocationDB()
    location_db.initialize_()

    return func


@app_setup
def main():
    """
    Parses log file, populates location database, and produces forecast high temperature histogram for locations.

    Always assumes log file is new, or contains new data, and thus does not check file hash, or entries found within
    existing location database.
    """

    # Announce that we're starting
    logging.info("Starting application run!")
    logging.info("Detailed DEBUG logging can be found at '/data/output.log'")

    # Process log input file and produce list of IPs (locations)
    logging.info("Starting parsing of log file.")
    log = LogParser(app_settings['log_input'], consider_multiple_ips=True)
    ip_list = log.build_ip_list()
    logging.info("Completed parsing log file.")

    # Geolocate IPs found in log file
    logging.info("Starting geolocation of IPs and writing results to location database.")
    g = GeoBuilder()
    g.build_locations(ip_list)
    logging.info("Completed geolocation of IPs and writing results to location database.")

    # Populate location forecast information
    logging.info("Starting populating location latest forecast high temperatures.")
    update_forecast_high_temperatures()
    logging.info("Completed populating location latest forecast high temperatures.")

    # Construct temperature list needed for histogram
    logging.info("Starting building of location temperature list.")
    temperature_list = forecast_high_temperature_list()
    logging.info("Completed building location temperature list.")

    # Produce histogram, and save as tab delimited file
    logging.info("Starting production of histogram.")
    h = Histogram(temperature_list)
    h.build_histogram()
    h.save_histogram()
    h.display_histogram()
    logging.info("Completed production of histogram.")

    # Announce that we're done
    logging.info("All done!")


if __name__ == '__main__':
    main()
