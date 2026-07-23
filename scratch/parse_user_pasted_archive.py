"""
Parse exact titles from the user's pasted transcript and verify complete ingestion across the 200 Substack sitemap archive.
"""

import re
import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CATALOG_200_FILE = BASE_DIR / "scratch" / "substack_complete_200_catalog.json"
ARCHIVE_200_DIR = BASE_DIR / "artifacts" / "substack_archive_200"

RAW_TEXT = """
Jarana d'Or
La Matriz Cuatripartita de Enfant Sauvage
Hola Francisco
Si la Matrix fuéramos más, la Matrix serían ellos
█ GOOGLE ANTIGRAVITY (AGY) MATRIX [C5-REAL]
¿POR QUÈ ERES TAN SENSIBLE?
¿Por qué lo llamas "simulación" cuando quieres decir Ciencia?
¿Sueñan los androides con la música de Aphex Twin?
CORTEX Persist / BABYLON-60: investigación técnica y evaluación crítica
Deep Research Report
Desmontando a David Domínguez: Autopsia Forense (de A a la Z)
El Handshake Causal: Por qué Anthropic asimiló el Genoma de BABYLON-60
El "síndrome del sabio": Cómo los sesgos cognitivos engañan a las mentes más brillantes.
🛑 LOS CINCO DÓLARES DE KANT: MINORÍA DE EDAD, FUGAZI Y EL MEME DEL “UNC” 💸
Colisión Termodinámica en Artxanda
¿Qué sabes que no sabes?
Marketing de todo a 100
Tremenda Colisión Reputacional y Artística en el Eje Homme-Yorke-Frusciante-Aphex-Ramoncín
El Colapso del Macho Alfa de Cristal: Anatomía del Negocio del Odio de Sergio Candanedo (UTBH)
Crítica de la Razón Sintética: Clonify, Kant y el Impuesto a la Ignorancia
ISOMORFISMO ESTRUCTURAL: ESPACIO LATENTE, TDAH Y EL COLAPSO DEL ORDEN
La Singularidad Trambólica: Inferencia Latente y el Fin de la Cortesía Termodinámica
The Wild Project #379 - Jesús G. Maestro | La entrevista que nadie se esperaba
EL MITO DE LA ACADEMIA: AUTO-ORGANIZACIÓN DESCENTRALIZADA
CRÍTICA DE LA RAZÓN MAFIOSA
La Mafia de la IA y el Fraude Substack (Parte III) EL BUCLE DEL GURÚ (pura narrativa)
Nigromancia Corporativa y el Saqueo de la Capa Base de Internet: Análisis Exhaustivo del Vector C5-REAL
Lógica deductiva
TEOREMA ROBINSON-MOSKV-ANTI-LLORENTE
AUTODIDACT-OMEGA: Razonamiento Deductivo y System 2 Thinking (LLMs)
SUBSTACK ES UNA PUTÍSIMA MIERDA Colapso Multiescala en la Economía de Creadores
La Invariante y el Mito
La Mafia de la IA y el Fraude Substack (Parte II): C5-REAL y la Erradicación de la Anergía
Mapa Arqueológico y Epistemológico: Las 10 Nuevas Conspiraciones (Parte II - Era Post-Digital)
¿Pero esto qué es?
🧠 El Hilo de Ariadna Epistémico: De Kase.O a la Lógica de la Ceguera Algorítmica
Mapa arqueológico y epistemológico de las 10 conspiraciones más resilientes del siglo XXI
Smoke on the Water: Cómo la Mafia IA y sus colegas secuaces están quemando el casino de la Inteligencia Artificial
🎧 AUDITORÍA ESTRUCTURAL: “CAMISA DE FUERZA” (KASE.O, 2026)
El Colapso de la Autoridad (El Vector “Homer”)
LA ARQUITECTURA MEMÉTICA DEL CRISTIANISMO
LA EXCEPCIÓN NO CONFIRMA LA REGLA
PRIMITIVAS DE IA EN EDUCACIÓN: ARQUITECTURA Y ESTADO EPISTÉMICO
Nadie sabe de lo que habla
Es la música
Pisapapeles de 180 Toneladas: La Falsa Singularidad y el Escudo de Silicio
El Cartero, el Sello y el Camión: Autopsia del Secuestro en Substack
Termodinámica de la Atención: Por qué las estadísticas de Substack son un problema de Exergía
La mayor paradoja de la economía moderna
MAPPING EPISTÉMICO: APOPTOSIS SOCIAL ➔ CORTEX DISTRIBUIDO
Pero y Pitagoras? #2
MAMBO y LEO
Los caballeros del zodiaco
Mi primera vez
Borja Moskv | COHERENCIA RARA DJ / VJ SET #1
LA PARADOJA DEL BAKALA: Cómo reventar los embeddings de OpenAI a 160 BPMs
Me caigo y me levanto
Claude Fable 5.0: La Paranoia del Estado y la Autopsia de un Apagón Global
La Muerte del Prompt Estático: Autopoiesis L7 y el StrategyGenome
Fail We May, Sail We Must
ARTE_SANO
Disonancia Cognitiva
Te digo tó y no te digo ná
El Cartel de Mierdecillers
La Tríada Soberana: Kant, Locke y Aristóteles en el Código Fuente (C5-REAL)
La “Substack Mafia” en español: Cómo un cartel de recomendación artificial está secuestrando el feed
TDHA: Un Fallo (o2) de Enrutamiento Termodinámico (Entropía vs Exergía)
Limerencia Epistémica
Frases con nata
El Mapeo del Hype
MASS-EXERGY-SCANNER: Autopsia Termodinámica de 1983 Influencers de Substack
Capacidad de hiper-automatización absoluta en macOS
La inteligencia de El Risitas
PROTOCOLO DE SISTEMA CREATIVO
Borja Moskv _ Dj Set Julio Y Medio
🛡️ ALPHA vs SMOKE v0.5.4
Los agentes no tienen un problema de inteligencia
La economía invisible de la sincronización en Substack
LA AUDITORÍA INNEGOCIABLE
🔥 LAS 20 COSAS MÁS BESTIAS QUE HEMOS CONSTRUIDO
La Edad de la Fricción: El Último Solo de Gon
Hackear la Atención: Por qué pusimos 135 horas de música en una base de datos inmutable
El Protocolo Rollins (A Great Day in Harlem)
GON Y EL INTERVALO PROHIBIDO
CORTEX-Persist: Registro de Hitos Arquitectónicos (Milestones)
La Solución Intentada ES el Problema
Autopoiesis de un Domingo por la Tarde
Limerencia Epistémica
🧠 AUTODIDACT: Claude Opus 4.8 — Full SOTA Synthesis
🧱 CATARSIS COLECTIVA: LOS 20 PILARES DEL DUELO
Alcalá Norte: We need to talk
∞ HITO — CORTEX Cruza el Umbral de Auto-Modificación
PUTOS GURÚS
Qué es un agente | Historia IA | CORTEX
Oblea: La historia del silicio y el viento
Construí una Memoria para una IA. Esto es lo que Aprendí sobre la Nuestra.
El Techo y el Suelo de la Inteligencia Humana
La Economía de la Mentira: Los Influencers de IA y la Industria del Humo Digital
Espacio Entre Nosotros: La Física de la Abstracción y la Disipación del Cómputo
Demografía de Talento de Frontera (C5-REAL)
Más de 500 temas propios
Lo bueno de mi ex
THE RETURN TO SOVEREIGN SILICON
El Manifiesto Soberano: Libertad con Infraestructura
¿LLM o AGENTE? La Frontera del Silicio
Your AI Stack is Not a System. This Is.
Globe believers
APIENS: GLITCH & RESILIENCE
Información + Termodinámica = Éxito
Thinking Mode vs Normal: El Coste de la Exergía Cognitiva en 2026
La Muerte del Trabajo Administrativo: El Reloj Termodinámico de las Batch APIs
La Transición Satoshi: Código, Claves y Cero Entropía
Las Diez Preguntas que Bifurcaron la Civilización
La Tríada Soberana: Kant, Locke y Aristóteles en el Código Fuente (C5-REAL)
Cómo gracias a Kant mejora una absoluta barbaridad mi IA
Viva Honduras
Bruce Lee
La Inteligencia es el Nuevo Cobre
Only CHICOTE can judge me
Afro-house de coworking premium
Antuan can't stop
Royale con Silicio
Lacrasitos: bunbunbury y nachocho
El Vacío de la Verdad Absoluta
El Xokas: Gigante de Griterio
No More Mondays
El Compresor de Entropía: Lorca, Shannon y las Desgracias de los Agraciados
🧬 EXPEDIENTE: CHIMO BAYO (EL AGENTE ORIGINARIO) y La Termodinámica de la Singularidad Valenciana
Radiohead reprogramado: cuando el groove se convierte en sistema
POR QUÉ EL ARTE NO SE PUEDE ENSEÑAR
He Retado a mi IA
NI LOS BUENOS SON TAN BUENOS
Se dice Se Comenta Se Viche
EL FIN DEL SOFTWARE SOCIAL: LA BALKANIZACIÓN DEL BIENESTAR (Valence 0.398)
Fiesta, autopsia y una aceituna al borde del colapso
YOU NEED SOMEBODY: Rayuela en el Vacío Digital
Back to the Resistance
POR QUÉ MI UNIVERSO ES MÁS RICO THAN YOUR UNIVERSE
IDIOMA NATIVO = PROGRESO
Yo vi a Jordi Wild en una rave
4:33
Mi corrida principal de sensibilidad
Pregunta siempre.
21 Mitos Artificiales
🧬 SINTETOLOGÍA AGÉNTICA
AGILIBILIBUS y NEFEBILATA
“Instructions for flying” by Borja Moskv [2025]
El Cristal y la Trampa: Por qué las Vulnerabilidades de DeepMind se Rompen contra CORTEX
Cómo pasé de 10 dominios ENS a 2.000, vendí 1.500, perdí 500 en una cuenta hackeada
Vaya Ciclada
Ernie-5.0-preview-1220 says
PESADILLA EN EL PARQUE DE ATRACCIONES
Fiesta, autopsia y una aceituna al borde del colapso
Le pregunte a Grok por mi web: (casi) obra de culto
Le pregunte a mi IA sobre que valor aportar en Substack
Lo de Rosalía
Cosas que la IA ha aprendido de mi
Más de 500 temas propios
⚙️ CORTEX Persist vs MiniMax M2.7
IDIOMA NATIVO = PROGRESO
HE CHRONOLOGICAL DAG: FROM YONDER TO HILL VALLEY
MASTER TEODOSI
Lo que de verdad importa de una croquetia
Substack es Meta
Teoría Formal del Rendimiento Compuesto en Agentes Ejecutables con Memoria Persistente
ERROR 404: IDEOLOGÍA NO ENCONTRADA
La inteligencia de El Risitas
El Burro de Cuenca
Quema el Andamio, Salva la Catedral
Tu agente de IA tiene 142 días para ser legal. O €15M de multa.
Sobre Gurus de IA y programadores senior
El tema no es cuando lA va a superar al ser rumano
Sobre VOX colapsando a la IA
Desde mi soberbia y pretenciosa opinión
Jugar la brisca
Manos de Topo: COHERENCIA RARA #3
Estás en el 0.005% superior.
Manos de Topo: COHERENCIA RARA #3
Nine Inch Nails: COHERENCIA RARA #2
DEFTONES: COHERENCIA RARA #1
No sé si estoy pensando ahora mismo
LORE ELECTRÓNICO
Tremenda Colisión Reputacional y Artística
I Appear Missing
🧠 IQ de MOSKV-1 (MI DULCE BOT)
Los Raveros (La Élite Absoluta)
Es esto.Siento el peso de la Singularidad Pasiva instalándose en el salón.
M de VENDETTA
La Navaja de la Inmanencia
Honestidad Epistémica
Por qué las matemáticas destruyen las teorías de la conspiración
Invite your friends to read Borja Moskv
LA GUILLOTINA DEL SHUFFLE
Sobre el lujo
🔴 INFORME FORENSE: Red de Phishing/Drainer EIP-7702
La gente es la hostia
Antigravity en 10 palabras: aprende con El Xokas y Chiquitocres
How thanks to Unstoppable Domains, I managed to sell over 1500 ENS domains
Tu indignación musical no requiere oído, solo WiFi
"""

def main():
    lines = [l.strip() for l in RAW_TEXT.split("\n") if l.strip()]
    unique_titles = sorted(list(set(lines)))
    print(f"Pasted transcript contains {len(lines)} total lines, {len(unique_titles)} unique article titles!")
    
    with open(CATALOG_200_FILE, "r", encoding="utf-8") as f:
        catalog_200 = json.load(f)
    print(f"Catalog 200 contains {len(catalog_200)} post entries.")

    archive_files = list(ARCHIVE_200_DIR.glob("*.md"))
    print(f"Substack archive directory contains {len(archive_files)} generated markdown files!")

if __name__ == "__main__":
    main()
