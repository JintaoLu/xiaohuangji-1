#-*-coding:utf-8-*-

"""
Copyright (c) 2012 wong2 <wonderfuly@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
'Software'), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""


# 人人各种接口

import requests
import json
import re
import random
from urlparse import urlparse, parse_qsl
from pyquery import PyQuery
from ntype import NTYPES
from encrypt import encryptString
import pickle
import sys


class RenRen:

    def __init__(self, email=None, pwd=None):
        self.session = requests.Session()
        self.token = {}

        if email and pwd:
            self.login(email, pwd)

    def save(self, path = None):
        if path is None:
            path = self.email + ".info.pickle"
        obj = {'cookie': self.session.cookies, 'token': self.token, 'info': self.info}
        pickle.dump(obj, open(path, 'w'))
        return True


    def load(self, path = None):
        if path is None:
            path = self.email + ".info.pickle"
        try:
            obj = pickle.load(open(path, 'r'))
            self.session.cookies = obj['cookie']
            self.token = obj['token']
            self.info = obj['info']
            self.getToken()
            if self.token['requestToken'] != '':
                return True
            else:
                return False
        except Exception, e:
            return False

    def loginByCookie(self, cookie_path):
        with open(cookie_path) as fp:
            cookie_str = fp.read()
            cookie_dict = dict([v.split('=', 1) for v in cookie_str.strip().split(';')])
            print cookie_dict
            self.session.cookies = requests.utils.cookiejar_from_dict(cookie_dict)

        self.getToken()

    def saveCookie(self, cookie_path):
        with open(cookie_path, 'w') as fp:
            cookie_dict = requests.utils.dict_from_cookiejar(self.session.cookies)
            print cookie_dict
            cookie_str = ';'.join([k + '=' + v for k, v in cookie_dict.iteritems()])
            fp.write(cookie_str)

    def login(self, email, pwd):
        self.email = email
        if self.load():
            return

        key = self.getEncryptKey()

        if self.getShowCaptcha(email) == 1:
            self.getICode()
            print "Please input the code in file 'icode.jpg':"
            icode = raw_input().strip()
        else:
            icode = ''

        data = {
            'email': email,
            'origURL': 'http://www.renren.com/home',
            'icode': icode,
            'domain': 'renren.com',
            'key_id': 1,
            'captcha_type': 'web_login',
            'password': encryptString(key['e'], key['n'], pwd) if key['isEncrypt'] else pwd,
            'rkey': key['rkey']
        }
        print "login data: %s" % data
        url = 'http://www.renren.com/ajaxLogin/login?1=1&uniqueTimestamp=%f' % random.random()
        r = self.post(url, data)
        result = r.json()
        print result
        if result['code']:
            print 'login successfully'
            self.email = email
            r = self.get(result['homeUrl'])
            self.info = self.getUserInfo()
            self.getToken(r.text)
            self.save()
        else:
            print 'login error', r.text

    def getICode(self):
        # What's wrong with the following?
        #r = self.get('http://icode.renren.com/getcode.do', \
        #        data = {'t':'web_login','rnd':random.random()})
        r = self.get("http://icode.renren.com/getcode.do?t=web_login&rnd=%s" % random.random())
        if r.status_code == 200 and r.raw.headers['content-type'] == 'image/jpeg':
            with open('icode.jpg', 'wb') as f:
                for chunk in r.iter_content():
                    f.write(chunk)
        else:
            print "get icode failure"
        

    def getShowCaptcha(self, email = None):
        r = self.post('http://www.renren.com/ajax/ShowCaptcha', data = {'email':email})
        return r.json()

    def getEncryptKey(self):
        r = requests.get('http://login.renren.com/ajax/getEncryptKey')
        return r.json()

    def getToken(self, html=''):
        p = re.compile("get_check:'(.*)',get_check_x:'(.*)',env")

        if not html or html == '':
            r = self.get('http://www.renren.com')
            html = r.text

        result = p.search(html)
        self.token = {
            'requestToken': result.group(1),
            '_rtk': result.group(2)
        }

    def _parse_timeline(self, text):
        dom = PyQuery(text)
        articles = dom.children()
        s_list = []
        for a in articles:
            aa = PyQuery(a)
            try:
                f = {}
                f['text'] = PyQuery(aa.children()[1]).text()
                try:
                    # This is a share item
                    f['reply'] = json.loads(PyQuery(PyQuery(aa.children()[3]).children()[3]).text())
                    #print "a share item"
                except IndexError:
                    # This is a status item
                    try:
                        f['reply'] = json.loads(PyQuery(PyQuery(aa.children()[2]).children()[3]).text())
                        #print "a status item"
                    except IndexError:
                        print "un recognizable feeds: %s" % f['text']
                if 'reply' in f:
                    s_list.append(f)
            except Exception, e:
                print "Exception: %s" % e
                pass

        for s in s_list:
            s['data'] = {
                    'doing_id': s['reply']['cid'], 
                    'owner_id': s['reply']['oid'],
                    'type_num': s['reply']['typeNum']
                    }

        return s_list
        #return text

    def update(self, text):
        url_update = 'http://shell.renren.com/%s/status' % self.info['hostid']
        r = self.post(url_update, {'content': text, 'hostid': self.info['hostid'], 'channel': 'renren'})
        return r.json()

    def home_timeline(self, page = None):
        if page:
            r = self.post('http://guide.renren.com/feedguide.do', {'p':page})
        else:
            r = self.post('http://guide.renren.com/feedguide.do')
        return self._parse_timeline(r.text)

    def request(self, url, method, data={}):
        if data:
            data.update(self.token)

        if method == 'get':
            return self.session.get(url, data=data)
        elif method == 'post':
            return self.session.post(url, data=data)

    def get(self, url, data={}):
        return self.request(url, 'get', data)

    def post(self, url, data={}):
        return self.request(url, 'post', data)

    def getUserInfo(self):
        r = self.get('http://notify.renren.com/wpi/getonlinecount.do')
        return r.json()

    def getNotifications(self):
        url = 'http://notify.renren.com/rmessage/get?getbybigtype=1&bigtype=1&limit=999&begin=0&view=16&random=' + str(random.random())
        r = self.get(url)
        try:
            result = json.loads(r.text, strict=False)
        except:
            print 'error'
        return result 

    def getDoings(self, uid, page=0):
        url = 'http://status.renren.com/GetSomeomeDoingList.do?userId=%s&curpage=%d' % (str(uid), page)
        r = self.get(url)
        return r.json().get('doingArray', [])

    def getDoingById(self, owner_id, doing_id):
        doings = self.getDoings(owner_id)
        doing = filter(lambda doing: doing['id'] == doing_id, doings)
        return doing[0] if doing else None

    def getDoingComments(self, owner_id, doing_id):
        url = 'http://status.renren.com/feedcommentretrieve.do'
        r = self.post(url, {
            'doingId': doing_id,
            'source': doing_id,
            'owner': owner_id,
            't': 3
        })

        return r.json()['replyList']

    def getCommentById(self, owner_id, doing_id, comment_id):
        comments = self.getDoingComments(owner_id, doing_id)
        comment = filter(lambda comment: comment['id'] == comment_id, comments)
        return comment[0] if comment else None

    def addCommentGeneral(self, data):
        url = 'http://status.renren.com/feedcommentreply.do'
        #url = 'http://page.renren.com/doing/reply'

        # 'stype' is not mandatory
        # 't'=4 is for shares
        # 't'=3 is for status
        # t must exist
        payloads = {
            'rpLayer': 0,
            'source': data['doing_id'],
            'owner': data['owner_id'],
            'c': data['message']
        }
        if data.get('type_num', None):
            payloads['t'] = data.get('type_num')

        if data.get('reply_id', None):
            payloads.update({
                'rpLayer': 1,
                'replyTo': data['author_id'],
                'replyName': data['author_name'],
                'secondaryReplyId': data['reply_id'],
                'c': '回复%s：%s' % (data['author_name'].encode('utf-8'), data['message'])
            })

        print payloads
        print self.email, 'going to send a comment: ', payloads['c']

        r = self.post(url, payloads)
        r.raise_for_status()

        print 'comment sent', r.json()
        return r.json()

    def addCommentShare(self, data):
        url = 'http://status.renren.com/feedcommentreply.do'
        #url = 'http://page.renren.com/doing/reply'

        # 'stype' is not mandatory
        # 't'=4 is for shares
        # 't'=3 is for status
        # t must exist
        payloads = {
            't': 4,
            #'stype': 103, 
            'rpLayer': 0,
            'source': data['doing_id'],
            'owner': data['owner_id'],
            'c': data['message']
        }

        if data.get('reply_id', None):
            payloads.update({
                'rpLayer': 1,
                'replyTo': data['author_id'],
                'replyName': data['author_name'],
                'secondaryReplyId': data['reply_id'],
                'c': '回复%s：%s' % (data['author_name'].encode('utf-8'), data['message'])
            })

        print payloads
        print self.email, 'going to send a comment: ', payloads['c']

        r = self.post(url, payloads)
        r.raise_for_status()

        print 'comment sent', r.json()
        return r.json()

    def addComment(self, data):
        url = 'http://status.renren.com/feedcommentreply.do'
        #url = 'http://page.renren.com/doing/reply'

        payloads = {
            't': 3,
            'rpLayer': 0,
            'source': data['doing_id'],
            'owner': data['owner_id'],
            'c': data['message']
        }

        if data.get('reply_id', None):
            payloads.update({
                'rpLayer': 1,
                'replyTo': data['author_id'],
                'replyName': data['author_name'],
                'secondaryReplyId': data['reply_id'],
                'c': '回复%s：%s' % (data['author_name'].encode('utf-8'), data['message'])
            })

        print payloads
        print self.email, 'going to send a comment: ', payloads['c']

        r = self.post(url, payloads)
        r.raise_for_status()

        print 'comment sent', r.json()
        return r.json()

    # 访问某人页面
    def visit(self, uid):
        self.get('http://www.renren.com/' + str(uid) + '/profile')

if __name__ == '__main__':
    try:
        from my_accounts import accounts
    except:
        print "please configure your renren account in 'my_account.py' first"
        sys.exit(-1)
    renren = RenRen()
    renren.login(accounts[0][0], accounts[0][1])
    #renren.saveCookie('cookie.txt')
    #renren.loginByCookie('cookie.txt')
    #info = renren.getUserInfo()
    print renren.info
    #print 'hello', info['hostname']
    #print renren.getNotifications()
    #renren.visit(328748051)
