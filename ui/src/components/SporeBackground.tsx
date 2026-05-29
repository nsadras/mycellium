import { useEffect, useRef } from 'react';

interface Spore {
  x: number;
  y: number;
  vx: number;
  vy: number;
  baseVx: number;
  baseVy: number;
  radius: number;
  color: string;
  alpha: number;
  pulseSpeed: number;
  pulsePhase: number;
}

export default function SporeBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const mouseRef = useRef({ x: -1000, y: -1000 });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    // Track resize
    const handleResize = () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };
    window.addEventListener('resize', handleResize);

    // Track mouse
    const handleMouseMove = (e: MouseEvent) => {
      mouseRef.current = { x: e.clientX, y: e.clientY };
    };
    const handleMouseLeave = () => {
      mouseRef.current = { x: -1000, y: -1000 };
    };
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseleave', handleMouseLeave);

    // Initialize spores (increased density cap from 65 to 95 and divisor from 22000 to 14000)
    const sporesCount = Math.min(95, Math.floor((width * height) / 14000));
    const spores: Spore[] = [];

    for (let i = 0; i < sporesCount; i++) {
      // Random drift velocities (very slow, organic)
      const baseVx = (Math.random() - 0.5) * 0.28;
      const baseVy = (Math.random() - 0.5) * 0.28;
      
      // Alternate colors between bioluminescent green and spore lavender
      const isGreen = Math.random() < 0.72;
      const color = isGreen ? '16, 185, 129' : '192, 132, 252'; // Emerald or Soft Lavender

      spores.push({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: baseVx,
        vy: baseVy,
        baseVx,
        baseVy,
        radius: Math.random() * 1.8 + 1.2, // 1.2px to 3.0px
        color,
        alpha: Math.random() * 0.35 + 0.15, // 0.15 to 0.50 opacity
        pulseSpeed: Math.random() * 0.015 + 0.005,
        pulsePhase: Math.random() * Math.PI * 2,
      });
    }

    // Animation loop
    const animate = () => {
      ctx.clearRect(0, 0, width, height);

      const mouse = mouseRef.current;

      for (let i = 0; i < spores.length; i++) {
        const p = spores[i];

        // 1. Slow organic pulsing alpha
        p.pulsePhase += p.pulseSpeed;
        const currentAlpha = p.alpha + Math.sin(p.pulsePhase) * 0.08;
        const clampedAlpha = Math.max(0.08, Math.min(0.65, currentAlpha));

        // 2. Physics & Repulsion calculations
        const dx = p.x - mouse.x;
        const dy = p.y - mouse.y;
        const dist = Math.hypot(dx, dy);

        if (dist < 160) {
          // Calculate push force (stronger closer to mouse)
          const force = (160 - dist) / 160;
          const angle = Math.atan2(dy, dx);
          
          // Add acceleration
          p.vx += Math.cos(angle) * force * 0.65;
          p.vy += Math.sin(angle) * force * 0.65;
        }

        // Apply friction to dampen repulsion
        p.vx *= 0.94;
        p.vy *= 0.94;

        // Restore natural base drift slowly over time
        p.vx += (p.baseVx - p.vx) * 0.06;
        p.vy += (p.baseVy - p.vy) * 0.06;

        // Move particle
        p.x += p.vx;
        p.y += p.vy;

        // Screen boundary wrap-around
        if (p.x < -10) p.x = width + 10;
        else if (p.x > width + 10) p.x = -10;

        if (p.y < -10) p.y = height + 10;
        else if (p.y > height + 10) p.y = -10;

        // 3. Render Spore with soft bioluminescent glow
        ctx.shadowBlur = 7;
        ctx.shadowColor = `rgba(${p.color}, ${clampedAlpha})`;
        ctx.fillStyle = `rgba(${p.color}, ${clampedAlpha})`;
        
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fill();
      }

      ctx.shadowBlur = 0; // Reset shadow for next frame drawing operations
      animationFrameId = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseleave', handleMouseLeave);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 w-full h-full pointer-events-none z-30"
      style={{ display: 'block' }}
    />
  );
}
