#!/bin/bash
# Unstarts an Amazon EC2 cluster
set -e
echo -n "Enter name of cluster to shutdown: "
read name
# Clean up and shut down
rm -rf launch.log
# Note that this technically will allow you to shut down anyone's cluster..
ec2-describe-instances --filter "key-name=$name" | grep INSTANCE | awk '{print $2}' | xargs ec2-terminate-instances
rm -rf $name.pem
ec2-delete-keypair $name
