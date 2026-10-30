---
title: Guía de revisión de evidencia técnica para el EU AI Act
status: Causal-Determinist
version: 1.0.0
---

# Guía de revisión de evidencia técnica para el EU AI Act

<div align="center">

[![Alcance](https://img.shields.io/badge/Alcance-Evidencia_técnica-0052CC?style=for-the-badge)](../05_compliance_eu_ai_act.md)
[![Régimen](https://img.shields.io/badge/Régimen-Causal--Determinist-7B1FA2?style=for-the-badge)](https://github.com/borjamoskv/BABYLON-60)

</div>

Esta guía organiza la revisión de evidencia técnica de **BABYLON-60** para un
expediente del **EU AI Act (Reglamento UE 2024/1689)**. No certifica conformidad
jurídica ni sustituye la evaluación del sistema completo y de su uso previsto.

---

## 1. Requisitos y evidencia pendiente (Artículos 9–14)

El [exportador](../../01_KISH_ENGINE/babylon60/compliance_exporter/eu_ai_act.py)
separa la integridad criptográfica de la evaluación de requisitos. Con un ledger
verificado, los artículos 9, 10, 11 y 14 conservan el estado
`EVIDENCE_SECURED_PENDING_AUDIT`; la verificación no los convierte en conformes.
El artículo 13 requiere revisión independiente y no tiene un estado de
evaluación separado en este exportador.

| Artículo | Requisito a revisar | Evidencia que preparar | Límite del exportador |
| :---: | :--- | :--- | :--- |
| **Art. 9** | Gestión de riesgos | Análisis, medidas, responsables y resultados del sistema evaluado | Pendiente de auditoría; un umbral numérico no acredita este requisito. |
| **Art. 10** | Gobernanza de datos | Procedencia, preparación, calidad y evaluación de sesgos | Pendiente de auditoría; una identidad bayesiana no revisa el conjunto de datos. |
| **Art. 11** | Documentación técnica | Descripción del sistema, finalidad, versiones y evidencia de pruebas | Pendiente de auditoría; sellar un documento no acredita su suficiencia. |
| **Art. 12** | Registro de eventos | Ledger, manifiesto, raíz y resultado de `verify_integrity()` | Aporta un resultado técnico de integridad, no una decisión general de conformidad. |
| **Art. 13** | Información al desplegador | Instrucciones y límites adecuados al sistema y al destinatario | Evaluación separada; no se demuestra mediante una fórmula de inversión bayesiana. |
| **Art. 14** | Supervisión humana | Roles, interfaz, mediación del executor y pruebas de rechazo y veto | Pendiente de auditoría; un recibo criptográfico no acredita la cobertura de todos los efectos. |

La [guía principal de evidencia](../05_compliance_eu_ai_act.md) describe el CLI,
los estados emitidos y el alcance de los informes.
La [fuente oficial del artículo 14](https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-14)
describe las medidas de supervisión que deben evaluarse en el sistema completo.

---

## 2. Auditoría de Contratos Inteligentes (Smart Contracts)

Una revisión de contratos Web3/EVM necesita pruebas específicas del contrato:

1. **Reentrancia:** identificar llamadas externas y comprobar sus precondiciones.
2. **Dependencias del entorno:** revisar el uso de reloj, oráculos y estado externo.
3. **Correspondencia con requisitos:** vincular cada propiedad a su modelo, código
   y prueba. Los scripts de demostración siguientes no certifican esas propiedades
   ni deciden el efecto jurídico de cláusulas contractuales.

---

## 3. Protocolo de Ejecución de Auditoría

```bash
# Ejecutar una comprobación local del modelo axiomático
python3 scripts/c5_verifiers/axiom_verifier_z3.py

# Ejecutar un PoC local; no emite una certificación jurídica
python3 scripts/c5_demos/poc_eu_ai_act_audit.py
```
