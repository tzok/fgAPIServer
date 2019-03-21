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

from Crypto.Cipher import ARC4
import time
import base64

__author__ = 'Riccardo Bruno'
__copyright__ = '2019'
__license__ = 'Apache'
__version__ = 'v0.0.10'
__maintainer__ = 'Riccardo Bruno'
__email__ = 'riccardo.bruno@ct.infn.it'
__status__ = 'devel'
__update__ = '2019-03-21 16:25:52'

key = "0123456789ABCDEF"  # (!) Please use fgapiserver_secret value
username = "futuregateway"
password = "futuregateway"


# Encode
def token_encode(key, username, password):
    obj = ARC4.new(key)
    return base64.b64encode(
        obj.encrypt(
            "username=%s:password=%s:timestamp=%s" %
            (username, password, int(
                time.time()))))


# Decode
def token_decode(key, token):
    obj = ARC4.new(key)
    return obj.decrypt(base64.b64decode(token))


def token_info(key, token):
    tinfo = str(token_decode(key, token))
    tinfo_fields = tinfo.split(':')
    return \
        tinfo_fields[0].split("=")[1], \
        tinfo_fields[1].split("=")[1], \
        tinfo_fields[2].split("=")[1][:-1]


if __name__ == "__main__":
    token = token_encode(key, username, password)
    tinfo = token_decode(key, token)
    print("Token with key: '%s'; "
          "encoding: 'username:=%s:"
          "password=%s:"
          "timestamp=<issue_time>' is '%s'"
          % (key, username, password, token))
    print("Decoded token: '%s' -> '%s'" % (token, tinfo))
    username, password, timestamp = token_info(token)
    print("Token info: 'username=%s:password=%s:timestamp=%s'"
          % (username, password, timestamp))
