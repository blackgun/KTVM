import os
import json
import requests
import time
import sys

# --- Configuration & Credentials ---
# In a real app, use a .env or config file. For now, we check environment.
VULTR_API_KEY = os.environ.get("VULTR_API_KEY")
DATA_FILE = "ktvm/vps_data.json"

# Vultr Constants
VULTR_API_URL = "https://api.vultr.com/v2"
VULTR_PLAN = "vc2-1c-1gb"
VULTR_OS = 1743  # Ubuntu 22.04

# --- Data Management ---
def load_vps():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

def save_vps(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- Vultr API Wrappers ---
def vultr_request(method, endpoint, data=None):
    if not VULTR_API_KEY:
        print("\n[错误] 未设置 VULTR_API_KEY 环境参数。")
        return None
    
    headers = {
        "Authorization": f"Bearer {VULTR_API_KEY}",
        "Content-Type": "application/json"
    }
    url = f"{VULTR_API_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        
        if response.status_code in [200, 201, 202, 204]:
            return response.json() if response.text else {}
        else:
            print(f"\nVultr API 错误 ({response.status_code}): {response.text}")
            return None
    except Exception as e:
        print(f"\n请求异常: {str(e)}")
        return None

# --- VPN User Data ---
# Based on blackgun/vpn reference
USER_DATA_VPN = """#!/bin/bash
apt-get update -y
apt-get install -y curl jq docker.io
systemctl enable docker
systemctl start docker
docker run -d --name shadowbox --restart=unless-stopped --net=host -v /opt/outline:/root/shadowbox/persisted-state quay.io/outline/shadowbox:stable
"""

# --- UI Rendering ---
def render_main_menu(vps_list):
    print("\n[XFF 控制台]")
    print("-" * 65)
    print(f"{'ID':<3} {'名称':<15} {'地点':<6} {'IP':<15} {'VPN(Outline)':<15} {'OpenClaw'}")
    for v in vps_list:
        vpn_status = "● 运行" if v.get('vpn') else "○ 停止"
        claw_status = "● 活跃" if v.get('claw') else "○ 离线"
        print(f"{v['id']:<3} {v['name']:<15} {v['loc']:<6} {v['ip']:<15} {vpn_status:<15} {claw_status}")
    print("-" * 65)
    print("[0] 返回  [N] 新增服务器  [R] 刷新状态  [H] 帮助")

def render_detail_menu(vps):
    print(f"\n服务器 {vps['id']} 详情 ({vps['name']})")
    print("-" * 40)
    s1 = "✓" if vps.get('vpn') else "✘"
    s2 = "✓" if vps.get('claw') else "✘"
    s3 = "✓" if vps.get('page') else "✘"
    
    print(f"1.VPN {s1}    2.AI {s2}    3.Page {s3}")
    print("-" * 40)
    print("[0] 返回  [1-3] 选择安装 (无卸载)")

# --- Logic Actions ---
def add_vultr_server():
    print("\n[新增服务器 - Vultr]")
    print("选择区域:")
    print("1) 🇯🇵 日本 (Tokyo)")
    print("2) 🇰🇷 韩国 (Seoul)")
    print("0) 取消")
    
    choice = input("> ").strip()
    if choice == '1': region, loc = "nrt", "日本"
    elif choice == '2': region, loc = "icn", "韩国"
    else: return None

    name = input("服务器名称 (默认: vpn-server): ").strip() or "vpn-server"
    
    data = {
        "region": region,
        "plan": VULTR_PLAN,
        "os_id": VULTR_OS,
        "label": name,
        "user_data": USER_DATA_VPN if input("是否预装 VPN？(y/n): ").lower() == 'y' else ""
    }
    
    print("\n正在向 Vultr 发送创建请求...")
    res = vultr_request("POST", "/instances", data)
    if res:
        instance = res.get("instance")
        print(f"成功！服务器 ID: {instance['id']}，正在初始化...")
        return {
            "id": len(load_vps()) + 1,
            "external_id": instance['id'],
            "name": instance['label'],
            "loc": loc,
            "ip": "分配中...",
            "vpn": True if data['user_data'] else False,
            "claw": False,
            "page": False
        }
    return None

def sync_vultr_status(vps_list):
    print("\n正在从 Vultr 同步状态...")
    res = vultr_request("GET", "/instances")
    if res:
        instances = res.get("instances", [])
        updated = False
        for v in vps_list:
            if "external_id" in v:
                match = next((i for i in instances if i['id'] == v['external_id']), None)
                if match:
                    if v['ip'] != match['main_ip']:
                        v['ip'] = match['main_ip'] or "分配中..."
                        updated = True
        if updated:
            save_vps(vps_list)
            print("状态已更新。")
        else:
            print("没有变化。")

# --- Main App ---
def main():
    if not VULTR_API_KEY:
        print("\n[⚠️ 警告] 未检测到 VULTR_API_KEY。")
        print("请运行: export VULTR_API_KEY='你的密钥'")
    
    vps_list = load_vps()
    state = "MAIN"
    selected_vps = None

    while True:
        if state == "MAIN":
            render_main_menu(vps_list)
            choice = input("\n选择 ID 或动作 > ").strip().upper()
            
            if choice == '0': break
            elif choice == 'N':
                new_vps = add_vultr_server()
                if new_vps:
                    vps_list.append(new_vps)
                    save_vps(vps_list)
            elif choice == 'R':
                sync_vultr_status(vps_list)
            elif choice == 'H':
                print("\n帮助: 输入 ID 进入详情，N 新增，R 刷新。")
                input("按回车继续...")
            else:
                try:
                    idx = int(choice)
                    selected_vps = next((v for v in vps_list if v['id'] == idx), None)
                    if selected_vps: state = "DETAIL"
                except: pass
        
        elif state == "DETAIL":
            render_detail_menu(selected_vps)
            choice = input("\n选择 > ").strip()
            if choice == '0':
                state = "MAIN"
                selected_vps = None
            elif choice in ['1', '2', '3']:
                # Logic for installing modules on an existing VPS would go here
                print("\n[功能开发中] 正在执行安装...")
                time.sleep(1)

if __name__ == "__main__":
    main()
