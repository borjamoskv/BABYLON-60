#!/usr/bin/env python3
import json

def onif_rule_engine(evidence_profile):
    """
    Motor de Decisión Fiscal AEAT/ONIF (C5-REAL).
    Hipótesis Central Única: Prestación de servicios digitales encubierta bajo canal de mecenazgo indirecto.
    """
    
    # 1. Trazabilidad Directa (La variable crítica absoluta)
    has_explicit_condition = evidence_profile.get("prueba_condicional_explicita", False)
    has_implicit_condition = evidence_profile.get("prueba_condicional_implicita", False)
    
    # 2. Cruce Informático / Económico
    is_price_equivalent = evidence_profile.get("equivalencia_economica_exacta", False)
    platform_bypassed = evidence_profile.get("uso_cupones_100_por_ciento", False)

    report = {
        "hipotesis_central": "Posible prestación de servicios digitales encubierta bajo canal de mecenazgo indirecto.",
        "estado_expediente": "",
        "probabilidad_requerimiento_porcentaje": 0,
        "fundamentos_habilitados": [],
        "accion_recomendada": ""
    }

    # Árbol de decisión fiscal (If/Else)
    if has_explicit_condition:
        report["estado_expediente"] = "ALTA PRIORIDAD - INDICIOS DE RELEVANCIA PROBATORIA PRIMARIA"
        report["probabilidad_requerimiento_porcentaje"] = 95
        report["fundamentos_habilitados"].append("Art. 13 LGT (Calificación por naturaleza real: prestación onerosa)")
        report["accion_recomendada"] = "Emitir Requerimiento Art. 93 LGT a Fundación intermediaria y Plataforma digital (cruce de logs)."
        
        if is_price_equivalent and platform_bypassed:
            report["fundamentos_habilitados"].append("Art. 16 LGT (Posible Simulación)")
            
    elif has_implicit_condition:
        report["estado_expediente"] = "PRIORIDAD MEDIA - ELEMENTO APTO PARA CRUCE INFORMÁTICO"
        report["probabilidad_requerimiento_porcentaje"] = 60
        report["fundamentos_habilitados"].append("Art. 13 LGT (En fase de verificación de indicios)")
        report["accion_recomendada"] = "Solicitar cruce automático preliminar de NIFs entre donantes declarados y altas en servicio."
        
    else:
        report["estado_expediente"] = "BAJA PRIORIDAD - ARCHIVO (SIN NEXO CAUSAL MATERIAL)"
        report["probabilidad_requerimiento_porcentaje"] = 5
        report["fundamentos_habilitados"].append("Ley 49/2002 (Se mantiene presunción de mecenazgo puro y simple)")
        report["accion_recomendada"] = "Archivo del expediente por ausencia de condicionalidad verificable."

    return report

if __name__ == "__main__":
    print("=== ONIF RULE ENGINE: SIMULACIÓN DE EXPEDIENTE ===\n")
    
    print("CASO A: Evidencia Explícita Documentada (El pantallazo del email)")
    caso_a = {
        "prueba_condicional_explicita": True,
        "prueba_condicional_implicita": True,
        "equivalencia_economica_exacta": True,
        "uso_cupones_100_por_ciento": True
    }
    print(json.dumps(onif_rule_engine(caso_a), indent=2, ensure_ascii=False))
    print("\n--------------------------------------------------\n")
    
    print("CASO B: Evidencia Implícita (Solo correlación estadística)")
    caso_b = {
        "prueba_condicional_explicita": False,
        "prueba_condicional_implicita": True,
        "equivalencia_economica_exacta": True,
        "uso_cupones_100_por_ciento": False
    }
    print(json.dumps(onif_rule_engine(caso_b), indent=2, ensure_ascii=False))
    print("\n--------------------------------------------------\n")
    
    print("CASO C: Ergodicidad Real (Sin correlación verificable)")
    caso_c = {
        "prueba_condicional_explicita": False,
        "prueba_condicional_implicita": False,
        "equivalencia_economica_exacta": False,
        "uso_cupones_100_por_ciento": False
    }
    print(json.dumps(onif_rule_engine(caso_c), indent=2, ensure_ascii=False))
