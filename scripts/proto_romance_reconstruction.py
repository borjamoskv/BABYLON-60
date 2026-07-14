import os
import math
import csv
import numpy as np
from scipy.linalg import expm
GOLD = {'key': 'k l a v e', 'night': 'n o k t e', 'eight': 'o k t o', 'milk': 'l a k t e', 'to_do': 'f a k e r e', 'fire': 'f o k u', 'hundred': 'k e n t u', 'moon': 'l u n a', 'sea': 'm a r e', 'flower': 'f l o r e', 'to_sing': 'k a n t a r e', 'dog': 'k a n e', 'to_have': 'h a b e r e', 'water': 'a k w a', 'to_die': 'm o r i r e', 'name': 'n o m e n', 'new': 'n o v u', 'to_love': 'a m a r e'}
DATA = {'key': {'es': 'L a v e', 'pt': 'S a v e', 'fr': 'k l e', 'it': 'k j a v e', 'ro': 'k e j e', 'sc': 'k r a e'}, 'night': {'es': 'n o C e', 'pt': 'n o j t e', 'fr': 'n w i', 'it': 'n o t e', 'ro': 'n o a p t e', 'sc': 'n o t e'}, 'eight': {'es': 'o C o', 'pt': 'o j t o', 'fr': 'w i t', 'it': 'o t o', 'ro': 'o p t', 'sc': 'o t o'}, 'milk': {'es': 'l e C e', 'pt': 'l e j t e', 'fr': 'l e', 'it': 'l a t e', 'ro': 'l a p t e', 'sc': 'l a t e'}, 'to_do': {'es': 'a s e r', 'pt': 'f a z e r', 'fr': 'f e r', 'it': 'f a r e', 'ro': 'f a C e'}, 'fire': {'es': 'f w e g o', 'pt': 'f o g o', 'it': 'f w o k o', 'ro': 'f o k', 'sc': 'f o g u'}, 'hundred': {'es': 's j e n', 'fr': 's a n', 'it': 'C e n t o', 'ro': 's u t e'}, 'moon': {'es': 'l u n a', 'pt': 'l u a', 'fr': 'l y n', 'it': 'l u n a', 'ro': 'l u n a', 'sc': 'l u n a'}, 'sea': {'es': 'm a r', 'pt': 'm a r', 'fr': 'm e r', 'it': 'm a r e', 'ro': 'm a r e', 'sc': 'm a r e'}, 'flower': {'es': 'f l o r', 'pt': 'f l o r', 'it': 'f j o r e', 'ro': 'f l o a r e'}, 'to_sing': {'es': 'k a n t a r', 'pt': 'k a n t a r', 'fr': 'S a n t e', 'it': 'k a n t a r e', 'ro': 'k a n t a'}, 'dog': {'es': 'k a n', 'fr': 'S j e n', 'it': 'k a n e', 'ro': 'k a i n e', 'sc': 'k a n e'}, 'to_have': {'es': 'a b e r', 'pt': 'a v e r', 'fr': 'a v w a r', 'it': 'a v e r e', 'ro': 'a v e a'}, 'water': {'es': 'a g w a', 'pt': 'a g w a', 'it': 'a k w a', 'ro': 'a p e', 'sc': 'a b a'}, 'to_die': {'es': 'm o r i r', 'pt': 'm o r e r', 'fr': 'm u r i r', 'it': 'm o r i r e', 'ro': 'm u r i'}, 'name': {'es': 'n o m b r e', 'pt': 'n o m e', 'fr': 'n o n', 'it': 'n o m e', 'ro': 'n u m e'}, 'new': {'es': 'n w e v o', 'pt': 'n o v o', 'it': 'n w o v o', 'ro': 'n o u', 'sc': 'n o b u'}, 'to_love': {'es': 'a m a r', 'pt': 'a m a r', 'fr': 'e m e', 'it': 'a m a r e', 'ro': 'a m a'}}
GAP = '-'
FEAT = {'p': ('C', 0, 0, 0), 'b': ('C', 0, 0, 1), 'f': ('C', 0, 1, 0), 'v': ('C', 0, 1, 1), 'm': ('C', 0, 3, 1), 'w': ('C', 0, 6, 1), 't': ('C', 1, 0, 0), 'd': ('C', 1, 0, 1), 's': ('C', 1, 1, 0), 'z': ('C', 1, 1, 1), 'n': ('C', 1, 3, 1), 'l': ('C', 1, 4, 1), 'r': ('C', 1, 5, 1), 'S': ('C', 2, 1, 0), 'Z': ('C', 2, 1, 1), 'C': ('C', 2, 2, 0), 'G': ('C', 2, 2, 1), 'J': ('C', 3, 3, 1), 'L': ('C', 3, 4, 1), 'j': ('C', 3, 6, 1), 'k': ('C', 4, 0, 0), 'g': ('C', 4, 0, 1), 'h': ('C', 5, 1, 0), 'a': ('V', 2, 1, 0), 'e': ('V', 1, 0, 0), 'i': ('V', 0, 0, 0), 'o': ('V', 1, 2, 1), 'u': ('V', 0, 2, 1), 'y': ('V', 0, 0, 1)}

