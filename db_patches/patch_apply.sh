#!/bin/bash
# 
# patch_apply.sh - Apply available patches to APIServerDaemon DB
#
# Author: Riccardo Bruno <riccardo.bruno@ct.infn.it>
#
. patch_functions.sh

DEFAULTDBVER="0.0.1" # Baseline setup version

ts() {
  date +%Y%m%d%H%M%S
}

out() {
  TS=$(ts)
  echo "$TS $*"
}

err() {
  TS=$(ts)
  echo "$TS $*" >&2
}

local_exec() {
  OUT=$(mktemp)
  ERR=$(mktemp)
  $* >$OUT 2>$ERR
  while read ln; do
    out "$ln"
  done < $OUT
  while read ln; do
    err "$ln"
  done < $ERR
  rm -f $OUT
  rm -f $ERR
}

get_dbver() {
  DBVER=$(asdb_cmd "select version from db_patches order by id desc limit 1;" 2>/dev/null)
  if [ "$DBVER" = "" ]; then
    DBVER=$DEFAULTDBVER
  fi
  echo $DBVER
}


#
# Apply patches
#

# Get current DB version
DBVER=$(get_dbver)
out "Current DB version: $DBVER"
# Build the list of patches to apply
DBVERVAL=$(echo $DBVER | awk -F'.' '{ print 1000000*$1+1000*$2+$3 }')
DBPATCHES=$(/bin/ls -1 |\
            grep patch_[0-9*] |\
            sort --version-sort --field-separator=_ --key=2 |\
            awk -v dbver=$DBVER\
                'BEGIN{ p = 0; }\
                      { s = sprintf("patch_%s.sh", dbver);\
                        if(p == 1) print $1;\
                        if(s == $1) p=1;\
                      }')
out "Selected patch versions: '"$(echo $DBPATCHES | sed s/\ /,\ /g)"'"
# Apply selected patches
COUNT=0
STOPPED=0
for patch in $DBPATCHES
do
  out "Executing: ${patch}"
  PATCH_LOG=$(echo ${patch} | sed s/.sh/.log/)
  chmod +x ${patch}
  local_exec "${patch}" > ./$PATCH_LOG
  # Verify patch
  NEWDBVER=$(get_dbver)
  if [ "$NEWDBVER" = "$DBVER" ]; then
    err "An error occurred while applying patch: ${patch}"
    err "Exiting"
    STOPPED=1
    break
  else
    DBVER=$NEWDBVER
    COUNT=$((COUNT+1))
  fi
done
# Report about execution
if [ $STOPPED -ne 0 ]; then
  err "Patching has been interrupted while executing ${patch} file"
  err "Please verify its content and the $PATCH_LOG file"
  err "Then try to complete its execution manually and retry to"
  err "apply further patches if needed"
else
  out "Applied $COUNT patches"
  out "DB is now version $DBVER"
  out "Done"
fi

