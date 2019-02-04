# -*- coding: gbk -*-
import thostmduserapi as mdapi  

class CFtdcMdSpi(mdapi.CThostFtdcMdSpi):
    tapi=''
    def __init__(self,tapi):
        mdapi.CThostFtdcMdSpi.__init__(self)
        self.tapi=tapi
    def OnFrontConnected(self):
        print ("OnFrontConnected")
        loginfield = mdapi.CThostFtdcReqUserLoginField()
        loginfield.BrokerID="8000"
        loginfield.UserID="000005"
        loginfield.Password="123456"
        loginfield.UserProductInfo="python dll"
        self.tapi.ReqUserLogin(loginfield,0)
    def OnRspUserLogin(self, *args):
        print ("OnRspUserLogin")
        rsploginfield=args[0]
        rspinfofield=args[1]
        print ("SessionID=",rsploginfield.SessionID)
        print ("ErrorID=",rspinfofield.ErrorID)
        print ("ErrorMsg=",rspinfofield.ErrorMsg)
        ret=self.tapi.SubscribeMarketData([b"ru1905",b"rb1905"],2)

    def OnRtnDepthMarketData(self, *args):
        print ("OnRtnDepthMarketData")
        field=args[0]
        print ("InstrumentID=",field.InstrumentID)
        print ("LastPrice=",field.LastPrice)

def main():
    mduserapi=mdapi.CThostFtdcMdApi_CreateFtdcMdApi()
    mduserspi=CFtdcMdSpi(mduserapi) 
    mduserapi.RegisterFront("tcp://180.168.146.187:10031")
    mduserapi.RegisterSpi(mduserspi)
    mduserapi.Init()    
    mduserapi.Join()

if __name__ == '__main__':
    main()