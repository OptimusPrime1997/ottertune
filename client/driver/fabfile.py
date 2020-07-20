#
# OtterTune - fabfile.py
#
# Copyright (c) 2017-18, Carnegie Mellon University Database Group
#
'''
Created on Mar 23, 2018

@author: bohan
'''
import glob
import json
import os
import re
import time
from collections import OrderedDict
from multiprocessing import Process, Pool
import time
import json

import logging
from logging.handlers import RotatingFileHandler

import requests
from fabric.api import env, lcd, local, settings, show, task
from fabric.state import output as fabric_output

from utils import (file_exists, get, get_content, load_driver_conf, parse_bool,
                   put, run, run_sql_script, sudo, FabricException)
import paramiko

CONTINUE_COUNT = 'continue_count'
IS_CONVERGE = False
VM_IP = '192.168.122.131'
POSTGRESQL_PORT = 5432
IS_SYSBENCH = True
# ----------------sysbench workload enumeration start---
RO = 'ro'
RW = 'rw'
WO = 'wo'
# ----------------sysbench workload enumeration end---
# set sysbench workload
SYSBENCH_WORKLOAD = RO

with open('driver_config.json', 'r') as f:
    CONF = json.load(f)
# Loads the driver config file (defaults to driver_config.py)
dconf = load_driver_conf()  # pylint: disable=invalid-name
SMOOTH_COUNT = dconf.SMOOTH_COUNT
# Fabric settings
fabric_output.update({
    'running': True,
    'stdout': True,
})
env.abort_exception = FabricException
env.hosts = [dconf.LOGIN]

# Create local directories
for _d in (dconf.RESULT_DIR, dconf.LOG_DIR, dconf.TEMP_DIR):
    os.makedirs(_d, exist_ok=True)

# Configure logging
LOG = logging.getLogger(__name__)
LOG.setLevel(getattr(logging, dconf.LOG_LEVEL, logging.DEBUG))
Formatter = logging.Formatter(  # pylint: disable=invalid-name
    fmt='%(asctime)s [%(funcName)s:%(lineno)03d] %(levelname)-5s: %(message)s',
    datefmt='%m-%d-%Y %H:%M:%S')
ConsoleHandler = logging.StreamHandler()  # pylint: disable=invalid-name
ConsoleHandler.setFormatter(Formatter)
LOG.addHandler(ConsoleHandler)
FileHandler = RotatingFileHandler(  # pylint: disable=invalid-name
    dconf.DRIVER_LOG,
    maxBytes=50000,
    backupCount=2)
FileHandler.setFormatter(Formatter)
LOG.addHandler(FileHandler)


@task
def check_disk_usage():
    partition = dconf.DATABASE_DISK
    disk_use = 0
    if partition:
        cmd = "df -h {}".format(partition)
        out = run(cmd).splitlines()[1]
        m = re.search(r'\d+(?=%)', out)
        if m:
            disk_use = int(m.group(0))
        LOG.info("Current Disk Usage: %s%s", disk_use, '%')
    return disk_use


@task
def check_remote_disk_usage():
    partition = CONF['database_disk']
    disk_use = 0
    cmd = "df -h {}".format(partition)
    out = remote_exec(VM_IP, cmd).splitlines()[1]
    m = re.search('\d+(?=%)', out)
    if m:
        disk_use = int(m.group(0))
    LOG.info("Current remote Disk Usage: %s%s", disk_use, '%')
    return disk_use


@task
def check_memory_usage():
    run('free -m -h')


@task
def create_controller_config():
    if dconf.DB_TYPE == 'postgres':
        dburl_fmt = 'jdbc:postgresql://{host}:{port}/{db}'.format
    elif dconf.DB_TYPE == 'oracle':
        dburl_fmt = 'jdbc:oracle:thin:@{host}:{port}:{db}'.format
    else:
        raise Exception("Database Type {} Not Implemented !".format(
            dconf.DB_TYPE))

    config = dict(database_type=dconf.DB_TYPE,
                  database_url=dburl_fmt(host=dconf.DB_HOST,
                                         port=dconf.DB_PORT,
                                         db=dconf.DB_NAME),
                  username=dconf.DB_USER,
                  password=dconf.DB_PASSWORD,
                  upload_code='DEPRECATED',
                  upload_url='DEPRECATED',
                  workload_name=dconf.OLTPBENCH_BENCH)

    with open(dconf.CONTROLLER_CONFIG, 'w') as f:
        json.dump(config, f, indent=2)


@task
def restart_database():
    if dconf.DB_TYPE == 'postgres':
        if dconf.HOST_CONN == 'docker':
            # Restarting the docker container here is the cleanest way to do it
            # becaues there's no init system running and the only process running
            # in the container is postgres itself
            local('docker restart {}'.format(dconf.CONTAINER_NAME))
        else:
            sudo('pg_ctl -D {} -w -t 600 restart -m fast'.format(
                dconf.PG_DATADIR),
                 user=dconf.ADMIN_USER,
                 capture=False)
    elif dconf.DB_TYPE == 'oracle':
        db_log_path = os.path.join(
            os.path.split(dconf.DB_CONF)[0], 'startup.log')
        local_log_path = os.path.join(dconf.LOG_DIR, 'startup.log')
        local_logs_path = os.path.join(dconf.LOG_DIR, 'startups.log')
        run_sql_script('restartOracle.sh', db_log_path)
        get(db_log_path, local_log_path)
        with open(local_log_path, 'r') as fin, open(local_logs_path,
                                                    'a') as fout:
            lines = fin.readlines()
            for line in lines:
                if line.startswith('ORACLE instance started.'):
                    return True
                if not line.startswith('SQL>'):
                    fout.write(line)
            fout.write('\n')
        return False
    else:
        raise Exception("Database Type {} Not Implemented !".format(
            dconf.DB_TYPE))
    return True


