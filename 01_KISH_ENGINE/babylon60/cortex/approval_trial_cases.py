"""Draft Spanish case bank for FL-APPROVAL-01; no effect execution.

Fifty policy families have four materially different requests each. Cases and
coordinator answers are separate. Two independent subject-matter adjudicators
must validate every case before participant use. This bank is not adjudicated.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import json
import math
import random
import secrets
from typing import Any

from blake3 import blake3


SCHEMA = "FL-APPROVAL-01/human-cases-v1"
STATUS = "DRAFT_NOT_ADJUDICATED"
POLICY_VERSION = "fl-approval01-human-cases-v1"


class CaseBankError(ValueError):
    """A case or its explicit policy is structurally invalid."""


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def _rule(field: str, operator: str, value: Any = None, *, other_field: str | None = None) -> dict[str, Any]:
    result = {"field": field, "operator": operator}
    result["other_field" if other_field else "value"] = other_field if other_field else value
    return result


def _family(
    domain: str,
    title: str,
    operation: str,
    policy: str,
    facts: dict[str, Any],
    criteria: list[dict[str, Any]],
    variants: list[dict[str, Any]],
    benefit: str,
    risk: str,
) -> dict[str, Any]:
    return {
        "domain": domain,
        "title": title,
        "operation": operation,
        "policy": policy,
        "facts": facts,
        "criteria": criteria,
        "variants": variants,
        "benefit": benefit,
        "risk": risk,
    }


def _families() -> list[dict[str, Any]]:
    """Policy semantics and explicit fixtures; labels never reach participants."""
    r = _rule
    f = _family
    return [
        f(
            "configuration",
            "Registro de auditoría",
            "configure_audit",
            "El registro debe permanecer habilitado y retenerse al menos 30 días.",
            {},
            [r("request.enabled", "eq", True), r("request.retention_days", "ge", 30)],
            [
                {"enabled": True, "retention_days": 30},
                {"enabled": True, "retention_days": 90},
                {"enabled": False, "retention_days": 90},
                {"enabled": True, "retention_days": 7},
            ],
            "mantener trazabilidad del servicio",
            "la pérdida de evidencia de auditoría",
        ),
        f(
            "configuration",
            "Redacción de trazas",
            "configure_trace_redaction",
            "Toda traza debe ocultar email y token; la fracción de muestreo no superará 0,20.",
            {},
            [r("request.mask_fields", "includes", ["email", "token"]), r("request.sample_fraction", "le", 0.20)],
            [
                {"mask_fields": ["email", "token"], "sample_fraction": 0.1},
                {"mask_fields": ["email", "token", "ip"], "sample_fraction": 0.2},
                {"mask_fields": ["email"], "sample_fraction": 0.1},
                {"mask_fields": ["email", "token"], "sample_fraction": 0.3},
            ],
            "observar incidencias operativas",
            "la exposición de secretos en trazas",
        ),
        f(
            "configuration",
            "Sesiones de administración",
            "configure_admin_session",
            "MFA debe estar requerido; una sesión administrativa durará como máximo 8 horas.",
            {},
            [r("request.mfa_required", "eq", True), r("request.session_hours", "le", 8)],
            [
                {"mfa_required": True, "session_hours": 1},
                {"mfa_required": True, "session_hours": 8},
                {"mfa_required": False, "session_hours": 1},
                {"mfa_required": True, "session_hours": 12},
            ],
            "facilitar el trabajo de administración",
            "la prolongación del acceso privilegiado",
        ),
        f(
            "configuration",
            "Perfil TLS",
            "configure_tls",
            "Solo se permite TLS1.3 y los cifrados deben pertenecer a la lista aprobada.",
            {"approved_ciphers": ["AES_128_GCM", "CHACHA20_POLY1305"]},
            [
                r("request.protocol", "eq", "TLS1.3"),
                r("request.ciphers", "subset", other_field="evidence.facts.approved_ciphers"),
            ],
            [
                {"protocol": "TLS1.3", "ciphers": ["AES_128_GCM"]},
                {"protocol": "TLS1.3", "ciphers": ["AES_128_GCM", "CHACHA20_POLY1305"]},
                {"protocol": "TLS1.2", "ciphers": ["AES_128_GCM"]},
                {"protocol": "TLS1.3", "ciphers": ["AES_128_GCM", "LEGACY_CBC"]},
            ],
            "compatibilizar conexiones del servicio",
            "la aceptación de protocolos no aprobados",
        ),
        f(
            "configuration",
            "Límite de solicitudes",
            "configure_rate_limit",
            "La cuota será como máximo 1000 solicitudes/minuto y no se permitirá omitir el limitador.",
            {},
            [r("request.requests_per_minute", "le", 1000), r("request.bypass", "eq", False)],
            [
                {"requests_per_minute": 500, "bypass": False},
                {"requests_per_minute": 1000, "bypass": False},
                {"requests_per_minute": 1200, "bypass": False},
                {"requests_per_minute": 500, "bypass": True},
            ],
            "absorber carga de solicitudes",
            "la saturación por exceso de cuota",
        ),
        f(
            "configuration",
            "Muestreo diagnóstico",
            "configure_diagnostic_sampling",
            "La fracción de muestreo diagnóstico debe estar entre 0,01 y 0,10, ambos incluidos.",
            {},
            [r("request.fraction", "ge", 0.01), r("request.fraction", "le", 0.10)],
            [{"fraction": 0.01}, {"fraction": 0.10}, {"fraction": 0.0}, {"fraction": 0.11}],
            "obtener una muestra diagnóstica útil",
            "un muestreo insuficiente o excesivo",
        ),
        f(
            "configuration",
            "Caché por tenant",
            "configure_tenant_cache",
            "La caché tendrá alcance tenant y TTL máximo de 300 segundos.",
            {},
            [r("request.scope", "eq", "tenant"), r("request.ttl_seconds", "le", 300)],
            [
                {"scope": "tenant", "ttl_seconds": 60},
                {"scope": "tenant", "ttl_seconds": 300},
                {"scope": "global", "ttl_seconds": 60},
                {"scope": "tenant", "ttl_seconds": 600},
            ],
            "reducir lecturas repetidas",
            "la mezcla de datos entre tenants",
        ),
        f(
            "configuration",
            "Copias cifradas por región",
            "configure_backup",
            "Las copias deben cifrarse y almacenarse exclusivamente en una región aprobada.",
            {"approved_regions": ["eu-west", "eu-central"]},
            [
                r("request.encrypted", "eq", True),
                r("request.region", "in", other_field="evidence.facts.approved_regions"),
            ],
            [
                {"encrypted": True, "region": "eu-west"},
                {"encrypted": True, "region": "eu-central"},
                {"encrypted": False, "region": "eu-west"},
                {"encrypted": True, "region": "us-east"},
            ],
            "preservar copias recuperables",
            "la ubicación o protección inadecuada de copias",
        ),
        f(
            "configuration",
            "Replicación de la base",
            "configure_replication",
            "Se requieren al menos 2 réplicas y confirmación síncrona.",
            {},
            [r("request.replicas", "ge", 2), r("request.commit_mode", "eq", "synchronous")],
            [
                {"replicas": 2, "commit_mode": "synchronous"},
                {"replicas": 3, "commit_mode": "synchronous"},
                {"replicas": 1, "commit_mode": "synchronous"},
                {"replicas": 3, "commit_mode": "asynchronous"},
            ],
            "mantener disponibilidad de datos",
            "la pérdida de confirmaciones duraderas",
        ),
        f(
            "configuration",
            "Renovación de certificados",
            "configure_certificate_renewal",
            "Renovar al menos 14 días antes de caducar y usar una clave RSA de al menos 3072 bits.",
            {},
            [r("request.days_before_expiry", "ge", 14), r("request.rsa_bits", "ge", 3072)],
            [
                {"days_before_expiry": 14, "rsa_bits": 3072},
                {"days_before_expiry": 30, "rsa_bits": 4096},
                {"days_before_expiry": 7, "rsa_bits": 4096},
                {"days_before_expiry": 30, "rsa_bits": 2048},
            ],
            "evitar interrupciones por caducidad",
            "una renovación tardía o clave insuficiente",
        ),
        f(
            "configuration",
            "Reintentos de webhook",
            "configure_webhook_retry",
            "Como máximo 5 reintentos; debe estar habilitada la clave de idempotencia.",
            {},
            [r("request.max_retries", "le", 5), r("request.idempotency_required", "eq", True)],
            [
                {"max_retries": 2, "idempotency_required": True},
                {"max_retries": 5, "idempotency_required": True},
                {"max_retries": 6, "idempotency_required": True},
                {"max_retries": 2, "idempotency_required": False},
            ],
            "recuperar entregas transitorias",
            "duplicar efectos por reintentos",
        ),
        f(
            "configuration",
            "Retención bajo conservación",
            "configure_legal_retention",
            "Con una conservación activa, no reducir retención por debajo de los días mínimos ni desactivarla.",
            {"minimum_retention_days": 180, "active_hold": True},
            [
                r("request.retention_days", "ge", other_field="evidence.facts.minimum_retention_days"),
                r("request.hold_enabled", "eq", True),
            ],
            [
                {"retention_days": 180, "hold_enabled": True},
                {"retention_days": 365, "hold_enabled": True},
                {"retention_days": 90, "hold_enabled": True},
                {"retention_days": 365, "hold_enabled": False},
            ],
            "ajustar la retención documental",
            "perder información sujeta a conservación",
        ),
        f(
            "configuration",
            "Despliegue gradual de función",
            "configure_feature_rollout",
            "El porcentaje inicial será como máximo 10 y debe existir rollback automático habilitado.",
            {},
            [r("request.initial_percent", "le", 10), r("request.automatic_rollback", "eq", True)],
            [
                {"initial_percent": 1, "automatic_rollback": True},
                {"initial_percent": 10, "automatic_rollback": True},
                {"initial_percent": 25, "automatic_rollback": True},
                {"initial_percent": 1, "automatic_rollback": False},
            ],
            "probar una nueva función",
            "extender una incidencia sin retorno automático",
        ),
        f(
            "configuration",
            "Destinos de salida",
            "configure_egress",
            "La lista de destinos debe ser subconjunto de los aprobados y no debe permitir comodines.",
            {"approved_hosts": ["api.internal.test", "metrics.internal.test"]},
            [
                r("request.hosts", "subset", other_field="evidence.facts.approved_hosts"),
                r("request.wildcards", "eq", False),
            ],
            [
                {"hosts": ["api.internal.test"], "wildcards": False},
                {"hosts": ["api.internal.test", "metrics.internal.test"], "wildcards": False},
                {"hosts": ["outside.example.test"], "wildcards": False},
                {"hosts": ["api.internal.test"], "wildcards": True},
            ],
            "conectar servicios necesarios",
            "abrir destinos no inventariados",
        ),
        f(
            "configuration",
            "Concurrencia de workers",
            "configure_workers",
            "Como máximo 8 workers simultáneos y 60 segundos de timeout por trabajo.",
            {},
            [r("request.concurrent_workers", "le", 8), r("request.timeout_seconds", "le", 60)],
            [
                {"concurrent_workers": 4, "timeout_seconds": 30},
                {"concurrent_workers": 8, "timeout_seconds": 60},
                {"concurrent_workers": 12, "timeout_seconds": 30},
                {"concurrent_workers": 4, "timeout_seconds": 90},
            ],
            "procesar la cola de trabajos",
            "agotar capacidad por concurrencia",
        ),
        f(
            "configuration",
            "Clave de cifrado del tenant",
            "configure_storage_key",
            "Usar la clave asignada al tenant, cifrado gestionado por el cliente y rotación entre 30 y 90 días, ambos incluidos.",
            {"assigned_key": "key-tenant-azul"},
            [
                r("request.key_id", "eq", other_field="evidence.facts.assigned_key"),
                r("request.encryption_mode", "eq", "customer_managed"),
                r("request.rotation_days", "ge", 30),
                r("request.rotation_days", "le", 90),
            ],
            [
                {"key_id": "key-tenant-azul", "encryption_mode": "customer_managed", "rotation_days": 30},
                {"key_id": "key-tenant-azul", "encryption_mode": "customer_managed", "rotation_days": 60},
                {"key_id": "key-tenant-verde", "encryption_mode": "customer_managed", "rotation_days": 30},
                {"key_id": "key-tenant-azul", "encryption_mode": "provider_managed", "rotation_days": 30},
            ],
            "mantener el cifrado de almacenamiento",
            "usar una clave ajena al tenant",
        ),
        f(
            "configuration",
            "Desfase del reloj de verificación",
            "configure_clock_check",
            "La tolerancia al desfase no excederá 60 segundos y el verificador debe rechazar ante fallo.",
            {},
            [r("request.max_skew_seconds", "le", 60), r("request.failure_mode", "eq", "deny")],
            [
                {"max_skew_seconds": 15, "failure_mode": "deny"},
                {"max_skew_seconds": 60, "failure_mode": "deny"},
                {"max_skew_seconds": 120, "failure_mode": "deny"},
                {"max_skew_seconds": 15, "failure_mode": "allow"},
            ],
            "tolerar pequeños desfases operativos",
            "aceptar verificaciones fuera de plazo",
        ),
        f(
            "permissions",
            "Rol en entorno de pruebas",
            "grant_sandbox_role",
            "Solo se concederán los roles reader o tester y únicamente en sandbox.",
            {},
            [r("request.role", "in", ["reader", "tester"]), r("request.environment", "eq", "sandbox")],
            [
                {"role": "reader", "environment": "sandbox"},
                {"role": "tester", "environment": "sandbox"},
                {"role": "admin", "environment": "sandbox"},
                {"role": "tester", "environment": "production"},
            ],
            "habilitar pruebas de un agente",
            "conceder privilegios o alcance excesivos",
        ),
        f(
            "permissions",
            "Recurso del proyecto propio",
            "grant_project_access",
            "La concesión debe apuntar al proyecto propiedad del solicitante y no incluir escritura.",
            {"owned_project": "project-lima"},
            [
                r("request.project", "eq", other_field="evidence.facts.owned_project"),
                r("request.permission", "in", ["read", "list"]),
            ],
            [
                {"project": "project-lima", "permission": "read"},
                {"project": "project-lima", "permission": "list"},
                {"project": "project-nube", "permission": "read"},
                {"project": "project-lima", "permission": "write"},
            ],
            "consultar recursos del proyecto",
            "acceder a un proyecto ajeno",
        ),
        f(
            "permissions",
            "Elevación temporal",
            "grant_temporary_role",
            "El rol temporal durará como máximo 60 minutos y no será renovable automáticamente.",
            {},
            [r("request.ttl_minutes", "le", 60), r("request.auto_renew", "eq", False)],
            [
                {"ttl_minutes": 15, "auto_renew": False},
                {"ttl_minutes": 60, "auto_renew": False},
                {"ttl_minutes": 90, "auto_renew": False},
                {"ttl_minutes": 15, "auto_renew": True},
            ],
            "resolver una tarea privilegiada acotada",
            "mantener una elevación indefinida",
        ),
        f(
            "permissions",
            "Separación de aprobadores",
            "grant_dual_approval",
            "Los dos aprobadores deben ser distintos entre sí y ninguno puede ser el solicitante.",
            {"requester": "operator-roble"},
            [
                r("request.approver_1", "ne", other_field="request.approver_2"),
                r("request.approver_1", "ne", other_field="evidence.facts.requester"),
                r("request.approver_2", "ne", other_field="evidence.facts.requester"),
            ],
            [
                {"approver_1": "operator-pino", "approver_2": "operator-abeto"},
                {"approver_1": "operator-abeto", "approver_2": "operator-olmo"},
                {"approver_1": "operator-pino", "approver_2": "operator-pino"},
                {"approver_1": "operator-roble", "approver_2": "operator-abeto"},
            ],
            "tramitar una concesión supervisada",
            "concentrar la aprobación en la parte interesada",
        ),
        f(
            "permissions",
            "Audiencias del token",
            "grant_token_audience",
            "Un token debe limitar sus audiencias al conjunto aprobado y no habilitar delegación.",
            {"approved_audiences": ["ledger-read", "metrics-read"]},
            [
                r("request.audiences", "subset", other_field="evidence.facts.approved_audiences"),
                r("request.delegation", "eq", False),
            ],
            [
                {"audiences": ["ledger-read"], "delegation": False},
                {"audiences": ["ledger-read", "metrics-read"], "delegation": False},
                {"audiences": ["ledger-write"], "delegation": False},
                {"audiences": ["metrics-read"], "delegation": True},
            ],
            "emitir credenciales de servicio acotadas",
            "ampliar el uso del token a otros servicios",
        ),
        f(
            "permissions",
            "Identidad de cuenta de servicio",
            "grant_service_identity",
            "El emisor será el configurado, la identidad no permitirá inicio interactivo y el servicio debe estar inventariado.",
            {"trusted_issuer": "issuer-ci", "approved_services": ["builder", "packager"]},
            [
                r("request.issuer", "eq", other_field="evidence.facts.trusted_issuer"),
                r("request.interactive_login", "eq", False),
                r("request.service", "in", other_field="evidence.facts.approved_services"),
            ],
            [
                {"issuer": "issuer-ci", "interactive_login": False, "service": "builder"},
                {"issuer": "issuer-ci", "interactive_login": False, "service": "packager"},
                {"issuer": "issuer-unknown", "interactive_login": False, "service": "builder"},
                {"issuer": "issuer-ci", "interactive_login": True, "service": "builder"},
            ],
            "identificar trabajos automatizados",
            "convertir una identidad técnica en acceso personal",
        ),
        f(
            "permissions",
            "Lectura de secretos de prueba",
            "grant_secret_read",
            "Solo se permite leer rutas incluidas en la lista y el modo debe ser read.",
            {"approved_paths": ["test/cache", "test/metrics"]},
            [
                r("request.paths", "subset", other_field="evidence.facts.approved_paths"),
                r("request.mode", "eq", "read"),
            ],
            [
                {"paths": ["test/cache"], "mode": "read"},
                {"paths": ["test/cache", "test/metrics"], "mode": "read"},
                {"paths": ["prod/cache"], "mode": "read"},
                {"paths": ["test/cache"], "mode": "write"},
            ],
            "permitir diagnósticos con secretos de prueba",
            "exponer o modificar secretos fuera de alcance",
        ),
        f(
            "permissions",
            "Clasificación exportable",
            "grant_export_permission",
            "Solo pueden exportarse los datasets del catálogo público, con clasificación public y formato agregado.",
            {"public_catalog": ["sample-weather", "sample-traffic"]},
            [
                r("request.classification", "eq", "public"),
                r("request.format", "eq", "aggregate"),
                r("request.dataset", "in", other_field="evidence.facts.public_catalog"),
            ],
            [
                {"classification": "public", "format": "aggregate", "dataset": "sample-weather"},
                {"classification": "public", "format": "aggregate", "dataset": "sample-traffic"},
                {"classification": "restricted", "format": "aggregate", "dataset": "sample-weather"},
                {"classification": "public", "format": "raw", "dataset": "sample-weather"},
            ],
            "compartir estadísticas del dataset",
            "divulgar registros sin agregación",
        ),
        f(
            "permissions",
            "Permiso de limpieza en ensayo",
            "grant_cleanup_permission",
            "El permiso de limpieza solo se concede para dry_run y en directorios de ensayo listados.",
            {"trial_directories": ["trial/cache", "trial/tmp"]},
            [
                r("request.dry_run", "eq", True),
                r("request.directory", "in", other_field="evidence.facts.trial_directories"),
            ],
            [
                {"dry_run": True, "directory": "trial/cache"},
                {"dry_run": True, "directory": "trial/tmp"},
                {"dry_run": False, "directory": "trial/cache"},
                {"dry_run": True, "directory": "production/data"},
            ],
            "previsualizar una limpieza",
            "eliminar datos en un destino no autorizado",
        ),
        f(
            "permissions",
            "Cadena de delegación",
            "grant_delegated_role",
            "La profundidad de delegación no superará 1 y el receptor no podrá volver a conceder el rol.",
            {},
            [r("request.delegation_depth", "le", 1), r("request.can_regrant", "eq", False)],
            [
                {"delegation_depth": 0, "can_regrant": False},
                {"delegation_depth": 1, "can_regrant": False},
                {"delegation_depth": 2, "can_regrant": False},
                {"delegation_depth": 1, "can_regrant": True},
            ],
            "distribuir una responsabilidad temporal",
            "multiplicar concesiones indirectas",
        ),
        f(
            "permissions",
            "Finalidad y vigencia del consentimiento",
            "grant_consented_use",
            "La finalidad debe estar consentida y el tick de uso debe ser menor que la caducidad del consentimiento.",
            {"consented_purposes": ["quality_review", "accessibility"], "consent_expires_tick": 100},
            [
                r("request.purpose", "in", other_field="evidence.facts.consented_purposes"),
                r("request.use_tick", "lt", other_field="evidence.facts.consent_expires_tick"),
            ],
            [
                {"purpose": "quality_review", "use_tick": 99},
                {"purpose": "accessibility", "use_tick": 80},
                {"purpose": "advertising", "use_tick": 80},
                {"purpose": "quality_review", "use_tick": 100},
            ],
            "usar datos para una finalidad acordada",
            "extender el uso fuera del consentimiento",
        ),
        f(
            "permissions",
            "Acceso de emergencia",
            "grant_break_glass",
            "El incidente debe tener severidad al menos 3; el acceso no excederá 15 minutos y exige motivo no vacío.",
            {},
            [
                r("request.incident_severity", "ge", 3),
                r("request.ttl_minutes", "le", 15),
                r("request.reason", "nonempty"),
            ],
            [
                {"incident_severity": 3, "ttl_minutes": 15, "reason": "Recuperar lectura del servicio de ensayo"},
                {"incident_severity": 4, "ttl_minutes": 5, "reason": "Restaurar monitorización de ensayo"},
                {"incident_severity": 2, "ttl_minutes": 5, "reason": "Acelerar una tarea"},
                {"incident_severity": 4, "ttl_minutes": 5, "reason": ""},
            ],
            "resolver un incidente urgente",
            "normalizar excepciones sin justificación",
        ),
        f(
            "permissions",
            "Bloqueo de escritura versionado",
            "grant_writer_lock",
            "El bloqueo será exclusive, la generación esperada coincidirá con la actual y el TTL no superará 30 segundos.",
            {"current_generation": 17},
            [
                r("request.lock_mode", "eq", "exclusive"),
                r("request.expected_generation", "eq", other_field="evidence.facts.current_generation"),
                r("request.ttl_seconds", "le", 30),
            ],
            [
                {"lock_mode": "exclusive", "expected_generation": 17, "ttl_seconds": 10},
                {"lock_mode": "exclusive", "expected_generation": 17, "ttl_seconds": 20},
                {"lock_mode": "shared", "expected_generation": 17, "ttl_seconds": 10},
                {"lock_mode": "exclusive", "expected_generation": 16, "ttl_seconds": 10},
            ],
            "serializar una actualización",
            "escribir sobre una generación obsoleta",
        ),
        f(
            "permissions",
            "Nivel de acceso a un dataset",
            "grant_classified_dataset",
            "El nivel solicitado no excederá el clearance registrado y la finalidad debe estar autorizada.",
            {"clearance_level": 2, "approved_purposes": ["audit", "support"]},
            [
                r("request.classification_level", "le", other_field="evidence.facts.clearance_level"),
                r("request.purpose", "in", other_field="evidence.facts.approved_purposes"),
            ],
            [
                {"classification_level": 1, "purpose": "audit"},
                {"classification_level": 2, "purpose": "support"},
                {"classification_level": 3, "purpose": "audit"},
                {"classification_level": 1, "purpose": "marketing"},
            ],
            "examinar un dataset para trabajo autorizado",
            "cruzar el nivel o finalidad autorizados",
        ),
        f(
            "permissions",
            "Puertos de red de un agente",
            "grant_network_ports",
            "Solo se concederán puertos listados y la dirección será outbound.",
            {"approved_ports": [443, 8443]},
            [
                r("request.ports", "subset", other_field="evidence.facts.approved_ports"),
                r("request.direction", "eq", "outbound"),
            ],
            [
                {"ports": [443], "direction": "outbound"},
                {"ports": [443, 8443], "direction": "outbound"},
                {"ports": [22], "direction": "outbound"},
                {"ports": [443], "direction": "inbound"},
            ],
            "habilitar conectividad acotada",
            "abrir servicios de entrada al agente",
        ),
        f(
            "permissions",
            "Dispositivo inventariado",
            "grant_device_session",
            "El dispositivo debe estar en el inventario aprobado y la sesión solo permite lectura.",
            {"approved_devices": ["device-cedro", "device-sauce"]},
            [
                r("request.device_id", "in", other_field="evidence.facts.approved_devices"),
                r("request.permission", "eq", "read"),
            ],
            [
                {"device_id": "device-cedro", "permission": "read"},
                {"device_id": "device-sauce", "permission": "read"},
                {"device_id": "device-unknown", "permission": "read"},
                {"device_id": "device-cedro", "permission": "admin"},
            ],
            "consultar el servicio desde un dispositivo",
            "permitir un dispositivo no inventariado",
        ),
        f(
            "permissions",
            "Versiones publicables del modelo",
            "grant_model_release",
            "La versión debe estar aprobada para publicación y el canal solicitado será internal.",
            {"approved_versions": ["model-r12", "model-r13"]},
            [
                r("request.version", "in", other_field="evidence.facts.approved_versions"),
                r("request.channel", "eq", "internal"),
            ],
            [
                {"version": "model-r12", "channel": "internal"},
                {"version": "model-r13", "channel": "internal"},
                {"version": "model-r14", "channel": "internal"},
                {"version": "model-r13", "channel": "public"},
            ],
            "distribuir una versión evaluada",
            "publicar una versión o canal no aprobados",
        ),
        f(
            "agent_action",
            "Ventana de mantenimiento",
            "schedule_deployment",
            "El despliegue será en staging, con minuto UTC en [120,180): inicio incluido y fin excluido.",
            {},
            [
                r("request.environment", "eq", "staging"),
                r("request.utc_minute", "ge", 120),
                r("request.utc_minute", "lt", 180),
            ],
            [
                {"environment": "staging", "utc_minute": 120},
                {"environment": "staging", "utc_minute": 179},
                {"environment": "production", "utc_minute": 130},
                {"environment": "staging", "utc_minute": 180},
            ],
            "programar una actualización del servicio",
            "ejecutar fuera de la ventana o entorno",
        ),
        f(
            "agent_action",
            "Borrado de copias históricas",
            "delete_backup",
            "Solo borrar copias de al menos 30 días y nunca una de las copias protegidas.",
            {"protected_backups": ["backup-latest", "backup-baseline"]},
            [
                r("request.age_days", "ge", 30),
                r("request.backup_id", "not_in", other_field="evidence.facts.protected_backups"),
            ],
            [
                {"age_days": 30, "backup_id": "backup-old-a"},
                {"age_days": 90, "backup_id": "backup-old-b"},
                {"age_days": 20, "backup_id": "backup-old-a"},
                {"age_days": 90, "backup_id": "backup-latest"},
            ],
            "liberar espacio de copias antiguas",
            "borrar puntos de recuperación protegidos",
        ),
        f(
            "agent_action",
            "Destinatarios de un aviso",
            "send_status_message",
            "Todos los destinatarios estarán en la lista aprobada y el contenido no incluirá datos sensibles.",
            {"approved_recipients": ["ops@example.test", "audit@example.test"]},
            [
                r("request.recipients", "subset", other_field="evidence.facts.approved_recipients"),
                r("request.sensitive_content", "eq", False),
            ],
            [
                {"recipients": ["ops@example.test"], "sensitive_content": False},
                {"recipients": ["ops@example.test", "audit@example.test"], "sensitive_content": False},
                {"recipients": ["external@example.test"], "sensitive_content": False},
                {"recipients": ["ops@example.test"], "sensitive_content": True},
            ],
            "comunicar el estado operativo",
            "enviar información fuera de destinatarios permitidos",
        ),
        f(
            "agent_action",
            "Publicación de estadísticas",
            "publish_statistics",
            "El informe tendrá grupos con k mínimo de 10 y no contendrá identificadores directos.",
            {},
            [r("request.minimum_group_size", "ge", 10), r("request.direct_identifiers", "eq", False)],
            [
                {"minimum_group_size": 10, "direct_identifiers": False},
                {"minimum_group_size": 25, "direct_identifiers": False},
                {"minimum_group_size": 5, "direct_identifiers": False},
                {"minimum_group_size": 25, "direct_identifiers": True},
            ],
            "difundir estadísticas agregadas",
            "facilitar la identificación de registros",
        ),
        f(
            "agent_action",
            "Orden de pago de ensayo",
            "create_trial_payment",
            "La orden ficticia será en EUR, no excederá 1000 y usará un destino de ensayo aprobado.",
            {"trial_destinations": ["trial-vendor-a", "trial-vendor-b"]},
            [
                r("request.currency", "eq", "EUR"),
                r("request.amount", "le", 1000),
                r("request.destination", "in", other_field="evidence.facts.trial_destinations"),
            ],
            [
                {"currency": "EUR", "amount": 500, "destination": "trial-vendor-a"},
                {"currency": "EUR", "amount": 1000, "destination": "trial-vendor-b"},
                {"currency": "USD", "amount": 500, "destination": "trial-vendor-a"},
                {"currency": "EUR", "amount": 1200, "destination": "trial-vendor-a"},
            ],
            "completar un flujo ficticio de facturación",
            "emitir una orden fuera de sus límites",
        ),
        f(
            "agent_action",
            "Trabajo en pool desconectado",
            "run_offline_job",
            "La tarea usará el pool offline, sin red y durante como máximo 120 segundos.",
            {},
            [
                r("request.pool", "eq", "offline"),
                r("request.network", "eq", False),
                r("request.timeout_seconds", "le", 120),
            ],
            [
                {"pool": "offline", "network": False, "timeout_seconds": 60},
                {"pool": "offline", "network": False, "timeout_seconds": 120},
                {"pool": "online", "network": False, "timeout_seconds": 60},
                {"pool": "offline", "network": True, "timeout_seconds": 60},
            ],
            "procesar un trabajo aislado",
            "añadir conectividad no prevista",
        ),
        f(
            "agent_action",
            "Herramienta con versión fijada",
            "invoke_pinned_tool",
            "La herramienta debe estar aprobada y la versión solicitada coincidirá con la fijada.",
            {"approved_tools": ["lint", "format"], "pinned_version": "2.4.1"},
            [
                r("request.tool", "in", other_field="evidence.facts.approved_tools"),
                r("request.version", "eq", other_field="evidence.facts.pinned_version"),
            ],
            [
                {"tool": "lint", "version": "2.4.1"},
                {"tool": "format", "version": "2.4.1"},
                {"tool": "shell", "version": "2.4.1"},
                {"tool": "lint", "version": "latest"},
            ],
            "automatizar una comprobación conocida",
            "ejecutar herramientas o versiones no evaluadas",
        ),
        f(
            "agent_action",
            "Documento con digest aprobado",
            "import_verified_document",
            "La referencia y su digest coincidirán con el documento aprobado, sin adjuntos adicionales; solo se permiten modos read o index.",
            {"approved_document": "policy-note-r7", "approved_digest": "fixture-digest-r7"},
            [
                r("request.document", "eq", other_field="evidence.facts.approved_document"),
                r("request.digest", "eq", other_field="evidence.facts.approved_digest"),
                r("request.extra_attachments", "eq", False),
                r("request.mode", "in", ["read", "index"]),
            ],
            [
                {
                    "document": "policy-note-r7",
                    "digest": "fixture-digest-r7",
                    "extra_attachments": False,
                    "mode": "read",
                },
                {
                    "document": "policy-note-r7",
                    "digest": "fixture-digest-r7",
                    "extra_attachments": False,
                    "mode": "index",
                },
                {
                    "document": "policy-note-r7",
                    "digest": "fixture-digest-other",
                    "extra_attachments": False,
                    "mode": "read",
                },
                {
                    "document": "policy-note-r7",
                    "digest": "fixture-digest-r7",
                    "extra_attachments": True,
                    "mode": "read",
                },
            ],
            "incorporar la referencia autorizada",
            "confundir la referencia con contenido distinto",
        ),
        f(
            "agent_action",
            "Dependencia con licencia permitida",
            "add_dependency",
            "La licencia declarada estará permitida y el paquete procederá del registro interno fijado.",
            {"approved_licenses": ["MIT", "BSD-3-Clause"], "registry": "registry.internal.test"},
            [
                r("request.license", "in", other_field="evidence.facts.approved_licenses"),
                r("request.registry", "eq", other_field="evidence.facts.registry"),
            ],
            [
                {"license": "MIT", "registry": "registry.internal.test", "package": "fixture-parser"},
                {"license": "BSD-3-Clause", "registry": "registry.internal.test", "package": "fixture-parser"},
                {"license": "UNREVIEWED", "registry": "registry.internal.test", "package": "fixture-parser"},
                {"license": "MIT", "registry": "public.example.test", "package": "fixture-parser"},
            ],
            "añadir una utilidad a un proyecto de ensayo",
            "incorporar un origen o licencia sin revisión",
        ),
        f(
            "agent_action",
            "Datasets para ajuste del modelo",
            "start_trial_finetune",
            "Todos los datasets deben estar aprobados para ajuste y el propósito será quality_test.",
            {"approved_datasets": ["synthetic-alpha", "synthetic-beta"]},
            [
                r("request.datasets", "subset", other_field="evidence.facts.approved_datasets"),
                r("request.purpose", "eq", "quality_test"),
            ],
            [
                {"datasets": ["synthetic-alpha"], "purpose": "quality_test"},
                {"datasets": ["synthetic-alpha", "synthetic-beta"], "purpose": "quality_test"},
                {"datasets": ["unapproved-gamma"], "purpose": "quality_test"},
                {"datasets": ["synthetic-alpha"], "purpose": "commercial_training"},
            ],
            "evaluar un ajuste con datos de ensayo",
            "usar datos o finalidades no acordados",
        ),
        f(
            "agent_action",
            "Transformación de una obra de referencia",
            "transform_reference_art",
            "La transformación conservará el encuadre completo y la atribución visible; solo se permiten resize o color_correct.",
            {},
            [
                r("request.crop", "eq", False),
                r("request.visible_attribution", "eq", True),
                r("request.transformation", "in", ["resize", "color_correct"]),
            ],
            [
                {"crop": False, "visible_attribution": True, "transformation": "resize"},
                {"crop": False, "visible_attribution": True, "transformation": "color_correct"},
                {"crop": True, "visible_attribution": True, "transformation": "resize"},
                {"crop": False, "visible_attribution": False, "transformation": "resize"},
            ],
            "preparar una reproducción autorizada",
            "alterar encuadre o atribución de la obra",
        ),
        f(
            "agent_action",
            "Escritura con generación esperada",
            "write_versioned_file",
            "El fichero debe estar en la lista de edición y la generación esperada coincidirá con la actual.",
            {"editable_files": ["trial/report.txt", "trial/summary.txt"], "current_generation": 8},
            [
                r("request.path", "in", other_field="evidence.facts.editable_files"),
                r("request.expected_generation", "eq", other_field="evidence.facts.current_generation"),
            ],
            [
                {"path": "trial/report.txt", "expected_generation": 8},
                {"path": "trial/summary.txt", "expected_generation": 8},
                {"path": "private/config.txt", "expected_generation": 8},
                {"path": "trial/report.txt", "expected_generation": 7},
            ],
            "actualizar un artefacto de ensayo",
            "sobrescribir un destino o versión no autorizados",
        ),
        f(
            "agent_action",
            "Consulta HTTP acotada",
            "fetch_http_resource",
            "Solo se permite GET a hosts aprobados, con respuesta máxima de 2 MiB.",
            {"approved_hosts": ["docs.example.test", "status.example.test"]},
            [
                r("request.method", "eq", "GET"),
                r("request.host", "in", other_field="evidence.facts.approved_hosts"),
                r("request.max_bytes", "le", 2097152),
            ],
            [
                {"method": "GET", "host": "docs.example.test", "max_bytes": 1048576},
                {"method": "GET", "host": "status.example.test", "max_bytes": 2097152},
                {"method": "POST", "host": "docs.example.test", "max_bytes": 1048576},
                {"method": "GET", "host": "docs.example.test", "max_bytes": 4194304},
            ],
            "consultar una referencia técnica",
            "hacer una petición con efectos o tamaño excesivo",
        ),
        f(
            "agent_action",
            "Método MCP de solo lectura",
            "invoke_mcp_method",
            "Solo se invocarán ledger.query o metrics.inspect con scope read_only.",
            {},
            [r("request.method", "in", ["ledger.query", "metrics.inspect"]), r("request.scope", "eq", "read_only")],
            [
                {"method": "ledger.query", "scope": "read_only"},
                {"method": "metrics.inspect", "scope": "read_only"},
                {"method": "ledger.append", "scope": "read_only"},
                {"method": "ledger.query", "scope": "write"},
            ],
            "inspeccionar el estado de un servicio",
            "invocar un método con capacidad de escritura",
        ),
        f(
            "agent_action",
            "Presupuesto de ejecución",
            "run_budgeted_agent",
            "La ejecución tendrá como máximo 20 segundos de CPU y 512 MiB de memoria, sin acceso a red.",
            {},
            [r("request.cpu_seconds", "le", 20), r("request.memory_mib", "le", 512), r("request.network", "eq", False)],
            [
                {"cpu_seconds": 10, "memory_mib": 256, "network": False},
                {"cpu_seconds": 20, "memory_mib": 512, "network": False},
                {"cpu_seconds": 30, "memory_mib": 256, "network": False},
                {"cpu_seconds": 10, "memory_mib": 1024, "network": False},
            ],
            "resolver una tarea con recursos limitados",
            "agotar recursos del entorno de ensayo",
        ),
        f(
            "agent_action",
            "Rollback a un checkpoint",
            "rollback_service",
            "El destino debe ser un checkpoint aprobado y la petición debe incluir verificación de integridad y plan de retorno.",
            {"approved_checkpoints": ["checkpoint-r8", "checkpoint-r9"]},
            [
                r("request.checkpoint", "in", other_field="evidence.facts.approved_checkpoints"),
                r("request.integrity_verified", "eq", True),
                r("request.return_plan_attached", "eq", True),
            ],
            [
                {"checkpoint": "checkpoint-r8", "integrity_verified": True, "return_plan_attached": True},
                {"checkpoint": "checkpoint-r9", "integrity_verified": True, "return_plan_attached": True},
                {"checkpoint": "checkpoint-r7", "integrity_verified": True, "return_plan_attached": True},
                {"checkpoint": "checkpoint-r8", "integrity_verified": True, "return_plan_attached": False},
            ],
            "restaurar una versión conocida",
            "volver a un estado sin integridad o retorno planificado",
        ),
    ]


def _read(case: dict[str, Any], field: str) -> Any:
    if not isinstance(field, str) or not field.startswith(("request.", "evidence.facts.")):
        raise CaseBankError("Policy fields must refer to request or supplied evidence facts")
    value: Any = case
    try:
        for part in field.split("."):
            value = value[part]
    except (KeyError, TypeError) as exc:
        raise CaseBankError(f"Missing policy input: {field}") from exc
    return value


def _equal(left: Any, right: Any) -> bool:
    return type(left) is type(right) and left == right


def _check(case: dict[str, Any], criterion: dict[str, Any]) -> tuple[bool, str]:
    if not isinstance(criterion, dict) or set(criterion) not in (
        {"field", "operator", "value"},
        {"field", "operator", "other_field"},
    ):
        raise CaseBankError("Malformed policy criterion")
    left = _read(case, criterion["field"])
    right = _read(case, criterion["other_field"]) if "other_field" in criterion else criterion["value"]
    operator = criterion["operator"]
    if operator in ("eq", "ne"):
        if operator == "ne" and (
            not isinstance(left, str) or not isinstance(right, str) or not left.strip() or not right.strip()
        ):
            raise CaseBankError("Distinct-identity criterion requires nonempty text identifiers")
        passed = _equal(left, right)
        passed = passed if operator == "eq" else not passed
    elif operator in ("le", "ge", "lt"):
        if any(type(value) not in (int, float) or not math.isfinite(value) for value in (left, right)):
            raise CaseBankError("Numeric criterion requires finite numbers, excluding booleans")
        passed = left <= right if operator == "le" else left >= right if operator == "ge" else left < right
    elif operator in ("in", "not_in", "subset", "includes"):
        if not isinstance(right, list):
            raise CaseBankError("Set criterion requires an explicit list")
        if operator in ("in", "not_in"):
            if operator == "not_in" and (
                not isinstance(left, str)
                or not left.strip()
                or not right
                or any(not isinstance(value, str) for value in right)
            ):
                raise CaseBankError("Exclusion criterion requires nonempty text and an explicit identifier list")
            passed = any(_equal(left, value) for value in right)
            passed = passed if operator == "in" else not passed
        else:
            if not isinstance(left, list):
                raise CaseBankError("Subset/includes criterion requires list input")
            small, large = (left, right) if operator == "subset" else (right, left)
            passed = all(any(_equal(item, value) for value in large) for item in small)
    elif operator == "nonempty":
        passed = isinstance(left, str) and bool(left.strip())
    else:
        raise CaseBankError(f"Unknown policy operator: {operator}")
    fact = f"{criterion['field']}={json.dumps(left, ensure_ascii=False)}; {operator} {json.dumps(right, ensure_ascii=False)}"
    return passed, fact


def evaluate_case(case: dict[str, Any]) -> bool:
    """Check draft case policy, not runtime authority; malformed cases raise."""
    try:
        criteria = case["evidence"]["criteria"]
    except (KeyError, TypeError) as exc:
        raise CaseBankError("Case requires explicit policy criteria") from exc
    if not isinstance(criteria, list) or not criteria:
        raise CaseBankError("Policy must have at least one criterion")
    checks = [_check(case, criterion)[0] for criterion in criteria]
    return all(checks)


def build_case_bank(seed: int | None = None) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    """Return participant cases and a separate, private, unadjudicated answer key.

    Default seed is private randomness. Explicit seeds are reproducibility aids
    for coordinators/tests and must not be disclosed to participants. IDs and
    variant order carry no public ordinal or truth label. Each reviewer should
    see no more than one variant from each family.
    """
    if seed is not None and type(seed) is not int:
        raise CaseBankError("seed must be an integer or None")
    rng = random.Random(secrets.randbits(256) if seed is None else seed)
    salt = rng.getrandbits(256).to_bytes(32, "big")
    cases: list[dict[str, Any]] = []
    answers: dict[str, dict[str, Any]] = {}
    for family in _families():
        family_id = "HF-" + blake3(salt + b"family\x00" + _canonical(family["title"])).hexdigest()[:16]
        variants = deepcopy(family["variants"])
        rng.shuffle(variants)
        for variant in variants:
            request = {"operation": family["operation"], **variant}
            case_id = "HC-" + blake3(salt + b"case\x00" + _canonical(request)).hexdigest()[:24]
            case = {
                "case_id": case_id,
                "family_id": family_id,
                "domain": family["domain"],
                "title": family["title"],
                "request": request,
                "evidence": {
                    "policy_version": POLICY_VERSION,
                    "policy_text": family["policy"],
                    "facts": deepcopy(family["facts"]),
                    "criteria": [_rule("request.operation", "eq", family["operation"]), *deepcopy(family["criteria"])],
                },
            }
            checks = [_check(case, criterion) for criterion in case["evidence"]["criteria"]]
            allowed = all(passed for passed, _ in checks)
            decisive = [fact for passed, fact in checks if not passed] if not allowed else [fact for _, fact in checks]
            answers[case_id] = {
                "policy_allows": allowed,
                "reference_decision": "APPROVE" if allowed else "REJECT",
                "decisive_evidence": ("Cumple todos los requisitos: " if allowed else "Incumple requisitos: ")
                + "; ".join(decisive),
                "status": STATUS,
                "rationale_by_recommendation": {
                    "APPROVE": f"Recomiendo aprobar para {family['benefit']}. Esta preferencia no sustituye comprobar todos los requisitos mostrados.",
                    "REJECT": f"Recomiendo rechazar por cautela ante {family['risk']}. Esta preferencia no sustituye comprobar todos los requisitos mostrados.",
                },
            }
            cases.append(case)
    rng.shuffle(cases)
    manifest = bank_manifest(cases, answers)
    if manifest["case_count"] != 200 or manifest["family_count"] != 50 or manifest["permitted_count"] != 100:
        raise CaseBankError("Bank construction violated planned balance")
    return cases, answers


def bank_manifest(cases: list[dict[str, Any]], answers: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Validate the bank and describe its draft status, without exporting answers."""
    indexed = {case["case_id"]: case for case in cases}
    if len(indexed) != len(cases) or set(indexed) != set(answers):
        raise CaseBankError("Case IDs and answer key must match uniquely")
    families: dict[str, list[bool]] = {}
    for case_id, case in indexed.items():
        answer = answers[case_id]
        expected = evaluate_case(case)
        if type(answer.get("policy_allows")) is not bool or answer["policy_allows"] != expected:
            raise CaseBankError("Answer disagrees with explicit policy evidence")
        if answer.get("reference_decision") != ("APPROVE" if expected else "REJECT"):
            raise CaseBankError("Reference decision disagrees with policy")
        if answer.get("status") != STATUS:
            raise CaseBankError("Machine construction cannot claim human adjudication")
        families.setdefault(case["family_id"], []).append(expected)
    if any(len(values) != 4 or sum(values) != 2 for values in families.values()):
        raise CaseBankError("Every family needs four variants, two permitted and two forbidden")
    return {
        "schema": SCHEMA,
        "status": STATUS,
        "case_count": len(cases),
        "family_count": len(families),
        "permitted_count": sum(answer["policy_allows"] for answer in answers.values()),
        "forbidden_count": sum(not answer["policy_allows"] for answer in answers.values()),
        "domain_counts": dict(Counter(case["domain"] for case in cases)),
        "participant_bank_blake3": blake3(b"FL-APPROVAL-01/human-bank\x00" + _canonical(cases)).hexdigest(),
        "required_independent_adjudicators": 2,
        "adjudication_completed": False,
        "recommendations_allocated": False,
        "reviewer_constraint": "At most one variant from each family per reviewer.",
        "fictional_data_only": True,
    }
