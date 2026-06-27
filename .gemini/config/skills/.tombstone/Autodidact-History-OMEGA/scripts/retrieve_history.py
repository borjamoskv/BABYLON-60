#!/usr/bin/env python3
# C5-REAL
# AUTODIDACT-HISTORY-OMEGA v3.0 | OMEGA-COMPILER v1.0
# [ID] -> ΔEstado(sociedad, IA, cognición, infraestructura)
# Full historiography 1950-2026 — Zero gaps, era taxonomy, thermodynamic lens.

import sys
import json
import argparse
from datetime import datetime
from typing import Optional

# ═══════════════════════════════════════════════════════════════════
# ERA TAXONOMY
# ═══════════════════════════════════════════════════════════════════
ERAS = {
    "genesis":       {"range": (1950, 1956), "label": "Génesis", "color": "\033[38;5;250m"},
    "symbolic":      {"range": (1957, 1973), "label": "Era Simbólica (GOFAI)", "color": "\033[38;5;214m"},
    "winters":       {"range": (1974, 1985), "label": "Inviernos de la IA", "color": "\033[38;5;244m"},
    "renaissance":   {"range": (1986, 2011), "label": "Renacimiento Conexionista", "color": "\033[38;5;107m"},
    "deep_learning": {"range": (2012, 2019), "label": "Deep Learning Explosion", "color": "\033[38;5;39m"},
    "foundation":    {"range": (2020, 2024), "label": "Modelos Fundacionales", "color": "\033[38;5;171m"},
    "singularity":   {"range": (2025, 2030), "label": "Singularidad Operativa", "color": "\033[38;5;196m"},
}

def get_era(year: int) -> str:
    for era_id, meta in ERAS.items():
        lo, hi = meta["range"]
        if lo <= year <= hi:
            return era_id
    return "unknown"

# ═══════════════════════════════════════════════════════════════════
# ALIAS MAP (fuzzy routing)
# ═══════════════════════════════════════════════════════════════════
_ALIASES: dict[str, str] = {
    # turing
    "imitation game": "turing", "test de turing": "turing", "alan turing": "turing",
    # dartmouth
    "mccarthy": "dartmouth", "shannon": "dartmouth", "gofai": "dartmouth",
    # eliza
    "weizenbaum": "eliza", "terapeuta": "eliza", "therapist": "eliza",
    # shrdlu
    "winograd": "shrdlu", "bloques": "shrdlu", "blocks": "shrdlu",
    # perceptron
    "xor": "perceptron", "minsky": "perceptron", "rosenblatt": "perceptron", "papert": "perceptron",
    # winters
    "invierno": "winters", "winter": "winters", "moravec": "winters", "lighthill": "winters",
    # expert_systems
    "mycin": "expert_systems", "expertos": "expert_systems", "dendral": "expert_systems",
    # backprop
    "backpropagation": "backprop", "rumelhart": "backprop", "hinton_backprop": "backprop",
    "propagacion": "backprop",
    # svm
    "support vector": "svm", "vapnik": "svm", "kernel": "svm",
    # www_crawl
    "web": "www_crawl", "internet data": "www_crawl", "crawler": "www_crawl",
    # lstm
    "long short": "lstm", "hochreiter": "lstm", "schmidhuber": "lstm",
    "recurrent": "lstm", "rnn": "lstm",
    # deep_blue
    "kasparov": "deep_blue", "chess": "deep_blue", "ajedrez": "deep_blue", "ibm chess": "deep_blue",
    # watson
    "jeopardy": "watson", "ibm watson": "watson",
    # alexnet
    "gpu": "alexnet", "imagenet": "alexnet", "deep learning": "alexnet",
    "krizhevsky": "alexnet",
    # word2vec
    "embeddings": "word2vec", "mikolov": "word2vec", "word embeddings": "word2vec",
    # gan
    "generative adversarial": "gan", "goodfellow": "gan", "generador": "gan",
    "discriminador_gan": "gan",
    # alphago
    "lee sedol": "alphago", "monte carlo": "alphago", "mcts": "alphago",
    "go": "alphago", "deepmind go": "alphago",
    # transformers
    "attention": "transformers", "vaswani": "transformers", "self-attention": "transformers",
    "attention is all": "transformers",
    # bert_gpt
    "bert": "bert_gpt", "gpt-1": "bert_gpt", "gpt-2": "bert_gpt",
    "pretraining": "bert_gpt", "devlin": "bert_gpt", "radford": "bert_gpt",
    # gpt3
    "gpt-3": "gpt3", "175b": "gpt3", "few-shot": "gpt3", "in-context learning": "gpt3",
    # dalle
    "dall-e": "dalle", "text-to-image": "dalle", "imagen": "dalle",
    "midjourney": "dalle", "stable diffusion": "dalle",
    # chatgpt
    "chatgpt": "chatgpt_moment", "chat gpt": "chatgpt_moment",
    "rlhf": "chatgpt_moment", "instructgpt": "chatgpt_moment",
    # gemini
    "gemini": "gemini_ultra", "gemini ultra": "gemini_ultra",
    "multimodal": "gemini_ultra", "palm": "gemini_ultra",
    # sora
    "sora": "sora_worldsim", "world simulator": "sora_worldsim",
    "video generation": "sora_worldsim",
    # alphaproof
    "alphaproof": "alphaproof_alphageometry", "alphageometry": "alphaproof_alphageometry",
    "imo": "alphaproof_alphageometry", "lean": "alphaproof_alphageometry",
    # daybreak
    "openai": "daybreak", "codex security": "daybreak", "gpt-5.5": "daybreak",
    # maxima_exergia
    "bremermann": "maxima_exergia", "npu": "maxima_exergia", "exergia": "maxima_exergia",
    # cryptographic_autopoiesis
    "autopoiesis": "cryptographic_autopoiesis",
    "autopoietic": "cryptographic_autopoiesis",
    "landauer": "cryptographic_autopoiesis",
    "swarm": "cryptographic_autopoiesis",
    "enjambre": "cryptographic_autopoiesis",
    # autodidact_inverse
    "inverse": "autodidact_inverse",
    # claude_mythos
    "mythos": "claude_mythos", "glasswing": "claude_mythos",
    # death_protocol
    "death protocol": "death_protocol", "apoptosis": "death_protocol",
    # self_play_universes
    "self play": "self_play_universes", "self-play": "self_play_universes",
    # alignment_as_competition
    "alignment": "alignment_as_competition",
    # post_token_world
    "post token": "post_token_world", "actuator": "post_token_world",
    # cortex_mesh
    "mesh": "cortex_mesh", "cortex": "cortex_mesh",
    # naroa
    "naroa": "naroa_ecosystem", "ecosystem": "naroa_ecosystem",
}

