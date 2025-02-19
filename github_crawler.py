"""
GitHub项目获取工具 v1.0
作者: 凡人
功能: 通过GitHub API获取指定关键词的项目信息，并将结果保存为CSV格式
创建时间: 2025年
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import threading
import os
import json
from tkinter.scrolledtext import ScrolledText
import csv
from datetime import datetime  # 添加datetime导入

CONFIG_FILE = "github_crawler.cfg"

def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            token_entry.insert(0, config.get('token', ''))
            save_token_var.set(True)
    except FileNotFoundError:
        pass

def save_config(token):
    with open(CONFIG_FILE, 'w') as f:
        json.dump({'token': token}, f)

def select_folder():
    folder = filedialog.askdirectory()
    if folder:
        path_var.set(folder)

def fetch_data():
    def task():
        try:
            # 获取输入参数
            token = token_entry.get()
            keyword = keyword_entry.get()
            count = int(count_entry.get())
            save_path = path_var.get()
            save_token = save_token_var.get()

            # 验证输入
            if not all([token, keyword, count > 0, save_path]):
                messagebox.showerror("错误", "请填写所有有效参数")
                return

            # 保存Token配置
            if save_token:
                save_config(token)
            else:
                if os.path.exists(CONFIG_FILE):
                    os.remove(CONFIG_FILE)

            # 更新状态
            status_label.config(text="正在获取中...", foreground='blue')
            
            # 设置GitHub API请求头
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            # 计算需要的页数
            per_page = 30  # GitHub API 默认每页30个结果
            pages = (count + per_page - 1) // per_page
            
            collected_repos = []
            
            # 分页获取仓库数据
            for page in range(1, pages + 1):
                # 构建API URL
                url = f'https://api.github.com/search/repositories?q={keyword}&sort=stars&order=desc&page={page}&per_page={per_page}'
                
                # 发送请求
                response = requests.get(url, headers=headers)
                
                if response.status_code != 200:
                    raise Exception(f"API请求失败: {response.status_code} - {response.text}")
                
                # 解析响应
                data = response.json()
                repos = data.get('items', [])
                
                # 收集仓库信息
                for repo in repos:
                    if len(collected_repos) >= count:
                        break
                    
                    repo_info = {
                        'name': repo['name'],
                        'full_name': repo['full_name'],
                        'description': repo['description'],
                        'url': repo['html_url'],
                        'stars': repo['stargazers_count'],
                        'forks': repo['forks_count'],
                        'language': repo['language']
                    }
                    collected_repos.append(repo_info)
                
                if len(collected_repos) >= count:
                    break
            
            # 生成当前时间的文件名
            current_time = datetime.now().strftime('%Y%m%d%H%M%S')
            output_file = os.path.join(save_path, f'{current_time}.csv')
            
            with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:  # 使用 utf-8-sig 添加 BOM 头
                writer = csv.DictWriter(f, fieldnames=['name', 'full_name', 'url', 'stars', 'forks', 'description'])
                writer.writeheader()
                for repo in collected_repos:
                    # 确保所有字段都是字符串，并处理可能的 None 值
                    row = {
                        'name': str(repo['name']),
                        'full_name': str(repo['full_name']),
                        'url': str(repo['url']),
                        'stars': str(repo['stars']),
                        'forks': str(repo['forks']),
                        'description': str(repo.get('description', '')).replace('\r', '').replace('\n', ' ')  # 处理换行符
                    }
                    writer.writerow(row)
            
            # 更新状态
            status_label.config(text=f"获取完成！已保存{len(collected_repos)}个仓库信息到: {output_file}", foreground='green')

        except Exception as e:
            messagebox.showerror("错误", str(e))
            status_label.config(text="发生错误", foreground='red')
    
    threading.Thread(target=task).start()

# 创建GUI界面
root = tk.Tk()
root.title("GitHub项目获取工具 v1.0")
root.geometry("750x600")

# 配置加载
save_token_var = tk.BooleanVar(value=False)

# 输入面板
input_frame = ttk.Frame(root, padding=10)
input_frame.pack(fill='x')

ttk.Label(input_frame, text="GitHub Token:").grid(row=0, column=0, sticky='w', pady=2)
token_entry = ttk.Entry(input_frame, width=50)
token_entry.grid(row=0, column=1, padx=5)

save_token_cb = ttk.Checkbutton(
    input_frame, 
    text="记住Token", 
    variable=save_token_var,
    command=lambda: save_config(token_entry.get()) if save_token_var.get() else None
)
save_token_cb.grid(row=0, column=2, padx=5)

ttk.Label(input_frame, text="搜索关键词:").grid(row=1, column=0, sticky='w', pady=2)
keyword_entry = ttk.Entry(input_frame, width=50)
keyword_entry.grid(row=1, column=1, columnspan=2, sticky='w', padx=5)

ttk.Label(input_frame, text="获取数量:").grid(row=2, column=0, sticky='w', pady=2)
count_entry = ttk.Entry(input_frame, width=50)
count_entry.grid(row=2, column=1, columnspan=2, sticky='w', padx=5)

# 路径选择
path_var = tk.StringVar()
ttk.Label(input_frame, text="保存路径:").grid(row=3, column=0, sticky='w', pady=2)
ttk.Entry(input_frame, textvariable=path_var, width=50).grid(row=3, column=1, sticky='w', padx=5)
ttk.Button(input_frame, text="选择文件夹", command=select_folder).grid(row=3, column=2)

# 操作按钮
ttk.Button(root, text="开始获取", command=fetch_data).pack(pady=10)

# 状态显示
status_label = ttk.Label(root, text="就绪", foreground='gray')
status_label.pack()

# Token申请说明面板
help_frame = ttk.LabelFrame(root, text="GitHub Token 申请步骤", padding=10)
help_frame.pack(fill='both', expand=True, padx=10, pady=10)

help_text = """1. 登录GitHub账号后访问：https://github.com/settings/tokens
2. 点击右上角 Generate new token → Generate new token (classic)
3. 填写备注（如：AI项目获取）
4. 勾选权限（至少选择 repo 权限组）
5. 点击页面底部 Generate token 按钮
6. 立即复制保存生成的token（关闭页面后不可再次查看）"""

help_label = ScrolledText(help_frame, wrap=tk.WORD, height=6, font=('Consolas', 10))
help_label.insert(tk.END, help_text)
help_label.configure(state='disabled')
help_label.pack(fill='both', expand=True)

# 加载已保存的配置
load_config()

root.mainloop()
