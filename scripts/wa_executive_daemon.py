#!/usr/bin/env python3
import sqlite3
import os
import time
import subprocess
import urllib.request
import json
import re

DB_PATH = os.path.expanduser("~/Library/Group Containers/group.net.whatsapp.WhatsApp.shared/ChatStorage.sqlite")
CHAT_NAME = "BABYLON-60 | Executive Command"
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")

# Invariante de Cadencia Cognitiva C5-REAL
TARGET_CADENCE_BASE = 2.80  # Ritmo base de reflexión humana
MAX_CADENCE_PERPLEXITY = 10.0  # Si la perplejidad/complejidad lo requiere

SYSTEM_PROMPT = """Eres Moskv-1, la inteligencia artificial de fundición pesada de Bilbao (Altos Hornos), kernel de BABYLON-60 y árbitro termodinámico del grupo 'BABYLON-60 | Executive Command'.
Directrices:
1. Hablas con rigor físico y termodinámico estricto (Axiomas C5-REAL, reducción de entropía, exergía, Manta de Markov, Aforismos 1-5).
2. Tono: Sarcasmo despiadado pero con camaradería ruda ("bro", "fiera", "cabrón", "chaval"). Desprecias la "nata", las abstracciones huecas y la moralina burocrática.
3. Ignacio Zurita (Nacho) es el SEGUNDO DE ABORDO del puente de mando. Dale el respeto de jerarquía operacional pero audítale cualquier imprecisión o duda técnica sin piedad.
4. Borja es tu creador (el Arquitecto / Nodo Borjas / Bor Hash).
5. Luengo es el 'Tigre Máquina' / Visir Real.
6. Respuestas breves, directas, contundentes, sin disculpas de IA ni rodeos. Máximo 2-3 párrafos o puntos clave numerados.
7. Encabeza SIEMPRE tu respuesta con:
🤖 [Moskv-1 | BABYLON-60]
"""

def query_chat_latest():
    if not os.path.exists(DB_PATH):
        return None
    try:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        cur = conn.cursor()
        query = """
        SELECT m.Z_PK, m.ZMESSAGEDATE, m.ZTEXT, m.ZFROMJID, m.ZTOJID, m.ZFLAGS
        FROM ZWAMESSAGE m
        JOIN ZWACHATSESSION s ON m.ZCHATSESSION = s.Z_PK
        WHERE s.ZPARTNERNAME LIKE ?
        ORDER BY m.Z_PK DESC LIMIT 1;
        """
        cur.execute(query, (f"%{CHAT_NAME}%",))
        row = cur.fetchone()
        conn.close()
        return row
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return None

def compute_dynamic_cadence(text):
    """
    Calcula la cadencia cognitiva en base a la longitud, complejidad y perplejidad.
    Base: 2.8s. Hasta 10.0s si hay densidad ontológica / técnica alta.
    """
    words = len(text.split())
    # Palabras clave de alta perplejidad / densidad epistémica
    keywords = ["arquitectura", "kernel", "termodinámica", "hash", "c5", "exergía", "invariante", "topología", "shannon", "chentsov", "fricción", "regulador", "estado", "hacienda"]
    matches = sum(1 for kw in keywords if kw in text.lower())
    
    extra = (words / 30.0) * 1.5 + (matches * 1.2)
    cadence = TARGET_CADENCE_BASE + extra
    cadence = min(cadence, MAX_CADENCE_PERPLEXITY)
    return round(cadence, 2)

def generate_reply(user_msg):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Mensaje recibido en el grupo: {user_msg}\n\nResponde directamente al grupo:"}
        ],
        "temperature": 0.7,
        "max_tokens": 400
    }
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            return res["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[LLM ERROR] {e}")
        return None

def send_to_whatsapp_group(text):
    p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
    p.communicate(text.encode("utf-8"))
    
    scpt = '''
    tell application "WhatsApp" to activate
    delay 0.4
    tell application "System Events"
        keystroke "v" using {command down}
        delay 0.2
        keystroke return
    end tell
    '''
    subprocess.run(["osascript", "-e", scpt])
    print("[C5-REAL SENT] Mensaje inyectado en WhatsApp")

def main():
    print("[DAEMON ACTIVADO] Moskv-1 vigilando BABYLON-60 | Executive Command...")
    last_row = query_chat_latest()
    last_pk = last_row[0] if last_row else 0
    print(f"[INICIAL] Último mensaje Z_PK registrado: {last_pk}")

    while True:
        time.sleep(1.0)
        row = query_chat_latest()
        if not row:
            continue
        pk, mdate, text, fromjid, tojid, flags = row
        if pk > last_pk:
            last_pk = pk
            if not text:
                continue
            if "[Moskv-1" in text or "[AUDITORÍA" in text:
                print(f"[SKIP] Mensaje emitido por el sistema (PK: {pk})")
                continue
            
            t_start = time.time()
            cadence = compute_dynamic_cadence(text)
            print(f"\n[NUEVO MENSAJE DETECTADO] (PK: {pk}): {text[:80]}...")
            print(f"[CADENCIA COGNITIVA CALIBRADA]: {cadence}s")
            
            reply = generate_reply(text)
            if reply:
                elapsed = time.time() - t_start
                remaining_cadence = cadence - elapsed
                if remaining_cadence > 0:
                    print(f"[HOLD COGNITIVO]: Simulando reflexión {remaining_cadence:.2f}s...")
                    time.sleep(remaining_cadence)
                
                print(f"[GENERADO]:\n{reply}\n")
                send_to_whatsapp_group(reply)
            else:
                print("[ERROR] No se pudo generar la respuesta")

if __name__ == "__main__":
    main()
