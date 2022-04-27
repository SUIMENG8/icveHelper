from io import BytesIO
from PIL import Image
import time
import base64
import random
import json
import sys
import math
import requests

# version 1.1
# author: xinyunaha
# date: 2020.10.24 18:26

minTime = 5  # 观看完一个小节的最小等待时间(单位：秒) 最低5,推荐20以上
maxTime = 8  # 观看完一个小节的最大等待时间(单位：秒) 最低8,推荐30以上

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,like Gecko) '
                         'Chrome/86.0.4240.75 Safari/537.36'}


class Mooc:
    def __init__(self):
        self.username = input("请输入您的账号:")
        self.password = input("请输入您的密码:")
        self.verifyCode = None
        self.userid = None
        self.courseId = None
        self.cellId = None
        self.notWatched = {}
        self.session = requests.session()
        self.verify()
        self.login()
        self.getUserInfo()
        self.getAllClass()
        self.getWatchTime()
        self.Run()

    def verify(self):
        codeContent = self.session.get(f'https://www.icve.com.cn/portal/VerifyCode/index?t={random.random()}',
                                       headers=headers).content
        byteIoObj = BytesIO()
        byteIoObj.write(codeContent)
        Image.open(byteIoObj).show()
        self.verifyCode = input('请输入验证码：')

    def login(self):
        data = {'userName': base64.b64encode(self.username.encode()),
                'pwd': base64.b64encode(self.password.encode()),
                'verifycode': self.verifyCode}
        res = self.session.post('https://www.icve.com.cn/portal/Register/Login_New', headers=headers, data=data).text
        _json = json.loads(res)
        if _json['code'] == 1:
            print('登录成功')
        else:
            print(_json['msg'])
            sys.exit(-1)

    def getWatchTime(self):
        data = {'id': 5, 'courseId': self.courseId, 'serchName': '', 'page': 1}
        res1 = self.session.post('https://www.icve.com.cn/study/Stat/getTable', headers=headers, data=data).text
        pages = math.ceil(
            json.loads(res1)['pagination'].get('totalCount') / json.loads(res1)['pagination'].get('pageSize'))
        for i1 in range(pages):
            _data = {'id': 5, 'courseId': self.courseId, 'serchName': '', 'page': i1}
            res2 = self.session.post('https://www.icve.com.cn/study/Stat/getTable', headers=headers, data=_data).text
            for i2 in range(len(json.loads(res2)['list'])):
                Status = json.loads(res2)['list'][i2].get('Status')
                Score = json.loads(res2)['list'][i2].get('Score')
                Id = json.loads(res2)['list'][i2].get('Id')
                CountLength = json.loads(res2)['list'][i2].get('CountLength')
                if CountLength == '0':
                    pass
                elif Status != 1 or int(Score.replace('%')) != 100:
                    self.notWatched[Id] = toSec(CountLength)

    def getUserInfo(self):
        res = self.session.get('https://www.icve.com.cn/common/common/getJcInfo', headers=headers).text
        _json = json.loads(res)
        self.userid = _json['userInfo'].get('Id')
        print('登录用户:', self.userid)

    def getAllClass(self):
        data = {'userid': self.userid}
        res = self.session.post("https://www.icve.com.cn/studycenter/MyCourse/studingCourse", headers=headers,
                                data=data).text
        print('=========================')
        self.classnum=len(json.loads(res)['list'])
        self.allclass=json.loads(res)['list']
        print("\t-1、自动刷全部课程")
        for i in range(self.classnum):
            print(f'\t{i}、', json.loads(res)['list'][i].get('title'))
        while True:
            num = input('选择您的课程:')
            try:
                if int(num)==-1:
                    self.finishAll=True;
                    self.courseId = json.loads(res)['list'][0].get('id')
                    break
                else:
                    self.finishAll = False;
                    self.courseId = json.loads(res)['list'][int(num)].get('id')
                    break
            except:
                print('输入错误')

    def Run(self):
        print('=========================')
        data = {'courseId': self.courseId}
        res = self.session.post('https://www.icve.com.cn/study/Directory/directoryList', headers=headers,
                                data=data).text
        _json = json.loads(res)
        for i1 in range(len(_json['directory'])):
            for i2 in range(len(_json['directory'][i1].get('chapters'))):
                if len(_json['directory'][i1].get('chapters')[i2].get('knowleges')) > 0:

                    for i3 in range(len(_json['directory'][i1].get('chapters')[i2].get('knowleges'))):
                        for i4 in range(len(_json["directory"][i1].get("chapters")[i2].get("knowleges")[i3].get("cells"))):
                            type = _json["directory"][i1].get("chapters")[i2].get("knowleges")[i3].get("cells")[i4].get(
                                "CellType")
                            id = _json["directory"][i1].get("chapters")[i2].get("knowleges")[i3].get("cells")[i4].get("Id")
                            title = _json["directory"][i1].get("chapters")[i2].get("knowleges")[i3].get("cells")[i4].get(
                                "Title")
                            status = _json["directory"][i1].get("chapters")[i2].get("knowleges")[i3].get("cells")[i4].get(
                                "Status")

                            if _json['directory'][i1].get('chapters')[i2].get('knowleges')[i3].get('cells')[i4].get(
                                    'Status') == 1:
                                print(f'已完成-跳过 第{i1 + 1}模块-第{i2 + 1}单元-第{i3 + 1}讲-{title}')
                            else:
                                if type == 'video' and status != 1:
                                    print(f'新事件-观看视频 第{i1 + 1}模块-第{i2 + 1}单元-第{i3 + 1}讲-{title}')
                                    self.view(id, True)
                                elif type == 'audio' and status != 1:
                                    print(f'新事件-观看音频 第{i1 + 1}模块-第{i2 + 1}单元-第{i3 + 1}讲-{title}')
                                    self.view(id, False)
                                elif type == 'ppt' and status != 1:
                                    print(f'新事件-观看ppt 第{i1 + 1}模块-第{i2 + 1}单元-第{i3 + 1}讲-{title}')
                                    self.view(id, False)
                                elif type == 'question' and status != 1:
                                    print(f'新事件-答题 第{i1 + 1}模块-第{i2 + 1}单元-第{i3 + 1}讲-{title}')
                                    self.answer(id)
                                elif type=='text'and status != 1:
                                    print(f'新事件-观看文件 第{i1 + 1}模块-第{i2 + 1}单元-第{i3 + 1}讲-{title}')
                                    self.view(id, False)
                if len(_json['directory'][i1].get('chapters')[i2].get('cells'))>0:
                    for i3 in _json['directory'][i1].get('chapters')[i2].get('cells'):
                        _title = i3['Title']
                        _id = i3['Id']
                        _status = i3['Status']
                        _type = i3['ResType'] #1是视频，2是，，，，，4是ppt text image
                        if _status !=1:
                            if _type == 1:

                                print(f'新事件-观看 第{i1 + 1}模块-第{i2 + 1}单元-{_title}')
                                self.view(_id, True)

                            elif _type == 4 :
                                print(f'新事件-观看 第{i1 + 1}模块-第{i2 + 1}单元-{_title}')
                                self.view(_id, False)
                        else: #已完成
                            print(f'已完成-跳过 第{i1 + 1}模块-第{i2 + 1}单元-{_title}')

        print('刷完啦,觉得好用的话就给个Star吧~')

    def view(self, cellId, timeStatus):
        data = {'cellId': cellId, 'courseId': self.courseId, 'enterType': 'study'}
        try:
            res = self.session.post('https://www.icve.com.cn/study/directory/view', headers=headers, data=data).json()
        except:
            res= self.session.post('https://www.icve.com.cn/study/directory/view', headers=headers, data=data)
            print("遇到错误",res)
        if timeStatus:
            self.updateStatus(cellId)
        else:
            sleepTime = random.randrange(minTime, maxTime)
            try:
                print('\t {} 等待 {}s 后继续'.format(res['msg'], sleepTime))
                time.sleep(sleepTime)
            except:

                print('\t {} 等待 {}s 后继续'.format(res['cell']['Title'], sleepTime))
                time.sleep(sleepTime)
    def updateStatus(self, cellId):
        sleepTime = random.randrange(minTime, maxTime)
        try:
            t = self.notWatched[cellId]
        except:
            t = random.randint(300, 600)
        data = {'cellId': cellId, 'learntime': t, 'status': 1}
        res = self.session.post('https://www.icve.com.cn/study/directory/updateStatus', data=data,
                                headers=headers).text
        if json.loads(res)['code'] != 1:
            print('添加时长失败')
        else:
            try:
                print('\t {} 等待 {}s 后继续'.format(json.loads(res)['msg'],sleepTime))
                time.sleep(sleepTime)
            except:
                print('\t {} 等待 {}s 后继续'.format(res['cell']['Title'], sleepTime))
                time.sleep(sleepTime)

    def answer(self, cellId):
        data1 = {'cellId': cellId, 'courseId': self.courseId, 'enterType': 'study'}
        res1 = self.session.post('https://www.icve.com.cn/study/directory/view', data=data1, headers=headers).text
        _json1 = json.loads(res1)
        workId = _json1['works'].get('Id')
        length = len(_json1["data"].get("paper").get("PaperQuestions"))
        print(f'\t获取到了{length}道试题')
        for i in range(len(_json1['data'].get('paper').get('PaperQuestions'))):
            timer = random.randrange(4, 10)
            print(f'\t\t等待{timer}s')
            time.sleep(timer)
            Id = _json1["data"].get("paper").get("PaperQuestions")[i].get('Id')
            Answers = _json1["data"].get("paper").get("PaperQuestions")[i].get('Answers')
            data2 = {'works': workId, 'paperItemId': Id, 'answer': Answers}
            res2 = self.session.post('https://www.icve.com.cn/study/directory/answerpaper', data=data2,
                                     headers=headers).text
            _json2 = json.loads(res2)
            if _json2['code'] == 1:
                print(f'\t\t{i + 1}/{length} 回答成功!')
            else:
                print(f'\t\t答题失败 {_json2["msg"]}')
        data3 = {'studentWorksId': workId}
        res3 = self.session.post('https://www.icve.com.cn/study/directory/subPaper', data=data3, headers=headers).text
        _json3 = json.loads(res3)
        if _json3['code'] == 1:
            print(f'\t提交成功!')
        else:
            print(f'\t\t提交失败 {_json3["msg"]}')


def toSec(text):
    _text = text
    _time = 0
    if len(_text.split('小时')) != 1:
        try:
            _time += int(_text.split('小时')[0]) * 60 * 60
            _text = text.split('小时')[1]
            _time += int(_text.split('分钟')[0]) * 60
            _text = _text.split('分钟')[1]
            _time += int(_text.split('秒')[0])
            _text = _text.split('秒')[1]
        except:pass
    elif len(text.split('分钟')) != 1:
        try:
            _time += int(_text.split('分钟')[0]) * 60
            _text = _text.split('分钟')[1]
            _time += int(_text.split('秒')[0])
            _text = _text.split('秒')[1]
        except:pass
    else:
        try:
            _time += int(_text.split('秒')[0])
            _text = _text.split('秒')[1]
        except:pass
    return _time


if __name__ == "__main__":
    a=Mooc()
    if a.finishAll :
        for i in range(1,a.classnum):
            print("正在进行",i,a.allclass[i].get('title'))
            a.courseId = a.allclass[i].get('id')
            a.getWatchTime()
            a.Run()
