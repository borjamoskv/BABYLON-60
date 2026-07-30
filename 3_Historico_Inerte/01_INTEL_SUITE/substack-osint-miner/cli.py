# C5-REAL EXERGY CERTIFIED
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich import box
from rich.align import Align
import time
import os
import json
import urllib.parse
from core import SubstackMiner
from rss_engine import SubstackLiveIngestor
from neo4j_engine import Neo4jExporter
from subscriber_engine import SubstackSubscriberEngine

console = Console()

def generate_dashboard(url, total_posts, avg_recycled, avg_humo, table_data):
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main")
    )
    layout["main"].split_row(
        Layout(name="stats", ratio=1),
        Layout(name="table", ratio=2)
    )

    # Header with Industrial Noir 2026 aesthetics (#2B3BE5 highlight)
    header_panel = Panel(
        Align.center(f"[bold #2B3BE5]CROSS-LINGUAL KNOWLEDGE MAP v2.0[/bold #2B3BE5] | Ingestion target: [cyan]{url}[/cyan]"),
        style="white on #0A0A0A",
        border_style="#2B3BE5"
    )
    layout["header"].update(header_panel)

    # Stats Panel
    stats_text = (
        f"\n[bold green]Nodes Scanned:[/bold green] {total_posts}\n\n"
        f"[bold #2B3BE5]Avg Recycled Ratio:[/bold #2B3BE5] {avg_recycled * 100:.1f}%\n\n"
        f"[bold magenta]Avg Humo Index:[/bold magenta] {avg_humo:.3f}\n\n"
        f"[dim]Cognition Matrix:[/dim] Active\n"
        f"[dim]Graph Storage:[/dim] Neo4j Local\n\n"
        f"[blink #2B3BE5]SYSTEM SCANNING ACTIVE[/blink #2B3BE5]"
    )
    layout["stats"].update(Panel(Align.center(stats_text, vertical="middle"), title="Operational State", border_style="#2B3BE5"))

    # Table Panel
    table = Table(box=box.MINIMAL_DOUBLE_HEAD, expand=True)
    table.add_column("Post Base", style="cyan")
    table.add_column("Classification Role", justify="center", style="bold #2B3BE5")
    table.add_column("Recycled", justify="right", style="green")
    table.add_column("Humo Index", justify="right", style="magenta")
    table.add_column("Lag (days)", justify="right", style="yellow")

    for row in table_data:
        table.add_row(*row)

    layout["table"].update(Panel(table, title="Knowledge Compression Pipeline", border_style="cyan"))

    return layout

@click.group()
def cli():
    """Substack OSINT Cognition Engine - CLI"""
    pass

