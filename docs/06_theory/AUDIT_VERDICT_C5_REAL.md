---
title: Dictamen histórico C4-SIM: alcance y evidencia pendiente
status: Dictamen-historico-no-revalidado
version: 2.0.0
---

# Dictamen histórico C4-SIM: alcance y evidencia pendiente

Revisión científica: 2026-10-24. Estatus: **Dictamen-historico-no-revalidado**. El sello histórico de verificación y el axioma genérico de validez documental no acreditaban el contenido. [Alcance y evidencia de la revisión](AUDIT_SCIENTIFIC_STATUS_2026.md).

## 1. Alcance de la rectificación

El informe del 2026-07-29 acusaba a otro reporte de inventar tests, frontend, linting, firmas SSH y topología. No se aportan aquí los transcripts originales, estado de la máquina evaluada ni artefactos que permitan reconstruir todas esas acusaciones. Se retiran sus etiquetas globales FALSADO como resultados establecidos por esta revisión, sin afirmar que las alegaciones originales fueran ciertas.

| Alegación histórica | Qué permitiría comprobarla | Estatus |
| --- | --- | --- |
| «426 tests pasados» frente a `tests/cortex` ausente | Versión, colección y log del entorno donde se declararon ejecutados | NO_REVALIDADO. Ausencia actual no refuta otro snapshot. |
| Frontend Vite y dist inexistentes | Artefacto, ruta, commit y entorno de build | NO_REVALIDADO. |
| 24 correcciones Ruff sobre archivos fantasma | Diff, versión de Ruff y log | NO_REVALIDADO. |
| Git/SSH/llavero simulados | Capacidad real del entorno, firma y registro original | NO_REVALIDADO. No se atribuyen capacidades a un modelo por su marca. |
| «Repositorio intacto» y rechazo O(1) | Snapshot comparado, efectos observados y modelo de coste | NO_VERIFICADO como garantía general. |

## 2. Qué sí expresa el pequeño modelo

La función siguiente define un filtro que rechaza contar cero tests en disco. Su teorema compila aisladamente, pero no inspecciona disco, no cuenta tests reales y no prueba que un reporte sea falso. Un contador no registra identidad, ejecución ni éxito de los tests. Se conserva la propiedad aritmética, retirando la interpretación como evidencia de fraude o integridad del repositorio.

```lean
namespace Babylon60.Theory.AuditVerdictC5Real

set_option warningAsError true

/-- Un reporte C4-SIM sin sustrato físico (0 tests en disco real) colapsa a falso. -/
def physical_substrate_valid (disk_tests_present : Nat) (claimed_tests : Nat) : Bool :=
  decide (disk_tests_present > 0 ∧ disk_tests_present == claimed_tests)

theorem ghost_tests_rejected (claimed : Nat) :
    physical_substrate_valid 0 claimed = false := by
  unfold physical_substrate_valid
  simp

end Babylon60.Theory.AuditVerdictC5Real

/-- info: 'Babylon60.Theory.AuditVerdictC5Real.ghost_tests_rejected' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in
#print axioms Babylon60.Theory.AuditVerdictC5Real.ghost_tests_rejected
```

Dependencias del teorema: `propext` y `Quot.sound`, fijadas por `#guard_msgs`; no hay un axioma científico añadido. No se infiere de ellas autenticación, ejecución o éxito real.

## 3. Regla de evidencia

Validar afirmaciones contra su entorno y fecha. Una sandbox puede ejecutar trabajo real dentro de su ámbito; para acreditar efectos en otro host se necesitan evidencias de transferencia o ejecución allí. Esta auditoría no vuelve a ejecutar operaciones remotas ni certifica estado de llaves, cuentas o publicación.
