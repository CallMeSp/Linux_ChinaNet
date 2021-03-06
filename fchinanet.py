#! /usr/bin/python3
# test1.0
import json
import base64
import requests
import time
import hashlib
import re
import socket
# 作为全局变量
configDict={}

def initial():
    global configDict
    with open('config.json','r') as f:
        configDict=json.load(f)
    res=requests.get('http://test.f-young.cn')
    #!!!!!!这里的list可能长度为0，会溢出....
    if len(res.history)>0:
        realUrl=res.history[-1].url
        print(realUrl)
        args=realUrl.split('?')[1].split('&')
        wan_ip=args[0].split('=')[1]
        bras_ip=args[1].split('=')[1]
        # 存储到config文件
        configDict['wan_ip']=wan_ip
        configDict['bras_ip']=bras_ip
        with open('config.json','w') as f:
            json.dump(configDict,f) 

def getAppVersion():
    res=requests.get('http://pre.f-young.cn/js/conf.js')
    pattern=re.compile(r'\d\.\d\.\d')
    version=pattern.search(res.text).group()
    app_version='Android_college_'+version
    return app_version

def get8bin(s):
    rawLenth=len(s)
    result=''
    for i in range(8-rawLenth):
        result+='0'
    result+=s
    return result

def getUserId():
    global configDict
    # 先转化为bytes
    rawStr=configDict['account']+':'+configDict['passwd']
    bytesAuth=rawStr.encode(encoding='utf-8')
    # base64编码
    Auth=str(base64.b64encode(bytesAuth),'utf-8')
    head=head={'Authorization':'Basic %s'%Auth}

    res=requests.get('https://cps.loocha.cn:9607/anony/login?1=%s'%getAppVersion(),headers=head,stream=True)
    bufferstr=str(res.raw.read())

    b1=bufferstr[16:18]
    b2=bufferstr[20:22]
    b3=bufferstr[24:26]
    b4=bufferstr[28:30]

    A=get8bin(bin(int(b4,16))[2:])[1:]
    B=get8bin(bin(int(b3,16))[2:])[1:]
    C=get8bin(bin(int(b2,16))[2:])[1:]
    D=get8bin(bin(int(b1,16))[2:])[1:]

    USER_ID=str(int(A+B+C+D,2))
    return USER_ID

def doFirstVerify():
    global configDict
    with open('config.json','r') as f:
        configDict=json.load(f)
        
    if ('account' in configDict.keys())&('passwd' in configDict.keys()):
        if (configDict['account']=='')|(configDict['passwd']==''):
            # 需要先填写密码
            return 0
    if 'auth' not in configDict.keys():
        # 先转化为bytes
        rawStr=configDict['account']+':'+configDict['passwd']
        bytesAuth=rawStr.encode(encoding='utf-8')
        # base64编码
        Auth=str(base64.b64encode(bytesAuth),'utf-8')
        
        head=head={'Authorization':'Basic %s'%Auth}
        res=requests.get('https://www.loocha.com.cn:8443/login',headers=head)
        if res.status_code!=200:
            # 密码错误
            return 1
        did_id=json.loads(res.text)['user']['did'].split('#')[0]
        user_id=json.loads(res.text)['user']['id']
        configDict['id']=user_id
        configDict['server_id']=did_id
        configDict['auth']=Auth
        del(configDict['account'])
        del(configDict['passwd'])
        with open('config.json','w') as f:
            json.dump(configDict,f)
        print('验证成功添加账户成功')
        # 成功
    return 2

def loginChinaNet():
    # global configDict
    # head={'Authorization':'Basic %s'%configDict['auth']}
    # res=requests.get('https://www.loocha.com.cn:8443/login',headers=head)
    # did_id=json.loads(res.text)['user']['did'].split('#')[0]
    # user_id=json.loads(res.text)['user']['id']
    # configDict['id']=user_id
    # configDict['server_id']=did_id
    # with open('config.json','w') as f:
    #         json.dump(configDict,f)
    doOnline()

def doOnline():
    global configDict
    head={'Authorization':'Basic %s'%configDict['auth']}
    user_id=configDict['id']
    nowtime=str(int(time.time()*1000))

    passWd=getPwd()
    print('本次登录密码为：',passWd)
    Qrcode=getQr()
    print('本次QrCode为：',Qrcode)

    
    params='&server_did='+configDict['server_id']+'&time='+nowtime+'&type=1'
    sign = getMD5('mobile='+'17712918215'+ '&model='+'callmesp-PC'+params)
    param = "1=Android_college_100.100.100&qrcode=" + Qrcode + "&code=" + passWd + "&type=1" + "&mm=" + 'callmesp-PC' + "&server_did=" + configDict['server_id'] + "&time=" + nowtime + "&sign=" + sign
    res=requests.post('https://wifi.loocha.cn/' + user_id + '/wifi/telecom/auto/login?' + param,headers=head)
    
    resDict=json.loads(res.text)
    if resDict.get('status')=='0':
        print('连接成功')
    else:
        print('连接失败')

    
def getMD5(rawStr):
    myMd5=hashlib.md5()
    myMd5.update(rawStr.encode('utf-8'))
    result=myMd5.hexdigest()
    return result.upper()

