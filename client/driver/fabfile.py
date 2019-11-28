#
# OtterTune - fabfile.py
#
# Copyright (c) 2017-18, Carnegie Mellon University Database Group
#
'''
Created on Mar 23, 2018

@author: bohan
'''
import sys
import json
import logging
import time
import os.path
import re
import glob
from multiprocessing import Process
from fabric.api import (env, local, task, lcd)
from fabric.state import output as fabric_output
import paramiko
from collections import OrderedDict


VM_IP = "192.168.122.77"
LOG = logging.getLogger()
# LOG.setLevel(logging.DEBUG)
LOG.setLevel(logging.INFO)

Formatter = logging.Formatter(  # pylint: disable=invalid-name
    "%(asctime)s [%(levelname)s]  %(message)s")

# print the log
ConsoleHandler = logging.StreamHandler(
    sys.stdout)  # pylint: disable=invalid-name
ConsoleHandler.setFormatter(Formatter)
LOG.addHandler(ConsoleHandler)

# Fabric environment settings
env.hosts = ['localhost']
fabric_output.update({
    'running': True,
    'stdout': True,
})

# intervals of restoring the databse
RELOAD_INTERVAL = 10
# maximum disk usage
MAX_DISK_USAGE = 90

with open('driver_config.json', 'r') as f:
    CONF = json.load(f)


@task
def check_disk_usage():
    partition = CONF['database_disk']
    disk_use = 0
    cmd = "df -h {}".format(partition)
    out = local(cmd, capture=True).splitlines()[1]
    m = re.search('\d+(?=%)', out)
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
    cmd = 'free -m -h'
    local(cmd)


@task
def restart_remote_database():
    if CONF['database_type'] == 'postgres':
        cmd = 'sudo service postgresql restart'
    elif CONF['database_type'] == 'oracle':
        driver_folder = CONF['oltpbench_log'][:CONF['oltpbench_log'].rfind(
            '/')+1]
        cmd = ('cd {} && sh oracleScripts/shutdownOracle.sh '
               '&& sh oracleScripts/startupOracle.sh').format(driver_folder)
    else:
        raise Exception("Database Type {} Not Implemented !".format(
            CONF['database_type']))
    remote_exec(VM_IP, cmd)


@task
def restart_database():
    if CONF['database_type'] == 'postgres':
        cmd = 'echo "123" | sudo -S service postgresql restart'
    elif CONF['database_type'] == 'oracle':
        cmd = 'sh oracleScripts/shutdownOracle.sh && sh oracleScripts/startupOracle.sh'
    else:
        raise Exception("Database Type {} Not Implemented !".format(
            CONF['database_type']))
    local(cmd)


@task
def drop_database():
    if CONF['database_type'] == 'postgres':
        cmd = "PGPASSWORD={} dropdb -e --if-exists {} -U {}".\
              format(CONF['password'], CONF['database_name'], CONF['username'])
    else:
        raise Exception("Database Type {} Not Implemented !".format(
            CONF['database_type']))
    local(cmd)


@task
def drop_remote_database():
    if CONF['database_type'] == 'postgres':
        cmd = 'echo "123"|sudo -S PGPASSWORD={} dropdb\
             -e --if-exists {} -U {}'.format(CONF['password'],
                                             CONF['database_name'],
                                             CONF['username'])
    else:
        raise Exception("Database Type {} Not Implemented !".format(
            CONF['database_type']))
    remote_exec(VM_IP, cmd)


@task
def create_database():
    if CONF['database_type'] == 'postgres':
        cmd = "PGPASSWORD={} createdb -e {} -U {}".\
              format(CONF['password'], CONF['database_name'], CONF['username'])
    else:
        raise Exception("Database Type {} Not Implemented !".format(
            CONF['database_type']))
    local(cmd)


@task
def create_remote_database():
    if CONF['database_type'] == 'postgres':
        cmd = 'echo "123"|sudo -S PGPASSWORD={} createdb -e {} -U {}'.\
              format(CONF['password'], CONF['database_name'], CONF['username'])
    else:
        raise Exception("Database Type {} Not Implemented !".format(
            CONF['database_type']))
    remote_exec(VM_IP, cmd)


