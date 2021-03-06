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
# user_apis_queries - Provide queries for user_apis tests
#

__author__ = 'Riccardo Bruno'
__copyright__ = '2019'
__license__ = 'Apache'
__version__ = 'v0.0.10'
__maintainer__ = 'Riccardo Bruno'
__email__ = 'riccardo.bruno@ct.infn.it'
__status__ = 'devel'
__update__ = '2019-10-18 15:19:14'

# user_apis tests queries
user_apis_queries = [
    {'id': 0,
     'query': 'select user_id, subject\n'
              'from fg_token\n'
              'where token = %s\n'
              '  and creation+expiry > now();',
     'result': [['1', 'test_user', ], ]},
    {'id': 1,
     'query': 'insert into fg_token (token,\n'
              '                      subject,\n'
              '                      user_id,\n'
              '                      creation,\n'
              '                      expiry)\n'
              '  select %s, %s, id, now() creation, 24*60*60\n'
              '  from  fg_user u\n'
              '  where u.name=%s\n'
              '    and u.password=sha(%s);',
     'result': None},
    {'id': 2,
     'query': 'insert into fg_token (token,\n'
              '                      subject,\n'
              '                      user_id,\n'
              '                      creation,\n'
              '                      expiry)\n'
              '  select %s, %s, id, now() creation, 24*60*60\n'
              '  from  fg_user u\n'
              '  where u.name=%s;',
     'result': None},
    {'id': 3,
     'query': 'select if(count(*)>0,\n'
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
              '  and (select creation+expiry > now()\n'
              '       from fg_token\n'
              '       where token = %s);',
     'result': [['new:DELEGATED_ACCESS_TOKEN', ], ]},
    {'id': 4,
     'query': 'insert into fg_group (id, name, creation, modified)\n'
              'select if(max(id) is NULL,1,max(id)+1),\n'
              '       %s,\n'
              '       now(),\n'
              '       now()\n'
              'from fg_group;',
              'result': None},
    {'id': 5,
     'query': 'select id,\n'
              '       name,\n'
              '       date_format(creation,\n'
              '                   \'%Y-%m-%dT%TZ\') creation,\n'
              '       date_format(modified,\n'
              '                   \'%Y-%m-%dT%TZ\') modified\n'
              'from fg_group\n'
              'where name = %s',
     'result': [[1, 'TEST_GROUP', '01-01-1979', '01-01-1970'], ]},
    {'id': 6,
     'query': 'select id\n'
              'from fg_group\n'
              'where name=%s;',
     'result': [[1, ], ]},
    {'id': 7,
     'query': 'delete from fg_user_group\n'
              'where user_id=%s\n'
              '  and group_id=%s;',
     'result': []},
    {'id': 8,
     'query': 'select a.id,\n'
              '       a.name,\n'
              '       a.description,\n'
              '       a.outcome,\n'
              '       date_format(a.creation,\n'
              '                   \'%Y-%m-%dT%TZ\') creation,\n'
              '       a.enabled\n'
              'from fg_group_apps ga,\n'
              '      application a\n'
              'where group_id=%s\n'
              '  and ga.app_id=a.id;',
     'result': [['1',
                 'TEST_APPLICATION',
                 'Test application',
                 'JOB',
                 '01-01-1970',
                 '1'], ]},
    {'id': 9,
     'query': 'select count(*)>0 from application where id = %s;',
     'result': [[1, ], ]},
    {'id': 10,
     'query': 'insert into fg_group_apps (group_id,\n'
              '                           app_id,\n'
              '                           creation)\n'
              'values (%s, %s, now());',
     'result': []},
    {'id': 11,
     'query': 'select t.id\n'
              'from task t,\n'
              '     fg_user u,\n'
              '     application a\n'
              'where u.id=%s\n'
              '  and t.status != \'PURGED\'\n'
              '  and t.user=u.name\n'
              '  and t.app_id=a.id\n'
              'order by t.id desc;',
     'result': [[1, ], ]},
    {'id': 12,
     'query': 'select id,\n'
              '       name,\n'
              '       date_format(creation,\n'
              '                   \'%Y-%m-%dT%TZ\') creation,\n'
              '       date_format(modified,\n'
              '                   \'%Y-%m-%dT%TZ\') modified\n'
              'from fg_role;',
     'result': [[1, 'TEST_ROLE_1', '01-01-1970', '01-01-1970'],
                [2, 'TEST_ROLE_2', '01-01-1970', '01-01-1970'],
                [3, 'TEST_ROLE_3', '01-01-1970', '01-01-1970'], ]},
    {'id': 13,
     'query': 'select r.id,\n'
              '       r.name,\n'
              '       date_format(r.creation,\n'
              '                   \'%Y-%m-%dT%TZ\') creation,\n'
              '       date_format(r.modified,\n'
              '                   \'%Y-%m-%dT%TZ\') modified\n'
              'from fg_group_role gr,\n'
              '     fg_role r\n'
              'where gr.group_id = %s\n'
              '  and gr.role_id = r.id;',
     'result': [[1, 'TEST_ROLE_1', '01-01-1970', '01-01-1970'],
                [2, 'TEST_ROLE_2', '01-01-1970', '01-01-1970'],
                [3, 'TEST_ROLE_3', '01-01-1970', '01-01-1970'], ]},
    {'id': 14,
     'query': 'select count(*)>0 from fg_role where id = %s;',
     'result': [[1, ], ]},
    {'id': 15,
     'query': 'insert into fg_group_role (group_id,\n'
              '                           role_id,\n'
              '                           creation)\n'
              'values (%s, %s, now());',
     'result': []},
    {'id': 16,
     'query': 'select ud.data_id,\n'
              '       ud.data_name,\n'
              '       ud.data_value,\n'
              '       ud.data_desc,\n'
              '       ud.data_proto,\n'
              '       ud.data_type,\n'
              '       date_format(ud.creation,\n'
              '                   \'%Y-%m-%dT%TZ\') creation,\n'
              '       date_format(ud.last_change,\n'
              '                   \'%Y-%m-%dT%TZ\') last_change\n'
              'from fg_user_data ud\n'
              'where ud.user_id=%s\n'
              '  and ud.data_id = (select max(data_id)\n'
              '                    from fg_user_data\n'
              '                    where user_id=ud.user_id\n'
              '                      and data_name=ud.data_name);',
     'result': [[1,
                 'TEST_DATA_NAME',
                 'TEST_DATA_VALUE',
                 'TEST_DATA_DESCRIPTION',
                 'TEST_DATA_PROTO',
                 'TEST_DATA_TYPE',
                 '01-01-1970',
                 '01-01-1970'], ]},
    {'id': 17,
     'query': 'insert into fg_user_data (user_id,\n'
              '                          data_id,\n'
              '                          data_name,\n'
              '                          data_value,\n'
              '                          data_desc,\n'
              '                          data_proto,\n'
              '                          data_type,\n'
              '                          creation,\n'
              '                          last_change)\n'
              'select %s,\n'
              '       (select if(max(data_id) is NULL,\n'
              '                  1,\n'
              '                  max(data_id)+1)\n'
              '        from fg_user_data\n'
              '        where user_id = %s\n'
              '          and data_name = %s),\n'
              '       %s,\n'
              '       %s,\n'
              '       %s,\n'
              '       %s,\n'
              '       %s,\n'
              '       now(),\n'
              '       now();',
     'result': None},
    {'id': 18,
     'query': 'select max(data_id)\n'
              'from fg_user_data\n'
              'where user_id=%s\n'
              '  and data_name=%s;',
     'result': '1'},
    {'id': 19,
     'query': 'update fg_user_data\n'
              'set data_value = %s,\n'
              '    data_desc = %s,\n'
              '    data_proto = %s,\n'
              '    data_type = %s,\n'
              '    last_change = now()\n'
              'where user_id=%s\n'
              '  and data_id=%s\n'
              '  and data_name=%s;',
     'result': None},
    {'id': 20,
     'query': 'delete from fg_user_data\n'
              'where user_id=%s\n'
              '  and data_name=%s;',
     'result': None},
    {'id': 21,
     'query': 'select ud.data_id,\n'
              '       ud.data_name,\n'
              '       ud.data_value,\n'
              '       ud.data_desc,\n'
              '       ud.data_proto,\n'
              '       ud.data_type,\n'
              '       date_format(ud.creation,\n'
              '                   \'%Y-%m-%dT%TZ\') creation,\n'
              '       date_format(ud.last_change,\n'
              '                   \'%Y-%m-%dT%TZ\') last_change\n'
              'from fg_user_data ud\n'
              'where ud.user_id=%s\n'
              '  and ud.data_id=(select max(data_id)\n'
              '                  from fg_user_data\n'
              '                  where user_id=ud.user_id\n'
              '                    and data_name=ud.data_name)\n'
              '  and ud.data_name=%s;',
     'result': [[1,
                 'TEST_DATA_NAME',
                 'TEST_DATA_VALUE',
                 'TEST_DATA_DESCRIPTION',
                 'TEST_DATA_PROTO',
                 'TEST_DATA_TYPE',
                 '01-01-1970',
                 '01-01-1970'], ]},
]

# user_apis tests queries
queries = [
    {'category': 'user_apis',
     'statements': user_apis_queries}]
