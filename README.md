# Python-CTPAPI

# 基于python2即将停止更新，这里不提供了，需要的可以根据教程自己生成。目前github中升级到了3.7.2版本。
# 6.3.11_20180109是非穿透式生产版本，6.3.15_20190220是最新的穿透式版本。
# CTP有的返回字段是中文gbk编码的，通过在C++中转换为utf-8编码方式，终于成功解决了这问题，现在中文可以直接print，详见blog。
# 关于SubscribeMarketData这个函数的C++二级指针也找到了更好的方法解决，通过将python list转化为c++二级指针。注意传入合约参数的时候记得b"cu1906"的形式，详见mdapidemo。
# 文章参考https://blog.csdn.net/pjjing/article/details/77338423，demo都附在文中。
# 欢迎加入QQ群：767101469，讨论交流
