---
title: Compendio C5-REAL — información, escalabilidad y límites de la analogía termodinámica
status: Auditado-con-alcance-limitado
version: 2.0.0
---

# Compendio C5-REAL: información, escalabilidad y límites físicos

Revisión científica: 2026-10-24. Sustituye la versión 1.0.0: se retiran el sello «Verified», las atribuciones de modelo no acreditadas y la presentación de axiomas como pruebas. Este documento especifica conceptos y un modelo aritmético; no certifica BABYLON-60 en ejecución.

## 1. Estatus de las afirmaciones y ocho capas

**Definición** fija una convención; **demostrado** exige hipótesis y prueba; **hipótesis** necesita contraste; **metáfora** no establece una equivalencia física. **NO_VERIFICADO** señala una afirmación concreta sin evidencia suficiente. Los resultados publicados tienen el alcance de sus experimentos, no el de una garantía universal.

Las ocho capas se conservan como taxonomía de ingeniería propuesta, no como clasificación termodinámica demostrada.

| Capa heredada | Interpretación operativa | Estatus y límite |
| --- | --- | --- |
| L1 Data Exergy | Selección, procedencia y evaluación de datos | Hipótesis: la curación mejora tareas identificadas; la densidad textual no garantiza calidad. |
| L2 Alignment Exergy | Entrenamiento con preferencias humanas | Mecanismo de aprendizaje; no transferencia de trabajo termodinámico a «sinapsis» ni garantía de verdad. |
| L3 Context Exergy | Recuperación de documentos y herramientas | RAG tiene resultados empíricos específicos [5]; recuperar texto no garantiza su verdad. |
| L4 Prompt Exergy | Instrucciones y restricciones | Un prompt no modifica la función de pérdida durante inferencia ni impone restricciones infranqueables; estas requieren validadores externos. |
| L5 Reflexive Exergy | Ciclos de propuesta, ejecución y test | Hipótesis de mejora con oráculos adecuados; latencia en milisegundos NO_VERIFICADA. |
| L6 Synthetic Exergy | Datos sintéticos, destilación y RLAIF | Son técnicas distintas; RLAIF aprende de preferencias de IA [6], no equivale por definición a destilar un maestro. |
| L7 Swarm Exergy | Trabajo paralelo y revisión | Diseño; consenso entre LLMs no demuestra BFT ni independencia de errores. |
| L8 Physical Exergy | Control mediante visión, lenguaje y acciones | Torque y energía requieren actuadores, unidades y medición; los tokens no son energía mecánica. |

En todas las capas, «exergía», «anergía», «colapso del AST» y «autolisis» son metáforas salvo un modelo físico explícito. La temperatura de muestreo no es temperatura en kelvin; decodificar con temperatura cero no aporta verdad ni garantiza reproducibilidad entre implementaciones.

## 2. Entropía de tokens: corrección matemática

**Definiciones.** Sea un vocabulario finito Σ, de cardinal m ≥ 1, y un contexto fijo c. Para un historial u de probabilidad positiva e índice i:

$$p_i(a\mid u,c)=P(T_i=a\mid T_{<i}=u,C=c),\qquad a\in\Sigma,$$
$$h_i(u,c)=-\sum_{a\in\Sigma}p_i(a\mid u,c)\log_2 p_i(a\mid u,c),\qquad 0\log_2 0:=0.$$

La suma recorre el vocabulario, no las posiciones de una secuencia observada. Definimos el **déficit de entropía respecto a la uniforme**, en bits por token:

$$\xi_i(u,c):=\log_2 m-h_i(u,c).$$

**Resultado matemático**, para una distribución normalizada sobre ese vocabulario:

$$0\le h_i(u,c)\le\log_2 m,\qquad 0\le\xi_i(u,c)\le\log_2 m.$$

Se obtiene de la no negatividad de la divergencia KL respecto a la uniforme U: $D_{\mathrm{KL}}(p_i\Vert U)=\log_2 m-h_i$. No es un teorema nuevo de exergía ni una medida de exactitud [1].

Para longitud fija N ≥ 1, la regla de la cadena exige promediar también sobre los historiales:

$$H(T_{1:N}\mid C=c)=\sum_{i=1}^{N}\mathbb E_{T_{<i}\mid c}[h_i(T_{<i},c)],$$
$$\bar\xi(c):=\log_2 m-\frac{H(T_{1:N}\mid C=c)}{N}.$$

No se compara una entropía de secuencia con un máximo por token sin dividir por N. Longitudes variables requieren modelar terminación y longitud. La sorpresa de una secuencia concreta es $-\log_2 P(t_{1:N}\mid c)$, no su entropía.