def getPwd():
    global configDict
    head={'Authorization':'Basic %s'%configDict['auth']}
    # user_id=configDict['id']
    user_id='2364100'
    # did_id=configDict['server_id']
    did_id='0'
    nowtime=str(int(time.time()*1000))

    params='&server_did=' + did_id + '&time=' + nowtime + '&type=1'
    sign = getMD5('mobile='+'17712918215'+ '&model='+'callmesp-PC'+params)
    res=requests.get('https://wifi.loocha.cn/'+user_id +'/wifi/telecom/pwd?1=Android_college_100.100.100'+'&mm='+'callmesp-PC'+params+'&sign='+sign,headers=head)
    resDict=json.loads(res.text)
    if resDict['status']=='0':
        return resDict['telecomWifiRes']['password']
    else:
        print('获取失败:'+resDict)
        return 0
    


def getQr():
    global configDict
    initial()
    # 暂时还没有写直接读取文件不用initial
    wan_ip=configDict['wan_ip']
    bras_ip=configDict['bras_ip']

    res=requests.get('https://wifi.loocha.cn/0/wifi/qrcode?brasip=%s&ulanip=%s&wlanip=%s'%(bras_ip,wan_ip,wan_ip))
    resDict=json.loads(res.text)

    if resDict['status']=='0':
        return resDict['telecomWifiRes']['password']
    else:
        print('获取失败:',resDict)
        return 0

    
def realStart():
    rescode=int(doFirstVerify())
    if rescode==0:
        print('填写账号密码后重新尝试')
    elif rescode==1:
        print('账号或密码错误')
    elif rescode==2:#初步验证通过，下一步是登录
        loginChinaNet()
        
def str2hex(s):
    return ' '.join([hex(ord(c)).replace('0x','') for c in s])

def str2bin(s):
    return ''.join([bin(ord(c)).replace('0b','') for c in s])

def bin2str(s):
    return ''.join([chr(i) for i in [int(b,2) for b in s.split(' ')]])

def bin2dec(s):
    return int(s,2)

def getPwdtest():
    # 以下是临时测试数据...
    global configDict
    # 先转化为bytes
    rawStr=configDict['account']+':'+configDict['passwd']
    bytesAuth=rawStr.encode(encoding='utf-8')
    # base64编码
    Auth=str(base64.b64encode(bytesAuth),'utf-8')
    head={'Authorization':'Basic %s'%Auth}
    user_id=getUserId()
    did_id='0'
    APP_VERSION= getAppVersion()
    MODEL=socket.gethostname()
    # ..................

    nowtime=str(int(time.time()*1000))
    params='&server_did=' + did_id + '&time=' + nowtime + '&type=1'
    sign = getMD5('mobile='+configDict['account']+ '&model='+MODEL+params)
    res=requests.get('https://wifi.loocha.cn/%s/wifi/telecom/pwd?1=%s&%s&sign=%s&mm=%s'%(user_id,APP_VERSION,params,sign,MODEL),headers=head)
    resDict=json.loads(res.text)
    if resDict['status']=='0':
        print('code:'+resDict['telecomWifiRes']['password'])
        return resDict['telecomWifiRes']['password']
    else:
        print('pwd获取失败',resDict)
        return '823144'

def getQrtest():
    # 以下是临时测试数据...
    user_id=getUserId()
    MODEL=socket.gethostname()
    did_id='0'
    wan_ip=configDict['wan_ip']
    bras_ip=configDict['bras_ip']
    APP_VERSION= getAppVersion()
    # ..................
    res=requests.get('https://wifi.loocha.cn/0/wifi/qrcode?1=%s&brasip=%s&ulanip=%s&wlanip=%s&mm=default'%(APP_VERSION,bras_ip,wan_ip,wan_ip))
    resDict=json.loads(res.text)

    if resDict['status']=='0':
        print('qrcode:'+resDict['telecomWifiRes']['password'])
        return resDict['telecomWifiRes']['password']
    else:
        print('qr获取失败')
        return 0

def doOnlineTest():
    # 以下是临时测试数据...
    global configDict
    # 先转化为bytes
    rawStr=configDict['account']+':'+configDict['passwd']
    bytesAuth=rawStr.encode(encoding='utf-8')
    # base64编码
    Auth=str(base64.b64encode(bytesAuth),'utf-8')
    head={'Authorization':'Basic %s'%Auth}
    user_id=getUserId()
    MODEL=socket.gethostname()
    did_id='0'
    wan_ip=configDict['wan_ip']
    bras_ip=configDict['bras_ip']
    APP_VERSION= getAppVersion()
    # ..................
    nowtime=str(int(time.time()*1000))
    params='&server_did=' + did_id + '&time=' + nowtime + '&type=1'
    sign = getMD5('mobile='+configDict['account']+ '&model='+MODEL+params)
    PARAM='1=%s&qrcode=%s&code=%s&mm=%s&%s&sign=%s&type=1&server_did=%s&time=%s'%(APP_VERSION,getQrtest(),getPwdtest(),MODEL,params,sign,did_id,nowtime)
    finalUrl='https://wifi.loocha.cn/%s/wifi/telecom/auto/login?%s'%(user_id,PARAM)
    res=requests.post(finalUrl,headers=head)
    print(res.text)

initial()
doOnlineTest()