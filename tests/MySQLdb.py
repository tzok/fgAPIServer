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

import fgapiserver_queries
import user_apis_queries

#
# MySQLdb.py emulates the MySQL module returning configurable outputs
#            accordingly to pre-defined queries (see queries variable)
#

__author__ = "Riccardo Bruno"
__copyright__ = "2015"
__license__ = "Apache"
__version__ = "v0.0.2-30-g37540b8-37540b8-37"
__maintainer__ = "Riccardo Bruno"
__email__ = "riccardo.bruno@ct.infn.it"

queries = [
    {'category': 'empty',
     'statements': [
         {'query': None,
          'result': None}, ]}, ]

# Load tests queries
queries += fgapiserver_queries.queries
queries += user_apis_queries.queries


class cursor:

    position = 0
    cursor_results = None

    def __getitem__(self, i):
        return self.cursor_results[i]

    def __len__(self):
        return len(self.cursor_results)

    def rank_query(self, q1, q2):
        if q1 is None or q2 is None:
            return 0
        rank = 0
        ccnt = 0
        for c in q1:
            if ccnt < len(q2) and ord(c) == ord(q2[ccnt]):
                rank += 1
            ccnt += 1
        return rank

    def hilight_diff(self, q1, q2, show=None):
        if q1 is not None and q2 is not None:
            dcnt = 0
            scnt = 0
            ccnt = 0
            diff_report = ''
            for c in q1:
                if ccnt < len(q2):
                    if ord(c) == ord(q2[ccnt]):
                        if c == '\n':
                            diff_report += "%3d \\n ok\n" % ccnt
                        else:
                            diff_report += "%3d %2s ok\n" % (ccnt, c)
                        scnt += 1
                    else:
                        if c == '\n':
                            c_str = '\\n'
                        else:
                            c_str = "%s" % c
                        if q2[ccnt] == '\n':
                            q2_str = '\\n'
                        else:
                            q2_str = "%s" % q2[ccnt]
                        diff_report += ("%3d %2s ko - %2s\n"
                                        % (ccnt, c_str, q2_str))
                        dcnt += 1
                else:
                    dcnt += 1
                ccnt += 1
            if show is not None:
                print "Hilighting differences:"
                print diff_report
                print "%4d characters are matching" % scnt
                print "%4d characters are not matching" % dcnt
        return scnt, dcnt

    def execute(self, sql, sql_data=None):
        print "Executing: '%s'" % sql
        self.position = 0
        self.cursor_results = None
        rank_max = 0
        rank_query = ''
        query_found = False
        rank_index = 0
        for query_element in queries:
            query_index = 0
            category = query_element['category']
            for query in query_element['statements']:
                if query['query'] is not None:
                    rankq = self.rank_query(query['query'], sql)
                    if rank_max < rankq:
                        rank_max = rankq
                        rank_query = query['query']
                        rank_index = query['id']
                    if sql == query['query']:
                        self.cursor_results = query['result']
                        print "Test query found, category: '%s' at %s" %\
                              (category, query_index)
                        print "result: '%s'" % self.cursor_results
                        query_found = True
                        break
                query_index += 1
        if query_found is not True:
            print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
            print "!!! Test query not found !!!"
            print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
            print "Procesed queries %s" % query_index
            print "Closest query at index: '%s' is:" % rank_index
            print "'%s'" % rank_query
            print "whith score: %s" % rank_max
            self.hilight_diff(sql, rank_query, True)

    def fetchone(self):
        if self.cursor_results is None:
            return ''
        else:
            res = self.cursor_results[self.position]
            self.position += 1
            print "fetchone: %s" % res
            return res

    def close(self):
        print "cursor close"
        return None


class MySQLError(Exception):
    pass


class Error:
    pass


def connect(*args, **kwargs):
    db = MySQLdb()
    return db


class MySQLdb:

    Error = None

    def __init__(self, *args, **kwargs):
        Error = MySQLError()

    def cursor(self):
        cr = cursor()
        return cr

    def close(self):
        print "MySQLdb.close"
        return None

    def commit(self):
        print "MySQLdb.commit"
        return None
