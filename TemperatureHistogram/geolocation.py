"""
Exercise geolocation module.
"""

import datetime
import geoip2.database
from ipaddress import AddressValueError
import logging
import multiprocessing
import sqlite3

from TemperatureHistogram.handlers import GracefulException
from TemperatureHistogram.settings import app_settings


class GeoBuilder(object):
    """
    Manages geolocation reference database, and populates location database 'locations' table.
    """

    def __init__(self):
        self._prepare_geo_db()

    def _prepare_geo_db(self):
        """
        Prepares geolocation reference database.
        """

        geo_db = app_settings['geodb_filename']
        logging.debug("Preparing geolocation database '{}' file.".format(geo_db))
        try:
            self.reader = geoip2.database.Reader(geo_db)
        except FileNotFoundError:
            raise GracefulException("Could not find geolocation reference database!")
        except ValueError:
            raise GracefulException("Invalid geolocation reference database!")

    def _process_ip_list_slice(self, p, list_slice):
        """
        Processes an IP list slice, and writes locations to location database.

        :param p: Multiprocess process number.
        :param list_slice: IP list slice to process.
        """

        logging.debug("Process {} started to process IP list slice containing {} IPs.".format(p, len(list_slice)))
        location_db = LocationDB()

        for ip in list_slice:

            # Pseudo schema and Default values for location entry
            ip_epoch = datetime.datetime.now().strftime('%s')  # Epoch when location was written
            geolocated = 0  # Whether or not the IP was geolocated
            latitude = 0.0  # Latitude in decimal degrees format
            longitude = 0.0  # Longitude in decimal degrees format
            city = ""  # City name
            region = ""  # ISO 3166-2 principal subdivision code
            country = ""  # ISO 3166-1 alpha-2 country code
            forecast_temperature = 0.0
            # forecast_epoch = gen_epoch(0)  # Set initial epoch to coincide with "today"
            forecast_epoch = 0  # Set initial epoch to effectively "none"

            # Geolocate IP address
            try:
                response = self.reader.city(ip)
                geolocated = 1
                latitude = response.location.latitude
                longitude = response.location.longitude
                city = response.city.name
                region = response.subdivisions.most_specific.iso_code
                country = response.country.iso_code
                logging.debug(
                    "Successfully geolocated IP address '{}' to latitude: '{}' longitude: '{})"
                    .format(ip, latitude, longitude))
            except AttributeError:
                # This is not likely to happen, but should 'geodb' object fail, handle it
                raise GracefulException(
                    "Geolocation reference database object is invalid! Database was either not found previously, and "
                    "exception handling failed, or the database is no longer locked to us.")
            except AddressValueError:
                logging.debug(
                    "Failed to geolocate IP address '{}'! IP not found in geolocation reference database."
                    .format(ip))

            # Write location to location database
            location_db.insert_(
                '''
                INSERT OR IGNORE INTO locations 
                (ip, ip_epoch, geolocated, latitude, longitude, city, region, country, 
                forecast_temperature, forecast_epoch)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                '''.format(ip),
                ip, ip_epoch,geolocated, latitude, longitude, city, region, country,
                forecast_temperature, forecast_epoch)

    def build_locations(self, ip_list):
        """
        Builds location database entry composed of geolocation information for a given list of IP addresses.

        :param ip_list: List of IP addresses
        """

        logging.debug("Geolocating IPs and building location dictionary.")

        def chunks_(l, n):
            """
            Prepare chunks for use within IP list slice.

            :param l: IP list.
            :param n: Chunk size based on CPUs.
            :return: Chunked slice.
            """

            # Not the world's ugliest list comprehension, but deserves an honorable mention
            return [l[_:_ + n] for _ in range(0, len(l), n)]

        # Slice IP list and multiprocess them
        logging.debug("Building location entries from IP list.")
        try:
            cpu_count = multiprocessing.cpu_count()
            logging.debug("Got system CPU count of {}. Starting {} processes.".format(cpu_count, cpu_count))
        except NotImplementedError:
            cpu_count = 1
            logging.warning("Unable to dynamically ascertain system CPU count. Assuming one.")
        chunk_size = round(len(ip_list) / cpu_count)
        slice_ = chunks_(ip_list, int(chunk_size))
        process_list = []
        for i, list_slice in enumerate(slice_):
            process = multiprocessing.Process(target=self._process_ip_list_slice, args=(i, list_slice))
            process_list.append(process)
        for process in process_list:
            process.start()
        for process in process_list:
            process.join()
        logging.info("Populated location database table with geolocated IPs.")


class LocationDB(object):  # TODO: Consolidate exception handling
    """
    Reusable location database wrapper.
    """

    def __init__(self):
        self.db_file = app_settings['location_db']

    def initialize_(self):
        """
        Initialize location database and 'locations' table.
        """

        try:
            """
            Attempt connection to location database. If the database or 'locations' table do not exist, they will be 
            created in an idempotent fashion.
            """
            with sqlite3.connect(self.db_file) as connection:
                cursor = connection.cursor()
                cursor.execute(
                    '''
                    CREATE TABLE IF NOT EXISTS locations (
                    ip TEXT PRIMARY KEY, ip_epoch INTEGER,
                    geolocated INTEGER, latitude REAL, longitude REAL, city TEXT, region TEXT, country TEXT, 
                    forecast_temperature REAL, forecast_epoch INTEGER 
                    )
                    ''')
                connection.commit()
        except sqlite3.OperationalError as e:
            logging.error("Locations database exception: {}".format(e))
            raise GracefulException("Unable to setup location database!")

    def select_(self, sql):
        """
        Read (fetch) row from table.
        :param sql: SQL query.
        :return: Table rows matching query.
        """

        try:
            with sqlite3.connect(self.db_file) as connection:
                cursor = connection.cursor()
                cursor.execute('{}'.format(sql))
                rows = cursor.fetchall()
                return rows
        except sqlite3.OperationalError as e:
            logging.error("Locations database exception: {}".format(e))
            raise GracefulException("Locations database failure!")

    def insert_(self, sql, *args):
        """
        Write (insert) row to table.

        :param sql: SQL statement.
        :param args: Table values vars.
        """

        try:
            with sqlite3.connect(self.db_file) as connection:
                cursor = connection.cursor()
                cursor.execute('{}'.format(sql), args)
                connection.commit()
        except sqlite3.IntegrityError or sqlite3.ProgrammingError or sqlite3.OperationalError as e:
            logging.error("Locations database exception: {}".format(e))
            raise GracefulException("Locations database failure!")

    def update_(self, sql):
        """
        Update row in table.

        :param sql: SQL statement.
        """

        try:
            with sqlite3.connect(self.db_file) as connection:
                cursor = connection.cursor()
                cursor.execute('{}'.format(sql))
                connection.commit()
        except sqlite3.IntegrityError or sqlite3.ProgrammingError or sqlite3.OperationalError as e:
            logging.error("Locations database exception: {}".format(e))
            raise GracefulException("Locations database failure!")


def gen_epoch(days_offset):
    """
    Provides epoch for a given day.

    :param days_offset: Forecast offset in days. This would previously help calculate more advanced forecast epochs, but
    keeping it around for epoch uniformity, and reusable calculation.
        Example: No offset would return epoch for current day's forecast, while '1' would indicate tomorrow or "next
        day" forecast.
    :return: Returns epoch seconds as integer.
    """

    # Calculate current epoch
    date = datetime.datetime.today().date()
    epoch = int(date.strftime('%s'))

    # Add 24hrs in seconds to epoch for each offset day
    for _ in range(0, days_offset):
        epoch += 86400

    return epoch
