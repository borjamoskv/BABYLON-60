# Lote 3 ejecutado: autorización y publicación — 28/10/2026

> Alcance de la distribución pública: las referencias marcadas como material no distribuido identifican evidencia o herramientas excluidas deliberadamente de este checkout. Se conservan sus rutas y los resultados históricos; esos soportes no pueden verificarse desde esta distribución.

Estado: ejecutado localmente. Véase el
[informe de corrección](REMEDIATION_SWARM100_LOTE3_2026-10-28.md). Los
hashes de selección (material no distribuido: `evidence/swarm100-lot2-20261028/lot3-selection.json`)
fijaron el estado previo. Se agruparon dos P1 originales y el P1 adicional de
referencia mutable, inicialmente CONFIRMED_STATIC/OPEN. Los tres tienen
reproducción confinada y corrección ejecutable.
Este plan no autoriza ni ejecuta commits, merges, acceso remoto, publicación o
autenticación biométrica.

| ID | Fuente | Resultado exigido |
| --- | --- | --- |
| C0413 | `scripts/c5_git_utils/c5_distill_public_mirror.sh` | Rechazar publicación si falta/falla el escáner obligatorio; comprobar el árbol que realmente se publicará. |
| SW100-R3-0001 | Mismo archivo | Publicar el commit inmutable preparado y ligado al efecto autorizado, aunque otra invocación cambie la rama de conveniencia. |
| C0418 | `scripts/c5_git_utils/c5_ship.sh` | Abortar si ningún gate biométrico está disponible; no alcanzar push ni comunicar un recibo inexistente. |

SW100-R3-0001 permanece fuera de los 598 IDs originales. C0414, sobre las
mutaciones locales permitidas durante dry-run, no se reabre ni se utiliza
como sustituto del problema de referencia mutable.

## Reproducción antes del parche

Copiar únicamente los scripts a un workspace temporal. Encerrar todas sus
rutas, utilidades y efectos en esa fixture: el comando Git remoto/publicador
de prueba solo registra argumentos y no conecta ni publica. No ejecutar las
versiones originales desde este checkout, que contiene trabajo ajeno.

- C0413: ausencia, salida de error y hallazgos del escáner deben impedir llegar
  al publicador de prueba. Comprobar también que el árbol escaneado coincide
  con el objeto inmutable seleccionado, no un worktree posterior.
- SW100-R3-0001: programar dos invocaciones de fixture. B cambia la referencia
  compartida mientras A está detenida antes del despacho. A debe conservar
  exactamente su commit/árbol/destino autorizados. Validar el contrato de hash
  y argumentos del gate antes de editar; no inventar una atestación válida.
- C0418: sin binario ni fuente Swift del gate, la ruta debe abortar y el
  publicador de prueba no debe ejecutarse. Un gate fallido/cancelado no debe
  reintentarse, reutilizar aprobación ni derivar a autenticación alternativa.

Los dobles de prueba solo permiten observar flujo y argumentos sobre efectos
inocuos. No producirán recibos ATTESTED ni simularán la satisfacción de una
atestación hardware para un efecto protegido. La integración hardware real
seguirá fuera del alcance de estos ensayos y exigirá el protocolo vigente.

## Corrección propuesta y aceptación

1. Establecer precondiciones explícitas: herramientas obligatorias, errores del
   escáner y disponibilidad del gate. Ninguna advertencia puede convertirse en
   autorización para publicar. Revisar el orden respecto a mutaciones locales.
2. Mantener identificadores inmutables del árbol y commit durante verificación,
   autorización y despacho. El publicador recibirá el commit guardado, no una
   rama mutable. Vincular también el destino según el contrato real del efecto.
3. Mantener la separación de preview/publicación y declarar comprobaciones no
   ejecutadas. Un dry-run no debe anunciar verificación completa si faltan
   requisitos, aunque su preparación local esté permitida.
4. Casos negativos deben terminar con código no cero, sin publicación ni recibo
   de éxito. Los positivos aislados solo prueban selección de objeto y flujo;
   no certificarán un push real ni Secure Enclave.
5. Ejecutar pruebas dirigidas, checks de shell disponibles, revisión independiente
   y controles documentales. Actualizar los dos IDs originales y el adicional
   por separado, conservando hashes y límites.

Solo se editaron las dos fuentes declaradas, tras la autorización de ejecución. La consolidación C0460 sigue MITIGATED y necesita un contrato de
persistencia propio; no se mezcla con este bloque.
