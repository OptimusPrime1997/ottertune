import paramiko
import json
from collections import OrderedDict

from sklearn.datasets import make_regression
from sklearn.linear_model import Lasso, LassoCV
import numpy as np


def train_lasso():
    reg_data, reg_target = make_regression(
        n_samples=200, n_features=500, n_informative=5, noise=5)
    print("reg_data.shape:", reg_data.shape)
    print("reg_target.shape:", reg_target.shape)

    lasso = Lasso(alpha=1, copy_X=True, fit_intercept=True, max_iter=1000,
                  normalize=False, positive=False, precompute=False,
                  random_state=None, selection='cyclic',
                  tol=0.0001, warm_start=False)
    lasso.fit(reg_data, reg_target)
    print("alpha=1 lasso nozero:", np.sum(lasso.coef_ != 0))

    lasso_0 = Lasso(0)
    lasso_0.fit(reg_data, reg_target)
    print("alpha=0 lasso nozero:", np.sum(lasso_0.coef_ != 0))

    lassocv = LassoCV()
    lassocv.fit(reg_data, reg_target)
    print(np.sum(lassocv.coef_))
    lassocv1 = LassoCV(alphas=None, copy_X=True, cv=None, eps=0.001,
                       fit_intercept=True, max_iter=1000,
                       n_alphas=100, n_jobs=1,
                       normalize=False, positive=False,
                       precompute='auto', random_state=None,
                       selection='cyclic', tol=0.0001,
                       verbose=False)
    lassocv1.fit(reg_data, reg_target)
    print(lassocv1.alpha_)
    print(lassocv1.coef_[:5])
    print(np.sum(lassocv1.coef_ != 0))
    mask = (lassocv1.coef_ != 0)
    new_reg_data = reg_data[:, mask]
    print(new_reg_data.shape)


# ===================================================


def remote_connect():
    # 创建SSH对象
    ssh = paramiko.SSHClient()
    # 允许连接不在know_hosts文件中的主机
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # 连接服务器
    ssh.connect(hostname='192.168.122.77', port=22,
                username='root', password='123')
    # 执行命令  stdout命令结果，stderr错误
    stdin, stdout, stderr = ssh.exec_command('df -hl')
    # 获取命令结果
    result = stdout.read()
    print(result)
    # 关闭连接
    ssh.close()


