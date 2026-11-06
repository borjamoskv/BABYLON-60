//! C5-REAL Bare-metal Compiler Frontend
//! Topología: Lexer y Árbol Sintáctico Afín (AST)

#[derive(Debug, PartialEq, Clone)]
pub enum Token {
    KeywordLet,
    KeywordUnsafe,
    KeywordConsume,
    Identifier(String),
    OperatorAssign,
    ParenOpen,
    ParenClose,
    EndOfFile,
}

#[derive(Debug, PartialEq)]
pub enum AstNode {
    /// Representa la introducción causal de un recurso en el grafo lógico
    AffineAllocation {
        identifier: String,
        is_unsafe_boundary: bool,
    },
    /// Transición de consumo (Move Semantics)
    Consume { target: String },
    /// Asignación que consume otro recurso (ej. let x = consume(y))
    ConsumeAssignment { identifier: String, target: String },
}

pub struct C5Lexer<'a> {
    input: &'a str,
    position: usize,
}

impl<'a> C5Lexer<'a> {
    pub fn new(input: &'a str) -> Self {
        Self { input, position: 0 }
    }

    fn skip_whitespace(&mut self) {
        while self.position < self.input.len() {
            let c = self.input.as_bytes()[self.position] as char;
            if c.is_whitespace() {
                self.position += 1;
            } else {
                break;
            }
        }
    }

    pub fn next_token(&mut self) -> Token {
        self.skip_whitespace();

        if self.position >= self.input.len() {
            return Token::EndOfFile;
        }

        let bytes = self.input.as_bytes();
        let c = bytes[self.position] as char;

        if c == '=' {
            self.position += 1;
            return Token::OperatorAssign;
        }

        if c == '(' {
            self.position += 1;
            return Token::ParenOpen;
        }

        if c == ')' {
            self.position += 1;
            return Token::ParenClose;
        }

        if c.is_alphabetic() || c == '_' {
            let start = self.position;
            while self.position < self.input.len() {
                let current = bytes[self.position] as char;
                if current.is_alphanumeric() || current == '_' {
                    self.position += 1;
                } else {
                    break;
                }
            }
            let text = &self.input[start..self.position];
            match text {
                "let" => Token::KeywordLet,
                "unsafe" => Token::KeywordUnsafe,
                "consume" => Token::KeywordConsume,
                _ => Token::Identifier(text.to_string()),
            }
        } else {
            // Fricción térmica: Carácter inválido. En C5-REAL debemos fallar determinísticamente.
            panic!("Token inválido detectado en la posición {}", self.position);
        }
    }
}

pub struct C5Parser<'a> {
    lexer: C5Lexer<'a>,
    current: Token,
}

impl<'a> C5Parser<'a> {
    pub fn new(mut lexer: C5Lexer<'a>) -> Self {
        let current = lexer.next_token();
        Self { lexer, current }
    }

    fn advance(&mut self) {
        self.current = self.lexer.next_token();
    }

    pub fn parse(&mut self) -> Result<Vec<AstNode>, String> {
        let mut nodes = Vec::new();
        while self.current != Token::EndOfFile {
            let node = self.parse_statement()?;
            nodes.push(node);
        }
        Ok(nodes)
    }

    fn parse_statement(&mut self) -> Result<AstNode, String> {
        match &self.current {
            Token::KeywordLet => self.parse_let_declaration(),
            Token::KeywordConsume => self.parse_consume_statement(),
            _ => Err(format!(
                "Token inesperado en inicio de sentencia: {:?}",
                self.current
            )),
        }
    }

