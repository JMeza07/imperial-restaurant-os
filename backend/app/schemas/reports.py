from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.enums import PaymentMethod


class ReportSummaryRead(BaseModel):
    date_from: date
    date_to: date

    total_sales: Decimal
    paid_orders_count: int
    average_ticket: Decimal

    open_orders_count: int
    pending_kitchen_items: int

    surveys_count: int
    avg_general_score: Optional[float]

    low_stock_count: int


class DailySalesRead(BaseModel):
    report_date: date
    orders_count: int

    subtotal: Decimal
    tax_amount: Decimal
    tip_amount: Decimal
    delivery_fee: Decimal
    discount_amount: Decimal
    total: Decimal
    total_paid: Decimal


class CategorySalesRead(BaseModel):
    category_id: UUID
    category_name: str

    dishes_count: int
    quantity: int
    revenue: Decimal


class TopDishRead(BaseModel):
    dish_id: UUID
    dish_name: str
    category_name: Optional[str]

    quantity: int
    revenue: Decimal


class PaymentMethodSalesRead(BaseModel):
    payment_method: PaymentMethod
    payments_count: int
    amount: Decimal


class EmployeePerformanceRead(BaseModel):
    employee_id: UUID
    full_name: Optional[str]
    role: Optional[str]

    orders_count: int
    items_prepared: int
    deliveries_count: int

    sales_total: Decimal
    commissions_total: Decimal


class SurveyCommentRead(BaseModel):
    comment: str
    general_score: int
    created_at: datetime


class SurveySummaryRead(BaseModel):
    surveys_count: int

    avg_food_score: Optional[float]
    avg_service_score: Optional[float]
    avg_general_score: Optional[float]

    comments: List[SurveyCommentRead] = []


class CommissionSummaryRead(BaseModel):
    employee_id: UUID
    full_name: Optional[str]
    role: Optional[str]

    total_calculated: Decimal
    total_approved: Decimal
    total_paid: Decimal


class CashSummaryRead(BaseModel):
    payment_method: PaymentMethod
    payments_count: int
    amount: Decimal


class InventoryConsumptionRead(BaseModel):
    ingredient_id: UUID
    ingredient_name: str

    purchased_quantity: Decimal
    sold_quantity: Decimal
    waste_quantity: Decimal
    adjustment_out_quantity: Decimal
