import os
import time
import git
import sys
import shutil
import tkinter
from tkinter.messagebox import *

def rmdir(path):
    shutil.rmtree(path)

repo_url = "https://github.com/yht0511/blog.git"
repo_name = "blog"
typora_path = r"D:\Software\Typora\Typora.exe"


def new(filepath):
    # Get the current file directory
    cwd = os.path.dirname(os.path.abspath(__file__))
    # Get the temp directory
    temp_dir = os.path.join(cwd, "temp_"+repo_name)
    os.chdir(temp_dir)
    # If exists
    if os.path.exists(temp_dir):
        os.popen("git pull").read()
    else:
        git.Repo.clone_from(repo_url, temp_dir)
    # Get the file
    with open(filepath, "r") as f:
        data = f.read()
    # Create blog
    r=os.popen("hugo new post/未指定标题/index.md").read()
    print(r)
    # Write the file
    with open(temp_dir+"/content/post/未指定标题/index.md", "a") as f:
        f.write("\n")
        f.write(data)
    # Open by typora
    os.popen(typora_path+" \""+temp_dir+"/content/post/未指定标题/index.md\"").read()
    if not alert("是否提交?"): return
    # Get the title
    title = ""
    with open(temp_dir+"/content/post/未指定标题/index.md", "r") as f:
        d = f.read()
        title = d.split("---")[1].split("\n")[1].split(":")[1].strip()
        if title[0]=="\"":
            title = title[1:-1]
    # Change the directory
    if os.path.exists(temp_dir+"/content/post/"+title+"/"):
        rmdir(temp_dir+"/content/post/"+title+"/")
    os.rename(temp_dir+"/content/post/未指定标题/", temp_dir+"/content/post/"+title+"/")
    time.sleep(1)
    # Commit the change
    os.popen("hugo").read()
    os.popen("git add . ").read()
    os.popen("git commit -m \"添加新文章.\"").read()
    os.popen("git push").read()
    
def remove(name):
    # Get the current working directory
    cwd = os.path.dirname(os.path.abspath(__file__))
    temp_dir = os.path.join(cwd, "temp_"+repo_name)
    os.chdir(temp_dir)
    # If exists
    if os.path.exists(temp_dir):
        os.popen("git pull").read()
    else:
        git.Repo.clone_from(repo_url, temp_dir)
    if not alert(f"是否删除:{name}?"): return
    rmdir(temp_dir+"/content/post/"+name)
    # Commit the change 
    # os.popen("cd "+temp_dir+" && hugo &&git add . && git commit -m \"删除文章.\" && git push").read()
    os.popen("hugo").read()
    os.popen("git add . ").read()
    os.popen("git commit -m \"删除文章.\"").read()
    os.popen("git push").read()

def alert(msg):
    result = askyesnocancel("yht.life", msg)
    return result
    
    
if __name__ == "__main__":
    window = tkinter.Tk()
    window.withdraw()  # 退出默认 tk 窗口
    if len(sys.argv)!=3:
        print("Usage: python upload.py [new|remove] [filepath|name]")
        sys.exit(1)
    if sys.argv[1]=="new":
        new(sys.argv[2])
    elif sys.argv[1]=="remove":
        remove(sys.argv[2])