# 302 Primitivas de Biologia del Cancer

### Ontologia CORTEX / BABYLON-60 -- bloques fundamentales que la investigacion del cancer estudia y ataca

*Generado 2026-07-14 | 302 primitivas | escala de confianza C5-established | fuente unica: `empiric_science/gen_oncology_primitives.py`*

> **AVISO IMPORTANTE.** Esto es una ONTOLOGIA DE CONOCIMIENTO de la biologia molecular del cancer (oncologia) y de sus dianas terapeuticas: los bloques fundamentales que la investigacion del cancer estudia y ataca. NO es un diagnostico, NO es un protocolo de tratamiento, NO es una guia clinica y NO es consejo medico. Los farmacos aqui listados se citan para ilustrar pares mecanismo->diana; su indicacion depende del tipo tumoral, del biomarcador (mutacion/expresion) y del contexto clinico, y NO deben autoadministrarse. El cancer requiere diagnostico y tratamiento por oncologos y equipos multidisciplinares cualificados. Cualquier decision de salud debe tomarse con profesionales sanitarios.

> *NOTICE.* This is a KNOWLEDGE ONTOLOGY of the molecular biology of cancer (oncology) and its therapeutic targets: the fundamental building blocks that cancer research studies and attacks. It is NOT a diagnosis, NOT a treatment protocol, NOT a clinical guideline and NOT medical advice. Listed drugs are cited to illustrate mechanism->target pairs; their indication depends on tumor type, biomarker (mutation/expression) and clinical context, and they must NOT be self-administered. Cancer requires diagnosis and treatment by qualified oncologists and multidisciplinary teams. Consult healthcare professionals for any decision.

Autoria artistica/arquitectonica del sustrato (AKA): **Borja Moskv** (`borjamoskv`).

---

<a id="indice"></a>
## Indice de categorias

### Resumen por capa
| Capa | Categorias | Primitivas |
| :--- | :---: | :---: |
| `meta` | 3 | 50 |
| `molecular` | 4 | 74 |
| `pathway` | 1 | 20 |
| `cellular` | 4 | 50 |
| `tissue` | 4 | 62 |
| `therapy` | 2 | 46 |
| **TOTAL** | **18** | **302** |

