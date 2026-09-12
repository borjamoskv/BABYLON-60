#!/usr/bin/env python3
"""
Native Messaging Host para CORTEX / BABYLON-60
Aislado, 0 anergía, comunicación por Stdin/Stdout binario.
"""

import sys
import struct
import json
import logging
import os
from typing import Any

# Toda traza o log DEBE ir a stderr o archivo, nunca a stdout, ya que arruina el túnel IPC
LOG_FILE = os.path.join(os.path.dirname(__file__), "native_host.log")
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def get_message() -> dict[str, Any] | None:
    raw_length = sys.stdin.buffer.read(4)
    if len(raw_length) == 0:
        return None
    message_length: int = struct.unpack("@I", raw_length)[0]
    message = sys.stdin.buffer.read(message_length).decode("utf-8")
    data = json.loads(message)
    if isinstance(data, dict):
        return data
    return None


def send_message(message_dict: dict[str, Any]) -> None:
    message = json.dumps(message_dict)
    encoded_message = message.encode("utf-8")
    sys.stdout.buffer.write(struct.pack("@I", len(encoded_message)))
    sys.stdout.buffer.write(encoded_message)
    sys.stdout.buffer.flush()


def main() -> None:
    logging.info("=======================================")
    logging.info("BABYLON-60 NATIVE HOST ACTIVE (Ring-0)")
    logging.info("=======================================")

    while True:
        try:
            msg = get_message()
            if msg is None:
                logging.info("EOF: Chrome cerró el túnel IPC.")
                break

            logging.info(f"Mensaje entrante de Extensión: {msg}")

            # PoC Causal Echo
            cmd = msg.get("cmd")
            if cmd == "PING":
                reply = {"status": "POC_SUCCESS", "kernel": "MOSKV-1", "echo": msg.get("payload", "")}
                send_message(reply)
                logging.info(f"Respuesta enviada: {reply}")
            elif cmd == "GENERATE":
                # FSM Integration
                reply = {"status": "QUEUED", "message": "FSM Signal Acknowledged by Python Kernel"}
                send_message(reply)
                logging.info("Comando GENERATE interceptado.")
            else:
                send_message({"status": "UNKNOWN_CMD", "cmd": cmd})

        except Exception as e:
            logging.error(f"Error termodinámico fatal en IPC: {e}")
            break


if __name__ == "__main__":
    main()
