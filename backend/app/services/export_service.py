import csv
import io
from decimal import Decimal
from pathlib import Path

from fpdf import FPDF
from openpyxl import Workbook

from app.schemas.report import ReportData
from app.utils.money import format_brl

CSV_COLUMNS = [
    "data",
    "descricao",
    "tipo",
    "status",
    "categoria",
    "conta",
    "cartao",
    "valor",
]


def _rows(report: ReportData) -> list[dict]:
    rows = []
    for item in report.lancamentos:
        rows.append(
            {
                "data": item.get("date", ""),
                "descricao": item.get("description", ""),
                "tipo": item.get("type", ""),
                "status": item.get("status", ""),
                "categoria": item.get("category") or "",
                "conta": item.get("account") or "",
                "cartao": item.get("card") or "",
                "valor": item.get("amount", ""),
            }
        )
    return rows


def export_csv(report: ReportData) -> bytes:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS, delimiter=";")
    writer.writeheader()
    for row in _rows(report):
        writer.writerow(row)
    return buffer.getvalue().encode("utf-8-sig")


def export_xlsx(report: ReportData) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Relatorio"
    ws.append(
        [
            "Data",
            "Descricao",
            "Tipo",
            "Status",
            "Categoria",
            "Conta",
            "Cartao",
            "Valor",
        ]
    )
    for row in _rows(report):
        ws.append(
            [
                row["data"],
                row["descricao"],
                row["tipo"],
                row["status"],
                row["categoria"],
                row["conta"],
                row["cartao"],
                Decimal(row["valor"] or "0"),
            ]
        )
    ws2 = wb.create_sheet("Resumo")
    ws2.append(["Indicador", "Valor"])
    ws2.append(["Total de receitas", str(report.total_receitas)])
    ws2.append(["Total de despesas", str(report.total_despesas)])
    ws2.append(["Resultado", str(report.resultado)])
    for cat in report.por_categoria:
        key = "receita" if "receita" in cat else "despesa"
        ws2.append(["Categoria", cat.get("name", "?")])
        ws2.append([f"{key.capitalize()} por categoria", cat.get(key)])
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


PDF_FONT_CANDIDATES = {
    "regular": [
        Path(__file__).resolve().parent.parent / "fonts" / "DejaVuSans.ttf",
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
        Path("/Library/Fonts/Arial.ttf"),
    ],
    "bold": [
        Path(__file__).resolve().parent.parent / "fonts" / "DejaVuSans-Bold.ttf",
        Path("C:/Windows/Fonts/arialbd.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
        Path("/Library/Fonts/Arial-Bold.ttf"),
    ],
}


def _load_pdf_font(pdf: FPDF, family: str = "DejaVu") -> tuple[str, bool]:
    """Registra uma fonte Unicode e retorna (família, tem_negrito)."""
    regular = next((p for p in PDF_FONT_CANDIDATES["regular"] if p.exists()), None)
    if regular is None:
        return "Helvetica", False
    pdf.add_font(family, "", str(regular))
    has_bold = False
    bold = next((p for p in PDF_FONT_CANDIDATES["bold"] if p.exists()), None)
    if bold is not None:
        pdf.add_font(family, "B", str(bold))
        has_bold = True
    return family, has_bold


def _make_font(pdf: FPDF, family: str, has_bold: bool, style: str, size: int):
    style = style if (style != "B" or has_bold) else ""
    pdf.set_font(family, style, size)


def export_pdf(report: ReportData) -> bytes:
    pdf = FPDF(format="A4", unit="mm")
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    family, has_bold = _load_pdf_font(pdf)

    _make_font(pdf, family, has_bold, "B", 16)
    pdf.cell(0, 10, "Relatório Financeiro", ln=True)
    _make_font(pdf, family, has_bold, "", 10)
    pdf.cell(
        0,
        6,
        f"Período: {report.query.start_date} a {report.query.end_date}",
        ln=True,
    )
    pdf.ln(4)

    _make_font(pdf, family, has_bold, "B", 11)
    pdf.cell(0, 6, "Resumo", ln=True)
    _make_font(pdf, family, has_bold, "", 10)
    values = [
        ("Receitas", format_brl(report.total_receitas)),
        ("Despesas", format_brl(report.total_despesas)),
        ("Resultado", format_brl(report.resultado)),
    ]
    for label, value in values:
        pdf.cell(0, 6, f"{label}: {value}", ln=True)
    pdf.ln(4)

    _make_font(pdf, family, has_bold, "B", 11)
    pdf.cell(0, 6, "Despesas por categoria", ln=True)
    _make_font(pdf, family, has_bold, "", 10)
    for cat in report.por_categoria:
        amount = cat.get("despesa") or cat.get("receita") or "0"
        pdf.cell(0, 6, f"{cat.get('name', '?')}: {format_brl(amount)}", ln=True)

    pdf.ln(4)
    _make_font(pdf, family, has_bold, "B", 11)
    pdf.cell(0, 6, "Evolução mensal", ln=True)
    _make_font(pdf, family, has_bold, "", 10)
    for row in report.evolucao_mensal:
        pdf.cell(
            0,
            6,
            f"{row['month']}: R {format_brl(row['receitas'])} / D {format_brl(row['despesas'])}",
            ln=True,
        )

    return bytes(pdf.output())


def export_report(report: ReportData, fmt: str) -> bytes:
    fmt = fmt.lower()
    if fmt == "csv":
        return export_csv(report)
    if fmt in ("xlsx", "excel"):
        return export_xlsx(report)
    if fmt == "pdf":
        return export_pdf(report)
    raise ValueError(f"Formato de exportação inválido: {fmt}")