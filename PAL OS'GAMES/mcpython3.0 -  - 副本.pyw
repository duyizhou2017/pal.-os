import sys
import os
import random
import time
import webbrowser
import multiprocessing
import threading
import socket
import json
import urllib.request
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk
from queue import Queue

# 延迟导入 3D 引擎和噪声库，确保启动器和更新界面秒开
def import_ursina():
    global Ursina, FirstPersonController, color, scene, DirectionalLight, AmbientLight, Button, camera, Entity, Text, mouse, destroy, invoke, Vec3, held_keys
    from ursina import Ursina, color, scene, DirectionalLight, AmbientLight, Button, camera, Entity, Text, mouse, destroy, invoke, Vec3, held_keys
    from ursina.prefabs.first_person_controller import FirstPersonController
    
    global PerlinNoise
    try:
        from perlin_noise import PerlinNoise
    except ImportError:
        # 使用 subprocess 替代 os.system，实现真正的无窗口静默安装
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "perlin-noise"], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=0x08000000)
        except Exception:
            pass
        from perlin_noise import PerlinNoise

# ==========================================
# --- 0. 全局配置 ---
# ==========================================
CURRENT_VERSION = 4.0
VERSION_URL = "https://raw.githubusercontent.com/duyizhou2017/mc-c-Repository/main/version.txt"
CODE_URL = "https://raw.githubusercontent.com/duyizhou2017/mc-c-Repository/main/mcpython3.1.pyw"
SAVE_FILE = "map_save.json"

# ==========================================
# --- 1. 独立启动更新界面 ---
# ==========================================
class SplashUpdater:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Minecraft Python 3.1 启动检查")
        self.root.geometry("360x180")
        self.root.resizable(False, False)
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.geometry(f"+{int((screen_width-360)/2)}+{int((screen_height-180)/2)}")
        
        self.lbl_title = tk.Label(self.root, text="正在初始化游戏配置...", font=("Microsoft YaHei", 12, "bold"))
        self.lbl_title.pack(pady=15)
        
        self.lbl_status = tk.Label(self.root, text="正在准备本地资源...", font=("Microsoft YaHei", 9), fg="gray")
        self.lbl_status.pack(pady=5)
        
        self.progress = ttk.Progressbar(self.root, mode="indeterminate", length=280)
        self.progress.pack(pady=10)
        self.progress.start(15)
        
        self.root.after(200, self.start_async_check)
        self.root.mainloop()

    def start_async_check(self):
        self.lbl_status.config(text="正在连接云端检查更新...")
        threading.Thread(target=self.check_update_logic, daemon=True).start()

    def check_update_logic(self):
        try:
            req = urllib.request.Request(VERSION_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3) as response:
                latest_version = float(response.read().decode('utf-8').strip())
            
            if latest_version > CURRENT_VERSION:
                self.root.after(0, lambda: self.prompt_update(latest_version))
            else:
                self.root.after(0, self.finish_and_launch)
        except Exception:
            self.root.after(0, lambda: self.skip_update("无法连接到更新服务器，即将直接进入游戏..."))

    def prompt_update(self, latest_version):
        self.progress.stop()
        self.progress.config(mode="determinate", value=0)
        self.lbl_title.config(text="发现新版本！", fg="#4CAF50")
        self.lbl_status.config(text=f"当前版本: V{CURRENT_VERSION}  ->  最新版本: V{latest_version}", fg="black")
        
        ans = messagebox.askyesno("发现新版本！", f"检测到有新版本 V{latest_version} 可用。\n是否立即自动下载更新？", parent=self.root)
        if ans:
            self.lbl_title.config(text="正在更新核心文件...")
            self.progress.config(mode="indeterminate")
            self.progress.start(10)
            threading.Thread(target=self.download_logic, daemon=True).start()
        else:
            self.finish_and_launch()

    def download_logic(self):
        try:
            current_file = sys.argv[0]
            temp_file = current_file + ".tmp"
            if os.path.exists(temp_file):
                try: os.remove(temp_file)
                except: pass
            urllib.request.urlretrieve(CODE_URL, temp_file)
            if os.path.exists(current_file): 
                try: os.remove(current_file)
                except: os.rename(current_file, current_file + f".v{CURRENT_VERSION}.old")
            os.rename(temp_file, current_file)
            messagebox.showinfo("更新成功", "游戏已成功更新！即将自动重启。", parent=self.root)
            self.root.destroy()
            os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception as e:
            messagebox.showerror("更新失败", f"下载更新时出错: {e}", parent=self.root)
            self.finish_and_launch()

    def skip_update(self, reason):
        self.progress.stop()
        self.lbl_status.config(text=reason, fg="orange")
        self.root.after(800, self.finish_and_launch)

    def finish_and_launch(self):
        self.root.destroy()
        create_main_launcher()


