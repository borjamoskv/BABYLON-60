# Reconstrucción proto-lingüística probabilística — Proto-Romance

**Qué es esto.** Una versión *real y falsable* de la idea de "invertir la derivación
y recuperar el proto-lenguaje". En vez de afirmar que existe una raíz única sin
ambigüedad, reconstruye cada proto-segmento como una **distribución de probabilidad**
y **valida contra el latín atestiguado**, porque el ancestro del romance sí lo conocemos.

## Método (el mismo de la filogenética bayesiana de lenguas)

1. **Datos.** 18 cognados en 6 lenguas romances (es, pt, fr, it, ro, sardo), transcripción
   fonética ASCII coarse tipo ASJP. El latín se reserva como *ground truth*.
2. **Alineamiento.** Needleman–Wunsch con puntuación fonética por rasgos + MSA progresivo
   (center-star), para poner en correspondencia posición a posición.
3. **Modelo de sustitución.** Cadena de Markov de tiempo continuo, reversible (GTR-like)
   sobre 25 estados-segmento; las tasas de intercambio salen de la distancia fonética por
   rasgos (lugar, modo, sonoridad; altura, anterioridad, redondeamiento).
4. **Inferencia.** Poda de Felsenstein sobre un árbol romance fijo (sardo conservador =
   rama corta; francés = rama larga). Da la **posterior** del proto-segmento en la raíz.
5. **Incertidumbre.** Entropía (bits) de cada posterior = incertidumbre irreducible.

Invariantes verificados: filas de Q suman 0, P(t) estocástica y no-negativa,
detailed-balance (cadena reversible), salida determinista.

## Resultados (vs. latín atestiguado)

| Métrica | Valor |
|---|---|
| Acierto por segmento | **78.7 %** |
| Edit distance normalizado | **0.261** (0 = perfecto) |
| Entropía media en aciertos | 0.55 bits |
| Entropía media en errores | 2.24 bits |
| corr(entropía, error) | **+0.687** |

Reconstrucciones perfectas y de baja entropía donde la información se conservó:
`moon → l u n a` (H≈0.08), `sea → m a r e`, `to_sing → k a n t a r e`, `to_die → m o r i r e`.

Errores concentrados donde el cambio fonético **fusionó** sonidos y borró información:
el grupo latino `-ct-` (`night nocte`, `milk lacte`, `eight octo` — todas las hijas lo
alteraron de forma distinta), la fusión `b/v` (`have`, `water`), la pérdida de `h-`.

## El hallazgo honesto

La separación de entropía (0.55 vs 2.24 bits) y la correlación **+0.69** significan que
el modelo *sabe lo que no sabe*: su incertidumbre predice sus errores. Ahí está,
**medida**, la irreversibilidad del cambio fonético. No hay "token único libre de
ambigüedad": donde varios proto-fonemas colapsaron en uno, la inversa no es una función,
es una distribución. El cómputo no recupera lo que la entropía ya destruyó — pero sí
cuantifica exactamente cuánto se perdió y dónde.

## Límites y escalado

- Muestra ilustrativa (18 conceptos, transcripción coarse: geminadas y vocales
  nasales/anteriores redondeadas simplificadas). El acierto absoluto subiría con
  transcripción fina y más cognados.
- Árbol y longitudes de rama fijados a mano (cronología conocida). La versión de
  producción los **infiere** conjuntamente por MCMC (BEAST2 / MrBayes).
- El método escala sin cambios estructurales a **Lexibank**, **ASJP** o **IE-CoR**
  (indoeuropeo). Para PIE no hay gold: se reportarían proto-formas *con su banda de
  incertidumbre*, no una única raíz.

## Archivos

- `proto_romance_reconstruction.py` — pipeline autocontenido (numpy + scipy).
- `reconstruccion_resultados.csv` — reconstrucción, latín, entropía y acierto por cognado.