@task
def change_conf():
    next_conf = 'next_config'
    cmd = "sudo python3 ConfParser.py {} {} {}".\
          format(CONF['database_type'], next_conf, CONF['database_conf'])
    local(cmd)


@task
def change_remote_conf():
    driver_folder = CONF['oltpbench_log'][:CONF['oltpbench_log'].rfind(
        '/')+1]
    next_conf = 'next_config'
    cmd = 'cd {} && echo "123" | sudo -S python3 ConfParser.py {} {} {}'.\
          format(driver_folder, CONF['database_type'],
                 next_conf, CONF['database_conf'])
    remote_exec(VM_IP, cmd)


@task
def load_oltpbench():
    cmd = "./oltpbenchmark -b {} -c {} --create=true --load=true".\
          format(CONF['oltpbench_workload'], CONF['oltpbench_config'])
    with lcd(CONF['oltpbench_home']):  # pylint: disable=not-context-manager
        local(cmd)


@task
def run_oltpbench():
    cmd = "./oltpbenchmark -b {} -c {} --execute=true -s 5 -o outputfile".\
          format(CONF['oltpbench_workload'], CONF['oltpbench_config'])
    with lcd(CONF['oltpbench_home']):  # pylint: disable=not-context-manager
        local(cmd)


@task
def run_oltpbench_bg():
    cmd = "./oltpbenchmark -b {} -c {} --execute=true\
         -s 5 -o outputfile > {} 2>&1 &".format(CONF['oltpbench_workload'],
                                                CONF['oltpbench_config'], CONF['oltpbench_log'])
    with lcd(CONF['oltpbench_home']):  # pylint: disable=not-context-manager
        local(cmd)


@task
def run_remote_oltpbench_bg():
    cmd = "cd {}/ && nohup {}/oltpbenchmark -b {} -c {} --execute=true \
        -s 5 -o outputfile > {} 2>&1 &".\
          format(CONF['oltpbench_home'], CONF['oltpbench_home'], CONF['oltpbench_workload'],
                 CONF['oltpbench_config'], CONF['oltpbench_log'])
    # with lcd(CONF['oltpbench_home']):  # pylint: disable=not-context-manager
    #     local(cmd)
    remote_exec(VM_IP, cmd)


@task
def run_controller():
    cmd = 'sudo gradle run -PappArgs="-c {} -d output/" --no-daemon > {}'.\
          format(CONF['controller_config'], CONF['controller_log'])
    with lcd("../controller"):  # pylint: disable=not-context-manager
        local(cmd)


@task
def run_remote_controller():
    cmd = 'echo "123" | sudo -S gradle run -PappArgs="-c {} -d output/" --no-daemon > {}'.\
          format(CONF['controller_config'], CONF['controller_log'])
    # with lcd("../controller"):  # pylint: disable=not-context-manager
    #     local(cmd)
    driver_folder = CONF['oltpbench_log'][:CONF['oltpbench_log'].rfind('/')+1]
    remote_exec(VM_IP, 'cd {}../controller && {}'.format(driver_folder, cmd))


@task
def signal_controller():
    pid = int(open('../controller/pid.txt').read())
    cmd = 'sudo kill -2 {}'.format(pid)
    with lcd("../controller"):  # pylint: disable=not-context-manager
        local(cmd)


@task
def signal_remote_controller():
    driver_folder = CONF['oltpbench_log'][:CONF['oltpbench_log'].rfind(
        '/')+1]
    pid_path = driver_folder+'../controller/pid.txt'
    pid = remote_exec(VM_IP, 'cat {}'.format(pid_path))
    remote_exec(VM_IP, 'echo "123" | sudo -S kill -2 {}'.format(pid))
    remote_exec(VM_IP, 'echo "123"|sudo -S ps -ef | grep gradle |'
                ' awk {print $2}|xargs sudo kill -2 ')


@task
def save_dbms_result():
    t = int(time.time())
    files = ['knobs.json', 'metrics_after.json',
             'metrics_before.json', 'summary.json']
    for f_ in files:
        f_prefix = f_.split('.')[0]
        cmd = 'cp ../controller/output/{} {}/{}__{}.json'.\
              format(f_, CONF['save_path'], t, f_prefix)
        local(cmd)


