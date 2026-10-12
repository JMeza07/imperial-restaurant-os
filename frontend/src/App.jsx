import React, { useState, useEffect } from 'react';
import WelcomeScreen from './components/WelcomeScreen';
import ClientMenu from './components/ClientMenu';
import KitchenKDS from './components/KitchenKDS';
import AdminDashboard from './components/AdminDashboard';
import LoginModal from './components/LoginModal';
import ParallaxBackground from './components/ParallaxBackground';
import { ThemeCustomizerProvider } from './utils/ThemeCustomizerContext';
import { api } from './services/api';

export default function App() {
  return (
    <ThemeCustomizerProvider>
      <MainAppContent />
    </ThemeCustomizerProvider>
  );
}

function MainAppContent() {
  // Recuperar sesión activa de mesa persistida para este dispositivo
  const [tableSession, setTableSession] = useState(() => {
    try {
      const saved = localStorage.getItem('imperial_table_session');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  // Vistas: 'WELCOME' | 'MENU' | 'KDS' | 'ADMIN'
  const [currentView, setCurrentView] = useState(() => {
    // Si el dispositivo ya tiene una mesa guardada, ir directo al menú
    try {
      const savedSession = localStorage.getItem('imperial_table_session');
      if (savedSession) {
        const parsed = JSON.parse(savedSession);
        if (parsed?.qrCode) return 'MENU';
      }
    } catch {
      // ignore
    }
    return 'WELCOME';
  });

  const [authToken, setAuthToken] = useState(() => localStorage.getItem('imperial_auth_token') || null);
  const [userRole, setUserRole] = useState(() => localStorage.getItem('imperial_user_role') || null);
  const [currentUserEmail, setCurrentUserEmail] = useState(() => localStorage.getItem('imperial_user_email') || null);
  const [showLoginModal, setShowLoginModal] = useState(false);

  // Sincronizar datos de mesa activa cuando hay sesión persistida
  useEffect(() => {
    const syncSavedTable = async () => {
      if (!tableSession?.qrCode) return;
      try {
        const tData = await api.getTableByQR(tableSession.qrCode);
        if (tData) {
          setTableSession((prev) => ({
            ...prev,
            tableNumber: tData.number,
            customerName: tData.open_order?.customer_name || prev?.customerName,
            tableData: tData,
          }));
        }
      } catch (err) {
        console.warn('Aviso sincronizando mesa:', err);
      }
    };

    if (currentView === 'MENU' && tableSession?.qrCode) {
      syncSavedTable();
    }
  }, [tableSession?.qrCode]);

  // Cuando el comensal escanea el QR e ingresa su nombre
  const handleSelectTable = ({ qrCode, tableNumber, customerName, tableData }) => {
    const sessionData = {
      qrCode,
      tableNumber,
      customerName,
      tableData,
    };
    setTableSession(sessionData);
    try {
      localStorage.setItem('imperial_table_session', JSON.stringify(sessionData));
    } catch (e) {
      console.warn('Error guardando sesion de mesa:', e);
    }
    setCurrentView('MENU');
  };

  // Liberar el dispositivo de la mesa cuando el pago se realiza
  const handleClearTableSession = () => {
    setTableSession(null);
    try {
      localStorage.removeItem('imperial_table_session');
      localStorage.removeItem('imperial_dish_customizations');
      localStorage.removeItem('imperial_active_order');
    } catch (e) {
      // ignore
    }
    setCurrentView('WELCOME');
  };

  // Al iniciar sesión el personal del sistema, se despliega su pantalla según su ROL
  const handleLoginSuccess = (token, role, email) => {
    setAuthToken(token);
    setUserRole(role);
    setCurrentUserEmail(email);

    try {
      localStorage.setItem('imperial_auth_token', token);
      localStorage.setItem('imperial_user_role', role);
      localStorage.setItem('imperial_user_email', email);
    } catch (e) {
      console.warn('Error saving session:', e);
    }

    if (role === 'COCINERO') {
      setCurrentView('KDS'); // Despliega comandas e información de cocina
    } else {
      setCurrentView('ADMIN'); // Despliega el panel administrativo
    }
  };

  const handleLogout = () => {
    setAuthToken(null);
    setUserRole(null);
    setCurrentUserEmail(null);
    try {
      localStorage.removeItem('imperial_auth_token');
      localStorage.removeItem('imperial_user_role');
      localStorage.removeItem('imperial_user_email');
    } catch (e) {
      // ignore
    }
    setCurrentView('WELCOME');
  };

  return (
    <div style={{ minHeight: '100vh', width: '100%', display: 'flex', flexDirection: 'column', position: 'relative' }}>
      {/* Fondo Parallax Inteligente Dinámico */}
      <ParallaxBackground />

      {/* Contenido Dinámico de la Pantalla: Capa superior zIndex 1 */}
      <main style={{ flex: 1, width: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', position: 'relative', zIndex: 1 }}>
        {/* 1. PANTALLA INICIAL: BIENVENIDA, NOMBRE DEL RESTAURANTE Y ESCANEO QR DE LA MESA */}
        {currentView === 'WELCOME' && (
          <WelcomeScreen
            onSelectTable={handleSelectTable}
            onOpenLogin={() => setShowLoginModal(true)}
          />
        )}

        {/* 2. CARTA DIGITAL DEL CLIENTE TRAS ESCANEO Y REGISTRO DE NOMBRE */}
        {currentView === 'MENU' && (
          <ClientMenu 
            initialTableQr={tableSession?.qrCode || 'aed6f350-c441-40aa-8fd1-2b6c191a549f'}
            initialCustomerName={tableSession?.customerName || ''}
            onBackToWelcome={() => setCurrentView('WELCOME')}
            onOpenStaffLogin={() => setShowLoginModal(true)}
            onTableLiberated={handleClearTableSession}
          />
        )}

        {/* 3. VISTA SEGÚN TIPO DE USUARIO: COCINA (KDS) */}
        {currentView === 'KDS' && (
          <KitchenKDS 
            token={authToken}
            userRole={userRole}
            currentUserEmail={currentUserEmail}
            onLogout={handleLogout}
            onNavigate={(view) => setCurrentView(view)} 
          />
        )}

        {/* 4. VISTA SEGÚN TIPO DE USUARIO: ADMINISTRACIÓN */}
        {currentView === 'ADMIN' && (
          <AdminDashboard 
            token={authToken} 
            userRole={userRole}
            currentUserEmail={currentUserEmail}
            onLogout={handleLogout} 
            onNavigate={(view) => setCurrentView(view)} 
          />
        )}
      </main>

      {/* Modal de Inicio de Sesión si es requerido */}
      {showLoginModal && (
        <LoginModal
          onLoginSuccess={handleLoginSuccess}
          onClose={() => setShowLoginModal(false)}
        />
      )}
    </div>
  );
}
