use proc_macro::TokenStream;
use quote::quote;
use syn::parse::{Parse, ParseStream};
use syn::{braced, Ident, Token};
use std::collections::{HashMap, HashSet};

struct EpistemicGraph {
    pub name: Ident,
    pub edges: Vec<EpistemicEdge>,
}

#[derive(Clone, Debug)]
struct EpistemicNode {
    pub kind: Option<Ident>,
    pub name: Ident,
}

struct EpistemicEdge {
    pub from: EpistemicNode,
    pub to: EpistemicNode,
    pub weight: f64,
}

impl Parse for EpistemicGraph {
    fn parse(input: ParseStream) -> syn::Result<Self> {
        let _graph_kw: Ident = input.parse()?;
        let name: Ident = input.parse()?;

        let content;
        braced!(content in input);

        let mut edges = Vec::new();

        while !content.is_empty() {
            let mut kind1 = None;
            let mut name1: Ident = content.parse()?;
            if content.peek(syn::Ident) && !content.peek(Token![->]) {
                kind1 = Some(name1);
                name1 = content.parse()?;
            }
            let from = EpistemicNode { kind: kind1, name: name1 };

            let _arrow: Token![->] = content.parse()?;

            let mut kind2 = None;
            let mut name2: Ident = content.parse()?;
            if content.peek(syn::Ident) && !content.peek(syn::token::Bracket) && !content.peek(Token![;]) {
                kind2 = Some(name2);
                name2 = content.parse()?;
            }
            let to = EpistemicNode { kind: kind2, name: name2 };
            
            let weight: f64 = if content.peek(syn::token::Bracket) {
                let bracketed_content;
                syn::bracketed!(bracketed_content in content);
                let lit: syn::Lit = bracketed_content.parse()?;
                match lit {
                    syn::Lit::Float(f) => f.base10_parse()?,
                    syn::Lit::Int(i) => i.base10_parse::<f64>()?,
                    _ => return Err(syn::Error::new(lit.span(), "Expected float or int weight")),
                }
            } else {
                1.0
            };

            let _semi: Token![;] = content.parse()?;

            edges.push(EpistemicEdge { from, to, weight });
        }

        Ok(Self { name, edges })
    }
}

fn validate_epistemology(edges: &[EpistemicEdge]) -> syn::Result<()> {
    // 1. Matriz de Rechazo Ontológico (EPISTEMIC_002)
    for edge in edges {
        if let (Some(k1), Some(k2)) = (&edge.from.kind, &edge.to.kind) {
            let k1_str = k1.to_string();
            let k2_str = k2.to_string();
            
            if k1_str == "Latent" && k2_str == "Observable" {
                return Err(syn::Error::new_spanned(
                    &edge.to.name,
                    "EPISTEMIC_002: Observables cannot be derived from Latent variables. Provenance violation."
                ));
            }
            
            if k1_str == "Intervention" && (k2_str == "Evidence" || k2_str == "RawEvidence") {
                return Err(syn::Error::new_spanned(
                    &edge.to.name,
                    "EPISTEMIC_002: An intervention cannot mutate basal Evidence. Temporal violation."
                ));
            }
            
            if k1_str == "Invariant" {
                return Err(syn::Error::new_spanned(
                    &edge.from.name,
                    "EPISTEMIC_002: Invariants are terminal bounds. They cannot emit causality to other nodes."
                ));
            }
        }
    }

    // 2. Cycle Detection (EPISTEMIC_001)
    let mut graph: HashMap<&Ident, Vec<&Ident>> = HashMap::new();

    for e in edges {
        graph.entry(&e.from.name).or_default().push(&e.to.name);
    }

    fn dfs<'a>(
        node: &'a Ident,
        graph: &HashMap<&'a Ident, Vec<&'a Ident>>,
        visiting: &mut HashSet<&'a Ident>,
        visited: &mut HashSet<&'a Ident>,
    ) -> Result<(), &'a Ident> {
        if visiting.contains(node) {
            return Err(node);
        }
        if visited.contains(node) {
            return Ok(());
        }

        visiting.insert(node);

        if let Some(neigh) = graph.get(node) {
            for n in neigh {
                dfs(n, graph, visiting, visited)?;
            }
        }

        visiting.remove(node);
        visited.insert(node);

        Ok(())
    }

    let mut visited = HashSet::new();
    let mut visiting = HashSet::new();

    for node in graph.keys() {
        if let Err(cycle_node) = dfs(node, &graph, &mut visiting, &mut visited) {
            return Err(syn::Error::new_spanned(
                cycle_node,
                "EPISTEMIC_001: invalid causal inversion (cycle detected)",
            ));
        }
    }

    Ok(())
}

