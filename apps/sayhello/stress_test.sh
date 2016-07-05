#!/bin/bash
FGHOST=localhost
FGPORT=8888
FGAPIV=v1.0
SUBMIT_COUNT=10
SUBMIT_DELAY=10
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

# Execute test
for i in $(seq 1 $SUBMIT_COUNT)
do
  echo "Submitting job #$i"
  TMP=$(mktemp)  
  CMD="curl -H \"Content-Type: application/json\" -H \"Authorization: $SESSION_TOKEN\" -X POST -d '{\"application\":\"2\",\"description\":\"sayhello@csgfsdk test run\", \"arguments\": [\"\\\"I am saying hello\\\"\"],  \"output_files\": [{\"name\":\"sayhello.data\"}], \"input_files\": [{\"name\":\"sayhello.sh\"},{\"name\":\"sayhello.txt\"}]}' http://$FGHOST:$FGPORT/$FGAPIV/tasks$FILTER 2>/dev/null >$TMP"    
  echo "Executing: $CMD"
  eval $CMD
  id=$(cat $TMP | jq '.id' | sed s/\"//g)
  status=$(cat $TMP | jq '.status' | sed s/\"//g)
  echo "id for job $i = $id"
  # Submission needs to specify jobs?
  if [ "$status" == "WAITING" ]; then
    CMD="curl -H \"Authorization: $SESSION_TOKEN\" -F \"file[]=@sayhello.txt\" -F \"file[]=@sayhello.sh\" http://$FGHOST:$FGPORT/$FGAPIV/tasks/$id/input$FILTER"    
	echo "Executing: $CMD"
	eval $CMD
  fi
  rm -f $TMP
  if [ $i -lt $SUBMIT_COUNT ]; then
    printf "Waiting $SUBMIT_DELAY seconds for next submission ... "
    sleep $SUBMIT_DELAY
	echo "done"
  fi
done
echo "Submission finished"
