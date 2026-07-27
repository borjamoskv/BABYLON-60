import{V as o,R as a,C as n,T as l,P as c,a as u,M as h}from"./vendor-7OteaNBb.js";class m{constructor(){this.container=document.querySelector(".hero-immersive__image-wrapper"),this.img=document.querySelector(".hero-immersive__image"),!(!this.container||!this.img)&&(this.renderer=null,this.gl=null,this.camera=null,this.scene=null,this.mouse=new o(0,0),this.lastMouse=new o(0,0),this.mouseVelocity=new o(0,0),this.targetVelo=0,this.currentVelo=0,this.img.complete?this.init():this.img.onload=()=>this.init())}init(){this.createRenderer(),this.createCamera(),this.createScene(),this.addEventListeners(),this.onResize(),this.update(0),this.img.style.opacity="0"}createRenderer(){this.renderer=new a({alpha:!0,dpr:Math.min(window.devicePixelRatio,2),antialias:!0}),this.gl=this.renderer.gl,this.gl=this.renderer.gl,this.renderer.canvas&&(this.renderer.canvas.classList.add("liquid-canvas"),Object.assign(this.renderer.canvas.style,{position:"absolute",inset:"0",width:"100%",height:"100%",zIndex:"1",pointerEvents:"none"})),this.container.appendChild(this.renderer.canvas)}createCamera(){this.camera=new n(this.gl),this.camera.position.z=5}createScene(){const e=new l(this.gl,{image:this.img,generateMipmaps:!1}),t=new c(this.gl,{widthSegments:48,heightSegments:48}),i=`
            attribute vec3 position;
            attribute vec2 uv;
            uniform mat4 modelViewMatrix;
            uniform mat4 projectionMatrix;
            uniform float uTime;
            uniform float uVelo;
            uniform vec2 uMouse;
            varying vec2 vUv;

            void main() {
                vUv = uv;
                vec3 pos = position;
                
                // Subtle organic wave based on time and global velocity
                float wave = sin(pos.x * 2.0 + uTime * 2.0) * cos(pos.y * 2.0 + uTime * 1.5) * 0.04 * uVelo;
                pos.z += wave;
                
                gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
            }
        `,s=`
            precision highp float;
            uniform sampler2D tMap;
            uniform vec2 uMouse;
            uniform float uVelo;
            uniform float uTime;
            uniform vec2 uResolution;
            uniform vec2 uImageResolution;
            varying vec2 vUv;

            vec2 getUV(vec2 uv, vec2 res, vec2 imgRes) {
                float screenAspect = res.x / res.y;
                float imageAspect = imgRes.x / imgRes.y;
                vec2 ratio = vec2(
                    min(screenAspect / imageAspect, 1.0),
                    min(imageAspect / screenAspect, 1.0)
                );
                return uv * ratio + (1.0 - ratio) * 0.5;
            }

            void main() {
                vec2 uv = vUv;
                vec2 correctedUv = getUV(uv, uResolution, uImageResolution);
                
                vec2 mouseDirection = correctedUv - uMouse;
                float dist = length(mouseDirection);
                
                float radius = 0.45;
                float strength = smoothstep(radius, 0.0, dist);
                
                vec2 distortion = mouseDirection * strength * uVelo * 1.5;
                
                // Final UV with clamping to avoid black edge artifacts
                vec2 targetUv = correctedUv + distortion;
                
                // Slight offset for chromatic aberration
                float r = texture2D(tMap, clamp(targetUv + distortion * 0.05, 0.0, 1.0)).r;
                float g = texture2D(tMap, clamp(targetUv, 0.0, 1.0)).g;
                float b = texture2D(tMap, clamp(targetUv - distortion * 0.05, 0.0, 1.0)).b;
                
                vec3 color = vec3(r, g, b);
                
                // [NEXUS CONFIG] Industrial Noir Tint (#0a1f3a)
                vec3 tintColor = vec3(0.039, 0.122, 0.227); // #0a1f3a converted to 0-1
                color = mix(color, tintColor, 0.1 * strength); // Adaptive tint
                
                float noise = fract(sin(dot(correctedUv, vec2(12.9898, 78.233))) * 43758.5453) * 0.015;
                
                // Progressive Vignette Bloom (UX Enhancement)
                float vignette = smoothstep(radius * 1.2, radius, dist);
                color *= mix(1.0, 1.15, vignette * uVelo); // Bloom on movement
                
                // Subtle edge mask
                float edgeMask = smoothstep(0.0, 0.05, uv.x) * smoothstep(1.0, 0.95, uv.x) *
                                smoothstep(0.0, 0.05, uv.y) * smoothstep(1.0, 0.95, uv.y);
                
                gl_FragColor = vec4((color + noise) * edgeMask, edgeMask);
            }
        `;this.program=new u(this.gl,{vertex:i,fragment:s,uniforms:{tMap:{value:e},uMouse:{value:this.mouse},uVelo:{value:0},uTime:{value:0},uResolution:{value:new o},uImageResolution:{value:new o(this.img.naturalWidth,this.img.naturalHeight)}},transparent:!0}),this.mesh=new h(this.gl,{geometry:t,program:this.program}),this.renderer.canvas.style.willChange="opacity, transform"}addEventListeners(){window.addEventListener("resize",this.onResize.bind(this)),window.addEventListener("mousemove",this.onMouseMove.bind(this))}onMouseMove(e){const t=e.clientX/window.innerWidth,i=1-e.clientY/window.innerHeight,s=Math.abs(t-this.lastMouse.x),r=Math.abs(i-this.lastMouse.y);this.targetVelo=Math.min((s+r)*2,.8),this.mouse.set(t,i),this.lastMouse.set(t,i)}onResize(){const{width:e,height:t}=this.container.getBoundingClientRect();this.renderer.setSize(e,t),this.program&&this.program.uniforms.uResolution.value.set(e,t);const i=45*(Math.PI/180),s=2*Math.tan(i/2)*this.camera.position.z,r=s*(e/t);this.mesh.scale.set(r,s,1)}update(e){requestAnimationFrame(this.update.bind(this)),this.program&&(this.program.uniforms.uTime.value=e*.001,this.currentVelo+=(this.targetVelo-this.currentVelo)*.06,this.program.uniforms.uVelo.value=this.currentVelo,this.program.uniforms.uMouse.value.lerp(this.mouse,.12),this.targetVelo*=.96),this.renderer.render({scene:this.mesh,camera:this.camera})}}new m;export{m as LiquidDistortion};
