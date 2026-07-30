# 300 Primitivas de Biologia del Envejecimiento

### Ontologia CORTEX / BABYLON-60 -- bloques fundamentales que la gerociencia estudia y modula

*Generado 2026-07-14 | 300 primitivas | escala de confianza C5-established | fuente unica: `empiric_science/gen_aging_primitives.py`*

> **AVISO IMPORTANTE.** AVISO. Esto es una ONTOLOGIA DE CONOCIMIENTO de la biologia molecular del envejecimiento (gerociencia) y de sus dianas de modulacion: los bloques fundamentales que la investigacion del envejecimiento estudia y modula. NO es una cura del envejecimiento, NO es un protocolo de longevidad, NO es un tratamiento anti-edad y NO es consejo medico. Ninguna primitiva individual ni el conjunto 'revierten el envejecimiento' ni 'alargan la vida humana': la inmensa mayoria de la evidencia es preclinica (levadura, gusano, mosca, raton) y su traduccion a personas NO esta probada. Varios compuestos aqui listados son experimentales, tienen efectos dependientes de sexo/dosis y riesgos; NO deben autoadministrarse. Cualquier decision de salud debe tomarse con profesionales sanitarios cualificados.

> *NOTICE.* NOTICE. This is a KNOWLEDGE ONTOLOGY of the molecular biology of aging (geroscience) and its modulation targets. It is NOT a cure for aging, NOT a longevity protocol, NOT an anti-aging treatment and NOT medical advice. No single primitive nor the whole set 'reverses aging' or 'extends human lifespan': the overwhelming majority of evidence is preclinical (yeast, worm, fly, mouse) and human translation is NOT established. Several listed compounds are experimental, sex/dose-dependent and carry risks; they must NOT be self-administered. Consult qualified healthcare professionals for any health decision.

Autoria artistica/arquitectonica del sustrato (AKA): **Borja Moskv** (`borjamoskv`).

---

<a id="indice"></a>
## Indice de categorias

### Resumen por capa
| Capa | Categorias | Primitivas |
| :--- | :---: | :---: |
| `meta` | 3 | 42 |
| `molecular` | 4 | 70 |
| `pathway` | 1 | 24 |
| `cellular` | 4 | 64 |
| `tissue` | 4 | 52 |
| `therapy` | 2 | 48 |
| **TOTAL** | **18** | **300** |

