# -*- coding: gbk -*-
import thosttraderapi as api
import time

def ReqorderfieldInsert(tradeapi):
	print ("ReqOrderInsert Start")
	orderfield=api.CThostFtdcInputOrderField()
	orderfield.BrokerID="9999"
	orderfield.InstrumentID="rb1905"
	orderfield.UserID="070624"
	orderfield.InvestorID="070624"
	orderfield.Direction=api.THOST_FTDC_D_Sell
	orderfield.LimitPrice=3200
	orderfield.VolumeTotalOriginal=1
	orderfield.OrderPriceType=api.THOST_FTDC_OPT_LimitPrice
	orderfield.ContingentCondition = api.THOST_FTDC_CC_Immediately
	orderfield.TimeCondition = api.THOST_FTDC_TC_GFD
	orderfield.VolumeCondition = api.THOST_FTDC_VC_AV
	orderfield.CombHedgeFlag="1"
	orderfield.CombOffsetFlag="0"
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
		#time.sleep( 60 )
		loginfield = api.CThostFtdcReqUserLoginField()
		loginfield.BrokerID="8000"
		loginfield.UserID="00001"
		loginfield.Password="00001"
		loginfield.UserProductInfo="python dll"
		self.tapi.ReqUserLogin(loginfield,0)
		print ("send login ok")
	def OnRspUserLogin(self, *args):
		print ("OnRspUserLogin")
		rsploginfield=args[0]
		rspinfofield=args[1]
		msg=args[2]
		print ("SessionID=",rsploginfield.SessionID)
		print ("ErrorID=",rspinfofield.ErrorID)
		print ("ErrorMsg=",rspinfofield.ErrorMsg.encode("utf-8",errors='surrogateescape').decode('gbk'))

		qryinfofield = api.CThostFtdcQrySettlementInfoField()
		qryinfofield.BrokerID="8000"
		qryinfofield.InvestorID="00001"
		self.tapi.ReqQrySettlementInfo(qryinfofield,0)
		print ("send ReqQrySettlementInfo ok")
		#ReqorderfieldInsert(self.tapi)

	def OnRspQrySettlementInfo(self, *args):
		print ("OnRspQrySettlementInfo")
		pSettlementInfo=args[0]
		print ("content:",pSettlementInfo.Content.encode("utf-8",errors='surrogateescape').decode('gbk'))


	def OnRtnOrder(self, *args):
		print ("OnRtnOrder")
		rtnfield=args[0]
		print ("OrderStatus=",rtnfield.OrderStatus)
		print ("StatusMsg=",rtnfield.StatusMsg.encode("utf-8",errors='surrogateescape').decode('gbk'))
		print ("LimitPrice=",rtnfield.LimitPrice)
		
	def OnRspOrderInsert(self, *args):
		print ("OnRspOrderInsert")
		rspinfofield=args[1]
		print ("ErrorID=",rspinfofield.ErrorID)
		print ("ErrorMsg=",rspinfofield.ErrorMsg.encode("utf-8",errors='surrogateescape').decode('gbk'))
		
def main():
	tradeapi=api.CThostFtdcTraderApi_CreateFtdcTraderApi()
	tradespi=CTradeSpi(tradeapi)
	tradeapi.RegisterFront("tcp://180.168.146.187:10030")
	#tradeapi.RegisterFront("tcp://172.24.125.199:50233")
	tradeapi.RegisterSpi(tradespi)
	tradeapi.SubscribePrivateTopic(api.THOST_TERT_RESUME)
	tradeapi.SubscribePublicTopic(api.THOST_TERT_RESUME)
	tradeapi.Init()
	tradeapi.Join()
	
if __name__ == '__main__':
	main()