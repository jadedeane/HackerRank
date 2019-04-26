"""
Exercise Application settings.
"""

import logging
import os
import sys
import traceback


class _LazyParamDict(dict):
    """
    Simple lazy dictionary that will populate only when lookup is done initially. Acts as basic input validator as well.
    Placeholder to avoid potential issues during tests.
    """

    def __init__(self, *args, **kw):
        if not args and not kw:
            self._populated = False
        dict.__init__(self, *args, **kw)

    def __getitem__(self, key):
        if not self._populated:
            self._populate()
        return dict.__getitem__(self, key)

    def _populate(self):
        stack = traceback.format_stack()
        if stack is not None and len(stack) >= 3:
            logging.debug("Populating setting due to reference at: {}".format(stack[-3]))
        try:
            # Required params
            params = {
                'log_input': os.environ.get('LOG_INPUT'),
                'reduce_sample_size': int(os.environ.get('REDUCE_SAMPLE_SIZE')),
                'tsv_output': os.environ.get('TSV_OUTPUT'),
                'buckets': int(os.environ.get('BUCKETS')),
                'faux_temperature_data': int(os.environ.get('FAUX_TEMPERATURE_DATA')),
                'geodb_filename': '/data/GeoLite2-City.mmdb',
                'location_db': '/data/location.db',
                'owm_api_key': os.environ.get('OWM_API_KEY'),
                'owm_rpm': int(os.environ.get('OWM_RPM'))
            }
            # Optional params
            if params['reduce_sample_size'] == 1:
                try:
                    params.update({'max_sample_size': int(os.environ.get('MAX_SAMPLE_SIZE'))})
                except Exception as e:
                    logging.error("Reduced sample size enabled, but unable to set sample size!")
                    logging.fatal(e)
            for k, v in params.items():
                dict.__setitem__(self, k, v)
            self._populated = True
        except Exception as e:
            type_, value_, traceback_ = sys.exc_info()
            name_ = os.path.split(traceback_.tb_frame.f_code.co_filename)[1]
            logging.error("Triggered {} at line {} in {}".format(type_, traceback_.tb_lineno, name_))
            logging.fatal("Invalid settings! Exception: {}".format(e))
            traceback.print_exc()
            exit(-1)


app_settings = _LazyParamDict()
