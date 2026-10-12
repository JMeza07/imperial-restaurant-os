import React, { useState } from 'react';
import { 
  X, 
  Plus, 
  Trash2, 
  Save, 
  AlertCircle, 
  Check, 
  Utensils, 
  Sliders, 
  HelpCircle,
  DollarSign
} from 'lucide-react';
import { api } from '../services/api';
import { getIngredientIconInfo } from '../utils/ingredientIcons';

export default function RecipeEditorModal({ 
  dish, 
  allIngredients = [], 
  token, 
  onClose, 
  onSuccess 
}) {
  if (!dish) return null;

  // Inicializar lista de ingredientes de la receta
  // Cada elemento: { ingredient_id, quantity, unit, is_removable, is_addable, extra_price, sort_order }
  const [recipeItems, setRecipeItems] = useState(() => {
    if (dish.recipe && dish.recipe.length > 0) {
      return dish.recipe.map((r, idx) => ({
        ingredient_id: r.ingredient_id,
        quantity: r.quantity || 10,
        unit: r.unit || 'g',
        is_removable: !!r.is_removable,
        is_addable: !!r.is_addable,
        extra_price: r.extra_price !== null && r.extra_price !== undefined ? r.extra_price : (r.ingredient?.price_extra || 0),
        sort_order: idx + 1,
      }));
    }
    return [];
  });

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  // Agregar un ingrediente a la receta
  const handleAddIngredient = () => {
    // Buscar el primer ingrediente no agregado
    const unused = allIngredients.find((ing) => !recipeItems.some((r) => r.ingredient_id === ing.id));
    const target = unused || allIngredients[0];

    if (!target) {
      setError('No hay más ingredientes disponibles en el catálogo.');
      return;
    }

    setRecipeItems([
      ...recipeItems,
      {
        ingredient_id: target.id,
        quantity: 50,
        unit: target.unit || 'g',
        is_removable: true, // Por defecto se puede quitar si es básico
        is_addable: false,
        extra_price: parseFloat(target.price_extra || 0),
        sort_order: recipeItems.length + 1,
      },
    ]);
  };

  // Eliminar un ingrediente de la receta
  const handleRemoveItem = (index) => {
    setRecipeItems(recipeItems.filter((_, i) => i !== index));
  };

  // Modificar atributos de un ingrediente
  const handleItemChange = (index, field, value) => {
    const next = [...recipeItems];
    next[index] = {
      ...next[index],
      [field]: value,
    };
    setRecipeItems(next);
  };

  // Guardar receta en el backend
  const handleSaveRecipe = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError(null);

    try {
      // Validar que no haya duplicados
      const ids = recipeItems.map((r) => r.ingredient_id);
      const uniqueIds = new Set(ids);
      if (uniqueIds.size !== ids.length) {
        throw new Error('La receta no puede contener ingredientes repetidos.');
      }

      const payloadItems = recipeItems.map((r, idx) => ({
        ingredient_id: r.ingredient_id,
        quantity: parseFloat(r.quantity) || 0,
        unit: r.unit || 'g',
        is_removable: Boolean(r.is_removable),
        is_addable: Boolean(r.is_addable),
        extra_price: r.is_addable ? (parseFloat(r.extra_price) || 0) : 0,
        sort_order: idx + 1,
      }));

      await api.updateDishRecipe(dish.id, payloadItems, token);
      onSuccess(`Receta de '${dish.name}' actualizada exitosamente.`);
      onClose();
    } catch (err) {
      console.error(err);
      setError(err.message || 'Error al guardar la receta');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.85)',
      backdropFilter: 'blur(8px)',
      zIndex: 1400,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '16px',
    }}>
      <div className="glass-panel" style={{
        maxWidth: '840px',
        width: '100%',
        maxHeight: '86vh',
        height: '86vh',
        display: 'flex',
        flexDirection: 'column',
        borderRadius: '24px',
        border: '1px solid rgba(245, 158, 11, 0.3)',
        background: '#0d131f',
        overflow: 'hidden',
        boxShadow: '0 25px 60px rgba(0, 0, 0, 0.8)',
      }}>
        {/* Header */}
        <div style={{
          padding: '16px 24px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: 'rgba(245, 158, 11, 0.08)',
          flexShrink: 0,
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="badge badge-gold">Control Total de Receta</span>
              <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>ID: {dish.id.slice(0, 8)}</span>
            </div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: '800', color: '#f8fafc', marginTop: '4px' }}>
              Configurar Receta: {dish.name}
            </h2>
          </div>

          <button
            onClick={onClose}
            style={{
              background: 'rgba(255, 255, 255, 0.08)',
              border: 'none',
              borderRadius: '50%',
              width: '36px',
              height: '36px',
              color: '#94a3b8',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Guía Explicativa de Negocio */}
        <div style={{
          padding: '10px 24px',
          background: 'rgba(255, 255, 255, 0.02)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
          fontSize: '0.82rem',
          color: '#cbd5e1',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '8px',
          flexShrink: 0,
        }}>
          <div>
            📌 <strong>Reglas de Receta:</strong> Define qué ingredientes son <strong>Básicos Removibles</strong> y cuáles son <strong>Adicionales</strong>.
          </div>
          <button
            type="button"
            onClick={handleAddIngredient}
            className="btn-primary"
            style={{ padding: '8px 14px', fontSize: '0.82rem' }}
          >
            <Plus size={15} />
            Añadir Ingrediente a Receta
          </button>
        </div>

        {error && (
          <div style={{
            margin: '12px 24px 0',
            padding: '10px 14px',
            borderRadius: '10px',
            background: 'rgba(244, 63, 94, 0.15)',
            border: '1px solid rgba(244, 63, 94, 0.3)',
            color: '#fb7185',
            fontSize: '0.85rem',
            flexShrink: 0,
          }}>
            {error}
          </div>
        )}

        {/* Lista de Ingredientes de la Receta (con scroll interno fluido dentro del límite de altura) */}
        <div className="custom-scroll" style={{ padding: '20px 24px', overflowY: 'auto', flex: 1, minHeight: 0 }}>
          {recipeItems.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px 10px', color: '#64748b' }}>
              Este plato aún no tiene ingredientes asociados. Haz clic en "Añadir Ingrediente a Receta".
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {recipeItems.map((item, idx) => {
                const selectedIng = allIngredients.find((i) => i.id === item.ingredient_id);

                return (
                  <div
                    key={idx}
                    style={{
                      background: 'rgba(255, 255, 255, 0.03)',
                      border: '1px solid rgba(255, 255, 255, 0.08)',
                      borderRadius: '16px',
                      padding: '16px',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '12px',
                    }}
                  >
                    {/* Fila 1: Selector de Ingrediente y Cantidad / Unidad */}
                    <div style={{
                      display: 'grid',
                      gridTemplateColumns: '2fr 1fr 1fr auto',
                      gap: '12px',
                      alignItems: 'center',
                    }}>
                      <div>
                        <label style={{ display: 'block', fontSize: '0.74rem', color: '#94a3b8', marginBottom: '4px' }}>
                          Ingrediente
                        </label>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span style={{ fontSize: '1.25rem', lineHeight: 1 }}>
                            {getIngredientIconInfo(selectedIng?.name).emoji}
                          </span>
                          <select
                            value={item.ingredient_id}
                            onChange={(e) => handleItemChange(idx, 'ingredient_id', e.target.value)}
                            style={{
                              width: '100%',
                              padding: '8px 12px',
                              borderRadius: '8px',
                              background: '#121824',
                              border: '1px solid rgba(255, 255, 255, 0.12)',
                              color: '#fff',
                              fontSize: '0.88rem',
                            }}
                          >
                            {allIngredients.map((ing) => (
                              <option key={ing.id} value={ing.id}>
                                {ing.name} ({ing.unit})
                              </option>
                            ))}
                          </select>
                        </div>
                      </div>

                      <div>
                        <label style={{ display: 'block', fontSize: '0.74rem', color: '#94a3b8', marginBottom: '4px' }}>
                          Cantidad
                        </label>
                        <input
                          type="number"
                          step="0.5"
                          min="0"
                          value={item.quantity}
                          onChange={(e) => handleItemChange(idx, 'quantity', e.target.value)}
                          style={{
                            width: '100%',
                            padding: '8px 12px',
                            borderRadius: '8px',
                            background: '#121824',
                            border: '1px solid rgba(255, 255, 255, 0.12)',
                            color: '#fff',
                            fontSize: '0.88rem',
                          }}
                        />
                      </div>

                      <div>
                        <label style={{ display: 'block', fontSize: '0.74rem', color: '#94a3b8', marginBottom: '4px' }}>
                          Unidad
                        </label>
                        <input
                          type="text"
                          value={item.unit}
                          onChange={(e) => handleItemChange(idx, 'unit', e.target.value)}
                          placeholder="g, ml, unidad"
                          style={{
                            width: '100%',
                            padding: '8px 12px',
                            borderRadius: '8px',
                            background: '#121824',
                            border: '1px solid rgba(255, 255, 255, 0.12)',
                            color: '#fff',
                            fontSize: '0.88rem',
                          }}
                        />
                      </div>

                      <div style={{ paddingTop: '18px' }}>
                        <button
                          type="button"
                          onClick={() => handleRemoveItem(idx)}
                          style={{
                            background: 'rgba(244, 63, 94, 0.15)',
                            border: '1px solid rgba(244, 63, 94, 0.3)',
                            borderRadius: '8px',
                            width: '36px',
                            height: '36px',
                            color: '#fb7185',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            cursor: 'pointer',
                          }}
                          title="Eliminar de la receta"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>

                    {/* Fila 2: Configuraciones de Negocio (Removible vs Adicional con Precio Extra) */}
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      background: 'rgba(0, 0, 0, 0.25)',
                      padding: '10px 14px',
                      borderRadius: '10px',
                      flexWrap: 'wrap',
                      gap: '12px',
                    }}>
                      <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
                        {/* Checkbox 1: Básico Removible */}
                        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.84rem', color: '#f8fafc', cursor: 'pointer' }}>
                          <input
                            type="checkbox"
                            checked={item.is_removable}
                            onChange={(e) => handleItemChange(idx, 'is_removable', e.target.checked)}
                          />
                          <span>Ingrediente Básico Removible (El cliente puede omitirlo)</span>
                        </label>

                        {/* Checkbox 2: Adicional Extra */}
                        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.84rem', color: '#fbbf24', cursor: 'pointer' }}>
                          <input
                            type="checkbox"
                            checked={item.is_addable}
                            onChange={(e) => handleItemChange(idx, 'is_addable', e.target.checked)}
                          />
                          <span>Ingrediente Adicional (El cliente puede pedir extra)</span>
                        </label>
                      </div>

                      {/* Input de Precio Extra si está marcado como adicionable */}
                      {item.is_addable && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Precio Extra (COP):</span>
                          <input
                            type="number"
                            step="500"
                            min="0"
                            value={item.extra_price}
                            onChange={(e) => handleItemChange(idx, 'extra_price', e.target.value)}
                            style={{
                              width: '110px',
                              padding: '6px 10px',
                              borderRadius: '6px',
                              background: '#121824',
                              border: '1px solid rgba(245, 158, 11, 0.4)',
                              color: '#fbbf24',
                              fontWeight: '700',
                              fontSize: '0.85rem',
                            }}
                          />
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer con Guardar */}
        <div style={{
          padding: '14px 24px',
          borderTop: '1px solid rgba(255, 255, 255, 0.08)',
          background: 'rgba(10, 14, 23, 0.98)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '14px',
          flexShrink: 0,
        }}>
          <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
            Total ingredientes configurados: <strong style={{ color: '#fff' }}>{recipeItems.length}</strong>
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              type="button"
              onClick={onClose}
              style={{
                padding: '10px 18px',
                borderRadius: '10px',
                background: 'rgba(255, 255, 255, 0.08)',
                color: '#fff',
                fontSize: '0.88rem',
                border: 'none',
                cursor: 'pointer',
              }}
            >
              Cancelar
            </button>

            <button
              type="button"
              disabled={saving}
              onClick={handleSaveRecipe}
              className="btn-primary"
              style={{ padding: '10px 22px', fontSize: '0.92rem' }}
            >
              <Save size={16} />
              {saving ? 'Guardando Receta...' : 'Guardar y Publicar Receta'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
