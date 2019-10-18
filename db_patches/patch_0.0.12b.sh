#!/bin/bash
#
# patch_0.0.12.sh
#
# This patch includes the following features: 
#
# - EnvConfig 
#

# Include functions
. ./patch_functions.sh

PATCH="0.0.12b"
PATCH_DESC="EnvConfig"
check_patch $PATCH

# Create a temporary SQL file
SQLTMP=$(mktemp /tmp/patch_${PATCH}_XXXXXX)

#
# Alter columns/tables
#

cat >$SQLTMP <<EOF
--
-- Service registry
--
-- FutureGateway foresees the use of one or many components which presence is tracked
-- by the FutureGateway database
--
create table srv_registry (
    uuid          varchar(1024) not null
   ,creation      datetime      not null
   ,last_access   datetime      not null
   ,enabled       boolean default true
   ,cfg_hash      varchar(1024)
   ,primary key(uuid)
);

-- Service configuration
--
-- FutureGateway uses registered services to store their configuration settings
-- this allows safe service restarts as well as 'on the fly' change of configuration
-- settings for all modules supporting this
-- Configuration values are stored in the form conf_name = conf_value
-- the field conf_enabled tells if the configuration is enabled or not
--
create table srv_config (
    uuid          varchar(1024) not null
   ,name          varchar(256)  not null
   ,value         varchar(4096)
   ,enabled       boolean default true
   ,created       datetime not null
   ,modified      datetime not null
   ,foreign key (uuid) references srv_registry(uuid)
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

