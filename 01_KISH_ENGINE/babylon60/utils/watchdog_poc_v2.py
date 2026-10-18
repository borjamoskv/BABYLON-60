import os


def trigger_aggressive_alert() -> None:
    # 1. Alerta de Voz Inmediata (Asíncrona)
    os.system("say 'Critical failure detected in Babylon 60 core. Epistemic Halt activated.' &")

    # 2. Modal Bloqueante en el centro de la pantalla
    apple_script = """
    tell application "System Events"
        activate
        display alert "🛑 COLAPSO EPISTÉMICO (BABYLON-60)" message "El Kernel ha detectado una alucinación crítica o estado inválido.\n\nESTADO: 0xDEAD_6060 (Envenenado)\nACCIÓN: Interrupción de seguridad (Fail-Stop) ejecutada.\n\nEl recibo criptográfico SCITT ha sido sellado." as critical buttons {"Desconectar Enjambre y Analizar Logs"} cancel button "Desconectar Enjambre y Analizar Logs" default button "Desconectar Enjambre y Analizar Logs"
    end tell
    """

    # Ejecutamos el modal
    os.system(f"osascript -e '{apple_script}'")


print("🛡️ [WATCHDOG V2] Simulando envenenamiento...")
trigger_aggressive_alert()