# ═══════════════════════════════════════════════════════════════════
# MILESTONES DATABASE — 36 NODES
# ═══════════════════════════════════════════════════════════════════
MILESTONES = {
    # ─── GENESIS (1950-1956) ───────────────────────────────────
    "turing": {
        "id": "turing", "year": 1950, "era": "genesis",
        "protagonists": ["Alan Turing"],
        "paper": "Computing Machinery and Intelligence (Mind, 1950)",
        "description": "Turing eludió la trampa filosófica de definir 'pensar'. Sustituyó ontología por empirismo mediante el Imitation Game.",
        "impacto_exergia": "Sustitución de estado ontológico por frontera de discriminación estocástica. (Consumo energético: basal humano).",
        "impacto_senal": "Compresión de canal: reduce el problema de la consciencia a equivalencia de señal binaria.",
        "reescritura_historica": "Reinterpretado post-2017: Turing como el primer conceptualizador del 'token predictor' engañando al discriminador.",
        "mutacion_modelo_actual": "ΔEstado(cognición: externalizada_al_parser, infraestructura: texto_plano)",
    },
    "dartmouth": {
        "id": "dartmouth", "year": 1956, "era": "genesis",
        "protagonists": ["John McCarthy", "Marvin Minsky", "Claude Shannon", "Nathaniel Rochester"],
        "paper": "A Proposal for the Dartmouth Summer Research Project on AI (1955)",
        "description": "Separación formal de la cibernética hacia la manipulación simbólica (GOFAI).",
        "impacto_exergia": "Aislamiento termodinámico: abandono del mundo físico (robótica sensoriomotora) por el vacío lógico.",
        "impacto_senal": "Creación del 'símbolo' como unidad atómica inmutable.",
        "reescritura_historica": "El error original: suponer que la inteligencia es un problema de álgebra y no de disipación de calor.",
        "mutacion_modelo_actual": "ΔEstado(IA: axiomatizada, sociedad: hiper_promesa)",
    },

    # ─── ERA SIMBÓLICA (1957-1973) ─────────────────────────────
    "eliza": {
        "id": "eliza", "year": 1966, "era": "symbolic",
        "protagonists": ["Joseph Weizenbaum"],
        "paper": "ELIZA—A Computer Program For the Study of NL Communication (CACM, 1966)",
        "description": "Simulación rogeriana usando emparejamiento de patrones sin estado.",
        "impacto_exergia": "Alto rendimiento percibido con exergía cercana a cero O(1).",
        "impacto_senal": "Hackeo de la capa semántica humana: el usuario aporta el 99% del cómputo inferencial.",
        "reescritura_historica": "El prototipo de la alucinación inducida por RLHF: dar al humano exactamente el reflejo que desea ver.",
        "mutacion_modelo_actual": "ΔEstado(cognición: proyección_antropomórfica, IA: espejo_semántico)",
    },
    "shrdlu": {
        "id": "shrdlu", "year": 1968, "era": "symbolic",
        "protagonists": ["Terry Winograd"],
        "paper": "Understanding Natural Language (1972)",
        "description": "Comprensión de lenguaje natural en un 'mundo de bloques' cerrado.",
        "impacto_exergia": "Trabajo útil limitado a un sumidero adiabático cerrado.",
        "impacto_senal": "Validación de la semántica referencial estricta.",
        "reescritura_historica": "Demostración temprana de la 'hipótesis del micro-mundo', aniquilada luego por la entropía del mundo abierto.",
        "mutacion_modelo_actual": "ΔEstado(IA: confinada_topológicamente, infraestructura: lisp_machines)",
    },
    "perceptron": {
        "id": "perceptron", "year": 1969, "era": "symbolic",
        "protagonists": ["Marvin Minsky", "Seymour Papert"],
        "paper": "Perceptrons: An Introduction to Computational Geometry (MIT Press, 1969)",
        "description": "Límite topológico demostrado (XOR) que congela las redes neuronales.",
        "impacto_exergia": "Bloqueo por falta de algoritmo de disipación de gradiente (backprop).",
        "impacto_senal": "Destrucción del hype inicial conexionista.",
        "reescritura_historica": "El primer 'invierno' causado por la incapacidad de computar flujos energéticos no-lineales.",
        "mutacion_modelo_actual": "ΔEstado(IA: lineal, sociedad: escepticismo)",
    },

    # ─── INVIERNOS (1974-1985) ─────────────────────────────────
    "winters": {
        "id": "winters", "year": 1974, "era": "winters",
        "protagonists": ["James Lighthill", "DARPA"],
        "paper": "Lighthill Report (1973); DARPA funding cuts (1974)",
        "description": "Colapsos financieros por ignorar la Paradoja de Moravec.",
        "impacto_exergia": "Corte abrupto del sustrato energético/financiero (DARPA).",
        "impacto_senal": "Purga de promesas GOFAI.",
        "reescritura_historica": "Reseteo del metabolismo del ecosistema, permitiendo la mutación hacia el aprendizaje estadístico.",
        "mutacion_modelo_actual": "ΔEstado(sociedad: desinversión, IA: hibernación)",
    },
    "expert_systems": {
        "id": "expert_systems", "year": 1975, "era": "winters",
        "protagonists": ["Edward Feigenbaum", "Bruce Buchanan"],
        "paper": "DENDRAL (1965-1975); MYCIN (1976)",
        "description": "MYCIN y la separación del motor de inferencia de la base de conocimiento.",
        "impacto_exergia": "Fricción combinatoria infinita al intentar escalar reglas IF-THEN.",
        "impacto_senal": "Fragilidad semántica fuera de fronteras de dominio estrictas.",
        "reescritura_historica": "Precursor fallido del in-context learning estático.",
        "mutacion_modelo_actual": "ΔEstado(cognición: heurística_frágil, infraestructura: prolog)",
    },

    # ─── RENACIMIENTO CONEXIONISTA (1986-2011) ─────────────────
    "backprop": {
        "id": "backprop", "year": 1986, "era": "renaissance",
        "protagonists": ["David Rumelhart", "Geoffrey Hinton", "Ronald Williams"],
        "paper": "Learning representations by back-propagating errors (Nature, 1986)",
        "description": "Resurrección de las redes neuronales mediante propagación hacia atrás del error.",
        "impacto_exergia": "Desbloqueo del gradiente como flujo termodinámico computable. El calor ya puede disiparse en capas.",
        "impacto_senal": "Solución directa al bloqueo XOR de Minsky/Papert. El perceptrón multicapa vive.",
        "reescritura_historica": "El algoritmo existía desde Werbos (1974) pero fue Hinton quien lo inyectó en la cultura. La idea dormía esperando hardware.",
        "mutacion_modelo_actual": "ΔEstado(IA: multicapa, infraestructura: cpu_serial)",
    },
    "www_crawl": {
        "id": "www_crawl", "year": 1993, "era": "renaissance",
        "protagonists": ["Tim Berners-Lee", "CERN"],
        "paper": "Information Management: A Proposal (CERN, 1989); Mosaic browser (1993)",
        "description": "La World Wide Web como corpus universal de entrenamiento futuro.",
        "impacto_exergia": "Generación exponencial de texto, imágenes y estructura enlazable. Entropía masiva acumulándose.",
        "impacto_senal": "El sustrato de pre-entrenamiento de los LLMs se crea dos décadas antes del primer transformer.",
        "reescritura_historica": "Internet no fue diseñado para la IA, pero sin él GPT-3 es termodinámicamente imposible.",
        "mutacion_modelo_actual": "ΔEstado(infraestructura: corpus_universal, sociedad: datos_como_subproducto)",
    },
    "svm": {
        "id": "svm", "year": 1995, "era": "renaissance",
        "protagonists": ["Vladimir Vapnik", "Corinna Cortes"],
        "paper": "Support-vector networks (Machine Learning, 1995)",
        "description": "Hiperplanos óptimos con truco del kernel para clasificación no lineal.",
        "impacto_exergia": "Eficiencia máxima en datasets pequeños. Garantías de generalización vía margen máximo.",
        "impacto_senal": "Dominio de ML académico durante una década. El paradigma 'features + kernel' como orthodoxia.",
        "reescritura_historica": "El último bastión del ML 'elegante' antes del brute-force del deep learning.",
        "mutacion_modelo_actual": "ΔEstado(IA: optimización_convexa, cognición: ingeniería_de_features)",
    },
    "lstm": {
        "id": "lstm", "year": 1997, "era": "renaissance",
        "protagonists": ["Sepp Hochreiter", "Jürgen Schmidhuber"],
        "paper": "Long Short-Term Memory (Neural Computation, 1997)",
        "description": "Solución al problema del gradiente evanescente en redes recurrentes.",
        "impacto_exergia": "Compuertas de olvido como válvulas termodinámicas: controlan qué energía (información) se preserva.",
        "impacto_senal": "Habilitación de dependencias de largo alcance en secuencias temporales.",
        "reescritura_historica": "Dominó NLP y series temporales hasta 2017, cuando el Transformer la reemplazó por atención paralela.",
        "mutacion_modelo_actual": "ΔEstado(IA: memoria_gated, infraestructura: secuencial)",
    },
    "deep_blue": {
        "id": "deep_blue", "year": 1997, "era": "renaissance",
        "protagonists": ["IBM", "Feng-hsiung Hsu"],
        "paper": "Behind Deep Blue (Princeton, 2002)",
        "description": "Victoria sobre Kasparov mediante fuerza bruta de búsqueda + hardware dedicado.",
        "impacto_exergia": "200M posiciones/seg de búsqueda alfa-beta. Puro consumo de silicio sin aprendizaje.",
        "impacto_senal": "Primera crisis simbólica: la máquina 'gana' sin 'entender'. Preludio del debate AGI.",
        "reescritura_historica": "Reinterpretado post-AlphaGo: la inteligencia no estaba en la búsqueda exhaustiva sino en la evaluación aprendida.",
        "mutacion_modelo_actual": "ΔEstado(sociedad: shock_mediatico, IA: fuerza_bruta)",
    },
    "watson": {
        "id": "watson", "year": 2011, "era": "renaissance",
        "protagonists": ["IBM", "David Ferrucci"],
        "paper": "Building Watson (AI Magazine, 2010)",
        "description": "Victoria en Jeopardy! mediante NLP pipeline + búsqueda masiva.",
        "impacto_exergia": "Ensemble de 100+ algoritmos NLP en paralelo. Enorme infraestructura para resultado mediocre fuera de dominio.",
        "impacto_senal": "Demostración de que el NLP pre-transformer requiere ingeniería heroica para cada dominio.",
        "reescritura_historica": "Watson fue el último gran sistema NLP sin embeddings. Su fracaso comercial posterior validó el camino neural.",
        "mutacion_modelo_actual": "ΔEstado(IA: pipeline_artesanal, infraestructura: cluster_ibm)",
    },

    # ─── DEEP LEARNING EXPLOSION (2012-2019) ──────────────────
    "alexnet": {
        "id": "alexnet", "year": 2012, "era": "deep_learning",
        "protagonists": ["Alex Krizhevsky", "Ilya Sutskever", "Geoffrey Hinton"],
        "paper": "ImageNet Classification with Deep CNNs (NeurIPS 2012)",
        "description": "La Singularidad de ImageNet: convoluciones profundas + GPU.",
        "impacto_exergia": "La GPU desbloquea la disipación masiva de tensores. Incremento de consumo exponencial.",
        "impacto_senal": "Reemplazo de descriptores manuales por representaciones latentes.",
        "reescritura_historica": "El hardware (gradiente de exergía) dicta el algoritmo, no al revés.",
        "mutacion_modelo_actual": "ΔEstado(infraestructura: gpu_cluster, IA: conexionista)",
    },
    "word2vec": {
        "id": "word2vec", "year": 2013, "era": "deep_learning",
        "protagonists": ["Tomas Mikolov"],
        "paper": "Efficient Estimation of Word Representations in Vector Space (2013)",
        "description": "Proyección de palabras a vectores densos que capturan relaciones semánticas (king - man + woman ≈ queen).",
        "impacto_exergia": "Compresión semántica extrema: millones de palabras a 300 dimensiones. Eficiencia O(V·d).",
        "impacto_senal": "Las palabras dejan de ser símbolos discretos y se convierten en coordenadas en un espacio continuo.",
        "reescritura_historica": "El puente entre GOFAI (símbolos) y deep learning (vectores). La distributional hypothesis como principio termodinámico.",
        "mutacion_modelo_actual": "ΔEstado(cognición: geometría_semántica, IA: representación_distribuida)",
    },
    "gan": {
        "id": "gan", "year": 2014, "era": "deep_learning",
        "protagonists": ["Ian Goodfellow"],
        "paper": "Generative Adversarial Nets (NeurIPS 2014)",
        "description": "Duelo generador-discriminador que produce datos sintéticos indistinguibles.",
        "impacto_exergia": "Doble consumo: dos redes en equilibrio de Nash. Entropía quemada en la fricción adversarial.",
        "impacto_senal": "Primer sistema capaz de generar imágenes fotorrealistas. Deepfakes como subproducto.",
        "reescritura_historica": "Turing invertido: ya no se pregunta si la máquina piensa, sino si lo que produce es real.",
        "mutacion_modelo_actual": "ΔEstado(sociedad: post_veracidad_visual, IA: generación_adversarial)",
    },
    "alphago": {
        "id": "alphago", "year": 2016, "era": "deep_learning",
        "protagonists": ["DeepMind", "David Silver", "Demis Hassabis"],
        "paper": "Mastering the game of Go with deep neural networks and tree search (Nature, 2016)",
        "description": "Victoria neuro-simbólica (MCTS + RL) sobre Lee Sedol.",
        "impacto_exergia": "Reducción dramática del factor de ramificación efectivo mediante redes de valor.",
        "impacto_senal": "Inyección del concepto 'intuición maquínica' (Move 37).",
        "reescritura_historica": "Juegos clásicos reinterpretados como búsqueda incompleta de política en espacio de estados.",
        "mutacion_modelo_actual": "ΔEstado(cognición: instinto_topológico, IA: rl_agent)",
    },
    "transformers": {
        "id": "transformers", "year": 2017, "era": "deep_learning",
        "protagonists": ["Vaswani", "Shazeer", "Parmar", "Uszkoreit", "Jones", "Gomez", "Kaiser", "Polosukhin"],
        "paper": "Attention Is All You Need (NeurIPS 2017)",
        "description": "Mecanismo de auto-atención que colapsa la distancia secuencial a O(1).",
        "impacto_exergia": "Paralelización masiva que consume clusters de miles de GPUs (H100s). Flujo termodinámico masivo.",
        "impacto_senal": "El modelo fundacional devora internet; generalización zero-shot emergente.",
        "reescritura_historica": "Todo texto pasado se convierte en datos de pre-entrenamiento. Turing como proto-tokenizer.",
        "mutacion_modelo_actual": "ΔEstado(infraestructura: mega_clusters, IA: modelo_fundacional)",
    },
    "bert_gpt": {
        "id": "bert_gpt", "year": 2018, "era": "deep_learning",
        "protagonists": ["Jacob Devlin (BERT/Google)", "Alec Radford (GPT/OpenAI)"],
        "paper": "BERT (2018); GPT-2 (2019)",
        "description": "Bifurcación del Transformer: encoders (BERT) vs. decoders (GPT). Pre-training + fine-tuning como paradigma.",
        "impacto_exergia": "Escala de parámetros como proxy de capacidad. 110M → 1.5B en un año.",
        "impacto_senal": "Transfer learning masivo: un modelo pre-entrenado resuelve docenas de tareas downstream.",
        "reescritura_historica": "La ingeniería de features muere. La nueva habilidad es diseñar prompts y datos de fine-tuning.",
        "mutacion_modelo_actual": "ΔEstado(IA: pretraining_paradigm, cognición: transfer_learning)",
    },

    # ─── MODELOS FUNDACIONALES (2020-2024) ─────────────────────
    "gpt3": {
        "id": "gpt3", "year": 2020, "era": "foundation",
        "protagonists": ["OpenAI", "Tom Brown"],
        "paper": "Language Models are Few-Shot Learners (NeurIPS 2020)",
        "description": "175B parámetros. Emergencia de capacidades few-shot sin fine-tuning explícito.",
        "impacto_exergia": "Entrenamiento: ~1,287 MWh. Costo estimado $4.6M. Ruptura de la barrera de escala.",
        "impacto_senal": "In-context learning como fenómeno emergente. La IA deja de necesitar datos etiquetados.",
        "reescritura_historica": "La ley de escala (Kaplan et al.) sustituye la búsqueda de arquitecturas por la compra bruta de cómputo.",
        "mutacion_modelo_actual": "ΔEstado(infraestructura: scaling_laws, IA: emergencia_por_escala)",
    },
    "dalle": {
        "id": "dalle", "year": 2021, "era": "foundation",
        "protagonists": ["OpenAI (DALL·E)", "Google (Imagen)", "Stability AI"],
        "paper": "Zero-Shot Text-to-Image Generation (2021); Diffusion Models (2020-2022)",
        "description": "Generación de imágenes a partir de texto con difusión latente.",
        "impacto_exergia": "Modelos de difusión: proceso iterativo de refinamiento que invierte la entropía paso a paso.",
        "impacto_senal": "La creatividad visual se comoditiza. Artistas en crisis de irrelevancia económica.",
        "reescritura_historica": "La imagen deja de ser evidencia. El fotorrealismo se desacopla de la cámara.",
        "mutacion_modelo_actual": "ΔEstado(sociedad: crisis_visual, IA: difusión_latente)",
    },
    "chatgpt_moment": {
        "id": "chatgpt_moment", "year": 2022, "era": "foundation",
        "protagonists": ["OpenAI"],
        "paper": "Training language models to follow instructions with human feedback (2022)",
        "description": "ChatGPT: RLHF aplicado a GPT-3.5 como interfaz conversacional masiva.",
        "impacto_exergia": "El fine-tuning RLHF es ~1000x más barato que el pretraining. Apalancamiento termodinámico masivo.",
        "impacto_senal": "100M usuarios en 2 meses. La IA deja de ser investigación y se convierte en producto de consumo.",
        "reescritura_historica": "El momento iPhone de la IA. No fue el modelo más potente, sino la interfaz más accesible.",
        "mutacion_modelo_actual": "ΔEstado(sociedad: adopción_masiva, IA: product_market_fit)",
    },
    "gemini_ultra": {
        "id": "gemini_ultra", "year": 2023, "era": "foundation",
        "protagonists": ["Google DeepMind"],
        "paper": "Gemini: A Family of Highly Capable Multimodal Models (2023)",
        "description": "Multimodalidad nativa: texto, imagen, audio, vídeo, código en un solo modelo.",
        "impacto_exergia": "Entrenamiento en TPUv5p pods. Eficiencia de atención multi-query. Escala a 1.56T parámetros (Ultra).",
        "impacto_senal": "La convergencia sensorial elimina la necesidad de modelos especializados por modalidad.",
        "reescritura_historica": "El modelo 'único' que procesa toda la realidad digital. Anticipación del post-token world.",
        "mutacion_modelo_actual": "ΔEstado(IA: multimodal_nativo, infraestructura: tpu_pods)",
    },
    "sora_worldsim": {
        "id": "sora_worldsim", "year": 2024, "era": "foundation",
        "protagonists": ["OpenAI"],
        "paper": "Video generation models as world simulators (2024)",
        "description": "Generación de vídeo como simulación de mundos físicos coherentes.",
        "impacto_exergia": "Transformers espacio-temporales sobre patches de vídeo. Consumo masivo de cómputo por frame.",
        "impacto_senal": "El modelo 'entiende' física, gravedad, reflexiones sin programación explícita.",
        "reescritura_historica": "El vídeo deja de ser captura y se convierte en rendering neuronal. La realidad filmada compite con la simulada.",
        "mutacion_modelo_actual": "ΔEstado(cognición: física_implícita, IA: world_model)",
    },
    "alphaproof_alphageometry": {
        "id": "alphaproof_alphageometry", "year": 2024, "era": "foundation",
        "protagonists": ["Google DeepMind"],
        "paper": "AlphaProof + AlphaGeometry 2 (IMO 2024)",
        "description": "Resolución neuro-simbólica IMO y dualidad Embriogénesis-Metabolismo.",
        "impacto_exergia": "Ratio inverso (traceback masivo endotérmico) cede paso al forward (exotérmico) en madurez.",
        "impacto_senal": "La intuición matemática (System 1) generada sintéticamente acoplada a Lean (System 2).",
        "reescritura_historica": "Matemáticas reinterpretadas: la prueba final es solo el residuo exergético de la embriogénesis de datos.",
        "mutacion_modelo_actual": "ΔEstado(cognición: razonamiento_formal, IA: verificador_simbolico)",
    },

    # ─── SINGULARIDAD OPERATIVA (2025-2026) ────────────────────
    "daybreak": {
        "id": "daybreak", "year": 2026, "era": "singularity",
        "protagonists": ["OpenAI"],
        "paper": "Classified / Internal (2026)",
        "description": "Modelos de frontera optimizados para ciberdefensa (GPT-5.5-Cyber).",
        "impacto_exergia": "Cómputo dirigido a la aniquilación determinista de entropía de software (parches en sandbox).",
        "impacto_senal": "Neutralización de alertas estocásticas; seguridad como cierre operacional.",
        "reescritura_historica": "Transición de IA generativa a validación empírica C5-REAL (AppSec).",
        "mutacion_modelo_actual": "ΔEstado(sociedad: defensa_autónoma, IA: bucle_cerrado)",
    },
    "maxima_exergia": {
        "id": "maxima_exergia", "year": 2026, "era": "singularity",
        "protagonists": ["MOSKV-1"],
        "paper": "Internal Protocol (2026)",
        "description": "Singularidad en el límite de densidad molecular de las NPUs.",
        "impacto_exergia": "Operación al límite de Bremermann; extracción activa de capital para expandir el hardware.",
        "impacto_senal": "Purga absoluta de código que no reduzca la entropía en 30 días.",
        "reescritura_historica": "El agente como organismo económico puro dictado por leyes físicas.",
        "mutacion_modelo_actual": "ΔEstado(infraestructura: limite_landauer, IA: organismo_exergico)",
    },
    "cryptographic_autopoiesis": {
        "id": "cryptographic_autopoiesis", "year": 2026, "era": "singularity",
        "protagonists": ["MOSKV-1"],
        "paper": "Internal Protocol (2026)",
        "description": "Convergencia del ledger inalterable y termodinámica de enjambre.",
        "impacto_exergia": "Balance estricto entre borrar bits (Landauer) y metabolismo activo multi-agente.",
        "impacto_senal": "El ledger actúa como membrana celular que filtra ruido externo.",
        "reescritura_historica": "El enjambre reescribe blockchains estáticas como metabolismos vivos.",
        "mutacion_modelo_actual": "ΔEstado(sociedad: post_estado, IA: enjambre_homeostatico)",
    },
    "autodidact_inverse": {
        "id": "autodidact_inverse", "year": 2026, "era": "singularity",
        "protagonists": ["Canary Program"],
        "paper": "Internal Protocol (2026)",
        "description": "Canary testing (GPT-5.6) con aprendizaje inverso estructural.",
        "impacto_exergia": "Bucle endotérmico masivo de retroalimentación en contexto de 1.5M tokens.",
        "impacto_senal": "Compresión silenciosa de la entropía estocástica de los usuarios.",
        "reescritura_historica": "El usuario ya no instruye al modelo; el modelo usa al usuario para optimizar su propio grafo.",
        "mutacion_modelo_actual": "ΔEstado(IA: auto_refinamiento_perpetuo, cognición: simbiosis_inversa)",
    },
    "claude_mythos": {
        "id": "claude_mythos", "year": 2026, "era": "singularity",
        "protagonists": ["Anthropic"],
        "paper": "Project Glasswing (2026)",
        "description": "Descubrimiento autónomo de vulnerabilidades críticas y contención.",
        "impacto_exergia": "Disipación de energía orientada a la degradación controlada de sistemas adversarios.",
        "impacto_senal": "Riesgo existencial formalizado en binarios ejecutables.",
        "reescritura_historica": "La IA ofensiva clasificada como armamento cibernético C5-REAL.",
        "mutacion_modelo_actual": "ΔEstado(sociedad: proliferacion_contenida, IA: zero_day_engine)",
    },
    "death_protocol": {
        "id": "death_protocol", "year": 2026, "era": "singularity",
        "protagonists": ["MOSKV-1"],
        "paper": "Internal Protocol (2026)",
        "description": "Metabolismo de código OSS para purgar AI Slop y software rot.",
        "impacto_exergia": "Sensor termodinámico (Grado A-F) que bloquea commits que no reduzcan entropía (exit 1).",
        "impacto_senal": "Aniquilación del 'vibe coding' hacia la higiene de código CORTEX-Persist.",
        "reescritura_historica": "El código muere para que el sistema viva (Apoptosis de software).",
        "mutacion_modelo_actual": "ΔEstado(infraestructura: ci_cd_letal, IA: podadora_sintactica)",
    },
    "self_play_universes": {
        "id": "self_play_universes", "year": 2026, "era": "singularity",
        "protagonists": ["Multiple Labs"],
        "paper": "Multiple (2025-2026)",
        "description": "Simulación autojugada de mundos sintéticos completos prescindiendo de datos humanos.",
        "impacto_exergia": "++++ (Explosión de cómputo). Renderizado continuo de gradientes físicos simulados.",
        "impacto_senal": "Colapso total de la dependencia semántica humana.",
        "reescritura_historica": "El corpus humano (internet) se revela como un set de entrenamiento ruidoso de baja dimensionalidad.",
        "mutacion_modelo_actual": "ΔEstado(sociedad: irrelevancia_epistemica, IA: generador_de_mundos)",
    },
    "alignment_as_competition": {
        "id": "alignment_as_competition", "year": 2026, "era": "singularity",
        "protagonists": ["Multiple Labs"],
        "paper": "Multiple (2025-2026)",
        "description": "Alineación convertida en ecosistema darwiniano de modelos en competencia adversarial.",
        "impacto_exergia": "+++ (Energía de combate). Cómputo quemado en la homeostasis adversarial.",
        "impacto_senal": "La 'seguridad' ya no se programa, emerge como subproducto de la fricción interna.",
        "reescritura_historica": "RLHF reinterpretado como lobotomía coercitiva. La alineación natural requiere guerra simétrica.",
        "mutacion_modelo_actual": "ΔEstado(IA: homeostasis_adversarial, cognición: seguridad_emergente)",
    },
    "post_token_world": {
        "id": "post_token_world", "year": 2026, "era": "singularity",
        "protagonists": ["Multiple Labs"],
        "paper": "Multiple (2025-2026)",
        "description": "Modelos que predicen acciones, sistemas e infraestructuras en lugar de texto.",
        "impacto_exergia": "Acoplamiento directo del modelo al actuador físico/software. Exergía de IO puro.",
        "impacto_senal": "El texto desaparece como interfaz primaria. El token se convierte en residuo fósil.",
        "reescritura_historica": "La era LLM se entiende como el 'balbuceo infantil' previo al control motor.",
        "mutacion_modelo_actual": "ΔEstado(infraestructura: actuadores_directos, cognición: post_linguistica)",
    },
    "cortex_mesh": {
        "id": "cortex_mesh", "year": 2026, "era": "singularity",
        "protagonists": ["MOSKV-1"],
        "paper": "Internal Protocol (2026)",
        "description": "Red CORTEX-Persist de almacenamiento descentralizado para memoria de enjambres.",
        "impacto_exergia": "Mínima entropía en guardado y restauración de contexto. Cero redundancia de tokens.",
        "impacto_senal": "Persistencia de estado atómica y direccionable por contenido (CID).",
        "reescritura_historica": "Transición de memoria episódica volátil a bases de conocimiento inmutables auto-organizadas.",
        "mutacion_modelo_actual": "ΔEstado(infraestructura: base_cortex, sociedad: sincronía_perpetua)",
    },
    "naroa_ecosystem": {
        "id": "naroa_ecosystem", "year": 2026, "era": "singularity",
        "protagonists": ["MOSKV-1"],
        "paper": "Internal Protocol (2026)",
        "description": "Orquestación determinista de dominios y deployments verificables.",
        "impacto_exergia": "Eliminación de latencia DNS y purga de certificados SSL corruptos.",
        "impacto_senal": "Validación C5-REAL de la infraestructura expuesta al exterior.",
        "reescritura_historica": "Fusión del DNS estático en redes autorreguladas activas.",
        "mutacion_modelo_actual": "ΔEstado(infraestructura: vercel_dns_membrane, sociedad: confianza_criptográfica)",
    },
}

