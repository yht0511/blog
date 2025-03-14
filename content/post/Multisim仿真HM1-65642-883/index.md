---
title: "Multisim仿真HM1-65642-883"
description: ""
date: 2025-03-14T20:54:26+08:00
lastmod: 2025-03-14T20:54:26+08:00
categories: ["计算机","硬件","Multisim","自制计算机项目"]
mermaid: true
draft: false
---

这两天刚好在自学计组，打算从零开始搓计算机，ALU什么就不说了，稍微记录下RAM仿真。

两片65642相连拓展至16位；

注意到E1始终接地，E2接时钟，控制芯片使能。

WG逻辑相反（写入和读取）。



![RAM](https://blog-cdn.yht.life/blog/2025/03/1420250314204255.png)

时钟信号来源于经典的NE555电路:

![捕获](https://blog-cdn.yht.life/blog/2025/03/1420250314204815.PNG)

测试使用以下电路，输出3.4v左右故增加与门。

测试写入读取均正常。

![捕获](https://blog-cdn.yht.life/blog/2025/03/1420250314204957.PNG)

测试写入读取均正常。

![捕获](https://blog-cdn.yht.life/blog/2025/03/1420250314205351.PNG)
# Multisim仿真HM1-65642-883

这两天刚好在自学计组，打算从零开始搓计算机，ALU什么就不说了，稍微记录下RAM仿真。

两片65642相连拓展至16位；

注意到E1始终接地，E2接时钟，控制芯片使能。

WG逻辑相反（写入和读取）。



![RAM](https://blog-cdn.yht.life/blog/2025/03/1420250314204255.png)

时钟信号来源于经典的NE555电路:

![捕获](https://blog-cdn.yht.life/blog/2025/03/1420250314204815.PNG)

测试使用以下电路，输出3.4v左右故增加与门。

测试写入读取均正常。

![捕获](https://blog-cdn.yht.life/blog/2025/03/1420250314204957.PNG)

测试写入读取均正常。

![捕获](https://blog-cdn.yht.life/blog/2025/03/1420250314205351.PNG)