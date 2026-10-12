import React, { useState } from 'react';
import { 
  Heart, 
  AlertTriangle, 
  Plus, 
  Minus, 
  Check, 
  Sparkles, 
  ShieldCheck, 
  Flame, 
  Leaf,
  Info,
  X
} from 'lucide-react';

export default function DishModal({ dish, onClose, onAddToCart }) {
  if (!dish) return null;

  const [quantity, setQuantity] = useState(1);
  const [removedIngredients, setRemovedIngredients] = useState(new Set());
  const [addedExtras, setAddedExtras] = useState(new Set());
  const [specialNotes, setSpecialNotes] = useState('');

  // Ingredientes del plato (de la receta)
  const recipeItems = dish.recipe || [];

  const toggleRemove = (ingredientId) => {
    setRemovedIngredients((prev) => {
      const next = new Set(prev);
      if (next.has(ingredientId)) {
        next.delete(ingredientId);
      } else {
        next.add(ingredientId);
      }
      return next;
    });
  };

  const toggleAdd = (ingredientId) => {
    setAddedExtras((prev) => {
      const next = new Set(prev);
      if (next.has(ingredientId)) {
        next.delete(ingredientId);
      } else {
        next.add(ingredientId);
      }
      return next;
    });
  };

  // Cálculo de precio
  const basePrice = parseFloat(dish.price_base) || 0;
  let extraPriceTotal = 0;
  recipeItems.forEach((item) => {
    if (addedExtras.has(item.ingredient_id)) {
      extraPriceTotal += parseFloat(item.extra_price || item.ingredient?.price_extra || 0);
    }
  });

  const unitPrice = basePrice + extraPriceTotal;
  const totalPrice = unitPrice * quantity;

  // Recopilar beneficios y alérgenos de todos los ingredientes
  const allBenefits = [];
  const allAllergens = [];

  recipeItems.forEach((r) => {
    const ing = r.ingredient;
    if (ing) {
      if (ing.benefit_links) {
        ing.benefit_links.forEach((b) => {
          if (b.benefit && !allBenefits.some((item) => item.id === b.benefit.id)) {
            allBenefits.push({
              ...b.benefit,
              ingredientName: ing.name,
            });
          }
        });
      }
      if (ing.allergen_links) {
        ing.allergen_links.forEach((a) => {
          if (a.allergen && !allAllergens.some((item) => item.id === a.allergen.id)) {
            allAllergens.push({
              ...a.allergen,
              ingredientName: ing.name,
            });
          }
        });
      }
    }
  });

  const handleConfirm = () => {
    const modifications = [];
    removedIngredients.forEach((id) => {
      modifications.push({
        ingredient_id: id,
        action: 'REMOVE',
        price_extra: 0,
      });
    });
    addedExtras.forEach((id) => {
      const item = recipeItems.find((r) => r.ingredient_id === id);
      modifications.push({
        ingredient_id: id,
        action: 'AGREGAR',
        price_extra: parseFloat(item?.extra_price || item?.ingredient?.price_extra || 0),
      });
    });

    onAddToCart({
      dish,
      quantity,
      unitPrice,
      totalPrice,
      modifications,
      removedIngredientNames: recipeItems
        .filter((r) => removedIngredients.has(r.ingredient_id))
        .map((r) => r.ingredient?.name),
      addedExtraNames: recipeItems
        .filter((r) => addedExtras.has(r.ingredient_id))
        .map((r) => r.ingredient?.name),
      specialNotes,
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
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      backdropFilter: 'blur(8px)',
      zIndex: 1000,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '16px',
    }}>
      <div className="glass-panel" style={{
        maxWidth: '720px',
        width: '100%',
        maxHeight: '90vh',
        overflowY: 'auto',
        borderRadius: '24px',
        border: '1px solid rgba(245, 158, 11, 0.2)',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)',
        position: 'relative',
        background: '#0d131f',
      }}>
        {/* Header & Botón Cerrar */}
        <div style={{
          position: 'sticky',
          top: 0,
          background: 'rgba(13, 19, 31, 0.95)',
          backdropFilter: 'blur(10px)',
          padding: '20px 24px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          zIndex: 10,
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span className="badge badge-gold">Receta de Autor</span>
              {dish.is_featured && <span className="badge badge-emerald">Destacado</span>}
            </div>
            <h2 style={{ fontSize: '1.6rem', color: '#f8fafc', marginTop: '6px' }}>{dish.name}</h2>
          </div>
          <button 
            onClick={onClose}
            style={{
              background: 'rgba(255, 255, 255, 0.06)',
              color: '#94a3b8',
              borderRadius: '50%',
              width: '38px',
              height: '38px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <X size={20} />
          </button>
        </div>

        <div style={{ padding: '24px' }}>
          {/* Descripción & Tiempos */}
          <p style={{ color: '#94a3b8', fontSize: '0.98rem', lineHeight: '1.6', marginBottom: '20px' }}>
            {dish.long_description || dish.short_description}
          </p>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
            gap: '12px',
            marginBottom: '24px',
          }}>
            <div style={{
              background: 'rgba(255, 255, 255, 0.03)',
              padding: '12px 16px',
              borderRadius: '12px',
              border: '1px solid rgba(255, 255, 255, 0.05)',
            }}>
              <div style={{ fontSize: '0.75rem', color: '#64748b', textTransform: 'uppercase' }}>Tiempo Cocina</div>
              <div style={{ fontSize: '1.1rem', fontWeight: '700', color: '#f8fafc', marginTop: '4px' }}>
                ⏱️ {dish.preparation_time_minutes || 15} min
              </div>
            </div>

            <div style={{
              background: 'rgba(255, 255, 255, 0.03)',
              padding: '12px 16px',
              borderRadius: '12px',
              border: '1px solid rgba(255, 255, 255, 0.05)',
            }}>
              <div style={{ fontSize: '0.75rem', color: '#64748b', textTransform: 'uppercase' }}>Calorías Estimadas</div>
              <div style={{ fontSize: '1.1rem', fontWeight: '700', color: '#f59e0b', marginTop: '4px' }}>
                <Flame size={16} style={{ display: 'inline', marginRight: '4px' }} />
                {dish.calories_estimate ? `${dish.calories_estimate} kcal` : 'Aprox. 450 kcal'}
              </div>
            </div>

            <div style={{
              background: 'rgba(255, 255, 255, 0.03)',
              padding: '12px 16px',
              borderRadius: '12px',
              border: '1px solid rgba(255, 255, 255, 0.05)',
            }}>
              <div style={{ fontSize: '0.75rem', color: '#64748b', textTransform: 'uppercase' }}>Nutrición Inteligente</div>
              <div style={{ fontSize: '1.1rem', fontWeight: '700', color: '#10b981', marginTop: '4px' }}>
                <Leaf size={16} style={{ display: 'inline', marginRight: '4px' }} />
                Ingredientes Vivos
              </div>
            </div>
          </div>

          {/* SECCIÓN CLAVE REQUERIDA: Beneficios para la Salud de los Ingredientes */}
          {allBenefits.length > 0 && (
            <div style={{
              background: 'rgba(16, 185, 129, 0.06)',
              border: '1px solid rgba(16, 185, 129, 0.25)',
              borderRadius: '16px',
              padding: '20px',
              marginBottom: '24px',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                <Heart size={20} color="#10b981" />
                <h3 style={{ fontSize: '1.1rem', color: '#34d399', fontWeight: '700' }}>
                  Impacto Positivo & Beneficios para la Salud
                </h3>
              </div>
              <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '14px' }}>
                Cada ingrediente aporta micronutrientes comprobados para el bienestar de tu cuerpo:
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {allBenefits.map((b) => (
                  <div key={b.id} style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '10px',
                    background: 'rgba(0, 0, 0, 0.25)',
                    padding: '10px 14px',
                    borderRadius: '10px',
                  }}>
                    <Sparkles size={16} color="#fbbf24" style={{ marginTop: '2px', flexShrink: 0 }} />
                    <div>
                      <span style={{ fontWeight: '700', color: '#f8fafc', fontSize: '0.92rem' }}>
                        {b.name}
                      </span>
                      <span style={{ color: '#94a3b8', fontSize: '0.85rem', marginLeft: '6px' }}>
                        (Aporte de <strong style={{ color: '#e2e8f0' }}>{b.ingredientName}</strong>)
                      </span>
                      <p style={{ color: '#cbd5e1', fontSize: '0.84rem', marginTop: '3px' }}>
                        {b.description}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Alérgenos Declarados */}
          {allAllergens.length > 0 && (
            <div style={{
              background: 'rgba(244, 63, 94, 0.06)',
              border: '1px solid rgba(244, 63, 94, 0.25)',
              borderRadius: '14px',
              padding: '16px 20px',
              marginBottom: '24px',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <AlertTriangle size={18} color="#f43f5e" />
                <h4 style={{ fontSize: '0.95rem', color: '#fb7185', fontWeight: '700' }}>
                  Alérgenos Presentes en la Receta Base
                </h4>
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '8px' }}>
                {allAllergens.map((a) => (
                  <span key={a.id} className="badge badge-rose" style={{ textTransform: 'none' }}>
                    {a.name} ({a.ingredientName})
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Personalizador de Ingredientes (Quitar / Adicionar Extras) */}
          <div style={{ marginBottom: '24px' }}>
            <h3 style={{ fontSize: '1.1rem', color: '#f8fafc', marginBottom: '12px' }}>
              Personaliza tu Plato a tu Gusto
            </h3>
            <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '14px' }}>
              Puedes retirar ingredientes no deseados o añadir extras para potenciar tu porción.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {recipeItems.map((item) => {
                const ing = item.ingredient;
                const isRemoved = removedIngredients.has(item.ingredient_id);
                const isAdded = addedExtras.has(item.ingredient_id);
                const extraPrice = parseFloat(item.extra_price || ing?.price_extra || 0);

                return (
                  <div key={item.ingredient_id} style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '12px 16px',
                    borderRadius: '12px',
                    background: isRemoved 
                      ? 'rgba(244, 63, 94, 0.08)' 
                      : isAdded 
                        ? 'rgba(245, 158, 11, 0.08)' 
                        : 'rgba(255, 255, 255, 0.03)',
                    border: isRemoved 
                      ? '1px solid rgba(244, 63, 94, 0.3)' 
                      : isAdded 
                        ? '1px solid rgba(245, 158, 11, 0.3)' 
                        : '1px solid rgba(255, 255, 255, 0.06)',
                  }}>
                    <div>
                      <div style={{ 
                        fontWeight: '600', 
                        color: isRemoved ? '#94a3b8' : '#f8fafc',
                        textDecoration: isRemoved ? 'line-through' : 'none',
                      }}>
                        {ing?.name || 'Ingrediente'}
                        <span style={{ fontSize: '0.8rem', color: '#64748b', marginLeft: '6px', fontWeight: 'normal' }}>
                          ({item.quantity} {item.unit})
                        </span>
                      </div>
                      {ing?.protein && (
                        <div style={{ fontSize: '0.75rem', color: '#10b981', marginTop: '2px' }}>
                          Prot: {ing.protein}g | Carbs: {ing.carbs || 0}g | Cal: {ing.calories || 0}
                        </div>
                      )}
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      {item.is_removable && (
                        <button
                          type="button"
                          onClick={() => toggleRemove(item.ingredient_id)}
                          style={{
                            padding: '6px 12px',
                            borderRadius: '8px',
                            fontSize: '0.8rem',
                            fontWeight: '600',
                            background: isRemoved ? '#f43f5e' : 'rgba(255, 255, 255, 0.06)',
                            color: isRemoved ? '#fff' : '#94a3b8',
                            border: '1px solid rgba(255, 255, 255, 0.1)',
                          }}
                        >
                          {isRemoved ? '✕ Quitado' : 'Quitar'}
                        </button>
                      )}

                      {item.is_addable && (
                        <button
                          type="button"
                          onClick={() => toggleAdd(item.ingredient_id)}
                          style={{
                            padding: '6px 12px',
                            borderRadius: '8px',
                            fontSize: '0.8rem',
                            fontWeight: '600',
                            background: isAdded ? '#f59e0b' : 'rgba(245, 158, 11, 0.12)',
                            color: isAdded ? '#000' : '#fbbf24',
                            border: '1px solid rgba(245, 158, 11, 0.3)',
                          }}
                        >
                          {isAdded ? `✓ Extra (+$${extraPrice.toLocaleString('es-CO')})` : `+ Extra (+$${extraPrice.toLocaleString('es-CO')})`}
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Notas para cocina */}
          <div style={{ marginBottom: '24px' }}>
            <label style={{ display: 'block', fontSize: '0.88rem', color: '#94a3b8', marginBottom: '8px' }}>
              Instrucciones especiales para cocina (Opcional):
            </label>
            <input 
              type="text"
              placeholder="Ej: Plato bien caliente, sin sal adicional, salsas aparte..."
              value={specialNotes}
              onChange={(e) => setSpecialNotes(e.target.value)}
              style={{
                width: '100%',
                padding: '12px 16px',
                borderRadius: '10px',
                background: 'rgba(255, 255, 255, 0.04)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                color: '#fff',
                fontSize: '0.9rem',
              }}
            />
          </div>

          {/* Footer de Selección y Precio */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            paddingTop: '20px',
            borderTop: '1px solid rgba(255, 255, 255, 0.1)',
            gap: '16px',
            flexWrap: 'wrap',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <button
                onClick={() => setQuantity(Math.max(1, quantity - 1))}
                style={{
                  width: '38px',
                  height: '38px',
                  borderRadius: '10px',
                  background: 'rgba(255, 255, 255, 0.08)',
                  color: '#fff',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Minus size={16} />
              </button>
              <span style={{ fontSize: '1.2rem', fontWeight: '700', minWidth: '24px', textAlign: 'center' }}>
                {quantity}
              </span>
              <button
                onClick={() => setQuantity(quantity + 1)}
                style={{
                  width: '38px',
                  height: '38px',
                  borderRadius: '10px',
                  background: 'rgba(255, 255, 255, 0.08)',
                  color: '#fff',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Plus size={16} />
              </button>
            </div>

            <button
              onClick={handleConfirm}
              className="btn-primary"
              style={{ flex: 1, minWidth: '240px', padding: '14px 20px', fontSize: '1.05rem' }}
            >
              <Check size={20} />
              Agregar {quantity} por ${totalPrice.toLocaleString('es-CO')}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