#[proc_macro]
pub fn epistemic(input: TokenStream) -> TokenStream {
    let graph = syn::parse_macro_input!(input as EpistemicGraph);

    if let Err(e) = validate_epistemology(&graph.edges) {
        return e.to_compile_error().into();
    }

    let mut unique_nodes: HashMap<String, EpistemicNode> = HashMap::new();
    for edge in &graph.edges {
        unique_nodes.insert(edge.from.name.to_string(), edge.from.clone());
        unique_nodes.insert(edge.to.name.to_string(), edge.to.clone());
    }
    
    let nodes: Vec<_> = unique_nodes.values().map(|n| &n.name).collect();

    let node_structs = unique_nodes.values().map(|n| {
        let name = &n.name;
        if let Some(kind) = &n.kind {
            quote! {
                pub struct #name(pub epistemic_engine::#kind);
            }
        } else {
            quote! {
                pub struct #name;
            }
        }
    });
    
    let transitions = graph.edges.iter().map(|edge| {
        let from = &edge.from.name;
        let to = &edge.to.name;
        let weight = edge.weight;
        quote! {
            impl epistemic_engine::Transition<states::#from> for epistemic_engine::Inference<states::#from> {
                type To = states::#to;
                fn apply(self) -> epistemic_engine::Inference<Self::To> {
                    epistemic_engine::Inference {
                        value: self.value,
                        confidence: self.confidence * #weight,
                        _state: std::marker::PhantomData,
                    }
                }
            }
        }
    });

    let constructors = nodes.iter().map(|n| {
        quote! {
            impl EpistemicNew for epistemic_engine::Inference<states::#n> {
                fn new(value: String, confidence: f64) -> Self {
                    epistemic_engine::Inference {
                        value,
                        confidence,
                        _state: std::marker::PhantomData,
                    }
                }
            }
        }
    });
    
    let mut dot_edges = String::new();
    for edge in &graph.edges {
        let from_str = if let Some(k) = &edge.from.kind { format!("{}_{}", k, edge.from.name) } else { edge.from.name.to_string() };
        let to_str = if let Some(k) = &edge.to.kind { format!("{}_{}", k, edge.to.name) } else { edge.to.name.to_string() };
        dot_edges.push_str(&format!("    {} -> {} [label=\"{}\"];\n", from_str, to_str, edge.weight));
    }
    let graph_name = &graph.name;
    let dot_graph = format!("digraph {} {{\n    rankdir=LR;\n    node [shape=box, style=filled, fillcolor=\"#0A0A0A\", fontcolor=\"#2B3BE5\", fontname=\"Helvetica\"];\n    edge [color=\"#2B3BE5\", fontcolor=\"#ffffff\"];\n    bgcolor=\"#000000\";\n\n{}}}", graph_name, dot_edges);

    let expanded = quote! {
        pub mod states {
            #(#node_structs)*
            
            pub mod sealed {
                pub trait Sealed {}
                #(impl Sealed for super::#nodes {})*
            }
            
            pub trait EpistemicState: sealed::Sealed {}
            
            #(impl EpistemicState for #nodes {})*

            pub const CORTEX_SANEDRIN_DOT: &str = #dot_graph;
        }
        
        pub trait EpistemicNew {
            fn new(value: String, confidence: f64) -> Self;
        }

        #(#constructors)*
        
        #(#transitions)*
    };

    expanded.into()
}