@task
def save_dbms_result():
    t = int(time.time())
    files = ['knobs.json', 'metrics_after.json',
             'metrics_before.json', 'summary.json']
    for f_ in files:
        f_prefix = f_.split('.')[0]
        cmd = 'cp ../controller/output/{} {}/{}__{}.json'.\
              format(f_, CONF['save_path'], t, f_prefix)
        local(cmd)


@task
def save_remote_dbms_result():
    t = int(time.time())
    files = ['knobs.json', 'metrics_after.json',
             'metrics_before.json', 'summary.json']
    driver_folder = CONF['oltpbench_log'][:CONF['oltpbench_log'].rfind(
        '/')+1]
    for f_ in files:
        f_prefix = f_.split('.')[0]
        cmd = ('echo "123"'
               ' | sudo -S cp {}../controller/output/{} {}/{}__{}.json').\
            format(driver_folder, f_, CONF['save_path'], t, f_prefix)
        remote_exec(VM_IP, cmd)


@task
def free_cache():
    cmd = 'sync; sudo bash -c "echo 1 > /proc/sys/vm/drop_caches"'
    local(cmd)


@task
def free_remote_cache():
    cmd = 'sync; sudo bash -c "echo 1 > /proc/sys/vm/drop_caches"'
    remote_exec(VM_IP, cmd)


@task
def upload_result():
    cmd = 'python3 ../../server/website/script/upload/upload.py \
           ../controller/output/ {} {}/new_result/'.format(CONF['upload_code'],
                                                           CONF['upload_url'])
    local(cmd)


@task
def upload_remote_result():
    driver_folder = CONF['oltpbench_log'][:CONF['oltpbench_log'].rfind(
        '/')+1]
    cmd = 'python3 {}../../server/website/script/upload/upload.py \
           {}../controller/output/ {} {}/new_result/'.format(
        driver_folder,
        driver_folder,
        CONF['upload_code'],
        CONF['upload_url'])
    remote_exec(VM_IP, cmd)


@task
def get_result():
    cmd = 'python3 ../../script/query_and_get.py {} {} 5'.\
          format(CONF['upload_url'], CONF['upload_code'])
    local(cmd)


@task
def get_remote_result():
    driver_folder = CONF['oltpbench_log'][:CONF['oltpbench_log'].rfind(
        '/')+1]
    cmd = 'cd {} && echo "123" | \
        sudo -S python3 ../../script/query_and_get.py {} {} 5'.\
          format(driver_folder, CONF['upload_url'], CONF['upload_code'])
    # local(cmd)
    remote_exec(VM_IP, cmd)
    remote_exec(VM_IP, 'cd {} \
    && echo "123" | sudo -S rsync -au root@{}:{}next_config {}'
                .format(driver_folder,
                        VM_IP,
                        driver_folder,
                        driver_folder))


@task
def add_udf():
    cmd = 'sudo python3 ./LatencyUDF.py ../controller/output/'
    local(cmd)


@task
def upload_batch():
    cmd = 'python3 ./upload_batch.py {} {} {}/new_result/'.format(CONF['save_path'],
                                                                  CONF['upload_code'],
                                                                  CONF['upload_url'])
    local(cmd)


@task
def dump_database():
    db_file_path = '{}/{}.dump'.format(
        CONF['database_save_path'], CONF['database_name'])
    if os.path.exists(db_file_path):
        LOG.info('%s already exists ! ', db_file_path)
        return False
    else:
        LOG.info('Dump database %s to %s', CONF['database_name'], db_file_path)
        # You must create a directory named dpdata through sqlplus in your Oracle database
        if CONF['database_type'] == 'oracle':
            cmd = 'expdp {}/{}@{} schemas={} dumpfile={}.dump DIRECTORY=dpdata'.format(
                'c##tpcc', 'oracle', 'orcldb', 'c##tpcc', 'orcldb')
        elif CONF['database_type'] == 'postgres':
            cmd = 'PGPASSWORD={} pg_dump -U {} -F c -d {} > {}'.format(CONF['password'],
                                                                       CONF['username'],
                                                                       CONF['database_name'],
                                                                       db_file_path)
        else:
            raise Exception("Database Type {} Not Implemented !".format(
                CONF['database_type']))
        local(cmd)
        return True


