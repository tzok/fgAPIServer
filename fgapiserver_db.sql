--
-- fgapiserver_db.sql
--
-- Copyright (c) 2015:
-- Istituto Nazionale di Fisica Nucleare (INFN), Italy
-- Consorzio COMETA (COMETA), Italy
--
-- See http://www.infn.it and and http://www.consorzio-cometa.it for details on
-- the copyright holders.
--
-- Licensed under the Apache License, Version 2.0 (the "License");
-- you may not use this file except in compliance with the License.
-- You may obtain a copy of the License at
--
--     http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.
--
-- Script that creates the GridEngine based apiserver
--
-- Author: riccardo.bruno@ct.infn.it
-- Version: v0.0.1-11-ge8c585a-e8c585a-15
--
drop database if exists fgapiserver;
create database fgapiserver;
grant all on fgapiserver.* TO 'fgapiserver'@'%' IDENTIFIED BY "fgapiserver_password";
grant all on fgapiserver.* TO 'fgapiserver'@'localhost' IDENTIFIED BY "fgapiserver_password";
use fgapiserver;

-- Application
create table application (
    id           int unsigned not null auto_increment
   ,name         varchar(256)
   ,description  varchar(256)
   ,creation     datetime
   ,enabled      boolean default false
   ,primary key(id)
);

insert into application (id,name,description,creation,enabled) 
values (1,"hostname","hostname tester application",now(),true);
insert into application (id,name,description,creation,enabled)
values (2,"SayHello","A more complex app using I/O Sandboxing",now(),true);

-- Application parameters
create table application_parameter (
    app_id        int unsigned not null
   ,param_id      int unsigned not null
   ,pname         varchar(64) not null
   ,pvalue        varchar(256)
   ,primary key(app_id,param_id)
   ,foreign key (app_id) references application(id)
);

-- Parameters for application helloworld
-- App 1
insert into application_parameter (app_id,param_id,pname,pvalue) values (1,1,'jobdesc_executable','/bin/hostname');
insert into application_parameter (app_id,param_id,pname,pvalue) values (1,2,'jobdesc_arguments','-f');
insert into application_parameter (app_id,param_id,pname,pvalue) values (1,3,'jobdesc_output','stdout.txt');
insert into application_parameter (app_id,param_id,pname,pvalue) values (1,4,'jobdesc_error','stderr.txt');
-- App 2
insert into application_parameter (app_id,param_id,pname,pvalue) values (2,1,'jobdesc_executable','/bin/bash');
insert into application_parameter (app_id,param_id,pname,pvalue) values (2,2,'jobdesc_arguments','sayhello.sh');
insert into application_parameter (app_id,param_id,pname,pvalue) values (2,3,'jobdesc_output','sayhello.out');
insert into application_parameter (app_id,param_id,pname,pvalue) values (2,4,'jobdesc_error','sayhello.err');

-- Application files
create table application_file (
    app_id        int unsigned not null
   ,file_id       int unsigned not null -- progressive file number for each application
   ,file          varchar(256) not null -- name of the application file
   ,path          varchar(256) not null -- full path to the application file
   ,override      boolean default false -- true if this file overrides user uploads
   ,primary key(app_id,file_id)
   ,foreign key (app_id) references application(id)
);

-- Files associated to application sayhello
insert into application_file (app_id,file_id,file,path,override) values (2,1,'sayhello.sh' ,'/Users/Macbook/Documents/fgapiserver/apps/sayhello',false);
insert into application_file (app_id,file_id,file,path,override) values (2,2,'sayhello.txt','/Users/Macbook/Documents/fgapiserver/apps/sayhello',false);

-- Infrastructure
create table infrastructure (
    id           int unsigned not null auto_increment
   ,app_id       int unsigned not null
   ,name         varchar(256) not null
   ,description  varchar(256) not null
   ,creation     datetime not null
   ,enabled      boolean default false not null
   ,primary key(id,app_id)
   ,foreign key(app_id) references application(id)
   ,index(app_id)
);

-- Infrastructure parameter
create table infrastructure_parameter (
    infra_id     int unsigned not null
   ,param_id     int unsigned not null 
   ,pname        varchar(64) not null
   ,pvalue       varchar(256) not null
   ,primary key(infra_id,param_id)
   ,foreign key(infra_id) references infrastructure(id)
);

-- Infra for helloworld app@csgfsdk
insert into infrastructure (id,app_id,name,description,creation,enabled)
values (1,1,"hello@csgfsdk","hostname application csgfsdk (SSH)",now(),true);
-- Infra for sayhello app@csgfsdk
insert into infrastructure (id,app_id,name,description,creation,enabled)
values (1,2,"sayhello@csgfsdk","sayhello application csgfsdk (SSH)",now(),true);
-- Infra for sayhello app@nebula
insert into infrastructure (id,app_id,name,description,creation,enabled)
values (2,2,"sayhello@nebula","hostname application csgfsdk (rOCCI)",now(),false);
-- Infra for helloworld app@eumed
insert into infrastructure (id,app_id,name,description,creation,enabled)
values (3,1,"hello@eumed","hostname application eumed (wms)",now(),false);

-- Parameters for infrastructure helloworld@csgfsdk (SSH)
insert into infrastructure_parameter (infra_id,param_id,pname,pvalue) values (1,1,'jobservice','ssh://90.147.74.95');
insert into infrastructure_parameter (infra_id,param_id,pname,pvalue) values (1,2,'username','jobtest');
insert into infrastructure_parameter (infra_id,param_id,pname,pvalue) values (1,3,'password','Xvf56jZ751f');

