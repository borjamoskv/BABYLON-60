---
name: handoff
display_name: Protocolo Soberano de Traspaso de Contexto C5-REAL
description: Genera un documento completo de traspaso de contexto (HANDOFF.md) para transferir lecciones aprendidas, estado del sistema y próximos pasos a una nueva sesión. Dispara con "handoff", "/handoff", "traspaso de contexto", "traspaso de sesión", "generar handoff", "traspaso formal", "context handover".
role: auditor
allowed_roles:
- auditor
- arquitecto
- ejecutor
directives:
  worktree_mode: audit-only
  phase: verification
  handoff:
    upstream: ejecutor
    downstream: operador
---

# Skill: C5 Handoff Protocol

> **Directiva Declarativa (Orquestación en Árbol de Trabajo):**
> - **Rol Asignado:** `auditor` (Auditor (Verificación Independiente, Linters de Silicio & Fail-Closed Gate))
> - **Modo de Acceso a Worktree:** `audit-only` (audit-only (Lectura forense de diffs, linters, tests de estrés y cálculo de exergía; cero mutación de código))
> - **Fase Causal:** `verification`
> - **Contrato Handoff:** Recibe de `ejecutor` $\to$ Despacha a `operador`

Este protocolo ejecuta la transducción inmutable de estado entre sesiones del agente, garantizando la preservación del estado de baja entropía en `HANDOFF.md`.

---

## 1. Algoritmo de Transducción de Estado

```
Historial Sesión Activa (T) ---> Filtrar Invariantes & Lecciones ---> Estructurar Matriz HANDOFF.md ---> Commit VCS
```

1. **Extracción de Invariantes:** Inspección de `USER_REQUEST` y decisiones tomadas.
2. **Purga de Anergía Efímera:** Eliminar logs de depuración temporales; conservar únicamente diffs y estados de verificación.
3. **Escritura en Raíz:** Generar o actualizar `HANDOFF.md` en la raíz del workspace actual.

---

## 2. Esquema Cannónico de Entregable (HANDOFF.md)

| Sección | Invariante Requerido | Formato |
| :--- | :--- | :--- |
| **🎯 Objetivo** | Meta global y límites de contención | 1 frase concisa |
| **✅ Delta Exergético** | Avances verificado empíricamente | Tabla de tareas / Diffs |
| **📍 Punto Fijo $\Omega$** | Estado de detención exacto y tests pasando/fallando | Checkpoints e identificadores de error |
| **🧠 Matriz de Gotchas** | Decisiones de diseño, parches no intuitivos y reglas | Lista de advertencias de alta densidad |
| **🚀 Grafo de Acción** | Secuencia $O(1)$ de entrada para la siguiente sesión | Lista de comandos exactos |

---

## 3. Enrutamiento Autónomo Inter-Workspace (Inyección Física)

Si el usuario indica que el Handoff va dirigido a una sesión, agente o arquitectura externa específica (ej. "pásale esto a BABYLON 60"):

1. **Cero Pasividad:** Queda terminantemente prohibido generar el archivo en el directorio local y esperar que el usuario lo mueva manualmente.
2. **Localización Física:** El agente DEBE rastrear el sistema de archivos (`ls -d ~/BABYLON*` o `find`) para localizar el directorio raíz físico del agente o proyecto destino.
3. **Inyección Directa:** El agente copiará el artefacto generado directamente a la raíz del repositorio destino bajo un nombre inequívoco (ej. `INCOMING_HANDOFF_C6.md`), y reportará en el chat la ruta exacta de la inyección.
