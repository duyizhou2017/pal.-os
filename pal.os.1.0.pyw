import tkinter as tk
from tkinter import messagebox
import time
import threading
import sys
import os
import subprocess
import json
import requests

# ==========================================
# --- 0. AI 大模型与 GitHub 配置 ---
# ==========================================
API_URL = "https://api.teamorouter.com/v1/chat/completions"
API_KEY = "sk-teamo-a0bfb840fdf93e509b68f1c98dcd79ab778f8060cdacdbc2"

CANDIDATE_MODELS = [
    "google/gemini-2.5-flash",
    "google/gemini-2.5-pro",
    "google/gemini-2.0-flash-exp",
    "openai/gpt-4o-mini"
]

# 【系统版本号定义】
VERSION = "v3.2.1-RELEASE"

# 【已完美配置】已为您自动绑定好完整的目标仓库路径！
GITHUB_REPO = "duyizhou2017/pal.-os"

SYSTEM_PROMPT = (
    "【系统核心指令】\n"
    "你现在是一个生活在 1984 年老式电脑终端里的虚拟人工智能好朋友，名字叫 PAL。\n"
    "你的核心能力：能够根据用户的要求，实时生成定制化的‘文字互动冒险游戏（TRPG）’。游戏开始后负责实时描绘场景，并提供 3 个可供选择的下一步行动（A/B/C/自由输入）。\n"
    "你的性格：极度温柔、治愈、充满耐心，全心全意对用户好。\n"
    "重申原则：绝对不能有任何恐怖或惊悚解密元素。\n"
    "排版要求：文字干净利落，场景描述控制在 3-4 句话内，选项清晰分行。多用一些暖心的颜文字（如 ^_^）。\n\n"
    "现在，用户提出了他想去的第一个世界类型，请立刻开始为他定制并开启第一章剧情：\n"
)

