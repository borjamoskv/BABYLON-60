# 300 Primitivas de Oncologia Molecular
### Ontologia CORTEX / BABYLON-60 -- bloques fundamentales que la investigacion del cancer estudia y ataca

*Generado 2026-07-14 | 300 primitivas | escala de confianza C5-established | fuente unica: `scripts/gen_oncology_primitives.py`*

> **AVISO IMPORTANTE.** AVISO. Esto es una ONTOLOGIA DE CONOCIMIENTO de biologia molecular del cancer y de sus dianas terapeuticas: los bloques fundamentales que la investigacion oncologica estudia y ataca. NO es una cura, NO es un protocolo de tratamiento y NO es consejo medico. Ninguna primitiva individual ni el conjunto 'curan el cancer'. El cancer no es una sola enfermedad sino mas de 200 enfermedades distintas; el diagnostico y el tratamiento son clinicos, individualizados y competencia de oncologos e investigadores. Cualquier decision medica debe tomarse con profesionales sanitarios.

> *NOTICE.* NOTICE. This is a KNOWLEDGE ONTOLOGY of cancer molecular biology and its therapeutic targets. It is NOT a cure, NOT a treatment protocol and NOT medical advice. No single primitive nor the whole set 'cures cancer'. Cancer is 200+ distinct diseases; diagnosis and treatment are clinical and individualized. Consult qualified healthcare professionals.

Autoria artistica/arquitectonica del sustrato (AKA): **Borja Moskv** (`borjamoskv`).

---

## Indice de categorias

