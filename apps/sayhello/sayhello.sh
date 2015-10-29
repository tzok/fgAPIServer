#!/bin/bash
INPFILE=sayhello.txt
DATAFILE=sayhello.data
if [ "${1}" = "" ]; then
  SAYS="nothing"
else
  SAYS=$1
fi
echo "User "$(whoami)" says: $SAYS" | tee -i $DATAFILE 
if [ -f "$INPFILE" ]; then
  echo "Receiving sayhello.txt file"
  cat $INPFILE 
else
  echo "Did not find $INPFILE"
fi