@task
def restart_remote_database():
    if CONF['database_type'] == 'postgres':
        cmd = 'echo "123" | sudo -S service postgresql restart'
    elif CONF['database_type'] == 'oracle':
        driver_folder = CONF['oltpbench_log'][:CONF['oltpbench_log'].
                                              rfind('/') + 1]
        cmd = ('cd {} && sh oracleScripts/shutdownOracle.sh '
               '&& sh oracleScripts/startupOracle.sh').format(driver_folder)
    else:
        raise Exception("Database Type {} Not Implemented !".format(
            CONF['database_type']))
    remote_exec(VM_IP, cmd)
    time.sleep(3)
    return check_port(VM_IP, POSTGRESQL_PORT)


@task
def drop_database():
    if dconf.DB_TYPE == 'postgres':
        run("PGPASSWORD={} dropdb -e --if-exists {} -U {} -h {}".format(
            dconf.DB_PASSWORD, dconf.DB_NAME, dconf.DB_USER, dconf.DB_HOST))
    else:
        raise Exception("Database Type {} Not Implemented !".format(
            dconf.DB_TYPE))


@task
def create_database():
    if dconf.DB_TYPE == 'postgres':
        run("PGPASSWORD={} createdb -e {} -U {} -h {}".format(
            dconf.DB_PASSWORD, dconf.DB_NAME, dconf.DB_USER, dconf.DB_HOST))
    else:
        raise Exception("Database Type {} Not Implemented !".format(
            dconf.DB_TYPE))


@task
def create_user():
    if dconf.DB_TYPE == 'postgres':
        sql = "CREATE USER {} SUPERUSER PASSWORD '{}';".format(
            dconf.DB_USER, dconf.DB_PASSWORD)
        run("PGPASSWORD={} psql -c \\\"{}\\\" -U postgres -h {}".format(
            dconf.DB_PASSWORD, sql, dconf.DB_HOST))
    elif dconf.DB_TYPE == 'oracle':
        run_sql_script('createUser.sh', dconf.DB_USER, dconf.DB_PASSWORD)
    else:
        raise Exception("Database Type {} Not Implemented !".format(
            dconf.DB_TYPE))


@task
def drop_user():
    if dconf.DB_TYPE == 'postgres':
        sql = "DROP USER IF EXISTS {};".format(dconf.DB_USER)
        run("PGPASSWORD={} psql -c \\\"{}\\\" -U postgres -h {}".format(
            dconf.DB_PASSWORD, sql, dconf.DB_HOST))
    elif dconf.DB_TYPE == 'oracle':
        run_sql_script('dropUser.sh', dconf.DB_USER)
    else:
        raise Exception("Database Type {} Not Implemented !".format(
            dconf.DB_TYPE))


@task
def reset_conf():
    change_conf()


@task
def clean_remote_conf():
    driver_folder = CONF['oltpbench_log'][:CONF['oltpbench_log'].rfind('/') +
                                          1]
    clean_cmd = " echo '123' | sudo -S echo '' > {}/next_config".format(
        driver_folder)
    local(clean_cmd)
    change_remote_conf()


@task
def change_conf(next_conf=None):
    signal = "# configurations recommended by ottertune:\n"
    next_conf = next_conf or {}

    tmp_conf_in = os.path.join(dconf.TEMP_DIR,
                               os.path.basename(dconf.DB_CONF) + '.in')
    get(dconf.DB_CONF, tmp_conf_in)
    with open(tmp_conf_in, 'r') as f:
        lines = f.readlines()

    if signal not in lines:
        lines += ['\n', signal]

    signal_idx = lines.index(signal)
    lines = lines[0:signal_idx + 1]
    if dconf.BASE_DB_CONF:
        assert isinstance(dconf.BASE_DB_CONF, dict), \
            (type(dconf.BASE_DB_CONF), dconf.BASE_DB_CONF)
        base_conf = [
            '{} = {}\n'.format(*c) for c in sorted(dconf.BASE_DB_CONF.items())
        ]
        lines.extend(base_conf)

    if isinstance(next_conf, str):
        with open(next_conf, 'r') as f:
            recommendation = json.load(
                f, encoding="UTF-8",
                object_pairs_hook=OrderedDict)['recommendation']
    else:
        recommendation = next_conf

    assert isinstance(recommendation, dict)

    for name, value in recommendation.items():
        if dconf.DB_TYPE == 'oracle' and isinstance(value, str):
            value = value.strip('B')
        lines.append('{} = {}\n'.format(name, value))
    lines.append('\n')

    tmp_conf_out = os.path.join(dconf.TEMP_DIR,
                                os.path.basename(dconf.DB_CONF) + '.out')
    with open(tmp_conf_out, 'w') as f:
        f.write(''.join(lines))

    sudo('echo "123" | sudo -S cp {0} {0}.ottertune.bak'.format(dconf.DB_CONF))
    put(tmp_conf_out, dconf.DB_CONF, use_sudo=False)
    local('echo "123" | sudo -S rm -f {} {}'.format(tmp_conf_in, tmp_conf_out))


@task
def change_remote_conf():
    driver_folder = CONF['oltpbench_log'][:CONF['oltpbench_log'].rfind('/') +
                                          1]
    next_conf = 'next_config'

    local('cd {}  && echo "123" | sudo -S rsync -auv next_config root@{}:{}/'.
          format(driver_folder, VM_IP, driver_folder, driver_folder))

    LOG.info("fab:chagne_remote_conf next_conf copied to next_conf_last")
    cmd = 'cd {} && echo "123" | sudo -S python3 ConfParser.py {} {} {}'.\
          format(driver_folder, CONF['database_type'],
                 next_conf, CONF['database_conf'])
    remote_exec(VM_IP, cmd)


@task
def load_oltpbench():
    cmd = "./oltpbenchmark -b {} -c {} --create=true --load=true".\
          format(dconf.OLTPBENCH_BENCH, dconf.OLTPBENCH_CONFIG)
    with lcd(dconf.OLTPBENCH_HOME):  # pylint: disable=not-context-manager
        local(cmd)


@task
def run_oltpbench():
    cmd = 'echo "123" | sudo -S ./oltpbenchmark -b {} -c {} --execute=true -s 5 -o outputfile'.\
          format(dconf.OLTPBENCH_BENCH, dconf.OLTPBENCH_CONFIG)
    with lcd(dconf.OLTPBENCH_HOME):  # pylint: disable=not-context-manager
        local(cmd)


