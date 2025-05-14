import os
import shutil
import zipfile
from datetime import datetime
from nicegui import ui
from pathlib import Path

UPLOAD_DIR = Path("uploads")
SORTED_DIR = Path("sorted")
ZIP_PATH = Path("output.zip")

# Sicherstellen, dass Ordner vorhanden sind
UPLOAD_DIR.mkdir(exist_ok=True)
SORTED_DIR.mkdir(exist_ok=True)

# Benutzerstatus pro Session
@ui.page('/')
def main_page():
    user_data = {
        'date_type': 'modified',
        'files': []
    }

    status_label = ui.label()

    ui.label("📁 Datei-Organizer Web").classes("text-2xl font-bold my-4")

    ui.label("📤 Dateien hochladen").classes("mt-4")
    uploader = ui.upload(multiple=True, auto_upload=True, on_upload=lambda e: handle_upload(e, user_data))
    ui.label("Dateien werden temporär auf dem Server gespeichert.")

    ui.label("📅 Sortieren nach:")
    ui.radio(
        ["modified", "created"],
        value="modified",
        on_change=lambda e: user_data.update({'date_type': e.value})
    ).props("inline")

    ui.button("🚀 Sortieren und ZIP erstellen", on_click=lambda: sort_and_zip(user_data, status_label)).classes("mt-4")

    ui.separator()

    status_label = ui.label()

    with ui.row().classes("mt-4"):
        ui.button("📥 ZIP herunterladen", on_click=download_zip)

# Dateiupload verarbeiten
def handle_upload(e, user_data):
    file_path = UPLOAD_DIR / e.name
    with open(file_path, "wb") as f:
        f.write(e.content.read())
    user_data['files'].append(file_path)

# Dateien sortieren und ZIP erstellen
def sort_and_zip(user_data, status_label):
    # Leeren des Zielordners
    if SORTED_DIR.exists():
        shutil.rmtree(SORTED_DIR)
    SORTED_DIR.mkdir(exist_ok=True)

    try:
        for file_path in user_data['files']:
            if not file_path.exists():
                continue
            timestamp = os.path.getctime(file_path) if user_data['date_type'] == 'created' else os.path.getmtime(file_path)
            year = datetime.fromtimestamp(timestamp).year
            target_folder = SORTED_DIR / str(year)
            target_folder.mkdir(parents=True, exist_ok=True)
            shutil.copy(file_path, target_folder / file_path.name)

        # ZIP-Datei erstellen
        with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zipf:
            for foldername, _, filenames in os.walk(SORTED_DIR):
                for filename in filenames:
                    file_path = os.path.join(foldername, filename)
                    arcname = os.path.relpath(file_path, SORTED_DIR)
                    zipf.write(file_path, arcname)

        status_label.text = "✅ Sortierung abgeschlossen. ZIP bereit zum Download."
    except Exception as e:
        status_label.text = f"❌ Fehler beim Sortieren: {e}"

# Download-Funktion
def download_zip():
    if ZIP_PATH.exists():
        ui.download(ZIP_PATH)
    else:
        ui.notify("❌ Keine ZIP-Datei gefunden. Bitte zuerst sortieren.", color='negative')

# App starten
ui.run(host='0.0.0.0', port=8080)
