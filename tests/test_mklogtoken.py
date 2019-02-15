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
from mklogtoken import token_encode, token_decode, token_info

__author__ = "Riccardo Bruno"
__copyright__ = "2015"
__license__ = "Apache"
__version__ = "v0.0.2-30-g37540b8-37540b8-37"
__maintainer__ = "Riccardo Bruno"
__email__ = "riccardo.bruno@ct.infn.it"


class TestMkLogToken(unittest.TestCase):

    def setUp(self):
        pass

    def test_mklogtoken(self):
        key = "0123456789abcdef"
        username = "test"
        password = "test"
        token = token_encode(key, username, password)
        # Check decoded token
        decoded_token = token_decode(key, token).split(':')
        self.assertEqual(username, decoded_token[0].split('=')[1])
        self.assertEqual(password, decoded_token[1].split('=')[1])
        #  Check token_info
        tusrnm, tpaswd, tkntms = token_info(key, token)
        self.assertEqual(username, tusrnm)
        self.assertEqual(password, tpaswd)
        self.assertGreater(tkntms, 0, '')


if __name__ == '__main__':
    print "----------------------------------"
    print "Starting unit tests ..."
    print "----------------------------------"
    unittest.main(failfast=True)