La perplejidad de la distribución es $2^{H(T_{1:N}\mid c)/N}$. La estimación usual en un corpus usa entropía cruzada, $\widehat L=-N^{-1}\sum_i\log_2 q(t_i\mid t_{<i},c)$ y $\widehat{\mathrm{PPL}}=2^{\widehat L}$; no debe confundirse con la entropía propia de q ni hereda su cota superior $\log_2 m$.

**Contraejemplo a «menos entropía implica más verdad».** Sobre dos respuestas, un modelo que siempre emite la incorrecta tiene h = 0 y ξ = 1 bit; un modelo uniforme tiene h = 1 y ξ = 0, y acierta la mitad de las veces. Tampoco un aumento de entropía demuestra degradación. Condicionar reduce entropía *en promedio* para variables con distribución conjunta fija; no necesariamente para cada contexto, ni al cambiar modelo o prompt.

### Separación física

La exergía física es trabajo útil máximo respecto a un entorno de referencia y se expresa en julios. El déficit anterior se expresa en bits. Bajo el modelo ideal de borrado isotermo de un bit inicialmente equiprobable, el límite de Landauer es $Q_{\mathrm{bath}}\ge k_B T_{\mathrm{bath}}\ln 2$ [2]. No es el coste de producir un token ni identifica ξ con trabajo extraíble. No se han medido aquí julios por token, potencia, temperatura física ni ciclos de borrado.

## 3. Datos sintéticos y «Slop Horizon»

**Evidencia publicada acotada.** Shumailov et al. muestran degradación bajo regímenes de entrenamiento recursivo y pérdida de colas de distribución [3]. Gerstgrasser et al. encuentran que acumular datos reales y sintéticos puede evitar el colapso en los escenarios estudiados [4]. No se deriva una ley universal sobre todo dato sintético.

**Se retira como teorema** $\Xi(1\,\mathrm{TB\ auditado})\gg\Xi(10\,\mathrm{TB\ no\ auditado})$: faltan distribución, tarea y definición de Ξ para corpus. «Slop Horizon» queda como metáfora de degradación, sin umbral demostrado. Auditar no ordena automáticamente la entropía ni la utilidad.

**Hipótesis contrastable.** A igual arquitectura, tokenizador y presupuesto de entrenamiento, comparar corpus versionados sobre tareas externas preregistradas. Publicar procedencia, mezcla real/sintética, semillas, intervalos de incertidumbre, cobertura de casos raros y coste. La hipótesis de superioridad de la curación falla si no mejora la métrica primaria según el criterio fijado antes del experimento. No se ejecutó ese experimento en esta revisión.

## 4. Enjambres y control de concurrencia

**Propuesta**, sin atribución acreditada a «Kimi K3»: descomponer tareas, limitar trabajadores, validar resultados y medir coste. No hay evidencia en este compendio de un scheduler instalado ni de comportamiento BFT.

- $P\times S\le n_{\mathrm{cores}}$ puede ser una política inicial para cargas CPU homogéneas; no es una ley ni una garantía contra thrashing. GPU, memoria, I/O y heterogeneidad requieren presupuestos propios. Un semáforo solo limita si el programa lo aplica.
- Dormir 2,8 s no ejecuta búsqueda Monte Carlo ni colapsa caminos; el supuesto efecto MCTS se retira. MCTS necesita estados, selección, expansión, evaluación y actualización.
- `ru_nivcsw > 2132` no es un umbral universal. Requiere plataforma, intervalo o tasa, carga de referencia y medición de latencia, fallos de página y memoria. Aborto automático: NO_VERIFICADO.
- Un patrón proposer/validator no aporta por sí mismo tolerancia bizantina: hacen falta modelo de fallos, protocolo, supuestos y prueba de seguridad/vivacidad.

## 5. LEARN — SHIP — ITERATE

**Heurística de producto.** Identificar un problema medible, preparar un cambio revisable, validarlo y evaluar su efecto. Una publicación no prueba utilidad ni corrección; escribir en disco no convierte semántica en exergía física. Release pública y `SIGKILL` no son obligaciones científicas ni instrucciones de esta revisión. Los efectos se rigen por la autorización y los contratos de BABYLON-60.

## 6. Escalabilidad: índices propuestos y resultados condicionales

Se conserva la propuesta local de separar producto y agente. **Definiciones de índices**, no leyes empíricas:

