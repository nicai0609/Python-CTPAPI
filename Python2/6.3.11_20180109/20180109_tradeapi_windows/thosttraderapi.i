%module(directors="1") thosttraderapi 
%{ 
#include "ThostFtdcTraderApi.h"
%}
%feature("director") CThostFtdcTraderSpi; 
%ignore THOST_FTDC_VTC_BankBankToFuture;
%ignore THOST_FTDC_VTC_BankFutureToBank;
%ignore THOST_FTDC_VTC_FutureBankToFuture;
%ignore THOST_FTDC_VTC_FutureFutureToBank;
%ignore THOST_FTDC_FTC_BankLaunchBankToBroker;
%ignore THOST_FTDC_FTC_BrokerLaunchBankToBroker;
%ignore THOST_FTDC_FTC_BankLaunchBrokerToBank;
%ignore THOST_FTDC_FTC_BrokerLaunchBrokerToBank;  
%feature("director") CThostFtdcTraderSpi; 
%include "ThostFtdcUserApiDataType.h"
%include "ThostFtdcUserApiStruct.h" 
%include "ThostFtdcTraderApi.h"