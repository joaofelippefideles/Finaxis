from decimal import Decimal, ROUND_HALF_UP

CENTESIMOS = Decimal("0.01")


def money(v) -> Decimal:
    """Normaliza um valor para 2 casas decimais usando arredondamento correto."""
    if v is None:
        return Decimal("0")
    return Decimal(str(v)).quantize(CENTESIMOS, rounding=ROUND_HALF_UP)


def format_brl(v) -> str:
    """Formata um valor no padrão brasileiro: R$ 1.250,50."""
    d = money(v)
    return f"R$ {d:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def split_installment_value(total: Decimal, total_parcels: int) -> list[Decimal]:
    """Divide o valor total em parcelas iguais (última parcela absorve o resíduo)."""
    total = money(total)
    if total_parcels <= 0:
        return []
    base = (total / Decimal(total_parcels)).quantize(CENTESIMOS, rounding=ROUND_HALF_UP)
    parcels = [base] * total_parcels
    leftover = total - sum(parcels)
    if leftover != 0:
        parcels[-1] = (parcels[-1] + leftover).quantize(CENTESIMOS, rounding=ROUND_HALF_UP)
    return parcels


def parse_brl_amount(value: str) -> Decimal:
    """Converte '1.250,50' ou '1250,50' ou '1250.50' para Decimal."""
    v = value.strip().replace("R$", "").strip()
    if "," in v and "." in v:
        if v.rfind(",") > v.rfind("."):
            v = v.replace(".", "").replace(",", ".")
        else:
            v = v.replace(",", "")
    elif "," in v:
        v = v.replace(",", ".")
    return money(v)