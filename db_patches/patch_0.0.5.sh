#!/bin/bash
#
# patch_0.0.4.sh
#
# This patch includes the following features: 
#
# - User membership, groups and roles
# - Login and session token managemen 
# - Protected API calls
#

# Include functions
. ./patch_functions.sh

PATCH="0.0.5"
check_patch $PATCH

# Create a temporary SQL file
SQLTMP=$(mktemp /tmp/patch_${PATCH}_XXXXXX)

#
# Missing columns/tables
#

out "Modifying simple_tosca table"
cat >$SQLTMP <<EOF
alter table simple_tosca modify tosca_id varchar(1024);
EOF
asdb_file $SQLTMP
out "Database changed"
out ""
# Removing SQL file
rm -f $SQLTMP

out "registering patch $PATCH"
register_patch "$PATCH" "patch_${PATCH}.sh" "Increase targetId (TOSCA UUID) field"
out "patch registered"

