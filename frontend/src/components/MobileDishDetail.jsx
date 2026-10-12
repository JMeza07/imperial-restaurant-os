import React, { useState, useEffect } from 'react';
import { 
  ArrowLeft, 
  Heart, 
  Star, 
  Plus, 
  Minus, 
  Share2, 
  SlidersHorizontal,
  Flame,
  Clock,
  Sparkles,
  ShoppingBag,
  Check,
  X
} from 'lucide-react';
import IngredientCustomizerModal from './IngredientCustomizerModal';

export default function MobileDishDetail({ 
  dish, 
  tableNumber, 
  initialCustomization = null,
  onUpdateCustomization,
  onBack, 
  onAddToCart 
}) {
  if (!dish) return null;

  const [quantity, setQuantity] = useState(initialCustomization?.quantity || 1);
  const [removedIngredients, setRemovedIngredients] = useState(
    initialCustomization?.removedIngredients ? new Set(initialCustomization.removedIngredients) : new Set()
  );
  const [addedExtras, setAddedExtras] = useState(
    initialCustomization?.addedExtras ? new Set(initialCustomization.addedExtras) : new Set()
  );
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [customizerMode, setCustomizerMode] = useState('REMOVE'); // 'REMOVE' o 'ADD'
  const [specialNotes, setSpecialNotes] = useState(initialCustomization?.specialNotes || '');
  const [isFavorite, setIsFavorite] = useState(false);
  const [showNutritionModal, setShowNutritionModal] = useState(false);

  const recipeItems = dish.recipe || [];

  // Calcular recargo total de extras seleccionados
  let extraPriceTotal = 0;
  recipeItems.forEach((item) => {
    if (addedExtras.has(item.ingredient_id)) {
      extraPriceTotal += parseFloat(item.extra_price || item.ingredient?.price_extra || 0);
    }
  });

  // Calcular precio
  const basePrice = parseFloat(dish.price_base) || 0;
  const unitPrice = basePrice + extraPriceTotal;
  const totalPrice = unitPrice * quantity;

  const handleApplyCustomization = ({ removed, added }) => {
    setRemovedIngredients(removed);
    setAddedExtras(added);
    if (onUpdateCustomization) {
      onUpdateCustomization(dish.id, {
        quantity,
        removedIngredients: Array.from(removed),
        addedExtras: Array.from(added),
        specialNotes,
      });
    }
  };

  const handleConfirmOrder = () => {
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
  };

  return (
    <div className="animate-fade-in responsive-container" style={{
      width: '100%',
      maxWidth: '680px',
      margin: '0 auto',
      minHeight: '100vh',
      background: '#151922', // Tema Dark idéntico al Mockup 2
      color: '#ffffff',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between',
      paddingBottom: '20px',
      fontFamily: "'Plus Jakarta Sans', sans-serif",
      position: 'relative',
    }}>
      {/* IMAGEN DE PLATO A ANCHO COMPLETO (NO CIRCULAR) CON DEGRADADO HACIA EL NOMBRE Y DESCRIPCIÓN */}
      <div style={{
        position: 'relative',
        width: '100%',
        height: '320px',
        overflow: 'hidden',
      }}>
        {/* Foto nítida del plato que abarca todo el ancho */}
        <img
          src={dish.image_url || "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=1200&q=80"}
          alt={dish.name}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            display: 'block',
          }}
        />

        {/* Degradado: Arriba nítido (transparente) y ligera opacidad oscura gradual que inicia hacia el nombre y descripción */}
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'linear-gradient(180deg, rgba(21, 25, 34, 0.35) 0%, rgba(21, 25, 34, 0) 30%, rgba(21, 25, 34, 0.45) 65%, rgba(21, 25, 34, 0.95) 92%, #151922 100%)',
          pointerEvents: 'none',
        }} />

        {/* Barra superior flotante sobre la foto con botones Back, Favorito y Compartir */}
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          padding: '16px 20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          zIndex: 10,
        }}>
          <button
            onClick={onBack}
            style={{
              width: '40px',
              height: '40px',
              borderRadius: '12px',
              background: 'rgba(21, 25, 34, 0.75)',
              backdropFilter: 'blur(8px)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              color: '#fff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
            }}
          >
            <ArrowLeft size={18} />
          </button>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button
              onClick={() => setIsFavorite(!isFavorite)}
              style={{
                width: '40px',
                height: '40px',
                borderRadius: '12px',
                background: 'rgba(21, 25, 34, 0.75)',
                backdropFilter: 'blur(8px)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                color: isFavorite ? '#f59e0b' : '#94a3b8',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
              }}
            >
              <Star size={18} fill={isFavorite ? '#f59e0b' : 'none'} />
            </button>

            <button
              style={{
                width: '40px',
                height: '40px',
                borderRadius: '12px',
                background: 'rgba(21, 25, 34, 0.75)',
                backdropFilter: 'blur(8px)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                color: '#94a3b8',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
              }}
            >
              <Share2 size={18} />
            </button>
          </div>
        </div>
      </div>

      {/* INFORMACIÓN DEL PLATO: TÍTULO, SUBTÍTULO, PRECIO Y ESTRELLAS */}
      <div style={{ padding: '4px 24px 0', flex: 1, position: 'relative', zIndex: 5 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '6px' }}>
          <div>
            <h1 style={{ fontSize: '1.5rem', fontWeight: '800', color: '#ffffff', margin: 0, lineHeight: '1.25' }}>
              {dish.name}
            </h1>
            <div style={{ fontSize: '0.85rem', color: '#94a3b8', marginTop: '4px' }}>
              {dish.short_description || 'Exquisita receta imperial elaborada al momento'}
            </div>
          </div>

          <div style={{ textAlign: 'right' }}>
            <span style={{ fontSize: '1.5rem', fontWeight: '900', color: '#ffffff' }}>
              ${unitPrice.toLocaleString('es-CO')}
            </span>
          </div>
        </div>

        {/* Calificación 5 estrellas doradas y botón de información nutricional */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', margin: '10px 0 12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            {[1, 2, 3, 4, 5].map((st) => (
              <Star key={st} size={15} color="#f59e0b" fill="#f59e0b" />
            ))}
            <span style={{ fontSize: '0.8rem', color: '#94a3b8', marginLeft: '6px' }}>
              (4.9) &bull; ⏱️ {dish.preparation_time_minutes || 15} min
            </span>
          </div>

          {/* Botón icono de información nutricional sobre la descripción */}
          <button
            type="button"
            onClick={() => setShowNutritionModal(true)}
            className="pulse-live"
            style={{
              background: '#151922',
              border: '2px solid #d97706',
              borderRadius: '50%',
              width: '42px',
              height: '42px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              boxShadow: '0 0 16px rgba(245, 158, 11, 0.45)',
              transition: 'transform 0.2s ease',
            }}
            title="Ver información nutricional del plato"
          >
            <span style={{ fontSize: '1.25rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>🥗</span>
          </button>
        </div>

        {/* Descripción en texto secundario */}
        <p style={{
          fontSize: '0.82rem',
          color: '#94a3b8',
          lineHeight: '1.6',
          marginBottom: '16px',
        }}>
          {dish.long_description || dish.short_description || 'Selección de ingredientes frescos cocinados con técnicas de alta gastronomía.'}
        </p>

        {/* BOTONES PARA AGREGAR O QUITAR INGREDIENTES */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '10px',
          marginBottom: '20px',
        }}>
          <button
            type="button"
            onClick={() => {
              setCustomizerMode('REMOVE');
              setIsModalOpen(true);
            }}
            style={{
              padding: '10px 12px',
              borderRadius: '12px',
              background: 'rgba(244, 63, 94, 0.1)',
              border: '1px solid rgba(244, 63, 94, 0.3)',
              color: '#fb7185',
              fontSize: '0.8rem',
              fontWeight: '700',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
              cursor: 'pointer',
            }}
          >
            <Minus size={14} />
            Quitar Ingredientes
            {removedIngredients.size > 0 && (
              <span style={{ background: '#f43f5e', color: '#fff', fontSize: '0.65rem', padding: '1px 5px', borderRadius: '50%' }}>
                {removedIngredients.size}
              </span>
            )}
          </button>

          <button
            type="button"
            onClick={() => {
              setCustomizerMode('ADD');
              setIsModalOpen(true);
            }}
            style={{
              padding: '10px 12px',
              borderRadius: '12px',
              background: 'rgba(245, 158, 11, 0.1)',
              border: '1px solid rgba(245, 158, 11, 0.3)',
              color: '#fbbf24',
              fontSize: '0.8rem',
              fontWeight: '700',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
              cursor: 'pointer',
            }}
          >
            <Plus size={14} />
            Agregar Extras
            {addedExtras.size > 0 && (
              <span style={{ background: '#f59e0b', color: '#000', fontSize: '0.65rem', padding: '1px 5px', borderRadius: '50%' }}>
                {addedExtras.size}
              </span>
            )}
          </button>
        </div>

        {/* Resumen de cambios */}
        {(removedIngredients.size > 0 || addedExtras.size > 0) && (
          <div style={{
            background: 'rgba(255, 255, 255, 0.03)',
            borderRadius: '12px',
            padding: '10px 14px',
            fontSize: '0.78rem',
            border: '1px solid rgba(255, 255, 255, 0.06)',
            marginBottom: '16px',
            display: 'flex',
            flexDirection: 'column',
            gap: '4px',
          }}>
            {removedIngredients.size > 0 && (
              <span style={{ color: '#fb7185' }}>
                ✕ Sin: {recipeItems.filter((r) => removedIngredients.has(r.ingredient_id)).map((r) => r.ingredient?.name).join(', ')}
              </span>
            )}
            {addedExtras.size > 0 && (
              <span style={{ color: '#fbbf24' }}>
                ✓ Extras: {recipeItems.filter((r) => addedExtras.has(r.ingredient_id)).map((r) => r.ingredient?.name).join(', ')} (+${extraPriceTotal.toLocaleString('es-CO')})
              </span>
            )}
          </div>
        )}
      </div>

      {/* FOOTER BAR: SELECTOR DE CANTIDAD (- 01 +) Y BOTÓN "Order Now" (IDÉNTICO A MOCKUP 2) */}
      <div style={{
        padding: '12px 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '16px',
        background: '#151922',
        borderTop: '1px solid rgba(255, 255, 255, 0.05)',
      }}>
        {/* Selector de cantidad rectangular '- 01 +' */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '14px',
          background: 'rgba(255, 255, 255, 0.06)',
          borderRadius: '14px',
          padding: '8px 14px',
          border: '1px solid rgba(255, 255, 255, 0.05)',
        }}>
          <button
            onClick={() => setQuantity(Math.max(1, quantity - 1))}
            style={{
              background: 'none',
              border: 'none',
              color: '#94a3b8',
              cursor: 'pointer',
              padding: '2px',
              display: 'flex',
              alignItems: 'center',
            }}
          >
            <Minus size={15} />
          </button>
          <span style={{ fontWeight: '800', fontSize: '0.95rem', color: '#fff', minWidth: '22px', textAlign: 'center' }}>
            {quantity < 10 ? `0${quantity}` : quantity}
          </span>
          <button
            onClick={() => setQuantity(quantity + 1)}
            style={{
              background: 'none',
              border: 'none',
              color: '#94a3b8',
              cursor: 'pointer',
              padding: '2px',
              display: 'flex',
              alignItems: 'center',
            }}
          >
            <Plus size={15} />
          </button>
        </div>

        {/* Botón degradado 'Order Now' */}
        <button
          onClick={handleConfirmOrder}
          style={{
            flex: 1,
            padding: '14px 20px',
            borderRadius: '16px',
            background: 'linear-gradient(135deg, #f97316 0%, #ec4899 100%)', // Degradado idéntico al botón Order Now del mockup
            color: '#fff',
            fontWeight: '800',
            fontSize: '1rem',
            border: 'none',
            cursor: 'pointer',
            boxShadow: '0 8px 24px rgba(249, 115, 22, 0.4)',
            textAlign: 'center',
          }}
        >
          Order Now
        </button>
      </div>

      {/* VENTANA MODAL PARA QUITAR O AGREGAR INGREDIENTES */}
      <IngredientCustomizerModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        dish={dish}
        mode={customizerMode}
        initialRemoved={removedIngredients}
        initialAdded={addedExtras}
        onApply={handleApplyCustomization}
      />

      {/* MODAL INFORMATIVO DE NUTRICIÓN DEL PLATO */}
      {showNutritionModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.85)',
          backdropFilter: 'blur(10px)',
          zIndex: 1200,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '20px',
        }}>
          <div className="glass-panel" style={{
            maxWidth: '460px',
            width: '100%',
            padding: '24px',
            borderRadius: '24px',
            background: '#0d131f',
            border: '1.5px solid #f59e0b',
            boxShadow: '0 25px 70px rgba(245, 158, 11, 0.25)',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '18px' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span className="badge badge-gold" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Sparkles size={13} />
                    Ficha Nutricional Oficial
                  </span>
                </div>
                <h3 style={{ fontSize: '1.25rem', color: '#f8fafc', fontWeight: '800', marginTop: '6px' }}>
                  {dish.name}
                </h3>
                <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                  Estimación basada en porción estándar y técnica culinaria Imperial
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowNutritionModal(false)}
                style={{ background: 'none', color: '#94a3b8', border: 'none', cursor: 'pointer', padding: '4px' }}
              >
                <X size={20} />
              </button>
            </div>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(2, 1fr)',
              gap: '10px',
              marginBottom: '20px',
            }}>
              <div style={{ background: 'rgba(255, 255, 255, 0.04)', padding: '10px 12px', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.08)', display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ width: '34px', height: '34px', borderRadius: '50%', background: 'rgba(249, 115, 22, 0.2)', color: '#f97316', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: '800', fontSize: '0.9rem' }}>
                  %
                </div>
                <div>
                  <div style={{ fontSize: '0.72rem', fontWeight: '800', color: '#f8fafc', textTransform: 'uppercase' }}>APORTE CALÓRICO</div>
                  <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>{dish.calories_estimate || 510} kcal</div>
                </div>
              </div>

              <div style={{ background: 'rgba(255, 255, 255, 0.04)', padding: '10px 12px', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.08)', display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ width: '34px', height: '34px', borderRadius: '50%', background: 'rgba(34, 197, 94, 0.2)', color: '#22c55e', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1rem' }}>
                  🥗
                </div>
                <div>
                  <div style={{ fontSize: '0.72rem', fontWeight: '800', color: '#f8fafc', textTransform: 'uppercase' }}>FIBRA DIGESTIVA</div>
                  <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Microbiota saludable</div>
                </div>
              </div>

              <div style={{ background: 'rgba(255, 255, 255, 0.04)', padding: '10px 12px', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.08)', display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ width: '34px', height: '34px', borderRadius: '50%', background: 'rgba(59, 130, 246, 0.2)', color: '#3b82f6', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1rem' }}>
                  🥕
                </div>
                <div>
                  <div style={{ fontSize: '0.72rem', fontWeight: '800', color: '#f8fafc', textTransform: 'uppercase' }}>VITAMINA A & C</div>
                  <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Defensas inmunes</div>
                </div>
              </div>

              <div style={{ background: 'rgba(255, 255, 255, 0.04)', padding: '10px 12px', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.08)', display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ width: '34px', height: '34px', borderRadius: '50%', background: 'rgba(236, 72, 153, 0.2)', color: '#ec4899', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1rem' }}>
                  ❤️
                </div>
                <div>
                  <div style={{ fontSize: '0.72rem', fontWeight: '800', color: '#f8fafc', textTransform: 'uppercase' }}>CARDIO SALUD</div>
                  <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Bajo sodio & grasas</div>
                </div>
              </div>
            </div>

            <button
              type="button"
              onClick={() => setShowNutritionModal(false)}
              className="btn-primary"
              style={{ width: '100%', padding: '10px', fontSize: '0.9rem', justifyContent: 'center' }}
            >
              Cerrar Ficha
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