def test_json():
    data = '''{
    "99th_lat_ms": 573.907,
    "pg_stat_archiver.archived_count": 0.0,
    "pg_stat_archiver.failed_count": 0.0,
    "pg_stat_bgwriter.buffers_alloc": 6389.866666666667,
    "pg_stat_bgwriter.buffers_backend": 0.0,
    "pg_stat_bgwriter.buffers_backend_fsync": 0.0,
    "pg_stat_bgwriter.buffers_checkpoint": 0.0,
    "pg_stat_bgwriter.buffers_clean": 0.0,
    "pg_stat_bgwriter.checkpoint_sync_time": 0.0,
    "pg_stat_bgwriter.checkpoint_write_time": 0.0,
    "pg_stat_bgwriter.checkpoints_req": 0.0,
    "pg_stat_bgwriter.checkpoints_timed": 0.0,
    "pg_stat_bgwriter.maxwritten_clean": 0.0,
    "pg_stat_database.blk_read_time": 0.0,
    "pg_stat_database.blk_write_time": 0.0,
    "pg_stat_database.blks_hit": 159266.06666666668,
    "pg_stat_database.blks_read": 6387.966666666666,
    "pg_stat_database.conflicts": 0.0,
    "pg_stat_database.deadlocks": 0.0,
    "pg_stat_database.temp_bytes": 0.0,
    "pg_stat_database.temp_files": 0.0,
    "pg_stat_database.tup_deleted": 249.9,
    "pg_stat_database.tup_fetched": 36872.6,
    "pg_stat_database.tup_inserted": 3483.766666666667,
    "pg_stat_database.tup_returned": 39656.73333333333,
    "pg_stat_database.tup_updated": 6723.466666666666,
    "pg_stat_database.xact_commit": 611.9,
    "pg_stat_database.xact_rollback": 2.8666666666666667,
    "pg_stat_database_conflicts.confl_bufferpin": 0.0,
    "pg_stat_database_conflicts.confl_deadlock": 0.0,
    "pg_stat_database_conflicts.confl_lock": 0.0,
    "pg_stat_database_conflicts.confl_snapshot": 0.0,
    "pg_stat_database_conflicts.confl_tablespace": 0.0,
    "pg_stat_user_indexes.idx_scan": 18967.666666666668,
    "pg_stat_user_indexes.idx_tup_fetch": 28887.566666666666,
    "pg_stat_user_indexes.idx_tup_read": 31510.366666666665,
    "pg_stat_user_tables.analyze_count": 0.0,
    "pg_stat_user_tables.autoanalyze_count": 0.06666666666666667,
    "pg_stat_user_tables.autovacuum_count": 0.06666666666666667,
    "pg_stat_user_tables.idx_scan": 23871.066666666666,
    "pg_stat_user_tables.idx_tup_fetch": 33790.96666666667,
    "pg_stat_user_tables.n_dead_tup": 253737.0,
    "pg_stat_user_tables.n_live_tup": 107858321.0,
    "pg_stat_user_tables.n_mod_since_analyze": 576637.0,
    "pg_stat_user_tables.n_tup_del": 249.66666666666666,
    "pg_stat_user_tables.n_tup_hot_upd": 3905.866666666667,
    "pg_stat_user_tables.n_tup_ins": 3482.233333333333,
    "pg_stat_user_tables.n_tup_upd": 6722.8,
    "pg_stat_user_tables.seq_scan": 0.0,
    "pg_stat_user_tables.seq_tup_read": 0.0,
    "pg_stat_user_tables.vacuum_count": 0.0,
    "pg_statio_user_indexes.idx_blks_hit": 74309.1,
    "pg_statio_user_indexes.idx_blks_read": 1443.1,
    "pg_statio_user_tables.heap_blks_hit": 62999.9,
    "pg_statio_user_tables.heap_blks_read": 4391.933333333333,
    "pg_statio_user_tables.idx_blks_hit": 91629.73333333334,
    "pg_statio_user_tables.idx_blks_read": 1989.1333333333334,
    "pg_statio_user_tables.tidx_blks_hit": 0.0,
    "pg_statio_user_tables.tidx_blks_read": 0.0,
    "pg_statio_user_tables.toast_blks_hit": 0.0,
    "pg_statio_user_tables.toast_blks_read": 0.0,
    "throughput_txn_per_sec": 611.9
  }'''

    metric_data = json.loads(data, encoding='UTF-8',
                             object_pairs_hook=OrderedDict)
    print(metric_data)
    print(metric_data['99th_lat_ms'])


