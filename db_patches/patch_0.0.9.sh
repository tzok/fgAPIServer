#!/bin/bash
#
# patch_0.0.9.sh
#
# This patch includes the following features: 
#
# - PTV uses get-token feature to get fresh tokens
#

# Include functions
. ./patch_functions.sh

PATCH="0.0.9"
PATCH_DESC="PTV uses get-token feature to get fresh tokens "
check_patch $PATCH

# Create a temporary SQL file
SQLTMP=$(mktemp /tmp/patch_${PATCH}_XXXXXX)

#
# Missing columns/tables
#

out "Adding column subject in fg_token table"
cat >$SQLTMP <<EOF
alter table fg_token add subject varchar(1024) not null default '';
EOF
asdb_file $SQLTMP
out "Database changed"
out ""
# Removing SQL file
rm -f $SQLTMP

out "registering patch $PATCH"
register_patch "$PATCH" "patch_${PATCH}.sh" "$PATCH_DESC"
out "patch registered"

