#!/bin/bash
#
# setup_app.sh - Script to install an application on FutureGateway
#
USER=brunor
APPNAME="hostname@tosca"
APPDESC="hostname tester application on tosca"
OUTCOME="JOB"
INFRADESC="Tosca test at 90.147.170.168:32101"
INFRANAME="tosca_Test@BA"
FILESPATH="$FGLOCATION/fgAPIServer/apps/toscaTest"

# Prepare data setting for curl command
CURLDATA="'{\"infrastructures\": [{\"description\": \"$APPDESC\",\"parameters\": [{\"name\": \"tosca_endpoint\",\"value\": \"tosca://90.147.170.152:80/orchestrator/deployments\"},{\"name\": \"tosca_token\",\"value\": \"11223344556677889900AABBCCDDEEFF\"},{\"name\": \"tosca_template\",\"value\": \"tosca_template.yaml\"},{\"name\": \"tosca_parameters\",\"value\": \"wait_ms=30000&max_waits=30\"}],\"enabled\": true,\"virtual\": false,\"name\": \"$INFRANAME\"}],\"parameters\": [{\"name\": \"target_executor\",\"value\": \"SimpleTosca\",\"description\": \"\"},{\"name\": \"jobdesc_executable\",\"value\": \"tosca_test.sh\",\"description\": \"\"},{\"name\": \"jobdesc_output\",\"value\": \"stdout.txt\",\"description\": \"\"},{\"name\": \"jobdesc_error\",\"value\": \"stderr.txt\",\"description\": \"\"}],\"enabled\": true,\"input_files\": [{\"override\": false,\"path\": \"$FILESPATH\",\"name\": \"tosca_template.yaml\"},{\"override\": false,\"path\": \"$FILESPATH\",\"name\": \"tosca_test.sh\"}],\"name\": \"$APPNAME\",\"description\": \"$APPDESC\",\"outcome\": \"$OUTCOME\"}'"

# Setup application, retrieve id and sets stress_test app_id
TMP=$(mktemp)
CMD="curl -H \"Content-Type: application/json\" -X POST -d $CURLDATA http://localhost:8888/v1.0/applications?user=$USER" 
# echo $CMD
eval $CMD | tee $TMP
#APPID=$(cat $TMP | grep "\"id\"" | awk -F":" '{ print $2 }' | xargs echo | sed s/,//g)
APPID=$(cat $TMP | jq .id | xargs echo)
sed -i -e "s/<app_id>/$APPID/" stress_test.sh
rm -f $TMP
