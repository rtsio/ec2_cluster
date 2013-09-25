#!/bin/bash
sudo sysctl -w vm.swappiness=0
echo -e "ubuntu\t\tsoft\tnofile\t65536" | sudo tee --append /etc/security/limits.conf
echo -e "ubuntu\t\thard\tnofile\t65536" | sudo tee --append /etc/security/limits.conf

sudo umount /mnt;
sudo /sbin/mkfs.xfs -f /dev/xvdb;
sudo mount -o noatime /dev/xvdb /mnt;
sudo rm -rf /mnt2;
sudo mkdir /mnt2;
sudo /sbin/mkfs.xfs -f /dev/xvdc;
sudo mount -o noatime /dev/xvdc /mnt2;
sudo chown -R ubuntu /mnt
sudo chown -R ubuntu /mnt2

mkdir /mnt/hdfs
mkdir /mnt/namenode
mkdir /mnt/mapred
mkdir /mnt/walogs
mkdir /mnt2/hdfs
mkdir /mnt2/mapred


