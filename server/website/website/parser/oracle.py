#
# OtterTune - oracle.py
#
# Copyright (c) 2017-18, Carnegie Mellon University Database Group
#

from .base import BaseParser


class OracleParser(BaseParser):

    def __init__(self, dbms_obj):
        super().__init__(dbms_obj)
        self.true_value = 'TRUE'
        self.false_value = 'FALSE'

    ORACLE_BASE_KNOBS = {
    }

    @property
    def base_configuration_settings(self):
        return dict(self.ORACLE_BASE_KNOBS)

    @property
    def knob_configuration_filename(self):
        return 'initorcldb.ora'

    @property
    def transactions_counter(self):
        return 'global.user commits'

    @property
    def latency_timer(self):
        return 'global.user commits'

    def parse_version_string(self, version_string):
        return version_string
