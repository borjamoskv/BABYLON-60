
// C5-REAL: GPT-5.6 Sol Cinematic Premium WebGL Engine & GSAP/Lenis Orchestrator
(function() {
  // --- 1. Smooth Scroll (Lenis) ---
  const lenis = new Lenis({
    duration: 1.2,
    easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
    direction: 'vertical',
    gestureDirection: 'vertical',
    smooth: true,
    mouseMultiplier: 1,
    smoothTouch: false,
    touchMultiplier: 2,
    infinite: false,
  });

  function raf(time) {
    lenis.raf(time);
    requestAnimationFrame(raf);
  }
  requestAnimationFrame(raf);

  // --- 2. Custom Magnetic Cursor ---
  const cursor = document.getElementById('cursor-magnet');
  let mouseX = 0;
  let mouseY = 0;
  let cursorX = 0;
  let cursorY = 0;

  window.addEventListener('mousemove', (e) => {
    mouseX = e.clientX;
    mouseY = e.clientY;
  });

  // Magnetic hover effect
  const hoverElements = document.querySelectorAll('a, button, .btn');
  hoverElements.forEach(el => {
    el.addEventListener('mouseenter', () => cursor.classList.add('hover'));
    el.addEventListener('mouseleave', () => cursor.classList.remove('hover'));
  });

  // --- 3. Three.js Volumetric Particle Swarm (Industrial Noir x Cobalt/Gold) ---
  const canvas = document.getElementById('bg-canvas');
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
  const renderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true });
  
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

  // Particles
  const particlesGeometry = new THREE.BufferGeometry();
  const particlesCount = 3000; // Dense swarm
  const posArray = new Float32Array(particlesCount * 3);
  const colorArray = new Float32Array(particlesCount * 3);

  const colorCobalt = new THREE.Color('#2B3BE5');
  const colorGold = new THREE.Color('#F59E0B');

  for(let i = 0; i < particlesCount * 3; i+=3) {
    // Distribute in a volumetric torus-like shape
    const radius = 10 + Math.random() * 20;
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos((Math.random() * 2) - 1);

    posArray[i] = radius * Math.sin(phi) * Math.cos(theta);     // x
    posArray[i+1] = radius * Math.sin(phi) * Math.sin(theta);   // y
    posArray[i+2] = radius * Math.cos(phi) + (Math.random()*10 - 5); // z

    // Mix colors based on position
    const mixedColor = colorCobalt.clone().lerp(colorGold, Math.random() * 0.4);
    colorArray[i] = mixedColor.r;
    colorArray[i+1] = mixedColor.g;
    colorArray[i+2] = mixedColor.b;
  }

  particlesGeometry.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
  particlesGeometry.setAttribute('color', new THREE.BufferAttribute(colorArray, 3));

  // Custom Shader Material for glow and volumetric look
  const particlesMaterial = new THREE.PointsMaterial({
    size: 0.05,
    vertexColors: true,
    blending: THREE.AdditiveBlending,
    transparent: true,
    opacity: 0.8
  });

  const particleMesh = new THREE.Points(particlesGeometry, particlesMaterial);
  scene.add(particleMesh);

  camera.position.z = 25;

  // Animation Loop for Three.js and Cursor
  let clock = new THREE.Clock();
  function animate() {
    const elapsedTime = clock.getElapsedTime();
    
    // Smooth cursor follow
    cursorX += (mouseX - cursorX) * 0.2;
    cursorY += (mouseY - cursorY) * 0.2;
    cursor.style.transform = `translate(${cursorX}px, ${cursorY}px) translate(-50%, -50%)`;

    // Rotate particles
    particleMesh.rotation.y = elapsedTime * 0.05;
    particleMesh.rotation.x = elapsedTime * 0.02;

    // React to scroll (parallax)
    camera.position.y = -(window.scrollY * 0.01);
    
    // Slight mouse parallax
    particleMesh.position.x = (mouseX / window.innerWidth - 0.5) * 2;
    particleMesh.position.y = -(mouseY / window.innerHeight - 0.5) * 2;

    renderer.render(scene, camera);
    requestAnimationFrame(animate);
  }
  animate();

  window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });
})();
