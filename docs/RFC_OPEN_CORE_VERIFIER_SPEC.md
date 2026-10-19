---
rfc: RFC-B60-2026-02
title: Open-Core Independent Compliance Verifier & Standard Specification
status: Standards Track / Open-Core Frozen
version: 1.0.0
date: 2026-10-09
author: Borja Moskv (borjamoskv) <borja@babylon60.com>
domain: EU AI Act Regulation (EU) 2024/1689 | BFT Forensic Auditing | Kerckhoffs Cryptosystem
---

# RFC-B60-2026-02: Open-Core Independent Compliance Verifier Specification

<div align="center">

[![C5-REAL Verified](https://img.shields.io/badge/C5--REAL-Verified-00F0FF?style=for-the-badge&logo=shield)](https://github.com/borjamoskv/BABYLON-60)
[![Régimen](https://img.shields.io/badge/Régimen-Causal--Determinist-7B1FA2?style=for-the-badge)](https://github.com/borjamoskv/BABYLON-60)

</div>


## 1. Declaración de Conformidad con el Principio de Kerckhoffs

### 1.1 El Teorema de Kerckhoffs en la Auditoría de Inteligencia Artificial
En 1883, Auguste Kerckhoffs formuló el principio fundacional de la criptografía moderna:
> *"Il faut qu'il n'exige pas le secret, et qu'il puisse sans inconvénient tomber entre les mains de l'ennemi."*
> (Un sistema criptográfico debe ser seguro incluso si todo lo relativo al sistema, excepto la clave secreta, es de conocimiento público).

En el paradigma contemporáneo de gobernanza y auditoría de IA (especialmente bajo el **Reglamento Europeo de Inteligencia Artificial - Reglamento (UE) 2024/1689** y la directiva **(UE) 2026/1744**), la industria del software corporativo ha incurrido sistemáticamente en la falacia de **"Seguridad por Oscuridad"** (*Security through Obscurity*): plataformas SaaS propietarias donde la verificación del cumplimiento depende de invocaciones cerradas a APIs en la nube, código binario no auditable o atestaciones comerciales sin garantías matemáticas formales.

### 1.2 Resolución Open-Core en BABYLON-60
BABYLON-60 resuelve la paradoja de Kerckhoffs desacoplando radicalmente la infraestructura operativa del verificador forense:
1. **Zero Proprietary Dependencies:** El motor de verificación (`babylon60.verifier.standalone_verify`) y su interfaz de línea de comandos (`babylon-verify`) no exigen suscripciones, tokens de API, pasarelas de red, ni binarios propietarios de BABYLON-60.
2. **Offline Air-Gapped Verification:** Cualquier CISO, Delegado de Protección de Datos (DPO), auditor judicial o inspector de la autoridad supervisora (AESIA, BSI, CNIL) puede tomar el certificado JSON, el archivo de ledger SQLite/JSON y el código del verificador en una máquina sin conexión a Internet (*Air-Gap*) y obtener un veredicto binario determinista en $O(N)$ o $O(\log N)$.
3. **Auditabilidad Universal:** Los algoritmos de canonicidad JSON (RFC 8785), funciones de resumen criptográfico (SHA-256 / SHA3-256), árboles de Merkle con separación de dominios y firmas digitales Ed25519 (RFC 8032) son estándares abiertos del IETF y el NIST. La seguridad del certificado reside **exclusivamente en la clave privada de firma del operador** y en la resistencia a colisiones de las funciones hash.

---

## 2. Especificación Formal del Certificado de Cumplimiento JSON

### 2.1 Esquema de Datos Canónico (JSON Schema)
Todo Certificado de Cumplimiento emitido bajo este estándar es un objeto JSON estricto estructurado en las siguientes secciones obligatorias y opcionales:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "EUAIActComplianceCertificate",
  "type": "object",
  "required": [
    "certificate_id",
    "system_identifier",
    "operator",
    "issued_at",
    "valid_until",
    "global_merkle_root",
    "articles_compliance",
    "signature"
  ],
  "properties": {
    "title": { "type": "string" },
    "locale": { "type": "string", "enum": ["es", "en", "de", "fr", "it"] },
    "compliance_standard": { "type": "string" },
    "supervisory_authority": { "type": "string" },
    "report_id": { "type": "string", "pattern": "^EU-AIA-REPORT-[A-F0-9]{16}$" },
    "certificate_id": { "type": "string", "pattern": "^EU-AIA-CERT-[A-F0-9]{16}$" },
    "system_identifier": { "type": "string" },
    "operator": { "type": "string" },
    "issued_at": { "type": "string", "format": "date-time" },
    "valid_until": { "type": "string", "format": "date-time" },
    "validity_days": { "type": "integer", "minimum": 1 },
    "global_merkle_root": { "type": "string", "pattern": "^[a-f0-9]{64}$" },
    "quarantine_status": { "type": "string" },
    "legal_disclaimer": { "type": "string" },
    "evidence_verification": {
      "type": "object",
      "properties": {
        "ledger_path": { "type": ["string", "null"] },
        "ledger_present": { "type": "boolean" },
        "integrity_verified": { "type": ["boolean", "null"] },
        "ledger_merkle_root": { "type": ["string", "null"] },
        "manifest_global_hash": { "type": "string" },
        "evidence_match": { "type": ["boolean", "null"] },
        "verified": { "type": "boolean" },
        "detail": { "type": "string" }
      }
    },
    "revocation": {
      "type": "object",
      "required": ["status"],
      "properties": {
        "status": { "type": "string", "enum": ["ACTIVE", "REVOKED", "SUSPENDED"] },
        "check_hash": { "type": "string", "pattern": "^[a-f0-9]{64}$" },
        "revocation_authority": { "type": "string" }
      }
    },
    "hardware_anchor": {
      "type": "object",
      "properties": {
        "pcr_index": { "type": "string" },
        "hardware_uuid": { "type": "string" },
        "pcr_composite": { "type": "string" },
        "quote_signature": { "type": "string" }
      }
    },
    "articles_compliance": {
      "type": "object",
      "required": [
        "Article_9_Risk_Management",
        "Article_10_Data_Governance",
        "Article_11_Technical_Documentation",
        "Article_12_Record_Keeping_Logging",
        "Article_14_Human_Oversight",
        "Article_15_Robustness_Cybersecurity"
      ],
      "additionalProperties": {
        "type": "object",
        "required": ["title", "status", "mechanism", "evidence_hash"],
        "properties": {
          "title": { "type": "string" },
          "status": { "type": "string" },
          "mechanism": { "type": "string" },
          "evidence_hash": { "type": "string", "pattern": "^[a-f0-9]{64}$" }
        }
      }
    },
    "cryptographic_attestation": {
      "type": "object",
      "properties": {
        "policy": { "type": "string" },
        "attestation_engine": { "type": "string" },
        "fingerprint": { "type": "string", "pattern": "^[a-f0-9]{64}$" }
      }
    },
    "signature": {
      "type": "object",
      "required": ["algorithm", "public_key", "signature"],
      "properties": {
        "algorithm": { "type": "string", "enum": ["Ed25519"] },
        "public_key": { "type": "string", "pattern": "^[a-f0-9]{64}$" },
        "signature": { "type": "string", "pattern": "^[a-f0-9]{128}$" },
        "signed_payload_sha256": { "type": "string", "pattern": "^[a-f0-9]{64}$" },
        "canonicalization": { "type": "string" },
        "ephemeral": { "type": "boolean" }
      }
    }
  }
}
```

### 2.2 Desglose de Campos Cardinales
1. **`certificate_id`**: Identificador único global inmutable (`EU-AIA-CERT-<FINGERPRINT16>`).
2. **`system_identifier`**: Slug o identificador del modelo o agente de IA bajo evaluación.
3. **`global_merkle_root`**: Hash SHA3-256 o SHA-256 de 64 caracteres hexadecimales que ancla la totalidad del historial de eventos del sistema.
4. **`valid_until`**: Fecha de caducidad en formato ISO 8601 UTC (`YYYY-MM-DDTHH:MM:SSZ`). Los certificados son nulos una vez superada esta marca temporal.
5. **`articles_compliance`**: Matriz de evaluación artículo por artículo. Cada artículo contiene un `evidence_hash` derivado deterministamente de la raíz global mediante:
   $$\text{evidence\_hash}_k = \text{SHA-256}(\text{"ART"} \mathbin{\Vert} k \mathbin{\Vert} \text{":"} \mathbin{\Vert} \text{global\_merkle\_root})$$
6. **`signature`**: Contenedor criptográfico Ed25519 con la clave pública del auditor/emisor (32 bytes = 64 hex) y la firma digital (64 bytes = 128 hex).

---

## 3. Especificación Matemática del Árbol de Merkle y Canonicidad JSON

### 3.1 Canonicidad JSON Determinista (RFC 8785)
Para garantizar la reproducibilidad unívoca del payload firmado a través de diferentes plataformas, lenguajes (Rust, Python, Go) y arquitecturas de procesador, la serialización se rige por las siguientes reglas:
1. **Ordenación Léxica de Claves:** Todas las claves de los objetos JSON se ordenan lexicográficamente por su valor Unicode en cada nivel de anidamiento (`sort_keys=True`).
2. **Separadores Compactos:** Sin espacios en blanco superfluos; los delimitadores son estrictamente `","` entre elementos y `":"` entre clave y valor (`separators=(",", ":")`).
3. **Codificación de Caracteres:** UTF-8 estricto sin secuencias de escape no obligatorias (`ensure_ascii=False`).
4. **Prohibición de Valores No Estándar:** Prohibición explícita de `NaN`, `Infinity`, o `-Infinity` (`allow_nan=False`).

La función de canonicidad se define como:
$$\mathcal{C}(D) = \text{JSON\_JCS}(D) \in \{0, 1\}^*$$

El payload canónico para la firma es el certificado completo **excluyendo** el nodo `signature`:
$$\text{Payload} = \mathcal{C}(C \setminus \{\text{"signature"}\})$$

### 3.2 Construcción del Árbol de Merkle con Separación de Dominio
Para prevenir ataques de colisión de longitud y segundas preimágenes (donde un atacante presenta un nodo interno como hoja), BABYLON-60 implementa **Domain Separation Tags (DST)** conforme a los estándares de atestación criptográfica del IETF:

#### 1. Capa de Hojas ($L_0$):
Cada evento $e_i$ del ledger se procesa calculando su hash de entrada:
$$h_i = \text{compute\_cortex\_hash}(e_i) \in \{0, 1\}^{256}$$
$$\text{Layer}_0 = [h_1, h_2, \dots, h_N]$$

#### 2. Agregación de Capas Superiores ($L_k$ para $k \ge 1$):
Para cada nivel $k$ del árbol:
- Si el número de nodos es impar, el último nodo se duplica:
  $$\text{Layer}_k[-1] = \text{Layer}_k[-1]$$
- Cada par de nodos adyacentes $(A, B)$ se concatena con un prefijo de dominio:
  $$\text{Tag}_k = \begin{cases} \mathtt{0x00} & \text{si } k = 0 \text{ (fusión de hojas)} \\ \mathtt{0x01} & \text{si } k > 0 \text{ (fusión de nodos internos)} \end{cases}$$
  $$\text{Parent}(A, B) = \text{SHA3-256}(\text{Tag}_k \mathbin{\Vert} A \mathbin{\Vert} B)$$

#### 3. Anclaje de Cardinalidad Final ($R$):
Una vez colapsado el árbol en un único nodo raíz $H_{\text{top}}$, la Raíz Global de Merkle se sella con el prefijo $\mathtt{0x02}$ y el número total de hojas $N$ codificado como un entero sin signo de 64 bits en orden *little-endian*:
$$R = \text{SHA3-256}(\mathtt{0x02} \mathbin{\Vert} H_{\text{top}} \mathbin{\Vert} \text{uint64\_le}(N))$$

Este anclaje garantiza que es computacionalmente imposible sustituir un subárbol o alterar la cantidad de eventos registrados sin invalidar la raíz $R$.

### 3.3 Verificación de la Firma Ed25519 (RFC 8032)
La verificación de la firma digital utiliza el algoritmo PureEd25519 sobre la curva retorcida de Edwards Edwards25519:
$$\text{Verify}(PK, \text{Payload}, \sigma) \in \{\text{True}, \text{False}\}$$
Donde:
- $PK \in \{0, 1\}^{256}$ es la clave pública decodificada de `cert.signature.public_key`.
- $\sigma \in \{0, 1\}^{512}$ es la firma decodificada de `cert.signature.signature`.
- $\text{Payload} = \mathcal{C}(C \setminus \{\text{"signature"}\})$ es el flujo de bytes canónico.

---

## 4. Modelo de Amenazas y Garantías de Verificación Offline

### 4.1 Modelo de Amenazas
El verificador independiente asume un entorno adversarial donde intervienen los siguientes vectores de ataque:

| Vector de Amenaza | Descripción del Ataque | Mitigación Criptográfica en Verificador Open-Core |
| :--- | :--- | :--- |
| **Operador Malicioso (Post-Facto Tampering)** | El operador altera las decisiones de riesgo, el nombre del sistema o el estatus de un artículo tras un incidente. | **Firma Ed25519 Fail-Closed:** Cualquier mutación de un solo bit en el JSON invalida la firma criptográfica. Veredicto: `valid=False`. |
| **Falsificación de Registro Histórico (Ledger Rewriting)** | El operador altera eventos en la base de datos SQLite para ocultar sesgos o vulnerabilidades. | **Recomputación de Hash-Chain & Merkle:** El verificador recomputa todos los hashes fila por fila comprobando Lamport, `prev_hash` y la raíz de Merkle. |
| **Inyección de Certificado Expirado** | Un proveedor presenta un certificado emitido hace 18 meses para un modelo que ha sido reentrenado. | **Inspección de Ventana de Vida:** Verificación estricta contra `valid_until`. Veredicto: `CERTIFICATE_EXPIRED`. |
| **Uso de Certificado Revocado** | Un certificado cuya clave fue comprometida es presentado a un cliente corporativo. | **Comprobación CRL Determinista:** Comparación contra lista de revocación local o cabecera `revocation.status == "REVOKED"`. |
| **Ataque de Intermediario (Man-in-the-Middle)** | Un intermediario altera el certificado en tránsito durante su entrega. | **Resistencia de Clave Pública:** La verificación utiliza exclusivamente la clave pública del emisor acreditado; el canal de transmisión no requiere confianza. |

### 4.2 Garantías para CISOs, DPOs y Auditores de la EU AI Act

#### 1. Garantía para el CISO (Seguridad de la Información):
- **Cero Superficie de Exfiltración:** El verificador se ejecuta localmente. Ningún dato del sistema, identificador interno o topología se transmite a servidores remotos.
- **Auditoría de Código Fuente Completa:** El código fuente del verificador (`standalone_verify.py`) consta de menos de 500 líneas de Python estándar sin dependencias ofuscadas, permitiendo auditoría de seguridad línea por línea en menos de 15 minutos.

#### 2. Garantía para el DPO (Privacidad y Protección de Datos):
- **Cumplimiento del Artículo 10 (Gobernanza de Datos):** La evidencia almacenada en los ledgers pasa por una capa de redacción criptográfica no reversible (`[REDACTED_AUDIT_SAFE]`, `[REDACTED_AWS_AKIA]`). El verificador comprueba la integridad de la evidencia sin necesidad de desencriptar o exponer datos personales (PII).

#### 3. Garantía para el Auditor Regulatorio (EU AI Act):
- **Cumplimiento del Artículo 12 (Conservación Automática de Registros):** Capacidad de comprobar en segundos si los logs generados durante la vida útil del sistema corresponden bit a bit con el certificado presentado ante la autoridad de supervisión.
- **Independencia Pericial:** El auditor no requiere solicitar acceso a la infraestructura interna del auditado; únicamente exige el par `(cert.json, ledger.db)` y ejecuta:
  ```bash
  python -m babylon60.verifier.cli --cert cert.json --ledger ledger.db
  ```

---

## 5. Instrucciones de Implementación y Ejecución de Referencia

### 5.1 Instalación con Cero Dependencias Propietarias
Para un entorno limpio de auditoría con Python 3.10+:
```bash
pip install cryptography
# o alternativamente: pip install pynacl
```

### 5.2 Verificación Independiente vía CLI
```bash
# Verificación básica del certificado (esquema, firma y ciclo de vida)
python -m babylon60.verifier.cli --cert compliance_cert.json

# Verificación forense profunda con ledger SQLite
python -m babylon60.verifier.cli --cert compliance_cert.json --ledger audit_ledger.db

# Verificación con lista de certificados revocados (CRL) y salida JSON para CI/CD
python -m babylon60.verifier.cli --cert compliance_cert.json --crl crl.json --json
```

### 5.3 Códigos de Retorno Deterministas
- **`0`**: Certificado conforme, íntegro, no revocado, no expirado y (si se suministró ledger) matemáticamente idéntico a la evidencia registrada.
- **`1`**: Certificado corrupto, firma inválida, expirado, revocado o con discrepancia en la raíz de Merkle.
