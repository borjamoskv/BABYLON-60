//! C5-REAL Bare-metal Compiler Frontend
//! Topología: Lexer y Árbol Sintáctico Afín (AST)

#[derive(Debug, PartialEq)]
pub enum Token {
    KeywordLet,
    KeywordUnsafe,
    Identifier(String),
    OperatorAssign,
    EndOfFile,
}

#[derive(Debug)]
pub enum AstNode {
    /// Representa la introducción causal de un recurso en el grafo lógico
    AffineAllocation {
        identifier: String,
        is_unsafe_boundary: bool,
    },
    /// Transición de consumo (Move Semantics)
    Consume {
        target: String,
    }
}

pub struct C5Lexer<'a> {
    input: &'a str,
    position: usize,
}

impl<'a> C5Lexer<'a> {
    pub fn new(input: &'a str) -> Self {
        Self { input, position: 0 }
    }
    // TODO: Implementar el colapso léxico determinista
}#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn it_works() {
        let result = add(2, 2);
        assert_eq!(result, 4);
    }
}
