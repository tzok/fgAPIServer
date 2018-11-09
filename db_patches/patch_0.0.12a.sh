#!/bin/bash
#
# patch_0.0.12a.sh
#
# This patch includes the following features: 
#
# - fg_user enabling flag 
#

# Include functions
. ./patch_functions.sh

PATCH="0.0.12a"
PATCH_DESC="Enabling flag for FutureGateway users"
check_patch $PATCH

# Create a temporary SQL file
SQLTMP=$(mktemp /tmp/patch_${PATCH}_XXXXXX)

#
# Alter columns/tables
#

out "Adding column enabled to fg_user"
out "Creating new table fg_user_check to enable users by web link"
out "WARNING: This change will insert new column having false"
out "         as default value. However existing users will be"
out "         enabled."
cat >$SQLTMP <<EOF
alter table fg_user add column enabled boolean default false;
update fg_user set enabled = true;
create table fg_user_check (
    user_id        int unsigned  not null -- User id to enable
   ,token          varchar(1024) not null -- Enabling token
   ,token_expiry   datetime      not null -- Expiry date for enabling token
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

