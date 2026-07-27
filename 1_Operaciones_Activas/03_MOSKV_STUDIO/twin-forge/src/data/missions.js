export const MISSIONS = [
  {
    id: 1, title: "Hola Mundo", icon: "🚀", lang: "javascript",
    description: "Tu primer programa. Escribe un mensaje en la consola usando console.log().",
    template: '// Misión 1: Hola Mundo\n// Escribe tu nombre entre las comillas\nconsole.log("¡Hola, mundo!");\n',
    hints: [
      "Usa console.log() para mostrar texto en la consola",
      'Escribe: console.log("¡Hola, soy [tu nombre]!");',
      'Solución: console.log("¡Hola, soy Martina!");'
    ],
    validate: (output) => output.some(l => l.text && l.text.length > 0)
  },
  {
    id: 2, title: "La Calculadora", icon: "🧮", lang: "javascript",
    description: "Aprende a usar variables y operaciones matemáticas. Calcula tu edad en días.",
    template: '// Misión 2: La Calculadora\nlet edad = 14;\nlet diasPorAnio = 365;\n\n// Calcula tu edad en días\nlet edadEnDias = edad * diasPorAnio;\nconsole.log("Tienes " + edadEnDias + " días de vida");\n\n// Ahora calcula tu edad en horas\n// Tu código aquí:\n',
    hints: [
      "Multiplica edadEnDias por 24 (horas en un día)",
      "let edadEnHoras = edadEnDias * 24;",
      'console.log("Tienes " + edadEnHoras + " horas de vida");'
    ],
    validate: (output) => output.some(l => l.text && l.text.includes("días"))
  },
  {
    id: 3, title: "¿Cómo te llamas?", icon: "💬", lang: "javascript",
    description: "Aprende sobre strings (textos). Combina palabras para crear frases.",
    template: '// Misión 3: Strings\nlet nombre = "Escribe tu nombre";\nlet apellido = "Escribe tu apellido";\n\n// Junta nombre y apellido\nlet nombreCompleto = nombre + " " + apellido;\nconsole.log("Me llamo " + nombreCompleto);\n\n// Haz que tu nombre salga en MAYÚSCULAS\n// Pista: usa .toUpperCase()\n',
    hints: [
      "Los strings tienen métodos como .toUpperCase() y .toLowerCase()",
      "console.log(nombreCompleto.toUpperCase());",
      'También prueba: console.log(nombreCompleto.length + " letras");'
    ],
    validate: (output) => output.some(l => l.text && l.text.includes("Me llamo"))
  },
  {
    id: 4, title: "El Adivino", icon: "🎲", lang: "javascript",
    description: "Genera un número aleatorio y usa if/else para tomar decisiones.",
    template: '// Misión 4: El Adivino\n// Math.random() genera un número entre 0 y 1\nlet numero = Math.floor(Math.random() * 10) + 1;\nconsole.log("El número secreto es: " + numero);\n\n// Comprueba si el número es mayor que 5\nif (numero > 5) {\n  console.log("¡Es un número GRANDE!");\n} else {\n  console.log("Es un número pequeño");\n}\n\n// Añade más condiciones: ¿es par o impar?\n// Pista: usa el operador % (módulo)\n',
    hints: [
      "Un número es par si numero % 2 === 0",
      'if (numero % 2 === 0) { console.log("Es PAR"); }',
      'else { console.log("Es IMPAR"); }'
    ],
    validate: (output) => output.some(l => l.text && l.text.includes("número"))
  },
  {
    id: 5, title: "Cuenta Atrás", icon: "⏳", lang: "javascript",
    description: "Usa bucles for para repetir acciones. Crea una cuenta atrás épica.",
    template: '// Misión 5: Cuenta Atrás\n// Un bucle for repite código varias veces\n\nfor (let i = 10; i >= 1; i--) {\n  console.log(i + "...");\n}\nconsole.log("🚀 ¡DESPEGUE!");\n\n// Ahora haz un bucle que muestre los números del 1 al 20\n// pero solo los que sean múltiplos de 3\n',
    hints: [
      "Usa for (let i = 1; i <= 20; i++)",
      "Dentro del bucle: if (i % 3 === 0) { console.log(i); }",
      "Los múltiplos de 3 hasta 20 son: 3, 6, 9, 12, 15, 18"
    ],
    validate: (output) => output.some(l => l.text && l.text.includes("DESPEGUE"))
  },
  {
    id: 6, title: "La Lista de la Compra", icon: "📝", lang: "javascript",
    description: "Aprende arrays: listas de cosas que puedes modificar y recorrer.",
    template: '// Misión 6: Arrays\nlet lista = ["pizza", "helado", "patatas"];\n\nconsole.log("Mi lista tiene " + lista.length + " cosas");\nconsole.log("Lo primero es: " + lista[0]);\n\n// Añade un elemento\nlista.push("chocolate");\n\n// Muestra toda la lista\nfor (let item of lista) {\n  console.log("🛒 " + item);\n}\n\n// Crea tu propia lista de 5 juegos favoritos\n',
    hints: [
      'let juegos = ["Minecraft", "Fortnite", ...];',
      "Usa .push() para añadir y .pop() para quitar el último",
      "Recorre con: for (let juego of juegos) { console.log(juego); }"
    ],
    validate: (output) => output.some(l => l.text && l.text.includes("🛒"))
  },
  {
    id: 7, title: "Tu Primer Dibujo", icon: "🎨", lang: "javascript",
    description: "Dibuja en el canvas: líneas, formas y colores. ¡Arte digital!",
    template: '// Misión 7: Canvas — Tu Primer Dibujo\n// El canvas es como un lienzo donde puedes dibujar\n\n// Fondo negro\nctx.fillStyle = "#0A0A0A";\nctx.fillRect(0, 0, canvas.width, canvas.height);\n\n// Dibuja un círculo\nctx.beginPath();\nctx.arc(160, 120, 50, 0, Math.PI * 2);\nctx.fillStyle = "#A855F7";\nctx.fill();\n\n// Dibuja un rectángulo\nctx.fillStyle = "#06B6D4";\nctx.fillRect(50, 50, 80, 40);\n\n// Escribe texto\nctx.fillStyle = "#F0F0F0";\nctx.font = "20px Inter";\nctx.fillText("¡Hola Canvas!", 70, 200);\n\n// Ahora dibuja algo tuyo: una cara, una casa, lo que quieras\n',
    hints: [
      "ctx.arc(x, y, radio, 0, Math.PI * 2) dibuja un círculo",
      "ctx.fillRect(x, y, ancho, alto) dibuja un rectángulo relleno",
      "Cambia los colores con ctx.fillStyle = '#FF0000';"
    ],
    validate: () => true
  },
  {
    id: 8, title: "Pong Mini", icon: "🏓", lang: "javascript",
    description: "Tu primer juego: una pelota que rebota por la pantalla.",
    template: '// Misión 8: Pong Mini — Pelota Rebotando\nlet x = 160, y = 120;\nlet dx = 3, dy = 2;\nlet radius = 10;\n\nfunction gameLoop() {\n  // Limpiar pantalla\n  ctx.fillStyle = "#0A0A0A";\n  ctx.fillRect(0, 0, canvas.width, canvas.height);\n\n  // Dibujar pelota\n  ctx.beginPath();\n  ctx.arc(x, y, radius, 0, Math.PI * 2);\n  ctx.fillStyle = "#A855F7";\n  ctx.fill();\n\n  // Mover pelota\n  x += dx;\n  y += dy;\n\n  // Rebotar en los bordes\n  if (x + radius > canvas.width || x - radius < 0) dx = -dx;\n  if (y + radius > canvas.height || y - radius < 0) dy = -dy;\n\n  requestAnimationFrame(gameLoop);\n}\n\ngameLoop();\n',
    hints: [
      "dx y dy son la velocidad. Cámbialos para ir más rápido",
      "Añade más pelotas creando más variables x2, y2, etc.",
      "Cambia el color cada vez que rebote usando Math.random()"
    ],
    validate: () => true
  },
  {
    id: 9, title: "Snake", icon: "🐍", lang: "javascript",
    description: "El juego clásico de la serpiente. ¡Tu mayor reto hasta ahora!",
    template: '// Misión 9: Snake — El Juego Clásico\nconst TILE = 20;\nconst COLS = Math.floor(canvas.width / TILE);\nconst ROWS = Math.floor(canvas.height / TILE);\n\nlet snake = [{x: 5, y: 5}];\nlet dir = {x: 1, y: 0};\nlet food = spawnFood();\nlet score = 0;\n\nfunction spawnFood() {\n  return {\n    x: Math.floor(Math.random() * COLS),\n    y: Math.floor(Math.random() * ROWS)\n  };\n}\n\ndocument.addEventListener("keydown", (e) => {\n  if (e.key === "ArrowUp" && dir.y === 0) dir = {x: 0, y: -1};\n  if (e.key === "ArrowDown" && dir.y === 0) dir = {x: 0, y: 1};\n  if (e.key === "ArrowLeft" && dir.x === 0) dir = {x: -1, y: 0};\n  if (e.key === "ArrowRight" && dir.x === 0) dir = {x: 1, y: 0};\n});\n\nfunction update() {\n  const head = {x: snake[0].x + dir.x, y: snake[0].y + dir.y};\n  \n  // Game over si sale del mapa\n  if (head.x < 0 || head.x >= COLS || head.y < 0 || head.y >= ROWS) {\n    console.log("💀 Game Over — Puntos: " + score);\n    return;\n  }\n  \n  snake.unshift(head);\n  \n  if (head.x === food.x && head.y === food.y) {\n    score += 10;\n    food = spawnFood();\n    console.log("🍎 ¡+10 puntos! Total: " + score);\n  } else {\n    snake.pop();\n  }\n  \n  // Dibujar\n  ctx.fillStyle = "#0A0A0A";\n  ctx.fillRect(0, 0, canvas.width, canvas.height);\n  \n  ctx.fillStyle = "#22C55E";\n  for (let s of snake) {\n    ctx.fillRect(s.x * TILE + 1, s.y * TILE + 1, TILE - 2, TILE - 2);\n  }\n  \n  ctx.fillStyle = "#EF4444";\n  ctx.fillRect(food.x * TILE + 1, food.y * TILE + 1, TILE - 2, TILE - 2);\n  \n  ctx.fillStyle = "#F0F0F0";\n  ctx.font = "14px Inter";\n  ctx.fillText("Puntos: " + score, 10, 20);\n  \n  setTimeout(() => requestAnimationFrame(update), 120);\n}\n\nupdate();\n',
    hints: [
      "Usa las flechas del teclado para mover la serpiente",
      "Prueba a cambiar el setTimeout de 120 a 80 para más velocidad",
      "Añade game-over cuando la serpiente se toque a sí misma"
    ],
    validate: () => true
  },
  {
    id: 10, title: "Hola Python", icon: "🐍", lang: "python",
    description: "Tu primer programa en Python. ¡El lenguaje más popular del mundo!",
    template: '# Misión 10: Hola Python\n# Python es diferente a JavaScript pero más fácil de leer\n\nprint("¡Hola desde Python!")\n\n# Variables\nnombre = "Tu nombre aquí"\nedad = 14\n\nprint(f"Me llamo {nombre} y tengo {edad} años")\n\n# Listas (como arrays en JavaScript)\ncolores = ["rojo", "azul", "verde"]\nfor color in colores:\n    print(f"Color favorito: {color}")\n\n# Calcula algo\nresultado = 2 ** 10  # 2 elevado a 10\nprint(f"2 elevado a 10 = {resultado}")\n',
    hints: [
      "En Python usamos print() en vez de console.log()",
      "f-strings: f\"Hola {variable}\" mezcla texto y variables",
      "Python usa indentación (espacios) en vez de llaves {}"
    ],
    validate: (output) => output.some(l => l.text && l.text.includes("Hola"))
  },
  {
    id: 11, title: "Python Math", icon: "📐", lang: "python",
    description: "Funciones y módulo math. Crea tu propia calculadora científica.",
    template: '# Misión 11: Python Math\nimport math\n\n# Funciones: bloques de código reutilizables\ndef area_circulo(radio):\n    return math.pi * radio ** 2\n\n# Prueba tu función\nradio = 5\narea = area_circulo(radio)\nprint(f"Área de un círculo con radio {radio}: {area:.2f}")\n\n# Crea una función que calcule el área de un triángulo\n# Fórmula: base * altura / 2\ndef area_triangulo(base, altura):\n    # Tu código aquí\n    pass\n\n# Pruébala:\n# print(area_triangulo(10, 5))\n',
    hints: [
      "Cambia pass por: return base * altura / 2",
      ":.2f muestra solo 2 decimales",
      "Prueba también: math.sqrt(144) para raíz cuadrada"
    ],
    validate: (output) => output.some(l => l.text && l.text.includes("Área"))
  },
  {
    id: 12, title: "Dibuja con Turtle", icon: "🐢", lang: "python",
    description: "Turtle graphics: programa una tortuga que dibuja por ti.",
    template: '# Misión 12: Turtle Graphics\n# (Versión simplificada para el navegador)\nimport math\n\n# Simulamos turtle con print\ndef dibujar_cuadrado(lado):\n    print(f"🐢 Dibujando cuadrado de {lado}px")\n    for i in range(4):\n        print(f"  → Avanza {lado} pixels")\n        print(f"  ↻ Gira 90 grados")\n\ndef dibujar_triangulo(lado):\n    print(f"🐢 Dibujando triángulo de {lado}px")\n    for i in range(3):\n        print(f"  → Avanza {lado} pixels")\n        print(f"  ↻ Gira 120 grados")\n\ndibujar_cuadrado(100)\nprint()\ndibujar_triangulo(80)\n\n# Crea tu propia función para dibujar un polígono de N lados\n# Pista: el ángulo de giro = 360 / N\n',
    hints: [
      "def dibujar_poligono(lados, tamano):",
      "angulo = 360 / lados",
      "for i in range(lados): print(f'Gira {angulo} grados')"
    ],
    validate: (output) => output.some(l => l.text && l.text.includes("🐢"))
  },
  {
    id: 13, title: "Tu Web", icon: "🌐", lang: "html",
    description: "Crea tu primera página web con HTML y CSS.",
    template: '<!-- Misión 13: Tu Primera Web -->\n<!DOCTYPE html>\n<html>\n<head>\n  <style>\n    body {\n      background: #0A0A0A;\n      color: #F0F0F0;\n      font-family: sans-serif;\n      display: flex;\n      flex-direction: column;\n      align-items: center;\n      padding: 40px;\n    }\n    h1 {\n      background: linear-gradient(135deg, #A855F7, #06B6D4);\n      -webkit-background-clip: text;\n      -webkit-text-fill-color: transparent;\n      font-size: 3rem;\n    }\n    .card {\n      background: #1A1A1A;\n      border: 1px solid #333;\n      border-radius: 16px;\n      padding: 24px;\n      margin: 16px;\n      max-width: 400px;\n    }\n  </style>\n</head>\n<body>\n  <h1>Mi Web</h1>\n  <div class="card">\n    <h2>Sobre mí</h2>\n    <p>Escribe algo sobre ti aquí</p>\n  </div>\n  <!-- Añade más cards con tus hobbies, juegos favoritos, etc. -->\n</body>\n</html>',
    hints: [
      "Copia el div.card y pégalo debajo para crear más tarjetas",
      "Cambia los colores del gradiente en h1",
      "Añade imágenes con <img src='url' />"
    ],
    validate: () => true
  },
  {
    id: 14, title: "Web Interactiva", icon: "⚡", lang: "html",
    description: "Añade interactividad con JavaScript: botones, eventos, DOM.",
    template: '<!-- Misión 14: Web Interactiva -->\n<!DOCTYPE html>\n<html>\n<head>\n  <style>\n    body { background: #0A0A0A; color: #F0F0F0; font-family: sans-serif; text-align: center; padding: 40px; }\n    button {\n      background: linear-gradient(135deg, #A855F7, #EC4899);\n      color: white; border: none; padding: 12px 24px;\n      border-radius: 12px; font-size: 1rem;\n      cursor: pointer; margin: 8px;\n      transition: transform 0.2s;\n    }\n    button:hover { transform: scale(1.1); }\n    #contador { font-size: 4rem; margin: 20px; }\n    #mensaje { font-size: 1.2rem; margin: 20px; min-height: 30px; }\n  </style>\n</head>\n<body>\n  <h1>Contador Interactivo</h1>\n  <div id="contador">0</div>\n  <button onclick="sumar()">➕ Sumar</button>\n  <button onclick="restar()">➖ Restar</button>\n  <button onclick="reset()">🔄 Reset</button>\n  <p id="mensaje"></p>\n\n  <script>\n    let count = 0;\n    const display = document.getElementById("contador");\n    const msg = document.getElementById("mensaje");\n\n    function sumar() {\n      count++;\n      display.textContent = count;\n      if (count === 10) msg.textContent = "🎉 ¡Has llegado a 10!";\n    }\n\n    function restar() {\n      count--;\n      display.textContent = count;\n    }\n\n    function reset() {\n      count = 0;\n      display.textContent = count;\n      msg.textContent = "";\n    }\n  </script>\n</body>\n</html>',
    hints: [
      "document.getElementById() encuentra elementos del HTML",
      "onclick='funcion()' ejecuta código al hacer click",
      "Añade un botón que multiplique por 2: count *= 2;"
    ],
    validate: () => true
  },
  {
    id: 15, title: "Proyecto Libre", icon: "🏆", lang: "javascript",
    description: "¡Crea lo que quieras! Un juego, una calculadora, arte digital... ¡tú decides!",
    template: '// Misión 15: Proyecto Libre\n// ¡Esto es TUYO! Crea lo que quieras.\n//\n// Ideas:\n// 🎮 Un juego (usa el canvas)\n// 🧮 Una calculadora especial\n// 🎨 Arte generativo con Math.random()\n// 📊 Un quiz de preguntas\n// 🎵 Un secuenciador de sonidos\n//\n// ¡No hay reglas! Experimenta y diviértete.\n\nconsole.log("¡Empieza tu proyecto aquí!");\n',
    hints: [
      "Reutiliza código de misiones anteriores como base",
      "Combina canvas + teclado para hacer un juego",
      "No tengas miedo de equivocarte — ¡así se aprende!"
    ],
    validate: () => true
  }
];

