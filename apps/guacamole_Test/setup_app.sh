#!/bin/bash
#
# setup_app.sh - Script to install an application on FutureGateway
#
FGPROTO=http
FGHOST=localhost
FGPORT=8888
FGAPIV=v1.0
APPNAME="guactest@tosca"
APPDESC="guacamole tester application on tosca"
OUTCOME="JOB"
INFRADESC="guactest infrastructure at 90.147.170.152:80"
INFRANAME="guactest_test@BA"
FILESPATH="$FGLOCATION/fgAPIServer/apps/guacamole_Test"
SESSION_TOKEN='<place here your session token>'
USER='' # change this if you want to run on behalf of this user

# Session token as 1st argument (if present)
if [ "$1" != "" ]; then
  SESSION_TOKEN=$1
fi

# User name as 2nd argument (if present)
if [ "$2" != "" -a "$USER" == "" ]; then
  USER=$2
fi

# Prepare the filter string
if [ "$USER" != "" ]; then
  FILTER="?user=$USER"
fi

# Prepare data setting for curl command
CURLDATA="'{\"infrastructures\": [{\"description\": \"$APPDESC\",\"parameters\": [{\"name\": \"tosca_endpoint\",\"value\": \"tosca://90.147.170.152:80/orchestrator/deployments\"},{\"name\": \"tosca_token\",\"value\": \"11223344556677889900AABBCCDDEEFF\"},{\"name\": \"tosca_template\",\"value\": \"guactest_template.yaml\"},{\"name\": \"tosca_parameters\",\"value\": \"wait_ms=30000&max_waits=30\"}],\"enabled\": true,\"virtual\": false,\"name\": \"$INFRANAME\"}],\"parameters\": [{\"name\": \"target_executor\",\"value\": \"SimpleTosca\",\"description\": \"\"},{\"name\": \"jobdesc_executable\",\"value\": \"run_guactest.sh\",\"description\": \"\"},{\"name\": \"jobdesc_output\",\"value\": \"stdout.txt\",\"description\": \"\"},{\"name\": \"jobdesc_error\",\"value\": \"stderr.txt\",\"description\": \"\"}],\"enabled\": true,\"input_files\": [{\"override\": false,\"path\": \"$FILESPATH\",\"name\": \"guactest_template.yaml\"},{\"override\": false,\"path\": \"$FILESPATH\",\"name\": \"run_guactest.sh\"},{\"override\": false,\"path\": \"\",\"name\": \"guactest_taskinfo.txt\"}],\"name\": \"$APPNAME\",\"description\": \"$APPDESC\",\"outcome\": \"$OUTCOME\"}'"

# Setup application, retrieve id and sets stress_test app_id
TMP=$(mktemp)
CMD="curl -H \"Content-Type: application/json\" -H \"Authorization: $SESSION_TOKEN\" -X POST -d $CURLDATA \"$FGPROTO://$FGHOST:$FGPORT/$FGAPIV/applications$FILTER\" 2>/dev/null >$TMP"
eval $CMD | tee $TMP
APPID=$(cat $TMP | jq .id | xargs echo)
sed -i -e "s/<app_id>/$APPID/" stress_test.sh
sed -i -e "s/<user_id>/$USER/" stress_test.sh
rm -f $TMP
if [ "$APPID" != "" ]; then
  echo "Application '"$APPNAME"' successfully installed with id: '"$APPID"'"
else
  echo "Failed to install application: '"$APPNAME"'"
  exit 1
fi
echo "Done"

