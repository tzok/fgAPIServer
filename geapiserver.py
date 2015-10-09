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
__version__    = "1.0"
__maintainer__ = "Riccardo Bruno"
__email__      = "riccardo.bruno@ct.infn.it"

"""
  GridEngine API Server engine
"""
from flask import Flask
from flask import request
from flask import Response
from flask import jsonify
from werkzeug import secure_filename
from geapiserver_db import geapiserver_db
import os
import sys
import uuid
import time
import json

# geapiserver settings
geapiver='v1.0'
geapiserver_name='GridEngine API Server %s' % geapiver
geapisrv_host='localhost'
geapisrv_port=7777

# geapiserver database settings
geapisrv_db_host = 'localhost'
geapisrv_db_port = 3306
geapisrv_db_user = 'geapiserver'
geapisrv_db_pass = 'geapiserver_password'
geapisrv_db_name = 'geapiserver'

# setup path and Flask app
base_path=os.path.dirname(__file__)
app = Flask(__name__)

##
## Routes as specified for APIServer at http://docs.csgfapis.apiary.io
##

#
# / path; used retrieve informative or service healty information
#
@app.route('/')
@app.route('/%s/' % geapiver)
def index():
    index_response = {
        'service' : 'GridEngine APIServer %s' % geapiver
    }
    js = json.dumps(index_response)
    resp = Response(js, status=200, mimetype='application/json')
    resp.headers['Content-type'] = 'application/json'
    resp.headers.add('Server',geapiserver_name)
    return resp

##
## Task handlers
##

# tasks - used to view o create a new task
# GET  - View task info
# POST - Create a new task; it only prepares the task for execution
@app.route('/%s/tasks' % geapiver,methods=['GET','POST'])
def task_create():
    page     = request.values.get('page')
    per_page = request.values.get('per_page')
    status   = request.values.get('status')
    user     = request.values.get('user')
    if request.method == 'GET':
        return 'task(GET)' 
    elif request.method == 'POST':
        # Getting values
        params = request.get_json()
        app_id   = params.get('application','')
        app_desc = params.get('description','')
        app_args = params.get('arguments'  ,[])
        app_inpf = params.get('input_files',[])
        app_outf = params.get('output_files',[])
        # Connect database
        geapisrv_db = geapiserver_db(db_host=geapisrv_db_host
                                    ,db_port=geapisrv_db_port
                                    ,db_user=geapisrv_db_user
                                    ,db_pass=geapisrv_db_pass
                                    ,db_name=geapisrv_db_name)
        db_state=geapisrv_db.getState()
        if db_state[0] != 0:
            # Couldn't contact database
            # Prepare for 404 not found
            task_response = {
                'message' : db_state[1]
            }
            js = json.dumps(task_response)
            resp = Response(js, status=404, mimetype='application/json')
            resp.headers['Content-type'] = 'application/json'
            resp.headers.add('Server',geapiserver_name)
            return resp
        # Create task
        task_id = geapisrv_db.initTask(app_id
                                      ,app_desc
                                      ,user
                                      ,app_args
                                      ,app_inpf
                                      ,app_outf)
        if task_id < 0:
            task_state = geapisrv_db.getState()
            # Couldn't contact database
            # Prepare for 410 error
            task_response = {
                'message' : task_state[1]
            }
            js = json.dumps(task_response)
            resp = Response(js, status=410, mimetype='application/json')
            resp.headers['Content-type'] = 'application/json'
            resp.headers.add('Server',geapiserver_name)
            return resp
        # Prepare response
        task_record = geapisrv_db.getTaskRecord(task_id)
        task_response = {
             'id'          : task_record['id']
            ,'application' : task_record['app_id']
            ,'description' : task_record['description']
            ,'arguments'   : task_record['arguments']
            ,'input_files' : task_record['input_files']
            ,'output_files': task_record['output_files']
            ,'status'      : task_record['status']
            ,'user'        : task_record['user']
            ,'date'        : str(task_record['last_change'])
            ,'_links'      : [{
                                 'rel' : 'self'
                                ,'href': '/%s/tasks/%s' % (geapiver,task_id)
                              }
                             ,{
                                 'rel' : 'input'
                                ,'href': '/%s/tasks/%s/input' % (geapiver,task_id)
                              }]
               }
        js = json.dumps(task_response)
        resp = Response(js, status=200, mimetype='application/json')
        resp.headers['Content-type'] = 'application/json'
        resp.headers.add('Location','/v1.0/tasks/%s' % task_id)
        resp.headers.add('Link'
                        ,'</v1.0/tasks/%s/input>; rel="input", </v1.0/tasks/%s>; rel="self"'
                        %(task_id,task_id))
        resp.headers.add('Server',geapiserver_name)
        return resp

# This is an informative call
# GET  - shows details
# POST - could reshape the request (Delete/Recreate)
@app.route('/%s/tasks/<task_id>' % geapiver,methods=['GET','POST'])
def task_id(task_id=None):
    if request.method == 'GET':
        geapisrv_db = geapiserver_db(db_host=geapisrv_db_host
                                    ,db_port=geapisrv_db_port
                                    ,db_user=geapisrv_db_user
                                    ,db_pass=geapisrv_db_pass
                                    ,db_name=geapisrv_db_name)
        db_state=geapisrv_db.getState()
        if db_state[0] != 0:
            # Couldn't contact database
            # Prepare for 404 not found
            task_response = {
                'message' : db_state[1]
            }
            js = json.dumps(task_response)
            resp = Response(js, status=404, mimetype='application/json')
            resp.headers['Content-type'] = 'application/json'
            resp.headers.add('Server',geapiserver_name)
            return resp
        # Display task details
        task_response=geapisrv_db.getTaskInfo(task_id)
        js = json.dumps(task_response)
        resp = Response(js, status=200, mimetype='application/json')
        resp.headers['Content-type'] = 'application/json'
        resp.headers.add('Server',geapiserver_name)
        return resp
    elif request.method == 'POST':
        return 'hello task_id %s' % task_id