@task
def dump_remote_database():
    db_file_path = '{}/{}.dump'.format(
        CONF['database_save_path'], CONF['database_name'])
    if remote_file_exists(db_file_path):
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
def restore_database():
    if CONF['database_type'] == 'oracle':
        # You must create a directory named dpdata through sqlplus in your Oracle database
        # The following script assumes such directory exists.
        # You may want to modify the username, password, and dump file name in the script
        cmd = 'sh oracleScripts/restoreOracle.sh'
    elif CONF['database_type'] == 'postgres':
        db_file_path = '{}/{}.dump'.format(
            CONF['database_save_path'], CONF['database_name'])
        drop_database()
        create_database()
        cmd = 'PGPASSWORD={} pg_restore -U {} -n public -j 8 -F c -d {} {}'.\
              format(CONF['password'], CONF['username'],
                     CONF['database_name'], db_file_path)
    else:
        raise Exception("Database Type {} Not Implemented !".format(
            CONF['database_type']))
    LOG.info('Start restoring database')
    local(cmd)
    LOG.info('Finish restoring database')


@task
def restore_remote_database():
    if CONF['database_type'] == 'oracle':
        # You must create a directory named dpdata through sqlplus in your Oracle database
        # The following script assumes such directory exists.
        # You may want to modify the username, password, and dump file name in the script
        cmd = 'sh oracleScripts/restoreOracle.sh'
    elif CONF['database_type'] == 'postgres':
        db_file_path = '{}/{}.dump'.format(
            CONF['database_save_path'], CONF['database_name'])
        drop_remote_database()
        create_remote_database()
        cmd = 'echo "123"|sudo -S PGPASSWORD={} pg_restore -U {} -n public -j 8 -F c -d {} {}'.\
              format(CONF['password'], CONF['username'],
                     CONF['database_name'], db_file_path)
    else:
        raise Exception("Database Type {} Not Implemented !".format(
            CONF['database_type']))
    LOG.info('Start restoring database')
    remote_exec(VM_IP, cmd)
    LOG.info('Finish restoring database')


def _ready_to_start_oltpbench():
    return (os.path.exists(CONF['controller_log']) and
            'Output the process pid to'
            in open(CONF['controller_log']).read())

# remote ready check
@task
def _ready_to_start_remote_oltpbench():
    out = remote_exec(VM_IP, 'cat {}'.format(CONF['controller_log']))
    # result = ('cat:' not in out and 'Output the process pid to' in out)
    result = 'cat:' not in out
    LOG.info('fabfile._ready_to_start_remote_oltpbench={}'.format(result))
    return result


def _ready_to_start_controller():
    return (os.path.exists(CONF['oltpbench_log']) and
            'Warmup complete, starting measurements'
            in open(CONF['oltpbench_log']).read())


@task
def _ready_to_start_remote_controller():
    return remote_file_exists(VM_IP, CONF['oltpbench_log']) \
        and 'Warmup complete, starting measurements' \
        in remote_exec(VM_IP, 'cat {}'.format(CONF['oltpbench_log']))
    # return (os.path.exists(CONF['oltpbench_log']) and
    #         'Warmup complete, starting measurements'
    #         in open(CONF['oltpbench_log']).read())


def _ready_to_shut_down_controller():
    pid_file_path = '../controller/pid.txt'
    return (os.path.exists(pid_file_path) and os.path.exists(CONF['oltpbench_log']) and
            'Output throughput samples into file' in open(CONF['oltpbench_log']).read())


def _ready_to_shut_down_remote_controller():
    driver_folder = CONF['oltpbench_log'][:CONF['oltpbench_log'].rfind(
        '/')+1]
    pid_file_path = driver_folder+'../controller/pid.txt'
    return remote_file_exists(VM_IP, pid_file_path) \
        and remote_file_exists(VM_IP, CONF['oltpbench_log']) \
        and 'Output throughput samples into file' in \
        remote_exec(VM_IP, 'cat {}'.format(CONF['oltpbench_log']))


