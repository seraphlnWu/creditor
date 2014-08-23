from twisted.application import service

import os.path
import configurations.node as node_cfg
import configurations as server_cfg

from twisted.conch.manhole_tap import Options, makeService
from twisted.internet import reactor

from twisted.web import client

from observer.node.client import Client
from observer.utils import getObject

application = service.Application('Observer Creditor Active Spider Page Client')

try:
    app_path = server_cfg.app_path
except:
    app_path = None

if app_path is None:
    app_path = os.path.split(__file__)[0]
    server_cfg.app_path = app_path

NodeService = getObject('observer.platform.creditor.page_client.NodeService')

idx = 1
nodeservice = NodeService(cfg=node_cfg)
node = Client(nodeservice)
nodeservice.setServiceParent(application)

o = Options()
o.parseOptions([
    '--passwd',
    'manholeusers.txt',
    '--sshPort',
    str(node_cfg.client_manhole_port),
])

namespace = {}
namespace['application'] = application
namespace['services'] = service.IServiceCollection(application)
namespace['nodeservice'] = nodeservice
o['namespace'] = namespace

manhole_service = makeService(o)
manhole_service.setServiceParent(application)
