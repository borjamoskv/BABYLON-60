//! Deterministic STEP ISO 10303-21 IFC Parser for CORTEX-GUARD
//! C5-REAL Compliant: Zero-Alucination, Deterministic AST Extraction

use std::collections::HashMap;
use std::path::PathBuf;

#[derive(Debug, Clone)]
pub struct StepEntity {
    pub id: u64,
    pub name: String,
    pub raw_params: String,
    pub line_number: u32,
    pub numeric_properties: HashMap<String, f64>,
    #[allow(dead_code)]
    pub string_properties: HashMap<String, String>,
    pub coordinates: Option<(f64, f64, f64)>,
}

#[derive(Debug)]
pub struct IfcModel {
    pub entities: HashMap<u64, StepEntity>,
    pub file_path: PathBuf,
}

impl IfcModel {
    pub fn parse(content: &str, file_path: PathBuf) -> Result<Self, String> {
        let mut entities = HashMap::new();
        let mut in_data = false;

        let mut current_statement = String::new();
        let mut statement_start_line = 1u32;

        for (idx, line) in content.lines().enumerate() {
            let line_num = (idx + 1) as u32;
            let trimmed = line.trim();

            if trimmed == "DATA;" {
                in_data = true;
                continue;
            } else if trimmed == "ENDSEC;" && in_data {
                in_data = false;
                continue;
            }

            if !in_data {
                continue;
            }

            if current_statement.is_empty() {
                statement_start_line = line_num;
            }

            // Remove comments if any
            let clean_line = if let Some(pos) = trimmed.find("/*") {
                &trimmed[..pos]
            } else {
                trimmed
            };

            current_statement.push_str(clean_line);
            current_statement.push(' ');

            if current_statement.contains(';') {
                let parts: Vec<&str> = current_statement.split(';').collect();
                for part in parts.iter().take(parts.len() - 1) {
                    let stmt = part.trim();
                    if let Some(ent) = parse_step_statement(stmt, statement_start_line) {
                        entities.insert(ent.id, ent);
                    }
                }
                current_statement = parts.last().unwrap_or(&"").trim().to_string();
            }
        }

        // Second pass: Extract Cartesian Points (Coordinates)
        let mut coords_map: HashMap<u64, (f64, f64, f64)> = HashMap::new();
        for ent in entities.values() {
            if ent.name == "IFCCARTESIANPOINT" {
                if let Some(coords) = extract_cartesian_coords(&ent.raw_params) {
                    coords_map.insert(ent.id, coords);
                }
            }
        }

        // Third pass: Extract Property Single Values
        // Format: ('PropertyName', $, MEASURETYPE(123.45), $)
        let mut prop_values: HashMap<u64, (String, f64)> = HashMap::new();
        for ent in entities.values() {
            if ent.name == "IFCPROPERTYSINGLEVALUE" {
                if let Some((pname, pval)) = extract_property_single_value(&ent.raw_params) {
                    prop_values.insert(ent.id, (pname, pval));
                }
            }
        }

        // Fourth pass: Extract Property Sets
        // Format: ('GUID', $, 'PsetName', $, (#1, #2, #3))
        let mut pset_properties: HashMap<u64, HashMap<String, f64>> = HashMap::new();
        for ent in entities.values() {
            if ent.name == "IFCPROPERTYSET" {
                let mut map = HashMap::new();
                for ref_id in extract_ref_ids(&ent.raw_params) {
                    if let Some((pname, pval)) = prop_values.get(&ref_id) {
                        map.insert(pname.clone(), *pval);
                    }
                }
                pset_properties.insert(ent.id, map);
            }
        }

        // Fifth pass: Link Property Sets to Elements via IFCRELDEFINESBYPROPERTIES
        // Format: ('GUID', $, $, $, (#target1, #target2), #pset_id)
        let mut element_props: HashMap<u64, HashMap<String, f64>> = HashMap::new();
        for ent in entities.values() {
            if ent.name == "IFCRELDEFINESBYPROPERTIES" {
                if let Some((targets, pset_id)) = extract_rel_defines(&ent.raw_params) {
                    if let Some(props) = pset_properties.get(&pset_id) {
                        for target_id in targets {
                            element_props
                                .entry(target_id)
                                .or_default()
                                .extend(props.clone());
                        }
                    }
                }
            }
        }

        // Sixth pass: Link coordinates via Placements
        // IfcLocalPlacement -> IfcAxis2Placement3D -> IfcCartesianPoint
        let mut placement_coords: HashMap<u64, (f64, f64, f64)> = HashMap::new();
        for ent in entities.values() {
            if ent.name == "IFCAXIS2PLACEMENT3D" {
                let refs = extract_ref_ids(&ent.raw_params);
                if let Some(point_id) = refs.first() {
                    if let Some(c) = coords_map.get(point_id) {
                        placement_coords.insert(ent.id, *c);
                    }
                }
            }
        }

        let mut local_coords: HashMap<u64, (f64, f64, f64)> = HashMap::new();
        for ent in entities.values() {
            if ent.name == "IFCLOCALPLACEMENT" {
                let refs = extract_ref_ids(&ent.raw_params);
                // The second reference is typically the axis2placement3d
                for r in refs {
                    if let Some(c) = placement_coords.get(&r) {
                        local_coords.insert(ent.id, *c);
                        break;
                    }
                }
            }
        }

        // Assign resolved properties and spatial coordinates to entities
        for (ent_id, ent) in entities.iter_mut() {
            if let Some(props) = element_props.remove(ent_id) {
                ent.numeric_properties.extend(props);
            }

            // Also check direct placement references for coordinates
            for r in extract_ref_ids(&ent.raw_params) {
                if let Some(c) = local_coords.get(&r) {
                    ent.coordinates = Some(*c);
                    // Automatically add Setback / Coordinate properties if not present
                    ent.numeric_properties.entry("CoordinateX".to_string()).or_insert(c.0);
                    ent.numeric_properties.entry("CoordinateY".to_string()).or_insert(c.1);
                    ent.numeric_properties.entry("CoordinateZ".to_string()).or_insert(c.2);
                    ent.numeric_properties.entry("SetbackDistance".to_string()).or_insert(c.0.abs().min(c.1.abs()));
                    break;
                }
            }
        }

        Ok(Self { entities, file_path })
    }

