# coding=utf8

from cookielib import CookieJar
from observer.lib import log
from twisted.internet import reactor, task, ssl
from OpenSSL import SSL

try:
    import json
except ImportError:
    import simplejson as json


def print_error(error):
    ''' print the given error to terminal '''
    print error
    return error


def json_dumps(obj):
    ''' '''
    return json.dumps(obj)


def json_loads(s):
    ''' '''
    try:
        r = json.loads(s)
        return r
    except:
        log.debug("error when json decode: " + s)
        raise


def wait(seconds):
    ''' '''
    def dummy():
        return

    return task.deferLater(reactor, seconds, dummy)


def hex_encode_bytes(s):
    ''' '''
    return ''.join('%02x' % ord(c) for c in s)


def getObject(objstr):
    ''' '''
    r = None
    ol = objstr.split('.')
    modulestr = '.'.join(ol[:-1])
    if modulestr:
        exec('import ' + modulestr)
    exec('r=' + objstr)
    return r


class TLSClientContextFactory(ssl.ClientContextFactory):

    def __init__(self, cert_file, key_file):
        self.cert_file = cert_file
        self, key_file = key_file

    def getContext(self):
        self.method = SSL.TLSv1_METHOD
        ctx = ssl.ClientContextFactory.getContext(self)
        ctx.use_certificate_file(self.cert_file)
        ctx.use_privatekey_file(self.key_file)

        return ctx
