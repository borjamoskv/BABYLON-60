// C5-REAL EXERGY CERTIFIED
// Lista de subdominios mafia inyectada
const mafiaDomains = ["spacioia", "overxtime", "emprender", "laiaqueimporta", "plumapifiada", "marcplanella", "webreactiva", "manoletux", "emprendizajes", "escribepro", "botondeayuda", "titonet", "podhacks", "estrategiabyaleph", "daviddominguez", "enriquemartinezbermejo", "platforms", "futuria", "medicosinconformistas", "tucoachpersonal", "raulcalderonc", "seveluna", "modoxtenx", "iaparatodo", "masteryweeks", "emarketersocial", "davidlahozmartin", "ekhocomunicacion", "ecommletter", "eponte", "conectaycrece", "destacadas", "coachingdeproducto", "crecerensubstack", "consultoresia", "hazloquequieras", "iaenespanol", "thefoundercorner", "susanaluque", "estomeinteresa", "agentesia", "unicorniosypiratas", "innerhythm", "somosbiz", "cosasdefreelance", "thevccorner", "dnogalesexperience", "jorgebosch", "hellojaume", "bookstrapping", "tudosisia", "sietediaspodcast", "vitalismo", "todatabeyond", "habitonutricion", "cafeconia", "aimafia", "aplicacionesai", "samueldominguez", "sumapositiva", "nosolosuerte", "dispersosdemierda"];

function log(msg, isErr = false) {
    const con = document.getElementById("console");
    const p = document.createElement("div");
    p.innerText = `> ${msg}`;
    p.style.color = isErr ? "#f87171" : "#34d399";
    con.appendChild(p);
    con.scrollTop = con.scrollHeight;
}

document.getElementById("purge-btn").addEventListener("click", async () => {
    const btn = document.getElementById("purge-btn");
    btn.disabled = true;
    btn.innerText = "Purgando...";

    log("Obteniendo pestaña activa...");
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab || !tab.url) {
        log("Error: No se pudo obtener la pestaña activa", true);
        btn.disabled = false;
        btn.innerText = "Purgar Recomendaciones";
        return;
    }

    const urlObj = new URL(tab.url);
    if (!urlObj.hostname.endsWith("substack.com")) {
        log("Error: Debes estar en un dominio de Substack", true);
        btn.disabled = false;
        btn.innerText = "Purgar Recomendaciones";
        return;
    }

    log(`Inyectando purga en ${urlObj.hostname}...`);

    try {
        await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            func: async (mafiaList) => {
                console.log("[Sentinel] Iniciando purga en pestaña...");
                try {
                    const res = await fetch("/api/v1/recommendations");
                    if (!res.ok) return { success: false, error: "HTTP " + res.status };

                    const recs = await res.json();
                    const targets = recs.filter(r => mafiaList.includes(r.target_publication.subdomain));

                    if (targets.length === 0) {
                        return { success: true, count: 0 };
                    }

                    let deleted = 0;
                    for (const item of targets) {
                        const dres = await fetch(`/api/v1/recommendations/${item.id}`, { method: "DELETE" });
                        if (dres.ok) deleted++;
                    }
                    return { success: true, count: deleted };
                } catch (e) {
                    return { success: false, error: e.message };
                }
            },
            args: [mafiaDomains]
        }, (results) => {
            if (!results || !results[0] || !results[0].result) {
                log("Error: No se pudo ejecutar el script", true);
                btn.disabled = false;
                btn.innerText = "Purgar Recomendaciones";
                return;
            }

            const data = results[0].result;
            if (data.success) {
                log(`Purga completada. Nodos eliminados: ${data.count}`);
            } else {
                log(`Error de ejecución: ${data.error}`, true);
            }

            btn.disabled = false;
            btn.innerText = "Purgar Recomendaciones";
        });
    } catch (e) {
        log(`Fallo al inyectar script: ${e.message}`, true);
        btn.disabled = false;
        btn.innerText = "Purgar Recomendaciones";
    }
});
