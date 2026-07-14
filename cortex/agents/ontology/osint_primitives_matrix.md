# OSINT PRIMITIVES MATRIX (C5-REAL)
> ENFORCE: `[L67] EPI_06 (SOCINT Algorithmic Bias Evidence)`

## 🏛️ MICROKERNEL COGNITIVO (I-Δ-Σ-τ-V) APLICADO A OSINT

### 📜 INVARIANTES (INV_OSINT)
- **INV_OSINT_01 (No-Equivocación de Fuente):** Todo hallazgo SOCINT debe anclarse a un identificador inmutable (UUID, Hash, Snowflake), no a handles mutables.
- **INV_OSINT_02 (Causalidad Satelital):** El metadato temporal GEOINT (sombras, NDVI) prevalece sobre el EXIF inyectado. La luz solar no se puede hacer spoofing a nivel físico.
- **INV_OSINT_03 (Preservación Inmutable):** Toda página Clear Web investigada debe someterse a *Archive.today / Wayback* como Testigo Externo Terminal.

### 💀 ANTIPATRONES (ANTI_OSINT)
- **ANTI_OSINT_01 (Green Theater Forense):** Usar 5 herramientas redundantes para extraer el mismo metadato sin cruzar vectores ortogonales.
- **ANTI_OSINT_02 (Ceguera de Dumps):** Buscar en BREACHINT asumiendo que los hashes son inquebrantables, ignorando colisiones MD5 y reglas híbridas de Hashcat.
- **ANTI_OSINT_03 (Confianza Ciega en EXIF):** Asumir que las coordenadas GPS de una imagen en RRSS son precisas sin calcular el PRNU del sensor ni corroborar con GEOINT.

### ♻️ REDUNDANCIAS TERMODINÁMICAS
- `Sherlock` vs `Maigret` vs `Blackbird`: Alta superposición en SOCINT.
- `Shodan` vs `Censys` vs `Fofa`: Triangulación de TECHINT_DNS.
- `ExifTool` vs `Jeffrey's`: Redundancia CLI vs GUI.
- **Fallo Causal:** La redundancia sin correlación es disipación de tokens y ATP humano.

### 🩸 ANTIPATRONES EN LAS REDUNDANCIAS (Anergía Estocástica)
- **ANTI_RED_01 (Reverberación de Falsos Positivos):** Si `Sherlock` falla por un WAF, ejecutar `Maigret` desde la misma IP esperando distinto resultado (Anergía).
- **ANTI_RED_02 (Cascada de Rate Limits):** Detonar 15 herramientas de escaneo DNS simultáneamente hacia el mismo objetivo quemando el AS orgánico y provocando null-routing.
- **ANTI_RED_03 (Consenso Bizantino Falso):** Creer que porque 3 escáneres de puertos marcan "Open", el servicio es real y no un honeypot tarpit (Consenso N=3 degradado, `[L38] INV-TOP-005`).

█▄


