/**
 * Kitchen (KDS) Domain API Service
 * Encapsulates real-time orders board and item status transitions for kitchen staff
 */
import { request } from '../../shared/api/client';

export const kdsApi = {
  getKitchenBoard(token) {
    return request('/cocina/tablero', { token });
  },

  updateItemStatus(itemId, newStatus, token) {
    return request(`/cocina/items/${itemId}/estado`, {
      method: 'PATCH',
      token,
      body: JSON.stringify({ status: newStatus }),
    });
  },
};
