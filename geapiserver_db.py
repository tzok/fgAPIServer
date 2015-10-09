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
  GridEngine API Server database
"""
import MySQLdb
import uuid
import os

"""
 Task sandboxing will be placed here
 Sandbox directories will be generated as UUID names generated during task creation
"""
iosandbbox_dir   = '/tmp'
geapiserverappid = '10000' # GridEngine sees API server as an application

"""
  geapiserver_db Class contain any call interacting with geapiserver database
"""
class geapiserver_db:

    db_host = 'localhost'
    db_port = 3306
    db_user = 'geapiserver'
    db_pass = 'geapiserver_password'
    db_name = 'geapiserver'

    err_flag = False
    err_msg  = ''
    message  = ''


    def __init__(self,db_host,db_port,db_user,db_pass,db_name):
        self.db_host = db_host
        self.db_port = db_port
        self.db_user = db_user
        self.db_pass = db_pass
        self.db_name = db_name
        self.test()

    def test(self):
        try:
            db = MySQLdb.connect(host=self.db_host
                              ,user=self.db_user
                              ,passwd=self.db_pass
                              ,db=self.db_name
                              ,port=self.db_port)
            # prepare a cursor object using cursor() method
            cursor = db.cursor()
            # execute SQL query using execute() method.
            cursor.execute("SELECT VERSION()")
            # Fetch a single row using fetchone() method.
            data = cursor.fetchone()
            # disconnect from server
            db.close()
            self.err_flag = False
            self.err_msg  = 'Database version : %s' % data[0]
        except:
            self.err_flag = True
            self.err_msg  = 'Unable to connect the database'

    """
      connect Connects to the geapiserver database
    """
    def connect(self):
        return MySQLdb.connect(host=self.db_host
                              ,user=self.db_user
                              ,passwd=self.db_pass
                              ,db=self.db_name
                              ,port=self.db_port)

    """
      getState returns the status and message of the last action on the DB
    """
    def getState(self):
        return (self.err_flag,self.err_msg)

    """
       getTaskRecord
    """
    def getTaskRecord(self,task_id):
        task_record = {}
        try:
            db=self.connect()
            cursor = db.cursor()
            # Task record
            sql=('select id\n'
                 '      ,status\n'
                 '      ,creation\n'
                 '      ,last_change\n'
                 '      ,app_id\n'
                 '      ,description\n'
                 '      ,status\n'
                 '      ,user\n'
                 'from task where id=%s;')
            sql_data=(task_id,)
            cursor.execute(sql,sql_data)
            task_dbrec=cursor.fetchone()
            task_dicrec={ 'id'          : task_dbrec[0]
                         ,'status'      : task_dbrec[1]
                         ,'creation'    : task_dbrec[2]
                         ,'last_change' : task_dbrec[3]
                         ,'app_id'      : task_dbrec[4]
                         ,'description' : task_dbrec[5]
                         ,'status'      : task_dbrec[6]
                         ,'user'        : task_dbrec[7]
                        }
            # Task arguments
            sql=('select argument\n'
                 'from task_arguments\n'
                 'where task_id=%s\n'
                 'order by arg_id asc;')
            sql_data=(task_id,)
            cursor.execute(sql,sql_data)
            task_args=()
            for arg in cursor:
                task_args+=(arg[0],)
            # Task input files
            sql=('select file\n'
                 'from task_input_file\n'
                 'where task_id=%s\n'
                 'order by file_id asc;')
            sql_data=(task_id,)
            cursor.execute(sql,sql_data)
            task_ifiles=()
            for ifile in cursor:
                task_ifiles+=(ifile[0],)
            # Task output files
            sql=('select file\n'
                 'from task_output_file\n'
                 'where task_id=%s\n'
                 'order by file_id asc;')
            sql_data=(task_id,)
            cursor.execute(sql,sql_data)
            task_ofiles=()
            for ofile in cursor:
                task_ofiles+=(ofile[0],)
            # Prepare output
            task_record= {
                 'id'          : task_dicrec['id']
                ,'status'      : task_dicrec['status']
                ,'creation'    : str(task_dicrec['creation'])
                ,'last_change' : str(task_dicrec['last_change'])
                ,'app_id'      : task_dicrec['app_id']
                ,'description' : task_dicrec['description']
                ,'status'      : task_dicrec['status']
                ,'user'        : task_dicrec['user']
                ,'arguments'   : task_args
                ,'input_files' : task_ifiles
                ,'output_files': task_ofiles
            }
            print task_record
        except MySQLdb.Error, e:
            db.rollback()
            self.err_flag = True
            self.err_msg  = "[ERROR] %d: %s\n" % (e.args[0], e.args[1])
        finally:
            cursor.close()
            db.close()
        return task_record

    """
      getTaskState - Return the status of a given Task
    """
    def getTaskStatus(self,task_id):
        return self.getTaskRecord(task_id).get('status',None)

    """
      getTaskInputFiles - Return information about InputFiles of a given Task
    """
    def getTaskInputFiles(self,task_id):
        task_ifiles=()
        try:
            db=self.connect()
            cursor = db.cursor()
            sql=('select file\n'
                 '      ,if(path is null,\'waiting\',\'ready\')\n'
                 'from task_input_file\n'
                 'where task_id = %s;')
            sql_data=(task_id)
            cursor.execute(sql,sql_data)
            for ifile in cursor:
                file_info = {
                    'name'  : ifile[0]
                   ,'status': ifile[1]
                }
                task_ifiles+=(file_info,)
        except MySQLdb.Error, e:
            db.rollback()
            self.err_flag = True
            self.err_msg  = "[ERROR] %d: %s\n" % (e.args[0], e.args[1])
        finally:
            cursor.close()
            db.close()
        return task_ifiles

    """
      getTaskOutputFiles - Return information about OutputFiles of a given Task
    """
    def getTaskOutputFiles(self,task_id):
        task_ifiles=()
        try:
            db=self.connect()
            cursor = db.cursor()
            sql=('select file\n'
                 '      ,if(path is null,\'waiting\',\'ready\')\n'
                 'from task_output_file\n'
                 'where task_id = %s;')
            sql_data=(task_id)
            cursor.execute(sql,sql_data)
            for ifile in cursor:
                file_info = {
                    'name'  : ifile[0]
                   ,'status': ifile[1]
                }
                task_ifiles+=(file_info,)
        except MySQLdb.Error, e:
            db.rollback()
            self.err_flag = True
            self.err_msg  = "[ERROR] %d: %s\n" % (e.args[0], e.args[1])
        finally:
            cursor.close()
            db.close()
        return task_ifiles

    """
      getTaskAppDetail - Return application details of a given Task
    """
    def getTaskAppDetail(self,task_id):
        task_record = self.getTaskRecord(task_id)
        app_detail = {}
        try:
            db=self.connect()
            cursor = db.cursor()
            sql=('select id\n'
                 '      ,name\n'
                 '      ,description\n'
                 '      ,creation\n'
                 '      ,enabled\n'
                 'from application\n'
                 'where id=%s;')
            sql_data=(str(task_record['app_id']))
            cursor.execute(sql,sql_data)
            app_record=cursor.fetchone()
            app_detail = {
                'id'          : app_record[0]
               ,'name'        : app_record[1]
               ,'description' : app_record[2]
               ,'creation'    : str(app_record[3])
               ,'enabled'     : app_record[4]
            }
            # Add now app parameters
            sql=('select pname\n'
                 '      ,pvalue\n'
                 'from application_parameter\n'
                 'where app_id=%s\n'
                 'order by param_id asc;')
            sql_data=(str(task_record['app_id']))
            cursor.execute(sql,sql_data)
            app_parameters=()
            for param in cursor:
                parameter = {
                     'param_name' : param[0]
                    ,'param_value': param[1]
                }
                app_parameters+=(parameter,)
            app_detail['parameters']=app_parameters
            # Get now ifnrastructures with their params
            infrastructures=()
        except MySQLdb.Error, e:
            db.rollback()
            self.err_flag = True
            self.err_msg  = "[ERROR] %d: %s\n" % (e.args[0], e.args[1])
        finally:
            cursor.close()
            db.close()
        return app_detail

    """
      getTaskInfo - Retrieve full information about given task_id
    """
    def getTaskInfo(self,task_id):
        task_record = self.getTaskRecord(task_id)
        task_app_details = self.getTaskAppDetail(task_id)
        task_info = task_record
        del task_info['app_id']
        task_info['application']=task_app_details
        return task_info

    """
      initTask initialize a task from a given application id
    """
    def initTask(self,app_id,description,user,arguments,input_files,output_files):
        task_id=-1
        # Create the Task IO Sandbox
        try:
            iosandbox = '%s/%s' % (iosandbbox_dir,str(uuid.uuid1()))
            os.makedirs(iosandbox)
        except:
            self.err_flag = True
            self.err_msg  = "Unable to create IO Sandbox '%s' for task_id: %s" % (iosandbox,task_id)
            return task_id
        # Insert new Task
        try:
            db=self.connect()
            cursor = db.cursor()
            sql=('insert into task (id\n'
                 '                 ,creation\n'
                 '                 ,last_change\n'
                 '                 ,app_id\n'
                 '                 ,description\n'
                 '                 ,status\n'
                 '                 ,user\n'
                 '                 ,iosandbox)\n'
                 'select if(max(id) is NULL,1,max(id)+1) -- new id\n'
                 '      ,now()                           -- creation date\n'
                 '      ,now()                           -- last change\n'
                 '      ,%s                              -- app_id\n'
                 '      ,%s                              -- description\n'
                 '      ,\'WAITING\'                     -- status WAITING\n'
                 '      ,%s                              -- user\n'
                 '      ,%s                              -- iosandbox\n'
                 'from task;\n'
                )
            sql_data = (app_id,description,user,iosandbox)
            cursor.execute(sql,sql_data)
            sql='select max(id) from task;'
            sql_data=''
            cursor.execute(sql)
            task_id = cursor.fetchone()[0]
            # Insert Task arguments
            if arguments != []:
                for arg in arguments:
                    sql=('insert into task_arguments (task_id\n'
                         '                           ,arg_id\n'
                         '                           ,argument)\n'
                         'select %s                                          -- task_id\n'
                         '      ,if(max(arg_id) is NULL,1,max(arg_id)+1)     -- arg_id\n'
                         '      ,%s                                          -- argument\n'
                         'from task_arguments\n'
                         'where task_id=%s'
                        )
                    sql_data=(task_id,arg,task_id)
                    cursor.execute(sql,sql_data)
            # Insert Task input_files
            if input_files != []:
                for inpfile in input_files:
                    sql=('insert into task_input_file (task_id\n'
                         '                            ,file_id\n'
                         '                            ,file)\n'
                         'select %s                                          -- task_id\n'
                         '      ,if(max(file_id) is NULL,1,max(file_id)+1)   -- file_id\n'
                         '      ,%s                                          -- file\n'
                         'from task_input_file\n'
                         'where task_id=%s'
                        )
                    sql_data=(task_id,inpfile,task_id)
                    cursor.execute(sql,sql_data)
            # Insert Task output_files
            print "output_files:"
            print output_files
            if output_files != []:
                for outfile in output_files:
                    sql=('insert into task_output_file (task_id\n'
                         '                             ,file_id\n'
                         '                             ,file)\n'
                         'select %s                                          -- task_id\n'
                         '      ,if(max(file_id) is NULL,1,max(file_id)+1)   -- file_id\n'
                         '      ,%s                                          -- file\n'
                         'from task_output_file\n'
                         'where task_id=%s'
                        )
                    sql_data=(task_id,outfile,task_id)
                    cursor.execute(sql,sql_data)
        except MySQLdb.Error, e:
            db.rollback()
            self.err_flag = True
            self.err_msg  = "[ERROR] %d: %s\n" % (e.args[0], e.args[1])
        finally:
            cursor.close()
            db.commit()
            db.close()
        return task_id

    """
      getTaskIOSandbox - Get the assigned IO Sandbox folder of the given task_id
    """
    def getTaskIOSandbox(self,task_id):
        iosandbox = None
        try:
            db=self.connect()
            cursor = db.cursor()
            sql='select iosandbox from task where id=%s;'
            sql_data=(task_id)
            cursor.execute(sql,sql_data)
            iosandbox = cursor.fetchone()[0]
        except MySQLdb.Error, e:
            db.rollback()
            self.err_flag = True
            self.err_msg  = "[ERROR] %d: %s\n" % (e.args[0], e.args[1])
        finally:
            cursor.close()
            db.close()
        return iosandbox

    """
      updateInputSandboxFile - Update input_sandbox_table with the fullpath of a given (task,filename)
    """
    def updateInputSandboxFile(self,task_id,filename,filepath):
        try:
            db=self.connect()
            cursor = db.cursor()
            sql=('update task_input_file\n'
                 'set path=%s\n'
                 'where task_id=%s\n'
                 '  and file=%s;')
            sql_data=(filepath,task_id,filename)
            cursor.execute(sql,sql_data)
        except MySQLdb.Error, e:
            db.rollback()
            self.err_flag = True
            self.err_msg  = "[ERROR] %d: %s\n" % (e.args[0], e.args[1])
        finally:
            cursor.close()
            db.commit()
            db.close()
        return

    """
      isInputSandboxReady - Return true if all input_sandbox files have been uploaded for a given (task_id)
                            True if all files have a file path registered or the task does not contain any
                            input file
    """
    def isInputSandboxReady(self,task_id):
        sandbox_ready = False
        try:
            db=self.connect()
            cursor = db.cursor()
            sql=('select sum(if(path is NULL,0,1))=count(*) or count(*)=0 sb_ready\n'
                 'from task_input_file\n'
                 'where task_id=%s;')
            sql_data=(task_id)
            cursor.execute(sql,sql_data)
            sandbox_ready = cursor.fetchone()[0]
        except MySQLdb.Error, e:
            db.rollback()
            self.err_flag = True
            self.err_msg  = "[ERROR] %d: %s\n" % (e.args[0], e.args[1])
        finally:
            cursor.close()
            db.close()
        return 1==int(sandbox_ready)

    """
      submitTaks - Trigger the GridEngine to submit the given task
                   This function takes care of all GridEngine needs to properly submit the applciation
    """
    def submitTaks(self,task_id):
        # Proceed only if task comes form a WAITING state
        task_record = getTaskRecord(task_id)
        task_status = task_record.get('status','')
        if task_status != 'WAITING':
            self.err_flag = True
            self.err_msg  = 'Wrong status (\'%s\') to ask submission for task_id: %s' % (task_status,task_id)
            return False
        # Prepare GridEngine required info (JSON file)
        """
        {
           "commonName": "helloworld@localhost test run",
           "application": 10000, -- Refers to the GridEngine APIServer registered app
           "identifier": "task_id: 1",
           "jobDescription": {
               "executable": "hostname",
               "output": "stdout.txt",
               "error": "stderr.txt"
               "arguments": "-f"
           },
           "infrastructure": {
               "resourceManagers": "fork://localhost"
           }
        }
        """
        GridEngineTaskDescription = {}
        GridEngineTaskDescription.update({'commonName' : '%s' % task_record.get('description','task_id: %s' % task_id)})
        GridEngineTaskDescription.update({'application': '%s' % geapiserverappid })
        GridEngineTaskDescription.update({'identifier': 'task_id: %s' % task_id })
        GridEgnineJobDescription = {}
        # Get application specific settings
        GridEngineTaskDescription.update({'jobDescription': GridEgnineJobDescription })
        # Get application specific infrastructure settings
        GridEngineInfrastructure = {}
        GridEngineTaskDescription.update({'jobDescription': GridEngineInfrastructure })
        # Switch task status and populate gequeue table accordingly
        return True