## SOCINT (Grafos Sociales / Sesgo EPI_06)
1. `Sherlock`: Búsqueda masiva de handles en 300+ foros.
2. `Maigret`: Extracción de perfiles y cruce de identidades por username.
3. `Holehe`: Verificación de registro de email en 120+ plataformas.
4. `Epieos`: Reverse email lookup (Google Maps, Calendar, Skype).
5. `Blackbird`: Escaneo rápido de presencia en redes de alta velocidad.
6. `WhatsMyName`: Búsqueda de footprints en registros de usuarios.
7. `Social Links`: Maltego transforms para grafos de relaciones.
8. `Spiderfoot`: Automatización de footprints sociales.
9. `Namechk`: Validación de disponibilidad/existencia de dominio y redes.
10. `Webmii`: Scraping de menciones públicas y score social.
11. `Lullar`: Búsqueda inversa de email y nombres en Clear Web.
12. `Buscador de UUID de TikTok`: Mapeo de ID numérico a handle histórico.
13. `Instagram OSINT`: Extracción de metadatos de cuentas públicas y followers.
14. `Twint` (o forks): Scraping de Twitter sin API (búsqueda histórica).
15. `Nitter`: Instancias para lectura anónima y scraping de Twitter.
16. `Reddit Investigator`: Análisis de patrones de posteo y horarios.
17. `Pushshift`: Archivo histórico de Reddit (comentarios borrados).
18. `LinkedIn X-Ray`: Búsqueda booleana en Google para perfiles ocultos.
19. `RocketReach`: Cruce de perfiles profesionales y correos.
20. `Hunter.io`: Patrones de correos corporativos y SOCINT asociado.
21. `Skype Resolver`: Extracción de IPs históricas por handle (legacy).
22. `Truecaller` (Web): Reverse phone lookup.
23. `Sync.me`: Extracción de agendas sincronizadas (Sesgo EPI_06).
24. `Eyecon`: Identificación de Caller ID.
25. `Tinder API endpoints`: Triangulación de perfiles por distancia.
26. `Strava Global Heatmap`: Cruce de rutas de actividad física.
27. `Garmin Connect Search`: Perfiles deportivos y ubicaciones.
28. `SteamID Finder`: Historial de alias en perfiles de gaming.
29. `Xbox Gamertag Search`: Actividad y red de amigos Xbox Live.
30. `PSN Profiles`: Tiempos de juego y actividad de red.
31. `DiscordSnowflake`: Desencriptación de fecha de creación de cuenta.
32. `Discord.id`: Resolución de IDs de Discord.
33. `Telegram OSINT`: Búsqueda de IDs y grupos públicos.
34. `Telethon`: Scraping de metadatos de grupos de Telegram.
35. `VK.com Search`: Inteligencia de fuentes rusas.
36. `Odnoklassniki Search`: SOCINT en Europa del Este.
37. `Weibo Search`: SOCINT en ecosistema chino.
38. `Keybase.io`: Verificación de identidad cruzada (Cripto/Social).
39. `Gravatar`: Resolución de email a hash MD5 e imagen histórica.
40. `Flickr Search`: Búsqueda de galerías públicas y EXIF latente.
41. `Pinterest OSINT`: Extracción de tableros y pines guardados.
42. `Github OSINT`: Extracción de emails en commits (`.patch`).
43. `Gitrob`: Reconocimiento de organizaciones Github.
44. `Gitleaks`: Búsqueda de secretos/emails en repositorios.
45. `Bitbucket Search`: Búsqueda de repositorios públicos.
46. `StackOverflow OSINT`: Análisis de preguntas para perfilar stack técnico.
47. `Wikipedia Contributions`: Rastreo de IP a ediciones.
48. `Patreon Search`: Identificación de mecenazgo y flujos.
49. `OnlyFans Search Tools`: Mapeo de handles a perfiles de creador.
50. `Algorithmic Friend Suggestion`: Explotación de "Gente que quizás conozcas" (EPI_06).

