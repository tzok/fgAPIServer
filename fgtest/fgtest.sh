#!/bin/bash
#
# fgtest.sh
#
FG_ENDPOINT=http://localhost:8888/v1.0
FG_TEST_TOKEN="TEST_TOKEN"
FG_HEAD_AUTH="-H \"Authorization: Bearer $FG_TEST_TOKEN\""
FG_HEAD_JSON="-H \"Content-type: application/json\""

PTV_ENDPOINT=http://localhost:8889
PTV_USER=tokenver_user
PTV_PASS=tokenver_pass

FGTEST_USR=fgtest_test
FGTEST_PWD=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 8 | head -n 1)
FGTEST_UPW=.$FGTEST_USR.passwd

REPORT_HOMEDIR=www
REPORT_HOME=fgtest
REPORT_INDEX=index.html

# Initialize all fgtest resources
fgtest_init() {
    FGTEST_OUT=$(mktemp)
    FGTEST_ERR=$(mktemp)
    echo "Generating test index page: $REPORT_HOMEDIR/$REPORT_INDEX" 
    cat >$REPORT_HOMEDIR/$REPORT_INDEX <<EOF
<html>
<title>FutureGateway test report</title>
<head>
  <link href="css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
<script src="js/jquery.min.js"></script>
<script src="js/bootstrap.min.js"></script>
<div class="container theme-showcase" role="main">
<div class="jumbotron">
<h1>FutureGateway test report</h1>
<p>This is the main page for tests executed on top of a baseline FutureGateway installation</p>
</div>
<table class="table table-bordered">
<thead>
<tr><th>Test</th><th>Status</th><th>Description</th></tr>
</thead>
<!-- Test list -->
</table>
<div class="page-header"><h1>Notes</h1></div>
<div class="well">
<p>This test can only operate on the FutureGateway baseline installations</p>
</div>
</div>
</body>
</html>
EOF
}

# Verify and create the fgtest user
# This is a pre-requisite and no report is foreseen for this test
fgtest_user() {
    TEST_PKG="Creating SSH test environment"

    CHK_FGTEST_USR=$(cat /etc/passwd | grep $FGTEST_USR)
    if [ "$CHK_FGTEST_USR" == "" ]; then
        echo "FutureGateway test user does not exists"
        adduser --disabled-password --gecos "" $FGTEST_USR
        echo "$FGTEST_USR:$FGTEST_PWD" | chpasswd
        echo "Test user $FGTEST_USR has been created"
        echo "SSH keyscanning"
        ssh-keyscan localhost
        echo "Test user password is: $FGTEST_PWD"
        echo $FGTEST_PWD > $FGTEST_UPW
    else
        echo "FutureGateway test user exists"
    fi
    CHK_FGTEST_USR=$(cat /etc/ssh/sshd_config | grep $FGTEST_USR)
    if [ "$CHK_FGTEST_USR" == "" ]; then
        echo "Adding ssh password authentication for the user: '"$FGTEST_USR"'"
        cat >> /etc/ssh/sshd_config <<EOF
# FutureGateway test user ${FGTEST_USR} (begin)
Match User ${FGTEST_USR}
PasswordAuthentication yes
# FutureGateway test user ${FGTEST_USR} (end)
EOF
        echo "Restarting ssh"
        /etc/init.d/ssh restart
    else
        echo "Test user already setup in ssh config"
    fi
    PUBKEY=$(cat $HOME/.ssh/id_rsa.pub)
    su - $FGTEST_USR -c "mkdir -p .ssh && touch .ssh/authorized_keys"
    su - $FGTEST_USR -c "cat .ssh/authorized_keys | grep \"$PUBKEY\" || echo \"$PUBKEY\" > /home/$FGTEST_USR/.ssh/authorized_keys"
    # Check connection
    CHK_FGTEST_USR=$(sshpass -p "$(cat $FGTEST_UPW)" ssh $FGTEST_USR@localhost whoami)
    if [ "$CHK_FGTEST_USR" != "$FGTEST_USR" ]; then
      echo "SSH connection test to $FGTEST_USR@localhost failed"
      return 1
    fi
    echo "SSH connection test to $FGTEST_USR@localhost passed"
    return 0
}

