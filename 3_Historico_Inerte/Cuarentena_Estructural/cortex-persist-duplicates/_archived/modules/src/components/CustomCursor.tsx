import React, { useEffect, useState, useRef } from 'react';
import { motion, useSpring, useMotionValue } from 'framer-motion';

export default function CustomCursor() {
  const cursorX = useMotionValue(-100);
  const cursorY = useMotionValue(-100);
  const cursorSize = useMotionValue(20);

  // Smooth springs for the cursor
  const springConfig = { damping: 25, stiffness: 300, mass: 0.5 };
  const smoothX = useSpring(cursorX, springConfig);
  const smoothY = useSpring(cursorY, springConfig);

  const [isHovered, setIsHovered] = useState(false);
  const [magneticPos, setMagneticPos] = useState<{ x: number, y: number, w: number, h: number } | null>(null);

  useEffect(() => {
    // Hide default cursor globally
    document.body.style.cursor = 'none';

    // Create style tag to hide cursor on hoverable elements as well
    const style = document.createElement('style');
    style.innerHTML = `
      * { cursor: none !important; }
    `;
    document.head.appendChild(style);

    const handleMouseMove = (e: MouseEvent) => {
      if (!magneticPos) {
        cursorX.set(e.clientX - cursorSize.get() / 2);
        cursorY.set(e.clientY - cursorSize.get() / 2);
      } else {
        // Magnetic physics: pull cursor towards center of hovered element based on mouse proximity
        const { x, y, w, h } = magneticPos;
        const centerX = x + w / 2;
        const centerY = y + h / 2;

        // Calculate distance from center to mouse
        const distX = e.clientX - centerX;
        const distY = e.clientY - centerY;

        // Attract cursor (0.3 factor of pull)
        cursorX.set(centerX - cursorSize.get() / 2 + distX * 0.3);
        cursorY.set(centerY - cursorSize.get() / 2 + distY * 0.3);
      }
    };

    const handleMouseOver = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      const hoverable = target.closest('a, button, [data-cursor="magnetic"]');

      if (hoverable) {
        setIsHovered(true);
        cursorSize.set(60);

        const rect = hoverable.getBoundingClientRect();
        setMagneticPos({
          x: rect.left,
          y: rect.top,
          w: rect.width,
          h: rect.height
        });
      }
    };

    const handleMouseOut = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      const hoverable = target.closest('a, button, [data-cursor="magnetic"]');

      if (hoverable) {
        // Only trigger out if we actually left the element entirely
        if (!e.relatedTarget || !hoverable.contains(e.relatedTarget as Node)) {
          setIsHovered(false);
          cursorSize.set(20);
          setMagneticPos(null);
        }
      }
    };

    window.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseover', handleMouseOver);
    document.addEventListener('mouseout', handleMouseOut);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseover', handleMouseOver);
      document.removeEventListener('mouseout', handleMouseOut);
      document.body.style.cursor = 'auto';
      document.head.removeChild(style);
    };
  }, [magneticPos, cursorX, cursorY, cursorSize]);

  return (
    <motion.div
      style={{
        position: 'fixed',
        left: 0,
        top: 0,
        x: smoothX,
        y: smoothY,
        width: cursorSize,
        height: cursorSize,
        borderRadius: '50%',
        backgroundColor: isHovered ? 'rgba(245, 158, 11, 0.1)' : 'rgba(43, 59, 229, 0.4)',
        border: isHovered ? '1px solid rgba(245, 158, 11, 0.8)' : '1px solid rgba(43, 59, 229, 0.8)',
        backdropFilter: isHovered ? 'blur(4px)' : 'none',
        pointerEvents: 'none',
        zIndex: 9999,
        mixBlendMode: 'difference',
      }}
      animate={{
        scale: isHovered ? 1.2 : 1,
      }}
      transition={{ type: 'spring', stiffness: 400, damping: 25 }}
    >
      {isHovered && (
        <motion.div
          initial={{ opacity: 0, scale: 0 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0 }}
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            width: 4,
            height: 4,
            borderRadius: '50%',
            backgroundColor: '#F59E0B',
          }}
        />
      )}
    </motion.div>
  );
}
