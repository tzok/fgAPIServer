#!/bin/bash
#
# setup_app.sh - Script to install an application on FutureGateway
#
USER=brunor
APPNAME="amber@docker.CT"
APPDESC="amber tester application with docker"
OUTCOME="JOB"
INFRADESC="amber test at stack-server-02.ct.infn.it"
INFRANAME="amber_test@CT_stack02"
FILESPATH="$FGLOCATION/fgAPIServer/apps/amber_Docker"

# Prepare data setting for curl command
CURLDATA="'{\"infrastructures\": [{\"description\": \"$APPDESC\",\"parameters\": [{\"name\": \"jobservice\",\"value\": \"rocci://stack-server-02.ct.infn.it:8787\"},{\"name\": \"os_tpl\",\"value\": \"e39c23f8-9a44-4cfe-aaa4-8f5d46c2da30\"},{\"name\": \"resource_tpl\",\"value\": \"m1-medium\"},{\"name\": \"attributes_title\",\"value\": \"attributes_title\"},{\"name\": \"eToken_host\",\"value\": \"etokenserver2.ct.infn.it\"},{\"name\": \"eToken_port\",\"value\": \"8082\"},{\"name\": \"eToken_id\",\"value\": \"bc779e33367eaad7882b9dfaa83a432c\"},{\"name\": \"voms\",\"value\": \"indigo\"},{\"name\": \"voms_role\",\"value\": \"indigo\"},{\"name\": \"rfc_proxy\",\"value\": \"true\"},{\"name\": \"disable-voms-proxy\",\"value\": \"false\"},{\"name\": \"proxy-renewal\",\"value\": \"false\"},{\"name\": \"secured\",\"value\": \"false\"},{\"name\": \"link\",\"value\": \"/network/public\"},{\"name\": \"sshport\",\"value\": \"2222\"}],\"enabled\": true,\"virtual\": false,\"name\": \"$INFRANAME\"}],\"parameters\": [{\"name\": \"target_executor\",\"value\": \"SimpleTosca\",\"description\": \"\"},{\"name\": \"jobdesc_executable\",\"value\": \"/bin/bash\",\"description\": \"\"},{\"name\": \"jobdesc_arguments\",\"value\": \"run_amber.sh\",\"description\": \"\"},{\"name\": \"jobdesc_output\",\"value\": \"stdout.txt\",\"description\": \"\"},{\"name\": \"jobdesc_error\",\"value\": \"stderr.txt\",\"description\": \"\"}],\"enabled\": true,\"input_files\": [{\"override\": false,\"path\": \"$FILESPATH\",\"name\": \"tosca_template.yaml\"},{\"override\": false,\"path\": \"$FILESPATH\",\"name\": \"run_amber.sh\"},{\"override\": false,\"path\": \"$FILESPATH\",\"name\": \"in.tgz\"}],\"name\": \"$APPNAME\",\"description\": \"$APPDESC\",\"outcome\": \"$OUTCOME\"}'"

# Setup application, retrieve id and sets stress_test app_id
TMP=$(mktemp)
CMD="curl -H \"Content-Type: application/json\" -X POST -d $CURLDATA http://localhost:8888/v1.0/applications?user=$USER" 
# echo $CMD
eval $CMD | tee $TMP
#APPID=$(cat $TMP | grep "\"id\"" | awk -F":" '{ print $2 }' | xargs echo | sed s/,//g)
APPID=$(cat $TMP | jq .id | xargs echo)
sed -i -e "s/<app_id>/$APPID/" stress_test.sh
rm -f $TMP
