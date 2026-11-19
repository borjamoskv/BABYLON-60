# Archivo de periféricos

Fuentes históricas conservadas byte a byte el 14 de octubre de 2026. No forman
parte de los paquetes Python instalables ni del catálogo de scripts activos.
El sufijo `.py.disabled` evita su descubrimiento normal como módulos Python;
no convierte en seguro ejecutarlas manualmente con un intérprete.

| Fuente conservada | Alcance y condición para reutilizarla |
| --- | --- |
| [HUD ilustrativo](codex_virtual_hud.py.disabled) | Sus estados y selector de modelos son ilustrativos. Usa atajos globales mediante pynput; no observa agentes ni certifica el modelo activo. |
| [Prigogine y Boltzmann](prigogine_boltzmann_simulation.py.disabled) | Simulación numérica autónoma; sus resultados no miden el runtime del kernel. |
| [Luhmann](luhmann_autopoiesis_simulation.py.disabled) | Intenta cargar un ledger opcional y escribir SQLite con una ruta derivada de su ubicación anterior. Antes de reutilizarla, separar la salida en un directorio temporal explícito. |
| [Ouroboros](ouroboros_infinity.py.disabled) | Escanea archivos y registra resultados en SQLite con rutas derivadas de su ubicación anterior. Antes de reutilizarla, revisar tanto el ámbito de lectura como el destino temporal de las escrituras. |
| [Ledger fragmentado simulado](sharded_ledger_ring.py.disabled) | Mantiene elementos en memoria; el método de volcado solo cuenta elementos y no persiste un WAL. La cifra de capacidad en la cabecera no es una medición verificada. |

[manifest.json](manifest.json) registra las rutas anteriores y el SHA-256 de cada
snapshot. La reubicación no modifica su contenido, no conserva como válidas sus
afirmaciones históricas y no acredita ejecución de ninguna de estas demos.
Las rutas antiguas no se mantienen como alias ejecutables.
