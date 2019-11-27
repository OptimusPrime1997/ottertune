#!/bin/bash
for dir in $(ls /sys/bus/mdev/devices/)
do
	echo 1 > /sys/bus/mdev/devices/$dir/remove
done
#wait for command complete
sleep 1