def remote_file_exists(ip, path):
    out = remote_exec(ip, 'ls {}'.format(path))
    return 'ls:' not in out


def clean_logs():
    # remove oltpbench log
    cmd = 'rm -f {}'.format(CONF['oltpbench_log'])
    local(cmd)

    # remove controller log
    cmd = 'rm -f {}'.format(CONF['controller_log'])
    local(cmd)


@task
def clean_remote_logs():
    # remove oltpbench log for remote vm
    cmd = 'rm -f {}'.format(CONF['oltpbench_log'])
    remote_exec(VM_IP, cmd)

    # remove controller log for remote vm
    cmd = 'rm -f {}'.format(CONF['controller_log'])
    remote_exec(VM_IP, cmd)


@task
def lhs_samples(count=10):
    cmd = 'python3 lhs.py {} {} {}'.format(
        count, CONF['lhs_knob_path'], CONF['lhs_save_path'])
    local(cmd)


@task
def remote_loop(iter=1):

    # restart qemu vm
    restart_qemu()

    # free remote vm cache
    free_remote_cache()

    # free cache
    # free_cache()

    # rsync local folder to remote vm{only for the first run}
    # rsync_remote_folder_all()

    # remove oltpbench log and controller log
    # clean_logs()

    # remove oltpbench log and controller log on remote vm
    clean_remote_logs()

    # restart database
    # restart_database()

    # restart remote vm database
    restart_remote_database()

    # restore database every reload interval
    if iter % RELOAD_INTERVAL == 0:
        restore_remote_database()

    # check disk usage
    # if check_disk_usage() > MAX_DISK_USAGE:
    #     LOG.WARN('Exceeds max disk usage %s', MAX_DISK_USAGE)

    # check remote disk usage
    if check_remote_disk_usage() > MAX_DISK_USAGE:
        LOG.WARN('remote vm Exceeds max disk usage %s', MAX_DISK_USAGE)

    # run controller from another process
    p = Process(target=run_remote_controller, args=())
    p.start()
    LOG.info('Run the remote controller')

    # run oltpbench as a background job
    while not _ready_to_start_remote_oltpbench():
        pass
    run_remote_oltpbench_bg()
    LOG.info('Run remote OLTP-Bench')

    # the controller starts the first collection
    while not _ready_to_start_remote_controller():
        pass
    # remote signal_controller()
    # ensure the remote controller is down
    signal_remote_controller()
    LOG.info('Start the first remote collection')

    # stop the experiment
    while not _ready_to_shut_down_remote_controller():
        pass
    signal_remote_controller()
    LOG.info('Start the second remote collection, shut down the controller')
    # LOG.info("fabfile.remote_loop p.join method start")
    p.join()
    # LOG.info("fabfile.remote_loop p.join method end")

    # add user defined target objective
    # add_udf()

    # save remote result
    save_remote_dbms_result()

    # upload remote result
    upload_remote_result()

    # get remote result
    get_remote_result()

    # change remote config
    change_remote_conf()


@task
def loop():

    # restart qemu vm
    restart_qemu()

    # free remote vm cache
    free_remote_cache()

    # free cache
    free_cache()

    # rsync local folder to remote vm
    rsync_remote_folder_all()

    # remove oltpbench log and controller log
    clean_logs()

    # remove oltpbench log and controller log on remote vm
    clean_remote_logs()

    # restart database
    restart_database()

    # restart remote vm database
    restart_remote_database()

    # check disk usage
    if check_disk_usage() > MAX_DISK_USAGE:
        LOG.WARN('Exceeds max disk usage %s', MAX_DISK_USAGE)

    # run controller from another process
    p = Process(target=run_controller, args=())
    p.start()
    LOG.info('Run the controller')

    # run oltpbench as a background job
    while not _ready_to_start_oltpbench():
        pass
    run_oltpbench_bg()
    LOG.info('Run OLTP-Bench')

    # the controller starts the first collection
    while not _ready_to_start_controller():
        pass
    signal_controller()
    LOG.info('Start the first collection')

    # stop the experiment
    while not _ready_to_shut_down_controller():
        pass
    signal_controller()
    LOG.info('Start the second collection, shut down the controller')

    p.join()

    # add user defined target objective
    # add_udf()

    # save result
    save_dbms_result()

    # upload result
    upload_result()

    # get result
    get_result()

    # change config
    change_conf()