### Categorias
| # | Categoria | Capa | Primitivas |
| :--- | :--- | :--- | :---: |
| 1 | [Hallmarks del envejecimiento](#hallmarks-del-envejecimiento) | `meta` | 16 |
| 2 | [Inestabilidad genomica y dano al ADN](#inestabilidad-genomica-y-dano-al-adn) | `molecular` | 22 |
| 3 | [Atricion telomerica](#atricion-telomerica) | `molecular` | 10 |
| 4 | [Alteraciones epigeneticas y relojes](#alteraciones-epigeneticas-y-relojes) | `molecular` | 20 |
| 5 | [Perdida de proteostasis](#perdida-de-proteostasis) | `cellular` | 16 |
| 6 | [Autofagia y mitofagia](#autofagia-y-mitofagia) | `cellular` | 14 |
| 7 | [Deteccion de nutrientes y vias de longevidad](#deteccion-de-nutrientes-y-vias-de-longevidad) | `pathway` | 24 |
| 8 | [Disfuncion mitocondrial y metabolismo NAD+](#disfuncion-mitocondrial-y-metabolismo-nad) | `molecular` | 18 |
| 9 | [Senescencia celular y SASP](#senescencia-celular-y-sasp) | `cellular` | 22 |
| 10 | [Agotamiento de celulas madre y regeneracion](#agotamiento-de-celulas-madre-y-regeneracion) | `cellular` | 12 |
| 11 | [Comunicacion intercelular alterada](#comunicacion-intercelular-alterada) | `tissue` | 12 |
| 12 | [Inflammaging e inmunosenescencia](#inflammaging-e-inmunosenescencia) | `tissue` | 14 |
| 13 | [Disbiosis del microbioma](#disbiosis-del-microbioma) | `tissue` | 10 |
| 14 | [Fisiologia de sistemas y fenotipos del envejecimiento](#fisiologia-de-sistemas-y-fenotipos-del-envejecimiento) | `tissue` | 16 |
| 15 | [Organismos modelo y geroprincipios](#organismos-modelo-y-geroprincipios) | `meta` | 14 |
| 16 | [Biomarcadores y relojes del envejecimiento](#biomarcadores-y-relojes-del-envejecimiento) | `meta` | 12 |
| 17 | [Geroterapeutica y modalidades](#geroterapeutica-y-modalidades) | `therapy` | 22 |
| 18 | [Primitivas intervencion -> diana](#primitivas-intervencion-diana) | `therapy` | 26 |
| | **TOTAL** | | **300** |

---

## Hallmarks del envejecimiento
<a id="hallmarks-del-envejecimiento"></a>

*Capa: meta | 16 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `AGE-001` | **Genomic instability** | hallmark primario | Acumulacion de dano al ADN nuclear y mitocondrial que erosiona la integridad del genoma con la edad. | Reparacion del ADN y restriccion calorica; marco de los sindromes progeroides. | Lopez-Otin et al., Cell 2013/2023 |
| `AGE-002` | **Telomere attrition** | hallmark primario | Acortamiento telomerico replicativo que agota la capacidad proliferativa y dispara senescencia. | Activacion de telomerasa (investigacion); riesgo en telomeropatias. | Lopez-Otin et al., Cell 2013/2023 |
| `AGE-003` | **Epigenetic alterations** | hallmark primario | Deriva de metilacion, cambios de histonas y perdida de heterocromatina que desregulan la expresion. | Reprogramacion parcial (OSKM); farmacos epigeneticos. | Lopez-Otin et al., Cell 2013/2023 |
| `AGE-004` | **Loss of proteostasis** | hallmark primario | Fallo de chaperonas y sistemas de degradacion que permite acumular agregados proteotoxicos. | Inductores de chaperonas y de autofagia. | Lopez-Otin et al., Cell 2013/2023 |
| `AGE-005` | **Disabled macroautophagy** | hallmark primario (2023) | Declive de la macroautofagia que reduce el reciclaje de organelas y proteinas danadas. | Espermidina, rapamicina, ayuno. | Lopez-Otin et al., Cell 2023 |
| `AGE-006` | **Deregulated nutrient-sensing** | hallmark antagonista | Desregulacion de IIS/mTOR/AMPK/sirtuinas que desacopla crecimiento y disponibilidad de nutrientes. | Rapamicina, metformina, restriccion calorica. | Lopez-Otin et al., Cell 2013/2023 |
| `AGE-007` | **Mitochondrial dysfunction** | hallmark antagonista | Perdida de eficiencia de la cadena respiratoria con aumento de ROS y de dano. | Mitohormesis, ejercicio, inductores de mitofagia. | Lopez-Otin et al., Cell 2013/2023 |
| `AGE-008` | **Cellular senescence** | hallmark antagonista | Arresto proliferativo estable con secretoma proinflamatorio (SASP) que remodela el tejido. | Senoliticos y senomorficos. | Lopez-Otin et al., Cell 2013/2023 |
| `AGE-009` | **Stem cell exhaustion** | hallmark integrador | Declive de la funcion regenerativa de las celulas madre tisulares. | Rejuvenecimiento de nichos; factores sistemicos. | Lopez-Otin et al., Cell 2013/2023 |
| `AGE-010` | **Altered intercellular communication** | hallmark integrador | Cambios endocrinos, neuronales e inmunes que propagan senales de envejecimiento entre tejidos. | Parabiosis/dilucion plasmatica; anti-inflamatorios. | Lopez-Otin et al., Cell 2013/2023 |
| `AGE-011` | **Chronic inflammation (inflammaging)** | hallmark integrador (2023) | Inflamacion esteril de bajo grado y sostenida que dana tejidos y agrava otros hallmarks. | Bloqueo de IL-6/TNF; inhibidores del inflamasoma. | Lopez-Otin et al., Cell 2023; Franceschi, Ann NY Acad Sci 2000 |
| `AGE-012` | **Dysbiosis** | hallmark integrador (2023) | Alteracion de la composicion y funcion del microbioma con impacto sistemico. | Probioticos, prebioticos, FMT; eje intestino-organo. | Lopez-Otin et al., Cell 2023 |
| `AGE-013` | **Geroscience hypothesis** | marco | El envejecimiento es el mayor factor de riesgo comun de las enfermedades cronicas; modularlo las retrasa en bloque. | Fundamento de la geroterapeutica y del ensayo TAME. | Kennedy et al., Cell 2014 |
| `AGE-014` | **Antagonistic pleiotropy** | teoria evolutiva | Genes que favorecen la aptitud juvenil resultan deletereos en la vejez. | Explica trade-offs de las vias de longevidad. | Williams, Evolution 1957 |
| `AGE-015` | **Disposable soma theory** | teoria evolutiva | Asignacion limitada de recursos entre mantenimiento somatico y reproduccion. | Marco conceptual de la restriccion calorica. | Kirkwood, Nature 1977 |
| `AGE-016` | **Gompertz-Makeham law of mortality** | marco | La mortalidad por causas intrinsecas crece de forma aproximadamente exponencial con la edad. | Marco demografico para medir efectos geroprotectores. | Gompertz, Phil Trans R Soc 1825 |

[volver al indice](#indice)

## Inestabilidad genomica y dano al ADN
<a id="inestabilidad-genomica-y-dano-al-adn"></a>

*Capa: molecular | 22 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `AGE-017` | **DNA double-strand break (DSB) accumulation** | proceso | Roturas de doble cadena que se acumulan y saturan la maquinaria de reparacion con la edad. | Diana de estrategias que refuerzan el DDR. | Lopez-Otin et al., Cell 2013 |
| `AGE-018` | **Somatic mutation accumulation** | proceso | Incremento de la carga mutacional somatica en tejidos a lo largo de la vida. | Base de expansiones clonales y de riesgo neoplasico. | Vijg & Suh, Annu Rev Physiol 2013 |
| `AGE-019` | **Clonal hematopoiesis (CHIP)** | biomarcador | Expansion de clones hematopoyeticos con mutaciones (DNMT3A, TET2, ASXL1) que crece con la edad. | Predice riesgo cardiovascular y hematologico. | Jaiswal et al., NEJM 2014 |
| `AGE-020` | **Mitochondrial DNA (mtDNA) mutations** | proceso | Acumulacion de mutaciones y deleciones en el genoma mitocondrial por replicacion y ROS. | Modelo mutador mtDNA (raton) recapitula envejecimiento. | Trifunovic et al., Nature 2004 |
| `AGE-021` | **DNA damage response (DDR) decline** | proceso | Perdida de eficiencia en la deteccion y reparacion coordinada del dano genomico. | Objetivo de refuerzo del mantenimiento genomico. | Lopez-Otin et al., Cell 2013 |
| `AGE-022` | **Base excision repair (BER) decline** | proceso | Reduccion de la reparacion de bases oxidadas o alquiladas. | Relacion con estres oxidativo tisular. | Maynard et al., Carcinogenesis 2009 |
| `AGE-023` | **Nucleotide excision repair (NER) decline** | proceso | Menor capacidad de eliminar lesiones voluminosas; su fallo causa progerias. | Marco de Cockayne y xeroderma pigmentoso. | Lopez-Otin et al., Cell 2013 |
| `AGE-024` | **Nuclear lamina disruption (Lamin B1 loss)** | proceso | Perdida de lamina B1 que desorganiza la arquitectura nuclear y la heterocromatina. | Marcador de senescencia y de envejecimiento nuclear. | Freund et al., Mol Biol Cell 2012 |
| `AGE-025` | **Progerin / LMNA (Hutchinson-Gilford)** | biomarcador | Isoforma toxica de lamina A por splicing aberrante que causa progeria acelerada. | Diana de lonafarnib (inhibidor de farnesiltransferasa). | Eriksson et al., Nature 2003 |
| `AGE-026` | **Werner syndrome (WRN helicase)** | biomarcador | Perdida de la helicasa WRN que provoca envejecimiento segmentario acelerado. | Modelo humano de inestabilidad genomica. | Yu et al., Science 1996 |
| `AGE-027` | **Transposable element / LINE-1 derepression** | proceso | Reactivacion de retrotransposones LINE-1 al perderse la represion heterocromatica. | Inhibidores de transcriptasa inversa (investigacion). | De Cecco et al., Nature 2019 |
| `AGE-028` | **Cytoplasmic chromatin / cGAS-STING activation** | proceso | ADN citosolico (retroelementos, fragmentos) que activa inmunidad innata e inflammaging. | Diana antiinflamatoria del eje cGAS-STING. | Gluck et al., Nat Cell Biol 2017 |
| `AGE-029` | **Heterochromatin loss at repeats** | proceso | Relajacion de la heterocromatina que expone repeticiones y desestabiliza el genoma. | Nexo con la teoria de perdida de heterocromatina. | Villeponteau, Exp Gerontol 1997 |
| `AGE-030` | **Telomere-associated DNA damage foci (TAF)** | biomarcador | Focos de dano persistente en telomeros que impulsan senescencia con independencia de la longitud. | Marcador de senescencia in vivo. | Hewitt et al., Nat Commun 2012 |
| `AGE-031` | **8-oxo-dG oxidative lesions** | biomarcador | Base oxidada canonica que refleja el dano oxidativo acumulado al ADN. | Biomarcador de estres oxidativo. | Maynard et al., Carcinogenesis 2009 |
| `AGE-032` | **PARP overactivation and NAD+ depletion** | proceso | El dano cronico hiperactiva PARP1, consumiendo NAD+ y limitando a las sirtuinas. | Racional de los refuerzos de NAD+. | Fang et al., Cell Metab 2016 |
| `AGE-033` | **Somatic mosaicism** | proceso | Mosaico de variantes somaticas y estructurales entre celulas de un mismo tejido. | Fuente de heterogeneidad funcional con la edad. | Vijg & Suh, Annu Rev Physiol 2013 |
| `AGE-034` | **Age-related replication stress** | proceso | Horquillas de replicacion inestables que generan dano en tejidos proliferativos envejecidos. | Vulnerabilidad y fuente de senescencia. | Lopez-Otin et al., Cell 2013 |
| `AGE-035` | **SIRT6 genome maintenance** | diana | Desacetilasa/mono-ADP-ribosiltransferasa que promueve reparacion de DSB y reprime LINE-1. | Su sobreexpresion alarga la vida en raton macho. | Kanfi et al., Nature 2012 |
| `AGE-036` | **SIRT1 in DNA repair** | diana | Sirtuina que participa en la respuesta al dano y la estabilidad genomica dependiente de NAD+. | Diana de activadores de sirtuinas. | Oberdoerffer et al., Cell 2008 |
| `AGE-037` | **Ku / DNA-PKcs NHEJ aging** | proceso | Cambios en la union de extremos no homologa que afectan fidelidad reparadora con la edad. | Contexto de radiosensibilidad tisular. | Lopez-Otin et al., Cell 2013 |
| `AGE-038` | **Nucleolar / rDNA instability** | proceso | Inestabilidad de las repeticiones de ADN ribosomal, fuente de envejecimiento en levadura. | El circulo de rDNA extracromosomico limita la vida replicativa. | Sinclair & Guarente, Cell 1997 |

[volver al indice](#indice)

## Atricion telomerica
<a id="atricion-telomerica"></a>

*Capa: molecular | 10 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `AGE-039` | **Telomere shortening (end-replication problem)** | proceso | Perdida progresiva de secuencia telomerica en cada division por replicacion incompleta del extremo. | Barrera proliferativa; diana conceptual de la telomerasa. | Harley et al., Nature 1990 |
| `AGE-040` | **Telomerase (TERT)** | diana | Transcriptasa inversa que elonga telomeros y confiere potencial replicativo. | Terapia genica de TERT alarga vida en raton (preclinico). | Greider & Blackburn, Cell 1985; Bernardes de Jesus, EMBO Mol Med 2012 |
| `AGE-041` | **TERC (RNA template)** | proceso | Componente ARN molde de la telomerasa; su mutacion causa telomeropatias. | Contexto de disqueratosis congenita. | Feng et al., Science 1995 |
| `AGE-042` | **Shelterin complex (TRF1/TRF2/POT1)** | proceso | Complejo que protege el extremo telomerico y regula el acceso de la telomerasa. | Su disfuncion dispara senales de dano. | de Lange, Genes Dev 2005 |
| `AGE-043` | **Replicative senescence (Hayflick limit)** | proceso | Arresto tras un numero finito de divisiones por acortamiento telomerico critico. | Marco fundacional de la inmortalizacion celular. | Hayflick & Moorhead, Exp Cell Res 1961 |
| `AGE-044` | **T-loop structure** | proceso | Lazo que oculta el extremo 3' telomerico y evita que sea leido como rotura. | Nodo estructural de la proteccion telomerica. | Griffith et al., Cell 1999 |
| `AGE-045` | **Telomere position effect (TPE)** | proceso | Silenciamiento de genes subtelomericos modulado por la longitud del telomero. | Nexo entre telomeros y expresion con la edad. | Baur et al., Science 2001 |
| `AGE-046` | **Telomeropathies (dyskeratosis congenita)** | biomarcador | Sindromes por mantenimiento telomerico deficiente con fallo medular y fibrosis. | Modelo humano de telomeros cortos. | Armanios & Blackburn, Nat Rev Genet 2012 |
| `AGE-047` | **Telomere length as biomarker** | biomarcador | La longitud telomerica en leucocitos se asocia a edad y a riesgo de enfermedad. | Biomarcador epidemiologico (con limitaciones). | Blackburn et al., Science 2015 |
| `AGE-048` | **Alternative lengthening of telomeres (ALT)** | proceso | Mantenimiento telomerico por recombinacion, independiente de telomerasa. | Relevante en un subconjunto de tumores. | Bryan et al., Nat Med 1997 |

[volver al indice](#indice)

## Alteraciones epigeneticas y relojes
<a id="alteraciones-epigeneticas-y-relojes"></a>

*Capa: molecular | 20 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `AGE-049` | **DNA methylation drift** | proceso | Perdida de la precision del patron de metilacion (deriva estocastica) con la edad. | Sustrato de los relojes epigeneticos. | Issa, J Clin Invest 2014 |
| `AGE-050` | **Global DNA hypomethylation** | proceso | Descenso global de 5mC que favorece inestabilidad y reactivacion de repeticiones. | Marca epigenetica del envejecimiento. | Wilson & Jones, Science 1983 |
| `AGE-051` | **Focal CpG island hypermethylation** | proceso | Hipermetilacion de promotores concretos que silencia genes con la edad. | Solapa con silenciamiento tumoral. | Issa, J Clin Invest 2014 |
| `AGE-052` | **Horvath multi-tissue clock (353 CpG)** | biomarcador | Estimador de edad basado en 353 sitios CpG aplicable a multiples tejidos (r~0.96). | Referencia de edad biologica epigenetica. | Horvath, Genome Biol 2013 |
| `AGE-053` | **Hannum blood clock** | biomarcador | Reloj de metilacion en sangre entrenado sobre ~71 CpG. | Reloj de primera generacion. | Hannum et al., Mol Cell 2013 |
| `AGE-054` | **PhenoAge / GrimAge clocks** | biomarcador | Relojes de segunda generacion entrenados con fenotipos clinicos y mortalidad. | Mejor prediccion de morbimortalidad. | Levine et al., Aging 2018; Lu et al., Aging 2019 |
| `AGE-055` | **DunedinPACE (pace of aging)** | biomarcador | Reloj de tercera generacion que estima la velocidad de envejecimiento longitudinal. | Endpoint candidato en ensayos geroprotectores. | Belsky et al., eLife 2022 |
| `AGE-056` | **Histone modification shifts (H3K9me3/H3K27me3)** | proceso | Redistribucion de marcas de histona activadoras y represoras con la edad. | Diana de escritores/borradores epigeneticos. | Benayoun et al., Nat Rev Mol Cell Biol 2015 |
| `AGE-057` | **Heterochromatin loss theory** | marco | Erosion de la heterocromatina que desestabiliza el epigenoma y la expresion. | Marco integrador de la deriva epigenetica. | Villeponteau, Exp Gerontol 1997 |
| `AGE-058` | **Histone protein loss** | proceso | Reduccion de la sintesis y disponibilidad de histonas centrales con la edad. | Su suplementacion prolonga vida en levadura. | Feser et al., Mol Cell 2010 |
| `AGE-059` | **Chromatin remodeling decline** | proceso | Perdida de funcion de complejos remodeladores que altera la accesibilidad. | Contexto de programas transcripcionales envejecidos. | Benayoun et al., Nat Rev Mol Cell Biol 2015 |
| `AGE-060` | **Partial reprogramming (OSKM)** | modalidad | Expresion transitoria de factores Yamanaka que revierte marcas de edad sin borrar identidad. | Rejuvenecimiento parcial in vivo (preclinico). | Ocampo et al., Cell 2016 |
| `AGE-061` | **Information theory of aging (ICE)** | marco | La perdida de informacion epigenetica, no solo mutaciones, seria causa del envejecimiento. | Base conceptual del rejuvenecimiento por reprogramacion. | Yang et al., Cell 2023 |
| `AGE-062` | **DNA methyltransferases (DNMT1/3A/3B)** | diana | Enzimas escritoras de la metilacion cuyo balance se altera con la edad. | Contexto de terapias hipometilantes. | Jones & Baylin, Nat Rev Genet 2002 |
| `AGE-063` | **TET enzymes and 5hmC** | proceso | Oxidan 5mC iniciando desmetilacion activa; su actividad depende de alfa-cetoglutarato. | Nexo metabolismo-epigenetica. | Tahiliani et al., Science 2009 |
| `AGE-064` | **Polycomb (PRC2/EZH2) redistribution** | proceso | Reasignacion de la marca represiva H3K27me3 que desregula programas con la edad. | Diana de inhibidores de EZH2. | Benayoun et al., Nat Rev Mol Cell Biol 2015 |
| `AGE-065` | **miRNA dysregulation (miR-34a)** | proceso | Cambios en microARNs reguladores (p.ej. miR-34a) que modulan senescencia e inflamacion. | Biomarcadores y dianas emergentes. | Smith-Vikos & Slack, J Cell Sci 2012 |
| `AGE-066` | **Transcriptional noise / heterogeneity** | proceso | Aumento de la variabilidad celula-a-celula en la expresion genica con la edad. | Firma de desregulacion epigenetica. | Bahar et al., Nature 2006 |
| `AGE-067` | **Circadian epigenetic reprogramming** | proceso | Reprogramacion del reloj circadiano y de sus dianas metabolicas en tejidos envejecidos. | Nexo cronobiologia-envejecimiento. | Sato et al., Cell 2017 |
| `AGE-068` | **Loss of nuclear organization (LADs)** | proceso | Reorganizacion de dominios asociados a lamina que altera la compartimentacion del genoma. | Contexto de progerias y senescencia. | Lopez-Otin et al., Cell 2013 |

[volver al indice](#indice)

## Perdida de proteostasis
<a id="perdida-de-proteostasis"></a>

*Capa: cellular | 16 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `AGE-069` | **Molecular chaperones (HSP70/HSP90)** | diana | Chaperonas que pliegan y estabilizan proteinas; su capacidad disminuye con la edad. | Diana de inductores de la respuesta de choque termico. | Hipp et al., Nat Rev Mol Cell Biol 2019 |
| `AGE-070` | **Heat shock factor 1 (HSF1)** | diana | Factor maestro que activa la transcripcion de chaperonas ante estres proteotoxico. | Su activacion protege modelos de proteinopatia. | Morimoto, Genes Dev 2008 |
| `AGE-071` | **Heat shock response decline** | proceso | Perdida de la capacidad de montar la respuesta de choque termico con la edad. | Objetivo de refuerzo proteostatico. | Labbadia & Morimoto, Annu Rev Biochem 2015 |
| `AGE-072` | **Unfolded protein response (UPR-ER)** | proceso | Via de senalizacion del reticulo que restaura el plegamiento ante estres. | Modulacion en enfermedades por mal plegamiento. | Walter & Ron, Science 2011 |
| `AGE-073` | **Ubiquitin-proteasome system (UPS) decline** | proceso | Descenso de la degradacion selectiva ubiquitina-dependiente de proteinas danadas. | Diana de activadores del proteasoma. | Saez & Vilchez, Curr Genomics 2014 |
| `AGE-074` | **Proteasome activity decline (26S/20S)** | proceso | Reduccion de la actividad y ensamblaje del proteasoma en tejidos envejecidos. | Su refuerzo mejora proteostasis (preclinico). | Chondrogianni et al., J Biol Chem 2005 |
| `AGE-075` | **Protein aggregation (amyloid/tau/alpha-synuclein)** | proceso | Acumulacion de agregados proteotoxicos caracteristica de enfermedades por edad. | Interfaz con neurodegeneracion. | Hipp et al., Nat Rev Mol Cell Biol 2019 |
| `AGE-076` | **Loss of proteostasis network capacity** | proceso | Saturacion del conjunto de plegamiento, trafico y degradacion proteica. | Marco integrador de la proteopatia. | Balch et al., Science 2008 |
| `AGE-077` | **ER stress with age** | proceso | Aumento del estres del reticulo endoplasmatico y de respuestas mal adaptativas. | Diana de chaperonas quimicas. | Walter & Ron, Science 2011 |
| `AGE-078` | **Mitochondrial UPR (UPRmt)** | proceso | Respuesta que restaura la proteostasis mitocondrial y modula longevidad. | Su activacion prolonga vida en C. elegans. | Durieux et al., Cell 2011 |
| `AGE-079` | **Chaperone-mediated autophagy (CMA / LAMP2A)** | proceso | Degradacion selectiva de proteinas con motivo KFERQ via LAMP2A, que declina con la edad. | Su restauracion mejora funcion hepatica en raton. | Zhang & Cuervo, Nat Med 2008 |
| `AGE-080` | **Aggresome and inclusion bodies** | proceso | Secuestro de agregados en inclusiones cuando falla la degradacion. | Marcador de colapso proteostatico. | Hipp et al., Nat Rev Mol Cell Biol 2019 |
| `AGE-081` | **Protein carbonylation / oxidative damage** | biomarcador | Modificacion oxidativa irreversible de proteinas que se acumula con la edad. | Biomarcador de dano proteico. | Stadtman, Free Radic Res 2006 |
| `AGE-082` | **Small heat shock proteins (HSPB)** | diana | Chaperonas ATP-independientes que amortiguan agregacion en estres. | Moduladores de proteostasis tisular. | Hipp et al., Nat Rev Mol Cell Biol 2019 |
| `AGE-083` | **Chemical chaperones (4-PBA, TUDCA)** | modalidad | Moleculas que estabilizan el plegamiento y alivian el estres del reticulo. | Estrategia proteostatica en investigacion. | Walter & Ron, Science 2011 |
| `AGE-084` | **Insulin/IGF-DAF-16 proteostasis link** | proceso | La senal reducida de IIS potencia chaperonas y proteostasis via DAF-16/FOXO. | Nexo nutrient-sensing-proteostasis. | Morley et al., PNAS 2002 |

[volver al indice](#indice)

## Autofagia y mitofagia
<a id="autofagia-y-mitofagia"></a>

*Capa: cellular | 14 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `AGE-085` | **Macroautophagy** | proceso | Secuestro de material citoplasmatico en autofagosomas para su degradacion lisosomal. | Su induccion es central a la geroproteccion. | Mizushima & Komatsu, Cell 2011 |
| `AGE-086` | **Age-related autophagy decline** | proceso | Reduccion del flujo autofagico en multiples tejidos con la edad. | Diana de restauracion (espermidina, ayuno). | Rubinsztein et al., Cell 2011 |
| `AGE-087` | **ATG genes / autophagosome formation** | proceso | Maquinaria ATG que nuclea y elonga la membrana del autofagosoma. | Su integridad condiciona la longevidad. | Mizushima & Komatsu, Cell 2011 |
| `AGE-088` | **mTORC1 inhibition of autophagy** | proceso | mTORC1 activo reprime la iniciacion autofagica via ULK1 y TFEB. | La inhibicion de mTOR desreprime la autofagia. | Kim et al., Nat Cell Biol 2011 |
| `AGE-089` | **AMPK / ULK1 activation of autophagy** | proceso | AMPK fosforila ULK1 e induce autofagia ante deficit energetico. | Nexo con metformina y ejercicio. | Egan et al., Science 2011 |
| `AGE-090` | **TFEB (lysosomal biogenesis master)** | diana | Factor de transcripcion que activa genes de autofagia y biogenesis lisosomal. | Su activacion despeja agregados (preclinico). | Settembre et al., Science 2011 |
| `AGE-091` | **Lysosomal dysfunction / lipofuscin** | proceso | Deterioro lisosomal con acumulo de lipofuscina no degradable. | Marcador clasico de envejecimiento celular. | Terman & Brunk, Int J Biochem Cell Biol 2004 |
| `AGE-092` | **Mitophagy (PINK1/Parkin)** | proceso | Eliminacion selectiva de mitocondrias danadas marcada por PINK1 y Parkin. | Diana de inductores de mitofagia. | Palikaras et al., Nature 2015 |
| `AGE-093` | **Urolithin A (mitophagy inducer)** | farmaco | Metabolito derivado de elagitaninos que induce mitofagia y mejora funcion muscular. | Ensayos humanos de resistencia muscular. | Ryu et al., Nat Med 2016 |
| `AGE-094` | **Spermidine (autophagy inducer)** | farmaco | Poliamina que induce autofagia via inhibicion de acetiltransferasas (EP300). | Prolonga vida en varios modelos; asociacion epidemiologica. | Eisenberg et al., Nat Cell Biol 2009 |
| `AGE-095` | **NIX/BNIP3 receptor mitophagy** | proceso | Receptores que dirigen mitofagia programada, relevante en eritrocitos y estres. | Contexto de calidad mitocondrial. | Palikaras et al., Nature 2015 |
| `AGE-096` | **Selective autophagy (aggrephagy)** | proceso | Degradacion dirigida de agregados proteicos mediante receptores como p62/SQSTM1. | Interfaz con proteinopatias. | Mizushima & Komatsu, Cell 2011 |
| `AGE-097` | **Beclin-1 / autophagy initiation** | diana | Componente del complejo de nucleacion cuya sobreexpresion prolonga vida en raton. | Diana de induccion autofagica. | Fernandez et al., Nature 2018 |
| `AGE-098` | **Fasting / CR-induced autophagy** | proceso | El ayuno y la restriccion calorica activan autofagia como efector geroprotector. | Mecanismo compartido de intervenciones dieteticas. | Madeo et al., Cell Metab 2019 |

[volver al indice](#indice)

## Deteccion de nutrientes y vias de longevidad
<a id="deteccion-de-nutrientes-y-vias-de-longevidad"></a>

*Capa: pathway | 24 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `AGE-099` | **Insulin/IGF-1 signaling (IIS)** | proceso | Via conservada que acopla nutrientes y crecimiento; su reduccion prolonga la vida. | Eje central de la geroterapeutica. | Kenyon, Nature 2010 |
| `AGE-100` | **daf-2 / daf-16 axis (C. elegans)** | proceso | Mutaciones en el receptor daf-2 duplican la vida via el factor FOXO daf-16. | Paradigma genetico de la longevidad. | Kenyon et al., Nature 1993 |
| `AGE-101` | **FOXO transcription factors (FOXO3)** | diana | Factores que activan defensa antioxidante, reparacion y autofagia aguas abajo de IIS. | FOXO3 se asocia a longevidad humana extrema. | Willcox et al., PNAS 2008 |
| `AGE-102` | **mTOR / mTORC1** | diana | Cinasa que integra nutrientes y crecimiento; su inhibicion extiende la vida. | Diana de rapamicina y rapalogos. | Johnson et al., Nature 2013 |
| `AGE-103` | **mTORC2** | proceso | Complejo de mTOR que regula supervivencia y metabolismo via AKT. | Contexto de efectos metabolicos de rapamicina. | Lamming et al., Science 2012 |
| `AGE-104` | **S6 kinase 1 (S6K1)** | diana | Efector de mTORC1; su deleccion prolonga vida y mejora metabolismo en raton hembra. | Nodo de la senal de crecimiento. | Selman et al., Science 2009 |
| `AGE-105` | **4E-BP1 translational control** | proceso | Represor de la traduccion cuya actividad media efectos de longevidad por baja mTOR. | Contexto de sintesis proteica y vida. | Zid et al., Cell 2009 |
| `AGE-106` | **AMPK (energy sensor)** | diana | Cinasa que detecta bajo ATP y activa catabolismo, autofagia y biogenesis mitocondrial. | Diana de metformina y del ejercicio. | Burkewitz et al., Cell Metab 2014 |
| `AGE-107` | **Sirtuins overview (SIRT1-7)** | diana | Desacetilasas dependientes de NAD+ que regulan metabolismo, reparacion y estres. | Diana de activadores y de refuerzos de NAD+. | Imai & Guarente, Trends Cell Biol 2014 |
| `AGE-108` | **SIRT1** | diana | Sirtuina nuclear/citoplasmatica que media efectos de la restriccion calorica. | Diana de STACs (resveratrol y sucesores). | Imai & Guarente, Trends Cell Biol 2014 |
| `AGE-109` | **SIRT3 (mitochondrial)** | diana | Sirtuina mitocondrial que desacetila enzimas metabolicas y antioxidantes. | Nexo con salud mitocondrial. | Imai & Guarente, Trends Cell Biol 2014 |
| `AGE-110` | **SIRT6 (chromatin/metabolism)** | diana | Sirtuina que mantiene el genoma y regula glucolisis; alarga vida al sobreexpresarse. | Diana emergente de longevidad. | Kanfi et al., Nature 2012 |
| `AGE-111` | **NAD+ as sirtuin cofactor** | proceso | Cofactor obligado de sirtuinas cuyo declive limita su actividad con la edad. | Racional de NR/NMN. | Verdin, Science 2015 |
| `AGE-112` | **PGC-1alpha (mitochondrial biogenesis)** | diana | Coactivador maestro de la biogenesis mitocondrial y el metabolismo oxidativo. | Efector de AMPK y del ejercicio. | Burkewitz et al., Cell Metab 2014 |
| `AGE-113` | **Caloric restriction (CR)** | modalidad | Reduccion de la ingesta sin desnutricion que extiende vida en multiples especies. | Intervencion geroprotectora de referencia. | Fontana et al., Science 2010 |
| `AGE-114` | **Methionine restriction** | modalidad | Restriccion de metionina que prolonga vida y mejora metabolismo sin restringir calorias. | Estrategia dietetica dirigida. | Miller et al., Aging Cell 2005 |
| `AGE-115` | **Intermittent fasting / TRE** | modalidad | Ventanas de alimentacion restringida que mejoran marcadores metabolicos y autofagia. | Intervencion conductual en estudio clinico. | de Cabo & Mattson, NEJM 2019 |
| `AGE-116` | **Growth hormone / GH-IGF axis** | proceso | El eje GH-IGF-1 acelera el crecimiento pero su reduccion se asocia a mayor longevidad. | Ratones enanos (Ames/Snell) muy longevos. | Bartke, Endocrinology 2005 |
| `AGE-117` | **Klotho (anti-aging hormone)** | diana | Hormona que modula IIS, fosfato y FGF23; su deficit acelera fenotipos de edad. | Su sobreexpresion prolonga vida en raton. | Kuro-o et al., Nature 1997; Kurosu et al., Science 2005 |
| `AGE-118` | **GDF15 (metabolic stress signal)** | biomarcador | Citocina de estres que aumenta con la edad y regula apetito y metabolismo via GFRAL. | Biomarcador y diana metabolica. | Mullican & Rangwala, Trends Pharmacol Sci 2018 |
| `AGE-119` | **mTOR-autophagy-longevity coupling** | proceso | La baja senal de mTOR prolonga vida en gran parte induciendo autofagia. | Explica solapamiento de intervenciones. | Johnson et al., Nature 2013 |
| `AGE-120` | **Nutrient-sensing network integration** | proceso | Diafonia coordinada entre IIS, mTOR, AMPK y sirtuinas que fija el estado metabolico. | Marco para combinaciones geroprotectoras. | Lopez-Otin et al., Cell 2016 |
| `AGE-121` | **Rheb / TSC1-TSC2 node** | proceso | Modulo GTPasa que activa mTORC1 en respuesta a factores de crecimiento y energia. | Nodo aguas arriba de mTOR. | Lamming et al., Science 2012 |
| `AGE-122` | **Amino-acid sensing (Sestrin/GATOR)** | proceso | Sensores de leucina y arginina que regulan mTORC1 segun disponibilidad de aminoacidos. | Diana de la restriccion proteica. | Wolfson et al., Science 2016 |

[volver al indice](#indice)

## Disfuncion mitocondrial y metabolismo NAD+
<a id="disfuncion-mitocondrial-y-metabolismo-nad"></a>

*Capa: molecular | 18 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `AGE-123` | **Electron transport chain decline** | proceso | Reduccion de la eficiencia de la fosforilacion oxidativa con la edad. | Diana de la mitohormesis y del ejercicio. | Sun et al., Mol Cell 2016 |
| `AGE-124` | **Mitochondrial free radical theory (ROS)** | marco | El dano oxidativo por ROS mitocondriales como motor propuesto del envejecimiento. | Matizada por la mitohormesis. | Harman, J Gerontol 1956 |
| `AGE-125` | **Mitohormesis** | proceso | Niveles bajos de ROS que activan defensas y prolongan la vida (respuesta adaptativa). | Explica limites de los antioxidantes masivos. | Ristow & Schmeisser, Free Radic Biol Med 2011 |
| `AGE-126` | **Mitochondrial biogenesis decline** | proceso | Menor generacion de mitocondrias nuevas por caida de PGC-1alfa y NAD+. | Diana de ejercicio y refuerzos de NAD+. | Lopez-Otin et al., Cell 2013 |
| `AGE-127` | **Mitochondrial dynamics (fission/fusion)** | proceso | Balance DRP1/MFN1-2/OPA1 que controla la red mitocondrial y su calidad. | Su desregulacion afecta mitofagia y funcion. | Sun et al., Mol Cell 2016 |
| `AGE-128` | **mtDNA heteroplasmy / common deletion** | biomarcador | Coexistencia de genomas mitocondriales mutados que se expande clonalmente con la edad. | Marcador de dano mitocondrial tisular. | Trifunovic et al., Nature 2004 |
| `AGE-129` | **NAD+ decline with age** | proceso | Descenso marcado del NAD+ tisular que limita sirtuinas, PARPs y metabolismo redox. | Racional central de NR/NMN. | Verdin, Science 2015; Covarrubias et al., Nat Rev Mol Cell Biol 2021 |
| `AGE-130` | **NAMPT (NAD+ salvage)** | diana | Enzima limitante del reciclaje de NAD+ cuya expresion cae con la edad. | Diana para sostener el pool de NAD+. | Yoshino et al., Cell Metab 2018 |
| `AGE-131` | **CD38 (NAD+ consumer)** | diana | NADasa que aumenta con la edad y agota NAD+, agravando la disfuncion metabolica. | Inhibidores de CD38 (investigacion). | Camacho-Pereira et al., Cell Metab 2016 |
| `AGE-132` | **NR / NMN (NAD+ precursors)** | farmaco | Precursores que elevan NAD+ y mejoran funcion mitocondrial en modelos. | Ensayos humanos de seguridad y biomarcadores. | Rajman et al., Cell Metab 2018 |
| `AGE-133` | **Mitochondrial sirtuin axis (SIRT3)** | proceso | SIRT3 desacetila enzimas mitocondriales dependiendo de NAD+ disponible. | Nexo NAD+-funcion mitocondrial. | Verdin, Science 2015 |
| `AGE-134` | **Mitochondrial membrane potential loss** | proceso | Caida del potencial de membrana que marca mitocondrias para mitofagia o disfuncion. | Parametro de calidad mitocondrial. | Sun et al., Mol Cell 2016 |
| `AGE-135` | **Permeability transition pore (mPTP)** | proceso | Poro que al abrirse colapsa la funcion mitocondrial y activa muerte celular. | Diana de proteccion mitocondrial. | Sun et al., Mol Cell 2016 |
| `AGE-136` | **Cardiolipin oxidation** | proceso | Oxidacion del fosfolipido cardiolipina que desestabiliza cristas y la cadena respiratoria. | Diana de elamipretide (SS-31). | Szeto, Br J Pharmacol 2014 |
| `AGE-137` | **Coenzyme Q10 / ubiquinone decline** | proceso | Descenso del transportador de electrones ubiquinona en tejidos envejecidos. | Racional de la suplementacion (evidencia mixta). | Hernandez-Camacho et al., Front Physiol 2018 |
| `AGE-138` | **Mitochondrial-derived peptides (humanin, MOTS-c)** | diana | Peptidos codificados por el mtDNA con efectos metabolicos y citoprotectores sistemicos. | MOTS-c como mimetico de ejercicio (preclinico). | Lee et al., Cell Metab 2015 |
| `AGE-139` | **Uncoupling proteins (UCP)** | proceso | Desacoplan la respiracion de la sintesis de ATP, modulando ROS y termogenesis. | Nexo entre metabolismo energetico y longevidad. | Brand, Exp Gerontol 2000 |
| `AGE-140` | **Mitochondrial quality control** | proceso | Integracion de biogenesis, dinamica y mitofagia que mantiene una red funcional. | Marco de intervenciones mitocondriales. | Palikaras et al., Nature 2015 |

[volver al indice](#indice)

## Senescencia celular y SASP
<a id="senescencia-celular-y-sasp"></a>

*Capa: cellular | 22 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `AGE-141` | **Cellular senescence** | proceso | Arresto proliferativo estable y resistente a apoptosis en respuesta a estres. | Diana de senoliticos y senomorficos. | Campisi, Annu Rev Physiol 2013 |
| `AGE-142` | **Replicative senescence** | proceso | Senescencia por acortamiento telomerico critico tras divisiones repetidas. | Base del limite de Hayflick. | Hayflick & Moorhead, Exp Cell Res 1961 |
| `AGE-143` | **Oncogene-induced senescence (OIS)** | proceso | Freno protector ante la activacion de oncogenes que evita transformacion. | Interfaz cancer-envejecimiento. | Serrano et al., Cell 1997 |
| `AGE-144` | **Stress-induced premature senescence (SIPS)** | proceso | Senescencia acelerada por estres oxidativo, genotoxico o mitocondrial. | Fuente de carga senescente tisular. | Campisi, Annu Rev Physiol 2013 |
| `AGE-145` | **Therapy-induced senescence** | proceso | Senescencia inducida por quimio o radioterapia con efectos duales. | Estrategias 'one-two punch' con senoliticos. | Demaria et al., Cancer Discov 2017 |
| `AGE-146` | **p16INK4a (CDKN2A)** | biomarcador | Inhibidor de CDK4/6 que impone el arresto senescente y se acumula con la edad. | Marcador y diana de aclaramiento senescente. | Krishnamurthy et al., J Clin Invest 2004 |
| `AGE-147` | **p21CIP1 (CDKN1A)** | proceso | Inhibidor de CDK inducido por p53 que inicia el arresto senescente. | Mediador temprano de la senescencia. | Campisi, Annu Rev Physiol 2013 |
| `AGE-148` | **p53-p21 senescence axis** | proceso | Eje que traduce dano genomico persistente en arresto estable. | Nodo de decision senescencia/apoptosis. | Campisi, Annu Rev Physiol 2013 |
| `AGE-149` | **Rb / p16 pathway** | proceso | Via que mantiene reprimido a E2F consolidando el arresto senescente. | Refuerzo del bloqueo proliferativo. | Campisi, Annu Rev Physiol 2013 |
| `AGE-150` | **SA-beta-galactosidase** | biomarcador | Actividad lisosomal aumentada usada como marcador clasico de senescencia. | Deteccion in situ de celulas senescentes. | Dimri et al., PNAS 1995 |
| `AGE-151` | **SASP (secretory phenotype)** | proceso | Secretoma de citocinas, quimiocinas y proteasas que remodela el microambiente. | Impulsor de inflammaging; diana senomorfica. | Coppe et al., PLoS Biol 2008 |
| `AGE-152` | **SASP regulation (NF-kB, C/EBPb, cGAS-STING)** | proceso | Redes transcripcionales y de sensado que controlan la intensidad del SASP. | Diana de inhibidores del SASP. | Gluck et al., Nat Cell Biol 2017 |
| `AGE-153` | **IL-6 / IL-8 SASP factors** | biomarcador | Citocinas prototipicas del SASP que propagan inflamacion y senescencia paracrina. | Biomarcadores y dianas antiinflamatorias. | Coppe et al., PLoS Biol 2008 |
| `AGE-154` | **Senescence-associated heterochromatin foci (SAHF)** | biomarcador | Focos de heterocromatina que silencian genes proliferativos en senescencia. | Marcador cromatinico de senescencia. | Narita et al., Cell 2003 |
| `AGE-155` | **Lamin B1 loss (senescence marker)** | biomarcador | Descenso de lamina B1 asociado al establecimiento de la senescencia. | Marcador complementario robusto. | Freund et al., Mol Biol Cell 2012 |
| `AGE-156` | **Senolytics (concept)** | modalidad | Farmacos que eliminan selectivamente celulas senescentes explotando sus dependencias. | Mejoran funcion y longevidad en raton. | Kirkland & Tchkonia, EBioMedicine 2017 |
| `AGE-157` | **Senomorphics (concept)** | modalidad | Agentes que suprimen el SASP sin matar la celula senescente. | Alternativa moduladora al aclaramiento. | Kirkland & Tchkonia, EBioMedicine 2017 |
| `AGE-158` | **BCL-2 family dependence** | diana | Las celulas senescentes dependen de anti-apoptoticos (BCL-xL) para sobrevivir. | Diana de navitoclax como senolitico. | Zhu et al., Aging Cell 2016 |
| `AGE-159` | **Senescent cell burden** | proceso | Aumento de la carga de celulas senescentes en tejidos que impulsa disfuncion. | Su reduccion mejora healthspan (preclinico). | Baker et al., Nature 2016 |
| `AGE-160` | **Immune surveillance of senescent cells** | proceso | Aclaramiento por celulas NK y macrofagos que decae con la edad. | Diana de inmunoterapia dirigida a senescencia. | Kang et al., Nature 2011 |
| `AGE-161` | **Senescence in age-related disease** | proceso | Contribucion causal de la senescencia a fibrosis, artrosis y disfuncion metabolica. | Racional de ensayos de senoliticos por indicacion. | Childs et al., Nat Med 2015 |
| `AGE-162` | **Genetic clearance model (INK-ATTAC)** | modalidad | Modelo transgenico que elimina celulas p16-altas y demuestra causalidad. | Prueba de concepto del aclaramiento senescente. | Baker et al., Nature 2011/2016 |

[volver al indice](#indice)

## Agotamiento de celulas madre y regeneracion
<a id="agotamiento-de-celulas-madre-y-regeneracion"></a>

*Capa: cellular | 12 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `AGE-163` | **Stem cell exhaustion** | proceso | Declive del numero y funcion de las celulas madre tisulares con la edad. | Diana de estrategias regenerativas. | Lopez-Otin et al., Cell 2013 |
| `AGE-164` | **Hematopoietic stem cell (HSC) aging** | proceso | Sesgo mieloide y perdida de potencial linfoide de las HSC envejecidas. | Nexo con inmunosenescencia y CHIP. | Rossi et al., PNAS 2005 |
| `AGE-165` | **Muscle satellite cell decline** | proceso | Perdida de capacidad regenerativa de las celulas satelite del musculo. | Diana frente a la sarcopenia. | Sousa-Victor et al., Nature 2014 |
| `AGE-166` | **Neural stem cell (NSC) decline** | proceso | Reduccion de la neurogenesis y de las NSC en nichos adultos. | Contexto de deterioro cognitivo. | Molofsky et al., Nature 2006 |
| `AGE-167` | **Intestinal stem cell aging** | proceso | Alteracion de la homeostasis del epitelio intestinal por ISC envejecidas. | Nexo con barrera y microbioma. | Lopez-Otin et al., Cell 2013 |
| `AGE-168` | **Mesenchymal stem cell aging** | proceso | Perdida de potencia y sesgo diferenciativo de las MSC con la edad. | Contexto de hueso y estroma. | Lopez-Otin et al., Cell 2013 |
| `AGE-169` | **Stem cell niche aging** | proceso | Deterioro del microambiente que sostiene y regula las celulas madre. | Diana de rejuvenecimiento del nicho. | Conboy et al., Nature 2005 |
| `AGE-170` | **Wnt signaling shift in aged niche** | proceso | Cambios en la senal Wnt del nicho que sesgan la diferenciacion con la edad. | Nexo regeneracion-envejecimiento. | Brack et al., Science 2007 |
| `AGE-171` | **Notch signaling in regeneration** | proceso | Via de contacto que regula activacion y autorrenovacion; su senal decae con la edad. | Diana de la regeneracion muscular. | Conboy et al., Nature 2005 |
| `AGE-172` | **Loss of asymmetric division / polarity** | proceso | Perdida de la division asimetrica que altera el balance autorrenovacion-diferenciacion. | Fuente de agotamiento del reservorio. | Florian et al., Cell Stem Cell 2012 |
| `AGE-173` | **Quiescence-activation imbalance** | proceso | Desequilibrio entre reposo y activacion que agota o inmoviliza el reservorio. | Diana de la homeostasis del reservorio. | Sousa-Victor et al., Nature 2014 |
| `AGE-174` | **Heterochronic parabiosis rejuvenation** | modalidad | La exposicion a sangre joven restaura parcialmente la funcion de celulas madre viejas. | Base experimental de factores sistemicos. | Conboy et al., Nature 2005 |

[volver al indice](#indice)

## Comunicacion intercelular alterada
<a id="comunicacion-intercelular-alterada"></a>

*Capa: tissue | 12 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `AGE-175` | **Endocrine dysregulation with age** | proceso | Cambios hormonales sistemicos (GH, esteroides, insulina) que reprograman tejidos. | Contexto de terapias endocrinas del envejecimiento. | Lopez-Otin et al., Cell 2013 |
| `AGE-176` | **GDF11 (systemic factor, debated)** | diana | Factor circulante propuesto como rejuvenecedor, con resultados debatidos. | Ilustra la complejidad de los factores sistemicos. | Loffredo et al., Cell 2013 |
| `AGE-177` | **CCL11 / eotaxin (pro-aging factor)** | biomarcador | Quimiocina que aumenta con la edad y se asocia a menor neurogenesis. | Biomarcador de envejecimiento sistemico. | Villeda et al., Nature 2011 |
| `AGE-178` | **Beta-2 microglobulin (pro-aging factor)** | biomarcador | Proteina sistemica cuyo aumento deteriora la funcion cognitiva en modelos. | Diana de factores plasmaticos deletereos. | Smith et al., Nat Med 2015 |
| `AGE-179` | **Extracellular vesicles / exosomes in aging** | proceso | Vesiculas que transportan ARNs y proteinas modulando funcion a distancia. | Biomarcadores y vehiculos terapeuticos. | Lopez-Otin et al., Cell 2023 |
| `AGE-180` | **Circulating cell-free / mtDNA** | biomarcador | ADN libre e mtDNA circulante que actua como senal inflamatoria (DAMP). | Nexo con inflammaging. | Pinti et al., Eur J Immunol 2014 |
| `AGE-181` | **Hypothalamic control of aging (NF-kB/GnRH)** | proceso | El hipotalamo integra inflamacion (NF-kB) y GnRH para regular el ritmo de envejecimiento sistemico. | Diana neuroendocrina emergente. | Zhang et al., Nature 2013 |
| `AGE-182` | **Plasma proteomic aging signals** | biomarcador | Firmas del proteoma plasmatico que cambian por olas a lo largo de la vida. | Base de relojes proteomicos. | Lehallier et al., Nat Med 2019 |
| `AGE-183` | **Systemic TGF-beta increase** | proceso | Aumento de la senal TGF-beta sistemica que inhibe regeneracion con la edad. | Diana combinada en rejuvenecimiento. | Yousef et al., Nat Med 2019 |
| `AGE-184` | **Renin-angiotensin system in aging** | proceso | Sobreactivacion del RAS que promueve fibrosis, inflamacion y disfuncion vascular. | Nexo con farmacos cardiovasculares. | Lopez-Otin et al., Cell 2013 |
| `AGE-185` | **Autonomic / sympathetic dysregulation** | proceso | Desbalance autonomico que afecta metabolismo, inmunidad y funcion cardiovascular. | Contexto de la fragilidad sistemica. | Lopez-Otin et al., Cell 2013 |
| `AGE-186` | **Gap junction / connexin changes** | proceso | Alteraciones en la comunicacion directa celula-a-celula por conexinas. | Modula propagacion de senales de estres. | Lopez-Otin et al., Cell 2013 |

[volver al indice](#indice)

## Inflammaging e inmunosenescencia
<a id="inflammaging-e-inmunosenescencia"></a>

*Capa: tissue | 14 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `AGE-187` | **Inflammaging** | proceso | Estado proinflamatorio cronico, esteril y de bajo grado que acompana al envejecimiento. | Diana de antiinflamatorios dirigidos. | Franceschi et al., Ann NY Acad Sci 2000 |
| `AGE-188` | **Immunosenescence** | proceso | Remodelado y declive de la inmunidad adaptativa e innata con la edad. | Contexto de vacunas y de infeccion en mayores. | Nikolich-Zugich, Nat Immunol 2018 |
| `AGE-189` | **Thymic involution** | proceso | Atrofia del timo que reduce la produccion de linfocitos T naive. | Diana de estrategias de regeneracion timica. | Palmer, Front Immunol 2013 |
| `AGE-190` | **Naive/memory T-cell shift** | proceso | Contraccion del compartimento naive y expansion de memoria con la edad. | Limita respuesta a antigenos nuevos. | Nikolich-Zugich, Nat Immunol 2018 |
| `AGE-191` | **T-cell senescence (CD28 loss)** | biomarcador | Acumulacion de linfocitos T con perdida de CD28 y funcion alterada. | Marcador de inmunosenescencia. | Nikolich-Zugich, Nat Immunol 2018 |
| `AGE-192` | **Chronic CMV / infection burden** | proceso | La infeccion cronica (p.ej. CMV) consume y sesga el repertorio inmune. | Factor de la 'huella inmune' del envejecimiento. | Nikolich-Zugich, Nat Immunol 2018 |
| `AGE-193` | **NLRP3 inflammasome activation** | diana | Plataforma que procesa IL-1beta e IL-18 y se activa cronicamente con la edad. | Diana de inhibidores del inflamasoma. | Youm et al., Cell Metab 2013 |
| `AGE-194` | **IL-6 as inflammaging driver** | biomarcador | Citocina cuya elevacion predice fragilidad, discapacidad y mortalidad. | Biomarcador y diana antiinflamatoria. | Ferrucci & Fabbri, Nat Rev Cardiol 2018 |
| `AGE-195` | **Chronic TNF-alpha elevation** | biomarcador | Aumento sostenido de TNF-alfa que promueve catabolismo e inflamacion. | Contexto de terapias anti-TNF. | Franceschi et al., Ann NY Acad Sci 2000 |
| `AGE-196` | **cGAS-STING innate sensing in aging** | proceso | Sensado de ADN citosolico que amplifica la inflamacion esteril del envejecimiento. | Diana antiinflamatoria emergente. | Gluck et al., Nat Cell Biol 2017 |
| `AGE-197` | **SASP-driven inflammation** | proceso | Las celulas senescentes alimentan el inflammaging a traves de su SASP. | Nexo senescencia-inflamacion; diana senolitica. | Coppe et al., PLoS Biol 2008 |
| `AGE-198` | **Macrophage dysfunction / polarization** | proceso | Cambios en polarizacion y funcion de macrofagos que sostienen inflamacion tisular. | Diana de reprogramacion mieloide. | Nikolich-Zugich, Nat Immunol 2018 |
| `AGE-199` | **Complement dysregulation** | proceso | Activacion aberrante del complemento que contribuye a dano tisular con la edad. | Contexto de degeneracion macular y neuroinflamacion. | Lopez-Otin et al., Cell 2013 |
| `AGE-200` | **Myeloid skewing / trained immunity** | proceso | Sesgo hacia produccion mieloide y memoria innata que altera el tono inflamatorio. | Nexo con CHIP e inflammaging. | Nikolich-Zugich, Nat Immunol 2018 |

[volver al indice](#indice)

## Disbiosis del microbioma
<a id="disbiosis-del-microbioma"></a>

*Capa: tissue | 10 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `AGE-201` | **Gut microbiome aging** | proceso | Reconfiguracion de la composicion microbiana intestinal a lo largo de la vida. | Diana de intervenciones dieteticas y probioticas. | Lopez-Otin et al., Cell 2023 |
| `AGE-202` | **Loss of microbial diversity** | biomarcador | Descenso de la diversidad taxonomica asociado a fragilidad en mayores. | Marcador de salud del microbioma. | Claesson et al., Nature 2012 |
| `AGE-203` | **Akkermansia muciniphila decline** | biomarcador | Reduccion de A. muciniphila, bacteria asociada a integridad de mucosa y metabolismo. | Candidata probiotica de nueva generacion. | Lopez-Otin et al., Cell 2023 |
| `AGE-204` | **SCFA / butyrate decline** | proceso | Menor produccion de acidos grasos de cadena corta antiinflamatorios y troficos. | Diana de prebioticos y fibra. | Lopez-Otin et al., Cell 2023 |
| `AGE-205` | **Gut barrier permeability (LPS translocation)** | proceso | Perdida de integridad de barrera que permite translocacion de LPS e inflamacion. | Nexo 'leaky gut'-inflammaging. | Thevaranjan et al., Cell Host Microbe 2017 |
| `AGE-206` | **Microbiome-immune axis** | proceso | Dialogo entre microbiota y sistema inmune que modula el tono inflamatorio sistemico. | Diana inmunometabolica. | Thevaranjan et al., Cell Host Microbe 2017 |
| `AGE-207` | **Gut-brain axis in aging** | proceso | Comunicacion bidireccional intestino-cerebro que influye en cognicion y neuroinflamacion. | Contexto de neurodegeneracion. | Lopez-Otin et al., Cell 2023 |
| `AGE-208` | **Microbiota transfer rejuvenation (model)** | modalidad | El trasplante de microbiota joven mejora fenotipos en modelos animales envejecidos. | Prueba de concepto de causalidad. | Parker et al., Microbiome 2022 |
| `AGE-209` | **Probiotics / prebiotics interventions** | modalidad | Modulacion dirigida de la microbiota para restaurar funciones perdidas. | Estrategia dietetica en estudio. | Lopez-Otin et al., Cell 2023 |
| `AGE-210` | **Microbial metabolites (indoles, TMAO)** | biomarcador | Metabolitos derivados de microbiota con efectos sistemicos beneficiosos o adversos. | Biomarcadores y dianas metabolicas. | Lopez-Otin et al., Cell 2023 |

[volver al indice](#indice)

## Fisiologia de sistemas y fenotipos del envejecimiento
<a id="fisiologia-de-sistemas-y-fenotipos-del-envejecimiento"></a>

*Capa: tissue | 16 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `AGE-211` | **Frailty (clinical phenotype)** | biomarcador | Sindrome de vulnerabilidad por declive multisistemico y baja reserva fisiologica. | Endpoint clinico de la geroterapeutica. | Fried et al., J Gerontol 2001 |
| `AGE-212` | **Sarcopenia** | proceso | Perdida progresiva de masa y funcion muscular esqueletica con la edad. | Diana de ejercicio, proteina y mitofagia. | Cruz-Jentoft et al., Age Ageing 2019 |
| `AGE-213` | **Osteoporosis / bone aging** | proceso | Perdida de densidad y microarquitectura osea por desbalance remodelador. | Diana de terapias oseas; nexo con senescencia. | Farr et al., Nat Med 2017 |
| `AGE-214` | **Vascular aging / arterial stiffness** | proceso | Rigidez arterial por remodelado de matriz y calcificacion con la edad. | Predictor cardiovascular; diana de intervencion. | Lakatta & Levy, Circulation 2003 |
| `AGE-215` | **Endothelial dysfunction** | proceso | Menor biodisponibilidad de oxido nitrico y disfuncion del endotelio vascular. | Diana de ejercicio y moduladores vasculares. | Lakatta & Levy, Circulation 2003 |
| `AGE-216` | **Cardiac aging (diastolic dysfunction)** | proceso | Hipertrofia, fibrosis y disfuncion diastolica del corazon envejecido. | Nexo con senescencia y metabolismo. | Lakatta & Levy, Circulation 2003 |
| `AGE-217` | **Skin aging (collagen/elastin loss)** | proceso | Perdida de colageno y elastina con adelgazamiento y arrugas dermicas. | Modelo visible de senescencia y matriz. | Lopez-Otin et al., Cell 2013 |
| `AGE-218` | **Advanced glycation end-products (AGEs)** | proceso | Entrecruzamiento no enzimatico de proteinas de larga vida por glicacion. | Diana de rompedores de crosslinks (investigacion). | Semba et al., J Gerontol 2010 |
| `AGE-219` | **Extracellular matrix stiffening** | proceso | Endurecimiento de la matriz por crosslinking que altera mecanotransduccion. | Nexo con fibrosis y funcion tisular. | Lopez-Otin et al., Cell 2013 |
| `AGE-220` | **Renal aging (nephron loss)** | proceso | Descenso del filtrado glomerular por perdida de nefronas y fibrosis. | Contexto de senescencia renal. | Lopez-Otin et al., Cell 2013 |
| `AGE-221` | **Pulmonary aging** | proceso | Perdida de retraccion elastica y capacidad de reparacion pulmonar. | Nexo con senescencia y fibrosis. | Lopez-Otin et al., Cell 2013 |
| `AGE-222` | **Cognitive decline / brain aging** | proceso | Atrofia, menor plasticidad y neuroinflamacion que deterioran la cognicion. | Interfaz con neurodegeneracion. | Mattson & Arumugam, Cell Metab 2018 |
| `AGE-223` | **Sensory decline (presbyopia/presbycusis)** | proceso | Perdida progresiva de vision de cerca y de audicion con la edad. | Fenotipos funcionales prevalentes. | Lopez-Otin et al., Cell 2013 |
| `AGE-224` | **Visceral adiposity / immunometabolic decline** | proceso | Redistribucion de grasa e inflamacion metabolica que agravan la resistencia insulinica. | Diana de intervenciones metabolicas. | Lopez-Otin et al., Cell 2013 |
| `AGE-225` | **Reproductive / ovarian aging (menopause)** | proceso | Agotamiento folicular y cese de la funcion ovarica como envejecimiento acelerado de organo. | Modelo de envejecimiento organo-especifico. | Lopez-Otin et al., Cell 2023 |
| `AGE-226` | **Hair graying (melanocyte SC depletion)** | proceso | Perdida de celulas madre melanociticas que despigmenta el cabello. | Fenotipo visible de agotamiento de reservorio. | Nishimura et al., Science 2005 |

[volver al indice](#indice)

## Organismos modelo y geroprincipios
<a id="organismos-modelo-y-geroprincipios"></a>

*Capa: meta | 14 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `AGE-227` | **Saccharomyces cerevisiae** | modelo | Levadura con envejecimiento replicativo y cronologico; origen del concepto de circulos de rDNA. | Cribado genetico de longevidad. | Sinclair & Guarente, Cell 1997 |
| `AGE-228` | **Caenorhabditis elegans** | modelo | Nematodo cuyo mutante daf-2 duplica la vida; sistema fundacional de la gerociencia. | Descubrimiento de vias de longevidad. | Kenyon et al., Nature 1993 |
| `AGE-229` | **Drosophila melanogaster** | modelo | Mosca usada para diseccionar dieta, IIS y mTOR en la longevidad. | Validacion de intervenciones conservadas. | Partridge et al., Nat Rev Genet 2005 |
| `AGE-230` | **Mus musculus (lab mouse)** | modelo | Mamifero de referencia para intervenciones farmacologicas y geneticas de longevidad. | Puente a la traduccion clinica. | Miller et al., Aging Cell 2005 |
| `AGE-231` | **Genetically heterogeneous mouse (UM-HET3)** | modelo | Cepa hibrida de cuatro vias usada por el ITP para robustez de resultados. | Estandar del cribado geroprotector. | Miller et al., Aging Cell 2011 |
| `AGE-232` | **Naked mole-rat** | modelo | Roedor extraordinariamente longevo con mortalidad casi independiente de la edad. | Modelo de resistencia al cancer y senescencia. | Ruby et al., eLife 2018 |
| `AGE-233` | **Killifish (Nothobranchius furzeri)** | modelo | Vertebrado de vida ultracorta ideal para estudios acelerados de envejecimiento. | Cribado vertebrado rapido. | Harel et al., Cell 2015 |
| `AGE-234` | **Comparative biology of long-lived species** | marco | El estudio de especies longevas (murcielagos, ballenas) revela mecanismos de proteccion. | Fuente de dianas geroprotectoras. | Gorbunova et al., Nat Rev Genet 2014 |
| `AGE-235` | **Ames / Snell dwarf mice** | modelo | Ratones enanos con deficit de GH que viven notablemente mas. | Prueba del eje GH-IGF en longevidad. | Bartke, Endocrinology 2005 |
| `AGE-236` | **Laron syndrome (GHR deficiency)** | modelo | Humanos con receptor de GH deficiente y baja incidencia de cancer y diabetes. | Correlato humano del eje GH-IGF. | Guevara-Aguirre et al., Sci Transl Med 2011 |
| `AGE-237` | **Centenarian genetics (FOXO3, APOE)** | marco | Variantes en FOXO3 y APOE enriquecidas en longevidad humana extrema. | Dianas geneticas de longevidad. | Willcox et al., PNAS 2008 |
| `AGE-238` | **Progeroid syndromes as models** | modelo | Enfermedades de envejecimiento acelerado (HGPS, Werner) que aislan hallmarks. | Modelos humanos de mecanismos concretos. | Lopez-Otin et al., Cell 2013 |
| `AGE-239` | **Peto's paradox** | marco | La ausencia de correlacion entre tamano corporal y cancer implica supresores extra en especies grandes. | Racional de mecanismos anti-cancer naturales. | Caulin & Maley, Trends Ecol Evol 2011 |
| `AGE-240` | **Negligible senescence** | marco | Especies sin aumento detectable de mortalidad con la edad (algunas tortugas, hidra). | Limite superior conceptual de la longevidad. | Jones et al., Nature 2014 |

[volver al indice](#indice)

## Biomarcadores y relojes del envejecimiento
<a id="biomarcadores-y-relojes-del-envejecimiento"></a>

*Capa: meta | 12 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `AGE-241` | **Epigenetic clocks (overview)** | biomarcador | Estimadores de edad basados en patrones de metilacion del ADN. | Endpoints candidatos de ensayos geroprotectores. | Horvath & Raj, Nat Rev Genet 2018 |
| `AGE-242` | **Biological vs chronological age** | marco | Distincion entre edad transcurrida y estado funcional/molecular del organismo. | Marco de medicion de intervenciones. | Ferrucci et al., Nat Aging 2020 |
| `AGE-243` | **Frailty index (deficit accumulation)** | biomarcador | Indice que cuantifica la acumulacion de deficits de salud. | Predictor robusto de resultados adversos. | Mitnitski et al., ScientificWorldJournal 2001 |
| `AGE-244` | **Proteomic aging clocks** | biomarcador | Relojes basados en firmas del proteoma plasmatico. | Prediccion multiorgano del envejecimiento. | Lehallier et al., Nat Med 2019 |
| `AGE-245` | **Metabolomic clocks** | biomarcador | Estimadores de edad a partir de perfiles de metabolitos circulantes. | Complemento metabolico de los relojes. | Ferrucci et al., Nat Aging 2020 |
| `AGE-246` | **Transcriptomic aging signatures** | biomarcador | Firmas de expresion genica asociadas a la edad tisular. | Base de relojes transcriptomicos. | Peters et al., Nat Commun 2015 |
| `AGE-247` | **Inflammatory aging clock (iAge)** | biomarcador | Reloj basado en marcadores inflamatorios que predice multimorbilidad. | Cuantifica el inflammaging. | Sayed et al., Nat Aging 2021 |
| `AGE-248` | **Glycan / IgG glycosylation age (GlycanAge)** | biomarcador | Cambios en la glicosilacion de IgG que reflejan estado inflamatorio y edad. | Biomarcador inmunometabolico. | Kristic et al., J Gerontol 2014 |
| `AGE-249` | **Composite clinical biomarkers (PhenoAge)** | biomarcador | Combinacion de parametros de laboratorio clinico en una edad fenotipica. | Predictor de mortalidad accesible. | Levine et al., Aging 2018 |
| `AGE-250` | **Functional biomarkers (grip, gait speed)** | biomarcador | Fuerza de prension y velocidad de marcha como indicadores funcionales de edad. | Predictores clinicos simples y robustos. | Studenski et al., JAMA 2011 |
| `AGE-251` | **Imaging aging clocks (brain, retina)** | biomarcador | Estimadores de edad a partir de imagenes cerebrales o retinianas. | Prediccion de riesgo por organo. | Cole & Franke, Trends Neurosci 2017 |
| `AGE-252` | **Surrogate endpoints for geroscience (TAME)** | marco | Diseno de ensayos con multimorbilidad como endpoint para probar geroprotectores. | Marco regulatorio de la geroterapeutica. | Barzilai et al., Cell Metab 2016 |

[volver al indice](#indice)

## Geroterapeutica y modalidades
<a id="geroterapeutica-y-modalidades"></a>

*Capa: therapy | 22 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `AGE-253` | **Caloric restriction (intervention)** | modalidad | Reduccion sostenida de calorias sin desnutricion como intervencion geroprotectora. | Referencia; ensayo humano CALERIE. | Fontana et al., Science 2010 |
| `AGE-254` | **Fasting-mimicking diet** | modalidad | Ciclos dieteticos que reproducen efectos del ayuno con menor carga. | Mejora marcadores metabolicos en humanos. | Wei et al., Sci Transl Med 2017 |
| `AGE-255` | **Rapamycin / rapalogs** | modalidad | Inhibicion de mTORC1 que extiende vida y mejora funcion inmune. | Geroprotector mejor validado en mamiferos. | Harrison et al., Nature 2009 |
| `AGE-256` | **Metformin** | modalidad | Biguanida que modula el complejo I mitocondrial y AMPK. | Ensayo TAME propuesto como prueba de geroproteccion. | Barzilai et al., Cell Metab 2016 |
| `AGE-257` | **Senolytics (D+Q, fisetin, navitoclax)** | modalidad | Farmacos que eliminan celulas senescentes y mejoran healthspan. | Ensayos clinicos por indicacion en curso. | Kirkland & Tchkonia, EBioMedicine 2017 |
| `AGE-258` | **Senomorphics (SASP inhibitors)** | modalidad | Agentes que atenuan el secretoma senescente sin eliminar la celula. | Alternativa moduladora del SASP. | Kirkland & Tchkonia, EBioMedicine 2017 |
| `AGE-259` | **NAD+ boosters (NR, NMN)** | modalidad | Precursores que restauran el NAD+ decaido con la edad. | Ensayos humanos de seguridad y biomarcadores. | Rajman et al., Cell Metab 2018 |
| `AGE-260` | **Spermidine supplementation** | modalidad | Poliamina inductora de autofagia con asociacion epidemiologica a menor mortalidad. | Intervencion nutricional en estudio. | Eisenberg et al., Nat Med 2016 |
| `AGE-261` | **Partial epigenetic reprogramming (OSK/OSKM)** | modalidad | Reprogramacion transitoria que revierte marcas de edad preservando identidad. | Rejuvenecimiento en investigacion preclinica. | Lu et al., Nature 2020 |
| `AGE-262` | **Sirtuin activators (STACs, resveratrol)** | modalidad | Moleculas que activan sirtuinas dependientes de NAD+. | Efectos y traduccion debatidos. | Howitz et al., Nature 2003 |
| `AGE-263` | **Acarbose (alpha-glucosidase inhibitor)** | modalidad | Enlentece la absorcion de glucosa reduciendo los picos posprandiales. | Extiende vida en raton (ITP), sesgo por sexo. | Harrison et al., Aging Cell 2014 |
| `AGE-264` | **17-alpha-estradiol** | modalidad | Estrogeno debilmente feminizante con efectos metabolicos geroprotectores. | Extiende vida en raton macho (ITP). | Harrison et al., Aging Cell 2014 |
| `AGE-265` | **SGLT2 inhibitors (canagliflozin)** | modalidad | Promueven glucosuria y mejoran el perfil metabolico. | Extiende vida en raton macho (ITP). | Miller et al., JCI Insight 2020 |
| `AGE-266` | **GLP-1 receptor agonists** | modalidad | Incretinomimeticos que mejoran metabolismo, peso e inflamacion. | Interes emergente en envejecimiento metabolico. | Lopez-Otin et al., Cell 2023 |
| `AGE-267` | **Taurine supplementation** | modalidad | Aminoacido sulfonado cuyo declive se asocia a envejecimiento en modelos. | Extiende salud/vida en animales (traduccion pendiente). | Singh et al., Science 2023 |
| `AGE-268` | **Urolithin A (Mitopure)** | modalidad | Inductor de mitofagia derivado de la microbiota que mejora funcion muscular. | Ensayos humanos de rendimiento muscular. | Ryu et al., Nat Med 2016 |
| `AGE-269` | **Exercise (geroprotective)** | modalidad | Estimulo que activa AMPK, PGC-1alfa, mitofagia y mejora casi todos los hallmarks. | Geroprotector no farmacologico mejor establecido. | Garatachea et al., Rejuvenation Res 2015 |
| `AGE-270` | **Therapeutic plasma exchange / dilution** | modalidad | Dilucion del plasma viejo que rejuvenece tejidos en modelos animales. | Prueba de concepto de factores sistemicos. | Mehdipour et al., Aging 2020 |
| `AGE-271` | **Young plasma / systemic factors** | modalidad | Transferencia de factores circulantes jovenes con efectos rejuvenecedores parciales. | Base de la parabiosis heterocronica. | Conboy et al., Nature 2005 |
| `AGE-272` | **Gene therapy (TERT, follistatin, Klotho)** | modalidad | Vectores que expresan factores geroprotectores en modelos animales. | Estrategia experimental de longevidad. | Bernardes de Jesus et al., EMBO Mol Med 2012 |
| `AGE-273` | **Alpha-ketoglutarate (Ca-AKG)** | modalidad | Metabolito del ciclo de Krebs con efectos epigeneticos y sobre la salud. | Mejora healthspan en raton (preclinico). | Shahmirzadi et al., Cell Metab 2020 |
| `AGE-274` | **GlyNAC (glycine + N-acetylcysteine)** | modalidad | Combinacion que restaura glutation y funcion mitocondrial en mayores. | Pilotos humanos de biomarcadores. | Kumar et al., J Gerontol 2023 |

[volver al indice](#indice)

## Primitivas intervencion -> diana
<a id="primitivas-intervencion-diana"></a>

*Capa: therapy | 26 primitivas*

| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `AGE-275` | **Rapamycin -> mTORC1** | intervencion->diana | Inhibe mTORC1 y desreprime autofagia; iniciado a los 600 dias extendio la vida (+9% machos, +14% hembras al 90% de mortalidad). | Geroprotector de referencia; a 42 ppm hasta +23/26%. | Harrison et al., Nature 2009 |
| `AGE-276` | **Metformin -> Complex I / AMPK** | intervencion->diana | Inhibe el complejo I mitocondrial y activa AMPK, remodelando el metabolismo energetico. | Base del ensayo TAME de geroproteccion. | Barzilai et al., Cell Metab 2016 |
| `AGE-277` | **Dasatinib + Quercetin -> senescent cells** | intervencion->diana | Combinacion senolitica que elimina celulas senescentes; en raton viejo aumento la supervivencia post-tratamiento ~36%. | Prototipo de senolitico intermitente. | Xu et al., Nat Med 2018 |
| `AGE-278` | **Fisetin -> senescent cells** | intervencion->diana | Flavonoide senolitico que reduce la carga senescente y prolonga vida en raton. | En ensayos clinicos por indicacion. | Yousefzadeh et al., EBioMedicine 2018 |
| `AGE-279` | **Navitoclax (ABT-263) -> BCL-2/BCL-xL** | intervencion->diana | Mimetico BH3 que mata celulas senescentes dependientes de anti-apoptoticos. | Senolitico potente, con toxicidad plaquetaria. | Zhu et al., Aging Cell 2016 |
| `AGE-280` | **Nicotinamide riboside -> NAD+** | intervencion->diana | Precursor que eleva NAD+ intracelular via la ruta de salvamento. | Ensayos humanos muestran subida de NAD+. | Rajman et al., Cell Metab 2018 |
| `AGE-281` | **NMN -> NAD+** | intervencion->diana | Mononucleotido que repone NAD+ y mejora funcion metabolica en modelos. | Ensayos humanos tempranos de metabolismo. | Yoshino et al., Cell Metab 2018 |
| `AGE-282` | **Spermidine -> autophagy (EP300)** | intervencion->diana | Inhibe acetiltransferasas (EP300) induciendo autofagia protectora. | Asociacion epidemiologica con menor mortalidad. | Eisenberg et al., Nat Cell Biol 2009 |
| `AGE-283` | **Resveratrol -> SIRT1** | intervencion->diana | Activador propuesto de SIRT1 que imita parte de la restriccion calorica. | Mecanismo y traduccion clinica debatidos. | Howitz et al., Nature 2003 |
| `AGE-284` | **OSKM (Yamanaka) -> epigenetic reprogramming** | intervencion->diana | Factores que revierten marcas epigeneticas de edad; restauran vision en glaucoma murino. | Rejuvenecimiento parcial en investigacion. | Lu et al., Nature 2020 |
| `AGE-285` | **Acarbose -> intestinal alpha-glucosidase** | intervencion->diana | Reduce picos de glucosa posprandiales; en raton extendio la vida (+22% machos, ITP). | Geroprotector con efecto sexo-dependiente. | Harrison et al., Aging Cell 2014 |
| `AGE-286` | **17-alpha-estradiol -> weak ER signaling** | intervencion->diana | Actua sobre senal estrogenica sin feminizacion completa; +12% de vida en raton macho (ITP). | Geroprotector especifico de machos. | Harrison et al., Aging Cell 2014 |
| `AGE-287` | **Canagliflozin -> SGLT2** | intervencion->diana | Inhibe el cotransportador renal SGLT2; +14% de vida mediana en raton macho (ITP). | Beneficio ausente en hembras. | Miller et al., JCI Insight 2020 |
| `AGE-288` | **Taurine -> multi-hallmark modulation** | intervencion->diana | Repone taurina decaida y reduce senescencia, dano de ADN e inflammaging; +10-12% de vida mediana en raton. | Traduccion humana pendiente de ensayos. | Singh et al., Science 2023 |
| `AGE-289` | **Urolithin A -> mitophagy** | intervencion->diana | Induce mitofagia mejorando la funcion mitocondrial del musculo. | Ensayos humanos de resistencia muscular. | Ryu et al., Nat Med 2016 |
| `AGE-290` | **INK-ATTAC -> p16-high senescent cells** | intervencion->diana | Sistema genetico que elimina celulas p16-altas y demuestra causalidad de la senescencia. | Prueba de concepto del aclaramiento senescente. | Baker et al., Nature 2016 |
| `AGE-291` | **Rapamycin + Acarbose -> mTOR + glucose** | intervencion->diana | Combinacion que suma inhibicion de mTOR y control glucemico; +34% machos y +28% hembras (ITP, inicio 9 meses). | Sinergia de vias de longevidad. | Strong et al., Aging Cell 2022 |
| `AGE-292` | **Klotho -> FGF23 / cognition** | intervencion->diana | Hormona anti-edad que modula fosfato e IIS; su elevacion mejora cognicion en modelos. | Diana sistemica emergente. | Kurosu et al., Science 2005 |
| `AGE-293` | **Elamipretide (SS-31) -> cardiolipin** | intervencion->diana | Peptido que estabiliza cardiolipina y las cristas mitocondriales. | Ensayos en miopatias mitocondriales. | Szeto, Br J Pharmacol 2014 |
| `AGE-294` | **Alpha-ketoglutarate -> epigenetic/metabolic** | intervencion->diana | Cofactor de dioxigenasas (TET, KDM) que enlaza metabolismo y epigenetica. | Mejora healthspan en raton (preclinico). | Shahmirzadi et al., Cell Metab 2020 |
| `AGE-295` | **GlyNAC -> glutathione synthesis** | intervencion->diana | Aporta glicina y cisteina para restaurar glutation y aliviar estres oxidativo. | Pilotos humanos de biomarcadores de edad. | Kumar et al., J Gerontol 2023 |
| `AGE-296` | **Sulforaphane -> NRF2** | intervencion->diana | Activa la respuesta antioxidante NRF2-KEAP1 induciendo defensas citoprotectoras. | Nutraceutico en estudio. | Santin-Marquez et al., Geroscience 2019 |
| `AGE-297` | **Low-dose lithium -> GSK-3 / autophagy** | intervencion->diana | Modula GSK-3 e induce autofagia; prolonga vida en invertebrados y se asocia a longevidad poblacional. | Senal geroprotectora en investigacion. | Zarse et al., Cell Metab 2011 |
| `AGE-298` | **Fisetin -> broad senolysis** | intervencion->diana | Senolitico natural de amplio espectro que reduce marcadores de senescencia. | Ensayos clinicos en marcha. | Yousefzadeh et al., EBioMedicine 2018 |
| `AGE-299` | **MOTS-c -> AMPK (exercise mimetic)** | intervencion->diana | Peptido mitocondrial que activa AMPK y mejora la homeostasis metabolica. | Mimetico de ejercicio (preclinico). | Lee et al., Cell Metab 2015 |
| `AGE-300` | **Exercise -> AMPK / PGC-1alpha / mitophagy** | intervencion->diana | Estimulo integral que activa sensores energeticos y biogenesis/limpieza mitocondrial. | Geroprotector no farmacologico de referencia. | Garatachea et al., Rejuvenation Res 2015 |

[volver al indice](#indice)

---

## Estadisticas
*300 primitivas | 18 categorias | 14 roles distintos*

| Rol | Primitivas |
| :--- | :---: |
| proceso | 138 |
| biomarcador | 40 |
| modalidad | 33 |
| intervencion->diana | 26 |
| diana | 25 |
| marco | 11 |
| modelo | 10 |
| hallmark primario | 4 |
| farmaco | 3 |
| hallmark antagonista | 3 |
| hallmark integrador | 2 |
| hallmark integrador (2023) | 2 |
| teoria evolutiva | 2 |
| hallmark primario (2023) | 1 |

---

## Nota metodologica
Las primitivas cubren desde los hallmarks del envejecimiento de Lopez-Otin et al. (Cell 2013; Cell 2023, 'Hallmarks of aging: an expanding universe') hasta pares intervencion->diana con evidencia preclinica o clinica registrada. Las referencias citan articulos o revisiones canonicas; los mecanismos reflejan conocimiento establecido a la fecha de generacion. Muchos resultados cuantitativos proceden de modelos animales (con marcado efecto de especie, sexo y dosis) y NO implican eficacia en humanos. Esto es material educativo y de modelado ontologico: **no sustituye juicio clinico ni investigacion primaria.**
