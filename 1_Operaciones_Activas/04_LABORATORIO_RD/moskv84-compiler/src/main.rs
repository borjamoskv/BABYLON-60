use tree_sitter::{Language, Parser};

unsafe extern "C" {
    fn tree_sitter_moskv84() -> Language;
}

fn main() {
    println!("[MOSKV-1] Moskv84 Compiler & LSP Node Initialized.");
    println!("Exergy Protocol: Enforced.");
    
    let language = unsafe { tree_sitter_moskv84() };
    let mut parser = Parser::new();
    parser.set_language(&language).expect("Error loading Moskv84 grammar");

    let source_code = "
        axiom config_limit : uint64 = 10_000;
        mutation init_vector(v: vec0) -> vec0 {
            require(v.len > 0);
            return v;
        }
    ";

    let tree = parser.parse(source_code, None).unwrap();
    let root_node = tree.root_node();

    println!("AST Causal Ouroboros [C5-REAL]:");
    println!("{}", root_node.to_sexp());
}