def phon_dist(a, b):
    if a == b:
        return 0.0
    fa, fb = (FEAT[a], FEAT[b])
    if fa[0] != fb[0]:
        return 3.0
    if fa[0] == 'C':
        return 1.0 * min(abs(fa[1] - fb[1]), 3) / 3.0 + 1.5 * (0 if fa[2] == fb[2] else 1) + 0.5 * abs(fa[3] - fb[3])
    else:
        return 1.0 * abs(fa[1] - fb[1]) / 2.0 + 1.0 * abs(fa[2] - fb[2]) / 2.0 + 0.5 * abs(fa[3] - fb[3])
GAP_PEN = -1.0

def sub_score(a, b):
    if a == GAP or b == GAP:
        return GAP_PEN
    return 2.0 - phon_dist(a, b)

def col_score(column, seg):
    vals = [sub_score(x, seg) if x != GAP else GAP_PEN for x in column]
    return sum(vals) / len(vals)

def align_seq_to_msa(msa_rows, seq):
    W = len(msa_rows[0]) if msa_rows else 0
    n = len(seq)
    cols = [[row[c] for row in msa_rows] for c in range(W)]
    NEG = -1000000000.0
    dp = np.full((W + 1, n + 1), NEG)
    bt = np.zeros((W + 1, n + 1), dtype=int)
    dp[0, 0] = 0.0
    for i in range(1, W + 1):
        dp[i, 0] = dp[i - 1, 0] + GAP_PEN
        bt[i, 0] = 1
    for j in range(1, n + 1):
        dp[0, j] = dp[0, j - 1] + GAP_PEN
        bt[0, j] = 2
    for i in range(1, W + 1):
        for j in range(1, n + 1):
            diag = dp[i - 1, j - 1] + col_score(cols[i - 1], seq[j - 1])
            up = dp[i - 1, j] + GAP_PEN
            left = dp[i, j - 1] + GAP_PEN
            best = max(diag, up, left)
            dp[i, j] = best
            bt[i, j] = 0 if best == diag else 1 if best == up else 2
    i, j = (W, n)
    new_cols = []
    while i > 0 or j > 0:
        b = bt[i, j]
        if i > 0 and j > 0 and (b == 0):
            new_cols.append((cols[i - 1], seq[j - 1]))
            i -= 1
            j -= 1
        elif i > 0 and (j == 0 or b == 1):
            new_cols.append((cols[i - 1], GAP))
            i -= 1
        else:
            new_cols.append((None, seq[j - 1]))
            j -= 1
    new_cols.reverse()
    R = len(msa_rows)
    out = [[] for _ in range(R + 1)]
    for col, seg in new_cols:
        if col is None:
            for r in range(R):
                out[r].append(GAP)
            out[R].append(seg)
        else:
            for r in range(R):
                out[r].append(col[r])
            out[R].append(seg)
    return out

def build_msa(forms):
    order = sorted(range(len(forms)), key=lambda k: -len(forms[k][1]))
    langs = [forms[order[0]][0]]
    msa = [list(forms[order[0]][1])]
    for k in order[1:]:
        lang, seq = forms[k]
        msa = align_seq_to_msa(msa, list(seq))
        langs.append(lang)
    return (langs, msa)

def L(name, length):
    return ('L', name, length)

def I(length, kids):
    return ('I', length, kids)
