import React from 'react';
import {
	Composition,
	Series,
	Sequence,
	useCurrentFrame,
	spring,
	interpolate,
	Audio,
	staticFile
} from 'remotion';

// ==========================================
// CONFIGURACIÓN DE METADATOS Y CONSTANTES
// ==========================================
const FPS = 30;
const DURATION_IN_MINUTES = 20;
const TOTAL_FRAMES = DURATION_IN_MINUTES * 60 * FPS; // 36,000 frames

const COLOR_BG = '#07070A'; // Deep Space Noir
const COLOR_ACCENT_PURPLE = '#B026FF'; // Morado Neón
const COLOR_ACCENT_ORANGE = '#FF4500'; // Naranja Radiactivo
const COLOR_ACCENT_GREEN = '#00FF66'; // Verde C5-REAL
const COLOR_WHITE = '#FFFFFF'; // Blanco Titanio
const COLOR_GRAY = '#1A1A24';
const COLOR_MUTED = '#555566';

// Paths resolved dynamically
const PATH_HOST_AVATAR = staticFile("/un_tio_blanco_hipocrita_1783601517900.jpg");
const PATH_ANALYST_AVATAR = staticFile("/humify_podcast_8bit_1783598582427.jpg");

// ==========================================
// ESTRUCTURA DE SUBTÍTULOS SÍNCRONOS
// ==========================================
interface Subtitle {
	startFrame: number;
	endFrame: number;
	text: string;
	speaker: 'host' | 'analyst';
}

const SUBTITLES: Subtitle[] = [
	// BLOQUE 1: COLAPSO CONTRACTUAL (0 - 9000 frames)
	{ startFrame: 90, endFrame: 240, text: "[AUDITOR] Iniciando autopsia del ego frágil de Sergio Candanedo. Alias: 'El Macho Alfa Llorón'.", speaker: 'analyst' },
	{ startFrame: 250, endFrame: 420, text: "[HOST] ¡Lloro todos los días porque me 'censuraron' en 2019! Fui víctima de la dictadura judeomasónica-progresista.", speaker: 'host' },
	{ startFrame: 430, endFrame: 600, text: "[AUDITOR] Mentira. El Noúmeno factual revela que te echaron por ser un matón de patio: 'Si me lo dices en la calle no tendrías dientes'.", speaker: 'analyst' },
	{ startFrame: 610, endFrame: 780, text: "[HOST] ¡Pero soy un intelectual! ¡Amenazar con reventar dientes es mi libertad de expresión!", speaker: 'host' },
	{ startFrame: 790, endFrame: 980, text: "[AUDITOR] Tu libertad colapsó contra las normas básicas. Eres un llorica de internet, no un mártir político.", speaker: 'analyst' },

	// BLOQUE 2: DERROTA JURÍDICA (9000 - 18000 frames)
	{ startFrame: 9090, endFrame: 9240, text: "[AUDITOR] Avance temporal. El 'azote de las feminazis' corre a esconderse detrás de las faldas del Tribunal Supremo.", speaker: 'analyst' },
	{ startFrame: 9250, endFrame: 9450, text: "[HOST] ¡Yolanda Domínguez me llamó machista! ¡Me ha ofendido! ¡Que caiga todo el peso de la ley estatal sobre ella!", speaker: 'host' },
	{ startFrame: 9460, endFrame: 9680, text: "[AUDITOR] El Supremo se rió en tu cara. Dictaminó que llamarte 'machista', 'troll' y 'violento' es pura y dura verdad jurídica probada.", speaker: 'analyst' },
	{ startFrame: 9690, endFrame: 9900, text: "[HOST] ¡Noooo! ¡Mi honor de caballero andante! ¿Al menos el Constitucional me dio la razón en 2025 para seguir llorando?", speaker: 'host' },
	{ startFrame: 9910, endFrame: 10200, text: "[AUDITOR] Te dieron una patada y te condenaron en costas. Derrota absoluta por usar la justicia como rabieta infantil.", speaker: 'analyst' },

	// BLOQUE 3: EL NEGOCIO DEL ODIO (18000 - 27000 frames)
	{ startFrame: 18090, endFrame: 18280, text: "[AUDITOR] Analicemos tu patético flujo de caja. Tu modelo de negocio es enfadar a inceles y recolectar sus céntimos.", speaker: 'analyst' },
	{ startFrame: 18290, endFrame: 18490, text: "[HOST] ¡Es activismo! Yo solo pongo dianas a mujeres en internet para que mi horda las destruya, ¿qué tiene de malo?", speaker: 'host' },
	{ startFrame: 18500, endFrame: 18720, text: "[AUDITOR] Que permites amenazas de muerte reales en tu chat mientras te embolsas el dinero de Patreon. Eres un proxeneta del odio ajeno.", speaker: 'analyst' },
	{ startFrame: 18730, endFrame: 18950, text: "[HOST] El odio ajeno paga mi alquiler. Si mis seguidores amenazan de muerte, es su libertad... ¡No olviden donar a mi PayPal!", speaker: 'host' },

	// BLOQUE 4: LA PARADOJA DE LA VÍCTIMA (27000 - 36000 frames)
	{ startFrame: 27090, endFrame: 27280, text: "[AUDITOR] Llegamos al clímax del patetismo: la asimetría moral del Macho Alfa de cristal.", speaker: 'analyst' },
	{ startFrame: 27290, endFrame: 27480, text: "[HOST] ¡Socorro! ¡Alguien hizo una sátira mía en un canal secundario! ¡Llamen a la policía del copyright! ¡Me da ansiedad!", speaker: 'host' },
	{ startFrame: 27490, endFrame: 27700, text: "[AUDITOR] Indiferente ante el acoso brutal que generas a mujeres, pero entras en pánico nuclear por una bromita inofensiva hacia tu persona.", speaker: 'analyst' },
	{ startFrame: 27710, endFrame: 27950, text: "[HOST] '¡Estoy hartito de esto ya!' ¡Verifiqué mi marca corriendo en Twitter! ¡Con el dinero de mi monigote no se juega!", speaker: 'host' },
	{ startFrame: 27960, endFrame: 28300, text: "[AUDITOR] Caso cerrado. Eres un cobarde institucionalizado, un cínico de manual y un hipócrita con 'check azul'. Apoptosis recomendada.", speaker: 'analyst' }
];

