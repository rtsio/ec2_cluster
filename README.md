This package enables a user to start and stop EC2 clusters. Using
a preconfigured instance-storage based AMI (which can be further 
'cooked' to install additional services) it will autoconfigure
Hadoop, Zookeeper, and Accumulo across any number of EC2 nodes, much
more cleanly than Apache Whirr.

To start a cluster, run python start_cluster.py
To shutdown a running cluster, run ./shutdown_cluster.sh
To update the Amazon AMI, run ./cook_ami.sh

Note that these scripts use the old, more common EC2 API tools on Java, 
for which the env variables must be configured. You will also have to
set up your access/secret keys and certificates for everything to work
properly (these have been excluded from the public repo).
