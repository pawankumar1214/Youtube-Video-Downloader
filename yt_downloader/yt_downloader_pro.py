import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import yt_dlp
import threading
import os
import requests
import time
from PIL import Image
from io import BytesIO

#THEME

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG_COLOR = "#1a1a1a"

queue_links = []
thumbnail_image = None
HISTORY_FILE = "history.txt"


# WINDOW

root = ctk.CTk(fg_color=BG_COLOR)
root.title("YouTube Downloader PRO")
root.geometry("900x700")   
root.update_idletasks()


# FUNCTIONS


def paste_url():
    try:
        url_entry.delete(0,"end")
        url_entry.insert(0, root.clipboard_get())
    except:
        pass

def browse_folder():
    folder = filedialog.askdirectory()
    if folder:
        folder_var.set(folder)

def format_time(seconds):
    if seconds is None:
        return "--"
    m = int(seconds)//60
    s = int(seconds)%60
    return f"{m:02d}:{s:02d}"

def save_history(text):
    with open(HISTORY_FILE,"a") as f:
        f.write(text+"\n")

def update_history():

    history_list.delete(0,"end")

    if os.path.exists(HISTORY_FILE):

        with open(HISTORY_FILE) as f:
            lines = f.readlines()

        for line in lines[-20:]:
            history_list.insert("end", line.strip())


# PREVIEW

def preview_video():

    url = url_entry.get()

    if not url:
        return

    def worker():

        global thumbnail_image

        try:

            with yt_dlp.YoutubeDL({"quiet": True}) as ydl:

                info = ydl.extract_info(
                    url,
                    download=False
                )

            title = info.get("title")
            duration = info.get("duration")
            thumb = info.get("thumbnail")

            
            root.after(
                0,
                lambda: title_label.configure(
                    text=f"Title: {title}"
                )
            )

            root.after(
                0,
                lambda: duration_label.configure(
                    text=f"Duration: {format_time(duration)}"
                )
            )

            if thumb:

                r = requests.get(thumb)

                img = Image.open(
                    BytesIO(r.content)
                )

                img = img.resize((220,130))

                thumbnail_image = ctk.CTkImage(
                    light_image=img,
                    dark_image=img,
                    size=(220,130)
                )

                root.after(
                    0,
                    lambda: thumbnail_label.configure(
                        image=thumbnail_image,
                        text=""
                    )
                )

        except Exception as e:

            root.after(
                0,
                lambda: messagebox.showerror(
                    "Preview Error",
                    str(e)
                )
            )

    threading.Thread(
        target=worker,
        daemon=True  
    ).start()


# QUEUE

def add_to_queue():

    url = url_entry.get()

    if not url:
        return

    queue_links.append(url)

    queue_list.insert(
        "end",
        url
    )

    url_entry.delete(0,"end")

def remove_selected():

    selected = queue_list.curselection()

    if selected:

        idx = selected[0]

        queue_list.delete(idx)

        queue_links.pop(idx)

def clear_queue():

    queue_list.delete(0,"end")

    queue_links.clear()


# DOWNLOAD

def download_one(url, folder):

    dtype = download_type.get()
    quality = quality_var.get()

    def hook(d):

        if d["status"]=="downloading":

            downloaded = d.get(
                "downloaded_bytes",0
            )

            total = d.get(
                "total_bytes"
            )

            if total:

                percent = int(
                    downloaded/total*100
                )

                progress.set(
                    percent/100
                )

            speed = d.get("speed")

            if speed:

                speed_label.configure(
                    text=f"Speed: {speed/1024:.1f} KB/s"
                )

            eta = d.get("eta")

            eta_label.configure(
                text=f"ETA: {format_time(eta)}"
            )

    if dtype=="Video":

        if quality=="Best":

            fmt = "bestvideo+bestaudio/best"

        else:

            q = quality.replace("p","")

            fmt = f"bestvideo[height<={q}]+bestaudio/best"

    else:

        fmt = "bestaudio/best"

    opts = {

        "outtmpl": os.path.join(
            folder,
            "%(title)s.%(ext)s"
        ),

        "progress_hooks":[hook],

        "format": fmt,

        "merge_output_format":"mp4",

        "quiet":True

    }

    with yt_dlp.YoutubeDL(opts) as ydl:

        info = ydl.extract_info(
            url,
            download=True
        )

    return info.get("title")


# START DOWNLOAD

def start_downloads():

    folder = folder_var.get()

    if not folder:

        messagebox.showerror(
            "Error",
            "Select folder first"
        )

        return

    if not queue_links:

        messagebox.showerror(
            "Error",
            "Queue empty"
        )

        return

    def worker():

        for url in queue_links:

            title = download_one(
                url,
                folder
            )

            now = time.strftime(
                "%Y-%m-%d %H:%M"
            )

            save_history(
                f"[{now}] {title}"
            )

        update_history()

        progress.set(0)

        status_label.configure(
            text="Completed ✅"
        )

    threading.Thread(
        target=worker
    ).start()


