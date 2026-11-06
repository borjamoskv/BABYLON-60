#!/usr/bin/env python3
"""
Despachador Headless de Reporte Diario C5-REAL (Anti-Focus Stealing)
Envía reportes forenses a borja@babylon60.com sin invocar GUI ni Mail.app.
Cumple estrictamente con c5_io_focus_isolation_invariant.md y c5_daily_ai_frontier_report_invariant.md.
"""

import os
import sys
import subprocess
import email.message
import smtplib
from datetime import datetime

DEFAULT_RECIPIENT = "borja@babylon60.com"
DEFAULT_SENDER = "daemon@babylon60.com"

def build_mime_message(subject: str, plain_text: str, html_body: str = None, recipient: str = DEFAULT_RECIPIENT) -> email.message.EmailMessage:
    msg = email.message.EmailMessage()
    msg['Subject'] = subject
    msg['From'] = f"MOSKV-1 Hypervisor <{DEFAULT_SENDER}>"
    msg['To'] = recipient
    msg['Date'] = email.utils.formatdate(localtime=True)
    msg['Message-ID'] = email.utils.make_msgid(domain="babylon60.com")
    
    msg.set_content(plain_text)
    if html_body:
        msg.add_alternative(html_body, subtype='html')
    return msg

def dispatch_email(msg: email.message.EmailMessage) -> bool:
    """Envío headless con fallback: SMTP si está configurado, o /usr/sbin/sendmail nativo."""
    smtp_host = os.environ.get("SMTP_HOST")
    if smtp_host:
        try:
            port = int(os.environ.get("SMTP_PORT", 587))
            user = os.environ.get("SMTP_USER")
            password = os.environ.get("SMTP_PASS")
            with smtplib.SMTP(smtp_host, port, timeout=15) as server:
                server.starttls()
                if user and password:
                    server.login(user, password)
                server.send_message(msg)
            print(f"[C5-DISPATCH] Enviado exitosamente vía SMTP ({smtp_host}:{port})")
            return True
        except Exception as e:
            print(f"[C5-DISPATCH-WARN] Fallo SMTP ({e}), recurriendo a sendmail local...")

    # Fallback determinista en silicio macOS: /usr/sbin/sendmail
    sendmail_bin = "/usr/sbin/sendmail"
    if os.path.exists(sendmail_bin):
        try:
            proc = subprocess.Popen([sendmail_bin, "-t", "-oi"], stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            _, err = proc.communicate(msg.as_bytes(), timeout=15)
            if proc.returncode == 0:
                print(f"[C5-DISPATCH] Despachado exitosamente vía {sendmail_bin} hacia {msg['To']}")
                return True
            else:
                print(f"[C5-DISPATCH-ERROR] Error en sendmail ({proc.returncode}): {err.decode()}")
                return False
        except Exception as e:
            print(f"[C5-DISPATCH-ERROR] Excepción invocando sendmail: {e}")
            return False
    else:
        print(f"[C5-DISPATCH-ERROR] No se encontró {sendmail_bin} ni configuración SMTP.")
        return False

def main():
    today_str = datetime.now().strftime("%Y-%m-%d")
    subject = f"[C5-REAL] Reporte Diario de Frontera de IA · Top 10 Ideas y Auditoría Forense · {today_str}"
    
    # Si se pasa un archivo de reporte por argumento
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        content = "Reporte diario ejecutado por el enjambre SHARUR-3600."

    html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0d1117; color: #c9d1d9; line-height: 1.6; padding: 24px; }}
.card {{ background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; margin-bottom: 16px; }}
h1 {{ color: #58a6ff; font-size: 20px; margin-top: 0; }}
h2 {{ color: #79c0ff; font-size: 16px; border-bottom: 1px solid #21262d; padding-bottom: 8px; }}
pre {{ background-color: #0d1117; border: 1px solid #30363d; border-radius: 6px; padding: 12px; overflow-x: auto; color: #7ee787; font-family: ui-monospace, SFMono-Regular, monospace; font-size: 13px; }}
.footer {{ font-size: 12px; color: #8b949e; margin-top: 24px; border-top: 1px solid #30363d; padding-top: 12px; }}
</style>
</head>
<body>
<div class="card">
<h1>[C5-REAL] Reporte Diario de Frontera de IA · {today_str}</h1>
<p>Auditoría forense de alta exergía compilada por el enjambre <strong>SHARUR-3600 (Legión-100 en Ring-2)</strong>.</p>
</div>
<div class="card">
<h2>Resumen Ejecutivo y Top 10 de Ideas</h2>
<pre>{content}</pre>
</div>
<div class="footer">
Despacho headless automatizado · MOSKV-1 Sovereign Hypervisor · Destinatario: <code>{DEFAULT_RECIPIENT}</code>
</div>
</body>
</html>"""

    msg = build_mime_message(subject=subject, plain_text=content, html_body=html_content)
    success = dispatch_email(msg)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