# PTV and Tosca simulator (needed for test
fgtest_ptv() {
    TEST_PKG="PTV service"
    TEST_TITLE="PTV presence"
    TEST_SHDESC="ptv_home"
    TEST_DESC="\
This test verifies that baseline PTV service is up and running calling \
<span class=\"badge\">/get-token</span> endpoint using <b>GET</b> method"
    TEST_APICALL="(GET) /get-token"
    TEST_CMD="curl -w \"\n%{http_code}\" -u '"$PTV_USER":"$PTV_PASS"' $PTV_ENDPOINT/get-token"
    echo "Executing: '"$TEST_CMD"'"
    eval "$TEST_CMD" >$FGTEST_OUT 2>$FGTEST_ERR
    TEST_HTTPRETCODE=$(cat $FGTEST_OUT | tail -n 1)
    sed -i '$ d' $FGTEST_OUT
    TEST_RES=$?
    TEST_CHK=$(cat $FGTEST_OUT | jq .error | xargs echo)
    echo "$TEST_CHK"
    fgtest_report
    if [ "$TEST_CHK" = "Unhandled method: 'GET'" ]; then
        echo "PTV service replied successfully"
    else
        echo "PTV service seems to be down"
        return 1
    fi
    return 0
}

# Test FutureGateway presence
fgtest_fg() {
    TEST_PKG="FutureGateway endpoint"
    TEST_TITLE="FG endpoint"
    TEST_SHDESC="fg_endpoint"
    TEST_DESC="\
This test verifies that baseline FutureGateway endpoint is up and running calling \
<span class=\"badge\">/</span> endpoint and using <b>GET</b> method"
    TEST_APICALL="(GET) /"
    TEST_CMD="curl -w \"\n%{http_code}\" -f $FG_ENDPOINT/"
    echo "Executing: '"$TEST_CMD"'"
    eval "$TEST_CMD" >$FGTEST_OUT 2>$FGTEST_ERR
    TEST_RES=$?
    TEST_HTTPRETCODE=$(cat $FGTEST_OUT | tail -n 1)
    sed -i '$ d' $FGTEST_OUT
    fgtest_report
    if [ $TEST_RES -eq 0 ]; then
        echo "Test: $TEST_PKG executed successfully"
    else
        echo "Test: $TEST_PKG failed to execute"
        return 1
    fi
    return 0
}

# Setup the SSH infrastructure using the fgtest user
fgtest_newinfra() {
    TEST_PKG="Create infrastructure"
    TEST_TITLE="Infrastructure create"
    TEST_SHDESC="infra_create"
    TEST_DESC="\
This test create a new infrastructure calling \
<span class=\"badge\">/infrastructures</span> endpoint and using <b>POST</b> method"
    TEST_APICALL="(POST) /infrastructures"
    NEW_INFRA_JSON=$(mktemp)
    cat >$NEW_INFRA_JSON <<EOF
{ "name": "SSH Test infrastructure",
  "parameters": [ { "name": "jobservice", 
                    "value": "ssh://localhost" },
                  { "name": "username",
                    "value": "${FGTEST_USR}" },
                  { "name": "password",
                    "value": "${FGTEST_PAS}" } ],
  "description": "SSH Test infrastructure for fgtest",
  "enabled": true,
  "virtual": false }
EOF
    FG_HEADERS=$FG_HEAD_AUTH" "$FG_HEAD_JSON
    TEST_JSON_DATA=$(cat $NEW_INFRA_JSON)
    TEST_CMD="curl -w \"\n%{http_code}\" -f $FG_HEADERS -X POST -d '"$TEST_JSON_DATA"' $FG_ENDPOINT/infrastructures"
    echo "Executing: '"$TEST_CMD"'"
    eval "$TEST_CMD" >$FGTEST_OUT 2>$FGTEST_ERR
    TEST_RES=$?
    TEST_HTTPRETCODE=$(cat $FGTEST_OUT | tail -n 1)
    sed -i '$ d' $FGTEST_OUT
    rm -f $NEW_INFRA_JSON
    TEST_INFRA_ID=$(cat $FGTEST_OUT | jq .id | xargs echo)
    fgtest_report
    if [ $TEST_RES -eq 0 ]; then
        echo "Test: $TEST_PKG executed successfully"
    else
        echo "Test: $TEST_PKG failed to execute"
        return 1
    fi
    return 0
}