# UI LAYOUT

main_frame = ctk.CTkFrame(
    root,
    fg_color=BG_COLOR
)

main_frame.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)

# URL

top_frame = ctk.CTkFrame(main_frame)
top_frame.pack(fill="x", pady=5)

url_entry = ctk.CTkEntry(
    top_frame,
    placeholder_text="Video / Playlist URL",
    width=420
)

url_entry.pack(side="left", padx=5)

ctk.CTkButton(
    top_frame,
    text="Paste",
    width=80,
    command=paste_url
).pack(side="left", padx=5)

ctk.CTkButton(
    top_frame,
    text="Preview",
    width=80,
    command=preview_video
).pack(side="left", padx=5)

ctk.CTkButton(
    top_frame,
    text="Add",
    width=80,
    command=add_to_queue
).pack(side="left", padx=5)

# PREVIEW

preview_frame = ctk.CTkFrame(main_frame)
preview_frame.pack(fill="x", pady=8)

thumbnail_label = ctk.CTkLabel(
    preview_frame,
    text="Thumbnail",
    width=220,
    height=130
)

thumbnail_label.pack(side="left", padx=10)

info_frame = ctk.CTkFrame(preview_frame)
info_frame.pack(side="left", padx=10)

title_label = ctk.CTkLabel(
    info_frame,
    text="Title: --"
)

title_label.pack(anchor="w")

duration_label = ctk.CTkLabel(
    info_frame,
    text="Duration: --"
)

duration_label.pack(anchor="w")

status_label = ctk.CTkLabel(
    info_frame,
    text="Ready ✅"
)

status_label.pack(anchor="w")

# FOLDER

folder_frame = ctk.CTkFrame(main_frame)
folder_frame.pack(fill="x", pady=5)

folder_var = tk.StringVar()

ctk.CTkEntry(
    folder_frame,
    textvariable=folder_var,
    width=500
).pack(side="left", padx=5)

ctk.CTkButton(
    folder_frame,
    text="Browse",
    command=browse_folder
).pack(side="left")

# OPTIONS

options_frame = ctk.CTkFrame(main_frame)
options_frame.pack(fill="x", pady=5)

download_type = tk.StringVar(value="Video")

ctk.CTkRadioButton(
    options_frame,
    text="Video",
    variable=download_type,
    value="Video"
).pack(side="left", padx=10)

ctk.CTkRadioButton(
    options_frame,
    text="Audio",
    variable=download_type,
    value="Audio"
).pack(side="left", padx=10)

quality_var = ctk.StringVar(value="Best")

quality_menu = ctk.CTkOptionMenu(
    options_frame,
    values=["Best","360p","720p","1080p"],
    variable=quality_var
)

quality_menu.pack(side="left", padx=20)

# QUEUE

queue_frame = ctk.CTkFrame(main_frame)
queue_frame.pack(fill="both", expand=True, pady=8)

queue_list = tk.Listbox(
    queue_frame,
    height=5
)

queue_list.pack(side="left", fill="both", expand=True)

scrollbar = tk.Scrollbar(
    queue_frame,
    command=queue_list.yview
)

scrollbar.pack(side="right", fill="y")

queue_list.config(
    yscrollcommand=scrollbar.set
)

# QUEUE BUTTONS

button_frame = ctk.CTkFrame(main_frame)
button_frame.pack(pady=5)

ctk.CTkButton(
    button_frame,
    text="Remove",
    width=120,
    command=remove_selected
).pack(side="left", padx=5)

ctk.CTkButton(
    button_frame,
    text="Clear",
    width=120,
    fg_color="red",
    command=clear_queue
).pack(side="left", padx=5)

# PROGRESS

progress = ctk.CTkProgressBar(
    main_frame,
    width=700
)

progress.pack(pady=5)

progress.set(0)

speed_label = ctk.CTkLabel(
    main_frame,
    text="Speed: --"
)

speed_label.pack()

eta_label = ctk.CTkLabel(
    main_frame,
    text="ETA: --"
)

eta_label.pack()

# HISTORY

history_frame = ctk.CTkFrame(main_frame)
history_frame.pack(fill="x", pady=5)

history_list = tk.Listbox(
    history_frame,
    height=4
)

history_list.pack(fill="both")

update_history()

# START BUTTON

ctk.CTkButton(
    main_frame,
    text="Start Downloads",
    width=200,
    command=start_downloads
).pack(pady=10)

root.mainloop()