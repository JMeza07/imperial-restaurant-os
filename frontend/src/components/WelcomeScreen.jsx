import React, { useState } from 'react';
import { 
  QrCode, 
  User, 
  LogIn, 
  Sparkles, 
  ArrowRight, 
  Camera, 
  CheckCircle2, 
  AlertCircle,
  ChefHat,
  ShieldCheck,
  UtensilsCrossed,
  ScanLine,
  Keyboard
} from 'lucide-react';
import { api } from '../services/api';
import { useThemeCustomizer } from '../utils/ThemeCustomizerContext';

export default function WelcomeScreen({ onSelectTable, onOpenLogin }) {
  const { themeSettings } = useThemeCustomizer();
  const [step, setStep] = useState('SCAN'); // 'SCAN' | 'NAME'
  const [qrCodeInput, setQrCodeInput] = useState('');
  const [scannedTable, setScannedTable] = useState(null);
  const [clientName, setClientName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isManualInput, setIsManualInput] = useState(false);

  // Simular escaneo de QR (detecta la mesa)
  const handleValidateQR = async (codeToTest) => {
    const code = (codeToTest || qrCodeInput).trim();
    if (!code) {
      setError('Por favor ingresa o escanea el código QR de la mesa');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const table = await api.getTableByQR(code);
      setScannedTable(table);
      setStep('NAME');
    } catch (err) {
      setError(err.message || 'Código QR no válido o mesa no encontrada');
    } finally {
      setLoading(false);
    }
  };

  // Confirmar nombre del cliente e iniciar sesión de mesa
  const handleConfirmName = (e) => {
    e.preventDefault();
    const finalName = clientName.trim() || 'Comensal Imperial';
    onSelectTable({
      qrCode: scannedTable.qr_code || scannedTable.codigo_qr || qrCodeInput,
      tableNumber: scannedTable.number,
      customerName: finalName,
      tableData: scannedTable
    });
  };

  return (
    <div className="animate-fade-in" style={{
      minHeight: '100vh',
      width: '100%',
      background: 'radial-gradient(circle at 50% 15%, #1c2438 0%, #0d121d 60%, #070a10 100%)',
      color: '#ffffff',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between',
      padding: '24px 20px',
      position: 'relative',
      fontFamily: "'Plus Jakarta Sans', sans-serif",
      overflow: 'hidden',
    }}>
      {/* Halo decorativo de luz ámbar imperial */}
      <div style={{
        position: 'absolute',
        top: '-80px',
        left: '50%',
        transform: 'translateX(-50%)',
        width: '360px',
        height: '360px',
        borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(245, 158, 11, 0.15) 0%, transparent 70%)',
        filter: 'blur(40px)',
        pointerEvents: 'none',
      }} />

      {/* CABECERA: NOMBRE DEL RESTAURANTE Y BIENVENIDA */}
      <div style={{ textAlign: 'center', marginTop: '16px', zIndex: 2 }}>
        {themeSettings?.logoUrl ? (
          <div style={{ marginBottom: '14px' }}>
            <img
              src={themeSettings.logoUrl}
              alt="Logo Restaurante Imperial"
              style={{ maxHeight: '75px', maxWidth: '240px', objectFit: 'contain', filter: 'drop-shadow(0 4px 12px rgba(0,0,0,0.5))' }}
            />
          </div>
        ) : (
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            background: 'rgba(245, 158, 11, 0.12)',
            border: '1px solid rgba(245, 158, 11, 0.3)',
            padding: '6px 14px',
            borderRadius: '9999px',
            marginBottom: '16px',
          }}>
            <UtensilsCrossed size={16} color="#fbbf24" />
            <span style={{ fontSize: '0.82rem', fontWeight: '800', color: '#fbbf24', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
              Alta Gastronomía &bull; Experiencia Digital
            </span>
          </div>
        )}

        <h1 style={{
          fontSize: '2.4rem',
          fontWeight: '900',
          letterSpacing: '-0.02em',
          background: 'linear-gradient(135deg, #ffffff 40%, #fbbf24 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          margin: '0 0 8px',
          lineHeight: '1.15',
        }}>
          {themeSettings?.brandName || 'RESTAURANTE IMPERIAL'}
        </h1>

        <p style={{
          fontSize: '0.98rem',
          color: '#94a3b8',
          maxWidth: '420px',
          margin: '0 auto',
          lineHeight: '1.5',
        }}>
          ¡Bienvenido a una experiencia culinaria única! Descubre nuestra carta viva, nutrición consciente y sabores excepcionales.
        </p>
      </div>

      {/* ZONA CENTRAL: PASO 1 (ESCANEAR QR) O PASO 2 (SOLICITAR NOMBRE) */}
      <div style={{
        maxWidth: '440px',
        width: '100%',
        margin: '24px auto',
        zIndex: 2,
      }}>
        {step === 'SCAN' ? (
          <div className="glass-panel" style={{
            background: 'rgba(18, 24, 38, 0.75)',
            border: '1.5px solid rgba(245, 158, 11, 0.25)',
            borderRadius: '24px',
            padding: '24px 22px',
            boxShadow: '0 20px 45px rgba(0, 0, 0, 0.6)',
            textAlign: 'center',
          }}>
            <div style={{
              width: '84px',
              height: '84px',
              borderRadius: '24px',
              background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.2) 0%, rgba(245, 158, 11, 0.05) 100%)',
              border: '2px solid rgba(245, 158, 11, 0.4)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 18px',
              position: 'relative',
            }}>
              <QrCode size={46} color="#fbbf24" />
              <ScanLine size={32} color="#f59e0b" style={{ position: 'absolute', opacity: 0.7 }} className="pulse-live" />
            </div>

            <h2 style={{ fontSize: '1.3rem', fontWeight: '800', color: '#ffffff', marginBottom: '8px' }}>
              Escanea el QR de tu Mesa
            </h2>
            <p style={{ fontSize: '0.84rem', color: '#94a3b8', marginBottom: '20px' }}>
              Apunta la cámara de tu dispositivo hacia el código QR ubicado en el centro o borde de tu mesa.
            </p>

            {error && (
              <div style={{
                background: 'rgba(244, 63, 94, 0.15)',
                border: '1px solid rgba(244, 63, 94, 0.3)',
                color: '#fb7185',
                padding: '10px',
                borderRadius: '12px',
                fontSize: '0.82rem',
                marginBottom: '16px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                justifyContent: 'center',
              }}>
                <AlertCircle size={16} />
                <span>{error}</span>
              </div>
            )}

            {/* Botón principal: Simular Escaneo Instantáneo de la Mesa Activa */}
            <button
              onClick={() => handleValidateQR('aed6f350-c441-40aa-8fd1-2b6c191a549f')}
              disabled={loading}
              className="btn-primary"
              style={{
                width: '100%',
                padding: '14px',
                fontSize: '0.98rem',
                borderRadius: '14px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '10px',
                marginBottom: '12px',
              }}
            >
              <Camera size={20} />
              {loading ? 'Verificando Mesa...' : 'Escanear Código QR'}
            </button>

            {/* Alternar ingreso manual si se desea probar otro código */}
            <button
              type="button"
              onClick={() => setIsManualInput(!isManualInput)}
              style={{
                background: 'none',
                border: 'none',
                color: '#94a3b8',
                fontSize: '0.8rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px',
                margin: '0 auto',
                textDecoration: 'underline',
              }}
            >
              <Keyboard size={14} />
              {isManualInput ? 'Ocultar ingreso manual' : '¿No puedes escanear? Ingresar código'}
            </button>

            {isManualInput && (
              <div style={{ marginTop: '14px', display: 'flex', gap: '8px' }}>
                <input
                  type="text"
                  placeholder="Ej: aed6f350-c441-40aa..."
                  value={qrCodeInput}
                  onChange={(e) => setQrCodeInput(e.target.value)}
                  style={{
                    flex: 1,
                    background: 'rgba(255, 255, 255, 0.05)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    padding: '10px 12px',
                    borderRadius: '10px',
                    color: '#fff',
                    fontSize: '0.84rem',
                  }}
                />
                <button
                  onClick={() => handleValidateQR(qrCodeInput)}
                  className="btn-secondary"
                  style={{ padding: '10px 14px', fontSize: '0.82rem' }}
                >
                  Validar
                </button>
              </div>
            )}
          </div>
        ) : (
          /* PASO 2: SOLICITUD DE NOMBRE TRAS ESCANEAR */
          <div className="glass-panel animate-fade-in" style={{
            background: 'rgba(18, 24, 38, 0.85)',
            border: '1.5px solid #10b981',
            borderRadius: '24px',
            padding: '26px 22px',
            boxShadow: '0 20px 45px rgba(16, 185, 129, 0.2)',
            textAlign: 'center',
          }}>
            <div style={{
              width: '64px',
              height: '64px',
              borderRadius: '50%',
              background: 'rgba(16, 185, 129, 0.15)',
              color: '#34d399',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 14px',
            }}>
              <CheckCircle2 size={36} />
            </div>

            <span className="badge badge-emerald" style={{ marginBottom: '8px' }}>
              Mesa #{scannedTable?.number} Reconocida
            </span>

            <h2 style={{ fontSize: '1.35rem', fontWeight: '800', color: '#ffffff', margin: '8px 0 4px' }}>
              ¿Cómo te llamas?
            </h2>
            <p style={{ fontSize: '0.82rem', color: '#94a3b8', marginBottom: '20px' }}>
              Ingresa tu nombre para personalizar tu servicio y asociar tus pedidos a tu comanda.
            </p>

            <form onSubmit={handleConfirmName} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ position: 'relative' }}>
                <input
                  type="text"
                  autoFocus
                  required
                  placeholder="Tu nombre (Ej: Carlos Pérez)"
                  value={clientName}
                  onChange={(e) => setClientName(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '14px 16px 14px 44px',
                    borderRadius: '14px',
                    background: 'rgba(255, 255, 255, 0.06)',
                    border: '1.5px solid rgba(245, 158, 11, 0.4)',
                    color: '#ffffff',
                    fontSize: '1rem',
                    fontWeight: '600',
                  }}
                />
                <User size={18} color="#f59e0b" style={{ position: 'absolute', left: '16px', top: '16px' }} />
              </div>

              <button
                type="submit"
                className="btn-primary"
                style={{
                  width: '100%',
                  padding: '14px',
                  fontSize: '1rem',
                  borderRadius: '14px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                }}
              >
                <span>Entrar a la Carta</span>
                <ArrowRight size={18} />
              </button>

              <button
                type="button"
                onClick={() => setStep('SCAN')}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#64748b',
                  fontSize: '0.78rem',
                  cursor: 'pointer',
                  marginTop: '4px',
                }}
              >
                Escanear otra mesa
              </button>
            </form>
          </div>
        )}
      </div>

      {/* PARTE INFERIOR: BOTÓN PARA USUARIOS DEL SISTEMA / STAFF LOGIN */}
      <div style={{
        textAlign: 'center',
        paddingTop: '16px',
        borderTop: '1px solid rgba(255, 255, 255, 0.08)',
        zIndex: 2,
      }}>
        <div style={{ fontSize: '0.78rem', color: '#64748b', marginBottom: '8px' }}>
          ¿Eres colaborador o administrador del restaurante?
        </div>
        
        <button
          onClick={onOpenLogin}
          style={{
            background: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid rgba(255, 255, 255, 0.12)',
            borderRadius: '12px',
            color: '#f8fafc',
            padding: '10px 22px',
            fontSize: '0.85rem',
            fontWeight: '700',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)';
            e.currentTarget.style.borderColor = '#f59e0b';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)';
            e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.12)';
          }}
        >
          <LogIn size={16} color="#fbbf24" />
          <span>Acceso para Personal del Sistema (Login)</span>
        </button>
      </div>
    </div>
  );
}
