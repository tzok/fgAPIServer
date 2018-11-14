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
    {'query': 'select user_id, subject\n'
              'from fg_token\n'
              'where token = %s\n'
              '  and creation+expiry > now();',
     'result': [['1', 'test_user', ], ]},
    {'query': 'insert into fg_token (token,\n'
              '                      subject,\n'
              '                      user_id,\n'
              '                      creation,\n'
              '                      expiry)\n'
              '  select %s, %s, id, now() creation, 24*60*60\n'
              '  from  fg_user\n'
              '  where name=%s\n'
              '    and fg_user.password=sha(%s);',
     'result': None},
    {'query': 'insert into fg_token (token,\n'
              '                      subject,\n'
              '                      user_id,\n'
              '                      creation,\n'
              '                      expiry)\n'
              '  select %s, %s, id, now() creation, 24*60*60\n'
              '  from  fg_user\n'
              '  where name=%s;',
     'result': None},
    {'query': 'select if(count(*)>0,uuid(),NULL) acctoken \n'
              'from fg_user \n'
              'where name=%s\n'
              '  and (select creation+expiry > now()\n'
              '       from fg_token\n'
              '       where token = %s);',
     'result': [['DELEGATED_ACCESS_TOKEN', ], ]},
]

# user_apis tests queries
queries = [
    {'category': 'user_apis',
     'statements': user_apis_queries}]
