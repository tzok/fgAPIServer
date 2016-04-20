#!/bin/bash
#
# Database patch functions
#

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

asdb_file() {
  SQLFILE=$1
  if [ "$SQLFILE" != "" -a -f $SQLFILE ]; then
    mysql -h localhost -P 3306 -u fgapiserver -pfgapiserver_password fgapiserver < $SQLFILE
  fi
}

register_patch() {
	PATCHVER=$1
    PATCHFILE=$2
	PATCHDESC=$3
    
	SQL=$(mktemp)
	cat >$SQL <<EOF
insert into db_patches (id,version,name,file,applied) select if(max(id) is NULL,1,max(id)+1),'${PATCHVER}','${PATCHDESC}','${PATCHFILE}',now() from db_patches;
EOF
	asdb_file $SQL
	rm -f $SQL
}