# ==========================================
# --- 2. 联机服务端进程 ---
# ==========================================
def run_dedicated_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server_socket.bind(("0.0.0.0", 25565))
        server_socket.listen()
    except Exception:
        return

    clients = {}
    player_data = {}
    client_id_counter = 1
    lock = threading.Lock()

    def handle_client(client_conn, client_id):
        nonlocal client_id_counter
        r, g, b = random.uniform(0.2, 1.0), random.uniform(0.2, 1.0), random.uniform(0.2, 1.0)
        player_name = f"Player_{client_id}"
        with lock:
            player_data[client_id] = {"x": 0, "y": 20, "z": 0, "color": [r, g, b], "name": player_name}
        broadcast(json.dumps({"type": "player_joined", "id": client_id, "color": [r, g, b], "name": player_name}))
        
        with lock:
            for existing_id, info in player_data.items():
                if existing_id != client_id:
                    try: client_conn.sendall((json.dumps({"type": "player_joined", "id": existing_id, "color": info["color"], "name": info["name"]}) + "\n").encode())
                    except: pass

        buffer = ""
        while True:
            try:
                data = client_conn.recv(2048).decode('utf-8')
                if not data: break
                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if not line: continue
                    msg = json.loads(line)
                    if msg["type"] == "my_position":
                        with lock:
                            if client_id in player_data:
                                player_data[client_id].update({"x": msg["x"], "y": msg["y"], "z": msg["z"]})
                    elif msg["type"] in ["place_block", "break_block"]:
                        broadcast(json.dumps(msg))
            except: 
                break

        with lock:
            if client_id in player_data: del player_data[client_id]
            if client_id in clients: del clients[client_id]
        broadcast(json.dumps({"type": "player_left", "id": client_id}))
        client_conn.close()

    def broadcast(message_str):
        payload = (message_str + "\n").encode('utf-8')
        with lock:
            for conn in list(clients.values()):
                try: conn.sendall(payload)
                except: pass

    def position_sync_loop():
        while True:
            with lock:
                if player_data: 
                    broadcast(json.dumps({"type": "update_positions", "data": player_data}))
            time.sleep(0.03)

    threading.Thread(target=position_sync_loop, daemon=True).start()

    while True:
        try:
            conn, addr = server_socket.accept()
            with lock:
                cid = client_id_counter
                client_id_counter += 1
                clients[cid] = conn
            threading.Thread(target=handle_client, args=(conn, cid), daemon=True).start()
        except: 
            break


