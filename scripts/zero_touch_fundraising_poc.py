#!/usr/bin/env python3
"""
Zero-Touch Fundraising Proof of Concept (PoC)
==============================================
Arquitectura de captación de capital asíncrona, desprovista de contacto humano.
Sustituye la trampa somática por scoring algorítmico de telemetría, filtrado 
estricto de inbound (Anti-Call Gate) y emisión determinista de SAFEs sellados en SHA-256.

Uso:
    python3 scripts/zero_touch_fundraising_poc.py --demo
    python3 scripts/zero_touch_fundraising_poc.py --test
"""

import argparse
import dataclasses
import hashlib
import json
import sys
import time
from typing import Dict, List, Optional, Tuple


@dataclasses.dataclass(frozen=True)
class CompanyTelemetry:
    mrr_usd: float
    churn_monthly_pct: float
    nrr_annual_pct: float
    cac_usd: float
    ltv_usd: float
    runway_months: float
    active_users: int

    @property
    def arr_usd(self) -> float:
        return self.mrr_usd * 12.0

    @property
    def ltv_cac_ratio(self) -> float:
        if self.cac_usd <= 0:
            return 999.0
        return self.ltv_usd / self.cac_usd


@dataclasses.dataclass(frozen=True)
class RoundTerms:
    target_raise_usd: float
    post_money_cap_usd: float
    discount_rate_pct: float
    min_ticket_usd: float
    treasury_multisig: str
    wire_routing_code: str


@dataclasses.dataclass(frozen=True)
class InvestorInquiry:
    inquiry_id: str
    entity_name: str
    proposed_ticket_usd: float
    requires_sync_call: bool
    demands_board_seat: bool
    demands_custom_terms: bool
    accepts_standard_safe: bool
    kyc_accredited_verified: bool
    contact_email: str


@dataclasses.dataclass(frozen=True)
class AdmissionDecision:
    inquiry_id: str
    status: str  # ACCEPTED | REJECTED
    reason_code: str
    rejection_details: Optional[str] = None
    allocated_ticket_usd: float = 0.0
    safe_contract_hash: Optional[str] = None
    dispatch_instructions: Optional[Dict[str, str]] = None


class TelemetryScoringKernel:
    """Evalúa la solvencia exergética de la empresa a partir de telemetría de silicio."""

    @staticmethod
    def evaluate_telemetry(metrics: CompanyTelemetry) -> Tuple[float, float, str]:
        """
        Retorna:
            (health_score [0..100], recommended_cap_usd, status_verdict)
        """
        score = 0.0

        # 1. ARR baseline
        if metrics.arr_usd >= 1_000_000:
            score += 30.0
        elif metrics.arr_usd >= 250_000:
            score += 20.0
        elif metrics.arr_usd >= 50_000:
            score += 10.0

        # 2. Churn control (invariante de retención)
        if metrics.churn_monthly_pct < 1.0:
            score += 25.0
        elif metrics.churn_monthly_pct < 2.5:
            score += 15.0
        elif metrics.churn_monthly_pct > 5.0:
            score -= 15.0

        # 3. NRR (Expansión)
        if metrics.nrr_annual_pct >= 120.0:
            score += 25.0
        elif metrics.nrr_annual_pct >= 105.0:
            score += 15.0

        # 4. LTV/CAC
        if metrics.ltv_cac_ratio >= 4.0:
            score += 20.0
        elif metrics.ltv_cac_ratio >= 3.0:
            score += 10.0

        score = max(0.0, min(100.0, score))

        # Multiplicador de valoración dinámico basado en salud
        if score >= 80.0:
            multiplier = 25.0
            verdict = "TIER_A_SOVEREIGN_PRIME"
        elif score >= 60.0:
            multiplier = 15.0
            verdict = "TIER_B_HIGH_EXERGY"
        else:
            multiplier = 8.0
            verdict = "TIER_C_EARLY_STAGE"

        recommended_cap = metrics.arr_usd * multiplier
        return score, recommended_cap, verdict


