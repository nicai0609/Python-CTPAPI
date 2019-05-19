# -*- coding: utf-8 -*-
import thosttraderapi as api

#Addr
#FrontAddr="tcp://180.168.146.187:10000"
FrontAddr="tcp://180.168.146.187:10030"
#LoginInfo
BROKERID="9999"
USERID="070624"
PASSWORD="123456"
#OrderInfo
INSTRUMENTID="rb1909"
PRICE=3200
VOLUME=1
DIRECTION=api.THOST_FTDC_D_Sell
#DIRECTION=api.THOST_FTDC_D_Buy
#open
OFFSET="0"
#close
#OFFSET="1"

def ReqorderfieldInsert(tradeapi):
	print ("ReqOrderInsert Start")
	orderfield=api.CThostFtdcInputOrderField()
	orderfield.BrokerID=BROKERID
	orderfield.InstrumentID=INSTRUMENTID
	orderfield.UserID=USERID
	orderfield.InvestorID=USERID
	orderfield.Direction=DIRECTION
	orderfield.LimitPrice=PRICE
	orderfield.VolumeTotalOriginal=VOLUME
	orderfield.OrderPriceType=api.THOST_FTDC_OPT_LimitPrice
	orderfield.ContingentCondition = api.THOST_FTDC_CC_Immediately
	orderfield.TimeCondition = api.THOST_FTDC_TC_GFD
	orderfield.VolumeCondition = api.THOST_FTDC_VC_AV
	orderfield.CombHedgeFlag="1"
	orderfield.CombOffsetFlag=OFFSET
	orderfield.GTDDate=""
	orderfield.orderfieldRef="1"
	orderfield.MinVolume = 0
	orderfield.ForceCloseReason = api.THOST_FTDC_FCC_NotForceClose
	orderfield.IsAutoSuspend = 0
	tradeapi.ReqOrderInsert(orderfield,0)
	print ("ReqOrderInsert End")
	

class CTradeSpi(api.CThostFtdcTraderSpi):
	tapi=''
	def __init__(self,tapi):
		api.CThostFtdcTraderSpi.__init__(self)
		self.tapi=tapi
		
	def OnFrontConnected(self):
		print ("OnFrontConnected")
		loginfield = api.CThostFtdcReqUserLoginField()
		loginfield.BrokerID=BROKERID
		loginfield.UserID=USERID
		loginfield.Password=PASSWORD
		loginfield.UserProductInfo="python dll"
		self.tapi.ReqUserLogin(loginfield,0)
		print ("send login ok")
	def OnRspUserLogin(self, *args):
		print ("OnRspUserLogin")
		rsploginfield=args[0]
		rspinfofield=args[1]
		msg=args[2]
		print ("TradingDay=",rsploginfield.TradingDay)
		print ("SessionID=",rsploginfield.SessionID)
		print ("ErrorID=",rspinfofield.ErrorID)
		print ("ErrorMsg=",rspinfofield.ErrorMsg)

		qryinfofield = api.CThostFtdcQrySettlementInfoField()
		qryinfofield.BrokerID=BROKERID
		qryinfofield.InvestorID=USERID
		qryinfofield.TradingDay=rsploginfield.TradingDay
		self.tapi.ReqQrySettlementInfo(qryinfofield,0)
		print ("send ReqQrySettlementInfo ok")
		

	def OnRspQrySettlementInfo(self, *args):
		print ("OnRspQrySettlementInfo")
		pSettlementInfo=args[0]
		if  pSettlementInfo is not None :
			print ("content:",pSettlementInfo.Content)
		pSettlementInfoConfirm=api.CThostFtdcSettlementInfoConfirmField()
		pSettlementInfoConfirm.BrokerID=BROKERID
		pSettlementInfoConfirm.InvestorID=USERID
		self.tapi.ReqSettlementInfoConfirm(pSettlementInfoConfirm,0)
		print ("send ReqSettlementInfoConfirm ok")
		
	def OnRspSettlementInfoConfirm(self, *args):
		print ("OnRspSettlementInfoConfirm")
		rspinfofield=args[1]
		print ("ErrorID=",rspinfofield.ErrorID)
		print ("ErrorMsg=",rspinfofield.ErrorMsg)
		ReqorderfieldInsert(self.tapi)
		print ("send ReqorderfieldInsert ok")


	def OnRtnOrder(self, *args):
		print ("OnRtnOrder")
		rtnfield=args[0]
		print ("OrderStatus=",rtnfield.OrderStatus)
		print ("StatusMsg=",rtnfield.StatusMsg)
		print ("LimitPrice=",rtnfield.LimitPrice)
		
	def OnRspOrderInsert(self, *args):
		print ("OnRspOrderInsert")
		rspinfofield=args[1]
		print ("ErrorID=",rspinfofield.ErrorID)
		print ("ErrorMsg=",rspinfofield.ErrorMsg)
		
def main():
	tradeapi=api.CThostFtdcTraderApi_CreateFtdcTraderApi()
	tradespi=CTradeSpi(tradeapi)
	tradeapi.RegisterFront(FrontAddr)
	tradeapi.RegisterSpi(tradespi)
	tradeapi.SubscribePrivateTopic(api.THOST_TERT_QUICK)
	tradeapi.SubscribePublicTopic(api.THOST_TERT_QUICK)
	tradeapi.Init()
	tradeapi.Join()
	
if __name__ == '__main__':
	main()