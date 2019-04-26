"""
Exercise histogram module.
"""

import logging
import numpy as np

from TemperatureHistogram.handlers import GracefulException
from TemperatureHistogram.settings import app_settings


class Histogram(object):
    """
    Build, save, and display a histogram produced using a list of temperatures.
    """

    def __init__(self, temperature_list):
        """

        :param temperature_list: List of temperatures.
        """
        self.temperature_list = temperature_list
        self.bins = app_settings['buckets']
        self.tsv_file = app_settings['tsv_output']
        self.histogram_array = None

        if not temperature_list:
            raise GracefulException("Unable to build location temperature list! List was empty.")

    def build_histogram(self):
        """
        Build histogram array needed for NumPy's `savetxt`.
        """
        a = np.array(self.temperature_list)  # Convert temperature list into numpy array
        freqs, bins = np.histogram(a, bins=self.bins)  # Produce histogram
        self.histogram_array = np.array(list(zip(bins[:-1], bins[1:] - 1, freqs)))  # "array_like" for `savetxt`

    def display_histogram(self):
        """
        Display previously saved histogram file.
        """
        try:
            with open(self.tsv_file, 'rt') as f:
                logging.info("Histogram tsv file as saved:\n" + str(f.read()))
        except FileNotFoundError:
            raise GracefulException(
                "File '{}' was not found! Couldn't display histogram results.".format(self.tsv_file))

    def save_histogram(self):
        """
        Save histogram as a tab delimited file.
        """
        try:
            np.savetxt(  # Save histogram and display it
                fname=self.tsv_file,
                X=self.histogram_array,
                comments="Exercise tsv content with a bucket count of {}:\n\n".format(self.bins),
                header='{}\t{}\t{}'.format("bucketMin", "bucketMax", "count"),
                fmt=['%.2f\t', '%.2f\t', '%d'],
                delimiter='\t',
                newline='\r\n')
            logging.info("Completed producing and saving histogram to '{}'.".format(self.tsv_file))
        except OSError:
            """
            If we can't save the histogram, handle exception, but after `FileNotFoundError` subclass to avoid ambiguity."
            """
            raise GracefulException("Could not save histogram to '{}'".format(self.tsv_file))
