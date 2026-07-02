#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Calculator Django Project - 启动脚本

使用方式:
    python run.py

默认启动在 http://127.0.0.1:8000/
"""

import os
import sys
import subprocess


def main():
    # 确保当前目录是项目根目录
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)

    # 将项目目录加入 Python 路径
    sys.path.insert(0, project_dir)

    # 设置 Django 环境变量
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'calculator_project.settings')

    # 执行迁移（创建数据库表）
    print("[*] 正在执行数据库迁移...")
    subprocess.run([sys.executable, 'manage.py', 'migrate'], check=True)

    # 启动开发服务器
    print("[*] 启动 Django 开发服务器...")
    print("[*] 访问地址: http://127.0.0.1:8000/")
    print("[*] API 地址: http://127.0.0.1:8000/api/")
    print("[*] 按 Ctrl+C 停止服务器")
    print()

    try:
        subprocess.run([sys.executable, 'manage.py', 'runserver', '0.0.0.0:8000'])
    except KeyboardInterrupt:
        print("\n[*] 服务器已停止")


if __name__ == '__main__':
    main()
