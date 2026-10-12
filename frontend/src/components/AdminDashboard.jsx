import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  UtensilsCrossed, 
  Layers, 
  Package, 
  Plus, 
  Edit3, 
  Trash2, 
  RefreshCw, 
  Check, 
  X, 
  QrCode, 
  Eye, 
  EyeOff, 
  Sparkles, 
  Heart, 
  AlertTriangle,
  DollarSign,
  TrendingUp,
  Save,
  Search,
  CheckCircle2,
  Sliders,
  ShoppingBag,
  Clock,
  ChevronDown,
  ChevronUp,
  Truck,
  Users,
  Award,
  ShieldCheck,
  Box,
  CreditCard,
  Calendar,
  Lock,
  Unlock,
  Activity,
  ArrowLeft,
  ChevronLeft,
  ChevronRight,
  LayoutDashboard,
  Compass,
  Server,
  ExternalLink,
  Settings,
  Image,
  Palette,
  Upload,
  FileText,
  ChefHat
} from 'lucide-react';
import { api } from '../services/api';
import RecipeEditorModal from './RecipeEditorModal';
import ReportsModule from './ReportsModule';
import { useThemeCustomizer } from '../utils/ThemeCustomizerContext';
import { getIngredientIconInfo } from '../utils/ingredientIcons';

