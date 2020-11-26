'''
# 作者    ： 张莹潇
# 创建时间 ： 20/11/26 10:56
'''
import thosttraderapi as api
import janus
import asyncio
import time
import queue
import numpy
import re

TThostFtdcVolumeConditionType = {"1": "ANY", "2": "MIN", "3": "ALL"}
TThostFtdcTimeConditionType = {'1': "IOC", '2': "GFS", '3': "GFD", '4': "GTD", '5': "GTC", '6': "GFA"}
TThostFtdcOrderStatusType = {'0': "全部成交", '1': "部分成交还在队列中", "2": "部分成交不在队列中", "3": "未成交还在队列中", "4": "未成交不在队列中",
                             "5": "撤单",
                             "a": "未知", "b": "尚未触发", "c": "已触发"}


# 查资金
def ReqQryTradingAccount(self):
    pQryTradingAccount = api.CThostFtdcQryTradingAccountField()
    pQryTradingAccount.BrokerID = self.BrokerID
    pQryTradingAccount.InvestorID = self.UserID
    pQryTradingAccount.CurrencyID = "CNY"
    self.tapi.ReqQryTradingAccount(pQryTradingAccount, 0)


# 查持仓
def ReqQryInvestorPosition(self):
    # print(555555555555)
    pQryInvestorPosition = api.CThostFtdcQryInvestorPositionField()
    pQryInvestorPosition.BrokerID = self.BrokerID
    pQryInvestorPosition.InvestorID = self.UserID
    a = self.tapi.ReqQryInvestorPosition(pQryInvestorPosition, 0)
    # print(a)
    # print(666)


# 查合约
def ReqQryInstrument(self):
    pQryInstrument = api.CThostFtdcQryInstrumentField()
    self.tapi.ReqQryInstrument(pQryInstrument, 0)


# 报单
#     订单md5         品种    买卖方向,开平 ,下单手数,下单价格,订单类型
def order_insert(self, md5, symbol, direction, offset, volume, price, advanced):
    offset_temp = {"OPEN": "0", "CLOSE": "1", "CLOSETODAY": "3"}
    print("ReqOrderInsert Start")
    orderfield = api.CThostFtdcInputOrderField()
    orderfield.BrokerID = self.BrokerID
    orderfield.ExchangeID = symbol.split(".")[0]
    orderfield.InstrumentID = symbol.split(".")[1]
    orderfield.UserID = self.UserID
    orderfield.InvestorID = self.UserID
    orderfield.Direction = api.THOST_FTDC_D_Buy if direction == "BUY" else api.THOST_FTDC_D_Sell
    orderfield.CombOffsetFlag = offset_temp[offset]
    orderfield.LimitPrice = price
    orderfield.VolumeTotalOriginal = volume

    # print(orderfield.Direction)
    # print(orderfield.CombOffsetFlag)
    # print(orderfield.LimitPrice)

    # 限价单子(默认限价)
    orderfield.OrderPriceType = api.THOST_FTDC_OPT_LimitPrice

    # 触发条件 (默认立刻执行)
    orderfield.ContingentCondition = api.THOST_FTDC_CC_Immediately

    TimeCondition_dict = {"GFD": api.THOST_FTDC_TC_GFD, "FAK": api.THOST_FTDC_TC_IOC, "FOK": api.THOST_FTDC_TC_IOC}
    # 有效期类型
    orderfield.TimeCondition = TimeCondition_dict[advanced]

    # 成交类型
    orderfield.VolumeCondition = api.THOST_FTDC_VC_AV if advanced != "FOK" else api.THOST_FTDC_VC_CV
    orderfield.CombHedgeFlag = "1"

    orderfield.ForceCloseReason = api.THOST_FTDC_FCC_NotForceClose
    orderfield.IsAutoSuspend = 0
    self.temp_id.append(md5)
    self.tapi.ReqOrderInsert(orderfield, 0)
    print("ReqOrderInsert End")


