#! /usr/bin/env bash
# STATIC CONF FILE - THIS DOES NOT CHANGE IN BETWEEN CLUSTERS
# Even though all of these environment variables are set at startup, 
# Accumulo is stupid and still requires setting them inside this file

# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.

if [ -z "$HADOOP_HOME" ]
then
   test -z "$HADOOP_PREFIX"      && export HADOOP_PREFIX=/usr/local/hadoop
else
   HADOOP_PREFIX="$HADOOP_HOME"
fi
test -z "$HADOOP_CONF_DIR"       && export HADOOP_CONF_DIR="$HADOOP_PREFIX/conf"

test -z "$JAVA_HOME"             && export JAVA_HOME=/usr/lib/jvm/jdk1.6.0_45
test -z "$ZOOKEEPER_HOME"        && export ZOOKEEPER_HOME=/usr/local/zookeeper
test -z "$ACCUMULO_LOG_DIR"      && export ACCUMULO_LOG_DIR=$ACCUMULO_HOME/logs
if [ -f ${ACCUMULO_HOME}/conf/accumulo.policy ]
then
   POLICY="-Djava.security.manager -Djava.security.policy=${ACCUMULO_HOME}/conf/accumulo.policy"
fi
test -z "$ACCUMULO_TSERVER_OPTS" && export ACCUMULO_TSERVER_OPTS="${POLICY} -Xmx384m -Xms384m "
test -z "$ACCUMULO_MASTER_OPTS"  && export ACCUMULO_MASTER_OPTS="${POLICY} -Xmx128m -Xms128m"
test -z "$ACCUMULO_MONITOR_OPTS" && export ACCUMULO_MONITOR_OPTS="${POLICY} -Xmx64m -Xms64m" 
test -z "$ACCUMULO_GC_OPTS"      && export ACCUMULO_GC_OPTS="-Xmx64m -Xms64m"
test -z "$ACCUMULO_GENERAL_OPTS" && export ACCUMULO_GENERAL_OPTS="-XX:+UseConcMarkSweepGC -XX:CMSInitiatingOccupancyFraction=75"
test -z "$ACCUMULO_OTHER_OPTS"   && export ACCUMULO_OTHER_OPTS="-Xmx128m -Xms64m"
export ACCUMULO_LOG_HOST=`(grep -v '^#' $ACCUMULO_HOME/conf/monitor ; echo localhost ) 2>/dev/null | head -1`
