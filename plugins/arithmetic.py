#!/usr/bin/env python
#-*-coding:utf-8-*-

"""
Copyright (c) 2012 Pili Hu <hpl1989@gmail.com>

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

# Basic Arithmetic Module
#
# 1. For security reasons, we only evaluate 4 preliminary operators,
#    i.e. + - * /
# 2. Non-programmer may find '5/3=1' non-intuitive. We stick to the
#    Python defaults and do not modify it. One can use floating point
#    expressions instead.
# 3. Emoji from:
#       http://zh.wikipedia.org/wiki/%E8%A1%A8%E6%83%85%E7%AC%A6%E5%8F%B7

import re
import threading

try:
    from settings import AI_ARITHMETIC_REGEX_TEST
except:
    AI_ARITHMETIC_REGEX_TEST = '([ \(\.\)0-9+\-*/]+)((\s*=\s*(\?|？))|(\s*是多少|\s*是几))'

try:
    from settings import AI_ARITHMETIC_REGEX_HANDLE
except:
    AI_ARITHMETIC_REGEX_HANDLE = AI_ARITHMETIC_REGEX_TEST

try:
    from settings import AI_ARITHMETIC_MAX_LEN_EXP
except:
    AI_ARITHMETIC_MAX_LEN_EXP = 100

try:
    from settings import AI_ARITHMETIC_MAX_LEN_REPLY
except:
    AI_ARITHMETIC_MAX_LEN_REPLY = 50

try:
    from settings import AI_ARITHMETIC_EVAL_TIMEOUT
except:
    AI_ARITHMETIC_EVAL_TIMEOUT = 1.0 # Second

REGEX_TEST = re.compile(AI_ARITHMETIC_REGEX_TEST)
REGEX_HANDLE = re.compile(AI_ARITHMETIC_REGEX_HANDLE)

class ChickCalculator(threading.Thread):
    def __init__(self, exp):
        threading.Thread.__init__(self)
        self.exp = exp
        self.result = None

    def cal(self, exp):
        try:
            ans = str(eval(exp))
            if len(ans) > AI_ARITHMETIC_MAX_LEN_REPLY:
                return '这个数字太大了！鸡才懒得回你呢╮(︶︿︶)╭'
            else:
                return '不就是%s嘛。啦啦啦……我是计算鸡…… ＼（￣︶￣）／' % ans
        except ZeroDivisionError:
            return '你好笨啊！除零了。跟小鸡学下四则运算吧 （＃￣▽￣＃）'
        except SyntaxError:
            return '(´･д･`) 这明显有问题嘛！！你确定没写错？'
        except Exception, e:
            #TODO:
            #    Any logging convention in this project? We should log the
            #    error for further investigation
            return '好复杂哦，计算鸡也不会了 ╮(︶︿︶)╭'

    def run(self):
        self.result = self.cal(self.exp)


def test(data, bot):
    return True if REGEX_TEST.search(data['message']) else False


def handle(data, bot):
    try:
        exp = REGEX_HANDLE.search(data['message']).groups()[0]
    except:
        # The flow is not supposed to reach here. 'data' is already
        # tested by AI_ARITHMETIC_REGEX_TEST so we should be able to
        # read group()[0]. This is just to prevent your customized
        # regex from causing errors.
        return '好复杂哦，计算鸡也不会了 ╮(︶︿︶)╭ （怎么会这样嘛）'

    if len(exp) > AI_ARITHMETIC_MAX_LEN_EXP:
        return '太长了……小鸡才不算呢。╮(︶︿︶)╭'

    cc = ChickCalculator(exp)
    cc.start()
    cc.join(AI_ARITHMETIC_EVAL_TIMEOUT)
    r = cc.result
    if r:
        return r
    else:
        return '太难了，计算鸡都算不出来 ╮(︶︿︶)╭'


def _ut_test(exp):
    print test({'message': exp}, None), "\t", 'test("%s")' % exp


def _ut_handle(exp):
    print handle({'message': exp}, None), "\t", 'handle("%s")' % exp

if __name__ == '__main__':
    _ut_test('hello')
    _ut_test('2 * 4+ 5/3 = ?')
    _ut_test('x *4+ 5/3 =?')
    _ut_test('2 * 4+ 5/3= ？')
    _ut_test('2 * 4+ 5/3 是多少')
    _ut_test('2 * 4+ 5/3 是几')
    _ut_test('sys.exit(-1)')
    _ut_test('sys.exit(-1) = ?')
    _ut_handle('2 * 4+ 5/3 = ?')
    _ut_handle('x *4+ 5/3 =?')
    _ut_handle('2 * 4+ 5/3= ？')
    _ut_handle('2 * 4+ 5/3 是多少')
    _ut_handle('2 * (4+ 5)/3 是几')
    _ut_handle('2 * 4+ 5/(3.0) 是几')
    _ut_handle('2 * 4+ 5/0 是几')
    _ut_handle('sys.exit(-1) = ?')
    _ut_handle('1' + ('+1' * (AI_ARITHMETIC_MAX_LEN_EXP / 2 - 1)) + '=?')
    _ut_handle('1' + ('+1' * (AI_ARITHMETIC_MAX_LEN_EXP / 2)) + '=?')
    _ut_handle(('1' * (AI_ARITHMETIC_MAX_LEN_REPLY)) + '=?')
    _ut_handle(('1' * (AI_ARITHMETIC_MAX_LEN_REPLY + 1)) + '=?')
    _ut_handle('2**' + ('9' * (AI_ARITHMETIC_MAX_LEN_EXP - 3)) + '=?') # Test time consumption
