#!/usr/bin/python 
# Manages instance launch by checking whether all instances are ready
import subprocess

localauth = subprocess.check_output('./keyauth.exp', shell=True)
nodes = open("nodes.txt")
node_list = nodes.readlines()
nodes.close()
keyname = subprocess.check_output('ls | grep *.pem', shell=True).rstrip()
for node in node_list:
	node = node.rstrip()
	node_out = subprocess.check_output('./copykey.exp' + ' ' + node + ' ' + keyname, shell=True)
	cat_auth = subprocess.check_output('./catkey.exp' + ' ' + node + ' ' + keyname, shell=True)
