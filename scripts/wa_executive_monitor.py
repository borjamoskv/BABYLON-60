#!/usr/bin/env python3
import sqlite3
import os
import time
import subprocess
import urllib.request
import json
from datetime import datetime, timezone, timedelta

DB_PATH = os.path.expanduser("~/Library/Group Containers/group.net.whatsapp.WhatsApp.shared/ChatStorage.sqlite")
CHAT_NAME = "BABYLON-60 | Executive Command"

# Modelo o API para inferencia rápida
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")

def get_last_msg_info():
    if not os.path.exists(DB_PATH):
        return None
    try:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        cur = conn.cursor()
        query = """
        SELECT m.Z_PK, m.ZMESSAGEDATE, m.ZTEXT, m.ZFROMJID, m.ZTOJID, m.ZPUSHNAME
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
        print(f"[ERROR DB] {e}")
        return None

print(f"[C5-REAL MONITOR] Test DB read: {get_last_msg_info()}")
