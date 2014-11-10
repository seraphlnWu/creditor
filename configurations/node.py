# coding=utf8

from os.path import join
from socket import gethostname

main_node_host = 'localhost'
main_node_port = 5034

main_node_manhole_port = 8787
app_root = '/home/wubin/observer'
key_root = join(app_root, '/keys')
server_key_file = join(key_root, 'server.key')
server_cert_file = join(key_root, 'server.cert')
ca_cert_file = join(key_root, 'cacert.pem')

user_mongo_host = 'localhost'
user_mongo_port = 27017
user_mongo_name = 'sandbox_keywords'
user_mongo_collection = 'users'
probe_mongo_collection = 'probes'

host_port = 5034
host_name = gethostname()

userdb_host = 'localhost'
userdb_port = 27017
userdb_dbname = 'sandbox_keywords'
collection_name = 'accounts'
userdb_idcollection = 'probe'
userdb_collection = 'users'

client_manhole_port = 8789

db_keywords_host = 'localhost'
db_keywords_port = 27017
db_keywords_dbname = 'sandbox_keywords'
db_keywords_collection = 'key'

min_priority = 1
max_priority = 10

controller_timeout=25

prefix = '_spider' 
http_proxy = None
http_agent='Mozilla/5.0 (X11; Linux i686; rv:8.0) Gecko/20100101 Firefox/8.0'

http_interval_min = 15.0
http_interval_max = 25.0
login_interval = 60.0
max_agent = 1
db_keywords_host = 'localhost'
db_keywords_port = 27017
db_keywords_dbname = 'sandbox_keywords'
db_keywords_collection = 'key'

min_priority = 1
max_priority = 10

keyword_freq_file = 'keywords_freq_file'
keyword_file = ''