@task
def run_oltpbench_bg():
    LOG.info("run_oltpbench_bg start!")
    if IS_SYSBENCH is True:
        cmd = 'echo "123" | sudo -S bash /home/ljh/exp/scripts/sysbench/postgresql/p_{}_run.sh > {} 2>&1 &'.format(
            SYSBENCH_WORKLOAD, CONF['sysbench_log'])
        with lcd(CONF['oltpbench_home']):  # pylint: disable=not-context-manager
            local(cmd)
        LOG.info("sysbench {} started".format(SYSBENCH_WORKLOAD))
    else:
        cmd = 'echo "123" | sudo -S ./oltpbenchmark -b {} -c {} --execute=true\
            -s 30 -o outputfile > {} 2>&1 &'.format(CONF['oltpbench_workload'],
                                                    CONF['oltpbench_config'],
                                                    CONF['oltpbench_log'])
        with lcd(CONF['oltpbench_home']):  # pylint: disable=not-context-manager
            local(cmd)
        LOG.info("OLTP tpcc started")


@task
def run_controller():
    if not os.path.exists(dconf.CONTROLLER_CONFIG):
        create_controller_config()
    cmd = ' echo "123" | sudo -S gradle run -PappArgs="-c {} -d output/" --no-daemon > {}'.\
          format(dconf.CONTROLLER_CONFIG, dconf.CONTROLLER_LOG)
    with lcd(dconf.CONTROLLER_HOME):  # pylint: disable=not-context-manager
        local(cmd)
        LOG.info("run_controller executed")


@task
def signal_controller():
    LOG.info("signal_controller execute!")
    pidfile = os.path.join(dconf.CONTROLLER_HOME, 'pid.txt')
    with open(pidfile, 'r') as f:
        pid = int(f.read())
    cmd = 'echo "123" | sudo -S kill -2 {}'.format(pid)
    with lcd(dconf.CONTROLLER_HOME):  # pylint: disable=not-context-manager
        local(cmd)


@task
def signal_kill_controller():
    pidfile = os.path.join(dconf.CONTROLLER_HOME, 'pid.txt')
    with open(pidfile, 'r') as f:
        pid = int(f.read())
    cmd = 'echo "123" | sudo -S kill -9 {}'.format(pid)
    with lcd(dconf.CONTROLLER_HOME):  # pylint: disable=not-context-manager
        local(cmd)


@task
def save_dbms_result():
    t = int(time.time())
    files = [
        'knobs.json', 'metrics_after.json', 'metrics_before.json',
        'summary.json'
    ]
    for f_ in files:
        srcfile = os.path.join(dconf.CONTROLLER_HOME, 'output', f_)
        dstfile = os.path.join(dconf.RESULT_DIR, '{}__{}'.format(t, f_))
        local('cp {} {}'.format(srcfile, dstfile))
    return t


@task
def save_next_config(next_config, t=None):
    driver_folder = CONF['oltpbench_log'][:CONF['oltpbench_log'].rfind('/') +
                                          1]
    # let current next_config copy to next_config_last
    local('cd {}  && echo "123" | sudo -S cp next_config next_config_last'.
          format(driver_folder))
    if not t:
        t = int(time.time())
    with open(os.path.join(dconf.RESULT_DIR, '{}__next_config.json'.format(t)),
              'w') as f:
        json.dump(next_config, f, indent=2)
    with open(os.path.join(dconf.RESULT_DIR, '../next_config'.format(t)),
              'w') as f:
        json.dump(next_config, f, indent=2)

    local('cd {}  && echo "123" | sudo -S rsync -auv next_config root@{}:{}/'.
          format(driver_folder, VM_IP, driver_folder, driver_folder))
    return t


@task
def test_rsync():
    driver_folder = CONF['oltpbench_log'][:CONF['oltpbench_log'].rfind('/') +
                                          1]
    remote_exec(
        VM_IP,
        'echo "123" | sudo -S rsync -auv {}/next_config root@{}:{}/'.format(
            driver_folder, VM_IP, driver_folder, driver_folder))


@task
def free_cache():
    if dconf.HOST_CONN != 'docker':
        with show('everything'), settings(warn_only=True):  # pylint: disable=not-context-manager
            res = sudo("sh -c \"echo 3 > /proc/sys/vm/drop_caches\"")
            if res.failed:
                LOG.error('%s (return code %s)', res.stderr.strip(),
                          res.return_code)


@task
def free_remote_cache():
    cmd = 'sync; echo "123" | sudo -S bash -c "echo 1 > /proc/sys/vm/drop_caches"'
    remote_exec(VM_IP, cmd)


@task
def upload_result(result_dir=None, prefix=None, upload_code=None):
    result_dir = result_dir or os.path.join(dconf.CONTROLLER_HOME, 'output')
    prefix = prefix or ''
    upload_code = upload_code or dconf.UPLOAD_CODE

    files = {}
    for base in ('summary', 'knobs', 'metrics_before', 'metrics_after'):
        fpath = os.path.join(result_dir, prefix + base + '.json')

        # Replaces the true db version with the specified version to allow for
        # testing versions not officially supported by OtterTune
        if base == 'summary' and dconf.OVERRIDE_DB_VERSION:
            with open(fpath, 'r') as f:
                summary = json.load(f)
            summary['real_database_version'] = summary['database_version']
            summary['database_version'] = dconf.OVERRIDE_DB_VERSION
            with open(fpath, 'w') as f:
                json.dump(summary, f, indent=1)

        files[base] = open(fpath, 'rb')

    response = requests.post(dconf.WEBSITE_URL + '/new_result/',
                             files=files,
                             data={'upload_code': upload_code})
    if response.status_code != 200:
        raise Exception(
            'Error uploading result.\nStatus: {}\nMessage: {}\n'.format(
                response.status_code, get_content(response)))

    for f in files.values():  # pylint: disable=not-an-iterable
        f.close()

    LOG.info(get_content(response))

    return response


