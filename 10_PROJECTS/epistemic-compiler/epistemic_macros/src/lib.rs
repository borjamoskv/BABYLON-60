use proc_macro::TokenStream;
use quote::quote;
use syn::parse::{Parse, ParseStream};
use syn::{braced, Ident, Token};
use std::collections::{HashMap, HashSet};

struct EpistemicGraph {
    pub name: Ident,
    pub edges: Vec<EpistemicEdge>,
}

struct EpistemicEdge {
    pub from: Ident,
    pub to: Ident,
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
            let from: Ident = content.parse()?;
            let _arrow: Token![->] = content.parse()?;
            let to: Ident = content.parse()?;
            
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

fn detect_cycle(edges: &[EpistemicEdge]) -> syn::Result<()> {
    // Store Ident to preserve span for error reporting
    let mut graph: HashMap<&Ident, Vec<&Ident>> = HashMap::new();

    for e in edges {
        graph.entry(&e.from).or_default().push(&e.to);
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

    if let Err(e) = detect_cycle(&graph.edges) {
        return e.to_compile_error().into();
    }

    let mut unique_nodes = HashMap::new();
    for edge in &graph.edges {
        unique_nodes.insert(edge.from.to_string(), edge.from.clone());
        unique_nodes.insert(edge.to.to_string(), edge.to.clone());
    }
    
    let nodes: Vec<_> = unique_nodes.values().collect();

    let node_structs = nodes.iter().map(|n| {
        quote! {
            pub struct #n;
        }
    });
    
    let transitions = graph.edges.iter().map(|edge| {
        let from = &edge.from;
        let to = &edge.to;
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
        dot_edges.push_str(&format!("    {} -> {} [label=\"{}\"];\n", edge.from, edge.to, edge.weight));
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
