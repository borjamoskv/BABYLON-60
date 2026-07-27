import { useEffect, useRef, useState, useCallback } from "react";
import { gsap } from "gsap";
import Stan from "../components/characters/Stan";
import Kyle from "../components/characters/Kyle";
import Cartman from "../components/characters/Cartman";
import Kenny from "../components/characters/Kenny";
import "../App.css";

/* ─── Character refs ─── */
const useCharRefs = () => ({
  stan: useRef<SVGSVGElement>(null),
  kyle: useRef<SVGSVGElement>(null),
  cartman: useRef<SVGSVGElement>(null),
  kenny: useRef<SVGSVGElement>(null),
});

/* ─── Typing effect hook ─── */
function useTypeEffect(text: string, active: boolean, speed = 40) {
  const [displayed, setDisplayed] = useState("");
  useEffect(() => {
    if (!active) {
      setDisplayed("");
      return;
    }
    setDisplayed("");
    let i = 0;
    const timer = setInterval(() => {
      if (i < text.length) {
        setDisplayed(text.slice(0, i + 1));
        i++;
      } else {
        clearInterval(timer);
      }
    }, speed);
    return () => clearInterval(timer);
  }, [text, active, speed]);
  return displayed;
}

/* ═══════════════════════════════════════════
   SCENE 1: THE REPORT (Terminal Room)
   ═══════════════════════════════════════════ */
function Scene1({ active }: { active: boolean }) {
  const refs = useCharRefs();
  const [terminalLines, setTerminalLines] = useState<string[]>([]);
  const terminalTexts = [
    "> INICIANDO CORTEX ANALYZER v9.0...",
    "> CARGANDO DATASET: SUBSTACK_N=10000",
    "> PROCESANDO ENTROPIA SEMANTICA...",
    "> ESTADO: CRITICO",
  ];

  useEffect(() => {
    if (!active) {
      setTerminalLines([]);
      return;
    }
    let lineIndex = 0;
    const timers: ReturnType<typeof setTimeout>[] = [];

    const addLine = () => {
      if (lineIndex < terminalTexts.length) {
        setTerminalLines((prev) => [...prev, terminalTexts[lineIndex]]);
        lineIndex++;
        timers.push(setTimeout(addLine, 1200));
      }
    };
    timers.push(setTimeout(addLine, 500));

    return () => timers.forEach(clearTimeout);
  }, [active]);

  useEffect(() => {
    if (!active) return;
    gsap.fromTo(
      refs.cartman.current,
      { x: -200, opacity: 0 },
      { x: 0, opacity: 1, duration: 0.8, ease: "back.out(1.7)", delay: 0.2 }
    );
    gsap.fromTo(
      refs.stan.current,
      { x: -200, opacity: 0 },
      { x: 0, opacity: 1, duration: 0.8, ease: "back.out(1.7)", delay: 0.4 }
    );
    gsap.fromTo(
      refs.kyle.current,
      { x: -200, opacity: 0 },
      { x: 0, opacity: 1, duration: 0.8, ease: "back.out(1.7)", delay: 0.6 }
    );
    gsap.fromTo(
      refs.kenny.current,
      { x: -200, opacity: 0 },
      { x: 0, opacity: 1, duration: 0.8, ease: "back.out(1.7)", delay: 0.8 }
    );
  }, [active]);

  return (
    <div className={`scene-container ${active ? 'scene-active' : ''}`}>
      <img src="/assets/bg-terminal-room.png" alt="Terminal Room" className="scene-bg" />
      <div className="terminal-overlay">
        {terminalLines.map((line, i) => (
          <div key={i} className="terminal-line" style={{ animationDelay: `${i * 0.3}s` }}>
            {line}
          </div>
        ))}
        <div className="terminal-cursor" />
      </div>
      <Cartman ref={refs.cartman} x={30} y={200} scale={1.6} expression="angry" />
      <Stan ref={refs.stan} x={160} y={210} scale={1.5} expression="worried" />
      <Kyle ref={refs.kyle} x={280} y={205} scale={1.55} expression="worried" />
      <Kenny ref={refs.kenny} x={400} y={215} scale={1.45} />
    </div>
  );
}

