/**
 * Staff & Authentication Domain API Service
 */
import { request } from '../../shared/api/client';

export const authApi = {
  login(email, password) {
    return request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  },
};