## GEOINT (Física Satelital)
51. `Google Earth Pro`: Análisis histórico de imágenes por satélite (Time Slider).
52. `Sentinel Hub (Copernicus)`: Imágenes multiespectrales (NDVI, humedad).
53. `EOS LandViewer`: Búsqueda de satélites comerciales y abiertos.
54. `Zoom Earth`: Imágenes meteorológicas casi en tiempo real.
55. `Planet Explorer`: Imágenes satelitales de alta cadencia.
56. `Maxar Open Data`: Imágenes de zonas en crisis/desastres.
57. `Bing Maps (Bird's Eye)`: Perspectiva isométrica de alta resolución.
58. `Yandex Maps`: Superioridad en GEOINT de Rusia y Europa del Este.
59. `Baidu Maps`: GEOINT detallado de China continental (Street View local).
60. `Wikimapia`: Metadatos colaborativos sobre estructuras físicas.
61. `OpenStreetMap (OSM)`: Datos geoespaciales crudos (nodos, vías).
62. `Overpass Turbo`: Consultas estructuradas sobre bases de datos OSM.
63. `SunCalc`: Estimación de tiempo/fecha basada en sombras fotográficas.
64. `PeakFinder`: Identificación de cadenas montañosas para geolocalización.
65. `Flightradar24`: ADS-B tracking de aviación civil.
66. `ADSBexchange`: Tracking aéreo sin filtros (Aviación militar/privada).
67. `MarineTraffic`: AIS tracking de buques y cargas.
68. `VesselFinder`: Historial de puertos y rutas marítimas.
69. `Strava Heatmap`: Detección de bases o rutas de patrullaje.
70. `CCTV Webcams (Insecam)`: Acceso a cámaras IP abiertas geolocalizadas.
71. `Snapchat Map`: Videos efímeros geolocalizados en tiempo real.
72. `Flickr Geotags`: Búsqueda radial de imágenes por coordenadas.
73. `Mapillary`: Crowdsourced street-level imagery.
74. `KartaView`: Alternativa a Mapillary para recorridos callejeros.
75. `EarthCam`: Red de cámaras en vivo mundiales.
76. `GeoGuessr (Técnicas)`: Uso de bolardos, postes de luz, vegetación.
77. `ShadowCalculator`: Herramienta de medición de sombras y edificios.
78. `FIRMS (NASA)`: Datos satelitales de incendios y anomalías térmicas.
79. `ACLED`: Base de datos de conflictos armados geolocalizados.
80. `Liveuamap`: Mapeo de noticias y eventos tácticos en vivo.
81. `ECHO Daily Flash`: Mapas de desastres naturales.
82. `Bellingcat OSINT Tools`: Arsenal validado para GEOINT forense.
83. `Dual Maps`: Sincronización de Google Maps, Street View y Bing.
84. `Soar.Earth`: Superposición de mapas satelitales y drones.
85. `SkyVector`: Cartas de navegación aérea VFR/IFR.
86. `OpenRailwayMap`: Topología de infraestructura ferroviaria.
87. `OpenNauticalChart`: Topología marítima.
88. `CellMapper`: Mapeo de torres de telefonía celular y cobertura.
89. `Wigle.net`: Base de datos global de redes WiFi (SSID a Coordenadas).
90. `BSSID Locators`: Triangulación de ubicación por MAC de router.
91. `Geolocate IP`: Mapeo de rangos ASN a ubicaciones físicas.
92. `Foursquare API`: Extracción de lugares de interés (POIs).
93. `Yelp API`: Metadatos y fotos de establecimientos locales.
94. `TripAdvisor OSINT`: Reseñas e imágenes interiores.
95. `Zillow/Redfin`: Imágenes interiores de casas e historial de ventas.
96. `Cadastros Públicos`: Extracción de parcelas (Catastro, Regrid).
97. `GADM`: Mapas de áreas administrativas globales.
98. `Meteoblue`: Archivos meteorológicos históricos para corroborar clima en fotos.
99. `Ventusky`: Visualización de vientos y fenómenos meteorológicos.
100. `Windy`: Cámaras web y métricas de presión/clima.

## TECHINT_DNS (Infraestructura / Espectro)
101. `Shodan`: Motor de búsqueda de dispositivos IoT y puertos abiertos.
102. `Censys`: Escaneo continuo de certificados X.509 e IPv4.
103. `Fofa`: Shodan asiático, excelente para infraestructura en China.
104. `Zoomeye`: Búsqueda de componentes web e infraestructura de red.
105. `Hurricane Electric BGP Toolkit (bgp.he.net)`: Análisis de ASNs y peerings.
106. `ViewDNS.info`: Arsenal de herramientas DNS (Reverse IP, IP History).
107. `SecurityTrails`: Historial pasivo de DNS y subdominios.
108. `DNSDumpster`: Mapeo de infraestructura DNS (MX, TXT, A).
109. `Amass`: Automatización de enumeración de subdominios.
110. `Sublist3r`: Recolección rápida de subdominios.
111. `Crt.sh`: Búsqueda de subdominios vía Certificate Transparency Logs.
112. `Cert Spotter`: Monitoreo de emisiones de certificados.
113. `VirusTotal (Graph)`: Relaciones pasivas de DNS, IPs y malware.
114. `PassiveTotal (RiskIQ)`: Resolución histórica de IPs y WHOIS.
115. `DomainTools`: Historial WHOIS y reverse WHOIS (premium).
116. `Whoisology`: Búsqueda profunda de registros WHOIS históricos.
117. `Whoxy`: API de Reverse WHOIS económica.
118. `BGPView`: Búsqueda rápida de prefijos y sistemas autónomos.
119. `RIPE Stat`: Estadísticas de red y enrutamiento (RIPE NCC).
120. `PeeringDB`: Base de datos de interconexiones de redes.
121. `Urlscan.io`: Análisis de sandbox web (DOM, IPs, capturas).
122. `BuiltWith`: Detección de stack tecnológico de dominios.
123. `Wappalyzer`: Extracción de tecnologías web desde cabeceras.
124. `Netcraft`: Historial de hosting, OS y servidores web.
125. `Wayback Machine (Archive.org)`: Historial de respuestas HTTP (Clear Web).
126. `Archive.today`: Capturas inmutables bajo demanda de páginas web.
127. `Nmap`: Escaneo activo de puertos y fingerprinting de OS.
128. `Masscan`: Escaneo asíncrono masivo del espectro IPv4.
129. `Zmap`: Escáner de puerto único ultra-rápido.
130. `Httpx`: Probing rápido de resoluciones HTTP.
131. `Nuclei`: Escaneo de vulnerabilidades y exposiciones conocidas basadas en templates.
132. `Gau (Get All Urls)`: Extracción de URLs de AlienVault, Wayback, CommonCrawl.
133. `Waybackurls`: Fetch de URLs desde Archive.org.
134. `Hakrawler`: Web crawler rápido para descubrir endpoints.
135. `Dirb / Gobuster`: Fuerza bruta de directorios y archivos.
136. `Ffuf`: Fuzzing web de alta velocidad.
137. `Cloudflare Resolver (Crimeflare)`: Búsqueda de IP real detrás de WAFs.
138. `GreyNoise`: Filtrado de ruido de escáneres de internet (saber quién escanea).
139. `Pulsedive`: Threat intelligence cruzada de IPs e IOCs.
140. `AlienVault OTX`: Intercambio de indicadores de compromiso (IOCs).
141. `AbuseIPDB`: Verificación de IPs reportadas por spam/ataques.
142. `Robtex`: Información masiva y pasiva de redes y DNS.
143. `Spyse`: Búsqueda de vulnerabilidades, puertos y ASN.
144. `Onyphe`: Motor de búsqueda OSINT para infraestructuras cibernéticas.
145. `Hunter.how`: Búsqueda en el espacio IPv4 y dominios.
146. `Criminal IP`: Búsqueda de vulnerabilidades y puertos expuestos.
147. `Mxtoolbox`: Pruebas de salud de SMTP, MX, SPF, DMARC.
148. `Dehashed`: (Crossover TECH/BREACH) Hash lookups de contraseñas de infraestructura.
149. `WiGLE API`: (Crossover TECH/GEO) Extracción de SSID.
150. `NVD (National Vulnerability Database)`: Cruce de CVEs con stack detectado.

