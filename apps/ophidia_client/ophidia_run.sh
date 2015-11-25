#!/bin/bash
#
# ophidia_run.sh
#
# Script that manages ophidia run execution
#
OPHTERM=oph_term
OPHCRDF=oph-credentials.txt
OPHHOST=193.204.199.174
OPHPORT=11732
OPHOPTS="-j"
OPHTERM_JSON="ophterm_out.json"

# Function that produces a timestamp
get_ts() {
 TS=$(date +%y%m%d%H%M%S)
}

# Function to print out log messages
log() {
 mode=$1
 message=$2
 if [ "${mode}" != "" -a "${mode}" = "out" ]; then
   OUT="1"
 else
   OUT="2"
 fi
 get_ts
 if [ "${message}" != "" ]; then
   echo "${TS} ${message}" >&$OUT
 fi
}

#
# Script execution
#
log out "Initializing ophidia_run execution"
# Arguments
ARG1=$1 # GUI Analisys file (json filename) './precip_trend_analysis.json'
ARG2=$2 # GUI args such as: '4 CMCC-CM rcp85 day 0.9 1980_2010 2080_2100 30:45|0:40 /data/repository /home/sysm01/INDIGO'

#OPHPARGS="4 CMCC-CM rcp85 day 0.9 1980_2010 2080_2100 30:45|0:40" # These will come from GUI
OPHPARGS=$ARG2
if [ "${OPHCRDF}" != "" -a -f $OPHCRDF ] ; then
  OPHUSER=$(cat $OPHCRDF  | awk -F: '{ print $1 }')
  OPHPASS=$(cat $OPHCRDF  | awk -F: '{ print $2 }')
else
  OPHUSER=indigo
  OPHPASS=1nD1g0_de
fi
#OPHREPO="/data/repository /home/sysm01/INDIGO"
OPHCRED="-u $OPHUSER -p $OPHPASS"
OPHCONN="-H $OPHHOST -P $OPHPORT"
#OPHTRND="./precip_trend_analysis.json"
OPHTRND=$ARG1
log out "Using following execution data"
log out "  host: '"$OPHHOST"'"
log out "  port: '"$OPHPORT"'"
log out "  user: '"$OPHUSER"'"
log out "  pass: '"$OPHPASS"'"
log out "Executing: '"$OPHTERM"'"
#CMD=$OPHTERM" "$OPHCRED" "$OPHCONN" -e \""$OPHTRND" "$OPHPARGS" "$OPHREPO"\" "$OPHOPTS" > "$OPHTERM_JSON
CMD=$OPHTERM" "$OPHCRED" "$OPHCONN" -e \""$OPHTRND" "$OPHPARGS\"" "$OPHOPTS" > "$OPHTERM_JSON
log out "  Command line: '$CMD'"
eval $CMD
RES=$?
#!NOTE: oph_term returns always 1
#if [ $RES -ne 0 ]; then
#  log err "Error executing $OPHTERM"
#  log out "Unsuccessfully executed $OPHTERM"
#  exit 4
#else
  log out "Successfully executed $OPHTERM"
#fi
if [ -f $OPHTERM_JSON ]; then
  log out "Generating image ..."
  python ophidia_helper.py $OPHTERM_JSON oph-credentials.txt out.png
  RES=$?
  echo "Ret code: "$RES
  #if [ $RES -ne 0 ]; then
  #  log err "Unable to generate output file: 'out.png'"
  #  log out "Unable to generate output file: 'out.png'"
  #  exit $RES
  #else
  #  log out "Output file 'out.png' regularly generated" 
  #fi
else
  log err "Unable to find $OPHTERM output file: '"$OPHTERM_JSON"'"
  log out "Unable to find $OPHTERM output file: '"$OPHTERM_JSON"'"
  exit 5
fi

log out "ophidia_run execution terminated!"