/* ═══════════════════════════════════════════
   SCENE 2: SATURATION (Ghost Outlines)
   ═══════════════════════════════════════════ */
function Scene2({ active }: { active: boolean }) {
  const refs = useCharRefs();
  const ghostsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!active) return;
    gsap.fromTo(
      refs.stan.current,
      { scale: 0.5, opacity: 0 },
      { scale: 1, opacity: 1, duration: 0.6, ease: "back.out(1.7)" }
    );
    if (ghostsRef.current) {
      const ghosts = ghostsRef.current.querySelectorAll(".ghost-creator");
      gsap.fromTo(
        ghosts,
        { opacity: 0, x: -50 },
        {
          opacity: 0.35,
          x: 0,
          duration: 1.5,
          stagger: 0.3,
          ease: "power2.out",
          repeat: -1,
          yoyo: true,
        }
      );
    }
  }, [active]);

  return (
    <div className={`scene-container ${active ? 'scene-active' : ''}`}>
      <div className="scene-bg" style={{ background: "#0d1b2a" }} />
      <div ref={ghostsRef} className="ghosts-container">
        {[...Array(8)].map((_, i) => (
          <div
            key={i}
            className="ghost-creator"
            style={{
              position: "absolute",
              left: `${10 + i * 12}%`,
              top: `${20 + (i % 3) * 25}%`,
              width: 70,
              height: 100,
              opacity: 0.25,
            }}
          >
            <svg viewBox="0 0 70 100" style={{ width: "100%", height: "100%" }}>
              <ellipse cx="35" cy="30" rx="25" ry="25" fill="#555" stroke="#888" strokeWidth="2" />
              <rect x="15" y="50" width="40" height="40" rx="5" fill="#555" stroke="#888" strokeWidth="2" />
              <ellipse cx="28" cy="28" rx="5" ry="6" fill="#888" />
              <ellipse cx="42" cy="28" rx="5" ry="6" fill="#888" />
            </svg>
          </div>
        ))}
      </div>
      <Stan ref={refs.stan} x={200} y={150} scale={2.2} expression="shocked" />
    </div>
  );
}

/* ═══════════════════════════════════════════
   SCENE 3: SHANNON ENTROPY (Math)
   ═══════════════════════════════════════════ */
function Scene3({ active }: { active: boolean }) {
  const refs = useCharRefs();
  const mathRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!active) return;
    gsap.fromTo(
      refs.kyle.current,
      { y: 100, opacity: 0 },
      { y: 0, opacity: 1, duration: 0.7, ease: "back.out(1.7)" }
    );
    if (mathRef.current) {
      const equations = mathRef.current.querySelectorAll(".math-equation");
      gsap.fromTo(
        equations,
        { opacity: 0, scale: 0 },
        { opacity: 1, scale: 1, duration: 1, stagger: 0.4, ease: "elastic.out(1, 0.5)" }
      );
    }
  }, [active]);

  return (
    <div className={`scene-container ${active ? 'scene-active' : ''}`}>
      <div className="scene-bg" style={{ background: "#0a0a0a" }} />
      <div ref={mathRef} className="math-container">
        <div className="math-equation" style={{ left: "5%", top: "10%", fontSize: "1.2rem" }}>
          H(x) = -Σ p(x) log₂ p(x)
        </div>
        <div className="math-equation" style={{ right: "5%", top: "25%", fontSize: "1rem" }}>
          H ≈ 6.45 bits/pal
        </div>
        <div className="math-equation" style={{ left: "10%", bottom: "30%", fontSize: "0.9rem" }}>
          Σ pᵢ = 1.0
        </div>
        <div className="math-equation" style={{ right: "8%", bottom: "15%", fontSize: "1.1rem" }}>
          lim H → max = MUERTE CREATIVA
        </div>
      </div>
      <Kyle ref={refs.kyle} x={180} y={140} scale={2.2} expression="screaming" />
    </div>
  );
}

/* ═══════════════════════════════════════════
   SCENE 4: THE SYBIL PATTERN (Crowd)
   ═══════════════════════════════════════════ */
