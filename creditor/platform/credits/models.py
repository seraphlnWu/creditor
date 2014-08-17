# coding=utf8

import json
from datetime import datetime


def parse_html_value(html):
    ''' '''
    return html[html.find('>')+1:html.rfind('<')]

def parse_a_href(atag):
    ''' '''
    start = atag.find('"') + 1
    end = atag.find('"', start)
    return atag[start:end]

def format_date(created_at):
    """ 格式化创建时间 """
    #if isinstance(created_at, unicode):
        #    return datetime.strptime(created_at, '%a %b %d %H:%M:%S +%f %Y')
        #        #else:
        #            #    return created_at
        #                return created_at
    return created_at


def do_save_statuses(ufile, sfile, statuses):
    ''' '''
    user = {}
    if statuses:
        st = statuses[0]
        u = st.get('user', {})
        user.update({
            '_id': u.get('id'),
            'uid': u.get('id'),
            'uam': u.get('allow_all_act_msg', False),
            'uac': u.get('allow_all_comment', True),
            'ah': u.get('avatar_hd', ''),
            'al': u.get('avatar_large', ''),
            'bfc': u.get('bi_followers_count', 0),
            'ba': u.get('block_app', 0),
            'bw': u.get('block_word', 0),
            'c': u.get('city', '0'),
            'cl': u.get('class', 0),
            'ct': format_date(u.get('created_at', '')),
            'desc': u.get('description', ''),
            'dm': u.get('domain', ''),
            'fc': u.get('favourites_count', 0),
            'fm': u.get('follow_me', False),
            'foc': u.get('followers_count', 0),
            'fi': u.get('following', False),
            'frc': u.get('friends_count', 0),
            'g': u.get('gender'),
            'ge': u.get('geo_enabled', True),
            'l': u.get('lang', ''),
            'loc': u.get('location', ''),
            'mr': u.get('mbrank', 0),
            'mt': u.get('mbtype', 0),
            'n': u.get('name', ''),
            'os': u.get('online_status', 0),
            'piu': u.get('profile_image_url', ''),
            'pu': u.get('profile_url', ''),
            'p': u.get('province', '0'),
            'pt': u.get('ptype', 0),
            'rmk': u.get('remark', 0),
            'sn': u.get('screen_name', ''),
            'star': u.get('star', 0),
            'stc': u.get('statuses_count', 0),
            'url': u.get('url', ''),
            'v': u.get('verified', False),
            'vr': u.get('verified_reason', ''),
            'vt': u.get('verified_type', -1),
            'wh': u.get('weihao', ''),
        })

        ufile.write('%s\n' % json.dumps(user))

    for st in statuses:
        rt = st.get('retweeted_status', {})
        result = {
            '_id': st.get('id', 0),
            'ac': st.get('attitudes_count', 0),
            'cc': st.get('comments_count', 0),
            'ct': format_date(st.get('created_at', '')),
            'fv': st.get('favorited', False),
            'geo': st.get('geo', None),
            'id': st.get('id', 0),
            'isn': st.get('in_reply_to_screen_name', ''),
            'isi': st.get('in_reply_to_status_id', ''),
            'iui': st.get('in_reply_to_user_id', ''),
            'mid': st.get('mid', ''),
            'ml': st.get('mlevel', 0),
            'pu': st.get('pic_urls', []),
            'rc': st.get('reposts_count', 0),
            'src': parse_html_value(st.get('source', '')),
            'su': parse_a_href(st.get('source', '')),
            'txt': st.get('text', ''),
            'trunc': st.get('truncated', False),
        }
        result.update({'user': user})

        if rt:
            ret = {
                'ac': rt.get('attitudes_count', 0),
                'bp': rt.get('bmiddle_pic', ''),
                'cc': rt.get('comments_count', 0),
                'ct': format_date(rt.get('created_at', '')),
                'fv': rt.get('favorited', False),
                'geo': rt.get('geo', None),
                'id': rt.get('id', 0),
                'isn': rt.get('in_reply_to_screen_name', ''),
                'isi': rt.get('in_reply_to_status_id', ''),
                'iui': rt.get('in_reply_to_user_id', ''),
                'mid': rt.get('mid', ''),
                'ml': rt.get('mlevel', 0),
                'op': rt.get('original_pic', ''),
                'pu': rt.get('pic_urls', []),
                'rc': rt.get('reposts_count', 0),
                'txt': rt.get('text', ''),
                'tp': rt.get('thumbnail_pic', ''),
                'trunc': rt.get('truncated', False),
                'src': parse_html_value(st.get('source', '')),
                'su': parse_a_href(st.get('source', '')),
                'ruid': rt.get('user', {}).get('id'),
            }
            result.update({'retweeted_status': ret})

        sfile.write('%s\n' % json.dumps(result))

def save_statuses(statuses):
    ''' '''
    now = datetime.now()
    try:
        ufile = open('/home/operation/data/users_%s%s%s.txt' % (now.year, now.month, now.day), 'a')
        sfile = open('/home/operation/data/statuses_%s%s%s.txt' % (now.year, now.month, now.day), 'a')
        do_save_statuses(ufile, sfile, statuses)
    except Exception as msg:
        print str(msg)
    finally:
        ufile.close()
        sfile.close()
