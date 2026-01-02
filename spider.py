import os
import re
import sys
import subprocess
import threading
import time
import json
import shutil
import tkinter as tk
from tkinter import END, MULTIPLE, Listbox, messagebox, scrolledtext,Toplevel,filedialog
from io import BytesIO
from typing import final

import requests
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import qrcode                # QR code
from PIL import Image, ImageTk

# GUI
class BiliDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Bilibili Video Downloader")
        self.root.geometry("1100x1400")

        # status label
        self.status_label = ttk.Label(
            root,
            text=" Status: Ready (Waiting for input) ",
            bootstyle="inverse-secondary",
            anchor="w"
        )
        self.status_label.pack(side=BOTTOM, fill=X)

        # Panewindow
        self.paned_window = ttk.Panedwindow(root, orient=VERTICAL)
        self.paned_window.pack(fill=BOTH, expand=YES, padx=10, pady=10)

        # control section
        self.control_pane = ttk.Frame(self.paned_window)
        self.paned_window.add(self.control_pane, weight=0)

        # Title
        title_label = ttk.Label(
            self.control_pane,
            text="Bilibili Video Downloader",
            font=("Helvetica", 24, "bold"),
            bootstyle="primary"
        )
        title_label.pack(pady=(0, 15))

        # init cofig(cookie) & download path
        self.config_file = "config.json"
        self.download_dir = os.getcwd() # default download path

        # STEP 1: URL & Cookie
        input_group = ttk.Labelframe(self.control_pane, text=" Step 1: Input URL & Login ", padding=12, bootstyle="info")
        input_group.pack(fill=X, pady=5)

        # URL Frame
        url_frame = ttk.Frame(input_group)
        url_frame.pack(fill=X, expand=YES)

        self.url_entry = ttk.Entry(url_frame, font=("Consolas", 11))
        self.url_entry.pack(side=LEFT, fill=X, expand=YES, padx=(0, 10))

        ttk.Button(
            url_frame,
            text="Clear",
            bootstyle="secondary-outline",
            command=lambda: self.url_entry.delete(0, END)
        ).pack(side=RIGHT)

        # Cookie/Login Frame
        login_frame = ttk.Frame(input_group)
        login_frame.pack(fill=X, expand=YES, pady=(10, 0))
        
        # Current Status
        ttk.Label(login_frame, text="Account:", font=("Helvetica", 10)).pack(side=LEFT)
        self.lbl_login_status = ttk.Label(login_frame, text="Guest (Low Quality)", bootstyle="secondary")
        self.lbl_login_status.pack(side=LEFT, padx=10)

        # Login button
        self.btn_login = ttk.Button(
            login_frame,
            text="Login via QR Code", # QR code to login
            bootstyle="warning-outline",
            command=self.open_qr_login_window
        )
        self.btn_login.pack(side=RIGHT)

        # init value
        self.qr_window = None
        self.stop_qr_check = False

        # --- STEP 2: Options ---

        # Download Path Frame
        path_frame = ttk.Frame(input_group)
        path_frame.pack(fill=X, pady=(0, 10))

        ttk.Label(path_frame, text="Save To:  ", font=("Helvetica", 10)).pack(side=LEFT)
        
        self.path_var = tk.StringVar(value=self.download_dir)
        self.path_entry = ttk.Entry(path_frame, textvariable=self.path_var, font=("Consolas", 9))
        self.path_entry.pack(side=LEFT, fill=X, expand=YES, padx=(0, 10))
        
        ttk.Button(path_frame, text="Browse...", bootstyle="secondary", command=self.browse_folder).pack(side=RIGHT)

        self.options_frame = ttk.Labelframe(self.control_pane, text=" Step 2: Download Options ", padding=12, bootstyle="primary")
        self.options_frame.pack(fill=BOTH, expand=YES, pady=10)

        # pages info on left
        self.opt_left = ttk.Frame(self.options_frame)
        self.opt_left.pack(side=LEFT, fill=BOTH, expand=YES, padx=(0, 15))

        # video/audio/output options on right
        self.opt_right = ttk.Frame(self.options_frame)
        self.opt_right.pack(side=RIGHT, fill=BOTH, expand=NO)

        # pages list
        ttk.Label(self.opt_left, text="Page List (Multi-select available):", font=("Helvetica", 10)).pack(anchor=W)
        list_scroll_frame = ttk.Frame(self.opt_left)
        list_scroll_frame.pack(fill=BOTH, expand=YES, pady=5)

        self.page_listbox = Listbox(list_scroll_frame, selectmode=MULTIPLE, height=10, font=("Consolas", 10))
        self.page_listbox.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar = ttk.Scrollbar(list_scroll_frame, orient=VERTICAL, command=self.page_listbox.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.page_listbox.config(yscrollcommand=scrollbar.set)

        btn_box = ttk.Frame(self.opt_left)
        btn_box.pack(fill=X)
        ttk.Button(btn_box, text="Select All", bootstyle="link", command=self.select_all_pages).pack(side=LEFT)
        ttk.Button(btn_box, text="Clear", bootstyle="link", command=self.clear_all_pages).pack(side=LEFT)

        # --- Quality & Output Mode Options ---
        
        # 1. Output Mode (New Feature)
        ttk.Label(self.opt_right, text="Output Format:", font=("Helvetica", 10, "bold")).pack(anchor=W, pady=(0, 5))
        self.output_mode_combo = ttk.Combobox(self.opt_right, state="readonly", width=28)
        self.output_mode_combo['values'] = [
            "Merge Video + Audio (Default)",
            "Audio Only (.m4a)",
            "Video Only (No Sound .mp4)"
        ]
        self.output_mode_combo.current(0)
        self.output_mode_combo.pack(fill=X, pady=(0, 15))

        # 2. Video Quality
        ttk.Label(self.opt_right, text="Video Quality:", font=("Helvetica", 10)).pack(anchor=W, pady=(0, 5))
        self.video_quality_combo = ttk.Combobox(self.opt_right, state="readonly", width=28)
        self.quality_map = {
            "Highest Available": 999,
            "8K Ultra (ID: 127)": 127,
            "Dolby Vision (ID: 126)": 126,
            "HDR True Color (ID: 125)": 125,
            "4K Ultra (ID: 120)": 120,
            "1080P 60FPS (ID: 116)": 116,
            "1080P+ High Bitrate (ID: 112)": 112,
            "1080P High (ID: 80)": 80,
            "720P 60FPS (ID: 74)": 74,
            "720P (ID: 64)": 64,
            "480P (ID: 32)": 32,
            "360P (ID: 16)": 16
        }
        self.video_quality_combo['values'] = list(self.quality_map.keys())
        self.video_quality_combo.current(0)
        self.video_quality_combo.pack(fill=X, pady=(0, 15))

        # 3. Audio Quality
        ttk.Label(self.opt_right, text="Audio Quality:", font=("Helvetica", 10)).pack(anchor=W, pady=(0, 5))
        self.audio_quality_combo = ttk.Combobox(self.opt_right, state="readonly", width=28)
        self.audio_quality_map = {
            "Highest": 999,
            "Hi-Res Lossless (ID: 30251)": 30251,
            "Dolby Atmos (ID: 30250)": 30250,
            "192K (ID: 30280)": 30280,
            "132K (ID: 30232)": 30232,
            "64K (ID: 30216)": 30216
        }
        self.audio_quality_combo['values'] = list(self.audio_quality_map.keys())
        self.audio_quality_combo.current(0)
        self.audio_quality_combo.pack(fill=X)

        # main button
        self.btn_action = ttk.Button(
            self.control_pane,
            text="Analyze URL",
            bootstyle="success",
            width=30,
            command=self.handle_button_click
        )
        self.btn_action.pack(pady=15)

        # progress
        self.progress_var = ttk.DoubleVar()
        self.progress_bar = ttk.Floodgauge(
            self.control_pane,
            bootstyle="success",
            font=("Helvetica", 10),
            text="Idle",
            variable=self.progress_var,
            maximum=100
        )
        self.progress_bar.pack(fill=X, pady=(0, 10))

        # Log pane
        self.log_pane = ttk.Labelframe(self.paned_window, text=" Execution Log ", padding=10, bootstyle="secondary")
        self.paned_window.add(self.log_pane, weight=1)

        self.log_box = scrolledtext.ScrolledText(
            self.log_pane,
            height=15,
            font=("Consolas", 10),
            bg="#2b3e50",
            fg="white",
            insertbackground="white"
        )
        self.log_box.pack(fill=BOTH, expand=YES)

        # State
        self.current_state = "analyze"
        self.video_metadata = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
            'Referer': 'https://www.bilibili.com/',
            # Default empty/guest cookie initially
            'Cookie': '' 
        }

        # load config with start
        self.load_settings()

    # download path setting

    def browse_folder(self):
        """打开文件夹选择框"""
        selected_dir = filedialog.askdirectory()
        if selected_dir:
            self.download_dir = selected_dir
            self.path_var.set(self.download_dir)
            self.save_settings() # save the choice

    def save_settings(self):
        data = {
            "cookie": self.headers.get('Cookie', ''),
            "download_dir": self.download_dir
        }
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Failed to save settings: {e}")

    def load_settings(self):
        if not os.path.exists(self.config_file):
            return
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            saved_dir = data.get("download_dir", "")
            if saved_dir and os.path.exists(saved_dir):
                self.download_dir = saved_dir
                self.path_var.set(self.download_dir)
            
            saved_cookie = data.get("cookie", "")
            if saved_cookie:
                self.headers['Cookie'] = saved_cookie
                # validate the cookie
                if "SESSDATA" in saved_cookie:
                    self.lbl_login_status.configure(text="Logged In (Auto-Loaded)", bootstyle="success")
                    self.log("[CONFIG] Cookies loaded from file.")
        except Exception as e:
            self.log(f"[CONFIG] Error loading config: {e}")

    def open_qr_login_window(self):

        if self.qr_window is not None:
            self.qr_window.lift()
            return

        self.qr_window = Toplevel(self.root)
        self.qr_window.title("Scan to Login")
        self.qr_window.geometry("600x600")
        self.qr_window.protocol("WM_DELETE_WINDOW", self.close_qr_window)

        # UI
        ttk.Label(self.qr_window, text="Please Scan with Bilibili App", font=("Helvetica", 11, "bold")).pack(pady=10)
        self.qr_image_label = ttk.Label(self.qr_window)
        self.qr_image_label.pack(pady=5)
        self.qr_status_label = ttk.Label(self.qr_window, text="Loading QR Code...", bootstyle="info")
        self.qr_status_label.pack(pady=10)

        self.stop_qr_check = False
        threading.Thread(target=self.qr_logic_thread, daemon=True).start()

    def close_qr_window(self):
        self.stop_qr_check = True
        if self.qr_window:
            self.qr_window.destroy()
            self.qr_window = None

    def qr_logic_thread(self):
        try:
            # 1. request API form Bilibili
            # Use Session to keep status
            session = requests.Session() 
            
            session.headers.update(self.headers) 

            res = session.get("https://passport.bilibili.com/x/passport-login/web/qrcode/generate")
            
            # Check
            if res.status_code != 200:
                self.log(f"[NETWORK ERROR] API returned {res.status_code}")
            
            data = res.json()['data']
            url = data['url']
            qrcode_key = data['qrcode_key']

            # 2. QR CODE
            qr = qrcode.QRCode(box_size=6, border=2)
            qr.add_data(url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            bio = BytesIO()
            img.save(bio, format="PNG")
            bio.seek(0)
            tk_img = ImageTk.PhotoImage(Image.open(bio))

            # Update UI
            if self.stop_qr_check: return 
            
            self.root.after(0, lambda: self.qr_image_label.configure(image=tk_img) if not self.stop_qr_check else None)
            self.root.after(0, lambda: setattr(self.qr_image_label, 'image', tk_img))

            # 3. Check with rotate
            while not self.stop_qr_check:
                time.sleep(2)
                if self.stop_qr_check: break 
                poll_url = "https://passport.bilibili.com/x/passport-login/web/qrcode/poll"
                poll_res = session.get(poll_url, params={'qrcode_key': qrcode_key})
                poll_data = poll_res.json()
                if self.stop_qr_check: break
                code = poll_res.json()['data']['code']

                if code == 0: # Login success
                    self.log("[LOGIN] Success!")
                    
                    # Cookie
                    cookies_dict = session.cookies.get_dict()
                    cookie_str = "; ".join([f"{k}={v}" for k, v in cookies_dict.items()])
                    
                    self.headers['Cookie'] = cookie_str
                    
                    # Save local after sucessed login
                    self.root.after(0, self.save_settings)

                     # Update UI
                    if not self.stop_qr_check:
                        self.root.after(0, lambda: self.lbl_login_status.configure(text="Logged In (Saved)", bootstyle="success"))
                        self.root.after(0, self.close_qr_window)
                    break
                
                elif code == 86101: # Waitting for scan
                    if not self.stop_qr_check:
                        self.root.after(0, lambda: self.qr_status_label.configure(text="Waiting for scan...", bootstyle="info"))
                elif code == 86090: # Waiting for confirm in mobile phone
                    if not self.stop_qr_check:
                        self.root.after(0, lambda: self.qr_status_label.configure(text="Scanned! Confirm on phone.", bootstyle="success"))
                else: # ERROR
                    if not self.stop_qr_check:
                        self.root.after(0, lambda: self.qr_status_label.configure(text="Expired/Error. Reopen.", bootstyle="danger"))
                    break

        except Exception as e:
            self.log(f"[LOGIN ERROR] {e}")
            print(f"QR Thread Warning: {e}")

    # Button control thread
    def handle_button_click(self):
        if self.current_state == "analyze":
            self.start_analysis_thread()
        elif self.current_state == "download":
            self.start_download_thread()

    def select_all_pages(self):
        self.page_listbox.select_set(0, END)

    def clear_all_pages(self):
        self.page_listbox.selection_clear(0, END)

    # analysis
    def start_analysis_thread(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Input Error", "Please enter a valid URL.")
            return

        self.btn_action.config(state=DISABLED, text="Analyzing...")
        self.update_progress(0, "Connecting to API...")
        self.page_listbox.delete(0, END)

        thread = threading.Thread(target=self.analyze_logic, args=(url,))
        thread.daemon = True
        thread.start()

    def analyze_logic(self, url):
        self.log(f"Analyzing: {url}")
        try:
            match = re.search(r'(BV\w+)', url)
            if not match:
                self.log("[ERROR] Invalid Bilibili URL.")
                self.reset_ui_analyze()
                return
            bvid = match.group(1)

            p_match = re.search(r'[?&]p=(\d+)', url)
            target_p = int(p_match.group(1)) if p_match else 1

            data = self.get_video_details(bvid)
            if not data:
                self.reset_ui_analyze()
                return

            self.video_metadata = {
                'bvid': bvid,
                'title': data['title'],
                'cover': data.get('pic', ''),
                'pages': data.get('pages', []),
                'target_p': target_p,
                'pages_num': data['videos']
            }

            self.log(f"Title: {data['title']}")
            self.root.after(0, self.populate_ui_after_analysis)

        except Exception as e:
            self.log(f"[EXCEPTION] {e}")
            self.reset_ui_analyze()

    def populate_ui_after_analysis(self):
        pages = self.video_metadata['pages']
        target_p = self.video_metadata['target_p']

        target_index = 0
        for i, p in enumerate(pages):
            self.page_listbox.insert(END, f"[P{p['page']}] {p['part']}")
            if p['page'] == target_p:
                target_index = i

        self.page_listbox.select_set(target_index)
        self.page_listbox.see(target_index)

        self.current_state = "download"
        self.btn_action.config(state=NORMAL, text="Download Selected", bootstyle="warning")
        self.status_label.configure(text=" Status: Please select pages, quality and output format. ")
        self.update_progress(0, "Waiting for user selection...")

    def reset_ui_analyze(self):
        self.root.after(0, lambda: self.btn_action.config(state=NORMAL, text="Analyze URL"))
        self.root.after(0, lambda: self.status_label.configure(text=" Status: Ready "))

    # download
    def start_download_thread(self):
        selected_indices = self.page_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Warning", "Please select at least one page.")
            return

        v_label = self.video_quality_combo.get()
        a_label = self.audio_quality_combo.get()
        out_mode_str = self.output_mode_combo.get()

        v_priority = self.quality_map.get(v_label, 999)
        a_priority = self.audio_quality_map.get(a_label, 999)
        
        # Determine simple mode code
        if "Audio Only" in out_mode_str:
            mode = "audio"
        elif "Video Only" in out_mode_str:
            mode = "video"
        else:
            mode = "merge"

        self.btn_action.config(state=DISABLED, text="Downloading...")
        tasks = [self.video_metadata['pages'][i] for i in selected_indices]

        thread = threading.Thread(target=self.download_logic, args=(tasks, v_priority, a_priority, mode))
        thread.daemon = True
        thread.start()

    # --- Feature 2: Download Logic with Modes ---
    def download_logic(self, tasks, v_priority, a_priority, mode):
        bvid = self.video_metadata['bvid']
        main_title = self.video_metadata['title']
        total = len(tasks)

        self.log(f"Starting batch download. Mode: {mode.upper()}. Tasks: {total}.")

        if not os.path.exists(self.download_dir):
            try:
                os.makedirs(self.download_dir)
            except:
                self.log(f"[ERROR] Cannot create directory: {self.download_dir}")
                return

        VIDEO_ID_MAP = {
            127: "8K 超高清",
            126: "杜比视界 (Dolby Vision)",
            125: "HDR 真彩",
            120: "4K 超高清",
            116: "1080P 60帧",
            112: "1080P+ 高码率",
            80:  "1080P 高清",
            74:  "720P 60帧",
            64:  "720P",
            32:  "480P",
            16:  "360P"
        }
        
        AUDIO_ID_MAP = {
            30251: "Hi-Res 无损音质",
            30250: "杜比全景声 (Dolby Atmos)",
            30280: "192K 高音质",
            30232: "132K 标准",
            30216: "64K 低音质"
        }

        CODEC_MAP = {
            7: "AVC/H.264",
            12: "HEVC/H.265",
            13: "AV1",
            0: "Unknown"
        }
        # ==========================================================

        for idx, page in enumerate(tasks):
            cid = page['cid']
            p_num = page['page']
            p_part = page['part']

            task_name = f"P{p_num}"
            self.log(f"--- Processing ({idx + 1}/{total}): {task_name} ---")
            self.update_progress(0, f"Getting Streams for {task_name}...")

            try:
                dash_data = self.get_play_info(bvid, cid)
                if not dash_data: continue
                
                safe_title = re.sub(r'[\\/*?:"<>|]', "", main_title)[:30]
                safe_part = re.sub(r'[\\/*?:"<>|]', "", p_part)[:30]
                
                base_name = f"{safe_title}" if self.video_metadata['pages_num'] == 1 else f"{safe_title}_P{p_num}_{safe_part}"

                cover_url = self.video_metadata.get('cover', '')
                temp_cover = None 

                if cover_url:
                    temp_cover = os.path.join(self.download_dir, f"temp_cover_{cid}.jpg")
                    # 移动缩进，或者增加判断
                    if not os.path.exists(temp_cover):
                        self.log(f"  [Cover] Downloading temp image...")
                        try:
                            c_res = requests.get(cover_url, headers=self.headers, timeout=10)
                            with open(temp_cover, 'wb') as f:
                                f.write(c_res.content)
                        except Exception as e:
                            self.log(f"  [Cover Error] {e}")
                            temp_cover = None

                final_mp4 = os.path.join(self.download_dir, f"{base_name}.mp4")
                final_m4a = os.path.join(self.download_dir, f"{base_name}.m4a")

                temp_v = os.path.join(self.download_dir, f"temp_v_{cid}.m4s")
                temp_a = os.path.join(self.download_dir, f"temp_a_{cid}.m4s")
                
                video_obj = None
                audio_obj = None

                # according mode
                if mode in ["video", "merge"]:
                    video_obj = self.choose_video_by_priority(dash_data, v_priority)
                
                if mode in ["audio", "merge"]:
                    audio_obj = self.choose_audio_by_priority(dash_data, a_priority)

                # print log
                log_msg = []
                if video_obj:
                    v_id = video_obj['id']
                    v_desc = VIDEO_ID_MAP.get(v_id, f"未知画质({v_id})")
                    v_codec = CODEC_MAP.get(video_obj.get('codecid', 0), "Unknown")
                    v_res = f"{video_obj['width']}x{video_obj['height']}"
                    self.log(f"  [Video] {v_desc} | 编码: {v_codec} | {v_res}")
                
                if audio_obj:
                    a_id = audio_obj['id']
                    a_desc = AUDIO_ID_MAP.get(a_id, f"未知音质({a_id})")
                    a_rate = audio_obj.get('bandwidth', 0) // 1000
                    self.log(f"  [Audio] {a_desc} | 码率: ≈{a_rate}kbps")
                
                # Audio Only
                if mode == "audio":
                    if not audio_obj:
                        self.log(f"[ERROR] Audio stream not found.")
                        continue
                    
                    self.log(f"Downloading Audio Track...")
                    self.download_file(audio_obj['baseUrl'], temp_a, f"{task_name} Audio", 0, 90)
                    
                    self.update_progress(90, f"Processing Audio {task_name}...")
                    if self.process_ffmpeg_single(temp_a, final_m4a, is_audio=True, cover_path=temp_cover):
                        self.log(f"[FINISHED] Saved: {os.path.basename(final_m4a)}")
                        self.update_progress(100, f"Done {task_name}")

                # Video Only
                elif mode == "video":
                    if not video_obj:
                        self.log(f"[ERROR] Video stream not found.")
                        continue

                    self.log(f"Downloading Video Track...")
                    self.download_file(video_obj['baseUrl'], temp_v, f"{task_name} Video", 0, 90)
                    
                    self.update_progress(90, f"Processing Video {task_name}...")
                    if self.process_ffmpeg_single(temp_v, final_mp4, is_audio=False, cover_path=temp_cover):
                        self.log(f"[FINISHED] Saved: {os.path.basename(final_mp4)}")
                        self.update_progress(100, f"Done {task_name}")

                # Merge
                else:
                    if not video_obj or not audio_obj:
                        self.log(f"[ERROR] Missing streams for merge.")
                        continue

                    self.log(f"Downloading Video Track...")
                    self.download_file(video_obj['baseUrl'], temp_v, f"{task_name} Video", 0, 45)

                    self.log(f"Downloading Audio Track...")
                    self.download_file(audio_obj['baseUrl'], temp_a, f"{task_name} Audio", 45, 90)

                    self.update_progress(90, f"Merging {task_name}...")
                    if self.combine_video_audio(temp_v, temp_a, final_mp4, cover_path=temp_cover):
                        self.log(f"[FINISHED] Saved: {os.path.basename(final_mp4)}")
                        self.update_progress(100, f"Done {task_name}")

                if temp_cover and os.path.exists(temp_cover):
                    os.remove(temp_cover)

            except Exception as e:
                self.log(f"[ERROR] {task_name} Failed: {e}")
                if temp_cover and os.path.exists(temp_cover):
                    os.remove(temp_cover)

        self.update_progress(100, "All Tasks Done")
        self.log("[SUCCESS] Batch download finished.")
        self.root.after(0, self.full_reset_ui)

    def full_reset_ui(self):
        self.current_state = "analyze"
        self.btn_action.config(state=NORMAL, text="Analyze URL", bootstyle="success")
        self.status_label.configure(text=" Status: Ready for next task. ")

    # Log
    def log(self, message):
        self.root.after(0, self._update_log_ui, message)

    def _update_log_ui(self, message):
        self.log_box.insert(END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.log_box.see(END)

    def update_progress(self, val, txt):
        self.root.after(0, lambda: [
            self.progress_var.set(val),
            self.status_label.configure(text=f" Status: {txt} "),
            self.progress_bar.configure(text=f"{txt} ({int(val)}%)")
        ])

    # API Interactions
    def get_video_details(self, bvid):
        api_url = "https://api.bilibili.com/x/web-interface/wbi/view"
        try:
            res = requests.get(api_url, params={'bvid': bvid}, headers=self.headers)
            data = res.json()
            if data['code'] == 0:
                return data['data']
            else:
                self.log(f"[API ERROR] {data['message']}")
                return None
        except Exception as e:
            self.log(f"[NETWORK ERROR] {e}")
            return None

    def get_play_info(self, bvid, cid):
        api_url = "https://api.bilibili.com/x/player/wbi/playurl"
        # fnval 4048 = dash
        params = {'bvid': bvid, 'cid': cid, 'fnver': 0, 'fnval': 4048, 'fourk': 1}
        try:
            res = requests.get(api_url, params=params, headers=self.headers)
            data = res.json()
            if data['code'] == 0 and 'dash' in data['data']:
                return data['data']['dash']
            else:
                self.log(f"[API ERROR] No DASH data. (Maybe cookie expired?)")
                return None
        except Exception as e:
            self.log(f"[NETWORK ERROR] {e}")
        return None

    def choose_video_by_priority(self, dash_data, priority):
        videos = dash_data.get('video', [])
        if not videos: return None
        sorted_videos = sorted(videos, key=lambda x: (x['id'], x['bandwidth']), reverse=True)
        if priority == 999: return sorted_videos[0]
        for v in sorted_videos:
            if v['id'] <= priority: return v
        return sorted_videos[0]

    def choose_audio_by_priority(self, dash_data, priority):
        # Dolby/Hi-res checks
        if priority == 999:
            if dash_data.get('flac') and dash_data['flac']['audio']:
                return dash_data['flac']['audio']
            if dash_data.get('dolby') and dash_data['dolby']['audio']:
                return dash_data['dolby']['audio'][0]
        
        audios = dash_data.get('audio', [])
        if not audios: return None
        sorted_audios = sorted(audios, key=lambda x: (x['id'], x['bandwidth']), reverse=True)
        if priority == 999: return sorted_audios[0]
        for a in sorted_audios:
            if a['id'] <= priority: return a
        return sorted_audios[0]

    def download_file(self, url, filename, task_name, start_pct, end_pct):
        max_retries = 3
        attempt = 0
        while attempt < max_retries:
            try:
                downloaded = 0
                if os.path.exists(filename):
                    downloaded = os.path.getsize(filename)
                
                headers = self.headers.copy()
                headers['Range'] = f'bytes={downloaded}-'
                
                res = requests.get(url, headers=headers, stream=True, timeout=20)
                if res.status_code == 416: # Range not satisfiable (already done)
                    return

                total = downloaded + int(res.headers.get('content-length', 0))
                mode = 'ab' if downloaded > 0 else 'wb'

                with open(filename, mode) as f:
                    for chunk in res.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total > 0:
                                file_progress = downloaded / total
                                current_pct = start_pct + (file_progress * (end_pct - start_pct))
                                if downloaded % (1024 * 512) < 8192: # limit update rate
                                    self.update_progress(current_pct, f"DL {task_name}")
                break
            except Exception as e:
                attempt += 1
                self.log(f"[RETRY {attempt}] {task_name}: {e}")
                time.sleep(2)
                if attempt >= max_retries: raise e

    def _get_ffmpeg_path(self):

        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.getcwd()

        target_ffmpeg = os.path.join(base_path, "ffmpeg.exe")
        if os.path.exists(target_ffmpeg):
            return target_ffmpeg
        
        system_ffmpeg = shutil.which("ffmpeg")
        if system_ffmpeg:
            return system_ffmpeg
            
        return None

    # Merge
    def combine_video_audio(self, v_path, a_path, out_path,cover_path=None):
        if os.path.exists(out_path): os.remove(out_path)
        ffmpeg_exe = self._get_ffmpeg_path()
        if not ffmpeg_exe:
            self.log("[ERROR] ffmpeg not found (Check script dir or system PATH).")
            return False
        
        # -c copy is fast and lossless
        cmd = [ffmpeg_exe, '-i', v_path, '-i', a_path]
        
        if cover_path and os.path.exists(cover_path):
            # 输入流 0:视频, 1:音频, 2:封面
            # -map 0, -map 1, -map 2: 选中所有流
            # -c copy: 不转码直接复制
            # -disposition:v:1 attached_pic: 把第二个视频流(封面)标记为附件图片
            cmd.extend(['-i', cover_path, '-map', '0', '-map', '1', '-map', '2', '-c', 'copy', '-disposition:v:1', 'attached_pic'])
        else:
            # 无封面模式
            cmd.extend(['-c', 'copy'])
            
        cmd.extend(['-y', out_path])
        return self._run_ffmpeg(cmd, [v_path, a_path])

    # Convert/Fix Single Stream (for Audio only or Video only)
    def process_ffmpeg_single(self, input_path, out_path, is_audio=False,cover_path=None):
        if os.path.exists(out_path): os.remove(out_path)
        ffmpeg_exe = self._get_ffmpeg_path()

        if not ffmpeg_exe:
            self.log("[ERROR] ffmpeg not found.")
            return False

        cmd = [ffmpeg_exe, '-i', input_path]
        
        if cover_path and os.path.exists(cover_path):
            cmd.extend(['-i', cover_path])
            if is_audio:
                # 音频模式: 输入0是音频，输入1是封面
                # 封面变成了唯一的视频流 (v:0)，标记为 attached_pic
                cmd.extend(['-map', '0', '-map', '1', '-c', 'copy', '-disposition:v:0', 'attached_pic'])
            else:
                # 视频模式: 输入0是视频，输入1是封面
                # 封面是第二个视频流 (v:1)
                cmd.extend(['-map', '0', '-map', '1', '-c', 'copy', '-disposition:v:1', 'attached_pic'])
        else:
            if is_audio:
                cmd.extend(['-vn', '-c:a', 'copy'])
            else:
                cmd.extend(['-an', '-c:v', 'copy'])
        
        cmd.extend(['-y', out_path])
        return self._run_ffmpeg(cmd, [input_path])

    def _run_ffmpeg(self, cmd, temp_files_to_remove):
        try:
            subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=0x08000000 if os.name == 'nt' else 0
            )
            # Cleanup temps
            for f in temp_files_to_remove:
                if os.path.exists(f): os.remove(f)
            return True
        except Exception as e:
            self.log(f"[FFMPEG ERROR] {e}")
            return False


if __name__ == "__main__":
    # Ensure ffmpeg.exe is in the folder or path
    root = ttk.Window(themename="superhero")
    app = BiliDownloaderApp(root)
    root.mainloop()