class AntiAnergyInboundGate:
    """
    Filtro determinista de admisión de inversores.
    Ejecuta el Invariante de Desacoplamiento Somático:
    Cero reuniones síncronas, cero asimetrías de gobernanza, cero regateo legal.
    """

    @staticmethod
    def audit_inquiry(inquiry: InvestorInquiry, terms: RoundTerms) -> AdmissionDecision:
        # Veto 1: Intento de forzar llamada síncrona / reunión presencial
        if inquiry.requires_sync_call:
            return AdmissionDecision(
                inquiry_id=inquiry.inquiry_id,
                status="REJECTED",
                reason_code="ERR_ANERGY_SYNC_CALL_ATTEMPT",
                rejection_details=(
                    "El proyecto opera bajo clausura asíncrona estricta. "
                    "Se rechazan reuniones de Zoom, llamadas y cafés corporativos. "
                    "Toda la due diligence reside auditada en el data room de silicio."
                ),
            )

        # Veto 2: Intrusión en gobernanza (exigencia de asiento en el consejo)
        if inquiry.demands_board_seat:
            return AdmissionDecision(
                inquiry_id=inquiry.inquiry_id,
                status="REJECTED",
                reason_code="ERR_GOVERNANCE_INTRUSION",
                rejection_details=(
                    "Inversión no dilutiva en gobernanza. Los SAFEs estandarizados no otorgan "
                    "asientos en consejo ni derechos de veto sobre el Operador Soberano."
                ),
            )

        # Veto 3: Coste de fricción legal (modificaciones personalizadas a contratos)
        if inquiry.demands_custom_terms or not inquiry.accepts_standard_safe:
            return AdmissionDecision(
                inquiry_id=inquiry.inquiry_id,
                status="REJECTED",
                reason_code="ERR_CUSTOM_LEGAL_OVERHEAD",
                rejection_details=(
                    "Solo se admiten contratos Post-Money SAFE estándar YC con Cap cerrado. "
                    "Queda prohibida la negociación bilateral de cláusulas parasitarias."
                ),
            )

        # Veto 4: Ticket inferior al umbral mínimo
        if inquiry.proposed_ticket_usd < terms.min_ticket_usd:
            return AdmissionDecision(
                inquiry_id=inquiry.inquiry_id,
                status="REJECTED",
                reason_code="ERR_SUB_THRESHOLD_TICKET",
                rejection_details=(
                    f"El ticket propuesto (${inquiry.proposed_ticket_usd:,.2f}) es inferior "
                    f"al umbral de activación asignado (${terms.min_ticket_usd:,.2f})."
                ),
            )

        # Veto 5: Falta de acreditación KYC
        if not inquiry.kyc_accredited_verified:
            return AdmissionDecision(
                inquiry_id=inquiry.inquiry_id,
                status="REJECTED",
                reason_code="ERR_UNVERIFIED_ACCREDITATION",
                rejection_details="Inversor sin hash de acreditación o certificación institucional válida.",
            )

        # Admisión válida: Generar contrato SAFE determinista
        safe_hash, contract_text = SafeContractGenerator.compile_post_money_safe(
            investor_name=inquiry.entity_name,
            ticket_usd=inquiry.proposed_ticket_usd,
            post_money_cap_usd=terms.post_money_cap_usd,
            discount_pct=terms.discount_rate_pct,
        )

        dispatch_info = {
            "safe_contract_sha256": safe_hash,
            "usdc_settlement_address": terms.treasury_multisig,
            "wire_settlement_reference": f"SAFE-REF-{inquiry.inquiry_id}",
            "execution_mode": "PURE_ASYNC_SILICON_SETTLEMENT",
        }

        return AdmissionDecision(
            inquiry_id=inquiry.inquiry_id,
            status="ACCEPTED",
            reason_code="STATUS_ADMITTED_ZERO_TOUCH",
            allocated_ticket_usd=inquiry.proposed_ticket_usd,
            safe_contract_hash=safe_hash,
            dispatch_instructions=dispatch_info,
        )


