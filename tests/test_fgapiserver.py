#!/usr/bin/env python
# Copyright (c) 2015:
# Istituto Nazionale di Fisica Nucleare (INFN), Italy
#
# See http://www.infn.it  for details on the copyrigh holder
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

import unittest
import fgapiserver
import hashlib
import json
import os
import io
import shutil
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
from fgapiserver import app
from mklogtoken import\
    token_encode,\
    token_decode,\
    token_info
from fgapiserver_user import User
from fgapiserver_db import fgapisrv_db

__author__ = 'Riccardo Bruno'
__copyright__ = '2019'
__license__ = 'Apache'
__version__ = 'v0.0.10'
__maintainer__ = 'Riccardo Bruno'
__email__ = 'riccardo.bruno@ct.infn.it'
__status__ = 'devel'
__update__ = '2019-05-27 10:41:55'

# FGTESTS_STOPATFAIL environment controls the execution
# of the tests, if defined, it stops test execution as
# soon as the first test error occurs
stop_at_fail = os.getenv('FGTESTS_STOPATFAIL') is not None


class TestfgAPIServer(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        self.app.debug = True

    @staticmethod
    def banner(test_name):
        print("\n"
              "------------------------------------------------\n"
              " Testing: %s\n"
              "------------------------------------------------\n"
              % test_name)

    @staticmethod
    def md5sum(filename, blocksize=65536):
        hash_value = hashlib.md5()
        with open(filename, "rb") as f:
            for block in iter(lambda: f.read(blocksize), b""):
                hash_value.update(block)
        return hash_value.hexdigest()

    @staticmethod
    def md5sum_str(string_value):
        str = u'%s' % string_value
        str = str.encode('utf-8')
        md5_value = hashlib.md5(str).hexdigest()
        return md5_value

    #
    # fgapiserver
    #

    # Baseline authentication must be activated

    def test_CkeckConfig(self):
        self.banner("Check configuration settings")
        self.assertEqual(
            fgapiserver.fg_config['fgapisrv_notoken'], True)
        self.assertEqual(
            fgapiserver.fg_config['fgapisrv_notokenusr'].lower(), 'test')

    def test_User(self):
        self.banner("User class")
        user = fgapiserver.User(1, 'test', 'test_token')
        self.assertEqual(1, user.get_id())
        self.assertEqual('test', user.get_name())
        self.assertEqual('test_token', user.get_token())

    def test_paginate_reposnse(self):
        self.banner("paginate_response(txt,'2','3',[])")
        response = ['111111111111111111111111111\n',
                    '222222222222222222222222222\n',
                    '333333333333333333333333333\n',
                    '444444444444444444444444444\n',
                    '555555555555555555555555555\n',
                    '666666666666666666666666666\n',
                    '777777777777777777777777777\n',
                    '888888888888888888888888888\n',
                    '999999999999999999999999999\n',
                    '000000000000000000000000000\n',
                    'AAAAAAAAAAAAAAAAAAAAAAAAAAA\n',
                    'BBBBBBBBBBBBBBBBBBBBBBBBBBB\n', ]
        expected_page = (['444444444444444444444444444\n',
                          '555555555555555555555555555\n',
                          '666666666666666666666666666\n'],
                         [{'href': '[]?page=1&per_page=3', 'rel': 'prev'},
                          {'href': '[]?page=2&per_page=3', 'rel': 'self'},
                          {'href': '[]?page=3&per_page=3', 'rel': 'next'},
                          {'href': '[]?page=4&per_page=3', 'rel': 'next'}])
        received_page = fgapiserver.paginate_response(response, '2', '3', [])
        self.assertEqual(expected_page, received_page)

    def test_checkDbVer(self):
        self.banner("checkDbVer()")
        self.assertEqual('0.0.13', fgapiserver.check_db_ver())

    def test_fgapiserver(self):
        self.banner("get_task_app_id(1)")
        self.assertEqual('1', fgapiserver.get_task_app_id(1))

    #
    # fgapiserverdb
    #

    def test_dbobject(self):
        self.banner("Testing fgapiserverdb get DB object")
        assert fgapisrv_db is not None

    def test_dbobj_connect(self):
        self.banner("Testing fgapiserverdb connect")
        conn = fgapisrv_db.connect()
        assert conn is not None

    def test_dbobj_test(self):
        self.banner("Testing fgapiserverdb test")
        result = fgapisrv_db.test()
        state = fgapisrv_db.get_state()
        print(result)
        print("DB state: %s" % (state,))
        assert state[0] is False

    def test_dbobj_create_session_token(self):
        self.banner("Testing fgapiserverdb create_session_token")
        fgapisrv_db.create_session_token('test', 'test', 'logts')
        state = fgapisrv_db.get_state()
        print("DB state: %s" % (state,))
        assert state[0] is False

    def test_dbobj_verify_session_token(self):
        self.banner("Testing fgapiserverdb verify_session_token")
        result = fgapisrv_db.verify_session_token('TESTSESSIONTOKEN')
        state = fgapisrv_db.get_state()
        print("DB state: %s" % (state,))
        assert state[0] is False
        assert result[0] == '1'
        assert result[1] == 'test_user'

    def test_get_token_info(self):
        self.banner("Testing fgapiserverdb get_token_info")
        result = fgapisrv_db.get_token_info('TESTSESSIONTOKEN')
        state = fgapisrv_db.get_state()
        print("DB state: %s" % (state, ))
        print("Result: %s" % result)
        assert state[0] is False
        expected_result = {
            'user_id': '1',
            'creation': '01/01/1970',
            'expiry': '01/01/1970',
            'token': 'TESTSESSIONTOKEN',
            'valid': True,
            'user_name': 'test_user',
            'lasting': 1000}
        assert result == expected_result

    def test_dbobj_register_token(self):
        self.banner("Testing fgapiserverdb register_token")
        result = fgapisrv_db.register_token(1, 'TESTSESSIONTOKEN', 'SUBJ')
        state = fgapisrv_db.get_state()
        print(result)
        print("DB state: %s" % (state,))
        assert state[0] is False

    def test_dbobj_verify_user_role(self):
        self.banner("Testing fgapiserverdb verify_user_role")
        result = fgapisrv_db.verify_user_role(1, 'test_role')
        state = fgapisrv_db.get_state()
        print("DB state: %s" % (state,))
        assert state[0] is False
        assert result > 0

    def test_dbobj_verify_user_app(self):
        self.banner("Testing fgapiserverdb verify_user_app")
        result = fgapisrv_db.verify_user_app(1, 1)
        state = fgapisrv_db.get_state()
        print("DB state: %s" % (state,))
        assert state[0] is False
        assert result == '1'

    def test_dbobj_same_group(self):
        self.banner("Testing fgapiserverdb same_group")
        result = fgapisrv_db.same_group('test_user1', 'test_user2')
        state = fgapisrv_db.get_state()
        print("DB state: %s" % (state,))
        assert state[0] is False
        assert result > 0

    def test_dbobj_get_user_info_by_name(self):
        self.banner("Testing fgapiserverdb get_user_info_by_name")
        result = fgapisrv_db.get_user_info_by_name('test_user1')
        state = fgapisrv_db.get_state()
        print("DB state: %s" % (state,))
        assert state[0] is False
        assert result is not None

    def test_dbobj_get_ptv_groups(self):
        self.banner("Testing fgapiserverdb get_ptv_groups")
        result = fgapisrv_db.get_ptv_groups(['test_group1',
                                             'test_group2'])
        state = fgapisrv_db.get_state()
        print("DB state: %s" % (state,))
        assert state[0] is False
        assert 'test_group1' in result
        assert 'test_group2' in result

    def test_dbobj_register_ptv_subjec(self):
        self.banner("Testing fgapiserverdb register_ptv_subject")
        result = fgapisrv_db.register_ptv_subject('test_user',
                                                  ['test_group1',
                                                   'test_group2'])
        state = fgapisrv_db.get_state()
        print("DB state: %s" % (state,))
        assert state[0] is False
        assert result[0] == 1
        assert result[1] == 'test_user'

    def test_dbobj_register_task_exists(self):
        self.banner("Testing fgapiserverdb task_exists")
        result = fgapisrv_db.task_exists(1, 1, [1])
        state = fgapisrv_db.get_state()
        print("DB state: %s" % (state,))
        assert state[0] is False
        assert result is True

    def test_dbobj_get_task_record(self):
        self.banner("Testing fgapiserverdb get_task_record")
        result = fgapisrv_db.get_task_record(1)
        state = fgapisrv_db.get_state()
        print("DB state: %s" % (state,))
        assert state[0] is False
        assert result is not None
        print(result)
        assert result['description'] == 'test task'

    def test_dbobj_get_task_status(self):
        self.banner("Testing fgapiserverdb get_task_status")
        result = fgapisrv_db.get_task_status(1)
        state = fgapisrv_db.get_state()
        print("DB state: %s" % (state,))
        assert state[0] is False
        assert result == 'WAITING'

    def test_dbobj_get_task_input_files(self):
        self.banner("Testing fgapiserverdb get_task_input_files")
        result = fgapisrv_db.get_task_input_files(1)
        state = fgapisrv_db.get_state()
        print("DB state: %s" % (state,))
        assert state[0] is False
        assert result is not None
        assert len(result) == 2

    def test_dbobj_get_task_output_files(self):
        self.banner("Testing fgapiserverdb get_task_output_files")
        result = fgapisrv_db.get_task_output_files(1)
        state = fgapisrv_db.get_state()
        print("DB state: %s" % (state,))
        assert state[0] is False
        assert result is not None
        assert len(result) == 2

    def test_dbobj_get_app_detail(self):
        self.banner("Testing fgapiserverdb get_app_detail")
        result = fgapisrv_db.get_app_detail(1)
        state = fgapisrv_db.get_state()
        print("DB state: %s" % (state,))
        assert state[0] is False
        assert result is not None
        assert result['name'] == 'test application'

    def test_dbobj_get_task_app_detail(self):
        self.banner("Testing fgapiserverdb get_task_app_detail")
        result = fgapisrv_db.get_task_app_detail(1)
        state = fgapisrv_db.get_state()
        print("DB state: %s" % (state,))
        assert state[0] is False
        assert result is not None
        assert result['name'] == 'test application'

    def test_dbobj_get_task_info(self):
        self.banner("Testing fgapiserverdb get_task_info")
        result = fgapisrv_db.get_task_info(1)
        state = fgapisrv_db.get_state()
        print("DB state: %s" % (state,))
        assert state[0] is False
        assert result is not None
        assert result['description'] == 'test task'

    def test_dbobj_get_app_files(self):
        self.banner("Testing fgapiserverdb get_app_files")
        result = fgapisrv_db.get_app_files(1)
        state = fgapisrv_db.get_state()
        print("DB state: %s" % (state,))
        assert state[0] is False
        assert result is not None
        assert len(result) == 2

    test_dir = '/tmp/test'

    def create_test_json(self):
        try:
            os.stat(self.test_dir)
        except OSError:
            os.mkdir(self.test_dir)
        f = open('%s/1.json' % self.test_dir, 'w')
        f.write('{}')
        f.close()

    def destroy_test_json(self):
        shutil.rmtree(self.test_dir)

    def test_dbobj_init_task(self):
        self.banner("Testing fgapiserverdb init_task")
        self.create_test_json()
        result = fgapisrv_db.init_task(1,
                                       'test_application',
                                       'test_user',
                                       ['arg 1', 'arg 2'],
                                       [{'name': 'test_ifile1',
                                         'path': '/path/to/file1',
                                         'override': False},
                                        {'name': 'test_ifile2',
                                         'path': '/path/to/file2',
                                         'override': True}, ],
                                       [{'name': 'test_ofile_1'},
                                        {'name': 'test_ofile_2'}, ],
                                       '')
        self.destroy_test_json()
        state = fgapisrv_db.get_state()
        print("DB state: %s" % (state,))
        assert state[0] is False
        assert result == 1

    def test_dbobj_get_task_io_sandbox(self):
        self.banner("Testing fgapiserverdb get_task_io_sandbox")
        result = fgapisrv_db.get_task_io_sandbox(1)
        state = fgapisrv_db.get_state()
        print("DB state: %s" % (state,))
        assert state[0] is False
        assert result == '/tmp/iosandbox'

    def test_dbobj_update_iniput_sandbox_file(self):
        self.banner("Testing fgapiserverdb update_iniput_sandbox_file")
        result = fgapisrv_db.update_input_sandbox_file(1,
                                                       'test_file1',
                                                       '/path/to/file')
        state = fgapisrv_db.get_state()
        print(result)
        print("DB state: %s" % (state,))
        assert state[0] is False

    def test_dbobj_is_input_sandbox_ready(self):
        self.banner("Testing fgapiserverdb is_input_sandbox_ready")
        result = fgapisrv_db.is_input_sandbox_ready(1)
        state = fgapisrv_db.get_state()
        print("DB state: %s" % (state,))
        assert state[0] is False
        assert result is True

    def test_dbobj_submit_task(self):
        self.banner("Testing fgapiserverdb submit_task")
        self.create_test_json()
        result = fgapisrv_db.submit_task(1)
        state = fgapisrv_db.get_state()
        print("DB state: %s" % (state,))
        self.destroy_test_json()
        assert state[0] is False
        assert result is True

    def test_dbobj_enqueue_task_request(self):
        self.banner("Testing fgapiserverdb enqueue_task_request")
        self.create_test_json()
        result = fgapisrv_db.enqueue_task_request(
            {'status': 'WAITING',
             'description': 'test task',
             'creation': '1970-01-01T00:00:00',
             'iosandbox': '/tmp/test',
             'user': 'test user',
             'id': '1',
             'output_files': [
                 {'url': 'file?path=%2Ftmp&name=output_file_1',
                  'name': 'output_file_1'},
                 {'url': 'file?path=%2Ftmp&name=output_file_2',
                  'name': 'output_file_2'}],
             'application': {
                 'infrastructures': [
                     {'status': 'enabled',
                      'description': ('test infrastructure for '
                                      'test application'),
                      'parameters': [
                          {'name': 'test_infra_param_name_1',
                           'value': 'test_infra_param_value_1'},
                          {'name': 'test_infra_param_name_2',
                           'value': 'test_infra_param_value_2'}],
                      'creation': '1970-01-01T00:00:00',
                      'virtual': 'real',
                      'id': '1',
                      'name': 'test infra'}],
                 'description': 'test application description',
                 'parameters': [
                     {'param_name': 'test_pname1',
                      'param_value': 'test_pvalue1'},
                     {'param_name': 'test_pname2',
                      'param_value': 'test_pvalue2'}],
                 'creation': '1970-01-01T00:00:00',
                 'enabled': True,
                 'outcome': 'JOB',
                 'id': '1',
                 'name': 'test application'},
             'arguments': ['argument'],
             'runtime_data': [
                 {'name': 'userdata_name_1',
                  'proto': 'NULL',
                  'last_change': '1970-01-01T00:00:00',
                  'creation': '1970-01-01T00:00:00',
                  'value': 'userdata_value_1',
                  'type': 'NULL',
                  'description': 'userdata_desc_1'},
                 {'name': 'userdata_name_2',
                  'proto': 'NULL',
                  'last_change': '1970-01-01T00:00:00',
                  'creation': '1970-01-01T00:00:00',
                  'value': 'userdata_value_2',
                  'type': 'NULL',
                  'description': 'userdata_desc_2'}],
             'input_files': [{'status': 'NEEDED',
                              'name': 'input_file_1'},
                             {'status': 'READY',
                              'url': ('file?path=%2Ftmp%2Ftest&name='
                                      'input_file_2'),
                              'name': 'input_file_2'}],
             'last_change': '1970-01-01T00:00:00'})
        state = fgapisrv_db.get_state()
        print("DB state: %s" % (state,))
        self.destroy_test_json()
        assert state[0] is False
        assert result is True

    def test_dbobj_get_task_list(self):
        self.banner("Testing fgapiserverdb get_task_list")
        result = fgapisrv_db.get_task_list((1, 'test_user'), 1)
        state = fgapisrv_db.get_state()
        print("DB state: %s" % (state,))
        assert state[0] is False
        assert result == [1]

    def test_dbobj_delete(self):
        self.banner("Testing fgapiserverdb delete")
        result = fgapisrv_db.delete(1)
        state = fgapisrv_db.get_state()
        print("DB state: %s" % (state,))
        assert state[0] is False
        assert result is True

    def test_dbobj_patch_task(self):
        self.banner("Testing fgapiserverdb patch_task")
        result = fgapisrv_db.patch_task(
            1,
            [{'data_name': 'test_data_name1',
              'data_value': 'test_data_value1',
              'data_desc': 'test_data_desc1',
              'data_type': 'test_data_type1',
              'data_proto': 'test_data_proto1'},
             {'data_name': 'test_data_name2',
              'data_value': 'test_data_value2',
              'data_desc': 'test_data_desc2',
              'data_type': 'test_data_type2',
              'data_proto': 'test_data_proto2'}])
        state = fgapisrv_db.get_state()
        print("DB state: %s" % (state,))
        assert state[0] is False
        assert result is True

    def test_dbobj_is_overridden_sandbox(self):
        self.banner("Testing fgapiserverdb is_overridden_sandbox")
        result = fgapisrv_db.is_overridden_sandbox(1)
        state = fgapisrv_db.get_state()
        print("DB state: %s" % (state,))
        assert state[0] is False
        assert result is True

    def test_dbobj_get_file_task_id(self):
        self.banner("Testing fgapiserverdb get_file_task_id")
        result = fgapisrv_db.get_file_task_id('test_file',
                                              '/tmp/testdir')
        state = fgapisrv_db.get_state()
        print("DB state: %s" % (state,))
        assert state[0] is False
        assert result == '1'

    def test_dbobj_status_change(self):
        self.banner("Testing fgapiserverdb status_change")
        result = fgapisrv_db.status_change(1, 'TEST')
        state = fgapisrv_db.get_state()
        print(result)
        print("DB state: %s" % (state,))
        assert state[0] is False

    def test_dbobj_app_exists(self):
        self.banner("Testing fgapiserverdb app_exists")
        result = fgapisrv_db.app_exists(1)
        state = fgapisrv_db.get_state()
        print("DB state: %s" % (state,))
        assert state[0] is False
        assert result is True

    def test_dbobj_get_app_list(self):
        self.banner("Testing fgapiserverdb get_app_list")
        result = fgapisrv_db.get_app_list()
        state = fgapisrv_db.get_state()
        print("DB state: %s" % (state,))
        assert state[0] is False
        assert result == [1]

    def test_dbobj_get_app_record(self):
        self.banner("Testing fgapiserverdb get_app_record")
        result = fgapisrv_db.get_app_record(1)
        state = fgapisrv_db.get_state()
        print("DB state: %s" % (state,))
        assert state[0] is False
        assert result['name'] == 'test application'

    def test_dbobj_init_app(self):
        self.banner("Testing fgapiserverdb init_app")
        result = fgapisrv_db.init_app(
            'test application',
            'test application description',
            'JOB',
            True,
            [{'name': 'test_param_name1',
              'value': 'test_param_value1',
              'description': 'test_param_desc1'},
             {'name': 'test_param_name1',
              'value': 'test_param_value1',
              'description': 'test_param_desc1'}],
            [],
            [{'name': 'test_app_file1'},
             {'name': 'test_app_file2'}],
            [1])
        state = fgapisrv_db.get_state()
        print("DB state: %s" % (state,))
        assert state[0] is False
        assert result == 1

    def test_dbobj_get_infra_record(self):
        self.banner("Testing fgapiserverdb get_infra_record")
        result = fgapisrv_db.get_infra_record(1)
        state = fgapisrv_db.get_state()
        print("DB state: %s" % (state,))
        assert state[0] is False
        assert result['name'] == 'test infra'

    def test_dbobj_insert_or_update_app_file(self):
        self.banner("Testing fgapiserverdb insert_or_update_app_file")
        result = fgapisrv_db.insert_or_update_app_file(1,
                                                       'test_app_file',
                                                       'test/file/path')
        state = fgapisrv_db.get_state()
        print("DB state: %s" % (state,))
        assert state[0] is False
        assert result is True

    def test_dbobj_init_infra(self):
        self.banner("Testing fgapiserverdb init_infra")
        result = fgapisrv_db.init_infra(
            'Test infrastructure',
            'Test infrastructure description',
            True,
            False,
            {})
        state = fgapisrv_db.get_state()
        print("DB state: %s" % (state,))
        assert state[0] is False
        assert result == '1'

    def test_dbobj_infra_change(self):
        self.banner("Testing fgapiserverdb infra_change")
        infra_desc = {"id": 1,
                      "name": "Infra test (changed)",
                      "enabled": False,
                      "virtual": True,
                      "description": "ansshifnra (changed)",
                      "parameters": [{"name": "jobservice",
                                      "value": "ssh://fgtest",
                                      "description": "fgtest ssh hots"}]}
        result = fgapisrv_db.infra_change(1, infra_desc)
        state = fgapisrv_db.get_state()
        print("DB state: %s" % (state,))
        assert state[0] is False
        assert result is True

    def test_dbobj_app_change(self):
        self.banner("Testing fgapiserverdb app_change")
        app_desc = {
            "files": ["tosca_template.yaml",
                      "tosca_test.sh"],
            "name": "hostname@toscaIDC",
            "parameters": [{"name": "target_executor",
                            "value": "ToscaIDC",
                            "description": ""},
                           {"name": "jobdesc_executable",
                            "value": "tosca_test.sh",
                            "description": "unused"},
                           {"name": "jobdesc_output",
                            "value": "stdout.txt",
                            "description": "unused"},
                           {"name": "jobdesc_error",
                            "value": "stderr.txt",
                            "description": "unused"}],
            "outcome": "JOB",
            "enabled": True,
            "id": "1",
            "infrastructures": [4],
            "description": "hostname tester application on toscaIDC"}
        result = fgapisrv_db.app_change(1, app_desc)
        state = fgapisrv_db.get_state()
        print("DB state: %s" % (state,))
        assert state[0] is False
        assert result is True

    def test_dbobj_get_file_app_id(self):
        self.banner("Testing fgapiserverdb get_file_app_id")
        app_id = fgapisrv_db.get_file_app_id('/tmp', 'input.txt')
        state = fgapisrv_db.get_state()
        print("DB state: %s" % (state,))
        assert state[0] is False
        assert app_id is not None

    #
    # mklogtoken
    #
    def test_mklogtoken(self):
        self.banner("Testing tokenEncode/tokenDecode/tokenInfo")
        key = "0123456789ABCDEF"
        username = 'test'
        password = 'testpwd'
        token = token_encode(key, username, password)
        tinfo = token_decode(key, token)
        print("Token with key: '%s':"
              "encoding: 'username:=%s:"
              "password=%s:"
              "timestamp=<issue_time>' is '%s'"
              % (key, username, password, token))
        print("Decoded token: '%s' -> '%s'" % (token, tinfo))
        username2, password2, timestamp2 = token_info(key, token)
        print("Token info: 'username=%s:password=%s:timestamp=%s'"
              % (username2, password2, timestamp2))
        self.assertEqual("%s:%s" % (username, password), "%s:%s" % (username2,
                                                                    password2))

    #
    # fgapiserver_user
    #
    def test_fgapiserver_user(self):
        self.banner("Testing user")
        user = User(1, "test_user", "test_token")
        assert user is not None

    #
    # REST APIs - Following tests are functional tests
    #
    # MD5 values are taken from the self.md5sum_str(result.data) value
    # then they are hardcoded in the assertEqual statement
    # check_result function verifies the API result
    #

    def check_result(self, result, md5, retcode):
        try:
            data = str(result.data, 'utf-8')
        except TypeError:
            data = str(result.data).encode('utf-8')
        data_md5 = self.md5sum_str(data)
        print("Result: '%s'" % result)
        print("Result data: '%s'" % data)
        print("MD5: '%s'" % data_md5)
        if retcode is not None:
            self.assertEqual(result.status_code, retcode)
        if md5 is not None:
            if isinstance(md5, type(())):
                self.assertTrue(md5[0] == data_md5 or
                                md5[1] == data_md5)
            else:
                self.assertEqual(md5, data_md5)

    def test_get_index(self):
        self.banner("GET /v1.0/")
        result = self.app.get('/v1.0/')
        try:
            data = str(result.data, 'utf-8')
        except TypeError:
            data = str(result.data).encode('utf-8')
        data_md5 = self.md5sum_str(data)
        print("Result: '%s'" % result)
        print("Result data: '%s'" % data)
        print("MD5: '%s'" % data_md5)
        result_data = json.loads(data)
        self.assertEqual('versions' in result_data, True)
        self.assertEqual('config' in result_data, True)

    """
    INFRASTRUCTURES
    """

    def test_get_infrastructures(self):
        self.banner("GET /v1.0/infrastructures")
        result = self.app.get('/v1.0/infrastructures')
        self.check_result(result,
                          ('e1c2b011c27a9b1c0eaf9f56cbb25e50',
                           '97b437330ba649e1a54d0abbf9ff0b93'), None)

    def test_get_infrastructure(self):
        self.banner("GET /v1.0/infrastructures/1")
        result = self.app.get('/v1.0/infrastructures/1')
        self.check_result(result,
                          ('9eee7f83fa43289b18732e8cc915138e',
                           '0f814c236f26fd5fd5feb6449f9f8afc'), None)

    def test_post_infrastructures(self):
        post_data = {'virtual': False,
                     'name': 'Test infrastructure',
                     'description': 'Testinfrastructure description',
                     'parameters': [],
                     'enabled': True}
        self.banner("POST /v1.0/infrastructures")
        result = self.app.post(
            '/v1.0/infrastructures',
            data=json.dumps(post_data),
            content_type="application/json")
        self.check_result(result,
                          ('017c4bc1cf1db5c32a0157e21571f97c',
                           '0ccd202bbf2ccbcded52eab2a64857bf'), None)

    def test_delete_infrastructure(self):
        self.banner("DELETE /v1.0/infrastructures/1")
        result = self.app.delete('/v1.0/infrastructures/1')
        self.check_result(result, "8ba55904600d405ea07f71e499ca3aa5", None)

    """
    APPLICATIONS
    """
    def test_get_applications(self):
        self.banner("GET /v1.0/applications")
        result = self.app.get('/v1.0/applications')
        self.check_result(result,
                          ('ca4891fa366cc77877364956ba7277b1',
                           'bf6dd500b7a7a72510139484c9588da6'), None)

    def test_get_application(self):
        self.banner("GET /v1.0/applications/1")
        result = self.app.get('/v1.0/applications/1')
        self.check_result(result,
                          ('e333a6935246027beeb48bf51b812a2f',
                           '473edf1da15f42eaf32992a3d759e631'), None)

    def test_post_application(self):
        post_data = {'name': 'Test application',
                     'description': 'Test application description',
                     'parameters': [],
                     'enabled': True}
        self.banner("POST /v1.0/applications")
        result = self.app.post(
            '/v1.0/applications',
            data=json.dumps(post_data),
            content_type="application/json")
        self.check_result(result,
                          ('4bd582a980b6021a13d8f1ea63d4104b',
                           'ac77cfbce136e375e4692d07212cb725'), None)

    def test_delete_application(self):
        self.banner("DELETE /v1.0/applications/1")
        result = self.app.delete('/v1.0/applications/1')
        self.check_result(result, None, 204)

    def test_get_application_input(self):
        self.banner("GET /v1.0/applications/1/input")
        result = self.app.get('/v1.0/applications/1/input')
        self.check_result(result,
                          ('5aacc0679a0791b896d97cdf50564945',
                           'b51fdff5c6e13ef4c4ed7a9b4bacd153'), 200)

    def test_post_application_input(self):
        self.banner("POST /v1.0/applications/1/input")
        # Upolad a file
        data = {
            'file[]': (io.BytesIO(b"Test file stream 1"), 'test_file_1'),
        }
        result = self.app.post('/v1.0/applications/1/input',
                               data=data,
                               content_type='multipart/form-data')
        self.check_result(result,
                          ('e65a989bab5f764c547c2027e1884b0f',
                           'eb546a7dc4a23c03b65eca8bfb74ced1'), None)
        data = {
            'file[]': (io.BytesIO(b"Test file stream 2"), 'test_file_2'),
        }
        result = self.app.post('/v1.0/applications/1/input',
                               data=data,
                               content_type='multipart/form-data')
        self.check_result(result,
                          ('3d7e1967ebfdbcdba0e0abea71c3b23e',
                           'f5173aca7b43f3895d63313dd6eaec21'), None)

    """
    TASKS
    """

    def test_get_tasks(self):
        self.banner("GET /v1.0/tasks")
        result = self.app.get('/v1.0/tasks')
        self.check_result(result,
                          ('b6fbc3c93e52713f54bb5874917309e9',
                           'cb8f131e1ec4fb565710a3b1b7d8a233'), None)

    def test_get_task(self):
        self.banner("GET /v1.0/tasks/1")
        result = self.app.get('/v1.0/tasks/1')
        self.check_result(result,
                          ('2e3b9251d2daf3b078b6b9d035fe5da8',
                           '6ab2753736658d09062ced3d7fecae6d'), None)

    def test_post_task(self):
        post_data = {'name': 'Test task',
                     'description': 'Test application execution',
                     'parameters': [],
                     'app_id': 1}
        self.banner("POST /v1.0/tasks")
        result = self.app.post(
            '/v1.0/tasks',
            data=json.dumps(post_data),
            content_type="application/json")
        self.check_result(result,
                          ('8737f277494e017f2c078330ca5ef51c',
                           'e2f5a4efa29a391496ca36935a5f106b'), None)

    def test_delete_task(self):
        self.banner("DELETE /v1.0/task/1")
        result = self.app.delete('/v1.0/tasks/1')
        self.check_result(result, None, 204)


if __name__ == '__main__':
    print("----------------------------------\n"
          "Starting unit tests ...\n"
          "----------------------------------\n")
    unittest.main(failfast=stop_at_fail)
    print("Tests completed")
