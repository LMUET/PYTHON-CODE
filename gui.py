import os
import re
import subprocess
import sys
import platform
import socket
import time
import random
import string
import threading
import concurrent.futures
import json
from urllib.parse import urlparse
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import ctypes
from ctypes import wintypes

# 隐藏启动时的控制台窗口
if platform.system() == "Windows":
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

class MinecraftIPv6ToolGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Minecraft联机工具 - 2.5.8 - Lyt_IT")
        self.root.geometry("900x760")
        self.root.resizable(True, True)
        
        # 设置程序图标
        self.set_window_icon()
        
        # 检查管理员权限
        self.is_admin = self.check_admin_privileges()
        
        self.ipv6 = ""
        self.mc_port = None
        self.mc_ports = [25565, 25566, 25567, 19132, 19133]
        self.available_nodes = []
        self.best_node = None
        self.all_nodes_cache = []  # 缓存所有节点信息
        
        # 端口映射相关变量
        self.port_mapping_process = None
        self.is_port_mapping_active = False
        self.mapped_port = None
        
        # 创建主框架
        self.create_main_frame()
        
        # 状态变量
        self.is_scanning = False
        self.is_connecting = False
        
        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def set_window_icon(self):
        """设置窗口图标"""
        try:
            # 尝试使用当前目录下的 lyy.ico 文件
            icon_path = "lyy.ico"
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
            else:
                # 如果找不到 lyy.ico，尝试其他可能的路径
                possible_paths = [
                    "./lyy.ico",
                    "lyy.ico",
                    os.path.join(os.path.dirname(__file__), "lyy.ico"),
                    os.path.join(os.path.dirname(sys.executable), "lyy.ico")
                ]
                for path in possible_paths:
                    if os.path.exists(path):
                        self.root.iconbitmap(path)
                        break
                else:
                    print("未找到 lyy.ico 图标文件，使用默认图标")
        except Exception as e:
            print(f"设置图标失败: {e}")
    
    def check_admin_privileges(self):
        """检查是否具有管理员权限"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def request_admin_privileges(self):
        """请求管理员权限 - 重新启动程序并请求UAC提升"""
        if self.is_admin:
            return True
            
        try:
            # 获取当前可执行文件路径
            if getattr(sys, 'frozen', False):
                # 如果是打包后的exe文件
                current_file = sys.executable
            else:
                # 如果是Python脚本
                current_file = sys.argv[0]
            
            # 使用shell执行请求管理员权限
            result = ctypes.windll.shell32.ShellExecuteW(
                None, 
                "runas", 
                current_file, 
                " ".join(sys.argv[1:]), 
                None, 
                1
            )
            
            if result > 32:
                # 成功启动管理员权限进程
                self.log("✅ 已请求管理员权限，请在新窗口中继续操作")
                # 退出当前实例
                self.root.quit()
                return True
            else:
                self.log("❌ 请求管理员权限失败")
                return False
                
        except Exception as e:
            self.log(f"❌ 请求管理员权限失败: {e}")
            return False
    
    def create_main_frame(self):
        """创建主界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题框架
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = ttk.Label(title_frame, text="🎮 Minecraft联机工具", 
                               font=("Arial", 16, "bold"))
        title_label.pack()
        
        # 显示管理员权限状态
        admin_status = "✅ 已获取管理员权限" if self.is_admin else "⚠️ 未获取管理员权限"
        admin_label = ttk.Label(title_frame, text=admin_status, 
                               foreground="green" if self.is_admin else "red")
        admin_label.pack(pady=2)
        
        author_label = ttk.Label(title_frame, text="作者: Lyt_IT | QQ: 2232908600", 
                                font=("Arial", 10))
        author_label.pack(pady=5)
        
        # 模式选择框架
        mode_frame = ttk.LabelFrame(main_frame, text="选择联机模式", padding="15")
        mode_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # IPv6模式按钮
        self.ipv6_btn = ttk.Button(mode_frame, text="🌐 IPv6获取联机地址（推荐，速度快，端口自动识别）", 
                                  command=self.run_ipv6_mode, width=80)
        self.ipv6_btn.pack(pady=10)
        
        # EasyTier创建房间按钮
        self.et_create_btn = ttk.Button(mode_frame, text="🏠 EasyTier联机 - 创建房间（端口必须为25565）", 
                                       command=self.run_easytier_create, 
                                       width=80)
        self.et_create_btn.pack(pady=10)
        
        # EasyTier加入房间按钮
        self.et_join_btn = ttk.Button(mode_frame, text="🔗 EasyTier联机 - 进入房间", 
                                     command=self.run_easytier_join, 
                                     width=80)
        self.et_join_btn.pack(pady=10)
        
        # 端口映射按钮
        self.port_map_btn = ttk.Button(mode_frame, text="🔄 将其他端口映射至25565", 
                                      command=self.run_port_mapping, 
                                      width=80)
        self.port_map_btn.pack(pady=10)
        
        # 状态显示区域
        status_frame = ttk.LabelFrame(main_frame, text="状态信息", padding="10")
        status_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.status_text = scrolledtext.ScrolledText(status_frame, height=20, width=80)
        self.status_text.pack(fill=tk.BOTH, expand=True)
        
        # 底部按钮框架
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=10)
        
        clear_btn = ttk.Button(bottom_frame, text="清空日志", command=self.clear_log)
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        help_btn = ttk.Button(bottom_frame, text="使用帮助", command=self.show_help)
        help_btn.pack(side=tk.LEFT, padx=5)
        
        exit_btn = ttk.Button(bottom_frame, text="退出程序", command=self.root.quit)
        exit_btn.pack(side=tk.RIGHT, padx=5)
        
    def lock_buttons(self):
        """锁定所有联机按钮"""
        self.ipv6_btn.config(state='disabled')
        self.et_create_btn.config(state='disabled')
        self.et_join_btn.config(state='disabled')
        self.port_map_btn.config(state='disabled')
        self.root.update()
        
    def unlock_buttons(self):
        """解锁所有联机按钮"""
        self.ipv6_btn.config(state='normal')
        self.et_create_btn.config(state='normal')
        self.et_join_btn.config(state='normal')
        self.port_map_btn.config(state='normal')
        self.root.update()
    
    def log(self, message):
        """添加日志到状态区域"""
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_log(self):
        """清空日志"""
        self.status_text.delete(1.0, tk.END)
    
    def show_help(self):
        """显示帮助信息"""
        help_window = tk.Toplevel(self.root)
        help_window.title("使用帮助")
        help_window.geometry("600x400")
        
        # 设置帮助窗口图标
        try:
            icon_path = "lyy.ico"
            if os.path.exists(icon_path):
                help_window.iconbitmap(icon_path)
        except:
            pass
        
        help_text = scrolledtext.ScrolledText(help_window, width=70, height=20)
        help_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        help_content = """
Minecraft联机工具使用说明

🌐 IPv6联机模式：
- 需要双方都有IPv6网络支持
- 速度快，延迟低
- 自动检测IPv6地址和Minecraft端口
- 自动复制联机地址到剪贴板

🏠 EasyTier创建房间：
- 无需IPv6，使用中转服务器
- 需要管理员权限
- 自动选择最佳节点
- 生成随机房间号
- 自动启动EasyTier服务

🔗 EasyTier进入房间：
- 输入朋友分享的房间号
- 需要管理员权限
- 自动连接到对应节点
- 自动启动EasyTier服务

🔄 端口映射功能：
- 将其他Minecraft端口映射到25565
- 方便使用非标准端口的服务器
- 自动关闭防火墙规则
- 程序退出时自动清理映射

管理员权限说明：
- EasyTier需要管理员权限来创建虚拟网络适配器
- 端口映射需要管理员权限修改防火墙规则
- 请以管理员权限运行本联机工具
- 如果未获取管理员权限，程序会自动提示

常见问题：
1. 如果无法连接，请检查防火墙设置
2. 确保已开启Minecraft局域网游戏
3. EasyTier模式需要管理员权限
4. 联机时不要关闭程序窗口

技术支持：
QQ: 2232908600
微信: liuyvetong
        """
        
        help_text.insert(1.0, help_content)
        help_text.config(state=tk.DISABLED)
        
        close_btn = ttk.Button(help_window, text="关闭", command=help_window.destroy)
        close_btn.pack(pady=10)
    
    def validate_ipv6(self, ipv6):
        """验证IPv6地址格式"""
        ipv6_pattern = r'^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$|^::1$|^([0-9a-fA-F]{1,4}:){1,7}:|^:(:[0-9a-fA-F]{1,4}){1,7}$'
        return re.match(ipv6_pattern, ipv6) is not None
    
    def get_ipv6_powershell(self):
        """使用PowerShell获取IPv6地址"""
        try:
            ps_command = """
            Get-NetIPAddress -AddressFamily IPv6 | 
            Where-Object {
                $_.PrefixOrigin -eq 'RouterAdvertisement' -and 
                $_.SuffixOrigin -ne 'Link' -and 
                $_.IPAddress -notlike 'fe80*' -and 
                $_.IPAddress -notlike 'fc*' -and 
                $_.IPAddress -notlike 'fd*' -and 
                $_.IPAddress -ne '::1'
            } | 
            Select-Object -First 1 -ExpandProperty IPAddress
            """
            
            result = subprocess.run(
                ["powershell", "-Command", ps_command], 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            ipv6 = result.stdout.strip()
            if ipv6 and self.validate_ipv6(ipv6):
                return ipv6
        except Exception:
            pass
        
        return None
    
    def get_ipv6_ipconfig(self):
        """使用ipconfig获取IPv6地址"""
        try:
            result = subprocess.run(["ipconfig"], capture_output=True, text=True, check=True)
            lines = result.stdout.split('\n')
            
            for line in lines:
                if "IPv6" in line and ":" in line:
                    parts = line.split(":")
                    if len(parts) > 1:
                        ipv6 = parts[1].strip()
                        self.log(f"检查地址: {ipv6}")
                        
                        if re.match(r"^2[0-9a-f][0-9a-f][0-9a-f]:", ipv6) and self.validate_ipv6(ipv6):
                            return ipv6
        except Exception:
            pass
        
        return None
    
    def copy_to_clipboard(self, text):
        """复制文本到剪贴板"""
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            return True
        except Exception:
            return False
    
    def is_port_occupied(self, port):
        """检查端口是否被占用"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('127.0.0.1', port))
                return result == 0
        except Exception:
            return False

    def is_port_occupied_by_java_original(self, port):
        """原始的检查端口是否被Java进程占用逻辑"""
        try:
            if platform.system() == "Windows":
                # 使用netstat查找指定端口的进程
                result = subprocess.run(
                    ["netstat", "-ano"], 
                    capture_output=True, 
                    text=True, 
                    check=True
                )
                lines = result.stdout.split('\n')
                
                for line in lines:
                    if f":{port}" in line and "LISTENING" in line:
                        # 提取PID
                        parts = line.split()
                        for part in parts:
                            if part.isdigit() and len(part) > 3:
                                pid = part
                                # 检查该PID是否为Java进程
                                task_result = subprocess.run(
                                    ["tasklist", "/fi", f"pid eq {pid}", "/fo", "csv"], 
                                    capture_output=True, 
                                    text=True, 
                                    check=True
                                )
                                if "java.exe" in task_result.stdout:
                                    self.log(f"端口 {port} 被Java进程占用 (PID: {pid})")
                                    return True
                return False
            else:
                # Linux/macOS
                result = subprocess.run(
                    ["lsof", "-i", f":{port}"], 
                    capture_output=True, 
                    text=True, 
                    check=True
                )
                return "java" in result.stdout
                
        except Exception as e:
            self.log(f"检查端口占用时出错: {e}")
            return False

    def is_port_occupied_by_java(self, port):
        """检查端口是否被Java进程占用 - 修改版，支持端口映射"""
        # 如果端口映射激活且检查的是25565端口，则检查映射的源端口
        if self.is_port_mapping_active and port == 25565 and self.mapped_port:
            self.log(f"🔀 端口映射激活中，检查映射源端口 {self.mapped_port}")
            return self.is_port_occupied_by_java_original(self.mapped_port)
        
        return self.is_port_occupied_by_java_original(port)
    
    def get_java_process_ports(self):
        """获取Java进程监听的端口 - 使用命令行版的逻辑"""
        java_ports = []
        
        try:
            if platform.system() == "Windows":
                # 使用netstat -ano 查找所有监听端口
                result = subprocess.run(
                    ["netstat", "-ano"], 
                    capture_output=True, 
                    text=True, 
                    check=True
                )
                lines = result.stdout.split('\n')
                
                # 获取所有Java进程的PID
                java_pids = set()
                task_result = subprocess.run(
                    ["tasklist", "/fi", "imagename eq java.exe", "/fo", "csv"], 
                    capture_output=True, 
                    text=True, 
                    check=True
                )
                for line in task_result.stdout.split('\n'):
                    if 'java.exe' in line:
                        parts = line.split(',')
                        if len(parts) >= 2:
                            pid = parts[1].strip('"')
                            if pid.isdigit():
                                java_pids.add(pid)
                
                # 查找Java进程监听的端口
                for line in lines:
                    if "LISTENING" in line:
                        # 提取端口和PID
                        parts = line.split()
                        for part in parts:
                            if ":" in part and "[" not in part:
                                try:
                                    port_str = part.split(":")[-1]
                                    port = int(port_str)
                                    # 查找PID
                                    for p in parts:
                                        if p.isdigit() and len(p) > 3:  # PID通常大于1000
                                            if p in java_pids and port not in java_ports:
                                                java_ports.append(port)
                                                self.log(f"发现Java进程监听端口: {port}")
                                                break
                                except ValueError:
                                    continue
                
            else:
                # Linux/macOS 使用 lsof
                result = subprocess.run(
                    ["lsof", "-i", "-P", "-n"], 
                    capture_output=True, 
                    text=True, 
                    check=True
                )
                for line in result.stdout.split('\n'):
                    if "java" in line and "LISTEN" in line:
                        parts = line.split()
                        if len(parts) >= 9:
                            port_part = parts[8]
                            if ":" in port_part:
                                try:
                                    port = int(port_part.split(":")[1])
                                    if port not in java_ports:
                                        java_ports.append(port)
                                        self.log(f"发现Java进程监听端口: {port}")
                                except ValueError:
                                    continue
                                    
        except Exception as e:
            self.log(f"获取Java进程端口时出错: {e}")
        
        return java_ports
    
    def tcping_port(self, port):
        """使用tcping验证端口是否为Minecraft联机端口 - 修改版，支持端口映射"""
        # 如果端口映射激活且检查的是25565端口，则检查映射的源端口
        actual_port = port
        if self.is_port_mapping_active and port == 25565 and self.mapped_port:
            self.log(f"🔀 端口映射激活中，实际检查端口 {self.mapped_port}")
            actual_port = self.mapped_port
        
        self.log(f"正在验证端口 {actual_port} 是否为Minecraft联机端口...")
        
        try:
            # 尝试连接端口并发送Minecraft握手包
            with socket.socket(socket.AF_INET6 if self.ipv6 else socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(3)
                
                # 连接到端口
                target_host = self.ipv6 if self.ipv6 else '127.0.0.1'
                s.connect((target_host, actual_port))
                self.log(f"端口 {actual_port} TCP连接成功")
                
                # 尝试发送Minecraft握手包（简化版本）
                try:
                    s.settimeout(1)
                    data = s.recv(1024)
                    if data:
                        self.log(f"端口 {actual_port} 有数据响应，可能是Minecraft服务")
                        return True
                    else:
                        self.log(f"端口 {actual_port} 连接成功但无数据响应")
                        return False
                except socket.timeout:
                    self.log(f"端口 {actual_port} 连接成功但读取超时，可能是Minecraft服务")
                    return True
                except Exception as e:
                    self.log(f"端口 {actual_port} 读取数据时出错: {e}")
                    return False
                    
        except socket.timeout:
            self.log(f"端口 {actual_port} 连接超时")
            return False
        except ConnectionRefusedError:
            self.log(f"端口 {actual_port} 连接被拒绝")
            return False
        except Exception as e:
            self.log(f"端口 {actual_port} 连接失败: {e}")
            return False
    
    def check_minecraft_ports(self):
        """检查Minecraft端口 - 修改版，支持端口映射"""
        self.log("正在检测Minecraft端口...")
        
        # 如果端口映射激活，直接使用映射配置
        if self.is_port_mapping_active and self.mapped_port:
            self.log(f"🔀 端口映射激活中，直接使用映射端口 {self.mapped_port}")
            if self.tcping_port(self.mapped_port):
                self.log(f"✅ 映射源端口 {self.mapped_port} 验证通过")
                return 25565  # 返回映射后的目标端口
            else:
                self.log(f"❌ 映射源端口 {self.mapped_port} 验证失败")
                return None
        
        candidate_ports = []
        
        # 首先检查25565端口是否被占用
        if not self.is_port_occupied(25565):
            self.log("25565端口未被占用，开始检测Java进程监听的端口...")
            
            # 获取所有Java进程监听的端口
            java_ports = self.get_java_process_ports()
            
            if java_ports:
                # 优先选择常见的Minecraft端口
                for port in java_ports:
                    if port in self.mc_ports:
                        candidate_ports.append(port)
                
                # 如果没有常见端口，添加所有Java端口
                if not candidate_ports:
                    candidate_ports = java_ports
            else:
                self.log("未找到Java进程监听的端口")
                return None
        else:
            self.log("25565端口已被占用，添加到候选端口")
            candidate_ports.append(25565)
        
        # 使用tcping验证候选端口
        valid_ports = []
        for port in candidate_ports:
            if self.tcping_port(port):
                valid_ports.append(port)
                self.log(f"✅ 端口 {port} 验证通过，可能是Minecraft联机端口")
            else:
                self.log(f"❌ 端口 {port} 验证失败")
        
        if valid_ports:
            # 优先选择25565端口
            if 25565 in valid_ports:
                return 25565
            else:
                # 选择第一个验证通过的端口
                return valid_ports[0]
        else:
            self.log("所有候选端口验证失败")
            return None
    
    def check_java_minecraft_server(self):
        """检查25565端口是否被Java Minecraft服务器占用 - 修改版，支持端口映射"""
        self.log("正在检查25565端口状态...")
        
        # 如果端口映射激活，检查映射的源端口
        if self.is_port_mapping_active and self.mapped_port:
            self.log(f"🔀 端口映射激活中，检查映射源端口 {self.mapped_port}")
            if self.is_port_occupied_by_java_original(self.mapped_port):
                self.log(f"✅ 映射源端口 {self.mapped_port} 被Java进程占用")
                return True
            else:
                self.log(f"❌ 映射源端口 {self.mapped_port} 未被Java进程占用")
                return False
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('127.0.0.1', 25565))
                if result == 0:
                    self.log("✅ 25565端口被占用，可能是Minecraft服务器")
                    return True
                else:
                    self.log("25565端口未被占用")
                    return False
        except Exception:
            self.log("25565端口检查失败")
            return False
    
    def manual_port_selection(self):
        """手动端口选择 - 使用命令行版的逻辑"""
        self.log("\n无法确定Minecraft使用的端口，请手动确认：")
        self.log("1. 我已在Minecraft中开启局域网游戏")
        self.log("2. 我还没有开启局域网游戏")
        
        # 由于GUI环境，这里简化处理，直接返回None让用户手动处理
        return None
    
    def generate_random_room_code(self, length=6):
        """生成随机房间号"""
        return ''.join(random.choices(string.ascii_lowercase, k=length))
    
    def get_node_status(self, node_id):
        """获取单个节点的状态和地址 - 使用urllib替代requests"""
        try:
            url = f"https://uptime.easytier.cn/node/{node_id}"
            # 设置请求头模拟浏览器
            req = Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
            
            with urlopen(req, timeout=5) as response:
                content = response.read().decode('utf-8')
                
                # 查找TCP地址模式
                tcp_match = re.search(r'tcp://([^:\s]+:\d+)', content)
                if tcp_match:
                    tcp_address = tcp_match.group(1)
                    return {
                        'node_id': node_id,
                        'url': url,
                        'tcp_address': f"tcp://{tcp_address}",
                        'status': 'online'
                    }
            return None
        except (URLError, HTTPError, Exception) as e:
            return None

    def get_et_nodes_from_api(self):
        """通过API获取EasyTier服务器列表"""
        self.log("正在从API获取EasyTier服务器列表...")
        
        try:
            # 构建API请求
            api_url = "https://uptime.easytier.cn/api/nodes?page=1&per_page=200"
            req = Request(api_url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json'
            })
            
            with urlopen(req, timeout=10) as response:
                content = response.read().decode('utf-8')
                data = json.loads(content)
                
                if data.get('success') and 'data' in data and 'items' in data['data']:
                    nodes = []
                    for item in data['data']['items']:
                        # 只选择活跃且可用的节点
                        if (item.get('is_active') and 
                            item.get('is_approved') and 
                            item.get('current_health_status') == 'healthy' and
                            item.get('address')):
                            
                            node_info = {
                                'node_id': item['id'],
                                'name': item.get('name', f'节点 {item["id"]}'),
                                'host': item.get('host', ''),
                                'port': item.get('port', 0),
                                'address': item['address'],
                                'current_connections': item.get('current_connections', 0),
                                'max_connections': item.get('max_connections', 100),
                                'last_response_time': item.get('last_response_time', 0),
                                'description': item.get('description', ''),
                                'tags': item.get('tags', []),
                                'usage_percentage': item.get('usage_percentage', 0)
                            }
                            nodes.append(node_info)
                    
                    self.log(f"✅ 从API获取到 {len(nodes)} 个可用节点")
                    # 缓存节点信息
                    self.all_nodes_cache = nodes
                    return nodes
                else:
                    self.log("❌ API返回数据格式错误")
                    return []
                    
        except Exception as e:
            self.log(f"❌ 获取API数据失败: {e}")
            return []
    
    def get_node_by_id(self, node_id):
        """根据节点ID获取节点信息"""
        # 如果缓存为空，先获取节点列表
        if not self.all_nodes_cache:
            self.get_et_nodes_from_api()
        
        # 在缓存中查找指定节点ID
        for node in self.all_nodes_cache:
            if node['node_id'] == node_id:
                return node
        
        # 如果没有找到，返回默认节点信息
        self.log(f"⚠️ 未找到节点 #{node_id} 的详细信息，使用默认地址")
        return {
            'node_id': node_id,
            'name': f'节点 {node_id}',
            'address': f'tcp://public.easytier.cn:{11009 + node_id}',
            'host': 'public.easytier.cn',
            'port': 11009 + node_id
        }
    
    def ping_node(self, node_url):
        """测试单个节点的延迟"""
        try:
            # 从URL中提取主机名和端口
            parsed = urlparse(node_url)
            hostname = parsed.hostname
            port = parsed.port or 80
            
            # 创建socket连接测试延迟
            start_time = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((hostname, port))
            end_time = time.time()
            sock.close()
            
            if result == 0:
                delay = int((end_time - start_time) * 1000)  # 转换为毫秒
                return delay
            else:
                return None
        except:
            return None
    
    def find_best_node(self, nodes):
        """从可用节点中找到延迟最低的最佳节点"""
        self.log("正在测试节点延迟，选择最佳节点...")
        
        best_node = None
        best_delay = float('inf')
        
        # 测试前10个节点的延迟（为了速度考虑）
        test_nodes = nodes[:10]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_node = {executor.submit(self.ping_node, node['address']): node for node in test_nodes}
            
            for future in concurrent.futures.as_completed(future_to_node):
                node = future_to_node[future]
                try:
                    delay = future.result()
                    if delay is not None and delay < best_delay:
                        best_delay = delay
                        best_node = node
                        self.log(f"发现更好节点 #{node['node_id']}，延迟: {delay}ms")
                except:
                    pass
        
        if best_node:
            self.log(f"✅ 选择最佳节点: #{best_node['node_id']} - {best_node['name']}，延迟: {best_delay}ms")
            return best_node
        else:
            # 如果没有找到低延迟节点，返回第一个可用节点
            self.log("⚠️ 未找到低延迟节点，使用第一个可用节点")
            return nodes[0] if nodes else None
    
    def get_best_et_node(self):
        """获取最佳ET节点 - 使用API获取节点列表"""
        self.log("正在获取EasyTier节点列表...")
        
        # 从API获取节点列表
        available_nodes = self.get_et_nodes_from_api()
        
        if not available_nodes:
            self.log("❌ 无法从API获取节点列表，使用默认节点")
            return {
                'node_id': 1,
                'name': '官方公共服务器-湖北浪浪云',
                'address': 'tcp://public.easytier.cn:11010',
                'status': 'default'
            }
        
        # 按使用率排序，选择使用率较低的节点
        available_nodes.sort(key=lambda x: x.get('usage_percentage', 100))
        
        # 显示前几个节点信息
        self.log("可用节点列表：")
        for i, node in enumerate(available_nodes[:5]):
            self.log(f"  #{node['node_id']}: {node['name']} - 使用率: {node['usage_percentage']:.1f}%")
        
        # 选择最佳节点（使用率最低的前5个中测试延迟）
        candidate_nodes = available_nodes[:5]
        best_node = self.find_best_node(candidate_nodes)
        
        if best_node:
            self.log(f"✅ 最终选择节点: #{best_node['node_id']} - {best_node['name']}")
            self.log(f"📊 节点信息: 使用率 {best_node['usage_percentage']:.1f}%, 连接数 {best_node['current_connections']}/{best_node['max_connections']}")
            if best_node.get('description'):
                self.log(f"📝 节点描述: {best_node['description']}")
            return best_node
        else:
            self.log("❌ 未找到可用节点，使用默认节点")
            return {
                'node_id': 1,
                'name': '官方公共服务器-湖北浪浪云',
                'address': 'tcp://public.easytier.cn:11010',
                'status': 'default'
            }
    
    def run_easytier_command(self, room_code, node_id, node_address, is_create=True):
        """运行EasyTier命令"""
        try:
            # 构建命令
            network_name = f"{room_code}_{node_id}"
            command = f'easytier-core.exe -d --network-name {network_name} --network-secret abc -p {node_address}'
            
            self.log(f"执行命令: {command}")
            
            if is_create:
                self.log("✅ 正在启动EasyTier服务...")
                self.log("📝 请查看新打开的EasyTier窗口")
            else:
                self.log("✅ 正在连接到房间...")
                self.log("📝 请查看新打开的EasyTier窗口")
            
            # 在新窗口中运行命令
            if platform.system() == "Windows":
                bat_content = f"""@echo off
chcp 65001 >nul
title EasyTier联机 - 房间号: {room_code}
echo ========================================
echo        EasyTier联机状态监控
echo ========================================
echo.
echo [STATUS] 正在启动EasyTier服务...
echo [INFO] 房间号: {room_code}
echo [INFO] 节点ID: {node_id}
echo [INFO] 节点地址: {node_address}
echo.
{command}
echo.
echo [STATUS] EasyTier服务已停止
pause
"""
                bat_filename = f"easytier_{room_code}.bat"
                with open(bat_filename, 'w', encoding='utf-8') as f:
                    f.write(bat_content)
                
                # 使用subprocess启动新的命令窗口
                subprocess.Popen(f'start cmd /c "{bat_filename}"', shell=True)
                self.log(f"✅ 已启动EasyTier服务窗口")
                
            return True
            
        except Exception as e:
            self.log(f"❌ 启动EasyTier失败: {e}")
            return False

    def create_port_mapping(self, source_port, target_port=25565):
        """创建端口映射规则"""
        try:
            # 使用netsh创建端口映射
            command = f'netsh interface portproxy add v4tov4 listenport={target_port} listenaddress=0.0.0.0 connectport={source_port} connectaddress=127.0.0.1'
            
            self.log(f"创建端口映射: {source_port} -> {target_port}")
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log("✅ 端口映射创建成功")
                
                # 添加防火墙规则
                firewall_command = f'netsh advfirewall firewall add rule name="Minecraft Port {target_port}" dir=in action=allow protocol=TCP localport={target_port}'
                subprocess.run(firewall_command, shell=True, capture_output=True)
                self.log("✅ 防火墙规则添加成功")
                
                return True
            else:
                self.log(f"❌ 端口映射创建失败: {result.stderr}")
                return False
                
        except Exception as e:
            self.log(f"❌ 创建端口映射时出错: {e}")
            return False

    def remove_port_mapping(self, target_port=25565):
        """移除端口映射规则"""
        try:
            # 移除端口映射
            command = f'netsh interface portproxy delete v4tov4 listenport={target_port} listenaddress=0.0.0.0'
            subprocess.run(command, shell=True, capture_output=True)
            
            # 移除防火墙规则
            firewall_command = f'netsh advfirewall firewall delete rule name="Minecraft Port {target_port}"'
            subprocess.run(firewall_command, shell=True, capture_output=True)
            
            self.log(f"✅ 已移除端口 {target_port} 的映射规则")
            return True
            
        except Exception as e:
            self.log(f"❌ 移除端口映射时出错: {e}")
            return False

    def run_port_mapping(self):
        """运行端口映射功能"""
        if not self.is_admin:
            messagebox.showwarning("管理员权限", "端口映射需要管理员权限，请以管理员权限运行本联机工具")
            return
        
        self.clear_log()
        self.lock_buttons()
        
        # 创建输入对话框
        input_window = tk.Toplevel(self.root)
        input_window.title("端口映射设置")
        input_window.geometry("400x200")
        input_window.transient(self.root)
        input_window.grab_set()
        
        # 设置输入窗口图标
        try:
            icon_path = "lyy.ico"
            if os.path.exists(icon_path):
                input_window.iconbitmap(icon_path)
        except:
            pass
        
        ttk.Label(input_window, text="请输入要映射的源端口:").pack(pady=10)
        
        port_entry = ttk.Entry(input_window, width=20)
        port_entry.pack(pady=5)
        
        ttk.Label(input_window, text="目标端口将固定为25565").pack(pady=5)
        
        def confirm_mapping():
            port_str = port_entry.get().strip()
            input_window.destroy()
            
            if not port_str:
                messagebox.showerror("错误", "端口号不能为空")
                self.unlock_buttons()
                return
            
            try:
                source_port = int(port_str)
                if not (1 <= source_port <= 65535):
                    messagebox.showerror("错误", "端口号必须在1-65535范围内")
                    self.unlock_buttons()
                    return
            except ValueError:
                messagebox.showerror("错误", "请输入有效的端口号")
                self.unlock_buttons()
                return
            
            def mapping_thread():
                try:
                    self.log(f"正在设置端口映射: {source_port} -> 25565")
                    
                    # 检查源端口是否被占用
                    if not self.is_port_occupied(source_port):
                        self.log(f"❌ 源端口 {source_port} 未被占用，请确保Minecraft服务正在运行")
                        messagebox.showerror("错误", f"源端口 {source_port} 未被占用，请确保Minecraft服务正在运行")
                        self.unlock_buttons()
                        return
                    
                    self.log(f"✅ 检测到源端口 {source_port} 正在运行")
                    
                    # 检查目标端口是否已被占用
                    if self.is_port_occupied(25565):
                        self.log("⚠️ 目标端口25565已被占用，正在清理...")
                        self.remove_port_mapping(25565)
                    
                    # 创建端口映射
                    if self.create_port_mapping(source_port, 25565):
                        self.mapped_port = source_port
                        self.is_port_mapping_active = True
                        
                        self.log("\n🎉 端口映射设置成功！")
                        self.log(f"🔀 映射规则: {source_port} -> 25565")
                        self.log("💡 现在可以使用25565端口连接Minecraft服务器")
                        self.log("⚠️ 注意：程序退出时将自动移除映射规则")
                        
                        # 更新按钮状态
                        self.port_map_btn.config(text="🔄 端口映射已激活 (点击关闭)", 
                                               command=self.stop_port_mapping)
                    else:
                        self.log("❌ 端口映射设置失败")
                    
                    self.unlock_buttons()
                    
                except Exception as e:
                    self.log(f"❌ 端口映射过程中出现错误: {e}")
                    self.unlock_buttons()
            
            threading.Thread(target=mapping_thread, daemon=True).start()
        
        def cancel_mapping():
            input_window.destroy()
            self.unlock_buttons()
        
        btn_frame = ttk.Frame(input_window)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="确认", command=confirm_mapping).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=cancel_mapping).pack(side=tk.LEFT, padx=5)
        
        # 绑定回车键
        input_window.bind('<Return>', lambda e: confirm_mapping())
        port_entry.focus()

    def stop_port_mapping(self):
        """停止端口映射"""
        if self.is_port_mapping_active:
            self.remove_port_mapping(25565)
            self.is_port_mapping_active = False
            self.mapped_port = None
            
            self.log("✅ 端口映射已停止")
            self.port_map_btn.config(text="🔄 将其他端口映射至25565", 
                                   command=self.run_port_mapping)
        else:
            self.log("⚠️ 没有激活的端口映射")

    def on_closing(self):
        """程序关闭时的清理操作"""
        if self.is_port_mapping_active:
            self.remove_port_mapping(25565)
            self.log("✅ 已自动清理端口映射规则")
        
        self.root.quit()
    
    def run_ipv6_mode(self):
        """IPv6联机模式 - 使用命令行版的逻辑"""
        self.clear_log()
        self.lock_buttons()  # 锁定按钮
        self.log("正在检测IPv6网络配置...")
        self.log("正在获取IPv6地址，请稍等...")
        
        def detect_ipv6():
            try:
                self.ipv6 = self.get_ipv6_powershell()
                
                if not self.ipv6:
                    self.ipv6 = self.get_ipv6_ipconfig()
                
                if not self.ipv6:
                    self.log("❌ 未检测到公网IPv6地址")
                    messagebox.showerror("错误", "未检测到公网IPv6地址，请联系QQ2232908600获取帮助")
                    self.unlock_buttons()  # 解锁按钮
                    return
                
                self.log(f"✅ 获取到IPv6地址: {self.ipv6}")
                
                # 自动检测Minecraft端口 - 使用命令行版的逻辑
                self.log("正在检测Minecraft联机端口...")
                self.mc_port = self.check_minecraft_ports()
                
                # 如果自动检测失败，尝试手动选择
                if not self.mc_port:
                    self.mc_port = self.manual_port_selection()
                
                if not self.mc_port:
                    self.log("❌ 未检测到有效的Minecraft联机端口")
                    self.log("")
                    self.log("可能的原因：")
                    self.log("1. 未开启Minecraft局域网游戏")
                    self.log("2. 防火墙阻止了端口访问")
                    self.log("3. Minecraft服务未正常启动")
                    self.log("")
                    self.log("💡 请先进入Minecraft单人游戏，开启局域网游戏：")
                    self.log("1. 进入单人游戏世界")
                    self.log("2. 按ESC键打开游戏菜单")
                    self.log("3. 点击'对局域网开放'")
                    self.log("4. 设置游戏模式（可选）")
                    self.log("5. 点击'创建局域网世界'")
                    self.log("6. 记下显示的端口号")
                    messagebox.showerror("错误", "未检测到Minecraft联机端口，请确保已在Minecraft中开启局域网游戏")
                    self.unlock_buttons()  # 解锁按钮
                    return
                
                self.log(f"✅ 验证通过！将使用端口 {self.mc_port} 进行联机")
                
                mc_address = f"[{self.ipv6}]:{self.mc_port}"
                
                self.log("=" * 50)
                self.log("🎮 Minecraft联机地址已生成！")
                self.log(mc_address)
                self.log("=" * 50)
                
                if self.copy_to_clipboard(mc_address):
                    self.log("📋 地址已自动复制到剪贴板！")
                self.log("")
                
                self.log("💡 使用说明：")
                self.log("1. 确保您已在Minecraft中开启局域网游戏")
                self.log("2. 您的朋友需要在Minecraft多人游戏中输入此地址")
                self.log("3. 双方都需要支持IPv6网络")
                self.log("")
                
                self.log(f"🎯 游戏联机地址： [{self.ipv6}]:{self.mc_port}")
                self.log("")
                self.log("❓ 常见问题：")
                self.log("- 如果无法连接，请检查防火墙设置")
                self.log("- 确保端口号与Minecraft中显示的一致")
                self.log("- '登入失败:无效会话'：安装联机模组关闭正版验证")
                self.log("")
                
                self.log("📞 如果使用本脚本联机时遇到问题，请联系：")
                self.log("QQ：2232908600")
                self.log("微信：liuyvetong")
                
                # 成功完成，解锁按钮
                self.unlock_buttons()
                
            except Exception as e:
                self.log(f"❌ IPv6检测过程中出现错误: {e}")
                self.unlock_buttons()  # 解锁按钮
        
        threading.Thread(target=detect_ipv6, daemon=True).start()
    
    def run_easytier_create(self):
        """EasyTier创建房间 - 修改版，支持端口映射"""
        if not self.is_admin:
            messagebox.showwarning("管理员权限", "EasyTier需要管理员权限，请以管理员权限运行本联机工具")
            return
        
        self.clear_log()
        self.lock_buttons()  # 锁定按钮
        self.log("正在创建EasyTier联机房间...")

        def create_room():
            try:
                # 首先检查25565端口是否被占用 - 支持端口映射
                self.log("正在检查25565端口状态...")
                
                # 如果端口映射激活，使用映射逻辑
                if self.is_port_mapping_active and self.mapped_port:
                    self.log(f"🔀 端口映射激活中，检查映射源端口 {self.mapped_port}")
                    if not self.is_port_occupied_by_java_original(self.mapped_port):
                        self.log(f"❌ 映射源端口 {self.mapped_port} 未被Java进程占用，未检测到Minecraft服务器")
                        self.log("")
                        self.log("可能的原因：")
                        self.log("1. 未开启Minecraft局域网游戏")
                        self.log("2. Minecraft服务未正常启动")
                        self.log("3. 端口映射配置错误")
                        self.log("")
                        self.log("💡 请先进入Minecraft单人游戏，开启局域网游戏：")
                        self.log("1. 进入单人游戏世界")
                        self.log("2. 按ESC键打开游戏菜单")
                        self.log("3. 点击'对局域网开放'")
                        self.log("4. 设置游戏模式（可选）")
                        self.log("5. 点击'创建局域网世界'")
                        self.log("6. 确保Minecraft服务正在运行")
                        self.log("")
                        self.log("⚠️ 注意：EasyTier联机模式要求Minecraft服务正在运行")
                        messagebox.showerror("错误", f"未检测到Minecraft服务器在端口 {self.mapped_port} 运行，请确保已在Minecraft中开启局域网游戏")
                        self.unlock_buttons()  # 解锁按钮
                        return
                else:
                    # 原始逻辑
                    if not self.is_port_occupied_by_java(25565):
                        self.log("❌ 25565端口未被Java进程占用，未检测到Minecraft服务器")
                        self.log("")
                        self.log("可能的原因：")
                        self.log("1. 未开启Minecraft局域网游戏")
                        self.log("2. Minecraft服务未正常启动")
                        self.log("3. 使用的不是25565端口")
                        self.log("")
                        self.log("💡 请先进入Minecraft单人游戏，开启局域网游戏：")
                        self.log("1. 进入单人游戏世界")
                        self.log("2. 按ESC键打开游戏菜单")
                        self.log("3. 点击'对局域网开放'")
                        self.log("4. 设置游戏模式（可选）")
                        self.log("5. 点击'创建局域网世界'")
                        self.log("6. 确保端口为25565")
                        self.log("")
                        self.log("⚠️ 注意：EasyTier联机模式要求Minecraft端口必须为25565")
                        messagebox.showerror("错误", "未检测到Minecraft服务器在25565端口运行，请确保已在Minecraft中开启局域网游戏且端口为25565")
                        self.unlock_buttons()  # 解锁按钮
                        return
            
                self.log("✅ 检测到Minecraft服务器正在运行")
                self.log("正在选择最佳ET节点...")
            
            # 获取最佳节点
                best_node = self.get_best_et_node()
            
                self.log(f"✅ 已选择节点: #{best_node['node_id']} - {best_node['name']}")
            
                # 生成随机房间号
                room_code = self.generate_random_room_code()
                full_room_code = f"{room_code}_{best_node['node_id']}"
            
                self.log(f"✅ 生成房间号: {full_room_code}")
                self.log(f"📝 节点信息: 使用节点 #{best_node['node_id']} - {best_node['name']}")
                self.log(f"🌐 节点地址: {best_node['address']}")
            
            # 运行EasyTier命令
                if self.run_easytier_command(room_code, best_node['node_id'], best_node['address'], True):
                    self.log("\n🎉 房间创建成功！")
                    self.log("👥 请将完整房间号分享给您的朋友")
                    self.log(f"🌐 完整房间号: {full_room_code}")
                    self.log("💡 房主IP: 10.126.126.1")
                    self.log("🎮 Minecraft地址: 10.126.126.1:25565")
                
                    if self.copy_to_clipboard(full_room_code):
                        self.log("📋 完整房间号已自动复制到剪贴板")
                    
                    self.log("\n⚠️ 注意：请不要关闭EasyTier窗口，否则联机会断开")
                else:
                    self.log("❌ 房间创建失败")
            
            # 完成操作，解锁按钮
                self.unlock_buttons()
            
            except Exception as e:
                self.log(f"❌ 创建房间过程中出现错误: {e}")
                self.unlock_buttons()  # 解锁按钮

        threading.Thread(target=create_room, daemon=True).start()
    
    def run_easytier_join(self):
        """EasyTier加入房间 - 修复节点地址识别问题"""
        if not self.is_admin:
            messagebox.showwarning("管理员权限", "EasyTier需要管理员权限，请以管理员权限运行本联机工具")
            return
            
        self.clear_log()
        self.lock_buttons()  # 锁定按钮
        
        # 创建输入对话框
        input_window = tk.Toplevel(self.root)
        input_window.title("输入房间号")
        input_window.geometry("400x150")
        input_window.transient(self.root)
        input_window.grab_set()
        
        # 设置输入窗口图标
        try:
            icon_path = "lyy.ico"
            if os.path.exists(icon_path):
                input_window.iconbitmap(icon_path)
        except:
            pass
        
        ttk.Label(input_window, text="请输入完整房间号:").pack(pady=10)
        
        room_entry = ttk.Entry(input_window, width=30)
        room_entry.pack(pady=5)
        
        def confirm_join():
            full_room_code = room_entry.get().strip()
            input_window.destroy()
            
            if not full_room_code:
                messagebox.showerror("错误", "房间号不能为空")
                self.unlock_buttons()  # 解锁按钮
                return
            
            # 解析房间号和节点ID
            if '_' not in full_room_code:
                messagebox.showerror("错误", "房间号格式错误，请使用完整房间号（包含节点ID）")
                self.unlock_buttons()  # 解锁按钮
                return
            
            room_parts = full_room_code.split('_')
            if len(room_parts) != 2:
                messagebox.showerror("错误", "房间号格式错误，请使用完整房间号（包含节点ID）")
                self.unlock_buttons()  # 解锁按钮
                return
            
            room_code = room_parts[0]
            node_id_str = room_parts[1]
            
            # 验证房间号格式
            if len(room_code) != 6 or not room_code.isalpha() or not room_code.islower():
                messagebox.showerror("错误", "房间号格式错误，前6位必须是6位小写字母")
                self.unlock_buttons()  # 解锁按钮
                return
            
            # 验证节点ID
            if not node_id_str.isdigit() or not (1 <= int(node_id_str) <= 1000):
                messagebox.showerror("错误", "节点ID格式错误，必须是1-1000的数字")
                self.unlock_buttons()  # 解锁按钮
                return
            
            self.log(f"正在加入房间: {full_room_code}")
            
            def join_thread():
                try:
                    node_id = int(node_id_str)
                    
                    # 使用新的方法获取节点信息
                    node_info = self.get_node_by_id(node_id)
                    
                    self.log(f"使用节点: #{node_info['node_id']} - {node_info['name']}")
                    self.log(f"节点地址: {node_info['address']}")
                    
                    # 运行EasyTier命令
                    if self.run_easytier_command(room_code, node_id, node_info['address'], False):
                        self.log("🎉 正在连接到房间！")
                        self.log("💡 使用说明：")
                        self.log("  1. 等待连接成功")
                        self.log("  2. 在Minecraft中添加服务器")
                        self.log("  3. 服务器地址输入: 10.126.126.1:25565")
                        self.log("  4. 等待朋友在Minecraft中开启游戏")
                        self.log(f"\n🌐 联机信息：")
                        self.log(f"   完整房间号: {full_room_code}")
                        self.log(f"   使用节点: #{node_info['node_id']} - {node_info['name']}")
                        self.log(f"   节点地址: {node_info['address']}")
                        self.log("   服务器地址: 10.126.126.1:25565")
                        
                        if self.copy_to_clipboard("10.126.126.1:25565"):
                            self.log("📋 服务器地址已自动复制到剪贴板")
                        
                        self.log("\n⚠️ 注意：请不要关闭EasyTier窗口，否则联机会断开")
                    else:
                        self.log("❌ 连接房间失败")
                    
                    # 完成操作，解锁按钮
                    self.unlock_buttons()
                    
                except Exception as e:
                    self.log(f"❌ 加入房间过程中出现错误: {e}")
                    self.unlock_buttons()  # 解锁按钮
            
            threading.Thread(target=join_thread, daemon=True).start()
        
        def cancel_join():
            input_window.destroy()
            self.unlock_buttons()  # 解锁按钮
        
        btn_frame = ttk.Frame(input_window)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="确认", command=confirm_join).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=cancel_join).pack(side=tk.LEFT, padx=5)
        
        # 绑定回车键
        input_window.bind('<Return>', lambda e: confirm_join())
        room_entry.focus()

def is_admin():
    """检查当前是否具有管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def request_uac():
    """请求UAC提升权限"""
    if is_admin():
        return True
        
    try:
        # 获取当前可执行文件路径
        if getattr(sys, 'frozen', False):
            current_file = sys.executable
        else:
            current_file = sys.argv[0]
        
        # 请求管理员权限
        result = ctypes.windll.shell32.ShellExecuteW(
            None, 
            "runas", 
            current_file, 
            " ".join(sys.argv[1:]), 
            None, 
            1
        )
        
        if result > 32:
            return True
        else:
            print("请求管理员权限失败")
            return False
    except Exception as e:
        print(f"请求管理员权限失败: {e}")
        return False

def main():
    # 检查平台
    if platform.system() != "Windows":
        messagebox.showerror("错误", "此程序目前仅支持Windows系统")
        return
    
    # 创建主窗口
    root = tk.Tk()
    app = MinecraftIPv6ToolGUI(root)
    
    # 启动主循环
    root.mainloop()

if __name__ == "__main__":
    # 如果以管理员权限运行，直接启动GUI
    if is_admin():
        main()
    else:
        # 否则请求UAC提升
        if request_uac():
            print("已请求管理员权限，请在新窗口中操作")
            sys.exit(0)
        else:
            # 如果UAC请求失败，仍然启动程序但显示警告
            print("UAC请求失败，以普通权限运行")
            main()
