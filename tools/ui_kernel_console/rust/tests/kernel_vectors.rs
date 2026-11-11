//! Contraste con los vectores dorados ACS del kernel (`tests/acs_cbor_golden.txt`, generados por
//! `tests/acs_authenticated.rs` y comprobados contra Lean). Las aserciones comparan bytes sin
//! imprimirlos.

mod common;

use babylon60_exec_receipt::canonical::signature_input;
use babylon60_exec_receipt::cbor;
use common::kernel_vector;
use ed25519_dalek::SigningKey;

/// Elemento del perfil CBOR restringido del kernel: enteros sin signo, bytes, texto y arrays.
enum Item {
    Uint(u64),
    Bytes(Vec<u8>),
    Text(String),
    Array(Vec<Item>),
}

fn read_head(data: &[u8], pos: &mut usize) -> Result<(u8, u64), String> {
    let initial = *data.get(*pos).ok_or("fin inesperado")?;
    *pos += 1;
    let (major, info) = (initial >> 5, initial & 0x1f);
    let width = match info {
        0..=23 => return Ok((major, u64::from(info))),
        24 => 1,
        25 => 2,
        26 => 4,
        27 => 8,
        _ => return Err(format!("información adicional {info} fuera del perfil")),
    };
    let slice = data.get(*pos..*pos + width).ok_or("fin inesperado")?;
    *pos += width;
    Ok((
        major,
        slice.iter().fold(0u64, |acc, b| (acc << 8) | u64::from(*b)),
    ))
}

fn decode(data: &[u8], pos: &mut usize) -> Result<Item, String> {
    let (major, arg) = read_head(data, pos)?;
    let take = |pos: &mut usize, n: u64| -> Result<Vec<u8>, String> {
        let n = usize::try_from(n).map_err(|_| "longitud")?;
        let out = data.get(*pos..*pos + n).ok_or("fin inesperado")?.to_vec();
        *pos += n;
        Ok(out)
    };
    match major {
        0 => Ok(Item::Uint(arg)),
        2 => Ok(Item::Bytes(take(pos, arg)?)),
        3 => Ok(Item::Text(
            String::from_utf8(take(pos, arg)?).map_err(|_| "texto no UTF-8")?,
        )),
        4 => (0..arg)
            .map(|_| decode(data, pos))
            .collect::<Result<Vec<_>, _>>()
            .map(Item::Array),
        _ => Err(format!("tipo mayor {major} fuera del perfil")),
    }
}

fn encode(item: &Item) -> Vec<u8> {
    match item {
        Item::Uint(n) => cbor::uint(*n),
        Item::Bytes(b) => cbor::bytes(b),
        Item::Text(s) => cbor::text(s),
        Item::Array(items) => cbor::array(items.iter().map(encode).collect()),
    }
}

#[test]
fn test_seeds_derive_the_kernel_public_keys() {
    let root = SigningKey::from_bytes(&[0x11; 32])
        .verifying_key()
        .to_bytes();
    let delegated = SigningKey::from_bytes(&[0x22; 32])
        .verifying_key()
        .to_bytes();
    assert!(
        kernel_vector("root") == root,
        "clave raíz distinta de la del kernel"
    );
    assert!(
        kernel_vector("delegated") == delegated,
        "clave delegada distinta de la del kernel"
    );
}

#[test]
fn sig_structure_matches_kernel_cose_signing_bytes() {
    for (payload, signing) in [("call", "call_signing"), ("forensic", "forensic_signing")] {
        assert!(
            signature_input(&kernel_vector(payload)) == kernel_vector(signing),
            "Sig_structure de {payload} distinta de la del kernel"
        );
    }
}

#[test]
fn restricted_cbor_reencoding_is_byte_identical_to_kernel() {
    for name in [
        "grant",
        "call",
        "call_signing",
        "forensic",
        "forensic_signing",
    ] {
        let data = kernel_vector(name);
        let mut pos = 0;
        let item = decode(&data, &mut pos).unwrap_or_else(|e| panic!("{name}: {e}"));
        assert_eq!(pos, data.len(), "{name}: bytes sobrantes tras el elemento");
        assert!(
            encode(&item) == data,
            "{name}: la recodificación difiere del kernel"
        );
    }
}
