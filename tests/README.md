# Tests
This section contains test scripts.
In order to test fgapiserver; the `PYTHON_PATH` environment variable must be set properly and test executed as follows:
```sh
export PYTHONPATH=$PYTHONPATH:..:.
./test_fgapiserver.py
```
Another mandatory configuration is related to the fgapiserver.conf which settings are depending from the test suite to execute as explained below:

**fgapiserver**
It tests basic fgAPIServer functionalities and does not need authentication at all
```
fgapisrv_notoken    = True
fgapisrv_notokenusr = test
```

**user_apis**
This test suite has been developed to test user specific APIs and it needs to enable baseline authentication
```
fgapisrv_notoken    = False
fgapisrv_lnkptvflag = False
```

## MySQLdb
Test script makes use of a custom `MySQLdb` class where each SQL statement executed by the `fgapiserverdb.py` file is hardcoded.
Each test suite has its own list of statements stored in a unique vector having the form:

The list of supported statements is included in a python vector of maps called: `queries`.
This vector of maps has the following structure:

```python
queries = [
    {'category': '<test suite>',
     'statements': [
         {'query': '<query statment as in fgapiserverdb.py>',
          'result': '<query result as MySQLdb cursor expects>}, ]}, ]
```
MySQLdb does not take in consideration query input values as they are defined in `sql_data` variable. Query results are then hardcoded inside the `result` field, to best control tests executions.
Each test suite inlcudes their own statements, importing its queries in MySQLdb code as reported below:

```python
# Load tests queries
queries += <test_suite_queries>
...
```

## test_fgapiserver.py
This test script makes use of unittests and its code is splitted in two separated sections. A firt part consists of unit tests on `fgapiserver.py` code; the second part contains functional tests on developed Flask endpoints.
In the functional tests; each returned JSON is compared through its MD5Sum value with the `assertEqual()` method. The MD5Sum value to compare is extracted during the test case development and then hardcoded inside the `assertEqual()` method.

## test_mklogtoken.py
This script executes a simple test on mklogtoken.py code used by the baseline Authentication and Authorization.
It starts to encrypt username/password and timestamp and retrieve back this information with decrypting method.

## test_user_apis.py
This test controls fgAPIServer APIs dedicated to the user management, using the baseline authentication method. For this reason it requires a specific configuration setting to work and a dedicated test case has been built to check this condition.
