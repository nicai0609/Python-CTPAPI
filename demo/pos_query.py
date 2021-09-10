'''
# 作者    ： 张莹潇
# 创建时间 ： 20/11/23 10:11
'''
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

def ReqQryInvestorPosition(tradeapi, BrokerID, UserID, InstrumentID):
    #print(555555555555)
    pQryInvestorPosition = api.CThostFtdcQryInvestorPositionField()
    pQryInvestorPosition.BrokerID = BrokerID
    pQryInvestorPosition.InvestorID = UserID
    pQryInvestorPosition.InstrumentID = InstrumentID
    tradeapi.ReqQryInvestorPosition(pQryInvestorPosition,0)

def ReqQryInstrument(tradeapi):
    print("启动持仓查询：")
    pQryInstrument = api.CThostFtdcQryInstrumentField()
    tradeapi.ReqQryInstrument(pQryInstrument, 0)


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
        # ReqQryInstrument(self.tapi)
        # time.sleep(2)
        # ReqQryInvestorPosition(self)

    # 持仓返回
    def OnRspQryInvestorPosition(self, pInvestorPosition: "CThostFtdcInvestorPositionField ",
                                 pRspInfo: "CThostFtdcRspInfoField", nRequestID: "int", bIsLast: "bool"):
        # #t1=time.time()
        # print("------------开始--------")
        # d={ x: getattr(pInvestorPosition, x) for x in dir(pInvestorPosition) if x[0]!="_"}
        # for x in d:
        #     print(x,d[x])
        # print("-----------结束--------")
        # # print(pInvestorPosition)
        try:
            if pInvestorPosition is None:
                pass
            else:
                symbol = self.symbol[pInvestorPosition.InstrumentID] + "." + pInvestorPosition.InstrumentID
                if symbol not in self.position:
                    self.position[symbol] = {"exchange_id": self.symbol[pInvestorPosition.InstrumentID],
                                             "instrument_id": pInvestorPosition.InstrumentID,
                                             'pos_long_his': 0,
                                             "pos_long_today": 0,
                                             "pos_short_his": 0,
                                             "pos_short_today": 0,
                                             "open_price_long": 0,
                                             "open_price_short": 0,
                                             "position_price_long": 0,
                                             "position_price_short": 0,
                                             "position_cost_long": 0,
                                             "position_cost_short": 0,
                                             "float_profit_long": 0,
                                             "float_profit_short": 0,
                                             "float_profit": 0,
                                             "position_profit_long": 0,
                                             "position_profit_short": 0,
                                             "position_profit": 0,
                                             "margin_long": 0,
                                             "margin_short": 0,
                                             'margin': 0,
                                             # 净持仓
                                             "pos": 0,
                                             "pos_long": 0,
                                             "pos_short": 0,
                                             "volume_long_frozen_today": 0,
                                             "volume_long_frozen_his": 0,
                                             "volume_short_frozen_today": 0,
                                             "volume_short_frozen_his": 0,
                                             "OpenCost_long": 0,
                                             "OpenCost_short": 0,
                                             "OpenCost_long_today": 0,
                                             "OpenCost_long_his": 0,
                                             "PositionCost_long_today": 0,
                                             "PositionCost_long_his": 0,
                                             "margin_long_today": 0,
                                             "margin_long_his": 0,
                                             "OpenCost_short_today": 0,
                                             "OpenCost_short_his": 0,
                                             "PositionCost_short_today": 0,
                                             "PositionCost_short_his": 0,
                                             "margin_short_today": 0,
                                             "margin_short_his": 0,
                                             "volume_long_frozen": 0,
                                             "volume_short_frozen": 0,
                                             }
                # print(pInvestorPosition.Position,pInvestorPosition.TodayPosition)
                # #平仓盈亏
                # print(pInvestorPosition.CloseProfit)
                if symbol not in self.temp_closep:
                    self.temp_closep[symbol] = pInvestorPosition.CloseProfit
                else:
                    self.temp_closep[symbol] += pInvestorPosition.CloseProfit

                # self.position[symbol]["CloseProfit"]=pInvestorPosition.CloseProfit
                # 买卖方向
                if pInvestorPosition.PosiDirection == "2":
                    # print(pInvestorPosition.InstrumentID,pInvestorPosition.Position,pInvestorPosition.TodayPosition,)
                    # print(pInvestorPosition.InstrumentID,"类型",pInvestorPosition.PositionDate,type(pInvestorPosition.PositionDate))
                    # 判断交易所是否是上交所和能源所
                    if self.symbol[pInvestorPosition.InstrumentID] not in ("SHFE", "INE"):

                        if pInvestorPosition.TodayPosition > 0:
                            self.position[symbol]["pos_long_today"] = pInvestorPosition.TodayPosition
                            self.position[symbol]["OpenCost_long"] = pInvestorPosition.OpenCost
                            self.position[symbol]["margin_long"] = pInvestorPosition.UseMargin
                            self.position[symbol]["volume_long_frozen"] = pInvestorPosition.LongFrozen
                            self.position[symbol]["PositionCost_long"] = pInvestorPosition.PositionCost

                        if pInvestorPosition.Position > pInvestorPosition.TodayPosition:
                            self.position[symbol][
                                "pos_long_his"] = pInvestorPosition.Position - pInvestorPosition.TodayPosition
                            self.position[symbol]["OpenCost_long"] = pInvestorPosition.OpenCost
                            self.position[symbol]["margin_long"] = pInvestorPosition.UseMargin
                            self.position[symbol]["volume_long_frozen"] = pInvestorPosition.LongFrozen
                            self.position[symbol]["PositionCost_long"] = pInvestorPosition.PositionCost
                    else:
                        if pInvestorPosition.PositionDate == "1":
                            self.position[symbol]["pos_long_today"] = pInvestorPosition.Position
                            self.position[symbol]["OpenCost_long_today"] = pInvestorPosition.OpenCost
                            self.position[symbol]["margin_long_today"] = pInvestorPosition.UseMargin
                            self.position[symbol]["volume_long_frozen_today"] = pInvestorPosition.LongFrozen
                            self.position[symbol]["PositionCost_long_today"] = pInvestorPosition.PositionCost
                        if pInvestorPosition.PositionDate == "2":
                            self.position[symbol]["pos_long_his"] = pInvestorPosition.Position
                            self.position[symbol]["OpenCost_long_his"] = pInvestorPosition.OpenCost
                            self.position[symbol]["margin_long_his"] = pInvestorPosition.UseMargin
                            self.position[symbol]["volume_long_frozen_his"] = pInvestorPosition.LongFrozen
                            self.position[symbol]["PositionCost_long_his"] = pInvestorPosition.PositionCost

                        # self.position[symbol]["pos_long_today"]=0
                        # self.position[symbol]["OpenCost_long_today"]=0
                        # self.position[symbol]["margin_long_today"]=0
                        # self.position[symbol]["volume_long_frozen_today"]=0
                        # self.position[symbol]["PositionCost_long_today"]=0
                        # self.position[symbol]["pos_long_his"]=0
                        # self.position[symbol]["OpenCost_long_his"]=0
                        # self.position[symbol]["margin_long_his"]=0
                        # self.position[symbol]["volume_long_frozen_his"]=0
                        # self.position[symbol]["PositionCost_long_his"]=0

                else:
                    # print(pInvestorPosition.InstrumentID,pInvestorPosition.Position,pInvestorPosition.TodayPosition,)
                    # print(pInvestorPosition.InstrumentID,"类型",pInvestorPosition.PositionDate)
                    if self.symbol[pInvestorPosition.InstrumentID] not in ("SHFE", "INE"):

                        if pInvestorPosition.TodayPosition > 0:
                            self.position[symbol]["pos_short_today"] = pInvestorPosition.TodayPosition
                            self.position[symbol]["OpenCost_short"] = pInvestorPosition.OpenCost
                            self.position[symbol]["margin_short"] = pInvestorPosition.UseMargin
                            self.position[symbol]["volume_short_frozen"] = pInvestorPosition.ShortFrozen
                            self.position[symbol]["PositionCost_short"] = pInvestorPosition.PositionCost

                        if pInvestorPosition.Position > pInvestorPosition.TodayPosition:
                            self.position[symbol][
                                "pos_short_his"] = pInvestorPosition.Position - pInvestorPosition.TodayPosition
                            self.position[symbol]["OpenCost_short"] = pInvestorPosition.OpenCost
                            self.position[symbol]["margin_short"] = pInvestorPosition.UseMargin
                            self.position[symbol]["volume_short_frozen"] = pInvestorPosition.ShortFrozen
                            self.position[symbol]["PositionCost_short"] = pInvestorPosition.PositionCost
                    else:
                        if pInvestorPosition.PositionDate == "1":
                            # if symbol=="INE.sc2012":
                            #     print("类型1",pInvestorPosition.Position,pInvestorPosition.TodayPosition)
                            self.position[symbol]["pos_short_today"] = pInvestorPosition.Position
                            self.position[symbol]["OpenCost_short_today"] = pInvestorPosition.OpenCost
                            self.position[symbol]["margin_short_today"] = pInvestorPosition.UseMargin
                            self.position[symbol]["volume_short_frozen_today"] = pInvestorPosition.ShortFrozen
                            self.position[symbol]["PositionCost_short_today"] = pInvestorPosition.PositionCost
                        if pInvestorPosition.PositionDate == "2":
                            # if symbol=="INE.sc2012":
                            #     print("类型2",pInvestorPosition.Position,pInvestorPosition.TodayPosition)
                            self.position[symbol]["pos_short_his"] = pInvestorPosition.Position
                            self.position[symbol]["OpenCost_short_his"] = pInvestorPosition.OpenCost
                            self.position[symbol]["margin_short_his"] = pInvestorPosition.UseMargin
                            self.position[symbol]["volume_short_frozen_his"] = pInvestorPosition.ShortFrozen
                            self.position[symbol]["PositionCost_short_his"] = pInvestorPosition.PositionCost

            if bIsLast:
                for symbol in self.position:
                    # 多空仓计算
                    self.position[symbol]["pos_long"] = self.position[symbol]["pos_long_today"] + \
                                                        self.position[symbol]["pos_long_his"]
                    self.position[symbol]["pos_short"] = self.position[symbol]["pos_short_today"] + \
                                                         self.position[symbol]["pos_short_his"]
                    # 开仓成本价计算,
                    long_c = (self.position[symbol]["pos_long_today"] + self.position[symbol]["pos_long_his"]) * \
                             self.symbol_v[symbol.split(".")[1]]
                    self.position[symbol]["position_cost_long"] = self.position[symbol]["OpenCost_long"] + \
                                                                  self.position[symbol]["OpenCost_long_today"] + \
                                                                  self.position[symbol]["OpenCost_long_his"]

                    # if self.init_start is None:
                    self.position[symbol]["open_price_long"] = self.position[symbol][
                                                                   "position_cost_long"] / long_c if long_c else 0

                    # print("OpenCost_short",self.position[symbol]["OpenCost_short"],self.position[symbol]["OpenCost_short_today"],self.position[symbol]["OpenCost_short_his"])
                    self.position[symbol]["position_cost_short"] = self.position[symbol]["OpenCost_short"] + \
                                                                   self.position[symbol]["OpenCost_short_today"] + \
                                                                   self.position[symbol]["OpenCost_short_his"]

                    short_c = (self.position[symbol]["pos_short_today"] + self.position[symbol]["pos_short_his"]) * \
                              self.symbol_v[symbol.split(".")[1]]
                    # if self.init_start is None:
                    self.position[symbol]["open_price_short"] = self.position[symbol][
                                                                    "position_cost_short"] / short_c if short_c else 0

                    # 持仓成本计算
                    long_c = (self.position[symbol]["pos_long_today"] + self.position[symbol]["pos_long_his"]) * \
                             self.symbol_v[symbol.split(".")[1]]
                    all_PositionCost = self.position[symbol]["PositionCost_long_today"] + self.position[symbol][
                        "PositionCost_long_his"]
                    self.position[symbol]["position_price_long"] = all_PositionCost / long_c if long_c else 0
                    all_PositionCost = self.position[symbol]["PositionCost_short_today"] + self.position[symbol][
                        "PositionCost_short_his"]
                    short_c = self.position[symbol]["pos_short_today"] + self.position[symbol]["pos_short_his"] * \
                              self.symbol_v[symbol.split(".")[1]]
                    self.position[symbol]["position_price_short"] = all_PositionCost / short_c if short_c else 0
                    # 处理保证金
                    if self.symbol[pInvestorPosition.InstrumentID] in ("SHFE", "INE"):

                        self.position[symbol]["margin_long"] = self.position[symbol]["margin_long_today"] + \
                                                               self.position[symbol]["margin_long_his"]
                        self.position[symbol]["margin_short"] = self.position[symbol]["margin_short_today"] + \
                                                                self.position[symbol]["margin_short_his"]
                        self.position[symbol]["margin"] = self.position[symbol]["margin_long"] + \
                                                          self.position[symbol]["margin_short"]
                    else:
                        self.position[symbol]["margin"] = self.position[symbol]["margin_long"] + \
                                                          self.position[symbol]["margin_short"]
                    # 处理冻结手数
                    if self.symbol[pInvestorPosition.InstrumentID] in ("SHFE", "INE"):
                        self.position[symbol]["volume_long_frozen"] = self.position[symbol][
                                                                          "volume_long_frozen_today"] + \
                                                                      self.position[symbol][
                                                                          "volume_long_frozen_his"]
                        self.position[symbol]["volume_short_frozen"] = self.position[symbol][
                                                                           "volume_short_frozen_today"] + \
                                                                       self.position[symbol][
                                                                           "volume_short_frozen_his"]
                    # 净持仓
                    self.position[symbol]["pos"] = self.position[symbol]["pos_long"] - self.position[symbol][
                        "pos_short"]
                    # #平仓盈利处理
                    self.position[symbol]["CloseProfit"] = self.temp_closep[symbol]
                    self.temp_closep[symbol] = 0
                # print(self.position)
                if self.init_start is None:
                    # 更新订单的交易所 和 成交价格
                    for x in self.order:
                        # 更新交易所
                        self.order[x]["exchange_id"] = self.symbol[self.order[x]["instrument_id"]]
                        # 更新委托单成交价格,和委托单相关成交字典
                        if x in self.order_trade:
                            if "&" not in self.order[x]["instrument_id"]:
                                all_vol = self.order[x]["volume_orign"]
                                temp_price_v_sum = 0
                                temp_v_sum = 0
                                for y in self.order_trade[x]:
                                    temp_price_v_sum += self.trade[y]["price"] * self.trade[y]["volume"]
                                    temp_v_sum += self.trade[y]["volume"]
                                    self.order[x]["trade_records"].append(
                                        {self.trade[y]["trade_id"]: self.trade[y]})
                                if all_vol == temp_v_sum:
                                    self.order[x]["trade_price"] = temp_price_v_sum / temp_v_sum
                            else:
                                # print("我怎么知道合成错了")
                                品种1 = re.findall(" ([a-zA-Z0-9]{1,})&", self.order[x]["instrument_id"])[0]
                                品种2 = re.findall("&([a-zA-Z0-9]{1,})", self.order[x]["instrument_id"])[0]
                                品种1成交量 = 0
                                品种2成交量 = 0
                                品种1成交总成交额度 = 0
                                品种2成交总成交额度 = 0
                                # print(self.order[x]["instrument_id"])
                                for y in self.order_trade[x]:
                                    # print(self.trade[y]["instrument_id"],品种1,品种2)
                                    if self.trade[y]["instrument_id"] == 品种1:
                                        品种1成交量 += self.trade[y]["volume"]
                                        品种1成交总成交额度 += self.trade[y]["price"] * self.trade[y]["volume"]
                                        self.order[x]["trade_records"].append(
                                            {self.trade[y]["trade_id"]: self.trade[y]})
                                    if self.trade[y]["instrument_id"] == 品种2:
                                        品种2成交量 += self.trade[y]["volume"]
                                        品种2成交总成交额度 += self.trade[y]["price"] * self.trade[y]["volume"]
                                # print(品种1成交量+品种2成交量,self.order[x]["volume_orign"]*2)
                                if (品种1成交量 + 品种2成交量) == self.order[x]["volume_orign"] * 2:
                                    self.order[x]["trade_price"] = (品种1成交总成交额度 - 品种2成交总成交额度) / 品种1成交量

                    for x in self.trade:
                        self.trade[x]["exchange_id"] = self.symbol[self.trade[x]["instrument_id"]]

                    print("持仓情况为：")
                    for symbol in self.position:
                        print(self.position[symbol])
                    # print(self.position)

        except:
            print("计算错误")



    # def OnRspQryInvestorPosition(self, pPosition: 'CThostFtdcInvestorPositionField', pRspInfo: 'CThostFtdcRspInfoField',
    #                              nRequestID: 'int', bIsLast: 'bool') -> "void":
    #     print("持仓情况")
    #     print("InstrumentID=", pPosition.InstrumentID)
    #     print("BrokerID=", pPosition.BrokerID)
    #     print("InvestorID=", pPosition.InvestorID)
    #     print("PosiDirection=", pPosition.PosiDirection)
    #     print("HedgeFlag=", pPosition.HedgeFlag)

    # 合约返回
    def OnRspQryInstrument(self, pInstrument: "CThostFtdcInstrumentField", pRspInfo: "CThostFtdcRspInfoField",
                           nRequestID: "int", bIsLast: "bool"):
        self.symbol[pInstrument.InstrumentID] = pInstrument.ExchangeID
        self.symbol_v[pInstrument.InstrumentID] = pInstrument.VolumeMultiple
        # print(6666666)
        if bIsLast:
            time.sleep(2)
            # ReqQryInvestorPosition(self)
            pQryInvestorPosition = api.CThostFtdcQryInvestorPositionField()
            pQryInvestorPosition.BrokerID = self.BrokerID
            pQryInvestorPosition.InvestorID = self.UserID
            # pQryInvestorPosition.InstrumentID
            self.tapi.ReqQryInvestorPosition(pQryInvestorPosition, 0)


def main():
    tradeapi = api.CThostFtdcTraderApi_CreateFtdcTraderApi()
    tradespi = CTradeSpi(tradeapi, BROKERID, USERID, PASSWORD, AppID, AuthCode)
    tradeapi.RegisterFront(FrontAddr)
    tradeapi.RegisterSpi(tradespi)
    tradeapi.SubscribePrivateTopic(api.THOST_TERT_QUICK)
    tradeapi.SubscribePublicTopic(api.THOST_TERT_QUICK)
    tradeapi.Init()
    time.sleep(10)
    ReqQryInstrument(tradeapi)
    # ReqQryInvestorPosition(tradeapi, BROKERID, USERID, "IF2012")
    tradeapi.Join()


if __name__ == '__main__':
    main()
