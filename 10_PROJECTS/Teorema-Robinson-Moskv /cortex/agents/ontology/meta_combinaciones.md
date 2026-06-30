# MATRIZ DE META-COMBINACIONES (n=4)

**NIVEL 1: Entidades Aisladas (4)**
- `[A]` Antipatrones
- `[R]` Redundancias
- `[P]` Primitivas de colisión
- `[I]` Invariantes

**NIVEL 2: Intersecciones Duales (6)**
- `[A-R]` Antipatrones + Redundancias (Ruido estructural replicado)
- `[A-P]` Antipatrones + Primitivas (Fallas de diseño que causan bloqueos)
- `[A-I]` Antipatrones + Invariantes (Código basura fosilizado)
- `[R-P]` Redundancias + Primitivas (Duplicación que genera race conditions)
- `[R-I]` Redundancias + Invariantes (Lógica core copiada innecesariamente)
- `[P-I]` Primitivas + Invariantes (Cuellos de botella en el núcleo determinista)

**NIVEL 3: Triadas Complejas (4)**
- `[A-R-P]` Antipatrones + Redundancias + Primitivas (Colapso estocástico por ruido concurrente)
- `[A-R-I]` Antipatrones + Redundancias + Invariantes (Fosilización de deuda técnica distribuida)
- `[A-P-I]` Antipatrones + Primitivas + Invariantes (Fractura térmica en el núcleo BFT)
- `[R-P-I]` Redundancias + Primitivas + Invariantes (Deadlocks en sistemas de alta disponibilidad)

**NIVEL 4: Singularidad Entrópica (1)**
- `[A-R-P-I]` Antipatrones + Redundancias + Primitivas + Invariantes (Degradación absoluta del vector causal)
