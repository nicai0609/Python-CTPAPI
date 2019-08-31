# -*- coding: utf-8 -*-
'''
@author : 景色
@csdn : https://blog.csdn.net/pjjing
@QQ群 : 767101469
@公众号 : QuantRoad2019
'''
import thostmduserapi as mdapi
import csv
'''
以下为需要订阅行情的合约号，注意选择有效合约；
有效连上但没有行情可能是过期合约或者不再交易时间内导致
'''
subID=["au1912","IC1909","i2001","TA001"]

class CFtdcMdSpi(mdapi.CThostFtdcMdSpi):

    def __init__(self,tapi):
        mdapi.CThostFtdcMdSpi.__init__(self)
        self.tapi=tapi
        self.csvfiles={}
        self.submap= {}
        
    def __openCsv(self):
        csvheader=(["TradingDay",\
        "InstrumentID",\
        "LastPrice",\
        "PreSettlementPrice",\
        "PreClosePrice",\
        "PreOpenInterest",\
        "OpenPrice",\
        "HighestPrice",\
        "LowestPrice",\
        "Volume",\
        "Turnover",\
        "OpenInterest",\
        "ClosePrice",\
        "SettlementPrice",\
        "UpperLimitPrice",\
        "LowerLimitPrice",\
        "PreDelta",\
        "CurrDelta",\
        "UpdateTime",\
        "UpdateMillisec",\
        "BidPrice1",\
        "BidVolume1",\
        "AskPrice1",\
        "AskVolume1",\
        "AveragePrice",\
        "ActionDay"])
        for id in subID:
            csvname=f"{id}.csv"
            csvfile=open(csvname,'w',newline='')
            csvfile_w=csv.writer(csvfile)
            csvfile_w.writerow(csvheader)
            self.csvfiles[id]=csvfile
            self.submap[id]=csvfile_w
            
    def OnFrontConnected(self) -> "void":
        print ("OnFrontConnected")
        loginfield = mdapi.CThostFtdcReqUserLoginField()
        loginfield.BrokerID="8000"
        loginfield.UserID="000005"
        loginfield.Password="123456"
        loginfield.UserProductInfo="python dll"
        self.tapi.ReqUserLogin(loginfield,0)
        self.__openCsv()
        
    def OnRspUserLogin(self, pRspUserLogin: 'CThostFtdcRspUserLoginField', pRspInfo: 'CThostFtdcRspInfoField', nRequestID: 'int', bIsLast: 'bool') -> "void":
        print (f"OnRspUserLogin, SessionID={pRspUserLogin.SessionID},ErrorID={pRspInfo.ErrorID},ErrorMsg={pRspInfo.ErrorMsg}")
        ret=self.tapi.SubscribeMarketData([id.encode('utf-8') for id in subID],len(subID))

    def OnRtnDepthMarketData(self, pDepthMarketData: 'CThostFtdcDepthMarketDataField') -> "void":
        print ("OnRtnDepthMarketData")        
        mdlist=([pDepthMarketData.TradingDay,\
        pDepthMarketData.InstrumentID,\
        pDepthMarketData.LastPrice,\
        pDepthMarketData.PreSettlementPrice,\
        pDepthMarketData.PreClosePrice,\
        pDepthMarketData.PreOpenInterest,\
        pDepthMarketData.OpenPrice,\
        pDepthMarketData.HighestPrice,\
        pDepthMarketData.LowestPrice,\
        pDepthMarketData.Volume,\
        pDepthMarketData.Turnover,\
        pDepthMarketData.OpenInterest,\
        pDepthMarketData.ClosePrice,\
        pDepthMarketData.SettlementPrice,\
        pDepthMarketData.UpperLimitPrice,\
        pDepthMarketData.LowerLimitPrice,\
        pDepthMarketData.PreDelta,\
        pDepthMarketData.CurrDelta,\
        pDepthMarketData.UpdateTime,\
        pDepthMarketData.UpdateMillisec,\
        pDepthMarketData.BidPrice1,\
        pDepthMarketData.BidVolume1,\
        pDepthMarketData.AskPrice1,\
        pDepthMarketData.AskVolume1,\
        pDepthMarketData.AveragePrice,\
        pDepthMarketData.ActionDay])
        print (mdlist)
        self.submap[pDepthMarketData.InstrumentID].writerow(mdlist)
        self.csvfiles[pDepthMarketData.InstrumentID].flush()

    def OnRspSubMarketData(self, pSpecificInstrument: 'CThostFtdcSpecificInstrumentField', pRspInfo: 'CThostFtdcRspInfoField', nRequestID: 'int', bIsLast: 'bool') -> "void":
        print ("OnRspSubMarketData")
        print ("InstrumentID=",pSpecificInstrument.InstrumentID)
        print ("ErrorID=",pRspInfo.ErrorID)
        print ("ErrorMsg=",pRspInfo.ErrorMsg)

def main():
    mduserapi=mdapi.CThostFtdcMdApi_CreateFtdcMdApi()
    mduserspi=CFtdcMdSpi(mduserapi)
    #mduserapi.RegisterFront("tcp://101.230.209.178:53313")
    '''以下是7*24小时环境'''
    mduserapi.RegisterFront("tcp://180.168.146.187:10131")
    mduserapi.RegisterSpi(mduserspi)
    mduserapi.Init()    
    mduserapi.Join()

if __name__ == '__main__':
    main()