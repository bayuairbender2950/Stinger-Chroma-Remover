import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import subprocess
import os
import sys
import shutil
import cv2
from PIL import Image, ImageTk
import threading
import queue
import json

class LanguageManager:
    def __init__(self, languages_dir='languages'):
        self.languages_dir = languages_dir
        self.available_languages = {}
        self.current_lang_data = {}
        self.scan_for_languages()
        if not self.available_languages:
            raise FileNotFoundError(f"No language files found in '{languages_dir}' directory.")
        self.load_language(list(self.available_languages.keys())[0])

    def scan_for_languages(self):
        if not os.path.exists(self.languages_dir): os.makedirs(self.languages_dir)
        for filename in os.listdir(self.languages_dir):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(self.languages_dir, filename), 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.available_languages[data.get("language_name", filename)] = filename
                except Exception as e: print(f"Warning: Could not parse {filename}. Error: {e}")

    def load_language(self, language_name):
        filename = self.available_languages.get(language_name)
        try:
            with open(os.path.join(self.languages_dir, filename), 'r', encoding='utf-8') as f:
                self.current_lang_data = json.load(f)
        except Exception: return False
        return True

    def get_string(self, key, sub_key=None, default=""):
        if sub_key: return self.current_lang_data.get(key, {}).get(sub_key, default)
        return self.current_lang_data.get(key, default)

