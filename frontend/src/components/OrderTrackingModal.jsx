import React, { useState, useEffect } from 'react';
import { 
  Clock, 
  CheckCircle2, 
  ChefHat, 
  CreditCard, 
  Star, 
  X, 
  RefreshCw, 
  Check, 
  Sparkles,
  ShoppingBag,
  Send,
  AlertCircle,
  FileText,
  Download,
  Printer,
  Receipt
} from 'lucide-react';
import confetti from 'canvas-confetti';
import { api } from '../services/api';

export default function OrderTrackingModal({ orderId, qrCode, onClose, onOrderCompleted }) {
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Estados de Pago & Cierre
  const [isClosingAccount, setIsClosingAccount] = useState(false);
  const [selectedTipRate, setSelectedTipRate] = useState(0.10); // 10% propina por defecto
  const [paymentMethod, setPaymentMethod] = useState('EFECTIVO');
  const [paymentAmount, setPaymentAmount] = useState('');
  const [processingPayment, setProcessingPayment] = useState(false);

  // Estados de Encuesta de Satisfacción
  const [showSurvey, setShowSurvey] = useState(false);
  const [foodRating, setFoodRating] = useState(5);
  const [serviceRating, setServiceRating] = useState(5);
  const [surveyComments, setSurveyComments] = useState('');
  const [surveySent, setSurveySent] = useState(false);

  // Estados de Factura de Venta
  const [invoice, setInvoice] = useState(null);
  const [loadingInvoice, setLoadingInvoice] = useState(false);
  const [showInvoiceModal, setShowInvoiceModal] = useState(false);

  const fetchInvoice = async () => {
    try {
      setLoadingInvoice(true);
      const invData = await api.getInvoicePublic(orderId, qrCode);
      setInvoice(invData);
    } catch (err) {
      console.warn('Aviso cargando factura:', err);
    } finally {
      setLoadingInvoice(false);
    }
  };

  const fetchOrder = async () => {
    try {
      const data = await api.getOrderPublic(orderId, qrCode);
      setOrder(data);
      if (!paymentAmount) {
        setPaymentAmount(data.saldo_pendiente || data.total || data.subtotal);
      }
      if (data.status === 'PAGADA' || parseFloat(data.total_paid || 0) > 0) {
        fetchInvoice();
      }
    } catch (err) {
      console.error(err);
      setError(err.message || 'No se pudo cargar la orden');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrder();
    const interval = setInterval(fetchOrder, 4000); // Polling cada 4 seg para seguir estados visuales en vivo
    return () => clearInterval(interval);
  }, [orderId, qrCode]);

  // Cierre de cuenta con propina opcional
  const handleCloseOrder = async () => {
    try {
      const updated = await api.closeOrderPublic(orderId, qrCode, null, selectedTipRate);
      setOrder(updated);
      setIsClosingAccount(false);
      setPaymentAmount(updated.saldo_pendiente || updated.total);
    } catch (err) {
      alert(`Error al solicitar cuenta: ${err.message}`);
    }
  };

  // Registrar pago
  const handlePay = async (e) => {
    e.preventDefault();
    setProcessingPayment(true);
    try {
      // Si la orden aún no está cerrada, cerrarla primero para fijar liquidación
      if (order?.status === 'ABIERTA') {
        try {
          await api.closeOrderPublic(orderId, qrCode, null, selectedTipRate);
        } catch (closeErr) {
          console.warn('Aviso al cerrar cuenta previo a pago:', closeErr);
        }
      }

      await api.payOrderPublic(orderId, {
        codigo_qr: qrCode,
        payment_method: paymentMethod,
        amount: parseFloat(paymentAmount),
        reference: paymentMethod === 'EFECTIVO' ? null : `CLIENTE-${Date.now().toString().slice(-6)}`,
      });
      await fetchOrder();

      confetti({
        particleCount: 80,
        spread: 60,
        origin: { y: 0.7 },
      });

      // Si quedó pagada, mostramos factura de venta y encuesta
      try {
        localStorage.removeItem('imperial_dish_customizations');
        localStorage.removeItem('imperial_active_order');
      } catch (e) {
        // ignore
      }
      await fetchInvoice();
      setShowInvoiceModal(true);
      setShowSurvey(true);
    } catch (err) {
      alert(`Error al registrar pago: ${err.message}`);
    } finally {
      setProcessingPayment(false);
    }
  };

  // Enviar encuesta de satisfacción
  const handleSendSurvey = async () => {
    try {
      // Calcular promedio redondeado como general_score (1 a 5)
      const calculatedGeneral = Math.max(1, Math.min(5, Math.round((foodRating + serviceRating) / 2)));
      await api.submitSurveyPublic(orderId, {
        codigo_qr: qrCode,
        food_score: foodRating,
        service_score: serviceRating,
        general_score: calculatedGeneral,
        comment: surveyComments.trim() || null,
      });
      setSurveySent(true);
      setShowSurvey(false);
      confetti({
        particleCount: 100,
        spread: 80,
      });
    } catch (err) {
      alert(`Error al enviar encuesta: ${err.message}`);
    }
  };

  if (!orderId) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.85)',
      backdropFilter: 'blur(8px)',
      zIndex: 2000,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '16px',
    }}>
      <div style={{
        background: '#121824',
        border: '1px solid rgba(245, 158, 11, 0.3)',
        borderRadius: '24px',
        width: '100%',
        maxWidth: '520px',
        maxHeight: '92vh',
        overflowY: 'auto',
        color: '#f8fafc',
        boxShadow: '0 25px 60px rgba(0, 0, 0, 0.8)',
        display: 'flex',
        flexDirection: 'column',
      }}>
        {/* Header */}
        <div style={{
          padding: '20px 24px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: 'rgba(245, 158, 11, 0.08)',
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="badge badge-gold">Comanda #{order?.display_code || '...'}</span>
              <span className="badge badge-emerald">Mesa #{order?.table_number || '1'}</span>
            </div>
            <h2 style={{ fontSize: '1.35rem', fontWeight: '800', marginTop: '4px' }}>
              Seguimiento & Cuenta
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
            <X size={18} />
          </button>
        </div>

        {/* Contenido */}
        <div style={{ padding: '20px 24px', flex: 1, display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* LÍNEA DE TIEMPO / ESTADOS VISUALES DEL PEDIDO (Exacto a Sección 7 del documento):
              Pedido recibido -> En preparación -> Listo -> Entregado */}
          <div style={{
            background: 'rgba(255, 255, 255, 0.03)',
            border: '1px solid rgba(255, 255, 255, 0.06)',
            borderRadius: '16px',
            padding: '16px',
          }}>
            <div style={{ fontSize: '0.85rem', fontWeight: '700', color: '#fbbf24', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <ChefHat size={16} />
              Estado en Cocina & Mesero
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {order?.items?.map((item) => {
                const isRecibido = item.status === 'RECIBIDO';
                const isPrep = item.status === 'EN_PREPARACION';
                const isListo = item.status === 'LISTO';
                const isEntregado = item.status === 'ENTREGADO';

                return (
                  <div key={item.id} style={{
                    background: 'rgba(0, 0, 0, 0.25)',
                    padding: '12px 14px',
                    borderRadius: '12px',
                    border: '1px solid rgba(255, 255, 255, 0.04)',
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <span style={{ fontWeight: '700', fontSize: '0.95rem' }}>
                        {item.quantity}x {item.dish_name}
                      </span>
                      <span style={{
                        fontSize: '0.75rem',
                        fontWeight: '800',
                        padding: '3px 8px',
                        borderRadius: '6px',
                        background: isEntregado ? 'rgba(16, 185, 129, 0.2)' : isListo ? 'rgba(59, 130, 246, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                        color: isEntregado ? '#34d399' : isListo ? '#60a5fa' : '#fbbf24',
                      }}>
                        {item.status}
                      </span>
                    </div>

                    {/* Barra de progreso de 4 pasos */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '4px', marginTop: '6px' }}>
                      <div style={{ height: '5px', borderRadius: '3px', background: '#f59e0b' }} title="Recibido" />
                      <div style={{ height: '5px', borderRadius: '3px', background: isPrep || isListo || isEntregado ? '#3b82f6' : 'rgba(255, 255, 255, 0.1)' }} title="En Preparación" />
                      <div style={{ height: '5px', borderRadius: '3px', background: isListo || isEntregado ? '#10b981' : 'rgba(255, 255, 255, 0.1)' }} title="Listo" />
                      <div style={{ height: '5px', borderRadius: '3px', background: isEntregado ? '#10b981' : 'rgba(255, 255, 255, 0.1)' }} title="Entregado" />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* DESGLOSE FINANCIERO: Total = subtotal + impuestos + propina - descuentos */}
          <div style={{
            background: 'rgba(255, 255, 255, 0.03)',
            borderRadius: '16px',
            padding: '16px',
            border: '1px solid rgba(255, 255, 255, 0.06)',
            fontSize: '0.88rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8' }}>
              <span>Subtotal Platos:</span>
              <span>${parseFloat(order?.subtotal || 0).toLocaleString('es-CO')}</span>
            </div>
            {parseFloat(order?.tip_amount || 0) > 0 && (
              <div style={{ display: 'flex', justifyContent: 'space-between', color: '#fbbf24' }}>
                <span>Propina Voluntaria:</span>
                <span>+${parseFloat(order.tip_amount).toLocaleString('es-CO')}</span>
              </div>
            )}
            <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8' }}>
              <span>Total Pagado:</span>
              <span style={{ color: '#34d399' }}>-${parseFloat(order?.total_paid || 0).toLocaleString('es-CO')}</span>
            </div>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              paddingTop: '8px',
              borderTop: '1px solid rgba(255, 255, 255, 0.1)',
              fontWeight: '800',
              fontSize: '1.15rem',
            }}>
              <span>Saldo Pendiente:</span>
              <span style={{ color: '#f59e0b' }}>
                ${parseFloat(order?.saldo_pendiente || order?.subtotal || 0).toLocaleString('es-CO')}
              </span>
            </div>
          </div>

          {/* INFORMACIÓN DE COBRO EN CAJA / ADMINISTRACIÓN (El cobro se realiza desde el panel de administrador) */}
          {parseFloat(order?.saldo_pendiente || 1) > 0 && order?.status !== 'PAGADA' && (
            <div style={{
              background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.08) 0%, rgba(30, 41, 59, 0.4) 100%)',
              border: '1px solid rgba(245, 158, 11, 0.3)',
              borderRadius: '16px',
              padding: '16px 18px',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Receipt size={18} color="#fbbf24" />
                <h4 style={{ fontSize: '0.95rem', fontWeight: '800', color: '#fbbf24', margin: 0 }}>
                  Cobro en Caja & Administración
                </h4>
              </div>
              <p style={{ fontSize: '0.82rem', color: '#cbd5e1', margin: 0, lineHeight: 1.45 }}>
                El cobro y cierre de tu cuenta se realiza directamente con el personal o en la caja del restaurante. 
                Una vez procesado el pago por el administrador, podrás visualizar y descargar aquí tu factura digital.
              </p>
              <div style={{
                marginTop: '4px',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                fontSize: '0.75rem',
                color: '#94a3b8',
                background: 'rgba(0, 0, 0, 0.25)',
                padding: '6px 10px',
                borderRadius: '8px',
                width: 'fit-content'
              }}>
                <Clock size={14} color="#f59e0b" />
                <span>Estado: Esperando liquidación y cobro en administración</span>
              </div>
            </div>
          )}

          {/* FACTURA DE VENTA FISCAL (Sección de Facturación del Sistema: SOLO cuando la mesa se ha cobrado/pagado) */}
          {(order?.status === 'PAGADA' || (invoice && parseFloat(order?.saldo_pendiente || 1) <= 0)) && (
            <div style={{
              background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%)',
              border: '1.5px solid rgba(245, 158, 11, 0.35)',
              borderRadius: '20px',
              padding: '18px 20px',
              boxShadow: '0 12px 30px rgba(0, 0, 0, 0.4)',
              position: 'relative',
              overflow: 'hidden',
            }}>
              {/* Encabezado de Factura */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', borderBottom: '1px solid rgba(255, 255, 255, 0.08)', paddingBottom: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div style={{
                    width: '42px',
                    height: '42px',
                    borderRadius: '12px',
                    background: 'rgba(245, 158, 11, 0.15)',
                    color: '#fbbf24',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    border: '1px solid rgba(245, 158, 11, 0.3)',
                  }}>
                    <Receipt size={22} />
                  </div>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontSize: '1.05rem', fontWeight: '800', color: '#f8fafc' }}>
                        Factura de Venta
                      </span>
                      <span className="badge badge-gold" style={{ fontSize: '0.68rem', padding: '2px 6px' }}>
                        {invoice?.invoice_number || `FAC-${order?.display_code || 'IMP'}`}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '2px' }}>
                      {invoice?.restaurant?.legal_name || 'Restaurante Imperial S.A.S.'} &bull; NIT: {invoice?.restaurant?.nit || '901.458.789-1'}
                    </div>
                  </div>
                </div>
              </div>

              {/* Datos de Emisión y Cliente */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '8px',
                fontSize: '0.76rem',
                color: '#94a3b8',
                marginBottom: '14px',
                background: 'rgba(255, 255, 255, 0.02)',
                padding: '8px 12px',
                borderRadius: '10px',
              }}>
                <div>
                  <span style={{ color: '#64748b' }}>Mesa:</span> <strong style={{ color: '#fff' }}>#{order?.table_number || invoice?.table_number || '1'}</strong>
                </div>
                <div>
                  <span style={{ color: '#64748b' }}>Medio de Pago:</span> <strong style={{ color: '#34d399' }}>{invoice?.payment_method || paymentMethod}</strong>
                </div>
                <div>
                  <span style={{ color: '#64748b' }}>Cliente:</span> <strong style={{ color: '#fff' }}>{order?.customer_name || invoice?.customer_name || 'Consumidor Final'}</strong>
                </div>
                <div>
                  <span style={{ color: '#64748b' }}>Estado:</span> <strong style={{ color: '#38bdf8' }}>Pagada & Almacenada</strong>
                </div>
              </div>

              {/* Detalle Ítem por Ítem del Consumo */}
              <div style={{ marginBottom: '14px' }}>
                <div style={{ fontSize: '0.78rem', fontWeight: '800', color: '#cbd5e1', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  Detalle del Consumo
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {(invoice?.items || order?.items || []).map((it, idx) => (
                    <div
                      key={it.id || idx}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '6px 10px',
                        borderRadius: '8px',
                        background: 'rgba(255, 255, 255, 0.03)',
                        fontSize: '0.82rem',
                      }}
                    >
                      <div style={{ flex: 1 }}>
                        <span style={{ fontWeight: '700', color: '#fff' }}>
                          {it.quantity}x {it.dish_name}
                        </span>
                        {it.modifications && it.modifications.length > 0 && (
                          <div style={{ fontSize: '0.7rem', color: '#94a3b8', marginTop: '2px' }}>
                            {Array.isArray(it.modifications) ? it.modifications.join(', ') : ''}
                          </div>
                        )}
                      </div>
                      <div style={{ fontWeight: '800', color: '#fbbf24', marginLeft: '12px' }}>
                        ${parseFloat(it.subtotal || (it.quantity * (it.unit_price || 0))).toLocaleString('es-CO')}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Resumen Fiscal Liquidado */}
              <div style={{
                borderTop: '1px dashed rgba(255, 255, 255, 0.15)',
                paddingTop: '10px',
                display: 'flex',
                flexDirection: 'column',
                gap: '4px',
                fontSize: '0.8rem',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8' }}>
                  <span>Subtotal:</span>
                  <span>${parseFloat(invoice?.subtotal || order?.subtotal || 0).toLocaleString('es-CO')}</span>
                </div>
                {parseFloat(invoice?.tax_amount || order?.tax_amount || 0) > 0 && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8' }}>
                    <span>Impuesto al Consumo (8%):</span>
                    <span>${parseFloat(invoice?.tax_amount || order?.tax_amount || 0).toLocaleString('es-CO')}</span>
                  </div>
                )}
                {parseFloat(invoice?.tip_amount || order?.tip_amount || 0) > 0 && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', color: '#fbbf24' }}>
                    <span>Propina Voluntaria:</span>
                    <span>+${parseFloat(invoice?.tip_amount || order?.tip_amount || 0).toLocaleString('es-CO')}</span>
                  </div>
                )}
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'baseline',
                  marginTop: '6px',
                  paddingTop: '8px',
                  borderTop: '1.5px solid rgba(255, 255, 255, 0.2)',
                  fontSize: '1.05rem',
                  fontWeight: '900',
                  color: '#34d399',
                }}>
                  <span>TOTAL PAGADO:</span>
                  <span>${parseFloat(invoice?.total || order?.total_paid || order?.total || order?.subtotal || 0).toLocaleString('es-CO')}</span>
                </div>
              </div>

              {/* Aviso de almacenamiento en el sistema */}
              <div style={{
                marginTop: '12px',
                fontSize: '0.72rem',
                color: '#64748b',
                textAlign: 'center',
                fontStyle: 'italic',
              }}>
                ✓ Factura generada y almacenada en el sistema. Puedes descargar el comprobante en PDF en la parte inferior.
              </div>
            </div>
          )}

          {/* ENCUESTA DE SATISFACCIÓN (Sección 7 del documento) */}
          {order?.status === 'PAGADA' && !surveySent && (
            <div style={{
              background: 'rgba(16, 185, 129, 0.08)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              borderRadius: '16px',
              padding: '16px',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <Sparkles size={18} color="#10b981" />
                <h4 style={{ fontSize: '0.98rem', fontWeight: '800', color: '#34d399' }}>
                  ¡Califica tu Experiencia Imperial!
                </h4>
              </div>
              <p style={{ fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '12px' }}>
                Tus respuestas premian a nuestros cocineros y meseros con comisiones de servicio.
              </p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <div>
                  <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Sabor y Calidad de la Comida:</span>
                  <div style={{ display: 'flex', gap: '6px', marginTop: '4px' }}>
                    {[1, 2, 3, 4, 5].map((s) => (
                      <button
                        key={s}
                        type="button"
                        onClick={() => setFoodRating(s)}
                        style={{
                          background: s <= foodRating ? '#f59e0b' : 'rgba(255, 255, 255, 0.08)',
                          color: s <= foodRating ? '#000' : '#94a3b8',
                          border: 'none',
                          borderRadius: '6px',
                          padding: '6px 10px',
                          cursor: 'pointer',
                          fontWeight: '800',
                        }}
                      >
                        ★ {s}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Atención del Mesero:</span>
                  <div style={{ display: 'flex', gap: '6px', marginTop: '4px' }}>
                    {[1, 2, 3, 4, 5].map((s) => (
                      <button
                        key={s}
                        type="button"
                        onClick={() => setServiceRating(s)}
                        style={{
                          background: s <= serviceRating ? '#10b981' : 'rgba(255, 255, 255, 0.08)',
                          color: s <= serviceRating ? '#000' : '#94a3b8',
                          border: 'none',
                          borderRadius: '6px',
                          padding: '6px 10px',
                          cursor: 'pointer',
                          fontWeight: '800',
                        }}
                      >
                        ★ {s}
                      </button>
                    ))}
                  </div>
                </div>

                <input
                  type="text"
                  placeholder="Comentarios u observaciones para el chef..."
                  value={surveyComments}
                  onChange={(e) => setSurveyComments(e.target.value)}
                  style={{
                    padding: '8px 12px',
                    borderRadius: '8px',
                    background: 'rgba(255, 255, 255, 0.05)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    color: '#fff',
                    fontSize: '0.85rem',
                  }}
                />

                <button
                  onClick={handleSendSurvey}
                  style={{
                    padding: '10px',
                    borderRadius: '10px',
                    background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                    color: '#000',
                    fontWeight: '800',
                    fontSize: '0.9rem',
                    border: 'none',
                    cursor: 'pointer',
                  }}
                >
                  Enviar Encuesta
                </button>
              </div>
            </div>
          )}

          {/* ACCIONES INFERIORES: Solo aparecen cuando la mesa ha sido cobrada (order?.status === 'PAGADA') */}
          {(order?.status === 'PAGADA' || parseFloat(order?.saldo_pendiente || 1) <= 0 || surveySent) && (
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '12px',
              padding: '16px 18px',
              borderRadius: '18px',
              background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(5, 150, 105, 0.18) 100%)',
              border: '1.5px solid rgba(16, 185, 129, 0.35)',
              boxShadow: '0 8px 25px rgba(0, 0, 0, 0.35)',
              marginTop: '4px',
            }}>
              <div style={{
                color: '#34d399',
                fontWeight: '800',
                fontSize: '0.95rem',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}>
                <CheckCircle2 size={18} color="#10b981" />
                <span>Mesa cobrada exitosamente. ¡Gracias por visitarnos!</span>
              </div>

              <div style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '10px',
                marginTop: '4px',
              }}>
                {/* Botón Descargar Factura PDF en la parte de abajo */}
                <a
                  href={api.getInvoicePdfUrl(orderId, qrCode)}
                  target="_blank"
                  rel="noreferrer"
                  download
                  id="btn-descargar-factura-pdf"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px',
                    padding: '12px',
                    borderRadius: '12px',
                    background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
                    color: '#000',
                    fontWeight: '800',
                    fontSize: '0.88rem',
                    textDecoration: 'none',
                    boxShadow: '0 4px 15px rgba(245, 158, 11, 0.3)',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    textAlign: 'center',
                  }}
                  title="Descargar factura en PDF"
                >
                  <Download size={18} />
                  <span>Descargar Factura</span>
                </a>

                {/* Botón Cerrar y Dejar Mesa Lista */}
                <button
                  type="button"
                  id="btn-cerrar-modal-mesa"
                  onClick={() => {
                    if (onOrderCompleted) onOrderCompleted();
                    else onClose();
                  }}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px',
                    padding: '12px',
                    borderRadius: '12px',
                    background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                    color: '#000',
                    fontWeight: '800',
                    fontSize: '0.88rem',
                    border: 'none',
                    cursor: 'pointer',
                    boxShadow: '0 4px 15px rgba(16, 185, 129, 0.35)',
                    transition: 'all 0.2s ease',
                    textAlign: 'center',
                  }}
                  title="Cerrar y dejar mesa lista para nuevos clientes"
                >
                  <Check size={18} />
                  <span>Cerrar</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
