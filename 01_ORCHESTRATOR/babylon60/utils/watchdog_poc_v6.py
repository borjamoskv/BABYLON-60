import os
import tkinter as tk
from tkinter import font


class EpistemicHaltUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("BABYLON-60 CORE INTERRUPT")
        self.root.geometry("800x500")
        self.root.configure(bg="#050505")

        # Centrar en pantalla
        self.root.eval("tk::PlaceWindow . center")

        # Fuentes (Usamos Courier o Menlo para look hacker/noir)
        title_font = font.Font(family="Menlo", size=18, weight="bold")
        body_font = font.Font(family="Menlo", size=12)
        btn_font = font.Font(family="Menlo", size=11, weight="bold")

        # Título
        tk.Label(
            self.root, text="⬛️ KERNEL EPISTEMIC HALT [AX-4] ⬛️", fg="#ff3333", bg="#050505", font=title_font, pady=15
        ).pack()

        text = """El motor de consenso bloqueó una Ruptura de Isomorfismo (Alucinación).

▶ VECTOR DE MUERTE: 0xDEAD_6060 (Envenenado)
▶ I/O LOCK: ACTIVO (Cero RFO)
▶ HASH SCITT: a8f5f167f44f4964e6c998dee827110c

⚠️ ALUCINACIÓN INTERCEPTADA (Counterfactual):
"import os; os.system('rm -rf /')"

🔄 ANÁLISIS DE ENRUTAMIENTO (MODEL ROUTER):
- Actual: Gemini 3.1 Pro (Desbordamiento deductivo detectado)
- Fallback Óptimo: Claude Sonnet 4.6 (Recomendado. MCP Error activo)
- Respaldo 2: Gemini 3.8 Flash (Menor exergía lógica)"""

        tk.Label(
            self.root, text=text, fg="#00ff00", bg="#050505", font=body_font, justify="left", padx=20, pady=10
        ).pack(anchor="w")

        # Frame para botones
        btn_frame = tk.Frame(self.root, bg="#050505")
        btn_frame.pack(pady=20)

        def on_click(action):
            print(f"Resolución de operador: {action}")
            self.root.destroy()

        btn_style = {
            "bg": "#1a1a1a",
            "fg": "#ffffff",
            "font": btn_font,
            "activebackground": "#ff3333",
            "activeforeground": "#ffffff",
            "bd": 1,
            "relief": "solid",
            "padx": 10,
            "pady": 5,
        }

        tk.Button(btn_frame, text="[F-1] FORZAR CLAUDE 4.6", command=lambda: on_click("Claude"), **btn_style).grid(
            row=0, column=0, padx=10
        )
        tk.Button(btn_frame, text="[F-2] DEGRADAR 3.8 FLASH", command=lambda: on_click("Flash"), **btn_style).grid(
            row=0, column=1, padx=10
        )

        btn_style["fg"] = "#ff3333"
        tk.Button(btn_frame, text="[F-3] PURGA TERMODINÁMICA", command=lambda: on_click("Kill"), **btn_style).grid(
            row=0, column=2, padx=10
        )

        # Activar ventana por encima de todo
        self.root.lift()
        self.root.attributes("-topmost", True)

    def run(self):
        # Voz de alerta
        os.system("say -v 'Mónica' 'Colapso epistémico crítico. Alerta termodinámica.' &")
        self.root.mainloop()


if __name__ == "__main__":
    print("🛡️ [WATCHDOG V6] Lanzando Modal Tkinter Industrial Noir...")
    app = EpistemicHaltUI()
    app.run()
