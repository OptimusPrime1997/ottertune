import os

# ==========================================================
#  HOST LOGIN
# ==========================================================

# Location of the database host relative to this driver
# Valid values: local, remote, or docker
# HOST_CONN = 'local'
HOST_CONN = 'remote'

# The name of the Docker container for the target database
# (only required if HOST_CONN = docker)
CONTAINER_NAME = None  # e.g., 'postgres_container'

# Host SSH login credentials (only required if HOST_CONN=remote)
# LOGIN_NAME = None
# LOGIN_HOST = None
# LOGIN_PORT = None  # Set when using a port other than the SSH default
LOGIN_NAME = 'root'
LOGIN_HOST = '192.168.122.131'
LOGIN_PORT = '22'

# ==========================================================
#  DATABASE OPTIONS
# ==========================================================

# Either Postgres or Oracle
DB_TYPE = 'postgres'

# Name of the database
DB_NAME = 'tpcc'

# Database username
DB_USER = 'postgres'

# Password for DB_USER
# DB_PASSWORD = 'dbpassword'
DB_PASSWORD = 'test123'

# Database admin username (for tasks like restarting the database)
ADMIN_USER = DB_USER

# Database host address
# DB_HOST = 'localhost'
DB_HOST = '192.168.122.131'

# Database port
DB_PORT = '5432'

# Path to the configuration file on the database server
DB_CONF = '/etc/postgresql/9.6/main/postgresql.conf'

# Path to the directory for storing database dump files
# DB_DUMP_DIR = '/var/lib/postgresql/9.6/main/dumpfiles'
DB_DUMP_DIR = '/mnt/data/'

# Base config settings to always include when installing new configurations
BASE_DB_CONF = {
    'track_counts': 'on',
    'track_functions': 'all',
    'track_io_timing': 'on',
    'autovacuum': 'off',
}

# Name of the device on the database server to monitor the disk usage, or None to disable
# DATABASE_DISK = None
DATABASE_DISK = '/dev/nvme0n1'

# Set this to a different database version to override the current version
# OVERRIDE_DB_VERSION = None
OVERRIDE_DB_VERSION = '9.6'

# POSTGRES-SPECIFIC OPTIONS >>>
PG_DATADIR = '/var/lib/postgresql/9.6/main'

# ORACLE-SPECIFIC OPTIONS >>>
ORACLE_AWR_ENABLED = False
ORACLE_FLASH_BACK = True
RESTORE_POINT = 'tpcc_point'
RECOVERY_FILE_DEST = '/opt/oracle/oradata/ORCL'
RECOVERY_FILE_DEST_SIZE = '15G'

# ==========================================================
#  DRIVER OPTIONS
# ==========================================================

# Path to this driver
DRIVER_HOME = os.path.dirname(os.path.realpath(__file__))

# Path to the directory for storing results
RESULT_DIR = os.path.join(DRIVER_HOME, 'results')

# Path to temp directory
# TEMP_DIR = '/tmp/driver'
TEMP_DIR = DRIVER_HOME

# Path to the directory for storing database dump files
# DB_DUMP_DIR = os.path.join(DRIVER_HOME, 'dumpfiles')
DB_DUMP_DIR = '/mnt/data/'

# Reload the database after running this many iterations
RELOAD_INTERVAL = 10

# The maximum allowable disk usage percentage. Reload the database
# whenever the current disk usage exceeds this value.
MAX_DISK_USAGE = 90

# Execute this many warmup iterations before uploading the next result
# to the website
WARMUP_ITERATIONS = 0

# Let the database initialize for this many seconds after it restarts
# RESTART_SLEEP_SEC = 300
RESTART_SLEEP_SEC = 10

# ==========================================================
#  OLTPBENCHMARK OPTIONS
# ==========================================================

# Path to OLTPBench directory
# OLTPBENCH_HOME = os.path.expanduser('~/oltpbench')
OLTPBENCH_HOME = '/home/ljh/projects/oltpbench/'

# Path to the OLTPBench configuration file
OLTPBENCH_CONFIG = os.path.join(OLTPBENCH_HOME,
                                'config/tpcc_config_postgres.xml')

# Name of the benchmark to run
OLTPBENCH_BENCH = 'tpcc'

# ==========================================================
#  CONTROLLER OPTIONS
# ==========================================================

# Path to the controller directory
# CONTROLLER_HOME = os.path.expanduser('~/ottertune/client/controller')
CONTROLLER_HOME = '/mnt/ottertune/client/controller/'

# Path to the controller configuration file
CONTROLLER_CONFIG = os.path.join(CONTROLLER_HOME,
                                 'config/sample_postgres_config.json')

# ==========================================================
#  LOGGING OPTIONS
# ==========================================================

LOG_LEVEL = 'DEBUG'

# Path to log directory
LOG_DIR = os.path.join(DRIVER_HOME, 'log')

# Log files
DRIVER_LOG = os.path.join(DRIVER_HOME, 'driver.log')
OLTPBENCH_LOG = os.path.join(DRIVER_HOME, 'oltpbench.log')
CONTROLLER_LOG = os.path.join(DRIVER_HOME, 'controller.log')

# ==========================================================
#  WEBSITE OPTIONS
# ==========================================================

# OtterTune website URL
# WEBSITE_URL = 'http://127.0.0.1:8001'
WEBSITE_URL = 'http://192.168.122.1:8001'

# Code for uploading new results to the website
UPLOAD_CODE = 'J687GUPDDPCSPE5BXEIH'

#threshold of convergence
THRESHOLD = 0.015

# threshold times
SMOOTH_COUNT = 3

# base iterations
BASE_ITERATION_NUM = 20
