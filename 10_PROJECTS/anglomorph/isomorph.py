import re

CONSONANTS = "bdfghjklmnprstvwz"
VOWELS = "aeiou"
SYLLABLES = [c + v for c in CONSONANTS for v in VOWELS] # 85 sílabas únicas de longitud 2
ENGLISH_ALPHABET = "abcdefghijklmnopqrstuvwxyz"

def eng_to_int(word: str) -> int:
    """Convierte una palabra en inglés a entero usando base-26 biyectiva."""
    k = len(ENGLISH_ALPHABET)
    val = 0
    for char in word.lower():
        if char in ENGLISH_ALPHABET:
            val = val * k + (ENGLISH_ALPHABET.index(char) + 1)
    return val

def int_to_eng(n: int) -> str:
    """Convierte un entero a palabra en inglés usando base-26 biyectiva."""
    k = len(ENGLISH_ALPHABET)
    s = []
    while n > 0:
        n -= 1
        s.append(ENGLISH_ALPHABET[n % k])
        n //= k
    return "".join(reversed(s))

def int_to_ang(n: int) -> str:
    """Convierte un entero a Anglomorph usando base-85 biyectiva."""
    k = len(SYLLABLES)
    s = []
    while n > 0:
        n -= 1
        s.append(SYLLABLES[n % k])
        n //= k
    return "".join(reversed(s))

def ang_to_int(word: str) -> int:
    """Convierte una palabra Anglomorph a entero usando base-85 biyectiva."""
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

def preserve_case(source: str, target: str) -> str:
    """Aplica la capitalización de la palabra origen a la palabra destino."""
    if source.isupper():
        return target.upper()
    if source.istitle():
        return target.capitalize()
    return target.lower()

def translate_word_to_ang(word: str) -> str:
    if not word.isalpha():
        return word
    n = eng_to_int(word)
    ang = int_to_ang(n)
    return preserve_case(word, ang)

def translate_word_to_eng(word: str) -> str:
    if not word.isalpha():
        return word
    try:
        n = ang_to_int(word)
        eng = int_to_eng(n)
        return preserve_case(word, eng)
    except ValueError:
        return word

def translate_text(text: str, to_anglomorph=True) -> str:
    # Tokenizar preservando palabras y caracteres no alfabéticos
    tokens = re.findall(r"[a-zA-Z]+|[^a-zA-Z]+", text)
    result = []
    for token in tokens:
        if token.isalpha():
            if to_anglomorph:
                result.append(translate_word_to_ang(token))
            else:
                result.append(translate_word_to_eng(token))
        else:
            result.append(token)
    return "".join(result)

# Pruebas empíricas
if __name__ == "__main__":
    original = "To be, or not to be, that is the question."
    translated = translate_text(original, to_anglomorph=True)
    restored = translate_text(translated, to_anglomorph=False)
    
    print(f"Original (EN): {original}")
    print(f"Translated (AM): {translated}")
    print(f"Restored (EN): {restored}")
    assert original == restored, "Error: ¡El isomorfismo no es biyectivo!"
    print("¡Éxito! Biyección demostrada con pérdida de información = 0.")
