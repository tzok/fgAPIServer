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

__author__ = 'Riccardo Bruno'
__copyright__ = '2019'
__license__ = 'Apache'
__version__ = 'v0.0.10'
__maintainer__ = 'Riccardo Bruno'
__email__ = 'riccardo.bruno@ct.infn.it'
__status__ = 'devel'
__update__ = '2019-10-03 10:05:34'


# FGTESTS_STOPATFAIL environment controls the execution
# of the tests, if defined, it stops test execution as
# soon as the first test error occurs
stop_at_fail = os.getenv('FGTESTS_STOPATFAIL') is not None


class TestUsersAPIs(unittest.TestCase):

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
    def md5sum_str(string):
        return hashlib.md5(string).hexdigest()

    #
    # fgapiserver
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

    def test_GroupAdd(self):
        self.banner("group_add (fgapiserverdb)")
        new_group = self.fgapisrv_db.group_add("TEST_GROUP")
        chk_group = {'creation': '1970-01-01T00:00:00Z',
                     'id': 1,
                     'modified': '1970-01-01T00:00:00Z',
                     'name': 'TEST_GROUP'}
        self.assertEqual(chk_group, new_group)

    def test_DeleteGroups(self):
        self.banner("delete_user_groups (fgapiserverdb)")
        groups_to_delete = ["TEST_GROUP_1", "TEST_GROUP_2", "TEST_GROUP_3", ]
        deleted_groups = self.fgapisrv_db.delete_user_groups("TEST_USER",
                                                             groups_to_delete)
        self.assertEqual(groups_to_delete, deleted_groups)

    #
    # REST APIs - Following tests are functional tests
    #
    # MD5 values are taken from the self.md5sum_str(result.data) value
    # then they are hardcoded in the assertEqual statement

    # Get token info from GET token/
    def test_get_token_info(self):
        self.banner("API: GET token/")
        url = '/v1.0/token'
        headers = {
            'Authorization': 'TESTSESSIONTOKEN',
        }
        result = self.app.get(
            url,
            headers=headers)
        print(result.data)
        print("MD5: '%s'" % self.md5sum_str(result.data))
        self.assertEqual(result.status_code, 200)
        self.assertEqual("4a27502cda0396d9f925a93c33b17ff4",
                         self.md5sum_str(result.data))

    """
    USERS
    """

    def test_get_users(self):
        self.banner("GET /v1.0/users")
        headers = {
            'Authorization': 'TEST_ACCESS_TOKEN',
        }
        url = '/v1.0/users'
        result = self.app.get(url,
                              headers=headers)
        print(result.data)
        print("MD5: '%s'" % self.md5sum_str(result.data))
        self.assertEqual("fc3b043abff5e4f45a92229d202419d6",
                         self.md5sum_str(result.data))

    def test_post_users(self):
        self.banner("POST /v1.0/users")
        headers = {
            'Authorization': 'TEST_ACCESS_TOKEN',
        }
        post_data = {'users': [
                        {'name': 'test1',
                         'first_name': 'test first name1',
                         'last_name': 'test last name1',
                         'institute': 'test institute1',
                         'mail': 'test mail1'},
                        {'name': 'test2',
                         'first_name': 'test first name2',
                         'last_name': 'test last name2',
                         'institute': 'test institute2',
                         'mail': 'test mail2'}, ]}
        url = '/v1.0/users'
        result = self.app.post(
            url,
            data=json.dumps(post_data),
            content_type="application/json",
            headers=headers)
        print(result.data)
        print("MD5: '%s'" % self.md5sum_str(result.data))
        self.assertEqual("992c43c0e90cbe43b3855f05da0377e6",
                         self.md5sum_str(result.data))

    def test_get_user(self):
        self.banner("GET /v1.0/users/test")
        headers = {
            'Authorization': 'TEST_ACCESS_TOKEN',
        }
        url = '/v1.0/users/test'
        result = self.app.get(url,
                              headers=headers)
        print(result.data)
        print("MD5: '%s'" % self.md5sum_str(result.data))
        self.assertEqual("8d288ea0c51a7d17a75393ececfd7af8",
                         self.md5sum_str(result.data))

    def test_post_user(self):
        self.banner("POST /v1.0/users/test")
        headers = {
            'Authorization': 'TEST_ACCESS_TOKEN',
        }
        post_data = {'name': 'test',
                     'first_name': 'test first name',
                     'last_name': 'test last name',
                     'institute': 'test institute',
                     'mail': 'test mail'}
        result = self.app.post(
            '/v1.0/users/test',
            data=json.dumps(post_data),
            content_type="application/json",
            headers=headers)
        print(result.data)
        print("MD5: '%s'" % self.md5sum_str(result.data))
        self.assertEqual("8d288ea0c51a7d17a75393ececfd7af8",
                         self.md5sum_str(result.data))

    def test_get_groups(self):
        self.banner("GET /v1.0/groups")
        headers = {
            'Authorization': 'TEST_ACCESS_TOKEN',
        }
        url = '/v1.0/groups'
        result = self.app.get(url,
                              headers=headers)
        print(result.data)
        print("MD5: '%s'" % self.md5sum_str(result.data))
        self.assertEqual("44456d87fe2e72dccdb2dee997d1e4e2",
                         self.md5sum_str(result.data))

    def test_get_user_groups(self):
        self.banner("GET /v1.0/users/test/groups")
        headers = {
            'Authorization': 'TEST_ACCESS_TOKEN',
        }
        url = '/v1.0/users/test/groups'
        result = self.app.get(url,
                              headers=headers)
        print(result.data)
        print("MD5: '%s'" % self.md5sum_str(result.data))
        self.assertEqual("44456d87fe2e72dccdb2dee997d1e4e2",
                         self.md5sum_str(result.data))

    def test_post_user_groups(self):
        self.banner("POST /v1.0/users/test/groups")
        headers = {
            'Authorization': 'TEST_ACCESS_TOKEN',
        }
        post_data = {'groups': [1]}
        url = '/v1.0/users/test/groups'
        result = self.app.post(
            url,
            data=json.dumps(post_data),
            content_type="application/json",
            headers=headers)
        print(result.data)
        print("MD5: '%s'" % self.md5sum_str(result.data))
        self.assertEqual("b8d1575a174363bfe4f586af1a224043",
                         self.md5sum_str(result.data))

    # Get access token from GET auth/ username/base64(password)
    def test_get_auth(self):
        self.banner("API: GET auth/ username/base64(password)")
        user = 'test'
        password = base64.b64encode('testpwd')
        url = ('/v1.0/auth?username=%s&password=%s&user=delegated_user'
               % (user, password))
        self.banner("GET '%s'" % url)
        result = self.app.get(url)
        md5val = self.md5sum_str(result.data)
        print(result.data)
        print("MD5: '%s'" % md5val)
        self.assertEqual(result.status_code, 200)
        self.assertEqual("387ef0914ffd298b43a9e18e7f951b5f", md5val)

    # Get access token from POST auth/ username/base64(password)
    def test_post_auth(self):
        self.banner("API: POST auth/ username/base64(password)")
        user = 'test'
        password = base64.b64encode('testpwd')
        url = '/v1.0/auth'
        headers = {
            'Authorization': "%s:%s" % (user, password),
        }
        result = self.app.post(
            url,
            content_type="application/json",
            headers=headers)
        print(result.data)
        print("MD5: '%s'" % self.md5sum_str(result.data))
        self.assertEqual(result.status_code, 200)
        self.assertEqual("bc97bbe5808595f75cdf3139fac38729",
                         self.md5sum_str(result.data))

    # Get user data of test_user (GET) /users/test_user/data
    def test_user_data(self):
        self.banner("GET /v1.0/users/test_user/data")
        headers = {
            'Authorization': 'TEST_ACCESS_TOKEN',
        }
        url = '/v1.0/users/test_user/data'
        result = self.app.get(url,
                              headers=headers)
        print(result.data)
        print("MD5: '%s'" % self.md5sum_str(result.data))
        self.assertEqual("fec4498548d4b81feadbbea883f375a1",
                         self.md5sum_str(result.data))

    # Add user data to test_user (POST) /users/test_user/data
    def test_post_user_data(self):
        self.banner("POST /v1.0/users/test_user/data")
        url = '/v1.0/users/test_user/data'
        headers = {
            'Authorization': 'TEST_ACCESS_TOKEN',
        }
        post_data = {
            "data": [
              {"data_name": "TEST_DATA_NAME_1",
               "data_value": "TEST_DATA_VALUE_1",
               "data_desc": "TEST_DATA_DESCRIPTION_1",
               "data_proto": "TEST_DATA_PROTO_1",
               "data_type": "TEST_DATA_TYPE_1"}, ]
        }
        result = self.app.post(
            url,
            data=json.dumps(post_data),
            content_type="application/json",
            headers=headers)
        print(result.data)
        print("MD5: '%s'" % self.md5sum_str(result.data))
        self.assertEqual(result.status_code, 201)
        self.assertEqual("c360b0c02967fbae59731216c095734e",
                         self.md5sum_str(result.data))

        # Add user data to test_user (POST) /users/test_user/data
        def test_post_user_data(self):
            self.banner("POST /v1.0/users/test_user/data")
            url = '/v1.0/users/test_user/data'
            headers = {
                'Authorization': 'TEST_ACCESS_TOKEN',
            }
            post_data = {
                "data": [
                    {"data_name": "TEST_DATA_NAME_1",
                     "data_value": "TEST_DATA_VALUE_1",
                     "data_desc": "TEST_DATA_DESCRIPTION_1",
                     "data_proto": "TEST_DATA_PROTO_1",
                     "data_type": "TEST_DATA_TYPE_1"}, ]
            }
            result = self.app.post(
                url,
                data=json.dumps(post_data),
                content_type="application/json",
                headers=headers)
            self.assertEqual(result.status_code, 201)
            print(result.data)
            print("MD5: '%s'" % self.md5sum_str(result.data))
            self.assertEqual("c360b0c02967fbae59731216c095734e",
                             self.md5sum_str(result.data))

    # Modify user data to test_user (PATCH) /users/test_user/data
    def test_patch_user_data(self):
        self.banner("PATCH /v1.0/users/test_user/data")
        url = '/v1.0/users/test_user/data'
        headers = {
            'Authorization': 'TEST_ACCESS_TOKEN',
        }
        post_data = {
            "data": [
                {"data_name": "TEST_DATA_NAME_1",
                 "data_value": "TEST_DATA_VALUE_1",
                 "data_desc": "TEST_DATA_DESCRIPTION_1",
                 "data_proto": "TEST_DATA_PROTO_1",
                 "data_type": "TEST_DATA_TYPE_1"}, ]
        }
        result = self.app.patch(
            url,
            data=json.dumps(post_data),
            content_type="application/json",
            headers=headers)
        print(result.data)
        print("MD5: '%s'" % self.md5sum_str(result.data))
        self.assertEqual(result.status_code, 201)
        self.assertEqual("c360b0c02967fbae59731216c095734e",
                         self.md5sum_str(result.data))

    # Delete user data to test_user (PATCH) /users/test_user/data
    def test_delete_user_data(self):
        self.banner("DELETE /v1.0/users/test_user/data")
        url = '/v1.0/users/test_user/data'
        headers = {
            'Authorization': 'TEST_ACCESS_TOKEN',
        }
        post_data = {
            "data": [
                {"data_name": "TEST_DATA_NAME"}, ]
        }
        result = self.app.delete(
            url,
            data=json.dumps(post_data),
            content_type="application/json",
            headers=headers)
        print(result.data)
        print("MD5: '%s'" % self.md5sum_str(result.data))
        self.assertEqual(result.status_code, 201)
        self.assertEqual("21a94e203b2ecb70f9fa1ea1ee09c119",
                         self.md5sum_str(result.data))

    # Get data_name from user data of test_user:
    # (GET) /users/test_user/data/TEST_DATA_NAME
    def test_user_data_data_name(self):
        self.banner("GET /v1.0/users/test_user/data/TEST_DATA_NAME")
        headers = {
            'Authorization': 'TEST_ACCESS_TOKEN',
        }
        url = '/v1.0/users/test_user/data/data_name'
        result = self.app.get(url,
                              headers=headers)
        print(result.data)
        print("MD5: '%s'" % self.md5sum_str(result.data))
        self.assertEqual("b4a113e4844840aa4dab41f9ee00cbdc",
                         self.md5sum_str(result.data))

    # Add user data TEST_DATA_NAME to test_user
    # (POST) /users/test_user/data/TEST_DATA_NAME
    def test_post_user_data_data_name(self):
        self.banner("POST /v1.0/users/test_user/data/TEST_DATA_NAME")
        url = '/v1.0/users/test_user/data/TEST_DATA_NAME'
        headers = {
            'Authorization': 'TEST_ACCESS_TOKEN',
        }
        post_data = {
            "data_proto": "TEST_DATA_PROTO",
            "creation": "1970-01-01T00:00:00Z",
            "data_value": "TEST_DATA_VALUE",
            "data_type": "TEST_DATA_TYPE",
            "data_desc": "TEST_DATA_DESCRIPTION",
            "last_change": "1970-01-01T00:00:00Z"
        }
        result = self.app.post(
            url,
            data=json.dumps(post_data),
            content_type="application/json",
            headers=headers)
        print(result.data)
        print("MD5: '%s'" % self.md5sum_str(result.data))
        self.assertEqual(result.status_code, 201)
        self.assertEqual("28cb19a7754b149607feead953bded16",
                         self.md5sum_str(result.data))

    # Modify user data TEST_DATA_NAME to test_user
    # (PATCH) /users/test_user/data/TEST_DATA_NAME
    def test_patch_user_data_data_name(self):
        self.banner("PATCH /v1.0/users/test_user/data/TEST_DATA_NAME")
        url = '/v1.0/users/test_user/data/TEST_DATA_NAME'
        headers = {
            'Authorization': 'TEST_ACCESS_TOKEN',
        }
        post_data = {
            "data_name": "TEST_DATA_NAME_1",
            "data_value": "TEST_DATA_VALUE_1",
            "data_desc": "TEST_DATA_DESCRIPTION_1",
            "data_proto": "TEST_DATA_PROTO_1",
            "data_type": "TEST_DATA_TYPE_1"
        }
        result = self.app.patch(
            url,
            data=json.dumps(post_data),
            content_type="application/json",
            headers=headers)
        print(result.data)
        print("MD5: '%s'" % self.md5sum_str(result.data))
        self.assertEqual(result.status_code, 201)
        self.assertEqual("cffd220dd6f3e76fee6129ec1ac37387",
                         self.md5sum_str(result.data))

    # Delete user data TEST_DATA_NAME to test_user
    # (DELETE) /users/test_user/data/TEST_DATA_NAME
    def test_delete_user_data_data_name(self):
        self.banner("DELETE /v1.0/users/test_user/data/TEST_DATA_NAME")
        url = '/v1.0/users/test_user/data/TEST_DATA_NAME'
        headers = {
            'Authorization': 'TEST_ACCESS_TOKEN',
        }
        post_data = {}
        result = self.app.delete(
            url,
            data=json.dumps(post_data),
            content_type="application/json",
            headers=headers)
        print(result.data)
        print("MD5: '%s'" % self.md5sum_str(result.data))
        self.assertEqual(result.status_code, 201)
        self.assertEqual("cf004012cf8b5bfd10cb415ecf03269e",
                         self.md5sum_str(result.data))

    #
    # Groups
    #

    # Insert group POST groups/
    def test_post_groups(self):
        self.banner("API: POST /groups/")
        url = '/v1.0/groups'
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
        print(result.data)
        print("MD5: '%s'" % self.md5sum_str(result.data))
        self.assertEqual(result.status_code, 201)
        self.assertEqual("0ac63b091cb357a9fc33951f1acda17d",
                         self.md5sum_str(result.data))

    # Delete group DELETE user /users/<user>/groups/
    def test_delete_user_groups(self):
        self.banner("API: DELETE /users/<user>/groups/")
        url = '/v1.0/users/test_user/groups'
        headers = {
            'Authorization': 'TEST_ACCESS_TOKEN',
        }
        post_data = {
            'groups': ["TEST_GROUP1",
                       "TEST_GROUP2",
                       "TEST_GROUP3", ]
        }
        result = self.app.delete(
            url,
            data=json.dumps(post_data),
            content_type="application/json",
            headers=headers)
        print(result.data)
        print("MD5: '%s'" % self.md5sum_str(result.data))
        self.assertEqual(result.status_code, 200)
        self.assertEqual("1fe788c3f2420c8655e5cf2e8155e32b",
                         self.md5sum_str(result.data))

    # Get group apps GET /group/<group>/apps
    def test_get_group_apps(self):
        self.banner("API: GET /group/<group>/apps")
        headers = {
            'Authorization': 'TEST_ACCESS_TOKEN',
        }
        url = '/v1.0/groups/test_group/apps'
        self.banner("GET '%s'" % url)
        result = self.app.get(url,
                              headers=headers)
        print(result.data)
        print("MD5: '%s'" % self.md5sum_str(result.data))
        self.assertEqual(result.status_code, 200)
        self.assertEqual("2c9250727962b4fea8b5f613c6f51fbf",
                         self.md5sum_str(result.data))

    # Add group app POST /groups/<group>/apps
    def test_post_group_apps(self):
        self.banner("API: POST /groups/<group>/apps")
        url = '/v1.0/groups/test_group/apps'
        headers = {
            'Authorization': 'TEST_ACCESS_TOKEN',
        }
        post_data = {
            'applications': [1, 2, 3],
        }
        result = self.app.post(
            url,
            data=json.dumps(post_data),
            content_type="application/json",
            headers=headers)
        print(result.data)
        print("MD5: '%s'" % self.md5sum_str(result.data))
        self.assertEqual(result.status_code, 201)
        self.assertEqual("41e0a74c8a471c981bcb5809fdd041b2",
                         self.md5sum_str(result.data))

    # Get group roles GET /group/<group>/roles
    def test_get_group_roles(self):
        self.banner("API: GET /group/<group>/roles")
        headers = {
            'Authorization': 'TEST_ACCESS_TOKEN',
        }
        url = '/v1.0/groups/test_group/roles'
        self.banner("GET '%s'" % url)
        result = self.app.get(url,
                              headers=headers)
        print(result.data)
        print("MD5: '%s'" % self.md5sum_str(result.data))
        self.assertEqual(result.status_code, 200)
        self.assertEqual("06d634a689f15f1a8fb0af55ea2738e9",
                         self.md5sum_str(result.data))

    # Add group roles POST /groups/<group>/roles
    def test_post_group_roles(self):
        self.banner("API: POST /groups/<group>/roles")
        url = '/v1.0/groups/test_group/roles'
        headers = {
            'Authorization': 'TEST_ACCESS_TOKEN',
        }
        post_data = {
            'roles': [1, 2, 3],
        }
        result = self.app.post(
            url,
            data=json.dumps(post_data),
            content_type="application/json",
            headers=headers)
        print(result.data)
        print("MD5: '%s'" % self.md5sum_str(result.data))
        self.assertEqual(result.status_code, 201)
        self.assertEqual("ac2771bff10d98720167fac7136ccdce",
                         self.md5sum_str(result.data))

    #
    # Roles
    #

    # Get roles /roles
    def test_get_roles(self):
        self.banner("API: GET /roles")
        url = '/v1.0/roles'
        headers = {
            'Authorization': 'TEST_ACCESS_TOKEN',
        }
        result = self.app.get(
            url,
            headers=headers)
        print(result.data)
        print("MD5: '%s'" % self.md5sum_str(result.data))
        self.assertEqual(result.status_code, 200)
        self.assertEqual("06d634a689f15f1a8fb0af55ea2738e9",
                         self.md5sum_str(result.data))


if __name__ == '__main__':
    print("----------------------------------\n"
          "Starting unit tests ...\n"
          "----------------------------------\n")
    unittest.main(failfast=stop_at_fail)
    print("Tests completed")