class SafeContractGenerator:
    """Generador determinista de contratos SAFE YC Post-Money sellados en SHA-256."""

    @staticmethod
    def compile_post_money_safe(
        investor_name: str,
        ticket_usd: float,
        post_money_cap_usd: float,
        discount_pct: float,
    ) -> Tuple[str, str]:
        contract_template = f"""
================================================================================
POST-MONEY SIMPLE AGREEMENT FOR FUTURE EQUITY (SAFE)
STANDARD C5-REAL ZERO-TOUCH CONTRACT SPECIFICATION
================================================================================
INVESTOR:               {investor_name}
PURCHASE AMOUNT (USD):  ${ticket_usd:,.2f}
POST-MONEY VALUATION:   ${post_money_cap_usd:,.2f}
DISCOUNT RATE:          {discount_pct:.1f}%
GOVERNANCE RIGHTS:      NONE (PURE ECONOMIC RIGHTS)
SYNC INTERACTION CLAUSE:STRICTLY ASYNCHRONOUS (ZERO-CALL INVARIANT)
================================================================================
This SAFE is entered into as an irrevocable, non-negotiable electronic contract.
Execution occurs upon cryptographic receipt and capital settlement.
================================================================================
"""
        contract_bytes = contract_template.strip().encode("utf-8")
        contract_hash = hashlib.sha256(contract_bytes).hexdigest()
        return contract_hash, contract_template


