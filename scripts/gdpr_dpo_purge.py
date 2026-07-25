import hashlib
import os
from datetime import UTC, datetime, timezone

DPO_REGISTRY = {
    "X_Twitter": "privacy@x.com",
    "Meta_Facebook_Instagram": "privacy@support.facebook.com",
    "Google_Alphabet": "data-protection-office@google.com",
    "LinkedIn": "dpo-team@linkedin.com",
    "TikTok": "privacy@tiktok.com",
    "Reddit": "privacy@reddit.com",
    "Telegram": "support@telegram.org",
    "Discord": "privacy@discord.com",
    "OpenAI": "dsar@openai.com",
    "Microsoft": "privacydpo@microsoft.com",
}
GDPR_TEMPLATE = "DE: {operator_identity} <{operator_email}>\nPARA: DPO / Data Protection Officer - {platform_name} ({dpo_email})\nFECHA: {date_iso}\nASUNTO: Solicitud formal de Supresión de Datos Personales (Art. 17 RGPD / Ejercicio de Derecho al Olvido)\n\nEstimado Delegado de Protección de Datos:\n\nPor la presente, ejerzo formalmente mi derecho de supresión y eliminación absoluta de datos personales previsto en el Artículo 17 del Reglamento General de Protección de Datos (RGPD - Reglamento UE 2016/679).\n\nSolicito la eliminación inmediata e irreversible de:\n1. Todas las cuentas, perfiles de usuario y credenciales asociadas a la identidad: {operator_identity} / {operator_email}.\n2. Todo contenido, publicaciones, imágenes, mensajes, registros de actividad (logs), metadatos, direcciones IP e identificadores persistentes almacenados en sus sistemas primarios y copias de seguridad.\n3. Notificación y propagación del borrado a cualquier encargado del tratamiento o tercero al que hayan sido transmitidos mis datos (Art. 17.2 RGPD).\n\nRequiero confirmación por escrito de la efectividad de esta eliminación en el plazo máximo de 30 días fijado por el Art. 12.3 del RGPD.\n\nFirma e Identificador Causal:\nCORTEX-TAINT Provenance: {cortex_taint}\nSha256 Signature Proof: {sha256_proof}\n"


def generate_erasure_dossier(
    operator_identity: str = "Borja Moskv", operator_email: str = "operator@cortex.local"
) -> dict[str, str]:
    now_str = datetime.now(UTC).isoformat()
    dossiers = {}
    out_dir = os.path.join(os.path.dirname(__file__), "..", "gdpr_dossiers")
    os.makedirs(out_dir, exist_ok=True)
    for platform, dpo_email in DPO_REGISTRY.items():
        raw_seed = f"{operator_identity}:{operator_email}:{platform}:{now_str}".encode()
        taint = f"CORTEX-TAINT:borjamoskv:gdpr_purge:{platform}:{hashlib.sha256(raw_seed).hexdigest()[:16]}"
        proof = hashlib.sha256(f"{taint}:{now_str}".encode()).hexdigest()
        letter = GDPR_TEMPLATE.format(
            operator_identity=operator_identity,
            operator_email=operator_email,
            platform_name=platform,
            dpo_email=dpo_email,
            date_iso=now_str,
            cortex_taint=taint,
            sha256_proof=proof,
        )
        filepath = os.path.join(out_dir, f"GDPR_Erasure_{platform}.txt")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(letter)
        dossiers[platform] = filepath
    return dossiers


if __name__ == "__main__":
    print("[C5-REAL] Generating GDPR Art. 17 Erasure Dossiers...")
    results = generate_erasure_dossier()
    print(f"🟢 Generated {len(results)} formal erasure dossiers in gdpr_dossiers/")
