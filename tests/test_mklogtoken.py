from mklogtoken import tokenEncode

def test_mklogtoken():
	assert len(tokenEncode("0123456789abcdef","username","password"))>0
