"""
PDF generation service using ReportLab.
Generates professional itinerary and booking confirmation PDFs.
"""
import io
import logging
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

logger = logging.getLogger(__name__)

# ── IBM Brand Colours ────────────────────────────────────────────────────────
IBM_BLUE   = colors.HexColor("#0f62fe")
IBM_DARK   = colors.HexColor("#161616")
IBM_TEAL   = colors.HexColor("#009d9a")
IBM_GREEN  = colors.HexColor("#198038")
IBM_GRAY   = colors.HexColor("#f4f4f4")
IBM_BORDER = colors.HexColor("#e0e0e0")
WHITE      = colors.white


def _styles():
    base = getSampleStyleSheet()
    custom = {
        "title": ParagraphStyle("title", fontSize=22, textColor=WHITE, fontName="Helvetica-Bold", alignment=TA_LEFT, spaceAfter=4),
        "subtitle": ParagraphStyle("subtitle", fontSize=11, textColor=colors.HexColor("#c6c6c6"), fontName="Helvetica", alignment=TA_LEFT),
        "section": ParagraphStyle("section", fontSize=13, textColor=IBM_BLUE, fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=6),
        "body": ParagraphStyle("body", fontSize=9, textColor=IBM_DARK, fontName="Helvetica", spaceAfter=4, leading=14),
        "small": ParagraphStyle("small", fontSize=8, textColor=colors.HexColor("#525252"), fontName="Helvetica", spaceAfter=2),
        "bold": ParagraphStyle("bold", fontSize=9, textColor=IBM_DARK, fontName="Helvetica-Bold", spaceAfter=4),
        "day_header": ParagraphStyle("day_header", fontSize=10, textColor=WHITE, fontName="Helvetica-Bold", alignment=TA_LEFT),
        "activity": ParagraphStyle("activity", fontSize=9, textColor=IBM_DARK, fontName="Helvetica", spaceAfter=3, leftIndent=8),
        "footer": ParagraphStyle("footer", fontSize=7, textColor=colors.HexColor("#8d8d8d"), fontName="Helvetica", alignment=TA_CENTER),
    }
    return custom


def _header_table(title: str, subtitle: str, ref: str = "") -> Table:
    """Dark IBM-styled header block."""
    s = _styles()
    data = [[
        Paragraph(title, s["title"]),
        Paragraph(ref, ParagraphStyle("ref", fontSize=9, textColor=colors.HexColor("#74b1ff"), fontName="Helvetica-Bold", alignment=TA_RIGHT)),
    ], [
        Paragraph(subtitle, s["subtitle"]),
        Paragraph("IBM Travel Planner · Powered by IBM Granite AI", ParagraphStyle("pow", fontSize=7, textColor=colors.HexColor("#8d8d8d"), fontName="Helvetica", alignment=TA_RIGHT)),
    ]]
    t = Table(data, colWidths=["70%", "30%"])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), IBM_DARK),
        ("TOPPADDING",    (0, 0), (-1, -1), 16),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
        ("LEFTPADDING",   (0, 0), (-1, -1), 18),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 18),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def _meta_table(rows: list[tuple]) -> Table:
    """2-column key-value meta table."""
    s = _styles()
    data = [[Paragraph(k, s["small"]), Paragraph(str(v), s["bold"])] for k, v in rows]
    t = Table(data, colWidths=["35%", "65%"])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), IBM_GRAY),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("LINEBELOW",     (0, 0), (-1, -2), 0.5, IBM_BORDER),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


# ── Itinerary PDF ────────────────────────────────────────────────────────────