# View all infrastructures
fgtest_viewinfras() {
    TEST_PKG="View infrastructures"
    TEST_TITLE="Infrastructure view all"
    TEST_SHDESC="infra_viewall"
    TEST_DESC="\
This test uses <span class=\"badge\">/infrastructures</span> API call to view \
all defined infrastructures using <b>GET</b> method"
    TEST_APICALL="(GET) /infrastructures"
    FG_HEADERS=$FG_HEAD_AUTH
    TEST_CMD="curl -w \"\n%{http_code}\" -f $FG_HEADERS $FG_ENDPOINT/infrastructures"
    echo "Executing: '"$TEST_CMD"'"
    eval "$TEST_CMD" >$FGTEST_OUT 2>$FGTEST_ERR
    TEST_RES=$?
    TEST_HTTPRETCODE=$(cat $FGTEST_OUT | tail -n 1)
    sed -i '$ d' $FGTEST_OUT
    fgtest_report
    if [ $TEST_RES -eq 0 ]; then
        echo "Test: $TEST_PKG executed successfully"
    else
        echo "Test: $TEST_PKG failed to execute"
        return 1
    fi
    return 0
}

# View last inserted infrastructure
fgtest_viewinfra() {
    TEST_PKG="View infrastructure"
    TEST_TITLE="Infrastructure view"
    TEST_SHDESC="infra_view"
    TEST_DESC="\
This test uses <span class=\"badge\">/infrastructures</span> API call to view the last \
inserted  infrastructure having id: '${TEST_INFRA_ID}' and using <b>GET</b> method"
    TEST_APICALL="(GET) /infrastructures/$TEST_INFRA_ID"
    FG_HEADERS=$FG_HEAD_AUTH
    TEST_CMD="curl -w \"\n%{http_code}\" -f $FG_HEADERS $FG_ENDPOINT/infrastructures/$TEST_INFRA_ID"
    echo "Executing: '"$TEST_CMD"'"
    eval "$TEST_CMD" >$FGTEST_OUT 2>$FGTEST_ERR
    TEST_RES=$?
    TEST_HTTPRETCODE=$(cat $FGTEST_OUT | tail -n 1)
    sed -i '$ d' $FGTEST_OUT
    fgtest_report
    if [ $TEST_RES -eq 0 ]; then
        echo "Test: $TEST_PKG executed successfully"
    else
        echo "Test: $TEST_PKG failed to execute"
        return 1
    fi
    return 0
}

# Modify last inserted infrastructure
fgtest_modinfra() {
    TEST_PKG="Modify infrastructure"
    TEST_TITLE="Infrastructure modify"
    TEST_SHDESC="infra_modify"
    TEST_DESC="\
This test modify the new inserted infrastructure having id: '${TEST_INFRA_ID}' calling \
<span class=\"badge\">/infrastructures</span> endpoint and using <b>PUT</b> method"
    TEST_APICALL="(PUT) /infrastructures/$TEST_INFRA_ID"
    MOD_INFRA_JSON=$(mktemp)
    cat >$MOD_INFRA_JSON <<EOF
{ "id": ${TEST_INFRA_ID},
  "name": "(modified) SSH Test infrastructure",
  "parameters": [ { "name": "jobservice", 
                    "value": "(modified) ssh://localhost" },
                  { "name": "username",
                    "value": "(modified) ${FGTEST_USR}" },
                  { "name": "password",
                    "value": "(modified) ${FGTEST_PAS}" } ],
  "description": "(modified) SSH Test infrastructure for fgtest",
  "enabled": false,
  "virtual": true }
EOF
    FG_HEADERS="$FG_HEAD_AUTH $FG_HEAD_JSON"
    TEST_JSON_DATA=$(cat $MOD_INFRA_JSON)
    TEST_CMD="curl -w \"\n%{http_code}\" -f $FG_HEADERS -X PUT -d '"$TEST_JSON_DATA"' $FG_ENDPOINT/infrastructures/$TEST_INFRA_ID"
    echo "Executing: '"$TEST_CMD"'"
    eval "$TEST_CMD" >$FGTEST_OUT 2>$FGTEST_ERR
    TEST_RES=$?
    TEST_HTTPRETCODE=$(cat $FGTEST_OUT | tail -n 1)
    sed -i '$ d' $FGTEST_OUT
    rm -f $NEW_INFRA_JSON
    fgtest_report
    if [ $TEST_RES -eq 0 ]; then
        echo "Test: $TEST_PKG executed successfully"
    else
        echo "Test: $TEST_PKG failed to execute"
        return 1
    fi
    return 0
}