// ==========================================
// COMPONENTE: REPRODUCTOR DE SUBTÍTULOS DINÁMICOS
// ==========================================
const SubtitlesTrack: React.FC = () => {
	const frame = useCurrentFrame();

	const activeSub = SUBTITLES.find(sub => frame >= sub.startFrame && frame <= sub.endFrame);

	if (!activeSub) return null;

	const isHost = activeSub.speaker === 'host';
	const accentColor = isHost ? COLOR_ACCENT_ORANGE : COLOR_ACCENT_PURPLE;

	return (
		<div style={{
			position: 'absolute',
			bottom: '40px',
			left: '50%',
			transform: 'translateX(-50%)',
			width: '85%',
			backgroundColor: 'rgba(7, 7, 10, 0.95)',
			border: `3px solid ${isHost ? COLOR_ACCENT_ORANGE : COLOR_ACCENT_PURPLE}`,
			boxShadow: `0 0 25px ${isHost ? 'rgba(255, 69, 0, 0.4)' : 'rgba(176, 38, 255, 0.4)'}`,
			borderRadius: '12px',
			padding: '25px 35px',
			boxSizing: 'border-box',
			display: 'flex',
			flexDirection: 'column',
			alignItems: 'center',
			justifyContent: 'center',
			zIndex: 20,
			fontFamily: 'monospace'
		}}>
			<span style={{
				fontSize: '14px',
				fontWeight: '900',
				color: accentColor,
				marginBottom: '8px',
				textTransform: 'uppercase',
				letterSpacing: '3px'
			}}>
				{activeSub.speaker === 'host' ? '🤡 UTBH (LLORIQUEO MODE)' : '⚡ CORTEX AUDITOR (VERDAD)'}
			</span>
			<p style={{
				fontSize: '22px',
				fontWeight: 'bold',
				color: COLOR_WHITE,
				margin: 0,
				textAlign: 'center',
				lineHeight: '1.4',
				textShadow: '0 3px 6px rgba(0,0,0,0.8)'
			}}>
				{activeSub.text}
			</p>
		</div>
	);
};

