// C5-REAL EXERGY CERTIFIED
// Parser Recursivo Descendente para ExergyScript
use crate::ast::*;
use crate::lexer::Token;

pub struct Parser {
    tokens: Vec<Token>,
    pos: usize,
}

impl Parser {
    pub fn new(tokens: Vec<Token>) -> Self {
        Self { tokens, pos: 0 }
    }

    fn peek(&self) -> Option<&Token> {
        self.tokens.get(self.pos)
    }

    fn advance(&mut self) -> Option<Token> {
        if self.pos < self.tokens.len() {
            let tok = self.tokens[self.pos].clone();
            self.pos += 1;
            Some(tok)
        } else {
            None
        }
    }

    fn expect(&mut self, expected: Token) -> Result<(), String> {
        match self.advance() {
            Some(tok) if tok == expected => Ok(()),
            Some(other) => Err(format!("Esperaba {:?}, pero encontré {:?}", expected, other)),
            None => Err(format!("Esperaba {:?}, pero finalizó el archivo", expected)),
        }
    }

    pub fn parse_program(&mut self) -> Result<Program, String> {
        let mut rules = Vec::new();
        while self.peek().is_some() {
            rules.push(self.parse_rule()?);
        }
        Ok(Program { rules })
    }

    fn parse_rule(&mut self) -> Result<Rule, String> {
        self.expect(Token::KwRule)?;
        let name = match self.advance() {
            Some(Token::Ident(n)) => n,
            other => return Err(format!("Esperaba nombre de regla, encontré {:?}", other)),
        };

        self.expect(Token::LBrace)?;

        let mut target_pattern = None;
        let mut guard = None;
        let mut action = None;
        let mut attest_scitt = false;

        while let Some(tok) = self.peek() {
            if *tok == Token::RBrace {
                break;
            }

            match tok {
                Token::KwTarget => {
                    self.advance();
                    self.expect(Token::Equals)?;
                    match self.advance() {
                        Some(Token::StringLit(s)) => target_pattern = Some(s),
                        other => return Err(format!("Esperaba patrón string para target, encontré {:?}", other)),
                    }
                }
                Token::KwGuard => {
                    self.advance();
                    self.expect(Token::Equals)?;
                    guard = Some(self.parse_expr()?);
                }
                Token::KwAction => {
                    self.advance();
                    self.expect(Token::Equals)?;
                    action = Some(match self.advance() {
                        Some(Token::KwSafeTrash) => ActionType::SafeTrash,
                        Some(Token::KwCloudEvict) => ActionType::CloudEvict,
                        Some(Token::KwImmune) => ActionType::Immune,
                        Some(Token::KwHealDNS) => ActionType::HealDNS,
                        Some(Token::KwHealLS) => ActionType::HealLS,
                        other => return Err(format!("Acción no reconocida: {:?}", other)),
                    });
                }
                Token::KwAttest => {
                    self.advance();
                    self.expect(Token::Equals)?;
                    match self.advance() {
                        Some(Token::KwSCITT) => attest_scitt = true,
                        other => return Err(format!("Modo de atestación no reconocido: {:?}", other)),
                    }
                }
                _ => return Err(format!("Directiva inesperada en regla: {:?}", tok)),
            }
        }

        self.expect(Token::RBrace)?;

        Ok(Rule {
            name,
            target_pattern: target_pattern.ok_or("Falta campo 'target' en la regla")?,
            guard: guard.unwrap_or(Expr::BoolLiteral(true)),
            action: action.ok_or("Falta campo 'action' en la regla")?,
            attest_scitt,
        })
    }

    fn parse_expr(&mut self) -> Result<Expr, String> {
        self.parse_or()
    }

    fn parse_or(&mut self) -> Result<Expr, String> {
        let mut left = self.parse_and()?;
        while let Some(Token::Or) = self.peek() {
            self.advance();
            let right = self.parse_and()?;
            left = Expr::Or(Box::new(left), Box::new(right));
        }
        Ok(left)
    }

    fn parse_and(&mut self) -> Result<Expr, String> {
        let mut left = self.parse_comparison()?;
        while let Some(Token::And) = self.peek() {
            self.advance();
            let right = self.parse_comparison()?;
            left = Expr::And(Box::new(left), Box::new(right));
        }
        Ok(left)
    }

    fn parse_comparison(&mut self) -> Result<Expr, String> {
        let left = self.parse_primary()?;
        if let Some(tok) = self.peek() {
            match tok {
                Token::Gt => {
                    self.advance();
                    let right = self.parse_primary()?;
                    Ok(Expr::Gt(Box::new(left), Box::new(right)))
                }
                Token::Lt => {
                    self.advance();
                    let right = self.parse_primary()?;
                    Ok(Expr::Lt(Box::new(left), Box::new(right)))
                }
                Token::EqEq => {
                    self.advance();
                    let right = self.parse_primary()?;
                    Ok(Expr::Eq(Box::new(left), Box::new(right)))
                }
                _ => Ok(left),
            }
        } else {
            Ok(left)
        }
    }

    fn parse_primary(&mut self) -> Result<Expr, String> {
        match self.advance() {
            Some(Token::LParen) => {
                let inner = self.parse_expr()?;
                self.expect(Token::RParen)?;
                Ok(inner)
            }
            Some(Token::Not) => {
                let inner = self.parse_primary()?;
                Ok(Expr::Not(Box::new(inner)))
            }
            Some(Token::KwAge) => Ok(Expr::FieldAge),
            Some(Token::KwSize) => Ok(Expr::FieldSize),
            Some(Token::KwEntropy) => Ok(Expr::FieldEntropy),
            Some(Token::KwIsDevArtifact) => Ok(Expr::IsDevArtifact),
            Some(Token::KwIsElectronCache) => Ok(Expr::IsElectronCache),
            Some(Token::KwIsLocked) => Ok(Expr::IsLocked),
            Some(Token::Days(d)) => Ok(Expr::AgeDays(d)),
            Some(Token::Bytes(b)) => Ok(Expr::SizeBytes(b)),
            Some(Token::Number(n)) => Ok(Expr::EntropyMax(n)),
            Some(Token::Bool(b)) => Ok(Expr::BoolLiteral(b)),
            other => Err(format!("Expresión primaria inesperada: {:?}", other)),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::lexer::Lexer;

    #[test]
    fn test_parse_complete_rule() {
        let code = r#"
            rule PurgeOldAdobe {
                target = "~/Library/Caches/com.adobe.*"
                guard  = (age > 14d) && (!is_locked)
                action = SafeTrash
                attest = SCITT
            }
        "#;
        let mut lexer = Lexer::new(code);
        let tokens = lexer.tokenize().unwrap();
        let mut parser = Parser::new(tokens);
        let program = parser.parse_program().unwrap();

        assert_eq!(program.rules.len(), 1);
        assert_eq!(program.rules[0].name, "PurgeOldAdobe");
        assert_eq!(program.rules[0].action, ActionType::SafeTrash);
        assert!(program.rules[0].attest_scitt);
    }
}
