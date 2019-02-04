# Python-CTPAPI

# 基于python2即将停止更新，这里不提供了，需要的可以根据教程自己生成
# CTP有的返回字段是中文gbk编码的，python3中直接print会出问题，所以中文字段这里采用如下方式`.encode("utf-8",errors='surrogateescape').decode('gbk')`，详见demo。
# 关于SubscribeMarketData这个函数的C++二级指针也找到了更好的方法解决，通过将python list转化为c++二级指针。注意传入合约参数的时候记得b"cu1906"的形式，详见mdapidemo。
# 文章参考https://blog.csdn.net/pjjing/article/details/77338423
# 欢迎加入QQ群：767101469，讨论交流