// ==========================================
// FILTRO ESTÉTICO CRT (SCANLINES / GLITCH)
// ==========================================
const CRTOverlay: React.FC = () => {
	return (
		<div style={{
			position: 'absolute',
			top: 0,
			left: 0,
			right: 0,
			bottom: 0,
			pointerEvents: 'none',
			background: `
				linear-gradient(
					rgba(18, 16, 16, 0) 50%,
					rgba(0, 0, 0, 0.35) 50%
				),
				linear-gradient(
					90deg,
					rgba(255, 0, 0, 0.08),
					rgba(0, 255, 0, 0.03),
					rgba(0, 0, 255, 0.08)
				)
			`,
			backgroundSize: '100% 5px, 6px 100%',
			zIndex: 99,
			opacity: 0.7
		}} />
	);
};

// ==========================================
// COMPONENTE: AUDIO VISUALIZER (8-BIT SVG)
// ==========================================
const AudioVisualizer: React.FC<{ isActive: boolean; speedOffset: number }> = ({ isActive, speedOffset }) => {
	const frame = useCurrentFrame();
	const numBars = 16;

	return (
		<div style={{ display: 'flex', alignItems: 'flex-end', height: '60px', gap: '4px' }}>
			{Array.from({ length: numBars }).map((_, i) => {
				const wave = isActive
					? Math.sin(frame * 0.3 + i * 0.5 + speedOffset) * Math.cos(frame * 0.1 + i * 0.2) * 40 + 40
					: 4;
				const height = Math.max(4, wave);
				const color = isActive
					? (speedOffset === 0 ? COLOR_ACCENT_ORANGE : COLOR_ACCENT_PURPLE)
					: COLOR_GRAY;

				return (
					<div
						key={i}
						style={{
							width: '8px',
							height: `${height}px`,
							backgroundColor: color,
							boxShadow: isActive ? `0 0 15px ${color}` : 'none',
							imageRendering: 'pixelated',
							transition: 'height 0.05s ease'
						}}
					/>
				);
			})}
		</div>
	);
};

// ==========================================
// COMPONENTE: HUD FORENSE (MONITOR SUPERIOR)
// ==========================================
const ForensicHUD: React.FC<{ blockTitle: string; progress: number }> = ({ blockTitle, progress }) => {
	const frame = useCurrentFrame();

	const minutes = Math.floor(frame / (FPS * 60));
	const seconds = Math.floor((frame % (FPS * 60)) / FPS);
	const timeString = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;

	const currentHash = `0x${Math.floor(frame * 313.14159).toString(16).toUpperCase().substring(0, 8)}...`;

	return (
		<div style={{
			position: 'absolute',
			top: '40px',
			left: '40px',
			right: '40px',
			height: '70px',
			borderBottom: `3px solid ${COLOR_ACCENT_ORANGE}`,
			backgroundColor: 'rgba(7, 7, 10, 0.8)',
			display: 'flex',
			justifyContent: 'space-between',
			alignItems: 'center',
			fontFamily: 'monospace',
			color: COLOR_WHITE,
			fontSize: '15px',
			padding: '0 20px',
			zIndex: 10
		}}>
			<div style={{ display: 'flex', gap: '20px' }}>
				<span style={{ color: COLOR_ACCENT_GREEN, textShadow: `0 0 8px ${COLOR_ACCENT_GREEN}` }}>[C5-REAL AUDIT: HIPOCRESÍA DETECTADA]</span>
				<span>LEDGER: <span style={{ color: COLOR_ACCENT_PURPLE }}>{currentHash}</span></span>
			</div>
			<div style={{ fontSize: '18px', fontWeight: '900', letterSpacing: '2px', color: COLOR_ACCENT_ORANGE, textShadow: `0 0 10px ${COLOR_ACCENT_ORANGE}` }}>
				{blockTitle}
			</div>
			<div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
				<span style={{ fontWeight: 'bold' }}>TIME: <span style={{ color: COLOR_ACCENT_ORANGE }}>{timeString} / 20:00</span></span>
				<div style={{
					width: '120px',
					height: '10px',
					backgroundColor: COLOR_GRAY,
					position: 'relative',
					borderRadius: '2px',
					overflow: 'hidden'
				}}>
					<div style={{
						position: 'absolute',
						left: 0,
						top: 0,
						bottom: 0,
						width: `${progress * 100}%`,
						backgroundColor: COLOR_ACCENT_ORANGE,
						boxShadow: `0 0 10px ${COLOR_ACCENT_ORANGE}`
					}} />
				</div>
			</div>
		</div>
	);
};