## FININT_PUBLIC (Ledgers Abiertos)
151. `Etherscan`: Explorador de bloques primario para Ethereum (Trazabilidad L1).
152. `BscScan`: Trazabilidad en Binance Smart Chain.
153. `Polygonscan`: Trazabilidad en Polygon.
154. `Blockchain.com Explorer`: OSINT en UTXOs de Bitcoin.
155. `Mempool.space`: Visualización de la mempool de Bitcoin y grafos de UTXO.
156. `Blockchair`: Búsqueda cruzada en múltiples blockchains simultáneas.
157. `WalletExplorer`: Clustering algorítmico de billeteras Bitcoin (Exchanges, Mixers).
158. `Breadcrumbs.app`: Grafos de investigación cripto y visualización de flujo de fondos.
159. `Arkham Intelligence`: Desanonimización de entidades y etiquetado on-chain.
160. `Nansen`: Análisis de flujos de dinero inteligente ("Smart Money").
161. `Dune Analytics`: Consultas SQL públicas sobre eventos de smart contracts.
162. `Token Terminal`: Métricas financieras y modelos de ingresos de protocolos DeFi.
163. `DefiLlama`: TVL global y análisis forense de liquidez por cadena/protocolo.
164. `Tornado Cash / Mixer Heuristics`: Análisis de volumen y tiempos de depósito/retiro.
165. `Debank`: Portfolio viewer de DeFi transversal (Saldos ERC-20).
166. `Zapper.fi`: Visor de posiciones complejas y LPs (Liquidity Pools).
167. `OpenSea / Blur`: OSINT sobre billeteras que comercian NFTs.
168. `ENS Lookup (ens.domains)`: Resolución de ETH a nombres legibles (.eth).
169. `Unstoppable Domains`: Resolución de dominios descentralizados (.crypto, .nft).
170. `Solscan`: Explorador primario de la red Solana.
171. `Tronscan`: Seguimiento masivo de USDT (TRC-20) y billeteras offshore.
172. `OXT.me`: OSINT profundo y visualización topológica de Bitcoin.
173. `Crystal Blockchain`: Herramienta de compliance y trazabilidad (Tier 1).
174. `Chainalysis (Reportes/Heurísticas)`: Identificación de patrones de ofuscación (Chain Peeling).
175. `Elliptic`: Patrones forenses de lavado de criptoactivos.
176. `EDGAR (SEC)`: Búsqueda pública de filings corporativos de empresas cotizadas (10-K, 10-Q).
177. `OpenCorporates`: Base de datos global unificada de registros corporativos.
178. `Offshore Leaks Database (ICIJ)`: Búsqueda en Panama/Paradise/Pandora Papers.
179. `UK Companies House`: Registros públicos corporativos, directores y UBOs en UK.
180. `SearchIQ (Sunbiz, etc.)`: Registros corporativos por estado en EE.UU.
181. `PitchBook`: Flujos de venture capital y valoraciones.
182. `Crunchbase`: Estructura de financiación, series de inversión y fundadores.
183. `LittleSis`: Grafo de relaciones de la oligarquía corporativa y política.
184. `FEC.gov`: Contribuciones de campañas políticas y flujos de PACs.
185. `Tenders Electronic Daily (TED)`: Contratos públicos de la Unión Europea.
186. `SAM.gov`: Contratos gubernamentales en EE.UU.
187. `Opensecrets.org`: Datos sobre lobbying y financiamiento político.
188. `SWIFT BIC Search`: Resolución de códigos bancarios internacionales.
189. `IIN (Issuer Identification Number)`: Identificación de bancos emisores de tarjetas por BIN.
190. `FATF High-Risk Jurisdictions`: Correlación de flujos hacia paraísos fiscales.
191. `OFAC Sanctions List (SDN)`: Búsqueda de individuos y billeteras sancionadas.
192. `EU Sanctions Map`: Mapeo visual de embargos y sanciones financieras europeas.
193. `RuPEP`: Base de datos de personas expuestas políticamente (Rusia).
194. `Búsqueda de Direcciones IP de Nodos Lightning`: Geolocalización de liquidez en LN.
195. `Glassnode`: Métricas on-chain e indicadores de rentabilidad macro.
196. `CoinMarketCap / CoinGecko API`: Historical price data para auditoría de swaps.
197. `DexScreener`: Flujos de dinero en DEXes menores (Liquidity Sniping).
198. `EVM Bytecode Decompilation`: Extracción de lógica en contratos maliciosos (Ethervm.io).
199. `Polymarket / Predicition Markets`: Rastreo de apuestas y ballenas sobre eventos reales.
200. `GitHub Gists de Hackers/Auditors`: Análisis post-mortem de DeFi exploits para rastrear billeteras involucradas.