    fn parse_let_declaration(&mut self) -> Result<AstNode, String> {
        self.advance(); // skip 'let'

        let identifier = match &self.current {
            Token::Identifier(id) => id.clone(),
            _ => return Err("Se esperaba un identificador después de 'let'".to_string()),
        };
        self.advance(); // skip identifier

        if self.current != Token::OperatorAssign {
            return Err("Se esperaba '=' después del identificador".to_string());
        }
        self.advance(); // skip '='

        match &self.current {
            Token::KeywordUnsafe => {
                self.advance(); // skip 'unsafe'
                Ok(AstNode::AffineAllocation {
                    identifier,
                    is_unsafe_boundary: true,
                })
            }
            Token::KeywordConsume => {
                self.advance(); // skip 'consume'
                if self.current != Token::ParenOpen {
                    return Err("Se esperaba '(' después de 'consume'".to_string());
                }
                self.advance(); // skip '('

                let target = match &self.current {
                    Token::Identifier(id) => id.clone(),
                    _ => {
                        return Err("Se esperaba un identificador dentro de 'consume()'".to_string())
                    }
                };
                self.advance(); // skip identifier

                if self.current != Token::ParenClose {
                    return Err(
                        "Se esperaba ')' después del identificador en 'consume()'".to_string()
                    );
                }
                self.advance(); // skip ')'

                Ok(AstNode::ConsumeAssignment { identifier, target })
            }
            Token::Identifier(val) => {
                let id = val.clone();
                self.advance(); // skip literal identifier (placeholder for allocation)
                Ok(AstNode::AffineAllocation {
                    identifier: id,
                    is_unsafe_boundary: false,
                })
            }
            _ => Err("Expresión inválida tras la asignación".to_string()),
        }
    }

    fn parse_consume_statement(&mut self) -> Result<AstNode, String> {
        self.advance(); // skip 'consume'
        if self.current != Token::ParenOpen {
            return Err("Se esperaba '(' después de 'consume'".to_string());
        }
        self.advance(); // skip '('

        let target = match &self.current {
            Token::Identifier(id) => id.clone(),
            _ => return Err("Se esperaba un identificador dentro de 'consume()'".to_string()),
        };
        self.advance(); // skip identifier

        if self.current != Token::ParenClose {
            return Err("Se esperaba ')' después del identificador en 'consume()'".to_string());
        }
        self.advance(); // skip ')'

        Ok(AstNode::Consume { target })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_lexer() {
        let mut lexer = C5Lexer::new("let x = consume(y)");
        assert_eq!(lexer.next_token(), Token::KeywordLet);
        assert_eq!(lexer.next_token(), Token::Identifier("x".to_string()));
        assert_eq!(lexer.next_token(), Token::OperatorAssign);
        assert_eq!(lexer.next_token(), Token::KeywordConsume);
        assert_eq!(lexer.next_token(), Token::ParenOpen);
        assert_eq!(lexer.next_token(), Token::Identifier("y".to_string()));
        assert_eq!(lexer.next_token(), Token::ParenClose);
        assert_eq!(lexer.next_token(), Token::EndOfFile);
    }

    #[test]
    fn test_parser_unsafe_alloc() {
        let lexer = C5Lexer::new("let resource = unsafe");
        let mut parser = C5Parser::new(lexer);
        let ast = parser.parse().expect("BFT Fallback");
        assert_eq!(ast.len(), 1);
        assert_eq!(
            ast[0],
            AstNode::AffineAllocation {
                identifier: "resource".to_string(),
                is_unsafe_boundary: true,
            }
        );
    }

    #[test]
    fn test_parser_consume_assignment() {
        let lexer = C5Lexer::new("let data2 = consume(data1)");
        let mut parser = C5Parser::new(lexer);
        let ast = parser.parse().expect("BFT Fallback");
        assert_eq!(ast.len(), 1);
        assert_eq!(
            ast[0],
            AstNode::ConsumeAssignment {
                identifier: "data2".to_string(),
                target: "data1".to_string(),
            }
        );
    }

    #[test]
    fn test_parser_standalone_consume() {
        let lexer = C5Lexer::new("consume(data)");
        let mut parser = C5Parser::new(lexer);
        let ast = parser.parse().expect("BFT Fallback");
        assert_eq!(ast.len(), 1);
        assert_eq!(
            ast[0],
            AstNode::Consume {
                target: "data".to_string(),
            }
        );
    }
}
