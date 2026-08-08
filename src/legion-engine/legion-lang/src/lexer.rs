// C5-REAL EXERGY CERTIFIED
// Lexer de Alto Rendimiento para ExergyScript

#[derive(Debug, Clone, PartialEq)]
pub enum Token {
    KwRule,
    KwTarget,
    KwGuard,
    KwAction,
    KwAttest,
    KwSafeTrash,
    KwCloudEvict,
    KwImmune,
    KwHealDNS,
    KwHealLS,
    KwSCITT,

    // Identificadores de Campos
    KwAge,
    KwSize,
    KwEntropy,
    KwIsDevArtifact,
    KwIsElectronCache,
    KwIsLocked,

    // Literales
    Ident(String),
    StringLit(String),
    Number(f64),
    Days(f64),
    Bytes(u64),
    Bool(bool),

    // Símbolos y Operadores
    LBrace,
    RBrace,
    LParen,
    RParen,
    Equals,
    And,
    Or,
    Gt,
    Lt,
    EqEq,
    Not,
    Comma,
}

pub struct Lexer<'a> {
    input: &'a str,
    chars: std::iter::Peekable<std::str::CharIndices<'a>>,
}

impl<'a> Lexer<'a> {
    pub fn new(input: &'a str) -> Self {
        Self {
            input,
            chars: input.char_indices().peekable(),
        }
    }

    pub fn tokenize(&mut self) -> Result<Vec<Token>, String> {
        let mut tokens = Vec::new();
        while let Some(&(i, ch)) = self.chars.peek() {
            if ch.is_whitespace() {
                self.chars.next();
                continue;
            }

            if ch == '/' {
                self.chars.next();
                if let Some(&(_, '/')) = self.chars.peek() {
                    // Comentario de una línea
                    while let Some(&(_, c)) = self.chars.peek() {
                        if c == '\n' {
                            break;
                        }
                        self.chars.next();
                    }
                    continue;
                } else {
                    return Err(format!("Carácter inesperado '/' en offset {}", i));
                }
            }

            match ch {
                '{' => { self.chars.next(); tokens.push(Token::LBrace); }
                '}' => { self.chars.next(); tokens.push(Token::RBrace); }
                '(' => { self.chars.next(); tokens.push(Token::LParen); }
                ')' => { self.chars.next(); tokens.push(Token::RParen); }
                '=' => {
                    self.chars.next();
                    if let Some(&(_, '=')) = self.chars.peek() {
                        self.chars.next();
                        tokens.push(Token::EqEq);
                    } else {
                        tokens.push(Token::Equals);
                    }
                }
                '&' => {
                    self.chars.next();
                    if let Some(&(_, '&')) = self.chars.peek() {
                        self.chars.next();
                        tokens.push(Token::And);
                    } else {
                        return Err(format!("Operador '&' incompleto en offset {}", i));
                    }
                }
                '|' => {
                    self.chars.next();
                    if let Some(&(_, '|')) = self.chars.peek() {
                        self.chars.next();
                        tokens.push(Token::Or);
                    } else {
                        return Err(format!("Operador '|' incompleto en offset {}", i));
                    }
                }
                '>' => { self.chars.next(); tokens.push(Token::Gt); }
                '<' => { self.chars.next(); tokens.push(Token::Lt); }
                '!' => { self.chars.next(); tokens.push(Token::Not); }
                ',' => { self.chars.next(); tokens.push(Token::Comma); }
                '"' => {
                    self.chars.next();
                    let start = i + 1;
                    let mut end = start;
                    while let Some(&(j, c)) = self.chars.peek() {
                        if c == '"' {
                            end = j;
                            self.chars.next();
                            break;
                        }
                        self.chars.next();
                    }
                    let s = self.input[start..end].to_string();
                    tokens.push(Token::StringLit(s));
                }
                _ if ch.is_alphabetic() || ch == '_' => {
                    let start = i;
                    let mut end = start;
                    while let Some(&(j, c)) = self.chars.peek() {
                        if c.is_alphanumeric() || c == '_' {
                            end = j + c.len_utf8();
                            self.chars.next();
                        } else {
                            break;
                        }
                    }
                    let ident = &self.input[start..end];
                    let tok = match ident {
                        "rule" => Token::KwRule,
                        "target" => Token::KwTarget,
                        "guard" => Token::KwGuard,
                        "action" => Token::KwAction,
                        "attest" => Token::KwAttest,
                        "SafeTrash" => Token::KwSafeTrash,
                        "CloudEvict" => Token::KwCloudEvict,
                        "Immune" => Token::KwImmune,
                        "HealDNS" => Token::KwHealDNS,
                        "HealLS" => Token::KwHealLS,
                        "SCITT" => Token::KwSCITT,
                        "age" => Token::KwAge,
                        "size" => Token::KwSize,
                        "entropy" => Token::KwEntropy,
                        "is_dev_artifact" => Token::KwIsDevArtifact,
                        "is_electron_cache" => Token::KwIsElectronCache,
                        "is_locked" => Token::KwIsLocked,
                        "true" => Token::Bool(true),
                        "false" => Token::Bool(false),
                        _ => Token::Ident(ident.to_string()),
                    };
                    tokens.push(tok);
                }
                _ if ch.is_ascii_digit() => {
                    let start = i;
                    let mut end = start;
                    while let Some(&(j, c)) = self.chars.peek() {
                        if c.is_ascii_digit() || c == '.' || c.is_alphabetic() {
                            end = j + c.len_utf8();
                            self.chars.next();
                        } else {
                            break;
                        }
                    }
                    let num_str = &self.input[start..end];
                    if let Some(stripped) = num_str.strip_suffix('d') {
                        let val: f64 = stripped.parse().map_err(|e| format!("{}", e))?;
                        tokens.push(Token::Days(val));
                    } else if let Some(stripped) = num_str.strip_suffix("GB") {
                        let val: f64 = stripped.parse().map_err(|e| format!("{}", e))?;
                        tokens.push(Token::Bytes((val * 1024.0 * 1024.0 * 1024.0) as u64));
                    } else if let Some(stripped) = num_str.strip_suffix("MB") {
                        let val: f64 = stripped.parse().map_err(|e| format!("{}", e))?;
                        tokens.push(Token::Bytes((val * 1024.0 * 1024.0) as u64));
                    } else if let Ok(val) = num_str.parse::<f64>() {
                        tokens.push(Token::Number(val));
                    } else {
                        return Err(format!("Formato numérico no válido: {}", num_str));
                    }
                }
                _ => return Err(format!("Carácter inesperado '{}' en offset {}", ch, i)),
            }
        }

        Ok(tokens)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_lexer_rule() {
        let input = r#"
            rule CleanAdobe {
                target = "~/Library/Caches/com.adobe.*"
                guard  = (age > 14d) && (!is_locked)
                action = SafeTrash
                attest = SCITT
            }
        "#;
        let mut lexer = Lexer::new(input);
        let tokens = lexer.tokenize().unwrap();
        assert_eq!(tokens[0], Token::KwRule);
        assert_eq!(tokens[1], Token::Ident("CleanAdobe".to_string()));
    }
}
