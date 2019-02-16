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

__author__ = "Riccardo Bruno"
__copyright__ = "2015"
__license__ = "Apache"
__version__ = "v0.0.2-30-g37540b8-37540b8-37"
__maintainer__ = "Riccardo Bruno"
__email__ = "riccardo.bruno@ct.infn.it"

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
        print ""
        print "------------------------------------------------"
        print " Testing: %s" % test_name
        print "------------------------------------------------"

    @staticmethod
    def md5sum(filename, blocksize=65536):
        md5_value = hashlib.md5()
        with open(filename, "rb") as f:
            for block in iter(lambda: f.read(blocksize), b""):
                md5_value.update(block)
        return md5_value.hexdigest()

    @staticmethod
    def md5sum_str(string):
        return hashlib.md5(string).hexdigest()

    #
    # auth/ endpoint 
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

    #
    # fgapiserverdb
    #
    fgapisrv_db = fgapiserver.get_fgapiserver_db()

    def test_CreateSessionToken(self):
        self.banner("create_session_token (fgapiserverdb)")
        username = 'test',
        password = 'testpwd'
        token = self.fgapisrv_db.create_session_token(username, password, None)
        self.assertEqual(token, 'TEST_ACCESS_TOKEN')

    def test_VerifySessionToken(self):
        self.banner("verify_session_token (fgapiserverdb)")
        sestoken = 'TEST_ACCESS_TOKEN'
        user_id, name = self.fgapisrv_db.verify_session_token(sestoken)
        self.assertEqual(user_id, '1')
        self.assertEqual(name, 'test_user')

    #
    # REST APIs - Following tests are functional tests
    #
    # MD5 values are taken from the self.md5sum_str(result.data) value
    # then they are hardcoded in the assertEqual statement

    # Token in header, just shows token info 
    def test_get_log_token_header(self):
        self.banner("GET /v1.0/auth")
        headers = {
            'Authorization': 'TEST_ACCESS_TOKEN',
        }
        url = '/v1.0/auth'
        result = self.app.get(url,
                              headers=headers)
        print result
        print result.data
        print "MD5: '%s'" % self.md5sum_str(result.data)
        self.assertEqual("4f05b2ed2ec408503e56c633a9315ecd",
                         self.md5sum_str(result.data))

    # Session token from credentials as filter
    def test_get_log_token_filter(self):
        self.banner("GET /v1.0/auth")
        test_password = 'test_password'
        test_password_b64 = base64.b64encode(test_password)
        url = '/v1.0/auth?username=test_user&password=%s' % test_password_b64
        result = self.app.get(url)
        print result
        print result.data
        print "MD5: '%s'" % self.md5sum_str(result.data)
        self.assertEqual("4f05b2ed2ec408503e56c633a9315ecd",
                         self.md5sum_str(result.data))

     
    # Session token creation user:password
    def test_post_users_column(self):
        self.banner("POST /v1.0/auth")
        test_password = 'test_password'
        test_password_b64 = base64.b64encode(test_password)
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
        print result
        print result.data
        print "MD5: '%s'" % self.md5sum_str(result.data)
        self.assertEqual("4f05b2ed2ec408503e56c633a9315ecd",
                         self.md5sum_str(result.data))

    # Session token creation user/password
    def test_post_users_slash(self):
        self.banner("POST /v1.0/auth")
        test_password = 'test_password'
        test_password_b64 = base64.b64encode(test_password)
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
        print result
        print result.data
        print "MD5: '%s'" % self.md5sum_str(result.data)
        self.assertEqual("4f05b2ed2ec408503e56c633a9315ecd",
                         self.md5sum_str(result.data))


if __name__ == '__main__':
    print "----------------------------------"
    print "Starting unit tests ..."
    print "----------------------------------"
    unittest.main(failfast=stop_at_fail)
    print "Tests completed"
