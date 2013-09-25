#!/bin/bash
# cook_ami.sh allows the `cooking` of a new AMI to Amazon EC2.
# Requires the public hostname and keypair file of a running instance to image
# Outputs a new AMI id to use
#
# Please be aware that updating the AMI will overwrite older ones, because the
# script always uses the same S3 bucket. This means that if you do not
# update the AMI_ID inside start_cluster.sh after updating the AMI, the script will
# hang at `Still launching..` forever.
#
# The way to fix this would be to implement incremental updates, with a new S3
# bucket for every AMI, so that they do not overwrite each other.
# This process is taken directly from http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/creating-snapshot-s3-linux.html
# If using, change script to use your EC2 user id, access/secret keys, S3 bucket name, 
# and make sure pk.pem and cert.pem exist
# In fact, these should be changed to variables + a .cfg file...

set -e
echo -n "Enter public hostname/IP of AMI to image: "
read host
echo -n "Enter name of SSH keypair file to connect: "
read key
echo "Copying private key and X.509 cert to /tmp..."
ssh -i $key ubuntu@$host 'sudo mkdir -p /tmp/cert;sudo chmod 777 /tmp/cert'

# You will need to supply pk.pem and cert.pem yourself
scp -i $key static/pk.pem static/cert.pem ubuntu@$host:/tmp/cert
echo "Running ec2-bundle-vol, this might take a few minutes..."
ssh -i $key ubuntu@$host 'export EC2_HOME=/usr/local/ec2ami;echo | sudo -E /usr/local/ec2ami/bin/ec2-bundle-vol -k /tmp/cert/pk.pem -c /tmp/cert/cert.pem --no-filter --exclude /tmp,/mnt -u YOURUSERID'
echo "Copying bundle to S3 bucket, this might take a few minutes..."
ssh -i $key ubuntu@$host 'export EC2_HOME=/usr/local/ec2ami;/usr/local/ec2ami/bin/ec2-upload-bundle -b YOURS3BUCKET -m /tmp/image.manifest.xml -a YOURACCESSKEY -s YOURSECRETKEY'

# This is technically not needed and should be automated with the current date or a random name
echo -n "Enter a name for the updated image: "
read name
echo "Registering new AMI with Amazon..."
ec2-register YOURS3BUCKET/image.manifest.xml -n $name -O YOURACCESSKEY -W YOURSECRETKEY
