# coding=utf8


import xlwt
import os, sys
import pymongo


db = pymongo.Connection()['creditor']

KEYS = [u'图片',
        u'名称',
        u'人均消费',
        u'服务电话',
        u'商户地址',
        u'优惠日期',
        u'刷卡消费',
        u'招牌服务',
        u'商户介绍',
        u'持卡优惠',
        u'优惠细则',
        u'停车环境',
        u'公交指南']


class OutputWrapper(object):
    ''' 输出文件excel '''

    def __init__(self, file_name, screen_name):
        ''' '''
        self.file_name = (file_name + screen_name).encode("gbk", "ignore")
        self.xlsfile = xlwt.Workbook()        
        self.sheet_cnt = 1
        self.row_cnt = 0
        self.row_limit = 50000
        self.cell_maxsize = 60000
        self.screen_name = screen_name

        self.table = self.xlsfile.add_sheet(self.screen_name + str(self.sheet_cnt))

    def close(self):
        ''' '''
        self.xlsfile.save(self.file_name + ".xls")
        return self.file_name

    def write(self, pos, data):
        ''' ''' 
        #写入excel
        cnt = pos
        for item in data:
            if isinstance(item, int):
                tmp_data = item
            elif isinstance(item, float):
                tmp_data = item
            elif isinstance(item, bool):
                tmp_data = item
            else:
                tmp_data = unicode(item).encode("gbk", "ignore").decode("gbk", "ignore")
                if len(tmp_data) > self.cell_maxsize:
                    tmp_data = tmp_data[:self.cell_maxsize]
            self.table.write(self.row_cnt, cnt, tmp_data)
            cnt += 1
            if cnt >= 256:
                self.row_cnt += 1
                cnt = pos

        self.row_cnt += 1
        if self.row_cnt >= self.row_limit:
            self.row_cnt = 0
            self.sheet_cnt += 1
            self.table = self.xlsfile.add_sheet(self.screen_name + str(self.sheet_cnt))

    def add_new_sheet(self):
        ''' '''
        self.table = self.xlsfile.add_sheet(self.screen_name+str(self.sheet_cnt))


def export_file():
    tmp_file = OutputWrapper("", 'cmbc')
    infos = db.cmbc.find()

    tmp_file.write(0, KEYS)

    for info in infos:
        cur_record = [info.get('pic'),
                      info.get('title'),
                      info.get('avg'),
                      info.get('tel'),
                      info.get('address'),
                      info.get('date'),
                      info.get('payload'),
                      info.get('best_seller'),
                      info.get('company_intro'),
                      info.get('preferential'),
                      info.get('card_detail'),
                      info.get('parking'),
                      info.get('buss')] 
        tmp_file.write(0, cur_record)
    
    tmp_file.close()


if __name__ == '__main__':
    export_file()