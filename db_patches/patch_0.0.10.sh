#!/bin/bash
#
# patch_0.0.10.sh
#
# This patch includes the following features: 
#
# - Enabling infrastructure based APIs 
#

# Include functions
. ./patch_functions.sh

PATCH="0.0.10"
PATCH_DESC="Enabling infrastructure based APIs"
check_patch $PATCH

# Create a temporary SQL file
SQLTMP=$(mktemp /tmp/patch_${PATCH}_XXXXXX)

#
# Alter columns/tables
#

out "Modifying database"
cat >$SQLTMP <<EOF
set session sql_mode='NO_AUTO_VALUE_ON_ZERO';
insert into application (id,name,description,outcome,creation,enabled) values (0,'infrastructure','unassigned infrastructure','INFRA',now(), false);
EOF
asdb_file $SQLTMP
out "Database changed"
out ""

# Removing SQL file
rm -f $SQLTMP

out "registering patch $PATCH"
register_patch "$PATCH" "patch_${PATCH}.sh" "$PATCH_DESC"
out "patch registered"