class StingerChromaRemover(ctk.CTk):
    def __init__(self, lang_manager):
        super().__init__()
        self.lang_manager = lang_manager
        
        self.source_video_path = ""
        self.chroma_key_color = ""
        self.preview_image_original = None
        self.preview_image_tk = None
        self.ffmpeg_executable_path = self._find_ffmpeg_executable()
        self.conversion_queue = queue.Queue()
        self.is_converting = False
        self.ffmpeg_process = None
        self.interactive_widgets = []

        self._setup_window()
        self._create_widgets()
        self._collect_interactive_widgets()
        self.update_ui_text()

    def _setup_window(self):
        self.title("Stinger Chroma Remover")
        self.geometry("1200x740")
        self.resizable(False, False)
        self.grid_columnconfigure(0, weight=1, minsize=600)
        self.grid_columnconfigure(1, weight=1, minsize=400)
        self.grid_rowconfigure(1, weight=1)

    def _create_widgets(self):
        self._create_header_frame()
        self._create_preview_frame()
        self._create_settings_tabs()
        self._create_status_bar()
        self.update_ffmpeg_status_text()

    def update_ui_text(self):
        self.title(self.lang_manager.get_string("app_title"))
        self.step1_label.configure(text=self.lang_manager.get_string("step1_label"))
        self.select_video_button.configure(text=self.lang_manager.get_string("select_video_button"))
        
        if not self.is_converting:
            self.convert_button.configure(text=self.lang_manager.get_string("step3_button"))
            
        if not self.source_video_path: self.file_label.configure(text=self.lang_manager.get_string("no_file_selected"))
        
        if not self.is_converting and not self.source_video_path:
             self.status_label.configure(text=self.lang_manager.get_string("welcome_message"))

        self.update_ffmpeg_status_text()
        
        self.q_header.configure(text=self.lang_manager.get_string("quality_tab", "header"))
        self.q_instruction.configure(text=self.lang_manager.get_string("quality_tab", "instruction"))
        self.tolerance_label.configure(text=self.lang_manager.get_string("quality_tab", "tolerance_label"))
        self.blend_label.configure(text=self.lang_manager.get_string("quality_tab", "blend_label"))
        self.denoise_label.configure(text=self.lang_manager.get_string("quality_tab", "denoise_label"))
        self.despill_label.configure(text=self.lang_manager.get_string("quality_tab", "despill_label"))
        self.despill_checkbox.configure(text=self.lang_manager.get_string("quality_tab", "despill_checkbox"))
        
        self.hw_accel_label.configure(text=self.lang_manager.get_string("advanced_tab", "hw_accel_label"))
        self.resolution_label.configure(text=self.lang_manager.get_string("advanced_tab", "resolution_label"))
        self.crf_label_widget.configure(text=self.lang_manager.get_string("advanced_tab", "crf_label"))
        self.speed_label_widget.configure(text=self.lang_manager.get_string("advanced_tab", "speed_label"))
        self.fps_label_widget.configure(text=self.lang_manager.get_string("advanced_tab", "fps_label"))
        self.keep_fps_checkbox.configure(text=self.lang_manager.get_string("advanced_tab", "keep_fps_checkbox"))
        self.audio_bitrate_label.configure(text=self.lang_manager.get_string("advanced_tab", "audio_bitrate_label"))
        self.no_audio_checkbox.configure(text=self.lang_manager.get_string("advanced_tab", "no_audio_checkbox"))
    
    def _create_header_frame(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, columnspan=2, padx=20, pady=(10, 0), sticky="ew")
        
        self.step1_label = ctk.CTkLabel(header_frame, font=ctk.CTkFont(size=16, weight="bold"))
        self.select_video_button = ctk.CTkButton(header_frame, command=self.select_video_file)
        self.file_label = ctk.CTkLabel(header_frame, text_color="gray")
        self.ffmpeg_status_label = ctk.CTkLabel(header_frame, font=ctk.CTkFont(weight="bold"))
        
        lang_options = list(self.lang_manager.available_languages.keys())
        self.language_menu = ctk.CTkOptionMenu(header_frame, values=lang_options, command=self.switch_language)
        
        self.convert_button = ctk.CTkButton(header_frame, command=self.start_conversion_process, state=tk.DISABLED, font=ctk.CTkFont(weight="bold"))
        self.default_button_color = self.convert_button.cget("fg_color")
        self.default_button_hover_color = self.convert_button.cget("hover_color")

        self.step1_label.pack(side="left", padx=(10,0)); self.select_video_button.pack(side="left", padx=10); self.file_label.pack(side="left", padx=10, fill="x")
        self.convert_button.pack(side="right", padx=10); self.language_menu.pack(side="right", padx=10); self.ffmpeg_status_label.pack(side="right", padx=10)

    def _create_preview_frame(self):
        self.preview_frame = ctk.CTkFrame(self)
        self.preview_frame.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")
        self.preview_frame.grid_rowconfigure(0, weight=1); self.preview_frame.grid_columnconfigure(0, weight=1)
        self.preview_canvas = tk.Canvas(self.preview_frame, cursor="crosshair", background="#242424", highlightthickness=0)
        self.preview_canvas.grid(row=0, column=0, sticky="nsew"); self.preview_canvas.bind("<Button-1>", self.on_preview_clicked)

    def _create_settings_tabs(self):
        self.tab_view = ctk.CTkTabview(self, width=400); self.tab_view.grid(row=1, column=1, padx=(0, 20), pady=20, sticky="nsew")
        
        quality_title = self.lang_manager.get_string("quality_tab", "title")
        advanced_title = self.lang_manager.get_string("advanced_tab", "title")
        log_title = self.lang_manager.get_string("log_tab", "title")
        
        self.tab_view.add(quality_title); self.tab_view.add(advanced_title); self.tab_view.add(log_title)
        
        self._populate_quality_tab(self.tab_view.tab(quality_title))
        self._populate_advanced_tab(self.tab_view.tab(advanced_title))
        self._populate_log_tab(self.tab_view.tab(log_title))

    def _create_status_bar(self):
        status_frame = ctk.CTkFrame(self, fg_color="transparent"); status_frame.grid(row=2, column=0, columnspan=2, padx=20, pady=(0, 10), sticky="ew")
        self.status_label = ctk.CTkLabel(status_frame); self.status_label.pack(side="left")
        self.progress_bar = ctk.CTkProgressBar(status_frame, width=300, mode='indeterminate')

    def _populate_quality_tab(self, tab):
        self.q_header = ctk.CTkLabel(tab, font=ctk.CTkFont(size=14, weight="bold")); self.q_header.pack(anchor="w", padx=10, pady=10)
        self.q_instruction = ctk.CTkLabel(tab); self.q_instruction.pack(anchor="w", padx=10)
        self.color_swatch = ctk.CTkLabel(tab, text="", fg_color=self.chroma_key_color or "white", width=30, height=30, corner_radius=6); self.color_swatch.pack(anchor="w", padx=10, pady=10)
        
        self.tolerance_label, self.tolerance_help_button = self._create_control_with_help(tab, lambda: self._show_help_message("tolerance"))
        self.tolerance_input = ctk.CTkEntry(tab); self.tolerance_input.insert(0, "0.15"); self.tolerance_input.pack(fill="x", padx=10, pady=(0,5))
        
        self.blend_label = ctk.CTkLabel(tab, font=ctk.CTkFont(weight="bold")); self.blend_label.pack(anchor="w", padx=10, pady=(10,0))
        self.blend_entry = ctk.CTkEntry(tab); self.blend_entry.insert(0, "0.1"); self.blend_entry.pack(fill="x", padx=10)
        
        self.denoise_label, self.denoise_help_button = self._create_control_with_help(tab, lambda: self._show_help_message("denoise"))
        self._create_denoise_slider(tab)
        
        self.despill_label, self.despill_help_button = self._create_control_with_help(tab, lambda: self._show_help_message("despill"))
        self._create_despill_toggle(tab)

    def _populate_advanced_tab(self, tab):
        self.hw_accel_label, self.hw_accel_help_button = self._create_control_with_help(tab, lambda: self._show_help_message("hw_accel"))
        self._create_gpu_select(tab)
        
        self.resolution_label = ctk.CTkLabel(tab, font=ctk.CTkFont(weight="bold")); self.resolution_label.pack(anchor="w", padx=10, pady=(10,0))
        self.resolution_entry = ctk.CTkEntry(tab); self.resolution_entry.pack(fill="x", padx=10)
        
        self.crf_label_widget, self.crf_help_button = self._create_control_with_help(tab, lambda: self._show_help_message("crf"))
        self._create_crf_slider(tab)
        
        self.speed_label_widget, self.speed_help_button = self._create_control_with_help(tab, lambda: self._show_help_message("speed"))
        self._create_speed_slider(tab)
        
        self.fps_label_widget, self.fps_help_button = self._create_control_with_help(tab, lambda: self._show_help_message("fps"))
        self._create_fps_slider(tab)
        
        self.audio_bitrate_label = ctk.CTkLabel(tab, font=ctk.CTkFont(weight="bold")); self.audio_bitrate_label.pack(anchor="w", padx=10, pady=(10,0))
        self.audio_bitrate_entry = ctk.CTkEntry(tab); self.audio_bitrate_entry.insert(0, "128k"); self.audio_bitrate_entry.pack(fill="x", padx=10)
        self.no_audio_checkbox = ctk.CTkCheckBox(tab, command=self.on_audio_toggle); self.no_audio_checkbox.pack(anchor="w", padx=10, pady=20)

    def _populate_log_tab(self, tab):
        self.log_textbox = ctk.CTkTextbox(tab, activate_scrollbars=True); self.log_textbox.pack(fill="both", expand=True, padx=5, pady=5); self.log_textbox.configure(state="disabled")

    def _create_control_with_help(self, parent, help_command):
        frame = ctk.CTkFrame(parent, fg_color="transparent"); frame.pack(fill="x", padx=10, pady=(10, 0))
        label = ctk.CTkLabel(frame, font=ctk.CTkFont(weight="bold")); label.pack(side="left")
        help_button = ctk.CTkButton(frame, text="?", width=25, height=25, command=help_command); help_button.pack(side="right")
        return label, help_button

    def _create_denoise_slider(self, parent):
        f = ctk.CTkFrame(parent, fg_color="transparent"); f.pack(fill="x", padx=10, pady=5); f.grid_columnconfigure(0, weight=1)
        self.denoise_slider = ctk.CTkSlider(f, from_=0, to=5, number_of_steps=20, command=self.on_denoise_slider_update); self.denoise_slider.set(0)
        self.denoise_slider.grid(row=0, column=0, sticky="ew")
        self.denoise_value_label = ctk.CTkLabel(f, text="0.0", width=30); self.denoise_value_label.grid(row=0, column=1, padx=(10,0))

    def _create_despill_toggle(self, parent):
        self.despill_checkbox = ctk.CTkCheckBox(parent); self.despill_checkbox.pack(anchor="w", padx=10, pady=5)
    
    def _create_gpu_select(self, parent):
        self.gpu_select = ctk.CTkOptionMenu(parent, values=["None (CPU Only)", "NVIDIA (CUDA)", "Intel (QSV)", "AMD (d3d11va)"]); self.gpu_select.pack(fill="x", padx=10, pady=5)

    def _create_crf_slider(self, parent):
        f = ctk.CTkFrame(parent, fg_color="transparent"); f.pack(fill="x", padx=10, pady=5); f.grid_columnconfigure(0, weight=1)
        self.crf_slider = ctk.CTkSlider(f, from_=0, to=63, number_of_steps=63, command=self.on_crf_slider_update); self.crf_slider.set(20)
        self.crf_slider.grid(row=0, column=0, sticky="ew")
        self.crf_value_label = ctk.CTkLabel(f, text="20", width=30); self.crf_value_label.grid(row=0, column=1, padx=(10,0))
    
    def _create_speed_slider(self, parent):
        f = ctk.CTkFrame(parent, fg_color="transparent"); f.pack(fill="x", padx=10, pady=5); f.grid_columnconfigure(0, weight=1)
        self.speed_slider = ctk.CTkSlider(f, from_=0, to=5, number_of_steps=5, command=self.on_speed_slider_update); self.speed_slider.set(2)
        self.speed_slider.grid(row=0, column=0, sticky="ew")
        self.speed_value_label = ctk.CTkLabel(f, text="2", width=30); self.speed_value_label.grid(row=0, column=1, padx=(10,0))

    def _create_fps_slider(self, parent):
        f = ctk.CTkFrame(parent, fg_color="transparent"); f.pack(fill="x", padx=10, pady=5); f.grid_columnconfigure(1, weight=1)
        self.keep_fps_checkbox = ctk.CTkCheckBox(f, command=self.on_fps_toggle); self.keep_fps_checkbox.select()
        self.keep_fps_checkbox.grid(row=0, column=0)
        self.fps_slider = ctk.CTkSlider(f, from_=15, to=60, number_of_steps=45, command=self.on_fps_slider_update, state="disabled"); self.fps_slider.set(30)
        self.fps_slider.grid(row=0, column=1, sticky="ew", padx=10)
        self.fps_value_label = ctk.CTkLabel(f, text="30", width=30); self.fps_value_label.grid(row=0, column=2)

    def _collect_interactive_widgets(self):
        self.interactive_widgets = [
            self.select_video_button, self.language_menu,
            self.tolerance_input, self.blend_entry, self.denoise_slider, self.despill_checkbox,
            self.gpu_select, self.resolution_entry, self.crf_slider, self.speed_slider,
            self.keep_fps_checkbox, self.fps_slider, self.audio_bitrate_entry, self.no_audio_checkbox,
            self.tolerance_help_button, self.denoise_help_button, self.despill_help_button,
            self.hw_accel_help_button, self.crf_help_button, self.speed_help_button, self.fps_help_button
        ]

    def on_crf_slider_update(self, val): self.crf_value_label.configure(text=f"{int(val)}")
    def on_denoise_slider_update(self, val): self.denoise_value_label.configure(text=f"{val:.1f}")
    def on_speed_slider_update(self, val): self.speed_value_label.configure(text=f"{int(val)}")
    def on_fps_slider_update(self, val): self.fps_value_label.configure(text=f"{int(val)}")

    def _find_ffmpeg_executable(self):
        name = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"; local_path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), name)
        if os.path.exists(local_path): return local_path
        return shutil.which(name)

    def update_ffmpeg_status_text(self):
        if self.ffmpeg_executable_path:
            self.ffmpeg_status_label.configure(text=self.lang_manager.get_string("ffmpeg_found"), text_color="lightgreen")
        else:
            self.ffmpeg_status_label.configure(text=self.lang_manager.get_string("ffmpeg_not_found"), text_color="red")
            
    def switch_language(self, language_name):
        if self.lang_manager.load_language(language_name):
            self.tab_view.destroy()
            self._create_settings_tabs()
            self._collect_interactive_widgets()
            self.update_ui_text()

    def update_log_from_queue(self):
        try:
            while True:
                line = self.conversion_queue.get_nowait()
                self.log_textbox.configure(state="normal"); self.log_textbox.insert("end", line); self.log_textbox.see("end"); self.log_textbox.configure(state="disabled")
        except queue.Empty: pass
        self.after(100, self.update_log_from_queue)

    def on_audio_toggle(self): self.audio_bitrate_entry.configure(state="disabled" if self.no_audio_checkbox.get() else "normal")
    def on_fps_toggle(self): self.fps_slider.configure(state="disabled" if self.keep_fps_checkbox.get() else "normal")

    def select_video_file(self):
        if self.is_converting: return
        self.source_video_path = filedialog.askopenfilename(filetypes=(("MP4 files", "*.mp4"), ("All files", "*.*")))
        if not self.source_video_path: return
        self.file_label.configure(text=os.path.basename(self.source_video_path), text_color="white")
        self.status_label.configure(text=self.lang_manager.get_string("video_loaded_message"))
        self.after(50, self.load_and_display_preview)

    def load_and_display_preview(self):
        try:
            cap = cv2.VideoCapture(self.source_video_path); ret, frame = cap.read(); cap.release()
            if not ret: raise ValueError("Could not read frame.")
            self.preview_image_original = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, _ = self.preview_image_original.shape
            self.resolution_entry.delete(0, 'end'); self.resolution_entry.insert(0, f"{w}x{h}")
            canvas_w, canvas_h = self.preview_canvas.winfo_width(), self.preview_canvas.winfo_height()
            if canvas_w < 20: canvas_w, canvas_h = 600, 600
            img_ratio = w / h; canvas_ratio = canvas_w / canvas_h
            new_w = canvas_w if img_ratio > canvas_ratio else int(canvas_h * img_ratio)
            new_h = int(new_w / img_ratio) if img_ratio > canvas_ratio else canvas_h
            display_frame = cv2.resize(self.preview_image_original, (new_w, new_h), interpolation=cv2.INTER_AREA)
            self.preview_image_tk = ImageTk.PhotoImage(image=Image.fromarray(display_frame))
            self.preview_canvas.create_image(canvas_w/2, canvas_h/2, anchor="center", image=self.preview_image_tk)
        except Exception as e: messagebox.showerror("Frame Error", f"Failed to load video frame. Error: {e}")

    def on_preview_clicked(self, event):
        if self.preview_image_original is None or self.is_converting: return
        canvas_w, canvas_h = self.preview_canvas.winfo_width(), self.preview_canvas.winfo_height()
        img_w, img_h = self.preview_image_tk.width(), self.preview_image_tk.height()
        offset_x, offset_y = (canvas_w - img_w) / 2, (canvas_h - img_h) / 2
        if not (offset_x <= event.x < offset_x + img_w and offset_y <= event.y < offset_y + img_h): return
        img_x, img_y = event.x - offset_x, event.y - offset_y
        orig_h, orig_w, _ = self.preview_image_original.shape
        orig_x, orig_y = int((img_x / img_w) * orig_w), int((img_y / img_h) * orig_h)
        r, g, b = self.preview_image_original[orig_y, orig_x]
        self.chroma_key_color = f"#{r:02x}{g:02x}{b:02x}"
        self.color_swatch.configure(fg_color=self.chroma_key_color)
        status_text = self.lang_manager.get_string("color_selected_message").format(color=self.chroma_key_color.upper())
        self.status_label.configure(text=status_text, text_color="white")
        self.convert_button.configure(state=tk.NORMAL)
    
    def _set_ui_conversion_state(self, is_converting):
        self.is_converting = is_converting
        state = "disabled" if is_converting else "normal"

        for widget in self.interactive_widgets:
            widget.configure(state=state)
        
        if not is_converting:
            self.on_fps_toggle()
            self.on_audio_toggle()

        if is_converting:
            cancel_text = self.lang_manager.get_string("cancel_button", default="Cancel")
            self.convert_button.configure(text=cancel_text, command=self.cancel_conversion, fg_color=("#F44336", "#D32F2F"), hover_color=("#E57373", "#B71C1C"))
            self.progress_bar.pack(side="right", padx=10); self.progress_bar.start()
        else:
            self.convert_button.configure(text=self.lang_manager.get_string("step3_button"), command=self.start_conversion_process, fg_color=self.default_button_color, hover_color=self.default_button_hover_color)
            self.progress_bar.stop(); self.progress_bar.pack_forget()

    def start_conversion_process(self):
        if self.is_converting: return
        if not self.ffmpeg_executable_path:
            self._show_help_message("ffmpeg_not_found"); return
        output_path = filedialog.asksaveasfilename(defaultextension=".webm", filetypes=[("WEBM Video", "*.webm")])
        if not output_path: return
        
        try:
            params = {"similarity": float(self.tolerance_input.get()),"blend": float(self.blend_entry.get()),"crf": int(self.crf_slider.get()),"denoise": self.denoise_slider.get()}
        except ValueError:
            messagebox.showerror("Invalid Input", "Tolerance and Blend must be valid numbers."); return
        
        self._set_ui_conversion_state(is_converting=True)
        self.status_label.configure(text="Converting, please wait...", text_color="yellow")
        self.log_textbox.configure(state="normal"); self.log_textbox.delete("1.0", "end"); self.log_textbox.configure(state="disabled")
        
        command = self._build_ffmpeg_command(output_path, params)
        threading.Thread(target=self.execute_ffmpeg_in_thread, args=(command, output_path), daemon=True).start()
        self.update_log_from_queue()

    def cancel_conversion(self):
        if self.ffmpeg_process and self.is_converting:
            try:
                self.ffmpeg_process.terminate()
                self.status_label.configure(text="Conversion cancelled.", text_color="orange")
            except Exception as e:
                print(f"Error terminating process: {e}")
            self.is_converting = False

    def _build_ffmpeg_command(self, output_path, params):
        pre_input_args = []; gpu_selection = self.gpu_select.get()
        if "NVIDIA" in gpu_selection: pre_input_args.extend(['-hwaccel', 'cuda'])
        elif "Intel" in gpu_selection: pre_input_args.extend(['-hwaccel', 'qsv', '-hwaccel_output_format', 'qsv'])
        elif "AMD" in gpu_selection: pre_input_args.extend(['-hwaccel', 'd3d11va'])
        command = [self.ffmpeg_executable_path] + pre_input_args + ['-i', self.source_video_path]
        vf_filters = []
        if params["denoise"] > 0: vf_filters.append(f"nlmeans=strength={params['denoise']}")
        vf_filters.append(f"chromakey=color={self.chroma_key_color}:similarity={params['similarity']}:blend={params['blend']}")
        if self.despill_checkbox.get(): vf_filters.append("despill")
        if self.resolution_entry.get(): vf_filters.append(f"scale={self.resolution_entry.get()}")
        command.extend(['-vf', ",".join(vf_filters)])
        encoder_opts = ['-c:v', 'libvpx-vp9', '-crf', str(params['crf']), '-b:v', '0', '-pix_fmt', 'yuva420p']
        encoder_opts.extend(['-speed', f"{int(self.speed_slider.get())}"])
        command.extend(encoder_opts)
        if not self.keep_fps_checkbox.get(): command.extend(['-r', f"{int(self.fps_slider.get())}"])
        if self.no_audio_checkbox.get(): command.append('-an')
        elif self.audio_bitrate_entry.get(): command.extend(['-c:a', 'libvorbis', '-b:a', self.audio_bitrate_entry.get()])
        command.extend(['-y', output_path])
        return command

    def execute_ffmpeg_in_thread(self, command, output_path):
        try:
            self.ffmpeg_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, universal_newlines=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            for line in iter(self.ffmpeg_process.stdout.readline, ''):
                self.conversion_queue.put(line)
            self.ffmpeg_process.stdout.close()
            return_code = self.ffmpeg_process.wait()

            if self.is_converting:
                if return_code == 0:
                    self.after(0, self.on_conversion_success, output_path)
                else:
                    raise subprocess.CalledProcessError(return_code, command)
        except Exception as e:
            self.after(0, self.on_conversion_error, e)
    
    def on_conversion_success(self, output_path):
        self._set_ui_conversion_state(is_converting=False)
        self.status_label.configure(text=f"Success! Saved as {os.path.basename(output_path)}", text_color="lightgreen")
        messagebox.showinfo("Success!", f"Video converted successfully!\n\nSaved to: {output_path}")

    def on_conversion_error(self, error):
        was_cancelled = not self.is_converting
        self._set_ui_conversion_state(is_converting=False)
        if not was_cancelled:
            self.status_label.configure(text="Conversion failed. See log.", text_color="red")
            messagebox.showerror("FFmpeg Error", f"An error occurred during conversion. See the Log tab for details.\n\nError: {error}")

    def _show_help_message(self, key):
        title = self.lang_manager.get_string("help", f"{key}_title")
        message = self.lang_manager.get_string("help", f"{key}_msg")
        messagebox.showinfo(title, message)
        
if __name__ == "__main__":
    try:
        lang_manager = LanguageManager()
        app = StingerChromaRemover(lang_manager)
        app.mainloop()
    except Exception as e:
        root = tk.Tk(); root.withdraw()
        messagebox.showerror("Application Start Error", f"A critical error occurred:\n\n{e}\n\nPlease ensure the 'languages' folder and valid .json files exist.")