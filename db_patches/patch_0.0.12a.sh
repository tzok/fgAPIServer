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
alter table fg_user add column enabled boolean default true;
update fg_user set enabled = true;
create table fg_user_check (
    user_id        int unsigned  not null -- User id to enable
   ,token          varchar(1024) not null -- Enabling token
   ,token_expiry   datetime      not null -- Expiry date for enabling token
   ,foreign key(user_id) references fg_user(id)
);
EOF
asdb_file $SQLTMP

out "Adding new roles necessary for user_api"
cat >$SQLTMP <<EOF
insert into fg_role (id,name,creation,modified) values (23,'users_view',now(),now());          -- Can view users
insert into fg_role (id,name,creation,modified) values (24,'users_change',now(),now());        -- Can change users
insert into fg_role (id,name,creation,modified) values (25,'users_groups_view',now(),now());   -- Can view user groups
insert into fg_role (id,name,creation,modified) values (26,'users_groups_change',now(),now()); -- Can change user groups
insert into fg_role (id,name,creation,modified) values (27,'users_tasks_view',now(),now());    -- Can view user tasks
insert into fg_role (id,name,creation,modified) values (28,'groups_view',now(),now());         -- Can change groups
insert into fg_role (id,name,creation,modified) values (29,'groups_change',now(),now());       -- Can change groups
insert into fg_role (id,name,creation,modified) values (30,'groups_apps_view',now(),now());    -- Can view applications in groups
insert into fg_role (id,name,creation,modified) values (31,'groups_apps_change',now(),now());  -- Can change applications in groups
insert into fg_role (id,name,creation,modified) values (32,'groups_roles_view',now(),now());   -- Can view roles in groups
insert into fg_role (id,name,creation,modified) values (33,'groups_roles_change',now(),now()); -- Can change roles in groups
insert into fg_role (id,name,creation,modified) values (34,'roles_view',now(),now());          -- Can view roles
-- Administrator roles (grant all privileges)
insert into fg_group_role (group_id,role_id,creation)
select 1,id,now() from fg_role where id > 22;
EOF
asdb_file $SQLTMP


out "Database changed"
out "New roles are now available, please configure groups to handle new roles to enable UGR APIs"
out ""

# Removing SQL file
rm -f $SQLTMP

out "registering patch $PATCH"
register_patch "$PATCH" "patch_${PATCH}.sh" "$PATCH_DESC"
out "patch registered"