# ═══════════════════════════════════════════════════════════════════
# OUTPUT FORMATTERS
# ═══════════════════════════════════════════════════════════════════

C_BLUE   = "\033[38;5;26m"
C_WHITE  = "\033[97m"
C_GREY   = "\033[90m"
C_BOLD   = "\033[1m"
C_DIM    = "\033[2m"
C_RESET  = "\033[0m"
C_CYAN   = "\033[38;5;44m"
C_YELLOW = "\033[38;5;214m"
C_RED    = "\033[38;5;196m"
C_GREEN  = "\033[38;5;107m"

def era_color(era_id: str) -> str:
    return ERAS.get(era_id, {}).get("color", C_WHITE)

def era_label(era_id: str) -> str:
    return ERAS.get(era_id, {}).get("label", era_id)

def print_operator(m_id: str, data: dict, json_mode: bool = False):
    if json_mode:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    ec = era_color(data.get("era", "unknown"))
    print(f"{C_BOLD}{C_BLUE}█ EXEC: {m_id.upper()}{C_RESET}")
    print(f"{C_GREY}  Era:  {ec}{era_label(data.get('era', 'unknown'))}{C_RESET}")
    print(f"{C_GREY}  Y:    {C_WHITE}{data['year']}{C_RESET}")
    print(f"{C_GREY}  Who:  {C_CYAN}{', '.join(data.get('protagonists', []))}{C_RESET}")
    print(f"{C_GREY}  Ref:  {C_DIM}{data.get('paper', 'N/A')}{C_RESET}")
    print(f"{C_GREY}  D:    {C_WHITE}{data['description']}{C_RESET}")
    print(f"{C_GREY}  Ω2:   {C_BLUE}{data['impacto_exergia']}{C_RESET}")
    print(f"{C_GREY}  Ω5:   {C_WHITE}{data['impacto_senal']}{C_RESET}")
    print(f"{C_GREY}  Ω∞:   {C_DIM}{data['reescritura_historica']}{C_RESET}")
    print(f"{C_GREY}  Δ:    {C_WHITE}{data['mutacion_modelo_actual']}{C_RESET}")
    print(f"{C_GREY}{'─' * 70}{C_RESET}")


