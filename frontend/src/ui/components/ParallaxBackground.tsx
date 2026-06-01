import React from "react";

export function ParallaxBackground() {
  const sceneRef = React.useRef<HTMLDivElement>(null);
  const reducedMotion = React.useRef(
    typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches
  );

  React.useEffect(() => {
    const scene = sceneRef.current;
    if (!scene || reducedMotion.current) return;

    let ticking = false;

    function update() {
      if (!scene) return;
      const y = window.scrollY;
      const l1 = scene.querySelector<HTMLElement>("[data-depth='0.15']");
      const l2 = scene.querySelector<HTMLElement>("[data-depth='0.28']");
      const l3 = scene.querySelector<HTMLElement>("[data-depth='0.42']");
      const l4 = scene.querySelector<HTMLElement>("[data-depth='0.08']");
      const l5 = scene.querySelector<HTMLElement>("[data-depth='0.22']");

      if (l1) l1.style.transform = `translate3d(-50%, calc(-50% + ${y * 0.15}px), 0)`;
      if (l2) l2.style.transform = `translate3d(0, ${y * 0.28}px, 0)`;
      if (l3) l3.style.transform = `translate3d(0, ${y * 0.42}px, 0)`;
      if (l4) l4.style.transform = `translate3d(0, ${y * 0.08}px, 0)`;
      if (l5) l5.style.transform = `translate3d(0, ${y * 0.22}px, 0) rotate(${y * 0.02}deg)`;

      ticking = false;
    }

    function onScroll() {
      if (!ticking) {
        ticking = true;
        requestAnimationFrame(update);
      }
    }

    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <div ref={sceneRef} className="parallax-scene" aria-hidden>
      <div className="parallax-base" />
      <div className="parallax-grid" data-depth="0.08" />
      <div className="parallax-orb parallax-orb--1" data-depth="0.15" />
      <div className="parallax-orb parallax-orb--2" data-depth="0.28" />
      <div className="parallax-orb parallax-orb--3" data-depth="0.42" />
      <div className="parallax-beam" data-depth="0.22" />
      <div className="parallax-sparkles" />
    </div>
  );
}
