#!/bin/bash

#QUEUE=$1
#remove nvme module at first
modprobe nvme
rmmod nvme
#load nvme-mdev module
modprobe nvme-mdev
#allocate hw queue
#change code to change the max queue number
modprobe nvme mdev_queues=36

for dir in $(ls /sys/bus/mdev/devices/)
do
        echo 1 > /sys/bus/mdev/devices/$dir/remove
done
#wait for command completed
sleep 1
exit
