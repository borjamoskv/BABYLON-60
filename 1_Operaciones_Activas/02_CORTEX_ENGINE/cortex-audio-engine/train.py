# C5-REAL EXERGY CERTIFIED
import torch
import torch.nn.functional as F
import torch.optim as optim
from model import CortexAudioOmega
from core_architecture import PhaseInvariantLoss
from codec_bridge import C5RealCodecBridge
import os

class FlowMatchingTrainer:
    """
    [Primitive 04] Continuous Flow Matching.
    Motor termodinámico de entrenamiento. Cero DDPM. ODE pura.
    """
    def __init__(self, device="mps"):
        self.device = device
        self.model = CortexAudioOmega().to(self.device)
        self.optimizer = optim.AdamW(self.model.parameters(), lr=1e-4, weight_decay=1e-5)
        self.phase_loss_fn = PhaseInvariantLoss().to(self.device)

        # Opcional: El puente codec si fuéramos a penalizar en espacio PCM
        # self.codec = C5RealCodecBridge(device=self.device)

    def flow_matching_loss(self, z_1, context):
        """
        z_1: [B, L, C] - Latente real del dataset (Target)
        z_0: [B, L, C] - Ruido termodinámico puro (Normal)
        """
        B, L, C = z_1.shape
        z_0 = torch.randn_like(z_1).to(self.device)

        # Muestreo estocástico uniforme de t en [0, 1]
        t = torch.rand((B,), device=self.device)

        # Ecuación de interpolación de trayectoria rectilínea (Optimal Transport ODE)
        # z_t = (1 - t) * z_0 + t * z_1
        t_expanded = t.view(B, 1, 1)
        z_t = (1 - t_expanded) * z_0 + t_expanded * z_1

        # Campo vectorial objetivo (Target Vector Field)
        # v_target = z_1 - z_0
        v_target = z_1 - z_0

        # Predicción del modelo
        # El modelo predice la dirección del vector para llegar de z_0 a z_1
        v_pred = self.model(z_t, t, context)

        # Loss de Flow Matching (L2 o L1)
        loss_fm = F.mse_loss(v_pred, v_target)

        return loss_fm

    def step(self, z_1, context):
        """
        Paso único de optimización termodinámica.
        """
        self.optimizer.zero_grad(set_to_none=True)

        loss = self.flow_matching_loss(z_1, context)
        loss.backward()

        # [Primitive 62] Gradient Clipping
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)

        self.optimizer.step()
        return loss.item()

    def save_checkpoint(self, path="cortex_checkpoint.pt"):
        """
        Anclaje físico al disco.
        """
        torch.save(self.model.state_dict(), path)
        print(f"[CORTEX] Checkpoint cristalizado en {path}")

# SYS_ID: borjamoskv
# Nivel: C5-REAL