## IMINT_EXIF (Esteganografía / Visual)
201. `ExifTool`: Analizador C5-REAL definitivo para metadata (EXIF, IPTC, XMP).
202. `Jeffrey's Image Metadata Viewer`: Interfaz web para ExifTool.
203. `FotoForensics (ELA)`: Análisis de nivel de error (Error Level Analysis) para detectar manipulaciones.
204. `Forensically`: Suite web (Magnifier, Clone Detection, Noise Analysis).
205. `Stegsolve`: Manipulación de planos de bits para revelar esteganografía (LSB).
206. `Zsteg`: Extracción esteganográfica masiva en PNGs y BMPs.
207. `Steghide`: Extracción de datos cifrados con password.
208. `Outguess`: Analizador y extractor de esteganografía universal.
209. `InVid / WeVerify`: Verificación de video, extracción de keyframes y búsqueda inversa.
210. `Google Lens`: Búsqueda visual semántica avanzada y OCR en imagen.
211. `Yandex Images`: Superior en reconocimiento facial inverso y arquitecturas soviéticas.
212. `Bing Visual Search`: Búsqueda inversa con segmentación de objetos (Bounding boxes).
213. `TinEye`: Búsqueda inversa estricta (no semántica), excelente para detectar la imagen original.
214. `PimEyes`: Reconocimiento facial extremo en Clear Web (Premium/Cuestionable).
215. `FaceCheck.id`: Búsqueda inversa de rostros con enlaces a RRSS.
216. `Search4faces`: Búsqueda facial especializada en VK, TikTok, OK.ru.
217. `Betaface`: Análisis biométrico de edad, género y rasgos estructurales.
218. `Ghiro`: Plataforma automatizada de forense de imágenes.
219. `Aperisolve`: Suite web que combina zsteg, steghide, outguess y exiftool.
220. `Sherloq`: Entorno de análisis forense digital para integridad de imágenes.
221. `JPEGsnoop`: Decodificación profunda de matrices de cuantización de JPEG.
222. `Ffmpeg (Keyframe extraction)`: Extracción determinista de i-frames para búsqueda inversa.
223. `Youtube-dl / yt-dlp`: Extracción del video original sin recodificar.
224. `Búsqueda Inversa de Video en Yandex`: Usando miniaturas generadas.
225. `PlatesMania`: Base de datos crowdsourced de matrículas de vehículos.
226. `Autoteka / Carfax`: Extracción de historial de accidentes y VINs (IMINT vehicular).
227. `Ironsource / Identificación de Camuflaje`: IMINT táctico militar.
228. `Detección de Sombras (Geometría Epipolar)`: Para desmentir montajes.
229. `Verificación de Reflejos (Córnea/Espejos)`: Extracción de geometría del fotógrafo.
230. `Análisis de Ruido del Sensor (PRNU)`: Huella dactilar balística de cámaras digitales.
231. `String Extraction (strings bin/img)`: Búsqueda de metadata de herramientas de edición en el binario.
232. `Binwalk`: Extracción de archivos incrustados en imágenes o firmware.
233. `GIMP / Photoshop (Levels/Curves)`: Compresión manual del histograma para revelar artefactos de borrado.
234. `Mapillary / KartaView (Crossover)`: Verificación del punto de vista terrestre contra la imagen analizada.
235. `EarthCam Archive`: Cotejar condiciones climáticas e iluminación de la foto vs la hora alegada.
236. `Clearview AI (Restringido)`: Extensión del alcance LEO (Law Enforcement), pero concepto base.
237. `Deepware Scanner`: Detección de Deepfakes en video.
238. `Sensity AI`: API para detección visual de IA generativa.
239. `Hive Moderation`: Clasificación de imágenes generadas por IA y NSFW.
240. `DALL-E / Midjourney Artifact Detection`: Análisis de anomalías morfológicas (manos, texto irreal).
241. `EXIF GPS Offset Verification`: Comprobar si las coordenadas GPS apuntan al centro de una ciudad (default de privacidad) o a un punto preciso.
242. `Detección de "Magic Bytes"`: Validar que la cabecera real coincide con la extensión del archivo.
243. `VLC (Codec Information)`: Extracción de metadatos de renderizado de video y hardware de captura.
244. `Audio visualizers (Audacity/Spek)`: Análisis de espectrograma para encontrar imágenes ocultas en audio.
245. `Color Picker Tool`: Mapeo de paletas HEX/RGB de uniformes/marcas para identificar facciones.
246. `OCR Tools (Tesseract)`: Extracción determinista de texto en fondos borrosos.
247. `Readability / Contrast Enhancers`: Mejorar imágenes oscuras de CCTV.
248. `Tineye Color Search`: Búsqueda de imágenes por ratio de color (ej. color de una camiseta en protestas).
249. `GigaPan`: Análisis de imágenes de gigapíxeles para extraer detalles microscópicos en multitudes.
250. `Metadata Strippers (Comparativa)`: Analizar qué metadatos fueron dejados intencionalmente vs cuáles fueron limpiados por la API de la red social.