def order_close(self, md5):
    order_id = self.order[md5]["exchange_order_id"]
    pInputOrderAction = api.CThostFtdcInputOrderActionField()
    pInputOrderAction.BrokerID = self.BrokerID
    pInputOrderAction.InvestorID = self.UserID
    pInputOrderAction.UserID = self.UserID
    pInputOrderAction.OrderSysID = order_id
    pInputOrderAction.ExchangeID = self.order[md5]['exchange_id']
    pInputOrderAction.InstrumentID = self.order[md5]["instrument_id"]
    pInputOrderAction.ActionFlag = api.THOST_FTDC_AF_Delete
    self.tapi.ReqOrderAction(pInputOrderAction, 0)


class CTradeSpi(api.CThostFtdcTraderSpi):
    def __init__(self, tapi, BrokerID, UserID, PassWord, AppID, AuthCode, all_queue_send):
        api.CThostFtdcTraderSpi.__init__(self)
        self.tapi = tapi
        self.BrokerID = BrokerID
        self.UserID = UserID
        self.AppID = AppID
        self.AuthCode = AuthCode
        self.PassWord = PassWord
        self.AppID = AppID
        self.AuthCode = AuthCode
        self.queue = all_queue_send
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

        # self._queue=queue.Queue()
        self.init_start = None

        # 缓存唯一id  md5 对应 OrderLocalID
        self.md5_Localid = {}

        # 缓存OrderLocalID 对应 唯一 id
        self.Localid_md5 = {}

        self.temp_id = []
        print(tapi, BrokerID, UserID, PassWord, AppID, AuthCode, all_queue_send)
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
        self.start_load()

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
        self.account.update(a)
        self.queue.put({"user": self.UserID, "account": self.account})
        print(a)
        if self.init_start is None:
            time.sleep(2)
            ReqQryInstrument(self)

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
                    self.position[symbol]["pos_long"] = self.position[symbol]["pos_long_today"] + self.position[symbol][
                        "pos_long_his"]
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
                        self.position[symbol]["margin"] = self.position[symbol]["margin_long"] + self.position[symbol][
                            "margin_short"]
                    else:
                        self.position[symbol]["margin"] = self.position[symbol]["margin_long"] + self.position[symbol][
                            "margin_short"]
                    # 处理冻结手数
                    if self.symbol[pInvestorPosition.InstrumentID] in ("SHFE", "INE"):
                        self.position[symbol]["volume_long_frozen"] = self.position[symbol][
                                                                          "volume_long_frozen_today"] + \
                                                                      self.position[symbol]["volume_long_frozen_his"]
                        self.position[symbol]["volume_short_frozen"] = self.position[symbol][
                                                                           "volume_short_frozen_today"] + \
                                                                       self.position[symbol]["volume_short_frozen_his"]
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
                                    self.order[x]["trade_records"].append({self.trade[y]["trade_id"]: self.trade[y]})
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

                    print("持仓情况：")
                    for symbol in self.position:
                        print(self.position[symbol])
                if self.init_start != 1:
                    self.init_start = 1
                    self.queue.put(
                        {"user": self.UserID, "position": self.position, "order": self.order, "trade": self.trade,
                         "account": self.account})
                else:
                    self.queue.put(
                        {"user": self.UserID, "position": self.position, "order": self.order, "trade": self.trade})

        except:
            print("计算错误")

    # 合约返回
    def OnRspQryInstrument(self, pInstrument: "CThostFtdcInstrumentField", pRspInfo: "CThostFtdcRspInfoField",
                           nRequestID: "int", bIsLast: "bool"):
        self.symbol[pInstrument.InstrumentID] = pInstrument.ExchangeID
        self.symbol_v[pInstrument.InstrumentID] = pInstrument.VolumeMultiple
        # print(6666666)
        if bIsLast:
            time.sleep(2)
            ReqQryInvestorPosition(self)

    def OnRtnOrder(self, pOrder: 'CThostFtdcOrderField') -> "void":
        try:
            # print("报单回报")
            # d={ x: getattr(pOrder, x) for x in dir(pOrder) if x[0]!="_"}
            print(time.strftime("%Y-%m-%d-%H:%I:%S", time.localtime( time.time() ) ), "报单成功")
            # 初始化的时候
            if self.init_start is None:
                # 如果报单id没在报单列表
                if pOrder.OrderLocalID not in self.order:
                    self.order[pOrder.OrderLocalID] = {
                        "order_id": pOrder.OrderLocalID,
                        "exchange_order_id": pOrder.OrderSysID,
                        "instrument_id": pOrder.InstrumentID,
                        "direction": "BUY" if pOrder.Direction == "0" else "SELL",
                        "offset": "OPEN" if pOrder.CombOffsetFlag == "0" else "CLOSE",
                        "volume_orign": pOrder.VolumeTotalOriginal,
                        "volume_left": pOrder.VolumeTotal,
                        "limit_price": pOrder.LimitPrice,
                        "price_type": "LIMIT" if pOrder.OrderType == "0" else "ANY",
                        "volume_condition": TThostFtdcVolumeConditionType[pOrder.VolumeCondition],
                        "time_condition": TThostFtdcTimeConditionType[pOrder.TimeCondition],
                        "insert_date_time": time.mktime(
                            time.strptime(pOrder.InsertDate + pOrder.InsertTime, '%Y%m%d%H:%M:%S')) * 1e9,
                        "last_msg": pOrder.StatusMsg,
                        "CTP_status": TThostFtdcOrderStatusType[pOrder.OrderStatus],
                        "status": "ALIVE" if pOrder.OrderStatus in ('1', '3', 'a', 'b') else "FINISHED",
                        "trade_price": numpy.nan,
                        "trade_records": []
                    }
                else:
                    # 如果报单id在报单列表
                    self.order[pOrder.OrderLocalID].update({
                        "volume_left": pOrder.VolumeTotal,
                        "limit_price": pOrder.LimitPrice,
                        "time_condition": TThostFtdcTimeConditionType[pOrder.TimeCondition],
                        "exchange_order_id": pOrder.OrderSysID,
                        "last_msg": pOrder.StatusMsg,
                        "CTP_status": TThostFtdcOrderStatusType[pOrder.OrderStatus],
                        "status": "ALIVE" if pOrder.OrderStatus in ('1', '3', 'a', 'b') else "FINISHED",
                    })


            else:
                # 如果报单id 没在报单列表 并且 报单id没在缓存md5中
                if pOrder.OrderLocalID not in self.order and pOrder.OrderLocalID not in self.Localid_md5:
                    if not self.temp_id:
                        md5 = pOrder.OrderLocalID
                    else:
                        md5 = self.temp_id.pop(0)
                        self.md5_Localid[md5] = pOrder.OrderLocalID
                        self.Localid_md5[pOrder.OrderLocalID] = md5

                    self.order[md5] = {
                        "order_id": md5,
                        "exchange_order_id": pOrder.OrderSysID,
                        'exchange_id': self.symbol[pOrder.InstrumentID],
                        "instrument_id": pOrder.InstrumentID,
                        "direction": "BUY" if pOrder.Direction == "0" else "SELL",
                        "offset": "OPEN" if pOrder.CombOffsetFlag == "0" else "CLOSE",
                        "volume_orign": pOrder.VolumeTotalOriginal,
                        "volume_left": pOrder.VolumeTotal,
                        "limit_price": pOrder.LimitPrice,
                        "price_type": "LIMIT" if pOrder.OrderType == "0" else "ANY",
                        "volume_condition": TThostFtdcVolumeConditionType[pOrder.VolumeCondition],
                        "time_condition": TThostFtdcTimeConditionType[pOrder.TimeCondition],
                        "insert_date_time": time.mktime(
                            time.strptime(pOrder.InsertDate + pOrder.InsertTime, '%Y%m%d%H:%M:%S')) * 1e9,
                        "last_msg": pOrder.StatusMsg,
                        "CTP_status": TThostFtdcOrderStatusType[pOrder.OrderStatus],
                        "status": "ALIVE" if pOrder.OrderStatus in ('1', '3', 'a', 'b') else "FINISHED",
                        "trade_price": numpy.nan,
                        "trade_records": []
                    }
                else:
                    if pOrder.OrderLocalID in self.Localid_md5:
                        md5 = self.Localid_md5[pOrder.OrderLocalID]
                    else:
                        md5 = pOrder.OrderLocalID
                    temp_volume_left = self.order[md5]["volume_left"]
                    temp_order = self.order[md5].copy()
                    self.order[md5].update({
                        "exchange_order_id": pOrder.OrderSysID,
                        "volume_left": pOrder.VolumeTotal,
                        "limit_price": pOrder.LimitPrice,
                        "time_condition": TThostFtdcTimeConditionType[pOrder.TimeCondition],
                        "last_msg": pOrder.StatusMsg,
                        "CTP_status": TThostFtdcOrderStatusType[pOrder.OrderStatus],
                        "status": "ALIVE" if pOrder.OrderStatus in ('1', '3', 'a', 'b') else "FINISHED",
                    })
                    # if temp_volume_left==self.order[pOrder.OrderLocalID]["volume_left"] and temp_order!= self.order[pOrder.OrderLocalID]:
                    if temp_order != self.order[md5] and self.order[md5]["volume_left"] != 0:
                        # print("需要推送")
                        self.queue.put({"user": self.UserID, "order": {md5: self.order[md5]}})
        except:
            print("报单计算出问题了")

    def OnRspOrderInsert(self, pInputOrder: 'CThostFtdcInputOrderField', pRspInfo: 'CThostFtdcRspInfoField',
                         nRequestID: 'int', bIsLast: 'bool') -> "void":
        print(time.strftime("%Y-%m-%d-%H:%I:%S", time.localtime( time.time() ) ), "报单失败", pRspInfo.ErrorMsg)
        md5 = self.temp_id.pop(0)
        self.order[md5] = {
            "order_id": md5,
            "exchange_order_id": "",
            'exchange_id': self.symbol[pInputOrder.InstrumentID],
            "instrument_id": pInputOrder.InstrumentID,
            "direction": "BUY" if pInputOrder.Direction == "0" else "SELL",
            "offset": "OPEN" if pInputOrder.CombOffsetFlag == "0" else "CLOSE",
            "volume_orign": pInputOrder.VolumeTotalOriginal,
            "volume_left": pInputOrder.VolumeTotalOriginal,
            "limit_price": pInputOrder.LimitPrice,
            "price_type": "LIMIT",
            "volume_condition": TThostFtdcVolumeConditionType[pInputOrder.VolumeCondition],
            "time_condition": TThostFtdcTimeConditionType[pInputOrder.TimeCondition],
            "insert_date_time": time.time() * 1e9,
            "last_msg": "报单失败",
            "CTP_status": pRspInfo.ErrorMsg,
            "status": "FINISHED",
            "trade_price": numpy.nan,
            "trade_records": []
        }
        self.queue.put({"user": self.UserID, "order": {md5: self.order[md5]}})

    def OnRtnInstrumentStatus(self, pInstrumentStatus: "CThostFtdcInstrumentStatusField"):
        d = {x: getattr(pInstrumentStatus, x) for x in dir(pInstrumentStatus) if x[0] != "_"}

    def OnRtnTrade(self, pTrade: "CThostFtdcTradeField"):
        d = {x: getattr(pTrade, x) for x in dir(pTrade) if x[0] != "_"}
        print(time.strftime("%Y-%m-%d-%H:%I:%S", time.localtime( time.time() ) ), "交易成功")
        try:
            if pTrade.OrderLocalID in self.Localid_md5:
                md5 = self.Localid_md5[pTrade.OrderLocalID]
            else:
                md5 = pTrade.OrderLocalID

            if md5 not in self.order_trade:
                self.order_trade[md5] = [pTrade.TradeID]
            else:
                self.order_trade[md5].append(pTrade.TradeID)
            if self.init_start is None:
                # print(md5,pTrade.InstrumentID)
                self.trade[pTrade.TradeID] = {
                    "order_id": md5,
                    "trade_id": pTrade.TradeID,
                    "exchange_order_id": pTrade.SequenceNo,
                    "instrument_id": pTrade.InstrumentID,
                    "direction": "BUY" if pTrade.Direction == "0" else "SELL",
                    "offset": "OPEN" if pTrade.OffsetFlag == "0" else "CLOSE",
                    "price": pTrade.Price,
                    "volume": pTrade.Volume,
                    "trade_date_time": time.mktime(
                        time.strptime(pTrade.TradeDate + pTrade.TradeTime, '%Y%m%d%H:%M:%S')) * 1e9,
                }
            else:
                # 根据成交,计算仓位变化,进行推送
                self.trade[pTrade.TradeID] = {
                    "order_id": md5,
                    "trade_id": pTrade.TradeID,
                    "exchange_order_id": pTrade.SequenceNo,
                    "instrument_id": pTrade.InstrumentID,
                    "direction": "BUY" if pTrade.Direction == "0" else "SELL",
                    "offset": "OPEN" if pTrade.OffsetFlag == "0" else "CLOSE",
                    "price": pTrade.Price,
                    "volume": pTrade.Volume,
                    "trade_date_time": time.mktime(
                        time.strptime(pTrade.TradeDate + pTrade.TradeTime, '%Y%m%d%H:%M:%S')) * 1e9,
                }
                self.order[md5]["trade_records"].append(
                    {self.trade[pTrade.TradeID]["trade_id"]: self.trade[pTrade.TradeID]})
                # 判断是否需要更新订单平均成交价格
                all_v = self.order[md5]["volume_orign"]
                if "&" not in self.order[md5]["instrument_id"]:
                    temp_v = 0
                    temp_v_p = 0
                    for x in self.order_trade[md5]:
                        temp_v += self.trade[x]["volume"]
                        temp_v_p += self.trade[x]["price"] * self.trade[x]["volume"]

                    if temp_v == all_v:
                        self.order[md5]["trade_price"] = temp_v_p / temp_v
                else:
                    品种1 = re.findall(" ([a-zA-Z0-9]{1,})&", self.order[md5]["instrument_id"])[0]
                    品种2 = re.findall("&([a-zA-Z0-9]{1,})", self.order[md5]["instrument_id"])[0]
                    品种1成交量 = 0
                    品种2成交量 = 0
                    品种1成交总成交额度 = 0
                    品种2成交总成交额度 = 0
                    # print(self.order[md5]["instrument_id"])
                    for y in self.order_trade[md5]:
                        # print(self.trade[y]["instrument_id"],品种1,品种2)
                        if self.trade[y]["instrument_id"] == 品种1:
                            品种1成交量 += self.trade[y]["volume"]
                            品种1成交总成交额度 += self.trade[y]["price"] * self.trade[y]["volume"]
                            self.order[md5]["trade_records"].append({self.trade[y]["trade_id"]: self.trade[y]})
                        if self.trade[y]["instrument_id"] == 品种2:
                            品种2成交量 += self.trade[y]["volume"]
                            品种2成交总成交额度 += self.trade[y]["price"] * self.trade[y]["volume"]
                    if 品种1成交量 + 品种2成交量 == self.order[md5]["volume_orign"] * 2:
                        # print(666)
                        self.order[md5]["trade_price"] = (品种1成交总成交额度 - 品种2成交总成交额度) / 品种1成交量
                # 维护实时持仓
                symbol = self.symbol[pTrade.InstrumentID] + "." + pTrade.InstrumentID
                # 如果品种原来没在,就是新开
                # print(667)
                if symbol not in self.position:
                    self.position[symbol] = {"exchange_id": self.symbol[pTrade.InstrumentID],
                                             "instrument_id": pTrade.InstrumentID,
                                             'pos_long_his': 0,
                                             "pos_long_today": pTrade.Volume if pTrade.Direction == "0" else 0,
                                             "pos_long": pTrade.Volume if pTrade.Direction == "0" else 0,
                                             "pos_short_his": 0,
                                             "pos_short_today": pTrade.Volume if pTrade.Direction != "0" else 0,
                                             "pos_short": pTrade.Volume if pTrade.Direction != "0" else 0,
                                             "open_price_long": pTrade.Price if pTrade.Direction == "0" else 0,
                                             "open_price_short": pTrade.Price if pTrade.Direction != "0" else 0,
                                             "position_price_long": pTrade.Price if pTrade.Direction == "0" else 0,
                                             "position_price_short": pTrade.Price if pTrade.Direction != "0" else 0,
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
                                             "pos": pTrade.Volume if pTrade.Direction == "0" else - pTrade.Volume,
                                             "volume_long_frozen_today": 0,
                                             "volume_long_frozen_his": 0,
                                             "volume_short_frozen_today": 0,
                                             "volume_short_frozen_his": 0,
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
                                             "margin_short_his": 0
                                             }
                else:
                    # 根据  #开平 OffsetFlag 和 方向, 计算
                    # 如果是 开仓
                    if pTrade.OffsetFlag == '0':
                        # 如果是开多
                        if pTrade.Direction == "0":
                            d = {"pos_long_today": self.position[symbol]["pos_long_today"] + pTrade.Volume,
                                 "pos_long": self.position[symbol]["pos_long"] + pTrade.Volume,
                                 'open_price_long': (self.position[symbol]["open_price_long"] * self.position[symbol][
                                     "pos_long"] + pTrade.Price * pTrade.Volume) / (
                                                                self.position[symbol]["pos_long"] + pTrade.Volume),
                                 "position_price_long": (self.position[symbol]["position_price_long"] *
                                                         self.position[symbol][
                                                             "pos_long"] + pTrade.Price * pTrade.Volume) / (
                                                                    self.position[symbol]["pos_long"] + pTrade.Volume),
                                 "pos": self.position[symbol]["pos"] + pTrade.Volume
                                 }
                        else:
                            d = {"pos_short_today": self.position[symbol]["pos_short_today"] + pTrade.Volume,
                                 "pos_short": self.position[symbol]["pos_short"] + pTrade.Volume,
                                 'open_price_short': (self.position[symbol]["open_price_short"] * self.position[symbol][
                                     "pos_short"] + pTrade.Price * pTrade.Volume) / (
                                                                 self.position[symbol]["pos_short"] + pTrade.Volume),
                                 "position_price_short": (self.position[symbol]["position_price_short"] *
                                                          self.position[symbol][
                                                              "pos_short"] + pTrade.Price * pTrade.Volume) / (
                                                                     self.position[symbol][
                                                                         "pos_short"] + pTrade.Volume),
                                 "pos": self.position[symbol]["pos"] - pTrade.Volume
                                 }
                        self.position[symbol].update(d)
                    else:
                        # 判断是否的上交所或者能源所的
                        if self.symbol[pTrade.InstrumentID] in ("INE", "SHFE"):
                            # 平今
                            if pTrade.OffsetFlag == '3':
                                # 买平
                                if pTrade.Direction == "0":
                                    d = {"pos_short_today": self.position[symbol]["pos_short_today"] - pTrade.Volume,
                                         'pos_short': self.position[symbol]["pos_short"] - pTrade.Volume,
                                         "open_price_short": self.position[symbol]["open_price_short"] if
                                         self.position[symbol]["pos_short"] - pTrade.Volume > 0 else 0,
                                         "position_price_short": self.position[symbol]["position_price_short"] if
                                         self.position[symbol]["pos_short"] - pTrade.Volume > 0 else 0,
                                         "pos": self.position[symbol]["pos"] + pTrade.Volume
                                         }
                                    self.position[symbol].update(d)
                                else:
                                    d = {"pos_long_today": self.position[symbol]["pos_long_today"] - pTrade.Volume,
                                         'pos_long': self.position[symbol]["pos_long"] - pTrade.Volume,
                                         "open_price_long": self.position[symbol]["open_price_long"] if
                                         self.position[symbol]["pos_long"] - pTrade.Volume > 0 else 0,
                                         "position_price_long": self.position[symbol]["position_price_long"] if
                                         self.position[symbol]["pos_long"] - pTrade.Volume > 0 else 0,
                                         "pos": self.position[symbol]["pos"] - pTrade.Volume
                                         }
                                    self.position[symbol].update(d)
                            else:  # 平昨日
                                if pTrade.Direction == "0":
                                    d = {"pos_short_his": self.position[symbol]["pos_short_his"] - pTrade.Volume,
                                         'pos_short': self.position[symbol]["pos_short"] - pTrade.Volume,
                                         "open_price_short": self.position[symbol]["open_price_short"] if
                                         self.position[symbol]["pos_short"] - pTrade.Volume > 0 else 0,
                                         "position_price_short": self.position[symbol]["position_price_short"] if
                                         self.position[symbol]["pos_short"] - pTrade.Volume > 0 else 0,
                                         "pos": self.position[symbol]["pos"] + pTrade.Volume
                                         }
                                    self.position[symbol].update(d)
                                else:
                                    d = {"pos_long_his": self.position[symbol]["pos_long_his"] - pTrade.Volume,
                                         'pos_long': self.position[symbol]["pos_long"] - pTrade.Volume,
                                         "open_price_long": self.position[symbol]["open_price_long"] if
                                         self.position[symbol]["pos_long"] - pTrade.Volume > 0 else 0,
                                         "position_price_long": self.position[symbol]["position_price_long"] if
                                         self.position[symbol]["pos_long"] - pTrade.Volume > 0 else 0,
                                         "pos": self.position[symbol]["pos"] - pTrade.Volume
                                         }
                                    self.position[symbol].update(d)
                        else:
                            # 如果是买平
                            if pTrade.Direction == "0":
                                temp_his = self.position[symbol]["pos_short_his"]
                                temp_today = self.position[symbol]["pos_short_today"]
                                if temp_his > pTrade.Volume:
                                    d = {"pos_short_his": self.position[symbol]["pos_short_his"] - pTrade.Volume,
                                         'pos_short': self.position[symbol]["pos_short"] - pTrade.Volume,
                                         "pos": self.position[symbol]["pos"] + pTrade.Volume
                                         }
                                elif temp_his == pTrade.Volume:
                                    d = {"pos_short_his": self.position[symbol]["pos_short_his"] - pTrade.Volume,
                                         'pos_short': self.position[symbol]["pos_short"] - pTrade.Volume,
                                         "open_price_short": self.position[symbol]["open_price_short"] if
                                         self.position[symbol]["pos_short"] - pTrade.Volume > 0 else 0,
                                         "position_price_short": self.position[symbol]["position_price_short"] if
                                         self.position[symbol]["pos_short"] - pTrade.Volume > 0 else 0,
                                         "pos": self.position[symbol]["pos"] + pTrade.Volume
                                         }
                                elif temp_his < pTrade.Volume:
                                    d = {"pos_short_his": 0,
                                         "pos_short_today": temp_today - (pTrade.Volume - temp_his),
                                         'pos_short': self.position[symbol]["pos_short"] - pTrade.Volume,
                                         "pos": self.position[symbol]["pos"] + pTrade.Volume,
                                         "open_price_short": self.position[symbol]["open_price_short"] if
                                         self.position[symbol]["pos_short"] - pTrade.Volume > 0 else 0,
                                         "position_price_short": self.position[symbol]["position_price_short"] if
                                         self.position[symbol]["pos_short"] - pTrade.Volume > 0 else 0,
                                         }
                                self.position[symbol].update(d)
                            else:
                                # 如果是卖平
                                temp_his = self.position[symbol]["pos_long_his"]
                                temp_today = self.position[symbol]["pos_long_today"]
                                if temp_his > pTrade.Volume:
                                    d = {"pos_long_his": self.position[symbol]["pos_long_his"] - pTrade.Volume,
                                         'pos_long': self.position[symbol]["pos_long"] - pTrade.Volume,
                                         "pos": self.position[symbol]["pos"] - pTrade.Volume
                                         }
                                elif temp_his == pTrade.Volume:
                                    d = {"pos_long_his": self.position[symbol]["pos_long_his"] - pTrade.Volume,
                                         'pos_long': self.position[symbol]["pos_long"] - pTrade.Volume,
                                         "open_price_long": self.position[symbol]["open_price_long"] if
                                         self.position[symbol]["pos_long"] - pTrade.Volume > 0 else 0,
                                         "position_price_long": self.position[symbol]["position_price_long"] if
                                         self.position[symbol]["pos_long"] - pTrade.Volume > 0 else 0,
                                         "pos": self.position[symbol]["pos"] - pTrade.Volume
                                         }
                                elif temp_his < pTrade.Volume:
                                    d = {"pos_long_his": 0,
                                         "pos_long_today": temp_today - (pTrade.Volume - temp_his),
                                         'pos_long': self.position[symbol]["pos_long"] - pTrade.Volume,
                                         "pos": self.position[symbol]["pos"] - pTrade.Volume,
                                         "open_price_long": self.position[symbol]["open_price_long"] if
                                         self.position[symbol]["pos_long"] - pTrade.Volume > 0 else 0,
                                         "position_price_long": self.position[symbol]["position_price_long"] if
                                         self.position[symbol]["pos_long"] - pTrade.Volume > 0 else 0,
                                         }
                                self.position[symbol].update(d)
                # print(668)
                self.queue.put({"user": self.UserID, "position": {symbol: self.position[symbol]}, "order": self.order,
                                "trade": self.trade})

        except:
            print("成交计算出错")

    def OnRspOrderAction(self, pInputOrderAction: "CThostFtdcInputOrderActionField", pRspInfo: "CThostFtdcRspInfoField",
                         nRequestID: "nRequestID", bIsLast: "bool"):
        d = {x: getattr(pInputOrderAction, x) for x in dir(pInputOrderAction) if x[0] != "_"}
        d2 = {x: getattr(pRspInfo, x) for x in dir(pRspInfo) if x[0] != "_"}
        print(d)
        print(d2)

    def start_load(self):
        time.sleep(2)
        ReqQryTradingAccount(self)