def generate_itinerary_pdf(itinerary: dict) -> bytes:
    """Generate a full itinerary PDF. Returns bytes."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=1.8*cm, rightMargin=1.8*cm,
        topMargin=1.5*cm, bottomMargin=2*cm,
    )
    s = _styles()
    story = []

    destination = itinerary.get("destination", "Your Destination")
    duration    = itinerary.get("duration_days", 0)
    start_date  = itinerary.get("start_date", "")
    budget      = itinerary.get("budget_level", "moderate").title()
    total_cost  = itinerary.get("estimated_total_cost_usd", "—")

    # Header
    story.append(_header_table(
        f"Travel Itinerary — {destination}",
        f"{duration} Days · {start_date} · {budget} Budget",
        f"Est. ${total_cost} USD",
    ))
    story.append(Spacer(1, 0.4*cm))

    # Meta
    story.append(_meta_table([
        ("Destination", destination),
        ("Duration", f"{duration} days"),
        ("Start Date", start_date),
        ("Budget Level", budget),
        ("Estimated Cost", f"USD {total_cost:,}" if isinstance(total_cost, (int, float)) else str(total_cost)),
        ("Generated", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")),
    ]))
    story.append(Spacer(1, 0.5*cm))

    # Days
    days = itinerary.get("days", [])
    for day in days:
        day_num = day.get("day", "?")
        date    = day.get("date", "")
        theme   = day.get("theme", "")
        budget_d = day.get("daily_budget_usd", "—")

        # Day header row
        header_data = [[
            Paragraph(f"Day {day_num}  ·  {date}", s["day_header"]),
            Paragraph(theme, ParagraphStyle("th2", fontSize=9, textColor=colors.HexColor("#a8a8a8"), fontName="Helvetica", alignment=TA_LEFT)),
            Paragraph(f"~${budget_d}/day", ParagraphStyle("th3", fontSize=9, textColor=colors.HexColor("#74b1ff"), fontName="Helvetica-Bold", alignment=TA_RIGHT)),
        ]]
        ht = Table(header_data, colWidths=["28%", "48%", "24%"])
        ht.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), IBM_BLUE),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ]))

        # Activities
        activities_content = [ht]
        for period in ["morning", "afternoon", "evening"]:
            act = day.get(period)
            if act and isinstance(act, dict) and act.get("activity"):
                period_label = period.title()
                act_name = act.get("activity", "")
                act_desc = act.get("description", "")
                act_loc  = act.get("location", "")
                act_cost = act.get("cost_usd", "")
                act_tip  = act.get("tips", "")
                line = f"<b>{period_label}:</b> {act_name}"
                if act_loc: line += f" — <i>{act_loc}</i>"
                if act_cost: line += f" (~${act_cost})"
                activities_content.append(Paragraph(line, s["activity"]))
                if act_desc:
                    activities_content.append(Paragraph(act_desc, s["small"]))
                if act_tip:
                    activities_content.append(Paragraph(f"💡 {act_tip}", ParagraphStyle("tip", fontSize=8, textColor=IBM_TEAL, fontName="Helvetica-Oblique", leftIndent=12)))

        meals = day.get("meals", {})
        if meals:
            meal_str = " · ".join(f"<b>{k.title()}:</b> {v}" for k, v in meals.items() if v)
            activities_content.append(Paragraph(f"🍽 {meal_str}", s["small"]))

        transport = day.get("transport", "")
        if transport:
            activities_content.append(Paragraph(f"🚌 Transport: {transport}", s["small"]))

        activities_content.append(Spacer(1, 0.3*cm))
        story.append(KeepTogether(activities_content))

    # Packing tips
    packing = itinerary.get("packing_tips", [])
    if packing:
        story.append(Paragraph("Packing Tips", s["section"]))
        for tip in packing:
            story.append(Paragraph(f"• {tip}", s["body"]))

    # Emergency contacts
    emergency = itinerary.get("emergency_contacts", {})
    if emergency:
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph("Emergency Contacts", s["section"]))
        rows = [(k.replace("_", " ").title(), v) for k, v in emergency.items() if v]
        if rows:
            story.append(_meta_table(rows))

    # Footer disclaimer
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=IBM_BORDER))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "This itinerary was AI-generated by IBM Travel Planner Agent powered by IBM Granite AI. "
        "Always verify visa requirements, opening hours, and prices with official sources before travel. "
        f"Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}.",
        s["footer"]
    ))

    doc.build(story)
    return buf.getvalue()


# ── Booking PDF ──────────────────────────────────────────────────────────────

def generate_booking_pdf(booking: dict) -> bytes:
    """Generate a booking confirmation PDF. Returns bytes."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=1.8*cm, rightMargin=1.8*cm,
        topMargin=1.5*cm, bottomMargin=2*cm,
    )
    s = _styles()
    story = []

    bid = booking.get("id", booking.get("booking_id", "—"))
    destination = booking.get("destination", "—")
    trip_name   = booking.get("trip_name", "—")
    start_date  = booking.get("start_date", "—")
    end_date    = booking.get("end_date", "—")
    traveler    = booking.get("traveler_name", "—")
    status      = booking.get("status", "confirmed").upper()
    details     = booking.get("details", {})

    story.append(_header_table(
        "Booking Confirmation",
        f"{trip_name} — {destination}",
        f"Ref: TRV-{bid}",
    ))
    story.append(Spacer(1, 0.5*cm))

    # Status badge
    status_color = IBM_GREEN if status == "CONFIRMED" else colors.HexColor("#da1e28")
    status_data = [[Paragraph(f"Status: {status}", ParagraphStyle("st", fontSize=11, textColor=WHITE, fontName="Helvetica-Bold", alignment=TA_CENTER))]]
    st = Table(status_data, colWidths=["100%"])
    st.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), status_color),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(st)
    story.append(Spacer(1, 0.4*cm))

    # Core details
    story.append(Paragraph("Booking Details", s["section"]))
    nights = ""
    try:
        from datetime import date
        d1 = date.fromisoformat(start_date)
        d2 = date.fromisoformat(end_date)
        nights = f" ({(d2 - d1).days} nights)"
    except Exception:
        pass

    story.append(_meta_table([
        ("Booking Reference", f"TRV-{bid}"),
        ("Trip Name", trip_name),
        ("Destination", destination),
        ("Lead Traveler", traveler),
        ("Departure Date", start_date),
        ("Return Date", f"{end_date}{nights}"),
        ("Booking Type", booking.get("booking_type", "trip").title()),
        ("Booking Date", booking.get("created_at", datetime.utcnow().isoformat())[:10]),
    ]))

    # Flight details
    flight = details.get("flight", {})
    if any(flight.values()):
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph("Flight Details", s["section"]))
        rows = []
        if flight.get("airline_pref"): rows.append(("Airline", flight["airline_pref"]))
        if flight.get("cabin"): rows.append(("Cabin Class", flight["cabin"].replace("_", " ").title()))
        if flight.get("flight_out"): rows.append(("Outbound Flight", flight["flight_out"]))
        if flight.get("flight_ret"): rows.append(("Return Flight", flight["flight_ret"]))
        if flight.get("baggage"): rows.append(("Baggage", flight["baggage"].replace("_", " ").title()))
        if flight.get("seat"): rows.append(("Seat Preference", flight["seat"].replace("_", " ").title()))
        if rows:
            story.append(_meta_table(rows))

    # Hotel details
    hotel = details.get("hotel", {})
    if hotel.get("name") or hotel.get("type"):
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph("Accommodation", s["section"]))
        rows = []
        if hotel.get("name"): rows.append(("Hotel / Property", hotel["name"]))
        if hotel.get("type"): rows.append(("Type", hotel["type"].replace("_", " ").title()))
        if hotel.get("stars"): rows.append(("Star Rating", f"{'★' * int(hotel['stars'])} ({hotel['stars']} star)"))
        if hotel.get("checkin"): rows.append(("Check-in", hotel["checkin"]))
        if hotel.get("checkout"): rows.append(("Check-out", hotel["checkout"]))
        if hotel.get("rooms"): rows.append(("Rooms", str(hotel["rooms"])))
        if hotel.get("room_type"): rows.append(("Room Type", hotel["room_type"].replace("_", " ").title()))
        if hotel.get("board"): rows.append(("Board Basis", hotel["board"].replace("_", " ").title()))
        if rows:
            story.append(_meta_table(rows))

    # Alerts
    alerts = booking.get("alerts", [])
    if alerts:
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph("Alerts & Notes", s["section"]))
        for alert in alerts:
            story.append(Paragraph(f"• {alert.get('message', '')}", s["body"]))

    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=IBM_BORDER))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "This is a trip planning record generated by IBM Travel Planner Agent. "
        "It is not a confirmed airline or hotel reservation. Always book directly with service providers. "
        f"Reference: TRV-{bid} · Generated {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        s["footer"]
    ))

    doc.build(story)
    return buf.getvalue()
