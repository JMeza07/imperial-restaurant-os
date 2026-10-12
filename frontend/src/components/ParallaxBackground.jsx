import React, { useState, useEffect } from 'react';
import { useThemeCustomizer } from '../utils/ThemeCustomizerContext';

export default function ParallaxBackground() {
  const { themeSettings } = useThemeCustomizer();
  const {
    parallaxEnabled,
    parallaxImages = [],
    slideDuration = 6,
    animationDuration = 1.5,
    animationType = 'fade-zoom',
    imageOpacity = 0.25,
    overlayColor = '#070a0f',
    overlayOpacity = 0.85,
    blurAmount = 2
  } = themeSettings;

  const [currentIndex, setCurrentIndex] = useState(0);

  // Rotación automática de imágenes según el slideDuration
  useEffect(() => {
    if (!parallaxEnabled || !parallaxImages.length) return;

    const interval = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % parallaxImages.length);
    }, Math.max(slideDuration * 1000, 2000));

    return () => clearInterval(interval);
  }, [parallaxEnabled, parallaxImages.length, slideDuration]);

  if (!parallaxEnabled || !parallaxImages.length) {
    return null;
  }

  // Clases o estilos de animación según animationType
  const getAnimationKeyframes = () => {
    switch (animationType) {
      case 'ken-burns':
        return `
          @keyframes parallaxKenBurns {
            0% { transform: scale(1) translate(0, 0); }
            50% { transform: scale(1.08) translate(-1%, -1%); }
            100% { transform: scale(1.15) translate(1%, 0.5%); }
          }
        `;
      case 'pan-left':
        return `
          @keyframes parallaxPanLeft {
            0% { transform: scale(1.08) translateX(2%); }
            100% { transform: scale(1.08) translateX(-2%); }
          }
        `;
      case 'fade-zoom':
      default:
        return `
          @keyframes parallaxFadeZoom {
            0% { transform: scale(1.02); }
            100% { transform: scale(1.1); }
          }
        `;
    }
  };

  const getAnimationName = () => {
    switch (animationType) {
      case 'ken-burns': return 'parallaxKenBurns';
      case 'pan-left': return 'parallaxPanLeft';
      default: return 'parallaxFadeZoom';
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        width: '100vw',
        height: '100vh',
        zIndex: 0,
        pointerEvents: 'none',
        overflow: 'hidden',
      }}
    >
      <style>{getAnimationKeyframes()}</style>

      {/* Capas de imágenes parallax superpuestas */}
      {parallaxImages.map((imgUrl, idx) => {
        const isActive = idx === currentIndex;
        return (
          <div
            key={imgUrl + idx}
            style={{
              position: 'absolute',
              inset: '-5%', // Ligero margen para que el zoom no muestre bordes vacíos
              backgroundImage: `url(${imgUrl})`,
              backgroundSize: 'cover',
              backgroundPosition: 'center',
              opacity: isActive ? imageOpacity : 0,
              filter: `blur(${blurAmount}px)`,
              transition: `opacity ${animationDuration}s ease-in-out`,
              animation: isActive ? `${getAnimationName()} ${slideDuration + animationDuration}s ease-out infinite alternate` : 'none',
              transformOrigin: 'center center',
            }}
          />
        );
      })}

      {/* Capa superior oscura ajustable para controlar contraste y legibilidad */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundColor: overlayColor,
          opacity: overlayOpacity,
          backdropFilter: 'blur(1px)',
        }}
      />
    </div>
  );
}
