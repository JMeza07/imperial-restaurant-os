/**
 * Client Domain API Service
 * Encapsulates guest QR scanning, menu browsing, ordering, and self-checkout
 */
import { request, API_BASE } from '../../shared/api/client';

export const clientApi = {
  // --- Carta & Platos ---
  getCarta() {
    return request('/carta');
  },

  getDishDetail(dishId) {
    return request(`/carta/platos/${dishId}`);
  },

  // --- Mesas & QR ---
  getTableByQR(qrCode) {
    return request(`/mesas/qr/${qrCode}`);
  },

  // --- Pedidos & Checkout ---
  createOrder(payload) {
    return request('/ordenes', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  getOrderPublic(orderId, qrCode) {
    return request(`/ordenes/${orderId}?codigo_qr=${qrCode}`);
  },

  closeOrderPublic(orderId, qrCode, tipAmount = 0, tipRate = 0) {
    return request(`/ordenes/${orderId}/cierre?codigo_qr=${qrCode}`, {
      method: 'POST',
      body: JSON.stringify({
        tip_amount: tipAmount ? parseFloat(tipAmount) : null,
        tip_rate: tipRate ? parseFloat(tipRate) : null,
      }),
    });
  },

  payOrderPublic(orderId, payload) {
    return request(`/ordenes/${orderId}/pagos`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  getInvoicePublic(orderId, qrCode) {
    const q = qrCode ? `?codigo_qr=${qrCode}` : '';
    return request(`/ordenes/${orderId}/factura${q}`);
  },

  getInvoicePdfUrl(orderId, qrCode) {
    const q = qrCode ? `?codigo_qr=${qrCode}` : '';
    return `${API_BASE}/ordenes/${orderId}/factura/pdf${q}`;
  },

  submitOrderSurvey(orderId, qrCode, payload) {
    return request(`/ordenes/${orderId}/encuesta?codigo_qr=${qrCode}`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
};