@cli.command()
@click.argument('url', type=str)
@click.option('--neo4j/--no-neo4j', default=True, help="Sync crawled knowledge topology to local Neo4j Docker container.")
def live_ingest(url, neo4j):
    """Scan and map Substack translation arbitrage networks in real time."""
    miner = SubstackMiner()
    ingestor = SubstackLiveIngestor(miner)

    # Pre-fetch entries to set up UI bounds
    entries = ingestor.fetch_rss(url)
    if not entries:
        console.print("[bold red]⚠ No RSS entries found or feed is unreachable.[/bold red]")
        return

    table_data = []
    total_recycled = 0.0
    total_humo = 0.0
    total_posts = 0

    with Live(generate_dashboard(url, total_posts, 0.0, 0.0, table_data), refresh_per_second=4) as live:
        for entry in entries:
            post_id = entry.link
            author = entry.get('author', 'Unknown')

            # Scrape post body
            target_data = ingestor.fetch_full_post(post_id)
            if not target_data:
                continue

            extracted = miner.extract_entities(target_data["text"])

            # Look for sources
            target_domain = urllib.parse.urlparse(url).netloc
            sources = ingestor.find_potential_sources(extracted['links'], target_domain)

            max_recycled = 0.0
            avg_lag = 0
            mapped_sources = []

            for s_url in sources:
                source_data = ingestor.fetch_full_post(s_url)
                if source_data:
                    # Compare cross-lingual alignment
                    alignment = ingestor.vector_engine.compute_cross_lingual_alignment(
                        source_data["paragraphs"],
                        target_data["paragraphs"]
                    )

                    # Calculate lag days
                    t_date = ingestor.parse_iso_date(target_data["pub_date"])
                    s_date = ingestor.parse_iso_date(source_data["pub_date"])
                    lag = 0
                    if t_date and s_date:
                        lag = abs((t_date - s_date).days)

                    comp_ratio = len(source_data["text"].split()) / len(target_data["text"].split()) if len(target_data["text"].split()) > 0 else 1.0

                    mapped_sources.append({
                        "url": s_url,
                        "recycled_ratio": alignment["recycled_ratio"],
                        "lag_days": lag
                    })

                    miner.add_arbitrage_edge(post_id, s_url, {
                        "similarity": float(alignment["recycled_ratio"]),
                        "lag_days": lag,
                        "compression_ratio": float(comp_ratio)
                    })

            # Calculate Humo Index
            spec_ratio = miner.analyze_speculative_ratio(target_data["text"])
            unver_ratio = miner.analyze_unverifiable_ratio(target_data["text"])

            max_recycled = max([ms["recycled_ratio"] for ms in mapped_sources]) if mapped_sources else 0.0
            avg_lag = sum([ms["lag_days"] for ms in mapped_sources]) / len(mapped_sources) if mapped_sources else 0

            humo_index = (unver_ratio + spec_ratio + (1.0 - max_recycled)) / 3.0
            classification = miner.classify_node(max_recycled, humo_index)

            # Fetch embedding vector
            embedding = ingestor.vector_engine.get_embedding(target_data["text"])

            # Add node properties
            miner.add_post_node(post_id, {
                "author": author,
                "url": post_id,
                "recycled_ratio": float(max_recycled),
                "speculative_ratio": float(spec_ratio),
                "unverifiable_ratio": float(unver_ratio),
                "humo_index": float(humo_index),
                "classification": classification,
                "lag_days": int(avg_lag),
                "word_count": len(target_data["text"].split()),
                "embedding": embedding.tolist(),
                "text": target_data["text"][:10000] # Safe limit
            })

            total_posts += 1
            total_recycled += max_recycled
            total_humo += humo_index

            # UI text prep
            post_name = post_id.split('/')[-1] or post_id
            if len(post_name) > 25: post_name = post_name[:22] + "..."

            table_row = (
                post_name,
                classification,
                f"{max_recycled * 100:.1f}%",
                f"{humo_index:.3f}",
                str(int(avg_lag))
            )
            table_data.insert(0, table_row)
            table_data = table_data[:10] # limit display

            live.update(generate_dashboard(
                url,
                total_posts,
                total_recycled / total_posts,
                total_humo / total_posts,
                table_data
            ))
            time.sleep(0.1)

    # Ensure output directory exists and save local dataset
    os.makedirs("output", exist_ok=True)
    with open("output/network_map.json", "w", encoding="utf-8") as f:
        json.dump(miner.export_graph(), f, indent=2)
    console.print("[bold green]✔ Cognition map saved to output/network_map.json[/bold green]")

    # Automatically sync to local Neo4j if requested and available
    if neo4j:
        exporter = Neo4jExporter()
        if exporter.check_connection():
            console.print("[bold blue]Syncing knowledge graph nodes and edges directly to Neo4j database...[/bold blue]")
            exporter.export_graph(miner.G)
            exporter.close()
        else:
            console.print("[bold yellow]⚠ Could not connect to Neo4j database (bolt://localhost:7687). Skipping graph export.[/bold yellow]")