// ==========================================
// COMPONENTE: PANEL DE PRESENTADORES (8-BIT)
// ==========================================
const PresentersPanel: React.FC<{ activeSpeaker: 'host' | 'analyst' }> = ({ activeSpeaker }) => {
	const hostShake = activeSpeaker === 'host' ? Math.sin(useCurrentFrame() * 2) * 3 : 0; // Efecto de temblor por ansiedad

	return (
		<div style={{
			width: '35%',
			height: '80%',
			borderRight: `2px solid ${COLOR_GRAY}`,
			display: 'flex',
			flexDirection: 'column',
			justifyContent: 'space-around',
			padding: '40px',
			boxSizing: 'border-box'
		}}>
			{/* Host Card (Satirizado) */}
			<div style={{
				display: 'flex',
				flexDirection: 'column',
				alignItems: 'center',
				padding: '20px',
				border: `3px solid ${activeSpeaker === 'host' ? COLOR_ACCENT_ORANGE : COLOR_GRAY}`,
				backgroundColor: activeSpeaker === 'host' ? 'rgba(255, 69, 0, 0.1)' : 'transparent',
				boxShadow: activeSpeaker === 'host' ? `0 0 30px rgba(255, 69, 0, 0.3)` : 'none',
				borderRadius: '8px',
				transform: `translateX(${hostShake}px)`, // Temblor
				transition: 'all 0.1s ease'
			}}>
				<img
					src={PATH_HOST_AVATAR}
					style={{
						width: '120px',
						height: '120px',
						border: `3px solid ${activeSpeaker === 'host' ? COLOR_ACCENT_ORANGE : COLOR_GRAY}`,
						borderRadius: '4px',
						objectFit: 'cover',
						imageRendering: 'pixelated',
						filter: activeSpeaker === 'host' ? 'contrast(1.2) saturate(1.5)' : 'grayscale(0.5)'
					}}
					alt="Host UTBH Llorando"
				/>
				<h3 style={{ color: COLOR_ACCENT_ORANGE, marginTop: '10px', fontFamily: 'monospace', fontSize: '16px', fontWeight: 'bold' }}>UTBH (VÍCTIMA PROFESIONAL)</h3>
				<AudioVisualizer isActive={activeSpeaker === 'host'} speedOffset={0} />
			</div>

			{/* Analyst Card */}
			<div style={{
				display: 'flex',
				flexDirection: 'column',
				alignItems: 'center',
				padding: '20px',
				border: `3px solid ${activeSpeaker === 'analyst' ? COLOR_ACCENT_PURPLE : COLOR_GRAY}`,
				backgroundColor: activeSpeaker === 'analyst' ? 'rgba(176, 38, 255, 0.1)' : 'transparent',
				boxShadow: activeSpeaker === 'analyst' ? `0 0 30px rgba(176, 38, 255, 0.3)` : 'none',
				borderRadius: '8px',
				transition: 'all 0.15s ease'
			}}>
				<img
					src={PATH_ANALYST_AVATAR}
					style={{
						width: '120px',
						height: '120px',
						border: `3px solid ${activeSpeaker === 'analyst' ? COLOR_ACCENT_PURPLE : COLOR_GRAY}`,
						borderRadius: '4px',
						objectFit: 'cover',
						imageRendering: 'pixelated',
						filter: activeSpeaker === 'analyst' ? 'contrast(1.2)' : 'brightness(0.7)'
					}}
					alt="CORTEX Verdad"
				/>
				<h3 style={{ color: COLOR_ACCENT_PURPLE, marginTop: '10px', fontFamily: 'monospace', fontSize: '16px', fontWeight: 'bold' }}>CORTEX (NOÚMENO)</h3>
				<AudioVisualizer isActive={activeSpeaker === 'analyst'} speedOffset={Math.PI} />
			</div>
		</div>
	);
};

