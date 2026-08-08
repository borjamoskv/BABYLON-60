// C5-REAL EXERGY CERTIFIED
// Detector y Auditor de Plugins de Audio (AU, VST3, AAX)
use std::path::Path;

pub struct AudioPluginFilter;

impl AudioPluginFilter {
    pub const AUDIO_PATHS: [&'static str; 4] = [
        "/Library/Audio/Plug-Ins/Components",
        "/Library/Audio/Plug-Ins/VST3",
        "/Library/Audio/Plug-Ins/VST",
        "/Library/Application Support/Avid/Audio/Plug-Ins",
    ];

    /// Devuelve true si la ruta corresponde a un plugin de audio en el sistema
    pub fn is_audio_plugin(path: &Path) -> bool {
        let path_str = path.to_string_lossy();
        path_str.contains("/Library/Audio/Plug-Ins/")
            || path_str.contains("/Avid/Audio/Plug-Ins/")
            || path_str.ends_with(".component")
            || path_str.ends_with(".vst3")
            || path_str.ends_with(".vst")
            || path_str.ends_with(".aaxplugin")
    }

    /// Clasifica el formato del plugin
    pub fn plugin_format(path: &Path) -> Option<&'static str> {
        let path_str = path.to_string_lossy();
        if path_str.ends_with(".component") || path_str.contains("/Components/") {
            Some("Audio Unit (AU)")
        } else if path_str.ends_with(".vst3") || path_str.contains("/VST3/") {
            Some("VST3")
        } else if path_str.ends_with(".vst") || path_str.contains("/VST/") {
            Some("VST2 (Legacy)")
        } else if path_str.ends_with(".aaxplugin") || path_str.contains("/Avid/") {
            Some("Pro Tools AAX")
        } else {
            None
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;

    #[test]
    fn test_detect_audio_units() {
        let p = PathBuf::from("/Library/Audio/Plug-Ins/Components/Serum.component");
        assert!(AudioPluginFilter::is_audio_plugin(&p));
        assert_eq!(AudioPluginFilter::plugin_format(&p), Some("Audio Unit (AU)"));
    }
}
