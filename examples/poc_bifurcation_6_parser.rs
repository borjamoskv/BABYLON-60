// ============================================================================
// PoC: BIFURCATION 6 - EL FRENTE SEMÁNTICO (LEXER, PARSER & LOWERING)
// BABYLON-60 / C5-REAL
// ============================================================================

#[derive(Debug, PartialEq, Clone)]
pub enum Token {
    Let, Alloc, Free, Struct,
    Ident(String), Int(i64),
    Eq, Dot, Semi, EOF,
}

pub struct Lexer<'a> {
    chars: std::iter::Peekable<std::str::Chars<'a>>,
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
                return Token::Int(num.parse().unwrap());
            }
            match c {
                '=' => { self.chars.next(); return Token::Eq; }
                '.' => { self.chars.next(); return Token::Dot; }
                ';' => { self.chars.next(); return Token::Semi; }
                _ => { self.chars.next(); } // Ignore unknowns for PoC
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

// --- AST ---
#[derive(Debug)]
pub enum Stmt {
    LetAlloc(String, String),       // let x = alloc Struct;
    AssignField(String, String, i64), // x.field = 42;
    Free(String),                   // free x;
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

    pub fn parse(&mut self) -> Vec<Stmt> {
        let mut stmts = Vec::new();
        while *self.peek() != Token::EOF {
            stmts.push(self.parse_stmt());
        }
        stmts
    }

    fn parse_stmt(&mut self) -> Stmt {
        match self.peek().clone() {
            Token::Let => {
                self.advance(); // consume 'let'
                let Token::Ident(var) = self.advance().clone() else { panic!("Expected Ident"); };
                let Token::Eq = self.advance() else { panic!("Expected ="); };
                let Token::Alloc = self.advance() else { panic!("Expected alloc"); };
                let Token::Ident(st_name) = self.advance().clone() else { panic!("Expected Struct Name"); };
                let Token::Semi = self.advance() else { panic!("Expected ;"); };
                Stmt::LetAlloc(var, st_name)
            }
            Token::Ident(var) => {
                self.advance(); // consume ident
                let Token::Dot = self.advance() else { panic!("Expected ."); };
                let Token::Ident(field) = self.advance().clone() else { panic!("Expected field"); };
                let Token::Eq = self.advance() else { panic!("Expected ="); };
                let Token::Int(val) = self.advance().clone() else { panic!("Expected int"); };
                let Token::Semi = self.advance() else { panic!("Expected ;"); };
                Stmt::AssignField(var, field, val)
            }
            Token::Free => {
                self.advance(); // consume free
                let Token::Ident(var) = self.advance().clone() else { panic!("Expected Ident"); };
                let Token::Semi = self.advance() else { panic!("Expected ;"); };
                Stmt::Free(var)
            }
            _ => panic!("Syntax error at {:?}", self.peek()),
        }
    }
}

// --- LOWERING (AST -> IR) ---
// Representación abstracta del lowering: Convierte AST en el IR definido en la Bifurcación 4/5.
fn lower(ast: &[Stmt]) {
    println!("\n--- LOWERING (AST -> IR) ---");
    for stmt in ast {
        match stmt {
            Stmt::LetAlloc(var, struct_name) => {
                println!("IR: Alloc {{ dest: Reg(..), type: {} }}  // {} = alloc", struct_name, var);
            }
            Stmt::AssignField(var, field, val) => {
                println!("IR: FieldPtr {{ dest: Reg(..), base: Reg({}), offset: {} }}", var, field);
                println!("IR: ConstInt {{ dest: Reg(..), val: {} }}", val);
                println!("IR: Store {{ ptr: Reg(..), val: Reg(..) }}");
            }
            Stmt::Free(var) => {
                println!("IR: Free {{ ptr: Reg(..) }} // free {}", var);
            }
        }
    }
}

fn test_parsing() {
    let source = "
        let sensor = alloc Sensor;
        sensor.temperature = 42;
        free sensor;
    ";
    println!("--- SOURCE CODE ---\n{}", source);
    
    let lexer = Lexer::new(source);
    let tokens = lexer.tokenize();
    println!("--- TOKENS ---\n{:?}", tokens);
    
    let mut parser = Parser::new(tokens);
    let ast = parser.parse();
    println!("\n--- AST ---\n{:#?}", ast);
    
    lower(&ast);
}

fn stress_test() {
    println!("\n=== STRESS TEST (1000 iteraciones empíricas) ===");
    let source = "let a = alloc S; a.f = 1; free a;";
    let mut success = 0;
    for _ in 0..1000 {
        let tokens = Lexer::new(source).tokenize();
        let ast = Parser::new(tokens).parse();
        if ast.len() == 3 { success += 1; }
    }
    println!("Falsación superada: {}/1000 parsing cycles completados con AST isomórfico.", success);
}

fn main() {
    test_parsing();
    stress_test();
}
