#!/bin/bash

SUBMIT_COUNT=100
SUBMIT_DELAY=10 

for i in $(seq 1 $SUBMIT_COUNT)
do
  echo "Submitting job #$i"
  TMP=$(mktemp)
  curl -i -H "Content-Type: application/json" -X POST -d '{"application":"1","description":"helloworld@csgfsdk test run" }' http://localhost:8888/v1.0/tasks?user=brunor > $TMP
  id=$(cat $TMP | grep id | awk -F":" '{ print $2 }' | tr \" ' ' | awk '{print $1}' | xargs echo)
  echo "id for job $i = $id"
  curl -i -X POST http://localhost:8888/v1.0/tasks/$id/input?user=brunor
  rm -f $TMP
  sleep $SUBMIT_DELAY
done
