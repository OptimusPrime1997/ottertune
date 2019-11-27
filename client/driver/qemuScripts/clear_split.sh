#!/bin/bash
sudo bash /home/ljh/exp/scripts/redhat-nvme/remove_mdev_device.sh
N=`sudo fdisk -l /dev/nvme0n1 | grep -c "/dev/nvme0n1p"`
echo "/dev/nvme0n1 has "$N" parts."
if [ $N -gt 0 ];then
	str=''
	i=1
	if [ $i -ge 4 ];then
		i=$((i+1))
	fi
	while [ $i -lt $N ];do
		str=${str}'d\n\n'
		i=$(($i+1))
	done
	str=${str}'d\n'
	str=${str}'w\n'
	echo -e $str
	echo -e $str | sudo fdisk /dev/nvme0n1	
else
	sudo fdisk /dev/nvme0n1
fi
