---
name: opentimestamps-l5-diagnostics
display_name: Atestación Criptográfica & Diagnóstico Bitcoin L5 (OpenTimestamps)
description: Verificación de atestación criptográfica y estampados temporales L5 en Bitcoin (OpenTimestamps). Dispara con "opentimestamps", "ots verify", "atestación l5", "bitcoin timestamp", "l5 diagnostics", "ots bitcoin", "sellado temporal l5".
role: auditor
allowed_roles:
- auditor
directives:
  worktree_mode: audit-only
  phase: verification
  handoff:
    upstream: ejecutor
    downstream: operador
---

# Skill: OpenTimestamps L5 Diagnostics

> **Directiva Declarativa (Orquestación en Árbol de Trabajo):**
> - **Rol Asignado:** `auditor` (Auditor (Verificación Independiente, Linters de Silicio & Fail-Closed Gate))
> - **Modo de Acceso a Worktree:** `audit-only` (audit-only (Lectura forense de diffs, linters, tests de estrés y cálculo de exergía; cero mutación de código))
> - **Fase Causal:** `verification`
> - **Contrato Handoff:** Recibe de `ejecutor` $\to$ Despacha a `operador`

## 1. Falso Positivo: Mutación de Salto de Línea
Si `ots verify` o el script de atestación lanza `[FALSIFIED] I4 ANCHOR: File does not match original!`, auditar de inmediato la entropía del archivo `.digest` objetivo.
- **Causa:** Un salto de línea `\n` inyectado por bash (`echo`) o editores convencionales eleva el tamaño a 65 bytes, alterando de forma destructiva el hash SHA-256 original (que debe ser estrictamente de 64 bytes para coincidir con la trayectoria Merkle del `.ots`).
- **Resolución Determinista:** Ejecutar el comando termodinámico puro de truncamiento en Perl (`perl -pi -e 'chomp if eof' *.digest`) antes de dar la atestación L5 por falsificada.

## 2. Dependencia de Infraestructura: Bitcoin Core RPC
Si la atestación falla indicando `Could not connect to Bitcoin node: Cookie file unusable` o que falta `.cookie` en `bitcoin.conf`:
- **Causa:** La librería `python-opentimestamps` invocada vía CLI requiere nativamente un nodo local completo de Bitcoin sincronizado en L1 para validar las cabeceras de bloque contra el *calendar server*.
- **Resolución Operativa:** Solicitar explícitamente al Operador que levante el daemon de Bitcoin local (`bitcoind`), o abortar el diagnóstico informando que la integridad L5 (aunque matemáticamente correcta a nivel archivo) no se puede certificar sin el nodo de atestación final en marcha.

## 3. Invariante Termodinámico: Agregación $\mathcal{O}(1)$ vs $\mathcal{O}(N)$
La atestación L5 nunca inyecta volumen masivo de datos en la cadena base de Bitcoin:
- **Compresión Criptográfica:** Millones de eventos, inferencias o estados ontológicos locales se agregan off-chain en un Árbol de Merkle.
- **Huella en L1:** Solo se publica periódicamente una raíz de 32 bytes (vía `OP_RETURN` o similar). La carga sobre la blockchain es estrictamente $\mathcal{O}(1)$ e independiente del volumen de atestaciones locales.

## 4. Inmunidad Anti-DoS y Paradoja de Subsidio al Minero
Ante la hipótesis de saturación o denegación de servicio deliberada mediante escrituras masivas:
1. **Defensas de Red:** Los nodos validadores descartan spam en socket TCP (`banScore`) y purgan la memoria RAM (`mempool eviction`, límite 300 MB) sin tocar disco.
2. **Inelasticidad de Bloque:** El rendimiento de L1 está limitado a ~4 MB de peso cada ~10 minutos. No existe mecanismo para forzar mayor throughput.
3. **Trampa del Atacante (Invariante C5 #3):** Monopolizar bloques pagando comisiones desorbitadas transfiere capital masivo a los mineros, elevando el hashrate y la dificultad de la red. El atacante se agota financieramente mientras subsidia la seguridad del sistema que pretendía destruir.

## 5. Delimitación Epistémica de Propiedad Intelectual
- **Dominio Público:** El anclaje temporal, el protocolo Bitcoin y los árboles de compromiso criptográfico son de dominio público y estándar abierto (Haber-Stornetta 1991, Satoshi 2008, Peter Todd 2016).
- **Propiedad del Sistema:** El valor y la autoría residen exclusivamente en la arquitectura de reducción dimensional previa: cómo el sistema de IA transforma ruido en conceptos de alta exergía, audita la ausencia de confabulación y construye el vector ontológico antes de su estampación.

## 6. Economía de la Atestación y Dualidad de Enrutamiento
El sistema C5-REAL opera bajo dos vectores de anclaje según el perfil de amenaza:
1. **Ruta L5 Estándar (Amortización Termodinámica - OpenTimestamps):**
   - **Mecanismo:** El hash se envía a un *Calendar Server* público que agrega millones de pruebas en un único Árbol de Merkle (coste geométrico $\mathcal{O}(1)$).
   - **Coste:** Gratis para el nodo local (la comisión de red la subsidia el servidor).
   - **Soberanía:** Intacta. La prueba (`.ots`) devuelta es pura matemática (Merkle Path) y se audita contra el nodo local `bitcoind`. No se requiere confianza residual en el servidor.
2. **Ruta L1 Soberana Absoluta (Raw OP_RETURN):**
   - **Mecanismo:** Ejecución de `scripts/c5_l1_ledger/l1_sink_bitcoin.py`. BABYLON-60 construye el árbol de Merkle y la transacción cruda (`6a20...`).
   - **Coste:** Requiere consumo directo de capital termodinámico (UTXOs del Operador para pagar la tarifa *sat/vB* a los mineros).
   - **Uso Estricto:** Reservado exclusivamente para escenarios de hostilidad extrema, caída coordinada de los Calendar Servers, o atestación de contratos en cámara de aire.
