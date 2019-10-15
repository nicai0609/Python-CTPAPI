# -*- coding: utf-8 -*-
'''
@author : 景色
@csdn : https://blog.csdn.net/pjjing
@QQ群 : 767101469
@公众号 : QuantRoad2019
@功能：现手、增仓、开平及对手盘的计算
'''
import thostmduserapi as mdapi
import copy
'''
以下为需要订阅行情的合约号，注意选择有效合约；
有效连上但没有行情可能是过期合约或者不再交易时间内导致
'''
subID=["au1912"]

def enum(**enums):
    return type('Enum', (), enums)
 
 
# 仓位变化方向
open_interest_delta_forward_enum = enum(OPEN="Open", CLOSE="Close", EXCHANGE="Exchange", NONE="None",
                                        OPENFWDOUBLE="OpenFwDouble", CLOSEFWDOUBLE="CloseFwDOuble")
# 订单成交区域，决定是多还是空
order_forward_enum = enum(UP="Up", DOWN="Down", MIDDLE="Middle")
 
# 最终需要的tick方向
tick_type_enum = enum(OPENLONG="OpenLong", OPENSHORT="OpenShort", OPENDOUBLE="OpenDouble",
                      CLOSELONG="CloseLong", CLOSESHORT="CloseShort", CLOSEDOUBLE="CloseDouble",
                      EXCHANGELONG="ExchangeLong", EXCHANGESHORT="ExchangeShort",
                      OPENUNKOWN="OpenUnkown", CLOSEUNKOWN="CloseUnkown", EXCHANGEUNKOWN="ExchangeUnkown",
                      UNKOWN="Unkown", NOCHANGE="NoChange")
 
tick_color_enum = enum(RED="Red", GREEN="Green", WHITE="White")
 
tick_type_key_enum = enum(TICKTYPE="TickType", TICKCOLOR="TickColor")
 
# 只与计算对手单的组成相关
opponent_key_enum = enum(OPPOSITE="Opposite", SIMILAR="Similar")
 
# 只做翻译成中文使用，对应 tick_type_enum
tick_type_str_dict = {tick_type_enum.OPENLONG: "多开", tick_type_enum.OPENSHORT: "空开",
                      tick_type_enum.OPENDOUBLE: "双开",
                      tick_type_enum.CLOSELONG: "多平", tick_type_enum.CLOSESHORT: "空平",
                      tick_type_enum.CLOSEDOUBLE: "双平",
                      tick_type_enum.EXCHANGELONG: "多换", tick_type_enum.EXCHANGESHORT: "空换",
                      tick_type_enum.OPENUNKOWN: "未知开仓", tick_type_enum.CLOSEUNKOWN: "未知平仓",
                      tick_type_enum.EXCHANGEUNKOWN: "未知换仓",
                      tick_type_enum.UNKOWN: "未知", tick_type_enum.NOCHANGE: "没有变化",
                      tick_color_enum.RED: "红", tick_color_enum.GREEN: "绿", tick_color_enum.WHITE: "白"}
 
