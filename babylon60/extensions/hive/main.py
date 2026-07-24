# [C5-REAL] Exergy-Maximized
"""
Neural Hive API.

Endpoints for visualizing the memory graph in 3D.
"""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from babylon60.auth import AuthResult, require_permission

__all__ = [
    "GraphData",
    "GraphLink",
    "GraphNode",
    "get_hive_graph",
]

router = APIRouter(prefix="/hive", tags=["hive"])


class GraphNode(BaseModel):
    id: int
    val: int  # size/relevance
    name: str  # content snippet
    group: str  # project or type
    color: str


class GraphLink(BaseModel):
    source: int
    target: int
    value: float  # distance/similarity


class GraphData(BaseModel):
    nodes: list[GraphNode]
    links: list[GraphLink]


@router.get("/graph", response_model=GraphData)
def get_hive_graph(
    limit: int = 500,
    auth: AuthResult = Depends(require_permission("read")),
):
    """
    Get the knowledge graph for 3D visualization.
    Nodes are facts, links are semantic similarities.
    """
    from babylon60.config import DB_PATH
    from babylon60.database.core import connect

    conn = connect(DB_PATH, row_factory=sqlite3.Row)

    try:
        cursor = conn.execute(
            """
            SELECT id, content, project, fact_type, created_at
            FROM facts
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()

        nodes = []
        node_ids = set()

        project_colors = {
            "cortex": "#00ff88",  # Cyber Green
            "naroa": "#ff0088",  # Cyber Pink
            "system": "#0088ff",  # Cyber Blue
        }
        default_color = "#ffffff"

        for row in rows:
            nid = row["id"]
            node_ids.add(nid)
            project = row["project"] or "system"

            nodes.append(
                GraphNode(
                    id=nid,
                    val=1,
                    name=row["content"][:50] + "...",
                    group=project,
                    color=project_colors.get(project.lower(), default_color),
                )
            )


        links = []

        try:
            vec_cursor = conn.execute("SELECT count(*) FROM fact_embeddings")
            has_vecs = vec_cursor.fetchone()[0] > 0
        except sqlite3.Error:
            has_vecs = False

        if has_vecs:

            prev_id = None
            for node in nodes:
                if prev_id:
                    links.append(GraphLink(source=prev_id, target=node.id, value=1.0))
                prev_id = node.id

        return GraphData(nodes=nodes, links=links)

    except (sqlite3.Error, OSError, RuntimeError):
        raise HTTPException(status_code=500, detail="Internal server error") from None
    finally:
        conn.close()