async def 启动():
    #Addr
    FrontAddr = "tcp://180.168.146.187:10101"
    # LoginInfo
    BROKERID = "9999"
    USERID = "086515"
    PASSWORD = "123456"
    #OrderInfo
    # EXCHANGEID="SHFE"
    # INSTRUMENTID="cu2010"
    # PRICE=51000
    # VOLUME=1
    # DIRECTION=api.THOST_FTDC_D_Sell
    #DIRECTION=api.THOST_FTDC_D_Buy
    #open
    # OFFSET="0"
    #close
    #OFFSET="1"
    AppID="simnow_client_test"
    AuthCode="0000000000000000"
    myqueue=janus.Queue()


    tradeapi=api.CThostFtdcTraderApi_CreateFtdcTraderApi()
    tradespi=CTradeSpi(tradeapi,BROKERID,USERID,PASSWORD,AppID,AuthCode,myqueue.sync_q)
    tradeapi.RegisterFront(FrontAddr)
    tradeapi.RegisterSpi(tradespi)
    tradeapi.SubscribePrivateTopic(api.THOST_TERT_RESTART)
    tradeapi.SubscribePublicTopic(api.THOST_TERT_RESTART)
    tradeapi.Init()
    n=0
    while True:
        a=myqueue.sync_q.get()
        if "SHFE.rb2101" in a:
            print("多",a[ "SHFE.rb2101"]["pos_long"],"空",a["SHFE.rb2101"]["pos_short"],"多成本",a[ "SHFE.rb2101"]["open_price_long"],"空成本",a[ "SHFE.rb2101"]["open_price_short"])

        if n==0:
            n=1
            # a=input("输入2222222222222222222222")
            # order_insert(tradespi,"weiquant","SHFE.cu2010","BUY","OPEN",1,51000,"GFD")
            # time.sleep(10)
            # print("撤单")
            # #order_insert(tradespi,"weiquant","SHFE.rb2101","BUY","OPEN",1,3500,"GFD")
            # order_close(tradespi,'weiquant')


    tradeapi.Join()

if __name__ == '__main__':
    loop=asyncio.new_event_loop()
    loop.create_task(启动())
    loop.run_forever()