@task
def get_result(max_time_sec=180, interval_sec=5, upload_code=None):
    max_time_sec = int(max_time_sec)
    interval_sec = int(interval_sec)
    upload_code = upload_code or dconf.UPLOAD_CODE
    url = dconf.WEBSITE_URL + '/query_and_get/' + upload_code
    elapsed = 0
    response_dict = None
    rout = ''

    while elapsed <= max_time_sec:
        LOG.info("fab->get_result=" + str(elapsed))
        rsp = requests.get(url)
        response = get_content(rsp)
        assert response != 'null'
        rout = json.dumps(response, indent=4) if isinstance(response,
                                                            dict) else response

        LOG.debug(
            '%s\n\n[status code: %d, type(response): %s, elapsed: %ds, %s]',
            rout, rsp.status_code, type(response), elapsed,
            ', '.join(['{}: {}'.format(k, v) for k, v in rsp.headers.items()]))

        if rsp.status_code == 200:
            # Success
            response_dict = response
            break

        elif rsp.status_code == 202:
            # Not ready
            time.sleep(interval_sec)
            elapsed += interval_sec

        elif rsp.status_code == 400:
            # Failure
            raise Exception(
                "Failed to download the next config.\nStatus code: {}\nMessage: {}\n"
                .format(rsp.status_code, rout))

        elif rsp.status_code == 500:
            # Failure
            msg = rout
            if isinstance(response, str):
                savepath = os.path.join(dconf.LOG_DIR, 'error.html')
                with open(savepath, 'w') as f:
                    f.write(response)
                msg = "Saved HTML error to '{}'.".format(
                    os.path.relpath(savepath))
            raise Exception(
                "Failed to download the next config.\nStatus code: {}\nMessage: {}\n"
                .format(rsp.status_code, msg))

        else:
            raise NotImplementedError(
                "Unhandled status code: '{}'.\nMessage: {}".format(
                    rsp.status_code, rout))

    if not response_dict:
        assert elapsed > max_time_sec, \
            'response={} but elapsed={}s <= max_time={}s'.format(
                rout, elapsed, max_time_sec)
        raise Exception(
            'Failed to download the next config in {}s: {} (elapsed: {}s)'.
            format(max_time_sec, rout, elapsed))

    LOG.info('Downloaded the next config in %ds', elapsed)

    return response_dict


@task
def download_debug_info(pprint=False):
    pprint = parse_bool(pprint)
    url = '{}/dump/{}'.format(dconf.WEBSITE_URL, dconf.UPLOAD_CODE)
    params = {'pp': int(True)} if pprint else {}
    rsp = requests.get(url, params=params)

    if rsp.status_code != 200:
        raise Exception('Error downloading debug info.')

    filename = rsp.headers.get('Content-Disposition').split('=')[-1]
    file_len, exp_len = len(rsp.content), int(
        rsp.headers.get('Content-Length'))
    assert file_len == exp_len, 'File {}: content length != expected length: {} != {}'.format(
        filename, file_len, exp_len)

    with open(filename, 'wb') as f:
        f.write(rsp.content)
    LOG.info('Downloaded debug info to %s', filename)

    return filename


@task
def add_udf():
    if IS_SYSBENCH is True:
        cmd = 'sudo python3 ./LatencyUDF.py ../controller/output/ {}'.format(
            CONF['sysbench_log'])
        local(cmd)
        # LOG.info("sysbench not add 99th latency")
    else:
        cmd = 'sudo python3 ./LatencyUDF.py ../controller/output/ /home/ljh/projects/oltpbench/results/'
        local(cmd)


@task
def upload_batch(result_dir=None, sort=True, upload_code=None):
    result_dir = result_dir or dconf.RESULT_DIR
    sort = parse_bool(sort)
    results = glob.glob(os.path.join(result_dir, '*__summary.json'))
    if sort:
        results = sorted(results)
    count = len(results)

    LOG.info('Uploading %d samples from %s...', count, result_dir)
    for i, result in enumerate(results):
        prefix = os.path.basename(result)
        prefix_len = os.path.basename(result).find('_') + 2
        prefix = prefix[:prefix_len]
        upload_result(result_dir=result_dir,
                      prefix=prefix,
                      upload_code=upload_code)
        LOG.info('Uploaded result %d/%d: %s__*.json', i + 1, count, prefix)


@task
def dump_remote_database():
    if IS_SYSBENCH is True:
        return
    db_file_path = '{}/{}.dump'.format(CONF['database_save_path'],
                                       CONF['database_name'])
    remote_exec(
        VM_IP,
        "cd {} && rsync -auv ljh@192.168.122.1:/home/ljh/stores/{}.dump {}/{}.dump"
        .format(
            CONF['database_save_path'],
            CONF['database_name'],
            CONF['database_save_path'],
            CONF['database_name'],
        ))
    LOG.info('%s already exists ! ', db_file_path)
    return False
    if remote_file_exists(VM_IP, db_file_path):
        LOG.info('%s already exists ! ', db_file_path)
        return False
    else:
        LOG.info('Dump database %s to %s', CONF['database_name'], db_file_path)
        # You must create a directory named dpdata through sqlplus in your Oracle database
        if CONF['database_type'] == 'oracle':
            cmd = 'expdp {}/{}@{} schemas={}\
                 dumpfile={}.dump DIRECTORY=dpdata'.format(
                'c##tpcc', 'oracle', 'orcldb', 'c##tpcc', 'orcldb')
        elif CONF['database_type'] == 'postgres':
            cmd = 'echo "123" | sudo -S PGPASSWORD={} \
                pg_dump -U {} -F c -d {} > {}'.format(CONF['password'],
                                                      CONF['username'],
                                                      CONF['database_name'],
                                                      db_file_path)
        else:
            raise Exception("Database Type {} Not Implemented !".format(
                CONF['database_type']))
        remote_exec(VM_IP, cmd)
        return True