@task
def run_lhs():
    datadir = CONF['lhs_save_path']
    samples = glob.glob(os.path.join(datadir, 'config_*'))

    # dump database if it's not done before.
    dump = dump_database()

    for i, sample in enumerate(samples):
        # reload database periodically
        if RELOAD_INTERVAL > 0:
            if i % RELOAD_INTERVAL == 0:
                if i == 0 and dump is False:
                    restore_database()
                elif i > 0:
                    restore_database()
        # free cache
        free_cache()

        LOG.info('\n\n Start %s-th sample %s \n\n', i, sample)
        # check memory usage
        # check_memory_usage()

        # check disk usage
        if check_disk_usage() > MAX_DISK_USAGE:
            LOG.WARN('Exceeds max disk usage %s', MAX_DISK_USAGE)

        # copy lhs-sampled config to the to-be-used config
        cmd = 'cp {} next_config'.format(sample)
        local(cmd)

        # remove oltpbench log and controller log
        clean_logs()

        # change config
        change_conf()

        # restart database
        restart_database()

        if CONF.get('oracle_awr_enabled', False):
            # create snapshot for oracle AWR report
            if CONF['database_type'] == 'oracle':
                local('sh snapshotOracle.sh')

        # run controller from another process
        p = Process(target=run_controller, args=())
        p.start()

        # run oltpbench as a background job
        while not _ready_to_start_oltpbench():
            pass
        run_oltpbench_bg()
        LOG.info('Run OLTP-Bench')

        while not _ready_to_start_controller():
            pass
        signal_controller()
        LOG.info('Start the first collection')

        while not _ready_to_shut_down_controller():
            pass
        # stop the experiment
        signal_controller()
        LOG.info('Start the second collection, shut down the controller')

        p.join()

        # save result
        save_dbms_result()

        # upload result
        upload_result()

        if CONF.get('oracle_awr_enabled', False):
            # create oracle AWR report for performance analysis
            if CONF['database_type'] == 'oracle':
                local(
                    'sh oracleScripts/snapshotOracle.sh && sh oracleScripts/awrOracle.sh')


@task
def run_loops(max_iter=5):
    # dump database if it's not done before.
    dump = dump_database()

    for i in range(int(max_iter)):
        if RELOAD_INTERVAL > 0:
            if i % RELOAD_INTERVAL == 0:
                if i == 0 and dump is False:
                    restore_database()
                elif i > 0:
                    restore_database()
        LOG.info('The %s-th Loop Starts / Total Loops %s', i + 1, max_iter)
        loop()
        LOG.info('The %s-th Loop Ends / Total Loops %s', i + 1, max_iter)


@task
def run_remote_loops(max_iter=1):
    # dump database if it's not done before.
    # dump_remote = dump_remote_database()

    for i in range(int(max_iter)):
        # if RELOAD_INTERVAL > 0:
        #     if i % RELOAD_INTERVAL == 0:
        #         if i == 0 and dump_remote is False:
        #             restore_remote_database()
        #         elif i > 0:
        #             restore_remote_database()
        LOG.info('The %s-th remote Loop Starts / Total Loops %s', i + 1, max_iter)
        remote_loop(i)
        LOG.info('The %s-th remote Loop Ends / Total Loops %s', i + 1, max_iter)


@task
def test_ping():
    test_out = remote_exec('192.168.122.1', 'ping -c 2 192.168.122.77')
    LOG.info("test_out={}".format(test_out))


