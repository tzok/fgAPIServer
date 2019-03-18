#!/bin/bash
#
# releasing - script that updates release values on python code files
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
  pycodestyle *.py &&\
  pycodestyle tests/*.py
}

test_suite() {
  NUM_TESTS=${#TEST_SUITE[@]}
  if [ $((NUM_TESTS)) -ne 0 ]; then
    RES=0
    for test in ${TEST_SUITE[@]}; do
      python -m unittest -f ${test} || RES=1
      [ $RES -ne 0 ] &&\
        echo "Error on test: '$test'" &&\
        break
    done
  fi
  return $RES
}

# Unittests
unit_tests() {
  RES=1
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
  return $RES
}

# Releasing
echo "Starting releasing ..." &&\
check_style &&\
unit_tests &&\
set_code_headers &&
echo "Done"