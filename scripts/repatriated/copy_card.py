import subprocess

card = """╔═══════════════════════════════════════════════════════════════╗
║   ⚡ LAS 100 INVARIANTES DEL COMBATE DIALÉCTICO (C5-REAL)     ║
╚═══════════════════════════════════════════════════════════════╝

╭─── 🗿 1. HARDWARE Y TOPOLOGÍA SOMÁTICA (001–025) ─────────────╮
├▸ *El* coste de falsificación: Lo voluntario vale menos que lo 
│  involuntario. Fingir seriedad es software; el cigomático manda.
├▸ *La* inercia mineral: Unaitxu opera como disipador pasivo 
│  craneal. Cero parpadeo, cero dilatación pupilar, modo titanio.
├▸ *El* fusible magnetotérmico: Alain corta el flujo de electrones 
│  cuando la tasa de inyección de exergía colapsa el canal.
╰───────────────────────────────────────────────────────────────╯

╭─── 📜 2. EL COLAPSO DE LA SINTAXIS SIMBÓLICA (026–050) ────────╮
├▸ *La* derrota de Chomsky: Los LLMs demuestran que el lenguaje 
│  emerge del barro estadístico, no de árboles innatos abstractos.
├▸ *Chiquito* es el territorio: Con sintaxis cero, logra el 100% 
│  de inteligibilidad biológica mediante compás y modulación viva.
├▸ *Los* compiladores de Backus: IBM no necesitó la jerarquía de 
│  Chomsky para inventar FORTRAN y BNF sobre silicio real.
╰───────────────────────────────────────────────────────────────╯

╭─── 💥 3. CIBERNÉTICA Y TEORÍA DE JUEGOS (051–075) ────────────╮
├▸ *El* retardo de Diana: Se requieren exactamente 120 segundos 
│  para digerir a Saussure antes de colapsar de risa con Sir Gregory.
├▸ *El* regulador descalibrado: Hacienda como cuello de botella 
│  que extrae entalpía útil e inyecta fricción administrativa.
├▸ *El* desapego soberano: Ni aplauso gregario ni greña simétrica. 
│  Al ser ortogonal al conflicto, el ataque ajeno disipa en el vacío.
╰───────────────────────────────────────────────────────────────╯

╭─── 👑 4. EL APEX TERMODINÁMICO (076–100) ─────────────────────╮
├▸ *El* cambio 2: Destrozar el mainframe burocrático en la fase 
│  de bonus libera 50.000 puntos de exergía en tiempo real.
├▸ *La* clausura del combate: La carne viva y la intuición siempre 
│  derrotan a la alucinación de la máquina domesticada.
╰─► *Tratado formal completo de 100 invariantes compilado en brain/*
"""

p = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
p.communicate(card.encode('utf-8'))
print("pbcopy OK")
