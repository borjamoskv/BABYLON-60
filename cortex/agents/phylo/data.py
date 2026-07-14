"""Romance cognate dataset and Latin gold standard for phylogenetic validation."""

from __future__ import annotations

# Tokens separados por espacio. Mayúsculas = 1 segmento:
# S=ʃ  Z=ʒ  C=tʃ  G=dʒ  J=ɲ  L=ʎ ; j,w = glides ; y = vocal ant. redondeada

GOLD: dict[str, str] = {
    "key": "k l a v e",
    "night": "n o k t e",
    "eight": "o k t o",
    "milk": "l a k t e",
    "to_do": "f a k e r e",
    "fire": "f o k u",
    "hundred": "k e n t u",
    "moon": "l u n a",
    "sea": "m a r e",
    "flower": "f l o r e",
    "to_sing": "k a n t a r e",
    "dog": "k a n e",
    "to_have": "h a b e r e",
    "water": "a k w a",
    "to_die": "m o r i r e",
    "name": "n o m e n",
    "new": "n o v u",
    "to_love": "a m a r e",
}

DAUGHTERS: dict[str, dict[str, str]] = {
    "key": {"es": "L a v e", "pt": "S a v e", "fr": "k l e", "it": "k j a v e", "ro": "k e j e", "sc": "k r a e"},
    "night": {"es": "n o C e", "pt": "n o j t e", "fr": "n w i", "it": "n o t e", "ro": "n o a p t e", "sc": "n o t e"},
    "eight": {"es": "o C o", "pt": "o j t o", "fr": "w i t", "it": "o t o", "ro": "o p t", "sc": "o t o"},
    "milk": {"es": "l e C e", "pt": "l e j t e", "fr": "l e", "it": "l a t e", "ro": "l a p t e", "sc": "l a t e"},
    "to_do": {"es": "a s e r", "pt": "f a z e r", "fr": "f e r", "it": "f a r e", "ro": "f a C e"},
    "fire": {"es": "f w e g o", "pt": "f o g o", "it": "f w o k o", "ro": "f o k", "sc": "f o g u"},
    "hundred": {"es": "s j e n", "fr": "s a n", "it": "C e n t o", "ro": "s u t e"},
    "moon": {"es": "l u n a", "pt": "l u a", "fr": "l y n", "it": "l u n a", "ro": "l u n a", "sc": "l u n a"},
    "sea": {"es": "m a r", "pt": "m a r", "fr": "m e r", "it": "m a r e", "ro": "m a r e", "sc": "m a r e"},
    "flower": {"es": "f l o r", "pt": "f l o r", "it": "f j o r e", "ro": "f l o a r e"},
    "to_sing": {"es": "k a n t a r", "pt": "k a n t a r", "fr": "S a n t e", "it": "k a n t a r e", "ro": "k a n t a"},
    "dog": {"es": "k a n", "fr": "S j e n", "it": "k a n e", "ro": "k a i n e", "sc": "k a n e"},
    "to_have": {"es": "a b e r", "pt": "a v e r", "fr": "a v w a r", "it": "a v e r e", "ro": "a v e a"},
    "water": {"es": "a g w a", "pt": "a g w a", "it": "a k w a", "ro": "a p e", "sc": "a b a"},
    "to_die": {"es": "m o r i r", "pt": "m o r e r", "fr": "m u r i r", "it": "m o r i r e", "ro": "m u r i"},
    "name": {"es": "n o m b r e", "pt": "n o m e", "fr": "n o n", "it": "n o m e", "ro": "n u m e"},
    "new": {"es": "n w e v o", "pt": "n o v o", "it": "n w o v o", "ro": "n o u", "sc": "n o b u"},
    "to_love": {"es": "a m a r", "pt": "a m a r", "fr": "e m e", "it": "a m a r e", "ro": "a m a"},
}
