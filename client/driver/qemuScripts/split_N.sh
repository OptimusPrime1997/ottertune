#!/bin/bash
#to do:if mounted, umount it

N=$1
if [ $N -lt 2 ];then
	exit
fi
SIZE=$((447/$N))
SIZE=${SIZE//.*/}
str=''
if [ $N -lt 4 ];then
	i=1
	while [ $i -lt $N ];do
		str=${str}'n\n\n\n\n+'${SIZE}'G\n'
		i=$(($i+1))
	done
	str=${str}'n\n\n\n\n\n'
	str=${str}'w\n'
else
	i=1
	while [ $i -lt 4 ];do
		str=${str}'n\n\n\n\n+'${SIZE}'G\n'
		i=$(($i+1))
	done
	str=${str}'n\n\n\n\n\n'
	i=5
	while [ $i -le $(($N)) ];do
		str=${str}'n\n\n+'${SIZE}'G\n'
		i=$(($i+1))
	done
	str=${str}'n\n\n\n\n'
	str=${str}'w\n'
fi

echo -e $str
echo -e $str | sudo fdisk /dev/nvme0n1
