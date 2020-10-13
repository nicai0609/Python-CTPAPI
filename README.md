# 一、简介
此CTP Python API在windows上由于Python3.X系列互不兼容，所以分别编译了Python3.7和Python3.8的版本，windows上使用时请务必安装对应Python版本，linux上无此问题。该API是用swig方法在官方C++ API上编译得到，完全开源，有兴趣自己编译的读者windows64版可以参考笔者[
CTP Python API及Demo（利用Swig封装）Windows版（traderapi）](https://blog.csdn.net/pjjing/article/details/77338423)这篇博客，Linux版只需要参考笔者其他博客，更改下makefile即可。此方法编译得到的API在数据结构，参数名，函数名及用法上与C++版API完全一致，十分容易上手。  
**编译维护不易，欢迎star，fork鼓励。**

# 二、文件清单
```
.
|-- 6.3.19_API接口说明_20200511.chm //官方文档，也可至http://www.sfit.com.cn/下载(加了日期便于区别版本)
|-- demo  //相关demo，见下面章节详述
|   |-- calculate_volume_delta.py
|   |-- candle_demo.py
|   |-- md_demo.py
|   |-- td_demo(auth).py
|   `-- td_demo.py
|-- LICENSE
|-- README.md  //本文档
|-- v6.3.19_P1_20200106   //CTP生产版本，用于正式交易或连simnow
|   |-- linux   //linux下版本（不区分Python3.X系列，通用）
|   |   |-- libthostmduserapi_se.so
|   |   |-- libthosttraderapi_se.so
|   |   |-- thostmduserapi.py
|   |   |-- _thostmduserapi.so
|   |   |-- thosttraderapi.py
|   |   `-- _thosttraderapi.so
|   `-- win64   //windows下版本，由于Python3.7和Python3.8不兼容，现同时提供两种
|       |-- py37 //Python3.7版本
|       |   |-- _thostmduserapi.pyd   //交易库转换文件
|       |   `-- _thosttraderapi.pyd   //交易库转换文件
|       |-- py38 //Python3.8版本
|       |   |-- _thostmduserapi.pyd
|       |   `-- _thosttraderapi.pyd
|       |-- thostmduserapi.py      //行情头文件（以下4个文件对于Python3.7和Python3.8版本是共用的）
|       |-- thostmduserapi_se.dll  //行情官方动态库
|       |-- thosttraderapi.py      //交易头文件
|       `-- thosttraderapi_se.dll  //交易官方动态库
`-- v6.3.19_T1_20200423  //CTP评测版本，用于穿透式认证评测，文件内容具体同上说明
    |-- linux
    |   |-- libthostmduserapi_se.so
    |   |-- libthosttraderapi_se.so
    |   |-- thostmduserapi.py
    |   |-- _thostmduserapi.so
    |   |-- thosttraderapi.py
    |   `-- _thosttraderapi.so
    `-- win64
        |-- py37
        |   |-- _thostmduserapi.pyd
        |   `-- _thosttraderapi.pyd
        |-- py38
        |   |-- _thostmduserapi.pyd
        |   `-- _thosttraderapi.pyd
        |-- thostmduserapi.py
        |-- thostmduserapi_se.dll
        |-- thosttraderapi.py
        `-- thosttraderapi_se.dll
```
# 三、请求函数及数据结构
所有函数名、参数及参数数据结构都是与官方```C++```版一致的，可以参见上期技术官网文档。以登录请求为例：  
官方C++版：  
函数名
```
virtual int ReqUserLogin(CThostFtdcReqUserLoginField *pReqUserLoginField, int nRequestID) = 0;
```
调用方法
```
CThostFtdcReqUserLoginField reqUserLogin = { 0 };
strcpy_s(reqUserLogin.BrokerID, “0000”);
strcpy_s(reqUserLogin.UserID, “00001”);
strcpy_s(reqUserLogin.Password, “123456”); 
m_pUserApi->ReqUserLogin(&reqUserLogin, nRequestID++);
```
Python版：  
函数名
```
def ReqUserLogin(self, pReqUserLoginField: 'CThostFtdcReqUserLoginField', nRequestID: 'int') -> "int":
```
调用方法
```
loginfield = api.CThostFtdcReqUserLoginField()
loginfield.BrokerID="0000"
loginfield.UserID="00001"
loginfield.Password="123456"
tradeapi.ReqUserLogin(loginfield,0)
```
所有的函数名均可以在相应头文件底部```class CThostFtdcTraderApi```和```class CThostFtdcMdApi```中查到，函数声明中自带了参数类型，参数结构直接在头文件中搜索就可以。至于对应的函数怎么用，请参考附带官方文档。以登录为例，找到文档中
```
/6.3.15_API接口说明/交易接口/CThostFtdcTraderApi/ReqUserLogin
```
这里面写的非常清楚。


# 四、回调函数及数据结构
所有函数名、参数及参数数据结构都是与官方```C++```版一致的，可以参见上期技术官网文档。以登录响应为例： 
官方C++版：  
函数名
```
virtual void OnRspUserLogin(CThostFtdcRspUserLoginField *pRspUserLogin, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {};
```
调用方法为继承该函数所在类，重写该函数调用。  
Python版：  
函数名
```
def OnRspUserLogin(self, pRspUserLogin: 'CThostFtdcRspUserLoginField', pRspInfo: 'CThostFtdcRspInfoField', nRequestID: 'int', bIsLast: 'bool') -> "void":
```
调用方法同样是继承所在CThostFtdcTraderSpi类，重写该函数，实现自己需要的逻辑。  
所有的函数名均可以在头文件底部```class CThostFtdcTraderSpi```和```class CThostFtdcMdSpi```中查到，函数名中自带了参数类型，参数结构直接在头文件中搜索就可以。

# 五、Demo及其用法
将td_demo(auth).py文件直接拷贝到API库交易相关文件(3个)同一文件夹中，切换到该目录运行Python td_demo(auth).py即可直接运行。此时如下几个文件应该在一个文件夹底下：
```
.
|-- _thosttraderapi.pyd
|-- td_demo(auth).py
|-- thosttraderapi.py
`-- thosttraderapi_se.dll
```
md_demo.py用法相同。

- td_demo.py实现了简单的登录，查询结算单，确认结算单并买开一手rb1909合约的功能。注意，要将td_demo.py顶部的几个参数改为你自己测试环境参数；合约过期的话要换成非过期合约。  
- md_demo.py实现了订阅"au1912","IC1909","i2001","TA001"这4个合约的功能，并将收取行情存入csv，可以修改subID列表订阅别的合约，同时也要注意修改底部的行情前置地址。
- td_demo(auth).py实现了加入认证功能后的登录报单等功能，适用于正式生产上。
- candle_demo.py实现了绘制K线图数据功能

# 六、常见问题
## 1. 运行时“ImportError: DLL load failed: 找不到指定的模块” 

首先确认运行的python版本，运行`python -V`，确保是对应的Python版本（目前仅支持Python3.7和Python3.8版本）。如果版本没有问题，windows上搜索“微软常用运行库合集64位” 安装，linux上确保so所在目录在环境变量LD_LIBRARY_PATH中。

## 2.出错直接退出

通常都是类型对象为None，却直接使用了该对象的成员变量。以查结算单为例，返回回调中，如果输出结算单内容通常直接写成：
```
def OnRspQrySettlementInfo(self, pSettlementInfo: 'CThostFtdcSettlementInfoField', pRspInfo: 'CThostFtdcRspInfoField', nRequestID: 'int', bIsLast: 'bool') -> "void":
    print ("content:",pSettlementInfo.Content)
```
这时如果查到结算单自然没有问题，但如果查回结算单为空则直接出错退出，因为pSettlementInfo是None类型。所以正确写法应该先判断是否为空，写成如下：
```
def OnRspQrySettlementInfo(self, pSettlementInfo: 'CThostFtdcSettlementInfoField', pRspInfo: 'CThostFtdcRspInfoField', nRequestID: 'int', bIsLast: 'bool') -> "void":
    if  pSettlementInfo is not None :
        print ("content:",pSettlementInfo.Content)
```

## 3.API调用init后为啥没有任何反应（demo运行没有任何反应或者没有OnFrontConnected回调）？
先检查网络链路是否畅通，可以telnet一下CTP前置地址，是否通畅。再检查API版本是否正确，**连生产或者simnow现必须是v6.3.19_P1_20200106版本api，评测请用v6.3.19_T1_20200423**。

## 4.运行mddemo没有收到行情？
请参考[CTP程序化交易入门系列之四：行情订阅常见问题解答](https://blog.csdn.net/pjjing/article/details/100532276)这篇博客

# 七、欢迎交流
欢迎扫二维码关注或者搜索程序化交易入门(QuantRoad2019)，一起学习程序化交易！  
![image](https://img-blog.csdnimg.cn/20190520205748924.jpg?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3lpc2h1aWhhbjEyMTI=,size_16,color_FFFFFF,t_70)

QQ交流群（767101469），一起讨论程序化交易！  
![image](https://img-blog.csdnimg.cn/20191005173130764.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3lpc2h1aWhhbjEyMTI=,size_16,color_FFFFFF,t_70)
