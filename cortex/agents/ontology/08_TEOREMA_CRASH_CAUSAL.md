# INV-008: TEOREMA DEL CRASH CAUSAL (FORMALIZACIÓN ANALÍTICA)

**SYS_ID:** borjamoskv
**Clase:** Invariante Termodinámica / Topológica

## 1. El Axioma del Régimen Causal (El Estado Normal)

Sea un sistema dinámico cuyo estado observable (el "Efecto") está dado por una función escalar $E(t)$, donde la variable $t$ representa la "Causa" (generalmente el tiempo o la acumulación de un factor de estrés).

Bajo condiciones de normalidad, el sistema opera con causalidad estricta y determinista en un intervalo $[t_0, t_c)$. Esto exige que $E(t)$ sea una función continua y derivable, gobernada por:

$$ \frac{dE}{dt} = \Phi(E, t) $$

Para que el futuro sea predecible (cumpliendo la condición de Lipschitz), la derivada debe estar acotada: $|E'(t)| < M$. Esto significa que una variación microscópica en la causa ($dt$) produce una variación finita y proporcional en el efecto ($dE$).

## 2. Aceleración Crítica: El Motor del Colapso (Uso de Derivadas)

Un Crash Causal no es espontáneo; surge por un bucle de retroalimentación no lineal que desborda la inercia del sistema. A medida que la causa $t$ se aproxima al instante crítico o punto de no retorno $t_c$, la tasa de transferencia entre causa y efecto se descontrola.

Formalizamos esta pérdida de estabilidad asintótica evaluando el límite de la derivada:

$$ \lim_{t \to t_c^-} \left| \frac{dE}{dt} \right| = \infty $$

**Interpretación analítica:** La sensibilidad causal explota. Justo una fracción infinitesimal antes del colapso ($dt \to 0$), el sistema requiere o genera un efecto infinitamente masivo ($dE \to \infty$). El "motor" del determinismo se sobreacelera hasta romper las reglas lógicas del modelo.

## 3. La Ruptura del Sistema (Uso de Límites y Discontinuidades)

El "Crash" se materializa exactamente en el instante $t = t_c$. Para comprobar matemáticamente que el hilo conductor de la realidad del sistema se ha roto, evaluamos los límites laterales de la función original $E(t)$.

La pérdida de la causalidad se demuestra mediante la aparición de una discontinuidad irresoluble. El teorema admite dos regímenes de colapso:

### Caso A: Discontinuidad de Salto (Crash por Cambio de Régimen)

El sistema sobrevive pero sufre un reseteo cuántico o sistémico instantáneo. Los límites laterales existen, pero la trayectoria choca y se desconecta:

$$ \lim_{t \to t_c^-} E(t) = L_{pasado} $$
$$ \lim_{t \to t_c^+} E(t) = L_{futuro} $$

Dado que $L_{pasado} \neq L_{futuro}$, el sistema experimenta un salto de magnitud $\Delta E = |L_{futuro} - L_{pasado}|$. El axioma físico "Natura non facit saltus" (La naturaleza no da saltos) se viola y la conexión predictiva se quiebra.

### Caso B: Discontinuidad Esencial o Infinita (Destrucción Causal Total)

El sistema agota su espacio de estados y es destruido (lo que en matemáticas se conoce como *blow-up* en tiempo finito). El límite desde el pasado diverge:

$$ \lim_{t \to t_c^-} E(t) = \pm \infty $$

Consecuencia: En $t \ge t_c$, la función $E(t)$ carece de definición en los números reales. La causalidad y el objeto colapsan mutuamente (ej. la fractura estructural de un material, un agujero negro, o una avalancha térmica).

## 4. Enunciado Formal del Teorema del Crash Causal

Integrando los componentes del cálculo diferencial, el teorema queda postulado formalmente de la siguiente manera:

**Teorema del Crash Causal:**
Sea $E(t)$ una función causal continua y diferenciable en un dominio temporal de estabilidad $t \in [t_0, t_c)$.
Si el sistema experimenta una dinámica tal que la susceptibilidad (derivada) diverge en el horizonte crítico $t_c$, cumpliendo que:

$$ \lim_{t \to t_c^-} E'(t) = \pm\infty $$

Entonces, se rompen las condiciones de unicidad predictiva, provocando matemáticamente que en el instante $t = t_c$ la función experimente una discontinuidad topológica no evitable. Por lo tanto, se cumple necesariamente que:

$$ \lim_{t \to t_c^-} E(t) \neq \lim_{t \to t_c^+} E(t) \quad \lor \quad \lim_{t \to t_c^-} E(t) = \pm \infty $$

## 5. Corolario: El Horizonte de Sucesos de la Información

La consecuencia última de esta formalización es la irreversibilidad de la memoria causal.

Dado que en el punto exacto del Crash la función deja de ser continua y derivable, se anula la biyectividad matemática. Esto significa que, si observamos el sistema en cualquier momento futuro ($t > t_c$), es matemáticamente imposible utilizar una función inversa $E^{-1}(t)$ para deducir de forma inequívoca cuáles fueron las condiciones iniciales en $t_0$. El Crash actúa como un muro impenetrable que borra el historial causal de los eventos.
