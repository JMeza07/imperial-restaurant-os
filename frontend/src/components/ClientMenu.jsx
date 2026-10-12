import React, { useState, useEffect } from 'react';
import { 
  ShoppingBag, 
  Sparkles, 
  Heart, 
  Send, 
  Loader2,
  Search,
  Star,
  Home,
  FileText,
  ChevronRight,
  ChevronLeft
} from 'lucide-react';
import confetti from 'canvas-confetti';
import { api } from '../services/api';
import MobileDishDetail from './MobileDishDetail';
import OrderTrackingModal from './OrderTrackingModal';

export default function ClientMenu({ 
  initialTableQr, 
  initialCustomerName = '', 
  onOpenStaffLogin,
  onBackToWelcome,
  onTableLiberated 
}) {
  const [tableQr, setTableQr] = useState(initialTableQr || 'aed6f350-c441-40aa-8fd1-2b6c191a549f');
  const [tableData, setTableData] = useState(null);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);

  // Vistas: 'HOME' (Mockup 1) | 'CATEGORY' (Mockup 3) | 'DETAIL' (Mockup 2)
  const [currentView, setCurrentView] = useState('HOME');
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [selectedDish, setSelectedDish] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTrackingOrderId, setActiveTrackingOrderId] = useState(null);
  const [favoriteDishIds, setFavoriteDishIds] = useState(new Set());

  const toggleFavorite = (e, dishId) => {
    e.stopPropagation();
    setFavoriteDishIds((prev) => {
      const next = new Set(prev);
      if (next.has(dishId)) next.delete(dishId);
      else next.add(dishId);
      return next;
    });
  };

  // PERSISTENCIA DE CONFIGURACIONES DE CADA PLATO
  const [dishCustomizations, setDishCustomizations] = useState(() => {
    try {
      const saved = localStorage.getItem('imperial_dish_customizations');
      return saved ? JSON.parse(saved) : {};
    } catch {
      return {};
    }
  });

  const handleUpdateCustomization = (dishId, config) => {
    setDishCustomizations((prev) => {
      const updated = {
        ...prev,
        [dishId]: config,
      };
      try {
        localStorage.setItem('imperial_dish_customizations', JSON.stringify(updated));
      } catch (err) {
        console.error('Error guardando en localStorage:', err);
      }
      return updated;
    });
  };

  // Carrito de compras
  const [cart, setCart] = useState([]);
  const [isCartOpen, setIsCartOpen] = useState(false);
  const [customerName, setCustomerName] = useState(initialCustomerName || '');
  const [customerPhone, setCustomerPhone] = useState('');
  const [submittingOrder, setSubmittingOrder] = useState(false);
  const [confirmedOrder, setConfirmedOrder] = useState(null);

  const [isDesktop, setIsDesktop] = useState(() => typeof window !== 'undefined' && window.innerWidth >= 900);

  useEffect(() => {
    const handleResize = () => {
      setIsDesktop(window.innerWidth >= 900);
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const loadData = async (qr, isInitial = false) => {
    if (isInitial) {
      setLoading(true);
    }
    try {
      const [tData, cData] = await Promise.all([
        api.getTableByQR(qr).catch(() => null),
        api.getCarta().catch(() => []),
      ]);
      setTableData(tData);
      setCategories(cData);

      // 1. Si la mesa tiene una orden activa en la base de datos (ABIERTA o CERRADA sin pagar), restaurar sus pedidos
      if (tData?.open_order) {
        setConfirmedOrder(tData.open_order);
        if (tData.open_order.customer_name && !customerName) {
          setCustomerName(tData.open_order.customer_name);
        }
      } else if (tData?.status === 'LIBRE') {
        // Si la mesa está libre y no hay orden confirmada en servidor, limpiar sólo el modal de tracking
        setActiveTrackingOrderId(null);
      }

      if (cData.length > 0) {
        setSelectedCategory((prev) => {
          if (!prev) return cData[0];
          const matched = cData.find((c) => c.id === prev.id);
          return matched || prev;
        });
      }
    } catch (err) {
      console.error('Error cargando carta o mesa:', err);
    } finally {
      if (isInitial) {
        setLoading(false);
      }
    }
  };

  // Sincronizar tableQr si initialTableQr cambia
  useEffect(() => {
    if (initialTableQr && initialTableQr !== tableQr) {
      setTableQr(initialTableQr);
    }
  }, [initialTableQr]);

  useEffect(() => {
    loadData(tableQr, true);
    // Polling en segundo plano sin interrumpir la interfaz ni recrear el loader
    const interval = setInterval(() => {
      loadData(tableQr, false);
    }, 4000);
    return () => clearInterval(interval);
  }, [tableQr]);

  useEffect(() => {
    if (initialCustomerName) {
      setCustomerName(initialCustomerName);
    }
  }, [initialCustomerName]);

  const handleAddToCart = (configuredItem) => {
    setCart((prev) => [...prev, configuredItem]);
    setSelectedDish(null);
    setCurrentView('HOME');
    setIsCartOpen(true);
  };

  const removeFromCart = (index) => {
    setCart((prev) => prev.filter((_, i) => i !== index));
  };

  const cartTotal = cart.reduce((acc, item) => acc + item.totalPrice, 0);

  const handleSendOrder = async () => {
    if (cart.length === 0) return;
    setSubmittingOrder(true);
    try {
      const payload = {
        codigo_qr: tableQr,
        customer_name: customerName || null,
        customer_phone: customerPhone || null,
        notes: null,
        items: cart.map((c) => ({
          dish_id: c.dish.id,
          quantity: c.quantity,
          notes: c.specialNotes || null,
          modifications: c.modifications || [],
        })),
      };

      const res = await api.createOrder(payload);
      setConfirmedOrder(res);
      setCart([]);
      setIsCartOpen(false);

      confetti({
        particleCount: 120,
        spread: 80,
        origin: { y: 0.6 },
      });
    } catch (err) {
      alert(`No se pudo enviar el pedido: ${err.message}`);
    } finally {
      setSubmittingOrder(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '60vh', gap: '16px' }}>
        <Loader2 className="pulse-live" size={40} color="#f59e0b" />
        <p style={{ color: '#94a3b8', fontSize: '1rem' }}>Cargando Carta Móvil Imperial...</p>
      </div>
    );
  }

  // Aplanar todos los platos disponibles
  const allDishes = categories.flatMap((cat) => cat.dishes || []);

  // Filtrar platos según búsqueda
  const filteredDishes = allDishes.filter((dish) => {
    if (!searchQuery.trim()) return true;
    return dish.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
           (dish.short_description && dish.short_description.toLowerCase().includes(searchQuery.toLowerCase()));
  });

  // Platos destacados / populares
  const popularDishes = allDishes.filter((d) => d.is_featured).length > 0
    ? allDishes.filter((d) => d.is_featured)
    : allDishes.slice(0, 4);

  // Plato estrella para el banner del Mockup 1
  const bannerDish = popularDishes[0] || allDishes[0];

  // Platos de la categoría seleccionada (Mockup 3)
  const categoryDishes = selectedCategory 
    ? (selectedCategory.dishes || [])
    : allDishes;

  // IMAGENES DECORATIVAS DE RESPALDO (Alta cocina, fotografía profesional de restaurante)
  const fallbackImages = [
    "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=600&q=80"
  ];

  /* =========================================================================
     PARTE 3: DETALLE CENTRAL DEL PLATO (MOCKUP 2 DEL USUARIO)
     ========================================================================= */
  if (selectedDish && currentView === 'DETAIL') {
    return (
      <MobileDishDetail
        dish={selectedDish}
        tableNumber={tableData?.number}
        initialCustomization={dishCustomizations[selectedDish.id] || null}
        onUpdateCustomization={handleUpdateCustomization}
        onBack={() => {
          setSelectedDish(null);
          setCurrentView(selectedCategory ? 'CATEGORY' : 'HOME');
        }}
        onAddToCart={handleAddToCart}
      />
    );
  }

  return (
    <div className="responsive-container" style={{
      width: '100%',
      maxWidth: isDesktop ? '1120px' : '100%',
      margin: '0 auto',
      minHeight: '100vh',
      background: '#151922', // Fondo dark elegante exacto al mock-up del usuario
      color: '#f8fafc',
      boxShadow: isDesktop ? '0 10px 60px rgba(0, 0, 0, 0.7)' : 'none',
      borderRadius: isDesktop ? '24px' : '0',
      marginTop: isDesktop ? '16px' : '0',
      marginBottom: isDesktop ? '32px' : '0',
      position: 'relative',
      paddingBottom: '86px',
      display: 'flex',
      flexDirection: 'column',
      fontFamily: "'Plus Jakarta Sans', sans-serif",
      overflowX: 'hidden',
    }}>

      {/* =========================================================================
          PARTE 1: MENU COMPLETO / HOME (MOCKUP 1 DEL USUARIO)
          ========================================================================= */}
      {currentView === 'HOME' && (
        <div className="animate-fade-in" style={{ padding: '20px 18px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          
          {/* Top Bar: Botón de búsqueda cuadrado, Saludo "Hello, User!" y Avatar */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '14px' }}>
            <div style={{
              width: '42px',
              height: '42px',
              borderRadius: '12px',
              background: '#222836',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              border: '1px solid rgba(255, 255, 255, 0.05)',
              color: '#94a3b8',
            }}>
              <Search size={20} />
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '0.85rem', fontWeight: '800', color: '#f8fafc' }}>
                  {customerName ? `¡Hola, ${customerName}!` : '¡Bienvenido!'}
                </div>
                <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
                  Mesa #{tableData?.number || '1'} {onBackToWelcome && (
                    <button 
                      onClick={onBackToWelcome}
                      style={{ background: 'none', border: 'none', color: '#f59e0b', fontSize: '0.7rem', cursor: 'pointer', marginLeft: '4px', textDecoration: 'underline' }}
                    >
                      (Cambiar)
                    </button>
                  )}
                </div>
              </div>
              <div 
                onClick={() => {
                  if (onOpenStaffLogin) onOpenStaffLogin();
                }}
                style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '50%',
                  overflow: 'hidden',
                  border: '2px solid rgba(255, 255, 255, 0.2)',
                  background: '#334155',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: onOpenStaffLogin ? 'pointer' : 'default',
                }}
                title={onOpenStaffLogin ? 'Acceso de Personal / Administración' : 'Usuario'}
              >
                <img
                  src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=150&q=80"
                  alt="Usuario"
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                />
              </div>
            </div>
          </div>

          {/* Banner Hero: Plato Destacado con 3D Floating Card (Guía UI/UX) */}
          {bannerDish && (
            <div
              onClick={() => {
                setSelectedDish(bannerDish);
                setCurrentView('DETAIL');
              }}
              className="card-3d"
              style={{
                borderRadius: '20px',
                cursor: 'pointer',
              }}
              onPointerMove={(e) => {
                const rect = e.currentTarget.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                const rotateY = ((x / rect.width) - 0.5) * 8;
                const rotateX = ((y / rect.height) - 0.5) * -8;
                const inner = e.currentTarget.querySelector('.card-3d-inner');
                if (inner) {
                  inner.style.transform = `translateY(-6px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
                }
              }}
              onPointerLeave={(e) => {
                const inner = e.currentTarget.querySelector('.card-3d-inner');
                if (inner) {
                  inner.style.transform = 'translateY(0) rotateX(0) rotateY(0)';
                }
              }}
            >
              <div
                className="card-3d-inner"
                style={{
                  background: 'linear-gradient(135deg, rgba(22, 30, 46, 0.85) 0%, rgba(10, 14, 22, 0.95) 100%)',
                  borderRadius: '20px',
                  padding: '16px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  border: '1px solid rgba(242, 178, 62, 0.25)',
                  boxShadow: '0 15px 35px rgba(0, 0, 0, 0.4)',
                  position: 'relative',
                  overflow: 'hidden',
                }}
              >
                <div 
                  className="card-3d-image"
                  style={{
                    width: '110px',
                    height: '90px',
                    borderRadius: '16px',
                    overflow: 'hidden',
                    flexShrink: 0,
                    boxShadow: '0 8px 24px rgba(0, 0, 0, 0.5)',
                    border: '1px solid rgba(255, 255, 255, 0.15)',
                    zIndex: 2,
                    marginRight: '14px',
                  }}
                >
                  <img
                    src={bannerDish.image_url || fallbackImages[0]}
                    alt={bannerDish.name}
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                  />
                </div>

                <div style={{ flex: 1, zIndex: 2 }}>
                  <div style={{
                    fontSize: '1rem',
                    fontWeight: '800',
                    color: '#ffffff',
                    lineHeight: '1.3',
                    marginBottom: '4px',
                  }}>
                    {bannerDish.name}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginBottom: '8px' }}>
                    {bannerDish.short_description || 'Lorem ipsum dolor'}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: '5px' }}>
                    <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>only</span>
                    <span style={{ fontSize: '1.25rem', fontWeight: '900', color: 'var(--gold)' }}>
                      ${parseFloat(bannerDish.price_base).toLocaleString('es-CO')}
                    </span>
                  </div>
                </div>

                {/* Halo sutil de fondo */}
                <div style={{
                  position: 'absolute',
                  top: '-20px',
                  right: '-20px',
                  width: '140px',
                  height: '140px',
                  borderRadius: '50%',
                  background: 'radial-gradient(circle, rgba(242, 178, 62, 0.2) 0%, transparent 70%)',
                  zIndex: 1,
                }} />
              </div>
            </div>
          )}

          {/* Sección "Meal Category": Pills con flecha '>' (Mockup 1) */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <div style={{ fontSize: '1rem', fontWeight: '800', color: '#f8fafc' }}>
                Meal Category
              </div>
            </div>

            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              overflowX: 'auto',
              paddingBottom: '6px',
              scrollbarWidth: 'none',
            }}>
              {categories.map((cat, idx) => {
                const isSelected = selectedCategory?.id === cat.id;
                return (
                  <button
                    key={cat.id || idx}
                    onClick={() => {
                      setSelectedCategory(cat);
                      setCurrentView('CATEGORY');
                    }}
                    style={{
                      padding: '8px 18px',
                      borderRadius: '12px',
                      fontSize: '0.82rem',
                      fontWeight: isSelected ? '800' : '600',
                      background: isSelected ? 'linear-gradient(135deg, #f43f5e 0%, #e11d48 100%)' : '#222836',
                      color: isSelected ? '#ffffff' : '#94a3b8',
                      border: isSelected ? 'none' : '1px solid rgba(255, 255, 255, 0.05)',
                      whiteSpace: 'nowrap',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                    }}
                  >
                    {cat.name}
                  </button>
                );
              })}

              <button
                onClick={() => setCurrentView('CATEGORY')}
                style={{
                  width: '34px',
                  height: '34px',
                  borderRadius: '10px',
                  background: '#222836',
                  color: '#94a3b8',
                  border: 'none',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer',
                  flexShrink: 0,
                }}
              >
                <ChevronRight size={16} />
              </button>
            </div>
          </div>

          {/* Sección "Popular Now" (Cuadrícula 2 columnas con estrellas y badge rojo de precio - Mockup 1) */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <div style={{ fontSize: '1rem', fontWeight: '800', color: '#f8fafc' }}>
                Popular Now
              </div>
            </div>

            <div className="row g-3" style={{ margin: 0 }}>
              {filteredDishes.slice(0, 4).map((dish, idx) => (
                <div key={dish.id} className="col-12 col-sm-6 col-md-3">
                  <div
                    onClick={() => {
                      setSelectedDish(dish);
                      setCurrentView('DETAIL');
                    }}
                    className="stripe-card"
                    style={{
                      borderRadius: '18px',
                      padding: '12px',
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between',
                      cursor: 'pointer',
                      background: 'rgba(15, 20, 30, 0.7)',
                      border: '1px solid rgba(255, 255, 255, 0.08)',
                    }}
                  >
                    <div>
                      <div className="dish-card-img-container">
                        <img
                          src={dish.image_url || fallbackImages[idx % fallbackImages.length]}
                          alt={dish.name}
                        />
                      </div>

                      <div className="dish-card-title">
                        {dish.name}
                      </div>

                      <div className="dish-card-desc">
                        {dish.short_description || 'Lorem ipsum'}
                      </div>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '4px' }}>
                      {/* Estrellitas */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: '2px' }}>
                        {[1, 2, 3, 4, 5].map((st) => (
                          <Star key={st} size={11} color="#f59e0b" fill="#f59e0b" />
                        ))}
                      </div>

                      {/* Badge circular/ovalado con precio en rosa/rojo idéntico al mockup 1 */}
                      <div style={{
                        background: '#f43f5e',
                        color: '#ffffff',
                        fontWeight: '900',
                        fontSize: '0.75rem',
                        padding: '3px 8px',
                        borderRadius: '8px',
                      }}>
                        ${parseFloat(dish.price_base).toLocaleString('es-CO')}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Puntos de paginación y botón "See More" */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px' }}>
              <div style={{ display: 'flex', gap: '5px' }}>
                <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#f43f5e' }} />
                <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#475569' }} />
                <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#475569' }} />
                <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#475569' }} />
              </div>

              <button
                onClick={() => setCurrentView('CATEGORY')}
                style={{
                  background: '#222836',
                  color: '#f8fafc',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  padding: '6px 14px',
                  borderRadius: '10px',
                  fontSize: '0.75rem',
                  fontWeight: '700',
                  cursor: 'pointer',
                }}
              >
                See More
              </button>
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================
          PARTE 2: CATEGORIAS DE PLATOS (MOCKUP 3 DEL USUARIO)
          ========================================================================= */}
      {currentView === 'CATEGORY' && (
        <div className="animate-fade-in" style={{ padding: '0 0 20px', display: 'flex', flexDirection: 'column' }}>
          
          {/* BANNER SUPERIOR CON FOTO DEL PLATO Y HEADER OVERLAY (MOCKUP 3) */}
          <div style={{
            position: 'relative',
            height: '240px',
            overflow: 'hidden',
          }}>
            <img
              src={categoryDishes[0]?.image_url || fallbackImages[2]}
              alt={selectedCategory?.name}
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
            {/* Degradado oscuro sobre la foto */}
            <div style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: 'linear-gradient(180deg, rgba(21, 25, 34, 0.7) 0%, rgba(21, 25, 34, 0.3) 40%, rgba(21, 25, 34, 0.95) 100%)',
            }} />

            {/* Top Bar: Botón atrás cuadrado y Avatar usuario (Mockup 3) */}
            <div style={{
              position: 'absolute',
              top: '16px',
              left: '16px',
              right: '16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              zIndex: 10,
            }}>
              <button
                onClick={() => setCurrentView('HOME')}
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
                <ChevronLeft size={20} />
              </button>

              <div style={{
                width: '40px',
                height: '40px',
                borderRadius: '50%',
                overflow: 'hidden',
                border: '2px solid rgba(255, 255, 255, 0.2)',
                background: '#334155',
              }}>
                <img
                  src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=150&q=80"
                  alt="Usuario"
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                />
              </div>
            </div>

            {/* Título central sobre la foto: "Lorem Ipsum Dolor Sit Amet" */}
            <div style={{
              position: 'absolute',
              bottom: '20px',
              left: '20px',
              right: '20px',
              textAlign: 'center',
              zIndex: 10,
            }}>
              <div style={{
                fontSize: '1.25rem',
                fontWeight: '900',
                color: '#ffffff',
                lineHeight: '1.2',
              }}>
                {selectedCategory?.name || 'Categoría Gastronómica'}
              </div>
              <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '4px' }}>
                {selectedCategory?.description || 'Tradición y frescura en cada plato'}
              </div>
            </div>
          </div>

          {/* Selector de categorías tipo pills */}
          <div style={{
            display: 'flex',
            gap: '8px',
            overflowX: 'auto',
            padding: '12px 18px 6px',
            scrollbarWidth: 'none',
          }}>
            {categories.map((c) => (
              <button
                key={c.id}
                onClick={() => setSelectedCategory(c)}
                style={{
                  padding: '6px 14px',
                  borderRadius: '10px',
                  fontSize: '0.76rem',
                  fontWeight: selectedCategory?.id === c.id ? '800' : '600',
                  background: selectedCategory?.id === c.id ? 'linear-gradient(135deg, #f43f5e 0%, #e11d48 100%)' : '#222836',
                  color: '#fff',
                  border: 'none',
                  whiteSpace: 'nowrap',
                  cursor: 'pointer',
                }}
              >
                {c.name}
              </button>
            ))}
          </div>

          {/* Cuadrícula adaptable: 1 columna en móvil (col-12) y multicolumna en pantallas medianas/grandes */}
          <div className="row g-3" style={{ padding: '12px 18px', margin: 0 }}>
            {categoryDishes.map((dish, idx) => (
              <div key={dish.id} className="col-12 col-sm-6 col-md-4 col-lg-3">
                <div
                  onClick={() => {
                    setSelectedDish(dish);
                    setCurrentView('DETAIL');
                  }}
                  className="stripe-card"
                  style={{
                    borderRadius: '18px',
                    padding: '12px',
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    cursor: 'pointer',
                    background: 'rgba(15, 20, 30, 0.7)',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                  }}
                >
                  <div>
                    <div className="dish-card-img-container">
                      <img
                        src={dish.image_url || fallbackImages[(idx + 2) % fallbackImages.length]}
                        alt={dish.name}
                      />
                    <div 
                      onClick={(e) => toggleFavorite(e, dish.id)}
                      style={{
                        position: 'absolute',
                        top: '8px',
                        right: '8px',
                        background: 'rgba(0, 0, 0, 0.6)',
                        borderRadius: '50%',
                        width: '26px',
                        height: '26px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: favoriteDishIds.has(dish.id) ? '#f43f5e' : '#cbd5e1',
                      }}
                    >
                      <Heart size={14} fill={favoriteDishIds.has(dish.id) ? '#f43f5e' : 'none'} />
                    </div>
                  </div>

                  <div className="dish-card-title">
                    {dish.name}
                  </div>

                  <div className="dish-card-desc">
                    {dish.short_description || 'Lorem ipsum dolor sit amet'}
                  </div>
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '4px' }}>
                    {/* Estrellitas */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '2px' }}>
                      {[1, 2, 3, 4, 5].map((st) => (
                        <Star key={st} size={10} color="#f59e0b" fill="#f59e0b" />
                      ))}
                    </div>

                    {/* Botón rojo/rosa 'Order' idéntico al mockup 3 */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedDish(dish);
                        setCurrentView('DETAIL');
                      }}
                      style={{
                        padding: '4px 10px',
                        borderRadius: '8px',
                        background: 'linear-gradient(135deg, #f43f5e 0%, #e11d48 100%)',
                        color: '#fff',
                        fontWeight: '800',
                        fontSize: '0.72rem',
                        border: 'none',
                        cursor: 'pointer',
                      }}
                    >
                      Order
                    </button>
                  </div>
                  <div style={{ fontSize: '0.84rem', fontWeight: '800', color: '#fbbf24', marginTop: '4px' }}>
                    ${parseFloat(dish.price_base).toLocaleString('es-CO')}
                  </div>
                </div>
              </div>
            </div>
          ))}
          </div>
        </div>
      )}

      {/* Floating Cart Button (si hay platos en el carrito) */}
      {cart.length > 0 && currentView !== 'DETAIL' && (
        <div style={{
          position: 'fixed',
          bottom: '76px',
          left: 0,
          right: 0,
          maxWidth: isDesktop ? '1080px' : '440px',
          margin: '0 auto',
          padding: '0 16px',
          zIndex: 400,
        }}>
          <button
            onClick={() => setIsCartOpen(true)}
            style={{
              width: '100%',
              padding: '14px 20px',
              borderRadius: '16px',
              background: 'linear-gradient(135deg, #f59e0b 0%, #ea580c 100%)',
              color: '#000',
              fontWeight: '900',
              fontSize: '0.95rem',
              border: 'none',
              boxShadow: '0 8px 25px rgba(234, 88, 12, 0.45)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              cursor: 'pointer',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ShoppingBag size={20} />
              <span>Ver Pedido ({cart.reduce((a, b) => a + b.quantity, 0)} platos)</span>
            </div>
            <span>${cartTotal.toLocaleString('es-CO')}</span>
          </button>
        </div>
      )}

      {/* BARRA DE NAVEGACIÓN INFERIOR (Dock exacto al mockup del usuario con Home, Cart, Notes, Star) */}
      <div style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        width: '100%',
        maxWidth: isDesktop ? '1120px' : '100%',
        margin: '0 auto',
        height: '66px',
        background: 'rgba(15, 20, 30, 0.75)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        borderTop: '1px solid rgba(255, 255, 255, 0.1)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-around',
        padding: '0 16px',
        zIndex: 500,
        boxShadow: '0 -10px 30px rgba(0, 0, 0, 0.5)',
      }}>
        {/* Tab 1: Home */}
        <button
          onClick={() => {
            setSelectedDish(null);
            setCurrentView('HOME');
          }}
          style={{
            background: 'none',
            border: 'none',
            color: currentView === 'HOME' ? '#fbbf24' : '#64748b',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
          }}
        >
          <Home size={22} />
        </button>

        {/* Tab 2: Carrito */}
        <button
          onClick={() => setIsCartOpen(true)}
          style={{
            background: 'none',
            border: 'none',
            color: cart.length > 0 ? '#f43f5e' : '#64748b',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            position: 'relative',
            cursor: 'pointer',
          }}
        >
          <ShoppingBag size={22} />
          {cart.length > 0 && (
            <span style={{
              position: 'absolute',
              top: '-4px',
              right: '-6px',
              background: '#f43f5e',
              color: '#fff',
              fontSize: '0.62rem',
              fontWeight: '800',
              borderRadius: '50%',
              width: '16px',
              height: '16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              {cart.reduce((a, b) => a + b.quantity, 0)}
            </span>
          )}
        </button>

        {/* Tab 3: Comanda / Notas */}
        <button
          onClick={() => {
            if (confirmedOrder?.id) {
              setActiveTrackingOrderId(confirmedOrder.id);
            }
          }}
          style={{
            background: 'none',
            border: 'none',
            color: '#64748b',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
          }}
        >
          <FileText size={22} />
        </button>

        {/* Tab 4: Favoritos (Star) */}
        <button
          onClick={() => setCurrentView('CATEGORY')}
          style={{
            background: 'none',
            border: 'none',
            color: currentView === 'CATEGORY' ? '#fbbf24' : '#64748b',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
          }}
        >
          <Star size={22} />
        </button>
      </div>

      {/* MODAL / DRAWER DE RESUMEN Y ENVÍO DE PEDIDO A COCINA */}
      {isCartOpen && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.85)',
          backdropFilter: 'blur(8px)',
          zIndex: 1500,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'flex-end',
        }}>
          <div 
            className="glass-card-strong"
            style={{
              color: '#fff',
              width: '100%',
              maxWidth: '440px',
              maxHeight: '85vh',
              borderTopLeftRadius: '28px',
              borderTopRightRadius: '28px',
              padding: '24px',
              display: 'flex',
              flexDirection: 'column',
              boxShadow: '0 -15px 45px rgba(0, 0, 0, 0.85)',
              border: '1px solid rgba(255, 255, 255, 0.12)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
              <div>
                <h3 style={{ fontSize: '1.25rem', fontWeight: '800', color: '#f8fafc' }}>
                  Pedido &bull; Mesa #{tableData?.number || '1'}
                </h3>
                <p style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                  Confirmación directa con el sistema KDS de Cocina
                </p>
              </div>
              <button
                onClick={() => setIsCartOpen(false)}
                style={{
                  background: 'rgba(255, 255, 255, 0.1)',
                  color: '#fff',
                  border: 'none',
                  padding: '6px 12px',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '0.85rem',
                }}
              >
                Cerrar
              </button>
            </div>

            <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '18px' }}>
              {cart.map((item, idx) => (
                <div key={idx} style={{
                  background: '#222836',
                  padding: '12px 14px',
                  borderRadius: '14px',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <div style={{ fontWeight: '700', fontSize: '0.95rem' }}>
                      {item.quantity}x {item.dish.name}
                    </div>
                    <div style={{ color: '#fbbf24', fontWeight: '800' }}>
                      ${item.totalPrice.toLocaleString('es-CO')}
                    </div>
                  </div>

                  {item.removedIngredientNames?.length > 0 && (
                    <div style={{ fontSize: '0.78rem', color: '#f43f5e', marginTop: '4px' }}>
                      ✕ Sin: {item.removedIngredientNames.join(', ')}
                    </div>
                  )}

                  {item.addedExtraNames?.length > 0 && (
                    <div style={{ fontSize: '0.78rem', color: '#fbbf24', marginTop: '2px' }}>
                      ✓ Extras: {item.addedExtraNames.join(', ')}
                    </div>
                  )}

                  <button
                    onClick={() => removeFromCart(idx)}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: '#f43f5e',
                      fontSize: '0.78rem',
                      cursor: 'pointer',
                      marginTop: '6px',
                      padding: 0,
                    }}
                  >
                    Eliminar
                  </button>
                </div>
              ))}
            </div>

            <div style={{ borderTop: '1px solid rgba(255, 255, 255, 0.1)', paddingTop: '16px' }}>
              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: '700', color: '#94a3b8', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  Nombre del Cliente (Para Facturación):
                </label>
                <input
                  type="text"
                  value={customerName}
                  onChange={(e) => setCustomerName(e.target.value)}
                  placeholder="Tu nombre (ej: Carlos Mendoza)"
                  style={{
                    width: '100%',
                    padding: '10px 14px',
                    borderRadius: '10px',
                    background: 'rgba(255, 255, 255, 0.06)',
                    border: '1px solid rgba(255, 255, 255, 0.15)',
                    color: '#fff',
                    fontSize: '0.88rem',
                    outline: 'none',
                    boxSizing: 'border-box',
                  }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '14px' }}>
                <span style={{ color: '#94a3b8' }}>Total de la Orden:</span>
                <span style={{ fontSize: '1.3rem', fontWeight: '800', color: '#fbbf24' }}>
                  ${cartTotal.toLocaleString('es-CO')}
                </span>
              </div>

              <button
                disabled={submittingOrder}
                onClick={handleSendOrder}
                style={{
                  width: '100%',
                  padding: '14px',
                  borderRadius: '14px',
                  background: 'linear-gradient(135deg, #f43f5e 0%, #e11d48 100%)',
                  color: '#fff',
                  fontWeight: '800',
                  fontSize: '1rem',
                  border: 'none',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                }}
              >
                {submittingOrder ? <Loader2 className="pulse-live" size={20} /> : <Send size={18} />}
                {submittingOrder ? 'Enviando a Cocina...' : 'Confirmar Pedido Ahora'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Seguimiento */}
      {activeTrackingOrderId && (
        <OrderTrackingModal
          orderId={activeTrackingOrderId}
          qrCode={tableQr}
          onClose={() => setActiveTrackingOrderId(null)}
          onOrderCompleted={() => {
            setActiveTrackingOrderId(null);
            setConfirmedOrder(null);
            setCart([]);
            try {
              localStorage.removeItem('imperial_dish_customizations');
              localStorage.removeItem('imperial_active_order');
            } catch (e) {
              // ignore
            }
            setDishCustomizations({});
            if (onTableLiberated) {
              onTableLiberated();
            } else {
              loadData(tableQr);
            }
          }}
        />
      )}
    </div>
  );
}