def run_full_simulation() -> int:
    print("=" * 80)
    print(" C5-REAL ZERO-TOUCH FUNDRAISING KERNEL · PROOF OF CONCEPT (PoC)")
    print("=" * 80)

    # 1. Ingesta de Telemetría Real de la Startup
    telemetry = CompanyTelemetry(
        mrr_usd=45_000.0,           # $540,000 ARR
        churn_monthly_pct=0.8,       # 0.8% Churn mensual (Sobresaliente)
        nrr_annual_pct=128.0,        # 128% Net Revenue Retention
        cac_usd=420.0,
        ltv_usd=4_500.0,             # LTV/CAC > 10.7x
        runway_months=18.0,
        active_users=12_400,
    )

    score, recommended_cap, verdict = TelemetryScoringKernel.evaluate_telemetry(telemetry)
    print(f"[*] Telemetría Auditada:")
    print(f"    - ARR Actual:           ${telemetry.arr_usd:,.2f}")
    print(f"    - Churn Mensual:        {telemetry.churn_monthly_pct}%")
    print(f"    - NRR Anual:            {telemetry.nrr_annual_pct}%")
    print(f"    - Ratio LTV/CAC:        {telemetry.ltv_cac_ratio:.2f}x")
    print(f"[*] Scoring de Silicio:     {score:.1f} / 100.0 -> {verdict}")
    print(f"[*] Valuation Cap Fijado:   ${recommended_cap:,.2f}")
    print("-" * 80)

    # 2. Configuración de Términos de Ronda
    terms = RoundTerms(
        target_raise_usd=1_000_000.0,
        post_money_cap_usd=recommended_cap,
        discount_rate_pct=0.0,
        min_ticket_usd=50_000.0,
        treasury_multisig="0xSafeBabylon60ZeroTouchTreasury8888",
        wire_routing_code="SWIFT-BABYLON-L1-SINK",
    )

    # 3. Casos de Inversores Inbound Evaluados por el Gate
    test_cases: List[InvestorInquiry] = [
        InvestorInquiry(
            inquiry_id="INQ-001-TIER1-VC-CALL",
            entity_name="Legacy Sequoia Clone Capital",
            proposed_ticket_usd=500_000.0,
            requires_sync_call=True,  # EXIGE ZOOM / REUNIÓN
            demands_board_seat=False,
            demands_custom_terms=False,
            accepts_standard_safe=True,
            kyc_accredited_verified=True,
            contact_email="partner@legacyvc.com",
        ),
        InvestorInquiry(
            inquiry_id="INQ-002-GREEDY-ANGEL",
            entity_name="Predatory Micro Fund",
            proposed_ticket_usd=100_000.0,
            requires_sync_call=False,
            demands_board_seat=True,  # EXIGE ASIENTO DE CONSEJO
            demands_custom_terms=False,
            accepts_standard_safe=False,
            kyc_accredited_verified=True,
            contact_email="board@microfund.com",
        ),
        InvestorInquiry(
            inquiry_id="INQ-003-QUANT-VC-SOVEREIGN",
            entity_name="Correlation Signals Algorithmic LP",
            proposed_ticket_usd=250_000.0,
            requires_sync_call=False,  # CERO LLAMADAS
            demands_board_seat=False,  # CERO INTRUSIÓN
            demands_custom_terms=False, # SAFE ESTÁNDAR
            accepts_standard_safe=True,
            kyc_accredited_verified=True,
            contact_email="allocations@correlationsignals.xyz",
        ),
        InvestorInquiry(
            inquiry_id="INQ-004-RUV-ANGEL-SYNDICATE",
            entity_name="Sovereign Tech Syndicate (AngelList RUV)",
            proposed_ticket_usd=150_000.0,
            requires_sync_call=False,
            demands_board_seat=False,
            demands_custom_terms=False,
            accepts_standard_safe=True,
            kyc_accredited_verified=True,
            contact_email="syndicate@angellist-ruv.com",
        ),
    ]

    total_raised = 0.0
    accepted_count = 0
    rejected_count = 0

    print("[*] Evaluando Inbound Pipeline con Anti-Anergy Gate:\n")
    for inq in test_cases:
        decision = AntiAnergyInboundGate.audit_inquiry(inq, terms)
        if decision.status == "ACCEPTED":
            accepted_count += 1
            total_raised += decision.allocated_ticket_usd
            print(f"  [✓] ADMITIDO: {inq.entity_name} ({inq.inquiry_id})")
            print(f"      - Ticket Aprobado: ${decision.allocated_ticket_usd:,.2f}")
            print(f"      - Hash SAFE SHA-256: {decision.safe_contract_hash}")
            print(f"      - Settlement: {decision.dispatch_instructions['usdc_settlement_address']}")
        else:
            rejected_count += 1
            print(f"  [✗] RECHAZADO: {inq.entity_name} ({inq.inquiry_id})")
            print(f"      - Motivo: {decision.reason_code}")
            print(f"      - Causa: {decision.rejection_details}")
        print()

    print("=" * 80)
    print(" RESUMEN DE EJECUCIÓN ZERO-TOUCH")
    print("=" * 80)
    print(f" Total Inquiries Evaluados:   {len(test_cases)}")
    print(f" Inversores Rechazados (Purga Anergía): {rejected_count}")
    print(f" Inversores Admitidos (Silicio Puro):   {accepted_count}")
    print(f" Capital Levantado Total:     ${total_raised:,.2f} / ${terms.target_raise_usd:,.2f}")
    print(f" Contacto Humano Empleado:     0 segundos (0 llamadas / 0 reuniones)")
    print(f" Estado de Ejecución:          CLIE_SETTLEMENT_NOMINAL")
    print("=" * 80)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Zero-Touch Fundraising PoC Engine")
    parser.add_argument("--demo", action="store_true", help="Ejecutar simulación completa de fundraising")
    parser.add_argument("--test", action="store_true", help="Ejecutar validación de aserciones de invariantes")
    args = parser.parse_args()

    if args.test:
        # Validación de aserciones deterministas
        t = CompanyTelemetry(50000, 0.5, 130.0, 300, 3500, 24, 10000)
        score, cap, _ = TelemetryScoringKernel.evaluate_telemetry(t)
        assert score >= 80.0, "Fallo en scoring prime"
        assert cap == 600000.0 * 25.0, "Fallo en cómputo de cap"

        terms = RoundTerms(500000, cap, 0.0, 50000, "0xSafe", "SWIFT")
        bad_inq = InvestorInquiry("1", "Bad VC", 100000, True, False, False, True, True, "a@b.com")
        res = AntiAnergyInboundGate.audit_inquiry(bad_inq, terms)
        assert res.status == "REJECTED" and res.reason_code == "ERR_ANERGY_SYNC_CALL_ATTEMPT"
        print("[✓] Todas las aserciones de invariantes superadas con éxito.")
        return 0

    return run_full_simulation()


if __name__ == "__main__":
    sys.exit(main())