export default function AdminDashboard({ token, userRole = 'ADMIN', currentUserEmail = '', onLogout, onNavigate }) {
  // Acceso al personalizador de colores, logotipo y parallax
  const { themeSettings, updateThemeSettings, resetThemeSettings } = useThemeCustomizer();

  // Tabs: 'OVERVIEW' | 'TABLES' | 'DISHES' | 'INGREDIENTS' | 'CASH' | 'DELIVERIES' | 'SHIFTS' | 'COMMISSIONS' | 'INVENTORY' | 'SYSTEM' | 'REPORTS' | 'SETTINGS'
  const [activeTab, setActiveTab] = useState('OVERVIEW');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [dishCarouselIndex, setDishCarouselIndex] = useState(0);

  // Estados de control de acceso por módulos y usuarios
  const [systemUsers, setSystemUsers] = useState([]);
  const [userModulePermissions, setUserModulePermissions] = useState(() => {
    try {
      const saved = localStorage.getItem('imperial_user_module_permissions');
      return saved ? JSON.parse(saved) : {};
    } catch {
      return {};
    }
  });

  // Lista canónica de módulos organizada según el FLUJO OPERACIONAL GASTRONÓMICO
  const ALL_MODULES = [
    // 1. Preparación, Fichas Técnicas & Bodega
    { id: 'KITCHEN', label: 'Cocina & Pantalla KDS', icon: ChefHat, description: 'Comandas activas, tiempos y preparación' },
    { id: 'INGREDIENTS', label: 'Ingredientes & Salud', icon: Heart, description: 'Nutrición, alérgenos y ficha técnica' },
    { id: 'INVENTORY', label: 'Inventario & Stock', icon: Box, description: 'Existencias, entradas y mermas de almacén' },
    { id: 'DISHES', label: 'Carta & Platos', icon: UtensilsCrossed, description: 'Catálogo de platos, recetas y precios' },

    // 2. Operación de Servicio al Cliente & Despachos
    { id: 'TABLES', label: 'Mesas & QR', icon: Layers, description: 'Salón, códigos QR y comandas activas' },
    { id: 'DELIVERIES', label: 'Domicilios', icon: Truck, description: 'Despachos externos y repartidores' },

    // 3. Cierre Financiero & Caja
    { id: 'CASH', label: 'Caja & Arqueo', icon: CreditCard, description: 'Apertura de turno, pagos y cierre de caja' },

    // 4. Gestión del Equipo Humano & Rendimiento
    { id: 'SHIFTS', label: 'Turnos & Personal', icon: Users, description: 'Horarios, colaboradores y asistencia' },
    { id: 'COMMISSIONS', label: 'Comisiones & Propinas', icon: Award, description: 'Distribución de propinas y porcentajes' },

    // 5. Inteligencia de Negocio, Auditoría & Gobernanza
    { id: 'REPORTS', label: 'Reportes & Analítica', icon: BarChart3, description: 'Ventas, encuestas y KPIs (Fase 11)' },
    { id: 'SYSTEM', label: 'Seguridad & Auditoría', icon: ShieldCheck, description: 'Logs inmutables y salud de base de datos' },
    { id: 'SETTINGS', label: 'Configuración General', icon: Settings, description: 'Control total de la app (Solo Admin)' },
  ];

  // Acciones y funciones específicas del Cocinero según el Documento Maestro (RF-07, RN-05, RN-06, Sección 4.7)
  const COCINERO_SPECIFIC_ACTIONS = [
    { id: 'KDS_VIEW_ORDERS', label: 'Consultar comandas en vivo', desc: 'Ver pedidos pendientes RECIBIDO y EN_PREPARACION en pantalla KDS' },
    { id: 'KDS_START_PREP', label: 'Iniciar Preparación', desc: 'Cambiar estado del plato a EN_PREPARACION (RF-07 y RN-06)' },
    { id: 'KDS_MARK_READY', label: 'Marcar Plato Listo', desc: 'Cambiar estado del plato a LISTO para notificar a meseros (RN-05)' },
    { id: 'KDS_BATCH_ACTIONS', label: 'Acciones en Lote', desc: 'Iniciar o finalizar todos los platos de una comanda con un solo clic' },
    { id: 'KDS_DELAY_ALERTS', label: 'Cronómetro & Alertas de Demora', desc: 'Monitoreo de tiempos de cocción y semáforo de retrasos (>15m y >25m)' },
    { id: 'KDS_AUDIO_ALERTS', label: 'Alertas Sonoras de Pedidos', desc: 'Campana acústica automática al ingresar nuevos pedidos a cocina' },
    { id: 'KDS_RECIPE_CONSULT', label: 'Fichas Técnicas & Modificaciones', desc: 'Visualizar ingredientes sin/extra y receta técnica del plato' },
    { id: 'KDS_STOCK_ALERTS', label: 'Disponibilidad de Insumos', desc: 'Ver existencias de insumos y notificar agotamiento en cocina' },
  ];

  // Permisos granulares de acciones por usuario
  const [userActionPermissions, setUserActionPermissions] = useState(() => {
    try {
      const saved = localStorage.getItem('imperial_user_action_permissions');
      return saved ? JSON.parse(saved) : {};
    } catch {
      return {};
    }
  });

  // Helper para verificar si un usuario tiene acceso a un módulo
  const canAccessModule = (moduleId) => {
    // El Administrador SIEMPRE tiene control total de todos los módulos y la configuración
    if (userRole === 'ADMIN' || !userRole) return true;
    
    // Módulo de Configuración está estrictamente reservado para el Administrador
    if (moduleId === 'SETTINGS') return false;

    // Verificar permisos asignados para el usuario actual
    const userPerms = currentUserEmail ? userModulePermissions[currentUserEmail] : null;
    if (userPerms && Array.isArray(userPerms)) {
      return userPerms.includes(moduleId);
    }

    // Permisos por defecto según ROL si aún no se le han asignado individualmente
    if (userRole === 'CAJERO') return ['CASH', 'TABLES', 'DELIVERIES'].includes(moduleId);
    if (userRole === 'MESERO') return ['TABLES', 'DISHES', 'COMMISSIONS'].includes(moduleId);
    if (userRole === 'COCINERO') return ['KITCHEN', 'DISHES', 'INGREDIENTS', 'INVENTORY'].includes(moduleId);
    if (userRole === 'DOMICILIARIO') return ['DELIVERIES'].includes(moduleId);
    if (userRole === 'RRHH') return ['SHIFTS', 'COMMISSIONS'].includes(moduleId);
    if (userRole === 'NUTRICIONISTA') return ['INGREDIENTS', 'DISHES'].includes(moduleId);
    if (userRole === 'AUDITOR') return ['SYSTEM', 'CASH', 'INVENTORY', 'REPORTS'].includes(moduleId);
    if (userRole === 'MANAGER') return ['KITCHEN', 'TABLES', 'DISHES', 'CASH', 'DELIVERIES', 'INVENTORY', 'REPORTS'].includes(moduleId);

    return false;
  };

  // Función para que el Administrador asigne o revoque un módulo a un usuario
  const toggleUserModulePermission = (userEmail, moduleId) => {
    if (userRole !== 'ADMIN') return; // Solo el Administrador puede modificar permisos
    
    setUserModulePermissions((prev) => {
      const currentList = prev[userEmail] || [];
      const updatedList = currentList.includes(moduleId)
        ? currentList.filter((m) => m !== moduleId)
        : [...currentList, moduleId];

      const newPerms = { ...prev, [userEmail]: updatedList };
      try {
        localStorage.setItem('imperial_user_module_permissions', JSON.stringify(newPerms));
      } catch (e) {
        console.error('Error guardando permisos:', e);
      }
      return newPerms;
    });
  };

  // Función para que el Administrador active o desactive acciones funcionales de Cocinero
  const toggleUserActionPermission = (userEmail, actionId) => {
    if (userRole !== 'ADMIN') return;

    setUserActionPermissions((prev) => {
      const currentList = prev[userEmail] !== undefined
        ? prev[userEmail]
        : COCINERO_SPECIFIC_ACTIONS.map(a => a.id); // Todas activas por defecto

      const updatedList = currentList.includes(actionId)
        ? currentList.filter((a) => a !== actionId)
        : [...currentList, actionId];

      const newPerms = { ...prev, [userEmail]: updatedList };
      try {
        localStorage.setItem('imperial_user_action_permissions', JSON.stringify(newPerms));
      } catch (e) {
        console.error('Error guardando permisos de acción:', e);
      }
      return newPerms;
    });
  };

  // Estados de datos
  const [summary, setSummary] = useState(null);
  const [tables, setTables] = useState([]);
  const [dishes, setDishes] = useState([]);
  const [categories, setCategories] = useState([]);
  const [ingredients, setIngredients] = useState([]);
  const [branches, setBranches] = useState([]);
  const [zones, setZones] = useState([]);
  const [activeOrders, setActiveOrders] = useState([]); // Órdenes en tiempo real para salón y mesas
  const [expandedTableOrders, setExpandedTableOrders] = useState({}); // Mapa para colapsar/expandir pedidos por mesa

  // Nuevos módulos maestros
  const [cashSession, setCashSession] = useState(null); // Caja y arqueo
  const [deliveries, setDeliveries] = useState([]); // Domicilios
  const [deliveryZones, setDeliveryZones] = useState([]); // Zonas de delivery
  const [employees, setEmployees] = useState([]); // Personal y RRHH
  const [shifts, setShifts] = useState([]); // Turnos y horarios
  const [shiftTemplates, setShiftTemplates] = useState([]); // Plantillas de turnos
  const [commissionRules, setCommissionRules] = useState([]); // Reglas de comisión
  const [commissionPeriods, setCommissionPeriods] = useState([]); // Liquidaciones
  const [stockItems, setStockItems] = useState([]); // Inventario y stock
  const [systemHealth, setSystemHealth] = useState(null); // Salud del sistema
  const [auditStats, setAuditStats] = useState([]); // Estadísticas de auditoría

  // Formularios rápidos de operaciones
  const [initialCashAmount, setInitialCashAmount] = useState('150000');
  const [stockAdjForm, setStockAdjForm] = useState({ ingredient_id: '', new_quantity: '', reason: 'COMPRA' });

  // Modales y formularios de edición
  const [editingDish, setEditingDish] = useState(null);
  const [showDishModal, setShowDishModal] = useState(false);
  const [recipeModalDish, setRecipeModalDish] = useState(null); // Control de receta por plato
  const [editingTable, setEditingTable] = useState(null);
  const [showTableModal, setShowTableModal] = useState(false);
  const [newCategoryName, setNewCategoryName] = useState('');
  const [showNewCatInput, setShowNewCatInput] = useState(false);

  // Estados de Modales y Configuración solicitados
  const [restaurantProfile, setRestaurantProfile] = useState(null);
  const [settingsSubTab, setSettingsSubTab] = useState('PROFILE'); // 'PROFILE' | 'PERMISSIONS'
  const [configForm, setConfigForm] = useState({
    name: '',
    legal_name: '',
    nit: '',
    address: '',
    phone: '',
    email: '',
    default_tax_rate: '0.08',
    default_tip_rate: '0.10',
    currency: 'COP',
    timezone: 'America/Bogota',
  });
  const [selectedStockIngredient, setSelectedStockIngredient] = useState(null); // Modal de editar/eliminar producto de stock
  const [editingIngredient, setEditingIngredient] = useState(null); // Modal de editar/crear ingrediente
  const [showIngredientModal, setShowIngredientModal] = useState(false);
  const [ingredientForm, setIngredientForm] = useState({
    name: '',
    unit: 'GRAMO',
    price_extra: '0',
    calories: '50',
    protein: '5',
    carbs: '10',
    fat: '2',
    fiber: '1',
    sodium: '20',
    origin: '',
    is_organic: false,
    available: true,
  });
  const [nutritionModalDish, setNutritionModalDish] = useState(null); // Modal informativo de nutrición del plato
  const [selectedTableDetail, setSelectedTableDetail] = useState(null); // Modal de órdenes y valor total de la mesa
  const [tablePaymentMethod, setTablePaymentMethod] = useState('EFECTIVO'); // EFECTIVO, TARJETA, TRANSFERENCIA
  const [isProcessingTablePayment, setIsProcessingTablePayment] = useState(false);
  const [showChargeSection, setShowChargeSection] = useState(false);
  const [dishForm, setDishForm] = useState({
    name: '',
    category_id: '',
    price_base: '',
    short_description: '',
    long_description: '',
    preparation_time_minutes: 15,
    calories_estimate: 400,
    available: true,
    is_featured: false,
  });

  // Formulario nueva/editar mesa
  const [tableForm, setTableForm] = useState({
    number: '',
    capacity: 4,
    branch_id: '',
    zone_id: '',
    status: 'LIBRE',
  });

  const loadAllData = async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const [
        sumData, 
        tabData, 
        dishData, 
        catData, 
        ingData, 
        brData, 
        zData, 
        ordData,
        cashData,
        delivData,
        delivZonesData,
        empData,
        shiftData,
        commRulesData,
        commPeriodsData,
        stockData,
        healthData,
        auditData,
        profileData,
        usersData
      ] = await Promise.all([
        api.getReportsSummary(token).catch(() => null),
        api.listTablesAdmin(token).catch(() => []),
        api.listDishesAdmin(token).catch(() => []),
        api.listCategoriesAdmin(token).catch(() => []),
        api.listIngredientsAdmin(token).catch(() => []),
        api.listBranchesAdmin(token).catch(() => []),
        api.listZonesAdmin(token).catch(() => []),
        api.listOrdersAdmin(token).catch(() => []),
        api.getOpenCashSession(token).catch(() => null),
        api.listDeliveriesAdmin(token).catch(() => []),
        api.listDeliveryZonesAdmin(token).catch(() => []),
        api.listEmployeesAdmin(token).catch(() => []),
        api.listShiftsAdmin(token).catch(() => []),
        api.listCommissionRulesAdmin(token).catch(() => []),
        api.listCommissionPeriodsAdmin(token).catch(() => []),
        api.listStockAdmin(token).catch(() => []),
        api.getSystemHealthAdmin(token).catch(() => null),
        api.getAuditStatsAdmin(token).catch(() => []),
        api.getRestaurantProfile().catch(() => null),
        api.listUsersAdmin(token).catch(() => []),
      ]);

      setSummary(sumData);
      setTables(tabData);
      setDishes(dishData);
      setCategories(catData);
      setIngredients(ingData);
      setBranches(brData);
      setZones(zData);
      setActiveOrders(ordData || []);
      setCashSession(cashData);
      setDeliveries(delivData || []);
      setDeliveryZones(delivZonesData || []);
      setEmployees(empData || []);
      setShifts(shiftData || []);
      setCommissionRules(commRulesData || []);
      setCommissionPeriods(commPeriodsData || []);
      setStockItems(stockData || []);
      setSystemHealth(healthData);
      setAuditStats(auditData || []);
      setSystemUsers(usersData || []);
      if (profileData) {
        setRestaurantProfile(profileData);
        setConfigForm({
          name: profileData.name || '',
          legal_name: profileData.legal_name || '',
          nit: profileData.nit || '',
          address: profileData.address || '',
          phone: profileData.phone || '',
          email: profileData.email || '',
          default_tax_rate: profileData.default_tax_rate || '0.08',
          default_tip_rate: profileData.default_tip_rate || '0.10',
          currency: profileData.currency || 'COP',
          timezone: profileData.timezone || 'America/Bogota',
        });
      }
    } catch (err) {
      console.error(err);
      if (!silent) notify('Error al cargar datos del sistema: ' + err.message, 'error');
    } finally {
      if (!silent) setLoading(false);
    }
  };

  useEffect(() => {
    loadAllData();
    // Polling en tiempo real cada 5 segundos para mantener actualizado los pedidos del salón
    const interval = setInterval(() => {
      loadAllData(true);
    }, 5000);
    return () => clearInterval(interval);
  }, [token]);

  // Rotación automática del carrusel de platos cada 3.5 segundos en la vista principal
  useEffect(() => {
    if (activeTab !== 'OVERVIEW' || dishes.length === 0) return;
    const carouselTimer = setInterval(() => {
      setDishCarouselIndex((prev) => (prev + 1) % dishes.length);
    }, 3500);
    return () => clearInterval(carouselTimer);
  }, [activeTab, dishes.length]);

  const notify = (msg, type = 'success') => {
    setMessage({ text: msg, type });
    setTimeout(() => setMessage(null), 4000);
  };

  // --- Handlers para Platos ---
  const handleOpenDishModal = (dish = null) => {
    if (dish) {
      setEditingDish(dish);
      setDishForm({
        name: dish.name,
        category_id: dish.category_id,
        price_base: dish.price_base,
        short_description: dish.short_description || '',
        long_description: dish.long_description || '',
        preparation_time_minutes: dish.preparation_time_minutes || 15,
        calories_estimate: dish.calories_estimate || 400,
        available: dish.available,
        is_featured: dish.is_featured,
      });
    } else {
      setEditingDish(null);
      setDishForm({
        name: '',
        category_id: categories[0]?.id || '',
        price_base: '25000',
        short_description: '',
        long_description: '',
        preparation_time_minutes: 15,
        calories_estimate: 450,
        available: true,
        is_featured: false,
      });
    }
    setShowDishModal(true);
  };

  const handleSaveDish = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        name: dishForm.name,
        category_id: dishForm.category_id,
        price_base: parseFloat(dishForm.price_base),
        short_description: dishForm.short_description || null,
        long_description: dishForm.long_description || null,
        preparation_time_minutes: parseInt(dishForm.preparation_time_minutes) || 15,
        calories_estimate: dishForm.calories_estimate ? parseFloat(dishForm.calories_estimate) : null,
        available: dishForm.available,
        is_featured: dishForm.is_featured,
      };

      if (editingDish) {
        await api.updateDish(editingDish.id, payload, token);
        notify(`Plato '${dishForm.name}' actualizado exitosamente`);
      } else {
        await api.createDish(payload, token);
        notify(`Plato '${dishForm.name}' creado exitosamente en la carta`);
      }

      setShowDishModal(false);
      await loadAllData();
    } catch (err) {
      notify(err.message, 'error');
    }
  };

  const handleToggleDishAvailability = async (dishId, currentName) => {
    try {
      await api.toggleDishAvailability(dishId, token);
      notify(`Disponibilidad de '${currentName}' actualizada`);
      await loadAllData();
    } catch (err) {
      notify(err.message, 'error');
    }
  };

  // --- Handlers para Mesas & QR ---
  const handleOpenTableModal = (table = null) => {
    if (table) {
      setEditingTable(table);
      setTableForm({
        number: table.number,
        capacity: table.capacity,
        branch_id: table.branch_id,
        zone_id: table.zone_id,
        status: table.status,
      });
    } else {
      setEditingTable(null);
      const nextNum = tables.length > 0 ? Math.max(...tables.map((t) => t.number || 0)) + 1 : 1;
      setTableForm({
        number: nextNum,
        capacity: 4,
        branch_id: branches[0]?.id || '',
        zone_id: zones[0]?.id || '',
        status: 'LIBRE',
      });
    }
    setShowTableModal(true);
  };

  const handleSaveTable = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        number: parseInt(tableForm.number),
        capacity: parseInt(tableForm.capacity),
        branch_id: tableForm.branch_id || branches[0]?.id,
        zone_id: tableForm.zone_id || zones[0]?.id,
      };

      if (editingTable) {
        await api.updateTable(editingTable.id, {
          capacity: payload.capacity,
          status: tableForm.status,
        }, token);
        notify(`Mesa #${tableForm.number} actualizada`);
      } else {
        await api.createTable(payload, token);
        notify(`Nueva Mesa #${tableForm.number} creada con código QR único`);
      }

      setShowTableModal(false);
      await loadAllData();
    } catch (err) {
      notify(err.message, 'error');
    }
  };

  const handleRegenerateQR = async (tableId, tableNum) => {
    if (!confirm(`¿Regenerar el código QR de la Mesa #${tableNum}? El QR anterior dejará de funcionar.`)) return;
    try {
      await api.regenerateQR(tableId, token);
      notify(`Código QR de la Mesa #${tableNum} regenerado exitosamente`);
      await loadAllData();
    } catch (err) {
      notify(err.message, 'error');
    }
  };

  // --- Handlers para Categorías ---
  const handleCreateCategory = async () => {
    if (!newCategoryName.trim()) return;
    try {
      await api.createCategory({ name: newCategoryName.trim(), description: 'Categoría gastronómica' }, token);
      notify(`Categoría '${newCategoryName}' agregada`);
      setNewCategoryName('');
      setShowNewCatInput(false);
      await loadAllData();
    } catch (err) {
      notify(err.message, 'error');
    }
  };

  // --- Handlers para Ingredientes ---
  const handleToggleIngredient = async (ingId, name) => {
    try {
      await api.toggleIngredientAvailability(ingId, token);
      notify(`Disponibilidad de '${name}' modificada`);
      await loadAllData();
    } catch (err) {
      notify(err.message, 'error');
    }
  };

  const handleOpenIngredientModal = (ing = null) => {
    if (ing) {
      setEditingIngredient(ing);
      setIngredientForm({
        name: ing.name || '',
        unit: ing.unit || 'GRAMO',
        price_extra: ing.price_extra ? String(ing.price_extra) : '0',
        calories: ing.calories ? String(ing.calories) : '50',
        protein: ing.protein ? String(ing.protein) : '5',
        carbs: ing.carbs ? String(ing.carbs) : '10',
        fat: ing.fat ? String(ing.fat) : '2',
        fiber: ing.fiber ? String(ing.fiber) : '1',
        sodium: ing.sodium ? String(ing.sodium) : '20',
        origin: ing.origin || '',
        is_organic: !!ing.is_organic,
        available: ing.available !== undefined ? ing.available : true,
      });
    } else {
      setEditingIngredient(null);
      setIngredientForm({
        name: '',
        unit: 'GRAMO',
        price_extra: '0',
        calories: '50',
        protein: '5',
        carbs: '10',
        fat: '2',
        fiber: '1',
        sodium: '20',
        origin: '',
        is_organic: false,
        available: true,
      });
    }
    setShowIngredientModal(true);
  };

  const handleSaveIngredient = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        name: ingredientForm.name.trim(),
        unit: ingredientForm.unit,
        price_extra: parseFloat(ingredientForm.price_extra) || 0,
        calories: parseFloat(ingredientForm.calories) || null,
        protein: parseFloat(ingredientForm.protein) || null,
        carbs: parseFloat(ingredientForm.carbs) || null,
        fat: parseFloat(ingredientForm.fat) || null,
        fiber: parseFloat(ingredientForm.fiber) || null,
        sodium: parseFloat(ingredientForm.sodium) || null,
        origin: ingredientForm.origin || null,
        is_organic: ingredientForm.is_organic,
        available: ingredientForm.available,
      };

      if (editingIngredient) {
        await api.updateIngredient(editingIngredient.id, payload, token);
        notify(`Ingrediente '${payload.name}' actualizado exitosamente`);
      } else {
        await api.createIngredient(payload, token);
        notify(`Ingrediente '${payload.name}' creado exitosamente`);
      }
      setShowIngredientModal(false);
      await loadAllData();
    } catch (err) {
      notify(err.message, 'error');
    }
  };

  const handleDeleteIngredient = async (ing) => {
    if (!confirm(`¿Eliminar o deshabilitar el ingrediente '${ing.name}'? Pasará a estar inactivo en la carta.`)) return;
    try {
      await api.updateIngredient(ing.id, { available: false, name: `[Inactivo] ${ing.name}` }, token);
      notify(`Ingrediente '${ing.name}' retirado del sistema`);
      setShowIngredientModal(false);
      await loadAllData();
    } catch (err) {
      notify(err.message, 'error');
    }
  };

  // --- Handlers para Stock e Inventario ---
  const handleSaveStockItem = async (e) => {
    e.preventDefault();
    if (!selectedStockIngredient) return;
    try {
      const stockId = selectedStockIngredient.stock_id;
      const ingId = selectedStockIngredient.id;
      const newQty = parseFloat(selectedStockIngredient.edit_current_stock);
      const newMin = parseFloat(selectedStockIngredient.edit_min_stock);

      if (stockId) {
        await api.updateStockItem(stockId, { min_stock: newMin }, token);
      }
      if (!isNaN(newQty)) {
        await api.createStockAdjustment({
          ingredient_id: ingId,
          branch_id: branches[0]?.id || null,
          quantity: newQty,
          reason: 'AJUSTE_MANUAL',
          notes: 'Ajuste directo desde panel de stock',
        }, token);
      }
      notify(`Stock de '${selectedStockIngredient.name}' actualizado`);
      setSelectedStockIngredient(null);
      await loadAllData();
    } catch (err) {
      notify(err.message, 'error');
    }
  };

  const handleDeleteStockItem = async (ing) => {
    if (!confirm(`¿Poner a cero o retirar de stock el ingrediente '${ing.name}'?`)) return;
    try {
      await api.createStockAdjustment({
        ingredient_id: ing.id,
        branch_id: branches[0]?.id || null,
        quantity: 0,
        reason: 'MERMA_RETIRO',
        notes: 'Stock puesto a cero desde panel administrativo',
      }, token);
      notify(`Stock de '${ing.name}' puesto en 0`);
      setSelectedStockIngredient(null);
      await loadAllData();
    } catch (err) {
      notify(err.message, 'error');
    }
  };


  return (
    <div 
      className="admin-dashboard-container animate-fade-in"
    >
      {/* Top Banner de Navegación & Acciones Rápidas: Solo se muestra al acceder a los módulos de trabajo */}
      {activeTab !== 'OVERVIEW' && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '16px',
          marginBottom: '20px',
          paddingBottom: '16px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          flexShrink: 0,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            {themeSettings?.logoUrl ? (
              <img
                src={themeSettings.logoUrl}
                alt="Logo Restaurante"
                style={{ maxHeight: '42px', maxWidth: '120px', objectFit: 'contain', borderRadius: '8px' }}
              />
            ) : (
              <div style={{
                background: 'var(--gold-gradient)',
                color: '#000',
                width: '42px',
                height: '42px',
                borderRadius: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}>
                <BarChart3 size={24} />
              </div>
            )}
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h1 style={{ fontSize: '1.45rem', fontWeight: '800', color: '#f8fafc', margin: 0 }}>
                  Panel de Administración & Control
                </h1>
                <span className="badge badge-gold">Modo Edición Activo</span>
              </div>
              <p style={{ color: '#94a3b8', fontSize: '0.82rem', margin: 0 }}>
                Gestión total de la Carta, Mesas QR, Disponibilidad en Cocina e Inventario
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            {onNavigate && (
              <div style={{ display: 'flex', gap: '6px' }}>
                <button
                  onClick={() => onNavigate('MENU')}
                  className="btn-secondary"
                  style={{ padding: '8px 12px', fontSize: '0.82rem', display: 'flex', alignItems: 'center', gap: '6px' }}
                  title="Ver Carta Digital QR"
                >
                  <QrCode size={15} />
                  <span>Carta QR</span>
                </button>
                <button
                  onClick={() => onNavigate('KDS')}
                  className="btn-secondary"
                  style={{ padding: '8px 12px', fontSize: '0.82rem', display: 'flex', alignItems: 'center', gap: '6px' }}
                  title="Ver Cocina KDS"
                >
                  <UtensilsCrossed size={15} />
                  <span>Cocina KDS</span>
                </button>
              </div>
            )}

            <button
              onClick={() => setActiveTab('OVERVIEW')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 14px',
                borderRadius: '8px',
                background: 'rgba(56, 189, 248, 0.15)',
                color: '#38bdf8',
                border: '1px solid rgba(56, 189, 248, 0.35)',
                fontSize: '0.85rem',
                fontWeight: '700',
                cursor: 'pointer',
              }}
            >
              <LayoutDashboard size={15} />
              Hub Principal
            </button>
            <button onClick={loadAllData} className="btn-secondary" style={{ padding: '8px 14px', fontSize: '0.85rem' }}>
              <RefreshCw size={15} />
              Recargar
            </button>
            <button
              onClick={onLogout}
              style={{
                padding: '8px 14px',
                borderRadius: '8px',
                background: 'rgba(244, 63, 94, 0.12)',
                color: '#fb7185',
                border: '1px solid rgba(244, 63, 94, 0.25)',
                fontSize: '0.85rem',
                fontWeight: '600',
              }}
            >
              Cerrar Sesión
            </button>
          </div>
        </div>
      )}

      {/* Notificación Flotante */}
      {message && (
        <div style={{
          padding: '12px 20px',
          borderRadius: '12px',
          background: message.type === 'error' ? 'rgba(244, 63, 94, 0.15)' : 'rgba(16, 185, 129, 0.15)',
          border: `1px solid ${message.type === 'error' ? 'rgba(244, 63, 94, 0.4)' : 'rgba(16, 185, 129, 0.4)'}`,
          color: message.type === 'error' ? '#fb7185' : '#34d399',
          marginBottom: '20px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          fontWeight: '600',
        }}>
          {message.type === 'error' ? <AlertTriangle size={18} /> : <CheckCircle2 size={18} />}
          {message.text}
        </div>
      )}

      {/* CONDICIONAL DE NAVEGACIÓN:
          - Si activeTab === 'OVERVIEW': Muestra la pantalla de la IMAGEN 1 (Carrusel central de platos, KPIs a la derecha, 4 tarjetas de módulos por fila abajo)
          - Si activeTab !== 'OVERVIEW': Muestra la vista detallada de la IMAGEN 2 (Barra lateral de módulos a la izquierda, contenido extendido a la derecha) */}

      {activeTab === 'OVERVIEW' ? (
        /* =========================================================================
           VISTA IMAGEN 1: HUB PRINCIPAL DEL RESTAURANTE
           - Centro-Izquierda: Hero carrusel de fotos de platos (solo imagen).
           - Derecha: Tarjetas de KPIs informativos en fondo traslúcido.
           - Abajo: Cuadrícula de módulos en distribución de 4 tarjetas por fila.
           ========================================================================= */
        <div 
          className="animate-fade-in custom-scroll" 
          style={{ 
            display: 'flex', 
            flexDirection: 'column', 
            gap: '16px',
            flex: 1,
            minHeight: 0,
            overflowY: 'auto',
            paddingRight: '6px',
          }}
        >
          
          {/* SECCIÓN SUPERIOR: CARRUSEL CENTRAL DE FOTOS (IZQ) + KPIS INFORMATIVOS (DER) */}
          <div className="admin-overview-hero">
            {/* HERO CARRUSEL CENTRAL (3D FLOATING PRODUCT CARD HERO) */}
            <div 
              className="card-3d"
              style={{
                borderRadius: '24px',
                position: 'relative',
                minHeight: '380px',
                height: '420px',
              }}
              onPointerMove={(e) => {
                const rect = e.currentTarget.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                const rotateY = ((x / rect.width) - 0.5) * 6;
                const rotateX = ((y / rect.height) - 0.5) * -6;
                const inner = e.currentTarget.querySelector('.card-3d-inner');
                if (inner) {
                  inner.style.transform = `translateY(-4px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
                }
              }}
              onPointerLeave={(e) => {
                const inner = e.currentTarget.querySelector('.card-3d-inner');
                if (inner) {
                  inner.style.transform = 'translateY(0) rotateX(0) rotateY(0)';
                }
              }}
            >
              <div 
                className="card-3d-inner"
                style={{
                  width: '100%',
                  height: '100%',
                  borderRadius: '24px',
                  position: 'relative',
                  overflow: 'hidden',
                  boxShadow: '0 20px 50px rgba(0, 0, 0, 0.6), inset 0 1px 2px rgba(255, 255, 255, 0.1)',
                  border: '1.5px solid rgba(242, 178, 62, 0.35)',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  background: 'var(--surface-strong)',
                }}
              >
                {/* IMAGEN DE FONDO QUE SE ESCALA Y RELLENA TODO EL RECUADRO */}
                <div style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: '100%',
                  zIndex: 1,
                }}>
                {dishes.length > 0 ? (
                  <img
                    key={dishes[dishCarouselIndex]?.id || dishCarouselIndex}
                    src={dishes[dishCarouselIndex]?.image_url || "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=1200&q=80"}
                    alt={dishes[dishCarouselIndex]?.name || "Plato Gourmet"}
                    style={{
                      width: '100%',
                      height: '100%',
                      objectFit: 'cover', // Se escala y rellena completamente todo el recuadro
                      display: 'block',
                      transition: 'all 0.5s ease',
                    }}
                  />
                ) : (
                  <img
                    src="https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=1200&q=80"
                    alt="Hamburguesa Gourmet"
                    style={{
                      width: '100%',
                      height: '100%',
                      objectFit: 'cover',
                      display: 'block',
                    }}
                  />
                )}
                {/* Degradado para garantizar legibilidad de controles y títulos */}
                <div style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  background: 'linear-gradient(180deg, rgba(13, 19, 31, 0.7) 0%, rgba(13, 19, 31, 0.1) 40%, rgba(13, 19, 31, 0.8) 100%)',
                  pointerEvents: 'none',
                }} />
              </div>

              {/* Título decorativo superior estilizado como Imagen 1 */}
              <div style={{
                position: 'relative',
                zIndex: 10,
                padding: '20px 24px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{
                    fontSize: '1.05rem',
                    fontWeight: '800',
                    letterSpacing: '0.05em',
                    color: '#ffffff',
                    textTransform: 'uppercase',
                    textShadow: '0 2px 8px rgba(0, 0, 0, 0.9)',
                  }}>
                    {dishes[dishCarouselIndex]?.name || 'Imperial Dishes Gallery'}
                  </span>
                  <span className="badge badge-gold" style={{ fontSize: '0.72rem', padding: '3px 8px', boxShadow: '0 2px 6px rgba(0,0,0,0.5)' }}>
                    {dishes.length > 0 ? `${dishCarouselIndex + 1}/${dishes.length}` : '1/1'}
                  </span>
                </div>
              </div>

              {/* Botones de control del carrusel CENTRADOS HORIZONTALMENTE */}
              <div style={{
                position: 'absolute',
                bottom: '20px',
                left: '50%',
                transform: 'translateX(-50%)',
                display: 'flex',
                alignItems: 'center',
                gap: '14px',
                zIndex: 10,
                background: 'rgba(13, 19, 31, 0.65)',
                backdropFilter: 'blur(8px)',
                padding: '6px 14px',
                borderRadius: '30px',
                border: '1px solid rgba(255, 255, 255, 0.1)',
              }}>
                <button
                  onClick={() => setDishCarouselIndex((prev) => (prev - 1 + (dishes.length || 1)) % (dishes.length || 1))}
                  style={{
                    background: 'rgba(255, 255, 255, 0.12)',
                    border: '1px solid rgba(255, 255, 255, 0.25)',
                    borderRadius: '50%',
                    width: '32px',
                    height: '32px',
                    color: '#fff',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: 'pointer',
                    transition: 'background 0.2s ease',
                  }}
                  title="Plato anterior"
                >
                  <ChevronLeft size={16} />
                </button>

                <div style={{ display: 'flex', gap: '6px' }}>
                  {dishes.slice(0, 7).map((_, dotIdx) => (
                    <div
                      key={dotIdx}
                      onClick={() => setDishCarouselIndex(dotIdx)}
                      style={{
                        width: dishCarouselIndex === dotIdx ? '22px' : '8px',
                        height: '8px',
                        borderRadius: '4px',
                        background: dishCarouselIndex === dotIdx ? '#38bdf8' : 'rgba(255, 255, 255, 0.3)',
                        cursor: 'pointer',
                        transition: 'all 0.3s ease',
                      }}
                    />
                  ))}
                </div>

                <button
                  onClick={() => setDishCarouselIndex((prev) => (prev + 1) % (dishes.length || 1))}
                  style={{
                    background: 'rgba(255, 255, 255, 0.12)',
                    border: '1px solid rgba(255, 255, 255, 0.25)',
                    borderRadius: '50%',
                    width: '32px',
                    height: '32px',
                    color: '#fff',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: 'pointer',
                    transition: 'background 0.2s ease',
                  }}
                  title="Siguiente plato"
                >
                  <ChevronRight size={16} />
                </button>
              </div>
            </div>
          </div>

          {/* TARJETAS DE LA DERECHA: KPIS INFORMATIVOS (ESTILO EXACTO IMAGEN 1) */}
          <div className="admin-kpis-grid">
            {[
              {
                id: 'sales',
                title: 'Ventas Brutas',
                icon: DollarSign,
                iconColor: 'var(--blue)',
                value: `$${parseFloat(summary?.total_sales || 44000).toLocaleString('es-CO')}`,
                sub: '↑ 18.5% vs ayer',
                subColor: 'var(--jade)',
                valColor: '#f8fafc',
              },
              {
                id: 'occupancy',
                title: 'Ocupación Salón',
                icon: Layers,
                iconColor: 'var(--gold)',
                value: `${tables.filter((t) => t.status === 'OCUPADA').length} / ${tables.length}`,
                sub: `${tables.filter((t) => t.status === 'LIBRE').length} mesas disponibles`,
                subColor: '#cbd5e1',
                valColor: 'var(--gold)',
              },
              {
                id: 'kds',
                title: 'Cocina KDS',
                icon: Clock,
                iconColor: 'var(--red)',
                value: activeOrders.reduce((acc, o) => acc + (o.items?.filter((i) => i.status !== 'ENTREGADO').length || 0), 0),
                sub: 'Platos en fogón activo',
                subColor: '#fda4af',
                valColor: '#fb7185',
              },
              {
                id: 'cash',
                title: 'Estado Caja',
                icon: CreditCard,
                iconColor: cashSession ? 'var(--jade)' : 'var(--red)',
                value: cashSession ? 'Abierta' : 'Cerrada',
                sub: `Base: $${parseFloat(cashSession?.initial_cash_amount || 0).toLocaleString('es-CO')}`,
                subColor: '#cbd5e1',
                valColor: cashSession ? 'var(--jade)' : 'var(--red)',
              },
              {
                id: 'deliveries',
                title: 'Domicilios',
                icon: Truck,
                iconColor: 'var(--blue)',
                value: deliveries.length,
                sub: `${deliveries.filter((d) => d.status === 'EN_CAMINO').length} en camino`,
                subColor: '#cbd5e1',
                valColor: 'var(--blue)',
              },
              {
                id: 'security',
                title: 'Seguridad',
                icon: ShieldCheck,
                iconColor: 'var(--jade)',
                value: '100% Protegido',
                sub: 'PostgreSQL + Redis ACID',
                subColor: '#cbd5e1',
                valColor: 'var(--jade)',
              },
            ].map((kpi) => {
              const KpiIcon = kpi.icon;
              return (
                <div
                  key={kpi.id}
                  className="glow-card"
                  style={{
                    padding: '16px',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    borderRadius: '18px',
                    background: 'linear-gradient(135deg, rgba(15, 20, 30, 0.75) 0%, rgba(7, 10, 15, 0.95) 100%)',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                  }}
                  onPointerMove={(e) => {
                    const rect = e.currentTarget.getBoundingClientRect();
                    e.currentTarget.style.setProperty('--x', `${e.clientX - rect.left}px`);
                    e.currentTarget.style.setProperty('--y', `${e.clientY - rect.top}px`);
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', position: 'relative', zIndex: 3 }}>
                    <span style={{ fontSize: '0.74rem', color: '#9aa5b1', fontWeight: '800', textTransform: 'uppercase' }}>
                      {kpi.title}
                    </span>
                    <KpiIcon size={16} color={kpi.iconColor} />
                  </div>
                  <div style={{ position: 'relative', zIndex: 3 }}>
                    <div style={{ fontSize: '1.45rem', fontWeight: '800', color: kpi.valColor || '#f8fafc' }}>
                      {kpi.value}
                    </div>
                    <div style={{ fontSize: '0.72rem', color: kpi.subColor, marginTop: '2px', fontWeight: '600' }}>
                      {kpi.sub}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
          </div>

          {/* =========================================================================
              SECCIÓN INFERIOR: DISTRIBUCIÓN DE MÓDULOS DEL SISTEMA
              Exactamente 4 tarjetas por fila, con diseño rectangular idéntico a Imagen 1
              Al hacer click en cualquier tarjeta, el sistema se despliega como IMAGEN 2.
              ========================================================================= */}
          <div>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '10px',
            }}>
              <h3 style={{ fontSize: '1.15rem', fontWeight: '800', color: '#f8fafc', letterSpacing: '-0.01em', margin: 0 }}>
                Módulos del Sistema Operativo Gastronómico
              </h3>
              <span style={{ fontSize: '0.78rem', color: '#94a3b8' }}>
                Selecciona cualquier módulo para abrir la vista de trabajo detallada
              </span>
            </div>

            <div className="admin-modules-grid">
              {[
                // 1. INSUMOS, BODEGA & CARTA
                {
                  id: 'KITCHEN',
                  title: 'Cocina & Pantalla KDS',
                  subtitle: 'Comandas en Vivo & Despacho',
                  icon: ChefHat,
                  image: "https://images.unsplash.com/photo-1556910103-1c02745aae4d?auto=format&fit=crop&w=400&q=80",
                  tag: 'Tiempo Real',
                  color: '#f97316'
                },
                {
                  id: 'INGREDIENTS',
                  title: 'Ingredientes & Salud',
                  subtitle: `${ingredients.length} Ingredientes & Nutrientes`,
                  icon: Heart,
                  image: "https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=400&q=80",
                  tag: 'Alérgenos & Cal.',
                  color: '#10b981'
                },
                {
                  id: 'INVENTORY',
                  title: 'Inventario & Stock',
                  subtitle: `${stockItems.length || ingredients.length} Insumos Registrados`,
                  icon: Box,
                  image: "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?auto=format&fit=crop&w=400&q=80",
                  tag: 'Mermas & Alertas',
                  color: '#ec4899'
                },
                {
                  id: 'DISHES',
                  title: 'Carta, Platos & Recetas',
                  subtitle: `${dishes.length} Platos en Menú`,
                  icon: UtensilsCrossed,
                  image: "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=400&q=80",
                  tag: 'Precios & Extras',
                  color: '#f59e0b'
                },

                // 2. ATENCIÓN AL COMENSAL & DESPACHOS
                {
                  id: 'TABLES',
                  title: 'Mesas del Salón & Códigos QR',
                  subtitle: `${tables.length} Mesas & Comandas en Vivo`,
                  icon: Layers,
                  image: "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=400&q=80",
                  tag: `${tables.filter((t) => t.status === 'OCUPADA').length} Ocupadas`,
                  color: '#38bdf8'
                },
                {
                  id: 'DELIVERIES',
                  title: 'Control de Domicilios',
                  subtitle: `${deliveries.length} Despachos Registrados`,
                  icon: Truck,
                  image: "https://images.unsplash.com/photo-1526367790999-0150786686a2?auto=format&fit=crop&w=400&q=80",
                  tag: `${deliveryZones.length} Zonas`,
                  color: '#0284c7'
                },

                // 3. FACTURACIÓN & CAJA
                {
                  id: 'CASH',
                  title: 'Caja & Arqueo Contable',
                  subtitle: cashSession ? 'Sesión Abierta' : 'Caja Cerrada',
                  icon: CreditCard,
                  image: "https://images.unsplash.com/photo-1559526324-4b87b5e36e44?auto=format&fit=crop&w=400&q=80",
                  tag: 'Turnos & Pagos',
                  color: '#6366f1'
                },

                // 4. GESTIÓN HUMANA & RETRIBUCIÓN
                {
                  id: 'SHIFTS',
                  title: 'Turnos & Personal RRHH',
                  subtitle: `${employees.length} Colaboradores`,
                  icon: Users,
                  image: "https://images.unsplash.com/photo-1556910103-1c02745aae4d?auto=format&fit=crop&w=400&q=80",
                  tag: 'Control Asistencia',
                  color: '#8b5cf6'
                },
                {
                  id: 'COMMISSIONS',
                  title: 'Comisiones & Propinas',
                  subtitle: `${commissionRules.length} Reglas & Liquidaciones`,
                  icon: Award,
                  image: "https://images.unsplash.com/photo-1559847844-5315695dadae?auto=format&fit=crop&w=400&q=80",
                  tag: 'Meseros & Ventas',
                  color: '#eab308'
                },

                // 5. INTELIGENCIA, AUDITORÍA & AJUSTES
                {
                  id: 'REPORTS',
                  title: 'Reportes & Analítica',
                  subtitle: 'Ventas, KPIs, Encuestas & Personal',
                  icon: BarChart3,
                  image: "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=400&q=80",
                  tag: 'Fase 11 TCC',
                  color: '#f59e0b'
                },
                {
                  id: 'SYSTEM',
                  title: 'Seguridad & Auditoría',
                  subtitle: 'Logs Inmutables & Salud DB',
                  icon: ShieldCheck,
                  image: "https://images.unsplash.com/photo-1563986768609-322da13575f3?auto=format&fit=crop&w=400&q=80",
                  tag: 'PostgreSQL + Redis',
                  color: '#14b8a6'
                },
                {
                  id: 'SETTINGS',
                  title: 'Configuración General',
                  subtitle: 'Restaurante, Moneda & Políticas',
                  icon: Settings,
                  image: "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=400&q=80",
                  tag: 'Perfil & Impuestos',
                  color: '#06b6d4'
                },
              ].filter((mod) => canAccessModule(mod.id)).map((mod) => {
                const ModIcon = mod.icon;
                return (
                  <div
                    key={mod.id}
                    onClick={() => {
                      if (mod.id === 'KITCHEN' && onNavigate) {
                        onNavigate('KDS');
                      } else {
                        setActiveTab(mod.id);
                      }
                    }}
                    className="stripe-card"
                    style={{
                      background: 'linear-gradient(180deg, rgba(15, 20, 30, 0.75) 0%, rgba(7, 10, 15, 0.95) 100%)',
                      border: '1px solid rgba(255, 255, 255, 0.08)',
                      borderRadius: '18px',
                      overflow: 'hidden',
                      cursor: 'pointer',
                      display: 'flex',
                      flexDirection: 'column',
                    }}
                  >
                    {/* Imagen superior rectangular representativa */}
                    <div style={{ position: 'relative', width: '100%', height: '88px', overflow: 'hidden' }}>
                      <img
                        src={mod.image}
                        alt={mod.title}
                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      />
                      <div style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        right: 0,
                        bottom: 0,
                        background: 'linear-gradient(180deg, transparent 40%, rgba(13, 19, 31, 0.95) 100%)',
                      }} />
                      <div style={{
                        position: 'absolute',
                        top: '8px',
                        right: '8px',
                        background: 'rgba(0, 0, 0, 0.65)',
                        backdropFilter: 'blur(4px)',
                        padding: '2px 7px',
                        borderRadius: '6px',
                        fontSize: '0.66rem',
                        fontWeight: '700',
                        color: mod.color,
                        border: `1px solid ${mod.color}40`,
                      }}>
                        {mod.tag}
                      </div>
                    </div>

                    {/* Contenido inferior de la tarjeta */}
                    <div style={{ padding: '10px 12px', flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                          <div style={{
                            width: '26px',
                            height: '26px',
                            borderRadius: '7px',
                            background: `${mod.color}20`,
                            color: mod.color,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            flexShrink: 0,
                          }}>
                            <ModIcon size={14} />
                          </div>
                          <div style={{
                            fontWeight: '800',
                            fontSize: '0.88rem',
                            color: '#f8fafc',
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                          }}>
                            {mod.title}
                          </div>
                        </div>
                        <div style={{ fontSize: '0.74rem', color: '#94a3b8', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                          {mod.subtitle}
                        </div>
                      </div>

                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        marginTop: '8px',
                        paddingTop: '6px',
                        borderTop: '1px solid rgba(255, 255, 255, 0.06)',
                        fontSize: '0.72rem',
                        fontWeight: '700',
                        color: '#38bdf8',
                      }}>
                        <span>Abrir módulo</span>
                        <ChevronRight size={13} />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      ) : (
        /* =========================================================================
           VISTA IMAGEN 2: LAYOUT DE TRABAJO EXPANDIDO
           - Izquierda: Barra vertical con todos los módulos accesibles (estilo panel Imagen 2).
           - Derecha: Contenido completo del módulo seleccionado ocupando el resto de la ventana.
           - Botón para volver al Hub Principal (Imagen 1).
           ========================================================================= */
        <div className="admin-detailed-layout animate-fade-in">
          {/* SIDEBAR LATERAL IZQUIERDO (IDÉNTICO A LA IMAGEN 2) */}
          <div 
            className="custom-scroll"
            style={{
              background: 'linear-gradient(180deg, #161c28 0%, #0d131f 100%)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: '20px',
              padding: '18px 16px',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px',
              boxShadow: '0 10px 30px rgba(0, 0, 0, 0.5)',
              height: '100%',
              minHeight: 0,
              overflowY: 'auto', // Permite scroll suave en la lista de módulos
              justifyContent: 'flex-start',
            }}
          >
            {/* Botón Volver al Hub General (Imagen 1) */}
            <button
              onClick={() => setActiveTab('OVERVIEW')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: '14px 16px',
                borderRadius: '14px',
                background: 'rgba(56, 189, 248, 0.12)',
                color: '#38bdf8',
                border: '1px solid rgba(56, 189, 248, 0.3)',
                fontWeight: '800',
                fontSize: '0.92rem',
                cursor: 'pointer',
                marginBottom: '10px',
                boxShadow: '0 4px 14px rgba(56, 189, 248, 0.15)',
              }}
            >
              <LayoutDashboard size={18} />
              <span>← Menú Principal</span>
            </button>

            <div style={{ fontSize: '0.74rem', color: '#64748b', fontWeight: '800', textTransform: 'uppercase', padding: '6px 10px', letterSpacing: '0.05em' }}>
              Módulos del Sistema
            </div>

            <div style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '6px',
              flex: 1, // Permite expandirse a lo largo del sidebar
            }}>
              {[
                // 1. Cocina, Insumos & Catálogo
                { id: 'KITCHEN', label: 'Cocina KDS', icon: ChefHat, count: 'En vivo' },
                { id: 'INGREDIENTS', label: 'Ingredientes', icon: Heart, count: ingredients.length },
                { id: 'INVENTORY', label: 'Inventario', icon: Box, count: stockItems.length || ingredients.length },
                { id: 'DISHES', label: 'Platos & Carta', icon: UtensilsCrossed, count: dishes.length },

                // 2. Operación y Servicio en Vivo
                { id: 'TABLES', label: 'Mesas & Salón', icon: Layers, count: tables.length },
                { id: 'DELIVERIES', label: 'Domicilios', icon: Truck, count: deliveries.length },

                // 3. Finanzas & Facturación
                { id: 'CASH', label: 'Caja & Arqueo', icon: CreditCard, count: cashSession ? 'Abierta' : 'Cerrada' },

                // 4. Equipo & Liquidaciones
                { id: 'SHIFTS', label: 'Turnos Personal', icon: Users, count: employees.length },
                { id: 'COMMISSIONS', label: 'Comisiones', icon: Award, count: commissionRules.length },

                // 5. Inteligencia, Seguridad & Sistema
                { id: 'REPORTS', label: 'Reportes & BI', icon: BarChart3, count: 'BI' },
                { id: 'SYSTEM', label: 'Seguridad DB', icon: ShieldCheck },
                { id: 'SETTINGS', label: 'Configuración', icon: Settings, count: 'Ajustes' },
              ].filter((mod) => canAccessModule(mod.id)).map((mod) => {
                const Icon = mod.icon;
                const isSelected = activeTab === mod.id;

                return (
                  <button
                    key={mod.id}
                    onClick={() => {
                      if (mod.id === 'KITCHEN' && onNavigate) {
                        onNavigate('KDS');
                      } else {
                        setActiveTab(mod.id);
                      }
                    }}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '0 14px',
                      height: '48px', // Mismo alto exacto para todos los botones
                      minHeight: '48px',
                      maxHeight: '48px',
                      borderRadius: '12px',
                      fontSize: '0.88rem',
                      fontWeight: isSelected ? '800' : '600',
                      background: isSelected ? 'var(--gold-gradient)' : 'transparent',
                      color: isSelected ? '#000' : '#cbd5e1',
                      border: isSelected ? 'none' : '1px solid transparent',
                      cursor: 'pointer',
                      transition: 'all 0.18s ease',
                      flexShrink: 0,
                      boxSizing: 'border-box',
                    }}
                    onMouseEnter={(e) => {
                      if (!isSelected) {
                        e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)';
                        e.currentTarget.style.color = '#fff';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!isSelected) {
                        e.currentTarget.style.background = 'transparent';
                        e.currentTarget.style.color = '#cbd5e1';
                      }
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', overflow: 'hidden' }}>
                      <Icon size={18} style={{ flexShrink: 0 }} />
                      <span style={{
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                      }}>
                        {mod.label}
                      </span>
                    </div>
                    {mod.count !== undefined && (
                      <span style={{
                        fontSize: '0.72rem',
                        padding: '3px 7px',
                        borderRadius: '6px',
                        background: isSelected ? 'rgba(0, 0, 0, 0.2)' : 'rgba(255, 255, 255, 0.08)',
                        color: isSelected ? '#000' : '#94a3b8',
                        fontWeight: '700',
                        flexShrink: 0,
                        marginLeft: '8px',
                      }}>
                        {mod.count}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {/* ÁREA DE CONTENIDO PRINCIPAL: OCUPA EL RESTO DE LA VENTANA */}
          <div 
            className="custom-scroll"
            style={{
              background: '#0d131f',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: '20px',
              padding: '20px 24px',
              boxShadow: '0 10px 40px rgba(0, 0, 0, 0.5)',
              height: '100%',
              minHeight: 0,
              overflowY: 'auto', // Barra lateral de desplazamiento para explorar todo el contenido
            }}
          >

      {/* --- TAB: COCINA & PANTALLA KDS (REDIRECCIÓN O ACCESO DIRECTO) --- */}
      {activeTab === 'KITCHEN' && (
        <div className="animate-fade-in" style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '40px 20px',
          textAlign: 'center',
          gap: '16px',
        }}>
          <div style={{
            width: '80px',
            height: '80px',
            borderRadius: '24px',
            background: 'rgba(249, 115, 22, 0.15)',
            border: '1.5px solid rgba(249, 115, 22, 0.35)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#f97316',
          }}>
            <ChefHat size={44} />
          </div>
          <div>
            <h2 style={{ fontSize: '1.4rem', color: '#f8fafc', fontWeight: '800', marginBottom: '6px' }}>
              Módulo de Cocina & Pantalla KDS en Tiempo Real
            </h2>
            <p style={{ color: '#94a3b8', fontSize: '0.9rem', maxWidth: '520px', margin: '0 auto', lineHeight: '1.5' }}>
              Visualiza pedidos activos, transiciones de comandas (RECIBIDO → EN_PREPARACION → LISTO), control de mermas y tiempos de despacho en la interfaz optimizada de cocina.
            </p>
          </div>
          <button
            onClick={() => onNavigate && onNavigate('KDS')}
            style={{
              marginTop: '10px',
              padding: '14px 28px',
              borderRadius: '14px',
              background: 'linear-gradient(135deg, #f97316 0%, #ea580c 100%)',
              color: '#fff',
              fontWeight: '900',
              fontSize: '1rem',
              border: 'none',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              boxShadow: '0 8px 24px rgba(249, 115, 22, 0.35)',
              transition: 'all 0.2s ease',
            }}
          >
            <ChefHat size={20} />
            <span>Abrir Pantalla Completa KDS</span>
            <ExternalLink size={18} />
          </button>
        </div>
      )}

      {/* --- TAB 2: GESTIÓN DE PLATOS DE LA CARTA --- */}
      {activeTab === 'DISHES' && (
        <div className="animate-fade-in">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <h2 style={{ fontSize: '1.3rem', color: '#f8fafc', fontWeight: '700' }}>
                Catálogo de Platos
              </h2>
              <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
                Edita precios, tiempos y visibilidad pública en la Carta Digital
              </p>
            </div>
            <button onClick={() => handleOpenDishModal()} className="btn-primary" style={{ padding: '10px 18px', fontSize: '0.9rem' }}>
              <Plus size={18} />
              Crear Nuevo Plato
            </button>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))',
            gap: '20px',
          }}>
            {dishes.map((dish) => {
              const isAvailable = dish.available;
              return (
                <div
                  key={dish.id}
                  className="glass-panel"
                  style={{
                    padding: '20px',
                    borderRadius: '16px',
                    border: isAvailable ? '1px solid rgba(255, 255, 255, 0.08)' : '1px solid rgba(244, 63, 94, 0.3)',
                    background: isAvailable ? '#0d131f' : 'rgba(244, 63, 94, 0.04)',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                      <span className="badge badge-gold" style={{ fontSize: '0.85rem' }}>
                        ${parseFloat(dish.price_base).toLocaleString('es-CO')}
                      </span>
                      <div style={{ display: 'flex', gap: '6px' }}>
                        {dish.is_featured && <span className="badge badge-emerald">Destacado</span>}
                        <span className={`badge ${isAvailable ? 'badge-emerald' : 'badge-rose'}`}>
                          {isAvailable ? 'Disponible' : 'Agotado'}
                        </span>
                      </div>
                    </div>

                    <h3 style={{ fontSize: '1.25rem', fontWeight: '700', color: '#f8fafc', marginBottom: '6px' }}>
                      {dish.name}
                    </h3>
                    <p style={{ color: '#94a3b8', fontSize: '0.85rem', lineHeight: '1.5', marginBottom: '16px' }}>
                      {dish.short_description || dish.long_description}
                    </p>

                    <div style={{
                      display: 'flex',
                      gap: '12px',
                      fontSize: '0.78rem',
                      color: '#cbd5e1',
                      background: 'rgba(255, 255, 255, 0.03)',
                      padding: '8px 12px',
                      borderRadius: '8px',
                      marginBottom: '16px',
                    }}>
                      <span>⏱️ {dish.preparation_time_minutes} min</span>
                      <span>🔥 {dish.calories_estimate ? `${dish.calories_estimate} kcal` : 'N/A'}</span>
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: '8px', paddingTop: '14px', borderTop: '1px solid rgba(255, 255, 255, 0.06)', flexWrap: 'wrap' }}>
                    <button
                      onClick={() => handleOpenDishModal(dish)}
                      className="btn-secondary"
                      style={{ flex: 1, padding: '8px', fontSize: '0.85rem', justifyContent: 'center' }}
                    >
                      <Edit3 size={15} />
                      Editar
                    </button>
                    <button
                      onClick={() => setNutritionModalDish(dish)}
                      style={{
                        padding: '8px 10px',
                        borderRadius: '8px',
                        fontSize: '0.82rem',
                        fontWeight: '700',
                        background: 'rgba(16, 185, 129, 0.15)',
                        color: '#34d399',
                        border: '1px solid rgba(16, 185, 129, 0.35)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '4px',
                        cursor: 'pointer',
                      }}
                      title="Ver información nutricional y beneficios"
                    >
                      <Sparkles size={14} />
                      Nutrición
                    </button>
                    <button
                      onClick={() => setRecipeModalDish(dish)}
                      style={{
                        flex: 1.3,
                        padding: '8px 10px',
                        borderRadius: '8px',
                        fontSize: '0.82rem',
                        fontWeight: '700',
                        background: 'rgba(245, 158, 11, 0.15)',
                        color: '#fbbf24',
                        border: '1px solid rgba(245, 158, 11, 0.35)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '6px',
                        cursor: 'pointer',
                      }}
                    >
                      <Sliders size={14} />
                      Configurar Receta
                    </button>
                    <button
                      onClick={() => handleToggleDishAvailability(dish.id, dish.name)}
                      style={{
                        padding: '8px 12px',
                        borderRadius: '8px',
                        fontSize: '0.85rem',
                        fontWeight: '600',
                        background: isAvailable ? 'rgba(244, 63, 94, 0.15)' : 'rgba(16, 185, 129, 0.15)',
                        color: isAvailable ? '#fb7185' : '#34d399',
                        border: `1px solid ${isAvailable ? 'rgba(244, 63, 94, 0.3)' : 'rgba(16, 185, 129, 0.3)'}`,
                      }}
                    >
                      {isAvailable ? 'Pausar' : 'Activar'}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* --- TAB 3: GESTIÓN DE MESAS & CÓDIGOS QR --- */}
      {activeTab === 'TABLES' && (
        <div className="animate-fade-in">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <h2 style={{ fontSize: '1.3rem', color: '#f8fafc', fontWeight: '700' }}>
                Mesas del Salón & Códigos QR
              </h2>
              <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
                Control de estados, capacidades y regeneración de códigos QR de acceso
              </p>
            </div>
            <button onClick={() => handleOpenTableModal()} className="btn-primary" style={{ padding: '10px 18px', fontSize: '0.9rem' }}>
              <Plus size={18} />
              Agregar Mesa
            </button>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)', // Exactamente 3 tarjetas por fila
            gap: '18px',
          }}>
            {tables.map((table) => {
              // Encontrar órdenes activas para esta mesa en la base de datos (ABIERTA, CERRADA sin pagar)
              const tableOrders = activeOrders.filter((ord) => 
                (ord.table_id === table.id || ord.table_number === table.number) &&
                ord.status !== 'CANCELADA' && 
                ord.status !== 'PAGADA' && 
                ord.status !== 'ENCUESTADA'
              );

              // Si tiene órdenes pendientes de pago, la mesa está ocupada
              const isOcupada = table.status === 'OCUPADA' || tableOrders.length > 0;

              // Extraer todos los ítems agregados en la orden de esta mesa
              const allItemsInTable = tableOrders.flatMap((o) => o.items || []);
              const isExpanded = !!expandedTableOrders[table.id];

              const toggleExpand = () => {
                setExpandedTableOrders((prev) => ({
                  ...prev,
                  [table.id]: !prev[table.id],
                }));
              };

              return (
                <div
                  key={table.id}
                  className="glass-panel"
                  style={{
                    padding: '20px',
                    borderRadius: '18px',
                    border: isOcupada ? '1.5px solid rgba(245, 158, 11, 0.45)' : '1px solid rgba(255, 255, 255, 0.08)',
                    background: isOcupada ? 'rgba(245, 158, 11, 0.06)' : '#0d131f',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontSize: '1.35rem', fontWeight: '800', color: '#f8fafc' }}>
                          Mesa #{table.number}
                        </span>
                        {isOcupada && (
                          <span style={{
                            fontSize: '0.68rem',
                            fontWeight: '800',
                            padding: '2px 6px',
                            borderRadius: '6px',
                            background: 'rgba(239, 68, 68, 0.2)',
                            color: '#f87171',
                            border: '1px solid rgba(239, 68, 68, 0.35)',
                          }}>
                            ● En Vivo
                          </span>
                        )}
                      </div>
                      <span className={`badge ${isOcupada ? 'badge-gold' : 'badge-emerald'}`}>
                        {isOcupada ? 'OCUPADA' : 'LIBRE'}
                      </span>
                    </div>

                    {/* DESCRIPCIÓN DE LA MESA: Al hacer clic muestra órdenes, descripción de cada orden, valor y total */}
                    <div 
                      onClick={() => setSelectedTableDetail({ table, orders: tableOrders, items: allItemsInTable })}
                      style={{ 
                        color: '#cbd5e1', 
                        fontSize: '0.84rem', 
                        marginBottom: '14px', 
                        cursor: 'pointer',
                        padding: '10px 12px',
                        borderRadius: '12px',
                        background: 'rgba(255, 255, 255, 0.04)',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                        transition: 'all 0.2s ease',
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.background = 'rgba(56, 189, 248, 0.08)';
                        e.currentTarget.style.borderColor = 'rgba(56, 189, 248, 0.35)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)';
                        e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.1)';
                      }}
                      title="Haz clic para ver las órdenes, consumos y valor total de esta mesa"
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div>👥 Capacidad: <strong style={{ color: '#fff' }}>{table.capacity} personas</strong></div>
                        <span style={{
                          fontSize: '0.72rem',
                          color: '#38bdf8',
                          fontWeight: '800',
                          background: 'rgba(56, 189, 248, 0.12)',
                          padding: '2px 8px',
                          borderRadius: '6px',
                          border: '1px solid rgba(56, 189, 248, 0.25)',
                        }}>
                          Ver Órdenes & Total ↗
                        </span>
                      </div>
                      <div style={{ marginTop: '4px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ color: '#94a3b8' }}>📍 {zones.find((z) => z.id === table.zone_id)?.name || 'Salón Principal'}</span>
                        {(() => {
                          const computedTableTotal = tableOrders.reduce((acc, ord) => {
                            const ordTot = parseFloat(ord.total || ord.total_amount || 0);
                            if (ordTot > 0) return acc + ordTot;
                            if (ord.items && ord.items.length > 0) {
                              return acc + ord.items.reduce((s, it) => s + parseFloat(it.subtotal || (it.quantity * (it.unit_price || it.price || 0))), 0);
                            }
                            return acc + parseFloat(ord.subtotal || 0);
                          }, 0);
                          return (
                            <strong style={{ color: computedTableTotal > 0 ? '#34d399' : '#94a3b8', fontSize: '0.82rem' }}>
                              {computedTableTotal > 0 ? `Total: $${computedTableTotal.toLocaleString('es-CO')}` : '$0 Pendiente'}
                            </strong>
                          );
                        })()}
                      </div>
                    </div>

                    {/* SECCIÓN EN TIEMPO REAL: PEDIDO ACTUAL DEL CLIENTE */}
                    <div style={{
                      background: 'rgba(0, 0, 0, 0.4)',
                      borderRadius: '12px',
                      padding: '12px',
                      marginBottom: '16px',
                      border: '1px solid rgba(255, 255, 255, 0.06)',
                    }}>
                      <div style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        marginBottom: allItemsInTable.length > 0 ? '10px' : '0',
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <ShoppingBag size={14} color="#fbbf24" />
                          <span style={{ fontSize: '0.78rem', fontWeight: '800', color: '#fbbf24', textTransform: 'uppercase' }}>
                            Comanda en Vivo ({allItemsInTable.length} platos)
                          </span>
                        </div>
                        {allItemsInTable.length > 0 && (
                          <button
                            onClick={toggleExpand}
                            style={{
                              background: 'transparent',
                              color: '#94a3b8',
                              fontSize: '0.75rem',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '2px',
                            }}
                          >
                            {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                            {isExpanded ? 'Ocultar' : 'Ver detalle'}
                          </button>
                        )}
                      </div>

                      {allItemsInTable.length === 0 ? (
                        <div style={{ fontSize: '0.76rem', color: '#64748b', fontStyle: 'italic', padding: '4px 0' }}>
                          Sin comandas activas en este momento
                        </div>
                      ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                          {/* Resumen rápido de platos */}
                          {(!isExpanded ? allItemsInTable.slice(0, 2) : allItemsInTable).map((item, itmIdx) => {
                            const removedMods = (item.modifications || []).filter((m) => m.action === 'QUITAR');
                            const addedMods = (item.modifications || []).filter((m) => m.action === 'AGREGAR');

                            return (
                              <div
                                key={item.id || itmIdx}
                                style={{
                                  background: 'rgba(255, 255, 255, 0.03)',
                                  borderRadius: '8px',
                                  padding: '8px 10px',
                                  border: '1px solid rgba(255, 255, 255, 0.05)',
                                }}
                              >
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                  <div style={{ fontWeight: '700', fontSize: '0.84rem', color: '#f8fafc' }}>
                                    {item.quantity}x {item.dish_name || 'Plato'}
                                  </div>
                                  <span style={{
                                    fontSize: '0.68rem',
                                    fontWeight: '700',
                                    padding: '2px 6px',
                                    borderRadius: '4px',
                                    background: item.status === 'LISTO' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                                    color: item.status === 'LISTO' ? '#34d399' : '#fbbf24',
                                  }}>
                                    {item.status}
                                  </span>
                                </div>

                                {/* Personalización por plato: Quitar / Agregar */}
                                {(removedMods.length > 0 || addedMods.length > 0) && (
                                  <div style={{ marginTop: '6px', display: 'flex', flexDirection: 'column', gap: '3px' }}>
                                    {/* Quitado */}
                                    {removedMods.map((mod) => {
                                      const icon = getIngredientIconInfo(mod.ingredient_name);
                                      return (
                                        <div
                                          key={mod.id || mod.ingredient_id}
                                          style={{
                                            fontSize: '0.72rem',
                                            color: '#fda4af',
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '4px',
                                          }}
                                        >
                                          <span>{icon.emoji}</span>
                                          <span style={{ textDecoration: 'line-through' }}>
                                            Sin {mod.ingredient_name}
                                          </span>
                                        </div>
                                      );
                                    })}

                                    {/* Cosas adicionales pedidas */}
                                    {addedMods.map((mod) => {
                                      const icon = getIngredientIconInfo(mod.ingredient_name);
                                      return (
                                        <div
                                          key={mod.id || mod.ingredient_id}
                                          style={{
                                            fontSize: '0.72rem',
                                            color: '#fde047',
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '4px',
                                            fontWeight: '600',
                                          }}
                                        >
                                          <span>{icon.emoji}</span>
                                          <span>
                                            + Extra {mod.ingredient_name}
                                            {mod.extra_cost > 0 && ` (+$${parseFloat(mod.extra_cost).toLocaleString('es-CO')})`}
                                          </span>
                                        </div>
                                      );
                                    })}
                                  </div>
                                )}

                                {/* Observaciones especiales */}
                                {item.observations && (
                                  <div style={{ fontSize: '0.7rem', color: '#94a3b8', fontStyle: 'italic', marginTop: '4px' }}>
                                    Nota: "{item.observations}"
                                  </div>
                                )}
                              </div>
                            );
                          })}

                          {!isExpanded && allItemsInTable.length > 2 && (
                            <div
                              onClick={toggleExpand}
                              style={{
                                fontSize: '0.72rem',
                                color: '#fbbf24',
                                textAlign: 'center',
                                cursor: 'pointer',
                                padding: '4px 0',
                                fontWeight: '600',
                              }}
                            >
                              + Ver {allItemsInTable.length - 2} platos más...
                            </div>
                          )}
                        </div>
                      )}
                    </div>

                    {/* QR Code UUID */}
                    <div style={{
                      background: 'rgba(0, 0, 0, 0.35)',
                      padding: '8px 10px',
                      borderRadius: '8px',
                      marginBottom: '16px',
                    }}>
                      <div style={{ fontSize: '0.7rem', color: '#64748b', textTransform: 'uppercase' }}>Código QR UUID:</div>
                      <div style={{
                        fontSize: '0.72rem',
                        color: '#fbbf24',
                        fontFamily: 'monospace',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                        marginTop: '2px',
                      }}>
                        {table.qr_code}
                      </div>
                    </div>
                  </div>

                  {/* Acciones de mesa */}
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                      onClick={() => handleOpenTableModal(table)}
                      className="btn-secondary"
                      style={{ flex: 1, padding: '8px', fontSize: '0.82rem', justifyContent: 'center' }}
                    >
                      <Edit3 size={14} />
                      Editar
                    </button>
                    <button
                      onClick={() => handleRegenerateQR(table.id, table.number)}
                      style={{
                        padding: '8px 12px',
                        borderRadius: '8px',
                        background: 'rgba(255, 255, 255, 0.06)',
                        color: '#cbd5e1',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                        fontSize: '0.82rem',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                      }}
                      title="Generar nuevo QR de seguridad"
                    >
                      <QrCode size={14} />
                      Nuevo QR
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* --- TAB 4: GESTIÓN DE INGREDIENTES & SALUD --- */}
      {activeTab === 'INGREDIENTS' && (
        <div className="animate-fade-in">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <h2 style={{ fontSize: '1.3rem', color: '#f8fafc', fontWeight: '700' }}>
                Ingredientes, Alérgenos y Beneficios Nutricionales
              </h2>
              <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
                Agrega, edita y administra ingredientes, macronutrientes y disponibilidad diaria
              </p>
            </div>
            <button 
              onClick={() => handleOpenIngredientModal()} 
              className="btn-primary" 
              style={{ padding: '10px 18px', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '8px' }}
            >
              <Plus size={18} />
              Nuevo Ingrediente
            </button>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(290px, 1fr))',
            gap: '16px',
          }}>
            {ingredients.map((ing) => {
              const icon = getIngredientIconInfo(ing.name);
              return (
                <div
                  key={ing.id}
                  className="glass-panel"
                  style={{
                    padding: '16px',
                    borderRadius: '14px',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    gap: '12px',
                    background: ing.available ? '#0d131f' : 'rgba(244, 63, 94, 0.05)',
                    border: ing.available ? '1px solid rgba(255, 255, 255, 0.08)' : '1px solid rgba(244, 63, 94, 0.3)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span style={{ fontSize: '1.4rem' }}>{icon.emoji}</span>
                      <div>
                        <div style={{ fontWeight: '700', color: '#f8fafc', fontSize: '1rem' }}>
                          {ing.name}
                        </div>
                        <div style={{ fontSize: '0.78rem', color: '#10b981', marginTop: '2px' }}>
                          Prot: {ing.protein || 0}g &bull; Cal: {ing.calories || 0} kcal &bull; {ing.unit || 'g'}
                        </div>
                      </div>
                    </div>
                    <span className={`badge ${ing.available ? 'badge-emerald' : 'badge-rose'}`} style={{ fontSize: '0.72rem' }}>
                      {ing.available ? 'Activo' : 'Pausado'}
                    </span>
                  </div>

                  {ing.price_extra > 0 && (
                    <div style={{ fontSize: '0.78rem', color: '#fbbf24', background: 'rgba(245, 158, 11, 0.1)', padding: '4px 8px', borderRadius: '6px', alignSelf: 'flex-start' }}>
                      + Extra: ${parseFloat(ing.price_extra).toLocaleString('es-CO')}
                    </div>
                  )}

                  <div style={{ display: 'flex', gap: '8px', paddingTop: '10px', borderTop: '1px solid rgba(255, 255, 255, 0.06)' }}>
                    <button
                      onClick={() => handleOpenIngredientModal(ing)}
                      className="btn-secondary"
                      style={{ flex: 1, padding: '7px', fontSize: '0.8rem', justifyContent: 'center' }}
                      title="Editar propiedades y valor nutricional"
                    >
                      <Edit3 size={14} />
                      Editar
                    </button>
                    <button
                      onClick={() => handleToggleIngredient(ing.id, ing.name)}
                      style={{
                        flex: 1,
                        padding: '7px',
                        borderRadius: '8px',
                        fontSize: '0.8rem',
                        fontWeight: '600',
                        background: ing.available ? 'rgba(244, 63, 94, 0.15)' : 'rgba(16, 185, 129, 0.15)',
                        color: ing.available ? '#fb7185' : '#34d399',
                        border: `1px solid ${ing.available ? 'rgba(244, 63, 94, 0.3)' : 'rgba(16, 185, 129, 0.3)'}`,
                      }}
                    >
                      {ing.available ? 'Pausar' : 'Activar'}
                    </button>
                    <button
                      onClick={() => handleDeleteIngredient(ing)}
                      style={{
                        padding: '7px 10px',
                        borderRadius: '8px',
                        background: 'rgba(244, 63, 94, 0.1)',
                        color: '#f43f5e',
                        border: '1px solid rgba(244, 63, 94, 0.25)',
                        cursor: 'pointer',
                      }}
                      title="Eliminar ingrediente"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* --- TAB 5: CAJA & ARQUEO (Fase 6 del Documento Maestro) --- */}
      {activeTab === 'CASH' && (
        <div className="animate-fade-in">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <h2 style={{ fontSize: '1.3rem', color: '#f8fafc', fontWeight: '700' }}>
                Caja, Turnos de Arqueo & Formas de Pago
              </h2>
              <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
                Control de apertura/cierre de caja, ingresos en efectivo, datáfono, transferencias y cuadre contable
              </p>
            </div>
            {cashSession ? (
              <button
                onClick={async () => {
                  try {
                    await api.closeCashSession(cashSession.id, { final_cash_amount: cashSession.expected_cash_amount || 250000 }, token);
                    notify('Sesión de caja cerrada y arqueada exitosamente');
                    loadAllData();
                  } catch (e) {
                    notify(e.message, 'error');
                  }
                }}
                style={{
                  background: 'rgba(239, 68, 68, 0.15)',
                  color: '#f87171',
                  border: '1px solid rgba(239, 68, 68, 0.35)',
                  padding: '10px 18px',
                  borderRadius: '12px',
                  fontWeight: '700',
                  fontSize: '0.9rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                }}
              >
                <Lock size={16} />
                Cerrar Caja & Realizar Arqueo
              </button>
            ) : (
              <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                <input
                  type="number"
                  placeholder="Base inicial ($)"
                  value={initialCashAmount}
                  onChange={(e) => setInitialCashAmount(e.target.value)}
                  style={{
                    padding: '8px 12px',
                    borderRadius: '8px',
                    background: '#121824',
                    border: '1px solid rgba(255, 255, 255, 0.12)',
                    color: '#fff',
                    width: '140px',
                    fontSize: '0.88rem',
                  }}
                />
                <button
                  onClick={async () => {
                    try {
                      await api.openCashSession({ branch_id: branches[0]?.id, initial_cash_amount: parseFloat(initialCashAmount) || 100000 }, token);
                      notify('Caja abierta exitosamente con base');
                      loadAllData();
                    } catch (e) {
                      notify(e.message, 'error');
                    }
                  }}
                  className="btn-primary"
                  style={{ padding: '9px 18px', fontSize: '0.9rem' }}
                >
                  <Unlock size={16} />
                  Abrir Caja
                </button>
              </div>
            )}
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
            gap: '18px',
            marginBottom: '28px',
          }}>
            <div className="glass-panel" style={{ padding: '20px' }}>
              <div style={{ fontSize: '0.78rem', color: '#64748b', textTransform: 'uppercase', fontWeight: '700' }}>
                Estado de la Caja
              </div>
              <div style={{ fontSize: '1.4rem', fontWeight: '800', color: cashSession ? '#34d399' : '#f87171', marginTop: '6px' }}>
                {cashSession ? '● ABIERTA & OPERANDO' : '○ CERRADA'}
              </div>
              <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '4px' }}>
                {cashSession ? `Apertura: ${new Date(cashSession.opened_at).toLocaleTimeString()}` : 'No hay cajero en turno'}
              </div>
            </div>

            <div className="glass-panel" style={{ padding: '20px' }}>
              <div style={{ fontSize: '0.78rem', color: '#64748b', textTransform: 'uppercase', fontWeight: '700' }}>
                Base de Apertura
              </div>
              <div style={{ fontSize: '1.6rem', fontWeight: '800', color: '#fbbf24', marginTop: '6px' }}>
                ${parseFloat(cashSession?.initial_cash_amount || 0).toLocaleString('es-CO')}
              </div>
              <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '4px' }}>
                Fondo para cambio en efectivo
              </div>
            </div>

            <div className="glass-panel" style={{ padding: '20px' }}>
              <div style={{ fontSize: '0.78rem', color: '#64748b', textTransform: 'uppercase', fontWeight: '700' }}>
                Efectivo Esperado en Arqueo
              </div>
              <div style={{ fontSize: '1.6rem', fontWeight: '800', color: '#38bdf8', marginTop: '6px' }}>
                ${parseFloat(cashSession?.expected_cash_amount || summary?.total_sales || 0).toLocaleString('es-CO')}
              </div>
              <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '4px' }}>
                Incluye ventas en efectivo + base
              </div>
            </div>
          </div>

          <div className="glass-panel" style={{ padding: '24px' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: '700', color: '#f8fafc', marginBottom: '16px' }}>
              Historial de Transacciones & Cierres de Cuenta
            </h3>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.86rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.08)', color: '#94a3b8', textAlign: 'left' }}>
                    <th style={{ padding: '10px' }}>Orden / Comanda</th>
                    <th style={{ padding: '10px' }}>Canal</th>
                    <th style={{ padding: '10px' }}>Subtotal</th>
                    <th style={{ padding: '10px' }}>Propina</th>
                    <th style={{ padding: '10px' }}>Total</th>
                    <th style={{ padding: '10px' }}>Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {activeOrders.slice(0, 8).map((ord) => (
                    <tr key={ord.id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                      <td style={{ padding: '12px 10px', fontWeight: '700', color: '#fbbf24' }}>
                        {ord.display_code || ord.id.slice(0, 8)}
                      </td>
                      <td style={{ padding: '12px 10px', color: '#cbd5e1' }}>
                        {ord.channel || 'MESA_QR'}
                      </td>
                      <td style={{ padding: '12px 10px', color: '#fff' }}>
                        ${parseFloat(ord.subtotal).toLocaleString('es-CO')}
                      </td>
                      <td style={{ padding: '12px 10px', color: '#34d399' }}>
                        ${parseFloat(ord.tip_amount || 0).toLocaleString('es-CO')}
                      </td>
                      <td style={{ padding: '12px 10px', fontWeight: '800', color: '#fff' }}>
                        ${parseFloat(ord.total).toLocaleString('es-CO')}
                      </td>
                      <td style={{ padding: '12px 10px' }}>
                        <span className={`badge ${ord.status === 'PAGADA' ? 'badge-emerald' : 'badge-gold'}`}>
                          {ord.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* --- TAB 6: DOMICILIOS & ENTREGAS (Fase 7 del Documento Maestro) --- */}
      {activeTab === 'DELIVERIES' && (
        <div className="animate-fade-in">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <h2 style={{ fontSize: '1.3rem', color: '#f8fafc', fontWeight: '700' }}>
                Control de Domicilios, Zonas de Cobertura & Repartidores
              </h2>
              <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
                Seguimiento en tiempo real de despachos, asignación de domiciliarios y tarifas por zona
              </p>
            </div>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
            gap: '18px',
            marginBottom: '28px',
          }}>
            {deliveries.length === 0 ? (
              <div className="glass-panel" style={{ padding: '36px', textAlign: 'center', color: '#94a3b8', gridColumn: '1 / -1' }}>
                <Truck size={40} color="#3b82f6" style={{ margin: '0 auto 12px' }} />
                <div style={{ fontSize: '1.1rem', fontWeight: '700', color: '#f8fafc' }}>
                  No hay pedidos a domicilio activos en este momento
                </div>
                <p style={{ fontSize: '0.85rem', marginTop: '6px' }}>
                  Los pedidos generados por la app de clientes o canal telefónico aparecerán aquí con su estado de despacho.
                </p>
              </div>
            ) : (
              deliveries.map((deliv) => (
                <div key={deliv.id} className="glass-panel" style={{ padding: '20px', borderRadius: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                    <span style={{ fontWeight: '800', color: '#fbbf24', fontSize: '1.1rem' }}>
                      #{deliv.order?.display_code || deliv.id.slice(0, 8)}
                    </span>
                    <span className="badge badge-gold">
                      {deliv.status}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.88rem', color: '#f8fafc', fontWeight: '700', marginBottom: '6px' }}>
                    👤 {deliv.customer_name} &bull; 📞 {deliv.customer_phone}
                  </div>
                  <div style={{ fontSize: '0.82rem', color: '#94a3b8', marginBottom: '10px' }}>
                    📍 {deliv.delivery_address}
                  </div>
                  <div style={{ fontSize: '0.82rem', color: '#cbd5e1', borderTop: '1px solid rgba(255, 255, 255, 0.08)', paddingTop: '10px', display: 'flex', justifyContent: 'space-between' }}>
                    <span>Costo de Envío:</span>
                    <strong style={{ color: '#38bdf8' }}>${parseFloat(deliv.delivery_fee || 0).toLocaleString('es-CO')}</strong>
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="glass-panel" style={{ padding: '24px' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: '700', color: '#f8fafc', marginBottom: '14px' }}>
              Zonas de Cobertura & Tarifas de Entrega
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '14px' }}>
              {deliveryZones.map((zone) => (
                <div key={zone.id} style={{
                  background: 'rgba(255, 255, 255, 0.03)',
                  padding: '14px',
                  borderRadius: '12px',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                }}>
                  <div style={{ fontWeight: '700', color: '#f8fafc', fontSize: '0.95rem' }}>
                    {zone.name}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '4px' }}>
                    Tarifa de envío: <strong style={{ color: '#fbbf24' }}>${parseFloat(zone.fee).toLocaleString('es-CO')}</strong>
                  </div>
                  <div style={{ fontSize: '0.74rem', color: '#34d399', marginTop: '4px' }}>
                    ⏱️ Tiempo promedio: {zone.estimated_minutes} min
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* --- TAB 7: TURNOS, HORARIOS & RRHH (Fase 4 del Documento Maestro) --- */}
      {activeTab === 'SHIFTS' && (
        <div className="animate-fade-in">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <h2 style={{ fontSize: '1.3rem', color: '#f8fafc', fontWeight: '700' }}>
                Gestión de Personal, Turnos & Control de Asistencia
              </h2>
              <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
                Monitoreo de meseros, cocineros, horarios programados, entradas/salidas y descansos
              </p>
            </div>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
            gap: '16px',
            marginBottom: '28px',
          }}>
            {employees.map((emp) => (
              <div key={emp.id} className="glass-panel" style={{ padding: '18px', borderRadius: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                  <span style={{ fontWeight: '800', color: '#f8fafc', fontSize: '1.05rem' }}>
                    {emp.user?.full_name || emp.identification_number}
                  </span>
                  <span className="badge badge-emerald">
                    {emp.job_title || 'Colaborador'}
                  </span>
                </div>
                <div style={{ fontSize: '0.82rem', color: '#94a3b8', marginBottom: '4px' }}>
                  🆔 Documento: <strong>{emp.identification_number}</strong>
                </div>
                <div style={{ fontSize: '0.82rem', color: '#94a3b8', marginBottom: '4px' }}>
                  💼 Contrato: {emp.contract_type || 'Término Indefinido'}
                </div>
                <div style={{ fontSize: '0.82rem', color: '#cbd5e1', borderTop: '1px solid rgba(255, 255, 255, 0.08)', paddingTop: '8px', marginTop: '10px' }}>
                  Salario Base: <strong style={{ color: '#fbbf24' }}>${parseFloat(emp.base_salary || 0).toLocaleString('es-CO')}</strong>
                </div>
              </div>
            ))}
          </div>

          <div className="glass-panel" style={{ padding: '24px' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: '700', color: '#f8fafc', marginBottom: '14px' }}>
              Turnos Programados & Registro de Entrada / Salida
            </h3>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.86rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.08)', color: '#94a3b8', textAlign: 'left' }}>
                    <th style={{ padding: '10px' }}>Fecha</th>
                    <th style={{ padding: '10px' }}>Empleado</th>
                    <th style={{ padding: '10px' }}>Horario Programado</th>
                    <th style={{ padding: '10px' }}>Hora Entrada</th>
                    <th style={{ padding: '10px' }}>Hora Salida</th>
                    <th style={{ padding: '10px' }}>Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {shifts.slice(0, 8).map((shift) => (
                    <tr key={shift.id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                      <td style={{ padding: '12px 10px', color: '#fff' }}>{shift.shift_date}</td>
                      <td style={{ padding: '12px 10px', fontWeight: '700', color: '#fbbf24' }}>
                        {shift.employee?.user?.full_name || 'Empleado'}
                      </td>
                      <td style={{ padding: '12px 10px', color: '#cbd5e1' }}>
                        {shift.scheduled_start_time?.slice(0, 5)} - {shift.scheduled_end_time?.slice(0, 5)}
                      </td>
                      <td style={{ padding: '12px 10px', color: '#34d399' }}>
                        {shift.actual_start_time ? new Date(shift.actual_start_time).toLocaleTimeString() : 'Pendiente'}
                      </td>
                      <td style={{ padding: '12px 10px', color: '#94a3b8' }}>
                        {shift.actual_end_time ? new Date(shift.actual_end_time).toLocaleTimeString() : 'En servicio'}
                      </td>
                      <td style={{ padding: '12px 10px' }}>
                        <span className={`badge ${shift.status === 'EN_CURSO' ? 'badge-emerald' : 'badge-gold'}`}>
                          {shift.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* --- TAB 8: COMISIONES & PROPINAS (Fase 5 del Documento Maestro) --- */}
      {activeTab === 'COMMISSIONS' && (
        <div className="animate-fade-in">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <h2 style={{ fontSize: '1.3rem', color: '#f8fafc', fontWeight: '700' }}>
                Reglas de Comisión, Propinas & Liquidaciones de Meseros
              </h2>
              <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
                Cálculo automatizado de comisiones por ventas, platos insignes y puntajes en encuestas de satisfacción
              </p>
            </div>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
            gap: '16px',
            marginBottom: '28px',
          }}>
            {commissionRules.map((rule) => (
              <div key={rule.id} className="glass-panel" style={{ padding: '18px', borderRadius: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span style={{ fontWeight: '800', color: '#f8fafc', fontSize: '1rem' }}>
                    {rule.name}
                  </span>
                  <span className="badge badge-gold">
                    {rule.rule_type}
                  </span>
                </div>
                <div style={{ fontSize: '0.82rem', color: '#94a3b8', marginBottom: '8px' }}>
                  {rule.description || 'Regla activa para liquidación quincenal'}
                </div>
                <div style={{ fontSize: '0.9rem', color: '#34d399', fontWeight: '700', borderTop: '1px solid rgba(255, 255, 255, 0.08)', paddingTop: '8px' }}>
                  Porcentaje: {rule.percentage ? `${rule.percentage}%` : `$${parseFloat(rule.fixed_amount || 0).toLocaleString('es-CO')}`}
                </div>
              </div>
            ))}
          </div>

          <div className="glass-panel" style={{ padding: '24px' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: '700', color: '#f8fafc', marginBottom: '14px' }}>
              Periodos de Liquidación & Desembolsos
            </h3>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.86rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.08)', color: '#94a3b8', textAlign: 'left' }}>
                    <th style={{ padding: '10px' }}>Periodo</th>
                    <th style={{ padding: '10px' }}>Fecha Inicio</th>
                    <th style={{ padding: '10px' }}>Fecha Fin</th>
                    <th style={{ padding: '10px' }}>Total Comisiones</th>
                    <th style={{ padding: '10px' }}>Total Propinas</th>
                    <th style={{ padding: '10px' }}>Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {commissionPeriods.map((period) => (
                    <tr key={period.id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                      <td style={{ padding: '12px 10px', fontWeight: '700', color: '#fff' }}>{period.name}</td>
                      <td style={{ padding: '12px 10px', color: '#94a3b8' }}>{period.start_date}</td>
                      <td style={{ padding: '12px 10px', color: '#94a3b8' }}>{period.end_date}</td>
                      <td style={{ padding: '12px 10px', color: '#fbbf24', fontWeight: '700' }}>
                        ${parseFloat(period.total_commissions || 0).toLocaleString('es-CO')}
                      </td>
                      <td style={{ padding: '12px 10px', color: '#34d399', fontWeight: '700' }}>
                        ${parseFloat(period.total_tips || 0).toLocaleString('es-CO')}
                      </td>
                      <td style={{ padding: '12px 10px' }}>
                        <span className={`badge ${period.status === 'PAGADO' ? 'badge-emerald' : 'badge-gold'}`}>
                          {period.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* --- TAB 9: INVENTARIO & STOCK (Fase 8 del Documento Maestro) --- */}
      {activeTab === 'INVENTORY' && (
        <div className="animate-fade-in">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <h2 style={{ fontSize: '1.3rem', color: '#f8fafc', fontWeight: '700' }}>
                Control de Stock, Recetas & Ajustes de Inventario
              </h2>
              <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
                Monitoreo de existencias. Haz clic sobre cualquier producto/ingrediente para editar cantidades, mínimo requerido o eliminarlo de stock.
              </p>
            </div>
            <button
              onClick={() => handleOpenIngredientModal()}
              className="btn-primary"
              style={{ padding: '10px 18px', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '8px' }}
            >
              <Plus size={18} />
              Agregar Producto al Stock
            </button>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
            gap: '16px',
            marginBottom: '28px',
          }}>
            {ingredients.map((ing) => {
              const icon = getIngredientIconInfo(ing.name);
              // Buscar stock item correspondiente si existe
              const matchedStock = stockItems.find((s) => s.ingredient_id === ing.id);
              const curStock = matchedStock ? matchedStock.current_stock : (ing.current_stock || 15);
              const minStock = matchedStock ? matchedStock.min_stock : (ing.min_stock || 5);
              const isLowStock = parseFloat(curStock) <= parseFloat(minStock);

              return (
                <div
                  key={ing.id}
                  className="glass-panel"
                  onClick={() => setSelectedStockIngredient({
                    ...ing,
                    stock_id: matchedStock?.id,
                    edit_current_stock: String(curStock),
                    edit_min_stock: String(minStock),
                  })}
                  style={{
                    padding: '18px',
                    borderRadius: '16px',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    border: isLowStock ? '1px solid rgba(244, 63, 94, 0.4)' : '1px solid rgba(255, 255, 255, 0.08)',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'translateY(-3px)';
                    e.currentTarget.style.borderColor = 'rgba(245, 158, 11, 0.5)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.borderColor = isLowStock ? 'rgba(244, 63, 94, 0.4)' : 'rgba(255, 255, 255, 0.08)';
                  }}
                  title="Haz clic para Editar o Eliminar este ingrediente de stock"
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontSize: '1.3rem' }}>{icon.emoji}</span>
                      <span style={{ fontWeight: '700', color: '#f8fafc', fontSize: '0.96rem' }}>
                        {ing.name}
                      </span>
                    </div>
                    <span className={`badge ${isLowStock ? 'badge-rose' : 'badge-emerald'}`}>
                      {isLowStock ? 'Alerta Stock' : 'Abastecido'}
                    </span>
                  </div>

                  <div style={{ fontSize: '0.85rem', color: '#94a3b8', display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <span>Stock Actual:</span>
                    <strong style={{ color: '#fbbf24', fontSize: '1rem' }}>
                      {curStock} {ing.unit || 'g'}
                    </strong>
                  </div>

                  <div style={{ fontSize: '0.78rem', color: '#64748b', display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                    <span>Mínimo requerido:</span>
                    <span>{minStock} {ing.unit || 'g'}</span>
                  </div>

                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '6px',
                    paddingTop: '8px',
                    borderTop: '1px solid rgba(255, 255, 255, 0.06)',
                    fontSize: '0.74rem',
                    color: '#fbbf24',
                    fontWeight: '600',
                  }}>
                    <Edit3 size={13} />
                    <span>Clic para gestionar</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* --- TAB 10: SEGURIDAD, AUDITORÍA & SISTEMA (Fase 11 del Documento Maestro) --- */}
      {activeTab === 'SYSTEM' && (
        <div className="animate-fade-in">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <h2 style={{ fontSize: '1.3rem', color: '#f8fafc', fontWeight: '700' }}>
                Seguridad de Grado Militar, Auditoría & Trazabilidad
              </h2>
              <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
                Logs de transacciones inmutables, monitoreo de conexiones asíncronas y salud de la base de datos
              </p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="badge badge-emerald" style={{ padding: '8px 14px', fontSize: '0.85rem' }}>
                <Activity size={15} />
                Sistema 100% Operativo
              </span>
            </div>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
            gap: '18px',
            marginBottom: '28px',
          }}>
            <div className="glass-panel" style={{ padding: '20px' }}>
              <div style={{ fontSize: '0.78rem', color: '#64748b', textTransform: 'uppercase', fontWeight: '700' }}>
                Motor de Base de Datos
              </div>
              <div style={{ fontSize: '1.4rem', fontWeight: '800', color: '#34d399', marginTop: '6px' }}>
                PostgreSQL 16 ACID
              </div>
              <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '4px' }}>
                Estado: {systemHealth?.database || 'Conectado & Verificado'}
              </div>
            </div>

            <div className="glass-panel" style={{ padding: '20px' }}>
              <div style={{ fontSize: '0.78rem', color: '#64748b', textTransform: 'uppercase', fontWeight: '700' }}>
                Capa de Memoria & Caché
              </div>
              <div style={{ fontSize: '1.4rem', fontWeight: '800', color: '#fbbf24', marginTop: '6px' }}>
                Redis 7 Pub/Sub
              </div>
              <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '4px' }}>
                Estado: {systemHealth?.redis || 'Latencia < 1ms'}
              </div>
            </div>

            <div className="glass-panel" style={{ padding: '20px' }}>
              <div style={{ fontSize: '0.78rem', color: '#64748b', textTransform: 'uppercase', fontWeight: '700' }}>
                Usuarios & Roles Registrados
              </div>
              <div style={{ fontSize: '1.4rem', fontWeight: '800', color: '#38bdf8', marginTop: '6px' }}>
                {systemHealth?.users_count || employees.length || '3'} Cuentas
              </div>
              <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '4px' }}>
                Seguridad Argon2id + JWT OAuth2
              </div>
            </div>
          </div>

          <div className="glass-panel" style={{ padding: '24px' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: '700', color: '#f8fafc', marginBottom: '14px' }}>
              Trazabilidad de Acciones & Logs de Auditoría (AuditLog)
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '12px' }}>
              {(auditStats.length > 0 ? auditStats : [
                { action: 'ORDEN_CREADA', count: 18 },
                { action: 'PAGO_REGISTRADO', count: 14 },
                { action: 'MODIFICACION_PLATO', count: 9 },
                { action: 'LOGIN_ADMIN', count: 6 },
                { action: 'CAMBIO_ESTADO_COCINA', count: 12 },
              ]).map((stat, idx) => (
                <div key={idx} style={{
                  background: 'rgba(255, 255, 255, 0.03)',
                  padding: '12px 16px',
                  borderRadius: '10px',
                  border: '1px solid rgba(255, 255, 255, 0.06)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}>
                  <div style={{ fontWeight: '700', color: '#cbd5e1', fontSize: '0.86rem' }}>
                    {stat.action}
                  </div>
                  <span className="badge badge-gold" style={{ fontSize: '0.75rem' }}>
                    {stat.count} eventos
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* --- TAB: REPORTES & ANALÍTICA DE NEGOCIO (Fase 11 del Documento Maestro) --- */}
      {activeTab === 'REPORTS' && (
        <ReportsModule token={token} notify={notify} />
      )}

      {/* --- TAB 10: CONFIGURACIÓN GENERAL DEL RESTAURANTE (Módulo 4.1 del Documento Maestro) --- */}
      {activeTab === 'SETTINGS' && (
        <div className="animate-fade-in">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '14px' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <h2 style={{ fontSize: '1.3rem', color: '#f8fafc', fontWeight: '700' }}>
                  Configuración del Sistema
                </h2>
                <span className="badge badge-gold" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Settings size={13} />
                  Panel Maestro
                </span>
              </div>
              <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
                Control total de políticas del restaurante y asignación de permisos de módulos a usuarios
              </p>
            </div>

            {/* Selector de Sub-pestañas dentro de Configuración */}
            <div style={{
              display: 'flex',
              background: 'rgba(255, 255, 255, 0.05)',
              padding: '4px',
              borderRadius: '12px',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              gap: '6px',
            }}>
              <button
                onClick={() => setSettingsSubTab('PROFILE')}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '8px 16px',
                  borderRadius: '9px',
                  fontSize: '0.86rem',
                  fontWeight: settingsSubTab === 'PROFILE' ? '800' : '600',
                  background: settingsSubTab === 'PROFILE' ? 'var(--gold-gradient)' : 'transparent',
                  color: settingsSubTab === 'PROFILE' ? '#000' : '#cbd5e1',
                  border: 'none',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                }}
              >
                <Settings size={15} />
                <span>Perfil & Parámetros</span>
              </button>

              <button
                onClick={() => setSettingsSubTab('PERMISSIONS')}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '8px 16px',
                  borderRadius: '9px',
                  fontSize: '0.86rem',
                  fontWeight: settingsSubTab === 'PERMISSIONS' ? '800' : '600',
                  background: settingsSubTab === 'PERMISSIONS' ? 'var(--gold-gradient)' : 'transparent',
                  color: settingsSubTab === 'PERMISSIONS' ? '#000' : '#cbd5e1',
                  border: 'none',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                }}
              >
                <ShieldCheck size={15} />
                <span>Módulos & Accesos</span>
              </button>

              <button
                onClick={() => setSettingsSubTab('THEME')}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '8px 16px',
                  borderRadius: '9px',
                  fontSize: '0.86rem',
                  fontWeight: settingsSubTab === 'THEME' ? '800' : '600',
                  background: settingsSubTab === 'THEME' ? 'var(--gold-gradient)' : 'transparent',
                  color: settingsSubTab === 'THEME' ? '#000' : '#cbd5e1',
                  border: 'none',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                }}
              >
                <Palette size={15} />
                <span>Personalización & Parallax</span>
              </button>
            </div>
          </div>

          {/* SUB-PESTAÑA 1: PERFIL GENERAL Y PARÁMETROS FINANCIEROS */}
          {settingsSubTab === 'PROFILE' && (
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                try {
                  await api.updateRestaurantProfile({
                    name: configForm.name,
                    legal_name: configForm.legal_name,
                    nit: configForm.nit,
                    address: configForm.address,
                    phone: configForm.phone,
                    email: configForm.email,
                    default_tax_rate: parseFloat(configForm.default_tax_rate),
                    default_tip_rate: parseFloat(configForm.default_tip_rate),
                    currency: configForm.currency,
                    timezone: configForm.timezone,
                  }, token);
                  notify('¡Configuración del restaurante guardada con éxito!');
                  await loadAllData();
                } catch (err) {
                  notify(err.message, 'error');
                }
              }}
              style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}
            >
              <div className="glass-panel" style={{ padding: '24px', borderRadius: '18px' }}>
                <h3 style={{ fontSize: '1.05rem', color: '#f8fafc', fontWeight: '800', marginBottom: '16px' }}>
                  Identidad & Datos de Contacto
                </h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>
                    Nombre Comercial del Restaurante
                  </label>
                  <input
                    type="text"
                    required
                    value={configForm.name}
                    onChange={(e) => setConfigForm({ ...configForm, name: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '10px 14px',
                      borderRadius: '8px',
                      background: 'rgba(255, 255, 255, 0.05)',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                      color: '#fff',
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>
                    Razón Social / Razón Legal
                  </label>
                  <input
                    type="text"
                    value={configForm.legal_name}
                    onChange={(e) => setConfigForm({ ...configForm, legal_name: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '10px 14px',
                      borderRadius: '8px',
                      background: 'rgba(255, 255, 255, 0.05)',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                      color: '#fff',
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>
                    NIT / Identificación Fiscal
                  </label>
                  <input
                    type="text"
                    value={configForm.nit || ''}
                    placeholder="901.234.567-8"
                    onChange={(e) => setConfigForm({ ...configForm, nit: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '10px 14px',
                      borderRadius: '8px',
                      background: 'rgba(255, 255, 255, 0.05)',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                      color: '#fff',
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>
                    Dirección Principal
                  </label>
                  <input
                    type="text"
                    value={configForm.address || ''}
                    onChange={(e) => setConfigForm({ ...configForm, address: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '10px 14px',
                      borderRadius: '8px',
                      background: 'rgba(255, 255, 255, 0.05)',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                      color: '#fff',
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>
                    Teléfono / WhatsApp de Pedidos
                  </label>
                  <input
                    type="text"
                    value={configForm.phone || ''}
                    onChange={(e) => setConfigForm({ ...configForm, phone: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '10px 14px',
                      borderRadius: '8px',
                      background: 'rgba(255, 255, 255, 0.05)',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                      color: '#fff',
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>
                    Correo Electrónico Notificaciones
                  </label>
                  <input
                    type="email"
                    value={configForm.email || ''}
                    onChange={(e) => setConfigForm({ ...configForm, email: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '10px 14px',
                      borderRadius: '8px',
                      background: 'rgba(255, 255, 255, 0.05)',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                      color: '#fff',
                    }}
                  />
                </div>
              </div>
            </div>

            <div className="glass-panel" style={{ padding: '24px', borderRadius: '18px' }}>
              <h3 style={{ fontSize: '1.05rem', color: '#f8fafc', fontWeight: '800', marginBottom: '16px' }}>
                Parámetros Financieros, Propinas & Moneda
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>
                    Impuesto al Consumo / IVA (decimal ej: 0.08 = 8%)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="1"
                    value={configForm.default_tax_rate}
                    onChange={(e) => setConfigForm({ ...configForm, default_tax_rate: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '10px 14px',
                      borderRadius: '8px',
                      background: 'rgba(255, 255, 255, 0.05)',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                      color: '#fff',
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>
                    Propina Voluntaria Sugerida (decimal ej: 0.10 = 10%)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="1"
                    value={configForm.default_tip_rate}
                    onChange={(e) => setConfigForm({ ...configForm, default_tip_rate: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '10px 14px',
                      borderRadius: '8px',
                      background: 'rgba(255, 255, 255, 0.05)',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                      color: '#fff',
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>
                    Código de Moneda
                  </label>
                  <input
                    type="text"
                    maxLength={3}
                    value={configForm.currency}
                    onChange={(e) => setConfigForm({ ...configForm, currency: e.target.value.toUpperCase() })}
                    style={{
                      width: '100%',
                      padding: '10px 14px',
                      borderRadius: '8px',
                      background: 'rgba(255, 255, 255, 0.05)',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                      color: '#fff',
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>
                    Zona Horaria
                  </label>
                  <input
                    type="text"
                    value={configForm.timezone}
                    onChange={(e) => setConfigForm({ ...configForm, timezone: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '10px 14px',
                      borderRadius: '8px',
                      background: 'rgba(255, 255, 255, 0.05)',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                      color: '#fff',
                    }}
                  />
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
              <button
                type="submit"
                className="btn-primary"
                style={{ padding: '12px 24px', fontSize: '0.92rem', display: 'flex', alignItems: 'center', gap: '8px' }}
              >
                <Save size={18} />
                Guardar Configuración General
              </button>
            </div>
          </form>
          )}

          {/* =========================================================================
              SUB-PESTAÑA 2 (SEPARADA):
              ESTRUCTURACIÓN POR MÓDULOS & ASIGNACIÓN DE PERMISOS A CADA USUARIO
              ========================================================================= */}
          {settingsSubTab === 'PERMISSIONS' && (
            <div className="glass-panel animate-fade-in" style={{ padding: '26px', borderRadius: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px', flexWrap: 'wrap', gap: '12px' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <h3 style={{ fontSize: '1.2rem', color: '#f8fafc', fontWeight: '800' }}>
                      Estructuración por Módulos & Asignación de Accesos a Usuarios
                    </h3>
                    <span className="badge badge-gold" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <ShieldCheck size={14} />
                      Control Total del Administrador
                    </span>
                  </div>
                  <p style={{ color: '#94a3b8', fontSize: '0.85rem', marginTop: '4px' }}>
                    Como Administrador del sistema, asigna con precisión a qué módulos específicos tiene acceso cada colaborador.
                  </p>
                </div>
              </div>

              {systemUsers.length === 0 ? (
                <div style={{
                  padding: '24px',
                  textAlign: 'center',
                  background: 'rgba(255, 255, 255, 0.02)',
                  borderRadius: '14px',
                  border: '1px dashed rgba(255, 255, 255, 0.1)',
                  color: '#94a3b8'
                }}>
                  <Users size={32} style={{ margin: '0 auto 10px', opacity: 0.5 }} />
                  <p>No se encontraron usuarios del sistema o cargando lista de usuarios...</p>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                  {systemUsers.map((u) => {
                    const isAdminUser = u.role === 'ADMIN';
                    const userPerms = userModulePermissions[u.email] || (
                      u.role === 'CAJERO' ? ['CASH', 'TABLES', 'DELIVERIES'] :
                      u.role === 'MESERO' ? ['TABLES', 'DISHES', 'COMMISSIONS'] :
                      u.role === 'COCINERO' ? ['DISHES', 'INGREDIENTS', 'INVENTORY'] :
                      u.role === 'DOMICILIARIO' ? ['DELIVERIES'] :
                      u.role === 'RRHH' ? ['SHIFTS', 'COMMISSIONS'] :
                      u.role === 'NUTRICIONISTA' ? ['INGREDIENTS', 'DISHES'] :
                      u.role === 'AUDITOR' ? ['SYSTEM', 'CASH', 'INVENTORY'] : []
                    );

                    return (
                      <div
                        key={u.id}
                        style={{
                          background: 'rgba(15, 23, 42, 0.65)',
                          border: isAdminUser ? '1.5px solid rgba(245, 158, 11, 0.4)' : '1px solid rgba(255, 255, 255, 0.08)',
                          borderRadius: '16px',
                          padding: '20px',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '14px',
                          boxShadow: '0 8px 24px rgba(0, 0, 0, 0.3)',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                            <div style={{
                              width: '42px',
                              height: '42px',
                              borderRadius: '12px',
                              background: isAdminUser ? 'var(--gold-gradient)' : 'rgba(56, 189, 248, 0.15)',
                              color: isAdminUser ? '#000' : '#38bdf8',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              fontWeight: '800',
                              fontSize: '1.1rem',
                            }}>
                              {u.full_name ? u.full_name.charAt(0).toUpperCase() : u.email.charAt(0).toUpperCase()}
                            </div>
                            <div>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <span style={{ fontSize: '1rem', fontWeight: '800', color: '#f8fafc' }}>
                                  {u.full_name || u.email.split('@')[0]}
                                </span>
                                <span style={{
                                  fontSize: '0.72rem',
                                  padding: '2px 8px',
                                  borderRadius: '6px',
                                  fontWeight: '700',
                                  background: isAdminUser ? 'rgba(245, 158, 11, 0.2)' : 'rgba(56, 189, 248, 0.15)',
                                  color: isAdminUser ? '#f59e0b' : '#38bdf8',
                                  border: isAdminUser ? '1px solid rgba(245, 158, 11, 0.4)' : '1px solid rgba(56, 189, 248, 0.3)',
                                }}>
                                  {u.role}
                                </span>
                              </div>
                              <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '2px' }}>
                                {u.email}
                              </div>
                            </div>
                          </div>

                          {isAdminUser ? (
                            <div style={{
                              fontSize: '0.78rem',
                              fontWeight: '700',
                              color: '#f59e0b',
                              background: 'rgba(245, 158, 11, 0.12)',
                              padding: '6px 14px',
                              borderRadius: '8px',
                              border: '1px solid rgba(245, 158, 11, 0.25)',
                            }}>
                              Acceso Total Incondicional (Administrador)
                            </div>
                          ) : (
                            <div style={{
                              fontSize: '0.78rem',
                              color: '#94a3b8',
                            }}>
                              {userPerms.length} de {ALL_MODULES.filter((m) => m.id !== 'SETTINGS').length} módulos permitidos
                            </div>
                          )}
                        </div>

                        {/* Selector de Módulos con Checkboxes */}
                        <div style={{
                          display: 'grid',
                          gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
                          gap: '10px',
                          marginTop: '4px',
                          paddingTop: '12px',
                          borderTop: '1px solid rgba(255, 255, 255, 0.05)',
                        }}>
                          {ALL_MODULES.filter((m) => m.id !== 'SETTINGS').map((moduleItem) => {
                            const isEnabled = isAdminUser || userPerms.includes(moduleItem.id);
                            const ModIcon = moduleItem.icon;

                            return (
                              <label
                                key={moduleItem.id}
                                style={{
                                  display: 'flex',
                                  alignItems: 'center',
                                  gap: '10px',
                                  padding: '10px 12px',
                                  borderRadius: '10px',
                                  background: isEnabled ? 'rgba(56, 189, 248, 0.08)' : 'rgba(255, 255, 255, 0.02)',
                                  border: isEnabled ? '1px solid rgba(56, 189, 248, 0.3)' : '1px solid rgba(255, 255, 255, 0.05)',
                                  cursor: isAdminUser ? 'default' : 'pointer',
                                  transition: 'all 0.2s ease',
                                }}
                              >
                                <input
                                  type="checkbox"
                                  disabled={isAdminUser}
                                  checked={isEnabled}
                                  onChange={() => toggleUserModulePermission(u.email, moduleItem.id)}
                                  style={{
                                    accentColor: '#38bdf8',
                                    width: '16px',
                                    height: '16px',
                                    cursor: isAdminUser ? 'default' : 'pointer',
                                  }}
                                />
                                <ModIcon size={16} color={isEnabled ? '#38bdf8' : '#64748b'} />
                                <div style={{ display: 'flex', flexDirection: 'column' }}>
                                  <span style={{
                                    fontSize: '0.82rem',
                                    fontWeight: isEnabled ? '700' : '500',
                                    color: isEnabled ? '#f8fafc' : '#64748b',
                                  }}>
                                    {moduleItem.label}
                                  </span>
                                </div>
                              </label>
                            );
                          })}
                        </div>

                        {/* ACCIONES Y FUNCIONES ESPECÍFICAS DE COCINERO (DOCUMENTO MAESTRO RF-07, RN-05, RN-06, SECCIÓN 4.7) */}
                        {(u.role === 'COCINERO' || userPerms.includes('KITCHEN') || isAdminUser) && (
                          <div style={{
                            marginTop: '12px',
                            padding: '14px 16px',
                            borderRadius: '12px',
                            background: 'rgba(249, 115, 22, 0.05)',
                            border: '1px solid rgba(249, 115, 22, 0.22)',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '10px',
                          }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <ChefHat size={16} color="#f97316" />
                                <span style={{ fontSize: '0.84rem', fontWeight: '800', color: '#fed7aa', letterSpacing: '0.02em' }}>
                                  Funciones Operativas de Cocinero / Pantalla KDS (Documento Maestro)
                                </span>
                              </div>
                              <span style={{ fontSize: '0.72rem', color: '#fdba74', background: 'rgba(249, 115, 22, 0.15)', padding: '2px 8px', borderRadius: '6px', fontWeight: '700' }}>
                                RF-07 &bull; RN-05 &bull; RN-06
                              </span>
                            </div>

                            <p style={{ fontSize: '0.74rem', color: '#94a3b8', margin: 0 }}>
                              Activa o desactiva qué tareas puede realizar este usuario en cocina y pantalla KDS.
                            </p>

                            <div style={{
                              display: 'grid',
                              gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
                              gap: '8px',
                              marginTop: '4px',
                            }}>
                              {COCINERO_SPECIFIC_ACTIONS.map((action) => {
                                const activeActions = userActionPermissions[u.email] !== undefined
                                  ? userActionPermissions[u.email]
                                  : COCINERO_SPECIFIC_ACTIONS.map(a => a.id);
                                const isActionActive = isAdminUser || activeActions.includes(action.id);

                                return (
                                  <label
                                    key={action.id}
                                    style={{
                                      display: 'flex',
                                      alignItems: 'flex-start',
                                      gap: '9px',
                                      padding: '8px 10px',
                                      borderRadius: '8px',
                                      background: isActionActive ? 'rgba(249, 115, 22, 0.1)' : 'rgba(255, 255, 255, 0.02)',
                                      border: isActionActive ? '1px solid rgba(249, 115, 22, 0.35)' : '1px solid rgba(255, 255, 255, 0.05)',
                                      cursor: isAdminUser ? 'default' : 'pointer',
                                      transition: 'all 0.18s ease',
                                    }}
                                  >
                                    <input
                                      type="checkbox"
                                      disabled={isAdminUser}
                                      checked={isActionActive}
                                      onChange={() => toggleUserActionPermission(u.email, action.id)}
                                      style={{
                                        accentColor: '#f97316',
                                        width: '15px',
                                        height: '15px',
                                        marginTop: '2px',
                                        cursor: isAdminUser ? 'default' : 'pointer',
                                      }}
                                    />
                                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                                      <span style={{
                                        fontSize: '0.8rem',
                                        fontWeight: isActionActive ? '700' : '500',
                                        color: isActionActive ? '#fff' : '#64748b',
                                      }}>
                                        {action.label}
                                      </span>
                                      <span style={{ fontSize: '0.68rem', color: isActionActive ? '#cbd5e1' : '#475569', marginTop: '2px', lineHeight: 1.3 }}>
                                        {action.desc}
                                      </span>
                                    </div>
                                  </label>
                                );
                              })}
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
              </div>
            )}
          </div>
          )}

          {/* =========================================================================
              SUB-PESTAÑA 3: PERSONALIZACIÓN VISUAL, LOGOTIPO & FONDO PARALLAX
              ========================================================================= */}
          {settingsSubTab === 'THEME' && (
            <div className="glass-panel animate-fade-in" style={{ padding: '26px', borderRadius: '20px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <h3 style={{ fontSize: '1.2rem', color: '#f8fafc', fontWeight: '800' }}>
                    Personalización del Sistema & Fondo con Efecto Parallax
                  </h3>
                  <span className="badge badge-gold" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Sparkles size={14} />
                    Personalización en Vivo
                  </span>
                </div>
                <p style={{ color: '#94a3b8', fontSize: '0.85rem', marginTop: '4px' }}>
                  Ajusta la paleta cromática de la aplicación, el logotipo corporativo y el fondo ambiental con rotación de imágenes y efecto parallax dinámico.
                </p>
              </div>

              {/* SECCIÓN 1: LOGOTIPO DE LA EMPRESA */}
              <div style={{ background: 'rgba(15, 23, 42, 0.65)', padding: '20px', borderRadius: '16px', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
                <h4 style={{ fontSize: '1rem', color: '#f8fafc', fontWeight: '800', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Image size={18} color="#f59e0b" />
                  Logotipo Oficial del Restaurante
                </h4>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px', alignItems: 'center' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.82rem', color: '#cbd5e1', marginBottom: '6px' }}>
                      URL del Logotipo o Cargar Archivo
                    </label>
                    <input
                      type="text"
                      placeholder="https://ejemplo.com/logo-restaurante.png"
                      value={themeSettings.logoUrl || ''}
                      onChange={(e) => updateThemeSettings({ logoUrl: e.target.value })}
                      style={{
                        width: '100%',
                        padding: '10px 14px',
                        borderRadius: '8px',
                        background: 'rgba(255, 255, 255, 0.05)',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                        color: '#fff',
                        marginBottom: '10px'
                      }}
                    />
                    <label style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '8px',
                      padding: '8px 14px',
                      borderRadius: '8px',
                      background: 'rgba(56, 189, 248, 0.12)',
                      color: '#38bdf8',
                      border: '1px solid rgba(56, 189, 248, 0.3)',
                      fontSize: '0.82rem',
                      fontWeight: '700',
                      cursor: 'pointer'
                    }}>
                      <Upload size={14} />
                      Subir Imagen desde el Equipo
                      <input
                        type="file"
                        accept="image/*"
                        style={{ display: 'none' }}
                        onChange={(e) => {
                          const file = e.target.files?.[0];
                          if (file) {
                            const reader = new FileReader();
                            reader.onload = (uploadEvent) => {
                              updateThemeSettings({ logoUrl: uploadEvent.target.result });
                              notify('Logotipo cargado exitosamente');
                            };
                            reader.readAsDataURL(file);
                          }
                        }}
                      />
                    </label>
                  </div>

                  {/* Vista Previa del Logotipo */}
                  <div style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '16px',
                    borderRadius: '12px',
                    background: 'rgba(0, 0, 0, 0.4)',
                    border: '1px dashed rgba(255, 255, 255, 0.15)',
                    minHeight: '110px'
                  }}>
                    {themeSettings.logoUrl ? (
                      <div style={{ textAlign: 'center' }}>
                        <img
                          src={themeSettings.logoUrl}
                          alt="Logo Oficial"
                          style={{ maxHeight: '70px', maxWidth: '180px', objectFit: 'contain' }}
                        />
                        <div style={{ marginTop: '6px' }}>
                          <button
                            type="button"
                            onClick={() => updateThemeSettings({ logoUrl: '' })}
                            style={{ background: 'none', border: 'none', color: '#fb7185', fontSize: '0.72rem', cursor: 'pointer', textDecoration: 'underline' }}
                          >
                            Quitar logotipo
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div style={{ color: '#94a3b8', fontSize: '0.82rem', textAlign: 'center' }}>
                        Sin logotipo cargado (Se usará el emblema tipográfico por defecto)
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* SECCIÓN 2: PALETA CROMÁTICA DEL SISTEMA */}
              <div style={{ background: 'rgba(15, 23, 42, 0.65)', padding: '20px', borderRadius: '16px', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
                <h4 style={{ fontSize: '1rem', color: '#f8fafc', fontWeight: '800', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Palette size={18} color="#38bdf8" />
                  Color Principal & Secundario del Sistema
                </h4>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '20px' }}>
                  {/* Color Principal */}
                  <div style={{ padding: '14px', borderRadius: '12px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
                    <label style={{ display: 'block', fontSize: '0.84rem', fontWeight: '700', color: '#cbd5e1', marginBottom: '8px' }}>
                      Color Principal (Destacados, Botones & Acentos)
                    </label>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <input
                        type="color"
                        value={themeSettings.primaryColor}
                        onChange={(e) => updateThemeSettings({ primaryColor: e.target.value })}
                        style={{ width: '46px', height: '40px', border: 'none', borderRadius: '8px', cursor: 'pointer', background: 'transparent' }}
                      />
                      <input
                        type="text"
                        value={themeSettings.primaryColor}
                        onChange={(e) => updateThemeSettings({ primaryColor: e.target.value })}
                        style={{
                          flex: 1,
                          padding: '8px 12px',
                          borderRadius: '8px',
                          background: 'rgba(255,255,255,0.05)',
                          border: '1px solid rgba(255,255,255,0.1)',
                          color: '#fff',
                          fontWeight: '700'
                        }}
                      />
                    </div>
                  </div>

                  {/* Color Secundario */}
                  <div style={{ padding: '14px', borderRadius: '12px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
                    <label style={{ display: 'block', fontSize: '0.84rem', fontWeight: '700', color: '#cbd5e1', marginBottom: '8px' }}>
                      Color Secundario (Gradientes, Alertas & Badges)
                    </label>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <input
                        type="color"
                        value={themeSettings.secondaryColor}
                        onChange={(e) => updateThemeSettings({ secondaryColor: e.target.value })}
                        style={{ width: '46px', height: '40px', border: 'none', borderRadius: '8px', cursor: 'pointer', background: 'transparent' }}
                      />
                      <input
                        type="text"
                        value={themeSettings.secondaryColor}
                        onChange={(e) => updateThemeSettings({ secondaryColor: e.target.value })}
                        style={{
                          flex: 1,
                          padding: '8px 12px',
                          borderRadius: '8px',
                          background: 'rgba(255,255,255,0.05)',
                          border: '1px solid rgba(255,255,255,0.1)',
                          color: '#fff',
                          fontWeight: '700'
                        }}
                      />
                    </div>
                  </div>
                </div>

                {/* Botones de Paletas Predefinidas Populares */}
                <div style={{ marginTop: '16px' }}>
                  <span style={{ fontSize: '0.78rem', color: '#94a3b8', display: 'block', marginBottom: '8px' }}>
                    Paletas Rápidas Recomendadas:
                  </span>
                  <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                    {[
                      { name: 'Imperial Gold & Ruby', p: '#f2b23e', s: '#e0472f' },
                      { name: 'Emerald & Gold', p: '#10b981', s: '#f59e0b' },
                      { name: 'Cyberpunk Neon', p: '#06b6d4', s: '#ec4899' },
                      { name: 'Ocean Luxury', p: '#38bdf8', s: '#6366f1' },
                    ].map((pal, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => updateThemeSettings({ primaryColor: pal.p, secondaryColor: pal.s })}
                        style={{
                          padding: '6px 12px',
                          borderRadius: '8px',
                          background: 'rgba(255,255,255,0.05)',
                          border: '1px solid rgba(255,255,255,0.1)',
                          color: '#cbd5e1',
                          fontSize: '0.78rem',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                          cursor: 'pointer'
                        }}
                      >
                        <span style={{ width: '12px', height: '12px', borderRadius: '50%', background: pal.p }} />
                        <span style={{ width: '12px', height: '12px', borderRadius: '50%', background: pal.s }} />
                        <span>{pal.name}</span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* SECCIÓN 3: CONFIGURACIÓN AVANZADA DE FONDO PARALLAX */}
              <div style={{ background: 'rgba(15, 23, 42, 0.65)', padding: '20px', borderRadius: '16px', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '10px' }}>
                  <h4 style={{ fontSize: '1rem', color: '#f8fafc', fontWeight: '800', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Sparkles size={18} color="#ec4899" />
                    Fondo con Efecto Parallax & Animación Continua
                  </h4>

                  {/* Switch para Activar / Quitar el fondo parallax */}
                  <label style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }}>
                    <span style={{ fontSize: '0.85rem', fontWeight: '700', color: themeSettings.parallaxEnabled ? '#10b981' : '#94a3b8' }}>
                      {themeSettings.parallaxEnabled ? 'Fondo Parallax Activado' : 'Fondo Parallax Desactivado'}
                    </span>
                    <input
                      type="checkbox"
                      checked={!!themeSettings.parallaxEnabled}
                      onChange={(e) => updateThemeSettings({ parallaxEnabled: e.target.checked })}
                      style={{ width: '20px', height: '20px', accentColor: '#10b981', cursor: 'pointer' }}
                    />
                  </label>
                </div>

                {themeSettings.parallaxEnabled && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
                    {/* Parámetros de Animación y Tiempos */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '14px' }}>
                      {/* Tipo de Animación */}
                      <div>
                        <label style={{ display: 'block', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '6px' }}>
                          Tipo de Animación
                        </label>
                        <select
                          value={themeSettings.animationType || 'fade-zoom'}
                          onChange={(e) => updateThemeSettings({ animationType: e.target.value })}
                          style={{
                            width: '100%',
                            padding: '9px 12px',
                            borderRadius: '8px',
                            background: '#121824',
                            border: '1px solid rgba(255,255,255,0.1)',
                            color: '#fff',
                            fontSize: '0.84rem'
                          }}
                        >
                          <option value="fade-zoom">Zoom Fluido (Fade + Zoom)</option>
                          <option value="ken-burns">Efecto Cine Ken Burns (Pan + Zoom)</option>
                          <option value="pan-left">Desplazamiento Suave (Pan Lateral)</option>
                        </select>
                      </div>

                      {/* Tiempo de duración de cada imagen */}
                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '6px' }}>
                          <span>Duración por Imagen</span>
                          <span style={{ color: '#f59e0b', fontWeight: '800' }}>{themeSettings.slideDuration || 6}s</span>
                        </div>
                        <input
                          type="range"
                          min="2"
                          max="20"
                          step="1"
                          value={themeSettings.slideDuration || 6}
                          onChange={(e) => updateThemeSettings({ slideDuration: parseFloat(e.target.value) })}
                          style={{ width: '100%', accentColor: '#f59e0b' }}
                        />
                      </div>

                      {/* Tiempo de duración de la transición */}
                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '6px' }}>
                          <span>Duración de Transición</span>
                          <span style={{ color: '#38bdf8', fontWeight: '800' }}>{themeSettings.animationDuration || 1.5}s</span>
                        </div>
                        <input
                          type="range"
                          min="0.5"
                          max="5"
                          step="0.5"
                          value={themeSettings.animationDuration || 1.5}
                          onChange={(e) => updateThemeSettings({ animationDuration: parseFloat(e.target.value) })}
                          style={{ width: '100%', accentColor: '#38bdf8' }}
                        />
                      </div>
                    </div>

                    {/* Capas y Transparencias */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '14px', paddingTop: '10px', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                      {/* Transparencia de la Imagen */}
                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '6px' }}>
                          <span>Opacidad de la Imagen de Fondo</span>
                          <span style={{ color: '#10b981', fontWeight: '800' }}>{Math.round((themeSettings.imageOpacity ?? 0.25) * 100)}%</span>
                        </div>
                        <input
                          type="range"
                          min="0.05"
                          max="1.0"
                          step="0.05"
                          value={themeSettings.imageOpacity ?? 0.25}
                          onChange={(e) => updateThemeSettings({ imageOpacity: parseFloat(e.target.value) })}
                          style={{ width: '100%', accentColor: '#10b981' }}
                        />
                      </div>

                      {/* Transparencia / Opacidad de la Capa Superior Oscura */}
                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '6px' }}>
                          <span>Opacidad Capa Superior (Contraste)</span>
                          <span style={{ color: '#ec4899', fontWeight: '800' }}>{Math.round((themeSettings.overlayOpacity ?? 0.85) * 100)}%</span>
                        </div>
                        <input
                          type="range"
                          min="0.0"
                          max="1.0"
                          step="0.05"
                          value={themeSettings.overlayOpacity ?? 0.85}
                          onChange={(e) => updateThemeSettings({ overlayOpacity: parseFloat(e.target.value) })}
                          style={{ width: '100%', accentColor: '#ec4899' }}
                        />
                      </div>
                    </div>

                    {/* Galería de Imágenes Seleccionadas para Parallax */}
                    <div style={{ paddingTop: '10px', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                        <span style={{ fontSize: '0.84rem', fontWeight: '700', color: '#cbd5e1' }}>
                          Imágenes en Rotación ({themeSettings.parallaxImages?.length || 0})
                        </span>
                        <button
                          type="button"
                          onClick={() => {
                            const newUrl = prompt('Ingresa la URL de la imagen que deseas agregar al fondo parallax:');
                            if (newUrl && newUrl.trim()) {
                              updateThemeSettings({
                                parallaxImages: [...(themeSettings.parallaxImages || []), newUrl.trim()]
                              });
                            }
                          }}
                          style={{
                            padding: '4px 10px',
                            borderRadius: '6px',
                            background: 'rgba(56, 189, 248, 0.15)',
                            color: '#38bdf8',
                            border: '1px solid rgba(56, 189, 248, 0.3)',
                            fontSize: '0.74rem',
                            fontWeight: '700',
                            cursor: 'pointer'
                          }}
                        >
                          + Agregar URL
                        </button>
                      </div>

                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))', gap: '10px' }}>
                        {(themeSettings.parallaxImages || []).map((imgUrl, i) => (
                          <div key={i} style={{ position: 'relative', height: '75px', borderRadius: '10px', overflow: 'hidden', border: '1px solid rgba(255,255,255,0.1)' }}>
                            <img src={imgUrl} alt={`Parallax ${i}`} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                            <button
                              type="button"
                              onClick={() => {
                                updateThemeSettings({
                                  parallaxImages: themeSettings.parallaxImages.filter((_, idx) => idx !== i)
                                });
                              }}
                              style={{
                                position: 'absolute',
                                top: '4px',
                                right: '4px',
                                background: 'rgba(239, 68, 68, 0.8)',
                                border: 'none',
                                borderRadius: '50%',
                                width: '20px',
                                height: '20px',
                                color: '#fff',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                cursor: 'pointer',
                                fontSize: '11px',
                                fontWeight: '900'
                              }}
                              title="Quitar imagen"
                            >
                              ✕
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Botones de Guardar / Restablecer */}
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                <button
                  type="button"
                  onClick={() => {
                    resetThemeSettings();
                    notify('Ajustes visuales restaurados a los valores de fábrica');
                  }}
                  style={{
                    padding: '10px 18px',
                    borderRadius: '10px',
                    background: 'rgba(255, 255, 255, 0.05)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    color: '#94a3b8',
                    fontSize: '0.85rem',
                    cursor: 'pointer'
                  }}
                >
                  Restablecer por Defecto
                </button>
                <button
                  type="button"
                  onClick={() => notify('¡Personalización visual y parallax guardada exitosamente!')}
                  className="btn-primary"
                  style={{ padding: '10px 22px', fontSize: '0.88rem', display: 'flex', alignItems: 'center', gap: '6px' }}
                >
                  <Save size={16} />
                  Guardar Personalización
                </button>
              </div>
            </div>
          )}
        </div>
      )}


          </div>
        </div>
      )}

      {/* --- MODAL EDITAR / CREAR PLATO --- */}
      {showDishModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.85)',
          backdropFilter: 'blur(8px)',
          zIndex: 1000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '16px',
        }}>
          <div className="glass-panel" style={{
            maxWidth: '560px',
            width: '100%',
            maxHeight: '90vh',
            overflowY: 'auto',
            padding: '28px',
            borderRadius: '20px',
            background: '#0d131f',
            border: '1px solid rgba(245, 158, 11, 0.3)',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3 style={{ fontSize: '1.3rem', color: '#f8fafc', fontWeight: '800' }}>
                {editingDish ? `Editar: ${editingDish.name}` : 'Crear Nuevo Plato en la Carta'}
              </h3>
              <button onClick={() => setShowDishModal(false)} style={{ background: 'none', color: '#94a3b8' }}>
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSaveDish} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>
                  Nombre del Plato *
                </label>
                <input
                  type="text"
                  required
                  value={dishForm.name}
                  onChange={(e) => setDishForm({ ...dishForm, name: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '10px 14px',
                    borderRadius: '8px',
                    background: 'rgba(255, 255, 255, 0.05)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    color: '#fff',
                  }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>
                    Categoría *
                  </label>
                  <select
                    value={dishForm.category_id}
                    onChange={(e) => setDishForm({ ...dishForm, category_id: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '10px 14px',
                      borderRadius: '8px',
                      background: '#121824',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                      color: '#fff',
                    }}
                  >
                    {categories.map((c) => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>
                    Precio Base (COP) *
                  </label>
                  <input
                    type="number"
                    step="500"
                    required
                    value={dishForm.price_base}
                    onChange={(e) => setDishForm({ ...dishForm, price_base: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '10px 14px',
                      borderRadius: '8px',
                      background: 'rgba(255, 255, 255, 0.05)',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                      color: '#fff',
                    }}
                  />
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>
                  Descripción Corta
                </label>
                <input
                  type="text"
                  value={dishForm.short_description}
                  onChange={(e) => setDishForm({ ...dishForm, short_description: e.target.value })}
                  placeholder="Ej: Salteado tradicional con verduras y proteína"
                  style={{
                    width: '100%',
                    padding: '10px 14px',
                    borderRadius: '8px',
                    background: 'rgba(255, 255, 255, 0.05)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    color: '#fff',
                  }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>
                    Tiempo Estimado (min)
                  </label>
                  <input
                    type="number"
                    value={dishForm.preparation_time_minutes}
                    onChange={(e) => setDishForm({ ...dishForm, preparation_time_minutes: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '10px 14px',
                      borderRadius: '8px',
                      background: 'rgba(255, 255, 255, 0.05)',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                      color: '#fff',
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>
                    Calorías (kcal)
                  </label>
                  <input
                    type="number"
                    value={dishForm.calories_estimate}
                    onChange={(e) => setDishForm({ ...dishForm, calories_estimate: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '10px 14px',
                      borderRadius: '8px',
                      background: 'rgba(255, 255, 255, 0.05)',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                      color: '#fff',
                    }}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', gap: '20px', marginTop: '6px' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.88rem', color: '#cbd5e1', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={dishForm.available}
                    onChange={(e) => setDishForm({ ...dishForm, available: e.target.checked })}
                  />
                  Disponible para Comensales
                </label>

                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.88rem', color: '#cbd5e1', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={dishForm.is_featured}
                    onChange={(e) => setDishForm({ ...dishForm, is_featured: e.target.checked })}
                  />
                  Destacado en Portada
                </label>
              </div>

              <div style={{ display: 'flex', gap: '10px', marginTop: '16px' }}>
                <button
                  type="button"
                  onClick={() => setShowDishModal(false)}
                  style={{
                    flex: 1,
                    padding: '12px',
                    borderRadius: '10px',
                    background: 'rgba(255, 255, 255, 0.08)',
                    color: '#fff',
                  }}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="btn-primary"
                  style={{ flex: 2, padding: '12px' }}
                >
                  <Save size={16} />
                  Guardar Cambios
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* --- MODAL EDITAR / CREAR MESA --- */}
      {showTableModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.85)',
          backdropFilter: 'blur(8px)',
          zIndex: 1000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '16px',
        }}>
          <div className="glass-panel" style={{
            maxWidth: '440px',
            width: '100%',
            padding: '24px',
            borderRadius: '20px',
            background: '#0d131f',
            border: '1px solid rgba(245, 158, 11, 0.3)',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '1.25rem', color: '#f8fafc', fontWeight: '800' }}>
                {editingTable ? `Editar Mesa #${editingTable.number}` : 'Agregar Nueva Mesa al Salón'}
              </h3>
              <button onClick={() => setShowTableModal(false)} style={{ background: 'none', color: '#94a3b8' }}>
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSaveTable} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>
                  Número de Mesa
                </label>
                <input
                  type="number"
                  required
                  disabled={!!editingTable}
                  value={tableForm.number}
                  onChange={(e) => setTableForm({ ...tableForm, number: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '10px 14px',
                    borderRadius: '8px',
                    background: 'rgba(255, 255, 255, 0.05)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    color: '#fff',
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>
                  Capacidad de Comensales
                </label>
                <input
                  type="number"
                  min="1"
                  max="20"
                  required
                  value={tableForm.capacity}
                  onChange={(e) => setTableForm({ ...tableForm, capacity: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '10px 14px',
                    borderRadius: '8px',
                    background: 'rgba(255, 255, 255, 0.05)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    color: '#fff',
                  }}
                />
              </div>

              {editingTable && (
                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>
                    Estado de la Mesa
                  </label>
                  <select
                    value={tableForm.status}
                    onChange={(e) => setTableForm({ ...tableForm, status: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '10px 14px',
                      borderRadius: '8px',
                      background: '#121824',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                      color: '#fff',
                    }}
                  >
                    <option value="LIBRE">LIBRE</option>
                    <option value="OCUPADA">OCUPADA</option>
                    <option value="RESERVADA">RESERVADA</option>
                    <option value="BLOQUEADA">BLOQUEADA</option>
                  </select>
                </div>
              )}

              <div style={{ display: 'flex', gap: '10px', marginTop: '14px' }}>
                <button
                  type="button"
                  onClick={() => setShowTableModal(false)}
                  style={{
                    flex: 1,
                    padding: '12px',
                    borderRadius: '10px',
                    background: 'rgba(255, 255, 255, 0.08)',
                    color: '#fff',
                  }}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="btn-primary"
                  style={{ flex: 2, padding: '12px' }}
                >
                  <Save size={16} />
                  Guardar Mesa
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* --- MODAL CONTROL TOTAL DE RECETA POR PLATO --- */}
      {recipeModalDish && (
        <RecipeEditorModal
          dish={recipeModalDish}
          allIngredients={ingredients}
          token={token}
          onClose={() => setRecipeModalDish(null)}
          onSuccess={async (msg) => {
            notify(msg);
            await loadAllData();
          }}
        />
      )}

      {/* --- MODAL 1: GESTIÓN Y AJUSTE DE STOCK POR INGREDIENTE --- */}
      {selectedStockIngredient && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.85)',
          backdropFilter: 'blur(8px)',
          zIndex: 1000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '16px',
        }}>
          <div className="glass-panel" style={{
            maxWidth: '460px',
            width: '100%',
            padding: '26px',
            borderRadius: '20px',
            background: '#0d131f',
            border: '1px solid rgba(245, 158, 11, 0.35)',
            boxShadow: '0 20px 50px rgba(0, 0, 0, 0.8)',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ fontSize: '1.6rem' }}>{getIngredientIconInfo(selectedStockIngredient.name).emoji}</span>
                <div>
                  <h3 style={{ fontSize: '1.2rem', color: '#f8fafc', fontWeight: '800' }}>
                    {selectedStockIngredient.name}
                  </h3>
                  <span style={{ fontSize: '0.78rem', color: '#94a3b8' }}>
                    Control de Existencias & Almacén
                  </span>
                </div>
              </div>
              <button onClick={() => setSelectedStockIngredient(null)} style={{ background: 'none', color: '#94a3b8' }}>
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSaveStockItem} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.82rem', color: '#cbd5e1', marginBottom: '6px' }}>
                  Cantidad en Stock Actual ({selectedStockIngredient.unit || 'g'})
                </label>
                <input
                  type="number"
                  step="0.1"
                  required
                  value={selectedStockIngredient.edit_current_stock}
                  onChange={(e) => setSelectedStockIngredient({ ...selectedStockIngredient, edit_current_stock: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '10px 14px',
                    borderRadius: '8px',
                    background: 'rgba(255, 255, 255, 0.05)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    color: '#fff',
                    fontSize: '1rem',
                    fontWeight: '700',
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.82rem', color: '#cbd5e1', marginBottom: '6px' }}>
                  Stock Mínimo Requerido ({selectedStockIngredient.unit || 'g'})
                </label>
                <input
                  type="number"
                  step="0.1"
                  required
                  value={selectedStockIngredient.edit_min_stock}
                  onChange={(e) => setSelectedStockIngredient({ ...selectedStockIngredient, edit_min_stock: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '10px 14px',
                    borderRadius: '8px',
                    background: 'rgba(255, 255, 255, 0.05)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    color: '#fff',
                  }}
                />
              </div>

              <div style={{ display: 'flex', gap: '10px', marginTop: '14px' }}>
                <button
                  type="button"
                  onClick={() => handleDeleteStockItem(selectedStockIngredient)}
                  style={{
                    flex: 1,
                    padding: '11px',
                    borderRadius: '10px',
                    background: 'rgba(244, 63, 94, 0.15)',
                    color: '#fb7185',
                    border: '1px solid rgba(244, 63, 94, 0.3)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '6px',
                    fontWeight: '700',
                    fontSize: '0.82rem',
                    cursor: 'pointer',
                  }}
                >
                  <Trash2 size={15} />
                  Retirar Stock
                </button>
                <button
                  type="submit"
                  className="btn-primary"
                  style={{ flex: 1.5, padding: '11px', fontSize: '0.88rem' }}
                >
                  <Save size={15} />
                  Guardar Ajuste
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* --- MODAL 2: CREAR / EDITAR INGREDIENTE --- */}
      {showIngredientModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.85)',
          backdropFilter: 'blur(8px)',
          zIndex: 1000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '16px',
        }}>
          <div className="glass-panel" style={{
            maxWidth: '520px',
            width: '100%',
            maxHeight: '90vh',
            overflowY: 'auto',
            padding: '26px',
            borderRadius: '20px',
            background: '#0d131f',
            border: '1px solid rgba(56, 189, 248, 0.35)',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
              <h3 style={{ fontSize: '1.25rem', color: '#f8fafc', fontWeight: '800' }}>
                {editingIngredient ? `Editar: ${editingIngredient.name}` : 'Nuevo Ingrediente / Insumo'}
              </h3>
              <button onClick={() => setShowIngredientModal(false)} style={{ background: 'none', color: '#94a3b8' }}>
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSaveIngredient} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.82rem', color: '#cbd5e1', marginBottom: '6px' }}>
                  Nombre del Ingrediente *
                </label>
                <input
                  type="text"
                  required
                  value={ingredientForm.name}
                  onChange={(e) => setIngredientForm({ ...ingredientForm, name: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '10px 14px',
                    borderRadius: '8px',
                    background: 'rgba(255, 255, 255, 0.05)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    color: '#fff',
                  }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', color: '#cbd5e1', marginBottom: '6px' }}>
                    Unidad de Medida
                  </label>
                  <select
                    value={ingredientForm.unit}
                    onChange={(e) => setIngredientForm({ ...ingredientForm, unit: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '10px 14px',
                      borderRadius: '8px',
                      background: '#121824',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                      color: '#fff',
                    }}
                  >
                    <option value="GRAMO">GRAMO (g)</option>
                    <option value="MILILITRO">MILILITRO (ml)</option>
                    <option value="UNIDAD">UNIDAD (ud)</option>
                    <option value="KILOGRAMO">KILOGRAMO (kg)</option>
                    <option value="LITRO">LITRO (L)</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', color: '#cbd5e1', marginBottom: '6px' }}>
                    Precio como Extra (COP)
                  </label>
                  <input
                    type="number"
                    step="500"
                    min="0"
                    value={ingredientForm.price_extra}
                    onChange={(e) => setIngredientForm({ ...ingredientForm, price_extra: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '10px 14px',
                      borderRadius: '8px',
                      background: 'rgba(255, 255, 255, 0.05)',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                      color: '#fff',
                    }}
                  />
                </div>
              </div>

              {/* Parámetros Nutricionales */}
              <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '12px', borderRadius: '10px', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
                <div style={{ fontSize: '0.82rem', color: '#10b981', fontWeight: '700', marginBottom: '10px' }}>
                  🥗 Información Nutricional (por porción estándar)
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.72rem', color: '#94a3b8' }}>Calorías (kcal)</label>
                    <input
                      type="number"
                      value={ingredientForm.calories}
                      onChange={(e) => setIngredientForm({ ...ingredientForm, calories: e.target.value })}
                      style={{ width: '100%', padding: '6px 8px', borderRadius: '6px', background: 'rgba(255, 255, 255, 0.05)', border: '1px solid rgba(255, 255, 255, 0.1)', color: '#fff' }}
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.72rem', color: '#94a3b8' }}>Proteína (g)</label>
                    <input
                      type="number"
                      step="0.1"
                      value={ingredientForm.protein}
                      onChange={(e) => setIngredientForm({ ...ingredientForm, protein: e.target.value })}
                      style={{ width: '100%', padding: '6px 8px', borderRadius: '6px', background: 'rgba(255, 255, 255, 0.05)', border: '1px solid rgba(255, 255, 255, 0.1)', color: '#fff' }}
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.72rem', color: '#94a3b8' }}>Fibra (g)</label>
                    <input
                      type="number"
                      step="0.1"
                      value={ingredientForm.fiber}
                      onChange={(e) => setIngredientForm({ ...ingredientForm, fiber: e.target.value })}
                      style={{ width: '100%', padding: '6px 8px', borderRadius: '6px', background: 'rgba(255, 255, 255, 0.05)', border: '1px solid rgba(255, 255, 255, 0.1)', color: '#fff' }}
                    />
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '20px', marginTop: '4px' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.84rem', color: '#cbd5e1', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={ingredientForm.available}
                    onChange={(e) => setIngredientForm({ ...ingredientForm, available: e.target.checked })}
                  />
                  Disponible en Carta
                </label>

                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.84rem', color: '#cbd5e1', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={ingredientForm.is_organic}
                    onChange={(e) => setIngredientForm({ ...ingredientForm, is_organic: e.target.checked })}
                  />
                  Certificado Orgánico
                </label>
              </div>

              <div style={{ display: 'flex', gap: '10px', marginTop: '14px' }}>
                <button
                  type="button"
                  onClick={() => setShowIngredientModal(false)}
                  style={{
                    flex: 1,
                    padding: '12px',
                    borderRadius: '10px',
                    background: 'rgba(255, 255, 255, 0.08)',
                    color: '#fff',
                  }}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="btn-primary"
                  style={{ flex: 2, padding: '12px' }}
                >
                  <Save size={16} />
                  Guardar Ingrediente
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* --- MODAL 3: ÓRDENES Y VALOR TOTAL DEL PEDIDO DE LA MESA --- */}
      {selectedTableDetail && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.85)',
          backdropFilter: 'blur(8px)',
          zIndex: 1000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '16px',
        }}>
          <div className="glass-panel" style={{
            maxWidth: '580px',
            width: '100%',
            maxHeight: '90vh',
            overflowY: 'auto',
            padding: '28px',
            borderRadius: '22px',
            background: '#0d131f',
            border: '1px solid rgba(245, 158, 11, 0.4)',
            boxShadow: '0 20px 60px rgba(0, 0, 0, 0.85)',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <h3 style={{ fontSize: '1.4rem', color: '#f8fafc', fontWeight: '800' }}>
                    Mesa #{selectedTableDetail.table?.number}
                  </h3>
                  <span className={`badge ${selectedTableDetail.table?.status === 'OCUPADA' ? 'badge-gold' : 'badge-emerald'}`}>
                    {selectedTableDetail.table?.status}
                  </span>
                </div>
                <div style={{ fontSize: '0.82rem', color: '#94a3b8', marginTop: '4px' }}>
                  Capacidad: {selectedTableDetail.table?.capacity} comensales &bull; Salón Principal
                </div>
              </div>
              <button onClick={() => setSelectedTableDetail(null)} style={{ background: 'none', color: '#94a3b8' }}>
                <X size={22} />
              </button>
            </div>

            {/* Listado de órdenes activas y su desglose */}
            <div style={{ marginBottom: '20px' }}>
              <div style={{ fontSize: '0.88rem', fontWeight: '700', color: '#f8fafc', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Órdenes & Comandas en Curso ({selectedTableDetail.orders?.length || 0})
              </div>

              {selectedTableDetail.orders?.length === 0 ? (
                <div style={{ padding: '24px', textAlign: 'center', background: 'rgba(255, 255, 255, 0.02)', borderRadius: '12px', color: '#94a3b8', fontSize: '0.9rem' }}>
                  No hay pedidos pendientes ni abiertos en esta mesa actualmente.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {selectedTableDetail.orders.map((ord) => (
                    <div key={ord.id} style={{ background: 'rgba(255, 255, 255, 0.03)', borderRadius: '14px', padding: '16px', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px', borderBottom: '1px solid rgba(255, 255, 255, 0.06)', paddingBottom: '8px' }}>
                        <div>
                          <span style={{ fontWeight: '800', color: '#38bdf8', fontSize: '0.88rem' }}>
                            {ord.display_code || `Comanda #${ord.id.slice(0, 6)}`}
                          </span>
                          <span style={{ fontSize: '0.74rem', color: '#94a3b8', marginLeft: '8px' }}>
                            {new Date(ord.created_at).toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                        <span className={`badge ${ord.status === 'SERVIDA' ? 'badge-emerald' : 'badge-gold'}`} style={{ fontSize: '0.72rem' }}>
                          {ord.status}
                        </span>
                      </div>

                      {/* Ítems del pedido con valor individual */}
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        {(ord.items || []).map((it) => {
                          const itemQty = parseFloat(it.quantity || 1);
                          const itemUnitPrice = parseFloat(it.unit_price || it.price || 0);
                          const itemSubtotal = parseFloat(it.subtotal || itemQty * itemUnitPrice);
                          return (
                            <div key={it.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.84rem' }}>
                              <div>
                                <span style={{ fontWeight: '700', color: '#f8fafc' }}>
                                  {it.quantity}x {it.dish_name || 'Plato'}
                                </span>
                                {it.observations && (
                                  <div style={{ fontSize: '0.72rem', color: '#94a3b8', fontStyle: 'italic' }}>
                                    "{it.observations}"
                                  </div>
                                )}
                              </div>
                              <span style={{ fontWeight: '700', color: '#cbd5e1' }}>
                                ${itemSubtotal.toLocaleString('es-CO')}
                              </span>
                            </div>
                          );
                        })}
                      </div>

                      {/* Subtotal real de la comanda calculando items o total_amount */}
                      {(() => {
                        const comandaSubtotal = ord.items && ord.items.length > 0
                          ? ord.items.reduce((s, it) => s + parseFloat(it.subtotal || (it.quantity * (it.unit_price || it.price || 0))), 0)
                          : parseFloat(ord.subtotal || ord.total || ord.total_amount || 0);
                        return (
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '12px', paddingTop: '8px', borderTop: '1px solid rgba(255, 255, 255, 0.06)', fontWeight: '800', fontSize: '0.88rem' }}>
                            <span style={{ color: '#94a3b8' }}>Subtotal Comanda:</span>
                            <span style={{ color: '#fbbf24' }}>
                              ${comandaSubtotal.toLocaleString('es-CO')}
                            </span>
                          </div>
                        );
                      })()}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Total General de la Mesa: Subtotal de consumo + Total a cobrar */}
            {(() => {
              const ordersList = selectedTableDetail.orders || [];
              const mesaSubtotal = ordersList.reduce((acc, ord) => {
                if (ord.items && ord.items.length > 0) {
                  return acc + ord.items.reduce((s, it) => s + parseFloat(it.subtotal || (it.quantity * (it.unit_price || it.price || 0))), 0);
                }
                return acc + parseFloat(ord.subtotal || ord.total || ord.total_amount || 0);
              }, 0);

              const mesaTotal = ordersList.reduce((acc, ord) => {
                const ordTot = parseFloat(ord.total || ord.total_amount || 0);
                if (ordTot > 0) return acc + ordTot;
                if (ord.items && ord.items.length > 0) {
                  return acc + ord.items.reduce((s, it) => s + parseFloat(it.subtotal || (it.quantity * (it.unit_price || it.price || 0))), 0);
                }
                return acc;
              }, 0);

              const hasUnpaidOrders = ordersList.some((o) => o.status !== 'PAGADA' && o.status !== 'CANCELADA');

              const handleExecuteCharge = async () => {
                if (ordersList.length === 0) return;
                setIsProcessingTablePayment(true);
                try {
                  const paidOrderIds = new Set();
                  // Preparar y registrar cobro para cada orden de la mesa
                  for (const ord of ordersList) {
                    if (ord.status !== 'PAGADA' && ord.status !== 'CANCELADA') {
                      // 1. Asegurar que los platos de la orden estén entregados para permitir el cierre
                      if (ord.status === 'ABIERTA') {
                        if (ord.items && ord.items.length > 0) {
                          for (const it of ord.items) {
                            if (it.status !== 'ENTREGADO' && it.status !== 'CANCELADO') {
                              try {
                                await api.markItemDelivered(it.id, token);
                              } catch (e) {
                                console.warn('Item delivery sync warning:', e);
                              }
                            }
                          }
                        }
                        // 2. Cerrar la orden administrativamente (calcula totales definitivos)
                        let closedOrder = null;
                        try {
                          closedOrder = await api.closeOrderAdmin(ord.id, {}, token);
                        } catch (e) {
                          console.warn('Order close warning:', e);
                        }

                        // 3. Registrar el pago de la orden con el total exacto cerrado
                        const amountToPay = parseFloat(
                          closedOrder?.saldo_pendiente ||
                          closedOrder?.total ||
                          ord.total ||
                          ord.items?.reduce((s, it) => s + parseFloat(it.subtotal || 0), 0) ||
                          mesaTotal ||
                          0
                        );
                        if (amountToPay > 0) {
                          await api.payOrderAdmin(
                            ord.id,
                            {
                              payment_method: tablePaymentMethod,
                              amount: amountToPay,
                              reference: `MESA-${selectedTableDetail.table?.number}-${Date.now().toString().slice(-4)}`,
                              note: `Cobro en mesa #${selectedTableDetail.table?.number} vía panel de salón`,
                            },
                            token
                          );
                        }
                      } else {
                        // Orden ya cerrada: Pagar saldo pendiente o total
                        const amountToPay = parseFloat(ord.saldo_pendiente || ord.total || mesaTotal || 0);
                        if (amountToPay > 0) {
                          await api.payOrderAdmin(
                            ord.id,
                            {
                              payment_method: tablePaymentMethod,
                              amount: amountToPay,
                              reference: `MESA-${selectedTableDetail.table?.number}-${Date.now().toString().slice(-4)}`,
                              note: `Cobro en mesa #${selectedTableDetail.table?.number} vía panel de salón`,
                            },
                            token
                          );
                        }
                      }
                      paidOrderIds.add(ord.id);
                    }
                  }

                  // Liberar la mesa para dejarla disponible y en cero
                  const tableId = selectedTableDetail.table?.id;
                  const tableNumber = selectedTableDetail.table?.number;
                  if (tableId) {
                    await api.updateTable(
                      tableId,
                      { status: 'LIBRE' },
                      token
                    );
                  }

                  // Limpiar inmediatamente el estado local: Quitar ítems y dejar mesa en CERO
                  setActiveOrders((prev) =>
                    prev.map((o) => {
                      if (paidOrderIds.has(o.id) || (o.table_id === tableId || o.table_number === tableNumber)) {
                        return { ...o, status: 'PAGADA', items: [] };
                      }
                      return o;
                    })
                  );

                  // Limpiar el estado de mesa en la lista de mesas
                  setTables((prev) =>
                    prev.map((t) =>
                      t.id === tableId || t.number === tableNumber
                        ? { ...t, status: 'LIBRE' }
                        : t
                    )
                  );

                  // Quitar órdenes desplegadas de la mesa
                  if (tableId) {
                    setExpandedTableOrders((prev) => {
                      const updated = { ...prev };
                      delete updated[tableId];
                      return updated;
                    });
                  }

                  // Limpiar cachés locales asociadas a pedidos o mesa
                  try {
                    localStorage.removeItem('imperial_dish_customizations');
                    localStorage.removeItem('imperial_active_order');
                  } catch (e) {
                    // ignore
                  }

                  notify(`¡Cobro de $${mesaTotal.toLocaleString('es-CO')} registrado con éxito! Mesa #${selectedTableDetail.table?.number} liberada con $0 pendientes.`);
                  setSelectedTableDetail(null);
                  setShowChargeSection(false);
                  await loadAllData(true);
                } catch (err) {
                  notify(err.message || 'Error al procesar el cobro de la mesa', 'error');
                } finally {
                  setIsProcessingTablePayment(false);
                }
              };

              return (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                  {/* Tarjeta de Resumen Financiero de la Mesa */}
                  <div style={{
                    background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, rgba(245, 158, 11, 0.05) 100%)',
                    border: '1.5px solid rgba(245, 158, 11, 0.4)',
                    borderRadius: '16px',
                    padding: '16px 20px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '10px',
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '0.86rem', color: '#cbd5e1', fontWeight: '600' }}>
                        Subtotal Consumos de la Mesa:
                      </span>
                      <span style={{ fontSize: '1.05rem', fontWeight: '800', color: '#f8fafc' }}>
                        ${mesaSubtotal.toLocaleString('es-CO')}
                      </span>
                    </div>

                    <div style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      paddingTop: '8px',
                      borderTop: '1px solid rgba(245, 158, 11, 0.25)',
                    }}>
                      <div>
                        <div style={{ fontSize: '0.84rem', color: '#fbbf24', textTransform: 'uppercase', fontWeight: '900', letterSpacing: '0.05em' }}>
                          VALOR TOTAL DEL PEDIDO DE LA MESA
                        </div>
                        <div style={{ fontSize: '0.74rem', color: '#94a3b8', marginTop: '2px' }}>
                          Sumatoria consolidada de consumos activos
                        </div>
                      </div>
                      <div style={{ fontSize: '1.65rem', fontWeight: '900', color: '#fbbf24', textShadow: '0 2px 10px rgba(245, 158, 11, 0.3)' }}>
                        ${mesaTotal.toLocaleString('es-CO')}
                      </div>
                    </div>
                  </div>

                  {/* Panel Interactivo de Cobro si se pulsa "Cobrar Mesa" */}
                  {showChargeSection && hasUnpaidOrders && (
                    <div className="animate-fade-in" style={{
                      background: 'rgba(15, 23, 42, 0.85)',
                      padding: '16px 18px',
                      borderRadius: '14px',
                      border: '1px solid rgba(56, 189, 248, 0.35)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '12px',
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '0.88rem', fontWeight: '800', color: '#38bdf8' }}>
                          Seleccionar Medio de Pago para el Cobro:
                        </span>
                        <span style={{ fontSize: '0.78rem', color: '#94a3b8' }}>
                          Mesa #{selectedTableDetail.table?.number}
                        </span>
                      </div>

                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
                        {[
                          { id: 'EFECTIVO', label: 'Efectivo', icon: DollarSign },
                          { id: 'TARJETA', label: 'Tarjeta', icon: CreditCard },
                          { id: 'TRANSFERENCIA', label: 'Transferencia', icon: CheckCircle2 },
                        ].map((pm) => {
                          const IconComp = pm.icon;
                          const isSel = tablePaymentMethod === pm.id;
                          return (
                            <button
                              key={pm.id}
                              type="button"
                              onClick={() => setTablePaymentMethod(pm.id)}
                              style={{
                                padding: '10px 8px',
                                borderRadius: '10px',
                                background: isSel ? 'rgba(56, 189, 248, 0.2)' : 'rgba(255, 255, 255, 0.04)',
                                border: isSel ? '1.5px solid #38bdf8' : '1px solid rgba(255, 255, 255, 0.08)',
                                color: isSel ? '#38bdf8' : '#cbd5e1',
                                fontWeight: isSel ? '800' : '600',
                                fontSize: '0.8rem',
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                gap: '6px',
                                cursor: 'pointer',
                              }}
                            >
                              <IconComp size={16} />
                              {pm.label}
                            </button>
                          );
                        })}
                      </div>

                      <div style={{ display: 'flex', gap: '10px', marginTop: '6px' }}>
                        <button
                          type="button"
                          onClick={() => setShowChargeSection(false)}
                          style={{
                            flex: 1,
                            padding: '10px',
                            borderRadius: '10px',
                            background: 'rgba(255, 255, 255, 0.06)',
                            color: '#94a3b8',
                            border: 'none',
                            fontSize: '0.84rem',
                            fontWeight: '600',
                            cursor: 'pointer',
                          }}
                        >
                          Cancelar
                        </button>
                        <button
                          type="button"
                          onClick={handleExecuteCharge}
                          disabled={isProcessingTablePayment}
                          className="btn-primary"
                          style={{
                            flex: 2,
                            padding: '10px',
                            fontSize: '0.88rem',
                            background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                            color: '#fff',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: '8px',
                          }}
                        >
                          <CheckCircle2 size={16} />
                          {isProcessingTablePayment ? 'Procesando Pago...' : `Confirmar Cobro ($${mesaTotal.toLocaleString('es-CO')})`}
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Botones Inferiores: Cobrar Mesa y Cerrar Detalle */}
                  <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '4px' }}>
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedTableDetail(null);
                        setShowChargeSection(false);
                      }}
                      style={{
                        padding: '10px 20px',
                        borderRadius: '10px',
                        background: 'rgba(255, 255, 255, 0.06)',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                        color: '#cbd5e1',
                        fontSize: '0.9rem',
                        fontWeight: '700',
                        cursor: 'pointer',
                      }}
                    >
                      Cerrar Detalle
                    </button>

                    {/* Botón Descargar Factura PDF: Solo aparece cuando la mesa ya ha sido cobrada / pagada */}
                    {ordersList.length > 0 && !hasUnpaidOrders && (
                      <a
                        href={api.getInvoicePdfUrl(ordersList[0].id, selectedTableDetail.table?.qr_code || selectedTableDetail.table?.codigo_qr)}
                        target="_blank"
                        rel="noreferrer"
                        download
                        style={{
                          padding: '10px 18px',
                          borderRadius: '10px',
                          background: 'rgba(56, 189, 248, 0.15)',
                          border: '1px solid rgba(56, 189, 248, 0.35)',
                          color: '#38bdf8',
                          fontSize: '0.88rem',
                          fontWeight: '700',
                          textDecoration: 'none',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                          cursor: 'pointer',
                        }}
                        title="Descargar factura de venta en PDF"
                      >
                        <FileText size={16} />
                        Factura PDF
                      </a>
                    )}

                    {hasUnpaidOrders && !showChargeSection && (
                      <button
                        type="button"
                        onClick={() => setShowChargeSection(true)}
                        className="btn-primary"
                        style={{
                          padding: '10px 26px',
                          fontSize: '0.92rem',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '8px',
                          background: 'linear-gradient(135deg, #f59e0b 0%, #ea580c 100%)',
                          color: '#fff',
                          fontWeight: '800',
                          boxShadow: '0 8px 25px rgba(245, 158, 11, 0.35)',
                        }}
                      >
                        <CreditCard size={18} />
                        Cobrar Mesa
                      </button>
                    )}
                  </div>
                </div>
              );
            })()}
          </div>
        </div>
      )}

      {/* --- MODAL 4: INFORMACIÓN NUTRICIONAL DEL PLATO EN EL CENTRO --- */}
      {nutritionModalDish && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.85)',
          backdropFilter: 'blur(10px)',
          zIndex: 1100,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '20px',
        }}>
          <div className="glass-panel" style={{
            maxWidth: '560px',
            width: '100%',
            padding: '30px',
            borderRadius: '24px',
            background: '#0d131f',
            border: '1.5px solid #f59e0b',
            boxShadow: '0 25px 70px rgba(245, 158, 11, 0.25)',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span className="badge badge-gold" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Sparkles size={13} />
                    Ficha Nutricional Oficial
                  </span>
                </div>
                <h3 style={{ fontSize: '1.4rem', color: '#f8fafc', fontWeight: '800', marginTop: '6px' }}>
                  {nutritionModalDish.name}
                </h3>
                <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
                  Estimación basada en porción estándar y técnica culinaria Imperial
                </div>
              </div>
              <button onClick={() => setNutritionModalDish(null)} style={{ background: 'none', color: '#94a3b8' }}>
                <X size={22} />
              </button>
            </div>

            {/* Cuadrícula de 8 beneficios y macronutrientes idéntica a la imagen del usuario */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(2, 1fr)',
              gap: '12px',
              marginBottom: '24px',
            }}>
              {/* 1. APORTE CALÓRICO */}
              <div style={{ background: 'rgba(255, 255, 255, 0.04)', padding: '12px 14px', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.08)', display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{ width: '38px', height: '38px', borderRadius: '50%', background: 'rgba(249, 115, 22, 0.2)', color: '#f97316', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: '800', fontSize: '1rem' }}>
                  %
                </div>
                <div>
                  <div style={{ fontSize: '0.78rem', fontWeight: '800', color: '#f8fafc', textTransform: 'uppercase' }}>APORTE CALÓRICO</div>
                  <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>{nutritionModalDish.calories_estimate || 510} kcal</div>
                </div>
              </div>

              {/* 2. FIBRA DIGESTIVA */}
              <div style={{ background: 'rgba(255, 255, 255, 0.04)', padding: '12px 14px', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.08)', display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{ width: '38px', height: '38px', borderRadius: '50%', background: 'rgba(34, 197, 94, 0.2)', color: '#22c55e', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.2rem' }}>
                  🥗
                </div>
                <div>
                  <div style={{ fontSize: '0.78rem', fontWeight: '800', color: '#f8fafc', textTransform: 'uppercase' }}>FIBRA DIGESTIVA</div>
                  <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>Microbiota saludable</div>
                </div>
              </div>

              {/* 3. VITAMINA A & C */}
              <div style={{ background: 'rgba(255, 255, 255, 0.04)', padding: '12px 14px', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.08)', display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{ width: '38px', height: '38px', borderRadius: '50%', background: 'rgba(245, 158, 11, 0.2)', color: '#f59e0b', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.2rem' }}>
                  🍊
                </div>
                <div>
                  <div style={{ fontSize: '0.78rem', fontWeight: '800', color: '#f8fafc', textTransform: 'uppercase' }}>VITAMINA A & C</div>
                  <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>Defensa celular activa</div>
                </div>
              </div>

              {/* 4. OMEGA & ÁCIDOS */}
              <div style={{ background: 'rgba(255, 255, 255, 0.04)', padding: '12px 14px', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.08)', display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{ width: '38px', height: '38px', borderRadius: '50%', background: 'rgba(132, 204, 22, 0.2)', color: '#84cc16', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.2rem' }}>
                  🥑
                </div>
                <div>
                  <div style={{ fontSize: '0.78rem', fontWeight: '800', color: '#f8fafc', textTransform: 'uppercase' }}>OMEGA & ÁCIDOS</div>
                  <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>Colesterol bueno HDL</div>
                </div>
              </div>

              {/* 5. ALTO EN PROTEÍNA */}
              <div style={{ background: 'rgba(255, 255, 255, 0.04)', padding: '12px 14px', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.08)', display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{ width: '38px', height: '38px', borderRadius: '50%', background: 'rgba(239, 68, 68, 0.2)', color: '#ef4444', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.2rem' }}>
                  🦐
                </div>
                <div>
                  <div style={{ fontSize: '0.78rem', fontWeight: '800', color: '#f8fafc', textTransform: 'uppercase' }}>ALTO EN PROTEÍNA</div>
                  <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>Desarrollo muscular</div>
                </div>
              </div>

              {/* 6. ANTIOXIDANTES */}
              <div style={{ background: 'rgba(255, 255, 255, 0.04)', padding: '12px 14px', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.08)', display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{ width: '38px', height: '38px', borderRadius: '50%', background: 'rgba(16, 185, 129, 0.2)', color: '#10b981', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.2rem' }}>
                  🌿
                </div>
                <div>
                  <div style={{ fontSize: '0.78rem', fontWeight: '800', color: '#f8fafc', textTransform: 'uppercase' }}>ANTIOXIDANTES</div>
                  <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>Protección celular</div>
                </div>
              </div>

              {/* 7. FUERZA & HIERRO */}
              <div style={{ background: 'rgba(255, 255, 255, 0.04)', padding: '12px 14px', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.08)', display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{ width: '38px', height: '38px', borderRadius: '50%', background: 'rgba(185, 28, 28, 0.2)', color: '#f87171', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.2rem' }}>
                  🥩
                </div>
                <div>
                  <div style={{ fontSize: '0.78rem', fontWeight: '800', color: '#f8fafc', textTransform: 'uppercase' }}>FUERZA & HIERRO</div>
                  <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>Nutrición balanceada</div>
                </div>
              </div>

              {/* 8. INGREDIENTES VIVOS */}
              <div style={{ background: 'rgba(255, 255, 255, 0.04)', padding: '12px 14px', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.08)', display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{ width: '38px', height: '38px', borderRadius: '50%', background: 'rgba(234, 179, 8, 0.2)', color: '#eab308', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.2rem' }}>
                  ✨
                </div>
                <div>
                  <div style={{ fontSize: '0.78rem', fontWeight: '800', color: '#f8fafc', textTransform: 'uppercase' }}>INGREDIENTES VIVOS</div>
                  <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>Cocina artesanal</div>
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'center' }}>
              <button
                type="button"
                onClick={() => setNutritionModalDish(null)}
                className="btn-primary"
                style={{ padding: '10px 30px', fontSize: '0.9rem' }}
              >
                Cerrar Ventana Nutricional
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
