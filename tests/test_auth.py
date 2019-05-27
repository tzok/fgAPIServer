#!/usr/bin/env python
# Copyright (c) 2015:
# Istituto Nazionale di Fisica Nucleare (INFN), Italy
# Consorzio COMETA (COMETA), Italy
#
# See http://www.infn.it and and http://www.consorzio-cometa.it for details on
# the copyright holders.
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
import base64
from fgapiserver import app
from mklogtoken import token_encode
from fgapiserver_db import fgapisrv_db

__author__ = 'Riccardo Bruno'
__copyright__ = '2019'
__license__ = 'Apache'
__version__ = 'v0.0.10'
__maintainer__ = 'Riccardo Bruno'
__email__ = 'riccardo.bruno@ct.infn.it'
__status__ = 'devel'
__update__ = '2019-05-27 11:23:18'

# FGTESTS_STOPATFAIL environment controls the execution
# of the tests, if defined, it stops test execution as
# soon as the first test error occurs
stop_at_fail = os.getenv('FGTESTS_STOPATFAIL') is not None


class TestUsersAPIs(unittest.TestCase):

    # Test scoped veriables
    session_token = None
    log_token = None

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
        md5_value = hashlib.md5()
        with open(filename, "rb") as f:
            for block in iter(lambda: f.read(blocksize), b""):
                md5_value.update(block)
        return md5_value.hexdigest()

    @staticmethod
    def md5sum_str(string_value):
        str = u'%s' % string_value
        str = str.encode('utf-8')
        md5_value = hashlib.md5(str).hexdigest()
        return md5_value

    #
    # auth/endpoint
    #

    # Baseline authentication must be activated
    def test_CkeckConfig(self):
        self.banner("Check configuration settings")
        self.assertEqual(
            fgapiserver.fg_config['fgapisrv_notoken'], False)
        self.assertEqual(
            fgapiserver.fg_config['fgapisrv_lnkptvflag'], False)

    # create_session_token
    def test_SessionTokenLogToken(self):
        self.banner("create_session_token (token)")
        key = "0123456789ABCDEF"
        username = 'test'
        password = 'testpwd'
        logtoken = token_encode(key, username, password)
        token, delegated_token = fgapiserver.create_session_token(
            logtoken=logtoken,
            user='delegated_test_user')
        self.assertEqual(token, 'TEST_ACCESS_TOKEN')
        self.assertEqual(delegated_token, 'DELEGATED_ACCESS_TOKEN')

    # create_session_token
    def test_SessionTokenUsrnPass(self):
        self.banner("create_session_token (user/password)")
        username = 'test'
        password = 'testpwd'
        token, delegated_token = fgapiserver.create_session_token(
            username=username,
            password=password,
            user='delegated_test_user')
        self.assertEqual(token, 'TEST_ACCESS_TOKEN')
        self.assertEqual(delegated_token, 'DELEGATED_ACCESS_TOKEN')

    def test_CreateSessionToken(self):
        self.banner("create_session_token (fgapiserverdb)")
        username = 'test',
        password = 'testpwd'
        token = fgapisrv_db.create_session_token(username, password, None)
        self.assertEqual(token, 'TEST_ACCESS_TOKEN')

    def test_VerifySessionToken(self):
        self.banner("verify_session_token (fgapiserverdb)")
        sestoken = 'TEST_ACCESS_TOKEN'
        user_id, name = fgapisrv_db.verify_session_token(sestoken)
        self.assertEqual(user_id, '1')
        self.assertEqual(name, 'test_user')

    #
    # REST APIs - Following tests are functional tests
    #
    # MD5 values are taken from the self.md5sum_str(result.data) value
    # then they are hardcoded in the assertEqual statement
    # check_result function verifies the API result

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

    # Token in header, just shows token info
    def test_get_log_token_header(self):
        self.banner("GET /v1.0/auth")
        headers = {
            'Authorization': 'TEST_ACCESS_TOKEN',
        }
        url = '/v1.0/auth'
        result = self.app.get(url,
                              headers=headers)
        self.check_result(result,
                          ('33d149198896da98df257416d7f80200',
                           '6dcf15f9ed8fd7bdb110125a0c6d68f4'), None)

    # Session token from credentials as filter
    def test_get_log_token_filter(self):
        self.banner("GET /v1.0/auth")
        test_password = 'test_password'
        try:
            bytes_pass = bytes(test_password, 'utf-8')
        except TypeError:
            bytes_pass = bytes(test_password)
        test_password_b64 = base64.b64encode(bytes_pass)
        url = '/v1.0/auth?username=test_user&password=%s' % test_password_b64
        result = self.app.get(url)
        self.check_result(result,
                          ('33d149198896da98df257416d7f80200',
                           '6dcf15f9ed8fd7bdb110125a0c6d68f4'), None)

    # Session token creation user:password
    def test_post_users_column(self):
        self.banner("POST /v1.0/auth")
        test_password = 'test_password'
        try:
            bytes_pass = bytes(test_password, 'utf-8')
        except TypeError:
            bytes_pass = bytes(test_password)
        test_password_b64 = base64.b64encode(bytes_pass)
        headers = {
            'Authorization': 'test_username:%s' % test_password_b64,
        }
        post_data = {}
        url = '/v1.0/auth'
        result = self.app.post(
            url,
            data=json.dumps(post_data),
            content_type="application/json",
            headers=headers)
        self.check_result(result,
                          ('33d149198896da98df257416d7f80200',
                           '6dcf15f9ed8fd7bdb110125a0c6d68f4'), None)

    # Session token creation user/password
    def test_post_users_slash(self):
        self.banner("POST /v1.0/auth")
        test_password = 'test_password'
        try:
            bytes_pass = bytes(test_password, 'utf-8')
        except TypeError:
            bytes_pass = bytes(test_password)
        test_password_b64 = base64.b64encode(bytes_pass)
        headers = {
            'Authorization': 'test_username/%s' % test_password_b64,
        }
        post_data = {}
        url = '/v1.0/auth'
        result = self.app.post(
            url,
            data=json.dumps(post_data),
            content_type="application/json",
            headers=headers)
        self.check_result(result,
                          ('33d149198896da98df257416d7f80200',
                           '6dcf15f9ed8fd7bdb110125a0c6d68f4'), None)


if __name__ == '__main__':
    print("----------------------------------\n"
          "Starting unit tests ...\n"
          "----------------------------------\n")
    unittest.main(failfast=stop_at_fail)
    print("Tests completed")
