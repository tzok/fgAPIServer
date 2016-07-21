from mklogtoken import token_encode


def test_mklogtoken():
    key = "0123456789abcdef"
    username = "test"
    password = "test"
    token = token_encode(key, username, password)
    tinfo = tokenDecode(token)
    tusrnm, tpaswd, tkntms = tokenInfo(tinfo)
    assert username == tusrnm and password == tpaswd and tkntms > 0
