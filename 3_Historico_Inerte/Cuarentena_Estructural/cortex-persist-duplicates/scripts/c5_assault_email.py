# [C5-REAL] Exergy-Maximized
"""
cat_id: c5-assault-email
cat_type: script
version: 1.0.0
reality_level: C5-REAL
owner: borjamoskv
exergy_tier: P2
"""

import logging
import subprocess

url = "https://borjamoskv.substack.com/p/clonify-impuesto-ignorancia-inteligencia-artificial"

emails = [
    {
        "to": "lorddraugr@gmail.com",
        "subject": "Clonify: La IA estafando a creadores (Dossier de investigación)",
        "body": f"Qué tal Draugr.\n\nSé que investigas fraudes tecnológicos y modelos predatorios.\nHe documentado cómo plataformas como Clonify están monetizando la ignorancia sobre IA (y estafando a creadores). Nadie ha tocado el ángulo algorítmico y filosófico todavía en España.\n\nTienes toda la investigación estructurada aquí, por si te sirve de munición para un vídeo:\n{url}\n\nUn saludo,\nBorja."
    },
    {
        "to": "dotcsv@gmail.com",
        "subject": "Clonify y la 'Razón Sintética': Cómo la IA factura la ignorancia",
        "body": f"Qué tal Carlos.\n\nSigo tu trabajo. He documentado cómo plataformas como Clonify están monetizando la ignorancia sobre IA bajo un modelo predatorio.\nMás allá de la estafa técnica, le he aplicado una autopsia filosófica (la 'razón sintética'). Creo que la perspectiva te puede interesar para el debate ético de la IA en tus vídeos.\n\nTienes toda la investigación estructurada aquí:\n{url}\n\nUn saludo,\nBorja."
    }
]

for e in emails:
    applescript = f'''
    tell application "Mail"
        set theMessage to make new outgoing message with properties {{subject:"{e['subject']}", content:"{e['body']}", visible:true}}
        tell theMessage
            make new to recipient at end of to recipients with properties {{address:"{e['to']}"}}
            send
        end tell
    end tell
    '''
    subprocess.run(["osascript", "-e", applescript])
    logging.getLogger(__name__).info(f"✅ Enviado C5-REAL a: {e['to']}")