# ==========================================
# --- 3. 核心 3D 游戏进程（无限多层柏林噪声优化版） ---
# ==========================================
def run_ursina_game(multiplayer_mode=False):
    import_ursina()  
    import math  # 引入数学库用于精确的坐标切片
    
    net_status = {"socket": None, "connected": False}
    other_players = {}
    msg_queue = Queue() 

    app = Ursina()
    app.hotkeys = {'toggle_fullscreen': 'f11'} 

    # === 视觉优化 ===
    camera.clip_plane_far = 300         # 稍微加长远景裁剪，配合无限地形
    scene.fog_density = 0.002           
    scene.fog_color = color.light_gray   

    BLOCK_TYPES = [
        {"name": "草方块", "color": color.rgb(108, 179, 71)},     
        {"name": "泥土块", "color": color.rgb(134, 96, 67)},      
        {"name": "石头块", "color": color.rgb(125, 125, 125)},    
        {"name": "木头块", "color": color.rgb(197, 150, 93)},     
        {"name": "红砖块", "color": color.rgb(163, 71, 55)}       
    ]
    current_block_index = 0  

    # --- 柏林噪声无限地形参数 ---
    # 调整 octaves 和缩放，可以让地形起伏更自然、雄伟
    noise = PerlinNoise(octaves=3, seed=random.randint(1, 10000))
    generated_chunks = {}   # 存储所有方块，结构为 {(x, y, z): Voxel_Entity}
    
    RENDER_DISTANCE = 10    # 动态加载半径（因为变多层了，渲染半径控制在10帧率最稳）
    BASE_HEIGHT = 5         # 基础地平线高度
    NOISE_SCALE = 12        # 噪声振幅（决定山峰的最大额外高度，5+12=17层，完美满足多层需求）

    def connect_to_server(ip, port):
        if net_status["socket"]:
            try: net_status["socket"].close()
            except: pass
            net_status["socket"] = None
            net_status["connected"] = False
        for p_id in list(other_players.keys()):
            destroy(other_players[p_id])
            del other_players[p_id]
        while not msg_queue.empty(): msg_queue.get()
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip, port))
            net_status["socket"] = s
            net_status["connected"] = True
            
            def receive_loop():
                buffer = ""
                while net_status["connected"]:
                    try:
                        data = s.recv(2048).decode('utf-8')
                        if not data: break
                        buffer += data
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            if line: msg_queue.put(json.loads(line))
                    except: break
                net_status["connected"] = False
            threading.Thread(target=receive_loop, daemon=True).start()
            server_info_text.text = f"当前连接: {ip}:{port}"
            server_info_text.color = color.green
        except Exception:
            server_info_text.text = f"连接失败: {ip}:{port}"
            server_info_text.color = color.red
            net_status["socket"] = None
            net_status["connected"] = False

    sun_light = DirectionalLight(parent=scene, y=2, z=3, rotation=(45, -45, 0))
    ambient_light = AmbientLight(parent=scene, color=color.rgba(140, 140, 140, 255))

    class Voxel(Button):
        def __init__(self, position=(0,0,0), custom_color=None, is_manual=False):
            chosen_color = custom_color if custom_color else BLOCK_TYPES[current_block_index]["color"]
            super().__init__(
                parent=scene, position=position, model='cube', texture='white_cube',            
                color=color.tint(chosen_color, random.uniform(-0.03, 0.03)), 
                highlight_color=color.white,       
            )
            self.is_manual = is_manual 
            
        def input(self, key):
            if self.hovered and not lobby_panel.enabled: 
                if key == 'right mouse down':
                    pos = self.position + mouse.normal
                    # 严格取整，防止浮点数键污染字典
                    ix, iy, iz = math.floor(pos.x), math.floor(pos.y), math.floor(pos.z)
                    if multiplayer_mode and net_status["connected"]: 
                        c = BLOCK_TYPES[current_block_index]["color"]
                        try: net_status["socket"].sendall((json.dumps({
                            "type": "place_block", "x": ix, "y": iy, "z": iz,
                            "r": c.r, "g": c.g, "b": c.b
                        }) + "\n").encode('utf-8'))
                        except: pass
                    else: 
                        v = Voxel(position=(ix, iy, iz), is_manual=True)
                        generated_chunks[(ix, iy, iz)] = v
                if key == 'left mouse down':
                    ix, iy, iz = math.floor(self.position.x), math.floor(self.position.y), math.floor(self.position.z)
                    if multiplayer_mode and net_status["connected"]: 
                        try: net_status["socket"].sendall((json.dumps({"type": "break_block", "x": ix, "y": iy, "z": iz}) + "\n").encode('utf-8'))
                        except: pass
                    else: 
                        pos_key = (ix, iy, iz)
                        if pos_key in generated_chunks: del generated_chunks[pos_key]
                        destroy(self)

    # 地图旧存档加载
    saved_blocks = []
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f: saved_blocks = json.load(f)
        except: pass
    if isinstance(saved_blocks, list) and saved_blocks:
        for b in saved_blocks:
            try:
                pos_tuple = (int(b['x']), int(b['y']), int(b['z']))
                v = Voxel(position=pos_tuple, custom_color=color.rgb(b['c'][0], b['c'][1], b['c'][2]), is_manual=True)
                generated_chunks[pos_tuple] = v
            except: pass

    # === 多层垂直填充生成函数 ===
    def generate_column(x, z):
        """根据柏林噪声在指定 (x, z) 坐标生成一整列垂直方块"""
        # 分母越大地形越平缓，越小山峰越陡峭
        noise_val = noise([x / 40, z / 40])
        
        # 计算当前坐标的最高地表高度
        max_y = int(noise_val * NOISE_SCALE) + BASE_HEIGHT
        
        # 从下往上生成多层方块（形成厚度超10层的实体大陆）
        for y in range(0, max_y + 1):
            pos_tuple = (x, y, z)
            if pos_tuple not in generated_chunks:
                if y == max_y:
                    # 最顶层是草方块
                    chosen_color = BLOCK_TYPES[0]["color"]
                elif y > max_y - 3:
                    # 地表下方2-3层是泥土
                    chosen_color = BLOCK_TYPES[1]["color"]
                else:
                    # 深层是坚硬的石头
                    chosen_color = BLOCK_TYPES[2]["color"]
                
                generated_chunks[pos_tuple] = Voxel(position=pos_tuple, custom_color=chosen_color)

    # 预生成出生点周围区块（防止开局掉落虚空）
    for x in range(-10, 10):
        for z in range(-10, 10):
            generate_column(x, z)

    # 动态无限渲染计算（随着玩家走动，实时生成前方的多层方块）
    def handle_infinite_terrain():
        px, pz = math.floor(player.x), math.floor(player.z)
        
        # 1. 动态生成新走进的视野区块
        for x in range(px - RENDER_DISTANCE, px + RENDER_DISTANCE):
            for z in range(pz - RENDER_DISTANCE, pz + RENDER_DISTANCE):
                generate_column(x, z)

        # 2. 远景自然方块定时安全回收（释放内存，防止无限世界导致程序卡死）
        for pos_key in list(generated_chunks.keys()):
            bx, _, bz = pos_key
            if not generated_chunks[pos_key].is_manual:
                if abs(bx - px) > RENDER_DISTANCE + 6 or abs(bz - pz) > RENDER_DISTANCE + 6:
                    destroy(generated_chunks[pos_key])
                    del generated_chunks[pos_key]

    # 初始化第一人称角色（将出生高度提高到 Y=25，确保100%落在新生成的高山上）
    player = FirstPersonController()
    player.position = (0, 25, 0)  
    player.is_dead = False

    def respawn():
        player.position = (0, 25, 0)  
        player.is_dead = False
        death_text.disable()

    # UI 界面
    death_text = Text(text="你死了！正在复活...", scale=3, origin=(0, 0), color=color.red, enabled=False)
    hotbar_panel = Entity(parent=camera.ui, model='quad', scale=(0.5, 0.06), position=(0, -0.44), color=color.black33)
    hotbar_text = Text(parent=hotbar_panel, text="", scale=1.4, position=(-0.45, 0), color=color.white)

    def update_hotbar_ui():
        hotbar_text.text = f"当前选块: {BLOCK_TYPES[current_block_index]['name']}"
    update_hotbar_ui()

    lobby_panel = Entity(parent=camera.ui, model='quad', scale=(0.6, 0.7), color=color.black66, enabled=False)
    Text(parent=lobby_panel, text="=== 服务器大厅 ===", scale=2, origin=(0, -3), color=color.gold)
    server_info_text = Text(parent=lobby_panel, text="未连接到任何服务器", scale=1.2, origin=(0, -2.2), color=color.white)

    def make_connect_callback(ip, port): return lambda: connect_to_server(ip, port)
    server_list = [{"name": "本地测试服", "ip": "127.0.0.1", "port": 25565}]
    for idx, s_info in enumerate(server_list):
        btn = Button(parent=lobby_panel, text=f"{s_info['name']} ({s_info['ip']}:{s_info['port']})", scale=(0.8, 0.08), y=0.1 - (idx * 0.12), color=color.azure)
        btn.on_click = make_connect_callback(s_info["ip"], s_info["port"])

    Text(parent=lobby_panel, text="提示: [Ctrl+5] 大厅 | [1-5] 物品切换 | 快速连按 10 次 [空格] 存档退出", scale=1, y=-0.4, origin=(0, 0), color=color.light_gray)

    if multiplayer_mode: connect_to_server("127.0.0.1", 25565)

    last_toggle_time = 0
    space_click_count = 0
    last_space_time = 0

    def save_and_exit_game():
        current_map_data = []
        for pos_key, e in generated_chunks.items():
            if e.is_manual: 
                current_map_data.append({
                    'x': int(pos_key[0]), 'y': int(pos_key[1]), 'z': int(pos_key[2]),
                    'c': [e.color.r, e.color.g, e.color.b]
                })
        try:
            with open(SAVE_FILE, "w", encoding="utf-8") as f: json.dump(current_map_data, f)
        except: pass
        if net_status["socket"]:
            try: net_status["socket"].close()
            except: pass
        os._exit(0)

    def input(key):
        nonlocal space_click_count, last_space_time, current_block_index
        if key == 'space':
            current_time = time.time()
            if current_time - last_space_time > 1.2: space_click_count = 1
            else: space_click_count += 1
            last_space_time = current_time
            if space_click_count >= 10: save_and_exit_game()
        if not lobby_panel.enabled:
            if key in ['1', '2', '3', '4', '5']:
                current_block_index = int(key) - 1
                update_hotbar_ui()

    def update():
        nonlocal last_toggle_time
        handle_infinite_terrain()

        if (held_keys['control'] and held_keys['5']) and (time.time() - last_toggle_time > 0.3):
            last_toggle_time = time.time()
            lobby_panel.enabled = not lobby_panel.enabled
            if lobby_panel.enabled:
                mouse.locked, mouse.visible, player.enabled = False, True, False
                hotbar_panel.disable() 
            else:
                mouse.locked, mouse.visible, player.enabled = True, False, True
                hotbar_panel.enable()

        # 因为世界加深了，所以坠入虚空的判定改为 -20 层以下
        if player.y < -20 and not player.is_dead: 
            player.is_dead = True
            death_text.enable()  
            invoke(respawn, delay=1.5)

        if multiplayer_mode and net_status["connected"]:
            try: net_status["socket"].sendall((json.dumps({"type": "my_position", "x": player.x, "y": player.y, "z": player.z}) + "\n").encode('utf-8'))
            except: net_status["connected"] = False

        while not msg_queue.empty():
            msg = msg_queue.get()
            m_type = msg.get("type")
            if m_type == "player_joined":
                idx = msg["id"]
                if idx not in other_players:
                    c = msg["color"]
                    p_model = Entity(model='cube', color=color.rgb(c[0], c[1], c[2]), scale=(1, 2, 1))
                    name_tag = Text(text=msg["name"], parent=p_model, position=(0, 0.8, 0), scale=5, origin=(0, 0), color=color.white)
                    name_tag.billboard = True 
                    other_players[idx] = p_model
            elif m_type == "player_left":
                idx = msg["id"]
                if idx in other_players:
                    destroy(other_players[idx])
                    del other_players[idx]
            elif m_type == "update_positions":
                for idx, info in msg["data"].items():
                    if int(idx) in other_players: other_players[int(idx)].position = Vec3(info["x"], info["y"], info["z"])
            elif m_type == "place_block":
                target_pos = Vec3(msg["x"], msg["y"], msg["z"])
                block_color = color.rgb(msg.get("r", 1), msg.get("g", 1), msg.get("b", 1))
                pos_tuple = (int(msg["x"]), int(msg["y"]), int(msg["z"]))
                if pos_tuple not in generated_chunks: 
                    generated_chunks[pos_tuple] = Voxel(position=target_pos, custom_color=block_color, is_manual=True)
            elif m_type == "break_block":
                pos_tuple = (int(msg["x"]), int(msg["y"]), int(msg["z"]))
                if pos_tuple in generated_chunks:
                    destroy(generated_chunks[pos_tuple])
                    del generated_chunks[pos_tuple]

    app.run()