# 根据 open_interest_delta_forward_enum 和 order_forward_enum 计算出tick类型的字典
tick_type_cal_dict = {
    open_interest_delta_forward_enum.NONE:
        {
            order_forward_enum.UP: {tick_type_key_enum.TICKTYPE: tick_type_enum.NOCHANGE,
                                    tick_type_key_enum.TICKCOLOR: tick_color_enum.WHITE},
            order_forward_enum.DOWN: {tick_type_key_enum.TICKTYPE: tick_type_enum.NOCHANGE,
                                      tick_type_key_enum.TICKCOLOR: tick_color_enum.WHITE},
            order_forward_enum.MIDDLE: {tick_type_key_enum.TICKTYPE: tick_type_enum.NOCHANGE,
                                        tick_type_key_enum.TICKCOLOR: tick_color_enum.WHITE}
        },
    open_interest_delta_forward_enum.EXCHANGE:
        {
            order_forward_enum.UP: {tick_type_key_enum.TICKTYPE: tick_type_enum.EXCHANGELONG,
                                    tick_type_key_enum.TICKCOLOR: tick_color_enum.RED},
            order_forward_enum.DOWN: {tick_type_key_enum.TICKTYPE: tick_type_enum.EXCHANGESHORT,
                                      tick_type_key_enum.TICKCOLOR: tick_color_enum.GREEN},
            order_forward_enum.MIDDLE: {tick_type_key_enum.TICKTYPE: tick_type_enum.EXCHANGEUNKOWN,
                                        tick_type_key_enum.TICKCOLOR: tick_color_enum.WHITE}
        },
    open_interest_delta_forward_enum.OPENFWDOUBLE:
        {
            order_forward_enum.UP: {tick_type_key_enum.TICKTYPE: tick_type_enum.OPENDOUBLE,
                                    tick_type_key_enum.TICKCOLOR: tick_color_enum.RED},
            order_forward_enum.DOWN: {tick_type_key_enum.TICKTYPE: tick_type_enum.OPENDOUBLE,
                                      tick_type_key_enum.TICKCOLOR: tick_color_enum.GREEN},
            order_forward_enum.MIDDLE: {tick_type_key_enum.TICKTYPE: tick_type_enum.OPENDOUBLE,
                                        tick_type_key_enum.TICKCOLOR: tick_color_enum.WHITE}
        },
    open_interest_delta_forward_enum.OPEN:
        {
            order_forward_enum.UP: {tick_type_key_enum.TICKTYPE: tick_type_enum.OPENLONG,
                                    tick_type_key_enum.TICKCOLOR: tick_color_enum.RED},
            order_forward_enum.DOWN: {tick_type_key_enum.TICKTYPE: tick_type_enum.OPENSHORT,
                                      tick_type_key_enum.TICKCOLOR: tick_color_enum.GREEN},
            order_forward_enum.MIDDLE: {tick_type_key_enum.TICKTYPE: tick_type_enum.OPENUNKOWN,
                                        tick_type_key_enum.TICKCOLOR: tick_color_enum.WHITE}
        },
    open_interest_delta_forward_enum.CLOSEFWDOUBLE:
        {
            order_forward_enum.UP: {tick_type_key_enum.TICKTYPE: tick_type_enum.CLOSEDOUBLE,
                                    tick_type_key_enum.TICKCOLOR: tick_color_enum.RED},
            order_forward_enum.DOWN: {tick_type_key_enum.TICKTYPE: tick_type_enum.CLOSEDOUBLE,
                                      tick_type_key_enum.TICKCOLOR: tick_color_enum.GREEN},
            order_forward_enum.MIDDLE: {tick_type_key_enum.TICKTYPE: tick_type_enum.CLOSEDOUBLE,
                                        tick_type_key_enum.TICKCOLOR: tick_color_enum.WHITE}
        },
    open_interest_delta_forward_enum.CLOSE:
        {
            order_forward_enum.UP: {tick_type_key_enum.TICKTYPE: tick_type_enum.CLOSESHORT,
                                    tick_type_key_enum.TICKCOLOR: tick_color_enum.RED},
            order_forward_enum.DOWN: {tick_type_key_enum.TICKTYPE: tick_type_enum.CLOSELONG,
                                      tick_type_key_enum.TICKCOLOR: tick_color_enum.GREEN},
            order_forward_enum.MIDDLE: {tick_type_key_enum.TICKTYPE: tick_type_enum.CLOSEUNKOWN,
                                        tick_type_key_enum.TICKCOLOR: tick_color_enum.WHITE}
        },
}
 
# 只与计算对手单的组成相关，只有4种tick类型才需要计算对手单的组成
handicap_dict = {tick_type_enum.OPENLONG: {opponent_key_enum.OPPOSITE: tick_type_enum.CLOSELONG,
                                           opponent_key_enum.SIMILAR: tick_type_enum.OPENSHORT},
                 tick_type_enum.OPENSHORT: {opponent_key_enum.OPPOSITE: tick_type_enum.CLOSESHORT,
                                            opponent_key_enum.SIMILAR: tick_type_enum.OPENLONG},
                 tick_type_enum.CLOSELONG: {opponent_key_enum.OPPOSITE: tick_type_enum.OPENLONG,
                                            opponent_key_enum.SIMILAR: tick_type_enum.CLOSESHORT},
                 tick_type_enum.CLOSESHORT: {opponent_key_enum.OPPOSITE: tick_type_enum.OPENSHORT,
                                             opponent_key_enum.SIMILAR: tick_type_enum.CLOSELONG}
                 }
 

