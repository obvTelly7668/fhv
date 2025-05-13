import os
import shutil
import sqlite3
from datetime import datetime
from nicegui import ui
from tkinter import Tk, filedialog

# ---------- Datenbank Setup ----------
def init_db():
    conn = sqlite3.connect("filelog.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS file_moves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            source_path TEXT,
            destination_path TEXT,
            date_used TEXT,
            date_type TEXT,
            moved_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def log_to_db(filename, src, dst, date_used, date_type_val):
    conn = sqlite3.connect("filelog.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO file_moves (filename, source_path, destination_path, date_used, date_type, moved_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        filename,
        src,
        dst,
        date_used,
        date_type_val,
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

# ---------- Globale Variablen ----------
source_path = ""
target_path = ""
date_type = "modified"

status_label = ui.label().classes("text-blue-600")

# ---------- Funktionen ----------
def choose_folder(callback):
    root = Tk()
    root.withdraw()
    folder = filedialog.askdirectory()
    root.destroy()
    if folder:
        callback(folder)

def set_source_path(path):
    global source_path
    source_path = path
    source_label.set_text(f"Quellordner: {path}")

def set_target_path(path):
    global target_path
    target_path = path
    target_label.set_text(f"Zielordner: {path}")

def sort_files():
    global source_path, target_path, date_type

    if not source_path or not target_path:
        status_label.set_text("❗ Bitte Quell- und Zielordner wählen.")
        return

    use_ctime = (date_type == "created")

    try:
        for filename in os.listdir(source_path):
            file_path = os.path.join(source_path, filename)
            if os.path.isfile(file_path):
                timestamp = os.path.getctime(file_path) if use_ctime else os.path.getmtime(file_path)
                year = datetime.fromtimestamp(timestamp).year
                target_folder = os.path.join(target_path, str(year))
                os.makedirs(target_folder, exist_ok=True)
                new_path = os.path.join(target_folder, filename)
                shutil.move(file_path, new_path)

                log_to_db(
                    filename=filename,
                    src=file_path,
                    dst=new_path,
                    date_used=datetime.fromtimestamp(timestamp).isoformat(),
                    date_type_val=date_type
                )
        status_label.set_text("✅ Dateien wurden erfolgreich sortiert und gespeichert.")
    except Exception as e:
        status_label.set_text(f"❌ Fehler: {e}")

# ---------- GUI ----------
init_db()

ui.label("📁 Datei-Organizer nach Jahr").classes("text-xl mt-4")

ui.button("Quellordner wählen", on_click=lambda: choose_folder(set_source_path))
source_label = ui.label("Noch kein Quellordner gewählt")

ui.button("Zielordner wählen", on_click=lambda: choose_folder(set_target_path))
target_label = ui.label("Noch kein Zielordner gewählt")

ui.label("Sortieren nach:").classes("mt-4")

ui.radio(
    ["modified", "created"],
    value="modified",
    on_change=lambda e: set_date_type(e.value)
).props("inline")

def set_date_type(value):
    global date_type
    date_type = value

ui.button("🚀 Sortieren starten", on_click=sort_files).classes("mt-4")

ui.separator()
status_label = ui.label()

ui.run(host='0.0.0.0')

