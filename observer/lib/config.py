#encoding=utf-8

from ConfigParser import SafeConfigParser, NoOptionError
from os.path import join, abspath, dirname

from observer.lib.singleton import Singleton
from observer.lib import log


class Config(object):
    """use singleton avoid global variables"""
    __metaclass__ = Singleton

    DEFAULT_CFILE = abspath(join(dirname(__file__), '../../conf/config.ini'))
    ACTUAL_CFILE = None
    SECTION_NAME = 'main'

    def __init__(self):
        self.load_config()

    def load_config(self):
        config_file = self.__class__.ACTUAL_CFILE or self.__class__.DEFAULT_CFILE
        self._cfg = SafeConfigParser()
        self._cfg.read([config_file, ])

    def get(self, option, section=None, value_type=str):
        return self._cfg._get(section or self.__class__.SECTION_NAME,
                              value_type, option)

    def __getattr__(self, option):
        try:
            return self.get(option)
        except NoOptionError:
            log.debug("Got an unknown config: %s" % option)
            return None

if __name__ == '__main__':
    #Config.SECTION_NAME = 'ssss'
    #print Config.SECTION_NAME
    print Config().get('base_path')
