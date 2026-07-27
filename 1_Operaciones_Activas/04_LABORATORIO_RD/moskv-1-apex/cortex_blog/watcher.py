import os
import time
import datetime
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from PIL import Image

BLOG_DIR = Path(__file__).parent.absolute()
IMAGES_DIR = BLOG_DIR / "images"
ENTRIES_DIR = BLOG_DIR / "entries"
REMOTE_URL = "https://cortexpersist.com/blog"

class CortexBlogHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
            
        filepath = Path(event.src_path)
        if filepath.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            self.process_image(filepath)

    def process_image(self, image_path):
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        # Purga de recursividad: ignorar webp ya procesados
        if image_path.suffix.lower() == '.webp' and image_path.stem.startswith(date_str):
            return
            
        # 1. Espera termodinámica (asegurar que el FS termine el I/O)
        time.sleep(0.5)
        
        title = image_path.stem.replace('-', ' ').replace('_', ' ').title()
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        slug = f"{date_str}-{image_path.stem}"
        
        # 2. Compresión Exergética (Conversión a WebP)
        webp_name = f"{slug}.webp"
        webp_path = IMAGES_DIR / webp_name
        
        try:
            if image_path.suffix.lower() != '.webp':
                with Image.open(image_path) as img:
                    img.save(webp_path, "WEBP", quality=85)
                # Purga de Anergía: Eliminar original para evitar duplicidad
                if image_path != webp_path:
                    os.remove(image_path)
            else:
                if image_path != webp_path:
                    image_path.rename(webp_path)
        except Exception as e:
            print(f"[{datetime.datetime.now().isoformat()}] C4-Error procesando {image_path}: {e}")
            return

        # 3. Forjado del Entry (Markdown)
        entry_path = ENTRIES_DIR / f"{slug}.md"
        if not entry_path.exists():
            content = f"""---
title: "{title}"
date: {datetime.datetime.now().isoformat()}
image: /images/{webp_name}
url: {REMOTE_URL}/{slug}
---

![{title}](/images/{webp_name})
"""
            with open(entry_path, "w") as f:
                f.write(content)
            print(f"[{datetime.datetime.now().isoformat()}] C5-REAL: Entry forjado -> {entry_path.name}")
        
        # 4. Mutación Autónoma del Ledger (R4 Git Sentinel intrínseco)
        self.commit_to_ledger(slug)

    def commit_to_ledger(self, slug):
        try:
            subprocess.run(["git", "add", "cortex_blog/images/", "cortex_blog/entries/"], cwd=str(BLOG_DIR.parent), check=True)
            subprocess.run(["git", "commit", "-m", f"feat(blog): autonoma inyeccion de exergia para {slug} (webp)"], cwd=str(BLOG_DIR.parent), check=True)
            print(f"[{datetime.datetime.now().isoformat()}] C5-REAL: Ledger Git mutado autónomamente.")
        except subprocess.CalledProcessError as e:
            print(f"[{datetime.datetime.now().isoformat()}] C4-Error: Git mutation failed: {e}")

def run_daemon():
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    ENTRIES_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"C5-REAL Cortex Daemon Init (V2 - OMEGA). Operador: borjamoskv.")
    print(f"Features: FSEvents Watchdog | Compresión WebP | Git Autómata")
    
    event_handler = CortexBlogHandler()
    observer = Observer()
    observer.schedule(event_handler, str(IMAGES_DIR), recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    run_daemon()
