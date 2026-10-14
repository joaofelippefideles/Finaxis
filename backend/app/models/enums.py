import enum


class TransactionType(str, enum.Enum):
    income = "receita"
    expense = "despesa"
    transfer = "transferencia"


class TransactionStatus(str, enum.Enum):
    pending = "pendente"
    paid = "pago"
    received = "recebido"
    canceled = "cancelado"


class RecurrenceFrequency(str, enum.Enum):
    daily = "diario"
    weekly = "semanal"
    monthly = "mensal"
    yearly = "anual"


class AccountType(str, enum.Enum):
    checking = "conta_corrente"
    savings = "poupanca"
    cash = "carteira"
    digital = "conta_digital"
    investment = "investimentos"


class CategoryType(str, enum.Enum):
    income = "receita"
    expense = "despesa"


class CardStatus(str, enum.Enum):
    active = "ativo"
    blocked = "bloqueado"
    canceled = "cancelado"


class RecurrenceStatus(str, enum.Enum):
    active = "ativo"
    paused = "pausado"
    canceled = "cancelado"


class ListItemStatus(str, enum.Enum):
    pending = "pendente"
    paid = "pago"
    received = "recebido"
    canceled = "cancelado"


class InstallmentStatus(str, enum.Enum):
    active = "ativo"
    completed = "concluido"
    canceled = "cancelado"


class NotificationType(str, enum.Enum):
    payable_due = "conta_vencida"
    payable_soon = "conta_proxima"
    receivable_due = "recebimento_vencido"
    receivable_soon = "recebimento_proximo"
    budget_warning = "orcamento_aviso"
    card_limit = "cartao_limite"
    invoice_due = "fatura_proxima"