import json
import os
import sys

# --- Data Management ---
DATA_FILE = "ktvm/vps_data.json"

def load_vps():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return [
        {"id": 1, "name": "HK-Aliyun", "loc": "香港", "ip": "47.92.1.44", "vpn": True, "claw": True, "page": True}
    ]

def save_vps(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- UI Rendering ---
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def render_main_menu(vps_list):
    print("\n[XFF 控制台]")
    print("-" * 55)
    print(f"{'ID':<3} {'名称':<12} {'地点':<6} {'IP':<15} {'VPN(Outline)':<15} {'OpenClaw'}")
    for v in vps_list:
        vpn_status = "● 运行" if v['vpn'] else "○ 停止"
        claw_status = "● 活跃" if v['claw'] else "○ 离线"
        print(f"{v['id']:<3} {v['name']:<12} {v['loc']:<6} {v['ip']:<15} {vpn_status:<15} {claw_status}")
    print("-" * 55)
    print("[0] 返回  [N] 新增服务器  [H] 帮助")

def render_detail_menu(vps):
    print(f"\n服务器{vps['id']}详情")
    # Checkmarks
    s1 = "✓" if vps['vpn'] else "✘"
    s2 = "✓" if vps['claw'] else "✘"
    s3 = "✓" if vps['page'] else "✘"
    
    print(f"1.VPN{s1}  2.AI{s2}  3.Page{s3}")
    print("-" * 40)
    print("[0] 返回  [0-N]选择安装(无卸载)")

# --- Main Logic ---
def main():
    vps_list = load_vps()
    state = "MAIN"
    selected_vps = None

    while True:
        # clear_screen()
        if state == "MAIN":
            render_main_menu(vps_list)
            choice = input("\n选择 ID 或动作 > ").strip().upper()
            
            if choice == '0': break
            elif choice == 'N': 
                input("\n[功能开发中] 按回车返回...")
            elif choice == 'H':
                print("\n帮助：输入 ID 进入详情，输入 N 添加新服务器。")
                input("按回车继续...")
            else:
                try:
                    idx = int(choice)
                    selected_vps = next((v for v in vps_list if v['id'] == idx), None)
                    if selected_vps:
                        state = "DETAIL"
                except ValueError:
                    pass
        
        elif state == "DETAIL":
            render_detail_menu(selected_vps)
            choice = input("\n选择 > ").strip()
            
            if choice == '0':
                state = "MAIN"
                selected_vps = None
            elif choice in ['1', '2', '3']:
                # Mock Installation
                key = ['vpn', 'claw', 'page'][int(choice)-1]
                if not selected_vps[key]:
                    print(f"\n正在安装组件 {key}...")
                    import time; time.sleep(1)
                    selected_vps[key] = True
                    save_vps(vps_list)
                    print("安装成功！")
                    time.sleep(1)
                else:
                    print(f"\n组件 {key} 已安装。")
                    time.sleep(1)

if __name__ == "__main__":
    main()