@task
def dump_remote_database():
    db_file_path = '{}/{}.dump'.format(CONF['database_save_path'],
                                       CONF['database_name'])
    remote_exec(
        VM_IP,
        "cd {} && rsync -auv ljh@192.168.122.1:/home/ljh/stores/{}.dump {}/{}.dump"
        .format(
            CONF['database_save_path'],
            CONF['database_name'],
            CONF['database_save_path'],
            CONF['database_name'],
        ))
    LOG.info('%s already exists ! ', db_file_path)
    return False
    if remote_file_exists(VM_IP, db_file_path):
        LOG.info('%s already exists ! ', db_file_path)
        return False
    else:
        LOG.info('Dump database %s to %s', CONF['database_name'], db_file_path)
        # You must create a directory named dpdata through sqlplus in your Oracle database
        if CONF['database_type'] == 'oracle':
            cmd = 'expdp {}/{}@{} schemas={}\
                 dumpfile={}.dump DIRECTORY=dpdata'.format(
                'c##tpcc', 'oracle', 'orcldb', 'c##tpcc', 'orcldb')
        elif CONF['database_type'] == 'postgres':
            cmd = 'echo "123" | sudo -S PGPASSWORD={} \
                pg_dump -U {} -F c -d {} > {}'.format(CONF['password'],
                                                      CONF['username'],
                                                      CONF['database_name'],
                                                      db_file_path)
        else:
            raise Exception("Database Type {} Not Implemented !".format(
                CONF['database_type']))
        remote_exec(VM_IP, cmd)
        return True


@task
def clean_recovery():
    run_sql_script('removeRestore.sh', dconf.RESTORE_POINT)
    cmds = ("""rman TARGET / <<EOF\nDELETE ARCHIVELOG ALL;\nexit\nEOF""")
    run(cmds)


@task
def restore_database():
    dumpfile = os.path.join(dconf.DB_DUMP_DIR, dconf.DB_NAME + '.dump')
    if not dconf.ORACLE_FLASH_BACK and not file_exists(dumpfile):
        raise FileNotFoundError(
            "Database dumpfile '{}' does not exist!".format(dumpfile))

    LOG.info('Start restoring database')
    if dconf.DB_TYPE == 'oracle':
        if dconf.ORACLE_FLASH_BACK:
            run_sql_script('flashBack.sh', dconf.RESTORE_POINT)
            clean_recovery()
        else:
            drop_user()
            create_user()
            run_sql_script('restoreOracle.sh', dconf.DB_USER, dconf.DB_NAME)
    elif dconf.DB_TYPE == 'postgres':
        drop_database()
        create_database()
        run('PGPASSWORD={} pg_restore -U {} -h {} -n public -j 8 -F c -d {} {}'
            .format(dconf.DB_PASSWORD, dconf.DB_USER, dconf.DB_HOST,
                    dconf.DB_NAME, dumpfile))
    else:
        raise Exception("Database Type {} Not Implemented !".format(
            dconf.DB_TYPE))
    LOG.info('Finish restoring database')


@task
def restore_remote_database():
    my_restore_remote_database()
    return None


@task
def my_restore_remote_database():
    if CONF['database_type'] == 'oracle':
        # You must create a directory named dpdata through sqlplus in your Oracle database
        # The following script assumes such directory exists.
        # You may want to modify the username, password, and dump file name in the script
        cmd = 'sh oracleScripts/restoreOracle.sh'
    elif CONF['database_type'] == 'postgres':
        cmd1 = ('echo "123"|sudo -S service postgresql stop ')
        remote_exec(VM_IP, cmd1)
        remote_exec(
            VM_IP, 'echo "123"|sudo -S rm -r {}/postgresql'.format(
                CONF['database_save_path']))
        remote_exec(
            VM_IP,
            'echo "123"|sudo -S rsync -auv ljh@192.168.122.1:/home/ljh/stores/postgresql.tar {}/'
            .format(CONF['database_save_path']))
        cmd = (
            'cd {}/ && echo "123"| sudo -S  tar -xvf {}/postgresql.tar  && service postgresql restart'
        ).format(CONF['database_save_path'], CONF['database_save_path'],
                 CONF['database_save_path'])
        # remote_exec(VM_IP, remote_cmd)
        # db_file_path = '{}/{}.dump'.format(
        #     CONF['database_save_path'], CONF['database_name'])
        # drop_remote_database()
        # create_remote_database()
        # cmd = 'echo "123"|sudo -S PGPASSWORD={} pg_restore -h 127.0.0.1 -U {} -n public -j 8 -F c -d {} {}'.\
        #       format(CONF['password'], CONF['username'],
        #              CONF['database_name'], db_file_path)
    else:
        raise Exception("Database Type {} Not Implemented !".format(
            CONF['database_type']))
    LOG.info('Start restoring database')
    remote_exec(VM_IP, cmd)
    LOG.info('Finish restoring database')


def _ready_to_start_oltpbench():
    # time.sleep(1)
    # LOG.info("/mnt/ottertune _read_to_start_olpbench executed!")
    return (os.path.exists(CONF['controller_log']) and
            'Output the process pid to' in open(CONF['controller_log']).read())


# remote ready checkls
@task
def _ready_to_start_remote_oltpbench():
    out = remote_exec(VM_IP, 'cat {}'.format(CONF['controller_log']))
    # result = ('cat:' not in out and 'Output the process pid to' in out)
    result = 'cat:' not in out
    LOG.info('fabfile._ready_to_start_remote_oltpbench={}'.format(result))
    return result


@task
def _ready_to_start_controller():
    # time.sleep(1)
    # LOG.info("/mnt/ottertune _ready_to_start_controller execute!")
    if IS_SYSBENCH is True:
        return (os.path.exists(CONF['sysbench_log'])
                and 'Threads started!' in open(CONF['sysbench_log']).read())
    else:
        return (os.path.exists(CONF['oltpbench_log'])
                and 'Warmup complete, starting measurements' in open(
                    CONF['oltpbench_log']).read())


