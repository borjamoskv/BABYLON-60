#!/usr/bin/env python3
# C5-REAL EXERGY CERTIFIED - INDIVIDUAL CREATOR DOSSIER GENERATOR (UNO POR UNO)
import json

def build_individual_dossiers():
    with open("output/subscriber_analysis.json", "r", encoding="utf-8") as f:
        subscribers = json.load(f)

    raw_input = """ericponce@gmail.com,wallstreetwolverine@gmail.com,lorddraugr@gmail.com,nategentile@gmail.com,tiparracosa@gmail.com,auronplay@gmail.com,elxokas@gmail.com,triline@gmail.com,zellendust@gmail.com,elmillor@gmail.com,leyendasyvideojuegos@gmail.com,cdeciencia@gmail.com,quantumfracture@gmail.com,tervlogs@gmail.com,outlasinfo@gmail.com,karchez@gmail.com,carolacontacto@gmail.com,rebornlive@gmail.com,contactobiyin@gmail.com,ampeterby7@gmail.com,vicenscontacto@gmail.com,djmariio@gmail.com,spursito@gmail.com,werlyb@gmail.com,knekro@gmail.com,srcheeto@gmail.com,willyrex@gmail.com,vegetta777contacto@gmail.com,luzuvlogs@gmail.com,alexby11@gmail.com,mangelrogel@gmail.com,drossrotzankyt@gmail.com,visualpolitik@gmail.com,byviruzzcontacto@gmail.com,gona89@gmail.com,contactoluh@gmail.com,sarastech@gmail.com,dotcsv@gmail.com,fedelobo@gmail.com,javieralatorre@gmail.com,alanxelmundoinfo@gmail.com,luisitocomunica@gmail.com,clavero@gmail.com,portilloyt@gmail.com,chutyyt@gmail.com,forcecontacto@gmail.com,bnetcontacto@gmail.com,gazircontacto@gmail.com,sarasocas@gmail.com,skoneyt@gmail.com,arkano@gmail.com,kiddkeo@gmail.com,contactorelsb@gmail.com,contactomorad@gmail.com,trueno@gmail.com,woscontacto@gmail.com,demente@gmail.com,pedritoviral@gmail.com,angelysaras@gmail.com,frigoadri@gmail.com,macundra@gmail.com,outconsumer@gmail.com,chincheto77@gmail.com,tonacho@gmail.com,saritacontacto@gmail.com,exicontacto@gmail.com,andresnavy@gmail.com,memoaponte@gmail.com,caelike@gmail.com,werevertumorrocontacto@gmail.com,contactoyuya@gmail.com,spreen@gmail.com,elmariana@gmail.com,robleiscontacto@gmail.com,contactocoscu@gmail.com,missasinfonia@gmail.com,fedevigevani@gmail.com,pedritosola@gmail.com,ladivaza@gmail.com,keniaoscontacto@gmail.com,kimberlyloaiza@gmail.com,jdpantoja@gmail.com,domelipa@gmail.com,iamferv@gmail.com,polinesios@gmail.com,karenpolinesia@gmail.com,lessliepolinesia@gmail.com,gibbybusiness@gmail.com,labala@gmail.com,antrax@gmail.com,thedonato@gmail.com,yoloaventuras@gmail.com,nandocontacto@gmail.com,marianaavila@gmail.com,pandacontacto@gmail.com,cracks@gmail.com,campeones@gmail.com,lamediainglesa@gmail.com,misterchip@gmail.com,davooxeneize@gmail.com,lacobra@gmail.com,losfutbolitos@gmail.com,papigavi@gmail.com,perxitaa@gmail.com,contactovioleta@gmail.com,contactoabby@gmail.com,contactoparacetamor@gmail.com,gemita@gmail.com,mayichi@gmail.com,riverscontacto@gmail.com,juanguarnizo@gmail.com,arigameplays@gmail.com,amablitz@gmail.com,contactodedreviil@gmail.com,contactoaldogeo@gmail.com,roierinfo@gmail.com,quackity@gmail.com,germancontacto@gmail.com,fernanfloo@gmail.com,rincongiorgio@gmail.com,luisitorey@gmail.com,wereverwerocontacto@gmail.com,escorpiondorado@gmail.com,alexmontiel@gmail.com,platicapolinesia@gmail.com,expcaseros@gmail.com,maydenexpcaseros@gmail.com,nataliaexpcaseros@gmail.com,aczino@gmail.com,rapder@gmail.com,loboestepario@gmail.com,rcfreestyle@gmail.com,jonybeltran@gmail.com,skiper@gmail.com,garzafreestyle@gmail.com,lancerliricaloficial@gmail.com,letrafreestyle@gmail.com,mnakyt@gmail.com,sweetpainyt@gmail.com,zaskomaster@gmail.com,bloncontacto@gmail.com,tirpayt@gmail.com,mregoyt@gmail.com,elekipo@gmail.com,hander@gmail.com,jadoyt@gmail.com,khancontacto@gmail.com,btacontacto@gmail.com,errece@gmail.com,stuartfreestyle@gmail.com,mechafreestyle@gmail.com,larrixfreestyle@gmail.com,mpeljuvenil@gmail.com,wolffreestyle@gmail.com,zainafreestyle@gmail.com,naistafreestyle@gmail.com,cachafreestyle@gmail.com,nitrofreestyle@gmail.com,acertijofreestyle@gmail.com,tomcrowley@gmail.com,jokkerfreestyle@gmail.com,chynonyno@gmail.com,vallest@gmail.com,marithea@gmail.com,lokillo@gmail.com,carpediemfreestyle@gmail.com,filosofo@gmail.com,nekroos@gmail.com,contactojaze@gmail.com,strikefreestyle@gmail.com,stickfreestyle@gmail.com,vijaykesh@gmail.com,pieropistas@gmail.com,lobolopez@gmail.com,jordicruz@gmail.com,bertabernad@gmail.com,gigivives@gmail.com,arethafuste@gmail.com,martacarriedo@gmail.com,madamederosa@gmail.com,dulceida@gmail.com,mariapombo@gmail.com,martapombo@gmail.com,gracevillarreal@gmail.com,paulagonu@gmail.com,giselacontacto@gmail.com,martariumbau@gmail.com,andreacompton@gmail.com,ineshernand@gmail.com,percebesygrelos@gmail.com,livingpostureo@gmail.com,lalachus@gmail.com,henaralvarez@gmail.com,jedetoficial@gmail.com"""

    target_emails = [e.strip().lower() for e in raw_input.split(",") if e.strip()]
    sub_map = {item.get("email", "").lower(): item for item in subscribers}

    dossiers = []
    for idx, email in enumerate(target_emails, 1):
        info = sub_map.get(email, {})
        name = info.get("name") or email.split("@")[0].capitalize()
        cls = info.get("classification", "General / Other")
        sub_type = info.get("type", "Free")
        engagement = info.get("engagement_score", 0)
        country = info.get("country", "ES")
        source = info.get("source_free", "import")

        # Categorización fina
        if any(k in email for k in ["freestyle", "rap", "chuty", "aczino", "wos", "skone", "gazir", "bnet", "arkano"]):
            cohort = "Urban & Freestyle Battle"
            perks = "Contenido tras las cámaras, audios sin editar, letras exclusivas"
        elif any(k in email for k in ["tech", "csv", "quantum", "ciencia", "gentile"]):
            cohort = "Tech & Divulgación Científica"
            perks = "Archivos PDF descargables, guías de código, análisis de IA"
        elif any(k in email for k in ["pombo", "dulceida", "gonu", "villarreal", "riumbau", "hernand", "postureo", "vives"]):
            cohort = "Lifestyle & Culture"
            perks = "Descuentos exclusivos, recomendaciones de marca, contenido personal"
        else:
            cohort = "Gaming & Streaming Entertainment"
            perks = "Acceso a Substack Chat, comunidad privada de Discord, eventos en vivo"

        dossier = {
            "id": idx,
            "name": name,
            "email": email,
            "classification": cls,
            "type": sub_type,
            "engagement_score": engagement,
            "country": country,
            "source": source,
            "cohort": cohort,
            "recommended_perks": perks
        }
        dossiers.append(dossier)

    # Export Markdown Dossier
    md_path = "output/dossier_creadores_uno_por_uno.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# DOSSIER DE INTELIGENCIA: ANÁLISIS UNO POR UNO DE 194 CREADORES\n")
        f.write("## Evaluación Individualizada de Perfil, Cohorte y Estrategia Substack 2026\n\n")
        f.write("---\n\n")

        for d in dossiers:
            f.write(f"### #{d['id']}. {d['name']} (`{d['email']}`)\n")
            f.write(f"- **Cohorte:** {d['cohort']}\n")
            f.write(f"- **Categoría:** {d['classification']}\n")
            f.write(f"- **Tipo de Suscripción:** {d['type']}\n")
            f.write(f"- **Puntuación de Engagement:** {d['engagement_score']}/10\n")
            f.write(f"- **País:** {d['country']} | **Fuente:** {d['source']}\n")
            f.write(f"- **Estrategia Recomendada de Pago:** {d['recommended_perks']}\n\n")
            f.write("---\n\n")

    print(f"Generated Markdown dossier: {md_path} ({len(dossiers)} entries)")

    # Export HTML Interactive Dossier
    html_path = "output/dossier_creadores_uno_por_uno.html"
    html_content = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Dossier Creadores Uno por Uno - Substack OSINT</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; background: #0d1117; color: #c9d1d9; padding: 30px; margin: 0; }
        .container { max-width: 1000px; margin: 0 auto; }
        h1 { color: #58a6ff; border-bottom: 2px solid #30363d; padding-bottom: 10px; }
        .search-box { width: 100%; padding: 12px; font-size: 1rem; border-radius: 6px; border: 1px solid #30363d; background: #161b22; color: #fff; margin-bottom: 25px; box-sizing: border-box; }
        .card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; margin-bottom: 15px; }
        .card-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #21262d; padding-bottom: 10px; margin-bottom: 10px; }
        .card-title { font-size: 1.2rem; font-weight: 700; color: #ffffff; }
        .badge { background: #238636; color: #fff; padding: 3px 8px; border-radius: 12px; font-size: 0.8rem; font-weight: 600; }
        .meta { font-size: 0.9rem; color: #8b949e; margin-bottom: 8px; }
        .strategy { background: rgba(56, 139, 253, 0.15); border-left: 3px solid #58a6ff; padding: 10px 15px; border-radius: 0 4px 4px 0; font-size: 0.9rem; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>DOSSIER DE CREADORES EN SUBSTACK (194 ANÁLISIS UNO POR UNO)</h1>
        <input type="text" id="searchInput" class="search-box" placeholder="Buscar por nombre, email o cohorte..." onkeyup="filterCards()">
        <div id="cardsContainer">
"""
    for d in dossiers:
        html_content += f"""
            <div class="card" data-search="{d['name'].lower()} {d['email'].lower()} {d['cohort'].lower()} {d['classification'].lower()}">
                <div class="card-header">
                    <span class="card-title">#{d['id']}. {d['name']}</span>
                    <span class="badge">{d['cohort']}</span>
                </div>
                <div class="meta"><strong>Email:</strong> {d['email']} | <strong>Tipo:</strong> {d['type']} | <strong>País:</strong> {d['country']}</div>
                <div class="meta"><strong>Categoría:</strong> {d['classification']} | <strong>Engagement:</strong> {d['engagement_score']}/10</div>
                <div class="strategy">💡 <strong>Beneficio de Pago Recomendado:</strong> {d['recommended_perks']}</div>
            </div>
"""

    html_content += """
        </div>
    </div>
    <script>
        function filterCards() {
            var input = document.getElementById('searchInput').value.toLowerCase();
            var cards = document.getElementsByClassName('card');
            for (var i = 0; i < cards.length; i++) {
                var searchData = cards[i].getAttribute('data-search');
                if (searchData.indexOf(input) > -1) {
                    cards[i].style.display = "";
                } else {
                    cards[i].style.display = "none";
                }
            }
        }
    </script>
</body>
</html>
"""
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Generated HTML interactive dossier: {html_path}")

if __name__ == "__main__":
    build_individual_dossiers()
