import json
import base64
import requests
import time
import hashlib
# 作为全局变量
configDict={}

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
    global configDict
    head={'Authorization':'Basic %s'%configDict['auth']}
    res=requests.get('https://www.loocha.com.cn:8443/login',headers=head)
    did_id=json.loads(res.text)['user']['did'].split('#')[0]
    user_id=json.loads(res.text)['user']['id']
    configDict['id']=user_id
    configDict['server_id']=did_id
    with open('config.json','w') as f:
            json.dump(configDict,f)
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
    user_id=configDict['id']
    did_id=configDict['server_id']
    nowtime=str(int(time.time()*1000))

    params='&server_did=' + did_id + '&time=' + nowtime + '&type=1'
    sign = getMD5('mobile='+'17712918215'+ '&model='+'callmesp-PC'+params)
    res=requests.get('https://wifi.loocha.cn/'+user_id +'/wifi/telecom/pwd?1=Android_college_100.100.100'+'&mm='+'callmesp-PC'+params+'&sign='+sign,headers=head)
    resDict=json.loads(res.text)
    if resDict['status']=='0':
        return resDict['telecomWifiRes']['password']
    else:
        print('获取失败')
        return 0
    
def initial():
    global configDict
    res=requests.get('http://test.f-young.cn')
    realUrl=res.history[-1].url
    args=realUrl.split('?')[1].split('&')
    wan_ip=args[0].split('=')[1]
    bras_ip=args[1].split('=')[1]
    # 存储到config文件
    configDict['wan_ip']=wan_ip
    configDict['bras_ip']=bras_ip
    with open('config.json','w') as f:
            json.dump(configDict,f)


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
        print('获取失败')
        return 0

    
def realStart():
    rescode=int(doFirstVerify())
    if rescode==0:
        print('填写账号密码后重新尝试')
    elif rescode==1:
        print('账号或密码错误')
    elif rescode==2:#初步验证通过，下一步是登录
        loginChinaNet()

res=requests.get('http://test.f-young.cn')
print(res.history[-1].url)
realStart()