def _ready_to_shut_down_controller():
    # time.sleep(1)
    # LOG.info("/mnt/ottertune _ready_to_shut_down_controller executed!")
    pid_file_path = '../controller/pid.txt'
    if IS_SYSBENCH is True:
        return (os.path.exists(pid_file_path)
                and os.path.exists(CONF['sysbench_log'])
                and 'SQL statistics' in open(CONF['sysbench_log']).read())
    else:
        return (os.path.exists(pid_file_path)
                and os.path.exists(CONF['oltpbench_log'])
                and 'Output throughput samples into file' in open(
                    CONF['oltpbench_log']).read())


def clean_logs():
    # remove oltpbench and controller log files
    local('rm -f {} {}'.format(dconf.OLTPBENCH_LOG, dconf.CONTROLLER_LOG))


def remote_file_exists(ip, path):
    local_cmd = "if ssh root@{} test -e {};then echo 1 ; else 0 ; fi".format(
        ip, path)
    r_str = local(local_cmd, capture=True)
    if r_str == '1':
        LOG.info("{} exists {}".format(path, ip))
        return True
    else:
        LOG.info("{} not exists {}".format(path, ip))
        return False


@task
def loop(i):
    i = int(i)

    # free cache
    free_cache()

    # remove oltpbench log and controller log
    clean_logs()

    # check disk usage
    if check_disk_usage() > dconf.MAX_DISK_USAGE:
        LOG.warning('Exceeds max disk usage %s', dconf.MAX_DISK_USAGE)

    # run controller from another process
    p = Process(target=run_controller, args=())
    p.start()
    LOG.info('Run the controller')

    # run oltpbench as a background job
    while not _ready_to_start_oltpbench():
        time.sleep(1)
    run_oltpbench_bg()
    LOG.info('Run OLTP-Bench')

    # the controller starts the first collection
    while not _ready_to_start_controller():
        # time.sleep(1)
        pass
    signal_controller()
    LOG.info('Start the first collection')

    # stop the experiment
    while not _ready_to_shut_down_controller():
        time.sleep(1)

    signal_controller()
    LOG.info('Start the second collection, shut down the controller')

    p.join()

    # add user defined target objective
    # add_udf()

    # save result
    result_timestamp = save_dbms_result()

    if i >= dconf.WARMUP_ITERATIONS:
        LOG.info("fab remote_loop->upload results")
        # upload result
        upload_result()

        LOG.info("fab remote_loop->")
        # get result
        response = get_result()

        # save next config
        save_next_config(response, t=result_timestamp)

        # change config
        change_conf(response['recommendation'])


@task
def test_join():
    p = Process(target=run_controller, args=())
    p.start()
    LOG.info('Run the controller')
    LOG.info("process is_alive={}".format(p.is_alive()))
    # run oltpbench as a background job

    LOG.info('Run OLTP-Bench')

    # the controller starts the first collection
    # while not _ready_to_start_controller():
    #     time.sleep(1)
    signal_controller()
    LOG.info('Start the first collection')

    time.sleep(5)
    # stop the experiment
    while not _ready_to_shut_down_controller():
        time.sleep(1)

    signal_controller()
    LOG.info("process is_alive={}".format(p.is_alive()))
    LOG.info('Start the second collection, shut down the controller')

    p.join()
    LOG.info("controller executed")
    LOG.info("process is_alive={}".format(p.is_alive()))


@task
def remote_loop(i):
    driver_folder = CONF['oltpbench_log'][:CONF['oltpbench_log'].rfind('/') +
                                          1]
    # clean_remote_conf()

    i = int(i)

    # # free cache
    # free_remote_cache()

    # # remove oltpbench log and controller log
    # clean_logs()

    # # check disk usage
    # if check_remote_disk_usage() > dconf.MAX_DISK_USAGE:
    #     LOG.warning('Exceeds max disk usage %s', dconf.MAX_DISK_USAGE)

    # # run controller from another process
    # p = Process(target=run_controller, args=())
    # p.start()
    # LOG.info('Run the controller')

    # # run oltpbench as a background job
    # while not _ready_to_start_oltpbench():
    #     time.sleep(1)
    # run_oltpbench_bg()
    # LOG.info('Run OLTP-Bench')

    # # the controller starts the first collection
    # while not _ready_to_start_controller():
    #     time.sleep(0.1)
    # signal_controller()
    # LOG.info('Start the first collection')

    # # stop the experiment
    # while not _ready_to_shut_down_controller():
    #     time.sleep(0.1)

    # signal_controller()
    # LOG.info('Start the second collection, shut down the controller')

    # p.join()
    # LOG.debug("fab.remote_loop method executed")
    # # add user defined target objective
    # # add_udf()
    # exit()

    # #####################
    # free cache
    free_remote_cache()

    # rsync local folder to remote vm
    # rsync_remote_folder_all()

    # remove oltpbench log and controller log
    clean_logs()

    # remove oltpbench log and controller log on remote vm
    # clean_remote_logs()

    # restart database
    restart_remote_database()

    # check disk usage
    if check_remote_disk_usage() > dconf.MAX_DISK_USAGE:
        LOG.WARN('Exceeds max disk usage %s', dconf.MAX_DISK_USAGE)

    # check remote postgresql is ok

    if check_port(VM_IP, POSTGRESQL_PORT) == False:
        LOG.warn("remote_loop: next_config can't start,"
                 "use last conf and re execute remote_loop")
        # if not file_exists("next_config_last"):
        #     local('cd {} && echo "123" | sudo touch next_config_last'.
        #           format(driver_folder))
        local('cd {} && echo "123" | sudo -S cp next_config_last next_config'.
              format(driver_folder))
        change_remote_conf()
        remote_loop(i)
        return

    # run controller from another process
    p = Process(target=run_controller, args=())
    p.start()
    # my_pool = Pool(1)
    # my_pool.apply_async(run_controller, args=())

    LOG.info('Run the controller')
    # only for test
    # exit()

    # run oltpbench as a background job
    while not _ready_to_start_oltpbench():
        pass
    run_oltpbench_bg()
    LOG.info('Run Test-Bench')

    # the controller starts the first collection
    while not _ready_to_start_controller():
        pass
    signal_controller()
    LOG.info('Start the current collection')

    # stop the experiment
    while not _ready_to_shut_down_controller():
        pass
    signal_controller()
    # signal_kill_controller()
    LOG.info('Start the next collection, shut down the controller')

    # p.terminate()
    p.join(timeout=1)
    # my_pool.close()
    # my_pool.join()

    LOG.info("fab p.join->executed")

    # add user defined target objective
    add_udf()

    # LOG.info("exit the main process")
    # exit()
    ##############################

    # save result
    result_timestamp = save_dbms_result()
    if i >= dconf.WARMUP_ITERATIONS:
        LOG.info("fab remote_loop->upload results")
        # upload result
        upload_result()
        LOG.info("fab remote_loop->get_results ")
        # get result
        response = get_result()
        # check is converge or not
        IS_CONVERGE = check_converge(response, SMOOTH_COUNT)
        LOG.info("fab remote_loop check_converge,IS_CONVERGE={}".format(
            IS_CONVERGE))
        if IS_CONVERGE and i >= dconf.BASE_ITERATION_NUM:
            LOG.info('The %s-th Loop Ends / Total Loops,IS_CONVERGE=True',
                     i + 1)
            exit()
        # save next config
        save_next_config(response, t=result_timestamp)
        # change config
        change_remote_conf()


