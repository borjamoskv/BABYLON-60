// ============================================================================
// BABYLON-60 v4.0 Sovereign Hardened (LEXER / PARSER)
// ============================================================================
use crate::ast::{AST, Stmt};
use std::iter::Peekable;
use std::str::Chars;

#[derive(Debug, PartialEq, Clone)]
pub enum Token {
    Let, Alloc, Free, Struct,
    Ident(String), Int(i64),
    Eq, Dot, Semi, EOF,
}

pub struct Lexer<'a> {
    chars: Peekable<Chars<'a>>,
}

impl<'a> Lexer<'a> {
    pub fn new(input: &'a str) -> Self {
        Self { chars: input.chars().peekable() }
    }

    fn consume_whitespace(&mut self) {
        while let Some(&c) = self.chars.peek() {
            if c.is_whitespace() { self.chars.next(); } else { break; }
        }
    }

    pub fn next_token(&mut self) -> Token {
        self.consume_whitespace();
        if let Some(&c) = self.chars.peek() {
            if c.is_alphabetic() {
                let mut ident = String::new();
                while let Some(&ch) = self.chars.peek() {
                    if ch.is_alphanumeric() || ch == '_' {
                        ident.push(ch);
                        self.chars.next();
                    } else { break; }
                }
                return match ident.as_str() {
                    "let" => Token::Let,
                    "alloc" => Token::Alloc,
                    "free" => Token::Free,
                    "struct" => Token::Struct,
                    _ => Token::Ident(ident),
                };
            }
            if c.is_ascii_digit() {
                let mut num = String::new();
                while let Some(&ch) = self.chars.peek() {
                    if ch.is_ascii_digit() {
                        num.push(ch);
                        self.chars.next();
                    } else { break; }
                }
                return Token::Int(num.parse().expect("BFT Fallback"));
            }
            match c {
                '=' => { self.chars.next(); return Token::Eq; }
                '.' => { self.chars.next(); return Token::Dot; }
                ';' => { self.chars.next(); return Token::Semi; }
                _ => { self.chars.next(); return Token::Ident(c.to_string()); } 
            }
        }
        Token::EOF
    }

    pub fn tokenize(mut self) -> Vec<Token> {
        let mut tokens = Vec::new();
        loop {
            let tok = self.next_token();
            if tok == Token::EOF { break; }
            tokens.push(tok);
        }
        tokens.push(Token::EOF);
        tokens
    }
}

#[derive(Debug, PartialEq, Eq, Clone)]
pub enum ParseError {
    UnexpectedToken(String),
}

pub struct Parser {
    tokens: Vec<Token>,
    pos: usize,
}

impl Parser {
    pub fn new(tokens: Vec<Token>) -> Self {
        Self { tokens, pos: 0 }
    }

    fn peek(&self) -> &Token { &self.tokens[self.pos] }
    fn advance(&mut self) -> &Token {
        let tok = &self.tokens[self.pos];
        if *tok != Token::EOF { self.pos += 1; }
        tok
    }

    pub fn parse(&mut self) -> Result<AST, ParseError> {
        let mut statements = Vec::new();
        while *self.peek() != Token::EOF {
            statements.push(self.parse_stmt()?);
        }
        Ok(AST { statements })
    }

    fn parse_stmt(&mut self) -> Result<Stmt, ParseError> {
        let start = self.peek().clone();
        match start {
            Token::Let => {
                self.advance(); 
                let var = match self.advance() { Token::Ident(i) => i.clone(), _ => return Err(ParseError::UnexpectedToken("Expected Ident".into())) };
                if *self.advance() != Token::Eq { return Err(ParseError::UnexpectedToken("Expected =".into())); }
                if *self.advance() != Token::Alloc { return Err(ParseError::UnexpectedToken("Expected alloc".into())); }
                let st_name = match self.advance() { Token::Ident(i) => i.clone(), _ => return Err(ParseError::UnexpectedToken("Expected Struct Name".into())) };
                if *self.advance() != Token::Semi { return Err(ParseError::UnexpectedToken("Expected ;".into())); }
                Ok(Stmt::LetAlloc(var, st_name))
            }
            Token::Ident(var) => {
                self.advance();
                if *self.advance() != Token::Dot { return Err(ParseError::UnexpectedToken("Expected .".into())); }
                let field = match self.advance() { Token::Ident(i) => i.clone(), _ => return Err(ParseError::UnexpectedToken("Expected field".into())) };
                if *self.advance() != Token::Eq { return Err(ParseError::UnexpectedToken("Expected =".into())); }
                let val = match self.advance() { Token::Int(i) => *i, _ => return Err(ParseError::UnexpectedToken("Expected int".into())) };
                if *self.advance() != Token::Semi { return Err(ParseError::UnexpectedToken("Expected ;".into())); }
                Ok(Stmt::AssignField(var, field, val))
            }
            Token::Free => {
                self.advance();
                let var = match self.advance() { Token::Ident(i) => i.clone(), _ => return Err(ParseError::UnexpectedToken("Expected Ident".into())) };
                if *self.advance() != Token::Semi { return Err(ParseError::UnexpectedToken("Expected ;".into())); }
                Ok(Stmt::Free(var))
            }
            _ => Err(ParseError::UnexpectedToken(format!("Unexpected token: {:?}", start))),
        }
    }
}

use kernel::isa::{Instruction, Opcode, Reg as KernelReg};

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct B60Program {
    pub instructions: Vec<Instruction>,
}

pub fn parse(source: &str) -> Result<B60Program, ParseError> {
    let mut instructions = Vec::new();
    for line in source.lines() {
        let trimmed = line.trim();
        if trimmed.is_empty() || trimmed.starts_with('#') || trimmed.starts_with("//") {
            continue;
        }
        let parts: Vec<&str> = trimmed.split_whitespace().collect();
        if parts.is_empty() {
            continue;
        }
        match parts[0].to_uppercase().as_str() {
            "HALT" => instructions.push(Instruction { opcode: Opcode::Halt }),
            "CRITICAL_HALT" => instructions.push(Instruction { opcode: Opcode::CriticalHalt }),
            "FORK" => {
                let label = parts.get(1).unwrap_or(&"default").to_string();
                instructions.push(Instruction { opcode: Opcode::Fork(label) });
            }
            "LOADIMM" => {
                let val = parts.get(1).and_then(|s| s.parse::<i64>().ok()).unwrap_or(0);
                instructions.push(Instruction { opcode: Opcode::LoadImm(KernelReg::R1, val) });
            }
            unknown => return Err(ParseError::UnexpectedToken(format!("Unknown opcode: {}", unknown))),
        }
    }
    Ok(B60Program { instructions })
}
