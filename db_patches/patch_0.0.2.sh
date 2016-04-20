#!/bin/bash
#
# patch_0.0.2.sh
#
# A complex script that updates an existing futuregteway
# with no patching mechanism to the 0.0.2 version (startup of patch)
#
# - 0.0.2 Features
# - SimpleTosca
# - as_queue checks
# - runtime_data
#

# Include functions
. ./patch_functions.sh

PATCH="0.0.2"
FGENV=$FGLOCATION/setenv.sh

# 1st setup DBUtils
ASDBCHK=$(set | grep "asdb\ ()")
UTDBCHK=$(set | grep "utdb\ ()")

if [ "$ASDBCHK" = "" ];
  cat >> $FGENV <<EOF
# DB functions
asdb() {
  cmd=\$(echo "\$*" | sed s/\$0//)
  if [ "\$cmd" != "" ]; then
    cmd="-e \\"\$cmd\\""
  fi
  eval mysql -h localhost -P 3306 -u fgapiserver -pfgapiserver_password fgapiserver \$cmd
}
utdb() {
  cmd=\$(echo "\$*" | sed s/\$0//)
    if [ "\$cmd" != "" ]; then
    cmd="-e \\"\$cmd\\""
  fi
  eval mysql -h localhost -P 3306 -u tracking_user -pusertracking userstracking \$cmd
}
EOF



# Load asdb/utdb utilities
source $FGENV

# Check for runtime_data
RUNTIMEDATA=$(asdb "desc runtime_data;" 2>/dev/null)
if [ "$RUNTIMEDATA" = "" ]; then
  SQLTMP=%(mktemp)
  cat >$SQLTMP <<EOF
create table runtime_data1 (
   task_id      int unsigned  not null      -- id of the task owning data
  ,data_id      int unsigned  not null      -- data identifier (a progressive number)
  ,data_name    varchar(128)  not null      -- name of data field
  ,data_value   varchar(1024) not null      -- value of data field
  ,data_desc    varchar(2048)               -- value of data description
  ,creation     datetime      not null      -- When data has been written the first time
  ,last_change  datetime      not null      -- When data has been updated
  ,primary key(task_id,data_id)
  ,foreign key (task_id) references task(id)
);
EOF
  asdb_file $SQLTMP
  rm -f $RUNTIMEDATA
fi

#
# Missing columns/tables
#

# Creating SQL file
SQLTMP=%(mktemp)

# as_queue.retry
out "Checking as_queue.retry"
NEWCOL=$(asdb "select count(retry) from as_queue;" 2>/dev/null | grep -v '+' | grep -v count)
if [ "$NEWCOL" = "" ]; then
  out "as_queue.retry missing; patching db"
  echo "alter table as_queue add retry int unsigned not null default 0;" > $SQLTMP
  asdb_file $SQLTMP
  out "as_queue.retry created"
else
  out "as_queue.retry column already exists"
fi

# as_queue.check_ts
NEWCOL=$(asdb "select count(check_ts) from as_queue;" 2>/dev/null | grep -v '+' | grep -v count)
if [ "$NEWCOL" = "" ]; then
  out "as_queue.check_ts missing; patching db"
  echo "alter table as_queue add check_ts datetime;"              > $SQLTMP
  echo "update as_queue set check_ts=last_change;"               >> $SQLTMP
  echo "alter table as_queue modify check_ts datetime not null;" >> $SQLTMP
  asdb_file $SQLTMP
  out "as_queue.check_ts created"
else
  out "as_queue.check_ts column already exists"
fi

# application_parameter.pdesc 
NEWCOL=$(asdb "select count(pdesc) from application_parameter;" 2>/dev/null | grep -v '+' | grep -v count)
if [ "$NEWCOL" = "" ]; then
  out "application_parameter.pdesc missing; patching db"
  echo "alter table application_parameter add pdesc varchar(1024);" > $SQLTMP
  asdb_file $SQLTMP
  out "application_parameter.pdesc created"
else
  out "application_parameter.pdesc already exists"
fi

# db_patch table
NEWTAB=$(asdb "select count(*) from db_patch; -s" 2>/dev/null | grep -v '+' | grep -v count)
if [ "$NEWTAB" = "" ]; then
  out "db_patch table missing; patching db"
  cat >$SQLTMP <<EOF
create table db_patches (
    id           int unsigned not null -- Patch Id
   ,version      varcher(32)  not null -- Current database version
   ,name         varchar(256) not null -- Name of the patch (it describes the involved feature)
   ,file         varchar(256) not null -- file refers to fgAPIServer/db_patches directory
   ,applied      datetime              -- Patch application timestamp
   ,primary key(id)
);
insert into db_patches (id,version,name,file,applied) values (1,'0.0.1','baseline setup','../fgapiserver_db.sql',now())
EOF
  asdb_file $SQLTMP
  out "db_patch table created"
else
  out "db_patch table already exists"
fi

# Removing SQL file
rm -f $SQLTMP

out "registering patch $"
regisger_patch "$PATCH" "patch_${PATCH}.sh" "first database patch" 
out "patch registered"
