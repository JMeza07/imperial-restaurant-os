import React, { useState, useEffect, useMemo, useRef } from 'react';
import { 
  ChefHat, 
  Clock, 
  CheckCircle2, 
  Flame, 
  RefreshCw, 
  AlertTriangle,
  Play,
  Check,
  Utensils,
  ArrowLeft,
  BarChart3,
  LogOut,
  Bell,
  Volume2,
  VolumeX,
  Filter,
  CheckCheck,
  Search,
  Sparkles,
  Timer,
  ShoppingBag,
  Layers,
  ChevronRight,
  TrendingUp,
  Maximize2,
  Minimize2
} from 'lucide-react';
import { api } from '../services/api';

export default function KitchenKDS({ token, userRole, currentUserEmail, onLogout, onNavigate }) {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastRefreshed, setLastRefreshed] = useState(new Date());
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);
  
  // Filtros de cocina
  const [selectedStatusFilter, setSelectedStatusFilter] = useState('ALL'); // 'ALL' | 'RECIBIDO' | 'EN_PREPARACION' | 'LISTO'
  const [selectedChannelFilter, setSelectedChannelFilter] = useState('ALL'); // 'ALL' | 'MESA' | 'DOMICILIO' | 'LLEVAR'
  const [searchQuery, setSearchQuery] = useState('');
  
  // Control de alertas de retraso (en minutos)
  const DELAY_THRESHOLD_MINUTES = 15;
  const URGENT_THRESHOLD_MINUTES = 25;

  // Seguimiento de cantidad de pedidos para reproducir sonido de campana ante nuevas órdenes
  const previousItemCountRef = useRef(0);

  // Verificación de permisos de acción configurados por el Administrador
  const canPerformAction = (actionId) => {
    if (userRole === 'ADMIN' || !userRole) return true;
    try {
      const saved = localStorage.getItem('imperial_user_action_permissions');
      if (!saved) return true;
      const parsed = JSON.parse(saved);
      const userActions = currentUserEmail ? parsed[currentUserEmail] : null;
      if (!userActions) return true; // Si no está configurado, activo por defecto
      return userActions.includes(actionId);
    } catch {
      return true;
    }
  };

  // Decodificar ID de usuario actual desde el JWT para comprobar exclusividad de cocinero
  const currentUserId = useMemo(() => {
    const activeToken = token || localStorage.getItem('imperial_auth_token');
    if (!activeToken) return null;
    try {
      const base64Url = activeToken.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      const decoded = JSON.parse(jsonPayload);
      return decoded.sub || null;
    } catch {
      return null;
    }
  }, [token]);

  // Sintetizador de audio / sonido web nativo para KDS sin dependencias externas
  const playKitchenBell = () => {
    if (!soundEnabled || !canPerformAction('KDS_AUDIO_ALERTS')) return;
    try {
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(880, audioCtx.currentTime); // Nota A5
      osc.frequency.exponentialRampToValueAtTime(1760, audioCtx.currentTime + 0.15); // A6

      gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.6);

      osc.connect(gain);
      gain.connect(audioCtx.destination);

      osc.start();
      osc.stop(audioCtx.currentTime + 0.6);
    } catch (e) {
      console.warn('AudioContext alert warning:', e);
    }
  };

  const fetchKitchenOrders = async () => {
    try {
      const activeToken = token || localStorage.getItem('imperial_auth_token');
      const data = await api.getKitchenActiveOrders(activeToken);
      setOrders(data || []);
      setLastRefreshed(new Date());

      // Contar platos pendientes
      const totalPending = (data || []).reduce(
        (sum, ord) => sum + (ord.items || []).filter(i => i.status === 'RECIBIDO').length, 
        0
      );

      // Si entraron nuevos pedidos y no es la primera carga, alertar al chef
      if (previousItemCountRef.current > 0 && totalPending > previousItemCountRef.current) {
        playKitchenBell();
      }
      previousItemCountRef.current = totalPending;
    } catch (err) {
      console.error('Error al actualizar KDS:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchKitchenOrders();
    const interval = setInterval(fetchKitchenOrders, 4000); // Polling cada 4 seg para KDS en vivo
    return () => clearInterval(interval);
  }, [token]);

  // Pantalla completa
  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().then(() => setIsFullscreen(true)).catch(() => {});
    } else {
      document.exitFullscreen().then(() => setIsFullscreen(false)).catch(() => {});
    }
  };

  // Transición de estado de un plato individual
  const handleUpdateStatus = async (itemId, newStatus) => {
    try {
      const activeToken = token || localStorage.getItem('imperial_auth_token');
      await api.updateItemStatusKitchen(itemId, newStatus, activeToken);
      await fetchKitchenOrders();
    } catch (err) {
      alert(`No se pudo cambiar estado: ${err.message}`);
    }
  };

  // Marcar entregado (Mesero / Cocinero en apoyo)
  const handleDeliver = async (itemId) => {
    try {
      const activeToken = token || localStorage.getItem('imperial_auth_token');
      await api.markItemDelivered(itemId, activeToken);
      await fetchKitchenOrders();
    } catch (err) {
      alert(`No se pudo entregar plato: ${err.message}`);
    }
  };

  // Acción rápida: Marcar TODOS los platos de una comanda en un estado
  const handleBatchUpdateOrder = async (order, targetStatus) => {
    const eligibleItems = (order.items || []).filter(i => {
      if (targetStatus === 'EN_PREPARACION') return i.status === 'RECIBIDO';
      if (targetStatus === 'LISTO') return i.status === 'RECIBIDO' || i.status === 'EN_PREPARACION';
      return false;
    });

    if (eligibleItems.length === 0) return;

    try {
      const activeToken = token || localStorage.getItem('imperial_auth_token');
      for (const item of eligibleItems) {
        // Si va para LISTO desde RECIBIDO, pasar por EN_PREPARACION primero si lo exige RN-05
        if (targetStatus === 'LISTO' && item.status === 'RECIBIDO') {
          try {
            await api.updateItemStatusKitchen(item.id, 'EN_PREPARACION', activeToken);
          } catch (e) {
            // ignore
          }
        }
        await api.updateItemStatusKitchen(item.id, targetStatus, activeToken);
      }
      playKitchenBell();
      await fetchKitchenOrders();
    } catch (err) {
      alert(`Error al procesar comanda: ${err.message}`);
    }
  };

  // Métricas rápidas de la sesión de cocina
  const metrics = useMemo(() => {
    let recibido = 0;
    let preparacion = 0;
    let listo = 0;
    let delayed = 0;

    const now = new Date().getTime();

    orders.forEach(ord => {
      (ord.items || []).forEach(it => {
        if (it.status === 'RECIBIDO') recibido += it.quantity || 1;
        if (it.status === 'EN_PREPARACION') preparacion += it.quantity || 1;
        if (it.status === 'LISTO') listo += it.quantity || 1;

        const openTime = new Date(ord.opened_at || it.created_at).getTime();
        const elapsedMinutes = Math.floor((now - openTime) / (1000 * 60));
        if (elapsedMinutes >= DELAY_THRESHOLD_MINUTES && it.status !== 'LISTO') {
          delayed += 1;
        }
      });
    });

    return { recibido, preparacion, listo, delayed, totalOrders: orders.length };
  }, [orders]);

  // Filtrado de órdenes
  const filteredOrders = useMemo(() => {
    return orders.filter(ord => {
      // Filtro por canal / tipo
      if (selectedChannelFilter !== 'ALL' && ord.order_type !== selectedChannelFilter && ord.channel !== selectedChannelFilter) {
        return false;
      }

      // Filtro por estado de platos
      if (selectedStatusFilter !== 'ALL') {
        const hasMatchingStatus = (ord.items || []).some(i => i.status === selectedStatusFilter);
        if (!hasMatchingStatus) return false;
      }

      // Filtro por texto de búsqueda (mesa, código, nombre plato o cliente)
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchCode = (ord.display_code || '').toLowerCase().includes(q);
        const matchTable = String(ord.table_number || '').includes(q);
        const matchCustomer = (ord.customer_name || '').toLowerCase().includes(q);
        const matchItem = (ord.items || []).some(i => (i.dish_name || '').toLowerCase().includes(q));
        if (!matchCode && !matchTable && !matchCustomer && !matchItem) return false;
      }

      return true;
    });
  }, [orders, selectedChannelFilter, selectedStatusFilter, searchQuery]);

  // Calcular tiempo transcurrido para una comanda
  const getElapsedInfo = (dateString) => {
    if (!dateString) return { minutes: 0, text: '0m', isUrgent: false, isDelayed: false };
    const diffMs = new Date().getTime() - new Date(dateString).getTime();
    const minutes = Math.floor(diffMs / (1000 * 60));
    const seconds = Math.floor((diffMs % (1000 * 60)) / 1000);

    const isUrgent = minutes >= URGENT_THRESHOLD_MINUTES;
    const isDelayed = minutes >= DELAY_THRESHOLD_MINUTES;

    return {
      minutes,
      text: `${minutes}m ${seconds}s`,
      isUrgent,
      isDelayed,
    };
  };

  return (
    <div className="animate-fade-in" style={{
      padding: '20px 28px',
      maxWidth: '1600px',
      width: '100%',
      margin: '0 auto',
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      gap: '20px',
    }}>
      {/* HEADER DE CONTROL KDS DE COCINA */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.9) 100%)',
        border: '1.5px solid rgba(245, 158, 11, 0.3)',
        borderRadius: '20px',
        padding: '18px 24px',
        boxShadow: '0 15px 35px rgba(0, 0, 0, 0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '16px',
      }}>
        {/* Identidad de Cocina & Rol */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{
            background: 'linear-gradient(135deg, #f59e0b 0%, #ea580c 100%)',
            color: '#000',
            width: '52px',
            height: '52px',
            borderRadius: '16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 6px 20px rgba(245, 158, 11, 0.35)',
          }}>
            <ChefHat size={30} />
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h1 style={{ fontSize: '1.75rem', fontWeight: '900', color: '#f8fafc', letterSpacing: '-0.02em', margin: 0 }}>
                KDS &bull; Módulo de Cocina
              </h1>
              <span className="badge badge-emerald pulse-live" style={{ fontSize: '0.72rem', padding: '3px 8px' }}>
                EN VIVO
              </span>
              <span className="badge badge-gold" style={{ fontSize: '0.72rem', padding: '3px 8px' }}>
                {userRole || 'COCINERO'}
              </span>
            </div>
            <p style={{ color: '#94a3b8', fontSize: '0.84rem', margin: '3px 0 0' }}>
              {currentUserEmail ? `${currentUserEmail} • ` : ''}Sincronización automática &bull; {lastRefreshed.toLocaleTimeString()}
            </p>
          </div>
        </div>

        {/* Botones de Utilidades y Navegación */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          {/* Alerta sonora */}
          <button
            onClick={() => {
              setSoundEnabled(!soundEnabled);
              if (!soundEnabled) playKitchenBell();
            }}
            className="btn-secondary"
            style={{
              padding: '9px 14px',
              fontSize: '0.85rem',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              color: soundEnabled ? '#fbbf24' : '#64748b',
              borderColor: soundEnabled ? 'rgba(245, 158, 11, 0.3)' : 'rgba(255, 255, 255, 0.1)',
            }}
            title={soundEnabled ? 'Sonido activado al recibir pedidos' : 'Sonido silenciado'}
          >
            {soundEnabled ? <Volume2 size={16} /> : <VolumeX size={16} />}
            <span>{soundEnabled ? 'Sonido ON' : 'Silencio'}</span>
          </button>

          {/* Pantalla Completa */}
          <button
            onClick={toggleFullscreen}
            className="btn-secondary"
            style={{ padding: '9px 12px', fontSize: '0.85rem' }}
            title="Modo pantalla completa KDS"
          >
            {isFullscreen ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
          </button>

          {/* Refrescar */}
          <button
            onClick={fetchKitchenOrders}
            className="btn-secondary"
            style={{ padding: '9px 14px', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <RefreshCw size={15} />
            <span>Actualizar</span>
          </button>

          {/* Acceso a Admin */}
          {onNavigate && (
            <button
              onClick={() => onNavigate('ADMIN')}
              className="btn-secondary"
              style={{ padding: '9px 14px', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              <BarChart3 size={15} />
              <span>Panel Admin</span>
            </button>
          )}

          {/* Cerrar Sesión */}
          {onLogout && (
            <button
              onClick={onLogout}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '9px 14px',
                borderRadius: '10px',
                background: 'rgba(244, 63, 94, 0.15)',
                border: '1px solid rgba(244, 63, 94, 0.35)',
                color: '#fb7185',
                fontSize: '0.85rem',
                fontWeight: '700',
                cursor: 'pointer',
              }}
              title="Cerrar sesión de cocinero"
            >
              <LogOut size={15} />
              <span>Salir</span>
            </button>
          )}
        </div>
      </div>

      {/* BARRA DE ESTADÍSTICAS RÁPIDAS Y TIEMPOS */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '14px',
      }}>
        {/* Recibidos (Nuevos) */}
        <div style={{
          background: 'rgba(245, 158, 11, 0.08)',
          border: '1px solid rgba(245, 158, 11, 0.3)',
          borderRadius: '16px',
          padding: '14px 18px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <div>
            <div style={{ fontSize: '0.78rem', color: '#f59e0b', fontWeight: '800', textTransform: 'uppercase' }}>
              Por Iniciar
            </div>
            <div style={{ fontSize: '1.7rem', fontWeight: '900', color: '#fff', marginTop: '2px' }}>
              {metrics.recibido}
            </div>
          </div>
          <Flame size={26} color="#f59e0b" />
        </div>

        {/* En Preparación */}
        <div style={{
          background: 'rgba(59, 130, 246, 0.08)',
          border: '1px solid rgba(59, 130, 246, 0.3)',
          borderRadius: '16px',
          padding: '14px 18px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <div>
            <div style={{ fontSize: '0.78rem', color: '#60a5fa', fontWeight: '800', textTransform: 'uppercase' }}>
              En Fuego / Prep.
            </div>
            <div style={{ fontSize: '1.7rem', fontWeight: '900', color: '#fff', marginTop: '2px' }}>
              {metrics.preparacion}
            </div>
          </div>
          <Timer size={26} color="#3b82f6" />
        </div>

        {/* Listos para Servir */}
        <div style={{
          background: 'rgba(16, 185, 129, 0.08)',
          border: '1px solid rgba(16, 185, 129, 0.3)',
          borderRadius: '16px',
          padding: '14px 18px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <div>
            <div style={{ fontSize: '0.78rem', color: '#34d399', fontWeight: '800', textTransform: 'uppercase' }}>
              Listos para Servir
            </div>
            <div style={{ fontSize: '1.7rem', fontWeight: '900', color: '#fff', marginTop: '2px' }}>
              {metrics.listo}
            </div>
          </div>
          <CheckCircle2 size={26} color="#10b981" />
        </div>

        {/* Comandas con Retraso (>15m) */}
        <div style={{
          background: metrics.delayed > 0 ? 'rgba(244, 63, 94, 0.15)' : 'rgba(255, 255, 255, 0.03)',
          border: `1px solid ${metrics.delayed > 0 ? 'rgba(244, 63, 94, 0.4)' : 'rgba(255, 255, 255, 0.08)'}`,
          borderRadius: '16px',
          padding: '14px 18px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <div>
            <div style={{ fontSize: '0.78rem', color: metrics.delayed > 0 ? '#fb7185' : '#94a3b8', fontWeight: '800', textTransform: 'uppercase' }}>
              Alerta Demora &gt;15m
            </div>
            <div style={{ fontSize: '1.7rem', fontWeight: '900', color: metrics.delayed > 0 ? '#fb7185' : '#64748b', marginTop: '2px' }}>
              {metrics.delayed}
            </div>
          </div>
          <AlertTriangle size={26} color={metrics.delayed > 0 ? '#f43f5e' : '#64748b'} />
        </div>
      </div>

      {/* BARRA DE FILTROS Y BÚSQUEDA */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '12px',
        background: 'rgba(15, 23, 42, 0.7)',
        padding: '12px 18px',
        borderRadius: '16px',
        border: '1px solid rgba(255, 255, 255, 0.06)',
      }}>
        {/* Filtros por Estado */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '0.8rem', color: '#94a3b8', fontWeight: '700', marginRight: '4px' }}>
            Estado:
          </span>
          {[
            { id: 'ALL', label: 'Todos' },
            { id: 'RECIBIDO', label: 'Por Iniciar' },
            { id: 'EN_PREPARACION', label: 'En Preparación' },
            { id: 'LISTO', label: 'Listos' },
          ].map(f => (
            <button
              key={f.id}
              onClick={() => setSelectedStatusFilter(f.id)}
              style={{
                padding: '6px 12px',
                borderRadius: '8px',
                fontSize: '0.8rem',
                fontWeight: '700',
                border: 'none',
                cursor: 'pointer',
                background: selectedStatusFilter === f.id ? '#f59e0b' : 'rgba(255, 255, 255, 0.06)',
                color: selectedStatusFilter === f.id ? '#000' : '#cbd5e1',
                transition: 'all 0.15s ease',
              }}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* Buscador Rápido */}
        <div style={{ position: 'relative', minWidth: '240px' }}>
          <Search size={15} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#64748b' }} />
          <input
            type="text"
            placeholder="Buscar mesa, plato, código..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              width: '100%',
              padding: '8px 12px 8px 34px',
              borderRadius: '10px',
              background: 'rgba(0, 0, 0, 0.3)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              color: '#fff',
              fontSize: '0.82rem',
              outline: 'none',
            }}
          />
        </div>
      </div>

      {/* GRID DE COMANDAS ACTIVAS */}
      {filteredOrders.length === 0 ? (
        <div className="glass-panel" style={{
          padding: '80px 20px',
          textAlign: 'center',
          color: '#64748b',
          borderRadius: '20px',
          border: '1px dashed rgba(255, 255, 255, 0.1)',
        }}>
          <Utensils size={52} style={{ margin: '0 auto 16px', opacity: 0.3, color: '#f59e0b' }} />
          <h3 style={{ fontSize: '1.35rem', color: '#94a3b8', fontWeight: '700' }}>
            Cocina al Día
          </h3>
          <p style={{ fontSize: '0.92rem', marginTop: '6px', maxWidth: '450px', margin: '6px auto 0' }}>
            {orders.length === 0 
              ? 'No hay comandas pendientes en preparación. Los nuevos pedidos recibidos desde las mesas o carta digital sonarán automáticamente aquí.' 
              : 'No hay comandas que coincidan con los filtros seleccionados.'}
          </p>
        </div>
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))',
          gap: '20px',
          alignItems: 'start',
        }}>
          {filteredOrders.map((ord) => {
            const items = ord.items || [];
            const elapsed = getElapsedInfo(ord.opened_at);

            // Determinar color de acento de la tarjeta según tiempo
            const cardAccentColor = elapsed.isUrgent ? '#f43f5e' : elapsed.isDelayed ? '#fb923c' : '#f59e0b';

            return (
              <div
                key={ord.id}
                style={{
                  borderRadius: '18px',
                  border: `1.5px solid ${elapsed.isDelayed ? cardAccentColor : 'rgba(245, 158, 11, 0.25)'}`,
                  background: 'linear-gradient(180deg, #0e1523 0%, #090e18 100%)',
                  boxShadow: elapsed.isUrgent ? '0 10px 30px rgba(244, 63, 94, 0.25)' : '0 10px 25px rgba(0, 0, 0, 0.5)',
                  display: 'flex',
                  flexDirection: 'column',
                  overflow: 'hidden',
                  position: 'relative',
                  transition: 'transform 0.2s ease',
                }}
              >
                {/* ENCABEZADO DE COMANDA */}
                <div style={{
                  background: elapsed.isUrgent ? 'rgba(244, 63, 94, 0.18)' : elapsed.isDelayed ? 'rgba(251, 146, 60, 0.15)' : 'rgba(245, 158, 11, 0.1)',
                  padding: '14px 18px',
                  borderBottom: `1px solid ${elapsed.isDelayed ? `${cardAccentColor}44` : 'rgba(255, 255, 255, 0.08)'}`,
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{
                        fontSize: '0.74rem',
                        fontWeight: '900',
                        color: cardAccentColor,
                        textTransform: 'uppercase',
                        letterSpacing: '0.04em',
                      }}>
                        Comanda #{ord.display_code}
                      </span>
                      <span className="badge" style={{
                        background: 'rgba(255, 255, 255, 0.08)',
                        color: '#94a3b8',
                        fontSize: '0.68rem',
                        padding: '1px 6px',
                      }}>
                        {ord.channel || ord.order_type || 'MESA'}
                      </span>
                    </div>

                    <div style={{
                      fontSize: '1.25rem',
                      fontWeight: '900',
                      color: '#fff',
                      marginTop: '3px',
                      display: 'flex',
                      alignItems: 'baseline',
                      gap: '8px',
                    }}>
                      <span>Mesa #{ord.table_number || '?'}</span>
                      {ord.customer_name && (
                        <span style={{ fontSize: '0.82rem', color: '#cbd5e1', fontWeight: '600' }}>
                          &bull; {ord.customer_name}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Cronómetro / Tiempo en cocina */}
                  <div style={{ textAlign: 'right' }}>
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                      color: elapsed.isUrgent ? '#fb7185' : elapsed.isDelayed ? '#fdba74' : '#fbbf24',
                      fontWeight: '800',
                      fontSize: '0.85rem',
                      background: 'rgba(0, 0, 0, 0.35)',
                      padding: '4px 8px',
                      borderRadius: '8px',
                      border: `1px solid ${elapsed.isDelayed ? `${cardAccentColor}55` : 'rgba(255, 255, 255, 0.06)'}`,
                    }}>
                      <Clock size={13} />
                      <span>{elapsed.text}</span>
                    </div>
                    {elapsed.isUrgent && (
                      <span style={{ fontSize: '0.66rem', color: '#f43f5e', fontWeight: '800', marginTop: '3px', display: 'block' }}>
                        ¡PRIORITARIO!
                      </span>
                    )}
                  </div>
                </div>

                {/* ACCIÓN RÁPIDA: Pasar toda la comanda */}
                {canPerformAction('KDS_BATCH_ACTIONS') && (
                  <div style={{
                    padding: '8px 18px',
                    background: 'rgba(255, 255, 255, 0.02)',
                    borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    fontSize: '0.76rem',
                  }}>
                    <span style={{ color: '#94a3b8' }}>
                      {items.length} {items.length === 1 ? 'plato' : 'platos'} en pedido
                    </span>

                    <div style={{ display: 'flex', gap: '6px' }}>
                      {canPerformAction('KDS_START_PREP') && (
                        <button
                          onClick={() => handleBatchUpdateOrder(ord, 'EN_PREPARACION')}
                          style={{
                            padding: '4px 8px',
                            borderRadius: '6px',
                            background: 'rgba(59, 130, 246, 0.15)',
                            border: '1px solid rgba(59, 130, 246, 0.3)',
                            color: '#60a5fa',
                            fontSize: '0.72rem',
                            fontWeight: '700',
                            cursor: 'pointer',
                          }}
                          title="Pasar todos los platos recibidos a preparación"
                        >
                          ▶ Iniciar Todos
                        </button>
                      )}
                      {canPerformAction('KDS_MARK_READY') && (
                        <button
                          onClick={() => handleBatchUpdateOrder(ord, 'LISTO')}
                          style={{
                            padding: '4px 8px',
                            borderRadius: '6px',
                            background: 'rgba(16, 185, 129, 0.15)',
                            border: '1px solid rgba(16, 185, 129, 0.3)',
                            color: '#34d399',
                            fontSize: '0.72rem',
                            fontWeight: '700',
                            cursor: 'pointer',
                          }}
                          title="Marcar todos los platos de la comanda como listos"
                        >
                          ✓ Todo Listo
                        </button>
                      )}
                    </div>
                  </div>
                )}

                {/* ITEMS DE LA COMANDA */}
                <div style={{
                  padding: '16px 18px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px',
                  flex: 1,
                }}>
                  {items.map((item) => {
                    const statusColor = 
                      item.status === 'RECIBIDO' ? '#f59e0b' :
                      item.status === 'EN_PREPARACION' ? '#3b82f6' :
                      item.status === 'LISTO' ? '#10b981' :
                      item.status === 'ENTREGADO' ? '#64748b' : '#f43f5e';

                    const isMyDish = item.prepared_by_user_id === currentUserId || !item.prepared_by_user_id;
                    const isLockedByOther = item.status === 'EN_PREPARACION' && item.prepared_by_user_id && item.prepared_by_user_id !== currentUserId && userRole !== 'ADMIN';

                    return (
                      <div
                        key={item.id}
                        style={{
                          background: item.status === 'EN_PREPARACION' 
                            ? (isLockedByOther ? 'rgba(100, 116, 139, 0.12)' : 'rgba(59, 130, 246, 0.08)')
                            : item.status === 'LISTO' 
                            ? 'rgba(16, 185, 129, 0.08)' 
                            : 'rgba(255, 255, 255, 0.03)',
                          border: `1.5px solid ${
                            item.status === 'EN_PREPARACION' 
                              ? (isLockedByOther ? 'rgba(148, 163, 184, 0.3)' : 'rgba(59, 130, 246, 0.4)')
                              : item.status === 'LISTO' 
                              ? 'rgba(16, 185, 129, 0.4)' 
                              : 'rgba(255, 255, 255, 0.06)'
                          }`,
                          borderRadius: '14px',
                          padding: '12px 14px',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '8px',
                          opacity: isLockedByOther ? 0.75 : 1,
                        }}
                      >
                        {/* Cabecera del ítem */}
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
                            <span style={{
                              display: 'inline-block',
                              background: '#f59e0b',
                              color: '#000',
                              fontWeight: '900',
                              padding: '2px 8px',
                              borderRadius: '6px',
                              fontSize: '0.88rem',
                              lineHeight: 1.2,
                            }}>
                              {item.quantity}x
                            </span>
                            <div>
                              <span style={{ fontSize: '1.02rem', fontWeight: '800', color: '#f8fafc', lineHeight: 1.3, display: 'block' }}>
                                {item.dish_name || item.dish?.name}
                              </span>
                              {item.preparer_name && (
                                <span style={{
                                  fontSize: '0.73rem',
                                  color: isLockedByOther ? '#fdba74' : '#60a5fa',
                                  fontWeight: '700',
                                  display: 'flex',
                                  alignItems: 'center',
                                  gap: '4px',
                                  marginTop: '2px',
                                }}>
                                  👨‍🍳 {isLockedByOther ? `Preparando por: ${item.preparer_name}` : `En tu preparación (${item.preparer_name})`}
                                </span>
                              )}
                            </div>
                          </div>

                          <span style={{
                            fontSize: '0.72rem',
                            fontWeight: '800',
                            padding: '3px 8px',
                            borderRadius: '6px',
                            background: `${statusColor}22`,
                            color: statusColor,
                            border: `1px solid ${statusColor}55`,
                            whiteSpace: 'nowrap',
                          }}>
                            {item.status}
                          </span>
                        </div>

                        {/* Modificaciones de Ingredientes (RN-03 y Personalización) */}
                        {item.modifications?.length > 0 && (
                          <div style={{
                            padding: '8px 10px',
                            borderRadius: '8px',
                            background: 'rgba(244, 63, 94, 0.1)',
                            border: '1px solid rgba(244, 63, 94, 0.25)',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '3px',
                          }}>
                            {item.modifications.map((m, mIdx) => {
                              const isRemove = m.action === 'REMOVE' || m.action === 'QUITAR';
                              return (
                                <div key={mIdx} style={{
                                  fontSize: '0.8rem',
                                  color: isRemove ? '#fb7185' : '#fbbf24',
                                  fontWeight: '800',
                                  display: 'flex',
                                  alignItems: 'center',
                                  gap: '5px',
                                }}>
                                  <span>{isRemove ? '🚫 SIN:' : '✨ EXTRA:'}</span>
                                  <span>{m.ingredient_name || 'Ingrediente'}</span>
                                </div>
                              );
                            })}
                          </div>
                        )}

                        {/* Observaciones adicionales del cliente */}
                        {item.observations && (
                          <div style={{
                            fontSize: '0.78rem',
                            color: '#94a3b8',
                            fontStyle: 'italic',
                            background: 'rgba(255, 255, 255, 0.03)',
                            padding: '6px 8px',
                            borderRadius: '6px',
                          }}>
                            Nota: "{item.observations}"
                          </div>
                        )}

                        {/* Botones de Acción KDS (Máquina de estados RN-05 y RN-06) */}
                        <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
                          {item.status === 'RECIBIDO' && canPerformAction('KDS_START_PREP') && (
                            <button
                              onClick={() => handleUpdateStatus(item.id, 'EN_PREPARACION')}
                              style={{
                                flex: 1,
                                padding: '9px',
                                borderRadius: '8px',
                                background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
                                color: '#fff',
                                fontWeight: '800',
                                fontSize: '0.82rem',
                                border: 'none',
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: '6px',
                                boxShadow: '0 4px 12px rgba(37, 99, 235, 0.3)',
                              }}
                            >
                              <Play size={14} />
                              Iniciar Preparación
                            </button>
                          )}

                          {item.status === 'EN_PREPARACION' && canPerformAction('KDS_MARK_READY') && (
                            isLockedByOther ? (
                              <div style={{
                                flex: 1,
                                padding: '8px',
                                borderRadius: '8px',
                                background: 'rgba(255, 255, 255, 0.04)',
                                border: '1px dashed rgba(255, 255, 255, 0.15)',
                                color: '#94a3b8',
                                fontSize: '0.75rem',
                                fontWeight: '600',
                                textAlign: 'center',
                              }}>
                                🔒 En preparación por otro cocinero
                              </div>
                            ) : (
                              <button
                                onClick={() => handleUpdateStatus(item.id, 'LISTO')}
                                style={{
                                  flex: 1,
                                  padding: '9px',
                                  borderRadius: '8px',
                                  background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                                  color: '#000',
                                  fontWeight: '900',
                                  fontSize: '0.82rem',
                                  border: 'none',
                                  cursor: 'pointer',
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                  gap: '6px',
                                  boxShadow: '0 4px 12px rgba(16, 185, 129, 0.3)',
                                }}
                              >
                                <Check size={15} />
                                Marcar Listo
                              </button>
                            )
                          )}

                          {item.status === 'LISTO' && (
                            <button
                              onClick={() => handleDeliver(item.id)}
                              style={{
                                flex: 1,
                                padding: '9px',
                                borderRadius: '8px',
                                background: 'rgba(16, 185, 129, 0.15)',
                                border: '1px solid rgba(16, 185, 129, 0.4)',
                                color: '#34d399',
                                fontWeight: '800',
                                fontSize: '0.82rem',
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: '6px',
                              }}
                            >
                              <CheckCircle2 size={15} />
                              Entregar a Mesa / Mesero
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