# ==========================================
# --- 4. 启动器主控制界面 ---
# ==========================================
def create_main_launcher():
    root = tk.Tk()
    root.title(f"Minecraft Python 启动器 V{CURRENT_VERSION}")
    root.geometry("340x360")  
    root.resizable(False, False)

    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"+{int((sw-340)/2)}+{int((sh-360)/2)}")

    def start_game():
        root.withdraw()
        mode_selected = game_mode_var.get()
        if mode_selected == 1:
            game_process = multiprocessing.Process(target=run_ursina_game, args=(False,))
            game_process.start()
        else:
            server_process = multiprocessing.Process(target=run_dedicated_server)
            server_process.daemon = True 
            server_process.start()
            time.sleep(0.5)  
            game_process = multiprocessing.Process(target=run_ursina_game, args=(True,))
            game_process.start()

        def monitor_game_process():
            game_process.join()  
            root.after(0, root.deiconify)
        threading.Thread(target=monitor_game_process, daemon=True).start()

    title_label = tk.Label(root, text="MINECRAFT PYTHON", font=("Arial Black", 15, "bold"), fg="#2C3E50")
    title_label.pack(pady=12)

    ver_label = tk.Label(root, text=f"Clear Horizon - Version {CURRENT_VERSION}", font=("Arial", 8, "italic"), fg="#7F8C8D")
    ver_label.pack()

    mode_frame = tk.LabelFrame(root, text=" 模式选择 ", font=("Microsoft YaHei", 10, "bold"), padx=10, pady=8)
    mode_frame.pack(fill="x", padx=20, pady=8)

    game_mode_var = tk.IntVar(value=1) 
    r1 = tk.Radiobutton(mode_frame, text="本地单人游戏", variable=game_mode_var, value=1, font=("Microsoft YaHei", 10))
    r1.pack(anchor="w", side="left", padx=15)
    r2 = tk.Radiobutton(mode_frame, text="局域网多人联机", variable=game_mode_var, value=2, font=("Microsoft YaHei", 10))
    r2.pack(anchor="w", side="left", padx=15)

    btn1 = tk.Button(root, text=" 进 入 游 戏 ", command=start_game, bg="#2ECC71", fg="white", font=("Microsoft YaHei", 12, "bold"), relief="flat", bd=0)
    btn1.pack(fill="x", padx=20, pady=12, ipady=4)  

    tk.Button(root, text="制作人员信息", command=lambda: messagebox.showinfo("开发者名单", "本程序由 Mojang AB · 杜奕洲 · Notch · Gemini 共同制作\n感谢您的游玩与支持！"), font=("Microsoft YaHei", 9)).pack(fill="x", padx=20, pady=2)
    tk.Button(root, text="访问官方网站", command=lambda: webbrowser.open("http://minecraft.net"), font=("Microsoft YaHei", 9)).pack(fill="x", padx=20, pady=2)   
    tk.Button(root, text="扩展与未来规划", command=lambda: messagebox.showinfo("4.0 多层无限世界版", f"1. 重构了无限世界算法，带来了立体垂直填充地形。\n2. 默认世界深度和起伏高度突破10层以上，增加挖矿乐趣。"), font=("Microsoft YaHei", 9)).pack(fill="x", padx=20, pady=2)   

    root.mainloop()


# ==========================================
# --- 5. 程序主入口 ---
# ==========================================
if __name__ == '__main__':
    multiprocessing.freeze_support()
    # 修复 Windows 下多进程重启循环初始化 Splash 的问题
    if len(sys.argv) == 1 or not sys.argv[0].endswith("pyw"):
        SplashUpdater()