$$S_{\mathrm{producto}}:=E_t E_e M_i S_f,\qquad S_{\mathrm{agente}}:=Q E_t E_e S_f.$$

Para un índice adimensional comparable deben fijarse escalas de referencia positivas y normalización; no mezclar elasticidades, moneda y probabilidades sin declararlo. Los factores no se vuelven independientes al multiplicarlos y su producto no es una probabilidad conjunta sin condiciones adicionales. El producto es una elección de agregación; una regla de mínimo $\min_j x_j$ es otra y no es algebraicamente equivalente.

| Factor | Definición operativa propuesta y dominio |
| --- | --- |
| Q | $n^{-1}\sum_{j=1}^{n}\mathbf1[\mathrm{oráculo\ acepta\ tarea}_j]$, n > 0; conjunto fijo, fallos incluidos y alcance del oráculo declarado. No prueba corrección total. |
| $E_t$ | Capacidad verificada por recurso, dividida por referencia fija; especificar carga y recurso. No confundir esta razón con elasticidad. |
| $E_e$ | $[V/(C_{\mathrm{inf}}+\lambda_t t)]/r_0$ con denominador y referencia $r_0$ positivos; λ convierte tiempo a unidades de coste. El inverso del coste sin V no mide valor/coste. |
| $M_i$ | $(\Delta R-\Delta C)/\Delta R$ para ΔR > 0. Puede ser negativo: un índice positivo/logarítmico exige restringir el dominio o declarar otra transformación. |
| $S_f$ | Probabilidad estimada de éxito sin fallo crítico en horizonte, carga y modelo de amenaza explícitos; informar incertidumbre. Un recibo firmado no estima esta probabilidad. |

**Demostrado algebraicamente.** Un factor exactamente cero anula un producto finito. Un factor que *tiende* a cero solo fuerza el límite cero si el producto de los demás permanece acotado; $x\,(1/x)=1$ para x > 0 es contraejemplo a la afirmación original sin esa condición.

Para factores positivos diferenciables respecto a N > 0:

