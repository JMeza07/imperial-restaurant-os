import React from 'react';
import {
  Flame,
  Leaf,
  Wheat,
  Milk,
  Egg,
  Fish,
  Apple,
  Carrot,
  Coffee,
  Drumstick,
  Cookie,
  Heart,
  Sparkles,
  ShieldAlert,
  HelpCircle,
  Cherry
} from 'lucide-react';

/**
 * Devuelve un icono React o Emoji y color temático según el nombre del ingrediente
 */
export function getIngredientIconInfo(name = '') {
  const n = (name || '').toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");

  // Carnes y Proteínas
  if (n.includes('carne') || n.includes('res') || n.includes('angus') || n.includes('rib') || n.includes('steak')) {
    return { icon: Drumstick, emoji: '🥩', bg: 'rgba(239, 68, 68, 0.15)', color: '#f87171' };
  }
  if (n.includes('pollo') || n.includes('pechuga') || n.includes('alitas')) {
    return { icon: Drumstick, emoji: '🍗', bg: 'rgba(245, 158, 11, 0.15)', color: '#fbbf24' };
  }
  if (n.includes('tocino') || n.includes('bacon') || n.includes('panceta') || n.includes('cerdo') || n.includes('jamon')) {
    return { icon: Flame, emoji: '🥓', bg: 'rgba(244, 63, 94, 0.15)', color: '#fb7185' };
  }
  if (n.includes('camaron') || n.includes('langostino') || n.includes('marisco') || n.includes('pescado') || n.includes('salmon') || n.includes('atun')) {
    return { icon: Fish, emoji: '🦐', bg: 'rgba(56, 189, 248, 0.15)', color: '#38bdf8' };
  }
  if (n.includes('huevo') || n.includes('frito') || n.includes('yema')) {
    return { icon: Egg, emoji: '🍳', bg: 'rgba(251, 191, 36, 0.15)', color: '#fde047' };
  }

  // Quesos y Lácteos
  if (n.includes('queso') || n.includes('cheddar') || n.includes('mozzarella') || n.includes('parmesano') || n.includes('gouda') || n.includes('brie')) {
    return { icon: Milk, emoji: '🧀', bg: 'rgba(250, 204, 21, 0.15)', color: '#facc15' };
  }
  if (n.includes('crema') || n.includes('leche') || n.includes('yogurt') || n.includes('mantequilla')) {
    return { icon: Milk, emoji: '🥛', bg: 'rgba(226, 232, 240, 0.15)', color: '#e2e8f0' };
  }

  // Vegetales y Verduras
  if (n.includes('tomate') || n.includes('cherry')) {
    return { icon: Cherry, emoji: '🍅', bg: 'rgba(239, 68, 68, 0.15)', color: '#f87171' };
  }
  if (n.includes('lechuga') || n.includes('espinaca') || n.includes('rucula') || n.includes('albahaca') || n.includes('hierba') || n.includes('verde')) {
    return { icon: Leaf, emoji: '🥬', bg: 'rgba(34, 197, 94, 0.15)', color: '#4ade80' };
  }
  if (n.includes('cebolla') || n.includes('morada') || n.includes('caramelizada')) {
    return { icon: Carrot, emoji: '🧅', bg: 'rgba(192, 132, 252, 0.15)', color: '#c084fc' };
  }
  if (n.includes('aguacate') || n.includes('palta') || n.includes('guacamole')) {
    return { icon: Leaf, emoji: '🥑', bg: 'rgba(74, 222, 128, 0.15)', color: '#86efac' };
  }
  if (n.includes('champiñon') || n.includes('hongo') || n.includes('seta') || n.includes('portobello')) {
    return { icon: Leaf, emoji: '🍄', bg: 'rgba(217, 119, 6, 0.15)', color: '#d97706' };
  }
  if (n.includes('pepinillo') || n.includes('pepino')) {
    return { icon: Leaf, emoji: '🥒', bg: 'rgba(16, 185, 129, 0.15)', color: '#34d399' };
  }
  if (n.includes('pimiento') || n.includes('morron') || n.includes('chile') || n.includes('jalapeno') || n.includes('picante')) {
    return { icon: Flame, emoji: '🌶️', bg: 'rgba(239, 68, 68, 0.2)', color: '#ef4444' };
  }
  if (n.includes('maiz') || n.includes('choclo') || n.includes('elote')) {
    return { icon: Wheat, emoji: '🌽', bg: 'rgba(250, 204, 21, 0.15)', color: '#facc15' };
  }
  if (n.includes('zanahoria')) {
    return { icon: Carrot, emoji: '🥕', bg: 'rgba(249, 115, 22, 0.15)', color: '#fb923c' };
  }
  if (n.includes('papa') || n.includes('frita') || n.includes('patata')) {
    return { icon: Sparkles, emoji: '🍟', bg: 'rgba(245, 158, 11, 0.15)', color: '#fbbf24' };
  }

  // Panes y Granos
  if (n.includes('pan') || n.includes('brioche') || n.includes('artesanal') || n.includes('masa') || n.includes('harina')) {
    return { icon: Wheat, emoji: '🍞', bg: 'rgba(217, 119, 6, 0.15)', color: '#fbbf24' };
  }
  if (n.includes('arroz') || n.includes('fideo') || n.includes('pasta')) {
    return { icon: Wheat, emoji: '🍚', bg: 'rgba(241, 245, 249, 0.15)', color: '#f1f5f9' };
  }

  // Salsas y Aderezos
  if (n.includes('mayonesa') || n.includes('alioli') || n.includes('tartara') || n.includes('ranch')) {
    return { icon: Sparkles, emoji: '🥣', bg: 'rgba(254, 240, 138, 0.15)', color: '#fef08a' };
  }
  if (n.includes('mostaza') || n.includes('dijon') || n.includes('miel')) {
    return { icon: Sparkles, emoji: '🍯', bg: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b' };
  }
  if (n.includes('barbacoa') || n.includes('bbq') || n.includes('ahumada') || n.includes('ketchup')) {
    return { icon: Flame, emoji: '🥫', bg: 'rgba(239, 68, 68, 0.15)', color: '#f87171' };
  }
  if (n.includes('aceite') || n.includes('oliva') || n.includes('vinagre')) {
    return { icon: Leaf, emoji: '🫒', bg: 'rgba(101, 163, 13, 0.15)', color: '#a3e635' };
  }

  // Frutas y Dulces
  if (n.includes('limon') || n.includes('lima')) {
    return { icon: Apple, emoji: '🍋', bg: 'rgba(234, 179, 8, 0.15)', color: '#facc15' };
  }
  if (n.includes('naranja') || n.includes('mandarina')) {
    return { icon: Apple, emoji: '🍊', bg: 'rgba(249, 115, 22, 0.15)', color: '#fb923c' };
  }
  if (n.includes('fresa') || n.includes('frutilla') || n.includes('berry')) {
    return { icon: Apple, emoji: '🍓', bg: 'rgba(244, 63, 94, 0.15)', color: '#fb7185' };
  }
  if (n.includes('chocolate') || n.includes('cacao')) {
    return { icon: Cookie, emoji: '🍫', bg: 'rgba(120, 53, 15, 0.15)', color: '#b45309' };
  }
  if (n.includes('cafe') || n.includes('espresso')) {
    return { icon: Coffee, emoji: '☕', bg: 'rgba(120, 53, 15, 0.15)', color: '#b45309' };
  }

  // Default
  return { icon: Sparkles, emoji: '🌿', bg: 'rgba(148, 163, 184, 0.12)', color: '#94a3b8' };
}