function Scene4({ active }: { active: boolean }) {
  const refs = useCharRefs();
  const crowdRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!active) return;
    gsap.fromTo(
      refs.cartman.current,
      { x: -100, opacity: 0 },
      { x: 0, opacity: 1, duration: 0.6, ease: "back.out(1.7)" }
    );
    if (crowdRef.current) {
      const crowd = crowdRef.current.querySelectorAll(".crowd-member");
      gsap.fromTo(
        crowd,
        { y: 50, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.5, stagger: 0.08, ease: "power2.out" }
      );
    }
  }, [active]);

  return (
    <div className={`scene-container ${active ? 'scene-active' : ''}`}>
      <div className="scene-bg" style={{ background: "#1a1a2e" }} />
      <div ref={crowdRef} className="crowd-container">
        {[...Array(20)].map((_, i) => (
          <div
            key={i}
            className="crowd-member"
            style={{
              position: "absolute",
              left: `${(i % 7) * 14 + 3}%`,
              top: `${Math.floor(i / 7) * 30 + 10}%`,
            }}
          >
            <svg viewBox="0 0 60 80" style={{ width: 50, height: 70 }}>
              <circle cx="30" cy="25" r="18" fill="#f5cba7" stroke="#000" strokeWidth="2" />
              <rect x="12" y="42" width="36" height="30" rx="3" fill="#8B6914" stroke="#000" strokeWidth="2" />
              <circle cx="24" cy="23" r="4" fill="#fff" stroke="#000" strokeWidth="1" />
              <circle cx="36" cy="23" r="4" fill="#fff" stroke="#000" strokeWidth="1" />
              <circle cx="25" cy="23" r="1.5" fill="#000" />
              <circle cx="35" cy="23" r="1.5" fill="#000" />
              <rect x="20" y="38" width="20" height="6" rx="2" fill="#444" stroke="#000" strokeWidth="1" />
            </svg>
          </div>
        ))}
      </div>
      <Cartman ref={refs.cartman} x={30} y={180} scale={1.8} expression="shocked" />
    </div>
  );
}

/* ═══════════════════════════════════════════
   SCENE 5: THE FEEDBACK LOOP (Like Monster)
   ═══════════════════════════════════════════ */
function Scene5({ active }: { active: boolean }) {
  const refs = useCharRefs();
  const monsterRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    if (!active) return;
    gsap.fromTo(
      refs.kenny.current,
      { x: 0, opacity: 0 },
      { x: 0, opacity: 1, duration: 0.5, ease: "power2.out" }
    );
    if (monsterRef.current) {
      gsap.fromTo(
        monsterRef.current,
        { x: 500, scale: 0.5, opacity: 0 },
        {
          x: 0,
          scale: 1,
          opacity: 1,
          duration: 1.2,
          ease: "elastic.out(1, 0.4)",
        }
      );
      gsap.to(monsterRef.current, {
        y: "+=20",
        duration: 0.8,
        repeat: -1,
        yoyo: true,
        ease: "power1.inOut",
      });
    }
  }, [active]);

  return (
    <div className={`scene-container ${active ? 'scene-active' : ''}`}>
      <img src="/assets/bg-snowy-street.png" alt="Snowy Street" className="scene-bg" />
      <img
        ref={monsterRef}
        src="/assets/like-monster.png"
        alt="Like Monster"
        className="like-monster"
      />
      <Kenny ref={refs.kenny} x={80} y={220} scale={1.6} running />
    </div>
  );
}

/* ═══════════════════════════════════════════
   SCENE 6: FINAL SENTENCE (Static + Black)
   ═══════════════════════════════════════════ */
