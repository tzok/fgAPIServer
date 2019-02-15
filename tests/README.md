# Tests
This section contains a suite of tests able to check the consistency of the FutureGateway APIServer code (fgAPIServer).
To properly execute tests, some environment variables and/or configuration file changes have to be done.<br/>
Configurations are normally taken from file: `fgapiserver.conf`, however, its parameters can be overridden, using environment variables. The name of these variables have to match the configuration file parameter name, all in upper case.
The following instructions explain how to configure the different tests.

##### PYTHONPATH
The `PYTHON_PATH` environment variable must be set properly and test executed as follows:
```sh
export PYTHONPATH=$PYTHONPATH:..:.
```
This setting allows to override the MySQLdb module and tests will use testing SQL queries instead to connect a real database.

##### Test control settings
Test execution can be controlled by environment variables as listed below:
|Environment variable|Description|
|---|---|
|**FGTESTS_STOPATFAIL**| If enabled, test execution stops as soon as the first error occurs, use: `export FGTESTS_STOPATFAIL=1` to enable this feature|

#### Test configurations
Following configurations are valid for tests:

| Test case |Description|Execution|
|-----------|-----------|---------|
|Log tokens|Baseline authentication methods|`python -m unittest test_mklogtoken`|
|Configuration|Configuration settings|`test_fgapiserverconfig`|
|Core APIs|Core API functionalities on Infrastructures/Applications/Tasks management|`test_fgapiserver`|

##### Parameters
```
fgapisrv_notoken    = True
fgapisrv_notokenusr = test
```

Following configurations are valid for tests:

| Test case |Description|Execution|
|-----------|-----------|---------|
|User APIs|Users groups and role management APIs|`python -m unittest test_users_apis`|

```
fgapisrv_notoken    = False
fgapisrv_lnkptvflag = False
```

## MySQLdb
Test script makes use of a custom `MySQLdb` class where each SQL statement is executed by the `fgapiserverdb.py` file
 is hardcoded. Each test suite has its own list of statements stored in a dedicated python code file having the name
 `<test_suite_name>_queries.py`.
The code has to define internnaly a vector variable named: `fgapiserver_queries`, a vector of maps having the structure:
```python
{'id': <progressive query number>,
 'query': <SQL statement as it figures in the code (including %s)>,
 'result': <The SQL statement results> }, 
 ```
 Queries results are `[]` for insert and update statements, or having the following structure:
 ```
 [[col1_record1, col2_record1, ..., coln_recordn],...
  [col1_record2, col2_record2, ..., coln_record2],...
  ...
  [col1_recordm, col2_recordm, ..., coln_recordm],...
 ```
 At bottom of the queries vector, a further variable assignment is used to associate the queries to the test suite, whith:
```python
 queries = [
    {'category': <test_suite>,
     'statements': <vector of queries>]
  ```
  
 The test suite queries are imported by the `MySQLdb.py` at the top of the file and then included with several 
 variable assignment statements like: 
```queries += <test_suite_name>_queries.queries``` 

## Available tests
Below details about the tests available:

### test_mklogtoken.py
This script executes a simple test on mklogtoken.py code used by the baseline Authentication and Authorization.
It starts to encrypt username/password and timestamp and retrieve back this information with decrypting method.

### test_fgapiserverconfig
This script checks the functionalities offered by the configuration settings of the API server.

### test_fgapiserver.py
This test script makes use of unittests and its code is splitted in two separated sections. 
 A firt part consists of unit tests on `fgapiserver.py` code; the second part contains functional tests on developed 
 Flask endpoints. In the functional tests; each returned JSON is compared through its MD5Sum value with the
 `assertEqual()` method. The MD5Sum value to compare is extracted during the test case development and then hardcoded
  inside the `assertEqual()` method.

### test_fgapiserverconfig.py
This test script makes use of unittests to perform tests on top of the FGApiServerConfig object used to store 
 fgAPIServer configuration options.

### test_user_apis.py
This test controls fgAPIServer APIs dedicated to the user management, using the baseline authentication method.
 For this reason it requires a specific configuration setting to work and a dedicated test case has been built to
  check this condition.

## Travis
Travis file `.travis` contain an example of test suite execution.