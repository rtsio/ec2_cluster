#!/usr/bin/python 
# Launches Accumulo, run on master EC2 node
import subprocess

# Grab default metrics and log files - should be incorporated into the AMI
copylog = subprocess.check_output('cp /usr/local/accumulo/conf/examples/1GB/standalone/log4j.properties /usr/local/accumulo/conf', shell=True)
copymetric = subprocess.check_output('cp /usr/local/accumulo/conf/examples/1GB/standalone/accumulo-metrics.xml /usr/local/accumulo/conf', shell=True)

# Copy conf files to slaves
nodes = open("nodes.txt")
node_list = nodes.readlines()
nodes.close()
keyname = subprocess.check_output('ls | grep *.pem', shell=True).rstrip()
for node in node_list:
	node = node.rstrip()
	copy_all = subprocess.check_output('scp /usr/local/accumulo/conf/accumulo-site.xml /usr/local/accumulo/conf/accumulo-env.sh /usr/local/accumulo/conf/log4j.properties /usr/local/accumulo/conf/accumulo-metrics.xml /usr/local/accumulo/conf/masters /usr/local/accumulo/conf/slaves ubuntu@' + node + ':/usr/local/accumulo/conf', shell=True)

# Set up passwordless SSH with internal hostnames (required for Accumulo)	
internal = open("internal_add.txt")
internal_ips = internal.readlines()
for ip in internal_ips:
	validate_key = subprocess.check_output('./internalauth.exp ' + ip, shell=True)
internal.close()

# Init and start 
start_accumulo = subprocess.check_output('/usr/local/accumulo/bin/accumulo init --instance-name ' + keyname[:(len(keyname)-4)] + ' --password ' + keyname[:(len(keyname)-4)], shell=True)
start_accumulo_dfs = subprocess.check_output('/usr/local/accumulo/bin/start-all.sh', shell=True)
