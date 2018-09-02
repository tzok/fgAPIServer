--
-- fgapiserver_db.sql
--
-- Copyright (c) 2015:
-- Istituto Nazionale di Fisica Nucleare (INFN), Italy
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
-- Script that creates FutureGateway APIServer
--
-- Author: riccardo.bruno@ct.infn.it
-- Version: %VERSION%
--
--

create user 'fgapiserver'@'%' identified by "fgapiserver_password";
grant all privileges on fgapiserver.* to 'fgapiserver'@'%' with grant option;

create user 'fgapiserver'@'localhost' identified by "fgapiserver_password";
grant all privileges on fgapiserver.* to 'fgapiserver'@'localhost' with grant option;