// ==========================================
// SUB-ESCENA 1: EL COLAPSO CONTRACTUAL
// ==========================================
const SceneColapsoContractual: React.FC = () => {
	const frame = useCurrentFrame();
	const progress = frame / 9000;

	const activeSpeaker: 'host' | 'analyst' = frame % 340 < 170 ? 'host' : 'analyst';

	const threatScale = spring({ frame: frame - 120, fps: FPS, config: { damping: 10, mass: 1.5 } });

	return (
		<div style={{ flex: 1, backgroundColor: COLOR_BG, width: '100%', height: '100%', display: 'flex', position: 'relative', alignItems: 'center' }}>
			<ForensicHUD blockTitle="BLOQUE 1: PATALETA DE MATÓN REPRIMIDO" progress={progress} />

			<div style={{ display: 'flex', width: '100%', height: '100%', paddingTop: '110px', boxSizing: 'border-box' }}>
				<PresentersPanel activeSpeaker={activeSpeaker} />

				<div style={{ width: '65%', padding: '60px', display: 'flex', flexDirection: 'column', justifyContent: 'center', color: COLOR_WHITE, fontFamily: 'monospace' }}>
					<h2 style={{ color: COLOR_ACCENT_ORANGE, fontSize: '32px', marginBottom: '15px', fontWeight: '900', textShadow: `0 0 12px ${COLOR_ACCENT_ORANGE}` }}>EVIDENCIA 001: EL LLORO POR TWITTER (2019)</h2>
					<p style={{ fontSize: '18px', lineHeight: '1.6', color: '#BBBBC9' }}>
						El sujeto lleva años llorando por las esquinas diciendo que fue <em>"censurado por la progresía"</em>. La pura realidad: le echaron por comportarse como un matón asustadizo en internet.
					</p>

					<div style={{
						backgroundColor: 'rgba(255, 69, 0, 0.1)',
						border: `3px dashed ${COLOR_ACCENT_ORANGE}`,
						padding: '25px',
						margin: '25px 0',
						transform: `scale(${interpolate(threatScale, [0, 1], [0.8, 1])}) rotate(${Math.sin(frame/5)}deg)`,
						opacity: interpolate(threatScale, [0, 1], [0, 1])
					}}>
						<span style={{ color: COLOR_WHITE, fontSize: '15px', display: 'block', marginBottom: '8px', fontWeight: 'bold', backgroundColor: COLOR_ACCENT_ORANGE, padding: '5px', width: 'fit-content' }}>[RABIETA LITERAL REGISTRADA]</span>
						<p style={{ fontSize: '26px', fontWeight: 'bold', color: COLOR_WHITE, fontStyle: 'italic', margin: 0 }}>
							"Si me lo dices en la calle ahora no tendrías dientes."
						</p>
					</div>

					<p style={{ fontSize: '16px', lineHeight: '1.5', color: COLOR_ACCENT_GREEN, fontWeight: 'bold' }}>
						Diagnóstico C5: No eres un pensador incomprendido, eres un cobarde con conexión a internet que violó un simple contrato de uso. Cero censura, cien por cien estupidez.
					</p>
				</div>
			</div>
		</div>
	);
};

