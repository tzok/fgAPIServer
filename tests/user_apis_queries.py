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

__author__ = "Riccardo Bruno"
__copyright__ = "2015"
__license__ = "Apache"
__version__ = "v0.0.2-30-g37540b8-37540b8-37"
__maintainer__ = "Riccardo Bruno"
__email__ = "riccardo.bruno@ct.infn.it"

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
              '                   \'%%Y-%%m-%%dT%%TZ\') creation,\n'
              '       date_format(modified,\n'
              '                   \'%%Y-%%m-%%dT%%TZ\') modified\n'
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
]

# user_apis tests queries
queries = [
    {'category': 'user_apis',
     'statements': user_apis_queries}]