TREE = I(0.0, [L('sc', 0.35), L('ro', 0.85), I(0.15, [L('it', 0.45), I(0.15, [L('fr', 0.95), I(0.15, [L('es', 0.5), L('pt', 0.5)])])])])

def node_len(node):
    return node[2] if node[0] == 'L' else node[1]
LAMBDA = 1.4
GAP_EXCH = 0.05

def build_Q(states, pi):
    S = len(states)
    idx = {s: i for i, s in enumerate(states)}
    R = np.zeros((S, S))
    for a in states:
        for b in states:
            if a == b:
                continue
            if a == GAP or b == GAP:
                R[idx[a], idx[b]] = GAP_EXCH
            else:
                R[idx[a], idx[b]] = math.exp(-LAMBDA * phon_dist(a, b))
    Q = np.zeros((S, S))
    for i in range(S):
        for j in range(S):
            if i != j:
                Q[i, j] = R[i, j] * pi[j]
        Q[i, i] = -np.sum(Q[i, :])
    scale = -np.sum(pi * np.diag(Q))
    return (Q / scale, idx)

class Model:

    def __init__(self, states, pi, Q, idx):
        self.states, self.pi, self.Q, self.idx = (states, pi, Q, idx)
        self._P = {}

    def P(self, t):
        key = round(t, 6)
        if key not in self._P:
            self._P[key] = expm(self.Q * t)
        return self._P[key]

def partial(node, column, model):
    S = len(model.states)
    if node[0] == 'L':
        _, name, _ = node
        seg = column.get(name)
        v = np.ones(S)
        if seg is not None:
            v = np.zeros(S)
            v[model.idx[seg]] = 1.0
        return v
    _, _, kids = node
    Ln = np.ones(S)
    for ch in kids:
        Lc = partial(ch, column, model)
        Ln *= model.P(node_len(ch)).dot(Lc)
    return Ln

def reconstruct_column(column, model):
    Lroot = partial(TREE, column, model)
    post = model.pi * Lroot
    tot = post.sum()
    post = post / tot if tot > 0 else np.ones(len(post)) / len(post)
    ent = -np.sum([p * math.log2(p) for p in post if p > 0])
    top = int(np.argmax(post))
    return (model.states[top], ent, post)