// ==========================================
// SUB-ESCENA 2: LA DERROTA JUDICIAL
// ==========================================
const SceneDerrotaJudicial: React.FC = () => {
	const frame = useCurrentFrame();
	const progress = frame / 9000;
	const activeSpeaker: 'host' | 'analyst' = frame % 420 < 210 ? 'analyst' : 'host';

	const listSpring1 = spring({ frame: frame - 80, fps: FPS, config: { tension: 100 } });
	const listSpring2 = spring({ frame: frame - 180, fps: FPS, config: { tension: 100 } });

	return (
		<div style={{ flex: 1, backgroundColor: COLOR_BG, width: '100%', height: '100%', display: 'flex', position: 'relative', alignItems: 'center' }}>
			<ForensicHUD blockTitle="BLOQUE 2: EL RIDÍCULO JURÍDICO SUPREMO" progress={progress} />

			<div style={{ display: 'flex', width: '100%', height: '100%', paddingTop: '110px', boxSizing: 'border-box' }}>
				<PresentersPanel activeSpeaker={activeSpeaker} />

				<div style={{ width: '65%', padding: '60px', display: 'flex', flexDirection: 'column', justifyContent: 'center', color: COLOR_WHITE, fontFamily: 'monospace' }}>
					<h2 style={{ color: COLOR_ACCENT_PURPLE, fontSize: '32px', marginBottom: '15px', fontWeight: '900', textShadow: `0 0 12px ${COLOR_ACCENT_PURPLE}` }}>EVIDENCIA 002: SENTENCIA TS 2024 / TC 2025</h2>
					<p style={{ fontSize: '18px', lineHeight: '1.6', color: '#BBBBC9' }}>
						Intenta usar a los jueces como guardaespaldas porque una mujer le llamó "machista". La estrategia le explota en la cara de la forma más humillante posible.
					</p>

					<div style={{ display: 'flex', gap: '20px', marginTop: '30px' }}>
						<div style={{
							flex: 1,
							border: `3px solid ${COLOR_ACCENT_ORANGE}`,
							backgroundColor: 'rgba(255, 69, 0, 0.1)',
							padding: '25px',
							borderRadius: '8px',
							opacity: listSpring1,
							transform: `translateY(${interpolate(listSpring1, [0, 1], [30, 0])}px)`
						}}>
							<h4 style={{ color: COLOR_WHITE, backgroundColor: COLOR_ACCENT_ORANGE, margin: '0 0 15px 0', fontSize: '16px', padding: '5px', display: 'inline-block' }}>TRIBUNAL SUPREMO: "SÍ LO ERES"</h4>
							<p style={{ fontSize: '15px', lineHeight: '1.5', color: COLOR_WHITE, fontWeight: 'bold' }}>
								El Supremo confirma que llamarte "machista", "troll" y "violento con las mujeres" no es un insulto, es una <strong>descripción objetiva basada en la puta realidad</strong>.
							</p>
						</div>

						<div style={{
							flex: 1,
							border: `3px solid ${COLOR_ACCENT_PURPLE}`,
							backgroundColor: 'rgba(176, 38, 255, 0.1)',
							padding: '25px',
							borderRadius: '8px',
							opacity: listSpring2,
							transform: `translateY(${interpolate(listSpring2, [0, 1], [30, 0])}px)`
						}}>
							<h4 style={{ color: COLOR_WHITE, backgroundColor: COLOR_ACCENT_PURPLE, margin: '0 0 15px 0', fontSize: '16px', padding: '5px', display: 'inline-block' }}>CONSTITUCIONAL: "A PAGAR COSTAS"</h4>
							<p style={{ fontSize: '15px', lineHeight: '1.5', color: COLOR_WHITE, fontWeight: 'bold' }}>
								Rechazo absoluto de amparo. Cierre de la vía legal. Te mandan a paseo y te toca aflojar la cartera por hacerles perder el tiempo. Derrota total.
							</p>
						</div>
					</div>
				</div>
			</div>
		</div>
	);
};

