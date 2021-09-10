# -*- coding: utf-8 -*-
import thosttraderapi as api
import time, re

# Addr交易服务器地址
FrontAddr = "tcp://218.202.237.33 :10102"
# LoginInfo
BROKERID = "9999"
USERID = "171525"
PASSWORD = "1234qwer@"
AppID="simnow_client_test"
AuthCode="0000000000000000"

#查资金
def ReqQryTradingAccount(self):
    print("启动资金查询：")
    pQryTradingAccount=api.CThostFtdcQryTradingAccountField()
    pQryTradingAccount.BrokerID=self.BrokerID
    pQryTradingAccount.InvestorID=self.UserID
    pQryTradingAccount.CurrencyID="CNY"
    self.tapi.ReqQryTradingAccount(pQryTradingAccount,0)

# def ReqQryInstrument(self):
#     pQryInstrument = api.CThostFtdcQryInstrumentField()
#     self.tapi.ReqQryInstrument(pQryInstrument, 0)


class CTradeSpi(api.CThostFtdcTraderSpi):
    def __init__(self, tapi, BrokerID, UserID, PassWord, AppID, AuthCode):
        api.CThostFtdcTraderSpi.__init__(self)
        self.tapi = tapi
        self.BrokerID = BrokerID
        self.UserID = UserID
        self.AppID = AppID
        self.AuthCode = AuthCode
        self.PassWord = PassWord
        self.AppID = AppID
        self.AuthCode = AuthCode
        # 持仓
        self.position = {}
        # 报单
        self.order = {}
        # 成交
        self.trade = {}
        # 报单,成交关联字典
        self.order_trade = {}
        # 资金
        self.account = {}
        self.temp = []
        # self.nRequestID=0
        # 合约-交易所
        self.symbol = {}
        # 合约乘数
        self.symbol_v = {}

        # 缓存唯一id  md5 对应 OrderLocalID
        self.md5_Localid = {}

        # 缓存OrderLocalID 对应 唯一 id
        self.Localid_md5 = {}

        self.temp_id = []
        print(tapi, BrokerID, UserID, PassWord, AppID, AuthCode)
        self.temp_closep = {}

    # 默认第一次启动后回调
    def OnFrontConnected(self) -> "void":
        print("OnFrontConnected")
        self.init_start = None
        authfield = api.CThostFtdcReqAuthenticateField()
        authfield.BrokerID = self.BrokerID
        authfield.UserID = self.UserID
        authfield.AppID = self.AppID
        authfield.AuthCode = self.AuthCode

        # 客户端认证请求  需要填入用户名和穿透appid 和穿透认证码
        self.tapi.ReqAuthenticate(authfield, 0)
        # print ("send ReqAuthenticate ok")
        print("启动回调,开始穿透验证")
        # d={x:getattr(authfield, x) for x in dir(authfield)}
        # print(d)

    # 返回穿透验证结构体和是否穿透验证成功
    def OnRspAuthenticate(self, pRspAuthenticateField: 'CThostFtdcRspAuthenticateField',
                          pRspInfo: 'CThostFtdcRspInfoField', nRequestID: 'int', bIsLast: 'bool') -> "void":
        print("BrokerID=", pRspAuthenticateField.BrokerID)
        print("UserID=", pRspAuthenticateField.UserID)
        print("AppID=", pRspAuthenticateField.AppID)
        print("AppType=", pRspAuthenticateField.AppType)
        print("ErrorID=", pRspInfo.ErrorID)
        print("ErrorMsg=", pRspInfo.ErrorMsg)
        if not pRspInfo.ErrorID:
            print("验证穿透已完成,开始登录")
            loginfield = api.CThostFtdcReqUserLoginField()
            loginfield.BrokerID = self.BrokerID
            loginfield.UserID = self.UserID
            loginfield.Password = self.PassWord
            loginfield.UserProductInfo = "python dll"
            # 请求账户登录
            time.sleep(2)
            self.tapi.ReqUserLogin(loginfield, 0)
            print("send login ok")

    # 返回登录是否成功
    def OnRspUserLogin(self, pRspUserLogin: 'CThostFtdcRspUserLoginField', pRspInfo: 'CThostFtdcRspInfoField',
                       nRequestID: 'int', bIsLast: 'bool') -> "void":
        print("OnRspUserLogin")
        print("TradingDay=", pRspUserLogin.TradingDay)
        print("SessionID=", pRspUserLogin.SessionID)
        print("ErrorID=", pRspInfo.ErrorID)
        print("ErrorMsg=", pRspInfo.ErrorMsg)

        qryinfofield = api.CThostFtdcQrySettlementInfoField()
        qryinfofield.BrokerID = self.BrokerID
        qryinfofield.InvestorID = self.UserID
        qryinfofield.TradingDay = pRspUserLogin.TradingDay
        # 查询当然结算和历史结算接口
        time.sleep(2)
        self.tapi.ReqQrySettlementInfo(qryinfofield, 0)
        # print ("send ReqQrySettlementInfo ok")
        print("开始确认历史结算")

    # 返回历史结算接口
    def OnRspQrySettlementInfo(self, pSettlementInfo: 'CThostFtdcSettlementInfoField',
                               pRspInfo: 'CThostFtdcRspInfoField', nRequestID: 'int', bIsLast: 'bool') -> "void":
        print("OnRspQrySettlementInfo")
        if pSettlementInfo is not None:
            print("content:", pSettlementInfo.Content)
        else:
            print("content null")
        pSettlementInfoConfirm = api.CThostFtdcSettlementInfoConfirmField()
        pSettlementInfoConfirm.BrokerID = self.BrokerID
        pSettlementInfoConfirm.InvestorID = self.UserID
        # 自动确认历史结算接口
        time.sleep(1.2)
        self.tapi.ReqSettlementInfoConfirm(pSettlementInfoConfirm, 0)
        print("send ReqSettlementInfoConfirm ok")

    # 确认历史结算接口

    def OnRspSettlementInfoConfirm(self, pSettlementInfoConfirm: 'CThostFtdcSettlementInfoConfirmField',
                                   pRspInfo: 'CThostFtdcRspInfoField', nRequestID: 'int', bIsLast: 'bool') -> "void":
        print("OnRspSettlementInfoConfirm")
        print("ErrorID=", pRspInfo.ErrorID)
        print("ErrorMsg=", pRspInfo.ErrorMsg)
        # ReqorderfieldInsert(self.tapi)
        print("send ReqorderfieldInsert ok")
        time.sleep(2)
        ReqQryTradingAccount(self)
        # time.sleep(10)

        # 资金返回
    def OnRspQryTradingAccount(self, pTradingAccount: "CThostFtdcTradingAccountField",
                               pRspInfo: "CThostFtdcRspInfoField", nRequestID: "int", bIsLast: "bool"):
        # d={ x: getattr(pTradingAccount, x) for x in dir(pTradingAccount) if x[0]!="_"}
        # for x in b:
        #     if x[0]!="_":
        #         d={x:getattr(pTradingAccount, x)}
        a = {"pre_balance": pTradingAccount.PreBalance,
             "static_balance": pTradingAccount.PreBalance + pTradingAccount.Deposit - pTradingAccount.Withdraw,
             "balance": pTradingAccount.Balance,
             "available": pTradingAccount.Available,
             "ctp_balance": pTradingAccount.Balance,
             "ctp_available": pTradingAccount.Available,
             "float_profit": 0,
             "position_profit": pTradingAccount.PositionProfit,
             "close_profit": pTradingAccount.CloseProfit,
             "frozen_margein": pTradingAccount.FrozenMargin,
             "margin": pTradingAccount.CurrMargin,
             "frozen_commission": pTradingAccount.FrozenCommission,
             "commission": pTradingAccount.Commission,
             "risk_ratio": 0
             }
        # self.account.update(a)
        # self.queue.put({"user": self.UserID, "account": self.account})
        print("账户资金：")
        print(a)
        # ReqQryInstrument(self)

    # # 合约返回
    # def OnRspQryInstrument(self, pInstrument: "CThostFtdcInstrumentField", pRspInfo: "CThostFtdcRspInfoField",
    #                        nRequestID: "int", bIsLast: "bool"):
    #     self.symbol[pInstrument.InstrumentID] = pInstrument.ExchangeID
    #     self.symbol_v[pInstrument.InstrumentID] = pInstrument.VolumeMultiple



def main():
    tradeapi = api.CThostFtdcTraderApi_CreateFtdcTraderApi()
    tradespi = CTradeSpi(tradeapi, BROKERID, USERID, PASSWORD, AppID, AuthCode)
    tradeapi.RegisterFront(FrontAddr)
    tradeapi.RegisterSpi(tradespi)
    tradeapi.SubscribePrivateTopic(api.THOST_TERT_QUICK)
    tradeapi.SubscribePublicTopic(api.THOST_TERT_QUICK)
    tradeapi.Init()
    tradeapi.Join()


if __name__ == '__main__':
    main()