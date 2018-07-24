#!/bin/bash
#
# patch_0.0.11.sh
#
# This patch includes the following features: 
#
# -  mysql8 compatibility
#

# Include functions
. ./patch_functions.sh

PATCH="0.0.11"
PATCH_DESC="mysql8 compatibility"
check_patch $PATCH

# Create a temporary SQL file
SQLTMP=$(mktemp /tmp/patch_${PATCH}_XXXXXX)

# Default fg_user password
FG_USER_PASSWORD=futuregateway

#
# Alter columns/tables
#

out "Moving fg_user password field values from PASSWORD to SHA"
out "WARNING: This change will reset previous fg_user passwords"
out "         FutureGateway administrator has to fix this"
out "         asking users to reset their own passwords."
out "         This scripts will reset each passord to the fixed"
out "         value: '"$FG_USER_PASSWORD"'"
cat >$SQLTMP <<EOF
update fg_user set password=SHA('${FG_USER_PASSWORD}') where first_name != 'PTV_TOKEN';
update fg_user set password=SHA('NOPASSWORD') where first_name = 'PTV_TOKEN';
EOF
asdb_file $SQLTMP

out "Database changed"
out ""

# Removing SQL file
rm -f $SQLTMP

out "registering patch $PATCH"
register_patch "$PATCH" "patch_${PATCH}.sh" "$PATCH_DESC"
out "patch registered"