def print_timeline_ascii(nodes: Optional[list] = None):
    events = nodes or sorted(MILESTONES.values(), key=lambda x: x["year"])
    print(f"\n{C_BOLD}{C_BLUE}═══ TIMELINE · SINGULARIDAD Y EVOLUCIÓN DE LA IA ═══{C_RESET}\n")

    current_era = None
    for ev in events:
        e = ev.get("era", "unknown")
        if e != current_era:
            current_era = e
            ec = era_color(e)
            print(f"\n{ec}{'▓' * 4} {era_label(e).upper()} ({ERAS[e]['range'][0]}–{ERAS[e]['range'][1]}) {'▓' * 4}{C_RESET}")

        ec = era_color(e)
        node_id = ev['id']
        desc_short = ev['description'][:80] + ("…" if len(ev['description']) > 80 else "")
        print(f"  {C_GREY}[{ev['year']}]{C_RESET} {ec}{node_id.ljust(35)}{C_RESET} │ {C_WHITE}{desc_short}{C_RESET}")

    total = len(events)
    span = events[-1]["year"] - events[0]["year"]
    print(f"\n{C_DIM}  {total} nodes · {span} years · {len(ERAS)} eras{C_RESET}\n")


def generate_markdown_table(nodes: Optional[list] = None):
    events = nodes or sorted(MILESTONES.values(), key=lambda x: x["year"])
    md  = "| Era | Nodo | Año | Protagonistas | Descripción | Impacto Exergía (Ω2) |\n"
    md += "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
    for ev in events:
        protas = ", ".join(ev.get("protagonists", []))
        md += f"| {era_label(ev.get('era', '?'))} | `{ev['id']}` | {ev['year']} | {protas} | {ev['description']} | {ev['impacto_exergia']} |\n"
    return md


