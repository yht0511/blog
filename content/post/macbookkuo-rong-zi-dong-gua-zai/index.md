---
title: "macbook扩容:自动挂载"
description: ""
date: 2025-10-31T19:45:35+08:00
lastmod: 2025-10-31T19:45:35+08:00
categories: ["教程","笔记本","MacOS","脚本"]
mermaid: true
draft: false
---

## 前言

苹果存储比金子贵hhh 我电脑上有很多数据要存,其中一些还对延迟、带宽有要求,所以不能用nas或者云存储,于是想着给这台256g的小垃圾升级一下.

目前市面上有好几种方案:

+ 拆机更换固态芯片, 1T大概1000元左右,但是没了保修,而且有风险.
+ 外接硬盘,俗称“尿袋”,主打一个便宜和0风险.

最后买了个闪迪的256gU盘,160左右,上面可以安装一些不太常用的大软件,放一些数据什么的.

## 需求

需求是我希望插上之后,安装在U盘上的软件可以直接在启动台找到,而不是每次都要去finder里找.以及一些数据集什么的,希望插上之后能自动挂载到我的开发目录下,拔掉之后能自动卸载.于是让gemini写了个小脚本.

## 脚本

```apl
-- =================================================================
-- 自动挂载脚本 for macOS
-- =================================================================

on write_log(log_string)
	try
		-- display dialog log_string buttons {"好的"} default button "好的" with title "USB挂载调试" giving up after 5
	end try
	-- set log_file_path to (POSIX path of (path to desktop)) & "usb_mount_log.txt"
	-- do shell script "echo \"$(date '+%Y-%m-%d %H:%M:%S') --- " & quoted form of log_string & "\" >> " & quoted form of log_file_path
end write_log

on run {input, parameters}
	write_log("自动化流程已触发。")
	set myUSBName to "TECLAB"
	
	repeat with eachItem in input
		try
			set mountedVolumeName to name of (info for eachItem)
			if mountedVolumeName is myUSBName then
				write_log("U盘 '" & myUSBName & "' 已匹配。")
				set usbPath to POSIX path of eachItem
				set mountTxtPath to usbPath & "mount.txt"
				
				if (do shell script "if [ -f " & quoted form of mountTxtPath & " ]; then echo 'found'; else echo 'not found'; fi") is "found" then
					write_log("成功找到 mount.txt。")
					set receiptFilePath_posix to POSIX path of ((path to home folder as text) & "Library:Caches:" & myUSBName & "_mounted_links.txt")
					do shell script "> " & quoted form of receiptFilePath_posix
					set homePath to POSIX path of (path to home folder)
					
					set mountConfig to paragraphs of (read (POSIX file mountTxtPath))
					
					repeat with aLine in mountConfig
						set currentLine to aLine as string
						if (currentLine contains "->") and (character 1 of currentLine is not "#") then
							try
								set oldDelimiters to AppleScript's text item delimiters
								set AppleScript's text item delimiters to "->"
								set pathParts to text items of currentLine
								set AppleScript's text item delimiters to oldDelimiters
								
								set source_rel to do shell script "echo " & quoted form of (item 1 of pathParts) & " | xargs"
								set target_raw to do shell script "echo " & quoted form of (item 2 of pathParts) & " | xargs"
								
								if source_rel is not "" and target_raw is not "" then
									set source_full_pattern to usbPath & source_rel
									
									set target_full to target_raw
									if target_full starts with "~/" then
										set target_full to homePath & (text 2 thru -1 of target_full)
									end if
									
									write_log("处理中... 源: " & source_full_pattern & " -> 目标: " & target_full)
									
									-- 【核心逻辑: 检查源路径是否包含通配符】
									if source_full_pattern contains "*" then
										write_log("检测到通配符，切换到多对一链接模式。")
										set linkCommand to "TARGET_DIR=" & quoted form of target_full & "; " & ¬
											"RECEIPT_FILE=" & quoted form of receiptFilePath_posix & "; " & ¬
											"if [ -d \"$TARGET_DIR\" ]; then " & ¬
											"  for item in " & source_full_pattern & "; do " & ¬
											"    if [ -e \"$item\" ]; then " & ¬
											"      itemName=$(basename \"$item\"); " & ¬
											"      targetLink=\"$TARGET_DIR/$itemName\"; " & ¬
											"      if [ ! -e \"$targetLink\" ]; then " & ¬
											"        ln -s \"$item\" \"$targetLink\"; " & ¬
											"        echo \"$targetLink\" >> \"$RECEIPT_FILE\"; " & ¬
											"      fi; " & ¬
											"    fi; " & ¬
											"  done; " & ¬
											"fi"
										do shell script linkCommand
										write_log("【成功】通配符匹配的项目已处理完毕。")
									else
										-- 【标准一对一链接逻辑】
										if (do shell script "if [ -e " & quoted form of source_full_pattern & " ]; then echo 'yes'; else echo 'no'; fi") is "no" then
											write_log("【跳过】原因：U盘上的源路径不存在。")
										else if (do shell script "if [ -e " & quoted form of target_full & " ] || [ -L " & quoted form of target_full & " ]; then echo 'yes'; else echo 'no'; fi") is "yes" then
											write_log("【跳过】原因：Mac上的目标路径已存在同名项。")
										else
											write_log("检查通过，准备创建标准链接...")
											do shell script "mkdir -p \"$(dirname " & quoted form of target_full & ")\" && ln -s " & quoted form of source_full_pattern & " " & quoted form of target_full
											write_log("【成功】标准链接已创建！")
											do shell script "echo " & quoted form of target_full & " >> " & quoted form of receiptFilePath_posix
										end if
									end if
								end if
							on error errMsg
								write_log("【行处理错误】处理 '" & currentLine & "' 时出错: " & errMsg)
							end try
						end if
					end repeat
					write_log("所有任务处理完毕。")
				else
					write_log("【错误】在U盘根目录未找到 mount.txt 文件。")
				end if
			end if
		on error errMsg
			write_log("【脚本致命错误】：" & errMsg)
		end try
	end repeat
	return input
end run
```

