# coding=utf8
#


'''
This module is task object
'''


class BaseTask(object):
    ''' '''
    
    def __init__(self, tid, tbody, *args, **kwargs):
        self.id = tid
        self.tbody = tbody

    def __repr__(self):
        ''' '''
        return "<Task %d with task content: %s>" % (self.id, str(self.tbody))