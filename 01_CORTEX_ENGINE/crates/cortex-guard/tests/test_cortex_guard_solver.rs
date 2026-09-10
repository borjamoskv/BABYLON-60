use cortex_guard::dsl::Rulebook;
use cortex_guard::eval::evaluate;
use cortex_guard::ifc::IfcModel;
use cortex_guard::sarif::generate_sarif;
use std::path::PathBuf;
use std::time::Instant;

const SAMPLE_INFRACTOR_IFC: &str = r#"ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');
FILE_NAME('test.ifc','2026-09-10T12:00:00',('Architect'),('Author'),'','','');
FILE_SCHEMA(('IFC4'));
ENDSEC;
DATA;
#1=IFCPROJECT('21A_XYZ',$,'Proyecto Infraccion',$,$,$,$,$,#2);
#10=IFCBUILDING('10A_XYZ',$,'Edificio Principal',$,$,$,$,$,.ELEMENT.,$,$,$);
#30=IFCWALL('30A_XYZ',$,'Fachada Norte',$,$,$,$,'WALL-001',.SOLIDWALL.);
#40=IFCPROPERTYSET('40A_XYZ',$,'Pset_EnvironmentalMetrics',$,(#41));
#41=IFCPROPERTYSINGLEVALUE('PrimaryEnergyConsumption',$,IFCENERGYMEASURE(31.4),$);
#50=IFCRELDEFINESBYPROPERTIES('50A_XYZ',$,$,$,(#10),#40);
#60=IFCPROPERTYSET('60A_XYZ',$,'Pset_WallCommon',$,(#61));
#61=IFCPROPERTYSINGLEVALUE('SetbackDistance',$,IFCLENGTHMEASURE(2.85),$);
#70=IFCRELDEFINESBYPROPERTIES('70A_XYZ',$,$,$,(#30),#60);
ENDSEC;
END-ISO-10303-21;
"#;

const SAMPLE_CONFORME_IFC: &str = r#"ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');
FILE_NAME('test.ifc','2026-09-10T12:00:00',('Architect'),('Author'),'','','');
FILE_SCHEMA(('IFC4'));
ENDSEC;
DATA;
#1=IFCPROJECT('21A_XYZ',$,'Proyecto Conforme',$,$,$,$,$,#2);
#10=IFCBUILDING('10A_XYZ',$,'Edificio Conforme',$,$,$,$,$,.ELEMENT.,$,$,$);
#30=IFCWALL('30A_XYZ',$,'Fachada Norte',$,$,$,$,'WALL-001',.SOLIDWALL.);
#40=IFCPROPERTYSET('40A_XYZ',$,'Pset_EnvironmentalMetrics',$,(#41));
#41=IFCPROPERTYSINGLEVALUE('PrimaryEnergyConsumption',$,IFCENERGYMEASURE(24.0),$);
#50=IFCRELDEFINESBYPROPERTIES('50A_XYZ',$,$,$,(#10),#40);
#60=IFCPROPERTYSET('60A_XYZ',$,'Pset_WallCommon',$,(#61));
#61=IFCPROPERTYSINGLEVALUE('SetbackDistance',$,IFCLENGTHMEASURE(3.50),$);
#70=IFCRELDEFINESBYPROPERTIES('70A_XYZ',$,$,$,(#30),#60);
ENDSEC;
END-ISO-10303-21;
"#;

const SAMPLE_RULEBOOK_YAML: &str = r#"
rules:
  - code: "ERR_042"
    title: "INCUMPLIMIENTO DE RETRANQUEO A LINDEROS"
    description: "Separacion minima a colindantes superada."
    target: "IFCWALL"
    property: "SetbackDistance"
    operator: ">="
    threshold: 3.0
    unit: "m"
    legal_citation: "PGOU Madrid - Seccion II, Art. 14.3.a"
    severity: "error"

  - code: "ERR_089"
    title: "EXCESO DE CONSUMO DE ENERGIA PRIMARIA"
    description: "Demanda termica supera el umbral limite."
    target: "IFCBUILDING"
    property: "PrimaryEnergyConsumption"
    operator: "<="
    threshold: 28.0
    unit: "kWh/m2·año"
    legal_citation: "CTE DB-HE0"
    severity: "error"
"#;

#[test]
fn test_ifc_step_parser_and_relation_linking() {
    let model = IfcModel::parse(SAMPLE_INFRACTOR_IFC, PathBuf::from("infractor.ifc")).expect("IFC parse failed");
    assert_eq!(model.entities.len(), 9);

    let walls = model.find_entities_by_type("IFCWALL");
    assert_eq!(walls.len(), 1);
    let wall = walls[0];
    assert_eq!(wall.id, 30);
    assert_eq!(wall.numeric_properties.get("SetbackDistance"), Some(&2.85));

    let buildings = model.find_entities_by_type("IFCBUILDING");
    assert_eq!(buildings.len(), 1);
    let building = buildings[0];
    assert_eq!(building.id, 10);
    assert_eq!(building.numeric_properties.get("PrimaryEnergyConsumption"), Some(&31.4));
}

#[test]
fn test_rulebook_yaml_parser() {
    let rulebook = Rulebook::parse(SAMPLE_RULEBOOK_YAML, &PathBuf::from("rules.yaml")).expect("YAML parse failed");
    assert_eq!(rulebook.rules.len(), 2);
    assert_eq!(rulebook.rules[0].code, "ERR_042");
    assert_eq!(rulebook.rules[1].code, "ERR_089");
}

#[test]
fn test_solver_infractor_detection() {
    let model = IfcModel::parse(SAMPLE_INFRACTOR_IFC, PathBuf::from("infractor.ifc")).unwrap();
    let rulebook = Rulebook::parse(SAMPLE_RULEBOOK_YAML, &PathBuf::from("rules.yaml")).unwrap();

    let result = evaluate(&model, &rulebook, "dummy_ifc_hash".into(), "dummy_pgou_hash".into(), Instant::now());
    assert_eq!(result.status, "UNSAT");
    assert_eq!(result.violations.len(), 2);

    let v42 = result.violations.iter().find(|v| v.code == "ERR_042").expect("ERR_042 missing");
    assert_eq!(v42.line, 10);
    assert!(v42.measured.contains("2.85"));
    assert!(v42.limit.contains("3.0"));

    let v89 = result.violations.iter().find(|v| v.code == "ERR_089").expect("ERR_089 missing");
    assert_eq!(v89.line, 9);
    assert!(v89.measured.contains("31.4"));
    assert!(v89.limit.contains("28.0"));

    // Check SARIF report generation
    let sarif = generate_sarif(&result);
    assert_eq!(sarif.runs.len(), 1);
    assert_eq!(sarif.runs[0].results.len(), 2);
}

#[test]
fn test_solver_conforme_acceptance() {
    let model = IfcModel::parse(SAMPLE_CONFORME_IFC, PathBuf::from("conforme.ifc")).unwrap();
    let rulebook = Rulebook::parse(SAMPLE_RULEBOOK_YAML, &PathBuf::from("rules.yaml")).unwrap();

    let result = evaluate(&model, &rulebook, "dummy_ifc_hash".into(), "dummy_pgou_hash".into(), Instant::now());
    assert_eq!(result.status, "SAT");
    assert_eq!(result.violations.len(), 0);

    let sarif = generate_sarif(&result);
    assert_eq!(sarif.runs[0].results.len(), 0);
}