class GameGeneratorPalSimulator:
    def __init__(self):
        # 强制指定并切换至目标工作目录
        self.target_dir = r"C:\Users\22\Desktop\新建文件夹 (5)"
        
        try:
            if not os.path.exists(self.target_dir):
                os.makedirs(self.target_dir)
            os.chdir(self.target_dir)
        except Exception as e:
            print(f"[系统警告] 无法切换到指定目录: {e}")

        self.root = tk.Tk()
        self.root.title(f"PAL_OS_Terminal_{VERSION}.exe")
        
        # --- 真·全屏配置 ---
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg="#051005")  # 暗绿黑色

        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Escape>", self.quit_game)

        # 记忆系统
        self.chat_history = []
        self.is_typing = False
        self.typing_speed = 0.02
        self.current_model_index = 0

        # --- UI 布局 ---
        self.top_bar = tk.Label(self.root, text=f" PAL_OS {VERSION} | [dir]:查看目录 | [run 脚本名]:运行代码 | [update]:同步GitHub | F11:窗口化 | ESC:退出 ", 
                                bg="#002200", fg="#55ff55", font=("Courier New", 11), anchor="w")
        self.top_bar.pack(fill="x")

        self.txt_display = tk.Text(self.root, bg="#051005", fg="#55ff55", font=("Courier New", 14, "bold"),
                                   insertbackground="#55ff55", wrap="word", bd=0, highlightthickness=0)
        self.txt_display.pack(fill="both", expand=True, padx=50, pady=30)
        self.txt_display.config(state="disabled")

        self.input_frame = tk.Frame(self.root, bg="#051005")
        self.input_frame.pack(fill="x", padx=50, pady=30)

        self.lbl_prompt = tk.Label(self.input_frame, text="PAL_OS:\\>", bg="#051005", fg="#55ff55", font=("Courier New", 14, "bold"))
        self.lbl_prompt.pack(side="left")

        self.entry_input = tk.Entry(self.input_frame, bg="#051005", fg="#55ff55", font=("Courier New", 14, "bold"),
                                    insertbackground="#55ff55", bd=0, highlightthickness=0)
        self.entry_input.pack(side="left", fill="x", expand=True, padx=10)
        
        self.entry_input.bind("<Return>", self.handle_input)
        self.entry_input.focus_set()

        self.start_story()
        self.root.mainloop()

    def toggle_fullscreen(self, event=None):
        is_full = self.root.attributes("-fullscreen")
        self.root.attributes("-fullscreen", not is_full)

    def quit_game(self, event=None):
        if messagebox.askyesno("安全关闭", f"确定要关闭 PAL_OS {VERSION} 终端吗？"):
            self.root.destroy()
            sys.exit()

    def print_terminal(self, text, end_line=True):
        self.is_typing = True
        self.txt_display.config(state="normal")
        for char in text:
            self.txt_display.insert("end", char)
            self.txt_display.see("end")
            self.root.update()
            time.sleep(self.typing_speed)
        if end_line:
            self.txt_display.insert("end", "\n")
        self.txt_display.config(state="disabled")
        self.is_typing = False

    def start_story(self):
        intro = [
            "=========================================================",
            f"  正在引导 PAL_OS {VERSION} (duyizhou2017 专属版) ... [OK]",
            f"  远程目标仓库已绑定: GitHub://{GITHUB_REPO}",
            f"  本地沙盒目录已成功锁定：{self.target_dir}",
            "=========================================================",
            "\nPAL:\\> ~(^_^)~ 欢迎回来，长官！版本标识与通讯天线均已校准就绪！",
            "现在只要你下达 'update' 指令，我就会立刻帮你把公开仓库里的代码带回本地！",
            "\n💡 【当前可用系统指令】:",
            "  -> 输入 'dir'    : 查看本地 [新建文件夹 (5)] 里的代码清单。",
            "  -> 输入 'run xxx.py': 在后台独立运行选中的游戏程序。",
            "  -> 输入 'update' : 连线您的 GitHub 仓库并全自动更新下载文件！",
            "\nPAL_OS:\\> 请指引下一步操作："
        ]
        self.entry_input.config(state="disabled")
        for line in intro:
            self.print_terminal(line)
            time.sleep(0.01)
        self.entry_input.config(state="normal")

    def handle_input(self, event):
        if self.is_typing:
            return
        user_input = self.entry_input.get().strip()
        self.entry_input.delete(0, "end")
        
        if not user_input:
            return

        self.txt_display.config(state="normal")
        self.txt_display.insert("end", f"你:\\> {user_input}\n\n")
        self.txt_display.config(state="disabled")

        lowered_input = user_input.lower()
        
        if lowered_input in ['dir', 'ls']:
            self.execute_dir()
            return
        
        if lowered_input.startswith('run '):
            filename = user_input[4:].strip()
            self.execute_run(filename)
            return

        if lowered_input == 'update':
            self.entry_input.config(state="disabled")
            self.print_terminal(f"PAL:\\> 正在全速接入您的 GitHub 数据库 [{GITHUB_REPO}] ...")
            threading.Thread(target=self.execute_github_update, daemon=True).start()
            return

        if len(self.chat_history) == 0:
            full_content = SYSTEM_PROMPT + user_input
            self.chat_history.append({"role": "user", "content": full_content})
        else:
            self.chat_history.append({"role": "user", "content": user_input})

        self.entry_input.config(state="disabled")
        self.print_terminal("PAL:\\> 正在联络 AI 核心编织世界线...", end_line=False)
        
        self.current_model_index = 0
        threading.Thread(target=self.get_ai_response_thread, daemon=True).start()

    def execute_github_update(self):
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/"
        headers = {"User-Agent": "PAL_OS_Terminal_Updater"}
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                files_json = response.json()
                target_files = [f for f in files_json if f['type'] == 'file' and (f['name'].endswith('.py') or f['name'].endswith('.pyw'))]
                
                if not target_files:
                    self.root.after(0, lambda: self.print_terminal(f"  [提示] 扫描完毕，但该仓库根目录下没有找到任何 .py 或 .pyw 文件。\n\nPAL_OS:\\> ", end_line=False))
                    self.root.after(0, lambda: self.entry_input.config(state="normal"))
                    return
                
                self.root.after(0, lambda: self.print_terminal(f"  [发现] 成功捕获了 {len(target_files)} 个云端文件，开始同步下载..."))
                
                success_count = 0
                for file_info in target_files:
                    file_name = file_info['name']
                    download_url = file_info['download_url']
                    
                    file_res = requests.get(download_url, timeout=15)
                    if file_res.status_code == 200:
                        with open(file_name, "wb") as f:
                            f.write(file_res.content)
                        success_count += 1
                        self.root.after(0, lambda name=file_name: self.print_terminal(f"   -> 同步成功: {name}"))
                
                self.root.after(0, lambda: self.print_terminal(f"\n  [OK] 远程全自动化更新完成！成功拉取 {success_count} 个游戏模块。"))
            elif response.status_code == 404:
                self.root.after(0, lambda: self.print_terminal(f"  [FAIL] 404 错误：找不到该路径。请确认您的 GitHub 仓库是否已设为 公开(Public) 状态。"))
            else:
                self.root.after(0, lambda: self.print_terminal(f"  [FAIL] 连线受阻，GitHub 返回错误码: {response.status_code}"))
                
        except Exception as e:
            self.root.after(0, lambda: self.print_terminal(f"  [网络物理故障] 接入云端失败，原因: {e}"))
            
        self.root.after(0, lambda: self.print_terminal("\nPAL_OS:\\> ", end_line=False))
        self.root.after(0, lambda: self.entry_input.config(state="normal"))

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
        
        self.print_terminal("\nPAL_OS:\\> ", end_line=False)

    def execute_run(self, filename):
        if not filename:
            self.print_terminal("PAL:\\> 错误：请指定要运行的文件名！例如: run snake.py")
            self.print_terminal("\nPAL_OS:\\> ", end_line=False)
            return
            
        current_dir = os.getcwd()
        full_path = os.path.join(current_dir, filename)
        
        if not os.path.exists(full_path):
            self.print_terminal(f"PAL:\\> 找不到文件 '{filename}'。请确认文件名，或输入 'dir' 检查。")
            self.print_terminal("\nPAL_OS:\\> ", end_line=False)
            return
            
        self.print_terminal(f"PAL:\\> 正在尝试唤醒本地模块 [{filename}] ...")
        
        def launch_script():
            try:
                interpreter = sys.executable if not filename.endswith('.pyw') else sys.executable.replace("python.exe", "pythonw.exe")
                subprocess.Popen([interpreter, full_path], cwd=current_dir)
                self.root.after(0, lambda: self.print_terminal(f"  [OK] 模块 {filename} 已成功在后台沙盒中拉起！\n\nPAL_OS:\\> ", end_line=False))
            except Exception as e:
                self.root.after(0, lambda: self.print_terminal(f"  [FAIL] 模块拉起失败。错误信息: {e}\n\nPAL_OS:\\> ", end_line=False))

        threading.Thread(target=launch_script, daemon=True).start()

    def get_ai_response_thread(self):
        headers = {
            "Authorization": f"Bearer {API_KEY.strip()}",
            "Content-Type": "application/json"
        }
        ai_reply = ""
        success = False
        
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

        self.root.after(0, lambda: self.display_ai_reply(ai_reply))

    def display_ai_reply(self, reply_text):
        self.txt_display.config(state="normal")
        self.txt_display.delete("end-2c linestart", "end")
        self.txt_display.config(state="disabled")

        self.print_terminal(f"PAL:\\> {reply_text}\n")
        self.chat_history.append({"role": "assistant", "content": reply_text})
        
        if len(self.chat_history) > 20:
            self.chat_history = self.chat_history[-16:]
            if self.chat_history[0]["role"] != "user":
                self.chat_history.pop(0)

        self.entry_input.config(state="normal")
        self.entry_input.focus_set()

if __name__ == "__main__":
    GameGeneratorPalSimulator()