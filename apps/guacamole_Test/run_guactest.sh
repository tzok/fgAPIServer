#!/bin/bash
#
# run_guactest.sh - This script demonstrate guacamole usage with the futuregateway 
#
GUACUSER=guactest # Username to grant acces via Guacamole

#
# Retrieve arguments
#

# FutureGateway Protocol http/https
if [ "$1" != "" ]; then
  FGPROTO=$1
fi
# FutureGateway Host
if [ "$2" != "" ]; then
  FGHOST=$2
fi
# FutureGateway Port
if [ "$3" != "" ]; then
  FGPORT=$3
fi
# FutureGateway version
if [ "$4" != "" ]; then
  FGVERS=$4
fi
# FutureGateway session token
if [ "$5" != "" ]; then
  SESSION_TOKEN=$5
fi

# Check existence of task_id info
if [ ! -f guactest_taskinfo.txt ]; then
  echo "Unable to find task specific information file 'guactest_taskinfo.txt'"
  exit 0
fi
TASK_ID=$(cat guactest_taskinfo.txt | grep task_id | awk -F'=' '{ print $2}' | xargs echo)
echo "Task info: '"$TASK_ID"'"

# Now install curl if it does not exists
CURL=$(which curl)
YUM=$(which yum)
BREW=$(which yum)
APTGET=$(which apt-get)
if [ "$CURL" = "" ]; then
  if [ "$YUM" != "" ]; then
    yum install curl -y
    RES=$?
  elif [ "$BREW" != "" ]; then
    brew install curl
    RES=$?
  elif [ "$APTGET" != "" ]; then
    apt-get update
    apt-get install curl
    RES=$?
  else
    echo "None of the supported installation methods found: apt-get, brew, yum"
    RES=1
  fi
  if [ $RES -ne 0 ]; then
    echo "Installation of curl failed; exiting ..."
    exit 0
  fi
fi
# Build the FutureGateway endpoint and test it
FGTEST=$(curl $FGPROTO://$FGHOST:$FGPORT/$FGVERS/ 2>/dev/null)
if [ "$FGTEST" == "" ]; then
  echo "Unable to contact APIServer with: '"$FGPROTO"://"$FGHOST":"$FGPORT"/"$FGVERS"/'" 
  exit 0
fi
echo "Successfully contacted APIServer with: '"$FGPROTO"://"$FGHOST":"$FGPORT"/"$FGVERS"/'"

# Now it is possible to send guactest credentials
adduser --disabled-password --gecos "" $GUACUSER 
RANDPASS=$(openssl rand -base64 32 | head -c 12)
sudo usermod --password $(echo "$RANDPASS" | openssl passwd -1 -stdin) $GUACUSER

# Store credentials into APIServer
IPADDR=$(curl curlmyip.org) # !!! This is not a good solution; Access data must be stored in USERDATA by the adaptor
PATCHDATA="'{\"runtime_data\": [ { \"data_name\": \"ipaddress\", \"data_value\": \"$IPADDR\", \"data_desc\": \"Guacamole test IP address\"},{ \"data_name\": \"username\", \"data_value\": \"$GUACUSER\", \"data_desc\": \"Guacamole test user name\"},{ \"data_name\": \"password\", \"data_value\": \"$RANDPASS\", \"data_desc\": \"Guacamole test user password\"} ]}'"
CMD="curl -H \"Content-Type: application/json\" -H \"Authorization: $SESSION_TOKEN\" -X PATCH -d $PATCHDATA "$FGPROTO://$FGHOST:$FGPORT/$FGVERS/tasks/$TASK_ID$FILTER" 2>/dev/null | tee curl_result.txt"
eval $CMD

# Now leave running the instantiated resource for a limited amount of time
echo "Entering resource lifetime loop ..."
CHKFILE=$(mktemp)
LIFETIME=$((60*60*2)) # 2 hours
for i in $(seq 1 $LIFETIME); do
  if [ ! -e $CHKFILE ]; then
    echo "Control file does not exists; exiting ..."
    break
  else
    echo "${i}/${LIFETIME}" > $CHKFILE
    sleep 1
  fi
done
rm -f $CHKFILE

if [ $i -lt $LIFETIME ]; then
  echo "Execution interrupted at ${i}/${LIFETIME}"
else
  echo "The resource expired its lifeyime of $LIFETIME seconds"
fi

# Notify end
echo "Done"
