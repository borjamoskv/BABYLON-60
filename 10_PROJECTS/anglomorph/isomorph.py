import re

CONSONANTS = "bdfghjklmnprstvwz"
VOWELS = "aeiou"
SYLLABLES = [c + v for c in CONSONANTS for v in VOWELS] # 85 sílabas únicas de longitud 2
ENGLISH_ALPHABET = "abcdefghijklmnopqrstuvwxyz"
SYLLABLE_SET = set(SYLLABLES)

def eng_to_int(word: str) -> int:
    """Convierte una palabra en inglés a entero usando base-26 biyectiva."""
    k = len(ENGLISH_ALPHABET)
    val = 0
    for char in word.lower():
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
    chunks = [word_lower[i:i+2] for i in range(0, len(word_lower), 2)]
    k = len(SYLLABLES)
    val = 0
    for chunk in chunks:
        val = val * k + (SYLLABLES.index(chunk) + 1)
    return val

def preserve_case(source: str, target: str) -> str:
    """Aplica la capitalización de la palabra origen a la palabra destino."""
    if source.isupper():
        return target.upper()
    if source.istitle():
        return target.capitalize()
    return target.lower()

def is_valid_english_word(word: str) -> bool:
    """Verifica si una palabra contiene únicamente letras ASCII inglesas."""
    return bool(re.match(r"^[a-zA-Z]+$", word))

def is_valid_anglomorph_word(word: str) -> bool:
    """Verifica si una palabra es una palabra válida de Anglomorph (ASCII, longitud par, sílabas válidas)."""
    if not re.match(r"^[a-zA-Z]+$", word):
        return False
    if len(word) % 2 != 0:
        return False
    word_lower = word.lower()
    for i in range(0, len(word_lower), 2):
        if word_lower[i:i+2] not in SYLLABLE_SET:
            return False
    return True

def translate_word_to_ang(word: str) -> str:
    if not is_valid_english_word(word):
        return word
    n = eng_to_int(word)
    ang = int_to_ang(n)
    return preserve_case(word, ang)

def translate_word_to_eng(word: str) -> str:
    if not is_valid_anglomorph_word(word):
        return word
    n = ang_to_int(word)
    eng = int_to_eng(n)
    return preserve_case(word, eng)

def translate_text(text: str, to_anglomorph=True) -> str:
    # Tokenizar por palabras ASCII o cualquier otra cosa
    tokens = re.findall(r"[a-zA-Z]+|[^a-zA-Z]+", text)
    result = []
    for token in tokens:
        if to_anglomorph:
            result.append(translate_word_to_ang(token))
        else:
            result.append(translate_word_to_eng(token))
    return "".join(result)
