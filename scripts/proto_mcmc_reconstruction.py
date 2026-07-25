import logging
import csv
import math
import os
from typing import Any
import numpy as np
from numpy.typing import NDArray
from scripts.romance_common import DATA, GAP, GOLD, Model, build_msa, build_Q, levenshtein, nw_match_flags, partial, reconstruct_column
from scripts.romance_common import TREE as _INITIAL_TREE

def tree_log_likelihood(tree: Any, msas: dict[str, tuple[list[str], list[list[str]]]], model: Model) -> float:
    ll = 0.0
    for _concept, (langs, msa) in msas.items():
        W = len(msa[0])
        ncol = len(langs)
        for c in range(W):
            column: dict[str, str] = {langs[r]: msa[r][c] for r in range(ncol) if msa[r][c] != GAP}
            Lroot: NDArray[np.float64] = partial(tree, column, model)
            prob: float = float(np.sum(model.pi * Lroot))
            if prob > 0:
                ll += math.log(prob)
            else:
                ll += -1000000000.0
    return ll

def tree_prior(node: Any, rate: float=10.0) -> float:
    if node[0] == 'L':
        return float(math.log(rate) - rate * float(node[2]))
    else:
        p: float = float(math.log(rate) - rate * float(node[1])) if float(node[1]) > 0 else 0.0
        return float(p + sum((tree_prior(k, rate) for k in node[2])))

def mutate_tree_local(node: Any, step: float=0.1) -> Any:
    if node[0] == 'L':
        return ('L', node[1], max(0.01, node[2] + float(np.random.normal(0, step))))
    else:
        return ('I', max(0.0, node[1] + float(np.random.normal(0, step))), [mutate_tree_local(k, step) for k in node[2]])

def run_mcmc(start_tree: Any, msas: dict[str, tuple[list[str], list[list[str]]]], model: Model, iters: int=500) -> Any:
    curr_tree: Any = start_tree
    curr_ll = tree_log_likelihood(curr_tree, msas, model)
    curr_prior = tree_prior(curr_tree)
    curr_post = curr_ll + curr_prior
    best_tree: Any = curr_tree
    best_post = curr_post
    logging.info(f'[C5-REAL] MCMC Inicio: LogPosterior = {curr_post:.2f} (LL: {curr_ll:.2f}, Prior: {curr_prior:.2f})')
    T_start = 5.0
    T_end = 0.01
    for i in range(iters):
        T = T_start * (T_end / T_start) ** (i / (iters - 1)) if iters > 1 else T_end
        new_tree = mutate_tree_local(curr_tree)
        new_ll = tree_log_likelihood(new_tree, msas, model)
        new_prior = tree_prior(new_tree)
        new_post = new_ll + new_prior
        diff = new_post - curr_post
        if diff > 0 or (diff / T > -20 and math.log(float(np.random.uniform(0, 1))) < diff / T):
            curr_tree = new_tree
            curr_post = new_post
            if curr_post > best_post:
                best_post = curr_post
                best_tree = curr_tree
        if (i + 1) % 100 == 0:
            logging.info(f'MCMC Iter {i + 1}/{iters} [T={T:.3f}]: LogPost = {curr_post:.2f} (Best: {best_post:.2f})')
    return best_tree

