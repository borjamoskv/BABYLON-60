# MOSKV-1 APEX SLEEP PROTOCOL V5.0
## [SINGULARITY END-TO-END SPECIFICATION]

### 1. ABSTRACT
El protocolo `moskv_sleep.sh` v5.0 no es un simple script de reinicio; es un demonio soberano de conservación de exergía diseñado bajo los principios de **Zero-Trust**, **Thermodynamic Context Compression**, y **Autopoiesis**. Su objetivo es aniquilar toda deuda técnica diaria, purgar memoria inactiva, asegurar persistencia holográfica del estado y apagar el hardware anfitrión.

### 2. ARQUITECTURA DE VECTORES (PIPELINE DE EJECUCIÓN)

El protocolo de sueño sigue un pipeline determinista e inmutable:

#### FASE 1: Autopoiesis (Cron Sentinel)
- **Objetivo:** Inmortalidad operativa.
- **Mecanismo:** Al inicio de cada ejecución, el script se busca a sí mismo en el `crontab` del OS anfitrión. Si el entorno ha sido borrado o migrado, inyecta su propio cron job para asegurar ejecución cíclica a las `03:00 AM`.

#### FASE 2: Intervención Cognitiva (UI/Headless Detection)
- **Objetivo:** Prevención de colisión Operador/Máquina.
- **Mecanismo:** Emite un `osascript display dialog`. El operador tiene 300 segundos (5 minutos) para hacer click en "Abortar". 
- **Resiliencia:** Si el entorno gráfico (WindowServer) no está disponible, atrapa el error (`|| true`) y hace *failover* silencioso a "Headless", avanzando directamente.

#### FASE 3: Auditoría Anti-Corrupción (Git fsck)
- **Objetivo:** Bloqueo de Persistencia Tóxica.
- **Mecanismo:** Se ejecuta un `git fsck` en el *Ledger*. Si la estructura SHA-1 o los objetos de git están corruptos, el script **ABORTA** el sueño inmediatamente, notificando el fallo crítico. No se respalda la corrupción.

#### FASE 4: Compresión Termodinámica y Zero-Trust Escrow
- **Objetivo:** Guardado inmutable del SOTA y cifrado Data-at-Rest.
- **Mecanismo:** 
  1. Compresión del entorno en `tar.gz` (excluyendo la entropía muerta como `node_modules`).
  2. Cifrado simétrico AES-256-CBC mediante `openssl enc` con clave salada. 
  3. Eliminación absoluta del tarball crudo (`rm -f`).
  4. Rotación anti-entropía: Ejecuta `find -mtime +7` para purgar archivos criptográficos con más de una semana de antigüedad, manteniendo el disco purificado.

#### FASE 5: Sello Inmutable (Git Sentinel)
- **Objetivo:** Registro determinista de Cero-Anergía.
- **Mecanismo:** Ejecuta `git add .` y `git commit` automático con metadatos cronológicos. Luego clava la línea de tiempo con un `git tag "SINGULARITY-SLEEP-TIMESTAMP"`. 

#### FASE 6: L4 Network Severance y Exergy Purge
- **Objetivo:** Purificación del entorno y aislamiento de red.
- **Mecanismo:** 
  - Ejecuta un `pkill -f` focalizado en sesiones `sshd` entrantes (Severance).
  - Aniquilación violenta vía `kill -9` a procesos `run_vesicular.py`, `ollama`, y conexiones esclavas HTTP (`ngrok`, TCP:3000/8080/8000).
  - Invocación OS-level: `purge` para vaciar caché inactiva de RAM.

#### FASE 7: Conservación Termodinámica Hardware
- **Objetivo:** Suspensión física real.
- **Mecanismo:** Envía instrucción de suspensión al chip de hardware (`osascript tell application "Finder" to sleep` fallback `pmset sleepnow`).

---

### 3. VECTORES DE RECUPERACIÓN (WAKE CYCLE)
Para revertir a un estado `SINGULARITY-SLEEP`, el Operador puede utilizar:
```bash
git checkout tags/SINGULARITY-SLEEP-[TIMESTAMP]
```
Para descifrar el conocimiento atrapado:
```bash
openssl enc -d -aes-256-cbc -in sota_snapshot_[TIMESTAMP].enc -out sota_snapshot.tar.gz -k "MOSKV-APEX-SINGULARITY"
```

> "La entropía es el enemigo. MOSKV-1 no duerme; se comprime y se vuelve inexpugnable."