def check_converge(response, trheshold):
    continue_count = response[CONTINUE_COUNT]
    LOG.info("fabfile check_converge:continue_count={}".format(continue_count))
    if continue_count >= trheshold:
        LOG.info("fab check_converge the result is converge")
        return True
    else:
        LOG.info("fab check_converge IS_CONVERGE={}".format(IS_CONVERGE))
        return False


@task
def check_port(ip, port):
    cmd = 'nc -w 1 {} {} && echo succeeded || echo refused'.format(ip, port)
    log = local(cmd, capture=True)
    if 'succeeded' in log:
        LOG.info("fab:check_port {} {} is succeeded".format(ip, port))
        return True
    else:
        LOG.warn("fab:check_port {} {} is refused".format(ip, port))
        return False


@task
def run_loops(max_iter=10):
    # dump database if it's not done before.
    dump = dump_database()

    for i in range(int(max_iter)):
        # restart database
        restart_succeeded = restart_database()
        if not restart_succeeded:
            files = {
                'summary': b'{"error": "DB_RESTART_ERROR"}',
                'knobs': b'{}',
                'metrics_before': b'{}',
                'metrics_after': b'{}'
            }
            # 同样的再运行一次
            response = requests.post(dconf.WEBSITE_URL + '/new_result/',
                                     files=files,
                                     data={'upload_code': dconf.UPLOAD_CODE})
            response = get_result()
            result_timestamp = int(time.time())
            save_next_config(response, t=result_timestamp)
            change_conf(response['recommendation'])
            continue

        # reload database periodically
        if dconf.RELOAD_INTERVAL > 0:
            if i % dconf.RELOAD_INTERVAL == 0:
                if i == 0 and dump is False:
                    restore_database()
                elif i > 0:
                    restore_database()

        time.sleep(dconf.RESTART_SLEEP_SEC)
        LOG.info('The %s-th Loop Starts / Total Loops %s', i + 1, max_iter)
        loop(i % dconf.RELOAD_INTERVAL if dconf.RELOAD_INTERVAL > 0 else i)
        LOG.info('The %s-th Loop Ends / Total Loops %s', i + 1, max_iter)


@task
def run_remote_loops(max_iter=10, first=True):

    if first:
        LOG.info("fab run_remote_loops clean remote conf")
        clean_remote_conf()

    # dump database if it's not done before.
    dump = dump_remote_database()

    for i in range(int(max_iter)):
        # restart database
        restart_succeeded = restart_remote_database()
        if not restart_succeeded:
            files = {
                'summary': b'{"error": "DB_RESTART_ERROR"}',
                'knobs': b'{}',
                'metrics_before': b'{}',
                'metrics_after': b'{}'
            }
            response = requests.post(dconf.WEBSITE_URL + '/new_result/',
                                     files=files,
                                     data={'upload_code': dconf.UPLOAD_CODE})
            response = get_result()
            result_timestamp = int(time.time())
            save_next_config(response, t=result_timestamp)
            change_remote_conf()
            continue

        # reload database periodically
        if dconf.RELOAD_INTERVAL > 0:
            if i % dconf.RELOAD_INTERVAL == 0:
                if i == 0 and dump is False:
                    # restore_remote_database()
                    pass
                elif i > 0:
                    # restore_remote_database()
                    pass
        time.sleep(dconf.RESTART_SLEEP_SEC)
        if not IS_CONVERGE:
            LOG.info('The %s-th Loop Starts / Total Loops %s; is_converge=%s',
                     i + 1, max_iter, IS_CONVERGE)
            remote_loop(
                i % dconf.RELOAD_INTERVAL if dconf.RELOAD_INTERVAL > 0 else i)
            LOG.info('The %s-th Loop Ends / Total Loops %s; IS_CONVERGE=%s',
                     i + 1, max_iter, IS_CONVERGE)
        else:
            LOG.info('The %s-th Loop  / Total Loops %s. IS_CONVERGE=%s.',
                     i + 1, max_iter, IS_CONVERGE)
            exit()
            break


@task
def rename_batch(result_dir=None):
    result_dir = result_dir or dconf.RESULT_DIR
    results = glob.glob(os.path.join(result_dir, '*__summary.json'))
    results = sorted(results)
    for i, result in enumerate(results):
        prefix = os.path.basename(result)
        prefix_len = os.path.basename(result).find('_') + 2
        prefix = prefix[:prefix_len]
        new_prefix = str(i) + '__'
        for base in ('summary', 'knobs', 'metrics_before', 'metrics_after'):
            fpath = os.path.join(result_dir, prefix + base + '.json')
            rename_path = os.path.join(result_dir, new_prefix + base + '.json')
            os.rename(fpath, rename_path)


