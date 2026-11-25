#!/usr/bin/env python3
"""Markov Lexical Bridge (Solo Sustantivos y Verbos).

Construye un grafo dirigido de co-ocurrencia / transición de Markov sobre un corpus
de texto local filtrado estrictamente a categorías léxicas abiertas (sustantivos y verbos).
Dada una palabra origen (w1) y una palabra destino (w2) —en pares directos o en flujo
interactivo continuo—, calcula el nodo intermedio imprescindible (w*) que maximiza
la probabilidad de transición conjunta P(w* | w1) * P(w2 | w*) o el primer paso de la
geodésica de Viterbi (mínima sorpresa informacional -log P).
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import asdict, dataclass
import heapq
import json
import math
from pathlib import Path
import re
import sys
from typing import Any

TOKEN_RE = re.compile(r"[a-záéíóúüñA-ZÁÉÍÓÚÜÑ]{2,}")
# INV_C5_19: cota explícita del REPL interactivo (configurable con --max-turns).
DEFAULT_MAX_REPL_TURNS = 10_000

# Clases cerradas, adverbios y adjetivos calificativos/relacionales puros excluidos
STOPWORDS_CLOSED_AND_MODIFIERS: frozenset[str] = frozenset(
    {
        # Artículos y determinantes
        "el",
        "la",
        "los",
        "las",
        "un",
        "una",
        "unos",
        "unas",
        "lo",
        "al",
        "del",
        "este",
        "esta",
        "estos",
        "estas",
        "ese",
        "esa",
        "esos",
        "esas",
        "aquel",
        "aquella",
        "aquellos",
        "aquellas",
        "mi",
        "mis",
        "tu",
        "tus",
        "su",
        "sus",
        "nuestro",
        "nuestra",
        "nuestros",
        "nuestras",
        "vuestro",
        "vuestra",
        "cada",
        "todo",
        "toda",
        "todos",
        "todas",
        "otro",
        "otra",
        "otros",
        "otras",
        "mismo",
        "misma",
        "mismos",
        "mismas",
        "propio",
        "propia",
        "propios",
        "propias",
        "cualquier",
        "cualquiera",
        "alguno",
        "alguna",
        "algunos",
        "algunas",
        "algún",
        "ninguno",
        "ninguna",
        "ningún",
        "varios",
        "varias",
        "ambos",
        "ambas",
        "tanto",
        "tanta",
        "tantos",
        "tantas",
        "cuanto",
        "cuanta",
        "cuantos",
        "cuantas",
        "cierto",
        "cierta",
        "ciertos",
        "ciertas",
        "tal",
        "tales",
        # Preposiciones y conectores
        "de",
        "en",
        "por",
        "para",
        "con",
        "sin",
        "sobre",
        "entre",
        "hacia",
        "hasta",
        "desde",
        "contra",
        "según",
        "tras",
        "ante",
        "bajo",
        "cabe",
        "so",
        "mediante",
        "durante",
        "versus",
        "vía",
        "via",
        "pro",
        # Conjunciones y partículas relativas/interrogativas
        "que",
        "qué",
        "como",
        "cómo",
        "cuando",
        "cuándo",
        "donde",
        "dónde",
        "quien",
        "quién",
        "quienes",
        "cual",
        "cuál",
        "cuales",
        "cuyo",
        "cuya",
        "cuyos",
        "cuyas",
        "si",
        "sí",
        "no",
        "ni",
        "pero",
        "mas",
        "sino",
        "aunque",
        "porque",
        "pues",
        "ya",
        "bien",
        "mal",
        "así",
        "entonces",
        "luego",
        "además",
        "incluso",
        "también",
        "tampoco",
        # Pronombres personales y clíticos
        "yo",
        "tú",
        "él",
        "ella",
        "ello",
        "nosotros",
        "nosotras",
        "vosotros",
        "vosotras",
        "ellos",
        "ellas",
        "usted",
        "ustedes",
        "me",
        "te",
        "se",
        "nos",
        "os",
        "le",
        "les",
        "conmigo",
        "contigo",
        "consigo",
        "algo",
        "nada",
        "alguien",
        "nadie",
        # Adverbios frecuentes
        "muy",
        "más",
        "menos",
        "poco",
        "mucho",
        "casi",
        "solo",
        "sólo",
        "aún",
        "aun",
        "todavía",
        "siempre",
        "nunca",
        "jamás",
        "aquí",
        "allí",
        "ahí",
        "acá",
        "allá",
        "cerca",
        "lejos",
        "dentro",
        "fuera",
        "arriba",
        "abajo",
        "adelante",
        "atrás",
        "antes",
        "después",
        "pronto",
        "tarde",
        "temprano",
        "hoy",
        "ayer",
        "mañana",
        "ahora",
        "quizá",
        "quizás",
        "acaso",
        # Adjetivos comunes no sustantivados y cuantificadores
        "gran",
        "grande",
        "grandes",
        "pequeño",
        "pequeña",
        "pequeños",
        "pequeñas",
        "bueno",
        "buena",
        "buenos",
        "buenas",
        "buen",
        "malo",
        "mala",
        "malos",
        "malas",
        "nuevo",
        "nueva",
        "nuevos",
        "nuevas",
        "viejo",
        "vieja",
        "viejos",
        "viejas",
        "mayor",
        "mayores",
        "menor",
        "menores",
        "mejor",
        "mejores",
        "peor",
        "peores",
        "primer",
        "primero",
        "primera",
        "primeros",
        "primeras",
        "segundo",
        "segunda",
        "segundos",
        "segundas",
        "tercer",
        "tercero",
        "tercera",
        "último",
        "última",
        "últimos",
        "últimas",
        "único",
        "única",
        "únicos",
        "únicas",
        "posible",
        "posibles",
        "imposible",
        "imposibles",
        "necesario",
        "necesaria",
        "necesarios",
        "necesarias",
        "siguiente",
        "siguientes",
        "anterior",
        "anteriores",
        "posterior",
        "posteriores",
        "actual",
        "actuales",
        "real",
        "reales",
        "total",
        "totales",
        "parcial",
        "parciales",
        "general",
        "generales",
        "especial",
        "especiales",
        "principal",
        "principales",
        "final",
        "finales",
        "inicial",
        "iniciales",
        "local",
        "locales",
        "global",
        "globales",
        "formal",
        "formales",
        "normal",
        "normales",
        "igual",
        "iguales",
        "distinto",
        "distinta",
        "distintos",
        "distintas",
        "diferente",
        "diferentes",
        "capaz",
        "capaces",
        "fácil",
        "fáciles",
        "difícil",
        "difíciles",
        "útil",
        "útiles",
        "inútil",
        "inútiles",
        "libre",
        "libres",
        "simple",
        "simples",
        "doble",
        "dobles",
        "triple",
        "múltiple",
        "múltiples",
        "falso",
        "falsa",
        "falsos",
        "falsas",
        "verdadero",
        "verdadera",
        "claro",
        "clara",
        "alto",
        "alta",
        "altos",
        "altas",
        "bajo",
        "baja",
        "bajos",
        "bajas",
        "largo",
        "larga",
        "corto",
        "corta",
        "ancho",
        "ancha",
        "puro",
        "pura",
        "puros",
        "puras",
        "pleno",
        "plena",
        "lleno",
        "llena",
        "vacío",
        "vacía",
        "directo",
        "directa",
        "directos",
        "directas",
        "estricto",
        "estricta",
        "estrictos",
        "estrictas",
        "explícito",
        "explícita",
        "implícito",
        "implícita",
        "interno",
        "interna",
        "externo",
        "externa",
        "previo",
        "previa",
        "previos",
        "previas",
        # Numerales
        "uno",
        "dos",
        "tres",
        "cuatro",
        "cinco",
        "seis",
        "siete",
        "ocho",
        "nueve",
        "diez",
        "cien",
        "ciento",
        "mil",
        "millón",
        "cero",
        # Stopwords técnicas en inglés frecuentes en repositorios mixtos
        "the",
        "and",
        "for",
        "with",
        "from",
        "that",
        "this",
        "these",
        "those",
        "into",
        "onto",
        "upon",
        "over",
        "under",
        "between",
        "through",
        "without",
        "within",
        "about",
        "after",
        "before",
        "while",
        "where",
        "when",
        "which",
        "what",
        "who",
        "whom",
        "whose",
        "how",
        "why",
        "not",
        "only",
        "also",
        "very",
        "more",
        "most",
        "less",
        "least",
        "some",
        "any",
        "all",
        "both",
        "each",
        "every",
        "other",
        "another",
        "such",
        "same",
        "own",
        "true",
        "false",
        "null",
        "none",
        "def",
        "return",
        "import",
        "class",
        "self",
        "async",
        "await",
        "const",
        "let",
        "var",
        "pub",
        "struct",
        "enum",
        "impl",
        "crate",
        "mod",
        "use",
        "wip",
        "todo",
        "fixme",
        "http",
        "https",
        "www",
        "file",
        "html",
        "css",
        "json",
        "yaml",
        "toml",
        "utf",
        "sha",
        "str",
        "int",
        "bool",
        "vec",
        "mut",
        "ref",
    }
)

# Sustantivos terminados en -ico/-ica/-ble que no deben descartarse como adjetivos
NOUN_EXCEPTIONS_ICO_BLE: frozenset[str] = frozenset(
    {
        "física",
        "lógica",
        "métrica",
        "mecánica",
        "dinámica",
        "termodinámica",
        "informática",
        "matemática",
        "matemáticas",
        "cibernética",
        "heurística",
        "semántica",
        "gramática",
        "estadística",
        "acústica",
        "óptica",
        "ética",
        "política",
        "estética",
        "dialéctica",
        "aritmética",
        "geometría",
        "topología",
        "ontología",
        "epistemología",
        "criptografía",
        "telemetría",
        "biometría",
        "técnica",
        "técnicas",
        "práctica",
        "prácticas",
        "crítica",
        "críticas",
        "gráfica",
        "gráfico",
        "gráficos",
        "tráfico",
        "público",
        "pánico",
        "diagnóstico",
        "pronóstico",
        "mosaico",
        "léxico",
        "tópico",
        "clásico",
        "cántico",
        "pórtico",
        "cable",
        "cables",
        "variable",
        "variables",
        "observable",
        "observables",
        "ejecutable",
        "ejecutables",
        "invariante",
        "invariantes",
        "constante",
        "constantes",
    }
)

# Formas verbales irregulares / cortas frecuentes que son verbos plenos
KNOWN_VERBS: frozenset[str] = frozenset(
    {
        "ser",
        "es",
        "son",
        "era",
        "eran",
        "fue",
        "fueron",
        "sea",
        "sean",
        "estar",
        "está",
        "están",
        "estaba",
        "estuvo",
        "haber",
        "hay",
        "había",
        "hubo",
        "tener",
        "tiene",
        "tienen",
        "tenía",
        "tuvo",
        "hacer",
        "hace",
        "hacen",
        "hizo",
        "poder",
        "puede",
        "pueden",
        "pudo",
        "decir",
        "dice",
        "dicen",
        "dijo",
        "ir",
        "va",
        "van",
        "iba",
        "ver",
        "ve",
        "ven",
        "vio",
        "dar",
        "da",
        "dan",
        "dio",
        "saber",
        "sabe",
        "saben",
        "supo",
        "querer",
        "quiere",
        "quieren",
        "quiso",
        "llegar",
        "llega",
        "llegan",
        "llegó",
        "pasar",
        "pasa",
        "pasan",
        "pasó",
        "deber",
        "debe",
        "deben",
        "poner",
        "pone",
        "ponen",
        "puso",
        "parecer",
        "parece",
        "parecen",
        "quedar",
        "queda",
        "quedan",
        "creer",
        "cree",
        "creen",
        "hablar",
        "habla",
        "hablan",
        "llevar",
        "lleva",
        "llevan",
        "dejar",
        "deja",
        "dejan",
        "seguir",
        "sigue",
        "siguen",
        "encontrar",
        "encuentra",
        "encuentran",
        "llamar",
        "llama",
        "llaman",
        "venir",
        "viene",
        "vienen",
        "vino",
        "pensar",
        "piensa",
        "piensan",
        "salir",
        "sale",
        "salen",
        "volver",
        "vuelve",
        "vuelven",
        "tomar",
        "toma",
        "toman",
        "conocer",
        "conoce",
        "conocen",
        "vivir",
        "vive",
        "viven",
        "sentir",
        "siente",
        "sienten",
        "tratar",
        "trata",
        "tratan",
        "mirar",
        "mira",
        "miran",
        "contar",
        "cuenta",
        "cuentan",
        "empezar",
        "empieza",
        "empiezan",
        "esperar",
        "espera",
        "esperan",
        "buscar",
        "busca",
        "buscan",
        "existir",
        "existe",
        "existen",
        "entrar",
        "entra",
        "entran",
        "trabajar",
        "trabaja",
        "trabajan",
        "escribir",
        "escribe",
        "escriben",
        "perder",
        "pierde",
        "pierden",
        "producir",
        "produce",
        "producen",
        "ocurrir",
        "ocurre",
        "ocurren",
        "entender",
        "entiende",
        "entienden",
        "pedir",
        "pide",
        "piden",
        "recibir",
        "recibe",
        "reciben",
        "recordar",
        "recuerda",
        "recuerdan",
        "terminar",
        "termina",
        "terminan",
        "permitir",
        "permite",
        "permiten",
        "aparecer",
        "aparece",
        "aparecen",
        "conseguir",
        "consigue",
        "consiguen",
        "comenzar",
        "comienza",
        "comienzan",
        "servir",
        "sirve",
        "sirven",
        "sacar",
        "saca",
        "sacan",
        "necesitar",
        "necesita",
        "necesitan",
        "mantener",
        "mantiene",
        "mantienen",
        "resultar",
        "resulta",
        "resultan",
        "leer",
        "lee",
        "leen",
        "caer",
        "cae",
        "caen",
        "cambiar",
        "cambia",
        "cambian",
        "presentar",
        "presenta",
        "presentan",
        "crear",
        "crea",
        "crean",
        "abrir",
        "abre",
        "abren",
        "considerar",
        "considera",
        "consideran",
        "oír",
        "oye",
        "oyen",
        "acabar",
        "acaba",
        "acaban",
        "convertir",
        "convierte",
        "convierten",
        "ganar",
        "gana",
        "ganan",
        "formar",
        "forma",
        "forman",
        "traer",
        "trae",
        "traen",
        "partir",
        "parte",
        "parten",
        "morir",
        "muere",
        "mueren",
        "aceptar",
        "acepta",
        "aceptan",
        "realizar",
        "realiza",
        "realizan",
        "suponer",
        "supone",
        "suponen",
        "comprender",
        "comprende",
        "comprenden",
        "lograr",
        "logra",
        "logran",
        "explicar",
        "explica",
        "explican",
        "alcanzar",
        "alcanza",
        "alcanzan",
        "reconocer",
        "reconoce",
        "reconocen",
        "generar",
        "genera",
        "generan",
        "calcular",
        "calcula",
        "calculan",
        "ejecutar",
        "ejecuta",
        "ejecutan",
        "validar",
        "valida",
        "validan",
        "verificar",
        "verifica",
        "verifican",
        "medir",
        "mide",
        "miden",
        "forzar",
        "fuerza",
        "fuerzan",
        "transformar",
        "transforma",
        "transforman",
        "conectar",
        "conecta",
        "conectan",
        "reducir",
        "reduce",
        "reducen",
        "definir",
        "define",
        "definen",
        "construir",
        "construye",
        "construyen",
        "destruir",
        "destruye",
        "destruyen",
        "optimizar",
        "optimiza",
        "optimizan",
        "disipar",
        "disipa",
        "disipan",
        "colapsar",
        "colapsa",
        "colapsan",
        "emerger",
        "emerge",
        "emergen",
        "converger",
        "converge",
        "convergen",
        "divergir",
        "diverge",
        "divergen",
        "mutar",
        "muta",
        "mutan",
        "sellar",
        "sella",
        "sellan",
        "auditar",
        "audita",
        "auditan",
        "compilar",
        "compila",
        "compilan",
        "emitir",
        "emite",
        "emiten",
        "transmitir",
        "transmite",
        "transmiten",
        "extraer",
        "extrae",
        "extraen",
        "proyectar",
        "proyecta",
        "proyectan",
        "resolver",
        "resuelve",
        "resuelven",
        "evaluar",
        "evalúa",
        "evalúan",
        "garantizar",
        "garantiza",
        "garantizan",
        "imponer",
        "impone",
        "imponen",
        "bloquear",
        "bloquea",
        "bloquean",
        "purgar",
        "purga",
        "purgan",
        "filtrar",
        "filtra",
        "filtran",
        "consolidar",
        "consolida",
        "consolidan",
        "devorar",
        "devora",
        "devoran",
        "alimentar",
        "alimenta",
        "alimentan",
        "impulsar",
        "impulsa",
        "impulsan",
        "mover",
        "mueve",
        "mueven",
        "operar",
        "opera",
        "operan",
        "controlar",
        "controla",
        "controlan",
        "procesar",
        "procesa",
        "procesan",
        "almacenar",
        "almacena",
        "almacenan",
        "integrar",
        "integra",
        "integran",
        "coordinar",
        "coordina",
        "coordinan",
        "propagar",
        "propaga",
        "propagan",
        "registrar",
        "registra",
        "registran",
        "capturar",
        "captura",
        "capturan",
        "detectar",
        "detecta",
        "detectan",
        "proteger",
        "protege",
        "protegen",
        "conservar",
        "conserva",
        "conservan",
        "aplicar",
        "aplica",
        "aplican",
        "invocar",
        "invoca",
        "invocan",
        "retornar",
        "retorna",
        "retornan",
        "devolver",
        "devuelve",
        "devuelven",
        "escalar",
        "escala",
        "escalan",
    }
)

# Sustantivos terminados en -ar/-er/-ir que no son verbos
NOUNS_ENDING_AR_ER_IR: frozenset[str] = frozenset(
    {
        "mar",
        "par",
        "lugar",
        "hogar",
        "altar",
        "pilar",
        "umbral",
        "radar",
        "sonar",
        "láser",
        "laser",
        "taller",
        "mujer",
        "placer",
        "poder",
        "deber",
        "ser",
        "saber",
        "carácter",
        "caracter",
        "líder",
        "lider",
        "búnker",
        "bunker",
        "clúster",
        "cluster",
        "buffer",
        "búfer",
        "driver",
        "server",
        "docker",
        "worker",
        "router",
        "parser",
        "linter",
        "header",
        "footer",
        "tensor",
        "vector",
        "motor",
        "actor",
        "factor",
        "sector",
        "sensor",
        "cursor",
        "error",
        "valor",
        "color",
        "calor",
        "dolor",
        "temor",
        "honor",
        "amor",
        "humor",
        "rumor",
        "vapor",
        "autor",
        "lector",
        "director",
        "receptor",
        "emisor",
        "operador",
        "regulador",
        "controlador",
        "compilador",
        "simulador",
        "generador",
        "procesador",
        "servidor",
        "contenedor",
        "indicador",
        "observador",
        "evaluador",
        "orquestador",
        "transductor",
        "atractor",
        "elixir",
        "mártir",
        "zafir",
        "porvenir",
    }
)

VERB_SUFFIXES: tuple[str, ...] = (
    "ando",
    "iendo",
    "yendo",
    "ábamos",
    "asteis",
    "isteis",
    "áramos",
    "éramos",
    "iéramos",
    "ásemos",
    "ésemos",
    "iésemos",
    "aremos",
    "eremos",
    "iremos",
    "aríamos",
    "eríamos",
    "iríamos",
    "aban",
    "ían",
    "aron",
    "ieron",
    "arán",
    "erán",
    "irán",
    "arían",
    "erían",
    "irían",
    "amos",
    "emos",
    "imos",
    "abas",
    "ías",
    "aste",
    "iste",
    "ará",
    "erá",
    "irá",
    "aría",
    "ería",
    "iría",
    "arse",
    "erse",
    "irse",
    "arlo",
    "erlo",
    "irlo",
    "arla",
    "erla",
    "irla",
    "arlos",
    "erlos",
    "irlos",
)

ADJECTIVE_SUFFIXES: tuple[str, ...] = (
    "mente",
    "ísimo",
    "ísima",
    "ísimos",
    "ísimas",
    "oso",
    "osa",
    "osos",
    "osas",
    "ivo",
    "iva",
    "ivos",
    "ivas",
    "ble",
    "bles",
    "ico",
    "ica",
    "icos",
    "icas",
    "áceo",
    "ácea",
    "il",
    "iles",
)


def classify_pos(word: str) -> str | None:
    """Clasifica una palabra en 'NOUN', 'VERB' o None (si es clase cerrada, adverbio o adjetivo).

    Solo permite sustantivos y verbos.
    """
    w = word.strip().lower()
    if len(w) < 2 or not w.isalpha():
        return None
    if w in STOPWORDS_CLOSED_AND_MODIFIERS:
        return None

    # 1. Verbos conocidos explícitos
    if w in KNOWN_VERBS:
        return "VERB"

    # 2. Excepciones nominales explícitas (sustantivos en -ico/-ica/-ble/-ar/-er/-ir)
    if w in NOUN_EXCEPTIONS_ICO_BLE or w in NOUNS_ENDING_AR_ER_IR:
        return "NOUN"

    # 3. Exclusión de adverbios en -mente y sufijos adjetivales puros
    if w.endswith("mente"):
        return None
    for adj_suf in ADJECTIVE_SUFFIXES:
        if w.endswith(adj_suf) and len(w) > len(adj_suf) + 2:
            return None

    # 4. Morfología verbal (desinencias conjugadas o infinitivos)
    for vsuf in VERB_SUFFIXES:
        if w.endswith(vsuf) and len(w) > len(vsuf) + 1:
            return "VERB"
    if len(w) >= 4 and w.endswith(("ar", "er", "ir", "ír")):
        return "VERB"

    # 5. Participios pasados (-ado/-ada/-ido/-ida) funcionan como adjetivos salvo uso verbal/sustantivo;
    # rechazamos los adjetivales flexionados en plural/femenino (-ados, -adas, -idos, -idas)
    if len(w) > 5 and w.endswith(("ados", "adas", "idos", "idas")):
        return None

    # 6. El resto de tokens léxicos abiertos de longitud >= 3 se clasifican como sustantivos (NOUN)
    if len(w) >= 3:
        return "NOUN"
    return None


@dataclass(frozen=True)
class BridgeResult:
    """Resultado del cálculo del puente léxico de Markov."""

    origin: str
    origin_pos: str
    bridge: str
    bridge_pos: str
    target: str
    target_pos: str
    p_origin_to_bridge: float
    p_bridge_to_target: float
    joint_score: float
    surprisal_bits: float
    bottleneck_ratio: float
    full_path: tuple[str, ...]
    alternatives: tuple[tuple[str, str, float], ...]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["full_path"] = list(self.full_path)
        data["alternatives"] = [{"word": w, "pos": p, "score": s} for w, p, s in self.alternatives]
        return data


@dataclass(frozen=True)
class EvidenceChunk:
    """Fragmento de evidencia textual recuperado por el grafo."""

    source: str
    block_index: int
    matched_tokens: tuple[str, ...]
    snippet: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["matched_tokens"] = list(self.matched_tokens)
        return data


@dataclass(frozen=True)
class GraphRAGResult:
    """Resultado del GraphRAG estocástico local sin vectores densos."""

    bridge_result: BridgeResult
    leg_1_chunks: tuple[EvidenceChunk, ...]  # Tramo 1: w1 -> w*
    leg_2_chunks: tuple[EvidenceChunk, ...]  # Tramo 2: w* -> w2
    joint_chunks: tuple[EvidenceChunk, ...]  # Tramo conjunto: w1 + w* + w2

    def to_dict(self) -> dict[str, Any]:
        return {
            "bridge": self.bridge_result.to_dict(),
            "joint_chunks": [c.to_dict() for c in self.joint_chunks],
            "leg_1_chunks": [c.to_dict() for c in self.leg_1_chunks],
            "leg_2_chunks": [c.to_dict() for c in self.leg_2_chunks],
        }


FENCED_CODE_RE = re.compile(r"```[\s\S]*?```")
URL_RE = re.compile(r"(?:https?|file)://\S+")


def _clean_markdown_prose(text: str) -> str:
    """Elimina bloques de código cercados y URLs para evitar contaminar el grafo con sintaxis."""
    cleaned = FENCED_CODE_RE.sub("\n\n", text)
    return URL_RE.sub(" ", cleaned)


class MarkovLexicalBridge:
    """Grafo de transición de Markov restringido a sustantivos y verbos."""

    def __init__(self, window_size: int = 4, decay: float = 0.65, idf_alpha: float = 0.25) -> None:
        if window_size < 1:
            raise ValueError("window_size debe ser >= 1")
        if not (0.0 < decay <= 1.0):
            raise ValueError("decay debe estar en (0, 1]")
        if not (0.0 <= idf_alpha <= 1.0):
            raise ValueError("idf_alpha debe estar en [0, 1]")
        self.window_size = window_size
        self.decay = decay
        self.idf_alpha = idf_alpha
        self.pos_tags: dict[str, str] = {}
        self.unigram_counts: dict[str, int] = defaultdict(int)
        self.transitions: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self.outgoing_mass: dict[str, float] = defaultdict(float)
        self.blocks: list[tuple[str, str]] = []
        self.word_to_blocks: dict[str, set[int]] = defaultdict(set)

    def ingest_text(self, text: str, source_path: str = "<memory>") -> int:
        """Extrae la secuencia de sustantivos y verbos y actualiza las transiciones de Markov."""
        prose = _clean_markdown_prose(text)
        # Dividimos por párrafos/bloques para no cruzar fronteras temáticas lejanas
        raw_blocks = re.split(r"\n\s*\n", prose)
        ingested = 0
        for block in raw_blocks:
            clean_block = block.strip()
            if not clean_block:
                continue
            block_idx = len(self.blocks)
            self.blocks.append((source_path, clean_block))

            raw_tokens = TOKEN_RE.findall(clean_block)
            filtered: list[str] = []
            block_words_seen: set[str] = set()
            for raw in raw_tokens:
                w = raw.lower()
                pos = classify_pos(w)
                if pos is not None:
                    self.pos_tags[w] = pos
                    self.unigram_counts[w] += 1
                    filtered.append(w)
                    block_words_seen.add(w)
                    ingested += 1

            for w in block_words_seen:
                self.word_to_blocks[w].add(block_idx)

            n = len(filtered)
            for i, u in enumerate(filtered):
                upper = min(n, i + 1 + self.window_size)
                for j in range(i + 1, upper):
                    v = filtered[j]
                    if u == v:
                        continue
                    dist = j - i
                    weight = self.decay ** (dist - 1)
                    # Transición directa y simétrica atenuada para co-ocurrencia en cláusula
                    self.transitions[u][v] += weight
                    self.outgoing_mass[u] += weight
                    rev_weight = weight * 0.35
                    self.transitions[v][u] += rev_weight
                    self.outgoing_mass[v] += rev_weight
        return ingested

    def ingest_paths(self, paths: list[Path], max_files: int = 400) -> tuple[int, int]:
        """Ingesta archivos .md y .txt desde las rutas especificadas."""
        files_read = 0
        tokens_added = 0
        for p in paths:
            if p.is_file():
                try:
                    tokens_added += self.ingest_text(
                        p.read_text(encoding="utf-8", errors="ignore"),
                        source_path=str(p.resolve()),
                    )
                    files_read += 1
                except OSError:
                    continue
            elif p.is_dir():
                for ext in ("*.md", "*.txt"):
                    for fp in sorted(p.rglob(ext)):
                        if files_read >= max_files:
                            return files_read, tokens_added
                        try:
                            tokens_added += self.ingest_text(
                                fp.read_text(encoding="utf-8", errors="ignore"),
                                source_path=str(fp.resolve()),
                            )
                            files_read += 1
                        except OSError:
                            continue
        return files_read, tokens_added

    def prob(self, u: str, v: str) -> float:
        """Probabilidad de transición de Markov P(v | u)."""
        mass = self.outgoing_mass.get(u, 0.0)
        if mass <= 0.0:
            return 0.0
        return self.transitions[u].get(v, 0.0) / mass

    def _idf_discount(self, word: str) -> float:
        """Factor de descuento Anti-Hub (1 / count^alpha) para priorizar puentes específicos."""
        if self.idf_alpha <= 0.0:
            return 1.0
        cnt = max(self.unigram_counts.get(word, 1), 1)
        return float(1.0 / (cnt**self.idf_alpha))

    def resolve_word(self, word: str) -> str:
        """Normaliza, valida POS y aplica resolución morfológica por raíz si la flexión no está literal."""
        w = word.strip().lower()
        pos = classify_pos(w)
        if pos is None:
            raise ValueError(f"«{word}» fue rechazada por el filtro morfológico: solo se admiten sustantivos y verbos.")
        if w in self.unigram_counts or not self.unigram_counts:
            self.pos_tags.setdefault(w, pos)
            return w

        # Resolución por raíz morfológica (ej. 'sistemas' -> 'sistema', 'consolidar' -> 'consolida')
        if w.endswith("es") and len(w) > 4 and w[:-2] in self.unigram_counts:
            return w[:-2]
        if w.endswith("s") and len(w) > 3 and w[:-1] in self.unigram_counts:
            return w[:-1]
        if len(w) >= 5:
            stem = w[: max(5, len(w) - 2)]
            matches = [(cnt, cand) for cand, cnt in self.unigram_counts.items() if cnt > 0 and cand.startswith(stem)]
            if matches:
                matches.sort(reverse=True)
                return matches[0][1]

        self.pos_tags.setdefault(w, pos)
        return w

    def find_bridge(self, origin: str, target: str, top_k: int = 3) -> BridgeResult:
        """Halla la siguiente palabra imprescindible (w*) para ir de origin (w1) a target (w2)."""
        w1 = self.resolve_word(origin)
        w2 = self.resolve_word(target)
        if w1 == w2:
            raise ValueError("La palabra origen y la palabra destino deben ser distintas.")

        # 1. Intento de puente directo de 2 saltos ponderado por especificidad Anti-Hub
        candidates: list[tuple[float, float, str, float, float]] = []
        out_w1 = self.transitions.get(w1, {})
        mass_w1 = self.outgoing_mass.get(w1, 0.0)

        if mass_w1 > 0.0:
            for mid, weight_1 in out_w1.items():
                if mid in (w1, w2):
                    continue
                p1 = weight_1 / mass_w1
                p2 = self.prob(mid, w2)
                if p2 > 0.0:
                    joint = p1 * p2
                    specificity_score = joint * self._idf_discount(mid)
                    candidates.append((specificity_score, joint, mid, p1, p2))

        if candidates:
            candidates.sort(key=lambda item: item[0], reverse=True)
            _, best_joint, best_mid, best_p1, best_p2 = candidates[0]
            surprisal = -math.log2(max(best_joint, 1e-18))
            total_joint = sum(c[1] for c in candidates)
            ratio = (best_joint / total_joint) if total_joint > 0.0 else 1.0
            alts = tuple(
                (mid, self.pos_tags.get(mid, "NOUN"), joint) for _, joint, mid, _, _ in candidates[1 : top_k + 1]
            )
            return BridgeResult(
                origin=w1,
                origin_pos=self.pos_tags[w1],
                bridge=best_mid,
                bridge_pos=self.pos_tags.get(best_mid, "NOUN"),
                target=w2,
                target_pos=self.pos_tags[w2],
                p_origin_to_bridge=best_p1,
                p_bridge_to_target=best_p2,
                joint_score=best_joint,
                surprisal_bits=surprisal,
                bottleneck_ratio=ratio,
                full_path=(w1, best_mid, w2),
                alternatives=alts,
            )

        # 2. Geodésica de Viterbi / Dijkstra sobre el grafo (-log2 P(v | u)) si están a >2 saltos
        path = self._shortest_markov_path(w1, w2)
        if path is not None and len(path) >= 3:
            first_bridge = path[1]
            p1 = self.prob(w1, first_bridge)
            # Probabilidad acumulada a lo largo de la geodésica
            log2_sum = 0.0
            for a, b in zip(path[:-1], path[1:], strict=False):
                p_step = max(self.prob(a, b), 1e-12)
                log2_sum += -math.log2(p_step)
            joint_equiv = 2.0 ** (-log2_sum)
            p_rest = joint_equiv / max(p1, 1e-12)
            return BridgeResult(
                origin=w1,
                origin_pos=self.pos_tags[w1],
                bridge=first_bridge,
                bridge_pos=self.pos_tags.get(first_bridge, "NOUN"),
                target=w2,
                target_pos=self.pos_tags[w2],
                p_origin_to_bridge=p1,
                p_bridge_to_target=p_rest,
                joint_score=joint_equiv,
                surprisal_bits=log2_sum,
                bottleneck_ratio=1.0,
                full_path=tuple(path),
                alternatives=(),
            )

        # 3. Fallback conectado por el hub léxico (sustantivo/verbo) de mayor centralidad
        hub = self._fallback_hub(exclude={w1, w2})
        return BridgeResult(
            origin=w1,
            origin_pos=self.pos_tags[w1],
            bridge=hub,
            bridge_pos=self.pos_tags.get(hub, "NOUN"),
            target=w2,
            target_pos=self.pos_tags[w2],
            p_origin_to_bridge=self.prob(w1, hub),
            p_bridge_to_target=self.prob(hub, w2),
            joint_score=0.0,
            surprisal_bits=float("inf"),
            bottleneck_ratio=0.0,
            full_path=(w1, hub, w2),
            alternatives=(),
        )

    def predict_auto_target_and_bridge(self, origin: str) -> BridgeResult:
        """Dada una sola palabra (w1), deduce la segunda palabra atractora (w2) a 2 pasos y el puente imprescindible (w*)."""
        w1 = self.resolve_word(origin)
        out_w1 = self.transitions.get(w1, {})
        mass_w1 = self.outgoing_mass.get(w1, 0.0)
        if mass_w1 <= 0.0:
            hub = self._fallback_hub(exclude={w1})
            target = self._fallback_hub(exclude={w1, hub})
            return self.find_bridge(w1, target)

        best_pair: tuple[float, float, str, str, float, float] | None = None
        candidates: list[tuple[float, float, str, str]] = []
        for mid, w_1 in out_w1.items():
            if mid == w1:
                continue
            p1 = w_1 / mass_w1
            out_mid = self.transitions.get(mid, {})
            mass_mid = self.outgoing_mass.get(mid, 0.0)
            if mass_mid <= 0.0:
                continue
            idf_mid = self._idf_discount(mid)
            for dst, w_2 in out_mid.items():
                if dst in (w1, mid):
                    continue
                p2 = w_2 / mass_mid
                joint = p1 * p2
                spec = joint * idf_mid * self._idf_discount(dst)
                candidates.append((spec, joint, mid, dst))
                if best_pair is None or spec > best_pair[0]:
                    best_pair = (spec, joint, mid, dst, p1, p2)

        if best_pair is None:
            hub = self._fallback_hub(exclude={w1})
            target = self._fallback_hub(exclude={w1, hub})
            return self.find_bridge(w1, target)

        _, best_joint, best_mid, best_dst, best_p1, best_p2 = best_pair
        candidates.sort(key=lambda item: item[0], reverse=True)
        total_joint = sum(c[1] for c in candidates)
        ratio = (best_joint / total_joint) if total_joint > 0.0 else 1.0
        alts = tuple((mid, self.pos_tags.get(mid, "NOUN"), joint) for _, joint, mid, _ in candidates[1:4])
        return BridgeResult(
            origin=w1,
            origin_pos=self.pos_tags[w1],
            bridge=best_mid,
            bridge_pos=self.pos_tags.get(best_mid, "NOUN"),
            target=best_dst,
            target_pos=self.pos_tags.get(best_dst, "NOUN"),
            p_origin_to_bridge=best_p1,
            p_bridge_to_target=best_p2,
            joint_score=best_joint,
            surprisal_bits=-math.log2(max(best_joint, 1e-18)),
            bottleneck_ratio=ratio,
            full_path=(w1, best_mid, best_dst),
            alternatives=alts,
        )

    def _shortest_markov_path(self, start: str, goal: str, max_hops: int = 10) -> list[str] | None:
        """Dijkstra sobre sorpresa informacional (-log2 P(v | u)) exigiendo al menos 1 nodo intermedio."""
        pq: list[tuple[float, str, list[str]]] = [(0.0, start, [start])]
        best_cost: dict[tuple[str, bool], float] = {(start, False): 0.0}

        while pq:
            cost, u, path = heapq.heappop(pq)
            if u == goal and len(path) >= 3:
                return path
            if len(path) > max_hops:
                continue

            mass_u = self.outgoing_mass.get(u, 0.0)
            if mass_u <= 0.0:
                continue
            for v, weight in self.transitions[u].items():
                if v in path:
                    continue
                if v == goal and len(path) < 2:
                    # Forzamos que exista una palabra intermedia imprescindible (len >= 3)
                    continue
                p = weight / mass_u
                step_cost = -math.log2(max(p, 1e-12))
                new_cost = cost + step_cost
                state = (v, len(path) >= 1)
                if new_cost < best_cost.get(state, float("inf")):
                    best_cost[state] = new_cost
                    heapq.heappush(pq, (new_cost, v, [*path, v]))
        return None

    def _fallback_hub(self, exclude: set[str]) -> str:
        """Devuelve el sustantivo o verbo de mayor masa de transición en el corpus."""
        ranked = sorted(self.outgoing_mass.items(), key=lambda item: item[1], reverse=True)
        for word, _ in ranked:
            if word not in exclude:
                return word
        return "sistema"

    def graph_rag(self, origin: str, target: str, limit_per_leg: int = 2) -> GraphRAGResult:
        """Recupera fragmentos de evidencia textual (GraphRAG) para los tramos (w1 -> w*) y (w* -> w2)."""
        bridge_res = self.find_bridge(origin, target)
        w1 = bridge_res.origin
        w_star = bridge_res.bridge
        w2 = bridge_res.target

        blocks_w1 = self.word_to_blocks.get(w1, set())
        blocks_bridge = self.word_to_blocks.get(w_star, set())
        blocks_w2 = self.word_to_blocks.get(w2, set())

        # 1. Bloques que contienen w1 + w* + w2 (tríada causal completa en el mismo bloque)
        joint_indices = sorted(blocks_w1 & blocks_bridge & blocks_w2)
        joint_chunks = tuple(
            EvidenceChunk(
                source=self.blocks[idx][0],
                block_index=idx,
                matched_tokens=(w1, w_star, w2),
                snippet=self._extract_snippet(self.blocks[idx][1], (w1, w_star, w2)),
            )
            for idx in joint_indices[:limit_per_leg]
        )

        # 2. Tramo 1: bloques con (w1 + w*) excluyendo los ya capturados en joint
        leg1_indices = sorted((blocks_w1 & blocks_bridge) - set(joint_indices))
        leg1_chunks = tuple(
            EvidenceChunk(
                source=self.blocks[idx][0],
                block_index=idx,
                matched_tokens=(w1, w_star),
                snippet=self._extract_snippet(self.blocks[idx][1], (w1, w_star)),
            )
            for idx in leg1_indices[:limit_per_leg]
        )

        # 3. Tramo 2: bloques con (w* + w2) excluyendo los ya capturados
        leg2_indices = sorted((blocks_bridge & blocks_w2) - set(joint_indices))
        leg2_chunks = tuple(
            EvidenceChunk(
                source=self.blocks[idx][0],
                block_index=idx,
                matched_tokens=(w_star, w2),
                snippet=self._extract_snippet(self.blocks[idx][1], (w_star, w2)),
            )
            for idx in leg2_indices[:limit_per_leg]
        )

        return GraphRAGResult(
            bridge_result=bridge_res,
            leg_1_chunks=leg1_chunks,
            leg_2_chunks=leg2_chunks,
            joint_chunks=joint_chunks,
        )

    def _extract_snippet(self, text: str, highlight_words: tuple[str, ...], max_len: int = 240) -> str:
        """Extrae un extracto de texto recortado en torno a las palabras clave."""
        clean = " ".join(text.split())
        if len(clean) <= max_len:
            return clean
        low = clean.lower()
        first_pos = len(clean)
        for hw in highlight_words:
            idx = low.find(hw)
            if idx != -1 and idx < first_pos:
                first_pos = idx
        start = max(0, first_pos - 40)
        end = min(len(clean), start + max_len)
        snippet = clean[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(clean):
            snippet = snippet + "..."
        return snippet


def format_result(res: BridgeResult) -> str:
    """Formatea la salida mostrando la palabra imprescindible y la métrica de Markov."""
    pos_map = {"NOUN": "Sustantivo", "VERB": "Verbo"}
    b_pos = pos_map.get(res.bridge_pos, res.bridge_pos)
    o_pos = pos_map.get(res.origin_pos, res.origin_pos)
    t_pos = pos_map.get(res.target_pos, res.target_pos)
    path_str = " -> ".join(f"[{w.upper()}]" if w == res.bridge else w for w in res.full_path)
    lines = [
        f"╭─► Origen (w1):          {res.origin} ({o_pos})",
        f"├─► IMPRESCINDIBLE (w*):  {res.bridge.upper()} ({b_pos})",
        f"├─► Destino (w2):         {res.target} ({t_pos})",
        f"├─► Cadena de Markov:     {path_str}",
        f"╰─► P(w*|w1)={res.p_origin_to_bridge:.4f} | P(w2|w*)={res.p_bridge_to_target:.4f} | Sorpresa={res.surprisal_bits:.2f} bits | Flujo={res.bottleneck_ratio * 100:.1f}%",
    ]
    if res.alternatives:
        alt_str = ", ".join(f"{w} ({pos_map.get(p, p)}, {s:.2e})" for w, p, s in res.alternatives)
        lines.append(f"    Alternativas:         {alt_str}")
    return "\n".join(lines)


def format_rag_result(rag: GraphRAGResult) -> str:
    """Formatea la salida GraphRAG con bloques de evidencia y citas."""
    lines = [
        format_result(rag.bridge_result),
        "",
        "╔══════════════════════════════════════════════════════════════════╗",
        "║ EVIDENCIA RECUPERADA (GraphRAG Local Cero-Embeddings)            ║",
        "╚══════════════════════════════════════════════════════════════════╝",
    ]
    if rag.joint_chunks:
        lines.append(
            f"► [TRÍADA CONJUNTA] {rag.bridge_result.origin} -> {rag.bridge_result.bridge.upper()} -> {rag.bridge_result.target}:"
        )
        for chunk in rag.joint_chunks:
            lines.append(f"  • {chunk.source} (bloque #{chunk.block_index}):")
            lines.append(f"    «{chunk.snippet}»")
    if rag.leg_1_chunks:
        lines.append(f"► [TRAMO 1] {rag.bridge_result.origin} -> {rag.bridge_result.bridge.upper()}:")
        for chunk in rag.leg_1_chunks:
            lines.append(f"  • {chunk.source} (bloque #{chunk.block_index}):")
            lines.append(f"    «{chunk.snippet}»")
    if rag.leg_2_chunks:
        lines.append(f"► [TRAMO 2] {rag.bridge_result.bridge.upper()} -> {rag.bridge_result.target}:")
        for chunk in rag.leg_2_chunks:
            lines.append(f"  • {chunk.source} (bloque #{chunk.block_index}):")
            lines.append(f"    «{chunk.snippet}»")
    if not (rag.joint_chunks or rag.leg_1_chunks or rag.leg_2_chunks):
        lines.append("  (No se encontraron bloques con co-ocurrencia directa de las palabras en el corpus).")
    return "\n".join(lines)


def build_default_corpus_paths(workspace_root: Path) -> list[Path]:
    """Rutas de corpus por defecto dentro del repositorio local."""
    candidates = [
        workspace_root / "docs",
        workspace_root / "README.md",
        workspace_root / "WHY_BABYLON_60.md",
    ]
    return [p for p in candidates if p.exists()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Calcula la siguiente palabra imprescindible (solo sustantivos y verbos) "
            "para llegar de una primera palabra a una segunda mediante un Grafo de Markov "
            "y recupera evidencia textual causal (GraphRAG local sin vectores)."
        )
    )
    parser.add_argument(
        "words",
        nargs="*",
        help="Una palabra (w1) o par de palabras (w1 w2). Si se omite, inicia el modo interactivo.",
    )
    parser.add_argument(
        "--rag",
        action="store_true",
        help="Activa recuperación GraphRAG extrayendo los fragmentos de texto exactos para w1->w* y w*->w2.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emite la salida en formato JSON estructurado para consumo agéntico M2M.",
    )
    parser.add_argument(
        "--corpus",
        nargs="*",
        type=Path,
        default=None,
        help="Archivos o directorios de texto para construir el grafo de Markov (por defecto: docs/).",
    )
    parser.add_argument(
        "--window",
        type=int,
        default=4,
        help="Tamaño de ventana de co-ocurrencia entre sustantivos y verbos (defecto: 4).",
    )
    parser.add_argument(
        "--idf-alpha",
        type=float,
        default=0.25,
        help="Exponente de descuento Anti-Hub (0.0 a 1.0, defecto: 0.25) para priorizar puentes específicos.",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=DEFAULT_MAX_REPL_TURNS,
        help=(
            "Límite de turnos del modo interactivo (INV_C5_19, defecto: "
            f"{DEFAULT_MAX_REPL_TURNS}). Debe ser un entero positivo."
        ),
    )
    args = parser.parse_args(argv)
    if args.max_turns < 1:
        parser.error("--max-turns debe ser un entero positivo")

    workspace_root = Path(__file__).resolve().parents[2]
    corpus_paths = args.corpus if args.corpus else build_default_corpus_paths(workspace_root)

    engine = MarkovLexicalBridge(window_size=args.window, idf_alpha=args.idf_alpha)
    files_read, tokens_added = engine.ingest_paths(corpus_paths)

    if tokens_added == 0:
        # Corpus semilla de respaldo si se ejecuta fuera de un árbol con documentos
        engine.ingest_text(
            "El sistema transforma ruido en información mediante cálculo y memoria. "
            "La memoria conserva estado mientras el cálculo ejecuta transiciones y verifica pruebas. "
            "El operador diseña código, compila binarios y audita teoremas para garantizar seguridad."
        )

    # Modo directo por argumentos CLI
    if len(args.words) >= 2:
        try:
            results_payload = []
            for i in range(len(args.words) - 1):
                if args.rag:
                    rag_res = engine.graph_rag(args.words[i], args.words[i + 1])
                    if args.json:
                        results_payload.append(rag_res.to_dict())
                    else:
                        print(format_rag_result(rag_res))
                else:
                    res = engine.find_bridge(args.words[i], args.words[i + 1])
                    if args.json:
                        results_payload.append(res.to_dict())
                    else:
                        print(format_result(res))
                if not args.json and i < len(args.words) - 2:
                    print()
            if args.json:
                print(
                    json.dumps(
                        results_payload[0] if len(results_payload) == 1 else results_payload,
                        indent=2,
                        ensure_ascii=False,
                    )
                )
            return 0
        except ValueError as exc:
            print(f"[ERROR MORFOLÓGICO] {exc}", file=sys.stderr)
            return 1

    if len(args.words) == 1:
        try:
            res = engine.predict_auto_target_and_bridge(args.words[0])
            if args.rag:
                rag_res = engine.graph_rag(res.origin, res.target)
                if args.json:
                    print(json.dumps(rag_res.to_dict(), indent=2, ensure_ascii=False))
                else:
                    print(format_rag_result(rag_res))
            elif args.json:
                print(json.dumps(res.to_dict(), indent=2, ensure_ascii=False))
            else:
                print(format_result(res))
            return 0
        except ValueError as exc:
            print(f"[ERROR MORFOLÓGICO] {exc}", file=sys.stderr)
            return 1

    # Modo interactivo REPL (soporta 1 palabra encadenada turno a turno o 2 palabras por línea)
    print(
        f"[MARKOV BRIDGE · SOLO SUSTANTIVOS Y VERBOS] "
        f"Corpus: {files_read} archivos | {len(engine.unigram_counts)} nodos léxicos activos."
    )
    print(
        "Escribe una palabra (encadena con la anterior o predice destino) o dos palabras ('w1 w2 [--rag]'). "
        "Escribe 'salir' para terminar.\n"
    )

    prev_word: str | None = None
    # INV_C5_19: el REPL termina por EOF/salida explícita o al agotar el límite de turnos.
    for _turn in range(args.max_turns):
        try:
            raw = input("palabra(s) > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not raw or raw.lower() in {"salir", "exit", "quit", "q"}:
            break

        raw_parts = raw.split()
        use_rag = args.rag or ("--rag" in raw_parts)
        parts = [p for p in raw_parts if not p.startswith("--")]
        if not parts:
            continue
        try:
            if len(parts) >= 2:
                if use_rag:
                    rag_res = engine.graph_rag(parts[0], parts[1])
                    print(format_rag_result(rag_res))
                else:
                    res = engine.find_bridge(parts[0], parts[1])
                    print(format_result(res))
                prev_word = engine.resolve_word(parts[1])
            elif prev_word is None:
                res = engine.predict_auto_target_and_bridge(parts[0])
                if use_rag:
                    rag_res = engine.graph_rag(res.origin, res.target)
                    print(format_rag_result(rag_res))
                else:
                    print(format_result(res))
                prev_word = engine.resolve_word(parts[0])
            else:
                if use_rag:
                    rag_res = engine.graph_rag(prev_word, parts[0])
                    print(format_rag_result(rag_res))
                else:
                    res = engine.find_bridge(prev_word, parts[0])
                    print(format_result(res))
                prev_word = engine.resolve_word(parts[0])
            print()
        except ValueError as exc:
            print(f"  ✗ {exc}\n")
    else:
        print(f"[MARKOV BRIDGE] Límite de {args.max_turns} turnos alcanzado; sesión cerrada.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