# Prepares a test report using the following:
#  TEST_TITLE - Title of the test
#  TEST_SHDESC - Short description of the test (used to generate html file)
#  TEST_DESC - Description of the test
#  FGTEST_OUT - File containing the text output of tested command
#  FGTEST_ERR - File containing the text error of tested command
#  TEST_RES - The curl return code (curl must have -f optrion)
#  TEST_HTTPRETCODE - The HTTP/s request return code 
fgtest_report() {
    TEST_CMD_CLEAN=$(echo $TEST_CMD | sed s/'-w\ "\\n%{http_code}"'// | sed s/-f\ //)
    TEST_OUT=$(cat $FGTEST_OUT)
    TEST_ERR=$(cat $FGTEST_ERR)
    if [ $TEST_RES -eq 0 ]; then
        TEST_RES_OUT="<span class=\"label label-success\">Passed</span>"
    else
        TEST_RES_OUT="<span class=\"label label-danger\">Failed</p>"
    fi
    BACK_LINK="<a href=\"${REPORT_INDEX}\">tests</a>"
    TEST_ROW="<tr><td><a href=\"${TEST_SHDESC}.html\">${TEST_TITLE}</a></td><td>${TEST_RES_OUT}</td><td>${TEST_DESC}</td></tr>"
    cat >$REPORT_HOMEDIR/${TEST_SHDESC}.html <<EOF
<html>
<title>${TEST_TITLE}</title>
<head>
  <link href="css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
<script src="js/jquery.min.js"></script>
<script src="js/bootstrap.min.js"></script>
<div class="container theme-showcase" role="main">
<div class="jumbotron">
<h1>${TEST_TITLE}</h1>
<p>${TEST_DESC}</p>
</div>
<table class="table table-bordered">
<tr><td>API call</td><td><pre>$TEST_APICALL</pre></td></tr>
<tr><td>Command</td><td style="word-wrap: break-word"><pre>${TEST_CMD_CLEAN}</pre></td></tr>
<tr><td>Curl return code</td><td><pre>${TEST_RES}</pre></td></tr>
<tr><td>HTTP return code</td><td><pre>${TEST_HTTPRETCODE}</pre></td></tr>
<tr><td>Output</td><td><pre>${TEST_OUT}</pre></td></tr>
<tr><td>Error</td><td><pre>${TEST_ERR}</pre></td></tr>
</table>
<div class="page-header"><h1>Notes</h1></div>
<div class="well">
<p>You can go back to the ${BACK_LINK} page</p>
</div>
</body>
</html>
EOF
    sed -i "/<!-- Test list -->/a ${TEST_ROW}" $REPORT_HOMEDIR/$REPORT_INDEX
}

# Close all opened resources before to exit
fgtest_close() {
    rm -f $FGTEST_OUT $FGTEST_ERR
}

#
# Code
#

# Initialize test environment
fgtest_init

# Perorm tests
fgtest_user &&
fgtest_ptv &&
fgtest_fg &&
fgtest_newinfra &&
fgtest_viewinfras &&
fgtest_viewinfra &&
fgtest_modinfra || echo "Error while perfomring test package: $TEST_PKG"

# Close the test environment
fgtest_close
