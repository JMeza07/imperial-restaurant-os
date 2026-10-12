import React, { createContext, useContext, useState, useEffect } from 'react';

const ThemeCustomizerContext = createContext(null);

const DEFAULT_SETTINGS = {
  // Paleta de colores
  primaryColor: '#f2b23e',      // Dorado Imperial
  secondaryColor: '#e0472f',    // Rubí / Fresa Imperial
  accentColor: '#38bdf8',       // Azul eléctrico / cian
  
  // Logotipo de la marca
  logoUrl: '',                  // URL o Data URI (base64) del logo
  brandName: 'IMPERIAL RESTAURANT OS',

  // Fondo Parallax y Animaciones
  parallaxEnabled: true,
  parallaxImages: [
    'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1920&q=80',
    'https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=1920&q=80',
    'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=1920&q=80',
    'https://images.unsplash.com/photo-1559847844-5315695dadae?auto=format&fit=crop&w=1920&q=80'
  ],
  slideDuration: 6,             // Segundos entre imágenes
  animationDuration: 1.5,       // Segundos de duración de la transición
  animationType: 'fade-zoom',   // 'fade-zoom' | 'pan-left' | 'ken-burns' | 'fade-only'
  imageOpacity: 0.25,           // Opacidad de la imagen (0.05 a 1.0)
  overlayColor: '#070a0f',      // Color de capa superior
  overlayOpacity: 0.85,         // Transparencia de la capa superior (0.0 a 1.0)
  blurAmount: 2,                // Desenfoque sutil en px
};

export function ThemeCustomizerProvider({ children }) {
  const [themeSettings, setThemeSettings] = useState(() => {
    try {
      const saved = localStorage.getItem('imperial_theme_customization');
      if (saved) {
        return { ...DEFAULT_SETTINGS, ...JSON.parse(saved) };
      }
    } catch (e) {
      console.warn('Error leyendo imperial_theme_customization:', e);
    }
    return DEFAULT_SETTINGS;
  });

  // Aplicar variables CSS en el elemento raíz (:root) dinámicamente
  useEffect(() => {
    const root = document.documentElement;
    root.style.setProperty('--gold', themeSettings.primaryColor);
    root.style.setProperty('--gold-primary', themeSettings.primaryColor);
    root.style.setProperty('--primary-theme', themeSettings.primaryColor);
    root.style.setProperty('--secondary-theme', themeSettings.secondaryColor);
    root.style.setProperty('--red', themeSettings.secondaryColor);
    root.style.setProperty('--rose-primary', themeSettings.secondaryColor);

    // Gradiente dinámico basado en el color primario seleccionado
    root.style.setProperty(
      '--gold-gradient', 
      `linear-gradient(135deg, ${themeSettings.primaryColor} 0%, ${themeSettings.secondaryColor} 100%)`
    );

    try {
      localStorage.setItem('imperial_theme_customization', JSON.stringify(themeSettings));
    } catch (e) {
      console.warn('Error guardando temas en localStorage:', e);
    }
  }, [themeSettings]);

  const updateThemeSettings = (newSettings) => {
    setThemeSettings((prev) => ({ ...prev, ...newSettings }));
  };

  const resetThemeSettings = () => {
    setThemeSettings(DEFAULT_SETTINGS);
  };

  return (
    <ThemeCustomizerContext.Provider value={{ themeSettings, updateThemeSettings, resetThemeSettings }}>
      {children}
    </ThemeCustomizerContext.Provider>
  );
}

export function useThemeCustomizer() {
  const context = useContext(ThemeCustomizerContext);
  if (!context) {
    throw new Error('useThemeCustomizer must be used within a ThemeCustomizerProvider');
  }
  return context;
}
