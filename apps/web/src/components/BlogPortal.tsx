import React, { useState } from 'react';
import { soundFx } from './AudioEngine';

export interface BlogPost {
  id: string;
  title: string;
  category: 'IA & Algoritmos' | 'EU AI Act & Derecho' | 'Termodinámica & Física' | 'Música & DSP';
  author: string;
  date: string;
  readTime: string;
  exergyScore: number; // Max 1000
  summary: string;
  content: string;
  tags: string[];
}

const INITIAL_POSTS: BlogPost[] = [
  {
    id: 'post-1',
    title: 'Atestación Causal C5-REAL: Por qué las DBs Vectoriales Fallan ante el Art. 12 del EU AI Act',
    category: 'EU AI Act & Derecho',
    author: 'Borja Moskv',
    date: '2026-08-13',
    readTime: '6 min',
    exergyScore: 998,
    summary: 'Las búsquedas K-NN por similitud coseno en bases de datos vectoriales no constituyen prueba de trazabilidad temporal ni linaje causal requeridos judicialmente.',
    content: `## El Error de Confundir Similitud Semántica con Linaje Causal

En la implementación estándar de RAG (Retrieval-Augmented Generation), se asume erróneamente que una búsqueda por vecinos más cercanos (K-NN) sobre embeddings vectoriales satisface la obligación de trazabilidad requerida por el Artículo 12 del EU AI Act (Reglamento UE 2024/1689).

### Por qué K-NN falla en auditoría judicial:
1. **Falta de Ordenación Causal Total:** La similitud de coseno cos(θ) mide cercanía en una variedad latente, pero es agnóstica a la flecha del tiempo y a las permutaciones de contexto.
2. **Deriva Entrópica del Generador:** Dos ejecuciones independientes del LLM sobre el mismo vector recuperado pueden generar respuestas contradictorias sin registro inmutable de la función de estado.
3. **Solución C5-REAL:** Sustituir índices K-NN por un Local Causal Ledger WAL con hashes SHA3-256 encadenados, garantizando que cada inferencia posee un hash de taint determinista irreversible.`,
    tags: ['EU AI Act', 'Causalidad', 'Vector DBs', 'SHA3-256', 'Derecho Digital'],
  },
  {
    id: 'post-2',
    title: 'Desintegración Bayesiana y Ópticas Categóricas: Eliminación de Anergía Semántica en Agentes',
    category: 'IA & Algoritmos',
    author: 'Borja Moskv',
    date: '2026-08-11',
    readTime: '8 min',
    exergyScore: 994,
    summary: 'Formalización de la cognición multi-agente mediante Teoría de Categorías, Lentes Bayesianas y la restricción del Principio de Energía Libre.',
    content: `## Transducción de Valor Ontológico V_A

Para evitar el colapso trófico de contexto en arquitecturas de agentes autónomos, la memoria no debe tratarse como un mero búfer de texto, sino como un Comonada de Almacenamiento (Store Comonad) donde cada estado es un punto fijo de Lawvere (T(X) ≅ X).

### Principio de Mínima Destrucción de Exergía:
δ ∫ F dt = 0

Al forzar que la discrepancia entre la distribución latente prior y posterior minimice la divergencia Kullback-Leibler D_KL, eliminamos la anergía semántica (tokens ineficientes o redundantes) y estabilizamos el rendimiento computacional en CPUs ARM64 sin throttling térmico.`,
    tags: ['Teoría de Categorías', 'Energía Libre', 'Store Comonad', 'C5-REAL', 'Sistemas Complejos'],
  },
  {
    id: 'post-3',
    title: 'Aritmética F60 Sexagesimal: Superando el Límite de Landauer en Procesadores Apple ARM64',
    category: 'Termodinámica & Física',
    author: 'Borja Moskv',
    date: '2026-08-08',
    readTime: '5 min',
    exergyScore: 989,
    summary: 'Cómo la eliminación de la deriva de coma flotante mediante una escala sexagesimal de 64 bits reduce los cambios de contexto involuntarios en el kernel.',
    content: `## Aritmética Exacta F60

Los schedulers convencionales basados en floats de 64 bits introducen errores de acumulación infinitesimales (10^-16) que fuerzan re-sincronizaciones constantes de hilos en el kernel del sistema operativo.

Al implementar la máquina de estados F60 (aritmética exacta de punto fijo sexagesimal), logramos:
- 0% CPU Involuntary Context Switches (ru_nivcsw = 0).
- Cumplimiento estricto del límite teórico de disipación de calor de Landauer (k_B T ln 2).
- Sincronización determinista de hasta 100,000 agentes concurrentes bajo el patrón AgentPager.`,
    tags: ['Física de la Computación', 'Landauer', 'F60', 'Rust', 'ARM64'],
  },
];

