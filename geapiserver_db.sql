--
-- geapiserver_db.sql
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
--
drop database if exists geapiserver;
create database geapiserver;
grant all on geapiserver.* TO 'geapiserver'@'%' IDENTIFIED BY "geapiserver_password";
grant all on geapiserver.* TO 'geapiserver'@'localhost' IDENTIFIED BY "geapiserver_password";
use geapiserver;

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
insert into application_parameter (app_id,param_id,pname,pvalue) values (1,1,'jobdesc_executable','/bin/hostname');
insert into application_parameter (app_id,param_id,pname,pvalue) values (1,2,'jobdesc_arguments','-f');
insert into application_parameter (app_id,param_id,pname,pvalue) values (1,3,'jobdesc_output','stdout.txt');
insert into application_parameter (app_id,param_id,pname,pvalue) values (1,4,'jobdesc_error','stderr.txt');

-- Infrastructure
create table infrastructure (
    id           int unsigned not null auto_increment
   ,app_id       int unsigned not null
   ,name         varchar(256) not null
   ,description  varchar(256) not null
   ,creation     datetime not null
   ,enabled      boolean default false not null
   ,primary key(id)
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

-- Infra for helloworld app
insert into infrastructure (id,app_id,name,description,creation,enabled)
values (1,1,"hostname@localhost","hostname application csgfsdk (SSH)",now(),true);
-- Parameters for infrastructure helloworld@csgfsdk (SSH)
insert into infrastructure_parameter (infra_id,param_id,pname,pvalue) values (1,1,'jobservice','ssh://90.147.74.95');
insert into infrastructure_parameter (infra_id,param_id,pname,pvalue) values (1,2,'username','jobtest');
insert into infrastructure_parameter (infra_id,param_id,pname,pvalue) values (1,3,'password','Xvf56jZ751f');

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

--
-- GridEngine queue table
--
-- GridEngine API Server makes use of this table as kink point between the REST engine
-- and the GridEngine daemon. Each change on the queue table will have effects on both
-- the REST engine and the GridEngine
--
create table ge_queue (
     task_id      int unsigned not null -- Taks reference for this GridEngine queue entry
    ,agi_id       int unsigned          -- UsersTracking' ActiveGridInteraction id reference
    ,action       varchar(32) not null  -- A string value that identifies the requested operation (SUBMIT,GETSTATUS,GETOUTPUT...
    ,status       varchar(32) not null  -- Operation status (QUEUED,TAKEN,DONE,FAILED)
    ,creation     datetime    not null  -- When the action is enqueued
    ,last_change  datetime    not null  -- When the record has been modified by the GridEngine last time
    ,action_info  varchar(128) -- Temporary directory path containing further info to accomplish the requested operation
    ,primary key(task_id,status)
    ,index(task_id)
    ,index(status)
    ,index(last_change)
);