@task
def restart_qemu():
    out = remote_exec('192.168.122.1', 'ping -c 2 {}'.format(VM_IP))
    LOG.info("fabfile.restart_qemu ping result={}".format(out))
    if 'Unreachable' not in out:
        remote_exec(VM_IP, 'echo "123"| sudo -S poweroff')
        while 'Unreachable' not in out:
            out = remote_exec('192.168.122.1', 'ping -c 2 {}'.format(VM_IP))
    # next_config_name = "next_config"
    next_config_name = "next_config.json"
    qemu_parameter = ''
    with open(next_config_name, 'r') as next_config:
        config = json.load(next_config, encoding="UTF-8",
                           object_pairs_hook=OrderedDict)
        qemu_parameter = config['qemu_parameter']
    if len(qemu_parameter) == 0:
        LOG.error("fabfile.restart_qemu qemu_parameter length is 0")
        exit()
    LOG.info("fabfile.restart_qemu qemu_parameter={}".format(qemu_parameter))

    LOG.info("Execute restart qemu virtual machine")
    remove_cmd = 'echo "123" | sudo -S bash ./qemuScripts/remove_mdev_device.sh'
    local(remove_cmd)
    pre_cmd = 'echo "123" | sudo -S bash ./qemuScripts/pre_mdev.sh'
    local(pre_cmd)
    vm_num = qemu_parameter['qemu_number']
    queue_num = qemu_parameter['hardware_queue_number']
    cpu_num = qemu_parameter['cpu_number']
    # GB,must delete the letter
    tmp_mem_size = qemu_parameter['memory_size']  # the unit is GB
    mem_size = tmp_mem_size[:len(tmp_mem_size)-1]
    start_vm_cmd = "sudo bash ./qemuScripts/start_vm_N_Q_C.sh {} {} {} {}".format(
        vm_num, queue_num, cpu_num, mem_size)
    local(start_vm_cmd)
    # exit()


@task
def rsync_remote_folder_all():
    qemu_script_path = CONF['qemu_script_path']
    otter_home = qemu_script_path[:qemu_script_path.find('/', 1)]
    otter_home_parent = otter_home[:otter_home.rfind('/')+1]
    oltpbench_home = CONF['oltpbench_home']
    oltpbench_home_parent = oltpbench_home[:oltpbench_home.rfind('/')+1]
    database_config_folder =\
        CONF['database_conf'][:CONF['database_conf'].rfind('/')]
    database_config_folder_parent = \
        database_config_folder[:database_config_folder.rfind(
            '/')+1]
    rsync_remote_single(otter_home, VM_IP, otter_home_parent)
    rsync_remote_single(oltpbench_home, VM_IP, oltpbench_home_parent)
    rsync_remote_single(otter_home, VM_IP, otter_home_parent)
    # rsync_otter_home_cmd =
    # 'echo "123" | sudo -S rsync -au {} root@{}:{}'.format(
    #      otter_home,VM_IP, otter_home_parent)
    # rsync_oltpbench_home_cmd =
    # 'echo "123" | sudo -S rsync -au {} root@{}:{}'.format(
    #      oltpbench_home,VM_IP, oltpbench_home_parent)
    # rsync_database_config_cmd =
    # 'echo "123" | sudo -S rsync -au {} root@{}:{}'.format(
    #     database_config_folder, VM_IP, database_config_folder_parent)
    # LOG.info(
    # "fabile.rsync_remote_folder rsync_otter_home={} \n
    #  rsync_oltpbench_home={} \n rsync_database_config={} ".format(
    #     rsync_otter_home_cmd, rsync_oltpbench_home_cmd,
    # rsync_database_config_cmd))
    # exit()
    # remote_exec(VM_IP, rsync_otter_home_cmd)
    # remote_exec(VM_IP, rsync_oltpbench_home_cmd)
    # remote_exec(VM_IP, rsync_database_config_cmd)


def rsync_remote_single(folder, ip, folder_parent):
    rsync_remote_cmd = 'echo "123" | sudo -S rsync -au {} root@{}:{}'.format(
        folder, ip, folder_parent)
    LOG.info("fabfile.rsync_remote_single remote_cmd={}".format(
        rsync_remote_cmd))
    remote_exec(ip, rsync_remote_cmd)


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
    ssh.connect(hostname=host, port=22,
                username='root', password='123')
    # 执行命令  stdout命令结果，stderr错误
    LOG.info("fabfile.remote_exec cmd={}".format(cmd))
    stdin, stdout, stderr = ssh.exec_command(cmd)
    # 获取命令结果
    std_str = str(stdout.read(), encoding="utf-8")
    LOG.info("connect to {} execute {} \n std_out={}".format(VM_IP, cmd, std_str))
    # 关闭连接
    ssh.close()
    return std_str
