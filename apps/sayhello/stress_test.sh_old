#!/bin/bash

SUBMIT_COUNT=100
SUBMIT_DELAY=$((3*60))

for i in $(seq 1 $SUBMIT_COUNT)
do
  echo "Submitting job #$i"
  TMP=$(mktemp)
  curl -i -H "Content-Type: application/json" -X POST -d '{"application":"2","description":"sayhello@csgfsdk test run", "arguments": ["\"I am saying hello!\""],  "output_files": [{"name":"sayhello.data"}], "input_files": [{"name":"sayhello.sh"},{"name":"sayhello.txt"}]}' http://localhost:8888/v1.0/tasks?user=brunor > $TMP
  id=$(cat $TMP | grep id | awk -F":" '{ print $2 }' | tr \" ' ' | awk '{print $1}' | xargs echo)
  echo "id for job $i = $id"
  curl -i -F "file[]=@sayhello.txt" -F "file[]=@sayhello.sh" http://localhost:8888/v1.0/tasks/$id/input?user=brunor
  rm -f $TMP
  sleep $SUBMIT_DELAY
done
