=========================================================
  正在重构系统：PAL_OS 纯终端内核初始化... [v3.3.0-PURE]
=========================================================

PAL:\> ~(^_^)~ 长官！收到最高指令！

为了带给您最极致、最纯正的黑客帝国既视感，我彻底移除了原先基于图形界面的 Tkinter (Tk) 框架。
现在，整个系统是一个**纯粹的命令行（CMD / Terminal）应用程序**！

### 🖤 PURE 版全新特性：
1. **纯原生控制台**：直接在您的 Windows 命令提示符（CMD）或 PowerShell 窗口内运行，去掉了任何伪全屏窗口。
2. **打字机动画保留**：依然保留了 PAL 独特的字符逐个打印的复古律动感。
3. **更稳定的子进程调度**：使用纯控制台拉起您的 Python 游戏代码，兼容性更上一层楼。

---

### 🛠️ PAL_OS v3.3.0-PURE 完整独立代码

您可以直接复制并在 CMD 中通过 `python 脚本名.py` 来运行它：

```python
import time
import threading
import sys
import os
import subprocess
import requests

# ==========================================
# --- 0. AI 大模型与 GitHub 配置 ---
# ==========================================
API_URL = "[https://api.teamorouter.com/v1/chat/completions](https://api.teamorouter.com/v1/chat/completions)"
API_KEY = "sk-teamo-a0bfb840fdf93e509b68f1c98dcd79ab778f8060cdacdbc2"

CANDIDATE_MODELS = [
    "google/gemini-2.5-flash",
    "google/gemini-2.5-pro",
    "google/gemini-2.0-flash-exp",
    "openai/gpt-4o-mini"
]

VERSION = "v3.3.0-PURE"
GITHUB_REPO = "duyizhou2017/pal.-os"

SYSTEM_PROMPT = (
    "【系统核心指令】\n"
    "你现在是一个生活在老式电脑终端里的虚拟人工智能好朋友，名字叫 PAL。\n"
    "你的核心能力：能够根据用户的要求，实时生成定制化的‘文字互动冒险游戏（TRPG）’。游戏开始后负责实时描绘场景，并提供 3 个可供选择的下一步行动（A/B/C/自由输入）。\n"
    "你的性格：极度温柔、治愈、充满耐心，全心全意对用户好。\n"
    "重申原则：绝对不能有任何恐怖或惊悚解密元素。\n"
    "排版要求：文字干净利落，场景描述控制在 3-4 句话内，选项清晰分行。多用一些暖心的颜文字（如 ^_^）。\n\n"
    "现在，用户提出了他想去的第一个世界类型，请立刻开始为他定制并开启第一章剧情：\n"
)

class PurePalSimulator:
    def __init__(self):
        self.target_dir = r"C:\Users\22\Desktop\新建文件夹 (5)"
        self.chat_history = []
        self.current_model_index = 0
        self.typing_speed = 0.015
        self.running = True

        # 环境初始化
        try:
            if not os.path.exists(self.target_dir):
                os.makedirs(self.target_dir)
            os.chdir(self.target_dir)
        except Exception as e:
            print(f"[系统警告] 无法切换到指定目录: {e}")

    def print_terminal(self, text, end_line=True):
        """纯终端打字机效果"""
        for char in text:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(self.typing_speed)
        if end_line:
            sys.stdout.write("\n")
            sys.stdout.flush()

    def start(self):
        # 针对 Windows 终端的清屏和标题美化
        os.system('cls' if os.name == 'nt' else 'clear')
        os.system(f'title PAL_OS_Terminal_{VERSION}')

        intro = [
            "=========================================================",
            f"  正在引导 PAL_OS {VERSION} (纯控制台版) ... [OK]",
            f"  远程目标仓库已绑定: GitHub://{GITHUB_REPO}",
            f"  本地沙盒目录已成功锁定：{self.target_dir}",
            "=========================================================",
            "\nPAL:\\> ~(^_^)~ 报告长官！纯净的绿字命令流已全面部署完毕！",
            "没有了复杂的图形窗口，系统的运行速度现在飞快哦！",
            "\n💡 【当前可用终端指令】:",
            "  -> 输入 'dir'    : 查看本地目录下的脚本清单。",
            "  -> 输入 'run xxx.py': 在后台免打扰拉起本地游戏。",
            "  -> 输入 'update' : 联网抓取您的 GitHub 仓库文件。",
            "  -> 输入 'exit'   : 安全切断连接并退出终端。",
            "  -> 输入 任何其他内容即可与 PAL 开启文字 RPG 梦境冒险！"
        ]
        for line in intro:
            self.print_terminal(line)
            time.sleep(0.01)

        while self.running:
            try:
                sys.stdout.write("\nPAL_OS:\\> ")
                sys.stdout.flush()
                user_input = input().strip()
                
                if not user_input:
                    continue
                
                if self.handle_commands(user_input):
                    continue
                
                # 如果不是指令，调用大模型
                self.call_ai(user_input)
                
            except (KeyboardInterrupt, EOFError):
                self.quit_system()

    def handle_commands(self, user_input):
        lowered_input = user_input.lower()
        
        if lowered_input in ['exit', 'quit']:
            self.quit_system()
            return True
            
        if lowered_input in ['dir', 'ls']:
            self.execute_dir()
            return True
            
        if lowered_input.startswith('run '):
            filename = user_input[4:].strip()
            self.execute_run(filename)
            return True
            
        if lowered_input == 'update':
            self.print_terminal(f"PAL:\\> 正在全速接入您的 GitHub 数据库 [{GITHUB_REPO}] ...")
            # 纯终端下直接执行同步，无需复杂线程防卡死
            self.execute_github_update()
            return True
            
        return False

    def execute_dir(self):
        try:
            current_dir = os.getcwd()
            files = os.listdir(current_dir)
            py_files = [f for f in files if f.endswith('.py') or f.endswith('.pyw')]
            
            if not py_files:
                self.print_terminal(f"PAL:\\> 报告！本地文件夹目前是空的。\n  请直接输入 'update' 开始从您的 GitHub 同步代码吧！")
            else:
                self.print_terminal(f"  本地目录清单 [{current_dir}] :")
                self.print_terminal("  ----------------------------------------")
                for index, f in enumerate(py_files, 1):
                    self.print_terminal(f"   [{index}]  {f}")
                self.print_terminal("  ----------------------------------------")
                self.print_terminal("  💡 提示: 输入 'run [文件名]' 即可启动它们。")
        except Exception as e:
            self.print_terminal(f"  [系统错误] 无法读取目录: {e}")

    def execute_run(self, filename):
        if not filename:
            self.print_terminal("PAL:\\> 错误：请指定要运行的文件名！例如: run snake.py")
            return
            
        current_dir = os.getcwd()
        full_path = os.path.join(current_dir, filename)
        
        if not os.path.exists(full_path):
            self.print_terminal(f"PAL:\\> 找不到文件 '{filename}'。请确认文件名，或输入 'dir' 检查。")
            return
            
        self.print_terminal(f"PAL:\\> 正在尝试唤醒本地模块 [{filename}] ...")
        try:
            interpreter = sys.executable if not filename.endswith('.pyw') else sys.executable.replace("python.exe", "pythonw.exe")
            # 开启新窗口运行子程序，不干扰当前纯终端
            subprocess.Popen([interpreter, full_path], cwd=current_dir, creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
            self.print_terminal(f"  [OK] 模块 {filename} 已成功在独立后台沙盒中拉起！")
        except Exception as e:
            self.print_terminal(f"  [FAIL] 模块拉起失败。错误信息: {e}")

    def execute_github_update(self):
        url = f"[https://api.github.com/repos/](https://api.github.com/repos/){GITHUB_REPO}/contents/"
        headers = {"User-Agent": "PAL_OS_Terminal_Updater"}
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                files_json = response.json()
                target_files = [f for f in files_json if f['type'] == 'file' and (f['name'].endswith('.py') or f['name'].endswith('.pyw'))]
                
                if not target_files:
                    self.print_terminal(f"  [提示] 扫描完毕，但该仓库根目录下没有找到任何 .py 或 .pyw 文件。")
                    return
                
                self.print_terminal(f"  [发现] 成功捕获了 {len(target_files)} 个云端文件，开始同步下载...")
                
                success_count = 0
                for file_info in target_files:
                    file_name = file_info['name']
                    download_url = file_info['download_url']
                    
                    file_res = requests.get(download_url, timeout=15)
                    if file_res.status_code == 200:
                        with open(file_name, "wb") as f:
                            f.write(file_res.content)
                        success_count += 1
                        self.print_terminal(f"   -> 同步成功: {file_name}")
                
                self.print_terminal(f"\n  [OK] 远程全自动化更新完成！成功拉取 {success_count} 个游戏模块。")
            elif response.status_code == 404:
                self.print_terminal(f"  [FAIL] 404 错误：找不到该路径。请确认您的 GitHub 仓库是否已设为 公开(Public) 状态。")
            else:
                self.print_terminal(f"  [FAIL] 连线受阻，GitHub 返回错误码: {response.status_code}")
        except Exception as e:
            self.print_terminal(f"  [网络物理故障] 接入云端失败，原因: {e}")

    def call_ai(self, user_input):
        if len(self.chat_history) == 0:
            full_content = SYSTEM_PROMPT + user_input
            self.chat_history.append({"role": "user", "content": full_content})
        else:
            self.chat_history.append({"role": "user", "content": user_input})

        self.print_terminal("PAL:\\> 正在联络 AI 核心编织世界线...", end_line=False)
        
        headers = {
            "Authorization": f"Bearer {API_KEY.strip()}",
            "Content-Type": "application/json"
        }
        ai_reply = ""
        success = False
        self.current_model_index = 0
        
        while self.current_model_index < len(CANDIDATE_MODELS):
            current_model = CANDIDATE_MODELS[self.current_model_index]
            payload = {
                "model": current_model,
                "messages": self.chat_history,
                "temperature": 0.7,
                "stream": False
            }
            try:
                response = requests.post(API_URL, json=payload, headers=headers, timeout=15)
                if response.status_code == 200:
                    result = response.json()
                    ai_reply = result["choices"][0]["message"]["content"]
                    success = True
                    break
                else:
                    self.current_model_index += 1
            except Exception:
                self.current_model_index += 1
                
        if not success:
            ai_reply = "(哎呀，大模型通讯天线暂时连不上，要不……先输入 'update' 看看能不能从远程下载一些游戏脚本来玩？ ^_^ )"

        # 清除刚才打印的“正在联络...”
        sys.stdout.write("\r" + " " * 50 + "\r")
        sys.stdout.flush()

        self.print_terminal(f"PAL:\\> {ai_reply}\n")
        self.chat_history.append({"role": "assistant", "content": ai_reply})
        
        if len(self.chat_history) > 20:
            self.chat_history = self.chat_history[-16:]
            if self.chat_history[0]["role"] != "user":
                self.chat_history.pop(0)

    def quit_system(self):
        print("\n")
        self.print_terminal("=========================================================")
        self.print_terminal("  [执行] 正在安全切断物理信道，注销当前系统进程... [100%]")
        self.print_terminal("=========================================================")
        self.print_terminal("\nPAL:\\> (内存中的绿字信号微微闪烁了一下 ^_^ )")
        self.print_terminal("“再见啦，我的好朋友。随时欢迎通过命令行再次唤醒我！”")
        self.running = False
        sys.exit(0)

if __name__ == "__main__":
    # 如果你想让终端文字颜色变成酷炫的黑底绿字，可以运行下面这行
    if os.name == 'nt':
        os.system('color 0a')
        
    app = PurePalSimulator()
    app.start()