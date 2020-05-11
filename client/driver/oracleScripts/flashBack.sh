#!/bin/sh

RESTORE_POINT="$1"

# Flash back
sqlplus / as sysdba <<EOF
    SHUTDOWN IMMEDIATE
    STARTUP MOUNT
    FLASHBACK DATABASE TO RESTORE POINT $RESTORE_POINT;
    ALTER DATABASE OPEN RESETLOGS;
quit
EOF