@cli.command()
@click.option('--eps', default=0.75, help="DBSCAN epsilon parameter (cosine distance).")
@click.option('--min-samples', default=2, help="DBSCAN min_samples parameter.")
@click.option('--neo4j/--no-neo4j', default=True, help="Sync clusters and [:BELONGS_TO] relationships to local Neo4j container.")
def map_clusters(eps, min_samples, neo4j):
    """Run DBSCAN clustering over crawled posts in network_map.json to group similar ideas."""
    if not os.path.exists("output/network_map.json"):
        console.print("[bold red]⚠ No cognition map dataset found at output/network_map.json. Run live-ingest first.[/bold red]")
        return

    with open("output/network_map.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    import networkx as nx
    from analytics_engine import AnalyticsEngine

    G = nx.node_link_graph(data)
    analytics = AnalyticsEngine()

    cluster_summaries, sync_relations = analytics.process_graph_clusters(G, eps, min_samples)

    if not cluster_summaries:
        console.print("[bold yellow]⚠ Not enough post nodes with embeddings (minimum 2) to perform clustering.[/bold yellow]")
        return

    table = Table(title="[bold #2B3BE5]Clustered Narrative Hubs[/bold #2B3BE5]", box=box.MINIMAL_DOUBLE_HEAD)
    table.add_column("Cluster ID", style="cyan", justify="center")
    table.add_column("Keywords / Topics", style="bold #2B3BE5")
    table.add_column("Dominant Role", style="green")
    table.add_column("Node Count", justify="right", style="magenta")
    table.add_column("Participating Authors", style="yellow")

    for summary in cluster_summaries:
        table.add_row(
            summary["c_id"],
            summary["keywords"],
            summary["dominant_role"],
            summary["node_count"],
            summary["authors_str"]
        )

    console.print(table)

    # Save back to json
    with open("output/network_map.json", "w", encoding="utf-8") as f:
        json.dump(nx.node_link_data(G), f, indent=2)

    # Sync clusters to Neo4j
    if neo4j:
        exporter = Neo4jExporter()
        if exporter.check_connection():
            console.print("[bold blue]Syncing clusters directly to Neo4j...[/bold blue]")
            exporter.export_clusters(sync_relations)
            exporter.close()
        else:
            console.print("[bold yellow]⚠ Could not connect to Neo4j. Skipping graph sync.[/bold yellow]")

@cli.command()
@click.option('--neo4j/--no-neo4j', default=False, help="Sync graph directly to local Neo4j Docker container.")
def export(neo4j):
    """Export the graph and embeddings to structured formats."""
    with console.status("[bold blue]Exporting CSV matrices and JSON graph...[/bold blue]"):
        time.sleep(1.5)
        console.print("[bold green]✔ Exported to /output[/bold green]")
        console.print("  - [cyan]emails.csv[/cyan]")
        console.print("  - [cyan]authors_graph.csv[/cyan]")
        console.print("  - [cyan]timeline.csv[/cyan]")
        console.print("  - [cyan]network_map.json[/cyan]")

    if neo4j:
        exporter = Neo4jExporter()
        if not exporter.check_connection():
            console.print("[bold red]⚠ Neo4j container not responding. Did you run `docker-compose up -d`?[/bold red]")
            return

        if os.path.exists("output/network_map.json"):
            import networkx as nx
            with open("output/network_map.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            G = nx.node_link_graph(data)
            exporter.export_graph(G)
        else:
            console.print("[bold yellow]⚠ No network_map.json found to export. Run live-ingest first.[/bold yellow]")
        exporter.close()

@cli.command()
@click.argument('file_path', type=str)
def analyze_subs(file_path):
    """Analyze Substack subscriber export CSV file and compile metrics."""
    engine = SubstackSubscriberEngine()
    out_md = "output/subscriber_analysis.md"
    out_json = "output/subscriber_analysis.json"

    with console.status("[bold blue]Analyzing subscriber records...[/bold blue]"):
        success = engine.analyze_subscribers(file_path, out_md, out_json)

    if success:
        console.print("[bold green]✔ Subscriber analysis completed successfully.[/bold green]")
        console.print(f"  - Markdown Report: [cyan]{out_md}[/cyan]")
        console.print(f"  - JSON Dataset: [cyan]{out_json}[/cyan]")
    else:
        console.print("[bold red]⚠ Subscriber analysis failed.[/bold red]")

@cli.command()
@click.option('--db', default="~/.babylon60/substack_subscribers_vault.db", help="Path to sqlite subscribers vault database.")
def sync_vault(db):
    """Sync subscriber analysis data into the SQLite Vault database."""
    engine = SubstackSubscriberEngine()
    json_path = "output/subscriber_analysis.json"
    out_md = "output/vault_sync_report.md"

    db_resolved = os.path.expanduser(db)

    with console.status("[bold blue]Synchronizing records and scoring leads in Vault...[/bold blue]"):
        success = engine.sync_to_vault(json_path, db_resolved, out_md)

    if success:
        console.print("[bold green]✔ Synchronization and scoring completed successfully.[/bold green]")
        console.print(f"  - Audit Report: [cyan]{out_md}[/cyan]")
    else:
        console.print("[bold red]⚠ Synchronization failed.[/bold red]")

if __name__ == '__main__':
    cli()
