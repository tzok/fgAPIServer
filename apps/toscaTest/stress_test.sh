#!/bin/bash
APP_ID=<app_id> # Place here the appId
USER=brunor
SUBMIT_COUNT=1
SUBMIT_DELAY=10 

if [ "$APP_ID" = "" ]; then
  echo "Unable to identify application '"$APP_NAME"'"
  exit 1
fi


for i in $(seq 1 $SUBMIT_COUNT)
do
  echo "Submitting job #$i"
  TMP=$(mktemp)
  CURLDATA="'{\"application\":\"$APP_ID\",\"description\":\"tosca test run\"}'"
  eval curl -i -H "Content-Type: application/json" -X POST -d $CURLDATA http://localhost:8888/v1.0/tasks?user=$USER | tee $TMP 
  id=$(cat $TMP | grep id | awk -F":" '{ print $2 }' | tr \" ' ' | awk '{print $1}' | xargs echo)
  echo "id for job $i = $id"
  curl -i -X POST http://localhost:8888/v1.0/tasks/$id/input?user=brunor
  rm -f $TMP
  if [ $i -ne $SUBMIT_COUNT ]; then
    sleep $SUBMIT_DELAY
  fi
done
