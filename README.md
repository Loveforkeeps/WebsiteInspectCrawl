# WebsiteInspectCrawl
Get site information by creating a website class

## 实现理念

（网站分类）页面信息抓取模仿用户态，要获取在实际访问中可以看见的页面信息

### 网站请求实现

建立网站对象的类，接受Url参数，在类的初始化中，实现网站信息获取，init函数中会若是请求失败则会再次实例化，次数可以设定（内部重连实现）。

类的静态变量中，有个访问失败list，其中会存储指定重连之后仍然无法访问的url，可以供外界读取（外部失败重连实现）

### 网站信息获取

在类的成员方法中用以下多种方式实现，根据实际需求选择方法，满足之后的可拓展性。
* 使用正则匹配
```
    def get_content(self):
        if self.hascontent:
            pattern = re.compile('<[^>]*>')
            content = pattern.sub('',self.content)
            return content
    # 测试效果：无法去除大量js代码
```
* 使用bs4库 （使用lxml解析，速度快容错性高）
* 使用Xpath和lxml 
* pyquery  text()函数直接返回页面中所有的文本信息，与之前正则获取中文词，做性能和需求满足比较
* 动态网站抓取Selenium 与 firefox 方式

### 分词

对以下三种分词库，根据需求进行性能测试
* jieba
* THULAC
* FoolNLTK

[参考链接](https://cuiqingcai.com/5844.html)

### 网站技术架构
* bulitwith 
* 部分从header中获取（buitwith不显示服务器版本信息，是否从header获取取决于需求度）


### 开发日志
2018-03-31
去除script和style，
Target=p.url,Url=p.res.url,Title=p.pq_get_title(),Content=p.get_content()
缺陷： js跳转无法正常跳转


2018-04-03
ubuntu 安装 firefox，实现headless模式下的网页截图

2018-04-15
新增根据domain判断是http还是https的方法（应对top1mlist的需求）



