| ID | Redundancia C5 | Función Topológica | Riesgo Mitigado | Coste (Overhead) | Dependencias |
| :--- | :--- | :--- | :--- | :--- | :--- |
| RED-021 | Sandbox Aislado | Ejecución obligatoria de código generado en un contenedor efímero aislado sin red. | Fugas de escape adversariales y mutación hostil del host. | Overhead de creación del subproceso (ms) y cuotas de cgroup. | Docker / gVisor / Subprocess + Non-root. |
