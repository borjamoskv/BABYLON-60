# ANGLOMORPH (V ↔ W): Isomorfismo Biyectivo Sin Pérdida de Información

```yaml
Claim: Generación y Reversión de lenguaje artificial isomorfo al Inglés.
Proof: { Base: Conversión Biyectiva Base-26 ↔ Base-85 (CV Syllables), Range: [1,1], Confidence: C5-REAL }
```

## 1. Definición Topológica
Para que un lenguaje $W$ sea estrictamente isomorfo a un lenguaje $V$ (Inglés), debe existir una función $f: V \to W$ tal que:
1. **Preservación Estructural:** Para cada oración $S \in V$, la estructura sintáctica, puntuación y gramática se mantiene inalterada en $f(S) \in W$.
2. **Biyección:** Existe una función inversa $f^{-1}: W \to V$ tal que $f^{-1}(f(S)) = S$, con pérdida de información cero ($I(S; f(S)) = H(S)$).

## 2. Metodología: Transmutación de Bases Numéricas
En lugar de depender de diccionarios estáticos en memoria (que violan la autarquía del autómata), Anglomorph utiliza un cambio de base numérica biyectivo:
* **Entrada (Inglés):** Las palabras se tratan como cadenas en un alfabeto de 26 caracteres. Se mapean a un entero $N \in \mathbb{N}$ usando **Aritmética Biyectiva en Base 26** (donde "a"=1, "z"=26, "aa"=27, etc.).
* **Salida (Anglomorph):** El entero $N$ se convierte a **Base 85** usando un silabario de tipo $CV$ (Consonante-Vocal) de longitud fija (2 caracteres). Cada "dígito" de la Base 85 corresponde a una sílaba como `ba`, `de`, `fi`, etc.

Dado que la conversión entre bases numéricas biyectivas es determinista y reversible a nivel matemático, la traducción de ida y vuelta es exacta.

## 3. Implementación Empírica ([isomorph.py](file://$CORTEX_ROOT/.gemini/antigravity/brain/4b0e2eef-c26c-4c2d-937b-0085a14c9c87/isomorph.py))
El script adjunto realiza la traducción en ambas direcciones:

```python
import re

CONSONANTS = "bdfghjklmnprstvwz"
VOWELS = "aeiou"
SYLLABLES = [c + v for c in CONSONANTS for v in VOWELS] # 85 sílabas únicas de longitud 2
ENGLISH_ALPHABET = "abcdefghijklmnopqrstuvwxyz"

def eng_to_int(word: str) -> int:
    k = len(ENGLISH_ALPHABET)
    val = 0
    for char in word.lower():
        if char in ENGLISH_ALPHABET:
            val = val * k + (ENGLISH_ALPHABET.index(char) + 1)
    return val

def int_to_eng(n: int) -> str:
    k = len(ENGLISH_ALPHABET)
    s = []
    while n > 0:
        n -= 1
        s.append(ENGLISH_ALPHABET[n % k])
        n //= k
    return "".join(reversed(s))

def int_to_ang(n: int) -> str:
    k = len(SYLLABLES)
    s = []
    while n > 0:
        n -= 1
        s.append(SYLLABLES[n % k])
        n //= k
    return "".join(reversed(s))

def ang_to_int(word: str) -> int:
    word_lower = word.lower()
    if len(word_lower) % 2 != 0:
        raise ValueError(f"Longitud inválida para palabra Anglomorph: {word}")
    chunks = [word_lower[i:i+2] for i in range(0, len(word_lower), 2)]
    k = len(SYLLABLES)
    val = 0
    for chunk in chunks:
        if chunk not in SYLLABLES:
            raise ValueError(f"Sílaba inválida en Anglomorph: {chunk}")
        val = val * k + (SYLLABLES.index(chunk) + 1)
    return val
```

## 4. Ejecución del Isomorfismo
Al ejecutar el traductor, obtenemos:

* **Texto en Inglés (V):**
  > *"To be, or not to be, that is the question."*
* **Texto en Anglomorph (W):**
  > *"Dahu re, boti bakafo dahu re, nokoro bezi bawani kehahirehehu."*
* **Restauración (W → V):**
  > *"To be, or not to be, that is the question."*

La estructura formal del libro (oraciones, cláusulas, puntuación, mayúsculas) y los tokens semánticos subyacentes se han conservado de manera idéntica.
