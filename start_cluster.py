#!/usr/bin/python 
# rostislav.tsiomenko@gmail.com
# This script managers starting up an Amazon EC2 cluster
# EC2 API tools must be installed and configured properly
# TODO: 
# Implement error checking that shuts down any started nodes if anything fails
# Tweak Hadoop and Accumulo performance settings in conf files (heap, etc)

import re
import sys
import time
import subprocess

AMI_ID = "ami-05ca886c"
AMI_type = "m1.large"

# Get user preferences and create EC2 key
# Keyname is the identifier entered by the user, used to name EC2 key
keyname = raw_input("Enter unique identifier for cluster: ")
# Limit is not actually checked; it would not make sense to launch less than
# 3 (at least 1 master and 2 slaves) and Amazon runs into problems launching more than 12-14 instances at once; Zookeeper prefers odd numbers
nodes = raw_input("Enter amount of nodes to launch (3 to 14): ")
key_output = subprocess.check_output("ec2-create-keypair " + keyname, shell=True)
key_regex = re.search(r'(-----BEGIN.*END RSA PRIVATE KEY-----)', key_output, re.DOTALL)
key_pem = keyname + ".pem"
key_file = open(key_pem, "w")
key_file.write(key_regex.group(1))
key_file.close()
subprocess.call("chmod 400 " + key_pem, shell=True)

# Start EC2 instances, note block mappings for m1.large
run_call = subprocess.check_output("ec2run " + AMI_ID + " -t " + AMI_type + " -k " + keyname + " -n " + nodes + " -b /dev/sdb=ephemeral0 -b /dev/sdc=ephemeral1", shell=True)
ready = False

# Wait until all EC2 instances are ready
while not ready:
    result = subprocess.check_output('ec2-describe-instances --filter "key-name=' + keyname + '"', shell=True)
    instance_state = re.compile(r'internal\t([a-z]*)\s')
    instcount = 0
    for state in instance_state.findall(result):
        if state == "running":
            instcount += 1
    if instcount == int(nodes):
        ready = True
    else:
        print "."
        time.sleep(15)

# New filter for 'running' must be made, otherwise previously terminated
# instances with the same name might show up
output = subprocess.check_output('ec2-describe-instances --filter "key-name=' + keyname + '" --filter "instance-state-name=running"', shell=True)
print "\nAmazon instances launched successfully, commencing set-up.\n"

# Get IPs of started instances
ami_id = re.compile(r'INSTANCE\t(.*)\tami')
public_ip = re.compile(r'\t(ec2.*com)\t')
private_ip = re.compile(r'\t(ip.*internal)\t')
public_ip_list = public_ip.findall(output)
private_ip_list = private_ip.findall(output)

# Set up disks, this must be made modular to use instances other than m1.large
print "Setting up partitions, permissions, etc..."
# This sleep is necessary so that instances have a few more seconds to start up
# Otherwise they will sometimes refuse SSH connections 
time.sleep(10)
for server in public_ip_list:
    # Run start.sh on node; other commands should be merged into the script
    run_start = subprocess.check_output("ssh -i " + key_pem + " -o ConnectTimeout=30 -o BatchMode=yes -o \"UserKnownHostsFile /dev/null\" -o StrictHostKeyChecking=no ubuntu@" + server + " './start.sh;chmod 755 /mnt/hdfs;chmod 755 /mnt2/hdfs;mkdir /usr/local/accumulo/logs' 2> /dev/null", shell=True)

# Set up passwordless SSH between nodes
print "Setting up SSH keys between instances..."
# Write down public and private IPs of slaves to put on the master node
master = public_ip_list[0]
slaves = open("nodes.txt", "w")
for server in public_ip_list[1:]:
    slaves.write("%s\n" % server)
slaves.close()
internal_addresses = open("internal_add.txt", "w")
for address in private_ip_list:
    internal_addresses.write("%s\n" % address)
internal_addresses.close()

# This takes care of passwordless SSH between nodes
master_host_verf = subprocess.check_output("./keyauth.exp " + master + " " + keyname, shell=True)
copy_addresses = subprocess.check_output("scp -i " + key_pem + " nodes.txt internal_add.txt " + key_pem + " ubuntu@" + master + ":/home/ubuntu", shell=True)
ssh_keygen = subprocess.check_output("ssh -i " + key_pem + " -o BatchMode=yes ubuntu@" + master + " 'ssh-keygen -q -t rsa -P \"\" -f ~/.ssh/id_rsa;cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys;python keys.py;rm -rf /usr/local/hadoop/conf/slaves;cat ~/nodes.txt >> /usr/local/hadoop/conf/slaves'", shell=True)

# Set up services

print "Setting up and starting Hadoop..."

# Create core-site.xml
core_site = open("core-site.xml", "w")
core_site.write("<?xml version=\"1.0\"?>\n<configuration>\n")
core_site.write("<property>\n<name>\nfs.default.name\n</name>\n<value>hdfs://")
core_site.write(master)
core_site.write(":9000</value>\n</property>\n</configuration>")
core_site.close()

