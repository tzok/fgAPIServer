#!/usr/bin/env python
# Copyright (c) 2015:
# Istituto Nazionale di Fisica Nucleare (INFN), Italy
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


#
# fgapiserver_queries - Provide queries for fgapiserver tests
#

__author__ = "Riccardo Bruno"
__copyright__ = "2015"
__license__ = "Apache"
__version__ = "v0.0.2-30-g37540b8-37540b8-37"
__maintainer__ = "Riccardo Bruno"
__email__ = "riccardo.bruno@ct.infn.it"


fgapiserver_queries = [
    {'id': 0,
     'query': 'SELECT VERSION()',
     'result': [['test', ], ]},
    {'id': 1,
     'query': 'select version from db_patches order by id desc limit 1;',
     'result': [['0.0.12b'], ]},
    {'id': 2,
     'query': 'select id\n'
              'from fg_user\n'
              'where name=%s;',
     'result': [[1], ]},
    {'id': 3,
     'query': 'select id\n'
              'from application\n'
              'where name=%s;',
     'result': [[1], ]},
    {'id': 4,
     'query': ('select '
               ' id\n'
               ',status\n'
               ',date_format(creation, \'%%Y-%%m-%%dT%%TZ\') creation\n'
               ',date_format(last_change, \'%%Y-%%m-%%dT%%TZ\') last_change\n'
               ',app_id\n'
               ',description\n'
               ',user\n'
               ',iosandbox\n'
               'from task\n'
               'where id=%s\n'
               '  and status != "PURGED";'),
     'result': [['1',
                 'WAITING',
                 '1970-01-01T00:00:00',
                 '1970-01-01T00:00:00',
                 '1',
                 'test task',
                 'test user',
                 '/tmp/test']], },
    {'id': 5,
     'query': ('select argument\n'
               'from task_arguments\n'
               'where task_id=%s\n'
               'order by arg_id asc;'),
     'result': [['argument'], ]},
    {'id': 6,
     'query': ('select file\n'
               '      ,if(path is null or length(path)=0,'
               '          \'NEEDED\','
               '          \'READY\') status\n'
               '      ,if(path is NULL,\'\',path)\n'
               'from task_input_file\n'
               'where task_id=%s\n'
               'order by file_id asc;'),
     'result': [['input_file_1', 'NEEDED', ''],
                ['input_file_2', 'READY', '/tmp/test'], ]},
    {'id': 7,
     'query': ('select file\n'
               '      ,if(path is NULL,\'\',path)\n'
               'from task_output_file\n'
               'where task_id=%s\n'
               'order by file_id asc;'),
     'result': [['output_file_1', '/tmp'], ['output_file_2', '/tmp'], ]},
    {'id': 8,
     'query': ('select '
               '  data_name\n'
               ' ,data_value\n'
               ' ,data_desc\n'
               ' ,data_type\n'
               ' ,data_proto\n'
               ' ,date_format(creation,'
               '              \'%%Y-%%m-%%dT%%TZ\') creation\n'
               ' ,date_format(last_change,'
               '              \'%%Y-%%m-%%dT%%TZ\') last_change\n'
               'from runtime_data\n'
               'where task_id=%s\n'
               'order by data_id asc;'),
     'result': [['userdata_name_1',
                 'userdata_value_1',
                 'userdata_desc_1',
                 'NULL',
                 'NULL',
                 '1970-01-01T00:00:00',
                 '1970-01-01T00:00:00'],
                ['userdata_name_2',
                 'userdata_value_2',
                 'userdata_desc_2',
                 'NULL',
                 'NULL',
                 '1970-01-01T00:00:00',
                 '1970-01-01T00:00:00'],
                ]},
    {'id': 9,
     'query': ('select id\n'
               '      ,name\n'
               '      ,description\n'
               '      ,outcome\n'
               '      ,date_format(creation, \'%%Y-%%m-%%dT%%TZ\') creation\n'
               '      ,enabled\n'
               'from application\n'
               'where id=%s;'),
     'result': [['1',
                 'test application',
                 'test application description',
                 'JOB',
                 '1970-01-01T00:00:00',
                 '1'],
                ]},
    {'id': 10,
     'query': ('insert into infrastructure_parameter (infra_id\n'
               '                                     ,param_id\n'
               '                                     ,pname\n'
               '                                     ,pvalue\n'
               '                                     ,pdesc)\n'
               'select %s\n'
               '      ,if(max(param_id) is NULL,\n'
               '          1,max(param_id)+1) \n'
               '      ,%s\n'
               '      ,%s\n'
               '      ,%s\n'
               'from infrastructure_parameter\n'
               'where infra_id = %s;'),
     'result': [['test_param_1', 'test_param_value_1', 'test_param_desc_1'],
                ['test_param_2', 'test_param_value_2'], None]},
    {'id': 11,
     'query': ('select id\n'
               '      ,name\n'
               '      ,description\n'
               '      ,date_format(creation, \'%%Y-%%m-%%dT%%TZ\') creation\n'
               '      ,if(enabled,\'enabled\',\'disabled\') status\n'
               '      ,if(vinfra,\'virtual\',\'real\') status\n'
               'from infrastructure\n'
               'where app_id=%s;'),
     'result': [['1',
                 'test infra',
                 'test infrastructure for test application',
                 '1970-01-01T00:00:00',
                 'enabled',
                 'real'], ]},
    {'id': 12,
     'query': ('select pname, pvalue\n'
               'from infrastructure_parameter\n'
               'where infra_id=%s\n'
               'order by param_id asc;'),
     'result': [['test_infra_param_name_1', 'test_infra_param_value_1'],
                ['test_infra_param_name_2', 'test_infra_param_value_2'], ]},
    {'id': 13,
     'query': ('select task_id '
               'from task_output_file '
               'where file=%s and path=%s;'),
     'result': ['1']},
    {'id': 14,
     'query': ('select if((creation+expiry)-now()>0,user_id,NULL) user_id\n'
               '      ,(select name from fg_user where id=user_id) name\n'
               'from fg_token\n'
               'where token=%s;'),
     'result': [['1', 'test_user'], ]},
    {'id': 15,
     'query': ('select task_id from task_output_file\n'
               'where file=%s and path=%s\n'
               'union all\n'
               'select task_id from task_input_file\n'
               'where file=%s and path=%s\n'
               'union all\n'
               'select null;'),
     'result': ['1']},
    {'id': 16,
     'query': ('select app_id from application_file\n'
               'where file=%s and path=%s\n'
               'union all\n'
               'select null;'),
     'result': ['1']},
    {'id': 17,
     'query': ('select id        \n'
               '      ,name      \n'
               '      ,password  \n'
               '      ,first_name\n'
               '      ,last_name \n'
               '      ,institute \n'
               '      ,mail      \n'
               '      ,creation  \n'
               '      ,modified  \n'
               'from fg_user     \n'
               'where name=%s;'),
     'result': [['1',
                 'futuregateway',
                 'XXXXYYYYZZZZ',
                 'futuregateway',
                 'futuregateway',
                 'futuregateway',
                 'futuregateway@futuregateway',
                 '1970-01-01T00:00:00',
                 '1970-01-01T00:00:00'], ]},
    {'id': 18,
     'query': ('select distinct id\n'
               'from infrastructure order by 1 asc;'),
     'result': ['1']},
    {'id': 19,
     'query': ('select app_id,\n'
               '       name,\n'
               '       description,\n'
               '       date_format(creation,\n'
               '                   \'%%Y-%%m-%%dT%%TZ\') creation,\n'
               '       enabled,\n'
               '       vinfra\n'
               'from infrastructure\n'
               'where id=%s\n'
               'order by 1 asc ,2 asc\n'
               'limit 1;'),
     'result': [['0',
                 'test infra',
                 'test infrastructure',
                 '1970-01-01T00:00:00',
                 0,
                 0]]},
    {'id': 20,
     'query': ('select pname\n'
               '      ,pvalue\n'
               '      ,pdesc\n'
               'from infrastructure_parameter\n'
               'where infra_id=%s\n'
               'order by param_id asc;'),
     'result': [['test_pname1', 'test_pvalue1', 'test_pdesc1'],
                ['test_pname2', 'test_pvalue2', 'test_pdesc2'],
                ['test_pname3', 'test_pvalue3', None], ]},
    {'id': 21,
     'query': ('select count(*)\n'
               'from infrastructure\n'
               'where id = %s;'),
     'result': ['1']},
    {'id': 22,
     'query': ('select count(*)>0      \n'
               'from fg_user        u  \n'
               '    ,fg_group       g  \n'
               '    ,fg_user_group ug  \n'
               '    ,fg_group_role gr  \n'
               '    ,fg_role        r  \n'
               'where u.id=%s          \n'
               '  and u.enabled = true \n'
               '  and u.id=ug.user_id  \n'
               '  and g.id=ug.group_id \n'
               '  and g.id=gr.group_id \n'
               '  and r.id=gr.role_id  \n'
               '  and r.name = %s;'),
     'result': ['1']},
    {'id': 23,
     'query': ('select count(*)>1               \n'
               'from fg_user_group              \n'
               'where user_id = (select id      \n'
               '                 from fg_user   \n'
               '                 where name=%s) \n'
               '   or user_id = (select id      \n'
               '                 from fg_user   \n'
               '                 where name=%s) \n'
               'group by group_id               \n'
               'having count(*) > 1;'),
     'result': ['1']},
    {'id': 24,
     'query': ('select pname\n'
               '      ,pvalue\n'
               'from application_parameter\n'
               'where app_id=%s\n'
               'order by param_id asc;'),
     'result': [['test_pname1', 'test_pvalue1'],
                ['test_pname2', 'test_pvalue2'], ]},
    {'id': 25,
     'query': ('insert into infrastructure (id\n'
               '                           ,app_id\n'
               '                           ,name\n'
               '                           ,description\n'
               '                           ,creation\n'
               '                           ,enabled\n'
               '                           ,vinfra\n'
               '                           )\n'
               'select if(max(id) is NULL,1,max(id)+1)\n'
               '      ,%s\n'
               '      ,%s\n'
               '      ,%s\n'
               '      ,now()\n'
               '      ,%s\n'
               '      ,%s\n'
               'from infrastructure;'),
     'result': []},
    {'id': 26,
     'query': 'select max(id) from infrastructure;',
     'result': ['1']},
    {'id': 27,
     'query': ('select count(*)\n'
               'from as_queue q\n'
               '    ,task t\n'
               '    ,application a\n'
               '    ,infrastructure i\n'
               'where i.app_id=a.id\n'
               '  and t.app_id=a.id\n'
               '  and q.task_id=t.id\n'
               '  and t.app_id=a.id\n'
               '  and q.status=\'RUNNING\'\n'
               '  and i.id = %s;'),
     'result': ['0']},
    {'id': 28,
     'query': ('delete from infrastructure_parameter\n'
               'where infra_id=%s;'),
     'result': []},
    {'id': 29,
     'query': 'delete from infrastructure where id=%s;',
     'result': []},
    {'id': 30,
     'query': ('select count(*)\n'
               'from application a\n'
               '    ,infrastructure i\n'
               'where i.app_id=a.id\n'
               '  and a.id != 0\n'
               '  and i.id = %s;'),
     'result': ['0']},
    {'id': 31,
     'query': ('select if(count(*)>0,\n'
               '          if((select count(token)\n'
               '              from fg_token t\n'
               '              where t.subject = %s\n'
               '                and t.creation+t.expiry>now()\n'
               '              order by t.creation desc\n'
               '              limit 1) > 0,\n'
               '             concat(\'recycled\',\':\',\n'
               '                    (select token\n'
               '                     from fg_token t\n'
               '                     where t.subject = %s\n'
               '                     and t.creation+t.expiry>now()\n'
               '                     order by t.creation desc\n'
               '                     limit 1)),\n'
               '             concat(\'new\',\':\',uuid())),\n'
               '          NULL) acctoken\n'
               'from fg_user u\n'
               'where u.name=%s\n'
               '  and u.password=sha(%s);'),
     'result': [['new:TEST_ACCESS_TOKEN'], ]},
    {'id': 32,
     'query': ('insert into fg_token \n'
               '  select %s, id, now() creation, 24*60*60\n'
               '  from  fg_user \n'
               '  where name=%s \n'
               '    and fg_user.password=sha(%s);'),
     'result': []},
    {'id': 33,
     'query': ('select count(*)>0      \n'
               'from fg_user        u  \n'
               '    ,fg_group       g  \n'
               '    ,application    a  \n'
               '    ,fg_user_group ug  \n'
               '    ,fg_group_apps ga  \n'
               'where u.id=%s          \n'
               '  and u.id=ug.user_id  \n'
               '  and a.id=%s          \n'
               '  and a.id=ga.app_id   \n'
               '  and g.id=ug.group_id \n'
               '  and g.id=ga.group_id;'),
     'result': ['1']},
    {'id': 34,
     'query': 'select count(*) from fg_group where lower(name)=%s;',
     'result': ['1']},
    {'id': 35,
     'query': 'select id, name from fg_user where name=%s;',
     'result': [[1, 'test_user'], ]},
    {'id': 36,
     'query': ('insert into fg_user (name, \n'
               '                     password,\n'
               '                     first_name,\n'
               '                     last_name,\n'
               '                     institute,\n'
               '                     mail,\n'
               '                     creation,\n'
               '                     modified)\n'
               'values (%s,\n'
               '        sha(\'NOPASSWORD\'),\n'
               '        \'PTV_TOKEN\',\n'
               '        \'PTV_TOKEN\',\n'
               '        \'PTV_TOKEN\',\n'
               '        \'PTV@TOKEN\',\n'
               '        now(),\n'
               '        now());'),
     'result': []},
    {'id': 37,
     'query': ('select count(*)\n'
               'from task\n'
               'where id = %s\n'
               '  and user = (select name\n'
               '              from fg_user\n'
               '              where id = %s);'),
     'result': ['1']},
    {'id': 38,
     'query': ('select file\n'
               '      ,if(path is null,\'NEEDED\',\'READY\') status\n'
               'from task_input_file\n'
               'where task_id = %s;'),
     'result': [['test_ifile_1', 'READY'],
                ['test_ifile_2', 'NEEDED'], ]},
    {'id': 39,
     'query': ('select file\n'
               '      ,if(path is null,\'waiting\',\'ready\')\n'
               'from task_output_file\n'
               'where task_id = %s;'),
     'result': [['test_ofile_1', 'ready'],
                ['test_ofile_2', 'ready'], ]},
    {'id': 40,
     'query': ('select file\n'
               '      ,path\n'
               '      ,override\n'
               'from application_file\n'
               'where app_id=%s\n'
               'order by file_id asc;'),
     'result': [['test_app_file1', '/path/to/file1', 0],
                ['test_app_file2', '/path/to/file2', 1], ]},
    {'id': 41,
     'query': 'select max(id) from task;',
     'result': [[1], ]},
    {'id': 42,
     'query': ('insert into task_output_file (task_id\n'
               '                             ,file_id\n'
               '                             ,file)\n'
               'select %s\n'
               '      ,if(max(file_id) is NULL,1,max(file_id)+1)\n'
               '      ,%s\n'
               'from task_output_file\n'
               'where task_id=%s'),
     'result': []},
    {'id': 43,
     'query': 'select '
              '  sum(if(path is NULL,0,1))=count(*) or count(*)=0 sb_ready\n'
              'from task_input_file\n'
              'where task_id=%s;',
     'result': ['1']},
    {'id': 44,
     'query': ('select '
               '  if(sum(override) is NULL,'
               '     TRUE,'
               '     count(*)=sum(override)) override\n'
               'from application_file\n'
               'where app_id=%s;'),
     'result': ['1']},
    {'id': 45,
     'query': 'select iosandbox from task where id=%s;',
     'result': [['/tmp/iosandbox'], ]},
    {'id': 46,
     'query': 'update task_input_file\n'
              'set path=%s\n'
              'where task_id=%s\n'
              '  and file=%s;',
     'result': []},
    {'id': 47,
     'query': ('select count(*)\n'
               'from task\n'
               'where id = %s\n'
               '  and status != \'PURGED\''
               '  and user = (select name\n'
               '              from fg_user\n'
               '              where id = %s);'),
     'result': [[1], ]},
    {'id': 48,
     'query': ('insert into as_queue (\n'
               '   task_id\n'
               '  ,target_id\n'
               '  ,target\n'
               '  ,action\n'
               '  ,status\n'
               '  ,target_status\n'
               '  ,creation\n'
               '  ,last_change\n'
               '  ,check_ts\n'
               '  ,action_info\n'
               ') values (%s,\n'
               '          NULL,\n'
               '         \'GridEngine\',\n'
               '         \'CLEAN\',\n'
               '         \'QUEUED\',\n'
               '          NULL,\n'
               '          now(),\n'
               '          now(),\n'
               '          now(),\n'
               '          %s);'),
     'result': []},
    {'id': 49,
     'query': ('update task set status=\'CANCELLED\', '
               'last_change=now() where id=%s;'),
     'result': []},
    {'id': 50,
     'query': ('insert into as_queue (\n'
               '   task_id       \n'
               '  ,target_id     \n'
               '  ,target        \n'
               '  ,action        \n'
               '  ,status        \n'
               '  ,target_status \n'
               '  ,creation      \n'
               '  ,last_change   \n'
               '  ,check_ts      \n'
               '  ,action_info   \n'
               ') values (%s,\n'
               '          NULL,\n'
               '          %s,\n'
               '          \'SUBMIT\',\n'
               '          \'QUEUED\',\n'
               '          NULL,\n'
               '          now(),\n'
               '          now(),\n'
               '          now(),\n'
               '          %s);'),
     'result': []},
    {'id': 51,
     'query': ('insert into task (id\n'
               '                 ,creation\n'
               '                 ,last_change\n'
               '                 ,app_id\n'
               '                 ,description\n'
               '                 ,status\n'
               '                 ,user\n'
               '                 ,iosandbox)\n'
               'select if(max(id) is NULL,1,max(id)+1) -- new id\n'
               '      ,now()                           -- creation date\n'
               '      ,now()                           -- last change\n'
               '      ,%s                              -- app_id\n'
               '      ,%s                              -- description\n'
               '      ,\'WAITING\'                     -- status WAITING\n'
               '      ,%s                              -- user\n'
               '      ,%s                              -- iosandbox\n'
               'from task;\n'),
     'result': []},
    {'id': 52,
     'query': ('insert into task_arguments (task_id\n'
               '                           ,arg_id\n'
               '                           ,argument)\n'
               'select %s\n'
               '      ,if(max(arg_id) is NULL,1,max(arg_id)+1)\n'
               '      ,%s\n'
               'from task_arguments\n'
               'where task_id=%s'),
     'result': []},
    {'id': 53,
     'query': ('update task set status=\'SUBMIT\', \n'
               'last_change=now() where id=%s;'),
     'result': []},
    {'id': 54,
     'query': ('insert into \n'
               'fg_token (token, subject, user_id, creation, expiry)\n'
               'select %s, %s, %s, now(), NULL\n'
               'from dual\n'
               'where (select count(*)\n'
               '       from fg_token\n'
               '       where token=%s) = 0;'),
     'result': []},
    {'id': 55,
     'query': ('select count(*)\n'
               'from runtime_data\n'
               'where data_name=%s\n'
               '  and task_id=%s;'),
     'result': ['1']},
    {'id': 56,
     'query': ('update runtime_data\n'
               'set data_value = %s\n'
               '   ,last_change = now()\n'
               'where data_name=%s\n'
               '  and task_id=%s;'),
     'result': []},
    {'id': 57,
     'query': ('insert into as_queue (task_id,\n'
               '                      action,\n'
               '                      status,\n'
               '                      target,\n'
               '                      target_status,\n'
               '                      creation,\n'
               '                      last_change,\n'
               '                      check_ts,\n'
               '                      action_info\n)'
               'select %s,\n'
               '       "STATUSCH",\n'
               '       "QUEUED",\n'
               '       (select target\n'
               '        from as_queue\n'
               '        where task_id=%s\n'
               '          and action="SUBMIT"),\n'
               '       %s,\n'
               '       now(),\n'
               '       now(),\n'
               '       now(),\n'
               '       (select action_info\n'
               '        from as_queue\n'
               '        where task_id=%s\n'
               '          and action=\'SUBMIT\');'),
     'result': []},
    {'id': 58,
     'query': ('select count(*)\n'
               'from application\n'
               'where id = %s;'),
     'result': ['1']},
    {'id': 59,
     'query': ('select id\n'
               'from application\n'
               'order by id asc;'),
     'result': [[1], ]},
    {'id': 60,
     'query': ('select id\n'
               '      ,name\n'
               '      ,description\n'
               '      ,outcome\n'
               '      ,date_format(creation, \'%%Y-%%m-%%dT%%TZ\') creation\n'
               '      ,enabled\n'
               'from application\n'
               'where id = %s;'),
     'result': [['1',
                 'test_app',
                 'test_app_desc',
                 'JOB',
                 '1970-01-01T00:00:00',
                 1], ]},
    {'id': 61,
     'query': ('select pname\n'
               '      ,pvalue\n'
               '      ,pdesc\n'
               'from application_parameter\n'
               'where app_id=%s\n'
               'order by param_id asc;'),
     'result': [['test_param_name1',
                 'test_param_value1',
                 'test_param_desc1'],
                ['test_param_name2',
                 'test_param_value2',
                 'test_param_desc2'], ]},
    {'id': 62,
     'query': ('select id\n'
               'from infrastructure\n'
               'where app_id = %s order by id asc;'),
     'result': ['1']},
    {'id': 63,
     'query': ('insert into application (id\n'
               '                        ,name\n'
               '                        ,description\n'
               '                        ,outcome\n'
               '                        ,creation\n'
               '                        ,enabled)\n'
               'select if(max(id) is NULL,1,max(id)+1) -- new id\n'
               '      ,%s                              -- name\n'
               '      ,%s                              -- description\n'
               '      ,%s                              -- outcome\n'
               '      ,now()                           -- creation\n'
               '      ,%s                              -- enabled\n'
               'from application;'),
     'result': []},
    {'id': 64,
     'query': ('insert into application_parameter (app_id\n'
               '                                  ,param_id\n'
               '                                  ,pname\n'
               '                                  ,pvalue\n'
               '                                  ,pdesc)\n'
               'select %s                                          \n'
               '      ,if(max(param_id) is NULL,1,max(param_id)+1) \n'
               '      ,%s                                          \n'
               '      ,%s                                          \n'
               '      ,%s                                          \n'
               'from application_parameter\n'
               'where app_id=%s'),
     'result': []},
    {'id': 65,
     'query': 'select max(id) from application;',
     'result': [[1], ]},
    {'id': 66,
     'query': ('insert into application_file (app_id\n'
               '                            ,file_id\n'
               '                            ,file\n'
               '                            ,path\n'
               '                            ,override)\n'
               'select %s\n'
               '      ,if(max(file_id) is NULL,1,max(file_id)+1)\n'
               '      ,%s\n'
               '      ,\'\'\n'
               '      ,TRUE\n'
               'from application_file\n'
               'where app_id=%s'),
     'result': []},
    {'id': 67,
     'query': ('select app_id,\n'
               '       name,\n'
               '       description,\n'
               '       enabled,\n'
               '       vinfra\n'
               'from infrastructure\n'
               'where id=%s\n'
               'order by 1 asc ,2 asc\n'
               'limit 1;'),
     'result': [[1,
                 'test application',
                 'test application description',
                 1,
                 0], ]},
    {'id': 68,
     'query':  ('insert into infrastructure (id\n'
                '                           ,app_id\n'
                '                           ,name\n'
                '                           ,description\n'
                '                           ,creation\n'
                '                           ,enabled\n'
                '                           ,vinfra\n'
                '                           )\n'
                'values (%s    \n'
                '       ,%s    \n'
                '       ,%s    \n'
                '       ,%s    \n'
                '       ,now() \n'
                '       ,%s    \n'
                '       ,%s);'),
     'result': None},
    {'id': 69,
     'query':  ('insert into infrastructure (id\n'
                '                           ,app_id\n'
                '                           ,name\n'
                '                           ,description\n'
                '                           ,creation\n'
                '                           ,enabled\n'
                '                           ,vinfra\n'
                '                           )\n'
                'select if(max(id) is NULL,1,max(id)+1)\n'
                '      ,0\n'
                '      ,%s\n'
                '      ,%s\n'
                '      ,now()\n'
                '      ,%s\n'
                '      ,%s\n'
                'from infrastructure;'),
     'result': None},
    {'id': 70,
     'query': ('select count(*)\n'
               'from application_file\n'
               'where app_id = %s\n'
               '  and file = %s;'),
     'result': ['1']},
    {'id': 71,
     'query': ('update application_file\n'
               'set path = %s\n'
               'where app_id = %s\n'
               '  and file = %s;'),
     'result': []},
    {'id': 72,
     'query': ('select file, path, override\n'
               'from application_file\n'
               'where app_id = %s;'),
     'result': [["test_input_file", "/tmp/test", 0], ]},
    {'id': 73,
     'query': ('select id\n'
               'from task\n'
               'where status != "PURGED"\n'
               '  and user = %s\n'
               '  and app_id = %s\n'
               'order by id desc;'),
     'result': [[1], ]},
    {'id': 74,
     'query': ('select id\n'
               'from task\n'
               'where status != "PURGED"\n'
               '  and user = %s\n'
               'order by id desc;'),
     'result': [[1], ]},
    {'id': 75,
     'query': 'select name from fg_user where id = %s;',
     'result': [['test_user', ], ]},
    {'id': 76,
     'query': ('insert into as_queue (\n'
               '   task_id\n'
               '  ,target_id\n'
               '  ,target\n'
               '  ,action\n'
               '  ,status\n'
               '  ,target_status\n'
               '  ,creation\n'
               '  ,last_change\n'
               '  ,check_ts\n'
               '  ,action_info\n'
               ') select %s,\n'
               '         NULL,\n'
               '         (select target\n'
               '          from as_queue\n'
               '          where task_id=%s\n'
               '          order by task_id asc\n'
               '          limit 1),\n'
               '         \'CLEAN\',\n'
               '         \'QUEUED\',\n'
               '         (select status\n'
               '          from as_queue\n'
               '          where task_id=%s\n'
               '          order by task_id asc\n'
               '          limit 1),\n'
               '         now(),\n'
               '         now(),\n'
               '         now(),\n'
               '         %s;'),
     'result': None},
    {'id': 77,
     'query': ('update infrastructure set\n'
               '    name=%s,\n'
               '    description=%s,\n'
               '    enabled=%s,\n'
               '    vinfra=%s\n'
               'where id=%s;'),
     'result': None},
    {'id': 78,
     'query': ('insert into infrastructure_parameter\n'
               '    (infra_id,\n'
               '     param_id,\n'
               '     pname,\n'
               '     pvalue,\n'
               '     pdesc)\n'
               '    select %s,\n'
               '           if(max(param_id) is NULL,\n'
               '              1,max(param_id)+1),\n'
               '           %s,\n'
               '           %s,\n'
               '           %s\n'
               '    from infrastructure_parameter\n'
               '    where infra_id=%s;'),
     'result': None},
    {'id': 79,
     'query': ('update application set\n'
               '    name=%s,\n'
               '    description=%s,\n'
               '    outcome=%s,\n'
               '    enabled=%s\n'
               'where id=%s;'),
     'result': None},
    {'id': 80,
     'query': ('select file, path\n'
               'from application_file\n'
               'where app_id = %s\n'
               '  and (path is not null or path != \'\');'),
     'result': [['test', 'test/path'], ]},
    {'id': 81,
     'query': ('insert into application_parameter\n'
               '    (app_id,\n'
               '     param_id,\n'
               '     pname,\n'
               '     pvalue,\n'
               '     pdesc)\n'
               '    select %s,\n'
               '           if(max(param_id) is NULL,\n'
               '              1,max(param_id)+1),\n'
               '           %s,\n'
               '           %s,\n'
               '           %s\n'
               '    from application_parameter\n'
               '    where app_id=%s;'),
     'result': None},
    {'id': 82,
     'query': ('delete from application_file\n'
               'where app_id=%s;'),
     'result': None},
    {'id': 83,
     'query': ('delete from application_file\n'
               'where app_id = %s\n'
               '  and file= %s\n'
               '  and path = %s;'),
     'result': None},
    {'id': 84,
     'query': ('insert into application_file\n'
               '    (app_id,\n'
               '     file_id,\n'
               '     file,\n'
               '     path,\n'
               '     override)\n'
               '    select %s,\n'
               '           if(max(file_id) is NULL,\n'
               '              1,max(file_id)+1),\n'
               '           %s,\n'
               '           %s,\n'
               '           TRUE\n'
               '    from application_file\n'
               '    where app_id=%s;'),
     'result': None},
    {'id': 85,
     'query': ('delete from application_parameter\n'
               'where app_id=%s;'),
     'result': None},
    {'id': 86,
     'query': ('insert into application_parameter\n'
               '    (app_id,\n'
               '     param_id,\n'
               '     pname,\n'
               '     pvalue,\n'
               '     pdesc)\n'
               '    select %s,\n'
               '           if(max(param_id) is NULL,\n'
               '              1,max(param_id)+1),\n'
               '           %s,\n'
               '           %s,\n'
               '           %s\n'
               '    from application_parameter\n'
               '    where app_id=%s;'),
     'result': None},
    {'id': 87,
     'query': 'select id from infrastructure where app_id=%s;',
     'result': [[1], ]},
    {'id': 88,
     'query': ('select count(*)=1\n'
               'from infrastructure\n'
               'where app_id=0 and id=%s;'),
     'result': [[1], ]},
    {'id': 89,
     'query': ('update infrastructure\n'
               'set app_id = %s\n'
               'where id = %s and app_id = 0;'),
     'result': None},
    {'id': 90,
     'query': ('select count(*)=1\n'
               'from infrastructure\n'
               'where id=%s;'),
     'result': [[1], ]},
    {'id': 91,
     'query': ('update infrastructure\n'
               'set app_id = 0\n'
               'where id=%s\n'
               '  and app_id=%s;'),
     'result': None},
    {'id': 92,
     'query': 'BEGIN',
     'result': None},
    {'id': 93,
     'query': 'select count(*)\n'
              'from fg_user\n'
              'where id=%s;',
     'result': [[1], ]},
    {'id': 94,
     'query': 'select id,\n'
              '       name,\n'
              '       first_name,\n'
              '       last_name,\n'
              '       institute,\n'
              '       mail,\n'
              '       date_format(creation,\n'
              '                   \'%%Y-%%m-%%dT%%TZ\') creation,\n'
              '       date_format(modified,\n'
              '                   \'%%Y-%%m-%%dT%%TZ\') modified\n'
              'from fg_user\n'
              'where name = %s;',
     'result': [['1',
                 'test_user',
                 'test_firstname',
                 'test_lastname',
                 'institute',
                 'mail',
                 '01/01/1970',
                 '01/01/1970'], ]},
    {'id': 94.1,
     'query': 'select id,\n'
              '       name,\n'
              '       first_name,\n'
              '       last_name,\n'
              '       institute,\n'
              '       mail,\n'
              '       date_format(creation,\n'
              '                   \'%%Y-%%m-%%dT%%TZ\') creation,\n'
              '       date_format(modified,\n'
              '                   \'%%Y-%%m-%%dT%%TZ\') modified\n'
              'from fg_user\n'
              'where id=%s;',
     'result': [['1',
                 'test_user',
                 'test_firstname',
                 'test_lastname',
                 'institute',
                 'mail',
                 '01/01/1970',
                 '01/01/1970'], ]},
    {'id': 95,
     'query': 'insert into fg_user (id\n'
              '                    ,name\n'
              '                    ,first_name\n'
              '                    ,last_name\n'
              '                    ,institute\n'
              '                    ,mail\n'
              '                    ,password\n'
              '                    ,creation\n'
              '                    ,modified\n'
              '                    ,enabled\n'
              '                    )\n'
              'select if(max(id) is NULL,1,max(id)+1)\n'
              '      ,%s\n'
              '      ,%s\n'
              '      ,%s\n'
              '      ,%s\n'
              '      ,%s\n'
              '      ,\'\'\n'
              '      ,now()\n'
              '      ,now()\n'
              '      ,true\n'
              'from fg_user;',
     'result': None},
    {'id': 96,
     'query': 'select id,\n'
              '       name,\n'
              '       date_format(creation,\n'
              '                   \'%%Y-%%m-%%dT%%TZ\') creation,\n'
              '       date_format(modified,\n'
              '                   \'%%Y-%%m-%%dT%%TZ\') modified\n'
              'from fg_group;',
     'result': [[1, 'test_group', '01/01/1970', '01/01/1970'], ]},
    {'id': 97,
     'query': 'select g.id,\n'
              '       g.name,\n'
              '       date_format(g.creation,\n'
              '                   \'%%Y-%%m-%%dT%%TZ\') creation,\n'
              '       date_format(g.modified,\n'
              '                   \'%%Y-%%m-%%dT%%TZ\') modified\n'
              'from fg_group g,\n'
              '     fg_user_group ug,\n'
              '     fg_user u\n'
              'where u.id = %s\n'
              '  and u.id = ug.user_id\n'
              '  and g.id = ug.group_id;',
     'result': [[1, 'test_group', '01/01/1970', '01/01/1970'], ]},
    {'id': 98,
     'query': 'select id,\n'
              '       name,\n'
              '       first_name,\n'
              '       last_name,\n'
              '       institute,\n'
              '       mail,\n'
              '       date_format(creation,\n'
              '                   \'%%Y-%%m-%%dT%%TZ\') creation,\n'
              '       date_format(modified,\n'
              '                   \'%%Y-%%m-%%dT%%TZ\') modified\n'
              'from fg_user\n',
     'result': [['1',
                 'test_user1',
                 'test_firstname',
                 'test_lastname',
                 'institute',
                 'mail',
                 '01/01/1970',
                 '01/01/1970'],
                ['2',
                 'test_user2',
                 'test_firstname',
                 'test_lastname',
                 'institute',
                 'mail',
                 '01/01/1970',
                 '01/01/1970'], ]},
    {'id': 99,
     'query': 'insert into fg_user_group (user_id,\n'
              '                           group_id,\n'
              '                           creation)\n'
              'select u.id, g.id, now()\n'
              'from fg_user u,\n'
              'fg_group g\n'
              'where u.id=%s\n'
              '  and g.id=%s\n'
              '  and (select count(*)\n'
              '       from fg_user u1,\n'
              '            fg_group g1,\n'
              '            fg_user_group ug1\n'
              '       where u1.id=%s\n'
              '         and g1.id=%s\n'
              '         and ug1.user_id=u1.id\n'
              '         and ug1.group_id=g1.id) = 0;',
     'result': None},
    {'id': 100,
     'query': 'select user_id\n'
              '      ,(select name from fg_user where id=user_id) name\n'
              '      ,date_format(creation,\n'
              '                   \'%%Y-%%m-%%dT%%TZ\') creation\n'
              '      ,expiry\n'
              '      ,(creation+expiry)-now()>0\n'
              '      ,if((creation+expiry)-now()>0,\n'
              '          (creation+expiry)-now(),\n'
              '          0) lasting\n'
              'from fg_token\n'
              'where token=%s;',
     'result': [['1',
                 'test_user',
                 None,
                 None,
                 1,
                 1000, ], ]},
    {'id': 101,
     'query': 'select count(*)\n'
              'from fg_user\n'
              'where name = %s\n'
              '   or mail = %s;',
     'result': [['0'], ]},
    {'id': 102,
     'query': 'select count(*)>0 from srv_registry where uuid = %s;',
     'result': [[1], ]},
    {'id': 103,
     'query': 'select cfg_hash srv_hash\n'
              'from srv_registry\n'
              'where uuid=%s;',
     'result': [['TEST_CFG_HASH', 'TEST_SRV_HASH'], ]},
    {'id': 104,
     'query': 'select md5(group_concat(value)) cfg_hash\n'
              'from srv_config\n'
              'where uuid = %s\n'
              'group by uuid;',
     'result': [['TEST_MDG_GROUP_CONTACT_VALUE'], ]},
    {'id': 105,
     'query': 'select name,\n'
              '       value\n'
              'from srv_config\n'
              'where uuid=%s and enabled=%s;',
     'result': [['TEST_CFG_NAME', 'TEST_CFG_VALUE'], ]},
    {'id': 106,
     'query': 'update srv_registry set cfg_hash = %s where uuid = %s;',
     'result': None},
    {'id': 107,
     'query': 'select group_id from fg_user_group where user_id = %s',
     'result': [[1], ]},
    {'id': 108,
     'query': 'insert into fg_group_apps (group_id, app_id, creation)\n'
              'values (%s, %s, now())',
     'result': None},
    {'id': 109,
     'query': 'delete from fg_group_apps where app_id=%s;',
     'result': None},
    {'id': 110,
     'query': 'delete from infrastructure_parameter\n'
              'where infra_id in (select id\n'
              '                   from infrastructure\n'
              '                   where app_id=%s);',
     'result': None},
    {'id': 111,
     'query': 'delete from infrastructure where app_id=%s;',
     'result': None},
    {'id': 112,
     'query': 'delete from application_file where app_id=%s;',
     'result': None},
    {'id': 113,
     'query': 'delete from application_parameter where app_id=%s;',
     'result': None},
    {'id': 114,
     'query': 'delete from application where id=%s;',
     'result': None},
]

# fgapiserver tests queries
queries = [
    {'category': 'fgapiserver',
     'statements': fgapiserver_queries}]