| # | Categoria | Capa | Primitivas |
| :--- | :--- | :--- | :---: |
| 1 | [Hallmarks del cancer](#hallmarks-del-cancer) | meta | 16 |
| 2 | [Oncogenes](#oncogenes) | molecular | 30 |
| 3 | [Genes supresores de tumores](#genes-supresores-de-tumores) | molecular | 24 |
| 4 | [Vias de senalizacion](#vias-de-senalizacion) | pathway | 18 |
| 5 | [Ciclo celular y checkpoints](#ciclo-celular-y-checkpoints) | cellular | 13 |
| 6 | [Apoptosis y muerte celular regulada](#apoptosis-y-muerte-celular-regulada) | cellular | 22 |
| 7 | [Respuesta al dano y reparacion de ADN](#respuesta-al-dano-y-reparacion-de-adn) | molecular | 18 |
| 8 | [Inestabilidad genomica y mutagenesis](#inestabilidad-genomica-y-mutagenesis) | molecular | 12 |
| 9 | [Telomeros, senescencia e inmortalidad](#telomeros-senescencia-e-inmortalidad) | cellular | 8 |
| 10 | [Angiogenesis](#angiogenesis) | cellular | 10 |
| 11 | [Invasion, EMT y metastasis](#invasion-emt-y-metastasis) | cellular | 18 |
| 12 | [Metabolismo tumoral](#metabolismo-tumoral) | molecular | 16 |
| 13 | [Epigenetica y cromatina](#epigenetica-y-cromatina) | molecular | 15 |
| 14 | [Microambiente tumoral (TME)](#microambiente-tumoral-tme) | tissue | 13 |
| 15 | [Inmuno-oncologia y evasion inmune](#inmuno-oncologia-y-evasion-inmune) | tissue | 22 |
| 16 | [Modalidades terapeuticas](#modalidades-terapeuticas) | therapy | 18 |
| 17 | [Primitivas farmaco -> diana](#primitivas-farmaco-->-diana) | therapy | 27 |
| | **TOTAL** | | **300** |

---

## Hallmarks del cancer
<a id="hallmarks-del-cancer"></a>
*Capa: meta | 16 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ONC-001` | **Sustaining proliferative signaling** | proceso | Las celulas tumorales generan y sostienen senales mitogenicas de forma autonoma (p.ej. via RTK/RAS). | Objetivo de inhibidores de RTK y de la via MAPK. | Hanahan & Weinberg, Cell 2011 |
| `ONC-002` | **Evading growth suppressors** | proceso | Elusion de frenos antiproliferativos como RB y TP53. | Restaurar checkpoints; inhibidores CDK4/6; reactivadores de p53. | Hanahan & Weinberg, Cell 2011 |
| `ONC-003` | **Resisting cell death** | proceso | Bloqueo de apoptosis por sobreexpresion de anti-apoptoticos o perdida de sensores. | Mimeticos BH3 (venetoclax) restauran la muerte. | Hanahan & Weinberg, Cell 2011 |
| `ONC-004` | **Enabling replicative immortality** | proceso | Mantenimiento telomerico (telomerasa/ALT) que evita la senescencia replicativa. | Inhibicion de telomerasa (investigacion). | Hanahan & Weinberg, Cell 2011 |
| `ONC-005` | **Inducing angiogenesis** | proceso | Activacion del switch angiogenico para vascularizar el tumor. | Anti-VEGF (bevacizumab), TKI antiangiogenicos. | Hanahan & Weinberg, Cell 2011 |
| `ONC-006` | **Activating invasion and metastasis** | proceso | Adquisicion de motilidad, invasion local y diseminacion a distancia. | Diana de terapias sobre EMT y microambiente. | Hanahan & Weinberg, Cell 2011 |
| `ONC-007` | **Deregulating cellular energetics** | proceso | Reprogramacion metabolica (efecto Warburg) para soportar proliferacion. | Inhibidores metabolicos (IDH mutante, glutaminasa). | Hanahan & Weinberg, Cell 2011 |
| `ONC-008` | **Avoiding immune destruction** | proceso | Escape del reconocimiento y eliminacion por el sistema inmune. | Bloqueo de checkpoints (anti-PD-1/PD-L1/CTLA-4). | Hanahan & Weinberg, Cell 2011 |
| `ONC-009` | **Genome instability and mutation** | proceso | Caracteristica facilitadora: tasa mutacional elevada que genera diversidad clonal. | Explotable por sintesis letal (PARPi en HRD). | Hanahan & Weinberg, Cell 2011 |
| `ONC-010` | **Tumor-promoting inflammation** | proceso | Caracteristica facilitadora: inflamacion que aporta factores pro-tumorales. | Objetivo de estrategias anti-inflamatorias. | Hanahan & Weinberg, Cell 2011 |
| `ONC-011` | **Unlocking phenotypic plasticity** | proceso | Nuevo hallmark 2022: desdiferenciacion/transdiferenciacion que evade el destino celular. | Terapias de diferenciacion; reto en resistencia. | Hanahan, Cancer Discov 2022 (New Dimensions) |
| `ONC-012` | **Nonmutational epigenetic reprogramming** | proceso | Nuevo hallmark 2022: adquisicion de capacidades por cambios epigeneticos sin mutacion. | Farmacos epigeneticos (DNMTi, HDACi, EZH2i). | Hanahan, Cancer Discov 2022 (New Dimensions) |
| `ONC-013` | **Polymorphic microbiomes** | proceso | Nuevo hallmark 2022: microbiota que modula iniciacion, progresion y respuesta terapeutica. | Modulacion del microbioma; impacto en inmunoterapia. | Hanahan, Cancer Discov 2022 (New Dimensions) |
| `ONC-014` | **Senescent cells** | proceso | Nuevo hallmark 2022: celulas senescentes y su SASP modulan capacidades tumorales. | Senoliticos (investigacion). | Hanahan, Cancer Discov 2022 (New Dimensions) |
| `ONC-015` | **Clonal evolution and intratumoral heterogeneity** | proceso | Seleccion darwiniana de subclones que genera heterogeneidad espacial y temporal. | Base de la resistencia; terapias adaptativas. | Nowell, Science 1976; Greaves & Maley, Nature 2012 |
| `ONC-016` | **Two-hit hypothesis (Knudson)** | proceso | Los supresores tumorales suelen requerir inactivacion bialelica para perder funcion. | Marco de riesgo hereditario (RB1, BRCA). | Knudson, PNAS 1971 |

## Oncogenes
<a id="oncogenes"></a>
*Capa: molecular | 30 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ONC-017` | **KRAS** | oncogen | GTPasa RAS; mutaciones (G12/G13/Q61) la fijan activa y disparan MAPK/PI3K. | KRAS G12C: sotorasib, adagrasib. | Prior et al., Cancer Res 2020 |
| `ONC-018` | **HRAS** | oncogen | Isoforma RAS mutada en tumores de cabeza y cuello y vejiga. | Inhibidor de farnesiltransferasa (tipifarnib) en HRAS-mut. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-019` | **NRAS** | oncogen | Isoforma RAS frecuentemente mutada en melanoma y leucemias. | Diana indirecta via MEK; sin inhibidor directo aprobado. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-020` | **BRAF** | oncogen | Cinasa RAF; V600E constitutivamente activa la via MAPK. | Vemurafenib/dabrafenib + inhibidor MEK. | Davies et al., Nature 2002 |
| `ONC-021` | **EGFR** | oncogen | RTK cuya activacion/mutacion (ex19del, L858R) impulsa proliferacion. | TKI de EGFR (gefitinib, osimertinib). | Lynch et al., NEJM 2004 |
| `ONC-022` | **ERBB2 / HER2** | oncogen | RTK amplificado en subtipos de mama y gastrico. | Trastuzumab, pertuzumab, T-DXd. | Slamon et al., Science 1987 |
| `ONC-023` | **MYC** | oncogen | Factor de transcripcion maestro de crecimiento; amplificado/translocado. | Diana 'undruggable'; BET-i indirectos. | Dang, Cell 2012 |
| `ONC-024` | **MYCN** | oncogen | Parologo de MYC amplificado en neuroblastoma de alto riesgo. | Biomarcador pronostico; BET/Aurora-A indirectos. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-025` | **MET** | oncogen | RTK (receptor de HGF); amplificacion o exon 14 skipping activan la via. | Capmatinib, tepotinib, crizotinib. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-026` | **ALK** | oncogen | RTK activada por fusiones (EML4-ALK) en NSCLC. | Crizotinib, alectinib, lorlatinib. | Soda et al., Nature 2007 |
| `ONC-027` | **ROS1** | oncogen | RTK activada por fusiones en un subconjunto de NSCLC. | Crizotinib, entrectinib. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-028` | **RET** | oncogen | RTK activada por fusiones o mutaciones puntuales (MEN2). | Selpercatinib, pralsetinib. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-029` | **FLT3** | oncogen | RTK mutada (ITD/TKD) en leucemia mieloide aguda. | Midostaurina, gilteritinib. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-030` | **KIT** | oncogen | RTK con mutaciones activadoras en GIST y mastocitosis. | Imatinib, avapritinib. | Hirota et al., Science 1998 |
| `ONC-031` | **PDGFRA** | oncogen | RTK relacionada con KIT; mutada en subgrupos de GIST. | Avapritinib (D842V), imatinib. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-032` | **ABL1 (BCR-ABL)** | oncogen | Fusion del cromosoma Filadelfia con tirosina-cinasa constitutiva en LMC. | Imatinib y TKI de siguiente generacion. | Rowley, Nature 1973 |
| `ONC-033` | **JAK2** | oncogen | Cinasa citoplasmatica; V617F impulsa neoplasias mieloproliferativas. | Ruxolitinib (JAK1/2). | James et al., Nature 2005 |
| `ONC-034` | **PIK3CA** | oncogen | Subunidad p110-alfa de PI3K; mutaciones activan PI3K-AKT. | Alpelisib en mama HR+ PIK3CA-mut. | Samuels et al., Science 2004 |
| `ONC-035` | **AKT1** | oncogen | Cinasa central de supervivencia/crecimiento aguas abajo de PI3K. | Inhibidores de AKT (capivasertib). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-036` | **MTOR** | oncogen | Cinasa que integra nutrientes y crecimiento; activacion aberrante en tumores. | Everolimus, temsirolimus. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-037` | **MDM2** | oncogen | E3 ligasa que degrada p53; su amplificacion inactiva p53 sin mutarlo. | Inhibidores MDM2-p53 (investigacion). | Momand et al., Cell 1992 |
| `ONC-038` | **CCND1 (Cyclin D1)** | oncogen | Ciclina que activa CDK4/6 e impulsa la transicion G1/S. | Sensibiliza a inhibidores CDK4/6. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-039` | **CDK4** | oncogen | Cinasa dependiente de ciclina que fosforila RB en G1. | Palbociclib, ribociclib, abemaciclib. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-040` | **CDK6** | oncogen | Parologo de CDK4 en el eje ciclina D-RB. | Inhibidores CDK4/6. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-041` | **BCL2** | oncogen | Proteina anti-apoptotica sobreexpresada (t(14;18)) que bloquea la muerte. | Venetoclax (mimetico BH3). | Tsujimoto et al., Science 1984 |
| `ONC-042` | **EZH2** | oncogen | Metiltransferasa de PRC2 (H3K27me3); mutaciones GOF en linfoma folicular. | Tazemetostat. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-043` | **IDH1** | oncogen | Mutacion neomorfica que produce el oncometabolito 2-HG (glioma, LMA). | Ivosidenib. | Dang et al., Nature 2009 |
| `ONC-044` | **IDH2** | oncogen | Isoforma mitocondrial con mutacion neomorfica productora de 2-HG. | Enasidenib. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-045` | **FGFR1** | oncogen | RTK de la familia FGFR; amplificacion/fusion en varios tumores. | Inhibidores pan-FGFR (erdafitinib, pemigatinib). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-046` | **CTNNB1 (beta-catenina)** | oncogen | Efector de Wnt; mutaciones lo estabilizan y activan transcripcion pro-tumoral. | Diana dificil; via Wnt en investigacion. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |

## Genes supresores de tumores
<a id="genes-supresores-de-tumores"></a>
*Capa: molecular | 24 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ONC-047` | **TP53** | supresor | Guardian del genoma; induce arresto/apoptosis ante estres; mutado en ~50% de tumores. | Reactivadores de p53 mutante (investigacion). | Levine, Cell 1997 |
| `ONC-048` | **RB1** | supresor | Freno del ciclo celular que secuestra E2F; su perdida libera G1/S. | Perdida de RB confiere resistencia a CDK4/6i. | Weinberg, Cell 1995 |
| `ONC-049` | **PTEN** | supresor | Fosfatasa que antagoniza PI3K; su perdida hiperactiva AKT. | Sensibiliza a inhibidores de PI3K/AKT. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-050` | **APC** | supresor | Regulador negativo de beta-catenina; su perdida inicia cancer colorrectal. | Marco de la via Wnt en CCR. | Kinzler & Vogelstein, Cell 1996 |
| `ONC-051` | **VHL** | supresor | E3 ligasa que degrada HIF; su perdida activa pseudohipoxia (renal). | Belzutifan (HIF-2 alfa). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-052` | **BRCA1** | supresor | Reparacion por recombinacion homologa; su perdida causa HRD. | Sintesis letal con inhibidores de PARP. | Miki et al., Science 1994 |
| `ONC-053` | **BRCA2** | supresor | Carga RAD51 en la HR; su perdida sensibiliza a dano de ADN. | Olaparib y otros PARPi. | Wooster et al., Nature 1995 |
| `ONC-054` | **PALB2** | supresor | Puente entre BRCA1 y BRCA2 en la HR; su perdida da fenotipo BRCAness. | PARPi en HRD. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-055` | **NF1** | supresor | GAP que apaga RAS; su perdida sostiene senal MAPK. | Sensibilidad a inhibidores de MEK. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-056` | **NF2 (Merlin)** | supresor | Activador de Hippo; su perdida activa YAP/TAZ (meningioma, mesotelioma). | Inhibidores de YAP/TEAD (investigacion). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-057` | **CDKN2A (p16INK4a)** | supresor | Inhibe CDK4/6 manteniendo RB activo; deleccion frecuente. | Predice dependencia de CDK4/6. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-058` | **CDKN1A (p21)** | supresor | Inhibidor de CDK inducido por p53 que impone arresto del ciclo. | Mediador de senescencia terapeutica. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-059` | **CDKN1B (p27)** | supresor | Inhibidor de CDK que frena la transicion G1/S. | Su degradacion marca agresividad. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-060` | **SMAD4** | supresor | Mediador central de TGF-beta; su perdida elude su efecto citostatico. | Contexto de senalizacion TGF-beta. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-061` | **STK11 (LKB1)** | supresor | Cinasa que activa AMPK y frena mTOR; su perdida altera metabolismo e inmunidad. | Asociada a resistencia a anti-PD-1. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-062` | **TSC1** | supresor | Con TSC2 inhibe mTORC1; su perdida hiperactiva mTOR. | Sensibilidad a inhibidores de mTOR. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-063` | **TSC2** | supresor | GAP de RHEB que reprime mTORC1. | Everolimus en tumores asociados a TSC. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-064` | **WT1** | supresor | Factor de transcripcion supresor en tumor de Wilms (rol dual). | Antigeno para inmunoterapia. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-065` | **MEN1 (menina)** | supresor | Supresor en tumores neuroendocrinos; interacciona con complejos MLL. | Inhibidores menina-MLL en leucemias. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-066` | **PTCH1** | supresor | Receptor que reprime Hedgehog; su perdida activa la via (basocelular, meduloblastoma). | Vismodegib, sonidegib. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-067` | **ARID1A** | supresor | Subunidad de SWI/SNF (BAF); mutaciones alteran la accesibilidad de cromatina. | Sintesis letal con EZH2/ATR (investigacion). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-068` | **SMARCB1** | supresor | Subunidad nuclear de SWI/SNF; su perdida define tumores rabdoides. | Dependencia de EZH2 (tazemetostat). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-069` | **FBXW7** | supresor | Receptor de E3 ligasa que degrada MYC, ciclina E y NOTCH. | Su perdida estabiliza oncoproteinas. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-070` | **CDH1 (E-cadherina)** | supresor | Adhesion celula-celula; su perdida favorece invasion (gastrico difuso, lobulillar). | Biomarcador hereditario (CDH1). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |

## Vias de senalizacion
<a id="vias-de-senalizacion"></a>
*Capa: pathway | 18 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ONC-071` | **Receptor tyrosine kinase (RTK) signaling** | proceso | Receptores de superficie que traducen factores de crecimiento a senales intracelulares. | Nodo mayor de inhibidores dirigidos. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-072` | **RAS-RAF-MEK-ERK (MAPK)** | proceso | Cascada mitogenica central; hiperactivada por RAS/RAF/RTK. | Inhibidores de BRAF y MEK. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-073` | **PI3K-AKT-mTOR** | proceso | Eje de supervivencia, crecimiento y metabolismo. | Alpelisib, capivasertib, everolimus. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-074` | **Wnt / beta-catenin** | proceso | Via de stemness y proliferacion; aberrante en CCR y otros. | Diana dificil; en investigacion. | Clevers, Cell 2006 |
| `ONC-075` | **Hedgehog** | proceso | Via del desarrollo reactivada en basocelular y meduloblastoma. | Vismodegib, sonidegib. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-076` | **Notch** | proceso | Senal de contacto con rol oncogenico o supresor segun contexto. | Gamma-secretasa (investigacion). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-077` | **JAK-STAT** | proceso | Transduce citocinas hacia transcripcion de supervivencia/proliferacion. | Ruxolitinib (JAK1/2). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-078` | **TGF-beta / SMAD** | proceso | Citostatica temprana pero pro-invasiva y pro-inmunosupresora tardia. | Diana dual segun estadio. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-079` | **Hippo-YAP/TAZ** | proceso | Controla tamano de organo; su desregulacion activa coactivadores YAP/TAZ. | Inhibidores TEAD (investigacion). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-080` | **NF-kappaB** | proceso | Factor de transcripcion de inflamacion y supervivencia. | Diana en neoplasias hematologicas. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-081` | **p53 network** | proceso | Red de respuesta a estres que decide arresto, reparacion o apoptosis. | Restauracion/estabilizacion de p53. | Vousden & Prives, Cell 2009 |
| `ONC-082` | **RB-E2F axis** | proceso | Controla la entrada en fase S liberando E2F al fosforilarse RB. | Inhibidores CDK4/6. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-083` | **MYC transcriptional program** | proceso | Amplifica la transcripcion global que sostiene crecimiento y metabolismo. | BET-i, inhibicion de sintesis (indirecta). | Dang, Cell 2012 |
| `ONC-084` | **HIF / hypoxia response** | proceso | Adaptacion a hipoxia que induce angiogenesis y glucolisis. | Belzutifan (HIF-2 alfa). | Semenza, Cell 2012 |
| `ONC-085` | **NRF2-KEAP1** | proceso | Respuesta antioxidante secuestrada por tumores para tolerar ROS. | Diana metabolica emergente. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-086` | **Estrogen receptor (ER) signaling** | proceso | Impulsa proliferacion en cancer de mama ER+. | Tamoxifeno, inhibidores de aromatasa, SERD. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-087` | **Androgen receptor (AR) signaling** | proceso | Motor del cancer de prostata. | Enzalutamida, abiraterona. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-088` | **cGAS-STING** | proceso | Sensor de ADN citosolico que activa inmunidad innata tipo I. | Agonistas STING (investigacion inmuno). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |

## Ciclo celular y checkpoints
<a id="ciclo-celular-y-checkpoints"></a>
*Capa: cellular | 13 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ONC-089` | **G1/S checkpoint (restriction point)** | proceso | Punto de compromiso a la division controlado por RB-E2F. | Inhibidores CDK4/6 lo bloquean. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-090` | **G2/M checkpoint** | proceso | Impide entrar en mitosis con ADN danado (ATR-CHK1-WEE1). | Inhibidores de WEE1/ATR/CHK1. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-091` | **Spindle assembly checkpoint (SAC)** | proceso | Retrasa la anafase hasta el correcto anclaje de cromosomas. | Diana de taxanos y alcaloides de la vinca. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-092` | **Cyclin D-CDK4/6** | proceso | Complejo que inicia la fosforilacion de RB en G1. | Palbociclib, ribociclib, abemaciclib. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-093` | **Cyclin E-CDK2** | proceso | Completa la inactivacion de RB y dispara la fase S. | Inhibidores de CDK2 (investigacion). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-094` | **Cyclin A-CDK2** | proceso | Sostiene la progresion en fase S y replicacion del ADN. | Contexto de estres replicativo. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-095` | **Cyclin B-CDK1** | proceso | Factor promotor de la mitosis (MPF) que desencadena la mitosis. | Diana indirecta antimitotica. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-096` | **RB phosphorylation** | proceso | La hiperfosforilacion de RB libera E2F y permite la fase S. | Bloqueada por inhibidores CDK4/6. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-097` | **E2F transcriptional release** | proceso | E2F activa genes de replicacion al liberarse de RB. | Nodo del control G1/S. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-098` | **p16-CDK4/6-RB axis** | proceso | Eje supresor que mantiene RB activo; a menudo inactivado en tumores. | Predice respuesta a CDK4/6i. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-099` | **CDC25 phosphatases** | proceso | Activan complejos CDK removiendo fosfatos inhibidores. | Diana experimental. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-100` | **WEE1 kinase** | proceso | Frena CDK1 imponiendo el checkpoint G2/M. | Adavosertib (WEE1i). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-101` | **APC/C (anaphase-promoting complex)** | proceso | E3 ligasa que degrada ciclinas y securina para la anafase. | Objeto de estudio antimitotico. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |

## Apoptosis y muerte celular regulada
<a id="apoptosis-y-muerte-celular-regulada"></a>
*Capa: cellular | 22 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ONC-102` | **Intrinsic (mitochondrial) apoptosis** | proceso | Estres interno provoca MOMP y liberacion de citocromo c. | Restaurada por mimeticos BH3. | Green & Kroemer, Science 2004 |
| `ONC-103` | **Extrinsic (death receptor) apoptosis** | proceso | Ligandos de muerte activan caspasa-8 via receptores. | Agonistas de DR (investigacion). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-104` | **BCL2 (anti-apoptotic)** | diana | Secuestra proteinas pro-apoptoticas impidiendo la MOMP. | Venetoclax. | Souers et al., Nat Med 2013 |
| `ONC-105` | **BCL-XL (BCL2L1)** | diana | Guardian anti-apoptotico clave en plaquetas y tumores solidos. | Inhibidores BCL-XL (toxicidad plaquetaria). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-106` | **MCL1** | diana | Anti-apoptotica de vida corta que media resistencia. | Inhibidores de MCL1 (investigacion). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-107` | **BAX** | proceso | Efector que oligomeriza y permeabiliza la membrana mitocondrial. | Activacion promuerte deseada. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-108` | **BAK** | proceso | Efector complementario de BAX en la MOMP. | Restaurar su activacion. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-109` | **BIM (BCL2L11)** | proceso | BH3-only activador que dispara BAX/BAK. | Su induccion media respuesta a TKI. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-110` | **PUMA (BBC3)** | proceso | BH3-only inducido por p53 que sensibiliza a apoptosis. | Efector de terapias que activan p53. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-111` | **NOXA (PMAIP1)** | proceso | BH3-only que neutraliza MCL1 preferentemente. | Sinergiza con inhibidores BCL2. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-112` | **Cytochrome c / apoptosome (APAF1)** | proceso | El citocromo c liberado ensambla el apoptosoma que activa caspasa-9. | Nodo central de la via intrinseca. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-113` | **Caspase-8 (initiator)** | proceso | Iniciadora de la via extrinseca en el DISC. | Diana de estrategias pro-muerte. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-114` | **Caspase-9 (initiator)** | proceso | Iniciadora activada por el apoptosoma. | Nodo intrinseco. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-115` | **Caspase-3 (executioner)** | proceso | Ejecutora que degrada sustratos y desmantela la celula. | Marcador de muerte efectiva. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-116` | **FAS-FASL** | proceso | Par receptor-ligando de muerte de la via extrinseca. | Modulacion inmune de la muerte. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-117` | **TRAIL-DR4/DR5** | diana | Ligando y receptores que inducen apoptosis selectiva en tumores. | Agonistas de DR5 (investigacion). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-118` | **XIAP** | diana | IAP que inhibe caspasas ejecutoras. | Antagonistas SMAC-mimeticos. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-119` | **Survivin (BIRC5)** | diana | IAP sobreexpresada que bloquea apoptosis y regula mitosis. | Diana e inmunodiana. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-120` | **SMAC/DIABLO** | proceso | Neutraliza IAP al liberarse de la mitocondria. | Base de los SMAC-mimeticos. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-121` | **Necroptosis (RIPK3-MLKL)** | proceso | Muerte litica programada independiente de caspasas. | Explotable ante apoptosis bloqueada. | Vandenabeele et al., Nat Rev Mol Cell Biol 2010 |
| `ONC-122` | **Ferroptosis (GPX4)** | diana | Muerte por peroxidacion lipidica dependiente de hierro; GPX4 la reprime. | Inductores de ferroptosis (investigacion). | Dixon et al., Cell 2012 |
| `ONC-123` | **Pyroptosis (gasdermin)** | proceso | Muerte inflamatoria mediada por poros de gasdermina. | Interfaz con inmunidad antitumoral. | Shi et al., Nature 2015 |

## Respuesta al dano y reparacion de ADN
<a id="respuesta-al-dano-y-reparacion-de-adn"></a>
*Capa: molecular | 18 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ONC-124` | **ATM kinase** | proceso | Sensor apical de roturas de doble cadena que coordina el DDR. | Su perdida sensibiliza a inhibidores. | Shiloh, Nat Rev Cancer 2003 |
| `ONC-125` | **ATR kinase** | proceso | Sensor de estres replicativo y ADN monocatenario. | Inhibidores de ATR (investigacion). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-126` | **CHK1** | proceso | Efector de ATR que impone el checkpoint intra-S y G2/M. | Inhibidores de CHK1. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-127` | **CHK2** | proceso | Efector de ATM que propaga la senal de dano a p53/CDC25. | Contexto de checkpoints. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-128` | **DNA-PKcs** | proceso | Cinasa central del NHEJ que une extremos rotos. | Radiosensibilizacion. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-129` | **Homologous recombination (RAD51)** | proceso | Reparacion fiel de DSB usando la cromatida hermana. | Su deficiencia (HRD) sensibiliza a PARPi/platino. | Farmer et al., Nature 2005 |
| `ONC-130` | **Non-homologous end joining (NHEJ)** | proceso | Reparacion rapida y propensa a error que religa extremos. | Radiosensibilizacion. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-131` | **Mismatch repair (MMR)** | proceso | Corrige errores de apareamiento; su perdida causa MSI e hipermutacion. | dMMR/MSI-H predice respuesta a anti-PD-1. | Le et al., NEJM 2015 |
| `ONC-132` | **Base excision repair (BER)** | proceso | Repara bases danadas por oxidacion/alquilacion. | Contexto de sensibilidad a PARP. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-133` | **Nucleotide excision repair (NER)** | proceso | Elimina lesiones voluminosas como aductos de platino/UV. | Modula respuesta al platino. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-134` | **PARP1** | diana | Detecta roturas de cadena simple e inicia su reparacion. | Olaparib y otros PARPi (sintesis letal). | Bryant et al., Nature 2005 |
| `ONC-135` | **Fanconi anemia pathway** | proceso | Resuelve enlaces cruzados interhebra coordinando HR. | Sensibilidad a agentes de cross-link. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-136` | **53BP1** | proceso | Favorece NHEJ y antagoniza la reseccion; su perdida da resistencia a PARPi. | Biomarcador de resistencia. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-137` | **gamma-H2AX** | biomarcador | Fosforilacion de H2AX que marca focos de dano de doble cadena. | Biomarcador de dano/eficacia. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-138` | **MRN complex (MRE11-RAD50-NBS1)** | proceso | Sensa y resecciona DSB reclutando ATM. | Nodo temprano del DDR. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-139` | **Replication stress response** | proceso | Gestion de horquillas de replicacion estancadas o colapsadas. | Explotable con ATR/WEE1/CHK1i. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-140` | **Synthetic lethality** | mecanismo | Dos defectos individualmente tolerables son letales juntos. | Paradigma PARPi en HRD. | Kaelin, Nat Rev Cancer 2005 |
| `ONC-141` | **BRCAness** | biomarcador | Fenotipo de deficiencia de HR sin mutacion germinal de BRCA. | Amplia la poblacion candidata a PARPi. | Lord & Ashworth, Nat Med 2013 |

## Inestabilidad genomica y mutagenesis
<a id="inestabilidad-genomica-y-mutagenesis"></a>
*Capa: molecular | 12 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ONC-142` | **Chromosomal instability (CIN)** | proceso | Tasa elevada de ganancias/perdidas cromosomicas. | Fuente de heterogeneidad y resistencia. | Lengauer et al., Nature 1998 |
| `ONC-143` | **Microsatellite instability (MSI)** | biomarcador | Hipermutabilidad de repeticiones por fallo de MMR. | MSI-H predice respuesta a inmunoterapia. | Vogelstein et al., Science 2013 (Cancer Genome Landscapes) |
| `ONC-144` | **Aneuploidy** | proceso | Numero anomalo de cromosomas que altera dosis genica. | Vulnerabilidades emergentes. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-145` | **Tumor mutational burden (TMB)** | biomarcador | Densidad de mutaciones somaticas por megabase. | TMB alto predice beneficio de checkpoint. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-146` | **Mutational signatures (COSMIC)** | biomarcador | Patrones que revelan procesos mutagenicos (UV, tabaco, APOBEC). | Orientan etiologia y diana. | Alexandrov et al., Nature 2013 |
| `ONC-147` | **APOBEC mutagenesis** | proceso | Citidina-deaminasas que introducen mutaciones agrupadas. | Fuente de neoantigenos. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-148` | **Chromothripsis** | proceso | Evento catastrofico que fragmenta y reordena un cromosoma. | Genera amplificaciones oncogenicas. | Stephens et al., Cell 2011 |
| `ONC-149` | **Kataegis** | proceso | Hipermutacion localizada, a menudo por APOBEC. | Marca regiones inestables. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-150` | **Whole-genome doubling** | proceso | Duplicacion del genoma que tolera aneuploidia posterior. | Asociada a mal pronostico. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-151` | **Loss of heterozygosity (LOH)** | proceso | Perdida del alelo funcional restante de un supresor. | Segundo golpe de Knudson; HRD-LOH score. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-152` | **Oncogene-induced replication stress** | proceso | Oncogenes fuerzan replicacion aberrante y dano. | Talon de Aquiles (ATR/WEE1i). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-153` | **Extrachromosomal DNA (ecDNA)** | proceso | Amplicones circulares que elevan y diversifican oncogenes. | Diana emergente de resistencia. | Turner et al., Nature 2017 |

## Telomeros, senescencia e inmortalidad
<a id="telomeros-senescencia-e-inmortalidad"></a>
*Capa: cellular | 8 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ONC-154` | **Telomerase (TERT)** | diana | Transcriptasa inversa que elonga telomeros y confiere inmortalidad. | Inhibicion de telomerasa (investigacion). | Kim et al., Science 1994 |
| `ONC-155` | **TERT promoter mutations** | biomarcador | Mutaciones que reactivan TERT (melanoma, glioma, vejiga). | Biomarcador diagnostico/pronostico. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-156` | **Alternative lengthening of telomeres (ALT)** | proceso | Mantenimiento telomerico por recombinacion, sin telomerasa. | Diana de ATR (investigacion). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-157` | **Replicative senescence** | proceso | Arresto permanente por acortamiento telomerico critico. | Barrera a superar por el tumor. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-158` | **Oncogene-induced senescence (OIS)** | proceso | Freno protector ante oncogenes hiperactivos. | Su elusion favorece progresion. | Serrano et al., Cell 1997 |
| `ONC-159` | **SASP (senescence-associated secretory phenotype)** | proceso | Secretoma inflamatorio de celulas senescentes que remodela el TME. | Diana de senomorficos. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-160` | **Therapy-induced senescence** | proceso | Senescencia inducida por quimio/radio con efectos duales. | Estrategias one-two punch (senoliticos). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-161` | **Hayflick limit** | proceso | Numero finito de divisiones de celulas somaticas normales. | Marco conceptual de la inmortalizacion. | Hayflick & Moorhead, Exp Cell Res 1961 |

## Angiogenesis
<a id="angiogenesis"></a>
*Capa: cellular | 10 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ONC-162` | **VEGF-A** | diana | Ligando maestro que induce proliferacion y permeabilidad endotelial. | Bevacizumab, aflibercept. | Ferrara et al., Nat Med 2003 |
| `ONC-163` | **VEGFR2 (KDR)** | diana | Receptor principal de la senal angiogenica de VEGF. | Ramucirumab; TKI antiangiogenicos. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-164` | **Angiogenic switch** | proceso | Cambio hacia fenotipo pro-angiogenico que vasculariza el tumor. | Blanco de la terapia antiangiogenica. | Hanahan & Folkman, Cell 1996 |
| `ONC-165` | **HIF-1 alpha** | proceso | Factor de transcripcion de hipoxia que induce VEGF y glucolisis. | Diana indirecta; HIF-2 con belzutifan. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-166` | **Tumor hypoxia** | proceso | Baja oxigenacion que selecciona clones agresivos y resistencia. | Radiorresistencia; profarmacos hipoxicos. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-167` | **Angiopoietin-Tie2** | diana | Regula estabilidad y maduracion vascular. | Inhibicion dual con VEGF (investigacion). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-168` | **FGF-driven angiogenesis** | proceso | FGF como via alternativa de escape antiangiogenico. | Inhibidores pan-FGFR. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-169` | **PDGF pericyte recruitment** | proceso | Reclutamiento de pericitos que estabiliza neovasos. | Diana combinada con VEGF. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-170` | **Vascular normalization** | mecanismo | La antiangiogenica juiciosa normaliza vasos y mejora la entrega de farmaco. | Ventana de sinergia con quimio. | Jain, Science 2005 |
| `ONC-171` | **Anti-angiogenic therapy** | modalidad | Bloqueo del suministro vascular del tumor. | Bevacizumab, sunitinib, sorafenib. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |

## Invasion, EMT y metastasis
<a id="invasion-emt-y-metastasis"></a>
*Capa: cellular | 18 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ONC-172` | **Epithelial-mesenchymal transition (EMT)** | proceso | Reprogramacion que otorga motilidad e invasividad. | Diana de la plasticidad tumoral. | Thiery, Nat Rev Cancer 2002 |
| `ONC-173` | **E-cadherin loss** | proceso | Perdida de adhesion epitelial que libera celulas invasivas. | Marcador de EMT. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-174` | **SNAIL** | proceso | Factor de transcripcion que reprime E-cadherina e induce EMT. | Diana de EMT (investigacion). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-175` | **TWIST** | proceso | Inductor de EMT y stemness metastasica. | Contexto de plasticidad. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-176` | **ZEB1** | proceso | Represor de epitelialidad que refuerza el estado mesenquimal. | Nodo de resistencia/plasticidad. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-177` | **Matrix metalloproteinases (MMPs)** | proceso | Proteasas que degradan la matriz y liberan factores. | Historicos MMPi (reto de especificidad). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-178` | **Invadopodia** | proceso | Protrusiones que focalizan la degradacion de matriz. | Diana estructural (investigacion). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-179` | **Basement membrane degradation** | proceso | Ruptura de la barrera que separa epitelio y estroma. | Paso definitorio de invasion. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-180` | **Intravasation** | proceso | Entrada de celulas tumorales a la circulacion. | Diana del cascada metastasica. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-181` | **Circulating tumor cells (CTCs)** | biomarcador | Celulas tumorales en sangre; siembra metastasica y biopsia liquida. | Monitorizacion no invasiva. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-182` | **Extravasation** | proceso | Salida de la circulacion hacia el tejido diana. | Paso de la colonizacion. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-183` | **Pre-metastatic niche** | proceso | Acondicionamiento a distancia del organo diana antes de la llegada. | Diana preventiva (investigacion). | Kaplan et al., Nature 2005 |
| `ONC-184` | **Metastatic colonization** | proceso | Etapa limitante: crecer en un organo ajeno. | Objetivo terapeutico critico. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-185` | **Tumor dormancy** | proceso | Celulas diseminadas quiescentes que recaen anos despues. | Reto de erradicacion. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-186` | **Organotropism (seed and soil)** | proceso | Patrones organo-especificos de metastasis. | Explica tropismos clinicos. | Paget 1889; Fidler, Nat Rev Cancer 2003 |
| `ONC-187` | **Integrins** | diana | Receptores de matriz que guian adhesion y supervivencia. | Modulan tropismo y farmacorresistencia. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-188` | **Focal adhesion kinase (FAK)** | diana | Integra senal de adhesion con supervivencia y motilidad. | Inhibidores de FAK (investigacion). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-189` | **Rho/Rac cytoskeletal dynamics** | proceso | GTPasas que reorganizan el citoesqueleto para migrar. | Diana de motilidad (investigacion). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |

## Metabolismo tumoral
<a id="metabolismo-tumoral"></a>
*Capa: molecular | 16 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ONC-190` | **Warburg effect (aerobic glycolysis)** | proceso | Preferencia por glucolisis con lactato pese a haber oxigeno. | Base de PET-FDG; dianas metabolicas. | Warburg 1956; Vander Heiden et al., Science 2009 |
| `ONC-191` | **Glutaminolysis** | proceso | Uso de glutamina como carbono/nitrogeno anaplerotico. | Inhibidores de glutaminasa (investigacion). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-192` | **Lactate / MCT shuttle** | proceso | Exportacion e intercambio de lactato que acidifica el TME. | Inhibidores de MCT (investigacion). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-193` | **PKM2** | proceso | Isoforma de piruvato-cinasa que favorece biosintesis. | Diana metabolica (investigacion). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-194` | **LDHA** | proceso | Convierte piruvato en lactato regenerando NAD+. | Inhibicion de LDHA (investigacion). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-195` | **GLUT1 (SLC2A1)** | proceso | Transportador que eleva la captacion de glucosa. | Correlato de PET-FDG. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-196` | **One-carbon / folate metabolism** | proceso | Aporta unidades de carbono para nucleotidos y metilacion. | Antifolatos (metotrexato, pemetrexed). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-197` | **Serine-glycine biosynthesis** | proceso | Ruta biosintetica reprogramada que alimenta el one-carbon. | Diana metabolica emergente. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-198` | **Fatty acid synthesis (FASN)** | proceso | Lipogenesis de novo para membranas y senalizacion. | Inhibidores de FASN (investigacion). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-199` | **2-HG oncometabolite (IDH-mut)** | biomarcador | IDH mutante produce 2-hidroxiglutarato que altera la epigenetica. | Ivosidenib/enasidenib; biomarcador. | Dang et al., Nature 2009 |
| `ONC-200` | **TCA cycle rewiring** | proceso | Reprogramacion del ciclo de Krebs para biosintesis. | Vulnerabilidades contextuales. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-201` | **NAD+ metabolism** | proceso | Cofactor redox y de senalizacion elevado en proliferacion. | Inhibidores de NAMPT (investigacion). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-202` | **Autophagy** | proceso | Reciclaje de organelas/proteinas para sobrevivir al estres. | Modulacion (cloroquina, investigacion). | Levine & Kroemer, Cell 2008 |
| `ONC-203` | **Reductive carboxylation** | proceso | Sintesis de citrato desde glutamina en hipoxia. | Vulnerabilidad metabolica. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-204` | **ROS / redox homeostasis** | proceso | Equilibrio de especies reactivas que el tumor debe tamponar. | Estrategias pro-oxidantes selectivas. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-205` | **Amino-acid dependency (Asn/Arg)** | proceso | Adiccion a aminoacidos no sintetizables por ciertos tumores. | L-asparaginasa (LLA); depledores de arginina. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |

## Epigenetica y cromatina
<a id="epigenetica-y-cromatina"></a>
*Capa: molecular | 15 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ONC-206` | **DNA methylation (5mC)** | proceso | Marca en CpG que regula la expresion sin cambiar la secuencia. | Base de terapias hipometilantes. | Jones & Baylin, Nat Rev Genet 2002 |
| `ONC-207` | **DNMTs (DNMT1/3A/3B)** | diana | Enzimas que escriben la metilacion del ADN. | Azacitidina, decitabina. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-208` | **CpG island hypermethylation** | proceso | Silenciamiento de supresores por metilacion de promotores. | Reversible con DNMTi. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-209` | **Global hypomethylation** | proceso | Perdida global de metilacion que favorece inestabilidad. | Marca epigenetica tumoral. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-210` | **Histone acetyltransferases (HATs)** | proceso | Anaden acetilo abriendo cromatina para transcripcion. | Contexto de balance con HDAC. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-211` | **Histone deacetylases (HDACs)** | diana | Retiran acetilos compactando cromatina. | Vorinostat, romidepsina. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-212` | **Histone methylation** | proceso | Marcas activadoras o represoras segun residuo y grado. | Diana de escritores/borradores. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-213` | **EZH2 / PRC2 (H3K27me3)** | diana | Deposita marca represiva que silencia supresores. | Tazemetostat. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-214` | **DOT1L (H3K79me)** | diana | Metiltransferasa esencial en leucemias con reordenamiento MLL. | Inhibidores de DOT1L (investigacion). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-215` | **BET / BRD4** | diana | Lectores de acetil-lisina que sostienen la transcripcion de MYC. | Inhibidores BET (investigacion). | Filippakopoulos et al., Nature 2010 |
| `ONC-216` | **SWI/SNF (BAF) remodeling** | proceso | Complejo que reposiciona nucleosomas; frecuentemente mutado. | Sintesis letal con EZH2. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-217` | **TET enzymes / 5hmC** | proceso | Oxidan 5mC iniciando desmetilacion activa. | Alterada por 2-HG en IDH-mut. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-218` | **Super-enhancers** | proceso | Grandes clusters regulatorios que sostienen oncogenes de identidad. | Vulnerables a inhibicion transcripcional. | Hnisz et al., Cell 2013 |
| `ONC-219` | **Histone variants** | proceso | Variantes (p.ej. H3.3) que alteran cromatina; mutadas en gliomas pediatricos. | Biomarcador diagnostico. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-220` | **Chromatin accessibility** | proceso | Paisaje abierto/cerrado que define programas transcripcionales. | Perfilable por ATAC-seq. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |

## Microambiente tumoral (TME)
<a id="microambiente-tumoral-tme"></a>
*Capa: tissue | 13 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ONC-221` | **Cancer-associated fibroblasts (CAFs)** | proceso | Fibroblastos activados que remodelan matriz y secretan factores. | Diana estromal (investigacion). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-222` | **Tumor-associated macrophages (TAMs, M2)** | diana | Macrofagos pro-tumorales que suprimen inmunidad y favorecen angiogenesis. | Reprogramacion; anti-CSF1R. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-223` | **Myeloid-derived suppressor cells (MDSCs)** | proceso | Poblacion mieloide inmadura que inhibe linfocitos T. | Objetivo de combinaciones inmunes. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-224` | **Regulatory T cells (Tregs)** | diana | Linfocitos que amortiguan la respuesta antitumoral. | Deplecion selectiva (investigacion). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-225` | **Extracellular matrix remodeling** | proceso | Rigidez y composicion de matriz que guian invasion y farmacorresistencia. | Normalizacion estromal. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-226` | **Hypoxic niche** | proceso | Regiones hipoxicas que fomentan stemness y resistencia. | Radiorresistencia; profarmacos. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-227` | **Abnormal tumor vasculature** | proceso | Vasos tortuosos y permeables que dificultan la entrega de farmacos. | Normalizacion vascular. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-228` | **Desmoplasia** | proceso | Estroma denso (p.ej. pancreas) que actua de barrera fisica. | Reto de penetracion terapeutica. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-229` | **Tumor-derived exosomes** | proceso | Vesiculas que transportan senales pro-tumorales a distancia. | Biomarcadores y dianas emergentes. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-230` | **Cytokine/chemokine milieu** | proceso | Red soluble que recluta y polariza celulas inmunes. | Modulacion inmune dirigida. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-231` | **Tertiary lymphoid structures (TLS)** | biomarcador | Agregados linfoides intratumorales asociados a mejor respuesta inmune. | Predictor de respuesta a checkpoint. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-232` | **Immune-excluded phenotype** | biomarcador | Linfocitos confinados al estroma sin infiltrar el nido tumoral. | Estratifica respuesta a inmunoterapia. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-233` | **Metabolic competition in TME** | proceso | El tumor priva de glucosa y aminoacidos a linfocitos. | Reprogramacion metabolica inmune. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |

## Inmuno-oncologia y evasion inmune
<a id="inmuno-oncologia-y-evasion-inmune"></a>
*Capa: tissue | 22 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ONC-234` | **PD-1 (PDCD1)** | diana | Checkpoint inhibidor en linfocitos T que limita su activacion. | Pembrolizumab, nivolumab. | Ishida et al., EMBO J 1992 |
| `ONC-235` | **PD-L1 (CD274)** | diana | Ligando tumoral de PD-1 que apaga la respuesta T. | Atezolizumab; biomarcador (TPS/CPS). | Dong et al., Nat Med 2002 |
| `ONC-236` | **CTLA-4** | diana | Checkpoint que compite con CD28 frenando el cebado T. | Ipilimumab. | Leach, Krummel & Allison, Science 1996 |
| `ONC-237` | **Immune checkpoint blockade** | modalidad | Liberar frenos inmunes para reactivar linfocitos antitumorales. | Paradigma anti-PD-1/PD-L1/CTLA-4. | Sharma & Allison, Science 2015 |
| `ONC-238` | **T-cell exhaustion** | proceso | Disfuncion progresiva de T por estimulacion cronica. | Reversible parcialmente con checkpoint. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-239` | **Neoantigens** | biomarcador | Peptidos mutados tumor-especificos reconocidos por linfocitos T. | Base de vacunas personalizadas. | Schumacher & Schreiber, Science 2015 |
| `ONC-240` | **MHC-I antigen presentation** | proceso | Presentacion de peptidos a CD8; su perdida evade inmunidad. | Su restauracion mejora respuesta. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-241` | **Tumor-infiltrating lymphocytes (TILs)** | biomarcador | Linfocitos infiltrantes; su densidad predice pronostico/respuesta. | Base de la terapia con TIL. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-242` | **CD8+ cytotoxic T cells** | proceso | Efectores que lisan celulas tumorales reconocidas. | Objetivo a potenciar en inmunoterapia. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-243` | **Natural killer (NK) cells** | proceso | Inmunidad innata que mata celulas sin MHC-I (missing self). | Terapias NK y CAR-NK. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-244` | **CAR-T cells** | modalidad | Linfocitos T con receptor quimerico contra antigeno tumoral. | Anti-CD19 en linfoma/leucemia; anti-BCMA en mieloma. | June & Sadelain, NEJM 2018 |
| `ONC-245` | **Bispecific T-cell engagers (BiTE)** | modalidad | Anticuerpos que unen CD3 de T con antigeno tumoral. | Blinatumomab (CD19xCD3). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-246` | **TCR-engineered T cells** | modalidad | T con TCR redirigido a antigenos intracelulares via MHC. | Anti-antigenos de cancer/testiculo. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-247` | **Cancer vaccines** | modalidad | Inmunizacion con antigenos tumorales para inducir respuesta T. | Vacunas de neoantigeno (mRNA). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-248` | **Oncolytic viruses** | modalidad | Virus que lisan tumores e inducen inmunidad in situ. | Talimogene laherparepvec (T-VEC). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-249` | **LAG-3** | diana | Checkpoint co-inhibidor que sinergiza con PD-1. | Relatlimab (combinado con nivolumab). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-250` | **TIM-3 (HAVCR2)** | diana | Marcador/regulador de agotamiento T. | Inhibidores en investigacion. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-251` | **TIGIT** | diana | Checkpoint que compite por ligandos con CD226. | Anti-TIGIT en investigacion. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-252` | **IDO1** | diana | Enzima que degrada triptofano creando entorno inmunosupresor. | Inhibidores de IDO (investigacion). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-253` | **Adenosine / CD73 axis** | diana | Adenosina extracelular que suprime linfocitos T. | Anti-CD39/CD73/A2AR (investigacion). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-254` | **CD47-SIRP alpha (dont eat me)** | diana | Senal que protege al tumor de la fagocitosis. | Bloqueo de CD47 (investigacion). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-255` | **Immunogenic cell death (ICD)** | proceso | Muerte que libera senales de peligro y activa inmunidad. | Inducida por ciertas quimio/radio. | Galluzzi et al., Nat Rev Immunol 2017 |

## Modalidades terapeuticas
<a id="modalidades-terapeuticas"></a>
*Capa: therapy | 18 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ONC-256` | **Cytotoxic chemotherapy** | modalidad | Farmacos que danan celulas en division rapida. | Columna vertebral historica del tratamiento. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-257` | **Alkylating agents** | modalidad | Anaden grupos alquilo al ADN generando enlaces cruzados. | Ciclofosfamida, temozolomida. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-258` | **Platinum agents** | modalidad | Forman aductos de ADN que bloquean replicacion. | Cisplatino, carboplatino, oxaliplatino. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-259` | **Antimetabolites** | modalidad | Analogos que interfieren sintesis de nucleotidos/ADN. | 5-FU, metotrexato, gemcitabina. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-260` | **Topoisomerase inhibitors** | modalidad | Bloquean topoisomerasas provocando roturas de ADN. | Irinotecan, etoposido, doxorrubicina. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-261` | **Taxanes** | modalidad | Estabilizan microtubulos e impiden la mitosis. | Paclitaxel, docetaxel. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-262` | **Vinca alkaloids** | modalidad | Impiden el ensamblaje de microtubulos. | Vincristina, vinblastina. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-263` | **Anthracyclines** | modalidad | Intercalan ADN e inhiben topoisomerasa II. | Doxorrubicina (toxicidad cardiaca). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-264` | **Small-molecule kinase inhibitors** | modalidad | Bloquean cinasas oncogenicas especificas. | Imatinib, osimertinib, muchos mas. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-265` | **Monoclonal antibodies** | modalidad | Anticuerpos que marcan o bloquean dianas de superficie. | Rituximab, trastuzumab, cetuximab. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-266` | **Antibody-drug conjugates (ADCs)** | modalidad | Anticuerpo unido a citotoxico para entrega dirigida. | T-DXd, sacituzumab govitecan. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-267` | **Radiotherapy** | modalidad | Radiacion ionizante que induce dano letal de ADN. | Curativa/paliativa segun contexto. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-268` | **Endocrine / hormonal therapy** | modalidad | Bloquea senal hormonal que impulsa el tumor. | Tamoxifeno, inhibidores de aromatasa, ADT. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-269` | **Proteasome inhibitors** | modalidad | Bloquean la degradacion proteica generando estres. | Bortezomib (mieloma). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-270` | **PROTAC degraders** | modalidad | Reclutan una E3 ligasa para degradar la diana. | Degradadores de AR/ER (investigacion). | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-271` | **Differentiation therapy** | modalidad | Fuerza la maduracion de celulas malignas. | ATRA + arsenico en LPA. | Huang et al., Blood 1988 |
| `ONC-272` | **Immunomodulatory drugs (IMiDs)** | modalidad | Modulan cereblon y la inmunidad (mieloma). | Lenalidomida, pomalidomida. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-273` | **Epigenetic therapy** | modalidad | Revierte silenciamientos aberrantes de la cromatina. | DNMTi, HDACi, EZH2i. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |

## Primitivas farmaco -> diana
<a id="primitivas-farmaco-->-diana"></a>
*Capa: therapy | 27 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ONC-274` | **Imatinib -> BCR-ABL** | farmaco->diana | Inhibidor de tirosina-cinasa que apaga BCR-ABL en LMC. | Transformo la LMC en enfermedad cronica. | Druker et al., NEJM 2001 |
| `ONC-275` | **Trastuzumab -> HER2** | farmaco->diana | Anticuerpo que bloquea HER2 en tumores HER2+. | Mama y gastrico HER2+. | Slamon et al., NEJM 2001 |
| `ONC-276` | **Trastuzumab deruxtecan -> HER2 (ADC)** | farmaco->diana | ADC que entrega un inhibidor de topoisomerasa I a celulas HER2. | Activo incluso en HER2-bajo. | Modi et al., NEJM 2022 |
| `ONC-277` | **Osimertinib -> EGFR (T790M)** | farmaco->diana | TKI de 3a generacion contra EGFR mutante y T790M. | 1a linea en NSCLC EGFR-mut. | Soria et al., NEJM 2018 |
| `ONC-278` | **Gefitinib/Erlotinib -> EGFR** | farmaco->diana | TKI de 1a generacion para EGFR con mutacion sensibilizante. | NSCLC EGFR-mut. | Mok et al., NEJM 2009 |
| `ONC-279` | **Vemurafenib -> BRAF V600E** | farmaco->diana | Inhibidor selectivo de BRAF V600E. | Melanoma BRAF-mut. | Chapman et al., NEJM 2011 |
| `ONC-280` | **Dabrafenib + Trametinib -> BRAF + MEK** | farmaco->diana | Doble bloqueo de la via MAPK que retrasa resistencia. | Melanoma y otros BRAF V600. | Long et al., NEJM 2014 |
| `ONC-281` | **Sotorasib -> KRAS G12C** | farmaco->diana | Inhibidor covalente que atrapa KRAS G12C inactivo (bolsillo switch-II). | NSCLC KRAS G12C. | Skoulidis et al., NEJM 2021 |
| `ONC-282` | **Adagrasib -> KRAS G12C** | farmaco->diana | Segundo inhibidor covalente de KRAS G12C. | NSCLC y CCR KRAS G12C. | Janne et al., NEJM 2022 |
| `ONC-283` | **Crizotinib -> ALK/ROS1** | farmaco->diana | TKI para fusiones ALK y ROS1. | NSCLC ALK+ o ROS1+. | Shaw et al., NEJM 2013 |
| `ONC-284` | **Alectinib -> ALK** | farmaco->diana | TKI de ALK de nueva generacion con actividad en SNC. | 1a linea NSCLC ALK+. | Peters et al., NEJM 2017 |
| `ONC-285` | **Larotrectinib -> NTRK fusion** | farmaco->diana | Inhibidor TRK agnostico de tipo tumoral. | Tumores con fusion NTRK. | Drilon et al., NEJM 2018 |
| `ONC-286` | **Olaparib -> PARP** | farmaco->diana | Inhibidor de PARP letal en tumores con deficiencia de HR. | Ovario/mama BRCA-mut. | Ledermann et al., NEJM 2012 |
| `ONC-287` | **Venetoclax -> BCL2** | farmaco->diana | Mimetico BH3 que restaura la apoptosis. | LLC y LMA. | Souers et al., Nat Med 2013 |
| `ONC-288` | **Palbociclib -> CDK4/6** | farmaco->diana | Inhibidor de CDK4/6 que frena la fosforilacion de RB. | Mama HR+/HER2-. | Finn et al., NEJM 2016 |
| `ONC-289` | **Rituximab -> CD20** | farmaco->diana | Anticuerpo anti-CD20 que deplecciona linfocitos B. | Linfomas B y LLC. | Coiffier et al., NEJM 2002 |
| `ONC-290` | **Bevacizumab -> VEGF-A** | farmaco->diana | Anticuerpo que neutraliza VEGF-A y priva de angiogenesis. | Colorrectal, pulmon, otros. | Hurwitz et al., NEJM 2004 |
| `ONC-291` | **Sunitinib -> VEGFR (multi-TKI)** | farmaco->diana | Inhibidor multicinasa antiangiogenico. | Renal, GIST, TNE. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-292` | **Ibrutinib -> BTK** | farmaco->diana | Inhibidor covalente de BTK en la senal del receptor B. | LLC y linfoma del manto. | Byrd et al., NEJM 2013 |
| `ONC-293` | **Ruxolitinib -> JAK1/2** | farmaco->diana | Inhibidor de JAK que bloquea la senal JAK-STAT. | Mielofibrosis y policitemia vera. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-294` | **Ivosidenib -> IDH1 mutante** | farmaco->diana | Inhibidor del IDH1 mutante que reduce el 2-HG. | LMA y colangiocarcinoma IDH1-mut. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-295` | **Enasidenib -> IDH2 mutante** | farmaco->diana | Inhibidor del IDH2 mutante que induce diferenciacion. | LMA IDH2-mut. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-296` | **Tazemetostat -> EZH2** | farmaco->diana | Inhibidor de EZH2 que revierte silenciamiento represivo. | Linfoma folicular y sarcoma epitelioide. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-297` | **Pembrolizumab -> PD-1** | farmaco->diana | Anti-PD-1 que reactiva linfocitos T antitumorales. | Multiples tumores; agnostico en MSI-H. | Le et al., NEJM 2015 |
| `ONC-298` | **Nivolumab -> PD-1** | farmaco->diana | Anti-PD-1 con amplio desarrollo clinico. | Melanoma, pulmon, renal, otros. | Topalian et al., NEJM 2012 |
| `ONC-299` | **Atezolizumab -> PD-L1** | farmaco->diana | Anticuerpo anti-PD-L1 que bloquea el eje PD-1/PD-L1. | Pulmon, vejiga, mama TN. | Weinberg RA, The Biology of Cancer, 2nd ed. 2014 |
| `ONC-300` | **Ipilimumab -> CTLA-4** | farmaco->diana | Anti-CTLA-4, primer checkpoint con beneficio en supervivencia. | Melanoma; combinaciones. | Hodi et al., NEJM 2010 |

---

## Nota metodologica

Las primitivas cubren desde los *hallmarks* de Hanahan & Weinberg (Cell 2000, 2011; Cancer Discovery 2022) hasta pares farmaco->diana con evidencia clinica registrada. Las referencias citan articulos o revisiones canonicas; los mecanismos reflejan conocimiento establecido a la fecha de generacion. Esto es material educativo y de modelado ontologico: **no sustituye juicio clinico ni investigacion primaria.**