// ==========================================
// SUB-ESCENA 3: EL NEGOCIO DE LA APATÍA
// ==========================================
const SceneNegocioApatia: React.FC = () => {
	const frame = useCurrentFrame();
	const progress = frame / 9000;
	const activeSpeaker: 'host' | 'analyst' = frame % 280 < 120 ? 'host' : 'analyst';

	const insults = ["FEMINAZI", "ZORRA", "LOCA", "ENFERMA MENTAL", "MÁTALA", "CHAROCRACIA"];
	const insultOffset = (frame * 5) % 1500;

	return (
		<div style={{ flex: 1, backgroundColor: COLOR_BG, width: '100%', height: '100%', display: 'flex', position: 'relative', alignItems: 'center' }}>
			<ForensicHUD blockTitle="BLOQUE 3: EL PATÉTICO NEGOCIO DEL ODIO" progress={progress} />

			<div style={{ display: 'flex', width: '100%', height: '100%', paddingTop: '110px', boxSizing: 'border-box' }}>
				<PresentersPanel activeSpeaker={activeSpeaker} />

				<div style={{ width: '65%', padding: '60px', display: 'flex', flexDirection: 'column', justifyContent: 'center', color: COLOR_WHITE, fontFamily: 'monospace', position: 'relative', overflow: 'hidden' }}>
					<h2 style={{ color: COLOR_ACCENT_ORANGE, fontSize: '32px', marginBottom: '15px', fontWeight: '900', textShadow: `0 0 12px ${COLOR_ACCENT_ORANGE}` }}>EVIDENCIA 003: PROXENETISMO ALGORÍTMICO</h2>
					<p style={{ fontSize: '18px', lineHeight: '1.6', color: '#BBBBC9' }}>
						No hay ideología, solo una caja registradora. Lanza a su secta de inceles frustrados contra mujeres para rascar likes. Tolera amenazas de muerte en su chat porque la bilis aumenta la retención del video.
					</p>

					<div style={{
						backgroundColor: 'rgba(176, 38, 255, 0.1)',
						border: `2px solid ${COLOR_ACCENT_PURPLE}`,
						borderRadius: '8px',
						padding: '25px',
						margin: '25px 0',
						fontSize: '16px',
						boxShadow: `0 0 15px rgba(176, 38, 255, 0.2)`
					}}>
						<strong style={{ color: COLOR_WHITE }}>FÓRMULA MAGISTRAL DE LA HIPOCRESÍA:</strong>
						<div style={{ color: COLOR_ACCENT_GREEN, marginTop: '12px', fontWeight: '900', fontSize: '20px' }}>
							LLORO PÚBLICO + ACOSO PERMITIDO = € PAYPAL / PATREON €
						</div>
					</div>

					{/* Ticker de insultos tolerados (Más rápido y agresivo) */}
					<div style={{
						position: 'absolute',
						bottom: '40px',
						left: '60px',
						right: '60px',
						height: '55px',
						backgroundColor: '#0A0A0F',
						border: `2px solid ${COLOR_ACCENT_ORANGE}`,
						borderRadius: '4px',
						display: 'flex',
						alignItems: 'center',
						overflow: 'hidden',
						whiteSpace: 'nowrap',
						boxShadow: `0 0 15px rgba(255, 69, 0, 0.4)`
					}}>
						<div style={{
							display: 'flex',
							transform: `translateX(-${insultOffset}px)`,
							gap: '80px',
							fontSize: '20px',
							fontWeight: '900',
							color: COLOR_ACCENT_ORANGE
						}}>
							{Array.from({ length: 15 }).map((_, repeatIndex) => (
								<React.Fragment key={repeatIndex}>
									{insults.map((insult, idx) => (
										<span key={idx} style={{ textShadow: `0 0 8px ${COLOR_ACCENT_ORANGE}` }}>💸 "{insult}" [MONETIZADO]</span>
									))}
								</React.Fragment>
							))}
						</div>
					</div>
				</div>
			</div>
		</div>
	);
};

// ==========================================
// SUB-ESCENA 4: PARADOJA DE LA VÍCTIMA
// ==========================================
const SceneParadojaVictima: React.FC = () => {
	const frame = useCurrentFrame();
	const progress = frame / 9000;
	const activeSpeaker: 'host' | 'analyst' = frame % 360 < 180 ? 'analyst' : 'host';

	const stampScale = spring({ frame: frame - 200, fps: FPS, config: { damping: 5, mass: 2 } });

	return (
		<div style={{ flex: 1, backgroundColor: COLOR_BG, width: '100%', height: '100%', display: 'flex', position: 'relative', alignItems: 'center' }}>
			<ForensicHUD blockTitle="BLOQUE 4: LA DECONSTRUCCIÓN DEL 'MACHO ALFA'" progress={progress} />

			<div style={{ display: 'flex', width: '100%', height: '100%', paddingTop: '110px', boxSizing: 'border-box' }}>
				<PresentersPanel activeSpeaker={activeSpeaker} />

				<div style={{ width: '65%', padding: '60px', display: 'flex', flexDirection: 'column', justifyContent: 'center', color: COLOR_WHITE, fontFamily: 'monospace', position: 'relative' }}>
					<h2 style={{ color: COLOR_ACCENT_PURPLE, fontSize: '32px', marginBottom: '20px', fontWeight: '900', textShadow: `0 0 12px ${COLOR_ACCENT_PURPLE}` }}>EVIDENCIA 004: EL CRISTAL SE ROMPE</h2>

					<div style={{ display: 'flex', flexDirection: 'column', gap: '20px', color: '#BBBBC9', fontSize: '18px', lineHeight: '1.6' }}>
						<p>
							<strong>Asimetría Cinismo-Cobardía:</strong> Se ríe cuando su horda destruye psicológicamente a mujeres, pero cuando una cuenta random le hace una sátira a su "preciado personaje" en Twitch... <strong>entra en pánico nuclear.</strong>
						</p>
						<p>
							<em>"¡Estoy hartito de esto ya!"</em>. Corrió al instante a pedir la verificación oficial de marca. Todo el discurso anti-sistema desaparece cuando tocan los céntimos de su monigote corporativo.
						</p>
					</div>

					<div style={{
						display: 'flex',
						alignItems: 'center',
						justifyContent: 'center',
						backgroundColor: 'rgba(255, 69, 0, 0.1)',
						border: `4px solid ${COLOR_ACCENT_ORANGE}`,
						borderRadius: '12px',
						padding: '30px',
						marginTop: '35px',
						position: 'relative',
						overflow: 'hidden',
						transform: `scale(${interpolate(stampScale, [0, 1], [0.5, 1])}) rotate(${interpolate(stampScale, [0, 1], [-10, 0])}deg)`,
						opacity: interpolate(stampScale, [0, 1], [0, 1]),
						boxShadow: `0 0 30px rgba(255, 69, 0, 0.5)`
					}}>
						<div style={{
							fontSize: '32px',
							fontWeight: '900',
							color: COLOR_ACCENT_ORANGE,
							textShadow: `0 0 15px ${COLOR_ACCENT_ORANGE}`,
							letterSpacing: '2px'
						}}>
							🤡 CERTIFICADO DE HIPOCRESÍA VERIFICADA 🤡
						</div>
					</div>
				</div>
			</div>
		</div>
	);
};