export const BlogPortal: React.FC = () => {
  const [posts, setPosts] = useState<BlogPost[]>(INITIAL_POSTS);
  const [selectedCategory, setSelectedCategory] = useState<string>('TODOS');
  const [activePost, setActivePost] = useState<BlogPost | null>(null);
  
  // New Article Form state
  const [showEditor, setShowEditor] = useState<boolean>(false);
  const [newTitle, setNewTitle] = useState<string>('');
  const [newCategory, setNewCategory] = useState<BlogPost['category']>('IA & Algoritmos');
  const [newSummary, setNewSummary] = useState<string>('');
  const [newContent, setNewContent] = useState<string>('');
  const [newTags, setNewTags] = useState<string>('C5-REAL, Exergía, Sistemas Complejos');

  const categories = ['TODOS', 'IA & Algoritmos', 'EU AI Act & Derecho', 'Termodinámica & Física', 'Música & DSP'];

  const filteredPosts = posts.filter(
    (p) => selectedCategory === 'TODOS' || p.category === selectedCategory
  );

  const calculateExergyScore = (title: string, content: string): number => {
    const len = title.length + content.length;
    if (len < 50) return 750;
    const keywords = ['C5-REAL', 'termodinámica', 'causal', 'SHA3-256', 'exergía', 'EU AI Act', 'Lean 4', 'Rust'];
    let hits = 0;
    keywords.forEach((k) => {
      if (content.toLowerCase().includes(k.toLowerCase())) hits++;
    });
    return Math.min(1000, 850 + hits * 25 + Math.min(50, Math.floor(len / 20)));
  };

  const handleCreatePost = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newContent.trim()) return;

    soundFx.playSuccess();
    const score = calculateExergyScore(newTitle, newContent);
    const tagsArray = newTags.split(',').map((t) => t.trim()).filter(Boolean);

    const post: BlogPost = {
      id: `post-${Date.now()}`,
      title: newTitle,
      category: newCategory,
      author: 'Borja Moskv',
      date: new Date().toISOString().slice(0, 10),
      readTime: `${Math.max(2, Math.ceil(newContent.length / 500))} min`,
      exergyScore: score,
      summary: newSummary || newContent.slice(0, 140) + '...',
      content: newContent,
      tags: tagsArray,
    };

    setPosts([post, ...posts]);
    setNewTitle('');
    setNewSummary('');
    setNewContent('');
    setShowEditor(false);
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-xl font-bold font-mono text-cyan-300 flex items-center gap-3">
            <span>📝 BLOG & HUB EPISTÉMICO DE ALTA EXERGÍA</span>
          </h2>
          <p className="text-xs text-slate-400 font-mono mt-1">
            Artículos de Investigación Original, Teoría de Sistemas Complejos, Derecho Digital y Termodinámica Cognitiva
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="c5-badge badge-amber font-mono">
            ⚡ EXERGÍA PROMEDIO: 993.7 / 1000
          </span>
          <button
            onClick={() => {
              soundFx.playClick();
              setShowEditor(!showEditor);
            }}
            className="px-4 py-2 bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-500/40 rounded-lg text-cyan-300 font-mono text-xs font-bold transition-all shadow-[0_0_15px_rgba(0,240,255,0.2)]"
          >
            {showEditor ? '✖️ CERRAR EDITOR' : '✍️ NUEVO ARTÍCULO EXÉRGICO'}
          </button>
        </div>
      </div>

      {/* Editor Modal / Panel */}
      {showEditor && (
        <form onSubmit={handleCreatePost} className="glass-panel p-6 space-y-4 font-mono border-cyan-500/50">
          <div className="text-xs font-bold text-cyan-300 flex items-center gap-2 border-b border-slate-800 pb-2">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
            PUBLICAR ARTÍCULO EN PUBLICACIÓN SOBERANA C5-REAL
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2">
              <label className="text-[10px] text-slate-400 block mb-1">TÍTULO DEL ARTÍCULO</label>
              <input
                type="text"
                placeholder="Ej. Formulación Categórica de la Reducción Entrópica en Enjambres"
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-white outline-none focus:border-cyan-500"
                required
              />
            </div>
            <div>
              <label className="text-[10px] text-slate-400 block mb-1">CATEGORÍA</label>
              <select
                value={newCategory}
                onChange={(e) => setNewCategory(e.target.value as BlogPost['category'])}
                className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-cyan-300 outline-none focus:border-cyan-500"
              >
                <option value="IA & Algoritmos">IA & Algoritmos</option>
                <option value="EU AI Act & Derecho">EU AI Act & Derecho</option>
                <option value="Termodinámica & Física">Termodinámica & Física</option>
                <option value="Música & DSP">Música & DSP</option>
              </select>
            </div>
          </div>

          <div>
            <label className="text-[10px] text-slate-400 block mb-1">RESUMEN EJECUTIVO / ABSTRACT</label>
            <input
              type="text"
              placeholder="Breve descripción del hallazgo o invariante teórico demostrado..."
              value={newSummary}
              onChange={(e) => setNewSummary(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-slate-300 outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <label className="text-[10px] text-slate-400 block mb-1">CONTENIDO COMPLETO (MARKDOWN)</label>
            <textarea
              rows={6}
              placeholder="Escribe aquí el contenido técnico en Markdown..."
              value={newContent}
              onChange={(e) => setNewContent(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded p-3 text-xs text-emerald-400 font-mono outline-none focus:border-emerald-500"
              required
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-[10px] text-slate-400 block mb-1">ETIQUETAS (SEPARADAS POR COMAS)</label>
              <input
                type="text"
                value={newTags}
                onChange={(e) => setNewTags(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-slate-400 outline-none focus:border-cyan-500"
              />
            </div>
            <div className="flex items-end justify-end">
              <button
                type="submit"
                className="w-full py-2.5 bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-500/50 rounded text-emerald-300 text-xs font-bold transition-all shadow-[0_0_15px_rgba(16,185,129,0.2)]"
              >
                🚀 PUBLICAR CON EVALUACIÓN DE EXERGÍA
              </button>
            </div>
          </div>
        </form>
      )}

      {/* Category Pills */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 font-mono text-xs">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => {
              soundFx.playClick();
              setSelectedCategory(cat);
            }}
            className={`px-3 py-1.5 rounded-lg transition-all text-xs font-semibold whitespace-nowrap ${
              selectedCategory === cat
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/50 shadow-[0_0_10px_rgba(0,240,255,0.2)]'
                : 'bg-slate-900/60 text-slate-400 border border-slate-800 hover:text-slate-200'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Main Grid Feed */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {filteredPosts.map((post) => (
          <article
            key={post.id}
            onClick={() => {
              soundFx.playClick();
              setActivePost(post);
            }}
            className="glass-panel p-6 space-y-4 border-slate-800 hover:border-cyan-500/50 cursor-pointer transition-all hover:scale-[1.01] group relative overflow-hidden"
          >
            <div className="flex justify-between items-center text-xs font-mono">
              <span className="px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-500/30 font-semibold">
                {post.category}
              </span>
              <div className="flex items-center gap-2">
                <span className="text-emerald-400 font-bold">⚡ {post.exergyScore} EXERGÍA</span>
                <span className="text-slate-500">• {post.readTime}</span>
              </div>
            </div>

            <h3 className="text-lg font-bold text-white group-hover:text-cyan-300 transition-colors font-mono leading-snug">
              {post.title}
            </h3>

            <p className="text-xs text-slate-300 leading-relaxed font-sans line-clamp-3">
              {post.summary}
            </p>

            <div className="flex justify-between items-center text-[11px] font-mono border-t border-slate-800/80 pt-3 text-slate-400">
              <span>Autor: <strong className="text-slate-200">{post.author}</strong></span>
              <span>{post.date}</span>
            </div>

            <div className="flex flex-wrap gap-1.5 pt-1">
              {post.tags.map((tag) => (
                <span key={tag} className="text-[10px] font-mono px-2 py-0.5 bg-slate-900 text-slate-400 rounded border border-slate-800">
                  #{tag}
                </span>
              ))}
            </div>
          </article>
        ))}
      </div>

      {/* Reader Modal */}
      {activePost && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="glass-panel max-w-3xl w-full max-h-[85vh] overflow-y-auto p-8 space-y-6 border-cyan-500/40 relative font-mono text-slate-200">
            <button
              onClick={() => setActivePost(null)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white text-lg font-bold"
            >
              ✕
            </button>

            <div className="flex items-center gap-3 text-xs">
              <span className="px-2.5 py-1 rounded bg-cyan-950 text-cyan-300 border border-cyan-500/40 font-bold">
                {activePost.category}
              </span>
              <span className="text-emerald-400 font-bold">⚡ Score de Exergía: {activePost.exergyScore}/1000</span>
              <span className="text-slate-400">• {activePost.date}</span>
            </div>

            <h2 className="text-2xl font-bold text-white leading-snug font-mono">
              {activePost.title}
            </h2>

            <div className="text-xs text-slate-400 border-b border-slate-800 pb-3 flex items-center gap-2">
              <span>Por <strong>{activePost.author}</strong></span>
              <span>•</span>
              <span>Tiempo de lectura: {activePost.readTime}</span>
            </div>

            <div className="text-xs leading-relaxed space-y-4 font-sans text-slate-300 whitespace-pre-line">
              {activePost.content}
            </div>

            <div className="border-t border-slate-800 pt-4 flex justify-between items-center text-xs">
              <div className="flex flex-wrap gap-1.5">
                {activePost.tags.map((t) => (
                  <span key={t} className="text-[10px] font-mono px-2 py-0.5 bg-slate-900 text-cyan-400 rounded border border-slate-800">
                    #{t}
                  </span>
                ))}
              </div>
              <button
                onClick={() => setActivePost(null)}
                className="px-4 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-700 rounded text-slate-300 text-xs"
              >
                CERRAR LECTURA
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
