use anyhow::{anyhow, Result};
use pest::Parser;
use pest_derive::Parser;

use crate::ast::*;

#[derive(Parser)]
#[grammar = "nul_grammar.pest"]
pub struct NulParser;

pub fn parse_circuit(input: &str) -> Result<Circuit> {
    let mut pairs = NulParser::parse(Rule::circuit, input)?;
    let circuit_pair = pairs.next().ok_or_else(|| anyhow!("Expected circuit rule"))?;

    let mut inner = circuit_pair.into_inner();
    let name_pair = inner.next().ok_or_else(|| anyhow!("Expected circuit name"))?;
    let name = name_pair.as_str().to_string();

    let mut params = Vec::new();
    let mut main_fn = None;

    for pair in inner {
        match pair.as_rule() {
            Rule::param_list => {
                for param_pair in pair.into_inner() {
                    params.push(parse_param(param_pair)?);
                }
            }
            Rule::function => {
                main_fn = Some(parse_function(pair)?);
            }
            Rule::EOI => {}
            r => return Err(anyhow!("Unexpected rule in circuit: {:?}", r)),
        }
    }

    let main_fn = main_fn.ok_or_else(|| anyhow!("Missing main function in circuit"))?;

    Ok(Circuit {
        name,
        params,
        main_fn,
    })
}

fn parse_param(pair: pest::iterators::Pair<Rule>) -> Result<Param> {
    let mut inner = pair.into_inner();
    let vis_pair = inner.next().ok_or_else(|| anyhow!("Expected visibility"))?;
    let vis = match vis_pair.as_str() {
        "public" => Visibility::Public,
        "private" => Visibility::Private,
        _ => return Err(anyhow!("Invalid visibility")),
    };

    let name_pair = inner.next().ok_or_else(|| anyhow!("Expected param name"))?;
    let name = name_pair.as_str().to_string();

    let _type_pair = inner.next().ok_or_else(|| anyhow!("Expected param type"))?;

    Ok(Param {
        name,
        visibility: vis,
        param_type: Type::Field,
    })
}

fn parse_function(pair: pest::iterators::Pair<Rule>) -> Result<Function> {
    let mut inner = pair.into_inner();
    let name_pair = inner.next().ok_or_else(|| anyhow!("Expected fn name"))?;
    let name = name_pair.as_str().to_string();

    let mut statements = Vec::new();
    for stmt_pair in inner {
        statements.push(parse_statement(stmt_pair)?);
    }

    Ok(Function { name, statements })
}

fn parse_statement(pair: pest::iterators::Pair<Rule>) -> Result<Statement> {
    let inner = pair.into_inner().next().ok_or_else(|| anyhow!("Empty statement"))?;
    match inner.as_rule() {
        Rule::stmt_let => {
            let mut parts = inner.into_inner();
            let var_name = parts.next().expect("C5-REAL: Termodinámica forzada. Unwrap purgado.").as_str().to_string();
            let expr = parse_expr(parts.next().expect("C5-REAL: Termodinámica forzada. Unwrap purgado."))?;
            Ok(Statement::Let { name: var_name, expr })
        }
        Rule::stmt_assert => {
            let mut parts = inner.into_inner();
            let expr = parse_expr(parts.next().expect("C5-REAL: Termodinámica forzada. Unwrap purgado."))?;
            Ok(Statement::Assert { expr })
        }
        r => Err(anyhow!("Invalid statement rule: {:?}", r)),
    }
}

fn parse_expr(pair: pest::iterators::Pair<Rule>) -> Result<Expression> {
    match pair.as_rule() {
        Rule::expr | Rule::expr_cmp | Rule::expr_add | Rule::expr_mul => {
            let mut primary = None;
            let mut pending_op = None;

            for child in pair.into_inner() {
                match child.as_rule() {
                    Rule::op_add => pending_op = Some(Op::Add),
                    Rule::op_sub => pending_op = Some(Op::Sub),
                    Rule::op_mul => pending_op = Some(Op::Mul),
                    Rule::op_eq  => pending_op = Some(Op::Eq),
                    _ => {
                        let rhs = parse_expr(child)?;
                        if let Some(lhs) = primary {
                            let op = pending_op.take().ok_or_else(|| anyhow!("Missing operator"))?;
                            primary = Some(Expression::BinaryOp {
                                op,
                                lhs: Box::new(lhs),
                                rhs: Box::new(rhs),
                            });
                        } else {
                            primary = Some(rhs);
                        }
                    }
                }
            }
            primary.ok_or_else(|| anyhow!("Empty expression"))
        }
        Rule::identifier => Ok(Expression::Identifier(pair.as_str().to_string())),
        Rule::number => {
            let val = pair.as_str().parse::<u64>()?;
            Ok(Expression::Literal(val))
        }
        r => Err(anyhow!("Unsupported expression rule: {:?}", r)),
    }
}
