#!/bin/bash
#
# patch_0.0.13.sh
#
# This patch includes the following features: 
#
# - EnvConfig 
#

# Include functions
. ./patch_functions.sh

PATCH="0.0.13"
PATCH_DESC="User data"
check_patch $PATCH

# Create a temporary SQL file
SQLTMP=$(mktemp /tmp/patch_${PATCH}_XXXXXX)

#
# Alter columns/tables
#

cat >$SQLTMP <<EOF
-- User data table; store persistent data associated to the user
create table fg_user_data (
    user_id      int unsigned  not null -- User id owning data
   ,data_id      int unsigned  not null -- Data identifier (a progressive number)
   ,data_name    varchar(128)  not null -- name of data field
   ,data_value   varchar(1024) not null -- value of data field
   ,data_desc    varchar(2048)          -- data description
   ,data_proto   varchar(128)           -- data protocol (manages complex data)
   ,data_type    varchar(128)           -- data type (works with data_proto)
   ,creation     datetime      not null -- When data has been written the first time
   ,last_change  datetime      not null -- When data has been updated
   ,primary key(user_id,data_id,data_name)
   ,foreign key(user_id) references fg_user(id)
);
EOF
asdb_file $SQLTMP

out "Database changed"
out ""

# Removing SQL file
rm -f $SQLTMP

out "registering patch $PATCH"
register_patch "$PATCH" "patch_${PATCH}.sh" "$PATCH_DESC"
out "patch registered"

