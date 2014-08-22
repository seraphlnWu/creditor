# coding=utf8

'''
    active spider controller节点
'''
import os.path
import sys
sys.path.append(os.path.split(__file__)[0])

from observer.node.controller import ControllerNode
from observer.utils import getObject
from twisted.application import service, internet
from twisted.spread import pb

import configurations.mainnode as nodecfg
import configurations as servercfg
import configurations.api as apicfg

from twisted.conch.manhole_tap import Options, makeService

application = service.Application('observer Active Spider')

try:
    app_path = servercfg.app_path
except:
    app_path = None

if app_path is None:
    app_path = os.path.dirname(__file__)
    servercfg.app_path = app_path

nodeservice = getObject('observer.platform.creditor.controller.ControllerService')(cfg=nodecfg)
mainnode = ControllerNode(nodeservice)

internet.TCPServer(
    nodecfg.main_node_port,
    pb.PBServerFactory(mainnode),
).setServiceParent(application)

nodeservice.setServiceParent(application)

o = Options()
o.parseOptions([
    "--passwd",
    "manholeusers.txt",
    "--sshPort",
    nodecfg.main_node_manhole_port,
])

namespace = {}
namespace['application'] = application
namespace['services'] = service.IServiceCollection(application)
namespace['nodeservice'] = nodeservice
o['namespace'] = namespace

manhole_service = makeService(o)
manhole_service.setServiceParent(application)
