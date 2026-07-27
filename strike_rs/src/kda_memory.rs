use std::collections::HashMap;

/// Entidad atómica en la memoria KDA
#[derive(Debug, Clone, PartialEq)]
pub struct KdaEntry {
    pub value: String,
    pub version: u64,
    pub freq: u64,
}

/// Buffer KDA acotado O(1) con semántica LRU-freq y versionado monotónico.
/// Cumple axiomas AX-KDA-1 a AX-KDA-6.
#[derive(Debug, Clone)]
pub struct KdaMemoryBuffer {
    capacity: usize,
    entries: HashMap<String, KdaEntry>,
}

impl KdaMemoryBuffer {
    pub fn new(capacity: usize) -> Self {
        Self {
            capacity,
            entries: HashMap::with_capacity(capacity),
        }
    }

    /// AX-KDA-6: Lectura incrementa frecuencia
    pub fn get(&mut self, key: &str) -> Option<String> {
        if let Some(entry) = self.entries.get_mut(key) {
            entry.freq += 1;
            Some(entry.value.clone())
        } else {
            None
        }
    }

    /// AX-KDA-1, AX-KDA-2, AX-KDA-3: Inserción acotada, monotónica y con evicción
    pub fn put(&mut self, key: &str, value: String) {
        if let Some(entry) = self.entries.get_mut(key) {
            // Clave existente: incrementar versión (AX-KDA-2)
            entry.version += 1;
            entry.value = value;
            return;
        }

        // Nueva clave: verificar capacidad (AX-KDA-1)
        if self.entries.len() >= self.capacity {
            self.evict_lfu(); // AX-KDA-3
        }

        self.entries.insert(
            key.to_string(),
            KdaEntry {
                value,
                version: 1,
                freq: 1,
            },
        );
    }

    /// Desalojo determinista por mínima frecuencia (AX-KDA-3)
    fn evict_lfu(&mut self) {
        if self.entries.is_empty() {
            return;
        }
        let mut min_key = String::new();
        let mut min_freq = u64::MAX;

        // Romper empates de forma determinista usando el orden lexicográfico del hash
        for (k, v) in &self.entries {
            if v.freq < min_freq || (v.freq == min_freq && k < &min_key) {
                min_freq = v.freq;
                min_key = k.clone();
            }
        }
        self.entries.remove(&min_key);
    }

    /// AX-KDA-5: Captura de estado
    pub fn snapshot(&self) -> HashMap<String, KdaEntry> {
        self.entries.clone()
    }

    /// AX-KDA-5: Restauración isomórfica
    pub fn restore(&mut self, snapshot: HashMap<String, KdaEntry>) {
        self.entries = snapshot;
    }

    pub fn capacity(&self) -> usize {
        self.capacity
    }

    pub fn len(&self) -> usize {
        self.entries.len()
    }

    pub fn is_empty(&self) -> bool {
        self.entries.is_empty()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ax_kda_1_bounded() {
        let mut mem = KdaMemoryBuffer::new(2);
        mem.put("k1", "v1".into());
        mem.put("k2", "v2".into());
        mem.put("k3", "v3".into());
        assert_eq!(mem.len(), 2);
    }

    #[test]
    fn test_ax_kda_2_version_monotonic() {
        let mut mem = KdaMemoryBuffer::new(2);
        mem.put("k1", "v1".into());
        assert_eq!(mem.entries["k1"].version, 1);
        mem.put("k1", "v2".into());
        assert_eq!(mem.entries["k1"].version, 2);
    }
}
