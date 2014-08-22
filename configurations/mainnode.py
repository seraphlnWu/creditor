# coding=utf8

from os.path import join

main_node_host = 'localhost'
main_node_port = 5036
controller_port = 5036
controller_timeout = 10

main_node_manhole_port = 8791

app_root = '/home/wubin/observer'

client_register_timeout = 10
client_request_timeout = 1000       # seconds

request_max_attempts = 1
request_attempt_interval = 1000     # seconds

versions = {
    'observer.creditor.active_spider': ((1, 0), (1, 0)),
}

mongo_host = 'localhost'
mongo_port = 27017
mongo_dbname = 'sandbox_keywords'
collection_name = 'accounts'
db_keywords_collection = 'keywords'

client_manhole_port = 8788

min_priority = 1
max_priority = 10

keyword_freq_file = 'keywords_freq_file'
feed_id_file = 'feed_id_file'
keyword_file = ''

db_uids_host = 'localhost'
db_uids_port = 27017
db_uids_dbname = 'sandbox_keywords'
db_uids_collection = 'uids'

db_backtracking_collection = 'backtracking_keywords'

REDIS_HOST = 'localhost'
REDIS_PORT = 6379

kafka_host = 'localhost'
kafka_port = 9092
kafka_topic = "store_topic"

controller_timeout = 15
