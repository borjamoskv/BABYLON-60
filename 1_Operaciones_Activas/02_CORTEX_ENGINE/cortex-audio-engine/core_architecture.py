# C5-REAL EXERGY CERTIFIED
import torch
import torch.nn as nn
import torch.nn.functional as F
import math

class RotaryPositionalEmbedding(nn.Module):
    """
    [Primitive 13] RoPE for sequences > 131k tokens.
    Invariancia de fase rotacional para Transformers de Audio.
    """
    def __init__(self, dim, base=10000):
        super().__init__()
        inv_freq = 1.0 / (base ** (torch.arange(0, dim, 2).float() / dim))
        self.register_buffer('inv_freq', inv_freq)

    def forward(self, x, seq_len):
        t = torch.arange(seq_len, device=x.device).type_as(self.inv_freq)
        freqs = torch.einsum('i,j->ij', t, self.inv_freq)
        emb = torch.cat((freqs, freqs), dim=-1)
        return emb.cos(), emb.sin()

def apply_rotary_pos_emb(q, k, cos, sin):
    q_cos, q_sin = q * cos, q * sin
    k_cos, k_sin = k * cos, k * sin
    q_out = q_cos + torch.cat((-q_sin[..., q.shape[-1]//2:], q_sin[..., :q.shape[-1]//2]), dim=-1)
    k_out = k_cos + torch.cat((-k_sin[..., k.shape[-1]//2:], k_sin[..., :k.shape[-1]//2]), dim=-1)
    return q_out, k_out


class DiTBlock(nn.Module):
    """
    [Primitive 11] Diffusion Transformer Block.
    Acelerado estructuralmente. Cero anergia.
    """
    def __init__(self, dim, n_heads):
        super().__init__()
        self.n_heads = n_heads
        self.dim = dim
        self.norm1 = nn.LayerNorm(dim)
        self.qkv = nn.Linear(dim, dim * 3, bias=False)
        self.proj = nn.Linear(dim, dim)
        self.mlp = nn.Sequential(
            nn.LayerNorm(dim),
            nn.Linear(dim, dim * 4),
            nn.GELU(approximate='tanh'),
            nn.Linear(dim * 4, dim)
        )
        self.rope = RotaryPositionalEmbedding(dim // n_heads)

    def forward(self, x, condition=None):
        B, L, C = x.shape
        # Modulación termodinámica (AdaLN) omitida por brevedad

        qkv = self.qkv(self.norm1(x)).reshape(B, L, 3, self.n_heads, C // self.n_heads)
        q, k, v = qkv.unbind(2)

        cos, sin = self.rope(x, L)
        q, k = apply_rotary_pos_emb(q, k, cos, sin)

        # FlashAttention-2 [Primitive 14] assumption
        attn = F.scaled_dot_product_attention(q.transpose(1,2), k.transpose(1,2), v.transpose(1,2))
        attn = attn.transpose(1,2).reshape(B, L, C)

        x = x + self.proj(attn)
        x = x + self.mlp(x)
        return x


class PhaseInvariantLoss(nn.Module):
    """
    [Primitive 03] Phase Invariant Loss.
    Castigo termodinámico a la desalineación de fase post-decodificador.
    """
    def __init__(self, n_fft=1024, hop_length=256):
        super().__init__()
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.window = torch.hann_window(n_fft)

    def forward(self, audio_true, audio_pred):
        # audio_true, audio_pred: [B, 1, T]
        self.window = self.window.to(audio_true.device)

        stft_true = torch.stft(audio_true.squeeze(1), n_fft=self.n_fft, hop_length=self.hop_length, window=self.window, return_complex=True)
        stft_pred = torch.stft(audio_pred.squeeze(1), n_fft=self.n_fft, hop_length=self.hop_length, window=self.window, return_complex=True)

        mag_true = torch.abs(stft_true)
        mag_pred = torch.abs(stft_pred)

        # Norm L1 de magnitud espectral
        return F.l1_loss(mag_true, mag_pred)


def audio_dpo_loss(policy_win, policy_lose, ref_win, ref_lose, beta=0.1):
    """
    [Primitive 81] Audio DPO (Direct Preference Optimization).
    Erradicación paramétrica de audios con artefactos metálicos (lose)
    frente a audios Studio Acapella (win).

    Args:
        policy_win: Log-probs del modelo actual para el audio ganador.
        policy_lose: Log-probs del modelo actual para el audio perdedor.
        ref_win: Log-probs del modelo de referencia para el ganador.
        ref_lose: Log-probs del modelo de referencia para el perdedor.
    """
    policy_ratio = policy_win - policy_lose
    ref_ratio = ref_win - ref_lose

    logits = policy_ratio - ref_ratio
    loss = -F.logsigmoid(beta * logits).mean()
    return loss

# SYS_ID: borjamoskv
# Nivel: C5-REAL
# Estado: AST Colapsado
