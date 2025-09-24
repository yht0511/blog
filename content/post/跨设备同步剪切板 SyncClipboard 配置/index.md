---
title: "跨设备同步剪切板 (SyncClipboard) 配置"
description: "配置 SyncClipboard 实现跨设备(Windows, macOS, Linux)同步剪切板，并使用自签名TLS证书保障安全。"
date: 2025-09-24T10:59:01+08:00
lastmod: 2025-09-24T10:59:01+08:00
categories: ["编程","配置","工具"]
mermaid: true
draft: false
---

# 跨设备同步剪切板 (SyncClipboard) 配置

最近搞了台macbook，本来说要用微软的Remote Desktop连接Windows服务器，但是macos本身还挺好用的，想想还是直接用mac写代码好了。但是这就牵扯到跨设备同步，本身文件已经有nas了，但是剪切板还没有。最后发现SyncClipboard不错，配置一下挺好。最开始是http，感觉校园网还是不安全，搞个tls吧。

## 配置流程

### 创建 OpenSSL 配置文件

```bash
cat <<EOF > /Docker/clipboard/certs/openssl.cnf
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_req
prompt = no

[req_distinguished_name]
C = CN                          # 国家代码，例如中国
ST = Province                   # 省份
L = City                        # 城市
O = Organization                # 组织
OU = Unit                       # 部门
CN = [你的服务器IP]             # 你的服务器IP地址作为通用名

[v3_req]
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
IP.1 = [你的服务器IP]           # 你的服务器IP地址
EOF
```

### 生成自签名 HTTPS 证书

```bash
openssl req -x509 -newkey rsa:4096 -nodes -keyout /Docker/clipboard/certs/key.pem -out /Docker/clipboard/certs/cert.pem -days 365 -config /Docker/clipboard/certs/openssl.cnf
```

### 创建并配置 `appsettings.json` 文件

```bash
cat <<EOF > /Docker/clipboard/config/appsettings.json
{
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft.AspNetCore": "Warning"
    }
  },
  "AllowedHosts": "*",
  "Kestrel": {
    "Endpoints": {
      "https": {
        "Url": "https://*:5033"
      }
    },
    "Certificates": {
      "Default": {
        "Path": "/app/certs/cert.pem",
        "KeyPath": "/app/certs/key.pem"
      }
    }
  },
  "AppSettings": {
    "UserName": "will_be_overridden_by_env_var",
    "Password": "will_be_overridden_by_env_var"
  }
}
EOF
```

### 运行 SyncClipboard Docker 容器

```bash
docker run -d \
  --name=syncclipboard-server \
  -p 5033:5033 \
  -e SYNCCLIPBOARD_USERNAME=admin \
  -e SYNCCLIPBOARD_PASSWORD=你的密码 \
  --restart unless-stopped \
  -v /Docker/clipboard/config/appsettings.json:/app/appsettings.json \
  -v /Docker/clipboard/certs/cert.pem:/app/certs/cert.pem \
  -v /Docker/clipboard/certs/key.pem:/app/certs/key.pem \
  jericx/syncclipboard-server:latest
```

根据实际情况替换 `CN` 和 `IP.1` 为你的服务器 IP 地址，并将 `你的密码` 替换为实际的密码。



剩下就是在各个设备上安装 SyncClipboard 客户端，配置服务器地址和账号密码即可。

发现一个小bug：如果mac上成功配置了https，并且不允许不安全的证书，那么有概率触发“空文件”的bug，下载模块会坏掉。应该是这程序问题。