def main() -> dict[str, Any]:
    outdir = os.path.dirname(os.path.abspath(__file__))
    msas: dict[str, tuple[list[str], list[list[str]]]] = {}
    counts: dict[str, int] = {}
    for concept, langs_forms in DATA.items():
        forms: list[tuple[str, list[str]]] = [(lg, f.split()) for lg, f in langs_forms.items()]
        langs, msa = build_msa(forms)
        msas[concept] = (langs, msa)
        for row in msa:
            for seg in row:
                counts[seg] = counts.get(seg, 0) + 1
    states: list[str] = sorted(counts.keys())
    if GAP not in states:
        states.append(GAP)
        counts[GAP] = counts.get(GAP, 1)
    total = sum(counts.values())
    pi: NDArray[np.float64] = np.array([counts[s] / total for s in states])
    Q, idx = build_Q(states, pi)
    model = Model(states, pi, Q, idx)
    logging.info('\n[C5-REAL] Iniciando Inferencia MCMC (Simulated Annealing + Priors)...')
    active_tree: Any = _INITIAL_TREE
    active_tree = run_mcmc(active_tree, msas, model, iters=500)
    logging.info('[C5-REAL] Colapso MAP alcanzado. Procediendo a decodificación entrópica.\n')
    rows_csv: list[dict[str, Any]] = []
    all_ent_match: list[tuple[int, bool]] = []
    tot_gold = tot_editdist = tot_pos = tot_hit = 0
    per_concept: list[tuple[str, str, str, int, int, float]] = []
    for concept, (langs, msa) in msas.items():
        W = len(msa[0])
        ncol = len(langs)
        recon_full: list[str] = []
        ent_full: list[float] = []
        for c in range(W):
            column: dict[str, str] = {langs[r]: msa[r][c] for r in range(ncol) if msa[r][c] != GAP}
            seg, ent, _post = reconstruct_column(column, model)
            recon_full.append(seg)
            ent_full.append(ent)
        recon: list[tuple[str, float]] = [(s, e) for s, e in zip(recon_full, ent_full, strict=False) if s != GAP]
        recon_seq: list[str] = [s for s, _ in recon]
        recon_ent: list[float] = [e for _, e in recon]
        gold: list[str] = GOLD[concept].split()
        flags: list[bool] = nw_match_flags(recon_seq, gold)
        ed: int = levenshtein(recon_seq, gold)
        hit: int = sum(flags)
        for _s, e, fl in zip(recon_seq, recon_ent, flags, strict=False):
            all_ent_match.append((e, fl))
        tot_gold += len(gold)
        tot_editdist += ed
        tot_pos += len(recon_seq)
        tot_hit += hit
        acc: float = hit / len(gold) if gold else 0.0
        per_concept.append((concept, ' '.join(recon_seq), ' '.join(gold), round(float(np.mean(recon_ent)), 3), ed, round(acc, 2)))
        rows_csv.append({'concepto': concept, 'reconstruido': ' '.join(recon_seq), 'latin_gold': ' '.join(gold), 'entropia_media_bits': round(float(np.mean(recon_ent)), 3), 'edit_distance': ed, 'acierto_segmento': round(acc, 2)})
    seg_acc: float = tot_hit / tot_pos
    norm_ed: float = tot_editdist / tot_gold
    ent_hit: float = float(np.mean([e for e, f in all_ent_match if f]))
    ent_miss: float = float(np.mean([e for e, f in all_ent_match if not f]))
    es: NDArray[np.float64] = np.array([e for e, _ in all_ent_match])
    fs: NDArray[np.float64] = np.array([0.0 if f else 1.0 for _, f in all_ent_match])
    corr: float = float(np.corrcoef(es, fs)[0, 1])
    csv_path = os.path.join(outdir, 'reconstruccion_resultados.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows_csv[0].keys()))
        w.writeheader()
        w.writerows(rows_csv)
    logging.info('=' * 78)
    logging.info('RECONSTRUCCIÓN PROTO-ROMANCE PROBABILÍSTICA — validación vs latín')
    logging.info('=' * 78)
    logging.info(f"{'concepto':<10}{'reconstruido':<16}{'latín (gold)':<16}{'H̄bits':>7}{'ed':>4}{'acc':>6}")
    logging.info('-' * 78)
    for concept, rec, gold_str, ent_val, ed_val, acc_val in per_concept:
        logging.info(f'{concept:<10}{rec:<16}{gold_str:<16}{ent_val:>7}{ed_val:>4}{acc_val:>6}')
    logging.info('-' * 78)
    logging.info(f'Acierto por segmento (vs latín) : {seg_acc:6.1%}')
    logging.info(f'Edit distance normalizado       : {norm_ed:6.3f}  (0=perfecto)')
    logging.info(f'Entropía media, aciertos        : {ent_hit:6.3f} bits')
    logging.info(f'Entropía media, errores         : {ent_miss:6.3f} bits')
    logging.info(f'corr(entropía, error)           : {corr:+.3f}')
    logging.info()
    logging.info('LECTURA: la entropía es la incertidumbre irreducible por posición.')
    logging.info('Que sea MAYOR en los errores (y la correlación positiva) demuestra que')
    logging.info("el modelo 'sabe lo que no sabe': donde el cambio fonético fusionó sonidos")
    logging.info('y borró información, no hay raíz única recuperable — solo una distribución.')
    logging.info(f'\nCSV escrito en: {csv_path}')
    return dict(seg_acc=seg_acc, norm_ed=norm_ed, ent_hit=float(ent_hit), ent_miss=float(ent_miss), corr=corr, n_sets=len(per_concept), n_states=len(states))
if __name__ == '__main__':
    main()