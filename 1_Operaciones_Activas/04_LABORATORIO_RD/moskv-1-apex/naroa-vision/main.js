import * as THREE from 'three';
import gsap from 'gsap';

// ==========================================
// 1. CUSTOM CURSOR
// ==========================================
const cursor = document.querySelector('.cursor');
const follower = document.querySelector('.cursor-follower');

let mouseX = 0, mouseY = 0;
let followerX = 0, followerY = 0;

window.addEventListener('mousemove', (e) => {
    mouseX = e.clientX;
    mouseY = e.clientY;
    
    // Direct position for the tiny dot
    gsap.set(cursor, { x: mouseX, y: mouseY });
});

// Lerp the follower for smooth physical inertia
gsap.ticker.add(() => {
    followerX += (mouseX - followerX) * 0.1;
    followerY += (mouseY - followerY) * 0.1;
    gsap.set(follower, { x: followerX, y: followerY });
});

// ==========================================
// 2. WEBGL SETUP
// ==========================================
const container = document.getElementById('webgl-container');

const scene = new THREE.Scene();
const camera = new THREE.OrthographicCamera(
    window.innerWidth / -2, window.innerWidth / 2,
    window.innerHeight / 2, window.innerHeight / -2,
    1, 1000
);
camera.position.z = 1;

const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
container.appendChild(renderer.domElement);

// ==========================================
// 3. ASSETS & TEXTURES
// ==========================================
const textures = [];
const imagePaths = [
    '/real_portrait.jpg',
    '/real_art_1.jpg',
    '/real_art_2.jpg',
    '/real_art_3.jpg'
];

const textureLoader = new THREE.TextureLoader();

// Promise wrapper to load all textures
const loadTextures = () => {
    return Promise.all(imagePaths.map(path => {
        return new Promise((resolve) => {
            textureLoader.load(path, (tex) => {
                // Ensure textures cover the plane nicely
                tex.generateMipmaps = false;
                tex.minFilter = THREE.LinearFilter;
                tex.magFilter = THREE.LinearFilter;
                resolve(tex);
            });
        });
    }));
};

// ==========================================
// 4. SHADER MATERIAL
// ==========================================
const vertexShader = `
    varying vec2 vUv;
    void main() {
        vUv = uv;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
`;

const fragmentShader = `
    uniform sampler2D tex1;
    uniform sampler2D tex2;
    uniform float progress;
    varying vec2 vUv;

    void main() {
        vec2 p = vUv;
        
        // Liquid Zoom effect
        vec2 uv1 = p + (p - 0.5) * progress * 0.3;
        vec2 uv2 = p + (p - 0.5) * (1.0 - progress) * 0.3;

        // RGB shift distortion for cinematic effect
        float r1 = texture2D(tex1, uv1 + vec2(0.02 * progress, 0.0)).r;
        float g1 = texture2D(tex1, uv1).g;
        float b1 = texture2D(tex1, uv1 - vec2(0.02 * progress, 0.0)).b;
        vec4 color1 = vec4(r1, g1, b1, 1.0);

        float r2 = texture2D(tex2, uv2 + vec2(0.02 * (1.0 - progress), 0.0)).r;
        float g2 = texture2D(tex2, uv2).g;
        float b2 = texture2D(tex2, uv2 - vec2(0.02 * (1.0 - progress), 0.0)).b;
        vec4 color2 = vec4(r2, g2, b2, 1.0);

        // Mix both textures based on progress
        gl_FragColor = mix(color1, color2, progress);
    }
`;

let material, plane;

// ==========================================
// 5. INTERACTION LOGIC
// ==========================================
let currentIndex = 0;
let isAnimating = false;

loadTextures().then(loadedTextures => {
    textures.push(...loadedTextures);

    // Create a plane covering the entire screen
    const geometry = new THREE.PlaneGeometry(window.innerWidth, window.innerHeight);
    
    material = new THREE.ShaderMaterial({
        vertexShader,
        fragmentShader,
        uniforms: {
            tex1: { value: textures[0] },
            tex2: { value: textures[1] },
            progress: { value: 0.0 }
        }
    });

    plane = new THREE.Mesh(geometry, material);
    scene.add(plane);

    // Event listener for scroll to trigger transitions
    window.addEventListener('wheel', handleScroll);
    
    // Optional: touch support
    let touchStartY = 0;
    window.addEventListener('touchstart', e => touchStartY = e.touches[0].clientY);
    window.addEventListener('touchend', e => {
        let touchEndY = e.changedTouches[0].clientY;
        if (touchStartY - touchEndY > 50) nextSlide();
        else if (touchEndY - touchStartY > 50) prevSlide();
    });

    render();
});

function handleScroll(e) {
    if (isAnimating) return;
    if (e.deltaY > 0) nextSlide();
    else if (e.deltaY < 0) prevSlide();
}

function nextSlide() {
    if (isAnimating || currentIndex === textures.length - 1) return;
    isAnimating = true;
    
    let nextIndex = currentIndex + 1;
    material.uniforms.tex2.value = textures[nextIndex];
    
    gsap.to(material.uniforms.progress, {
        value: 1,
        duration: 1.5,
        ease: "power3.inOut",
        onComplete: () => {
            currentIndex = nextIndex;
            material.uniforms.tex1.value = textures[currentIndex];
            material.uniforms.progress.value = 0;
            isAnimating = false;
        }
    });
}

function prevSlide() {
    if (isAnimating || currentIndex === 0) return;
    isAnimating = true;
    
    let prevIndex = currentIndex - 1;
    // To reverse, we swap the logic or just load the prev into tex2 
    // and animate progress from 1 to 0. 
    material.uniforms.tex2.value = textures[currentIndex];
    material.uniforms.tex1.value = textures[prevIndex];
    material.uniforms.progress.value = 1;
    
    gsap.to(material.uniforms.progress, {
        value: 0,
        duration: 1.5,
        ease: "power3.inOut",
        onComplete: () => {
            currentIndex = prevIndex;
            isAnimating = false;
        }
    });
}

// ==========================================
// 6. RESIZE & RENDER LOOP
// ==========================================
window.addEventListener('resize', () => {
    camera.left = window.innerWidth / -2;
    camera.right = window.innerWidth / 2;
    camera.top = window.innerHeight / 2;
    camera.bottom = window.innerHeight / -2;
    camera.updateProjectionMatrix();

    renderer.setSize(window.innerWidth, window.innerHeight);
    if(plane) {
        plane.geometry.dispose();
        plane.geometry = new THREE.PlaneGeometry(window.innerWidth, window.innerHeight);
    }
});

function render() {
    requestAnimationFrame(render);
    renderer.render(scene, camera);
}
