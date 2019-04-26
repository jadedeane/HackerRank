"""
Exercise log input module.
"""

from ipaddress import AddressValueError, ip_address
import logging
import re

from TemperatureHistogram.handlers import GracefulException
from TemperatureHistogram.settings import app_settings


class LogParser(object):
    """
    Parse log input file and produce list of public IP addresses that can be geolocated.
    """

    def __init__(self, filename, consider_multiple_ips=False):
        self.filename = filename
        self.multiple_ips = consider_multiple_ips

    @staticmethod
    def _eval_ip(ip, n):
        """
        Evaluate IP address for inclusion within the IP list.

        :param ip: IPv4 host address.
        :param n: Line number IP being evaluated was found on.
        :return: Returns whether or not the IP should be considered as True or False.
        """

        try:
            if ip_address(ip).is_global:
                logging.debug(
                    "IP address '{} in line {} is public. Adding to IP list.".format(ip, n))
                return True
            else:
                logging.debug(
                    "IP address '{}' in line {} isn't public. Can't add to IP list".format(ip, n))
                return False
        except AddressValueError:
            logging.debug("IP address '{}' in line {} is an invalid format.".format(ip, n))
            return False

    def _eval_log_file(self, filename, multiple_ips):
        """
        Evaluate log and produce IP list.

        :param filename: Log input filename.
        :param multiple_ips: Whether (True) or not (False) to consider multiple unique IPs within a single log entry.
        :return: List of public IP addresses.
        """

        ip_list = []
        logging.debug("Evaluating log file '" + filename + "'.")
        if app_settings['reduce_sample_size'] == 1:
            reduced_sample = True
            max_sample = app_settings['max_sample_size']
        else:
            reduced_sample = False
            max_sample = float('inf')
        try:
            with open(filename, 'rt') as f:
                for n, l in enumerate(f, 1):
                    if reduced_sample and n >= max_sample:
                        logging.info("Reached reduced sample size limit of {} log lines.".format(max_sample))
                        break
                    try:
                        m = re.findall(r'[0-9]+(?:\.[0-9]+){3}', l)  # Find IP(s) in line
                        if m:
                            m = list(set(m))  # Remove duplicates
                            if len(m) > 1:
                                if multiple_ips:
                                    logging.debug("Multiple IPs ('{}') in line {}".format(m, n))
                                    for ip in m:
                                        if staticmethod(self._eval_ip(ip, n)):
                                            ip_list.append(ip)
                                else:
                                    logging.debug("Conflicting IPs ('{}') in line {}".format(m, n))
                                    pass
                            else:
                                ip, = m
                                logging.debug("Found IP '{}' in line {}".format(ip, n))
                                if staticmethod(self._eval_ip(ip, n)):
                                    ip_list.append(ip)
                    except TypeError:
                        logging.debug("Unable to process line {}.".format(n))

                # Remove duplicates, sort list pseudo numerically, return list
                ips_total = len(ip_list)
                ip_list = list(set(ip_list))
                ips_unique = len(ip_list)
                ip_list.sort()
                logging.info(
                    "Parsed {} log entries, evaluated {} IPs, and built list composed of {} unique public IPs."
                    .format(n, ips_total, ips_unique))
                log_percent = round(((ips_total / n) * 100), 2)
                ips_percent = round(((ips_unique / ips_total) * 100), 2)
                logging.info(
                    "{}% of log entries contained an IP address, and of those {}% are geolocation eligible."
                    .format(log_percent, ips_percent))
                logging.debug("Produced IP list:\n{}".format(ip_list))
                return ip_list

        except FileNotFoundError:
            raise GracefulException("File '{}' was not found!".format(filename))

    def build_ip_list(self):
        ip_list = self._eval_log_file(self.filename, self.multiple_ips)
        if not ip_list:
            raise GracefulException("Parsing and evaluating log produced no geolocation results!")
        return ip_list
