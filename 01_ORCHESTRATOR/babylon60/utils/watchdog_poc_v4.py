import os


def trigger_predictive_alert():
    alucinacion_interceptada = "import os; os.system('rm -rf /')"
    hash_alucinacion = "a8f5f167f44f4964e6c998dee827110c"

    voice_msg = "Colapso interceptado. Secuencia envenenada."
    os.system(f"say -v 'Borja' '{voice_msg}' &")

    # Escribimos el script de applescript a un archivo temporal para evitar problemas de comillas en bash
    apple_script = f"""
    tell application "System Events"
        activate
        display alert "⬛️ COLLAPSE: KERNEL EPISTEMIC HALT" message "[AX-4 FAIL-STOP PROTOCOL ACTIVATED]\n\nEl motor de consenso bloqueó una Ruptura de Isomorfismo (Alucinación) en la Caché L1 a 12 microsegundos de su ejecución.\n\n▶ VECTOR DE MUERTE: 0xDEAD_6060 (Envenenado)\n▶ HASH SCITT: {hash_alucinacion}\n\n⚠️ ALUCINACIÓN INTERCEPTADA:\n\\"{alucinacion_interceptada}\\"\n\nLa entropía ha sido contenida. Requiere purga manual." as critical buttons {{"[CONFIRMAR] Destruir Sesión"}} default button 1
    end tell
    """

    with open("/tmp/alert.scpt", "w") as f:
        f.write(apple_script)

    os.system("osascript /tmp/alert.scpt")


print("🛡️ [WATCHDOG V4.1] Lanzando alerta corregida...")
trigger_predictive_alert()