def test_loads():
    load_data = '''{\n    "99th_lat_ms": 623.133,\n    "pg_stat_archiver.archived_count": 0.0,\n    "pg_stat_archiver.failed_count": 0.0,\n    "pg_stat_bgwriter.buffers_alloc": 6381.1,\n    "pg_stat_bgwriter.buffers_backend": 0.0,\n    "pg_stat_bgwriter.buffers_backend_fsync": 0.0,\n    "pg_stat_bgwriter.buffers_checkpoint": 0.0,\n    "pg_stat_bgwriter.buffers_clean": 0.0,\n    "pg_stat_bgwriter.checkpoint_sync_time": 0.0,\n    "pg_stat_bgwriter.checkpoint_write_time": 0.0,\n    "pg_stat_bgwriter.checkpoints_req": 0.0,\n    "pg_stat_bgwriter.checkpoints_timed": 0.0,\n    "pg_stat_bgwriter.maxwritten_clean": 0.0,\n    "pg_stat_database.blk_read_time": 0.0,\n    "pg_stat_database.blk_write_time": 0.0,\n    "pg_stat_database.blks_hit": 154975.33333333334,\n    "pg_stat_database.blks_read": 6381.1,\n    "pg_stat_database.conflicts": 0.0,\n    "pg_stat_database.deadlocks": 0.0,\n    "pg_stat_database.temp_bytes": 0.0,\n    "pg_stat_database.temp_files": 0.0,\n    "pg_stat_database.tup_deleted": 223.56666666666666,\n    "pg_stat_database.tup_fetched": 34428.6,\n    "pg_stat_database.tup_inserted": 3308.1,\n    "pg_stat_database.tup_returned": 39590.433333333334,\n    "pg_stat_database.tup_updated": 6217.433333333333,\n    "pg_stat_database.xact_commit": 575.0666666666667,\n    "pg_stat_database.xact_rollback": 2.5,\n    "pg_stat_database_conflicts.confl_bufferpin": 0.0,\n    "pg_stat_database_conflicts.confl_deadlock": 0.0,\n    "pg_stat_database_conflicts.confl_lock": 0.0,\n    "pg_stat_database_conflicts.confl_snapshot": 0.0,\n    "pg_stat_database_conflicts.confl_tablespace": 0.0,\n    "pg_stat_user_indexes.idx_scan": 17807.6,\n    "pg_stat_user_indexes.idx_tup_fetch": 26524.3,\n    "pg_stat_user_indexes.idx_tup_read": 29304.566666666666,\n    "pg_stat_user_tables.analyze_count": 0.0,\n    "pg_stat_user_tables.autoanalyze_count": 0.06666666666666667,\n    "pg_stat_user_tables.autovacuum_count": 0.06666666666666667,\n    "pg_stat_user_tables.idx_scan": 22436.0,\n    "pg_stat_user_tables.idx_tup_fetch": 31467.4,\n    "pg_stat_user_tables.n_dead_tup": 142909.0,\n    "pg_stat_user_tables.n_live_tup": 107761516.0,\n    "pg_stat_user_tables.n_mod_since_analyze": 286732.0,\n    "pg_stat_user_tables.n_tup_del": 223.33333333333334,\n    "pg_stat_user_tables.n_tup_hot_upd": 2609.9666666666667,\n    "pg_stat_user_tables.n_tup_ins": 3307.866666666667,\n    "pg_stat_user_tables.n_tup_upd": 6216.766666666666,\n    "pg_stat_user_tables.seq_scan": 12.6,\n    "pg_stat_user_tables.seq_tup_read": 2520.0,\n    "pg_stat_user_tables.vacuum_count": 0.0,\n    "pg_statio_user_indexes.idx_blks_hit": 72438.5,\n    "pg_statio_user_indexes.idx_blks_read": 1472.3,\n    "pg_statio_user_tables.heap_blks_hit": 61340.2,\n    "pg_statio_user_tables.heap_blks_read": 4339.633333333333,\n    "pg_statio_user_tables.idx_blks_hit": 89070.06666666667,\n    "pg_statio_user_tables.idx_blks_read": 2034.9666666666667,\n    "pg_statio_user_tables.tidx_blks_hit": 0.0,\n    "pg_statio_user_tables.tidx_blks_read": 0.0,\n    "pg_statio_user_tables.toast_blks_hit": 0.0,\n    "pg_statio_user_tables.toast_blks_read": 0.0,\n    "throughput_txn_per_sec": 575.0666666666667\n}', '{\n    "99th_lat_ms": 573.907,\n    "pg_stat_archiver.archived_count": 0.0,\n    "pg_stat_archiver.failed_count": 0.0,\n    "pg_stat_bgwriter.buffers_alloc": 6389.866666666667,\n    "pg_stat_bgwriter.buffers_backend": 0.0,\n    "pg_stat_bgwriter.buffers_backend_fsync": 0.0,\n    "pg_stat_bgwriter.buffers_checkpoint": 0.0,\n    "pg_stat_bgwriter.buffers_clean": 0.0,\n    "pg_stat_bgwriter.checkpoint_sync_time": 0.0,\n    "pg_stat_bgwriter.checkpoint_write_time": 0.0,\n    "pg_stat_bgwriter.checkpoints_req": 0.0,\n    "pg_stat_bgwriter.checkpoints_timed": 0.0,\n    "pg_stat_bgwriter.maxwritten_clean": 0.0,\n    "pg_stat_database.blk_read_time": 0.0,\n    "pg_stat_database.blk_write_time": 0.0,\n    "pg_stat_database.blks_hit": 159266.06666666668,\n    "pg_stat_database.blks_read": 6387.966666666666,\n    "pg_stat_database.conflicts": 0.0,\n    "pg_stat_database.deadlocks": 0.0,\n    "pg_stat_database.temp_bytes": 0.0,\n    "pg_stat_database.temp_files": 0.0,\n    "pg_stat_database.tup_deleted": 249.9,\n    "pg_stat_database.tup_fetched": 36872.6,\n    "pg_stat_database.tup_inserted": 3483.766666666667,\n    "pg_stat_database.tup_returned": 39656.73333333333,\n    "pg_stat_database.tup_updated": 6723.466666666666,\n    "pg_stat_database.xact_commit": 611.9,\n    "pg_stat_database.xact_rollback": 2.8666666666666667,\n    "pg_stat_database_conflicts.confl_bufferpin": 0.0,\n    "pg_stat_database_conflicts.confl_deadlock": 0.0,\n    "pg_stat_database_conflicts.confl_lock": 0.0,\n    "pg_stat_database_conflicts.confl_snapshot": 0.0,\n    "pg_stat_database_conflicts.confl_tablespace": 0.0,\n    "pg_stat_user_indexes.idx_scan": 18967.666666666668,\n    "pg_stat_user_indexes.idx_tup_fetch": 28887.566666666666,\n    "pg_stat_user_indexes.idx_tup_read": 31510.366666666665,\n    "pg_stat_user_tables.analyze_count": 0.0,\n    "pg_stat_user_tables.autoanalyze_count": 0.06666666666666667,\n    "pg_stat_user_tables.autovacuum_count": 0.06666666666666667,\n    "pg_stat_user_tables.idx_scan": 23871.066666666666,\n    "pg_stat_user_tables.idx_tup_fetch": 33790.96666666667,\n    "pg_stat_user_tables.n_dead_tup": 253737.0,\n    "pg_stat_user_tables.n_live_tup": 107858321.0,\n    "pg_stat_user_tables.n_mod_since_analyze": 576637.0,\n    "pg_stat_user_tables.n_tup_del": 249.66666666666666,\n    "pg_stat_user_tables.n_tup_hot_upd": 3905.866666666667,\n    "pg_stat_user_tables.n_tup_ins": 3482.233333333333,\n    "pg_stat_user_tables.n_tup_upd": 6722.8,\n    "pg_stat_user_tables.seq_scan": 0.0,\n    "pg_stat_user_tables.seq_tup_read": 0.0,\n    "pg_stat_user_tables.vacuum_count": 0.0,\n    "pg_statio_user_indexes.idx_blks_hit": 74309.1,\n    "pg_statio_user_indexes.idx_blks_read": 1443.1,\n    "pg_statio_user_tables.heap_blks_hit": 62999.9,\n    "pg_statio_user_tables.heap_blks_read": 4391.933333333333,\n    "pg_statio_user_tables.idx_blks_hit": 91629.73333333334,\n    "pg_statio_user_tables.idx_blks_read": 1989.1333333333334,\n    "pg_statio_user_tables.tidx_blks_hit": 0.0,\n    "pg_statio_user_tables.tidx_blks_read": 0.0,\n    "pg_statio_user_tables.toast_blks_hit": 0.0,\n    "pg_statio_user_tables.toast_blks_read": 0.0,\n    "throughput_txn_per_sec": 611.9\n}'''

    metric_datas = {r.pk: JSONUtil.loads(r.metric_data.data)}


if __name__ == "__main__":
    # pass
    # test_json()
    train_lasso()
