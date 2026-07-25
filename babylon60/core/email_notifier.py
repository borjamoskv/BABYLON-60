import logging
"""
BABYLON-60 INSTANT PURCHASE EMAIL & CONSOLE NOTIFIER (C5-REAL)
============================================================
Dispatches instant purchase notifications to Borjamoskv@gmail.com and records alerts.
"""
import json
import os
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any
TARGET_NOTIFY_EMAIL = 'Borjamoskv@gmail.com'
NOTIFICATIONS_LOG = Path.home() / '.babylon60' / 'purchase_notifications.json'

class PurchaseNotifier:
    """Instant Purchase Alert Dispatcher for Operator Borja Moskv."""

    def __init__(self, log_path: Path | None=None, target_email: str=TARGET_NOTIFY_EMAIL) -> None:
        self.log_path = log_path or NOTIFICATIONS_LOG
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.target_email = target_email

    def notify_purchase(self, customer_email: str, tier: str, amount_eur: int, license_key: str, session_id: str) -> dict[str, Any]:
        """Dispatch instant purchase notification to Borjamoskv@gmail.com and log alert."""
        now_str = time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
        alert_data = {'timestamp': now_str, 'event': 'PURCHASE_COMPLETED', 'target_email': self.target_email, 'customer_email': customer_email, 'tier': tier, 'amount_eur': amount_eur, 'session_id': session_id, 'license_key': license_key}
        self._append_to_log(alert_data)
        logging.info(f'\n🚨 [NUEVA COMPRA DETECTADA] ¡Ingreso de €{amount_eur}! Cliente: {customer_email} ({tier})')
        logging.info(f'   Aviso enviado a: {self.target_email}')
        logging.info(f'   Clave Emitida: {license_key}\n')
        smtp_user = os.environ.get('SMTP_USER')
        smtp_pass = os.environ.get('SMTP_PASS')
        if smtp_user and smtp_pass:
            self._send_smtp_email(alert_data, smtp_user, smtp_pass)
        return alert_data

    def _append_to_log(self, alert_data: dict[str, Any]) -> None:
        logs = []
        if self.log_path.exists():
            try:
                with open(self.log_path, encoding='utf-8') as f:
                    logs = json.load(f)
            except (json.JSONDecodeError, OSError):
                logs = []
        logs.append(alert_data)
        try:
            with open(self.log_path, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2)
        except OSError:
            pass

    def _send_smtp_email(self, data: dict[str, Any], smtp_user: str, smtp_pass: str) -> bool:
        try:
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = self.target_email
            msg['Subject'] = f"⚡ ¡Nueva Compra BABYLON-60! €{data['amount_eur']} - {data['tier']}"
            body = f"Hola Borja,\n\nSe ha completado una nueva compra en BABYLON-60:\n\n• Cliente: {data['customer_email']}\n• Plan: {data['tier']}\n• Importe: €{data['amount_eur']} EUR\n• ID de Sesión: {data['session_id']}\n• Clave Emitida: {data['license_key']}\n• Fecha: {data['timestamp']}\n\nCORTEX Monetization Engine (C5-REAL)"
            msg.attach(MIMEText(body, 'plain'))
            with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=5.0) as server:
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            return True
        except (smtplib.SMTPException, OSError):
            return False