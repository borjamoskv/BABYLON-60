#!/usr/bin/env python3
"""
Transductor Soberano de Correo C5-REAL (babylon60.com)
Ruta: 01_KISH_ENGINE/babylon60/transducers/c5_mail_transducer.py
"""

import os
import json
import subprocess
from typing import List, Optional, Dict, Any


class C5MailTransducer:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or self._get_keychain_secret()
        self.sender = "borja@babylon60.com"
        self.api_url = "https://api.resend.com/emails"

    @staticmethod
    def _get_keychain_secret() -> str:
        try:
            cmd = ["security", "find-generic-password", "-w", "-s", "CORTEX_P2P_SMTP_PASSWORD"]
            out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode().strip()
            if out and out.startswith("re_"):
                return out
        except Exception:
            pass
        token = os.environ.get("P2P_SMTP_PASSWORD", "")
        if token and token.startswith("re_"):
            return token
        return ""

    def dispatch(
        self,
        to: List[str],
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        reply_to: Optional[str] = "borja@babylon60.com",
    ) -> Dict[str, Any]:
        if not self.api_key:
            return {"status": "ERROR", "code": "NO_API_KEY", "detail": "Clave Resend no configurada en Keychain"}

        payload = {
            "from": f"Borja <{self.sender}>",
            "to": to,
            "subject": subject,
            "html": html_body,
            "text": text_body or "",
            "reply_to": reply_to,
        }

        cmd = [
            "curl",
            "-s",
            "-w",
            "\n%{http_code}",
            "-X",
            "POST",
            self.api_url,
            "-H",
            f"Authorization: Bearer {self.api_key}",
            "-H",
            "Content-Type: application/json",
            "-d",
            json.dumps(payload),
        ]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            lines = res.stdout.strip().split("\n")
            http_code = int(lines[-1]) if lines else 0
            body_raw = "\n".join(lines[:-1]) if len(lines) > 1 else ""

            try:
                body_json = json.loads(body_raw)
            except Exception:
                body_json = {"raw": body_raw}

            if 200 <= http_code < 300:
                return {"status": "DELIVERED", "id": body_json.get("id"), "http_code": http_code}
            else:
                return {"status": "FAILED", "http_code": http_code, "detail": body_json}
        except subprocess.CalledProcessError as e:
            return {"status": "ERROR", "detail": str(e.stderr or e)}
        except Exception as e:
            return {"status": "ERROR", "detail": str(e)}


if __name__ == "__main__":
    transducer = C5MailTransducer()
    has_key = bool(transducer.api_key)
    print(
        json.dumps({"transducer_ready": has_key, "sender": transducer.sender, "endpoint": transducer.api_url}, indent=2)
    )
