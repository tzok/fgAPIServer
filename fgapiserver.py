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
__author__     = "Riccardo Bruno"
__copyright__  = "2015"
__license__    = "Apache"
__version__    = "v0.0.1-5-g3a6b162-3a6b162-6"
__maintainer__ = "Riccardo Bruno"
__email__      = "riccardo.bruno@ct.infn.it"

"""
  GridEngine API Server engine
"""
from flask import Flask
from flask import request
from flask import Response
from flask import jsonify
from OpenSSL import SSL
from werkzeug import secure_filename
from fgapiserver_db import fgapiserver_db
from fgapiserver_cfg import fgapiserver_cfg
import os
import sys
import uuid
import time
import json
import ConfigParser

# setup path
fgapirundir=os.path.dirname(os.path.abspath(__file__))+'/'
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))

# fgapiserver configuration file
fgapiserver_config_file = fgapirundir+'fgapiserver.conf'

# Load configuration
fg_config = fgapiserver_cfg(fgapiserver_config_file)

# fgapiserver settings
fgapiver           =     fg_config.getConfValue('fgapiver')
fgapiserver_name   =     fg_config.getConfValue('fgapiserver_name')
fgapisrv_host      =     fg_config.getConfValue('fgapisrv_host')
fgapisrv_port      = int(fg_config.getConfValue('fgapisrv_port'))
fgapisrv_debug     =    (fg_config.getConfValue('fgapisrv_debug') == 'True')
fgapisrv_iosandbox =     fg_config.getConfValue('fgapisrv_iosandbox')
fgapisrv_geappid   = int(fg_config.getConfValue('fgapisrv_geappid'))
fgjson_indent      = int(fg_config.getConfValue('fgjson_indent'))
fgapisrv_key       =     fg_config.getConfValue('fgapisrv_key')
fgapisrv_crt       =     fg_config.getConfValue('fgapisrv_crt')

# fgapiserver database settings
fgapisrv_db_host =     fg_config.getConfValue('fgapisrv_db_host')
fgapisrv_db_port = int(fg_config.getConfValue('fgapisrv_db_port'))
fgapisrv_db_user =     fg_config.getConfValue('fgapisrv_db_user')
fgapisrv_db_pass =     fg_config.getConfValue('fgapisrv_db_pass')
fgapisrv_db_name =     fg_config.getConfValue('fgapisrv_db_name')

# setup Flask app
app = Flask(__name__)

##
## Routes as specified for APIServer at http://docs.csgfapis.apiary.io
##

