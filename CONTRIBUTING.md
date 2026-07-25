<!-- C5-REAL EXERGY CERTIFIED -->

# Contributing Guidelines for Agents

## Estructura de Ramas

- `main`: Producción / versión estable. (Push directo bloqueado)
- `develop`: Integración (opcional).
- `feature/*`: Funcionalidades.
- `fix/*`: Correcciones.
- `release/*`: Preparación de versión.
- `hotfix/*`: Arreglos urgentes.

## Convenciones de Commits

Utilizar Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`).

## Flujo de Trabajo

Issue → Rama (`feature/` o `fix/`) → Pull Request → CI (Tests/Lint) → Revisión (Automática/Humana) → Merge → Release/Deploy

## Estándares de Código

- Todo cambio debe estar vinculado a un issue.
- Ejecutar pruebas y lint antes de solicitar revisión.
- Crear PRs pequeños y enfocados.
- NO exponer secretos, tokens, ni claves.
- Actualizar documentación para cualquier cambio en la API pública o comportamiento.