def levenshtein(a, b):
    n, m = (len(a), len(b))
    d = np.zeros((n + 1, m + 1))
    for i in range(n + 1):
        d[i, 0] = i
    for j in range(m + 1):
        d[0, j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            d[i, j] = min(d[i - 1, j] + 1, d[i, j - 1] + 1, d[i - 1, j - 1] + (0 if a[i - 1] == b[j - 1] else 1))
    return int(d[n, m])

def nw_match_flags(recon, gold):
    n, m = (len(recon), len(gold))
    NEG = -1000000000.0
    dp = np.full((n + 1, m + 1), NEG)
    bt = np.zeros((n + 1, m + 1), dtype=int)
    dp[0, 0] = 0
    for i in range(1, n + 1):
        dp[i, 0] = dp[i - 1, 0] + GAP_PEN
        bt[i, 0] = 1
    for j in range(1, m + 1):
        dp[0, j] = dp[0, j - 1] + GAP_PEN
        bt[0, j] = 2
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            diag = dp[i - 1, j - 1] + sub_score(recon[i - 1], gold[j - 1])
            up = dp[i - 1, j] + GAP_PEN
            left = dp[i, j - 1] + GAP_PEN
            best = max(diag, up, left)
            dp[i, j] = best
            bt[i, j] = 0 if best == diag else 1 if best == up else 2
    i, j = (n, m)
    flags = [False] * n
    while i > 0 or j > 0:
        b = bt[i, j]
        if i > 0 and j > 0 and (b == 0):
            flags[i - 1] = recon[i - 1] == gold[j - 1]
            i -= 1
            j -= 1
        elif i > 0 and (j == 0 or b == 1):
            i -= 1
        else:
            j -= 1
    return flags

def main():
    outdir = os.path.dirname(os.path.abspath(__file__))
    msas = {}
    counts = {}
    for concept, langs_forms in DATA.items():
        forms = [(lg, f.split()) for lg, f in langs_forms.items()]
        langs, msa = build_msa(forms)
        msas[concept] = (langs, msa)
        for row in msa:
            for seg in row:
                counts[seg] = counts.get(seg, 0) + 1
    states = sorted(counts.keys())
    if GAP not in states:
        states.append(GAP)
        counts[GAP] = counts.get(GAP, 1)
    total = sum(counts.values())
    pi = np.array([counts[s] / total for s in states])
    Q, idx = build_Q(states, pi)
    model = Model(states, pi, Q, idx)
    rows_csv = []
    all_ent_match = []
    tot_gold = tot_editdist = tot_pos = tot_hit = 0
    per_concept = []
    for concept, (langs, msa) in msas.items():
        W = len(msa[0])
        ncol = len(langs)
        recon_full, ent_full = ([], [])
        for c in range(W):
            column = {langs[r]: msa[r][c] for r in range(ncol) if msa[r][c] != GAP}
            seg, ent, post = reconstruct_column(column, model)
            recon_full.append(seg)
            ent_full.append(ent)
        recon = [(s, e) for s, e in zip(recon_full, ent_full) if s != GAP]
        recon_seq = [s for s, _ in recon]
        recon_ent = [e for _, e in recon]
        gold = GOLD[concept].split()
        flags = nw_match_flags(recon_seq, gold)
        ed = levenshtein(recon_seq, gold)
        hit = sum(flags)
        for s, e, fl in zip(recon_seq, recon_ent, flags):
            all_ent_match.append((e, fl))
        tot_gold += len(gold)
        tot_editdist += ed
        tot_pos += len(recon_seq)
        tot_hit += hit
        acc = hit / len(gold) if gold else 0.0
        per_concept.append((concept, ' '.join(recon_seq), ' '.join(gold), round(np.mean(recon_ent), 3), ed, round(acc, 2)))
        rows_csv.append({'concepto': concept, 'reconstruido': ' '.join(recon_seq), 'latin_gold': ' '.join(gold), 'entropia_media_bits': round(float(np.mean(recon_ent)), 3), 'edit_distance': ed, 'acierto_segmento': round(acc, 2)})
    seg_acc = tot_hit / tot_pos
    norm_ed = tot_editdist / tot_gold
    ent_hit = np.mean([e for e, f in all_ent_match if f])
    ent_miss = np.mean([e for e, f in all_ent_match if not f])
    es = np.array([e for e, _ in all_ent_match])
    fs = np.array([0.0 if f else 1.0 for _, f in all_ent_match])
    corr = float(np.corrcoef(es, fs)[0, 1])
    csv_path = os.path.join(outdir, 'reconstruccion_resultados.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows_csv[0].keys()))
        w.writeheader()
        w.writerows(rows_csv)
    print('=' * 78)
    print('RECONSTRUCCIÓN PROTO-ROMANCE PROBABILÍSTICA — validación vs latín')
    print('=' * 78)
    print(f"{'concepto':<10}{'reconstruido':<16}{'latín (gold)':<16}{'H̄bits':>7}{'ed':>4}{'acc':>6}")
    print('-' * 78)
    for concept, rec, gold, ent, ed, acc in per_concept:
        print(f'{concept:<10}{rec:<16}{gold:<16}{ent:>7}{ed:>4}{acc:>6}')
    print('-' * 78)
    print(f'Acierto por segmento (vs latín) : {seg_acc:6.1%}')
    print(f'Edit distance normalizado       : {norm_ed:6.3f}  (0=perfecto)')
    print(f'Entropía media, aciertos        : {ent_hit:6.3f} bits')
    print(f'Entropía media, errores         : {ent_miss:6.3f} bits')
    print(f'corr(entropía, error)           : {corr:+.3f}')
    print()
    print('LECTURA: la entropía es la incertidumbre irreducible por posición.')
    print('Que sea MAYOR en los errores (y la correlación positiva) demuestra que')
    print("el modelo 'sabe lo que no sabe': donde el cambio fonético fusionó sonidos")
    print('y borró información, no hay raíz única recuperable — solo una distribución.')
    print(f'\nCSV escrito en: {csv_path}')
    return dict(seg_acc=seg_acc, norm_ed=norm_ed, ent_hit=float(ent_hit), ent_miss=float(ent_miss), corr=corr, n_sets=len(per_concept), n_states=len(states))
if __name__ == '__main__':
    main()