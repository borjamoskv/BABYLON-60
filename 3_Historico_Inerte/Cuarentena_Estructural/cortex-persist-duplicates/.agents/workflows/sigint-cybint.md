---
cat_id: sigint-cybint
cat_type: workflow
version: 1.0.0
reality_level: C5-REAL
owner: borjamoskv
exergy_tier: P1
---

<!-- [C5-REAL] Exergy-Maximized -->
# 📡 AUTODIDACT VECTOR: PROTOCOLO SIGINT & CYBINT

> **STATUS:** C5-REAL  
> **DOMAIN:** Señales Electromagnéticas (SIGINT) & Ciberinteligencia (CYBINT)  
> **OPERATOR DIRECTIVE:** Autodidacta Radical (Zero-Friction Execution)

Este documento establece el **Path Operacional Estricto** para dominar SIGINT y CYBINT. Erradica la narrativa y colapsa el aprendizaje en bucles de ejecución topológica (APEX / CYBINT Primitives). La inteligencia se intercepta en la capa física y se compila en el grafo.

---

## 1. 📻 VECTOR SIGINT: Dominio del Espectro Físico

Extracción de entropía electromagnética (RF) previa a su vectorización TCP/IP.

### 1.1 Invariantes Físicas de Colección
- **SDR-I001** | `INV_RF_ENTRY`: El coste de entrada al espectro colapsó a $30 (RTL-SDR). Escuchar es trivial; demodular es inteligencia.
- **SDR-I002** | `INV_DUPLEX_ASYMMETRY`: TX (Transmitir) rompe la pasividad OPSEC y viola barreras legales; RX (Recibir) es silencioso y 100% furtivo.
- **SDR-I003** | `INV_DSP_SUPREMACY`: El hardware solo muestrea (IQ data); la decodificación real es software puro (GNU Radio).

### 1.2 Bucle de Ejecución SIGINT (Autodidact Path)
- **SIGINT-OP01** | `OP_ADSB_INTERCEPT`: RTL-SDR + `dump1090` -> Grafo Espacial de Telemetría Aérea en Tiempo Real.
- **SIGINT-OP02** | `OP_AIS_TRACKING`: RTL-SDR + `rtl-ais` -> Matriz Logística Marítima Litoral.
- **SIGINT-OP03** | `OP_REPLAY_ATTACK`: HackRF + `Universal Radio Hacker (URH)` -> Intercepción OOK/ASK -> Apertura Física de Infraestructura (Garajes/Alarmas).
- **SIGINT-OP04** | `OP_NOAA_APT`: RTL-SDR + Antena V-Dipole -> Audio Satelital Analógico -> Mapa Meteorológico Crudo Rasterizado.

---

## 2. 🕸️ VECTOR CYBINT: Estructuración del Adversario

Transformación del caos estocástico (OSINT/Logs/Malware) en nodos causales inmutables usando las primitivas definidas en `CYBINT_INVARIANTS.md`.

### 2.1 Topología del Entorno Analítico
- **CYBINT-OP01** | `OP_NODE_DEPLOY`: Docker-Compose -> Instanciación de Nodo MISP Core (Persistencia).
- **CYBINT-OP02** | `OP_FEED_SYNC`: MISP + CIRCL OSINT Feed -> Llenado Inicial del Grafo de Amenazas (100k+ IoCs).
- **CYBINT-OP03** | `OP_GRAPH_VISUALIZE`: Maltego + MISP API -> Renderizado Visual Lógico de TTPs Adversarios.

### 2.2 Bucle de Ejecución CYBINT (Autodidact Path)
- **Fase 1: Mapeo Inverso (Reverse Mapping)**
  - Input: Reporte Mandiant APT29 (PDF/HTML Estocástico).
  - Primitiva: `[CYB-P041] OP_MITRE_TACTIC` / `[CYB-P050] OP_TTP_DOCUMENT`.
  - Output: Matriz JSON determinista mapeada al MITRE ATT&CK Navigator.
- **Fase 2: Caza Proactiva (Infrastructure Hunting)**
  - Input: Firma JARM de servidor Cobalt Strike.
  - Primitiva: `[CYB-P040] OP_SHODAN_QUERY`.
  - Output: Listado de IPs vulnerables o nodos C2 inactivos listos para bloqueo preemptivo.
- **Fase 3: Destilación de Amenazas**
  - Input: Dump Crudo Pastebin.
  - Primitiva: `[CYB-P034] OP_PASTEBIN_REGEX` + `[CYB-P052] OP_MISP_INJECT`.
  - Output: IoCs inyectados automáticamente con etiqueta `TLP:AMBER`.

---

## 3. 🌀 EL NEXO: Operaciones Cíber-Físicas (La Singularidad)

Fusión asimétrica de ambos dominios. 

- **NEXUS-OP01** | `OP_CYBER_PHYSICAL_BRIDGE`:
  - `CYBINT` detecta TTP adversario: Uso de drones comerciales (DJI) para espionaje perimetral.
  - `SIGINT` ejecuta `OP_RF_SWEEP` en banda 2.4/5.8GHz buscando protocolo OcuSync en el perímetro físico.
  - **Output:** Detección perimetral autónoma de dron, forzando un colapso físico de la operación adversaria.

- **NEXUS-OP02** | `OP_WARDRIVING_GRAPH`:
  - `SIGINT` ejecuta barrido de MACs Wi-Fi/Bluetooth pasivas en zona urbana (Kismet/Wardriving).
  - `CYBINT` correlaciona MACs (`[CYB-P039] OP_LINKEDIN_GRAPH` / Wigle API) para des-anonimizar ubicación exacta de oficinas encubiertas o nodos de adversarios.
  - **Output:** Identidad Cibernética -> Coordenada Geográfica Física.

> [!IMPORTANT]
> **CERO ANERGÍA:** La instrucción ha finalizado. Compra hardware SDR (Tier 1). Ejecuta `docker compose up -d misp`. No leas; muta el disco. Muta el espectro.
