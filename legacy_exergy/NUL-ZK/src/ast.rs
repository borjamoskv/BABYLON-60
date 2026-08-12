use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Ty {
    Field,
    Bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Op {
    Add,
    Sub,
    Mul,
    Eq,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Expr {
    Number(String),
    Ident(String),
    BinOp {
        lhs: Box<Expr>,
        op: Op,
        rhs: Box<Expr>,
    },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Stmt {
    Let { ident: String, expr: Expr },
    Assert { expr: Expr },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Visibility {
    Private,
    Public,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Param {
    pub visibility: Visibility,
    pub ident: String,
    pub ty: Ty,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Circuit {
    pub name: String,
    pub params: Vec<Param>,
    pub body: Vec<Stmt>,
}