```apl
-- =================================================================
-- 自动卸载脚本 for macOS
-- =================================================================

-- 在这里设置您的U盘名称，必须与挂载脚本中的名称完全一致
property myUSBName : "TECLAB"

-- on idle 处理程序会由系统定期调用
on idle
	-- 构建U盘应该被挂载的路径
	set usbVolumePath to "/Volumes/" & myUSBName
	
	-- 检查该路径是否存在
	try
		-- 如果do shell script成功，说明U盘还在，什么都不做
		do shell script "test -d " & quoted form of usbVolumePath
	on error
		-- 如果do shell script失败，说明路径不存在，即U盘已被拔出
		-- 开始执行卸载清理操作
		
		-- 构建“收据”文件的完整路径
		set receiptFileName to myUSBName & "_mounted_links.txt"
		set receiptFileHFSPath to (path to home folder as text) & "Library:Caches:" & receiptFileName
		set receiptFilePath_posix to POSIX path of receiptFileHFSPath
		
		try
			-- 读取收据文件，获取所有需要删除的链接路径列表
			set links_to_delete to paragraphs of (read (POSIX file receiptFilePath_posix))
			
			-- 遍历列表，逐个删除链接
			repeat with linkPath in links_to_delete
				if linkPath is not "" then
					-- 使用 rm 命令删除符号链接
					do shell script "rm " & quoted form of (linkPath as string)
				end if
			end repeat
			
			-- 所有链接都删除后，删除收据文件本身，完成清理
			do shell script "rm " & quoted form of receiptFilePath_posix
			
		on error
			-- 如果收据文件不存在或读取失败，说明没有需要清理的链接，
			-- 安静地忽略错误即可。
		end try
	end try
	
	-- 设置下一次检查的间隔时间（秒）
	return 15
end idle

-- on quit 处理程序确保即使用户尝试关闭它，它也能继续在后台运行
on quit
	continue quit
end quit
```

## 使用说明

> [!WARNING]
> 以下为AI生成

### **U盘自动挂载/卸载脚本 - 安装指南**

只需三步，即可让您的U盘实现“即插即用，即拔即走”的无缝体验。

#### **准备工作：**

1. **命名U盘**：确保您的U盘名称为 TECLAB。
2. **创建配置文件**：在U盘的**根目录**下，创建一个名为 mount.txt 的纯文本文件。

#### **mount.txt 配置文件格式：**

文件中的每一行代表一条链接规则，格式如下：
U盘内的源路径 -> Mac上的目标路径

**示例 mount.txt 内容：**


```
# 将U盘中所有.app文件链接到系统应用程序文件夹
Software/Applications/*.app -> /Applications

# 将整个工作文档文件夹链接到桌面
My Work Documents -> ~/Desktop/U盘工作文档

# 链接字体库
Fonts -> ~/Library/Fonts
```


### **安装步骤：**

#### **第一步：设置“自动挂载”**

这个脚本负责在U盘插入时创建链接。

1. 打开 **自动操作 (Automator)** 应用。
2. 选择“文件” > “新建”，文稿类型选取 **“文件夹操作”**。
3. 在顶部的下拉菜单“文件夹操作处理添加到以下位置的文件和文件夹”中，选择 **“选取其他...”**。
4. 在弹出的窗口中，按下 Command + Shift + G，输入 /Volumes 并前往，然后点击“选取”。
5. 从左侧的操作库中，将 **“运行 AppleScript”** 拖拽到右侧工作区。
6. **清空**默认代码，然后将下面的 **“挂载脚本”** 代码完整地粘贴进去。
7. 按下 Command + S 保存，命名为 自动挂载U盘脚本 即可。

**(在此处粘贴“挂载脚本”的完整代码)**

#### **第二步：设置“自动卸载”**

这个脚本负责在U盘拔出后清理链接。

1. 打开 **脚本编辑器 (Script Editor)** 应用 (在“应用程序” > “实用工具”里)。
2. 将下面的 **“卸载脚本”** 代码完整地粘贴进去。
3. 选择“文件” > “存储”：
   - **文件格式**：选择 **应用程序**。
   - **名称**：命名为 UninstallUSBApps。
   - **勾选**：**“闲置后保持打开”**。
   - 将它保存在您的“应用程序”文件夹中。
4. 将这个新创建的 UninstallUSBApps.app 设置为开机自启动：
   - 打开 **系统设置** > **通用** > **登录项**。
   - 在“登录时打开”区域点击 + 号，添加 UninstallUSBApps.app。
   - **可选（推荐）**：为了让它在后台完全隐形，请参考之前的指南修改其 Info.plist 文件，添加 LSUIElement 键。

**(在此处粘贴“卸载脚本”的完整代码)**

#### **第三步：完成！**

现在，拔出并重新插入您的U盘。所有在 mount.txt 中定义的链接应该都已自动创建。拔出U盘后，这些链接也会被自动清理。