export const ACHIEVEMENTS = [
  { id: "first_run", name: "Primer Paso", icon: "🚀", desc: "Ejecutar código por primera vez" },
  { id: "no_errors_5", name: "Sin Errores", icon: "⭐", desc: "5 ejecuciones seguidas sin error" },
  { id: "pythonista", name: "Pythonista", icon: "🐍", desc: "Completar primera misión Python" },
  { id: "artist", name: "Artista Digital", icon: "🎨", desc: "Dibujar en Canvas" },
  { id: "game_dev", name: "Game Dev", icon: "🎮", desc: "Completar misión Pong" },
  { id: "hacker", name: "Hacker", icon: "💻", desc: "Escribir 1000 líneas de código" },
  { id: "marathon", name: "Maratón", icon: "⏱️", desc: "Codear 1 hora seguida" },
  { id: "twin_sync", name: "Gemelos del Código", icon: "👯", desc: "Ambos perfiles completan la misma misión" },
  { id: "mission_5", name: "Medio Camino", icon: "🏅", desc: "Completar 5 misiones" },
  { id: "mission_10", name: "Veterano", icon: "🎖️", desc: "Completar 10 misiones" },
  { id: "mission_all", name: "Leyenda", icon: "🏆", desc: "Completar todas las misiones" },
  { id: "night_owl", name: "Búho Nocturno", icon: "🦉", desc: "Programar después de las 23:00" },
  { id: "early_bird", name: "Madrugador/a", icon: "🐦", desc: "Programar antes de las 8:00" },
  { id: "custom_code", name: "Creador/a", icon: "✨", desc: "Modificar código de una misión" },
  { id: "snake_score", name: "Snake Master", icon: "👑", desc: "Conseguir 100 puntos en Snake" }
];