$$\frac{d\ln S_{\mathrm{producto}}}{d\ln N}=\varepsilon_{E_t}+\varepsilon_{E_e}+\varepsilon_{M_i}+\varepsilon_{S_f},\qquad \varepsilon_x:=\frac{N x'(N)}{x(N)}.$$

Para el agente se sustituye $\varepsilon_{M_i}$ por $\varepsilon_Q$. La suma original de seis elasticidades requiere **otro índice** explícito, por ejemplo con factores positivos normalizados a una referencia fija:

$$J(N):=\frac{\widetilde{\mathrm{Cap}}\,\widetilde V\,\widetilde F}{\widetilde C\,\widetilde K\,\widetilde R},\qquad
\frac{d\ln J}{d\ln N}=\varepsilon_{\mathrm{Cap}}+\varepsilon_V+\varepsilon_F-\varepsilon_C-\varepsilon_K-\varepsilon_R.$$

Aquí F = fiabilidad, K = complejidad y R = riesgo. Definirlos sin doble conteo es una obligación metodológica, no un resultado. La identidad se deduce por logaritmos; la desigualdad > 0 es un **criterio propuesto de mejora local de J**, no una ley universal de escalado ni una predicción demostrada. Para N discreto usar diferencias logarítmicas entre dos escalas positivas distintas.

La USL de Gunther [7], $U(N)=N/[1+\sigma(N-1)+\kappa N(N-1)]$, es un modelo de capacidad con parámetros de contención/coherencia que requieren ajuste y validación. No prueba los índices económicos anteriores. `SharedManifest`, `SpscRingBuffer`, `KudurruBudgetGate`, SCITT/COSE y NEMESIS son referencias de diseño heredadas, no evidencia de rendimiento, márgenes, confinamiento o fiabilidad medida en esta revisión.

## 7. Verificación formal acotada: Lean 4

El bloque siguiente es autocontenido, sin Mathlib. **Demuestra únicamente** conservación, cotas y antitonicidad de una resta de presupuestos naturales bajo las hipótesis indicadas, y un contraejemplo discreto que separa déficit y etiqueta de corrección. La resta de naturales trunca a cero; `within` evita interpretar un exceso como déficit válido.

Es un modelo discreto auxiliar: no calcula entropía Shannon, logaritmos, KL ni sus cotas reales, no prueba la derivada anterior y no establece una correspondencia con runtime. Esas fórmulas se justifican matemáticamente en el texto y sus fuentes, no mediante este bloque. Se eliminan `token_exergy_theorem` y `slop_horizon_inequality` como axiomas científicos; declarar una proposición con `axiom` no la demuestra.

```lean
import Lean
set_option warningAsError true

namespace Babylon60.Theory.C5ThermodynamicInvariantsCompendium

-- Modelo discreto: unidades enteras de presupuesto, no entropía real.
def gap (budget entropy : Nat) : Nat := budget - entropy

theorem gap_conservation (b h : Nat) (within : h ≤ b) :
    gap b h + h = b := by
  exact Nat.sub_add_cancel within

theorem gap_bounds (b h : Nat) :
    0 ≤ gap b h ∧ gap b h ≤ b := by
  exact ⟨Nat.zero_le _, Nat.sub_le b h⟩

theorem gap_antitone (b h₁ h₂ : Nat)
    (ordered : h₁ ≤ h₂) :
    gap b h₂ ≤ gap b h₁ := by
  exact Nat.sub_le_sub_left ordered b

-- Un déficit alto no implica corrección: etiqueta externa independiente.
def correct (answer : Bool) : Prop := answer = true

theorem gap_does_not_certify_truth :
    gap 1 0 = 1 ∧ ¬ correct false := by
  exact ⟨rfl, Bool.noConfusion⟩

/-- info: 'Babylon60.Theory.C5ThermodynamicInvariantsCompendium.gap_conservation' depends on axioms: [propext] -/
#guard_msgs in
#print axioms gap_conservation
/-- info: 'Babylon60.Theory.C5ThermodynamicInvariantsCompendium.gap_bounds' does not depend on any axioms -/
#guard_msgs in
#print axioms gap_bounds
/-- info: 'Babylon60.Theory.C5ThermodynamicInvariantsCompendium.gap_antitone' depends on axioms: [propext] -/
#guard_msgs in
#print axioms gap_antitone
/-- info: 'Babylon60.Theory.C5ThermodynamicInvariantsCompendium.gap_does_not_certify_truth' does not depend on any axioms -/
#guard_msgs in
#print axioms gap_does_not_certify_truth

end Babylon60.Theory.C5ThermodynamicInvariantsCompendium
```

Reproducir: extraer este único bloque a un archivo y ejecutar `lean <archivo.lean>`. Los cuatro `#guard_msgs` fijan las dependencias exactas: `gap_conservation` y `gap_antitone` dependen de `propext` (extensionalidad proposicional de Lean); los otros dos no dependen de axiomas. No hay axiomas científicos añadidos, `sorryAx` ni `Classical.choice`. Resultado local: Lean 4.35.0, compilación sin errores el 2026-10-24. No se infiere de ello una certificación del resto del corpus.

## 8. Fuentes primarias y trazabilidad

1. C. E. Shannon (1948), *A Mathematical Theory of Communication*, Bell System Technical Journal 27, 379–423, 623–656. [DOI y artículo](https://doi.org/10.1002/j.1538-7305.1948.tb01338.x). Entropía, no veracidad semántica.
2. R. Landauer (1961), *Irreversibility and Heat Generation in the Computing Process*, IBM J. Res. Dev. 5, 183–191. [DOI](https://doi.org/10.1147/rd.53.0183). Borrado físico bajo condiciones específicas.
3. I. Shumailov et al. (2024), *AI models collapse when trained on recursively generated data*, Nature 631, 755–759. [Artículo](https://doi.org/10.1038/s41586-024-07566-y), [corrección de 2025](https://doi.org/10.1038/s41586-025-08905-3). Regímenes recursivos estudiados.
4. M. Gerstgrasser et al. (2024), *Is Model Collapse Inevitable? Breaking the Curse of Recursion by Accumulating Real and Synthetic Data*. [Preprint v2](https://arxiv.org/abs/2404.01413v2). Acumulación frente a sustitución.
5. P. Lewis et al. (2020), *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*, NeurIPS. [Artículo](https://arxiv.org/abs/2005.11401). Evaluación de RAG en tareas específicas.
6. Y. Bai et al. (2022), *Constitutional AI: Harmlessness from AI Feedback*. [Preprint](https://arxiv.org/abs/2212.08073). Procedimiento RLAIF.
7. N. J. Gunther (2008), *A General Theory of Computational Scalability Based on Rational Functions*. [Preprint v2](https://arxiv.org/abs/0808.1431v2). Modelo de escalabilidad computacional.

Alcance: revisión documental y formal local; sin experimento de entrenamiento, benchmark de hardware, verificación de modelos comerciales ni telemetría global. La declaración histórica de «VERIFICADO» para este compendio queda sustituida por el alcance explícito de esta versión.