    pub fn find_entities_by_type(&self, type_name: &str) -> Vec<&StepEntity> {
        let needle = type_name.to_uppercase();
        self.entities
            .values()
            .filter(|e| e.name == needle || e.name.replace('_', "") == needle)
            .collect()
    }
}

fn parse_step_statement(statement: &str, line_num: u32) -> Option<StepEntity> {
    // Expected: #123 = ENTITY_NAME(args...)
    let s = statement.trim();
    if !s.starts_with('#') {
        return None;
    }

    let eq_pos = s.find('=')?;
    let id_str = &s[1..eq_pos].trim();
    let id: u64 = id_str.parse().ok()?;

    let rest = s[eq_pos + 1..].trim();
    let paren_pos = rest.find('(')?;
    let name = rest[..paren_pos].trim().to_uppercase();

    if !rest.ends_with(')') {
        // Strip trailing tokens if any
    }
    let raw_params = rest[paren_pos + 1..rest.len() - 1].to_string();

    Some(StepEntity {
        id,
        name,
        raw_params,
        line_number: line_num,
        numeric_properties: HashMap::new(),
        string_properties: HashMap::new(),
        coordinates: None,
    })
}

fn extract_ref_ids(params: &str) -> Vec<u64> {
    let mut ids = Vec::new();
    let mut cur = String::new();
    let mut in_ref = false;

    for ch in params.chars() {
        if ch == '#' {
            in_ref = true;
            cur.clear();
        } else if in_ref {
            if ch.is_ascii_digit() {
                cur.push(ch);
            } else {
                if let Ok(id) = cur.parse::<u64>() {
                    ids.push(id);
                }
                in_ref = false;
                cur.clear();
            }
        }
    }

    if in_ref && !cur.is_empty() {
        if let Ok(id) = cur.parse::<u64>() {
            ids.push(id);
        }
    }

    ids
}

fn extract_cartesian_coords(params: &str) -> Option<(f64, f64, f64)> {
    // Format: ((x, y, z)) or (x, y, z)
    let open_p = params.find('(')?;
    let close_p = params.rfind(')')?;
    if close_p <= open_p {
        return None;
    }
    let inner = &params[open_p + 1..close_p];
    let nums: Vec<f64> = inner
        .split(',')
        .filter_map(|s| s.trim().trim_matches('(').trim_matches(')').parse::<f64>().ok())
        .collect();

    if nums.len() >= 3 {
        Some((nums[0], nums[1], nums[2]))
    } else if nums.len() == 2 {
        Some((nums[0], nums[1], 0.0))
    } else {
        None
    }
}

fn extract_property_single_value(params: &str) -> Option<(String, f64)> {
    // Format: ('PropertyName', $, IFCMEASURETYPE(value), ...)
    let first_quote = params.find('\'')?;
    let second_quote = params[first_quote + 1..].find('\'')? + first_quote + 1;
    let prop_name = params[first_quote + 1..second_quote].to_string();

    let after_name = &params[second_quote + 1..];
    // Find numeric value inside parentheses e.g. IFCENERGYMEASURE(31.4) or directly 31.4
    let val_open = after_name.find('(')?;
    let val_close = after_name[val_open + 1..].find(')')? + val_open + 1;
    let val_str = after_name[val_open + 1..val_close].trim();

    if let Ok(val) = val_str.parse::<f64>() {
        Some((prop_name, val))
    } else {
        None
    }
}

fn extract_rel_defines(params: &str) -> Option<(Vec<u64>, u64)> {
    // Format: ('GUID', $, $, $, (#target1, #target2), #pset)
    // Find the last reference which is #pset
    let refs = extract_ref_ids(params);
    if refs.len() >= 2 {
        let pset_id = *refs.last()?;
        let targets = refs[..refs.len() - 1].to_vec();
        Some((targets, pset_id))
    } else {
        None
    }
}