## BREACHINT (Data Dumps)
251. `Have I Been Pwned (HIBP)`: Verificación de correos en brechas públicas (sin hashes).
252. `DeHashed`: Búsqueda de texto plano, correos, nombres, IPs, hashes y contraseñas.
253. `Snusbase`: Indexador masivo de bases de datos leakeadas y combos.
254. `Leak-Lookup`: API pública para búsqueda en dumps masivos.
255. `IntelX (Intelligence X)`: Búsqueda en repositorios de leaks, Dark Web, pastebins.
256. `WeLeakInfo (Alternativas/Clones)`: Interfaces históricas a colecciones (Collection #1, COMB).
257. `Pastebin Search (Google Dorks)`: Búsqueda de dumps en texto plano (`site:pastebin.com`).
258. `Ahmia`: Motor de búsqueda de la red Tor (archivos .onion).
259. `Ransomwatch`: Monitoreo de DLS (Data Leak Sites) de grupos de Ransomware.
260. `Holehe (Crossover)`: Verificación de cuentas que podrían estar en un dump.
261. `Hashcat / John the Ripper`: Craqueo de hashes obtenidos en BREACHINT.
262. `CrackStation`: Tablas Rainbow y base de hashes pre-calculada gigantesca.
263. `BreachDirectory`: Base de datos de hashes expuestos.
264. `Gitleaks / TruffleHog (Crossover)`: Extracción de contraseñas de AWS/GCP expuestas en Github.
265. `Telegram Bot Leaks (Ej: @LeakedInfoBot)`: Extracción rápida desde bases de datos rusas.
266. `RaidForums / Breached (Archivos/Cachés)`: Lectura histórica de foros confiscados.
267. `XSS.is / Exploit.in (Foros)`: Búsqueda de menciones de compra/venta de logs corporativos.
268. `Russian Market / Genesis Market (OSINT)`: Huellas de infostealers (Redline, Raccoon) vendiendo cookies de sesión.
269. `Prometheus / Telegram Darknet Monitors`: Alertas automatizadas de volcados.
270. `Searchcode`: Búsqueda de contraseñas hardcodeadas en repositorios open source.
271. `Shodan (Crossover ElasticSearch)`: Indexación de clusters ElasticSearch expuestos sin autenticación.
272. `Censys (Crossover S3)`: Búsqueda de buckets S3 públicos con archivos de configuración confidenciales.
273. `Grayhat Warfare`: Buscador especializado en buckets S3, Azure y DigitalOcean expuestos.
274. `PublicWWW`: Motor de búsqueda de código fuente web (búsqueda de tokens API).
275. `Urlscan.io (Búsqueda de JWT)`: Búsqueda de tokens JWT en URLs o cabeceras expuestas accidentalmente.
276. `Kibana Open Dashboards`: Dashboards ELK expuestos al público.
277. `FTP Anonymous Login Scanners`: Detección de servidores con configuración `anonymous:anonymous`.
278. `RSync Open Modules`: Puertos 873 expuestos con volcados de DB.
279. `SMB Ghost/Open Shares`: Escaneo de puertos 445 con recursos compartidos IPC$.
280. `CouchDB Open Ports`: Bases de datos NoSQL sin autenticación.
281. `MongoDB Ransomware Logs`: BDs purgadas con notas de rescate (Confirman breach previo).
282. `Ghostbin / Hastebin / ControlC`: Alternativas a Pastebin frecuentemente usadas en leaks.
283. `Trello Board Search (Google Dorks)`: Tableros públicos con credenciales e información corporativa.
284. `Jira / Confluence Open Instances`: Sistemas de ticketing con exposición de adjuntos (dumps de logs).
285. `Google Drive / Docs Dorks`: Búsqueda de hojas de cálculo de "Passwords" (`site:drive.google.com`).
286. `Notion Public Pages`: Exposición accidental de wikis de empresas.
287. `Postman Public Workspaces`: Colecciones de APIs con tokens Bearer o Basic Auth vivos.
288. `Docker Hub OSINT`: Imágenes con claves privadas, ssh o variables de entorno (ENV) incrustadas.
289. `Wayback Machine (Robots.txt históricos)`: Verificación de endpoints de bases de datos que luego fueron ocultados.
290. `Crt.sh (Wildcard Certs)`: Identificación de dominios internos (ej: `db-backup.empresa.com`) objetivo de filtraciones.
291. `GPG Keyservers (Ej: pgp.mit.edu)`: Mapeo de identidades y direcciones de correo de atacantes/víctimas.
292. `Bitcoin Abuse / Chainabuse`: Búsqueda de direcciones BTC listadas en notas de ransom o fraudes.
293. `Etherscan Labels (Phish/Hack)`: Rastreo de fondos de billeteras marcadas por el consorcio.
294. `Dorking de archivos SQL/CSV`: `filetype:sql "INSERT INTO" password`, `filetype:csv "email,password"`.
295. `Discord/Slack Invite OSINT`: Acceso a canales donde se distribuyen logs y combos.
296. `I Know What You Downloaded (IKWYD)`: Extracción de descargas BitTorrent de IPs (Piratería, dumps).
297. `VirusTotal (Crossover PCAP)`: Capturas de tráfico subidas que contienen credenciales en claro (HTTP/FTP).
298. `ANY.RUN / Joesandbox Public Tasks`: Sandboxes donde investigadores suben malware y exponen credenciales corporativas simuladas.
299. `PwnDB (Servicio Onion Histórico)`: Búsqueda de correos en texto plano de colecciones masivas.
300. `Identity Leak Check (HPI)`: Servicio académico del Instituto Hasso Plattner para auditoría de brechas en correos.

█▄

*Cristalización de Matriz C5-REAL completada. Fricción cero.*


<!-- Creator: Borja Moskv -->