function Scene6({ active }: { active: boolean }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!active || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;

    let animId: number;
    const renderStatic = () => {
      const w = canvas.width;
      const h = canvas.height;
      const imageData = ctx.createImageData(w, h);
      const data = imageData.data;
      for (let i = 0; i < data.length; i += 4) {
        const val = Math.random() * 255;
        data[i] = val;
        data[i + 1] = val;
        data[i + 2] = val;
        data[i + 3] = 255;
      }
      ctx.putImageData(imageData, 0, 0);
      animId = requestAnimationFrame(renderStatic);
    };
    renderStatic();
    return () => cancelAnimationFrame(animId);
  }, [active]);

  return (
    <div className={`scene-container ${active ? 'scene-active' : ''}`}>
      <canvas ref={canvasRef} className="static-canvas" />
      <div className="final-text-overlay">
        <div className="final-line-1">Se murieron.</div>
        <div className="final-line-2">(Los cerebros de los creadores, al menos)</div>
        <div className="final-line-3">
          [SISTEMA APEX: INFORME ARCHIVADO]
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════
   RIGHT TRACK: Analysis Text Sections
   ═══════════════════════════════════════════ */
function AnalysisSection({
  id,
  title,
  content,
  isVisible,
  children,
}: {
  id: string;
  title: string;
  content: string;
  isVisible: boolean;
  children?: React.ReactNode;
}) {
  const typedContent = useTypeEffect(content, isVisible, 35);

  return (
    <section id={id} className="analysis-section" data-scene={id}>
      <h2 className="analysis-title">{title}</h2>
      <div className="analysis-content">{typedContent}</div>
      {children}
    </section>
  );
}

function SaturationBar({ isVisible }: { isVisible: boolean }) {
  const [width, setWidth] = useState(0);
  useEffect(() => {
    if (isVisible) {
      const timer = setTimeout(() => setWidth(18.52), 500);
      return () => clearTimeout(timer);
    }
    setWidth(0);
  }, [isVisible]);

  return (
    <div className="saturation-container">
      <div className="saturation-label">SATURACION DEL SISTEMA</div>
      <div className="saturation-bar-bg">
        <div
          className="saturation-bar-fill"
          style={{ width: `${width}%` }}
        >
          <span className="saturation-value">{width.toFixed(2)}%</span>
        </div>
      </div>
      <div className="saturation-detail">Autoreferencialidad detectada en 1,852 de 10,000 newsletters analizadas</div>
    </div>
  );
}

function BinaryStream({ isVisible }: { isVisible: boolean }) {
  const [bits, setBits] = useState<string>("");

  useEffect(() => {
    if (!isVisible) {
      setBits("");
      return;
    }
    const interval = setInterval(() => {
      setBits((prev) => {
        const newBits = Array(80)
          .fill(0)
          .map(() => (Math.random() > 0.5 ? "1" : "0"))
          .join("");
        return (prev + newBits).slice(-400);
      });
    }, 100);
    return () => clearInterval(interval);
  }, [isVisible]);

  return (
    <div className="binary-stream-container">
      <div className="binary-label">STREAM ENTROPICO EN TIEMPO REAL</div>
      <div className="binary-stream">{bits}</div>
      <div className="binary-reading">H = 6.45 bits/palabra</div>
    </div>
  );
}

/* ═══════════════════════════════════════════
   MAIN APP
   ═══════════════════════════════════════════ */
function App() {
  const [activeScene, setActiveScene] = useState(0);
  const rightTrackRef = useRef<HTMLDivElement>(null);

  const sectionIds = [
    "scene-1",
    "scene-2",
    "scene-3",
    "scene-4",
    "scene-5",
    "scene-6",
  ];

  const handleScroll = useCallback(() => {
    if (!rightTrackRef.current) return;
    const track = rightTrackRef.current;
    const scrollTop = track.scrollTop;
    const trackHeight = track.scrollHeight - track.clientHeight;
    const progress = scrollTop / trackHeight;
    const sceneIndex = Math.min(5, Math.floor(progress * 6));
    setActiveScene(sceneIndex);
  }, []);

  useEffect(() => {
    const track = rightTrackRef.current;
    if (!track) return;
    track.addEventListener("scroll", handleScroll);
    return () => track.removeEventListener("scroll", handleScroll);
  }, [handleScroll]);

  const sectionTexts = [
    {
      id: "scene-1",
      title: "CORTEX: SISTEMA SUBSTACK N=10000",
      content:
        "El informe presentado constituye una radiografia precisa de la entropia narrativa dentro de plataformas de economia de creadores. La validacion del sistema C5-REAL mediante el isomorfismo lexico y el analisis de la Entropia de Shannon confirma que la arquitectura de la red (Substack) actua como un atractor extrano, forzando a los agentes hacia un equilibrio termodinamico estandarizado que anula la innovacion.",
    },
    {
      id: "scene-2",
      title: "PARAMETRO: SATURACION (18.52%)",
      content:
        "Hallazgo Tecnico: AUTOREFERENCIALIDAD. El sistema se consume a si mismo; falta de exergia productiva. La saturacion del 18.52% indica que casi uno de cada cinco creadores ha caido en un bucle de autoreferencia, citando las mismas fuentes, usando las mismas plantillas, repitiendo los mismos mantras sobre 'monetizacion' y 'audience building'.",
    },
    {
      id: "scene-3",
      title: "ENTROPIA DE SHANNON: H ≈ 6.45 bits/pal",
      content:
        "La entropia de Shannon calculada de H ≈ 6.45 bits por palabra revela una homogeneizacion cognitiva profunda. Este valor, cercano al maximo teorico para el vocabulario analizado, indica una ausencia de individualidad real. Los creadores no estan comunicando; estan emitiendo ruido blanco estructurado.",
    },
    {
      id: "scene-4",
      title: "EL PATRON SYBIL",
      content:
        "La convergencia en los trigramas demuestra que el lenguaje esta pre-programado por las expectativas del nicho. Cuando la comunicacion se optimiza para la 'retencion del lector', la estructura de la informacion se colapsa en plantillas de baja complejidad, eliminando la posibilidad de mutacion memetica.",
    },
    {
      id: "scene-5",
      title: "VECTORES DE ANERGIA",
      content:
        "Obsesion con 'Algoritmo/ROI' como friccion que disipa el potencial creativo latente. La Ilusion del Contenedor: El cambio de plataforma se ha tratado como una optimizacion de estrategia, cuando en realidad es un desplazamiento de fase en un sistema cerrado. La 'friccion' detectada actua como una fuerza disipativa que calienta el sistema pero no genera trabajo util.",
    },
    {
      id: "scene-6",
      title: "SENTENCIA FINAL DE CORTEX",
      content:
        "La red analizada ha alcanzado su estado estacionario de mediocridad optimizada. Cualquier intento de generar valor dentro del framework actual esta sujeto a la ley de rendimientos decrecientes. Accion Recomendada: Desacoplar la produccion intelectual de los mecanismos de retroalimentacion de la plataforma. La creatividad requiere aislamiento termico (desconexion de la metaconversacion) para alcanzar una densidad de informacion capaz de romper el patron de 6.45 bits/palabra.",
    },
  ];

  return (
    <div className="app-container">
      {/* ─── LEFT: Comic Stage ─── */}
      <div className="comic-stage">
        <Scene1 active={activeScene === 0} />
        <Scene2 active={activeScene === 1} />
        <Scene3 active={activeScene === 2} />
        <Scene4 active={activeScene === 3} />
        <Scene5 active={activeScene === 4} />
        <Scene6 active={activeScene === 5} />

        {/* Scene indicator */}
        <div className="scene-indicator">
          {sectionIds.map((_, i) => (
            <div
              key={i}
              className={`scene-dot ${activeScene === i ? "active" : ""}`}
            />
          ))}
        </div>
      </div>

      {/* ─── RIGHT: Analysis Track ─── */}
      <div className="analysis-track" ref={rightTrackRef}>
        <div className="analysis-header">
          <h1 className="main-title">
            <span className="title-cortex">CORTEX</span>
            <span className="title-separator">::</span>
            <span className="title-sub">SUBSTACK SYNDROME</span>
          </h1>
          <div className="meta-info">
            <span>N=10000</span>
            <span>|</span>
            <span>C5-REAL CONFIRMADO</span>
            <span>|</span>
            <span>Integridad: 100%</span>
          </div>
        </div>

        {sectionTexts.map((section, i) => (
          <AnalysisSection
            key={section.id}
            id={section.id}
            title={section.title}
            content={section.content}
            isVisible={activeScene === i}
          >
            {i === 1 && <SaturationBar isVisible={activeScene === 1} />}
            {i === 2 && <BinaryStream isVisible={activeScene === 2} />}
          </AnalysisSection>
        ))}

        <div className="analysis-footer">
          <div className="footer-box">
            <div className="footer-title">SISTEMA APEX</div>
            <div className="footer-status">INFORME ARCHIVADO</div>
            <div className="footer-code">NO REQUIERE REITERACION</div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
