#!/bin/bash
#
# releasing.sh - script to check codestyle, perform unit tests and update release values on python sources
#
# Author: Riccardo Bruno <riccardo.bruno@ct.infn.it>
#

AUTHOR="Riccardo Bruno"
COPYRIGHT=$(date +"%Y")
LICENSE=Apache
VERSION=v0.0.10
MAINTANIER=$AUTHOR
EMAIL=riccardo.bruno@ct.infn.it
STATUS=devel
UPDATE=$(date +"%Y-%m-%d %H:%M:%S")
VENV2=venv2
VENV3=venv3
PYTHON2=python2
PYTHON3=python3

# Source code header generator
set_code_headers() {
  TMP=$(mktemp)
  cat >$TMP <<EOF
__author__ = '${AUTHOR}'
__copyright__ = '${COPYRIGHT}'
__license__ = '${LICENSE}'
__version__ = '${VERSION}'
__maintainer__ = '${MAINTANIER}'
__email__ = '${EMAIL}'
__status__ = '${STATUS}'
__update__ = '${UPDATE}'
EOF
  for pyfile in $(/bin/ls -1 *.py *.wsgi tests/*.py); do
      echo "Releasing file: '$pyfile'"
      while read rel_line; do
          rel_item=$(echo $rel_line | awk -F'=' '{ print $1 }' | xargs echo)
          echo "    Processing line item: '$rel_item'"
          CMD=$(echo "sed -i '' s/^${rel_item}.*/\"$rel_line\"/ $pyfile")
          eval $CMD
      done < $TMP
  done
  rm -f $TMP
}

# Call checkstyle
check_style() {
  pycodestyle --ignore=E402 *.py &&\
  pycodestyle tests/*.py
}

# Execute a given unittest suite of scripts specified in array variable: TEST_SUITE
test_suite() {
  NUM_TESTS=${#TEST_SUITE[@]}
  if [ $((NUM_TESTS)) -ne 0 ]; then
    RES=0
    for test in ${TEST_SUITE[@]}; do
      python -m unittest -f ${test} || RES=1
      [ $RES -ne 0 ] &&\
        echo "Error on test: '$test'" &&\
        cd - &&\
        break
    done
  fi
  return $RES
}

# Configure and execute unit tests suites
unit_tests() {
  cd tests
  export PYTHONPATH=$PYTHONPATH:..:.
  export FGTESTS_STOPATFAIL=1
  # Different tests need different configurations
  export FGAPISRV_NOTOKEN=True
  export FGAPISRV_NOTOKENUSR=test
  TEST_SUITE=(\
    test_mklogtoken
    test_fgapiserverconfig
    test_fgapiserver
  )
  test_suite || return 1
  export FGAPISRV_NOTOKEN=False
  export FGAPISRV_LNKPTVFLAG=False
  TEST_SUITE=(\
    test_auth
    test_users_apis
  )
  test_suite || return 1
  cd -
  return 0
}

# Prepare test environment for Python v2
venv2() {
  echo "Preparing virtualenv for Python2"
  $PYTHON2 -m virtualenv $VENV2 &&\
  source ./$VENV2/bin/activate &&\
  pip install -r requirements.txt &&\
  pip install pycodestyle
}

# Perform tests for Python v2
tests_py2() {
  echo "Testing for Python v2" &&\
  unit_tests
}

# Prepare test environment for Python v3
venv3() {
  echo "Preparing virtualenv for Python3"
  $PYTHON3 -m venv $VENV3 &&\
  source ./$VENV3/bin/activate &&\
  pip install -r requirements.txt &&\
  pip install pycodestyle
}

# Perform tests for Python v3
tests_py3() {
  echo "Testing for Python v3" &&\
  unit_tests
}


# Setup Virtual environment and start check style and unittests
check_style_and_tests() {

  # Check existing virtual environments
  [ "$VIRTUAL_ENV" != "" ] &&\
      echo "An active virtual environment is present at: '$VIRTUAL_ENV'" &&\
      echo "Call 'deactivate' command before to run this script" &&\
      return 1

  RES=0
  PYTHON_2=$(which $PYTHON2)
  [ "$PYTHON_2" = "" ] &&\
    echo "which command could not determine python2; trying with 'python'" &&\
    PYTHON_2=$(python --version 2>&1 | awk '{ print substr($2,1,1) }')
  [ "$PYTHON_2" = "2" ] &&\
    echo "python2 is python" &&\
    PYTHON2=python
  if [ "$PYTHON_2" != "" ]; then
    venv2 &&\
    check_style &&\
    tests_py2 &&\
    PY2_DONE=1 ||\
    PY2_DONE=0
  else
    echo "No python 2 found, skipping tests for this version"
  fi
  [ $((PY2_DONE)) -eq 0 ] &&\
    echo "Releasing chain for python2 failed" &&\
    return 1

  PYTHON_3=$(which $PYTHON3)
  [ "$PYTHON_3" = "" ] &&\
    echo "which command could not determine python3; trying with 'python'" &&\
    PYTHON_3=$(python --version 2>&1 | awk '{ print substr($2,1,1) }')
  [ "$PYTHON_3" = "3" ] &&\
    echo "python3 is python" &&\
    PYTHON3=python
  if [ "$PYTHON_3" != "" ]; then
    venv3 &&\
    check_style &&\
    tests_py3 &&\
    PY3_DONE=1 ||\
    PY3_DONE=0 
  else
    echo "No python 3 found, skipping tests for this version"
  fi
  [ $((PY3_DONE)) -eq 0 ] &&\
    echo "Releasing chain for python3 failed" &&\
    return 1

  # No python found at all
  [ $((PY2_DONE)) -eq 0 -a\
    $((PY3_DONE)) -eq 0 ] &&\
    echo "Neither python2 nor python3 found" &&\
    return 1 
  
  return 0
}

#
# Releasing
#
echo "Starting releasing fgAPIServer ..." &&\
check_style_and_tests &&\
set_code_headers &&\
echo "Done" ||\
echo "Failed"
