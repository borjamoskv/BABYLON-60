# Contrato — Lote 10 (29/10/2026, Europe/Madrid)

C0574/C0575: única fuente productiva editable scripts/c5_verifiers/purge_residuals.py.
Reproducir primero solo en directorios/repositorios de fixtures, HOME propio,
Git/config propios, lock O_EXCL con descriptor abierto y base SQLite temporal.
No purga del proyecto real ni bases del operador, ni cambios de dependencias,
lockfiles, commits/push reales, hardware/red o ATTESTED.

Ring-0 (persistencia/rutas), Ring-2 (locks/Git) y Ring-3 (reportes/CLI).
No eliminar locks operativos por edad/nombre/PID. No borrar DB/WAL/SHM o
parecidos por extensión/ruta/marcador. Excluir metadatos Git/worktree/common-dir
sin ampliar recorrido. No seguir symlinks. Cachés con alcance conservador y
reportes basados en efectos observados; no 0% entropía/certificación supuesta.
Aislar verify_va en fixtures; no efectos laterales del verificador real.

Aceptación: red/green por ID, datos/locks/inodos/exclusión observados,
cachés autorizadas/fallos/symlinks, suite relacionada, Ruff/MyPy, revisión
independiente, registro reconciliado y controles documentales. Preparar Lote11
sin aplicar. Preservar cambios ajenos y evidencia histórica.
Grafo babylon-60/raíz exacta: metadata_match best-effort, único caller __main__.

Refinamiento previo al parche: conservar TODOS los directorios y archivos
no reconocidos; la limpieza se limita a bytecode Python actual con cabecera
reconocida dentro de __pycache__, regular, propio y sin hardlinks. No rmtree
ni borrado de .DS_Store opaco. Excluir cachés desconocidas/scratch y árboles
protegidos, .git y estructuras gitdir/worktree incluso con otro nombre.
Usar descriptores relativos O_NOFOLLOW/O_NONBLOCK y comparar identidad antes
de unlink; esto no hace atómico stat->unlink frente a escritores hostiles.
API devuelve informe estructurado; CLI imprime resumen/JSON y falla ante
error de recorrido/borrado. Retirar verify_va automático: es efecto ajeno y
no demuestra propiedad de artefactos ni resultado de limpieza. Sin firmas,
0% entropía ni estimación de espacio físico recuperado.
