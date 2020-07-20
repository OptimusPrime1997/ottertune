#
# OtterTune - target_objective.py
#
# Copyright (c) 2017-18, Carnegie Mellon University Database Group
#
import logging

from ..base.target_objective import BaseThroughput, BaseTargetObjective, BaseThroughput_Mix
from website.types import DBMSType
from ..base.target_objective import target_objectives, LESS_IS_BETTER, MORE_IS_BETTER, LATENCY_99, THROUGHPUT_MIX
LOG = logging.getLogger(__name__)


class Latency99TH(BaseTargetObjective):
    def __init__(self):
        super().__init__(name=LATENCY_99,
                         pprint='99th Latency',
                         unit='seconds',
                         short_unit='s',
                         improvement=LESS_IS_BETTER)

    def compute(self, metrics, observation_time):
        # LOG.warn('Postgres.target_objective compute:{}={},{}'.format(
        #     LATENCY_99, (LATENCY_99 in metrics),
        #     metrics[list(metrics.keys())[-1]]))
        LOG.info(
            "postgres.target_objective LATENCY_99={},latency in metrics={},99th_lat(ms)In={}"
            .format(LATENCY_99, (LATENCY_99 in metrics),
                    (' 99th_lat(ms)' in metrics)))
        return float(metrics[LATENCY_99])


target_objective_list = tuple((
    DBMSType.POSTGRES, target_obj
) for target_obj in [  # pylint: disable=invalid-name
    BaseThroughput(transactions_counter='pg_stat_database.xact_commit'),
    Latency99TH()
    # BaseThroughput_Mix(transactions_counter='pg_stat_database.xact_commit')
])
