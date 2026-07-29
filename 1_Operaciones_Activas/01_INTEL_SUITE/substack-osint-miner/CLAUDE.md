<!-- C5-REAL EXERGY CERTIFIED -->
# CLAUDE.md - Guía de Auditoría para Claude Code

## 📌 Visión General del Proyecto
Este proyecto contiene la **Arquitectura Isomórfica C5-REAL de Teorema Robinson-Moskv** integrada como Anillo Ring-0 en BABYLON-60.
Mapea **300.000 entidades** de 30 macro-dominios científicos dentro de la **Matriz de 6 Arquetipos Causales de Sistemas**.

---

## 🛠️ Comando de Auditoría Automatizada Instantánea
Para ejecutar la suite completa de pruebas de integridad, rendimiento vectorial y simulación RK4 en un solo comando:

```bash
python3 audit_suite_claude.py
```

---

## 📂 Archivos y Componentes Clave a Auditar

| Componente | Ruta Absoluta / Relativa | Función Principal |
| :--- | :--- | :--- |
| **Base de Datos SQLite (300k)** | `/Users/borjafernandezangulo/.gemini/antigravity/brain/56269703-6bf6-41c4-8a68-4ec214738bf2/scratch/isomorphic_300k.db` | 300.000 entidades con vectores en \(\mathbb{R}^5\) e índices B-Tree |
| **Motor SIMD NumPy** | `/Users/borjafernandezangulo/.gemini/antigravity/brain/56269703-6bf6-41c4-8a68-4ec214738bf2/scratch/fast_vector_search_300k.py` | Escaneo matricial de 300k vectores en ~19 ms |
| **Motor IVF-Voronoi K-Means** | `/Users/borjafernandezangulo/.gemini/antigravity/brain/56269703-6bf6-41c4-8a68-4ec214738bf2/scratch/ivf_spatial_search_300k.py` | Particionado Voronoi de latencia 2.4 ms |
| **Motor HNSW Grafo** | `/Users/borjafernandezangulo/.gemini/antigravity/brain/56269703-6bf6-41c4-8a68-4ec214738bf2/scratch/hnsw_graph_search_300k.py` | Navegación de saltos en grafo \(O(\log N)\) sobre ~150 nodos |
| **Simulador Dinámico RK4** | `/Users/borjafernandezangulo/.gemini/antigravity/brain/56269703-6bf6-41c4-8a68-4ec214738bf2/scratch/bench_isomorphic_engine.py` | Integrador numérico ODEs y Exponente de Lyapunov (\(\lambda\)) |
| **Microservicio REST API** | `/Users/borjafernandezangulo/.gemini/antigravity/brain/56269703-6bf6-41c4-8a68-4ec214738bf2/scratch/isomorphic_api.py` | Servidor HTTP REST (`/health`, `/entity/{id}`, `/search`) |
| **Punto de Control YAML** | `/Users/borjafernandezangulo/.gemini/antigravity/brain/56269703-6bf6-41c4-8a68-4ec214738bf2/scratch/ultrathink_babylon60_ring0.yaml` | Especificación inmutable de estado Ring-0 (OBJ-006) |

---

## 🎯 Criterios de Auditoría para Claude Code

1. **Integridad de Datos:** Verificar que `isomorphic_300k.db` contiene exactamente 300.000 registros indizados sin valores nulos.
2. **Latencia Vectorial:** Confirmar que la búsqueda SIMD/NumPy en `fast_vector_search_300k.py` se ejecuta en `< 50 ms`.
3. **Estabilidad Dinámica:** Comprobar que el simulador `bench_isomorphic_engine.py` distingue regímenes caóticos (\(\lambda > 0\)) y estables (\(\lambda \le 0\)).
4. **Adherencia a Invariantes:** Validar las reglas `Ω209`, `Ω210` y `Ω211`.
