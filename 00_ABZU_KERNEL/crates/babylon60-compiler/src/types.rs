#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Type {
    I64,
    Bool,
    Struct(String),
    Pointer(Box<Type>),
}

#[derive(Debug, Clone)]
pub struct StructDef {
    pub name: String,
    pub fields: Vec<(String, Type)>,
}