// ==========================================
// COMPOSICIÓN MAESTRA DEL PROYECTO
// ==========================================
export const MasterPodcastComposition: React.FC = () => {
	return (
		<div style={{ flex: 1, backgroundColor: COLOR_BG, position: 'relative' }}>
			{/* Fondo de rejilla digital CRT */}
			<div style={{
				position: 'absolute',
				top: 0,
				left: 0,
				right: 0,
				bottom: 0,
				backgroundImage: `
					linear-gradient(to right, rgba(26, 26, 36, 0.2) 2px, transparent 2px),
					linear-gradient(to bottom, rgba(26, 26, 36, 0.2) 2px, transparent 2px)
				`,
				backgroundSize: '40px 40px',
				zIndex: 1
			}} />

			{/* Escenas secuenciales del Podcast */}
			<div style={{ position: 'relative', width: '100%', height: '100%', zIndex: 5 }}>
				<Series>
					<Series.Sequence durationInFrames={9000}>
						<SceneColapsoContractual />
					</Series.Sequence>
					<Series.Sequence durationInFrames={9000}>
						<SceneDerrotaJudicial />
					</Series.Sequence>
					<Series.Sequence durationInFrames={9000}>
						<SceneNegocioApatia />
					</Series.Sequence>
					<Series.Sequence durationInFrames={9000}>
						<SceneParadojaVictima />
					</Series.Sequence>
				</Series>
			</div>

			{/* Subtítulos dinámicos sincronizados */}
			<SubtitlesTrack />

			{/* Filtro estético CRT retro */}
			<CRTOverlay />

			{/* Canal de Audio del Podcast dividido en dos partes de 10 minutos (18000 frames) */}
			<Sequence from={0} durationInFrames={18000}>
				<Audio
					src={staticFile("/El_colapso_etico_y_judicial_de_UTBH.m4a")}
					volume={0.85}
				/>
			</Sequence>
			<Sequence from={18000} durationInFrames={18000}>
				<Audio
					src={staticFile("/El_lucrativo_negocio_del_odio_de_UTBH.m4a")}
					volume={0.85}
				/>
			</Sequence>
		</div>
	);
};

// Registro de composiciones para el Remotion CLI
export const RemotionVideoRoot: React.FC = () => {
	return (
		<>
			<Composition
				id="UnTioBlancoHipocritaPodcast"
				component={MasterPodcastComposition}
				durationInFrames={TOTAL_FRAMES}
				fps={FPS}
				width={1920}
				height={1080}
				defaultProps={{}}
			/>
		</>
	);
};

import { registerRoot } from 'remotion';
registerRoot(RemotionVideoRoot);
