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
import shutil
import base64
from fgapiserver import app
from mklogtoken import token_encode, token_decode, token_info
from fgapiserver_user import User

__author__ = "Riccardo Bruno"
__copyright__ = "2015"
__license__ = "Apache"
__version__ = "v0.0.2-30-g37540b8-37540b8-37"
__maintainer__ = "Riccardo Bruno"
__email__ = "riccardo.bruno@ct.infn.it"

# FGTESTS_STOPATFAIL environment controls the execution
# of the tests, if defined, it stops test execution as
# soon as the first test error occurs
stop_at_fail = os.getenv('FGTESTS_STOPATFAIL')
if stop_at_fail is None:
    stop_at_fail = False


class Test_UsersAPIs(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        self.app.debug = True

    def banner(self, test_name):
        print ""
        print "------------------------------------------------"
        print " Testing: %s" % test_name
        print "------------------------------------------------"

    def md5sum(self, filename, blocksize=65536):
        hash = hashlib.md5()
        with open(filename, "rb") as f:
            for block in iter(lambda: f.read(blocksize), b""):
                hash.update(block)
        return hash.hexdigest()

    def md5sum_str(self, str):
        return hashlib.md5(str).hexdigest()

    #
    # fgapiserver
    #

    # Baseline authentication must be activated
    def test_CkeckConfig(self):
        self.banner("Check configuration settings")
        self.assertEqual(
            fgapiserver.fg_config['fgapisrv_notoken'].lower(), 'false')
        self.assertEqual(
            fgapiserver.fg_config['fgapisrv_lnkptvflag'].lower(), 'false')

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
        key = "0123456789ABCDEF"
        username = 'test'
        password = 'testpwd'
        token, delegated_token = fgapiserver.create_session_token(
            username='test',
            password='testpwd',
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

    def test_GroupAdd(self):
        self.banner("group_add (fgapiserverdb)")
        new_group = self.fgapisrv_db.group_add("TEST_GROUP")
        chk_group = {'creation': '01-01-1979',
                     'id': 1,
                     'modified': '01-01-1970',
                     'name': 'TEST_GROUP'}
        self.assertEqual(chk_group, new_group)

    #
    # REST APIs - Following tests are functional tests
    #
    # MD5 values are taken from the self.md5sum_str(result.data) value
    # then they are hardcoded in the assertEqual statement

    # Get token info from GET token/
    def test_get_token_info(self):
        url = ('/v1.0/token')
        headers = {
            'Authorization': 'TESTSESSIONTOKEN',
        }
        result = self.app.get(
            url,
            headers=headers)
        print result
        print result.data
        print "MD5: '%s'" % self.md5sum_str(result.data)
        self.assertEqual("34fc109845dabbdf2ba6022048c9979d",
                         self.md5sum_str(result.data))

    #
    # Users
    #

    # Get access token from GET auth/ username/base64(password)
    def test_get_auth(self):
        user = 'test'
        password = base64.b64encode('testpwd')
        url = ('/v1.0/auth?username=%s&password=%s&user=delegated_user'
               % (user, password))

        self.banner("GET '%s'" % url)
        result = self.app.get(url)
        print result
        print result.data
        print "MD5: '%s'" % self.md5sum_str(result.data)
        self.assertEqual("d499b1c6c90550b83f4ce029fdb166c7",
                         self.md5sum_str(result.data))

    # Get access token from POST auth/ username/base64(password)
    def test_post_auth(self):
        user = 'test'
        password = base64.b64encode('testpwd')
        url = ('/v1.0/auth')
        headers = {
            'Authorization': "%s:%s" % (user, password),
        }
        result = self.app.post(
            url,
            content_type="application/json",
            headers=headers)
        print result
        print result.data
        print "MD5: '%s'" % self.md5sum_str(result.data)
        self.assertEqual("6dc5ac7125d809b087b0c461ad2ba342",
                         self.md5sum_str(result.data))

    # Insert group POST groups/
    def test_post_groups(self):
        url = ('/v1.0/groups')
        headers = {
            'Authorization': 'TEST_ACCESS_TOKEN',
        }
        post_data = {
            'name': "TEST_GROUP"
        }
        result = self.app.post(
            url,
            data=json.dumps(post_data),
            content_type="application/json",
            headers=headers)
        print result
        print result.data
        print "MD5: '%s'" % self.md5sum_str(result.data)
        self.assertEqual("6a4376e47c877f672e47eac39e0f106e",
                         self.md5sum_str(result.data))


if __name__ == '__main__':
    print "----------------------------------"
    print "Starting unit tests ..."
    print "----------------------------------"
    unittest.main(failfast=stop_at_fail)
    print "Tests completed"