### Categorias
| # | Categoria | Capa | Primitivas |
| :--- | :--- | :--- | :---: |
| 1 | [Hallmarks del cancer](#hallmarks-del-cancer) | `meta` | 20 |
| 2 | [Oncogenes y senalizacion proliferativa](#oncogenes-y-senalizacion-proliferativa) | `molecular` | 22 |
| 3 | [Genes supresores de tumores](#genes-supresores-de-tumores) | `molecular` | 18 |
| 4 | [Inestabilidad genomica y reparacion del ADN](#inestabilidad-genomica-y-reparacion-del-adn) | `molecular` | 18 |
| 5 | [Vias de senalizacion oncogenica](#vias-de-senalizacion-oncogenica) | `pathway` | 20 |
| 6 | [Ciclo celular y puntos de control](#ciclo-celular-y-puntos-de-control) | `cellular` | 14 |
| 7 | [Evasion de la muerte celular](#evasion-de-la-muerte-celular) | `cellular` | 16 |
| 8 | [Inmortalidad replicativa y telomeros](#inmortalidad-replicativa-y-telomeros) | `cellular` | 8 |
| 9 | [Metabolismo tumoral](#metabolismo-tumoral) | `molecular` | 16 |
| 10 | [Angiogenesis tumoral](#angiogenesis-tumoral) | `tissue` | 12 |
| 11 | [Invasion y metastasis](#invasion-y-metastasis) | `tissue` | 18 |
| 12 | [Microambiente tumoral](#microambiente-tumoral) | `tissue` | 14 |
| 13 | [Inmunologia tumoral y evasion inmune](#inmunologia-tumoral-y-evasion-inmune) | `tissue` | 18 |
| 14 | [Heterogeneidad, plasticidad y celulas madre tumorales](#heterogeneidad-plasticidad-y-celulas-madre-tumorales) | `cellular` | 12 |
| 15 | [Carcinogenos, virus e iniciacion](#carcinogenos-virus-e-iniciacion) | `meta` | 14 |
| 16 | [Biomarcadores, diagnostico y estadificacion](#biomarcadores-diagnostico-y-estadificacion) | `meta` | 16 |
| 17 | [Modalidades terapeuticas](#modalidades-terapeuticas) | `therapy` | 20 |
| 18 | [Primitivas farmaco -> diana](#primitivas-farmaco-diana) | `therapy` | 26 |
| | **TOTAL** | | **302** |

---

## Hallmarks del cancer
<a id="hallmarks-del-cancer"></a>

*Capa: meta | 20 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ONC-001` | **Sustaining proliferative signaling** | hallmark | Las celulas tumorales sostienen senales de crecimiento de forma autonoma (mutacion de RTK, RAS, autocrinia). | Diana de inhibidores de RTK y de la via RAS-MAPK. | Hanahan & Weinberg, Cell 2011 |
| `ONC-002` | **Evading growth suppressors** | hallmark | Inactivacion de frenos del ciclo como RB y TP53 que normalmente limitan la proliferacion. | Racional de restaurar checkpoints o explotar su perdida. | Hanahan & Weinberg, Cell 2011 |
| `ONC-003` | **Resisting cell death** | hallmark | Evasion de la apoptosis por sobreexpresion de anti-apoptoticos o perdida de proapoptoticos. | Diana de mimeticos BH3 (venetoclax). | Hanahan & Weinberg, Cell 2011 |
| `ONC-004` | **Enabling replicative immortality** | hallmark | Reactivacion de telomerasa que confiere potencial replicativo ilimitado. | Diana conceptual de inhibidores de telomerasa. | Hanahan & Weinberg, Cell 2011 |
| `ONC-005` | **Inducing angiogenesis** | hallmark | Activacion del 'switch' angiogenico (VEGF) para irrigar el tumor en crecimiento. | Diana de antiangiogenicos (bevacizumab). | Hanahan & Weinberg, Cell 2011 |
| `ONC-006` | **Activating invasion and metastasis** | hallmark | Programas de invasion (EMT) y diseminacion a organos distantes. | Principal causa de mortalidad; diana de la cascada metastasica. | Hanahan & Weinberg, Cell 2011 |
| `ONC-007` | **Genome instability and mutation** | caracteristica facilitadora | Inestabilidad genomica que acelera la adquisicion de alteraciones conductoras. | Base de la carga mutacional y de la letalidad sintetica. | Hanahan & Weinberg, Cell 2011 |
| `ONC-008` | **Tumor-promoting inflammation** | caracteristica facilitadora | La inflamacion asociada al tumor aporta factores que favorecen multiples hallmarks. | Diana de estrategias antiinflamatorias. | Hanahan & Weinberg, Cell 2011 |
| `ONC-009` | **Deregulating cellular energetics (Warburg)** | hallmark | Reprogramacion metabolica hacia glucolisis aerobia y biosintesis. | Diana de la dependencia metabolica tumoral. | Hanahan & Weinberg, Cell 2011 |
| `ONC-010` | **Avoiding immune destruction** | hallmark | Evasion de la vigilancia inmune por checkpoints y perdida de antigenos. | Diana de la inmunoterapia con checkpoints. | Hanahan & Weinberg, Cell 2011 |
| `ONC-011` | **Unlocking phenotypic plasticity** | hallmark (2022) | Desbloqueo de plasticidad y desdiferenciacion que escapa a la homeostasis tisular. | Diana emergente de la plasticidad celular. | Hanahan, Cancer Discov 2022 |
| `ONC-012` | **Nonmutational epigenetic reprogramming** | hallmark (2022) | Reprogramacion epigenetica que confiere fenotipos malignos sin mutacion del ADN. | Diana de farmacos epigeneticos. | Hanahan, Cancer Discov 2022 |
| `ONC-013` | **Polymorphic microbiomes** | hallmark (2022) | Microbiomas tumorales e intestinales que modulan progresion y respuesta terapeutica. | Nexo microbioma-inmunoterapia. | Hanahan, Cancer Discov 2022 |
| `ONC-014` | **Senescent cells (tumor context)** | hallmark (2022) | Celulas senescentes que, via su secretoma, pueden favorecer la progresion tumoral. | Diana de senoliticos en oncologia. | Hanahan, Cancer Discov 2022 |
| `ONC-015` | **Somatic mutation theory of cancer** | marco | El cancer surge de la acumulacion de mutaciones somaticas conductoras en una celula. | Fundamento de la genomica del cancer. | Nowell, Science 1976 |
| `ONC-016` | **Clonal evolution** | marco | El tumor evoluciona por seleccion darwiniana de subclones con ventaja proliferativa. | Explica heterogeneidad y resistencia adquirida. | Nowell, Science 1976 |
| `ONC-017` | **Knudson two-hit hypothesis** | marco | Se necesitan dos golpes para inactivar un gen supresor (ambos alelos). | Marco de los supresores tumorales y el retinoblastoma. | Knudson, PNAS 1971 |
| `ONC-018` | **Driver vs passenger mutations** | marco | Distincion entre mutaciones que confieren ventaja (driver) y las neutrales (passenger). | Prioriza dianas accionables en genomica del cancer. | Vogelstein et al., Science 2013 |
| `ONC-019` | **Cancer as an evolutionary and ecological process** | marco | El tumor es un ecosistema de clones que compiten y cooperan bajo presion selectiva. | Marco de estrategias adaptativas de tratamiento. | Greaves & Maley, Nature 2012 |
| `ONC-020` | **Field cancerization** | marco | Areas de epitelio con alteraciones preneoplasicas que predisponen a tumores multiples. | Racional de la vigilancia de segundos tumores. | Slaughter et al., Cancer 1953 |

[volver al indice](#indice)

## Oncogenes y senalizacion proliferativa
<a id="oncogenes-y-senalizacion-proliferativa"></a>

*Capa: molecular | 22 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ONC-021` | **KRAS** | oncogen | GTPasa que en estado mutado (G12/G13/Q61) queda constitutivamente activa e impulsa RAS-MAPK. | Diana de inhibidores de KRAS G12C (sotorasib, adagrasib). | Cox et al., Nat Rev Drug Discov 2014 |
| `ONC-022` | **NRAS** | oncogen | Isoforma de RAS mutada con frecuencia en melanoma y leucemias. | Contexto de dependencia de la via MAPK. | Cox et al., Nat Rev Drug Discov 2014 |
| `ONC-023` | **HRAS** | oncogen | Isoforma de RAS mutada en tumores de cabeza y cuello y de vejiga. | Diana de inhibidores de farnesiltransferasa (tipifarnib). | Cox et al., Nat Rev Drug Discov 2014 |
| `ONC-024` | **MYC** | oncogen | Factor de transcripcion maestro que amplifica programas de crecimiento y metabolismo. | Diana 'indruggable' clasica; enfoque indirecto. | Dang, Cell 2012 |
| `ONC-025` | **EGFR (ERBB1)** | oncogen | Receptor tirosina-cinasa cuya activacion (mutacion/amplificacion) dispara proliferacion. | Diana de erlotinib, gefitinib, osimertinib. | Sharma et al., Nat Rev Cancer 2007 |
| `ONC-026` | **HER2 (ERBB2)** | oncogen | RTK amplificado en ~15-20% de cancer de mama que potencia senalizacion proliferativa. | Diana de trastuzumab, pertuzumab, T-DM1, T-DXd. | Slamon et al., Science 1987 |
| `ONC-027` | **BRAF** | oncogen | Cinasa de la via MAPK; la mutacion V600E la activa de forma constitutiva. | Diana de vemurafenib, dabrafenib (con inhibidor de MEK). | Davies et al., Nature 2002 |
| `ONC-028` | **PIK3CA** | oncogen | Subunidad catalitica de PI3K frecuentemente mutada que activa PI3K-AKT. | Diana de alpelisib en cancer de mama. | Samuels et al., Science 2004 |
| `ONC-029` | **AKT1** | oncogen | Cinasa efectora de PI3K que promueve supervivencia y crecimiento. | Diana de inhibidores de AKT (capivasertib). | Manning & Toker, Cell 2017 |
| `ONC-030` | **ALK** | oncogen | RTK que por fusion (EML4-ALK) impulsa cancer de pulmon y linfomas. | Diana de crizotinib, alectinib, lorlatinib. | Soda et al., Nature 2007 |
| `ONC-031` | **MET** | oncogen | RTK del factor de crecimiento de hepatocitos; amplificacion/skipping de exon 14. | Diana de capmatinib, tepotinib. | Comoglio et al., Nat Rev Drug Discov 2008 |
| `ONC-032` | **RET** | oncogen | RTK activado por fusion o mutacion (MEN2, tiroides, pulmon). | Diana de selpercatinib, pralsetinib. | Mulligan, Nat Rev Cancer 2014 |
| `ONC-033` | **ROS1** | oncogen | RTK que por fusion impulsa un subgrupo de cancer de pulmon. | Diana de crizotinib, entrectinib. | Bergethon et al., J Clin Oncol 2012 |
| `ONC-034` | **FGFR (1-4)** | oncogen | Familia de RTK activada por fusion, amplificacion o mutacion. | Diana de erdafitinib, pemigatinib. | Turner & Grose, Nat Rev Cancer 2010 |
| `ONC-035` | **BCR-ABL1** | oncogen | Cinasa de fusion del cromosoma Filadelfia que dirige la leucemia mieloide cronica. | Paradigma de terapia dirigida (imatinib). | Rowley, Nature 1973; Druker et al., NEJM 2001 |
| `ONC-036` | **KIT** | oncogen | RTK mutado en tumores del estroma gastrointestinal (GIST) y mastocitosis. | Diana de imatinib en GIST. | Hirota et al., Science 1998 |
| `ONC-037` | **PDGFRA** | oncogen | RTK relacionado con KIT, mutado/fusionado en GIST y leucemias eosinofilicas. | Diana de imatinib y avapritinib. | Heinrich et al., Science 2003 |
| `ONC-038` | **FLT3** | oncogen | RTK con duplicaciones internas (ITD) frecuentes en leucemia mieloide aguda. | Diana de midostaurina, gilteritinib. | Nakao et al., Leukemia 1996 |
| `ONC-039` | **JAK2** | oncogen | Cinasa con la mutacion V617F que dirige neoplasias mieloproliferativas. | Diana de ruxolitinib. | James et al., Nature 2005 |
| `ONC-040` | **MYCN** | oncogen | Parologo de MYC amplificado que marca neuroblastoma de alto riesgo. | Biomarcador pronostico; diana indirecta. | Brodeur et al., Science 1984 |
| `ONC-041` | **CCND1 / Cyclin D1** | oncogen | Ciclina que activa CDK4/6 y empuja la transicion G1-S. | Nexo con inhibidores de CDK4/6. | Musgrove et al., Nat Rev Cancer 2011 |
| `ONC-042` | **SRC** | oncogen | Primera tirosina-cinasa oncogenica descrita; regula adhesion y proliferacion. | Diana de dasatinib (multidiana). | Martin, Nat Rev Mol Cell Biol 2001 |

[volver al indice](#indice)

## Genes supresores de tumores
<a id="genes-supresores-de-tumores"></a>

*Capa: molecular | 18 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ONC-043` | **TP53** | supresor | 'Guardian del genoma': activa arresto, reparacion, senescencia o apoptosis ante estres. | Mutado en ~50% de tumores; restauracion como diana. | Levine, Cell 1997 |
| `ONC-044` | **RB1** | supresor | Freno maestro de G1-S que secuestra E2F; su perdida libera la proliferacion. | Paradigma de Knudson (retinoblastoma). | Weinberg, Cell 1995 |
| `ONC-045` | **PTEN** | supresor | Fosfatasa que antagoniza PI3K desfosforilando PIP3; su perdida activa AKT. | Perdida frecuente; sensibiliza a inhibicion de PI3K. | Li et al., Science 1997 |
| `ONC-046` | **APC** | supresor | Regula la degradacion de beta-catenina; su perdida activa Wnt en cancer colorrectal. | Evento iniciador de la secuencia adenoma-carcinoma. | Kinzler & Vogelstein, Cell 1996 |
| `ONC-047` | **VHL** | supresor | Marca HIF-alpha para degradacion; su perdida activa la respuesta hipoxica. | Diana via HIF-2alpha (belzutifan) en carcinoma renal. | Kaelin, Nat Rev Cancer 2008 |
| `ONC-048` | **BRCA1** | supresor | Esencial para la reparacion por recombinacion homologa de roturas de doble cadena. | Letalidad sintetica con inhibidores de PARP. | Miki et al., Science 1994 |
| `ONC-049` | **BRCA2** | supresor | Carga RAD51 en la recombinacion homologa; su perdida causa inestabilidad genomica. | Letalidad sintetica con inhibidores de PARP. | Wooster et al., Nature 1995 |
| `ONC-050` | **CDKN2A (p16INK4a)** | supresor | Inhibidor de CDK4/6 que mantiene a RB activo; se inactiva por delecion o metilacion. | Nexo con inhibidores de CDK4/6. | Serrano et al., Nature 1993 |
| `ONC-051` | **NF1** | supresor | GAP que apaga RAS; su perdida activa la via MAPK (neurofibromatosis 1). | Contexto de dependencia de MEK. | Cichowski & Jacks, Cell 2001 |
| `ONC-052` | **NF2 (Merlin)** | supresor | Activa la via Hippo y frena la proliferacion; mutado en schwannomas y mesotelioma. | Nexo con la via Hippo-YAP. | McClatchey & Giovannini, Genes Dev 2005 |
| `ONC-053` | **STK11 (LKB1)** | supresor | Cinasa activadora de AMPK; su perdida desregula metabolismo y mTOR. | Marca resistencia a inmunoterapia en pulmon. | Shackelford & Shaw, Nat Rev Cancer 2009 |
| `ONC-054` | **SMAD4 (DPC4)** | supresor | Mediador central de TGF-beta; su perdida elimina senales antiproliferativas. | Perdida frecuente en cancer de pancreas. | Hahn et al., Science 1996 |
| `ONC-055` | **WT1** | supresor | Factor de transcripcion del desarrollo renal; su perdida causa tumor de Wilms. | Biomarcador y diana inmunologica. | Call et al., Cell 1990 |
| `ONC-056` | **TSC1/TSC2** | supresor | Complejo GAP de Rheb que reprime mTORC1; su perdida hiperactiva mTOR. | Diana de rapalogos (esclerosis tuberosa). | Crino et al., NEJM 2006 |
| `ONC-057` | **MEN1 (menin)** | supresor | Andamiaje epigenetico; su perdida causa neoplasia endocrina multiple tipo 1. | Diana emergente de inhibidores de menin. | Chandrasekharappa et al., Science 1997 |
| `ONC-058` | **PTCH1** | supresor | Receptor que reprime la via Hedgehog; su perdida la activa (carcinoma basocelular). | Nexo con inhibidores de Hedgehog (vismodegib). | Hahn et al., Cell 1996 |
| `ONC-059` | **ARID1A (SWI/SNF)** | supresor | Subunidad del remodelador de cromatina BAF; mutada en multiples tumores. | Diana de vulnerabilidades sinteticas (EZH2). | Wu & Roberts, Nat Rev Cancer 2011 |
| `ONC-060` | **VHL-independent tumor suppressor loss** | marco | La perdida de supresores define dependencias explotables por letalidad sintetica. | Marco general de las vulnerabilidades tumorales. | Kaelin, Nat Rev Cancer 2005 |

[volver al indice](#indice)

## Inestabilidad genomica y reparacion del ADN
<a id="inestabilidad-genomica-y-reparacion-del-adn"></a>

*Capa: molecular | 18 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ONC-061` | **Mismatch repair deficiency (dMMR)** | proceso | Fallo del sistema de reparacion de emparejamientos erroneos (MLH1, MSH2, MSH6, PMS2). | Predice respuesta a inmunoterapia (MSI-H). | Kunkel & Erie, Annu Rev Biochem 2005 |
| `ONC-062` | **Microsatellite instability (MSI)** | biomarcador | Hipermutabilidad de microsatelites por deficiencia de MMR. | Biomarcador tumor-agnostico de checkpoints. | Boland & Goel, Gastroenterology 2010 |
| `ONC-063` | **Homologous recombination deficiency (HRD)** | proceso | Incapacidad de reparar roturas de doble cadena con fidelidad (BRCA1/2, PALB2). | Marca sensibilidad a PARP y platino. | Lord & Ashworth, Nature 2016 |
| `ONC-064` | **PARP and synthetic lethality** | diana | PARP repara roturas de cadena simple; su inhibicion es letal en celulas HRD. | Paradigma de letalidad sintetica (olaparib). | Bryant et al., Nature 2005; Farmer et al., Nature 2005 |
| `ONC-065` | **Non-homologous end joining (NHEJ)** | proceso | Reparacion rapida pero propensa a error de roturas de doble cadena. | Contexto de radiosensibilidad y de reparacion tumoral. | Lieber, Annu Rev Biochem 2010 |
| `ONC-066` | **MGMT promoter methylation** | biomarcador | El silenciamiento de MGMT reduce la reparacion de aductos de alquilacion. | Predice respuesta a temozolomida en glioblastoma. | Hegi et al., NEJM 2005 |
| `ONC-067` | **Mutational signatures** | marco | Patrones de mutacion que reflejan procesos mutagenicos (UV, tabaco, APOBEC). | Trazan etiologia y vulnerabilidades. | Alexandrov et al., Nature 2013 |
| `ONC-068` | **APOBEC mutagenesis** | proceso | Citidina-desaminasas que introducen mutaciones agrupadas (kataegis). | Fuente de heterogeneidad y neoantigenos. | Roberts et al., Nat Genet 2013 |
| `ONC-069` | **Aneuploidy / chromosomal instability** | proceso | Ganancia y perdida de cromosomas por errores mitoticos que remodelan el genoma. | Marca agresividad; diana de checkpoints mitoticos. | Weaver & Cleveland, Cancer Cell 2006 |
| `ONC-070` | **Chromothripsis** | proceso | Fragmentacion y reensamblaje catastrofico de cromosomas en un solo evento. | Genera amplicones y fusiones oncogenicas. | Stephens et al., Cell 2011 |
| `ONC-071` | **Tumor mutational burden (TMB)** | biomarcador | Numero de mutaciones somaticas por megabase del exoma tumoral. | Biomarcador de respuesta a inmunoterapia. | Chan et al., Ann Oncol 2019 |
| `ONC-072` | **Replication stress** | proceso | Horquillas de replicacion inestables por oncogenes que generan dano genomico. | Diana de inhibidores de ATR, CHK1, WEE1. | Macheret & Halazonetis, Annu Rev Pathol 2015 |
| `ONC-073` | **ATM / ATR DNA damage signaling** | diana | Cinasas maestras que coordinan la respuesta al dano del ADN. | Diana de inhibidores de ATR/ATM (radiosensibilizacion). | Ciccia & Elledge, Mol Cell 2010 |
| `ONC-074` | **Base excision repair (BER)** | proceso | Repara bases danadas u oxidadas; su inhibicion potencia dano genotoxico. | Contexto del mecanismo de PARP. | Krokan & Bjoras, Cold Spring Harb Perspect Biol 2013 |
| `ONC-075` | **Nucleotide excision repair (NER)** | proceso | Elimina lesiones voluminosas (aductos de UV, cisplatino). | Modula resistencia a platinos. | Marteijn et al., Nat Rev Mol Cell Biol 2014 |
| `ONC-076` | **Telomere maintenance (TERT / ALT)** | proceso | Mantenimiento telomerico por telomerasa o por recombinacion (ALT). | Confiere inmortalidad replicativa; diana conceptual. | Shay & Wright, Nat Rev Genet 2019 |
| `ONC-077` | **Loss of heterozygosity (LOH)** | proceso | Perdida del alelo remanente que desenmascara mutaciones de supresores. | Segundo golpe del modelo de Knudson. | Knudson, PNAS 1971 |
| `ONC-078` | **BRCAness phenotype** | marco | Tumores sin mutacion BRCA que fenocopian el defecto de recombinacion homologa. | Amplia la poblacion candidata a PARP/platino. | Lord & Ashworth, Nat Rev Cancer 2016 |

[volver al indice](#indice)

## Vias de senalizacion oncogenica
<a id="vias-de-senalizacion-oncogenica"></a>

*Capa: pathway | 20 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ONC-079` | **RTK-RAS-MAPK pathway** | via | Cascada de receptores tirosina-cinasa a RAS-RAF-MEK-ERK que dirige proliferacion. | Via mas frecuentemente alterada; multiples dianas. | Samatar & Poulikakos, Nat Rev Drug Discov 2014 |
| `ONC-080` | **RAF-MEK-ERK cascade** | via | Modulo de cinasas aguas abajo de RAS que transmite la senal proliferativa al nucleo. | Diana de inhibidores de BRAF y MEK combinados. | Roberts & Der, Oncogene 2007 |
| `ONC-081` | **PI3K-AKT-mTOR pathway** | via | Eje de supervivencia, crecimiento y metabolismo activado por PI3K. | Diana de inhibidores de PI3K, AKT y mTOR. | Fruman et al., Cell 2017 |
| `ONC-082` | **mTORC1 signaling** | via | Integra nutrientes y factores de crecimiento para activar sintesis proteica. | Diana de rapalogos (everolimus, temsirolimus). | Saxton & Sabatini, Cell 2017 |
| `ONC-083` | **WNT / beta-catenin pathway** | via | Estabiliza beta-catenina que activa programas de auto-renovacion (colorrectal). | Diana emergente (tankyrasa, porcupina). | Clevers & Nusse, Cell 2012 |
| `ONC-084` | **Hedgehog pathway** | via | Via del desarrollo (PTCH-SMO-GLI) reactivada en basocelular y meduloblastoma. | Diana de vismodegib y sonidegib (SMO). | Ng & Curran, Nat Rev Cancer 2011 |
| `ONC-085` | **Notch signaling** | via | Senal de contacto con papel dual (oncogen en T-ALL, supresor en piel). | Diana de inhibidores de gamma-secretasa. | Aster et al., Annu Rev Pathol 2017 |
| `ONC-086` | **JAK-STAT pathway** | via | Transduce senales de citocinas a factores STAT que activan proliferacion. | Diana de ruxolitinib en mieloproliferativos. | O'Shea et al., Cell 2013 |
| `ONC-087` | **TGF-beta signaling** | via | Antiproliferativo temprano y prometastasico tardio (rol dual). | Diana con efecto dependiente del estadio. | Massague, Cell 2008 |
| `ONC-088` | **NF-kB pathway** | via | Factor de transcripcion de supervivencia e inflamacion activado en muchos tumores. | Nexo entre inflamacion y cancer. | Karin, Nature 2006 |
| `ONC-089` | **Hippo-YAP/TAZ pathway** | via | Controla tamano de organo; su inactivacion libera a YAP/TAZ prooncogenicos. | Diana emergente (mesotelioma, TEAD). | Zanconato et al., Cancer Cell 2016 |
| `ONC-090` | **HIF hypoxia pathway** | via | Respuesta a hipoxia (HIF-1/2) que induce angiogenesis y metabolismo glucolitico. | Diana de belzutifan (HIF-2alpha). | Semenza, Cell 2012 |
| `ONC-091` | **p53 network** | via | Red de respuesta a estres que decide arresto, senescencia o apoptosis. | Diana de inhibidores de MDM2 y reactivadores de p53. | Vousden & Prives, Cell 2009 |
| `ONC-092` | **RB-E2F axis** | via | Punto de restriccion G1-S controlado por fosforilacion de RB via CDK4/6. | Diana de inhibidores de CDK4/6 (palbociclib). | Dyson, Genes Dev 1998 |
| `ONC-093` | **MYC transcriptional program** | via | MYC amplifica globalmente la transcripcion de genes de crecimiento. | Diana de BET (indirecta) y de sintesis letal. | Dang, Cell 2012 |
| `ONC-094` | **Estrogen receptor signaling** | via | Senal hormonal que impulsa cancer de mama ER+. | Diana de tamoxifeno, inhibidores de aromatasa, SERD. | Jordan, Nat Rev Drug Discov 2003 |
| `ONC-095` | **Androgen receptor signaling** | via | Senal androgenica que dirige el cancer de prostata. | Diana de abiraterona y enzalutamida. | Watson et al., Nat Rev Cancer 2015 |
| `ONC-096` | **Integrin / FAK adhesion signaling** | via | Senal de adhesion a matriz que regula supervivencia y migracion. | Diana de inhibidores de FAK. | Desgrosellier & Cheresh, Nat Rev Cancer 2010 |
| `ONC-097` | **Autocrine growth factor loops** | proceso | El tumor produce y responde a sus propios factores de crecimiento. | Racional del bloqueo de ligando y receptor. | Sporn & Roberts, Nature 1985 |
| `ONC-098` | **Signaling pathway crosstalk and feedback** | marco | La diafonia y los bucles de retroalimentacion generan resistencia adaptativa. | Racional de combinaciones dirigidas. | Lito et al., Cancer Cell 2013 |

[volver al indice](#indice)

## Ciclo celular y puntos de control
<a id="ciclo-celular-y-puntos-de-control"></a>

*Capa: cellular | 14 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ONC-099` | **Cell cycle deregulation** | proceso | Perdida del control ordenado de G1-S-G2-M que permite proliferacion aberrante. | Diana central de la terapia antiproliferativa. | Hanahan & Weinberg, Cell 2011 |
| `ONC-100` | **CDK4/6-Cyclin D-RB** | diana | Complejo que fosforila RB e inicia la entrada en el ciclo. | Diana de palbociclib, ribociclib, abemaciclib. | Sherr et al., Cancer Discov 2016 |
| `ONC-101` | **CDK2-Cyclin E** | diana | Impulsa la transicion G1-S; su amplificacion causa resistencia a CDK4/6. | Diana emergente de inhibidores de CDK2. | Hwang & Clurman, Oncogene 2005 |
| `ONC-102` | **G1/S restriction point** | proceso | Punto de compromiso irreversible con la division celular. | Nodo de control explotado por inhibidores de CDK. | Pardee, PNAS 1974 |
| `ONC-103` | **G2/M DNA damage checkpoint** | proceso | Detiene la mitosis ante dano no reparado (ATR-CHK1-WEE1). | Diana de inhibidores de WEE1 (adavosertib). | Kastan & Bartek, Nature 2004 |
| `ONC-104` | **Spindle assembly checkpoint (SAC)** | proceso | Asegura la correcta union cromosoma-huso antes de la anafase. | Diana de inhibidores de cinasas mitoticas. | Musacchio & Salmon, Nat Rev Mol Cell Biol 2007 |
| `ONC-105` | **Aurora kinases** | diana | Cinasas mitoticas (A/B) que regulan huso y citocinesis. | Diana de inhibidores de Aurora. | Carmena & Earnshaw, Nat Rev Mol Cell Biol 2003 |
| `ONC-106` | **Polo-like kinase 1 (PLK1)** | diana | Regula entrada y progresion mitotica. | Diana de inhibidores de PLK1. | Strebhardt, Nat Rev Drug Discov 2010 |
| `ONC-107` | **WEE1 kinase** | diana | Frena CDK1 en G2; su inhibicion fuerza mitosis con dano y catastrofe. | Diana en tumores con p53 mutado. | Matheson et al., Trends Pharmacol Sci 2016 |
| `ONC-108` | **CHK1 / CHK2 checkpoint kinases** | diana | Transductores del checkpoint de dano que detienen el ciclo. | Diana de inhibidores de CHK1 (con genotoxicos). | Zhang & Hunter, Int J Cancer 2014 |
| `ONC-109` | **MDM2-p53 feedback** | diana | MDM2 ubiquitina y degrada p53; su inhibicion reactiva p53 nativo. | Diana de inhibidores de MDM2 (nutlins). | Wade et al., Nat Rev Cancer 2013 |
| `ONC-110` | **Mitotic catastrophe** | proceso | Muerte por division aberrante ante checkpoints defectuosos y dano. | Efecto de antimitoticos y radiacion. | Vitale et al., Nat Rev Mol Cell Biol 2011 |
| `ONC-111` | **Cyclin-dependent kinase inhibitors (p21/p27)** | supresor | Inhibidores endogenos (CIP/KIP) que frenan el ciclo; su perdida lo libera. | Nodo de control frecuentemente inactivado. | Sherr & Roberts, Genes Dev 1999 |
| `ONC-112` | **Centrosome amplification** | proceso | Exceso de centrosomas que causa mitosis multipolar e inestabilidad. | Diana de inhibidores de agrupamiento centrosomal. | Nigg, Nat Rev Cancer 2002 |

[volver al indice](#indice)

## Evasion de la muerte celular
<a id="evasion-de-la-muerte-celular"></a>

*Capa: cellular | 16 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ONC-113` | **Apoptosis evasion** | proceso | Desactivacion de la muerte celular programada que sostiene la supervivencia tumoral. | Diana de restauracion de la apoptosis. | Hanahan & Weinberg, Cell 2011 |
| `ONC-114` | **Intrinsic (mitochondrial) apoptosis** | proceso | Via de la permeabilizacion mitocondrial controlada por la familia BCL-2. | Diana de mimeticos BH3. | Green & Llambi, Cold Spring Harb Perspect Biol 2015 |
| `ONC-115` | **BCL-2 / BCL-xL / MCL-1** | diana | Proteinas anti-apoptoticas que secuestran a los efectores de muerte. | Diana de venetoclax (BCL-2) y anti-MCL-1. | Adams & Cory, Nat Rev Cancer 2016 |
| `ONC-116` | **BAX / BAK effectors** | proceso | Efectores que forman poros en la mitocondria liberando citocromo c. | Nodo terminal de la apoptosis intrinseca. | Green & Llambi, Cold Spring Harb Perspect Biol 2015 |
| `ONC-117` | **BH3-only proteins (BIM, PUMA, NOXA)** | proceso | Sensores proapoptoticos que activan BAX/BAK o neutralizan anti-apoptoticos. | Base racional de los mimeticos BH3. | Adams & Cory, Nat Rev Cancer 2016 |
| `ONC-118` | **Extrinsic (death receptor) apoptosis** | proceso | Via de receptores de muerte (FAS, TRAIL) que activa caspasa-8. | Diana de agonistas de TRAIL (historicamente dificil). | Ashkenazi, Nat Rev Cancer 2002 |
| `ONC-119` | **Caspase cascade** | proceso | Proteasas que ejecutan la desmantelacion ordenada de la celula. | Efector final de multiples vias de muerte. | Taylor et al., Nat Rev Mol Cell Biol 2008 |
| `ONC-120` | **Autophagy (dual role in cancer)** | proceso | Reciclaje que suprime tumores temprano pero sostiene tumores establecidos. | Diana con efecto dependiente del contexto. | White, Nat Rev Cancer 2012 |
| `ONC-121` | **Ferroptosis** | proceso | Muerte por peroxidacion lipidica dependiente de hierro (eje GPX4-glutation). | Diana emergente en tumores resistentes. | Stockwell et al., Cell 2017 |
| `ONC-122` | **Necroptosis** | proceso | Muerte programada litica via RIPK1/RIPK3-MLKL con senal inmunogenica. | Diana emergente con potencial inmunoestimulante. | Pasparakis & Vandenabeele, Nature 2015 |
| `ONC-123` | **Immunogenic cell death (ICD)** | proceso | Muerte que libera senales (calreticulina, HMGB1) y activa inmunidad antitumoral. | Racional de sinergias quimio-inmunoterapia. | Galluzzi et al., Nat Rev Immunol 2017 |
| `ONC-124` | **Anoikis resistance** | proceso | Resistencia a la apoptosis por perdida de anclaje que permite diseminacion. | Habilita la supervivencia de celulas circulantes. | Paoli et al., Biochim Biophys Acta 2013 |
| `ONC-125` | **Survivin (IAP family)** | diana | Inhibidor de apoptosis sobreexpresado que bloquea caspasas. | Diana y biomarcador pronostico. | Altieri, Nat Rev Cancer 2008 |
| `ONC-126` | **p53-mediated apoptosis loss** | proceso | La perdida de p53 elimina una via clave de muerte ante estres oncogenico. | Restauracion de p53 como estrategia. | Vousden & Prives, Cell 2009 |
| `ONC-127` | **Cellular stress adaptation (UPR)** | proceso | La respuesta a proteinas mal plegadas permite sobrevivir al estres tumoral. | Diana de inhibidores del proteasoma en mieloma. | Wang & Kaufman, Nat Rev Cancer 2014 |
| `ONC-128` | **Cytochrome c / apoptosome** | proceso | Plataforma que activa la caspasa-9 tras la salida de citocromo c. | Nodo de amplificacion de la apoptosis intrinseca. | Riedl & Salvesen, Nat Rev Mol Cell Biol 2007 |

[volver al indice](#indice)

## Inmortalidad replicativa y telomeros
<a id="inmortalidad-replicativa-y-telomeros"></a>

*Capa: cellular | 8 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ONC-129` | **Replicative immortality** | proceso | Capacidad de division ilimitada al superar la senescencia y la crisis. | Hallmark clasico del cancer. | Hanahan & Weinberg, Cell 2011 |
| `ONC-130` | **Telomerase (TERT) reactivation** | diana | Reactivacion de la transcriptasa inversa que elonga telomeros. | Presente en ~90% de tumores; diana conceptual. | Shay & Wright, Nat Rev Genet 2019 |
| `ONC-131` | **TERT promoter mutations** | biomarcador | Mutaciones del promotor que reactivan TERT (melanoma, glioma, vejiga). | Biomarcador de reactivacion telomerica. | Huang et al., Science 2013 |
| `ONC-132` | **Alternative lengthening of telomeres (ALT)** | proceso | Mantenimiento telomerico por recombinacion, independiente de telomerasa. | Presente en sarcomas y gliomas ATRX-mutados. | Cesare & Reddel, Nat Rev Genet 2010 |
| `ONC-133` | **Replicative senescence barrier** | proceso | Barrera antitumoral por acortamiento telomerico que el cancer debe superar. | Su evasion es requisito de la transformacion. | Campisi, Cell 2005 |
| `ONC-134` | **Telomere crisis** | proceso | Fusiones cromosomicas por telomeros criticamente cortos que generan inestabilidad. | Fuente de reordenamientos oncogenicos. | Maser & DePinho, Science 2002 |
| `ONC-135` | **Shelterin complex** | proceso | Complejo protector del telomero (TRF1/2, POT1) alterado en algunos tumores. | Nexo con predisposicion (mutaciones POT1). | de Lange, Genes Dev 2005 |
| `ONC-136` | **ATRX / DAXX loss** | proceso | Perdida del deposito de histona H3.3 que se asocia al fenotipo ALT. | Biomarcador de tumores ALT. | Heaphy et al., Science 2011 |

[volver al indice](#indice)

## Metabolismo tumoral
<a id="metabolismo-tumoral"></a>

*Capa: molecular | 16 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ONC-137` | **Warburg effect (aerobic glycolysis)** | proceso | Preferencia por la glucolisis aun con oxigeno, para biosintesis rapida. | Base del diagnostico por PET-FDG; diana metabolica. | Vander Heiden et al., Science 2009 |
| `ONC-138` | **Glutaminolysis** | proceso | Uso de glutamina como fuente de carbono y nitrogeno anaplerotica. | Diana de inhibidores de glutaminasa. | Wise & Thompson, Trends Biochem Sci 2010 |
| `ONC-139` | **IDH1/IDH2 mutations and 2-HG** | diana | Mutaciones que producen el oncometabolito 2-hidroxiglutarato, que altera la epigenetica. | Diana de ivosidenib (IDH1) y enasidenib (IDH2). | Dang et al., Nature 2009 |
| `ONC-140` | **HIF-1alpha metabolic switch** | proceso | Factor de hipoxia que induce transportadores de glucosa y enzimas glucoliticas. | Nexo hipoxia-metabolismo-angiogenesis. | Semenza, Nat Rev Cancer 2003 |
| `ONC-141` | **Lactate dehydrogenase A (LDHA)** | diana | Convierte piruvato en lactato sosteniendo la glucolisis aerobia. | Diana metabolica en investigacion. | Doherty & Cleveland, J Clin Invest 2013 |
| `ONC-142` | **Lipogenesis (FASN)** | diana | Sintesis de acidos grasos de novo para membranas y senalizacion. | Diana de inhibidores de FASN. | Menendez & Lupu, Nat Rev Cancer 2007 |
| `ONC-143` | **One-carbon / folate metabolism** | diana | Aporta unidades de carbono para nucleotidos y metilacion. | Diana clasica de antifolatos (metotrexato). | Locasale, Nat Rev Cancer 2013 |
| `ONC-144` | **Serine-glycine biosynthesis (PHGDH)** | diana | Ruta biosintetica amplificada que alimenta el metabolismo de un carbono. | Diana metabolica emergente. | Possemato et al., Nature 2011 |
| `ONC-145` | **Pentose phosphate pathway** | proceso | Genera NADPH y ribosa para biosintesis y defensa antioxidante. | Soporta proliferacion y redox tumoral. | Patra & Hay, Trends Biochem Sci 2014 |
| `ONC-146` | **MYC-driven metabolic reprogramming** | proceso | MYC coordina glucolisis, glutaminolisis y biogenesis ribosomal. | Nexo oncogen-metabolismo. | Stine et al., Cancer Discov 2015 |
| `ONC-147` | **AMPK-LKB1 energy sensing** | proceso | Sensor energetico que frena crecimiento; su perdida desregula metabolismo. | Nexo con metformina y STK11. | Shackelford & Shaw, Nat Rev Cancer 2009 |
| `ONC-148` | **Glucose transporters (GLUT1)** | biomarcador | Sobreexpresion de transportadores que aumenta la captacion de glucosa. | Base de la senal en PET-FDG. | Vander Heiden et al., Science 2009 |
| `ONC-149` | **Oxidative phosphorylation dependence** | proceso | Subgrupos tumorales (algunas leucemias) dependen de la respiracion mitocondrial. | Diana de inhibidores de OXPHOS. | Ashton et al., Clin Cancer Res 2018 |
| `ONC-150` | **Reactive oxygen species (ROS) balance** | proceso | Niveles elevados de ROS con defensa antioxidante reforzada (NRF2). | Ventana terapeutica redox. | Gorrini et al., Nat Rev Drug Discov 2013 |
| `ONC-151` | **Autophagy-supported metabolism** | proceso | La autofagia recicla nutrientes para sostener tumores con estres metabolico. | Diana en tumores dependientes de autofagia. | White, Nat Rev Cancer 2012 |
| `ONC-152` | **Oncometabolites (2-HG, fumarate, succinate)** | marco | Metabolitos acumulados que inhiben dioxigenasas y remodelan la epigenetica. | Nexo metabolismo-epigenetica (IDH, FH, SDH). | Yang et al., Nat Rev Cancer 2012 |

[volver al indice](#indice)

## Angiogenesis tumoral
<a id="angiogenesis-tumoral"></a>

*Capa: tissue | 12 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ONC-153` | **Angiogenic switch** | proceso | Transicion a un fenotipo pro-angiogenico que permite crecer mas alla de la difusion. | Momento diana de la terapia antiangiogenica. | Hanahan & Folkman, Cell 1996 |
| `ONC-154` | **VEGF / VEGFR axis** | diana | Principal eje pro-angiogenico que induce proliferacion y permeabilidad endotelial. | Diana de bevacizumab y de inhibidores de VEGFR. | Ferrara et al., Nat Med 2003 |
| `ONC-155` | **Hypoxia-driven angiogenesis (HIF)** | proceso | La hipoxia estabiliza HIF que transcribe VEGF y otros factores. | Nexo hipoxia-vascularizacion. | Semenza, Nat Rev Cancer 2003 |
| `ONC-156` | **Tumor vessel abnormality** | proceso | Vasos tumorales tortuosos y permeables que dificultan la perfusion y el farmaco. | Racional de la normalizacion vascular. | Jain, Science 2005 |
| `ONC-157` | **Vascular normalization** | marco | La antiangiogenesis juiciosa puede normalizar vasos y mejorar la entrega de farmacos. | Optimiza combinaciones con quimioterapia. | Jain, Nat Med 2001 |
| `ONC-158` | **PDGF / pericyte recruitment** | proceso | Reclutamiento de pericitos que estabiliza la neovasculatura tumoral. | Diana de doble bloqueo VEGF-PDGF. | Bergers & Benjamin, Nat Rev Cancer 2003 |
| `ONC-159` | **FGF angiogenic signaling** | proceso | Via alternativa de angiogenesis implicada en resistencia a anti-VEGF. | Diana de inhibidores multicinasa. | Turner & Grose, Nat Rev Cancer 2010 |
| `ONC-160` | **Angiopoietin-Tie2 axis** | diana | Regula estabilidad y remodelado vascular junto a VEGF. | Diana de bloqueo dual Ang2-VEGF. | Augustin et al., Nat Rev Mol Cell Biol 2009 |
| `ONC-161` | **Vasculogenic mimicry** | proceso | Formacion de canales por celulas tumorales que imitan vasos. | Mecanismo de resistencia antiangiogenica. | Maniotis et al., Am J Pathol 1999 |
| `ONC-162` | **Lymphangiogenesis (VEGF-C/D)** | proceso | Formacion de vasos linfaticos que facilita la diseminacion ganglionar. | Nexo con metastasis linfatica. | Stacker et al., Nat Rev Cancer 2014 |
| `ONC-163` | **Endothelial tip / stalk cells** | proceso | Especializacion endotelial (Notch-DLL4) que guia el brote vascular. | Diana de la senal DLL4-Notch. | Potente et al., Cell 2011 |
| `ONC-164` | **Anti-angiogenic resistance** | marco | Evasion por vias alternativas, invasion o cooptacion vascular. | Explica beneficio limitado de anti-VEGF en monoterapia. | Bergers & Hanahan, Nat Rev Cancer 2008 |

[volver al indice](#indice)

## Invasion y metastasis
<a id="invasion-y-metastasis"></a>

*Capa: tissue | 18 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ONC-165` | **Invasion-metastasis cascade** | proceso | Secuencia invasion-intravasacion-supervivencia-extravasacion-colonizacion. | Causa del ~90% de la mortalidad por cancer. | Lambert et al., Cell 2017 |
| `ONC-166` | **Epithelial-mesenchymal transition (EMT)** | proceso | Programa que confiere motilidad e invasividad perdiendo adhesion epitelial. | Diana conceptual de la diseminacion. | Thiery et al., Cell 2009 |
| `ONC-167` | **E-cadherin loss** | proceso | Perdida de la adhesion celula-celula que libera a la celula invasora. | Supresor de la invasion; evento clave de EMT. | Berx & van Roy, Cold Spring Harb Perspect Biol 2009 |
| `ONC-168` | **Matrix metalloproteinases (MMPs)** | diana | Proteasas que degradan la matriz extracelular abriendo paso a la invasion. | Diana historica (con ensayos decepcionantes). | Kessenbrock et al., Cell 2010 |
| `ONC-169` | **Invadopodia** | proceso | Protrusiones ricas en proteasas que degradan matriz localmente. | Estructura clave de la invasion. | Murphy & Courtneidge, Nat Rev Mol Cell Biol 2011 |
| `ONC-170` | **Intravasation** | proceso | Entrada de celulas tumorales en la circulacion sanguinea o linfatica. | Paso limitante de la diseminacion. | Reymond et al., Nat Rev Cancer 2013 |
| `ONC-171` | **Circulating tumor cells (CTCs)** | biomarcador | Celulas tumorales en sangre, a menudo en agrupaciones mas metastasicas. | Biomarcador de biopsia liquida. | Aceto et al., Cell 2014 |
| `ONC-172` | **Extravasation** | proceso | Salida de la circulacion e invasion del parenquima del organo distante. | Paso de la colonizacion metastasica. | Reymond et al., Nat Rev Cancer 2013 |
| `ONC-173` | **Pre-metastatic niche** | proceso | Acondicionamiento del organo diana por factores y exosomas antes de la llegada. | Diana de intervencion preventiva. | Peinado et al., Nat Rev Cancer 2017 |
| `ONC-174` | **Metastatic organotropism** | proceso | Preferencia de cada tumor por organos concretos ('seed and soil'). | Explicado en parte por integrinas de exosomas. | Hoshino et al., Nature 2015 |
| `ONC-175` | **Tumor cell dormancy** | proceso | Celulas diseminadas que permanecen latentes durante anos antes de recaer. | Diana para prevenir recaidas tardias. | Sosa et al., Nat Rev Cancer 2014 |
| `ONC-176` | **Metastatic colonization** | proceso | Reanudacion del crecimiento en el organo distante, paso mas ineficiente. | Cuello de botella de la metastasis. | Massague & Obenauf, Nature 2016 |
| `ONC-177` | **Mesenchymal-epithelial transition (MET)** | proceso | Reversion a fenotipo epitelial necesaria para colonizar el organo diana. | Complemento de la EMT en la cascada. | Thiery et al., Cell 2009 |
| `ONC-178` | **Collective cell migration** | proceso | Migracion invasiva en grupos cohesivos liderados por celulas de vanguardia. | Modo de invasion alternativo a la individual. | Friedl & Gilmour, Nat Rev Mol Cell Biol 2009 |
| `ONC-179` | **Exosomes in metastasis** | proceso | Vesiculas que preparan nichos y transfieren senales prometastasicas. | Biomarcadores y diana emergente. | Hoshino et al., Nature 2015 |
| `ONC-180` | **Seed and soil hypothesis** | marco | La metastasis depende de la compatibilidad entre celula tumoral y microambiente. | Marco clasico del tropismo metastasico. | Paget, Lancet 1889 |
| `ONC-181` | **Perineural / lymphovascular invasion** | biomarcador | Invasion de nervios y vasos como via de diseminacion y factor pronostico. | Parametro histopatologico de riesgo. | Liebig et al., Cancer 2009 |
| `ONC-182` | **TWIST / SNAIL / ZEB EMT factors** | diana | Factores de transcripcion maestros que orquestan la EMT. | Dianas conceptuales de la invasion. | De Craene & Berx, Nat Rev Cancer 2013 |

[volver al indice](#indice)

## Microambiente tumoral
<a id="microambiente-tumoral"></a>

*Capa: tissue | 14 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ONC-183` | **Tumor microenvironment (TME)** | marco | Ecosistema de celulas estromales, inmunes, vasos y matriz que rodea al tumor. | Diana de multiples estrategias combinadas. | Quail & Joyce, Nat Med 2013 |
| `ONC-184` | **Cancer-associated fibroblasts (CAFs)** | proceso | Fibroblastos activados que remodelan matriz y secretan factores protumorales. | Diana estromal emergente. | Sahai et al., Nat Rev Cancer 2020 |
| `ONC-185` | **Tumor-associated macrophages (TAMs)** | proceso | Macrofagos reprogramados (M2) que favorecen angiogenesis e inmunosupresion. | Diana de bloqueo CSF1R y reprogramacion. | Mantovani et al., Nat Rev Clin Oncol 2017 |
| `ONC-186` | **Myeloid-derived suppressor cells (MDSCs)** | proceso | Celulas mieloides inmaduras que suprimen la respuesta de linfocitos T. | Diana de la inmunosupresion mieloide. | Gabrilovich, Cancer Immunol Res 2017 |
| `ONC-187` | **Regulatory T cells (Tregs)** | proceso | Linfocitos T supresores que mantienen tolerancia y frenan la inmunidad antitumoral. | Diana de deplecion selectiva. | Togashi et al., Nat Rev Clin Oncol 2019 |
| `ONC-188` | **Extracellular matrix remodeling** | proceso | Deposito y entrecruzamiento (LOX) de matriz que rigidiza y facilita invasion. | Diana de la desmoplasia. | Cox & Erler, Dis Model Mech 2011 |
| `ONC-189` | **Tumor hypoxia** | proceso | Zonas de bajo oxigeno que promueven agresividad, angiogenesis y resistencia. | Factor de radiorresistencia; diana de HIF. | Wilson & Hay, Nat Rev Cancer 2011 |
| `ONC-190` | **Desmoplasia (stromal reaction)** | proceso | Estroma fibroso denso (tipico del pancreas) que limita la entrega de farmacos. | Barrera terapeutica y diana estromal. | Neesse et al., Gut 2011 |
| `ONC-191` | **Immune-excluded and cold tumors** | marco | Tumores con linfocitos ausentes o confinados al estroma, resistentes a checkpoints. | Objetivo de estrategias que 'calientan' el tumor. | Chen & Mellman, Nature 2017 |
| `ONC-192` | **Angiogenic-immune crosstalk** | proceso | VEGF favorece la inmunosupresion; su bloqueo puede potenciar la inmunoterapia. | Racional de combinar anti-VEGF con checkpoints. | Fukumura et al., Nat Rev Clin Oncol 2018 |
| `ONC-193` | **Metabolic competition in the TME** | proceso | Competencia por glucosa que priva a los linfocitos T de energia. | Nexo metabolismo-inmunidad. | Chang et al., Cell 2015 |
| `ONC-194` | **Exosome-mediated TME signaling** | proceso | Vesiculas que reprograman el estroma y el sistema inmune local. | Biomarcadores y diana emergente. | Kalluri, J Clin Invest 2016 |
| `ONC-195` | **Nerve infiltration of the TME** | proceso | Inervacion del tumor que aporta senales trofijas y protumorales. | Diana emergente (neuro-oncologia). | Zahalka & Frenette, Nat Rev Cancer 2020 |
| `ONC-196` | **Complement and coagulation in TME** | proceso | Sistemas del complemento y de coagulacion que modulan inflamacion y trombosis. | Nexo con el estado protrombotico del cancer. | Roumenina et al., Nat Rev Cancer 2019 |

[volver al indice](#indice)

## Inmunologia tumoral y evasion inmune
<a id="inmunologia-tumoral-y-evasion-inmune"></a>

*Capa: tissue | 18 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ONC-197` | **Cancer immunoediting (3 E's)** | marco | Eliminacion, equilibrio y escape que describen la relacion tumor-inmunidad. | Marco conceptual de la inmuno-oncologia. | Schreiber et al., Science 2011 |
| `ONC-198` | **Immune surveillance** | proceso | Vigilancia inmune que reconoce y elimina celulas transformadas. | Base racional de la inmunoterapia. | Dunn et al., Nat Immunol 2002 |
| `ONC-199` | **PD-1 / PD-L1 axis** | diana | Checkpoint que apaga a los linfocitos T; los tumores lo explotan expresando PD-L1. | Diana de nivolumab, pembrolizumab, atezolizumab. | Pardoll, Nat Rev Cancer 2012 |
| `ONC-200` | **CTLA-4 checkpoint** | diana | Freno temprano de la activacion T en el ganglio linfatico. | Diana de ipilimumab. | Leach et al., Science 1996 |
| `ONC-201` | **LAG-3 checkpoint** | diana | Receptor inhibidor coexpresado en linfocitos T exhaustos. | Diana de relatlimab (con anti-PD-1). | Anderson et al., Immunity 2016 |
| `ONC-202` | **TIM-3 / TIGIT checkpoints** | diana | Checkpoints inhibidores adicionales de linfocitos T y NK. | Dianas de nueva generacion en ensayos. | Anderson et al., Immunity 2016 |
| `ONC-203` | **Neoantigens** | biomarcador | Peptidos mutados presentados que el sistema inmune reconoce como extranos. | Base de vacunas y de la respuesta a checkpoints. | Schumacher & Schreiber, Science 2015 |
| `ONC-204` | **MHC class I loss / antigen presentation defects** | proceso | Perdida de HLA o de la maquinaria de presentacion que oculta el tumor. | Mecanismo de resistencia a inmunoterapia. | Garrido et al., Clin Cancer Res 2016 |
| `ONC-205` | **T-cell exhaustion** | proceso | Estado disfuncional de linfocitos T por estimulacion cronica (TOX, PD-1 alto). | Diana de la reinvigoracion con checkpoints. | Wherry & Kurachi, Nat Rev Immunol 2015 |
| `ONC-206` | **Tumor-infiltrating lymphocytes (TILs)** | biomarcador | Linfocitos que infiltran el tumor; su densidad predice pronostico y respuesta. | Base de la puntuacion inmune (Immunoscore). | Galon et al., Science 2006 |
| `ONC-207` | **Interferon-gamma signaling** | proceso | Citocina efectora que induce MHC y PD-L1; su perdida causa resistencia. | Nexo con resistencia (mutaciones JAK1/2). | Zaretsky et al., NEJM 2016 |
| `ONC-208` | **Immunosuppressive cytokines (TGF-beta, IL-10)** | proceso | Citocinas que amortiguan la respuesta inmune antitumoral. | Diana de bloqueo de TGF-beta. | Batlle & Massague, Immunity 2019 |
| `ONC-209` | **Adenosine (CD39-CD73) pathway** | diana | Eje que genera adenosina inmunosupresora en el microambiente. | Diana de inhibidores de CD73 y de A2AR. | Allard et al., Nat Rev Clin Oncol 2020 |
| `ONC-210` | **IDO / tryptophan metabolism** | diana | Enzima que agota triptofano y suprime linfocitos T locales. | Diana de inhibidores de IDO1 (resultados mixtos). | Munn & Mellor, Trends Immunol 2016 |
| `ONC-211` | **NK cell surveillance** | proceso | Celulas NK que eliminan celulas con MHC bajo (missing-self). | Diana de terapias basadas en NK. | Vivier et al., Science 2011 |
| `ONC-212` | **Tertiary lymphoid structures (TLS)** | biomarcador | Agregados linfoides intratumorales asociados a mejor respuesta inmune. | Biomarcador de respuesta a inmunoterapia. | Sautes-Fridman et al., Nat Rev Cancer 2019 |
| `ONC-213` | **Immune checkpoint blockade (concept)** | modalidad | Liberacion de los frenos de los linfocitos T para restaurar la inmunidad antitumoral. | Pilar de la inmuno-oncologia moderna. | Sharma & Allison, Cell 2015 |
| `ONC-214` | **Hyperprogression / immune-related adverse events** | marco | Progresion acelerada o toxicidad autoinmune asociadas a los checkpoints. | Consideraciones de seguridad de la inmunoterapia. | Postow et al., NEJM 2018 |

[volver al indice](#indice)

## Heterogeneidad, plasticidad y celulas madre tumorales
<a id="heterogeneidad-plasticidad-y-celulas-madre-tumorales"></a>

*Capa: cellular | 12 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ONC-215` | **Cancer stem cells (CSCs)** | proceso | Subpoblacion con auto-renovacion capaz de regenerar el tumor. | Diana para prevenir recaidas. | Reya et al., Nature 2001 |
| `ONC-216` | **Intratumoral heterogeneity** | proceso | Diversidad de subclones dentro de un mismo tumor en espacio y tiempo. | Reto para la biopsia y la terapia dirigida. | Marusyk et al., Nat Rev Cancer 2012 |
| `ONC-217` | **Clonal evolution and selection** | proceso | Seleccion de subclones con ventaja bajo presion terapeutica. | Explica la resistencia adquirida. | Greaves & Maley, Nature 2012 |
| `ONC-218` | **Phenotypic plasticity** | proceso | Capacidad de cambiar de estado/identidad celular (hallmark 2022). | Diana emergente de la plasticidad. | Hanahan, Cancer Discov 2022 |
| `ONC-219` | **Drug-tolerant persister cells** | proceso | Celulas que sobreviven al farmaco en un estado reversible de tolerancia. | Reservorio de la recaida; diana de erradicacion. | Sharma et al., Cell 2010 |
| `ONC-220` | **Epigenetic reprogramming (nonmutational)** | proceso | Cambios epigeneticos que confieren fenotipos malignos sin mutacion. | Diana de farmacos epigeneticos. | Flavahan et al., Science 2017 |
| `ONC-221` | **Lineage plasticity / transdifferentiation** | proceso | Cambio de linaje (p.ej. adeno a neuroendocrino) que evade la terapia dirigida. | Mecanismo de resistencia (prostata, pulmon). | Quintanal-Villalonga et al., Nat Rev Clin Oncol 2020 |
| `ONC-222` | **Tumor cell of origin** | marco | La celula que inicia el tumor condiciona su fenotipo y agresividad. | Marco de la clasificacion molecular. | Visvader, Nature 2011 |
| `ONC-223` | **Stochastic vs hierarchical models** | marco | Debate entre tumor jerarquico (CSC) y modelo estocastico clonal. | Marco conceptual de la organizacion tumoral. | Kreso & Dick, Cell Stem Cell 2014 |
| `ONC-224` | **Niche-dependent stemness** | proceso | El microambiente sostiene y regula el estado de celula madre tumoral. | Diana del nicho para eliminar CSC. | Plaks et al., Cell Stem Cell 2015 |
| `ONC-225` | **Epigenetic clock / DNA methylation in cancer** | biomarcador | Alteraciones globales y focales de metilacion que definen subtipos. | Base de la clasificacion epigenetica (gliomas). | Baylin & Jones, Nat Rev Cancer 2011 |
| `ONC-226` | **Polyploidy / giant cancer cells** | proceso | Celulas poliploides gigantes que resisten estres y repueblan el tumor. | Mecanismo emergente de resistencia. | Amend et al., Prostate 2019 |

[volver al indice](#indice)

## Carcinogenos, virus e iniciacion
<a id="carcinogenos-virus-e-iniciacion"></a>

*Capa: meta | 14 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ONC-227` | **Chemical carcinogenesis (initiation-promotion)** | marco | Modelo de iniciacion mutacional seguida de promocion proliferativa. | Base de la carcinogenesis experimental. | Berenblum & Shubik, Br J Cancer 1947 |
| `ONC-228` | **Tobacco smoke carcinogens** | carcinogeno | Mezcla mutagenica (benzopireno, nitrosaminas) causante de multiples tumores. | Firma mutacional caracteristica (C>A). | Alexandrov et al., Science 2016 |
| `ONC-229` | **Ultraviolet radiation** | carcinogeno | La luz UV genera dimeros de pirimidina que causan cancer de piel. | Firma mutacional C>T; base de la fotoproteccion. | Pfeifer et al., Mutat Res 2005 |
| `ONC-230` | **Ionizing radiation** | carcinogeno | Radiacion que provoca roturas de doble cadena y reordenamientos. | Nexo con leucemias y tumores solidos secundarios. | Little, Nat Rev Cancer 2005 |
| `ONC-231` | **Aflatoxin B1** | carcinogeno | Micotoxina que causa la mutacion R249S de TP53 en carcinoma hepatocelular. | Firma mutacional especifica; diana de prevencion. | Bressac et al., Nature 1991 |
| `ONC-232` | **Asbestos** | carcinogeno | Fibras que causan inflamacion cronica y mesotelioma. | Nexo inflamacion-carcinogenesis. | Carbone et al., Nat Rev Cancer 2013 |
| `ONC-233` | **Human papillomavirus (HPV)** | virus | Los oncoproteinas E6/E7 inactivan p53 y RB (cuello uterino, orofaringe). | Prevencion por vacuna; diana E6/E7. | zur Hausen, Nat Rev Cancer 2002 |
| `ONC-234` | **Hepatitis B and C virus (HBV/HCV)** | virus | Infeccion cronica que causa inflamacion, cirrosis y carcinoma hepatocelular. | Prevencion por vacuna (HBV) y antivirales (HCV). | El-Serag, Gastroenterology 2012 |
| `ONC-235` | **Epstein-Barr virus (EBV)** | virus | Virus asociado a linfoma de Burkitt, Hodgkin y carcinoma nasofaringeo. | Biomarcador (ADN de EBV) y diana emergente. | Young & Rickinson, Nat Rev Cancer 2004 |
| `ONC-236` | **Human T-lymphotropic virus 1 (HTLV-1)** | virus | Retrovirus causante de la leucemia/linfoma de celulas T del adulto. | Ejemplo de retrovirus oncogenico humano. | Matsuoka & Jeang, Nat Rev Cancer 2007 |
| `ONC-237` | **Helicobacter pylori** | carcinogeno | Bacteria que causa inflamacion cronica y cancer gastrico (via CagA). | Prevencion por erradicacion antibiotica. | Peek & Blaser, Nat Rev Cancer 2002 |
| `ONC-238` | **Kaposi sarcoma herpesvirus (HHV-8)** | virus | Herpesvirus causante del sarcoma de Kaposi en inmunodepresion. | Nexo cancer-inmunosupresion. | Mesri et al., Nat Rev Cancer 2010 |
| `ONC-239` | **Chronic inflammation and cancer** | marco | La inflamacion cronica aporta mutagenos, factores de crecimiento y angiogenesis. | Racional de la quimioprevencion (AINE). | Coussens & Werb, Nature 2002 |
| `ONC-240` | **Ames test (mutagenicity screen)** | marco | Ensayo bacteriano que estima el potencial mutagenico de un compuesto. | Cribado clasico de carcinogenos. | Ames et al., PNAS 1973 |

[volver al indice](#indice)

## Biomarcadores, diagnostico y estadificacion
<a id="biomarcadores-diagnostico-y-estadificacion"></a>

*Capa: meta | 16 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ONC-241` | **TNM staging system** | marco | Clasifica el tumor por extension (T), ganglios (N) y metastasis (M). | Base del estadiaje y del pronostico. | Brierley et al., UICC TNM 2017 |
| `ONC-242` | **Tumor grade (differentiation)** | biomarcador | Grado de diferenciacion histologica que estima agresividad. | Parametro pronostico clasico. | Rosai, Ackerman's Surgical Pathology 2011 |
| `ONC-243` | **Gleason score (prostate)** | biomarcador | Sistema de gradacion arquitectural del cancer de prostata. | Guia decisiones de tratamiento en prostata. | Epstein et al., Am J Surg Pathol 2016 |
| `ONC-244` | **PSA (prostate-specific antigen)** | biomarcador | Marcador serico usado en cribado y seguimiento del cancer de prostata. | Util pero con sobrediagnostico; uso matizado. | Catalona et al., NEJM 1991 |
| `ONC-245` | **CA-125** | biomarcador | Antigeno serico elevado en cancer de ovario, util en seguimiento. | Monitoriza respuesta y recaida. | Bast et al., NEJM 1983 |
| `ONC-246` | **CEA (carcinoembryonic antigen)** | biomarcador | Marcador serico de seguimiento en cancer colorrectal y otros. | Monitoriza recaida tras cirugia. | Goldenberg et al., JNCI 1976 |
| `ONC-247` | **AFP (alpha-fetoprotein)** | biomarcador | Marcador de carcinoma hepatocelular y tumores germinales. | Diagnostico y seguimiento. | Bruix & Sherman, Hepatology 2011 |
| `ONC-248` | **HER2 status (IHC/FISH)** | biomarcador | Amplificacion/sobreexpresion de HER2 que guia la terapia anti-HER2. | Diagnostico companion de trastuzumab. | Wolff et al., J Clin Oncol 2018 |
| `ONC-249` | **Hormone receptor status (ER/PR)** | biomarcador | Expresion de receptores de estrogeno/progesterona en cancer de mama. | Guia la terapia endocrina. | Allred et al., Mod Pathol 1998 |
| `ONC-250` | **MSI / MMR status** | biomarcador | Inestabilidad de microsatelites o deficiencia de reparacion de emparejamientos. | Predice respuesta a checkpoints (tumor-agnostico). | Le et al., NEJM 2015 |
| `ONC-251` | **Tumor mutational burden (TMB)** | biomarcador | Carga mutacional total que aproxima la neoantigenicidad. | Biomarcador de inmunoterapia. | Chan et al., Ann Oncol 2019 |
| `ONC-252` | **PD-L1 expression** | biomarcador | Expresion de PD-L1 (por IHC) usada para seleccionar inmunoterapia. | Diagnostico companion imperfecto de anti-PD-1. | Patel & Kurzrock, Mol Cancer Ther 2015 |
| `ONC-253` | **Circulating tumor DNA (ctDNA / liquid biopsy)** | biomarcador | ADN tumoral en sangre para genotipado y deteccion de enfermedad residual. | Genotipado no invasivo y monitorizacion. | Wan et al., Nat Rev Cancer 2017 |
| `ONC-254` | **Multigene expression assays (Oncotype DX)** | biomarcador | Firmas de expresion que estiman riesgo de recaida y beneficio de quimioterapia. | Guia la decision de quimioterapia en mama. | Paik et al., NEJM 2004 |
| `ONC-255` | **Companion diagnostics** | marco | Pruebas que identifican al paciente que se beneficia de una terapia dirigida. | Requisito de la medicina de precision. | Jorgensen, Expert Rev Mol Diagn 2015 |
| `ONC-256` | **Minimal residual disease (MRD)** | biomarcador | Deteccion de enfermedad residual por debajo del umbral clinico. | Guia decisiones de consolidacion y recaida. | Pantel & Alix-Panabieres, Nat Rev Clin Oncol 2019 |

[volver al indice](#indice)

## Modalidades terapeuticas
<a id="modalidades-terapeuticas"></a>

*Capa: therapy | 20 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ONC-257` | **Cytotoxic chemotherapy** | modalidad | Farmacos que danan el ADN o el huso para matar celulas en division. | Pilar historico; base de muchos regimenes. | DeVita & Chu, Cancer Res 2008 |
| `ONC-258` | **Alkylating agents** | modalidad | Anaden grupos alquilo al ADN causando entrecruzamientos (ciclofosfamida, temozolomida). | Amplio uso; nexo con MGMT. | Fu et al., Nat Rev Cancer 2012 |
| `ONC-259` | **Antimetabolites** | modalidad | Analogos que bloquean la sintesis de nucleotidos (5-FU, metotrexato, gemcitabina). | Base de multiples regimenes. | Chabner & Roberts, Nat Rev Cancer 2005 |
| `ONC-260` | **Platinum agents** | modalidad | Forman aductos y entrecruzamientos del ADN (cisplatino, carboplatino). | Especial eficacia en tumores HRD. | Kelland, Nat Rev Cancer 2007 |
| `ONC-261` | **Taxanes and vinca alkaloids** | modalidad | Antimicrotubulos que bloquean la mitosis (paclitaxel, vincristina). | Amplio uso en tumores solidos. | Jordan & Wilson, Nat Rev Cancer 2004 |
| `ONC-262` | **Topoisomerase inhibitors** | modalidad | Bloquean topoisomerasas I/II causando roturas del ADN (irinotecan, etoposido). | Componente de regimenes combinados. | Pommier, Nat Rev Cancer 2006 |
| `ONC-263` | **Anthracyclines** | modalidad | Intercalan el ADN e inhiben topoisomerasa II (doxorubicina). | Eficaces pero con cardiotoxicidad. | Minotti et al., Pharmacol Rev 2004 |
| `ONC-264` | **Radiation therapy** | modalidad | Radiacion ionizante que causa dano letal del ADN localizado. | Curativa o paliativa; radiosensibilizadores. | Baskar et al., Int J Med Sci 2012 |
| `ONC-265` | **Targeted small-molecule inhibitors** | modalidad | Inhibidores de cinasas y dianas especificas de la celula tumoral. | Base de la medicina de precision. | Sawyers, Nature 2004 |
| `ONC-266` | **Monoclonal antibodies** | modalidad | Anticuerpos que bloquean receptores o marcan celulas para destruccion. | Terapia dirigida e inmunoterapia. | Scott et al., Nat Rev Cancer 2012 |
| `ONC-267` | **Antibody-drug conjugates (ADCs)** | modalidad | Anticuerpo unido a un citotoxico que se entrega selectivamente a la diana. | Ejemplos: T-DM1, T-DXd, sacituzumab. | Chau et al., Lancet 2019 |
| `ONC-268` | **Immune checkpoint inhibitors** | modalidad | Liberan los frenos de los linfocitos T (anti-PD-1/PD-L1/CTLA-4). | Transformaron el tratamiento de multiples tumores. | Sharma & Allison, Cell 2015 |
| `ONC-269` | **CAR-T cell therapy** | modalidad | Linfocitos T del paciente reprogramados con un receptor quimerico. | Eficaz en neoplasias hematologicas CD19+. | June et al., Science 2018 |
| `ONC-270` | **Bispecific T-cell engagers (BiTE)** | modalidad | Anticuerpos que unen linfocito T y celula tumoral (blinatumomab). | Redirigen la citotoxicidad de linfocitos T. | Bargou et al., Science 2008 |
| `ONC-271` | **Hormone / endocrine therapy** | modalidad | Bloquea senales hormonales que impulsan tumores de mama y prostata. | Base del tratamiento de tumores hormonodependientes. | Jordan, Nat Rev Drug Discov 2003 |
| `ONC-272` | **PARP inhibitors** | modalidad | Explotan la letalidad sintetica en tumores con deficiencia de HR. | Aprobados en ovario, mama, prostata, pancreas. | Lord & Ashworth, Science 2017 |
| `ONC-273` | **Anti-angiogenic therapy** | modalidad | Bloquea la formacion de vasos tumorales (anti-VEGF). | Beneficio modesto; mejor en combinacion. | Jain, Science 2005 |
| `ONC-274` | **Differentiation therapy** | modalidad | Fuerza la maduracion de celulas malignas (ATRA en leucemia promielocitica). | Paradigma curativo en LPA. | Huang et al., Blood 1988 |
| `ONC-275` | **Cancer vaccines** | modalidad | Vacunas que estimulan inmunidad contra antigenos tumorales o neoantigenos. | Preventivas (HPV) y terapeuticas (en desarrollo). | Sahin & Tureci, Science 2018 |
| `ONC-276` | **Oncolytic virotherapy** | modalidad | Virus que lisan selectivamente celulas tumorales e inducen inmunidad (T-VEC). | Modalidad inmunoterapeutica emergente. | Kaufman et al., Nat Rev Drug Discov 2015 |

[volver al indice](#indice)

## Primitivas farmaco -> diana
<a id="primitivas-farmaco-diana"></a>

*Capa: therapy | 26 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ONC-277` | **Imatinib -> BCR-ABL / KIT** | farmaco->diana | Inhibidor de tirosina-cinasa que bloquea la cinasa de fusion BCR-ABL. | Convirtio la LMC en enfermedad cronica; paradigma de terapia dirigida. | Druker et al., NEJM 2001 |
| `ONC-278` | **Trastuzumab -> HER2** | farmaco->diana | Anticuerpo que bloquea el receptor HER2 amplificado. | Estandar en cancer de mama HER2+. | Slamon et al., NEJM 2001 |
| `ONC-279` | **Trastuzumab deruxtecan -> HER2 (ADC)** | farmaco->diana | Conjugado que entrega un inhibidor de topoisomerasa I a celulas HER2. | Activo incluso en tumores HER2-bajo. | Modi et al., NEJM 2022 |
| `ONC-280` | **Rituximab -> CD20** | farmaco->diana | Anticuerpo que marca linfocitos B CD20+ para su destruccion. | Base del tratamiento de linfomas B. | Coiffier et al., NEJM 2002 |
| `ONC-281` | **Bevacizumab -> VEGF-A** | farmaco->diana | Anticuerpo que secuestra VEGF-A bloqueando la angiogenesis. | Uso en colorrectal, pulmon, renal y otros. | Hurwitz et al., NEJM 2004 |
| `ONC-282` | **Erlotinib / gefitinib -> EGFR** | farmaco->diana | Inhibidores de EGFR eficaces en tumores con mutacion activadora. | Estandar en pulmon EGFR-mutado. | Lynch et al., NEJM 2004 |
| `ONC-283` | **Osimertinib -> EGFR T790M** | farmaco->diana | Inhibidor de tercera generacion activo frente a la resistencia T790M. | Estandar de primera linea en pulmon EGFR-mutado. | Soria et al., NEJM 2018 |
| `ONC-284` | **Vemurafenib / dabrafenib -> BRAF V600E** | farmaco->diana | Inhibidores de BRAF mutado que apagan la via MAPK. | Estandar en melanoma BRAF V600E (con anti-MEK). | Chapman et al., NEJM 2011 |
| `ONC-285` | **Trametinib -> MEK** | farmaco->diana | Inhibidor de MEK que se combina con anti-BRAF para retrasar resistencia. | Combinacion estandar en melanoma BRAF-mutado. | Long et al., NEJM 2014 |
| `ONC-286` | **Crizotinib / alectinib -> ALK** | farmaco->diana | Inhibidores de la cinasa de fusion ALK en cancer de pulmon. | Estandar en pulmon ALK-positivo. | Shaw et al., NEJM 2013 |
| `ONC-287` | **Olaparib -> PARP** | farmaco->diana | Inhibidor de PARP letal en tumores con deficiencia de recombinacion homologa. | Aprobado en ovario, mama, prostata y pancreas BRCA. | Ledermann et al., NEJM 2012 |
| `ONC-288` | **Pembrolizumab / nivolumab -> PD-1** | farmaco->diana | Anticuerpos que bloquean PD-1 reactivando los linfocitos T. | Uso amplio; primera terapia tumor-agnostica (MSI-H). | Le et al., NEJM 2015 |
| `ONC-289` | **Atezolizumab -> PD-L1** | farmaco->diana | Anticuerpo que bloquea el ligando PD-L1. | Uso en pulmon, vejiga y mama triple negativo. | Rittmeyer et al., Lancet 2017 |
| `ONC-290` | **Ipilimumab -> CTLA-4** | farmaco->diana | Anticuerpo que bloquea el checkpoint temprano CTLA-4. | Primer checkpoint que mejoro supervivencia en melanoma. | Hodi et al., NEJM 2010 |
| `ONC-291` | **Venetoclax -> BCL-2** | farmaco->diana | Mimetico BH3 que libera la apoptosis en celulas dependientes de BCL-2. | Estandar en LLC y en LMA (con hipometilantes). | Roberts et al., NEJM 2016 |
| `ONC-292` | **Palbociclib -> CDK4/6** | farmaco->diana | Inhibidor de CDK4/6 que restaura el freno de RB. | Estandar en mama HR+/HER2- (con terapia endocrina). | Finn et al., NEJM 2016 |
| `ONC-293` | **Sotorasib / adagrasib -> KRAS G12C** | farmaco->diana | Inhibidores covalentes que fijan a KRAS G12C en su estado GDP inactivo. | Primeros farmacos contra el 'indruggable' KRAS. | Skoulidis et al., NEJM 2021 |
| `ONC-294` | **Ivosidenib -> IDH1 mutante** | farmaco->diana | Inhibidor que reduce el oncometabolito 2-HG en tumores IDH1-mutados. | Uso en LMA y colangiocarcinoma IDH1-mutado. | DiNardo et al., NEJM 2018 |
| `ONC-295` | **Enasidenib -> IDH2 mutante** | farmaco->diana | Inhibidor de IDH2 que induce diferenciacion mieloide. | Uso en LMA IDH2-mutada. | Stein et al., Blood 2017 |
| `ONC-296` | **All-trans retinoic acid -> PML-RARA** | farmaco->diana | Fuerza la diferenciacion de promielocitos degradando PML-RARA. | Curativa (con arsenico) en leucemia promielocitica aguda. | Huang et al., Blood 1988 |
| `ONC-297` | **Arsenic trioxide -> PML-RARA** | farmaco->diana | Degrada la oncoproteina PML-RARA de forma complementaria a ATRA. | Componente del regimen curativo de LPA. | Lo-Coco et al., NEJM 2013 |
| `ONC-298` | **Tamoxifen -> estrogen receptor** | farmaco->diana | Modulador selectivo que antagoniza el receptor de estrogeno en la mama. | Pilar de la terapia endocrina en mama ER+. | EBCTCG, Lancet 2011 |
| `ONC-299` | **Abiraterone -> CYP17 (androgen synthesis)** | farmaco->diana | Bloquea la sintesis de androgenos suprimiendo la senal del receptor androgenico. | Estandar en cancer de prostata avanzado. | de Bono et al., NEJM 2011 |
| `ONC-300` | **Enzalutamide -> androgen receptor** | farmaco->diana | Antagonista potente del receptor androgenico. | Estandar en cancer de prostata resistente a castracion. | Scher et al., NEJM 2012 |
| `ONC-301` | **CD19 CAR-T -> CD19** | farmaco->diana | Linfocitos T con receptor quimerico que atacan celulas CD19+. | Respuestas duraderas en leucemia/linfoma B refractarios. | Maude et al., NEJM 2018 |
| `ONC-302` | **Blinatumomab -> CD19 x CD3** | farmaco->diana | Anticuerpo biespecifico que acerca linfocitos T a blastos CD19+. | Uso en leucemia linfoblastica aguda B. | Kantarjian et al., NEJM 2017 |

[volver al indice](#indice)

---

## Estadisticas
*302 primitivas | 18 categorias | 14 roles distintos*

| Rol | Primitivas |
| :--- | :---: |
| proceso | 95 |
| diana | 27 |
| farmaco->diana | 26 |
| biomarcador | 25 |
| marco | 25 |
| oncogen | 22 |
| modalidad | 21 |
| supresor | 18 |
| via | 18 |
| hallmark | 8 |
| carcinogeno | 6 |
| virus | 5 |
| hallmark (2022) | 4 |
| caracteristica facilitadora | 2 |

---

## Nota metodologica
Las primitivas cubren desde los hallmarks del cancer de Hanahan & Weinberg (Cell 2000; Cell 2011) y sus nuevas dimensiones (Hanahan, Cancer Discov 2022) hasta pares farmaco->diana con mecanismo establecido. Las referencias citan articulos o revisiones canonicas; los mecanismos reflejan conocimiento establecido a la fecha de generacion. La eficacia de cada terapia dirigida depende del contexto tumoral y del biomarcador, y varios farmacos citados actuan solo en subgrupos moleculares concretos. Esto es material educativo y de modelado ontologico: **no sustituye juicio clinico ni investigacion primaria.**
