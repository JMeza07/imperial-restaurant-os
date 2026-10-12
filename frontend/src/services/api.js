const API_BASE = '/api/v1';

export const api = {
  // --- Carta & Platos ---
  async getCarta() {
    const res = await fetch(`${API_BASE}/carta`);
    if (!res.ok) throw new Error('Error al cargar la carta');
    return res.json();
  },

  async getDishDetail(dishId) {
    const res = await fetch(`${API_BASE}/carta/platos/${dishId}`);
    if (!res.ok) throw new Error('Error al cargar el detalle del plato');
    return res.json();
  },

  // --- Mesas & QR ---
  async getTableByQR(qrCode) {
    const res = await fetch(`${API_BASE}/mesas/qr/${qrCode}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Mesa no encontrada');
    }
    return res.json();
  },

  // --- Pedidos ---
  async createOrder(payload) {
    const res = await fetch(`${API_BASE}/ordenes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Error al procesar el pedido');
    }
    return res.json();
  },

  async getOrderPublic(orderId, qrCode) {
    const res = await fetch(`${API_BASE}/ordenes/${orderId}?codigo_qr=${qrCode}`);
    if (!res.ok) throw new Error('Error al consultar orden');
    return res.json();
  },

  async closeOrderPublic(orderId, qrCode, tipAmount = 0, tipRate = 0) {
    const res = await fetch(`${API_BASE}/ordenes/${orderId}/cierre?codigo_qr=${qrCode}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        tip_amount: tipAmount ? parseFloat(tipAmount) : null,
        tip_rate: tipRate ? parseFloat(tipRate) : null,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Error al cerrar cuenta');
    }
    return res.json();
  },

  async payOrderPublic(orderId, payload) {
    const res = await fetch(`${API_BASE}/ordenes/${orderId}/pagos`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      const detailMsg = typeof err.detail === 'string'
        ? err.detail
        : (err.detail?.message || JSON.stringify(err.detail) || 'Error al registrar pago');
      throw new Error(detailMsg);
    }
    return res.json();
  },

  async submitSurveyPublic(orderId, payload) {
    const res = await fetch(`${API_BASE}/ordenes/${orderId}/encuesta`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Error al enviar encuesta');
    }
    return res.json();
  },

  // --- Autenticación Staff / Admin ---
  async login(email, password) {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Credenciales incorrectas');
    }
    return res.json();
  },

  // --- Cocina KDS ---
  async getKitchenActiveOrders(token) {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const res = await fetch(`${API_BASE}/cocina/ordenes-activas`, { headers });
    if (!res.ok) throw new Error('Error al cargar órdenes de cocina');
    return res.json();
  },

  async updateItemStatusKitchen(itemId, newStatus, token) {
    const headers = {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
    let endpoint = `${API_BASE}/detalles/${itemId}/estado`;
    let body = JSON.stringify({ status: newStatus });

    if (newStatus === 'EN_PREPARACION') {
      endpoint = `${API_BASE}/cocina/detalles/${itemId}/en-preparacion`;
      body = undefined;
    } else if (newStatus === 'LISTO') {
      endpoint = `${API_BASE}/cocina/detalles/${itemId}/listo`;
      body = undefined;
    }

    const res = await fetch(endpoint, {
      method: 'PATCH',
      headers,
      body,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Error al actualizar estado en cocina');
    }
    return res.json();
  },

  async markItemDelivered(itemId, token) {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const res = await fetch(`${API_BASE}/mesero/detalles/${itemId}/entregado`, {
      method: 'PATCH',
      headers,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Error al entregar plato');
    }
    return res.json();
  },

  // --- Reportes y Dashboard Admin ---
  async getReportsSummary(token) {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const res = await fetch(`${API_BASE}/admin/reportes/resumen`, { headers });
    if (!res.ok) throw new Error('Error al cargar reporte resumen');
    return res.json();
  },

  async getTopDishes(token) {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const res = await fetch(`${API_BASE}/admin/reportes/platos/mas-vendidos`, { headers });
    if (!res.ok) throw new Error('Error al cargar platos más vendidos');
    return res.json();
  },

  async listOrdersAdmin(token, orderStatus = null, tableId = null) {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const params = new URLSearchParams();
    if (orderStatus) params.append('order_status', orderStatus);
    if (tableId) params.append('table_id', tableId);
    const queryString = params.toString() ? `?${params.toString()}` : '';
    const res = await fetch(`${API_BASE}/admin/ordenes${queryString}`, { headers });
    if (!res.ok) throw new Error('Error al listar órdenes');
    return res.json();
  },

  // --- CRUD Admin Mesas ---
  async listTablesAdmin(token) {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const res = await fetch(`${API_BASE}/admin/mesas`, { headers });
    if (!res.ok) throw new Error('Error al listar mesas');
    return res.json();
  },

  async createTable(data, token) {
    const res = await fetch(`${API_BASE}/admin/mesas`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Error al crear mesa');
    }
    return res.json();
  },

  async updateTable(tableId, data, token) {
    const res = await fetch(`${API_BASE}/admin/mesas/${tableId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Error al actualizar mesa');
    }
    return res.json();
  },

  async regenerateQR(tableId, token) {
    const res = await fetch(`${API_BASE}/admin/mesas/${tableId}/regenerate-qr`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error('Error al regenerar código QR');
    return res.json();
  },

  // --- CRUD Admin Platos ---
  async listDishesAdmin(token) {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const res = await fetch(`${API_BASE}/admin/platos`, { headers });
    if (!res.ok) throw new Error('Error al listar platos');
    return res.json();
  },

  async createDish(data, token) {
    const res = await fetch(`${API_BASE}/admin/platos`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Error al crear plato');
    }
    return res.json();
  },

  async updateDish(dishId, data, token) {
    const res = await fetch(`${API_BASE}/admin/platos/${dishId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Error al actualizar plato');
    }
    return res.json();
  },

  async toggleDishAvailability(dishId, token) {
    const res = await fetch(`${API_BASE}/admin/platos/${dishId}/disponibilidad`, {
      method: 'PATCH',
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error('Error al cambiar disponibilidad del plato');
    return res.json();
  },

  async updateDishRecipe(dishId, items, token) {
    const res = await fetch(`${API_BASE}/admin/platos/${dishId}/receta`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ items }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Error al actualizar receta del plato');
    }
    return res.json();
  },

  // --- CRUD Admin Categorías ---
  async listCategoriesAdmin(token) {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const res = await fetch(`${API_BASE}/admin/categorias`, { headers });
    if (!res.ok) throw new Error('Error al listar categorías');
    return res.json();
  },

  async createCategory(data, token) {
    const res = await fetch(`${API_BASE}/admin/categorias`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Error al crear categoría');
    }
    return res.json();
  },

  // --- CRUD Admin Ingredientes & Salud ---
  async listIngredientsAdmin(token) {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const res = await fetch(`${API_BASE}/admin/ingredientes`, { headers });
    if (!res.ok) throw new Error('Error al listar ingredientes');
    return res.json();
  },

  async createIngredient(data, token) {
    const res = await fetch(`${API_BASE}/admin/ingredientes`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Error al crear ingrediente');
    }
    return res.json();
  },

  async updateIngredient(ingredientId, data, token) {
    const res = await fetch(`${API_BASE}/admin/ingredientes/${ingredientId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Error al actualizar ingrediente');
    }
    return res.json();
  },

  async toggleIngredientAvailability(ingredientId, token) {
    const res = await fetch(`${API_BASE}/admin/ingredientes/${ingredientId}/disponibilidad`, {
      method: 'PATCH',
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error('Error al cambiar disponibilidad');
    return res.json();
  },

  // --- Restaurante Profile & Configuración ---
  async getRestaurantProfile() {
    const res = await fetch(`${API_BASE}/restaurant/profile`);
    if (!res.ok) return null;
    return res.json();
  },

  async updateRestaurantProfile(data, token) {
    const res = await fetch(`${API_BASE}/admin/restaurant/profile`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Error al actualizar configuración del restaurante');
    }
    return res.json();
  },

  // --- Beneficios de Salud & Alérgenos ---
  async listBenefitsAdmin(token) {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const res = await fetch(`${API_BASE}/admin/beneficios`, { headers });
    if (!res.ok) throw new Error('Error al listar beneficios');
    return res.json();
  },

  async createBenefit(data, token) {
    const res = await fetch(`${API_BASE}/admin/beneficios`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Error al crear beneficio para la salud');
    return res.json();
  },

  // --- Sucursales y Zonas ---
  async listBranchesAdmin(token) {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const res = await fetch(`${API_BASE}/admin/branches`, { headers });
    if (!res.ok) throw new Error('Error al listar sucursales');
    return res.json();
  },

  async listZonesAdmin(token) {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const res = await fetch(`${API_BASE}/admin/zones`, { headers });
    if (!res.ok) throw new Error('Error al listar zonas');
    return res.json();
  },

  // --- Inventario y Stock ---
  async listStockAdmin(token) {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const res = await fetch(`${API_BASE}/admin/inventario/stock`, { headers });
    if (!res.ok) throw new Error('Error al listar inventario');
    return res.json();
  },

  async createStockAdjustment(data, token) {
    const res = await fetch(`${API_BASE}/admin/inventario/ajustes`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Error al ajustar stock');
    }
    return res.json();
  },

  async updateStockItem(stockId, data, token) {
    const res = await fetch(`${API_BASE}/admin/inventario/stock/${stockId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Error al actualizar stock');
    }
    return res.json();
  },

  async initializeStock(branchId, token) {
    const query = branchId ? `?branch_id=${branchId}` : '';
    const res = await fetch(`${API_BASE}/admin/inventario/stock/inicializar${query}`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error('Error al inicializar stock');
    return res.json();
  },

  // --- Caja y Arqueo ---
  async getOpenCashSession(token) {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const res = await fetch(`${API_BASE}/admin/caja/actual`, { headers });
    if (!res.ok) return null;
    return res.json();
  },

  async openCashSession(data, token) {
    const res = await fetch(`${API_BASE}/admin/caja/abrir`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Error al abrir caja');
    }
    return res.json();
  },

  async closeCashSession(sessionId, data, token) {
    const res = await fetch(`${API_BASE}/admin/caja/${sessionId}/cerrar`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Error al cerrar caja');
    }
    return res.json();
  },

  // --- Domicilios ---
  async listDeliveriesAdmin(token) {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const res = await fetch(`${API_BASE}/admin/domicilios`, { headers });
    if (!res.ok) throw new Error('Error al listar domicilios');
    return res.json();
  },

  async listDeliveryZonesAdmin(token) {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const res = await fetch(`${API_BASE}/admin/domicilios/zonas`, { headers });
    if (!res.ok) throw new Error('Error al listar zonas de domicilio');
    return res.json();
  },

  // --- Turnos y Personal ---
  async listEmployeesAdmin(token) {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const res = await fetch(`${API_BASE}/admin/empleados`, { headers });
    if (!res.ok) throw new Error('Error al listar empleados');
    return res.json();
  },

  async listShiftTemplatesAdmin(token) {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const res = await fetch(`${API_BASE}/admin/turnos/plantillas`, { headers });
    if (!res.ok) throw new Error('Error al listar plantillas de turno');
    return res.json();
  },

  async listShiftsAdmin(token) {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const res = await fetch(`${API_BASE}/admin/turnos`, { headers });
    if (!res.ok) throw new Error('Error al listar turnos');
    return res.json();
  },

  // --- Comisiones y Propinas ---
  async listCommissionRulesAdmin(token) {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const res = await fetch(`${API_BASE}/admin/comisiones/reglas`, { headers });
    if (!res.ok) throw new Error('Error al listar reglas de comisión');
    return res.json();
  },

  async listCommissionPeriodsAdmin(token) {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const res = await fetch(`${API_BASE}/admin/comisiones/periodos`, { headers });
    if (!res.ok) throw new Error('Error al listar periodos de comisión');
    return res.json();
  },

  async listCommissionEventsAdmin(token) {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const res = await fetch(`${API_BASE}/admin/comisiones/eventos`, { headers });
    if (!res.ok) throw new Error('Error al listar eventos de comisión');
    return res.json();
  },

  // --- Auditoría y Salud del Sistema ---
  async getSystemHealthAdmin(token) {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const res = await fetch(`${API_BASE}/admin/system/health`, { headers });
    if (!res.ok) throw new Error('Error al consultar estado del sistema');
    return res.json();
  },

  async getAuditStatsAdmin(token) {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const res = await fetch(`${API_BASE}/admin/system/audit-stats`, { headers });
    if (!res.ok) throw new Error('Error al consultar estadísticas de auditoría');
    return res.json();
  },

  // --- Facturación & Facturas de Venta ---
  async getInvoicePublic(orderId, qrCode) {
    const q = qrCode ? `?codigo_qr=${qrCode}` : '';
    const res = await fetch(`${API_BASE}/ordenes/${orderId}/factura${q}`);
    if (!res.ok) throw new Error('Error al consultar factura de venta');
    return res.json();
  },

  getInvoicePdfUrl(orderId, qrCode) {
    const q = qrCode ? `?codigo_qr=${qrCode}` : '';
    return `${API_BASE}/ordenes/${orderId}/factura/pdf${q}`;
  },

  async getInvoicesAdmin(token, limit = 50, skip = 0) {
    const res = await fetch(`${API_BASE}/admin/facturas?limit=${limit}&skip=${skip}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error('Error al consultar facturas');
    return res.json();
  },

  async closeOrderAdmin(orderId, payload, token) {
    const res = await fetch(`${API_BASE}/ordenes/${orderId}/cierre`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Error al cerrar cuenta');
    }
    return res.json();
  },

  async payOrderAdmin(orderId, payload, token) {
    const res = await fetch(`${API_BASE}/admin/ordenes/${orderId}/pagos`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Error al registrar cobro');
    }
    return res.json();
  },

  async listUsersAdmin(token) {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const res = await fetch(`${API_BASE}/admin/users`, { headers });
    if (!res.ok) throw new Error('Error al listar usuarios');
    return res.json();
  },

  async createUserAdmin(data, token) {
    const res = await fetch(`${API_BASE}/admin/users`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Error al crear usuario');
    }
    return res.json();
  },

  async updateUserAdmin(userId, data, token) {
    const res = await fetch(`${API_BASE}/admin/users/${userId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Error al actualizar usuario');
    }
    return res.json();
  },

  async getDailySales(token, dateFrom = null, dateTo = null) {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const params = new URLSearchParams();
    if (dateFrom) params.append('date_from', dateFrom);
    if (dateTo) params.append('date_to', dateTo);
    const qs = params.toString() ? `?${params.toString()}` : '';
    const res = await fetch(`${API_BASE}/admin/reportes/ventas/diarias${qs}`, { headers });
    if (!res.ok) throw new Error('Error al cargar ventas diarias');
    return res.json();
  },

  async getSalesByCategory(token, dateFrom = null, dateTo = null) {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const params = new URLSearchParams();
    if (dateFrom) params.append('date_from', dateFrom);
    if (dateTo) params.append('date_to', dateTo);
    const qs = params.toString() ? `?${params.toString()}` : '';
    const res = await fetch(`${API_BASE}/admin/reportes/ventas/categorias${qs}`, { headers });
    if (!res.ok) throw new Error('Error al cargar ventas por categorías');
    return res.json();
  },

  async getSalesByPaymentMethod(token, dateFrom = null, dateTo = null) {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const params = new URLSearchParams();
    if (dateFrom) params.append('date_from', dateFrom);
    if (dateTo) params.append('date_to', dateTo);
    const qs = params.toString() ? `?${params.toString()}` : '';
    const res = await fetch(`${API_BASE}/admin/reportes/ventas/metodos-pago${qs}`, { headers });
    if (!res.ok) throw new Error('Error al cargar ventas por métodos de pago');
    return res.json();
  },

  async getEmployeePerformance(token, dateFrom = null, dateTo = null) {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const params = new URLSearchParams();
    if (dateFrom) params.append('date_from', dateFrom);
    if (dateTo) params.append('date_to', dateTo);
    const qs = params.toString() ? `?${params.toString()}` : '';
    const res = await fetch(`${API_BASE}/admin/reportes/empleados/rendimiento${qs}`, { headers });
    if (!res.ok) throw new Error('Error al cargar rendimiento de empleados');
    return res.json();
  },

  async getSurveySummary(token) {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const res = await fetch(`${API_BASE}/admin/reportes/encuestas/resumen`, { headers });
    if (!res.ok) throw new Error('Error al cargar resumen de encuestas');
    return res.json();
  },

  async getCashSummary(token, dateFrom = null, dateTo = null) {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const params = new URLSearchParams();
    if (dateFrom) params.append('date_from', dateFrom);
    if (dateTo) params.append('date_to', dateTo);
    const qs = params.toString() ? `?${params.toString()}` : '';
    const res = await fetch(`${API_BASE}/admin/reportes/caja/resumen${qs}`, { headers });
    if (!res.ok) throw new Error('Error al cargar resumen de caja');
    return res.json();
  },

  async getInventoryConsumption(token, dateFrom = null, dateTo = null) {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const params = new URLSearchParams();
    if (dateFrom) params.append('date_from', dateFrom);
    if (dateTo) params.append('date_to', dateTo);
    const qs = params.toString() ? `?${params.toString()}` : '';
    const res = await fetch(`${API_BASE}/admin/reportes/inventario/consumo${qs}`, { headers });
    if (!res.ok) throw new Error('Error al cargar consumo de inventario');
    return res.json();
  },
};