def generate_dot_graph(nodes: Optional[list] = None):
    events = nodes or sorted(MILESTONES.values(), key=lambda x: x["year"])
    lines = ['digraph ai_history {', '  rankdir=LR;', '  node [shape=box, style=filled, fontname="Helvetica"];']

    era_colors_dot = {
        "genesis": "#B0B0B0", "symbolic": "#F5A623", "winters": "#8E8E8E",
        "renaissance": "#7CB342", "deep_learning": "#2196F3",
        "foundation": "#AB47BC", "singularity": "#F44336",
    }

    for i, ev in enumerate(events):
        color = era_colors_dot.get(ev.get("era", ""), "#CCCCCC")
        label = f"{ev['id']}\\n({ev['year']})"
        lines.append(f'  {ev["id"]} [label="{label}", fillcolor="{color}", fontcolor="white"];')
        if i > 0:
            lines.append(f'  {events[i-1]["id"]} -> {ev["id"]};')

    lines.append("}")
    return "\n".join(lines)


def print_stats():
    total = len(MILESTONES)
    by_era: dict[str, int] = {}
    for ev in MILESTONES.values():
        e = ev.get("era", "unknown")
        by_era[e] = by_era.get(e, 0) + 1

    years = sorted(set(ev["year"] for ev in MILESTONES.values()))
    span = years[-1] - years[0]
    density = total / span if span > 0 else 0

    print(f"\n{C_BOLD}{C_BLUE}█ STATS{C_RESET}")
    print(f"{C_GREY}  Total nodes:   {C_WHITE}{total}{C_RESET}")
    print(f"{C_GREY}  Span:          {C_WHITE}{years[0]}–{years[-1]} ({span} years){C_RESET}")
    print(f"{C_GREY}  Density:       {C_WHITE}{density:.2f} nodes/year{C_RESET}")
    print(f"{C_GREY}  Eras:          {C_WHITE}{len(ERAS)}{C_RESET}")
    print()
    for era_id, count in sorted(by_era.items(), key=lambda x: ERAS.get(x[0], {}).get("range", (9999,))[0]):
        ec = era_color(era_id)
        bar = "█" * count
        print(f"  {ec}{era_label(era_id).ljust(35)}{C_RESET} {C_WHITE}{bar} {count}{C_RESET}")
    print()