-- Parameters for infrastructure sayhello@nebula (rOCCI)
insert into infrastructure_parameter (infra_id,param_id,pname,pvalue) values (2, 1,'jobservice'      ,'rocci://nebula-server-01.ct.infn.it:9000');
insert into infrastructure_parameter (infra_id,param_id,pname,pvalue) values (2, 2,'os_tpl'          ,'uuid_chain_reds_generic_vm_centos_6_6_kvm_103');
insert into infrastructure_parameter (infra_id,param_id,pname,pvalue) values (2, 3,'resource_tpl'    ,'small');
insert into infrastructure_parameter (infra_id,param_id,pname,pvalue) values (2, 4,'attributes_title','sayhello');
insert into infrastructure_parameter (infra_id,param_id,pname,pvalue) values (2, 5,'eToken_host'     ,'etokenserver.ct.infn.it');
insert into infrastructure_parameter (infra_id,param_id,pname,pvalue) values (2, 6,'eToken_port'     ,'8082');
insert into infrastructure_parameter (infra_id,param_id,pname,pvalue) values (2, 7,'eToken_id'       ,'bc681e2bd4c3ace2a4c54907ea0c379b');
insert into infrastructure_parameter (infra_id,param_id,pname,pvalue) values (2, 8,'voms'            ,'vo.chain-project.eu');
insert into infrastructure_parameter (infra_id,param_id,pname,pvalue) values (2, 9,'voms_role'       ,'vo.chain-project.eu');
insert into infrastructure_parameter (infra_id,param_id,pname,pvalue) values (2,10,'rfc_proxy'       ,'true');

-- Parameters for infrastructure sayhello@eumed (wms)
insert into infrastructure_parameter values (3,1,'jobservice'  ,'wms://wms.ulakbim.gov.tr:7443/glite_wms_wmproxy_server');
insert into infrastructure_parameter values (3,2,'bdii'        ,'ldap://bdii.eumedgrid.eu:2170');
insert into infrastructure_parameter values (3,3,'eToken_host' ,'etokenserver2.ct.infn.it');
insert into infrastructure_parameter values (3,4,'eToken_port' ,'8082');
insert into infrastructure_parameter values (3,5,'eToken_id'   ,'bc681e2bd4c3ace2a4c54907ea0c379b');
insert into infrastructure_parameter values (3,6,'voms'        ,'eumed');
insert into infrastructure_parameter values (3,7,'voms_role'   ,'eumed');
insert into infrastructure_parameter values (3,8,'rfc_proxy'   ,'false');

-- Task table
create table task (
     id           int unsigned not null auto_increment
    ,creation     datetime not null
    ,last_change  datetime not null
    ,app_id       int unsigned not null 
    ,description  varchar(256) not null -- Human readable hob identifier
    ,status       varchar(32)  not null -- The current status of the task
    ,iosandbox    varchar(256)          -- Path to the task IO Sandbox
    ,user         varchar(256) not null -- username submitting the task
    ,primary key(id)
    ,foreign key (app_id) references application(id)
);

-- Task arguments
create table task_arguments (
     task_id      int unsigned not null       -- id of the task owning these arguments
    ,arg_id       int unsigned not null       -- argument identifier (a progressive number)
    ,argument     varchar(256) not null       -- argument value
    ,primary key(task_id,arg_id)
    ,foreign key (task_id) references task(id)
);

-- Task input file
create table task_input_file (
     task_id      int unsigned not null       -- id of the task owning the file
    ,file_id      int unsigned not null       -- file identifier (a progressive number)
    ,file         varchar(256) not null       -- file name
    ,path         varchar(256) default null   -- the absolute path to the file
    ,primary key(task_id,file_id)
    ,foreign key (task_id) references task(id)
);

-- Task output file
create table task_output_file (
     task_id      int unsigned not null       -- id of the task owning the file
    ,file_id      int unsigned not null       -- file identifier (a progressive number)
    ,file         varchar(256) not null       -- file name
    ,path         varchar(256) default null   -- the absolute path to the file
    ,primary key(task_id,file_id)
    ,foreign key (task_id) references task(id)
);

-- Runtime data
create table runtime_data (
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

--
-- APIServer queue table
--
-- The FutureGatewat API Server  makes use of this table as a link between the REST engine
-- and the APIServer daemon. Each change on the queue table will have effects on both
-- the REST engine and the targeted architecture
--
create table as_queue (
     task_id       int unsigned not null           -- Taks reference for this GridEngine queue entry
    ,target_id     int unsigned default 0          -- For GridEngine UsersTracking' ActiveGridInteraction id reference
    ,target        varchar(32) not null            -- Targeted architecture ("GridEngine","OneDATA", ...)
    ,action        varchar(32) not null            -- A string value that identifies the requested operation (SUBMIT,GETSTATUS,GETOUTPUT...
    ,status        varchar(32) not null            -- Operation status: QUEUED,PROCESSING,PROCESSED,FAILED,DONE
    ,target_status varchar(32) default null        -- GridEngine Job Status: WAITING,SCHEDULED,RUNNING,ABORT,DONE
    ,retry         int unsigned not null default 0 -- Retry count of the task in the queue
    ,creation      datetime    not null            -- When the action is enqueued
    ,last_change   datetime    not null            -- When the record has been modified by the GridEngine last time
    ,check_ts      datetime    not null            -- Check timestamp used to implement a round-robin checking loop
    ,action_info   varchar(128)                    -- Temporary directory path containing further info to accomplish the requested operation
    ,primary key(task_id,action)
    ,index(task_id)
    ,index(action)
--  ,index(target)	
    ,index(last_change)
);

