#
# OtterTune - postgres.py
#
# Copyright (c) 2017-18, Carnegie Mellon University Database Group
#

import re

from .base import BaseParser
from website.types import KnobUnitType
from website.utils import ConversionUtil


class PostgresParser(BaseParser):

    def __init__(self, dbms_obj):
        super().__init__(dbms_obj)
        self.valid_true_val = ("on", "true", "yes", 1)
        self.valid_false_val = ("off", "false", "no", 0)

    POSTGRES_BASE_KNOBS = {
        'global.data_directory': None,
        'global.hba_file': None,
        'global.ident_file': None,
        'global.external_pid_file': None,
        'global.listen_addresses': None,
        'global.port': None,
        'global.max_connections': None,
        'global.unix_socket_directories': None,
        'global.log_line_prefix': '%t [%p-%l] %q%u@%d ',
        'global.track_counts': 'on',
        'global.track_io_timing': 'on',
        'global.autovacuum': 'on',
        'global.default_text_search_config': 'pg_catalog.english',
    }

    @property
    def base_configuration_settings(self):
        return dict(self.POSTGRES_BASE_KNOBS)

    @property
    def knob_configuration_filename(self):
        return 'postgresql.conf'

    @property
    def transactions_counter(self):
        return 'pg_stat_database.xact_commit'

    @property
    def latency_timer(self):
        return 'pg_stat_database.xact_commit'

    def convert_integer(self, int_value, metadata):
        converted = None
        try:
            converted = super().convert_integer(int_value, metadata)
        except ValueError:
            if metadata.unit == KnobUnitType.BYTES:
                converted = ConversionUtil.get_raw_size(
                    int_value, system=ConversionUtil.DEFAULT_BYTES_SYSTEM)
            elif metadata.unit == KnobUnitType.MILLISECONDS:
                converted = ConversionUtil.get_raw_size(
                    int_value, system=ConversionUtil.DEFAULT_TIME_SYSTEM)
            else:
                raise Exception(
                    'Unknown unit type: {}'.format(metadata.unit))
        if converted is None:
            raise Exception('Invalid integer format for {}: {}'.format(
                metadata.name, int_value))
        return converted

    def format_integer(self, int_value, metadata):
        int_value = int(round(int_value))
        if metadata.unit != KnobUnitType.OTHER and int_value > 0:
            if metadata.unit == KnobUnitType.BYTES:
                int_value = ConversionUtil.get_human_readable(
                    int_value, ConversionUtil.DEFAULT_BYTES_SYSTEM)
            elif metadata.unit == KnobUnitType.MILLISECONDS:
                int_value = ConversionUtil.get_human_readable(
                    int_value, ConversionUtil.DEFAULT_TIME_SYSTEM)
            else:
                raise Exception(
                    'Invalid unit type for {}: {}'.format(
                        metadata.name, metadata.unit))
        else:
            int_value = super().format_integer(int_value, metadata)
        return int_value

    def parse_version_string(self, version_string):
        dbms_version = version_string.split(',')[0]
        return re.search(r'\d+\.\d+(?=\.\d+)', dbms_version).group(0)
