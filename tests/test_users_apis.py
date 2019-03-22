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
__update__ = '2019-03-22 11:41:02'


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

    def test_GroupAdd(self):
        self.banner("group_add (fgapiserverdb)")
        new_group = fgapisrv_db.group_add("TEST_GROUP")
        chk_group = {'creation': '01-01-1979',
                     'id': 1,
                     'modified': '01-01-1970',
                     'name': 'TEST_GROUP'}
        self.assertEqual(chk_group, new_group)

    def test_DeleteGroups(self):
        self.banner("delete_user_groups (fgapiserverdb)")
        groups_to_delete = ["TEST_GROUP_1", "TEST_GROUP_2", "TEST_GROUP_3", ]
        deleted_groups = fgapisrv_db.delete_user_groups("TEST_USER",
                                                        groups_to_delete)
        self.assertEqual(groups_to_delete, deleted_groups)

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
        self.check_result(result,
                          ('5d1deb89a9ea5c6e0a959fc0802115a7',
                           'd217201fe601c2cd9475d17d2b779091'), 200)

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
        self.check_result(result,
                          ('ca532b1f832ea261a3a8e9fe417cf416',
                           '1f6e310992a628fa7473c4f63c561ec5'), None)

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
        self.check_result(result,
                          ('b742b09ad65b6250b94932cbbfdfcb67',
                           '4bd146be73df313b35af48f107f3a23d'), None)

    def test_get_user(self):
        self.banner("GET /v1.0/users/test")
        headers = {
            'Authorization': 'TEST_ACCESS_TOKEN',
        }
        url = '/v1.0/users/test'
        result = self.app.get(url,
                              headers=headers)
        self.check_result(result,
                          ('e438ed9190c835b9dc54e9acf823c9db',
                           '27a2adc7411953be94a4711b088b3bb4'), None)

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
        self.check_result(result,
                          ('e438ed9190c835b9dc54e9acf823c9db',
                           '27a2adc7411953be94a4711b088b3bb4'), None)

    def test_get_groups(self):
        self.banner("GET /v1.0/groups")
        headers = {
            'Authorization': 'TEST_ACCESS_TOKEN',
        }
        url = '/v1.0/groups'
        result = self.app.get(url,
                              headers=headers)
        self.check_result(result,
                          ('83f593deea83c95adf93d55051b78eae',
                           '30661885dc0cdeb44de575468597f446'), None)

    def test_get_user_groups(self):
        self.banner("GET /v1.0/users/test/groups")
        headers = {
            'Authorization': 'TEST_ACCESS_TOKEN',
        }
        url = '/v1.0/users/test/groups'
        result = self.app.get(url,
                              headers=headers)
        self.check_result(result,
                          ('83f593deea83c95adf93d55051b78eae',
                           '30661885dc0cdeb44de575468597f446'), None)

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
        self.check_result(result, 'b8d1575a174363bfe4f586af1a224043', None)

    # Get access token from GET auth/ username/base64(password)
    def test_get_auth(self):
        self.banner("API: GET auth/ username/base64(password)")
        user = 'test'
        passwd = 'testpwd'
        try:
            bytes_pass = bytes(passwd, 'utf-8')
        except TypeError:
            bytes_pass = bytes(passwd)
        password = base64.b64encode(bytes_pass)
        url = ('/v1.0/auth?username=%s&password=%s&user=delegated_user'
               % (user, password))
        self.banner("GET '%s'" % url)
        result = self.app.get(url)
        self.check_result(result,
                          ('fa352b25bf2946f92faca1033527d10e',
                           '761b5b5b0e064a0e8c44db836b80ab64'), 200)

    # Get access token from POST auth/ username/base64(password)
    def test_post_auth(self):
        self.banner("API: POST auth/ username/base64(password)")
        user = 'test'
        passwd = 'testpwd'
        try:
            bytes_pass = bytes(passwd, 'utf-8')
        except TypeError:
            bytes_pass = bytes(passwd)
        password = base64.b64encode(bytes_pass)
        url = '/v1.0/auth'
        headers = {
            'Authorization': "%s:%s" % (user, password),
        }
        result = self.app.post(
            url,
            content_type="application/json",
            headers=headers)
        self.check_result(result,
                          ('33d149198896da98df257416d7f80200',
                           '6dcf15f9ed8fd7bdb110125a0c6d68f4'), 200)

    # Get user data of test_user (GET) /users/test_user/data
    def test_user_data(self):
        self.banner("GET /v1.0/users/test_user/data")
        headers = {
            'Authorization': 'TEST_ACCESS_TOKEN',
        }
        url = '/v1.0/users/test_user/data'
        result = self.app.get(url,
                              headers=headers)
        self.check_result(result,
                          ('663c26f118b6048b0f630c79d4183942',
                           'cb1a9cd6a613502200f149746c3deee6'), 200)

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
        self.check_result(result,
                          ('e1634c855d6102c4f4c5b491dfc6cff1',
                           'c360b0c02967fbae59731216c095734e'), 201)

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
            self.check_result(result, 'c360b0c02967fbae59731216c095734e', 201)

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
        self.check_result(result,
                          ('e1634c855d6102c4f4c5b491dfc6cff1',
                           'c360b0c02967fbae59731216c095734e'), 201)

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
        self.check_result(result, '21a94e203b2ecb70f9fa1ea1ee09c119', 201)

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
        self.check_result(result,
                          ('b46ebf6b6e7a33eb36c363cf1bf02d48',
                           '311a143087daeb030e865ffbd254e67d'), None)

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
            "creation": "01-01-1970",
            "data_value": "TEST_DATA_VALUE",
            "data_type": "TEST_DATA_TYPE",
            "data_desc": "TEST_DATA_DESCRIPTION",
            "last_change": "01-01-1970"
        }
        result = self.app.post(
            url,
            data=json.dumps(post_data),
            content_type="application/json",
            headers=headers)
        self.check_result(result,
                          ('0abac37d1a9c53be0e2eb46edf51e990',
                           '94439e3f4fdfe6db1eb77d748b6432e0'), None)

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
        self.check_result(result,
                          ('2894f608d7b319c609ea4a6d9ac68eff',
                           'cffd220dd6f3e76fee6129ec1ac37387'), 201)

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
        self.check_result(result, 'cf004012cf8b5bfd10cb415ecf03269e', 201)

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
        self.check_result(result,
                          ('7b4478a8cd7d14836b089ff531e27852',
                           '6a4376e47c877f672e47eac39e0f106e'), 201)

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
        self.check_result(result,
                          ('2f1aec377faae5831e79a734177d75dc',
                           '1fe788c3f2420c8655e5cf2e8155e32b'), 200)

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
        self.check_result(result,
                          ('028d974e20f53f67304289199f10a66d',
                           '61ac839061f508f995cb371009641151'), 200)

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
        self.check_result(result,
                          ('1c5e042722e1d4272332ea83c1d80af6',
                           '41e0a74c8a471c981bcb5809fdd041b2'), 201)

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
        self.check_result(result,
                          ('775c16e3e08b9f136698f52a85a24c58',
                           '39640ec912b6f4d69809e875adf9bfa7'), 200)

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
        self.check_result(result,
                          ('fbba576726bd4e2d095f2668ef3b9282',
                           'ac2771bff10d98720167fac7136ccdce'), 201)

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
        self.check_result(result,
                          ('775c16e3e08b9f136698f52a85a24c58',
                           '39640ec912b6f4d69809e875adf9bfa7'), 200)


if __name__ == '__main__':
    print("----------------------------------\n"
          "Starting unit tests ...\n"
          "----------------------------------\n")
    unittest.main(failfast=stop_at_fail)
    print("Tests completed")