# This finalizes the task request allowing to submit the task
# GET  - shows input files
# POST - specify input files
@app.route('/%s/tasks/<task_id>/input' % geapiver,methods=['GET','POST'])
def task_id_input(task_id=None):
    if request.method == 'GET':
        # Display task_input_file details
        geapisrv_db = geapiserver_db(db_host=geapisrv_db_host
                                    ,db_port=geapisrv_db_port
                                    ,db_user=geapisrv_db_user
                                    ,db_pass=geapisrv_db_pass
                                    ,db_name=geapisrv_db_name)
        db_state=geapisrv_db.getState()
        if db_state[0] != 0:
            # Couldn't contact database
            # Prepare for 404 not found
            task_response = {
                'message' : db_state[1]
            }
            js = json.dumps(task_response)
            resp = Response(js, status=404, mimetype='application/json')
            resp.headers['Content-type'] = 'application/json'
            resp.headers.add('Server',geapiserver_name)
            return resp
        task_response = {
             'task'        : task_id
            ,'input_files' : geapisrv_db.getTaskInputFiles(task_id)
        }
        js = json.dumps(task_response)
        resp = Response(js, status=200, mimetype='application/json')
        resp.headers['Content-type'] = 'application/json'
        resp.headers.add('Server',geapiserver_name)
        return resp
    elif request.method == 'POST':
        # First determin IO Sandbox location for this task
        geapisrv_db = geapiserver_db(db_host=geapisrv_db_host
                                    ,db_port=geapisrv_db_port
                                    ,db_user=geapisrv_db_user
                                    ,db_pass=geapisrv_db_pass
                                    ,db_name=geapisrv_db_name)
        db_state=geapisrv_db.getState()
        if db_state[0] != 0:
            # Couldn't contact database
            # Prepare for 404 not found
            task_response = {
                'message' : db_state[1]
            }
            js = json.dumps(task_response)
            resp = Response(js, status=404, mimetype='application/json')
            resp.headers['Content-type'] = 'application/json'
            resp.headers.add('Server',geapiserver_name)
            return resp
        task_sandbox = geapisrv_db.getTaskIOSandbox(task_id)
        if task_sandbox is None:
            task_response = {
                'message' : 'Could not find IO Sandbox dir for task: %s' % task_id
            }
            js = json.dumps(task_response)
            resp = Response(js, status=404, mimetype='application/json')
            resp.headers['Content-type'] = 'application/json'
            resp.headers.add('Server',geapiserver_name)
            return resp
        # Now process files to upload
        uploaded_files = request.files.getlist('file[]')
        file_list = ()
        for f in uploaded_files:
            filename = secure_filename(f.filename)
            f.save(os.path.join(task_sandbox, filename))
            geapisrv_db.updateInputSandboxFile(task_id
                                              ,filename
                                              ,os.path.join(task_sandbox))
            file_list+=(filename,)
        # Now get input_sandbox status
        if geapisrv_db.isInputSandboxReady(task_id):
            # The input_sandbox is completed; trigger the GE for this task
            if geapisrv_db.submitTaks(task_id):
                task_response = {
                     'task'    : task_id
                    ,'files'   : file_list
                    ,'message' : 'uploaded'
                    ,'gestatus': 'triggered'
                }
                js = json.dumps(task_response)
                resp = Response(js, status=200, mimetype='application/json')
                resp.headers['Content-type'] = 'application/json'
                resp.headers.add('Server',geapiserver_name)
                return resp
            else:
                task_response = {
                    'message' : geapisrv_db.getState()[1]
                }
                js = json.dumps(task_response)
                resp = Response(js, status=412, mimetype='application/json')
                resp.headers['Content-type'] = 'application/json'
                resp.headers.add('Server',geapiserver_name)
                return resp
        else:
            geapisrv_db.submitTaks(task_id)
            task_response = {
                 'task'    : task_id
                ,'files'   : file_list
                ,'message' : 'uploaded'
                ,'gestatus': 'waiting'
            }
            js = json.dumps(task_response)
            resp = Response(js, status=200, mimetype='application/json')
            resp.headers['Content-type'] = 'application/json'
            resp.headers.add('Server',geapiserver_name)
            return resp

#@app.route("/terminate",methods=['GET','POST'])
#def terminate():
#	if request.method == 'GET':
#		print "Unhandled method GET"
#		return None
#	elif request.method == 'POST':
#		event_id      = request.values.get('event_id')
#		event_endType = request.values.get('event_endType')
#		print "Terminating event_id:%s - event_endType:%s" % (event_id,event_endType)
#		db.terminateAction(event_id,event_endType)
#		return render_template('terminate.html',event_id=event_id)
	
# The app starts here
if __name__ == "__main__":
    app.debug = True
    app.run(host=geapisrv_host, port=geapisrv_port)

