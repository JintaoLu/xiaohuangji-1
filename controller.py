#-*-coding:utf-8-*-

"""
Copyright (c) 2012 wong2 <wonderfuly@gmail.com>
Copyright (c) 2012 Qijiang Fan <fqj1994@gmail.com>

Original Author:
    Wong2 <wonderfuly@gmail.com>
Changes Statement:
    Changes made by Qijiang Fan <fqj1994@gmail.com> on
    Jan 6 2013:
        Add keywordfilter bindings.

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


# 小黄鸡们

from renren import RenRen
from ai import magic
from ntype import NTYPES
from filter_manager import questionfilter, answerfilter
import re
try:
    from my_accounts import accounts
except:
    from accounts import accounts

# 匹配自己名字的正则
self_match_pattern = re.compile('<a.*@古月说.*</a>')

# 登录账号得到bot
def getBots(accounts):
    bots = []
    for account in accounts:
        bot = RenRen()
        bot.login(account[0], account[1])
        print bot.email, 'login'
        bots.append(bot)
    return bots

bots = getBots(accounts)

# 根据通知得到该回复的更详细信息
def getNotiData(bot, data):
    owner_id, doing_id = data['owner_id'], data['doing_id']

    payloads = {
      'owner_id': owner_id,
      'doing_id': doing_id,
      'type_num': 3
    }

    ntype = data['ntype']

    content = ''
    if ntype == NTYPES['at_in_status']:
        doing = bot.getDoingById(owner_id, doing_id)
        if doing:
            content = self_match_pattern.sub('', doing['content'].encode('utf-8'))
        else:
            return None, None

    elif ntype == NTYPES['reply_in_status_comment']:
        reply_id = data['reply_id']
        comment = bot.getCommentById(owner_id, doing_id, reply_id)
        if comment:
            payloads.update({
                'author_id': comment['ownerId'],
                'author_name': comment['ubname'],
                'reply_id': reply_id
            })
            content = comment['replyContent']
            content_s = content.split(u'\uff1a', 1)
            if len(content_s) == 1:
                content_s = content.split(': ', 1)
            if len(content_s) == 1:
                content_s = content.split(':', 1)
            content = content_s[-1]
            #print content
        else:
            return None, None

    return payloads, content

def answer(q):
    a = answerfilter(magic(questionfilter(q)))
    if a.find('王力宏') != -1:
        return "[simsimi]: (叹气)(叹气)(叹气)我千万不要再说王力宏了。。"
    else:
        return "[simsimi]: " + a

    #d['message'] = "[simsimi]:" + answerfilter(magic(questionfilter(data['text'])))


# 得到数据，找到答案，发送回复
def reply(data):
    bot = bots[0] # 现在只有一只小鸡了，且没了评论限制

    data, message = getNotiData(bot, data)

    if not data:
        return

    # 不要自问自答
    if 'author_name' in data and '古月说' in data['author_name'].encode('utf-8'):
        return

    print 'handling comment', data, '\n'

    #data['message'] = "[simsimi]:" + answerfilter(magic(questionfilter(message)))
    data['message'] = answer(message)

    result = bot.addComment(data)

    if result['code'] != 0:
        print 'Error sending comment by bot %s' % bot.email
        #raise Exception('Error sending comment by bot %s' % bot.email)

def reply_direct(data):
    bot = bots[0]

    #print "In 'reply_direct'"
    #print data

    d = data['data']
    try:
        #d['message'] = "[simsimi]:" + answerfilter(magic(questionfilter(data['text'])))
        d['message'] = answer(data['text'])
    except Exception, e:
        print e.message
        d['message'] = "[simsimi-fail]:这我该说什么。。。？？"

    result = bot.addCommentGeneral(d)
    
    if result['code'] != 0:
        print 'Error sending comment by bot %s' % bot.email
        #raise Exception('Error sending comment by bot %s' % bot.email)

if __name__ == '__main__':
    reply_direct({'text': u'\u80e1\u8a00\u5151 hpl :\xa0// \u8584\u5929\u5916 :\u4e00\u4e2a\u771f\u5b9e\u7684\u6545\u4e8b// \u8463\u96ef :// \u674e\u4f0f :// \u5415\u91d1\u534e :// \u9646\u8d5b\u7537 :// \u738b\u6c38 :// \u674e\u84b8 :\u86cb\u86cb\u7684\u5fe7\u4f24//\u5218\u4e00\u7487:\u5206\u4eab\u7167\u7247', 'data': {'type_num': u'4', 'doing_id': u'15106518111', 'owner_id': u'472085551'}, 'reply': {u'userDigged': u'', u'loadURI': u'http://status.renren.com/feedcommentretrieve.do', u'cid': u'15106518111', u'delURI': u'http://status.renren.com/feedcommentdelete.do', u'rpLength': u'5', u'oid': u'472085551', u'sendURI': u'http://status.renren.com/feedcommentreply.do?fin=3&ft=share&ff_id=472085551', u'type': u'share', u'digged': u'', u'stype': u'103', u'typeNum': u'4'}})
