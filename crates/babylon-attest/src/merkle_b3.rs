//! Merkle BLAKE3 versionado (INV_C5_ONWIRE_CANON), esquema v1.
//!
//! Bisimilar con `01_KISH_ENGINE/babylon60/attestation/merkle_b3.py`:
//! hoja `BLAKE3("B60-LEAF-v1\0" || bytes)`, nodo `BLAKE3("B60-NODE-v1\0" || izq || der)`
//! (nodo impar emparejado consigo mismo) y raíz
//! `"b3:" + BLAKE3("B60-ROOT-v1\0" || len_u64_LE || nodo_superior)`.
//! La separación de dominio impide que una hoja se haga pasar por un nodo interno y la raíz
//! compromete la cardinalidad (`[a,b,c]` != `[a,b,c,c]`).

const LEAF: &[u8] = b"B60-LEAF-v1\0";
const NODE: &[u8] = b"B60-NODE-v1\0";
const ROOT: &[u8] = b"B60-ROOT-v1\0";

/// Etiqueta de versión de las raíces emitidas.
pub const ROOT_TAG: &str = "b3:";

/// Posición del hermano en un paso de prueba.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Side {
    /// El hermano está a la izquierda.
    Left,
    /// El hermano está a la derecha.
    Right,
}

/// Hash de hoja con separación de dominio.
pub fn leaf_hash(data: &[u8]) -> [u8; 32] {
    let mut h = blake3::Hasher::new();
    h.update(LEAF);
    h.update(data);
    *h.finalize().as_bytes()
}

/// Hash de nodo interno con separación de dominio.
pub fn node_hash(left: &[u8; 32], right: &[u8; 32]) -> [u8; 32] {
    let mut h = blake3::Hasher::new();
    h.update(NODE);
    h.update(left);
    h.update(right);
    *h.finalize().as_bytes()
}

fn levels(leaves: &[Vec<u8>]) -> Result<Vec<Vec<[u8; 32]>>, String> {
    if leaves.is_empty() {
        return Err("EMPTY_TREE".to_string());
    }
    let mut out = vec![leaves.iter().map(|l| leaf_hash(l)).collect::<Vec<_>>()];
    while out.last().map_or(0, Vec::len) > 1 {
        let cur = out.last().expect("nivel no vacío");
        let next = cur
            .chunks(2)
            .map(|p| node_hash(&p[0], p.get(1).unwrap_or(&p[0])))
            .collect();
        out.push(next);
    }
    Ok(out)
}

fn seal(top: &[u8; 32], count: usize) -> String {
    let mut h = blake3::Hasher::new();
    h.update(ROOT);
    h.update(&(count as u64).to_le_bytes());
    h.update(top);
    format!("{}{}", ROOT_TAG, h.finalize().to_hex())
}

/// Raíz etiquetada `b3:<hex>` que compromete la cardinalidad.
pub fn build_root(leaves: &[Vec<u8>]) -> Result<String, String> {
    let lv = levels(leaves)?;
    Ok(seal(&lv[lv.len() - 1][0], leaves.len()))
}

/// Prueba de inclusión O(log N).
pub fn inclusion_proof(leaves: &[Vec<u8>], index: usize) -> Result<Vec<(Side, [u8; 32])>, String> {
    if index >= leaves.len() {
        return Err(format!("Índice de hoja fuera de rango: {} (total: {})", index, leaves.len()));
    }
    let lv = levels(leaves)?;
    let mut idx = index;
    let mut proof = Vec::new();
    for level in &lv[..lv.len() - 1] {
        if idx % 2 == 1 {
            proof.push((Side::Left, level[idx - 1]));
        } else {
            proof.push((Side::Right, *level.get(idx + 1).unwrap_or(&level[idx])));
        }
        idx /= 2;
    }
    Ok(proof)
}

/// Verifica una prueba contra raíz y cardinalidad declaradas.
pub fn verify_inclusion(
    leaf: &[u8],
    proof: &[(Side, [u8; 32])],
    leaf_count: usize,
    expected_root: &str,
) -> bool {
    if leaf_count == 0 {
        return false;
    }
    let mut cur = leaf_hash(leaf);
    for (side, sib) in proof {
        cur = match side {
            Side::Left => node_hash(sib, &cur),
            Side::Right => node_hash(&cur, sib),
        };
    }
    seal(&cur, leaf_count) == expected_root
}

#[cfg(test)]
mod tests {
    use super::*;

    fn leaves(n: usize) -> Vec<Vec<u8>> {
        (0..n).map(|i| format!("BISIM_LEAF_{i}").into_bytes()).collect()
    }

    #[test]
    fn root_is_tagged_and_deterministic() {
        let r = build_root(&leaves(5)).unwrap();
        assert!(r.starts_with(ROOT_TAG));
        assert_eq!(r.len(), ROOT_TAG.len() + 64);
        assert_eq!(r, build_root(&leaves(5)).unwrap());
    }

    #[test]
    fn empty_tree_is_rejected() {
        assert_eq!(build_root(&[]), Err("EMPTY_TREE".to_string()));
    }

    #[test]
    fn cardinality_is_committed() {
        let abc = vec![b"a".to_vec(), b"b".to_vec(), b"c".to_vec()];
        let abcc = vec![b"a".to_vec(), b"b".to_vec(), b"c".to_vec(), b"c".to_vec()];
        assert_ne!(build_root(&abc).unwrap(), build_root(&abcc).unwrap());
    }

    #[test]
    fn leaf_cannot_masquerade_as_internal_node() {
        let mut forged = leaf_hash(b"a").to_vec();
        forged.extend_from_slice(&leaf_hash(b"b"));
        assert_ne!(
            build_root(&[forged]).unwrap(),
            build_root(&[b"a".to_vec(), b"b".to_vec()]).unwrap()
        );
    }

    #[test]
    fn proofs_verify_and_mutations_fail() {
        for n in [1usize, 2, 3, 7, 8, 13] {
            let ls: Vec<Vec<u8>> = (0..n).map(|i| format!("L{i}").into_bytes()).collect();
            let root = build_root(&ls).unwrap();
            for (i, leaf) in ls.iter().enumerate() {
                let p = inclusion_proof(&ls, i).unwrap();
                assert!(verify_inclusion(leaf, &p, n, &root));
                let mut bad = leaf.clone();
                bad.push(b'x');
                assert!(!verify_inclusion(&bad, &p, n, &root));
                assert!(!verify_inclusion(leaf, &p, n + 1, &root));
            }
        }
        assert!(inclusion_proof(&[b"a".to_vec()], 1).is_err());
    }
}
