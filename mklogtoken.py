from Crypto.Cipher import ARC4
import time
import base64
key = "0123456789ABCDEF" # (!) Please use fgapiserver_secret value
username = "test"
password = "test"


# Encode
def tokenEncode(key,username,password):
    obj=ARC4.new(key)
    return base64.b64encode(obj.encrypt("username=%s:password=%s:timestamp=%s" % (username,password,int(time.time()))))



if __name__ == "__main__":
    print tokenEncode(key,username,password)
