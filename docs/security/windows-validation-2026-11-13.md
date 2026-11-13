# Validación nativa de Windows — 13 de noviembre de 2026

La [ejecución 43460028170](https://github.com/borjamoskv/BABYLON-60/actions/runs/43460028170)
validó la CLI y el MCP Python del candidato `a1a53e24306a056f994e923b617ce52e6d1cf4f5`.
GitHub ejecutó el merge de comprobación `8d5706ba907b1e64c6c816b4ab4f2ebc5e0c78bb`;
ambos comparten el árbol Git `c288af41f19c0d944c783cfb88cb8bb7bbfda314`.

| Entorno | Instalación, CLI y MCP | Migraciones | Omisiones y fallos |
| --- | --- | --- | --- |
| Windows, Python 3.11 | 6 pruebas aprobadas | 4 aprobadas | 0 |
| Windows, Python 3.12 | 6 pruebas aprobadas | 4 aprobadas | 0 |

Las migraciones cubren instalación ausente, editable, wheel y source-wheel.
Cada caso conservó el lockfile y verificó la exclusión de los módulos y comandos
retirados. El gate exige las cuatro evidencias, todas sus fases y códigos de salida
correctos; no admite casos omitidos ni un intento fallido anterior.

Los artefactos `windows-terminal-python-3.11` y `windows-terminal-python-3.12`
contienen JUnit, entorno, observaciones por migración y veredicto. Sus archivos ZIP
publicados por GitHub tienen SHA-256, respectivamente:

- `d4f0f795990b2cf2aee2c4f70ed9b242c4cd1c27042d4d3824223b315b54de62`
- `a31ee99d99c0841973e56d310420cc0b60f99181f5c27913901700f10436c79b`

El instalador observado en Windows usa CRLF y su SHA-256 es
`a2e395b01664b2a53d554be366f46baedfd7c532843883280dae1f1d6e8290bd`.
Coincide exactamente con `install.ps1` de ese candidato al representarlo con
finales de línea CRLF. La comprobación local de los informes volvió a aprobar
las ocho migraciones con esos bytes.

Esta evidencia corresponde a ese candidato. Una revisión posterior requiere sus
propios checks; no constituye una firma de release ni certifica el broker Rust,
aislamiento de procesos, biometría o Secure Enclave en Windows. Para el historial
anterior, véase la [validación de octubre](windows-validation-2026-10-23.md).
