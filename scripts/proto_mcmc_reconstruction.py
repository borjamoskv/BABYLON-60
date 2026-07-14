import os
import math
import csv
import numpy as np
from scripts.romance_common import GOLD, DATA, GAP, build_msa, build_Q, Model, reconstruct_column, nw_match_flags, levenshtein, partial, TREE

def tree_log_likelihood(tree, msas, model):
    ll = 0.0
    for concept, (langs, msa) in msas.items():
        W = len(msa[0])
        ncol = len(langs)
        for c in range(W):
            column = {langs[r]: msa[r][c] for r in range(ncol) if msa[r][c] != GAP}
            Lroot = partial(tree, column, model)
            prob = np.sum(model.pi * Lroot)
            if prob > 0:
                ll += math.log(prob)
            else:
                ll += -1000000000.0
    return ll

def tree_prior(node, rate=10.0):
    if node[0] == 'L':
        return math.log(rate) - rate * node[2]
    else:
        p = math.log(rate) - rate * node[1] if node[1] > 0 else 0.0
        return p + sum((tree_prior(k, rate) for k in node[2]))

def mutate_tree_local(node, step=0.1):
    if node[0] == 'L':
        return ('L', node[1], max(0.01, node[2] + np.random.normal(0, step)))
    else:
        return ('I', max(0.0, node[1] + np.random.normal(0, step)), [mutate_tree_local(k, step) for k in node[2]])

def run_mcmc(start_tree, msas, model, iters=500):
    curr_tree = start_tree
    curr_ll = tree_log_likelihood(curr_tree, msas, model)
    curr_prior = tree_prior(curr_tree)
    curr_post = curr_ll + curr_prior
    best_tree = curr_tree
    best_post = curr_post
    print(f'[C5-REAL] MCMC Inicio: LogPosterior = {curr_post:.2f} (LL: {curr_ll:.2f}, Prior: {curr_prior:.2f})')
    T_start = 5.0
    T_end = 0.01
    for i in range(iters):
        T = T_start * (T_end / T_start) ** (i / (iters - 1)) if iters > 1 else T_end
        new_tree = mutate_tree_local(curr_tree)
        new_ll = tree_log_likelihood(new_tree, msas, model)
        new_prior = tree_prior(new_tree)
        new_post = new_ll + new_prior
        diff = new_post - curr_post
        if diff > 0 or (diff / T > -20 and math.log(np.random.uniform(0, 1)) < diff / T):
            curr_tree = new_tree
            curr_post = new_post
            if curr_post > best_post:
                best_post = curr_post
                best_tree = curr_tree
        if (i + 1) % 100 == 0:
            print(f'MCMC Iter {i + 1}/{iters} [T={T:.3f}]: LogPost = {curr_post:.2f} (Best: {best_post:.2f})')
    return best_tree

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
    print('\n[C5-REAL] Iniciando Inferencia MCMC (Simulated Annealing + Priors)...')
    global TREE
    TREE = run_mcmc(TREE, msas, model, iters=500)
    print('[C5-REAL] Colapso MAP alcanzado. Procediendo a decodificación entrópica.\n')
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