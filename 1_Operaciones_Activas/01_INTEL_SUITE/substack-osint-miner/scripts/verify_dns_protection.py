#!/usr/bin/env python3
# C5-REAL EXERGY CERTIFIED - DOMAIN PROTECTION & DNS AUDIT SCRIPT
import sys
import dns.resolver

def audit_domain(domain="babylon60.com"):
    print(f"==================================================")
    print(f" 🛡️  AUDITORÍA DE PROTECCIÓN DNS: {domain}")
    print(f"==================================================")

    # 1. MX
    print("\n1. REGISTROS MX (Recepción):")
    try:
        mx = dns.resolver.resolve(domain, "MX")
        for r in mx:
            print(f"   🟢 MX: {r.exchange} (Pref: {r.preference})")
    except Exception as e:
        print(f"   🔴 ERROR MX: {e}")

    # 2. SPF
    print("\n2. REGISTRO SPF (Autenticación Remitente):")
    try:
        txt = dns.resolver.resolve(domain, "TXT")
        spf_found = False
        for r in txt:
            val = r.to_text()
            if "v=spf1" in val:
                spf_found = True
                if "include:substack.com" in val or "include:_spf.google.com" in val:
                    print(f"   🟢 SPF VÁLIDO: {val}")
                else:
                    print(f"   🟡 SPF PARCIAL (Falta incluir Substack/Google): {val}")
        if not spf_found:
            print("   🔴 FALTANTE: No existe registro SPF.")
    except Exception as e:
        print(f"   🔴 ERROR SPF: {e}")

    # 3. DMARC
    print("\n3. REGISTRO DMARC (Protección Anti-Spoofing & Gmail/Yahoo Compliance):")
    try:
        dmarc = dns.resolver.resolve(f"_dmarc.{domain}", "TXT")
        for r in dmarc:
            print(f"   🟢 DMARC ACTIVO: {r.to_text()}")
    except Exception as e:
        print(f"   🔴 FALTANTE (CRÍTICO): No existe registro _dmarc.{domain}")
        print("      👉 Debe crearse un TXT en _dmarc con valor: v=DMARC1; p=none; rua=mailto:borja@babylon60.com;")

    # 4. DKIM
    print("\n4. REGISTROS DKIM (Firma Criptográfica):")
    selectors = ["google", "s1", "s2", "sub1", "sub2", "st", "default", "mail", "k1", "substack"]
    dkim_count = 0
    for sel in selectors:
        try:
            dk = dns.resolver.resolve(f"{sel}._domainkey.{domain}", "TXT")
            print(f"   🟢 DKIM ({sel}): {dk[0].to_text()[:60]}...")
            dkim_count += 1
        except Exception:
            pass
    if dkim_count == 0:
        print("   🟡 DKIM: No detectado en selectores estándar (Verificar CNAMEs de Substack).")

    print("\n==================================================")

if __name__ == "__main__":
    dom = sys.argv[1] if len(sys.argv) > 1 else "babylon60.com"
    audit_domain(dom)
