# 一、简介
Python版本API基于Python版本win64 3.7.2，是用swig方法在官方C++ API上编译得到，完全开源，有兴趣自己编译的读者可以参考笔者[
CTP Python API及Demo（利用Swig 封装）Windows版（traderapi）](https://blog.csdn.net/pjjing/article/details/77338423)这篇博客。此方法编译得到的API在数据结构，函数名及用法上与C++版API完全一致，十分容易上手。调试请下载相同版本Python。

# 二、请求函数及数据结构
可以参见上期技术官网下载文档，所有函数名及数据结构都是一致的。
以登录为例，ReqUserLogin函数，CThostFtdcReqUserLoginField类型及其字段可以直接在文档中查到：  
官方C++版为：
```
CThostFtdcReqUserLoginField reqUserLogin = { 0 };
strcpy_s(reqUserLogin.BrokerID, “0000”);
strcpy_s(reqUserLogin.UserID, “00001”);
strcpy_s(reqUserLogin.Password, “123456”); 
m_pUserApi->ReqUserLogin(&reqUserLogin, nRequestID++);
```
Python版本为：
```
loginfield = api.CThostFtdcReqUserLoginField()
loginfield.BrokerID="0000"
loginfield.UserID="00001"
loginfield.Password="123456"
tradeapi.ReqUserLogin(loginfield,0)
```

# 三、回调函数及数据结构
Python版回调函数的参数是tuple结构，是将C++版回调函数的参数组合起来的tuple。以
```
def OnRspUserLogin(self, *args):
```
为例：
对应的C++版函数是：
```
virtual void OnRspUserLogin(CThostFtdcRspUserLoginField *pRspUserLogin, CThostFtdcRspInfoField *pRspInfo, int nRequestID, bool bIsLast)
```
其中args为tuple结构，是CThostFtdcRspUserLoginField，CThostFtdcRspInfoField，int，bool四个类型变量的组合。可以通过print (args)查看，如下：
```
(<thosttraderapi.CThostFtdcRspUserLoginField; proxy of <Swig Object of type 'CThostFtdcRspUserLoginField *' at 0x0000000002D26210> >,
<thosttraderapi.CThostFtdcRspInfoField; proxy of <Swig Object of type 'CThostFtdcRspInfoField *' at 0x0000000002DA3660> >, 
0, 
True)
```
所以，args[0]即是回调函数的第一个参数，在OnRspUserLogin函数中是CThostFtdcRspUserLoginField类型，这个类型的所有成员变量可以在文档中查到，也可直接用print (dir(args[0]))直接查看，如下：
```
['BrokerID', 
'CZCETime', 
'DCETime', 
'FFEXTime', 
'FrontID', 
'INETime', 
'LoginTime', 
'MaxOrderRef', 
'SHFETime', 
'SessionID',
'SystemName', 
'TradingDay',
'UserID', 
...]
```
于是可以使用print (args[0].TradingDay)输出该返回值的TradingDay变量值。
同样args[1]是CThostFtdcRspInfoField，这个类型返回的是对应的请求是否正确信息。

# 四、Demo及其用法
以Trade API为例，Python版CTP API有三个文件，thosttraderapi.py，_thosttraderapi.pyd及thosttraderapi.dll。其中第一个相当于头文件，第二个为包装动态库，第三个是CTP官方库。将td_demo.py文件直接拷贝到这三个文件的同一文件夹中，在命令行运行Python td_demo.py即可直接运行。  
td_demo.py实现了简单的登录，查询结算单，确认结算单并买开一手rb1909合约的功能。注意，要讲td_demo.py顶部的几个参数改为你自己测试环境参数。  
md_demo.py实现了订阅ru1909和rb1909两个合约的功能，可以修改SubscribeMarketData的参数订阅别的合约，同时也要注意修改底部的行情前置地址。

# 五、常见问题
## 1.出错直接退出
通常都是类型对象为None，却直接使用了该对象的成员变量。以查结算单为例，返回回调中，如果输出结算单内容通常直接写成：
```
def OnRspQrySettlementInfo(self, *args):
    print ("content:",args[0].Content)
```
这时如果查到结算单自然没有问题，如果查回结算单为空则直接出错退出，因为args[0]是None类型。所以正确写法应该先判断是否为空，写成如下：
```
def OnRspQrySettlementInfo(self, *args):
    if  args[0] is not None :
        print ("content:",args[0].Content)
```

## 2.待补充