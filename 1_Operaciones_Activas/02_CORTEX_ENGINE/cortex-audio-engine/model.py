# C5-REAL EXERGY CERTIFIED
import torch
import torch.nn as nn
from core_architecture import DiTBlock

class TimestepEmbedder(nn.Module):
    """
    Inyección térmica del tiempo de difusión (t) en el tensor.
    """
    def __init__(self, hidden_size, frequency_embedding_size=256):
        super().__init__()
        self.mlp = nn.Sequential(
            nn.Linear(frequency_embedding_size, hidden_size, bias=True),
            nn.SiLU(),
            nn.Linear(hidden_size, hidden_size, bias=True),
        )
        self.frequency_embedding_size = frequency_embedding_size

    @staticmethod
    def timestep_embedding(t, dim, max_period=10000):
        half = dim // 2
        freqs = torch.exp(
            -math.log(max_period) * torch.arange(start=0, end=half, dtype=torch.float32) / half
        ).to(device=t.device)
        args = t[:, None].float() * freqs[None]
        embedding = torch.cat([torch.cos(args), torch.sin(args)], dim=-1)
        if dim % 2:
            embedding = torch.cat([embedding, torch.zeros_like(embedding[:, :1])], dim=-1)
        return embedding

    def forward(self, t):
        t_freq = self.timestep_embedding(t, self.frequency_embedding_size)
        t_emb = self.mlp(t_freq)
        return t_emb

class CrossAttention(nn.Module):
    """
    [Primitive 16] Cross-Attention para mapear el Prompt Semántico al Latente Acústico.
    """
    def __init__(self, dim, context_dim, n_heads):
        super().__init__()
        self.n_heads = n_heads
        self.q_proj = nn.Linear(dim, dim, bias=False)
        self.k_proj = nn.Linear(context_dim, dim, bias=False)
        self.v_proj = nn.Linear(context_dim, dim, bias=False)
        self.out_proj = nn.Linear(dim, dim)

    def forward(self, x, context):
        # x: [B, L_audio, dim]
        # context: [B, L_text, context_dim]
        B, L_a, C = x.shape
        L_t = context.shape[1]

        q = self.q_proj(x).view(B, L_a, self.n_heads, C // self.n_heads).transpose(1, 2)
        k = self.k_proj(context).view(B, L_t, self.n_heads, C // self.n_heads).transpose(1, 2)
        v = self.v_proj(context).view(B, L_t, self.n_heads, C // self.n_heads).transpose(1, 2)

        attn_out = torch.nn.functional.scaled_dot_product_attention(q, k, v)
        attn_out = attn_out.transpose(1, 2).reshape(B, L_a, C)

        return self.out_proj(attn_out)


class CortexAudioOmega(nn.Module):
    """
    [C5-REAL] Backbone Completo del Transformer de Difusión (DiT).
    """
    def __init__(self, input_channels=1024, context_dim=768, hidden_size=1024, depth=12, n_heads=16):
        super().__init__()
        self.x_embedder = nn.Linear(input_channels, hidden_size)
        self.t_embedder = TimestepEmbedder(hidden_size)

        self.blocks = nn.ModuleList([
            DiTBlock(hidden_size, n_heads) for _ in range(depth)
        ])

        self.cross_attentions = nn.ModuleList([
            CrossAttention(hidden_size, context_dim, n_heads) for _ in range(depth)
        ])

        self.final_layer = nn.Sequential(
            nn.LayerNorm(hidden_size),
            nn.Linear(hidden_size, input_channels)
        )

    def forward(self, x, t, context):
        """
        x: [B, L, input_channels] - Latente ruidoso
        t: [B] - Pasos de difusión
        context: [B, L_text, context_dim] - Embeddings del Prompt de Texto (ej. RoBERTa/T5)
        """
        x = self.x_embedder(x)
        t = self.t_embedder(t).unsqueeze(1) # [B, 1, hidden_size]

        x = x + t # Inyección térmica aditiva simple

        for block, cross_attn in zip(self.blocks, self.cross_attentions):
            # Self-attention causal/acústica
            x = block(x)
            # Cross-attention con el texto
            x = x + cross_attn(x, context)

        x = self.final_layer(x)
        return x

import math

# SYS_ID: borjamoskv
# Nivel: C5-REAL
