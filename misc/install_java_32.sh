#!/bin/bash
# Attempts to download the last Java6 update and manually install it.
# This is due to the fact that some Apache apps are not stable with 7
# Run using `source` or JAVA_HOME will require a reboot
wget --no-cookies --header "Cookie: gpw_e24=http%3A%2F%2Fwww.oracle.com" "http://download.oracle.com/otn-pub/java/jdk/6u45-b06/jdk-6u45-linux-i586.bin"
chmod u+x jdk-6u45-linux-i586.bin
./jdk-6u45-linux-i586.bin
sudo mkdir -p /usr/lib/jvm
sudo mv jdk1.6.0_45 /usr/lib/jvm
sudo update-alternatives --install "/usr/bin/java" "java" "/usr/lib/jvm/jdk1.6.0_45/bin/java" 1
sudo update-alternatives --install "/usr/bin/javac" "javac" "/usr/lib/jvm/jdk1.6.0_45/bin/javac" 1
java=/usr/lib/jvm/jdk1.6.0_45/
export JAVA_HOME=$java
echo export JAVA_HOME=$java >> ~/.bashrc
rm -rf jdk-6u45-linux-i586.bin
