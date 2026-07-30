import React, { useEffect, useRef } from 'react';
import gsap from 'gsap';

export default function AwwwardsHero() {
  const containerRef = useRef<HTMLElement>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const subRef = useRef<HTMLParagraphElement>(null);

  useEffect(() => {
    if (titleRef.current && subRef.current) {
      gsap.fromTo(
        [titleRef.current, subRef.current],
        { y: 50, opacity: 0 },
        { y: 0, opacity: 1, duration: 1.5, ease: 'power4.out', stagger: 0.2 }
      );
    }
  }, []);

  return (
    <section
      ref={containerRef}
      id="hero"
      style={{
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        position: 'relative',
        zIndex: 10
      }}
    >
      <h1
        ref={titleRef}
        style={{
          fontSize: 'clamp(3rem, 8vw, 6rem)',
          fontWeight: 900,
          textAlign: 'center',
          color: '#fff',
          lineHeight: 1.1,
          letterSpacing: '-0.02em',
          margin: 0
        }}
      >
        BABYLON 60
      </h1>
      <p
        ref={subRef}
        style={{
          marginTop: '1.5rem',
          fontSize: 'clamp(1rem, 2vw, 1.5rem)',
          color: 'rgba(255,255,255,0.7)',
          textAlign: 'center',
          maxWidth: '600px',
          fontWeight: 300
        }}
      >
        The Sovereign C5-REAL Substrate. Annihilating generative entropy with cryptographic truth.
      </p>
    </section>
  );
}
