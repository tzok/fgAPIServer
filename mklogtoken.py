from Crypto.Cipher import ARC4
import time
import base64
secret = "0123456789ABCDEF" # (!) Please use fgapiserver_secret value
username = "test"
password = "test"
# Encode
obj=ARC4.new(secret)
logtoken = base64.b64encode(obj.encrypt("username=%s:password=%s:timestamp=%s" % (username,password,int(time.time()))))
print logtoken 
