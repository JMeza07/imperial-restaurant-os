import React, { useState } from 'react';
import { 
  Lock, 
  Mail, 
  Shield, 
  ArrowRight, 
  Loader2,
  Sparkles
} from 'lucide-react';
import { api } from '../services/api';

export default function LoginModal({ onLoginSuccess, onClose }) {
  const [email, setEmail] = useState('admin@imperial.local');
  const [password, setPassword] = useState('ChangeMe123!');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const data = await api.login(email, password);
      // Decodificar JWT para conocer el rol del usuario (ADMIN, COCINERO, MESERO, etc.)
      let role = 'ADMIN';
      try {
        const base64Url = data.access_token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(
          atob(base64)
            .split('')
            .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
            .join('')
        );
        const decoded = JSON.parse(jsonPayload);
        if (decoded.role) role = decoded.role;
      } catch (e) {
        console.warn('No se pudo decodificar rol del JWT:', e);
      }

      onLoginSuccess(data.access_token, role, email);
      onClose();
    } catch (err) {
      setError(err.message || 'Error de autenticación');
    } finally {
      setLoading(false);
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
      backdropFilter: 'blur(10px)',
      zIndex: 1000,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '16px',
    }}>
      <div className="glass-panel" style={{
        maxWidth: '420px',
        width: '100%',
        padding: '32px',
        borderRadius: '20px',
        border: '1px solid rgba(245, 158, 11, 0.3)',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.8)',
        background: '#0d131f',
      }}>
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <div style={{
            background: 'var(--gold-gradient)',
            color: '#000',
            width: '52px',
            height: '52px',
            borderRadius: '16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 14px',
          }}>
            <Shield size={28} />
          </div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: '800', color: '#f8fafc' }}>
            Acceso Corporativo
          </h2>
          <p style={{ color: '#94a3b8', fontSize: '0.85rem', marginTop: '4px' }}>
            Ingreso protegido para Administradores y Cocineros
          </p>
        </div>

        {error && (
          <div style={{
            padding: '10px 14px',
            borderRadius: '8px',
            background: 'rgba(244, 63, 94, 0.15)',
            border: '1px solid rgba(244, 63, 94, 0.3)',
            color: '#fb7185',
            fontSize: '0.85rem',
            marginBottom: '16px',
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>
              Correo Institucional
            </label>
            <div style={{ position: 'relative' }}>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                style={{
                  width: '100%',
                  padding: '12px 14px 12px 38px',
                  borderRadius: '10px',
                  background: 'rgba(255, 255, 255, 0.04)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  color: '#fff',
                  fontSize: '0.9rem',
                }}
              />
              <Mail size={16} color="#64748b" style={{ position: 'absolute', left: '12px', top: '14px' }} />
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>
              Contraseña
            </label>
            <div style={{ position: 'relative' }}>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                style={{
                  width: '100%',
                  padding: '12px 14px 12px 38px',
                  borderRadius: '10px',
                  background: 'rgba(255, 255, 255, 0.04)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  color: '#fff',
                  fontSize: '0.9rem',
                }}
              />
              <Lock size={16} color="#64748b" style={{ position: 'absolute', left: '12px', top: '14px' }} />
            </div>
          </div>

          <div style={{
            fontSize: '0.78rem',
            color: '#94a3b8',
            background: 'rgba(255, 255, 255, 0.03)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            padding: '10px 12px',
            borderRadius: '10px',
            marginTop: '2px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
          }}>
            <div style={{ fontWeight: '700', color: '#f8fafc' }}>
              ⚡ Cuentas de demostración según Rol:
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                type="button"
                onClick={() => {
                  setEmail('admin@imperial.local');
                  setPassword('ChangeMe123!');
                }}
                style={{
                  flex: 1,
                  padding: '6px 8px',
                  borderRadius: '8px',
                  background: 'rgba(245, 158, 11, 0.15)',
                  border: '1px solid rgba(245, 158, 11, 0.3)',
                  color: '#fbbf24',
                  fontSize: '0.75rem',
                  fontWeight: '700',
                  cursor: 'pointer',
                }}
              >
                👑 Administrador
              </button>
              <button
                type="button"
                onClick={() => {
                  setEmail('cocinero@imperial.local');
                  setPassword('Cocina123!');
                }}
                style={{
                  flex: 1,
                  padding: '6px 8px',
                  borderRadius: '8px',
                  background: 'rgba(59, 130, 246, 0.15)',
                  border: '1px solid rgba(59, 130, 246, 0.3)',
                  color: '#60a5fa',
                  fontSize: '0.75rem',
                  fontWeight: '700',
                  cursor: 'pointer',
                }}
              >
                👨‍🍳 Cocina (KDS)
              </button>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '10px', marginTop: '12px' }}>
            <button
              type="button"
              onClick={onClose}
              style={{
                flex: 1,
                padding: '12px',
                borderRadius: '10px',
                background: 'rgba(255, 255, 255, 0.08)',
                color: '#fff',
                fontSize: '0.9rem',
              }}
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="btn-primary"
              style={{
                flex: 2,
                padding: '12px',
                fontSize: '0.95rem',
              }}
            >
              {loading ? (
                <Loader2 className="pulse-live" size={18} />
              ) : (
                <>
                  Iniciar Sesión
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