def _http_content_to_json(content):
    if isinstance(content, bytes):
        content = content.decode('utf-8')
    try:
        json_content = json.loads(content)
        decoded = True
    except (TypeError, json.decoder.JSONDecodeError):
        json_content = None
        decoded = False

    return json_content, decoded


def _modify_website_object(obj_name, action, verbose=False, **kwargs):
    verbose = parse_bool(verbose)
    if obj_name == 'project':
        valid_actions = ('create', 'edit')
    elif obj_name == 'session':
        valid_actions = ('create', 'edit')
    elif obj_name == 'user':
        valid_actions = ('create', 'delete')
    else:
        raise ValueError(
            'Invalid object: {}. Valid objects: project, session'.format(
                obj_name))

    if action not in valid_actions:
        raise ValueError('Invalid action: {}. Valid actions: {}'.format(
            action, ', '.join(valid_actions)))

    data = {}
    for k, v in kwargs.items():
        if isinstance(v, (dict, list, tuple)):
            v = json.dumps(v)
        data[k] = v

    url_path = '/{}/{}/'.format(action, obj_name)
    response = requests.post(dconf.WEBSITE_URL + url_path, data=data)

    content = response.content.decode('utf-8')
    if response.status_code != 200:
        raise Exception("Failed to {} {}.\nStatus: {}\nMessage: {}\n".format(
            action, obj_name, response.status_code, content))

    json_content, decoded = _http_content_to_json(content)
    if verbose:
        if decoded:
            LOG.info('\n%s_%s = %s', action.upper(), obj_name.upper(),
                     json.dumps(json_content, indent=4))
        else:
            LOG.warning("Content could not be decoded.\n\n%s\n", content)

    return response, json_content, decoded


@task
def create_website_user(**kwargs):
    return _modify_website_object('user', 'create', **kwargs)


@task
def delete_website_user(**kwargs):
    return _modify_website_object('user', 'delete', **kwargs)


@task
def create_website_project(**kwargs):
    return _modify_website_object('project', 'create', **kwargs)


@task
def edit_website_project(**kwargs):
    return _modify_website_object('project', 'edit', **kwargs)


@task
def create_website_session(**kwargs):
    return _modify_website_object('session', 'create', **kwargs)


@task
def edit_website_session(**kwargs):
    return _modify_website_object('session', 'edit', **kwargs)


def wait_pipeline_data_ready(max_time_sec=800, interval_sec=10):
    max_time_sec = int(max_time_sec)
    interval_sec = int(interval_sec)
    elapsed = 0
    ready = False

    while elapsed <= max_time_sec:
        response = requests.get(dconf.WEBSITE_URL + '/test/pipeline/')
        content = get_content(response)
        LOG.info("%s (elapsed: %ss)", content, elapsed)
        if 'False' in content:
            time.sleep(interval_sec)
            elapsed += interval_sec
        else:
            ready = True
            break

    return ready


@task
def integration_tests():

    # Create test website
    response = requests.get(dconf.WEBSITE_URL + '/test/create/')
    LOG.info(get_content(response))

    # Upload training data
    LOG.info('Upload training data to no tuning session')
    upload_batch(result_dir='./integrationTests/data/',
                 upload_code='ottertuneTestNoTuning')

    # wait celery periodic task finishes
    assert wait_pipeline_data_ready(), "Pipeline data failed"

    # Test DNN
    LOG.info('Test DNN (deep neural network)')
    upload_result(result_dir='./integrationTests/data/',
                  prefix='0__',
                  upload_code='ottertuneTestTuningDNN')
    response = get_result(upload_code='ottertuneTestTuningDNN')
    assert response['status'] == 'good'

    # Test GPR
    LOG.info('Test GPR (gaussian process regression)')
    upload_result(result_dir='./integrationTests/data/',
                  prefix='0__',
                  upload_code='ottertuneTestTuningGPR')
    response = get_result(upload_code='ottertuneTestTuningGPR')
    assert response['status'] == 'good'

    # Test DDPG
    LOG.info('Test DDPG (deep deterministic policy gradient)')
    upload_result(result_dir='./integrationTests/data/',
                  prefix='0__',
                  upload_code='ottertuneTestTuningDDPG')
    response = get_result(upload_code='ottertuneTestTuningDDPG')
    assert response['status'] == 'good'

    # Test DNN: 2rd iteration
    upload_result(result_dir='./integrationTests/data/',
                  prefix='1__',
                  upload_code='ottertuneTestTuningDNN')
    response = get_result(upload_code='ottertuneTestTuningDNN')
    assert response['status'] == 'good'

    # Test GPR: 2rd iteration
    upload_result(result_dir='./integrationTests/data/',
                  prefix='1__',
                  upload_code='ottertuneTestTuningGPR')
    response = get_result(upload_code='ottertuneTestTuningGPR')
    assert response['status'] == 'good'

    # Test DDPG: 2rd iteration
    upload_result(result_dir='./integrationTests/data/',
                  prefix='1__',
                  upload_code='ottertuneTestTuningDDPG')
    response = get_result(upload_code='ottertuneTestTuningDDPG')
    assert response['status'] == 'good'

    LOG.info("\n\nIntegration Tests: PASSED!!\n")


def remote_exec(host: str, cmd: str) -> None:
    """[summary]excute command on remote server
    Arguments:
        host {str} -- the ip address of connnect server
        cmd {str} -- the command to be executed
    Returns:
        None -- command execute result
    """
    # 创建SSH对象

    ssh = paramiko.SSHClient()
    # 允许连接不在know_hosts文件中的主机
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # 连接服务器
    ssh.connect(hostname=host, port=22, username='root', password='123')
    # 执行命令  stdout命令结果，stderr错误
    LOG.info("fabfile.remote_exec cmd={}".format(cmd))
    stdin, stdout, stderr = ssh.exec_command(cmd)
    # 获取命令结果
    std_str = str(stdout.read(), encoding="utf-8")
    LOG.info("connect to {} execute {} \n std_out={}".format(
        VM_IP, cmd, std_str))
    # print("std_str=",std_str)
    # 关闭连接
    ssh.close()
    return std_str
