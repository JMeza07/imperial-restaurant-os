import React, { useState } from 'react';
import { 
  X, 
  Minus, 
  Plus, 
  Check, 
  Sparkles, 
  AlertTriangle, 
  SlidersHorizontal,
  Info
} from 'lucide-react';
import { getIngredientIconInfo } from '../utils/ingredientIcons';

export default function IngredientCustomizerModal({ 
  isOpen, 
  onClose, 
  dish, 
  mode = 'REMOVE', // 'REMOVE' (solo quitar) | 'ADD' (solo agregar)
  initialRemoved = new Set(), 
  initialAdded = new Set(),
  onApply 
}) {
  if (!isOpen || !dish) return null;

  const isRemoveMode = mode === 'REMOVE';
  const allRecipeItems = dish.recipe || [];

  // Filtrar estrictamente según la modalidad sin mezclar
  // Si es modo REMOVE: solo mostramos ingredientes que pertenecen al plato y son removibles
  // Si es modo ADD: solo mostramos ingredientes que son configurables como adicionales
  const displayItems = isRemoveMode
    ? allRecipeItems.filter((item) => item.is_removable)
    : allRecipeItems.filter((item) => item.is_addable);

  const [removed, setRemoved] = useState(new Set(initialRemoved));
  const [added, setAdded] = useState(new Set(initialAdded));

  const toggleRemove = (ingId) => {
    setRemoved((prev) => {
      const next = new Set(prev);
      if (next.has(ingId)) {
        next.delete(ingId);
      } else {
        next.add(ingId);
      }
      return next;
    });
  };

  const toggleAdd = (ingId) => {
    setAdded((prev) => {
      const next = new Set(prev);
      if (next.has(ingId)) {
        next.delete(ingId);
      } else {
        next.add(ingId);
      }
      return next;
    });
  };

  // Calcular impacto de recargo por extras
  let extraTotal = 0;
  allRecipeItems.forEach((item) => {
    if (added.has(item.ingredient_id)) {
      extraTotal += parseFloat(item.extra_price || item.ingredient?.price_extra || 0);
    }
  });

  const handleSave = () => {
    onApply({
      removed: new Set(removed),
      added: new Set(added),
      extraTotal,
    });
    onClose();
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.75)',
      backdropFilter: 'blur(8px)',
      zIndex: 1300,
      display: 'flex',
      alignItems: 'flex-end', // Bottom-sheet para experiencia móvil táctil
      justifyContent: 'center',
    }}>
      <div style={{
        background: '#161c28',
        borderTopLeftRadius: '28px',
        borderTopRightRadius: '28px',
        width: '100%',
        maxWidth: '480px',
        maxHeight: '85vh',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 -10px 40px rgba(0, 0, 0, 0.7)',
        border: isRemoveMode 
          ? '1px solid rgba(244, 63, 94, 0.3)' 
          : '1px solid rgba(245, 158, 11, 0.3)',
        overflow: 'hidden',
        animation: 'slideUp 0.25s cubic-bezier(0.16, 1, 0.3, 1)',
      }}>
        {/* Cabecera del Modal con Diferenciación Visual Total */}
        <div style={{
          padding: '18px 20px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: isRemoveMode 
            ? 'linear-gradient(90deg, rgba(244, 63, 94, 0.12) 0%, rgba(22, 28, 40, 0.95) 100%)' 
            : 'linear-gradient(90deg, rgba(245, 158, 11, 0.12) 0%, rgba(22, 28, 40, 0.95) 100%)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              background: isRemoveMode ? 'rgba(244, 63, 94, 0.18)' : 'rgba(245, 158, 11, 0.18)',
              color: isRemoveMode ? '#fb7185' : '#fbbf24',
              borderRadius: '12px',
              padding: '8px',
              display: 'flex',
            }}>
              {isRemoveMode ? <Minus size={20} /> : <Plus size={20} />}
            </div>
            <div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: '800', color: '#f8fafc', margin: 0 }}>
                {isRemoveMode ? 'Quitar Ingredientes' : 'Agregar Porciones Extras'}
              </h3>
              <p style={{ fontSize: '0.78rem', color: '#94a3b8', margin: 0, marginTop: '2px' }}>
                {isRemoveMode 
                  ? 'Selecciona los ingredientes que NO deseas en tu plato' 
                  : 'Añade extras para potenciar tu porción con recargo'}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            style={{
              background: 'rgba(255, 255, 255, 0.08)',
              border: 'none',
              borderRadius: '50%',
              width: '34px',
              height: '34px',
              color: '#94a3b8',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
            }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Lista de Ingredientes Filtrada Estrictamente por la Modalidad */}
        <div style={{
          padding: '18px 20px',
          overflowY: 'auto',
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
        }}>
          {displayItems.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '30px 10px', color: '#94a3b8', fontSize: '0.9rem' }}>
              {isRemoveMode 
                ? 'Este plato no tiene ingredientes configurados como removibles.' 
                : 'Este plato no tiene ingredientes adicionales configurados.'}
            </div>
          ) : (
            displayItems.map((item) => {
              const ing = item.ingredient;
              const extraPrice = parseFloat(item.extra_price || ing?.price_extra || 0);

              const iconInfo = getIngredientIconInfo(ing?.name);

              if (isRemoveMode) {
                // MODALIDAD 1: SOLO QUITAR INGREDIENTES
                const isRemoved = removed.has(item.ingredient_id);

                return (
                  <div
                    key={item.ingredient_id}
                    onClick={() => toggleRemove(item.ingredient_id)}
                    style={{
                      background: isRemoved ? 'rgba(244, 63, 94, 0.12)' : 'rgba(255, 255, 255, 0.03)',
                      border: isRemoved ? '1.5px solid rgba(244, 63, 94, 0.45)' : '1px solid rgba(255, 255, 255, 0.08)',
                      borderRadius: '16px',
                      padding: '14px 16px',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                      gap: '12px',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1 }}>
                      {/* Icono temático del ingrediente */}
                      <div style={{
                        width: '42px',
                        height: '42px',
                        borderRadius: '12px',
                        background: isRemoved ? 'rgba(244, 63, 94, 0.2)' : iconInfo.bg,
                        color: isRemoved ? '#f43f5e' : iconInfo.color,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '1.25rem',
                        flexShrink: 0,
                        border: `1px solid ${isRemoved ? 'rgba(244, 63, 94, 0.3)' : 'rgba(255, 255, 255, 0.06)'}`,
                      }}>
                        {iconInfo.emoji}
                      </div>

                      <div>
                        <div style={{
                          fontWeight: '700',
                          fontSize: '0.95rem',
                          color: isRemoved ? '#fda4af' : '#f8fafc',
                          textDecoration: isRemoved ? 'line-through' : 'none',
                        }}>
                          {ing?.name || 'Ingrediente'}
                          <span style={{ fontSize: '0.78rem', color: '#94a3b8', marginLeft: '6px', fontWeight: 'normal' }}>
                            ({item.quantity} {item.unit})
                          </span>
                        </div>
                        <div style={{ fontSize: '0.74rem', color: isRemoved ? '#f43f5e' : '#94a3b8', marginTop: '2px', fontWeight: '600' }}>
                          {isRemoved ? '⚠️ Se omitirá en la preparación' : 'Incluido por defecto en la receta'}
                        </div>
                      </div>
                    </div>

                    <div style={{
                      padding: '8px 14px',
                      borderRadius: '10px',
                      fontSize: '0.82rem',
                      fontWeight: '800',
                      background: isRemoved ? '#f43f5e' : 'rgba(255, 255, 255, 0.08)',
                      color: isRemoved ? '#fff' : '#cbd5e1',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                      flexShrink: 0,
                    }}>
                      {isRemoved ? '✕ Quitado' : 'Mantener'}
                    </div>
                  </div>
                );
              } else {
                // MODALIDAD 2: SOLO AGREGAR EXTRAS
                const isAdded = added.has(item.ingredient_id);

                return (
                  <div
                    key={item.ingredient_id}
                    onClick={() => toggleAdd(item.ingredient_id)}
                    style={{
                      background: isAdded ? 'rgba(245, 158, 11, 0.12)' : 'rgba(255, 255, 255, 0.03)',
                      border: isAdded ? '1.5px solid rgba(245, 158, 11, 0.45)' : '1px solid rgba(255, 255, 255, 0.08)',
                      borderRadius: '16px',
                      padding: '14px 16px',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                      gap: '12px',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1 }}>
                      {/* Icono temático del ingrediente */}
                      <div style={{
                        width: '42px',
                        height: '42px',
                        borderRadius: '12px',
                        background: isAdded ? 'rgba(245, 158, 11, 0.25)' : iconInfo.bg,
                        color: isAdded ? '#fbbf24' : iconInfo.color,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '1.25rem',
                        flexShrink: 0,
                        border: `1px solid ${isAdded ? 'rgba(245, 158, 11, 0.4)' : 'rgba(255, 255, 255, 0.06)'}`,
                      }}>
                        {iconInfo.emoji}
                      </div>

                      <div>
                        <div style={{
                          fontWeight: '700',
                          fontSize: '0.95rem',
                          color: isAdded ? '#fef08a' : '#f8fafc',
                        }}>
                          {ing?.name || 'Ingrediente'}
                          <span style={{ fontSize: '0.78rem', color: '#fbbf24', marginLeft: '6px', fontWeight: '800' }}>
                            +${extraPrice.toLocaleString('es-CO')}
                          </span>
                        </div>
                        <div style={{ fontSize: '0.74rem', color: isAdded ? '#f59e0b' : '#94a3b8', marginTop: '2px', fontWeight: '600' }}>
                          {isAdded ? '✨ Porción extra seleccionada' : 'Toca para agregar porción extra'}
                        </div>
                      </div>
                    </div>

                    <div style={{
                      padding: '8px 14px',
                      borderRadius: '10px',
                      fontSize: '0.82rem',
                      fontWeight: '800',
                      background: isAdded ? 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)' : 'rgba(245, 158, 11, 0.12)',
                      color: isAdded ? '#000' : '#fbbf24',
                      border: isAdded ? 'none' : '1px solid rgba(245, 158, 11, 0.3)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                      flexShrink: 0,
                    }}>
                      {isAdded ? '✓ Extra Añadido' : '+ Añadir Extra'}
                    </div>
                  </div>
                );
              }
            })
          )}
        </div>

        {/* Footer del Modal */}
        <div style={{
          padding: '16px 20px',
          borderTop: '1px solid rgba(255, 255, 255, 0.08)',
          background: 'rgba(18, 24, 38, 0.98)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '12px',
        }}>
          <div>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
              {isRemoveMode ? 'Ingredientes a omitir:' : 'Recargo total extras:'}
            </div>
            <div style={{
              fontSize: '1.05rem',
              fontWeight: '800',
              color: isRemoveMode ? (removed.size > 0 ? '#f43f5e' : '#cbd5e1') : (extraTotal > 0 ? '#f59e0b' : '#cbd5e1'),
            }}>
              {isRemoveMode ? `${removed.size} ingrediente(s)` : `+$${extraTotal.toLocaleString('es-CO')}`}
            </div>
          </div>

          <button
            onClick={handleSave}
            style={{
              flex: 1,
              padding: '13px 20px',
              borderRadius: '14px',
              background: isRemoveMode 
                ? 'linear-gradient(135deg, #f43f5e 0%, #e11d48 100%)' 
                : 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
              color: isRemoveMode ? '#fff' : '#000',
              fontWeight: '800',
              fontSize: '0.92rem',
              border: 'none',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
              boxShadow: isRemoveMode 
                ? '0 6px 16px rgba(244, 63, 94, 0.3)' 
                : '0 6px 16px rgba(245, 158, 11, 0.3)',
            }}
          >
            <Check size={18} />
            {isRemoveMode ? 'Confirmar Exclusiones' : 'Confirmar Extras'}
          </button>
        </div>
      </div>
    </div>
  );
}
