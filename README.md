#biliappproxy v0.0.2

## 使用说明：
+ 1.启动服务：
源码文件请根据requirements.txt配置环境，运行python main.py启动服务程序，编译版直接运行biliappproxy.exe启动服务，将开启一个命令控制台
+ 2.获取服务访问令牌：
第一次运行将随机生成一个32位长度的服务访问令牌，可在命令行控制台及程序目录的users.yaml文件（KEY字段）中获取
+ 3.用浏览器登录web控制台：
默认地址是http://127.0.0.1:1211/, 填入第二步中获取的32位服务访问令牌，验证登录web控制台
在地址栏输入http://127.0.0.1:1211/?key=32位服务访问令牌, 可跳过认证页面直接访问web控制台
+ 4.添加、配置账号：
web控制台进入“配置”页面，填入access_key（可一次性填入多个access_key批量登录）
access_key可通过login_win.exe用移动端app扫码获取（项目地址：https://github.com/XiaoMiku01/fansMedalHelper/, 编译版已附带此程序。）
+ 5.调用服务：
默认服务地址：http://127.0.0.1:1211/proxy?key=32位服务访问令牌
前端调用此代理服务的类可在程序目录\static\js\biliutils.js里找到
例子可以参考web控制台的“测试”页面

##注意事项：程序目录下的users.yaml存放了用户的B站账号access_key，请勿将此文件复制给别人

##配置文件参考：
```yaml
USERS:
  - access_key: 32位access_key1
  - access_key: 32位access_key2
  - access_key: 32位access_key3
KEY: 32位服务访问令牌
HOST: 监听地址
PORT: 监听端口
```