# Create mapred-site.xml
mapred_site = open("mapred-site.xml", "w")
mapred_site.write("<?xml version=\"1.0\"?>\n<configuration>\n<property>\n")
mapred_site.write("<name>mapred.job.tracker</name>")
mapred_site.write("<value>" + master + ":9001</value>\n")
mapred_site.write("</property><property><name>mapred.local.dir</name>")
mapred_site.write("<value>/mnt/mapred,/mnt2/mapred</value></property>")
mapred_site.write("</configuration>")
mapred_site.close()

# Copy hadoop conf files
for server in public_ip_list:
    copy = subprocess.check_output('scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i ' + keyname + '.pem core-site.xml mapred-site.xml static/hdfs-site.xml ubuntu@' + server + ':/usr/local/hadoop/conf > /dev/null 2>&1', shell=True)

# Now start Hadoop
start_hadoop = subprocess.check_output("ssh -i " + key_pem + " -o ConnectTimeout=30 -o BatchMode=yes ubuntu@" + master + " '/usr/local/hadoop/bin/hadoop namenode -format -force;/usr/local/hadoop/bin/start-dfs.sh;/usr/local/hadoop/bin/start-mapred.sh' 2> /dev/null", shell=True)

# Write Zookeeper config
zoo_config = open("zoo.cfg", "w")
zoo_config.write("tickTime=2000\ndataDir=/usr/local/zookeeper/data\n")
zoo_config.write("clientPort=2181\ninitLimit=5\nsyncLimit=2\nmaxClientCnxns=250\n")

# Write quorum servers to Zookeeper config
server_count = 1
for server in private_ip_list:
    zoo_config.write("server." + str(server_count) + "=" + server + ":2888:3888\n")
    server_count += 1
zoo_config.close()

# Copy the resulting zoo.cfg to the master and slaves
for server in public_ip_list:
    copy_zoo = subprocess.check_output('scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i ' + keyname + '.pem zoo.cfg ubuntu@' + server + ':/usr/local/zookeeper/conf  > /dev/null 2>&1', shell=True)

# Start zookeeper on all servers
zoo_count = 1
for server in public_ip_list:
    start_zookeeper = subprocess.check_output("ssh -i " + key_pem + " -o ConnectTimeout=30 -o BatchMode=yes -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no ubuntu@" + server + " 'mkdir /usr/local/zookeeper/data;echo " + str(zoo_count) + " > /usr/local/zookeeper/data/myid;/usr/local/zookeeper/bin/zkServer.sh start' 2> /dev/null", shell=True)
    zoo_count += 1

# Write accumulo-site.xml; note accumulo-env.sh is static and doesn't change
accumulo = open("accumulo-site.xml", "w")
accumulo.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>")
accumulo.write("\n<configuration>\n<property>\n<name>instance.zookeeper.host</name>\n")
accumulo.write("<value>")
comma_count = 1
for server in private_ip_list:
    accumulo.write(server + ":2181")
    if comma_count < len(private_ip_list):
        accumulo.write(",")
    comma_count += 1
accumulo.write("</value>\n</property>")
accumulo.close()

# Merge dynamic config with stock variables
merge_accumulo_config = subprocess.check_output('cat ~/static/accumulo-site.part >> accumulo-site.xml', shell=True)

# Create master and slave files
acc_master = open("masters", "w")
acc_master.write(private_ip_list.pop(0))
acc_master.close()
acc_slaves = open("slaves", "w")
for slave in private_ip_list:
    acc_slaves.write(slave + "\n")
acc_slaves.close()

# Copy everything over to the master
copy_accumulo_config = subprocess.check_output('scp -i ' + keyname + '.pem static/accumulo-env.sh accumulo-site.xml masters slaves ubuntu@' + master + ':/usr/local/accumulo/conf', shell=True)

# Copy over an additional accumulo script (that should be on the AMI, really) that starts Accumulo
copy_accumulo_scripts = subprocess.check_output('scp -i ' + keyname + '.pem accumulo/internalauth.exp accumulo/accumulo.py ubuntu@' + master + ':~', shell=True)

# Start accumulo
run_accumulo_scripts = subprocess.check_output("ssh -i " + keyname + ".pem ubuntu@" + master + " 'python accumulo.py;rm -rf *.exp;rm -rf start.sh'", shell=True)

# Write everything to log for posterity
log = open("launch.log", "w")
log.write("\nCluster name: %s\n" % keyname)
log.write("Number of instances: %s\n" % nodes)
log.write("Master node public IP: %s\n" % master)
for server in public_ip_list[1:]:
    log.write("Slave node public IP: %s\n" % server)
log.close()

# Clean up
subprocess.call("rm -rf accumulo-site.xml core-site.xml nodes.txt internal_add.txt masters slaves mapred-site.xml zoo.cfg", shell=True)

print "Set-up is now complete."
print "Log in to the master node with\n\n ssh -i " + keyname + ".pem ubuntu@" + master
print "\n\nAddresses of the other instances and other details can be found in launch.log."
print "\nUse " + master + ":50030, :50070, and :50095 to access web interfaces."
print "\nThe billing rate is $" + str(0.24*int(nodes)) + " per hour."
print "Please remember to shutdown the cluster when done using shutdown_cluster.\n"
