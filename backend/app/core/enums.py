from enum import Enum


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    CAJERO = "CAJERO"
    COCINERO = "COCINERO"
    MESERO = "MESERO"
    DOMICILIARIO = "DOMICILIARIO"
    RRHH = "RRHH"
    NUTRICIONISTA = "NUTRICIONISTA"
    AUDITOR = "AUDITOR"


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


class TableStatus(str, Enum):
    LIBRE = "LIBRE"
    OCUPADA = "OCUPADA"
    RESERVADA = "RESERVADA"
    BLOQUEADA = "BLOQUEADA"


class AllergenSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class EvidenceLevel(str, Enum):
    INFO = "INFO"
    TRADITIONAL = "TRADITIONAL"
    NUTRITIONAL = "NUTRITIONAL"
    CLINICAL = "CLINICAL"


class UnitOfMeasure(str, Enum):
    GRAMOS = "GRAMOS"
    MILILITROS = "MILILITROS"
    UNIDAD = "UNIDAD"
    PORCION = "PORCION"


class OrderType(str, Enum):
    MESA = "MESA"
    DOMICILIO = "DOMICILIO"
    LLEVAR = "LLEVAR"


class OrderStatus(str, Enum):
    ABIERTA = "ABIERTA"
    EN_PREPARACION = "EN_PREPARACION"
    LISTA = "LISTA"
    ENTREGADA = "ENTREGADA"
    CERRADA = "CERRADA"
    PAGADA = "PAGADA"
    ENCUESTADA = "ENCUESTADA"
    CANCELADA = "CANCELADA"


class OrderItemStatus(str, Enum):
    RECIBIDO = "RECIBIDO"
    EN_PREPARACION = "EN_PREPARACION"
    LISTO = "LISTO"
    ENTREGADO = "ENTREGADO"
    CANCELADO = "CANCELADO"

    def can_transition_to(self, destination: "OrderItemStatus") -> bool:
        """
        Regla de negocio RN-05:
        RECIBIDO -> EN_PREPARACION -> LISTO -> ENTREGADO
        Solo RECIBIDO puede pasar a CANCELADO.
        """
        if destination is None:
            return False

        if self == OrderItemStatus.RECIBIDO:
            return destination in (
                OrderItemStatus.EN_PREPARACION,
                OrderItemStatus.CANCELADO,
            )

        if self == OrderItemStatus.EN_PREPARACION:
            return destination == OrderItemStatus.LISTO

        if self == OrderItemStatus.LISTO:
            return destination == OrderItemStatus.ENTREGADO

        return False


class ModificationAction(str, Enum):
    REMOVE = "REMOVE"
    ADD_EXTRA = "ADD_EXTRA"
    QUITAR = "QUITAR"
    AGREGAR = "AGREGAR"


class PaymentMethod(str, Enum):
    EFECTIVO = "EFECTIVO"
    TARJETA = "TARJETA"
    TRANSFERENCIA = "TRANSFERENCIA"
    NEQUI = "NEQUI"
    DAVIPLATA = "DAVIPLATA"
    OTRO = "OTRO"


class PaymentStatus(str, Enum):
    PENDIENTE = "PENDIENTE"
    APROBADO = "APROBADO"
    RECHAZADO = "RECHAZADO"
    REEMBOLSADO = "REEMBOLSADO"


class CashSessionStatus(str, Enum):
    ABIERTA = "ABIERTA"
    CERRADA = "CERRADA"


class OrderChannel(str, Enum):
    QR = "QR"
    STAFF = "STAFF"
    WEB = "WEB"


class DeliveryStatus(str, Enum):
    PENDIENTE = "PENDIENTE"
    ASIGNADO = "ASIGNADO"
    EN_CAMINO = "EN_CAMINO"
    ENTREGADO = "ENTREGADO"
    CANCELADO = "CANCELADO"


class ShiftStatus(str, Enum):
    PROGRAMADO = "PROGRAMADO"
    CONFIRMADO = "CONFIRMADO"
    EN_TURNO = "EN_TURNO"
    EN_DESCANSO = "EN_DESCANSO"
    FINALIZADO = "FINALIZADO"
    AUSENTE = "AUSENTE"
    CANCELADO = "CANCELADO"


class ShiftEventType(str, Enum):
    CLOCK_IN = "CLOCK_IN"
    CLOCK_OUT = "CLOCK_OUT"
    BREAK_START = "BREAK_START"
    BREAK_END = "BREAK_END"
    STATUS_CHANGED = "STATUS_CHANGED"


class CommissionRuleType(str, Enum):
    PERCENT_NET_SALES = "PERCENT_NET_SALES"
    FIXED_PER_ORDER = "FIXED_PER_ORDER"
    PERCENT_ITEM_SALES = "PERCENT_ITEM_SALES"
    FIXED_PER_ITEM = "FIXED_PER_ITEM"
    FIXED_PER_DELIVERY = "FIXED_PER_DELIVERY"
    SURVEY_BONUS_FIXED = "SURVEY_BONUS_FIXED"


class CommissionPeriodStatus(str, Enum):
    ABIERTA = "ABIERTA"
    CALCULADA = "CALCULADA"
    APROBADA = "APROBADA"
    PAGADA = "PAGADA"
    ANULADA = "ANULADA"


class CommissionPayoutStatus(str, Enum):
    PENDIENTE = "PENDIENTE"
    PAGADO = "PAGADO"
    ANULADO = "ANULADO"


class CommissionEventStatus(str, Enum):
    CALCULADA = "CALCULADA"
    APROBADA = "APROBADA"
    ANULADA = "ANULADA"


class StockMovementDirection(str, Enum):
    IN = "IN"
    OUT = "OUT"


class StockMovementType(str, Enum):
    INICIAL = "INICIAL"
    COMPRA = "COMPRA"
    VENTA = "VENTA"
    DEVOLUCION_VENTA = "DEVOLUCION_VENTA"
    AJUSTE_ENTRADA = "AJUSTE_ENTRADA"
    AJUSTE_SALIDA = "AJUSTE_SALIDA"
    DESPERDICIO = "DESPERDICIO"


class PurchaseOrderStatus(str, Enum):
    BORRADOR = "BORRADOR"
    RECIBIDA = "RECIBIDA"
    ANULADA = "ANULADA"
