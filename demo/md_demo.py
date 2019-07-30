# -*- coding: utf-8 -*-
import thostmduserapi as mdapi  

class CFtdcMdSpi(mdapi.CThostFtdcMdSpi):
    tapi=''
    def __init__(self,tapi):
        mdapi.CThostFtdcMdSpi.__init__(self)
        self.tapi=tapi
    def OnFrontConnected(self) -> "void":
        print ("OnFrontConnected")
        loginfield = mdapi.CThostFtdcReqUserLoginField()
        loginfield.BrokerID="8000"
        loginfield.UserID="000005"
        loginfield.Password="123456"
        loginfield.UserProductInfo="python dll"
        self.tapi.ReqUserLogin(loginfield,0)
    def OnRspUserLogin(self, pRspUserLogin: 'CThostFtdcRspUserLoginField', pRspInfo: 'CThostFtdcRspInfoField', nRequestID: 'int', bIsLast: 'bool') -> "void":
        print ("OnRspUserLogin")
        print ("SessionID=",pRspUserLogin.SessionID)
        print ("ErrorID=",pRspInfo.ErrorID)
        print ("ErrorMsg=",pRspInfo.ErrorMsg)
        ret=self.tapi.SubscribeMarketData([b"ru1909",b"rb1909",b"au1912",b"ag1912"],4)

    def OnRtnDepthMarketData(self, pDepthMarketData: 'CThostFtdcDepthMarketDataField') -> "void":
        print ("OnRtnDepthMarketData")
        print ("InstrumentID=",pDepthMarketData.InstrumentID)
        print ("LastPrice=",pDepthMarketData.LastPrice)

    def OnRspSubMarketData(self, pSpecificInstrument: 'CThostFtdcSpecificInstrumentField', pRspInfo: 'CThostFtdcRspInfoField', nRequestID: 'int', bIsLast: 'bool') -> "void":
        print ("OnRspSubMarketData")
        print ("InstrumentID=",pSpecificInstrument.InstrumentID)
        print ("ErrorID=",pRspInfo.ErrorID)
        print ("ErrorMsg=",pRspInfo.ErrorMsg)

def main():
    mduserapi=mdapi.CThostFtdcMdApi_CreateFtdcMdApi()
    mduserspi=CFtdcMdSpi(mduserapi)
    mduserapi.RegisterFront("tcp://101.230.209.178:53313")
    '''以下是7*24小时环境'''
    #mduserapi.RegisterFront("tcp://180.168.146.187:10131")
    mduserapi.RegisterSpi(mduserspi)
    mduserapi.Init()    
    mduserapi.Join()

if __name__ == '__main__':
    main()