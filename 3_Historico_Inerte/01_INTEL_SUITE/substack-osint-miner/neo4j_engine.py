# C5-REAL EXERGY CERTIFIED
from neo4j import GraphDatabase
from rich.console import Console

console = Console()

class Neo4jExporter:
    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="osint-password-2026"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def check_connection(self):
        try:
            self.driver.verify_connectivity()
            return True
        except Exception:
            return False

    def export_graph(self, nx_graph):
        console.print("[dim]Syncing NetworkX topology to Neo4j in batched vectors...[/dim]")
        with self.driver.session() as session:
            from collections import defaultdict

            # 1. Batch Create Nodes
            nodes_by_type = defaultdict(list)
            for node_id, data in nx_graph.nodes(data=True):
                node_type = data.get("type", "Unknown").capitalize()
                if not node_type.isalnum(): node_type = "Entity"
                props = {k: v for k, v in data.items() if k != "type"}
                nodes_by_type[node_type].append({"id": str(node_id), "props": props})

            for node_type, batch in nodes_by_type.items():
                query = f"""
                UNWIND $batch AS item
                MERGE (n:{node_type} {{id: item.id}})
                SET n += item.props
                """
                session.run(query, batch=batch)

            # 2. Batch Create Edges
            edges_by_type = defaultdict(list)
            for u, v, data in nx_graph.edges(data=True):
                edge_type = data.get("type", "RELATES_TO").upper()
                if not edge_type.isalnum() and "_" not in edge_type: edge_type = "RELATES_TO"
                props = {k: v for k, v in data.items() if k != "type"}
                edges_by_type[edge_type].append({"u": str(u), "v": str(v), "props": props})

            for edge_type, batch in edges_by_type.items():
                query = f"""
                UNWIND $batch AS item
                MATCH (a {{id: item.u}}), (b {{id: item.v}})
                MERGE (a)-[r:{edge_type}]->(b)
                SET r += item.props
                """
                session.run(query, batch=batch)

        console.print("[bold green]✔ Topology crystallized in Neo4j.[/bold green]")

    def export_clusters(self, sync_relations):
        console.print("[dim]Syncing clusters and [:BELONGS_TO] relationships in batched vectors...[/dim]")
        with self.driver.session() as session:
            # Format batch: [ {post_id: X, c_name: Y, props: Z}, ... ]
            batch = [{"post_id": pid, "c_name": cname, "props": props} for pid, cname, props in sync_relations]

            # Batch Create Clusters
            q_cluster = """
            UNWIND $batch AS item
            MERGE (c:Cluster {id: item.c_name})
            SET c += item.props
            """
            session.run(q_cluster, batch=batch)

            # Batch Create Edges
            q_edge = """
            UNWIND $batch AS item
            MATCH (p:Post {id: item.post_id}), (c:Cluster {id: item.c_name})
            MERGE (p)-[r:BELONGS_TO]->(c)
            """
            session.run(q_edge, batch=batch)

        console.print("[bold green]✔ Cluster relationships crystallized in Neo4j.[/bold green]")
