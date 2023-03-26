# ViliServer
本项目利用Python Socket编写的支持多线程的微型WebServer程序（仅支持返回静态页面）

## 命令行
```
git clone https://github.com/Lns-XueFeng/WebServer.git
cd WebServer
python server.py
```

## 概览
- api: 里面编写了一个server和一个client, 使用了socket基本的api
- server.py: 利用socket实现了一个微型的web服务器
- vilivili: 主要是对请求的解析以及响应的返回

## vili包
- templates: html模板
- config.py: 配置文件
- request.py: 实现了Request对象
- response.py: 实现了Response对象
- utils.py: 实现了render_template函数
- views.py: 实现了视图函数

## 主要逻辑
```
1.实现server服务端
    make_response(request)
        返回响应报文
    fire_server()
        多线程处理请求
    process_connect(data_socket)
        request = Request(req_msg)   # 解析请求体
        response = make_response(request)
        data_socket.sendall(response)

2.实现Request类
    解析出method、path、headers

3.实现Response类
    包装响应报文

4.实现make_response(request)函数
    html_data = route()   # 通过routes查询相应的函数
    response = Response(data, headers=headers, status=status)
    return bytes(response)
```
