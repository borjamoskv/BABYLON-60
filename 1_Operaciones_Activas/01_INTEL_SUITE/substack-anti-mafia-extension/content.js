// C5-REAL EXERGY CERTIFIED
// Lista de subdominios mafia inyectada
const mafiaDomains = ["spacioia", "overxtime", "emprender", "laiaqueimporta", "plumapifiada", "marcplanella", "webreactiva", "manoletux", "emprendizajes", "escribepro", "botondeayuda", "titonet", "podhacks", "estrategiabyaleph", "daviddominguez", "enriquemartinezbermejo", "platforms", "futuria", "medicosinconformistas", "tucoachpersonal", "raulcalderonc", "seveluna", "modoxtenx", "iaparatodo", "masteryweeks", "emarketersocial", "davidlahozmartin", "ekhocomunicacion", "ecommletter", "eponte", "conectaycrece", "destacadas", "coachingdeproducto", "crecerensubstack", "consultoresia", "hazloquequieras", "iaenespanol", "thefoundercorner", "susanaluque", "estomeinteresa", "agentesia", "unicorniosypiratas", "innerhythm", "somosbiz", "cosasdefreelance", "thevccorner", "dnogalesexperience", "jorgebosch", "hellojaume", "bookstrapping", "tudosisia", "sietediaspodcast", "vitalismo", "todatabeyond", "habitonutricion", "cafeconia", "aimafia", "aplicacionesai", "samueldominguez", "sumapositiva", "nosolosuerte", "dispersosdemierda"];

(function() {
    const host = window.location.hostname;
    const sub = host.split(".")[0];

    if (mafiaDomains.includes(sub)) {
        console.log(`[Sentinel] Alerta: Nodo Substack Mafia detectado (${sub})`);

        const banner = document.createElement("div");
        banner.style.position = "fixed";
        banner.style.bottom = "10px";
        banner.style.left = "10px";
        banner.style.backgroundColor = "#07070b";
        banner.style.color = "#ff5600";
        banner.style.border = "2px solid #ff5600";
        banner.style.padding = "8px 12px";
        banner.style.borderRadius = "8px";
        banner.style.fontFamily = "sans-serif";
        banner.style.fontSize = "0.75rem";
        banner.style.fontWeight = "bold";
        banner.style.zIndex = "999999";
        banner.style.boxShadow = "0 4px 15px rgba(255, 86, 0, 0.3)";
        banner.innerHTML = "⚠️ ALERTA OSINT: Miembro del Cluster Substack Mafia (#C4-SIM)";

        document.body.appendChild(banner);
    }
})();