class CFtdcMdSpi(mdapi.CThostFtdcMdSpi):

    def __init__(self,tapi):
        mdapi.CThostFtdcMdSpi.__init__(self)
        self.tapi=tapi
        self.PreDepthMarketData = None
            
    def OnFrontConnected(self) -> "void":
        print ("OnFrontConnected")
        loginfield = mdapi.CThostFtdcReqUserLoginField()
        loginfield.BrokerID="8000"
        loginfield.UserID="000005"
        loginfield.Password="123456"
        loginfield.UserProductInfo="python dll"
        self.tapi.ReqUserLogin(loginfield,0)
        
    def OnRspUserLogin(self, pRspUserLogin: 'CThostFtdcRspUserLoginField', pRspInfo: 'CThostFtdcRspInfoField', nRequestID: 'int', bIsLast: 'bool') -> "void":
        print (f"OnRspUserLogin, SessionID={pRspUserLogin.SessionID},ErrorID={pRspInfo.ErrorID},ErrorMsg={pRspInfo.ErrorMsg}")
        ret=self.tapi.SubscribeMarketData([id.encode('utf-8') for id in subID],len(subID))

    def OnRtnDepthMarketData(self, pDepthMarketData: 'CThostFtdcDepthMarketDataField') -> "void":
        depthdata={}
        depthdata['AskPrice1']=round(pDepthMarketData.AskPrice1,2)
        depthdata['AskVolume1']=pDepthMarketData.AskVolume1
        depthdata['BidPrice1']=round(pDepthMarketData.BidPrice1,2)
        depthdata['BidVolume1']=pDepthMarketData.BidVolume1
        depthdata['BidVolume1']=pDepthMarketData.BidVolume1
        depthdata['LastPrice']=round(pDepthMarketData.LastPrice,2)
        depthdata['Volume']=pDepthMarketData.Volume
        depthdata['OpenInterest']=pDepthMarketData.OpenInterest
        depthdata['UpdateTime']=pDepthMarketData.UpdateTime
        depthdata['UpdateMillisec']=pDepthMarketData.UpdateMillisec
        if self.PreDepthMarketData is not None:
            # 计算两tick之间的差值
            ask_price_delta = self.PreDepthMarketData['AskPrice1'] - depthdata['AskPrice1']
            ask_volume_delta = self.PreDepthMarketData['AskVolume1'] - depthdata['AskVolume1']
            bid_price_delta = self.PreDepthMarketData['BidPrice1'] - depthdata['BidPrice1']
            bid_volume_delta = self.PreDepthMarketData['BidVolume1'] - depthdata['BidVolume1']
            last_price_delta = self.PreDepthMarketData['LastPrice'] - depthdata['LastPrice']
            volume_delta = depthdata['Volume'] - self.PreDepthMarketData['Volume']
            open_interest_delta = int(depthdata['OpenInterest'] - self.PreDepthMarketData['OpenInterest'])
 
            # 显示字符串
            ask_price_delta_str = self.get_delta_str(self.PreDepthMarketData['AskPrice1'], depthdata['AskPrice1'])
            ask_volume_delta_str = self.get_delta_str(self.PreDepthMarketData['AskVolume1'], depthdata['AskVolume1'])
            bid_price_delta_str = self.get_delta_str(self.PreDepthMarketData['BidPrice1'], depthdata['BidPrice1'])
            bid_volume_delta_str = self.get_delta_str(self.PreDepthMarketData['BidVolume1'], depthdata['BidVolume1'])
            last_price_delta_str = self.get_delta_str(self.PreDepthMarketData['LastPrice'], depthdata['LastPrice'])
 
            # 如果ask或者bid价格对比上一个tick都发生了变化则不显示价格变化幅度
            if ask_price_delta != 0:
                ask_volume_delta_str = ''
            if bid_price_delta != 0:
                bid_volume_delta_str = ''
            # input1 计算订单是在ask范围内成交还是在bid范围内成交
            order_forward = self.get_order_forward(depthdata['LastPrice'], depthdata['AskPrice1'], depthdata['BidPrice1'],
                                                           self.PreDepthMarketData['LastPrice'],
                                                           self.PreDepthMarketData['AskPrice1'],
                                                           self.PreDepthMarketData['BidPrice1']) 
			# input2 计算仓位变化方向
            open_interest_delta_forward = self.get_open_interest_delta_forward(open_interest_delta,
                                                                                       volume_delta)  
            # f(input1,input2) = output1 根据成交区域和仓位变化方向计算出tick的类型
            tick_type_dict = tick_type_cal_dict[open_interest_delta_forward][order_forward]
            if open_interest_delta_forward != open_interest_delta_forward_enum.NONE:
                # 输出相关变量
                print ("Ask\t" + str(depthdata['AskPrice1']) + ask_price_delta_str + "\t" + str(
                    depthdata['AskVolume1']) + ask_volume_delta_str \
                      + "\tBid\t" + str(depthdata['BidPrice1']) + bid_price_delta_str + "\t" + str(
                    depthdata['BidVolume1']) + bid_volume_delta_str)
 
                print (str(depthdata['UpdateTime']) + "." + str(depthdata['UpdateMillisec']) \
                      + "\t" + str(depthdata['LastPrice']) + last_price_delta_str \
                      + "\t成交 " + str(volume_delta) \
                      + "\t增仓 " + str(open_interest_delta) \
                      + "\t" + tick_type_str_dict[tick_type_dict[tick_type_key_enum.TICKTYPE]] \
                      + "\t" + tick_type_str_dict[tick_type_dict[tick_type_key_enum.TICKCOLOR]])
 
                if tick_type_dict[tick_type_key_enum.TICKTYPE] in handicap_dict.keys():
                    order_opposite, order_similar = CFtdcMdSpi.get_order_combination(open_interest_delta,
                                                                                       volume_delta)
                    print ("对手单：" + tick_type_str_dict[
                              handicap_dict[tick_type_dict[tick_type_key_enum.TICKTYPE]][opponent_key_enum.OPPOSITE]] \
                          + " " + str(order_opposite) \
                          + "\t" + tick_type_str_dict[
                              handicap_dict[tick_type_dict[tick_type_key_enum.TICKTYPE]][opponent_key_enum.SIMILAR]] \
                          + " " + str(order_similar))
 
                print ('--------------------------------------')
        self.PreDepthMarketData = copy.copy(depthdata)

    def OnRspSubMarketData(self, pSpecificInstrument: 'CThostFtdcSpecificInstrumentField', pRspInfo: 'CThostFtdcRspInfoField', nRequestID: 'int', bIsLast: 'bool') -> "void":
        print ("OnRspSubMarketData")
        print ("InstrumentID=",pSpecificInstrument.InstrumentID)
        print ("ErrorID=",pRspInfo.ErrorID)
        print ("ErrorMsg=",pRspInfo.ErrorMsg)
        
    @staticmethod
    def float_smaller_equal(smaller, bigger):
        return CFtdcMdSpi.float_bigger_equal(bigger, smaller)
 
    @staticmethod
    def float_bigger_equal(bigger, smaller):
        ret = False
        if abs(bigger - smaller) < 0.00001:
            ret = True
        elif bigger > smaller:
            ret = True
 
        return ret
 
    # ----------------------------------------------------------------------
    @staticmethod
    def get_open_interest_delta_forward(open_interest_delta, volume_delta):
        """根据成交量的差和持仓量的差来获取仓位变化的方向
            return: open_interest_delta_forward_enum
        """
        if open_interest_delta == 0 and volume_delta == 0:
            local_open_interest_delta_forward = open_interest_delta_forward_enum.NONE
        elif open_interest_delta == 0 and volume_delta > 0:
            local_open_interest_delta_forward = open_interest_delta_forward_enum.EXCHANGE
        elif open_interest_delta > 0:
            if open_interest_delta - volume_delta == 0:
                local_open_interest_delta_forward = open_interest_delta_forward_enum.OPENFWDOUBLE
            else:
                local_open_interest_delta_forward = open_interest_delta_forward_enum.OPEN
        elif open_interest_delta < 0:
            if open_interest_delta + volume_delta == 0:
                local_open_interest_delta_forward = open_interest_delta_forward_enum.CLOSEFWDOUBLE
            else:
                local_open_interest_delta_forward = open_interest_delta_forward_enum.CLOSE
        return local_open_interest_delta_forward
 
    # ----------------------------------------------------------------------
    @staticmethod
    def get_order_forward(last_price, ask_price1, bid_price1, pre_last_price, pre_ask_price1, pre_bid_price1):
        """获取成交的区域，根据当前tick的成交价和上个tick的ask和bid价格进行比对
           return: order_forward_enum
        """
        if CFtdcMdSpi.float_bigger_equal(last_price, pre_ask_price1):
            local_order_forward = order_forward_enum.UP
        elif CFtdcMdSpi.float_smaller_equal(last_price, pre_bid_price1):
            local_order_forward = order_forward_enum.DOWN
        else:
            if CFtdcMdSpi.float_bigger_equal(last_price, ask_price1):
                local_order_forward = order_forward_enum.UP
            elif CFtdcMdSpi.float_smaller_equal(last_price, bid_price1):
                local_order_forward = order_forward_enum.DOWN
            else:
                local_order_forward = order_forward_enum.MIDDLE
 
        return local_order_forward
 
    # ----------------------------------------------------------------------
    @staticmethod
    def get_order_combination(open_interest_delta, volume_delta):
        """根据成交量变化和持仓量的变化计算出对手单的组合
            仓位变化方向相反的单
                order_opposite
            仓位变化方向相同的单
                order_similar
        """
        open_interest_delta = open_interest_delta if open_interest_delta > 0 else -open_interest_delta
        volume_delta_single_side = volume_delta / 2.0
        open_close_delta = open_interest_delta - volume_delta_single_side + 0.0
        order_similar = volume_delta_single_side / 2 + open_close_delta / 2
        order_opposite = volume_delta_single_side / 2 - open_close_delta / 2
 
        return int(order_opposite), int(order_similar)
 
    @staticmethod
    def get_delta_str(pre, data):
        offset_str = ''
        if data > pre:
            offset_str = '(+' + str(round((data - pre),2)) + ")"
        elif data < pre:
            offset_str = '(-' + str(round((pre - data),2)) + ")"
        else:
            pass
        return offset_str		

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