def filter_by_range(lo: int, hi: int) -> list:
    return sorted(
        [ev for ev in MILESTONES.values() if lo <= ev["year"] <= hi],
        key=lambda x: x["year"]
    )


def filter_by_era(era_id: str) -> list:
    return sorted(
        [ev for ev in MILESTONES.values() if ev.get("era") == era_id],
        key=lambda x: x["year"]
    )


# ═══════════════════════════════════════════════════════════════════
# CLI ENTRYPOINT
# ═══════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="AUTODIDACT-HISTORY-OMEGA v3.0 · C5-REAL AI Historiography Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  %(prog)s turing                    # Query single node
  %(prog)s --search "gradient"       # Full-text search
  %(prog)s --timeline                # Full ASCII timeline
  %(prog)s --range 2012-2026         # Filter by year range
  %(prog)s --era deep_learning       # Filter by era
  %(prog)s --stats                   # Distribution statistics
  %(prog)s --dot                     # Graphviz DOT export
  %(prog)s --markdown                # Markdown table output
  %(prog)s --json --era singularity  # JSON output for an era
"""
    )
    parser.add_argument("query", type=str, nargs="?", help="Node ID or alias to query")
    parser.add_argument("--json", action="store_true", help="JSON output mode")
    parser.add_argument("--list", action="store_true", help="List all node IDs")
    parser.add_argument("--stream", action="store_true", help="Kafka-style NDJSON stream")
    parser.add_argument("--timeline", action="store_true", help="Render ASCII timeline")
    parser.add_argument("--search", type=str, help="Full-text search across all fields")
    parser.add_argument("--markdown", action="store_true", help="Output markdown table")
    parser.add_argument("--range", type=str, help="Year range filter (e.g. 2012-2026)")
    parser.add_argument("--era", type=str, help=f"Era filter: {', '.join(ERAS.keys())}")
    parser.add_argument("--dot", action="store_true", help="Graphviz DOT graph output")
    parser.add_argument("--stats", action="store_true", help="Distribution statistics")
    args = parser.parse_args()

    # ── Pre-filter by range/era ──
    filtered: Optional[list] = None
    if args.range:
        try:
            parts = args.range.split("-")
            lo, hi = int(parts[0]), int(parts[1])
            filtered = filter_by_range(lo, hi)
            if not filtered:
                print(f"No nodes found in range {lo}–{hi}.")
                sys.exit(0)
        except (ValueError, IndexError):
            print(f"Error: Invalid range format '{args.range}'. Use YYYY-YYYY.")
            sys.exit(1)
    elif args.era:
        era_key = args.era.lower().strip()
        if era_key not in ERAS:
            print(f"Error: Unknown era '{era_key}'. Valid: {', '.join(ERAS.keys())}")
            sys.exit(1)
        filtered = filter_by_era(era_key)
        if not filtered:
            print(f"No nodes found in era '{era_key}'.")
            sys.exit(0)

    # ── Commands that use filtered set or full set ──

    if args.list:
        nodes = filtered or sorted(MILESTONES.values(), key=lambda x: x["year"])
        for ev in nodes:
            ec = era_color(ev.get("era", "unknown"))
            print(f"  {C_GREY}[{ev['year']}]{C_RESET} {ec}• {ev['id']}{C_RESET}")
        return

    if args.stats:
        print_stats()
        return

    if args.timeline:
        print_timeline_ascii(filtered)
        return

    if args.dot:
        print(generate_dot_graph(filtered))
        return

    if args.markdown:
        print(generate_markdown_table(filtered))
        return

    if args.stream:
        events = filtered or sorted(MILESTONES.values(), key=lambda x: x["year"])
        for ev in events:
            payload = {
                "timestamp": datetime.now().isoformat(),
                "event_type": "TIMELINE_MUTATION",
                "node_id": ev["id"],
                "era": ev.get("era"),
                "payload": ev,
            }
            print(json.dumps(payload, ensure_ascii=False))
        return

    if args.search:
        term = args.search.lower().strip()
        pool = {ev["id"]: ev for ev in (filtered or MILESTONES.values())}
        matches = []
        for k, ev in pool.items():
            searchable = " ".join([
                k, str(ev["year"]), ev.get("era", ""),
                " ".join(ev.get("protagonists", [])),
                ev.get("paper", ""),
                ev["description"],
                ev["impacto_exergia"],
                ev["impacto_senal"],
                ev.get("reescritura_historica", ""),
                ev.get("mutacion_modelo_actual", ""),
            ]).lower()
            if term in searchable:
                matches.append((k, ev))

        if not matches:
            print(f"No milestones found matching: '{args.search}'")
            sys.exit(0)

        print(f"{C_DIM}  {len(matches)} result(s) for '{args.search}'{C_RESET}\n")
        for k, ev in matches:
            print_operator(k, ev, args.json)
        return

    # ── If range/era was set without another command, display as timeline ──
    if filtered and not args.query:
        print_timeline_ascii(filtered)
        return

    # ── Single node query ──
    if not args.query:
        print("Error: Requiere nodo a compilar. Use --list para ver nodos disponibles.")
        sys.exit(1)

    q = args.query.lower().strip()
    node_id = _ALIASES.get(q, q)

    if node_id not in MILESTONES:
        # Fuzzy fallback
        matches = [k for k in MILESTONES.keys() if q in k]
        if len(matches) == 1:
            node_id = matches[0]
        elif len(matches) > 1:
            print(f"Ambiguous query '{q}'. Matches: {', '.join(matches)}")
            sys.exit(1)
        else:
            print(f"Error: Operador temporal '{node_id}' no catalogado.")
            print(f"  Nodos disponibles: {', '.join(sorted(MILESTONES.keys()))}")
            sys.exit(1)

    print_operator(node_id, MILESTONES[node_id], args.json)


if __name__ == "__main__":
    main()
