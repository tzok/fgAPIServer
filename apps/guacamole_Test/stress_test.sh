#!/bin/bash
FGPROTO=http
FGHOST=localhost
FGPORT=8888
FGAPIV=v1.0
APP_ID=<app_id> # Place here the appId
USER=<user_id>  # Place here the userId
SUBMIT_COUNT=1
SUBMIT_DELAY=10 
SESSION_TOKEN='<place here your session token>'

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

if [ "$APP_ID" = "" ]; then
  echo "Unable to identify application '"$APP_NAME"'"
  exit 1
fi

# Submitting ...
# Session token for guactest could be built specifying a special user
# having only the userdata right; by default it uses SESSION_TOKEN
UDSSTKN=$SESSION_TOKEN
FGEXTIP=$(curl curlmyip.org)
for i in $(seq 1 $SUBMIT_COUNT)
do
  echo "Submitting job #$i"
  TMP=$(mktemp)
  CMD="curl -H \"Content-Type: application/json\" -H \"Authorization: $SESSION_TOKEN\" -X POST -d '{\"application\":\""$APP_ID"\",\"description\":\"guactest run\",\"arguments\": [\"$FGEXTIP\",\"$FGPORT\",\"$FGAPIV\",\"$SESSION_TOKEN\"]}' \"$FGPROTO://$FGHOST:$FGPORT/$FGAPIV/tasks$FILTER\" 2>/dev/null | tee $TMP"
  eval $CMD
  id=$(cat $TMP | jq .id | xargs echo)
  if [ "$id" != "" ]; then
    IOSANDBOX=$(curl "$FGPROTO://$FGHOST:$FGPORT/$FGAPIV/tasks/$id$FILTER" 2>/dev/null| jq .iosandbox | xargs echo)
    echo "id for job $i = $id"
    echo "io-sandbox: $IOSANDBOX"
    cat >$IOSANDBOX/guactest_taskinfo.txt <<EOF
task_id=${id}
EOF
    # Prepare input file with the task_id and send it as input file
    curl -F \"file[]=@$IOSANDBOX/guactest_taskinfo.txt\" \"$FGPROTO://$FGHOST:$FGPORT/$FGAPIV/tasks/$id/input$FILTER\" 2>/dev/null
  fi
  rm -f $TMP
  if [ $i -ne $SUBMIT_COUNT ]; then
    sleep $SUBMIT_DELAY
  fi
done
echo "Done"