#
# / path; used retrieve informative or service healty information
#
@app.route('/')
@app.route('/%s/' % fgapiver)
def index():
    versions = ({'id'    : fgapiver
                ,'_links': ({'rel' : 'self'
                            ,'href': fgapiver },)
                ,'media-types': ({'type':'application/json'})
                ,'status': 'prototype'
                ,'updated': '2015-10-19'
                },)
    index_response = {
        'versions' : versions
       ,'_links'   : ({ 'rel':'self'
                       ,'href': '/'},)
    }
    js = json.dumps(index_response,indent=fgjson_indent)
    resp = Response(js, status=200, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    return resp

##
## Task handlers
##

# tasks - used to view o create a new task
# GET  - View task info
# POST - Create a new task; it only prepares the task for execution
@app.route('/%s/tasks' % fgapiver,methods=['GET','POST'])
def tasks():
    page     = request.values.get('page')
    per_page = request.values.get('per_page')
    status   = request.values.get('status')
    user     = request.values.get('user')
    app_id   = request.values.get('app_id')
    task_state = 0
    if request.method == 'GET':
        # Show the whole task list
        # Connect database
        fgapisrv_db = fgapiserver_db(db_host=fgapisrv_db_host
                                    ,db_port=fgapisrv_db_port
                                    ,db_user=fgapisrv_db_user
                                    ,db_pass=fgapisrv_db_pass
                                    ,db_name=fgapisrv_db_name
                                    ,iosandbbox_dir=fgapisrv_iosandbox
                                    ,fgapiserverappid=fgapisrv_geappid)
        db_state=fgapisrv_db.getState()
        if db_state[0] != 0:
            # Couldn't contact database
            # Prepare for 404 not found
            task_state = 404
            task_response = {
                'message' : db_state[1]
            }
        else:
            # call to get tasks
            task_list = fgapisrv_db.getTaskList(user,app_id)
            db_state=fgapisrv_db.getState()
            if db_state[0] != 0:
                # DBError getting TaskList
                # Prepare for 402
                task_state = 402
                task_response = {
                    'message' : db_state[1]
                }
            else:
                # Prepare response
                task_response = []
                for task_id in task_list:
                    task_record = fgapisrv_db.getTaskRecord(task_id)
                    db_state=fgapisrv_db.getState()
                    if db_state[0] != 0:
                        # DBError getting TaskRecord
                        # Prepare for 403
                        task_state = 403
                        task_response = {
                            'message' : db_state[1]
                        }
                    else:
                        task_response += [{
                             'id'          : task_record['id']
                            ,'application' : task_record['application']
                            ,'description' : task_record['description']
                            ,'arguments'   : task_record['arguments']
                            ,'input_files' : task_record['input_files']
                            ,'output_files': task_record['output_files']
                            ,'status'      : task_record['status']
                            ,'user'        : task_record['user']
                            ,'date'        : str(task_record['creation'])
                            ,'last_change'        : str(task_record['last_change'])
                            ,'_links'      : [{
                                                 'rel' : 'self'
                                                ,'href': '/%s/tasks/%s' % (fgapiver,task_id)
                                              }
                                             ,{
                                                 'rel' : 'input'
                                                ,'href': '/%s/tasks/%s/input' % (fgapiver,task_id)
                                              }]
                        },]
                        task_state = 200
        js = json.dumps(task_response,indent=fgjson_indent)
        resp = Response(js, status=task_state, mimetype='application/json')
        resp.headers['Content-type'] = 'application/json'
        return resp
    elif request.method == 'POST':
        # Getting values
        params = request.get_json()
        app_id   = params.get('application','')
        app_desc = params.get('description','')
        app_args = params.get('arguments'  ,[])
        app_inpf = params.get('input_files',[])
        app_outf = params.get('output_files',[])
        # Connect database
        fgapisrv_db = fgapiserver_db(db_host=fgapisrv_db_host
                                    ,db_port=fgapisrv_db_port
                                    ,db_user=fgapisrv_db_user
                                    ,db_pass=fgapisrv_db_pass
                                    ,db_name=fgapisrv_db_name
                                    ,iosandbbox_dir=fgapisrv_iosandbox
                                    ,geapiserverappid=fgapisrv_geappid)
        db_state=fgapisrv_db.getState()
        if db_state[0] != 0:
            # Couldn't contact database
            # Prepare for 404 not found
            task_state = 404
            task_response = {
                'message' : db_state[1]
            }
        else:
            # Create task
            task_id = fgapisrv_db.initTask(app_id
                                          ,app_desc
                                          ,user
                                          ,app_args
                                          ,app_inpf
                                          ,app_outf)
            if task_id < 0:
                task_state = fgapisrv_db.getState()
                # Error initializing task
                # Prepare for 410 error
                task_state = 410
                task_response = {
                    'message' : task_state[1]
                }
            else:
                # Prepare response
                task_state = 200
                task_record = fgapisrv_db.getTaskRecord(task_id)
                task_response = {
                     'id'          : task_record['id']
                    ,'application' : task_record['application']
                    ,'description' : task_record['description']
                    ,'arguments'   : task_record['arguments']
                    ,'input_files' : task_record['input_files']
                    ,'output_files': task_record['output_files']
                    ,'status'      : task_record['status']
                    ,'user'        : task_record['user']
                    ,'date'        : str(task_record['last_change'])
                    ,'_links'      : [{
                                         'rel' : 'self'
                                        ,'href': '/%s/tasks/%s' % (fgapiver,task_id)
                                      }
                                     ,{
                                         'rel' : 'input'
                                        ,'href': '/%s/tasks/%s/input' % (fgapiver,task_id)
                                      }]
                }
        js = json.dumps(task_response,indent=fgjson_indent)
        resp = Response(js, status=task_state, mimetype='application/json')
        resp.headers['Content-type'] = 'application/json'
        if task_state == 200:
            resp.headers.add('Location','/v1.0/tasks/%s' % task_id)
            resp.headers.add('Link'
                            ,'</v1.0/tasks/%s/input>; rel="input", </v1.0/tasks/%s>; rel="self"'
                            %(task_id,task_id))
        return resp

# This is an informative call
# GET  - shows details
# POST - could reshape the request (Delete/Recreate)
@app.route('/%s/tasks/<task_id>' % fgapiver,methods=['GET','POST','DELETE','PATCH'])
def task_id(task_id=None):
    if request.method == 'GET':
        fgapisrv_db = fgapiserver_db(db_host=fgapisrv_db_host
                                    ,db_port=fgapisrv_db_port
                                    ,db_user=fgapisrv_db_user
                                    ,db_pass=fgapisrv_db_pass
                                    ,db_name=fgapisrv_db_name
                                    ,iosandbbox_dir=fgapisrv_iosandbox
                                    ,fgapiserverappid=fgapisrv_geappid)
        db_state=fgapisrv_db.getState()
        if db_state[0] != 0:
            # Couldn't contact database
            # Prepare for 404 not found
            task_status = 404
            task_response = {
                'message' : db_state[1]
            }
        elif not fgapisrv_db.taskExists(task_id):
            task_status = 404
            task_response = {
                'message' : "Unable to find task with id: %s" % task_id
            }
        else:
            # Get task details
            task_response=fgapisrv_db.getTaskRecord(task_id)
            db_state=fgapisrv_db.getState()
            if db_state[0] != 0:
                # Couldn't get TaskRecord
                # Prepare for 404 not found
                task_status = 404
                task_response = {
                    'message' : db_state[1]
                }
            else:
                task_status = 200
        # Display task details
        js = json.dumps(task_response,indent=fgjson_indent)
        resp = Response(js, status=task_status, mimetype='application/json')
        resp.headers['Content-type'] = 'application/json'
        return resp
    elif request.method == 'DELETE':
        fgapisrv_db = fgapiserver_db(db_host=fgapisrv_db_host
                                    ,db_port=fgapisrv_db_port
                                    ,db_user=fgapisrv_db_user
                                    ,db_pass=fgapisrv_db_pass
                                    ,db_name=fgapisrv_db_name
                                    ,iosandbbox_dir=fgapisrv_iosandbox
                                    ,fgapiserverappid=fgapisrv_geappid)
        db_state=fgapisrv_db.getState()
        if db_state[0] != 0:
            # Couldn't contact database
            # Prepare for 404 not found
            task_status = 404
            task_response = {
                'message' : db_state[1]
            }
        elif not fgapisrv_db.taskExists(task_id):
            task_status = 404
            task_response = {
                'message' : "Unable to find task with id: %s" % task_id
            }
        elif not fgapisrv_db.delete(task_id):
            task_status = 410
            task_response = {
                'message' : "Unable to delete task with id: %s" % task_id
            }
        else:
            task_status = 200
            task_response = {
                'message' : "Successfully removed task with id: %s" % task_id
            }
        js = json.dumps(task_response,indent=fgjson_indent)
        resp = Response(js, status=task_status, mimetype='application/json')
        resp.headers['Content-type'] = 'application/json'
        return resp
    elif request.method == 'PATCH':
        # PATCH on tasks accepts only changes on runtime_data
        # The input consists in a json having the form
        # { "runtime_data" : [ { "data_name":  "name"
        #                       ,"data_value": "value"
        #                       ,"data_desc": "description of the value"
        #                      }, ... ]
        # The insertion policy will be:
        #  1) data_name does not exists, a new record will be created in runtime_data table
        #  2) data_name exists the new value will be updated to the existing
        #
        params = request.get_json()
        runtime_data = params.get('runtime_data',[])
        fgapisrv_db = fgapiserver_db(db_host=fgapisrv_db_host
                                    ,db_port=fgapisrv_db_port
                                    ,db_user=fgapisrv_db_user
                                    ,db_pass=fgapisrv_db_pass
                                    ,db_name=fgapisrv_db_name
                                    ,iosandbbox_dir=fgapisrv_iosandbox
                                    ,fgapiserverappid=fgapisrv_geappid)
        db_state=fgapisrv_db.getState()
        if db_state[0] != 0:
            # Couldn't contact database
            # Prepare for 404 not found
            task_status = 404
            task_response = {
                'message' : db_state[1]
            }
        elif not fgapisrv_db.taskExists(task_id):
            task_status = 404
            task_response = {
                'message' : "Unable to find task with id: %s" % task_id
            }
        elif not fgapisrv_db.patch_task(task_id,runtime_data):
            task_status = 410
            task_response = {
                'message' : "Unable to delete task with id: %s" % task_id
            }
        else:
            task_status = 200
            task_response = {
                'message' : "Successfully patched task with id: %s" % task_id
            }
        js = json.dumps(task_response,indent=fgjson_indent)
        resp = Response(js, status=task_status, mimetype='application/json')
        resp.headers['Content-type'] = 'application/json'
        return resp
    elif request.method == 'POST':
        task_response = {
            'message' : 'Not supported yet'
        }
        js = json.dumps(task_response,indent=fgjson_indent)
        resp = Response(js, status=404, mimetype='application/json')
        resp.headers['Content-type'] = 'application/json'
        return resp

# This finalizes the task request allowing to submit the task
# GET  - shows input files
# POST - specify input files
@app.route('/%s/tasks/<task_id>/input' % fgapiver,methods=['GET','POST'])
def task_id_input(task_id=None):
    if request.method == 'GET':
        # Display task_input_file details
        fgapisrv_db = fgapiserver_db(db_host=fgapisrv_db_host
                                    ,db_port=fgapisrv_db_port
                                    ,db_user=fgapisrv_db_user
                                    ,db_pass=fgapisrv_db_pass
                                    ,db_name=fgapisrv_db_name
                                    ,iosandbbox_dir=fgapisrv_iosandbox
                                    ,geapiserverappid=fgapisrv_geappid)
        db_state=fgapisrv_db.getState()
        if db_state[0] != 0:
            # Couldn't contact database
            # Prepare for 404 not found
            task_status = 404
            task_response = {
                'message' : db_state[1]
            }
        elif not fgapisrv_db.taskExists(task_id):
            task_status = 404
            task_response = {
                'message' : "Unable to find task with id: %s" % task_id
            }
        else:
            task_status = 204
            task_response = {}
        js = json.dumps(task_response,indent=fgjson_indent)
        resp = Response(js, status=task_status, mimetype='application/json')
        resp.headers['Content-type'] = 'application/json'
        return resp
    elif request.method == 'POST':
        # First determine IO Sandbox location for this task
        fgapisrv_db = fgapiserver_db(db_host=fgapisrv_db_host
                                    ,db_port=fgapisrv_db_port
                                    ,db_user=fgapisrv_db_user
                                    ,db_pass=fgapisrv_db_pass
                                    ,db_name=fgapisrv_db_name
                                    ,iosandbbox_dir=fgapisrv_iosandbox
                                    ,fgapiserverappid=fgapisrv_geappid)
        db_state=fgapisrv_db.getState()
        if db_state[0] != 0:
            # Couldn't contact database
            # Prepare for 404 not found
            task_status = 404
            task_response = {
                'message' : db_state[1]
            }
        elif not fgapisrv_db.taskExists(task_id):
            task_status = 404
            task_response = {
                'message' : "Unable to find task with id: %s" % task_id
            }
        else:
            task_sandbox = fgapisrv_db.getTaskIOSandbox(task_id)
            if task_sandbox is None:
                task_status = 404
                task_response = {
                    'message' : 'Could not find IO Sandbox dir for task: %s' % task_id
                }
            else:
                # Now process files to upload
                uploaded_files = request.files.getlist('file[]')
                file_list = ()
                for f in uploaded_files:
                    filename = secure_filename(f.filename)
                    f.save(os.path.join(task_sandbox, filename))
                    fgapisrv_db.updateInputSandboxFile(task_id
                                                      ,filename
                                                      ,os.path.join(task_sandbox))
                    file_list+=(filename,)
                # Now get input_sandbox status
                if fgapisrv_db.isInputSandboxReady(task_id):
                    # The input_sandbox is completed; trigger the GE for this task
                    if fgapisrv_db.submitTask(task_id):
                        task_status = 200
                        task_response = {
                             'task'    : task_id
                            ,'files'   : file_list
                            ,'message' : 'uploaded'
                            ,'gestatus': 'triggered'
                        }
                    else:
                        task_status = 412
                        task_response = {
                            'message' : fgapisrv_db.getState()[1]
                        }
                else:
                    task_status = 200
                    task_response = {
                         'task'    : task_id
                        ,'files'   : file_list
                        ,'message' : 'uploaded'
                        ,'gestatus': 'waiting'
                    }
        js = json.dumps(task_response,indent=fgjson_indent)
        resp = Response(js, status=task_status, mimetype='application/json')
        resp.headers['Content-type'] = 'application/json'
        return resp

@app.route('/%s/file' % fgapiver,methods=['GET',])
def file():
    if request.method == 'GET':
        file_path = request.values.get('path')
        file_name = request.values.get('name')
    serve_file = None
    try:
        serve_file = open('%s/%s' % (file_path,file_name),'rb')
        serve_file_content = serve_file.read()
        resp = Response(serve_file_content, status=200)
        resp.headers['Content-type'] = 'application/octet-stream'
        resp.headers.add('Content-Disposition','attachment; filename="%s"' % file_name)
    except:
        task_response = {
            'message' : "Unable to get file: %s/%s" % (file_path,file_name)
        }
        js = json.dumps(task_response,indent=fgjson_indent)
        resp = Response(js, status=404)
        resp.headers['Content-type'] = 'application/json'
    finally:
        if serve_file is not None:
            serve_file.close()
    return resp

@app.after_request
def after_request(response):
  response.headers.add('Access-Control-Allow-Origin', '*')
  response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
  response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,PATCH')
  response.headers.add('Access-Control-Allow-Credentials', 'true')
  response.headers.add('Server',fgapiserver_name)
  return response

# The app starts here
if __name__ == "__main__":
    if len(fgapisrv_crt) > 0 and len(fgapisrv_key) > 0:
        context = SSL.Context(SSL.SSLv23_METHOD)
        context.use_privatekey_file(fgapisrv_key)
        context.use_certificate_file(fgapisrv_crt)
        app.run(host=fgapisrv_host, port=fgapisrv_port, ssl_context=context, debug=fgapisrv_debug)
    else:
        app.run(host=fgapisrv_host, port=fgapisrv_port,debug=fgapisrv_debug)

