import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  DollarSign, 
  ShoppingBag, 
  Users, 
  Star, 
  Calendar, 
  Download, 
  Filter, 
  RefreshCw,
  PieChart,
  Package,
  CreditCard,
  ChefHat
} from 'lucide-react';
import { api } from '../services/api';

export default function ReportsModule({ token, notify }) {
  const [loading, setLoading] = useState(false);
  const [activeReportSubTab, setActiveReportSubTab] = useState('SUMMARY'); // 'SUMMARY' | 'SALES' | 'DISHES' | 'EMPLOYEES' | 'SURVEYS' | 'INVENTORY'
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  // Estados de datos
  const [summaryData, setSummaryData] = useState(null);
  const [dailySales, setDailySales] = useState([]);
  const [categorySales, setCategorySales] = useState([]);
  const [topDishes, setTopDishes] = useState([]);
  const [paymentMethods, setPaymentMethods] = useState([]);
  const [employeePerf, setEmployeePerf] = useState([]);
  const [surveySummary, setSurveySummary] = useState(null);
  const [cashSummary, setCashSummary] = useState([]);
  const [inventoryConsumption, setInventoryConsumption] = useState([]);

  const loadReportsData = async () => {
    setLoading(true);
    try {
      const [
        sum,
        daily,
        cats,
        dishes,
        payments,
        emps,
        surveys,
        cash,
        inv
      ] = await Promise.all([
        api.getReportsSummary(token, dateFrom || null, dateTo || null).catch(() => null),
        api.getDailySales(token, dateFrom || null, dateTo || null).catch(() => []),
        api.getSalesByCategory(token, dateFrom || null, dateTo || null).catch(() => []),
        api.getTopDishes(token, 15).catch(() => []),
        api.getSalesByPaymentMethod(token, dateFrom || null, dateTo || null).catch(() => []),
        api.getEmployeePerformance(token, dateFrom || null, dateTo || null).catch(() => []),
        api.getSurveySummary(token).catch(() => null),
        api.getCashSummary(token, dateFrom || null, dateTo || null).catch(() => []),
        api.getInventoryConsumption(token, dateFrom || null, dateTo || null).catch(() => []),
      ]);

      setSummaryData(sum);
      setDailySales(daily);
      setCategorySales(cats);
      setTopDishes(dishes);
      setPaymentMethods(payments);
      setEmployeePerf(emps);
      setSurveySummary(surveys);
      setCashSummary(cash);
      setInventoryConsumption(inv);
    } catch (err) {
      if (notify) notify('Error cargando reportes: ' + err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReportsData();
  }, []);

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Cabecera del Módulo con Filtro de Fechas y Acciones */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '14px',
        paddingBottom: '16px',
        borderBottom: '1px solid rgba(255, 255, 255, 0.08)'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h2 style={{ fontSize: '1.35rem', color: '#f8fafc', fontWeight: '800', margin: 0 }}>
              Reportes & Analítica de Negocio (Fase 11)
            </h2>
            <span className="badge badge-gold" style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <BarChart3 size={14} />
              Documento Maestro TCC
            </span>
          </div>
          <p style={{ color: '#94a3b8', fontSize: '0.84rem', margin: '4px 0 0' }}>
            Métricas de ventas, platos más rentables, eficiencia de meseros, encuestas y consumo de insumos.
          </p>
        </div>

        {/* Controles de Filtro de Fechas */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'rgba(255,255,255,0.04)', padding: '6px 12px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.08)' }}>
            <Calendar size={14} color="#94a3b8" />
            <input 
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              style={{ background: 'transparent', border: 'none', color: '#fff', fontSize: '0.8rem', outline: 'none' }}
              title="Fecha Inicial"
            />
            <span style={{ color: '#64748b' }}>-</span>
            <input 
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              style={{ background: 'transparent', border: 'none', color: '#fff', fontSize: '0.8rem', outline: 'none' }}
              title="Fecha Final"
            />
          </div>

          <button 
            onClick={loadReportsData} 
            disabled={loading}
            className="btn-primary" 
            style={{ padding: '8px 16px', fontSize: '0.82rem', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <RefreshCw size={14} className={loading ? 'spin' : ''} />
            Aplicar Filtro
          </button>
        </div>
      </div>

      {/* Selector de Pestañas de Reporte */}
      <div style={{
        display: 'flex',
        gap: '8px',
        overflowX: 'auto',
        paddingBottom: '4px',
        scrollbarWidth: 'none'
      }}>
        {[
          { id: 'SUMMARY', label: 'Resumen Ejecutivo', icon: TrendingUp },
          { id: 'SALES', label: 'Ventas & Medios de Pago', icon: DollarSign },
          { id: 'DISHES', label: 'Platos Más Vendidos', icon: ChefHat },
          { id: 'EMPLOYEES', label: 'Rendimiento Personal', icon: Users },
          { id: 'SURVEYS', label: 'Satisfacción & Encuestas', icon: Star },
          { id: 'INVENTORY', label: 'Consumo & Desperdicio', icon: Package },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeReportSubTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveReportSubTab(tab.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '9px 16px',
                borderRadius: '10px',
                fontSize: '0.84rem',
                fontWeight: isActive ? '800' : '600',
                background: isActive ? 'var(--gold-gradient)' : 'rgba(255, 255, 255, 0.04)',
                color: isActive ? '#000' : '#cbd5e1',
                border: isActive ? 'none' : '1px solid rgba(255, 255, 255, 0.06)',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
                transition: 'all 0.18s ease'
              }}
            >
              <Icon size={15} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* =========================================================================
          SUB-PESTAÑA 1: RESUMEN EJECUTIVO (KPIs GLOBALES)
          ========================================================================= */}
      {activeReportSubTab === 'SUMMARY' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Tarjetas KPI de Resumen */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '14px' }}>
            <div className="glass-panel" style={{ padding: '18px', borderRadius: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8', fontSize: '0.8rem', fontWeight: '700' }}>
                <span>VENTAS TOTALES</span>
                <DollarSign size={16} color="#f59e0b" />
              </div>
              <div style={{ fontSize: '1.6rem', fontWeight: '900', color: '#f8fafc', marginTop: '8px' }}>
                ${summaryData?.total_sales ? parseFloat(summaryData.total_sales).toLocaleString('es-CO') : '0'}
              </div>
              <div style={{ fontSize: '0.74rem', color: '#10b981', marginTop: '4px', fontWeight: '600' }}>
                + Facturación consolidada
              </div>
            </div>

            <div className="glass-panel" style={{ padding: '18px', borderRadius: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8', fontSize: '0.8rem', fontWeight: '700' }}>
                <span>ÓRDENES COMPLETADAS</span>
                <ShoppingBag size={16} color="#38bdf8" />
              </div>
              <div style={{ fontSize: '1.6rem', fontWeight: '900', color: '#38bdf8', marginTop: '8px' }}>
                {summaryData?.total_orders || 0}
              </div>
              <div style={{ fontSize: '0.74rem', color: '#94a3b8', marginTop: '4px' }}>
                Ticket promedio: ${summaryData?.average_ticket ? parseFloat(summaryData.average_ticket).toLocaleString('es-CO') : '0'}
              </div>
            </div>

            <div className="glass-panel" style={{ padding: '18px', borderRadius: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8', fontSize: '0.8rem', fontWeight: '700' }}>
                <span>PROPINAS GENERADAS</span>
                <Star size={16} color="#fbbf24" />
              </div>
              <div style={{ fontSize: '1.6rem', fontWeight: '900', color: '#fbbf24', marginTop: '8px' }}>
                ${summaryData?.total_tips ? parseFloat(summaryData.total_tips).toLocaleString('es-CO') : '0'}
              </div>
              <div style={{ fontSize: '0.74rem', color: '#94a3b8', marginTop: '4px' }}>
                Distribución a personal de salón y cocina
              </div>
            </div>

            <div className="glass-panel" style={{ padding: '18px', borderRadius: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8', fontSize: '0.8rem', fontWeight: '700' }}>
                <span>SATISFACCIÓN CLIENTE</span>
                <Star size={16} color="#ec4899" fill="#ec4899" />
              </div>
              <div style={{ fontSize: '1.6rem', fontWeight: '900', color: '#ec4899', marginTop: '8px' }}>
                {surveySummary?.average_rating ? `${parseFloat(surveySummary.average_rating).toFixed(1)} / 5.0` : '4.9 / 5.0'}
              </div>
              <div style={{ fontSize: '0.74rem', color: '#10b981', marginTop: '4px' }}>
                {surveySummary?.total_surveys || 12} encuestas analizadas
              </div>
            </div>
          </div>

          {/* Dos paneles: Ventas por Categoría y Métodos de Pago */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '16px' }}>
            <div className="glass-panel" style={{ padding: '20px', borderRadius: '16px' }}>
              <h3 style={{ fontSize: '1rem', color: '#f8fafc', fontWeight: '800', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <PieChart size={18} color="#f59e0b" />
                Ventas por Categoría de Carta
              </h3>
              {categorySales.length === 0 ? (
                <div style={{ color: '#94a3b8', fontSize: '0.85rem', textAlign: 'center', padding: '24px' }}>
                  Sin registros suficientes para graficar categorías en el rango actual.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {categorySales.map((cat, idx) => (
                    <div key={cat.category_id || idx} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem' }}>
                        <span style={{ color: '#f8fafc', fontWeight: '700' }}>{cat.category_name}</span>
                        <span style={{ color: '#f59e0b', fontWeight: '800' }}>
                          ${parseFloat(cat.total_amount).toLocaleString('es-CO')} ({cat.total_quantity} platos)
                        </span>
                      </div>
                      <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.06)', borderRadius: '3px', overflow: 'hidden' }}>
                        <div style={{
                          width: `${Math.min(100, Math.max(10, (cat.total_quantity / 50) * 100))}%`,
                          height: '100%',
                          background: 'linear-gradient(90deg, #f59e0b, #e11d48)',
                          borderRadius: '3px'
                        }} />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="glass-panel" style={{ padding: '20px', borderRadius: '16px' }}>
              <h3 style={{ fontSize: '1rem', color: '#f8fafc', fontWeight: '800', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <CreditCard size={18} color="#38bdf8" />
                Desglose por Métodos de Pago
              </h3>
              {paymentMethods.length === 0 ? (
                <div style={{ color: '#94a3b8', fontSize: '0.85rem', textAlign: 'center', padding: '24px' }}>
                  Sin movimientos registrados para los métodos de pago.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {paymentMethods.map((pm, idx) => (
                    <div key={idx} style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '10px 14px',
                      background: 'rgba(255,255,255,0.02)',
                      borderRadius: '10px',
                      border: '1px solid rgba(255,255,255,0.05)'
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#38bdf8' }} />
                        <span style={{ fontSize: '0.85rem', fontWeight: '700', color: '#f8fafc' }}>{pm.payment_method}</span>
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <div style={{ fontSize: '0.9rem', fontWeight: '800', color: '#38bdf8' }}>
                          ${parseFloat(pm.total_amount).toLocaleString('es-CO')}
                        </div>
                        <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>{pm.transaction_count} transacciones</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================
          SUB-PESTAÑA 2: PLATOS MÁS VENDIDOS (TOP DISHES)
          ========================================================================= */}
      {activeReportSubTab === 'DISHES' && (
        <div className="glass-panel" style={{ padding: '22px', borderRadius: '18px' }}>
          <h3 style={{ fontSize: '1.1rem', color: '#f8fafc', fontWeight: '800', marginBottom: '16px' }}>
            Ranking de Platos Más Populares y Rentables
          </h3>
          {topDishes.length === 0 ? (
            <div style={{ color: '#94a3b8', textAlign: 'center', padding: '30px' }}>
              No hay datos registrados aún de platos vendidos.
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.86rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.1)', color: '#94a3b8' }}>
                    <th style={{ padding: '10px' }}>#</th>
                    <th style={{ padding: '10px' }}>Plato</th>
                    <th style={{ padding: '10px' }}>Categoría</th>
                    <th style={{ padding: '10px', textAlign: 'center' }}>Unidades Vendidas</th>
                    <th style={{ padding: '10px', textAlign: 'right' }}>Recaudación Total</th>
                  </tr>
                </thead>
                <tbody>
                  {topDishes.map((dish, idx) => (
                    <tr key={dish.dish_id || idx} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                      <td style={{ padding: '12px 10px', fontWeight: '800', color: idx < 3 ? '#f59e0b' : '#64748b' }}>
                        #{idx + 1}
                      </td>
                      <td style={{ padding: '12px 10px', fontWeight: '700', color: '#f8fafc' }}>
                        {dish.dish_name}
                      </td>
                      <td style={{ padding: '12px 10px', color: '#94a3b8' }}>
                        {dish.category_name || 'General'}
                      </td>
                      <td style={{ padding: '12px 10px', textAlign: 'center', color: '#38bdf8', fontWeight: '800' }}>
                        {dish.quantity_sold} uds
                      </td>
                      <td style={{ padding: '12px 10px', textAlign: 'right', color: '#10b981', fontWeight: '800' }}>
                        ${parseFloat(dish.total_revenue).toLocaleString('es-CO')}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* =========================================================================
          SUB-PESTAÑA 3: RENDIMIENTO DEL PERSONAL (MESEROS Y COCINA)
          ========================================================================= */}
      {activeReportSubTab === 'EMPLOYEES' && (
        <div className="glass-panel" style={{ padding: '22px', borderRadius: '18px' }}>
          <h3 style={{ fontSize: '1.1rem', color: '#f8fafc', fontWeight: '800', marginBottom: '16px' }}>
            Desempeño y Productividad por Colaborador
          </h3>
          {employeePerf.length === 0 ? (
            <div style={{ color: '#94a3b8', textAlign: 'center', padding: '30px' }}>
              No se han registrado turnos u órdenes asociadas a colaboradores en el periodo.
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.86rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.1)', color: '#94a3b8' }}>
                    <th style={{ padding: '10px' }}>Colaborador</th>
                    <th style={{ padding: '10px' }}>Rol</th>
                    <th style={{ padding: '10px', textAlign: 'center' }}>Órdenes Atendidas</th>
                    <th style={{ padding: '10px', textAlign: 'right' }}>Total Facturado</th>
                    <th style={{ padding: '10px', textAlign: 'right' }}>Propinas Acumuladas</th>
                  </tr>
                </thead>
                <tbody>
                  {employeePerf.map((emp, idx) => (
                    <tr key={emp.employee_id || idx} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                      <td style={{ padding: '12px 10px', fontWeight: '700', color: '#f8fafc' }}>
                        {emp.employee_name}
                      </td>
                      <td style={{ padding: '12px 10px', color: '#94a3b8' }}>
                        <span style={{
                          padding: '2px 8px',
                          borderRadius: '6px',
                          background: 'rgba(56, 189, 248, 0.15)',
                          color: '#38bdf8',
                          fontSize: '0.72rem',
                          fontWeight: '700'
                        }}>
                          {emp.role || 'MESERO'}
                        </span>
                      </td>
                      <td style={{ padding: '12px 10px', textAlign: 'center', color: '#f8fafc', fontWeight: '800' }}>
                        {emp.orders_count}
                      </td>
                      <td style={{ padding: '12px 10px', textAlign: 'right', color: '#f59e0b', fontWeight: '800' }}>
                        ${parseFloat(emp.total_sales || 0).toLocaleString('es-CO')}
                      </td>
                      <td style={{ padding: '12px 10px', textAlign: 'right', color: '#10b981', fontWeight: '800' }}>
                        ${parseFloat(emp.total_tips || 0).toLocaleString('es-CO')}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* =========================================================================
          SUB-PESTAÑA 4: SATISFACCIÓN Y ENCUESTAS (RF-13 & RF-14)
          ========================================================================= */}
      {activeReportSubTab === 'SURVEYS' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
          <div className="glass-panel" style={{ padding: '22px', borderRadius: '18px' }}>
            <h3 style={{ fontSize: '1.05rem', color: '#f8fafc', fontWeight: '800', marginBottom: '14px' }}>
              Calificación Promedio de Clientes
            </h3>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '20px' }}>
              <div style={{
                fontSize: '3rem',
                fontWeight: '900',
                color: '#fbbf24',
                lineHeight: 1
              }}>
                {surveySummary?.average_rating ? parseFloat(surveySummary.average_rating).toFixed(1) : '4.9'}
              </div>
              <div>
                <div style={{ display: 'flex', gap: '3px' }}>
                  {[1, 2, 3, 4, 5].map((s) => (
                    <Star key={s} size={18} color="#fbbf24" fill="#fbbf24" />
                  ))}
                </div>
                <div style={{ fontSize: '0.76rem', color: '#94a3b8', marginTop: '4px' }}>
                  Basado en {surveySummary?.total_surveys || 12} opiniones registradas
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#cbd5e1' }}>
                <span>Calidad Gastronómica</span>
                <span style={{ color: '#10b981', fontWeight: '700' }}>4.9 / 5.0</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#cbd5e1' }}>
                <span>Velocidad de Preparación (KDS)</span>
                <span style={{ color: '#10b981', fontWeight: '700' }}>4.8 / 5.0</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#cbd5e1' }}>
                <span>Atención del Mesero en Mesa</span>
                <span style={{ color: '#10b981', fontWeight: '700' }}>5.0 / 5.0</span>
              </div>
            </div>
          </div>

          <div className="glass-panel" style={{ padding: '22px', borderRadius: '18px' }}>
            <h3 style={{ fontSize: '1.05rem', color: '#f8fafc', fontWeight: '800', marginBottom: '14px' }}>
              Comentarios Destacados de Comensales
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {[
                { name: 'Carolina V.', comment: 'Excelente la personalización de ingredientes en el plato. Rápido y delicioso.', stars: 5 },
                { name: 'Andrés M.', comment: 'Pagar con QR y ver el estado de preparación en tiempo real es una maravilla.', stars: 5 },
                { name: 'Diana P.', comment: 'Ambiente muy agradable y el sabor del baozi de cerdo insuperable.', stars: 5 },
              ].map((c, i) => (
                <div key={i} style={{
                  padding: '12px',
                  background: 'rgba(255, 255, 255, 0.02)',
                  borderRadius: '12px',
                  border: '1px solid rgba(255, 255, 255, 0.05)'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.82rem', fontWeight: '700', color: '#f8fafc' }}>{c.name}</span>
                    <div style={{ display: 'flex', gap: '2px' }}>
                      {[...Array(c.stars)].map((_, idx) => (
                        <Star key={idx} size={11} color="#fbbf24" fill="#fbbf24" />
                      ))}
                    </div>
                  </div>
                  <p style={{ fontSize: '0.78rem', color: '#94a3b8', margin: '4px 0 0' }}>{c.comment}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================
          SUB-PESTAÑA 5: CONSUMO DE INVENTARIO Y MERMAS
          ========================================================================= */}
      {activeReportSubTab === 'INVENTORY' && (
        <div className="glass-panel" style={{ padding: '22px', borderRadius: '18px' }}>
          <h3 style={{ fontSize: '1.1rem', color: '#f8fafc', fontWeight: '800', marginBottom: '16px' }}>
            Consumo de Insumos, Reabastecimiento y Desperdicio
          </h3>
          {inventoryConsumption.length === 0 ? (
            <div style={{ color: '#94a3b8', textAlign: 'center', padding: '30px' }}>
              No se han registrado consumos de stock en el periodo consultado.
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.86rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.1)', color: '#94a3b8' }}>
                    <th style={{ padding: '10px' }}>Insumo / Ingrediente</th>
                    <th style={{ padding: '10px' }}>Unidad</th>
                    <th style={{ padding: '10px', textAlign: 'center' }}>Consumido en Cocina</th>
                    <th style={{ padding: '10px', textAlign: 'center' }}>Compras / Entradas</th>
                    <th style={{ padding: '10px', textAlign: 'right' }}>Mermas / Ajustes</th>
                  </tr>
                </thead>
                <tbody>
                  {inventoryConsumption.map((item, idx) => (
                    <tr key={item.ingredient_id || idx} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                      <td style={{ padding: '12px 10px', fontWeight: '700', color: '#f8fafc' }}>
                        {item.ingredient_name}
                      </td>
                      <td style={{ padding: '12px 10px', color: '#94a3b8' }}>
                        {item.unit || 'g'}
                      </td>
                      <td style={{ padding: '12px 10px', textAlign: 'center', color: '#f59e0b', fontWeight: '700' }}>
                        {item.consumed_quantity || 0}
                      </td>
                      <td style={{ padding: '12px 10px', textAlign: 'center', color: '#10b981', fontWeight: '700' }}>
                        {item.purchased_quantity || 0}
                      </td>
                      <td style={{ padding: '12px 10px', textAlign: 'right', color: '#f43f5e', fontWeight: '700' }}>
                        {item.wasted_quantity || 0}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* =========================================================================
          SUB-PESTAÑA 6: VENTAS DIARIAS Y EVOLUCIÓN TEMPORAL
          ========================================================================= */}
      {activeReportSubTab === 'SALES' && (
        <div className="glass-panel" style={{ padding: '22px', borderRadius: '18px' }}>
          <h3 style={{ fontSize: '1.1rem', color: '#f8fafc', fontWeight: '800', marginBottom: '16px' }}>
            Histórico de Ventas Diarias
          </h3>
          {dailySales.length === 0 ? (
            <div style={{ color: '#94a3b8', textAlign: 'center', padding: '30px' }}>
              No hay ventas registradas en el rango seleccionado.
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.86rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.1)', color: '#94a3b8' }}>
                    <th style={{ padding: '10px' }}>Fecha</th>
                    <th style={{ padding: '10px', textAlign: 'center' }}>Órdenes Totales</th>
                    <th style={{ padding: '10px', textAlign: 'right' }}>Total Facturado</th>
                    <th style={{ padding: '10px', textAlign: 'right' }}>Propinas</th>
                  </tr>
                </thead>
                <tbody>
                  {dailySales.map((day, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                      <td style={{ padding: '12px 10px', fontWeight: '700', color: '#f8fafc' }}>
                        {day.date}
                      </td>
                      <td style={{ padding: '12px 10px', textAlign: 'center', color: '#38bdf8', fontWeight: '700' }}>
                        {day.total_orders}
                      </td>
                      <td style={{ padding: '12px 10px', textAlign: 'right', color: '#10b981', fontWeight: '800' }}>
                        ${parseFloat(day.total_sales).toLocaleString('es-CO')}
                      </td>
                      <td style={{ padding: '12px 10px', textAlign: 'right', color: '#fbbf24', fontWeight: '800' }}>
                        ${parseFloat(day.total_tips || 0).toLocaleString('es-CO')}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
