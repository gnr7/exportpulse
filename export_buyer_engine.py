"""
ExportPulse AI — US Customs Buyer Intelligence & Outreach Engine (FastAPI)
==========================================================================
Single-file, zero-cost B2B micro-application for the 7-Day $5,000
Upfront Deployment Play (Section G of 'The $100 Income Engine').

Run:
    pip install -r requirements.txt
    uvicorn export_buyer_engine:app --reload --port 8000

Personalized demo URLs:
    http://127.0.0.1:8000/?factory=Konark%20Artisan%20Exports&city=Bhubaneswar&category=handicrafts

Optional environment variables:
    GEMINI_API_KEY    live LLM outreach (falls back to built-in templates at zero cost)
    BUYERS_CSV        client buyer file loaded at startup instead of the demo seed
                      (default: client_buyers.csv next to this file, if present)
    DEFAULT_FACTORY   banner name when no ?factory= is passed (client deployments)
    DEFAULT_CITY      banner city when no ?city= is passed
    DEFAULT_CATEGORY  sector shown when no ?category= is passed
    SELLER_WHATSAPP   your WhatsApp number with country code (e.g. 919876543210)
                      for the "Get the full list" button on demo pages
"""

import csv
import html
import io
import json
import os
import re
import urllib.request
import uuid
from datetime import datetime
from typing import Dict, List, Literal, Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# App Instance
# ---------------------------------------------------------------------------
app = FastAPI(
    title="ExportPulse AI — US Customs Buyer Intelligence",
    description=(
        "B2B US Customs Bill-of-Lading Matcher, FOB Landed-Cost Calculator "
        "& Automated Buyer Outreach Portal"
    ),
    version="1.1.0",
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
USD_TO_INR = 95.00
FREIGHT_INSURANCE_PCT = 8.0
AGENT_COMMISSION_PCT = 5.0
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.5-flash"

SECTORS = ("handicrafts", "agro_marine", "textiles", "leather")
Sector = Literal["handicrafts", "agro_marine", "textiles", "leather"]
SECTOR_ID_PREFIX = {"handicrafts": "hc", "agro_marine": "am", "textiles": "tx", "leather": "lt"}

BUYERS_CSV = os.environ.get(
    "BUYERS_CSV",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "client_buyers.csv"),
)
DEFAULT_FACTORY = os.environ.get("DEFAULT_FACTORY", "Your Export Company")
DEFAULT_CITY = os.environ.get("DEFAULT_CITY", "India")
DEFAULT_CATEGORY = os.environ.get("DEFAULT_CATEGORY", "handicrafts")
SELLER_WHATSAPP = re.sub(r"\D", "", os.environ.get("SELLER_WHATSAPP", ""))

# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------
class BuyerAdd(BaseModel):
    sector: Sector = "handicrafts"
    us_buyer: str = Field(min_length=1)
    hq_city: str
    hq_state: str = ""
    hs_code: str
    product_spec: str
    containers_12m: int = Field(ge=0)
    est_annual_usd: float = Field(ge=0)
    last_arrival_date: str
    competitor_fob_usd: float = Field(gt=0)
    us_duty_pct: float = Field(default=0.0, ge=0)
    vulnerability_signal: str = ""
    decision_maker_role: str = "Sourcing Manager"
    match_score: int = Field(default=75, ge=0, le=100)


class Buyer(BuyerAdd):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])


class CostResult(BaseModel):
    buyer_id: str
    us_buyer: str
    hs_code: str
    product_spec: str
    us_duty_pct: float
    competitor_fob_usd: float
    competitor_landed_usd: float
    your_fob_usd: float
    your_landed_usd: float
    savings_per_unit_usd: float
    annual_savings_10k_usd: float
    landed_savings_pct: float
    agent_commission_saved_inr: float


class OutreachRequest(BaseModel):
    buyer_id: str
    factory_name: str = "Your Export Company"
    factory_city: str = "India"
    your_fob_usd: float = 0.0


class OutreachResponse(BaseModel):
    cold_email_subject: str
    cold_email_body: str
    followup_subject: str
    followup_body: str
    linkedin_whatsapp: str
    engine: str = "template"


# ---------------------------------------------------------------------------
# In-Memory Data Store
# ---------------------------------------------------------------------------
BUYERS_DB: List[Buyer] = []

# ---------------------------------------------------------------------------
# Pre-Loaded Sector Datasets (ImportYeti US BoL-style records)
# ---------------------------------------------------------------------------
SEED_DATA: List[Dict] = [
    # ===== HANDICRAFTS (5 records) =====
    {
        "sector": "handicrafts",
        "us_buyer": "Pier 1 Imports Inc",
        "hq_city": "Fort Worth",
        "hq_state": "TX",
        "hs_code": "4420.10",
        "product_spec": "Carved Wooden Figurines & Decorative Panels",
        "containers_12m": 18,
        "est_annual_usd": 1_200_000,
        "last_arrival_date": "2026-09-14",
        "vulnerability_signal": "Primary India supplier volume down 35% YoY — sourcing gap open",
        "decision_maker_role": "VP Global Sourcing",
        "match_score": 92,
        "competitor_fob_usd": 4.80,
        "us_duty_pct": 3.2,
    },
    {
        "sector": "handicrafts",
        "us_buyer": "World Market (Cost Plus Inc)",
        "hq_city": "Alameda",
        "hq_state": "CA",
        "hs_code": "6802.99",
        "product_spec": "Hand-Carved Soapstone & Marble Artifacts",
        "containers_12m": 24,
        "est_annual_usd": 1_800_000,
        "last_arrival_date": "2026-10-02",
        "vulnerability_signal": "China Section 301 tariff at 25% — actively diversifying to India",
        "decision_maker_role": "Director of Product Development",
        "match_score": 88,
        "competitor_fob_usd": 6.20,
        "us_duty_pct": 4.0,
    },
    {
        "sector": "handicrafts",
        "us_buyer": "Z Gallerie LLC",
        "hq_city": "Gardena",
        "hq_state": "CA",
        "hs_code": "7419.80",
        "product_spec": "Brass Decor, Candle Holders & Table Accents",
        "containers_12m": 12,
        "est_annual_usd": 850_000,
        "last_arrival_date": "2026-08-20",
        "vulnerability_signal": "Switched 2 brass SKUs from China to India in Q2 — expanding India vendor base",
        "decision_maker_role": "Senior Buyer - Home Decor",
        "match_score": 85,
        "competitor_fob_usd": 5.50,
        "us_duty_pct": 3.5,
    },
    {
        "sector": "handicrafts",
        "us_buyer": "Pottery Barn (Williams-Sonoma)",
        "hq_city": "San Francisco",
        "hq_state": "CA",
        "hs_code": "6913.90",
        "product_spec": "Handmade Ceramic & Terracotta Tableware",
        "containers_12m": 30,
        "est_annual_usd": 2_400_000,
        "last_arrival_date": "2026-10-18",
        "vulnerability_signal": "RFQ posted on ThomasNet for Indian ceramic suppliers — Q1 2027 deadline",
        "decision_maker_role": "VP Supply Chain",
        "match_score": 94,
        "competitor_fob_usd": 3.90,
        "us_duty_pct": 6.0,
    },
    {
        "sector": "handicrafts",
        "us_buyer": "Ten Thousand Villages",
        "hq_city": "Akron",
        "hq_state": "PA",
        "hs_code": "4602.12",
        "product_spec": "Hand-Woven Basketware & Cane Storage",
        "containers_12m": 8,
        "est_annual_usd": 420_000,
        "last_arrival_date": "2026-07-05",
        "vulnerability_signal": "Fair-trade mandate — prefers direct-from-artisan sourcing, no middlemen",
        "decision_maker_role": "Sourcing Manager - South Asia",
        "match_score": 78,
        "competitor_fob_usd": 3.20,
        "us_duty_pct": 2.4,
    },
    # ===== AGRO & MARINE (5 records) =====
    {
        "sector": "agro_marine",
        "us_buyer": "McCormick & Company",
        "hq_city": "Hunt Valley",
        "hq_state": "MD",
        "hs_code": "0908.31",
        "product_spec": "Whole & Ground Cardamom (Guatemala + India origin)",
        "containers_12m": 42,
        "est_annual_usd": 3_800_000,
        "last_arrival_date": "2026-10-22",
        "vulnerability_signal": "Guatemala cardamom crop shortfall — shifting 15% volume to Kerala origin",
        "decision_maker_role": "VP Raw Material Procurement",
        "match_score": 91,
        "competitor_fob_usd": 18.50,
        "us_duty_pct": 0.0,
    },
    {
        "sector": "agro_marine",
        "us_buyer": "Sysco Corporation",
        "hq_city": "Houston",
        "hq_state": "TX",
        "hs_code": "0306.17",
        "product_spec": "Frozen Black Tiger & Vannamei Shrimp (IQF, headless)",
        "containers_12m": 65,
        "est_annual_usd": 8_200_000,
        "last_arrival_date": "2026-10-28",
        "vulnerability_signal": "FDA import alert on 3 Vietnam shrimp plants — India share rising",
        "decision_maker_role": "Director of Seafood Procurement",
        "match_score": 95,
        "competitor_fob_usd": 7.80,
        "us_duty_pct": 0.0,
    },
    {
        "sector": "agro_marine",
        "us_buyer": "Olam Americas Inc",
        "hq_city": "Fresno",
        "hq_state": "CA",
        "hs_code": "0801.32",
        "product_spec": "Raw & Roasted Cashew Kernels (W-240, W-320)",
        "containers_12m": 38,
        "est_annual_usd": 4_500_000,
        "last_arrival_date": "2026-09-30",
        "vulnerability_signal": "Ivory Coast raw cashew export ban — India processing capacity in demand",
        "decision_maker_role": "Head of Edible Nuts - Americas",
        "match_score": 87,
        "competitor_fob_usd": 8.40,
        "us_duty_pct": 0.0,
    },
    {
        "sector": "agro_marine",
        "us_buyer": "Ventura Foods LLC",
        "hq_city": "Brea",
        "hq_state": "CA",
        "hs_code": "0904.12",
        "product_spec": "Malabar & Tellicherry Black Pepper (whole, ASTA 550+)",
        "containers_12m": 28,
        "est_annual_usd": 2_100_000,
        "last_arrival_date": "2026-08-15",
        "vulnerability_signal": "Vietnam pepper prices up 40% YoY — cost-sensitive buyers looking at India",
        "decision_maker_role": "Commodity Purchasing Manager",
        "match_score": 82,
        "competitor_fob_usd": 5.60,
        "us_duty_pct": 0.0,
    },
    {
        "sector": "agro_marine",
        "us_buyer": "Red Chamber Co",
        "hq_city": "Vernon",
        "hq_state": "CA",
        "hs_code": "0306.17",
        "product_spec": "Frozen Vannamei Shrimp & Surimi (HOSO, HLSO)",
        "containers_12m": 55,
        "est_annual_usd": 6_800_000,
        "last_arrival_date": "2026-10-10",
        "vulnerability_signal": "Antidumping duty on Thai shrimp raised to 5.34% — India duty-free under GSP",
        "decision_maker_role": "VP Sourcing - Asia Pacific",
        "match_score": 89,
        "competitor_fob_usd": 7.20,
        "us_duty_pct": 0.0,
    },
    # ===== TEXTILES (5 records) =====
    {
        "sector": "textiles",
        "us_buyer": "Target Corporation",
        "hq_city": "Minneapolis",
        "hq_state": "MN",
        "hs_code": "6302.31",
        "product_spec": "Cotton Bed Linen Sets (200-400 TC, printed & solid)",
        "containers_12m": 120,
        "est_annual_usd": 15_000_000,
        "last_arrival_date": "2026-10-25",
        "vulnerability_signal": "Pakistan flood disruption — reallocating 20% bed-linen orders to India vendors",
        "decision_maker_role": "SVP Sourcing - Home Textiles",
        "match_score": 96,
        "competitor_fob_usd": 4.20,
        "us_duty_pct": 6.3,
    },
    {
        "sector": "textiles",
        "us_buyer": "Restoration Hardware (RH)",
        "hq_city": "Corte Madera",
        "hq_state": "CA",
        "hs_code": "5701.10",
        "product_spec": "Hand-Knotted & Hand-Tufted Wool Rugs (Indo-Persian)",
        "containers_12m": 35,
        "est_annual_usd": 4_200_000,
        "last_arrival_date": "2026-09-12",
        "vulnerability_signal": "Premium positioning — paying 30% above market for exclusivity, open to new ateliers",
        "decision_maker_role": "Director of Textiles & Rugs",
        "match_score": 84,
        "competitor_fob_usd": 22.00,
        "us_duty_pct": 4.5,
    },
    {
        "sector": "textiles",
        "us_buyer": "Welspun USA Inc",
        "hq_city": "New York",
        "hq_state": "NY",
        "hs_code": "6302.60",
        "product_spec": "Terry Towels & Bath Rugs (ringspun cotton, 500+ GSM)",
        "containers_12m": 85,
        "est_annual_usd": 11_000_000,
        "last_arrival_date": "2026-10-20",
        "vulnerability_signal": "Welspun India capex cycle — subcontracting overflow volume to approved vendors",
        "decision_maker_role": "VP Supply Chain - Americas",
        "match_score": 90,
        "competitor_fob_usd": 3.80,
        "us_duty_pct": 9.1,
    },
    {
        "sector": "textiles",
        "us_buyer": "Bed Bath & Beyond Inc",
        "hq_city": "Union",
        "hq_state": "NJ",
        "hs_code": "6303.92",
        "product_spec": "Readymade Curtains & Window Panels (poly-cotton blend)",
        "containers_12m": 48,
        "est_annual_usd": 5_500_000,
        "last_arrival_date": "2026-08-28",
        "vulnerability_signal": "Post-restructure — rebuilding vendor base, open to competitive direct sourcing",
        "decision_maker_role": "Chief Merchandising Officer",
        "match_score": 79,
        "competitor_fob_usd": 2.90,
        "us_duty_pct": 11.4,
    },
    {
        "sector": "textiles",
        "us_buyer": "Tuesday Morning Corp",
        "hq_city": "Dallas",
        "hq_state": "TX",
        "hs_code": "5702.42",
        "product_spec": "Flat-Weave Dhurrie & Kilim Rugs (cotton/jute blend)",
        "containers_12m": 22,
        "est_annual_usd": 1_800_000,
        "last_arrival_date": "2026-07-18",
        "vulnerability_signal": "Off-price channel — FOB price sensitivity highest, direct sourcing saves 12%+",
        "decision_maker_role": "Buyer - Home Decor & Rugs",
        "match_score": 76,
        "competitor_fob_usd": 5.10,
        "us_duty_pct": 4.5,
    },
    # ===== LEATHER (5 records) =====
    {
        "sector": "leather",
        "us_buyer": "Tapestry Inc (Coach)",
        "hq_city": "New York",
        "hq_state": "NY",
        "hs_code": "4202.21",
        "product_spec": "Full-Grain Leather Handbags & Crossbody Bags",
        "containers_12m": 40,
        "est_annual_usd": 6_500_000,
        "last_arrival_date": "2026-10-08",
        "vulnerability_signal": "Diversifying from Vietnam — piloting 3 Indian tannery partners in Kolkata & Chennai",
        "decision_maker_role": "VP Global Leather Sourcing",
        "match_score": 93,
        "competitor_fob_usd": 28.00,
        "us_duty_pct": 8.0,
    },
    {
        "sector": "leather",
        "us_buyer": "Fossil Group Inc",
        "hq_city": "Richardson",
        "hq_state": "TX",
        "hs_code": "4203.30",
        "product_spec": "Leather Belts, Wallets & Watch Straps",
        "containers_12m": 28,
        "est_annual_usd": 3_200_000,
        "last_arrival_date": "2026-09-22",
        "vulnerability_signal": "China leather tariff at 20% — evaluating Kanpur & Chennai tanneries",
        "decision_maker_role": "Director of Accessories Sourcing",
        "match_score": 86,
        "competitor_fob_usd": 6.80,
        "us_duty_pct": 5.3,
    },
    {
        "sector": "leather",
        "us_buyer": "Johnston & Murphy (Genesco)",
        "hq_city": "Nashville",
        "hq_state": "TN",
        "hs_code": "6403.59",
        "product_spec": "Premium Leather Dress Shoes & Oxford Lace-Ups",
        "containers_12m": 32,
        "est_annual_usd": 4_800_000,
        "last_arrival_date": "2026-09-05",
        "vulnerability_signal": "Long-term India sourcing — expanding Agra/Kanpur vendor pool for FW 2027",
        "decision_maker_role": "SVP Product & Sourcing",
        "match_score": 88,
        "competitor_fob_usd": 18.50,
        "us_duty_pct": 8.5,
    },
    {
        "sector": "leather",
        "us_buyer": "Cole Haan LLC",
        "hq_city": "Greenland",
        "hq_state": "NH",
        "hs_code": "6403.99",
        "product_spec": "Leather Sneakers, Loafers & Driving Mocs",
        "containers_12m": 45,
        "est_annual_usd": 7_200_000,
        "last_arrival_date": "2026-10-15",
        "vulnerability_signal": "Innovation focus — looking for Indian vendors with Grand.OS sole-bonding capability",
        "decision_maker_role": "VP Manufacturing & Sourcing",
        "match_score": 91,
        "competitor_fob_usd": 22.00,
        "us_duty_pct": 10.0,
    },
    {
        "sector": "leather",
        "us_buyer": "Dooney & Bourke Inc",
        "hq_city": "Norwalk",
        "hq_state": "CT",
        "hs_code": "4202.21",
        "product_spec": "Pebble-Grain Leather Totes & Satchels",
        "containers_12m": 18,
        "est_annual_usd": 2_800_000,
        "last_arrival_date": "2026-08-02",
        "vulnerability_signal": "Family-owned — values long-term vendor relationships, 2 India suppliers rotating",
        "decision_maker_role": "Sourcing Manager - Leather Goods",
        "match_score": 80,
        "competitor_fob_usd": 24.00,
        "us_duty_pct": 8.0,
    },
]


# ---------------------------------------------------------------------------
# Section 2: Helper Functions
# ---------------------------------------------------------------------------

# Accept both the current column names and the v1.0 names in uploaded CSVs.
CSV_ALIASES = {"company_name": "us_buyer", "est_annual_volume_usd": "est_annual_usd"}
CSV_FIELDS = [
    "id", "sector", "us_buyer", "hq_city", "hq_state", "hs_code",
    "product_spec", "containers_12m", "est_annual_usd", "last_arrival_date",
    "competitor_fob_usd", "us_duty_pct", "vulnerability_signal",
    "decision_maker_role", "match_score",
]


def _row_to_buyer(row: Dict[str, str]) -> Buyer:
    """Convert one CSV row (ImportYeti-style export) into a Buyer."""
    clean = {}
    for key, value in row.items():
        if key is None:
            continue
        k = key.strip().lower()
        k = CSV_ALIASES.get(k, k)
        v = (value or "").strip()
        if v:
            clean[k] = v
    clean["sector"] = clean.get("sector", "handicrafts").lower()
    if "containers_12m" in clean:
        clean["containers_12m"] = int(float(clean["containers_12m"]))
    if "match_score" in clean:
        clean["match_score"] = int(float(clean["match_score"]))
    for k in ("est_annual_usd", "competitor_fob_usd", "us_duty_pct"):
        if k in clean:
            clean[k] = float(clean[k].replace(",", "").replace("$", ""))
    return Buyer(**{k: v for k, v in clean.items() if k in Buyer.model_fields})


def _import_csv_text(text: str) -> Dict:
    """Parse CSV text, append valid rows to BUYERS_DB, report row errors."""
    reader = csv.DictReader(io.StringIO(text.lstrip("﻿")))
    added: List[Buyer] = []
    errors: List[str] = []
    for i, row in enumerate(reader, start=2):
        try:
            buyer = _row_to_buyer(row)
        except Exception as exc:
            errors.append(f"Row {i}: {exc}".splitlines()[0])
            continue
        if _find_buyer(buyer.id):
            buyer.id = uuid.uuid4().hex[:8]
        BUYERS_DB.append(buyer)
        added.append(buyer)
    return {
        "added": len(added),
        "sectors": sorted({b.sector for b in added}),
        "errors": errors[:10],
        "total_in_db": len(BUYERS_DB),
    }


def _load_initial_buyers() -> None:
    """Client deployments ship a client_buyers.csv; otherwise use the demo seed."""
    if os.path.isfile(BUYERS_CSV):
        with open(BUYERS_CSV, encoding="utf-8-sig") as fh:
            _import_csv_text(fh.read())
        return
    counters = {s: 0 for s in SECTORS}
    for item in SEED_DATA:
        counters[item["sector"]] += 1
        sid = f"{SECTOR_ID_PREFIX[item['sector']]}-{counters[item['sector']]:02d}"
        BUYERS_DB.append(Buyer(id=sid, **item))


def _find_buyer(buyer_id: str) -> Optional[Buyer]:
    """Look up a buyer by ID in the in-memory store."""
    return next((b for b in BUYERS_DB if b.id == buyer_id), None)


def _fmt_date(value: str) -> str:
    """2026-09-14 -> 14 Sep 2026 (leaves unparseable values untouched)."""
    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime("%d %b %Y")
    except ValueError:
        return value


def calculate_cost(buyer: Buyer, your_fob_usd: float) -> CostResult:
    """Landed cost = FOB x (1 + US duty % + 8% freight & insurance)."""
    multiplier = 1 + buyer.us_duty_pct / 100 + FREIGHT_INSURANCE_PCT / 100

    competitor_landed = buyer.competitor_fob_usd * multiplier
    your_landed = your_fob_usd * multiplier
    savings_per_unit = competitor_landed - your_landed

    return CostResult(
        buyer_id=buyer.id,
        us_buyer=buyer.us_buyer,
        hs_code=buyer.hs_code,
        product_spec=buyer.product_spec,
        us_duty_pct=buyer.us_duty_pct,
        competitor_fob_usd=round(buyer.competitor_fob_usd, 2),
        competitor_landed_usd=round(competitor_landed, 2),
        your_fob_usd=round(your_fob_usd, 2),
        your_landed_usd=round(your_landed, 2),
        savings_per_unit_usd=round(savings_per_unit, 2),
        annual_savings_10k_usd=round(savings_per_unit * 10_000, 2),
        landed_savings_pct=round(savings_per_unit / competitor_landed * 100, 1),
        agent_commission_saved_inr=round(
            buyer.est_annual_usd * AGENT_COMMISSION_PCT / 100 * USD_TO_INR, 2
        ),
    )


def _build_templates(
    buyer: Buyer, factory_name: str, factory_city: str, your_fob: float
) -> OutreachResponse:
    """Deterministic outreach templates — zero-cost fallback."""
    c = calculate_cost(buyer, your_fob)
    arrival = _fmt_date(buyer.last_arrival_date)
    hq = f"{buyer.hq_city}, {buyer.hq_state}" if buyer.hq_state else buyer.hq_city
    pct = c.landed_savings_pct

    if pct > 0:
        subject_hook = f"{pct:.0f}% lower landed cost"
        price_line = (
            f"That is {pct:.1f}% below your current landed cost — about "
            f"${c.annual_savings_10k_usd:,.0f} a year on 10,000 units — before "
            f"you remove the 5–8% buying-agent commission."
        )
        dm_price = f"about {pct:.0f}% below your current landed cost"
    else:
        subject_hook = "direct factory pricing"
        price_line = (
            "Buying direct also removes the 5–8% buying-agent commission "
            "from every order."
        )
        dm_price = "direct from the factory with no agent commission"

    cold_subject = (
        f"HS {buyer.hs_code} {buyer.product_spec}: {subject_hook} for {buyer.us_buyer}"
    )
    cold_body = (
        f"Dear {buyer.decision_maker_role},\n\n"
        f"US Customs bill-of-lading records show {buyer.us_buyer} cleared "
        f"{buyer.containers_12m} containers under HS {buyer.hs_code} in the last "
        f"12 months (~${buyer.est_annual_usd:,.0f}), with the most recent arrival "
        f"on {arrival}.\n\n"
        f"I’m writing from {factory_name} in {factory_city}, India. We "
        f"manufacture {buyer.product_spec} for direct export, and our quote is "
        f"${c.your_fob_usd:.2f}/unit FOB. Landed in the US that is "
        f"${c.your_landed_usd:.2f}/unit against roughly "
        f"${c.competitor_landed_usd:.2f}/unit on your current supply "
        f"({buyer.us_duty_pct:g}% duty + 8% freight & insurance included).\n\n"
        f"{price_line}\n\n"
        f"Could I send a complimentary sample box to your {buyer.hq_city} office "
        f"this week? A 10-minute call is enough to confirm specifications.\n\n"
        f"Best regards,\n{factory_name}\n{factory_city}, India"
    )

    followup_subject = (
        f"Complimentary DHL sample box for {buyer.us_buyer} — ready to ship "
        f"to {buyer.hq_city}"
    )
    followup_body = (
        f"Hi,\n\n"
        f"Following up on my note about HS {buyer.hs_code} "
        f"{buyer.product_spec}. We would like to send a complimentary "
        f"pre-production sample box to your {hq} headquarters by DHL Express, "
        f"at our cost.\n\n"
        f"The box includes:\n"
        f"• 3–5 pre-production samples of {buyer.product_spec}\n"
        f"• A side-by-side spec sheet comparing our materials, construction "
        f"and finish against your current HS {buyer.hs_code} supply\n"
        f"• Our FOB price sheet (${c.your_fob_usd:.2f}/unit) with the landed-cost "
        f"breakdown (${c.your_landed_usd:.2f} vs ${c.competitor_landed_usd:.2f}/unit)\n"
        f"• Factory audit and compliance documents\n\n"
        f"Reply with the best shipping contact and it leaves {factory_city} within "
        f"48 hours (2–3 business days to {buyer.hq_city}).\n\n"
        f"Best regards,\n{factory_name}\n{factory_city}, India"
    )

    linkedin_whatsapp = (
        f"Hi — US Customs data shows {buyer.us_buyer} brought in "
        f"{buyer.containers_12m} containers of HS {buyer.hs_code} "
        f"{buyer.product_spec} over the last 12 months, most recently on {arrival}. "
        f"We make the same product at {factory_name} in {factory_city} and can land "
        f"it at ${c.your_landed_usd:.2f}/unit, {dm_price}. "
        f"Can I send a complimentary DHL sample box to your {buyer.hq_city} team "
        f"this week?"
    )

    return OutreachResponse(
        cold_email_subject=cold_subject,
        cold_email_body=cold_body,
        followup_subject=followup_subject,
        followup_body=followup_body,
        linkedin_whatsapp=linkedin_whatsapp,
        engine="template",
    )


def _build_gemini_prompt(
    buyer: Buyer, factory_name: str, factory_city: str, your_fob: float
) -> str:
    """Construct the Gemini API prompt for outreach generation."""
    c = calculate_cost(buyer, your_fob)
    return (
        "You are a B2B export trade outreach specialist. Write 3 personalized "
        "messages from an Indian export manufacturer to a US importer.\n\n"
        f"Context:\n"
        f"- Indian factory: {factory_name} ({factory_city}, India)\n"
        f"- US buyer: {buyer.us_buyer} (HQ {buyer.hq_city}, {buyer.hq_state})\n"
        f"- Product: {buyer.product_spec} (HS {buyer.hs_code})\n"
        f"- US Customs BoL, last 12 months: {buyer.containers_12m} containers "
        f"(~${buyer.est_annual_usd:,.0f}); last arrival {_fmt_date(buyer.last_arrival_date)}\n"
        f"- Decision maker: {buyer.decision_maker_role}\n"
        f"- Our FOB ${c.your_fob_usd:.2f}/unit -> landed ${c.your_landed_usd:.2f}/unit; "
        f"current supply landed ${c.competitor_landed_usd:.2f}/unit "
        f"({c.landed_savings_pct:.1f}% landed-cost saving, "
        f"${c.annual_savings_10k_usd:,.0f}/yr on 10,000 units)\n"
        f"- Internal context (do not quote directly): {buyer.vulnerability_signal}\n\n"
        "Return ONLY a JSON object with these exact keys:\n"
        '{"cold_email_subject":"...","cold_email_body":"...",'
        '"followup_subject":"...","followup_body":"...",'
        '"linkedin_whatsapp":"..."}\n\n'
        "Guidelines:\n"
        "1. Day 1 cold email: cite the exact container count, HS code and last "
        "arrival date from US Customs records, and the landed-cost saving %. "
        "Offer a complimentary sample box.\n"
        "2. Day 3 follow-up: offer a complimentary pre-production sample box "
        f"shipped by DHL to their {buyer.hq_city} headquarters, with a "
        "side-by-side spec sheet against their current supply.\n"
        "3. LinkedIn/WhatsApp: exactly 3 sentences to the "
        f"{buyer.decision_maker_role}, direct and specific.\n"
        "Plain text bodies with \\n line breaks. No placeholders in brackets."
    )


def _call_gemini(prompt: str) -> Optional[str]:
    """Call Gemini API via urllib.request. Returns text or None on failure."""
    if not GEMINI_API_KEY:
        return None
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent"
    )
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 2048,
            "responseMimeType": "application/json",
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return None


def generate_outreach(
    buyer: Buyer, factory_name: str, factory_city: str, your_fob: float
) -> OutreachResponse:
    """Generate outreach: try Gemini API, fall back to deterministic templates."""
    if GEMINI_API_KEY:
        prompt = _build_gemini_prompt(buyer, factory_name, factory_city, your_fob)
        raw = _call_gemini(prompt)
        if raw:
            try:
                cleaned = raw.strip()
                # Strip markdown code fences if present
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                data = json.loads(cleaned)
                data["engine"] = "gemini"
                return OutreachResponse(**data)
            except Exception:
                pass  # Fall through to templates
    return _build_templates(buyer, factory_name, factory_city, your_fob)


_load_initial_buyers()


# ---------------------------------------------------------------------------
# Section 2: API Endpoints
# ---------------------------------------------------------------------------

def _sector_filter(category: Optional[str], sector: Optional[str]) -> List[Buyer]:
    wanted = category or sector
    return [b for b in BUYERS_DB if b.sector == wanted] if wanted else list(BUYERS_DB)


@app.get("/api/buyers", response_model=List[Buyer])
async def list_buyers(
    category: Optional[str] = Query(None, description="Filter by sector slug"),
    sector: Optional[str] = Query(None, description="Alias of category"),
):
    """List all buyers, optionally filtered by sector."""
    return _sector_filter(category, sector)


@app.post("/api/buyers/add", response_model=Buyer)
async def add_buyer(payload: BuyerAdd):
    """Add a single US buyer record via JSON."""
    buyer = Buyer(**payload.model_dump())
    BUYERS_DB.append(buyer)
    return buyer


@app.post("/api/buyers/import-csv")
async def import_csv(request: Request):
    """Import buyers from CSV.

    Accepts a raw text/csv body (what the dashboard sends), a JSON body
    {"csv": "..."}, or a multipart upload with a "file" field. The raw and
    JSON paths work without python-multipart installed.
    """
    ctype = request.headers.get("content-type", "")
    if ctype.startswith("multipart/form-data"):
        try:
            form = await request.form()
            upload = form.get("file")
            raw = await upload.read() if upload is not None else b""
        except Exception as exc:
            raise HTTPException(400, f"Could not read multipart upload: {exc}")
    elif ctype.startswith("application/json"):
        body = await request.json()
        raw = str(body.get("csv", "")).encode("utf-8")
    else:
        raw = await request.body()

    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")
    if not text.strip():
        raise HTTPException(400, "Empty CSV")
    return JSONResponse(_import_csv_text(text))


@app.get("/api/export-csv")
async def export_csv(
    category: Optional[str] = Query(None, description="Filter by sector slug"),
    sector: Optional[str] = Query(None, description="Alias of category"),
):
    """Download the buyer table as CSV (re-importable via /api/buyers/import-csv)."""
    filtered = _sector_filter(category, sector)
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=CSV_FIELDS)
    writer.writeheader()
    for b in filtered:
        writer.writerow({k: getattr(b, k) for k in CSV_FIELDS})

    ts = datetime.now().strftime("%Y%m%d")
    fname = f"exportpulse_buyers_{category or sector or 'all'}_{ts}.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@app.get("/api/cost-calc/{buyer_id}", response_model=CostResult)
async def cost_calc(
    buyer_id: str,
    your_fob_usd: Optional[float] = Query(
        None, gt=0, description="Your FOB price; defaults to 90 percent of competitor"
    ),
):
    """Calculate FOB & landed-cost comparison for a buyer."""
    buyer = _find_buyer(buyer_id)
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")
    fob = (
        your_fob_usd
        if your_fob_usd is not None
        else round(buyer.competitor_fob_usd * 0.90, 2)
    )
    return calculate_cost(buyer, fob)


@app.post("/api/outreach", response_model=OutreachResponse)
def outreach_endpoint(req: OutreachRequest):
    """Generate 3-tab outreach messages for a buyer.

    Sync on purpose: FastAPI runs it in a worker thread, so a slow Gemini
    call never blocks the event loop.
    """
    buyer = _find_buyer(req.buyer_id)
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")
    fob = (
        req.your_fob_usd
        if req.your_fob_usd > 0
        else round(buyer.competitor_fob_usd * 0.90, 2)
    )
    return generate_outreach(buyer, req.factory_name, req.factory_city, fob)


# ---------------------------------------------------------------------------
# Section 3: HTML Dashboard (Chartroom design, single page; see DESIGN.md)
# ---------------------------------------------------------------------------

DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ExportPulse AI — __FACTORY_HTML__</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..700&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Spline+Sans+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{
  --shell:#0F1D2B;--shell-2:#16293B;--shell-3:#1F3448;--shell-line:#22374B;--on-shell:#E6EDF2;--on-shell-2:#9FB2C0;
  --panel:#FFFFFF;--panel-2:#F4F6F7;--line:#DCE3E6;--line-2:#EEF2F3;
  --ink:#14232C;--ink-2:#44555E;--muted:#6F8189;--faint:#9AA8AE;
  --sea:#E2ECEC;--shoal:#CFE0E3;--land:#EDE4CB;--land-home:#E4D29F;--coast:#B5A57C;--grat:#C9D8D9;
  --mag:#B0235B;--mag-d:#8E1A48;--mag-2:#D27CA0;--mag-soft:#FBEFF4;
  --green:#1F6B41;--green-soft:#E6F3EB;--amber:#8A5A12;--amber-soft:#FBF3E4;--red:#B42318;--red-soft:#FDECEC;
  --sans:'Archivo',system-ui,-apple-system,'Segoe UI',sans-serif;
  --mono:'Spline Sans Mono',ui-monospace,Consolas,monospace;
  --pshadow:0 1px 2px rgba(15,29,43,.06),0 16px 36px -18px rgba(15,29,43,.35);
  --ease:cubic-bezier(.2,.75,.15,1);
}
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box}
html,body{height:100%}
body{font-family:var(--sans);background:var(--shell);color:var(--ink);font-size:13px;line-height:1.45;-webkit-font-smoothing:antialiased}
button,input,select,textarea{font:inherit;color:inherit}
button{cursor:pointer;background:none;border:none}
:focus-visible{outline:2px solid var(--mag);outline-offset:2px}
.num{font-variant-numeric:tabular-nums lining-nums}
.mono{font-family:var(--mono)}
.lbl{font-stretch:115%;font-weight:600;font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}

/* ============ App shell ============ */
.app{display:grid;grid-template-rows:56px minmax(0,1fr);height:100vh}
.tb{display:flex;align-items:center;gap:10px;padding:0 14px;color:var(--on-shell);min-width:0}
.brand{display:flex;align-items:center;gap:9px;font-stretch:125%;font-weight:700;font-size:12px;letter-spacing:.2em;white-space:nowrap;margin-right:6px}
.search{position:relative;width:min(300px,26vw)}
.search svg{position:absolute;left:10px;top:50%;transform:translateY(-50%);color:var(--on-shell-2);pointer-events:none}
.search input{width:100%;height:34px;padding:0 10px 0 32px;border-radius:9px;border:1px solid var(--shell-line);background:var(--shell-2);color:var(--on-shell);font-size:13px}
.search input::placeholder{color:#7F93A3}
.search input:focus{outline:none;border-color:#3B556D;background:var(--shell-3)}
.sel-wrap{position:relative}
.sel-wrap select{appearance:none;-webkit-appearance:none;height:34px;padding:0 30px 0 12px;border-radius:9px;border:1px solid var(--shell-line);background:var(--shell-2);color:var(--on-shell);font-size:13px;font-weight:500;cursor:pointer}
.sel-wrap select:focus{outline:none;border-color:#3B556D}
.sel-wrap svg{position:absolute;right:10px;top:50%;transform:translateY(-50%);pointer-events:none;color:var(--on-shell-2)}
.spacer{flex:1}
.kpi{display:flex;align-items:baseline;gap:6px;height:34px;padding:0 12px;border-radius:9px;background:var(--shell-2);white-space:nowrap}
.kpi b{font-size:14px;font-weight:600;color:#fff;letter-spacing:-.01em}
.kpi span{font-size:12px;color:var(--on-shell-2);align-self:center}
.kpi b{align-self:center}
.vsep{width:1px;height:22px;background:var(--shell-line);margin:0 2px}
.ib{display:grid;place-items:center;width:34px;height:34px;border-radius:9px;color:var(--on-shell-2);transition:background .15s,color .15s}
.ib:hover{background:var(--shell-2);color:var(--on-shell)}
.cta{display:inline-flex;align-items:center;gap:8px;height:34px;padding:0 14px;border-radius:9px;background:var(--mag);color:#fff;font-weight:600;font-size:13px;text-decoration:none;white-space:nowrap;transition:background .15s}
.cta:hover{background:#C2306B}
.menu-wrap{position:relative}
.menu{position:absolute;right:0;top:calc(100% + 8px);background:#fff;color:var(--ink);border:1px solid var(--line);border-radius:12px;padding:6px;min-width:240px;display:none;z-index:60;box-shadow:var(--pshadow)}
.menu.show{display:block;animation:fade .16s var(--ease)}
@keyframes fade{from{opacity:0;transform:translateY(-4px)}}
.menu button{display:flex;align-items:center;gap:10px;width:100%;text-align:left;padding:9px 10px;border-radius:8px;font-size:13px}
.menu button:hover{background:var(--panel-2)}
.menu button svg{color:var(--muted);flex-shrink:0}
.menu .sep{height:1px;background:var(--line);margin:6px 4px}

/* ============ Workspace ============ */
.ws{position:relative;min-height:0}
.stage{position:absolute;inset:0 10px 10px;border-radius:14px;overflow:hidden;background:var(--sea)}
#map{display:block;width:100%;height:100%;cursor:grab;touch-action:none}
#map.dragging{cursor:grabbing}
.m-shoal path{fill:none;stroke:var(--shoal);stroke-width:7;stroke-linejoin:round;vector-effect:non-scaling-stroke}
.m-land path{fill:var(--land);stroke:var(--coast);stroke-width:.5;vector-effect:non-scaling-stroke}
.m-land path.home{fill:var(--land-home)}
.m-grat{fill:none;stroke:var(--grat);stroke-width:.6;vector-effect:non-scaling-stroke}
.lane{fill:none;stroke:var(--mag-2);stroke-width:1.3;stroke-linecap:round;stroke-linejoin:round;vector-effect:non-scaling-stroke;opacity:.9}
.leg{fill:none;stroke:var(--ink-2);stroke-width:1;stroke-dasharray:1.5 3;stroke-linecap:round;opacity:.6;vector-effect:non-scaling-stroke}
.lane-on{fill:none;stroke:var(--mag);stroke-width:2.8;stroke-linecap:round;stroke-linejoin:round;vector-effect:non-scaling-stroke}
.lane-on.preview{opacity:.5}
.leg-on{fill:none;stroke:var(--mag);stroke-width:1.4;stroke-dasharray:2 3;stroke-linecap:round;vector-effect:non-scaling-stroke}
.m-water{font-family:var(--sans);font-stretch:115%;font-size:9.5px;font-weight:500;letter-spacing:.22em;fill:#86A6AE;text-anchor:middle;pointer-events:none}
.halo{paint-order:stroke;stroke:var(--sea);stroke-width:4px;stroke-linejoin:round}
.port rect{fill:#fff;stroke:var(--ink);stroke-width:1.2}
.port text{font-family:var(--mono);font-size:9.5px;fill:var(--ink-2);letter-spacing:.04em}
.org-dot{fill:var(--mag);stroke:#fff;stroke-width:2}
.org-name{font-family:var(--sans);font-size:12px;font-weight:600;fill:var(--ink)}
.org-sub{font-family:var(--mono);font-size:9.5px;fill:var(--ink-2);letter-spacing:.06em}
.mk{cursor:pointer;outline:none}
.mk-c{fill:#fff;stroke:var(--mag);stroke-width:1.6;transition:fill .15s}
.mk-n{font-family:var(--mono);font-size:10.5px;font-weight:600;fill:var(--mag);text-anchor:middle;dominant-baseline:central;pointer-events:none}
.mk:hover .mk-c,.mk:focus-visible .mk-c,.mk.hov .mk-c{fill:var(--mag-soft)}
.mk.on .mk-c{fill:var(--mag)}
.mk.on .mk-n{fill:#fff}
.mk-lead{stroke:var(--ink-2);stroke-width:.8;opacity:.55}
.m-off{font-family:var(--sans);font-size:14px;fill:var(--ink-2)}
.fade-in{animation:fadeIn .6s var(--ease) both}
@keyframes fadeIn{from{opacity:0}}

/* floating panels */
.pn{position:absolute;top:12px;bottom:22px;background:var(--panel);border:1px solid var(--line);border-radius:12px;box-shadow:var(--pshadow);display:flex;flex-direction:column;min-height:0;overflow:hidden}
.left{left:22px;width:316px}
.detail{right:22px;width:384px;transform:translateX(calc(100% + 24px));transition:transform .32s var(--ease);visibility:hidden}
.detail.open{transform:none;visibility:visible}
.ph{padding:14px 16px 12px;border-bottom:1px solid var(--line-2)}
h1.who{font-size:16px;font-weight:600;letter-spacing:-.01em;line-height:1.25;margin-top:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.who-sub{display:flex;align-items:center;gap:6px;font-size:12px;color:var(--ink-2);margin-top:3px}
.who-sub .mono{font-size:11px;color:var(--muted)}
.chips{display:flex;gap:6px;padding:10px 16px;border-bottom:1px solid var(--line-2);flex-wrap:wrap}
.fchip{height:26px;padding:0 10px;border-radius:999px;border:1px solid var(--line);font-size:12px;font-weight:500;color:var(--ink-2);white-space:nowrap;transition:background .15s,color .15s,border-color .15s}
.fchip:hover{border-color:#C4CED2}
.fchip.on{background:var(--ink);border-color:var(--ink);color:#fff}
.fchip .c{font-family:var(--mono);font-size:10.5px;opacity:.7;margin-left:4px}
.list-head{display:flex;justify-content:space-between;align-items:center;padding:10px 16px 4px}
.list{overflow-y:auto;flex:1;min-height:0;padding:4px 6px 8px;scrollbar-width:thin;scrollbar-color:var(--line) transparent}
.imp{display:grid;grid-template-columns:24px minmax(0,1fr) auto;gap:10px;align-items:center;width:100%;text-align:left;padding:9px 10px;border-radius:9px;transition:background .12s}
.imp:hover,.imp.hov{background:var(--panel-2)}
.imp.on{background:var(--mag-soft)}
.badge{width:22px;height:22px;border-radius:50%;border:1.5px solid var(--mag);color:var(--mag);display:grid;place-items:center;font-family:var(--mono);font-size:10.5px;font-weight:600;background:#fff}
.imp.on .badge{background:var(--mag);color:#fff}
.imp b{display:block;font-size:13px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.imp small{display:block;font-size:11.5px;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:1px}
.imp-side{text-align:right}
.score{display:inline-block;min-width:34px;padding:2px 7px;border-radius:999px;font-family:var(--mono);font-size:11px;font-weight:600;text-align:center}
.score.hi{background:var(--green-soft);color:var(--green)}
.score.md{background:var(--amber-soft);color:var(--amber)}
.score.lo{background:var(--red-soft);color:var(--red)}
.imp-side small{font-family:var(--mono);font-size:10.5px;margin-top:3px}
.empty{padding:32px 16px;text-align:center;color:var(--muted);font-size:13px}

/* map chrome */
.legend{position:absolute;bottom:14px;display:flex;flex-wrap:wrap;gap:4px 14px;align-items:center;background:rgba(255,255,255,.94);border:1px solid var(--line);border-radius:9px;padding:6px 10px;font-size:11.5px;color:var(--ink-2);transition:left .32s var(--ease)}
.legend span{display:inline-flex;align-items:center;gap:6px}
.zoom{position:absolute;bottom:14px;display:flex;flex-direction:column;background:#fff;border:1px solid var(--line);border-radius:9px;overflow:hidden;box-shadow:var(--pshadow);transition:right .32s var(--ease)}
.zoom button{width:32px;height:30px;display:grid;place-items:center;color:var(--ink-2)}
.zoom button+button{border-top:1px solid var(--line-2)}
.zoom button:hover{background:var(--panel-2);color:var(--ink)}

/* detail panel */
.dh{display:flex;align-items:flex-start;gap:10px;padding:14px 14px 10px 16px}
.dh h2{font-size:16px;font-weight:600;letter-spacing:-.01em;line-height:1.25}
.dh p{font-size:12px;color:var(--muted);margin-top:3px}
.x{width:30px;height:30px;border-radius:8px;display:grid;place-items:center;color:var(--muted);flex-shrink:0;margin-left:auto}
.x:hover{background:var(--panel-2);color:var(--ink)}
.tabs{display:flex;gap:2px;margin:0 16px;padding:3px;background:var(--panel-2);border-radius:9px}
.tabs button{flex:1;height:28px;border-radius:7px;font-size:12.5px;font-weight:500;color:var(--ink-2);white-space:nowrap}
.tabs button.on{background:#fff;color:var(--ink);box-shadow:0 0 0 1px var(--line)}
.body{flex:1;min-height:0;overflow-y:auto;padding:16px;scrollbar-width:thin;scrollbar-color:var(--line) transparent}
.tp[hidden]{display:none}
.facts{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.fact{background:var(--panel-2);border-radius:9px;padding:10px 12px}
.fact .k{font-size:11.5px;color:var(--muted)}
.fact .v{font-size:17px;font-weight:600;letter-spacing:-.015em;margin-top:3px}
.fact .s{font-size:11px;color:var(--muted);margin-top:1px}
.kv{margin-top:14px;display:grid;gap:10px}
.kv>div{display:grid;grid-template-columns:96px 1fr;gap:10px;font-size:12.5px}
.kv dt{color:var(--muted)}
.kv dd{color:var(--ink)}
.hs{display:inline-block;font-family:var(--mono);font-size:11px;border:1px solid var(--line);border-radius:5px;padding:0 5px;margin-right:4px;color:var(--ink-2)}
.signal{display:flex;gap:8px;align-items:flex-start;margin-top:14px;padding:10px 12px;border-radius:9px;background:var(--amber-soft);color:#6B4A10;font-size:12.5px}
.signal svg{flex-shrink:0;margin-top:2px}
.btns{display:flex;gap:8px;margin-top:16px}
.btn-p,.btn-s{flex:1;display:inline-flex;align-items:center;justify-content:center;gap:7px;height:38px;border-radius:9px;font-weight:600;font-size:13px;transition:background .15s}
.btn-p{background:var(--mag);color:#fff}
.btn-p:hover{background:var(--mag-d)}
.btn-s{border:1px solid var(--line);color:var(--ink)}
.btn-s:hover{background:var(--panel-2)}
.quote{display:flex;align-items:center;gap:8px}
.qv{flex:1;display:flex;align-items:baseline;gap:2px;min-width:0}
.qv .cur{font-size:22px;font-weight:500;color:var(--faint)}
#fobIn{width:100%;min-width:0;border:none;background:transparent;font-size:40px;font-weight:600;letter-spacing:-.035em;line-height:1;-moz-appearance:textfield;appearance:textfield;padding:0}
#fobIn::-webkit-outer-spin-button,#fobIn::-webkit-inner-spin-button{-webkit-appearance:none;margin:0}
#fobIn:focus{outline:none;color:var(--mag)}
.rb{width:34px;height:34px;border-radius:9px;border:1px solid var(--line);font-size:16px;line-height:1;color:var(--ink-2)}
.rb:hover{background:var(--panel-2)}
.q-sub{font-size:11.5px;color:var(--muted);margin-top:2px}
.rng{position:relative;margin-top:18px;padding-bottom:22px}
#fobRange{-webkit-appearance:none;appearance:none;width:100%;height:6px;border-radius:6px;background:linear-gradient(90deg,var(--mag) 0 calc(var(--pct,50)*1%),var(--line-2) calc(var(--pct,50)*1%) 100%);outline:none}
#fobRange::-webkit-slider-thumb{-webkit-appearance:none;width:18px;height:18px;border-radius:50%;background:#fff;border:2px solid var(--mag);box-shadow:0 1px 4px rgba(15,29,43,.25);cursor:grab}
#fobRange::-moz-range-thumb{width:14px;height:14px;border-radius:50%;background:#fff;border:2px solid var(--mag);cursor:grab}
.mark{position:absolute;top:-6px;left:calc(var(--m,50)*1%);width:2px;height:18px;border-radius:2px;background:var(--ink);pointer-events:none}
.mark span{position:absolute;top:22px;left:50%;transform:translateX(-50%);font-family:var(--mono);font-size:10.5px;color:var(--ink-2);white-space:nowrap}
.res{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:6px}
.res>div{padding:12px;border-radius:9px}
.res .k{font-size:11.5px;font-weight:500;color:var(--ink-2)}
.res .v{font-size:22px;font-weight:600;letter-spacing:-.03em;line-height:1.1;margin-top:5px;white-space:nowrap}
.res .s{font-size:11px;color:var(--muted);margin-top:2px}
#tSave{background:var(--green-soft)}
#tSave .v{color:var(--green)}
#tSave.neg{background:var(--red-soft)}
#tSave.neg .v{color:var(--red)}
#tComm{background:var(--mag-soft)}
#tComm .v{color:var(--mag)}
.note{font-size:11.5px;color:var(--muted);margin-top:12px}
.stops{list-style:none;position:relative}
.stops::before{content:"";position:absolute;left:5px;top:8px;bottom:8px;border-left:1.5px dashed var(--mag-2)}
.stops li{position:relative;padding:0 0 12px 22px;font-size:13px}
.stops li::before{content:"";position:absolute;left:0;top:4px;width:11px;height:11px;border-radius:50%;background:#fff;border:1.5px solid var(--mag)}
.stops li.via::before{width:7px;height:7px;left:2px;top:6px;border-color:var(--mag-2)}
.stops li.via{color:var(--muted);font-size:12px}
.stops li.end::before{background:var(--mag)}
.stops b{font-weight:600}
.stops span{display:block;font-family:var(--mono);font-size:10.5px;color:var(--muted)}
.lc{margin-top:8px;display:grid;gap:12px;padding-top:14px;border-top:1px solid var(--line-2)}
.lc .row{display:flex;justify-content:space-between;align-items:baseline;font-size:12.5px;color:var(--ink-2)}
.lc .row b{font-size:15px;font-weight:600;color:var(--ink)}
.cbar{height:8px;border-radius:5px;background:var(--line-2);margin-top:6px;overflow:hidden}
.cbar i{display:block;height:100%;width:0;border-radius:5px;transition:width .5s var(--ease)}
.cbar.comp i{background:#9AA8AE}
.cbar.you i{background:var(--mag)}
.delta{display:inline-flex;margin-top:14px;padding:5px 9px;border-radius:7px;font-size:12px;font-weight:600;background:var(--green-soft);color:var(--green)}
.delta.neg{background:var(--red-soft);color:var(--red)}
.otabs{display:flex;gap:2px;padding:3px;background:var(--panel-2);border-radius:9px}
.otabs button{flex:1;height:28px;border-radius:7px;font-size:12px;font-weight:500;color:var(--ink-2);white-space:nowrap}
.otabs button .d{font-family:var(--mono);font-size:10.5px;color:var(--muted);margin-right:4px}
.otabs button.on{background:#fff;color:var(--ink);box-shadow:0 0 0 1px var(--line)}
.msg{margin-top:10px;border:1px solid var(--line);border-radius:10px;overflow:hidden}
.msg .subj{padding:9px 12px;border-bottom:1px solid var(--line-2);font-size:12.5px;font-weight:600;background:#FAFBFB;line-height:1.4}
.msg .mbody{padding:10px 12px;font-size:12.5px;line-height:1.6;white-space:pre-wrap;max-height:300px;overflow-y:auto;color:var(--ink-2)}
.copy{display:flex;align-items:center;justify-content:center;gap:8px;width:100%;height:38px;margin-top:10px;border-radius:9px;background:var(--ink);color:#fff;font-weight:600;font-size:13px;transition:background .15s}
.copy:hover{background:#25394A}
.copy.ok{background:var(--green)}
.otag{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}
.tag{font-family:var(--mono);font-size:10.5px;color:var(--muted);padding:2px 8px;border-radius:999px;background:var(--panel-2)}
.tag.ai{color:#3355CC;background:#EEF2FF}
.wait{color:var(--muted);font-size:13px;padding:24px 0;text-align:center}

/* ============ Modals ============ */
.mov{display:none;position:fixed;inset:0;background:rgba(15,29,43,.5);z-index:1000;align-items:center;justify-content:center;padding:16px}
.mov.show{display:flex}
.mod{background:#fff;border-radius:14px;padding:22px;width:620px;max-width:100%;max-height:90vh;overflow-y:auto;box-shadow:0 30px 80px -20px rgba(15,29,43,.5);animation:fade .2s var(--ease)}
.mod.sm{width:440px}
.mh{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:18px}
.mh h2{font-size:17px;font-weight:600;letter-spacing:-.01em}
.mh p{font-size:12.5px;color:var(--muted);margin-top:3px}
.fg{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.fi.full{grid-column:1/-1}
.fi label{display:block;font-size:12px;font-weight:500;color:var(--ink-2);margin-bottom:5px}
.fi input,.fi select,.fi textarea{width:100%;padding:8px 11px;border:1px solid var(--line);border-radius:9px;font-size:13px;background:#fff}
.fi input:focus,.fi select:focus,.fi textarea:focus{outline:none;border-color:var(--mag);box-shadow:0 0 0 3px rgba(176,35,91,.14)}
.fi textarea{resize:vertical;min-height:60px}
.fa{margin-top:18px;display:flex;gap:8px;justify-content:flex-end}
.btn{display:inline-flex;align-items:center;justify-content:center;height:38px;padding:0 16px;border-radius:9px;border:1px solid var(--line);background:#fff;font-weight:600;font-size:13px}
.btn:hover{background:var(--panel-2)}
.btn-ink{background:var(--ink);border-color:var(--ink);color:#fff}
.btn-ink:hover{background:#25394A}
.csvinfo{font-size:12.5px;color:var(--ink-2);line-height:1.65;margin-bottom:14px}
.csvinfo code{font-family:var(--mono);font-size:11px;background:var(--panel-2);border-radius:5px;padding:1px 5px;word-break:break-word}
.drop{border:1.5px dashed var(--line);border-radius:10px;padding:24px;text-align:center;background:#FAFBFB}
.how{list-style:none;counter-reset:h;display:grid;gap:14px}
.how li{counter-increment:h;display:grid;grid-template-columns:30px 1fr;gap:12px}
.how li::before{content:counter(h);width:28px;height:28px;border-radius:50%;background:var(--mag-soft);color:var(--mag);font-family:var(--mono);font-size:12px;font-weight:600;display:grid;place-items:center}
.how b{display:block;font-size:13.5px;font-weight:600}
.how span{font-size:12.5px;color:var(--muted)}
.toast{position:fixed;left:50%;bottom:24px;transform:translate(-50%,12px);background:var(--ink);color:#fff;padding:10px 16px;border-radius:999px;font-size:13px;font-weight:500;z-index:2000;opacity:0;transition:opacity .2s,transform .2s;pointer-events:none;max-width:calc(100% - 32px);text-align:center}
.toast.show{opacity:1;transform:translate(-50%,0)}

/* ============ Responsive ============ */
@media (max-width:1320px){ .kpi.k3{display:none} }
@media (max-width:1180px){ .kpi.k2{display:none} .left{width:288px} .detail{width:352px} }
@media (max-width:980px){
  html,body{height:auto}
  .app{display:block;height:auto}
  .tb{flex-wrap:wrap;height:auto;padding:10px 12px;row-gap:8px}
  .search{order:5;width:100%}
  .spacer{display:none}
  .kpi.k1{order:6}
  .kpi.k2,.kpi.k3{display:flex;order:6}
  .vsep{display:none}
  .ws{padding:0 10px 10px}
  .stage{position:relative;inset:auto;height:52vh;min-height:320px}
  .stage .legend{left:10px}
  .pn{position:static;box-shadow:none;margin-top:10px}
  .left{width:auto}
  .left .list{max-height:none}
  .detail{width:auto;transform:none;visibility:visible;display:none}
  .detail.open{display:flex}
  .body{overflow:visible}
  .legend{left:10px!important;bottom:10px}
  .zoom{right:10px!important;bottom:10px}
}
@media (max-width:980px){
  .brand{order:0;margin-right:auto}
  .ib,.menu-wrap,.cta{order:1}
  .sel-wrap{order:4;width:100%}
  .sel-wrap select{width:100%}
  .legend{max-width:calc(100% - 64px)}
}
@media (max-width:560px){
  .cta{padding:0 10px}
  .cta .t{display:none}
  .fg{grid-template-columns:1fr}
  .legend .opt{display:none}
}
@media (prefers-reduced-motion:reduce){
  *,*::before,*::after{animation:none!important;transition:none!important}
}
</style>
</head>
<body>
<div class="app">
  <header class="tb">
    <div class="brand">
      <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="10.5" fill="none" stroke="#E6EDF2" stroke-width="1.5"/><path d="M12 1.5v21M1.5 12h21" stroke="#E6EDF2" stroke-width="1" opacity=".6"/><path d="M12 5l2.2 7L12 19l-2.2-7z" fill="#D27CA0"/></svg>
      EXPORTPULSE
    </div>
    <label class="search">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
      <input id="q" type="search" placeholder="Search importer, HS code, city or port" aria-label="Search importers" autocomplete="off">
    </label>
    <div class="sel-wrap">
      <select id="sector" aria-label="Sector">
        <option value="handicrafts">Handicrafts &amp; brassware</option>
        <option value="agro_marine">Spices, cashews &amp; marine</option>
        <option value="textiles">Home textiles</option>
        <option value="leather">Leather goods</option>
      </select>
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>
    </div>
    <div class="spacer"></div>
    <div class="kpi k1" title="5% buying-agent commission on these importers' annual US imports"><b class="num" id="kComm">–</b><span>agent fees / yr</span></div>
    <div class="kpi k2"><b class="num" id="kDem">–</b><span>US demand / yr</span></div>
    <div class="kpi k3"><b class="num" id="kCtr">–</b><span>containers · 12 mo</span></div>
    <div class="vsep"></div>
    <button class="ib" onclick="openM('mHow')" aria-label="Data source" title="Data source">
      <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="9.5"/><path d="M12 11v5M12 7.6v.4"/></svg>
    </button>
    <button class="ib" onclick="openM('mWho')" aria-label="Edit factory details" title="Edit factory details">
      <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 1 1 3 3L7 19l-4 1 1-4Z"/></svg>
    </button>
    <div class="menu-wrap">
      <button class="ib" id="mgBtn" aria-haspopup="true" aria-expanded="false" aria-label="Manage data" title="Manage data">
        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/></svg>
      </button>
      <div class="menu" id="mgMenu" role="menu">
        <button role="menuitem" onclick="menuGo('mAdd')"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg>Add a US buyer</button>
        <button role="menuitem" onclick="menuGo('mCsv')"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m17 8-5-5-5 5M12 3v12"/></svg>Upload ImportYeti CSV</button>
        <div class="sep"></div>
        <button role="menuitem" onclick="closeMenu();exportCsv()"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5M12 15V3"/></svg>Export this sector as CSV</button>
      </div>
    </div>
    <a class="cta" id="waBtn" href="#" target="_blank" rel="noopener" hidden>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2Zm0 18.2a8.2 8.2 0 0 1-4.2-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2Zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8-.2-.1-.4-.1-.6.1l-.8 1c-.1.2-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.3-.4.2-.4.7-1.3.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5a1 1 0 0 0-.7.3 3 3 0 0 0-.9 2.2 5.2 5.2 0 0 0 1.1 2.7 11.8 11.8 0 0 0 4.5 4c1.7.7 2.3.8 3.2.6.5-.1 1.5-.6 1.7-1.2.2-.6.2-1.1.2-1.2-.1-.1-.3-.2-.5-.3Z"/></svg>
      <span class="t">Get the full list</span>
    </a>
  </header>

  <main class="ws">
    <div class="stage" id="stage">
      <svg id="map" role="img" aria-label="Map of indicative sea lanes from your city to matched US importers">
        <g id="base"></g>
        <g id="overlay"></g>
      </svg>

      <div class="legend" id="legend">
        <span><svg width="20" height="6" aria-hidden="true"><path d="M1 3h18" stroke="#B0235B" stroke-width="2.6" stroke-linecap="round"/></svg>Indicative sea lane</span>
        <span class="opt"><svg width="20" height="6" aria-hidden="true"><path d="M1 3h18" stroke="#44555E" stroke-width="1" stroke-dasharray="1.5 3" stroke-linecap="round"/></svg>Inland</span>
        <span class="opt"><svg width="12" height="12" aria-hidden="true"><circle cx="6" cy="6" r="4.8" fill="#fff" stroke="#B0235B" stroke-width="1.4"/></svg>Size = containers</span>
        <span>US Customs records · last 12 months</span>
      </div>
      <div class="zoom" id="zoom">
        <button onclick="zoomBy(1.5)" aria-label="Zoom in"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg></button>
        <button onclick="zoomBy(1/1.5)" aria-label="Zoom out"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M5 12h14"/></svg></button>
        <button onclick="fitView()" aria-label="Fit to view"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/></svg></button>
      </div>
    </div>

      <aside class="pn left" aria-label="Importers">
        <div class="ph">
          <span class="lbl">Prepared exclusively for</span>
          <h1 class="who" data-bind="factory">__FACTORY_HTML__</h1>
          <div class="who-sub"><span><span data-bind="city">__CITY_HTML__</span>, India</span><span class="mono" id="oCoord"></span></div>
        </div>
        <div class="chips" role="group" aria-label="Filters">
          <button class="fchip on" data-f="all">All<span class="c" id="cAll"></span></button>
          <button class="fchip" data-f="recent">Arrived ≤ 30 days<span class="c" id="cRecent"></span></button>
          <button class="fchip" data-f="top">Match 85+<span class="c" id="cTop"></span></button>
        </div>
        <div class="list-head"><span class="lbl">Matched US importers</span><span class="lbl" style="letter-spacing:.06em">By match</span></div>
        <div class="list" id="tb"></div>
      </aside>

      <aside class="pn detail" id="detail" aria-label="Importer details">
        <div class="dh">
          <div style="min-width:0">
            <h2 id="selName"></h2>
            <p id="selMeta"></p>
          </div>
          <button class="x" onclick="closeDetail()" aria-label="Close details"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M6 6l12 12M18 6 6 18"/></svg></button>
        </div>
        <div class="tabs" role="tablist">
          <button role="tab" data-t="overview" class="on">Overview</button>
          <button role="tab" data-t="offer">Offer</button>
          <button role="tab" data-t="outreach">Outreach</button>
          <button role="tab" data-t="route">Route</button>
        </div>
        <div class="body">
          <section class="tp" data-tp="overview">
            <div class="facts">
              <div class="fact"><div class="k">Containers · 12 mo</div><div class="v num" id="fCtr"></div></div>
              <div class="fact"><div class="k">US imports / yr</div><div class="v num" id="fVol"></div></div>
              <div class="fact"><div class="k">Last recorded arrival</div><div class="v num" id="fLast"></div><div class="s" id="fLastS"></div></div>
              <div class="fact"><div class="k">Match score</div><div class="v num" id="fMatch"></div></div>
            </div>
            <dl class="kv">
              <div><dt>Product</dt><dd id="fProd"></dd></div>
              <div><dt>Contact</dt><dd id="fRole"></dd></div>
              <div><dt>HQ</dt><dd id="fHq"></dd></div>
            </dl>
            <div class="signal" id="fWhy" hidden></div>
            <div class="btns">
              <button class="btn-p" onclick="showTab('offer')">Build offer</button>
              <button class="btn-s" onclick="showTab('outreach')">Draft outreach</button>
            </div>
          </section>

          <section class="tp" data-tp="offer" hidden>
            <span class="lbl">Your FOB quote</span>
            <div class="quote" style="margin-top:6px">
              <div style="flex:1;min-width:0">
                <div class="qv"><span class="cur">$</span><input type="number" id="fobIn" step="0.01" min="0.01" class="num" aria-label="Your FOB quote in USD per unit"></div>
                <div class="q-sub">USD per unit, at Indian port</div>
              </div>
              <button type="button" class="rb" id="fobDn" aria-label="Lower quote by 5 cents">−</button>
              <button type="button" class="rb" id="fobUp" aria-label="Raise quote by 5 cents">+</button>
            </div>
            <div class="rng">
              <input type="range" id="fobRange" step="0.01" aria-label="Adjust your FOB quote">
              <div class="mark" id="fobMark"><span id="fobMarkL"></span></div>
            </div>
            <div class="res">
              <div id="tSave"><div class="k">Buyer saves / yr</div><div class="v num" id="saveAnnual"></div><div class="s" id="saveSub"></div></div>
              <div id="tComm"><div class="k">Commission you keep</div><div class="v num" id="commInr"></div><div class="s" id="commSub"></div></div>
            </div>
            <div class="note">The buyer's saving is on 10,000 units. The commission is the 5% a buying agent would take on this importer's annual US imports.</div>
          </section>

          <section class="tp" data-tp="outreach" hidden>
            <div class="otag"><span class="lbl">Sequence</span><span class="tag" id="engTag">Template · ₹0</span></div>
            <div id="oc"></div>
          </section>

          <section class="tp" data-tp="route" hidden>
            <span class="lbl">Indicative passage</span>
            <ol class="stops" id="legs" style="margin-top:12px"></ol>
            <div class="lc">
              <span class="lbl">Landed cost in the US</span>
              <div>
                <div class="row">Their current supplier <b id="compLanded" class="num"></b></div>
                <div class="cbar comp"><i id="barComp"></i></div>
              </div>
              <div>
                <div class="row">You, buying direct <b id="youLanded" class="num"></b></div>
                <div class="cbar you"><i id="barYou"></i></div>
              </div>
            </div>
            <div class="delta" id="lcDelta"></div>
            <div class="note" id="lcNote"></div>
          </section>
        </div>
      </aside>
  </main>
</div>

<!-- Edit details -->
<div class="mov" id="mWho">
  <div class="mod sm" role="dialog" aria-labelledby="mWhoT">
    <div class="mh">
      <div><h2 id="mWhoT">Prepared for</h2><p>Updates the name on the map, the panels and the outreach.</p></div>
      <button class="x" onclick="closeM('mWho')" aria-label="Close"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M6 6l12 12M18 6 6 18"/></svg></button>
    </div>
    <div class="fg">
      <div class="fi full"><label for="fnIn">Factory name</label><input id="fnIn" autocomplete="off"></div>
      <div class="fi full"><label for="fcIn">City</label><input id="fcIn" autocomplete="off"></div>
    </div>
    <div class="fa"><button class="btn btn-ink" onclick="closeM('mWho')">Done</button></div>
  </div>
</div>

<!-- Data source -->
<div class="mov" id="mHow">
  <div class="mod sm" role="dialog" aria-labelledby="mHowT">
    <div class="mh">
      <div><h2 id="mHowT">Data source</h2><p>Historical US Customs records, not live tracking.</p></div>
      <button class="x" onclick="closeM('mHow')" aria-label="Close"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M6 6l12 12M18 6 6 18"/></svg></button>
    </div>
    <ol class="how">
      <li><div><b>US Customs bills of lading</b><span>Public sea-shipment records for the last 12 months: importer, product, containers, arrival date.</span></div></li>
      <li><div><b>Matched to what you make</b><span>Filtered by your HS codes and product descriptions.</span></div></li>
      <li><div><b>Indicative routes</b><span>Sea lanes show a typical passage via Suez or Panama, not a vessel's actual track.</span></div></li>
    </ol>
    <div class="fa"><button class="btn btn-ink" onclick="closeM('mHow')">Got it</button></div>
  </div>
</div>

<!-- Add Buyer -->
<div class="mov" id="mAdd">
  <div class="mod" role="dialog" aria-labelledby="mAddT">
    <div class="mh">
      <div><h2 id="mAddT">Add a US buyer</h2><p>Copy the details from the importer's ImportYeti page.</p></div>
      <button class="x" onclick="closeM('mAdd')" aria-label="Close"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M6 6l12 12M18 6 6 18"/></svg></button>
    </div>
    <form id="addForm" onsubmit="addBuyer(event)">
      <div class="fg">
        <div class="fi"><label>Sector</label>
          <select name="sector" id="addSec">
            <option value="handicrafts">Handicrafts &amp; brassware</option>
            <option value="agro_marine">Spices, cashews &amp; marine</option>
            <option value="textiles">Home textiles</option>
            <option value="leather">Leather goods</option>
          </select></div>
        <div class="fi"><label>US buyer (company)</label><input name="us_buyer" required placeholder="e.g. Walmart Inc"></div>
        <div class="fi"><label>HQ city</label><input name="hq_city" required placeholder="e.g. Bentonville"></div>
        <div class="fi"><label>HQ state</label><input name="hq_state" placeholder="e.g. AR"></div>
        <div class="fi"><label>HS code</label><input name="hs_code" required placeholder="e.g. 6302.31"></div>
        <div class="fi"><label>Product</label><input name="product_spec" required placeholder="e.g. Cotton bed linen sets"></div>
        <div class="fi"><label>Containers, last 12 months</label><input name="containers_12m" type="number" min="0" required placeholder="e.g. 45"></div>
        <div class="fi"><label>Est. annual imports (USD)</label><input name="est_annual_usd" type="number" min="0" required placeholder="e.g. 5000000"></div>
        <div class="fi"><label>Last arrival date</label><input name="last_arrival_date" type="date" required></div>
        <div class="fi"><label>Decision maker role</label><input name="decision_maker_role" required placeholder="e.g. VP Sourcing"></div>
        <div class="fi"><label>Match score (0–100)</label><input name="match_score" type="number" min="0" max="100" required value="85"></div>
        <div class="fi"><label>Current supplier FOB (USD / unit)</label><input name="competitor_fob_usd" type="number" step="0.01" min="0.01" required placeholder="e.g. 4.80"></div>
        <div class="fi"><label>US duty %</label><input name="us_duty_pct" type="number" step="0.1" min="0" value="0"></div>
        <div class="fi full"><label>Why now (buying signal)</label><textarea name="vulnerability_signal" placeholder="e.g. Moving orders away from China after tariff rise"></textarea></div>
      </div>
      <div class="fa">
        <button type="button" class="btn" onclick="closeM('mAdd')">Cancel</button>
        <button type="submit" class="btn btn-ink">Add buyer</button>
      </div>
    </form>
  </div>
</div>

<!-- CSV Upload -->
<div class="mov" id="mCsv">
  <div class="mod" role="dialog" aria-labelledby="mCsvT">
    <div class="mh">
      <div><h2 id="mCsvT">Upload ImportYeti CSV</h2><p>Add many buyers at once from a spreadsheet.</p></div>
      <button class="x" onclick="closeM('mCsv')" aria-label="Close"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M6 6l12 12M18 6 6 18"/></svg></button>
    </div>
    <p class="csvinfo">
      Required columns: <code>us_buyer, hq_city, hs_code, product_spec, containers_12m, est_annual_usd, last_arrival_date, competitor_fob_usd</code><br>
      Optional: <code>sector, hq_state, us_duty_pct, vulnerability_signal, decision_maker_role, match_score</code><br>
      Tip: <strong>Export this sector as CSV</strong> downloads a file with the right headers to use as a template.
    </p>
    <div class="drop"><input type="file" accept=".csv,text/csv" id="csvIn"></div>
    <div class="fa">
      <button type="button" class="btn" onclick="closeM('mCsv')">Cancel</button>
      <button type="button" class="btn btn-ink" onclick="uploadCsv()">Upload &amp; import</button>
    </div>
  </div>
</div>

<div class="toast" id="toast" role="status"></div>

<script src="https://cdn.jsdelivr.net/npm/d3-array@3.2.4/dist/d3-array.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/d3-geo@3.1.1/dist/d3-geo.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/topojson-client@3.1.0/dist/topojson-client.min.js"></script>
<script>
/* ==================================================================
   State
   ================================================================== */
let S = __CATEGORY_JS__;
let FN = __FACTORY_JS__;
let FC = __CITY_JS__;
const SELLER_WA = __SELLER_JS__;
const DEMO = __DEMO_JS__;
let B = [];
let sel = null;
let OD = null;
let CT = 0;
let TAB = 'overview';
let costSeq = 0, outSeq = 0;
const FILT = {recent: false, top: false, q: ''};

/* ==================================================================
   Helpers
   ================================================================== */
const $ = id => document.getElementById(id);
const RM = matchMedia('(prefers-reduced-motion: reduce)').matches;
const isMobile = () => matchMedia('(max-width:980px)').matches;
const usd = n => (n < 0 ? '-$' : '$') + Math.abs(Number(n)).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});
const usd0 = n => (n < 0 ? '-$' : '$') + Math.abs(Number(n)).toLocaleString('en-US',{maximumFractionDigits:0});
const inr = n => '₹' + Number(n).toLocaleString('en-IN',{maximumFractionDigits:0});
const inrShort = n => n >= 1e7 ? '₹' + (n/1e7).toFixed(2) + ' Cr' : n >= 1e5 ? '₹' + (n/1e5).toFixed(1) + ' L' : inr(n);
const vol = n => n>=1e6 ? '$'+(n/1e6).toFixed(1)+'M' : '$'+(n/1e3).toFixed(0)+'K';
const esc = s => {
  const d = document.createElement('div');
  d.textContent = s == null ? '' : String(s);
  return d.innerHTML;
};
const trunc = (s, n) => s.length > n ? s.slice(0, n - 1) + '…' : s;
const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const parseDate = s => {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(s || '');
  return m ? new Date(+m[1], +m[2] - 1, +m[3]) : null;
};
const fmtDate = s => {
  const d = parseDate(s);
  return d ? String(d.getDate()).padStart(2, '0') + ' ' + MONTHS[d.getMonth()] + ' ' + d.getFullYear() : s;
};
const fmtShort = s => { const d = parseDate(s); return d ? String(d.getDate()).padStart(2, '0') + ' ' + MONTHS[d.getMonth()] : s; };
const TODAY = (() => { const d = new Date(); d.setHours(0,0,0,0); return d; })();
const daysAgo = s => { const d = parseDate(s); return d ? Math.round((TODAY - d) / 864e5) : null; };
const relText = d => d == null ? '' : d <= 0 ? 'today' : d === 1 ? '1 day ago' : d < 45 ? d + ' days ago' : Math.round(d / 30) + ' months ago';
const debounce = (fn, ms) => { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; };
const dms = (lat, lon) => {
  const f = (v, p, n) => { const a = Math.abs(v); let d = Math.floor(a), m = Math.round((a - d) * 60); if (m === 60) { d++; m = 0; } return d + '°' + String(m).padStart(2, '0') + '′' + (v >= 0 ? p : n); };
  return f(lat, 'N', 'S') + ' ' + f(lon, 'E', 'W');
};

/* Count numbers up/down instead of snapping */
const tween = (el, to, fmt, ms=600) => {
  const from = el._v ?? 0;
  el._v = to;
  cancelAnimationFrame(el._raf);
  if (RM || from === to) { el.textContent = fmt(to); return; }
  const t0 = performance.now();
  const step = now => {
    const p = Math.min(1, (now - t0) / ms), e = 1 - Math.pow(1 - p, 3);
    el.textContent = fmt(from + (to - from) * e);
    if (p < 1) el._raf = requestAnimationFrame(step);
  };
  el._raf = requestAnimationFrame(step);
};

const toast = (m, ms=2500) => {
  const t = $('toast');
  t.textContent = m;
  t.classList.add('show');
  clearTimeout(t._h);
  t._h = setTimeout(() => t.classList.remove('show'), ms);
};

/* Modals & menu */
const openM = id => { $(id).classList.add('show'); const f = $(id).querySelector('input,select,textarea'); if (f) setTimeout(() => f.focus(), 50); };
const closeM = id => $(id).classList.remove('show');
const closeMenu = () => { $('mgMenu').classList.remove('show'); $('mgBtn').setAttribute('aria-expanded', 'false'); };
const menuGo = id => { closeMenu(); openM(id); };
$('mgBtn').addEventListener('click', e => {
  e.stopPropagation();
  const open = !$('mgMenu').classList.contains('show');
  $('mgMenu').classList.toggle('show', open);
  $('mgBtn').setAttribute('aria-expanded', String(open));
});
document.addEventListener('click', e => {
  if (e.target.classList.contains('mov')) e.target.classList.remove('show');
  if (!e.target.closest('.menu-wrap')) closeMenu();
});
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') { document.querySelectorAll('.mov.show').forEach(m => m.classList.remove('show')); closeMenu(); }
});

const syncUrl = () => {
  const u = new URL(location.href);
  u.searchParams.set('factory', FN);
  u.searchParams.set('city', FC);
  u.searchParams.set('category', S);
  history.replaceState(null, '', u);
};

/* ==================================================================
   Geography: city coordinates, ports and indicative sea lanes.
   Coordinates are [lat, lon]; d3 wants [lon, lat].
   ================================================================== */
const norm = s => (s || '').toLowerCase().replace(/[^a-z ]/g, '').replace(/\s+/g, ' ').trim();
const IN_CITIES = {
  moradabad:[28.84,78.77], bhubaneswar:[20.30,85.82], panipat:[29.39,76.97], kolkata:[22.57,88.36], calcutta:[22.57,88.36],
  kanpur:[26.45,80.33], kochi:[9.93,76.27], cochin:[9.93,76.27], visakhapatnam:[17.69,83.22], vizag:[17.69,83.22],
  surat:[21.17,72.83], agra:[27.18,78.01], jaipur:[26.91,75.79], tiruppur:[11.11,77.34], chennai:[13.08,80.27],
  mumbai:[19.08,72.88], delhi:[28.61,77.21], 'new delhi':[28.61,77.21], noida:[28.54,77.39], ludhiana:[30.90,75.85],
  karur:[10.96,78.08], jodhpur:[26.24,73.02], saharanpur:[29.96,77.55], ahmedabad:[23.02,72.57], bengaluru:[12.97,77.59],
  bangalore:[12.97,77.59], hyderabad:[17.39,78.49], amritsar:[31.63,74.87], guntur:[16.31,80.44], mangaluru:[12.91,74.86],
  kollam:[8.89,76.61], firozabad:[27.15,78.40], bhadohi:[25.39,82.57], varanasi:[25.32,82.97], mirzapur:[25.15,82.57]
};
const US_CITIES = {
  'fort worth|TX':[32.75,-97.33], 'alameda|CA':[37.77,-122.24], 'gardena|CA':[33.89,-118.31], 'san francisco|CA':[37.77,-122.42],
  'akron|PA':[40.16,-76.20], 'hunt valley|MD':[39.50,-76.64], 'houston|TX':[29.76,-95.37], 'fresno|CA':[36.74,-119.79],
  'brea|CA':[33.92,-117.90], 'vernon|CA':[34.00,-118.23], 'minneapolis|MN':[44.98,-93.27], 'corte madera|CA':[37.93,-122.53],
  'new york|NY':[40.71,-74.01], 'union|NJ':[40.70,-74.26], 'dallas|TX':[32.78,-96.80], 'richardson|TX':[32.95,-96.73],
  'nashville|TN':[36.16,-86.78], 'greenland|NH':[43.04,-70.83], 'norwalk|CT':[41.12,-73.41], 'bentonville|AR':[36.37,-94.21],
  'los angeles|CA':[34.05,-118.24], 'chicago|IL':[41.88,-87.63], 'seattle|WA':[47.61,-122.33], 'atlanta|GA':[33.75,-84.39],
  'miami|FL':[25.76,-80.19], 'boston|MA':[42.36,-71.06]
};
const US_STATES = Object.fromEntries(('AL:32.8,-86.8|AK:61.4,-152.3|AZ:34.2,-111.7|AR:34.9,-92.4|CA:37.2,-119.5|CO:39.0,-105.5|CT:41.6,-72.7|' +
  'DE:39.0,-75.5|FL:28.6,-82.4|GA:32.7,-83.4|HI:20.8,-156.3|ID:44.4,-114.6|IL:40.0,-89.2|IN:39.9,-86.3|IA:42.1,-93.5|KS:38.5,-98.4|' +
  'KY:37.5,-85.3|LA:31.1,-92.0|ME:45.4,-69.2|MD:39.0,-76.8|MA:42.3,-71.8|MI:44.3,-85.4|MN:46.3,-94.3|MS:32.7,-89.7|MO:38.4,-92.5|' +
  'MT:47.0,-109.6|NE:41.5,-99.8|NV:39.3,-116.6|NH:43.7,-71.6|NJ:40.2,-74.7|NM:34.4,-106.1|NY:42.9,-75.5|NC:35.6,-79.4|ND:47.5,-100.5|' +
  'OH:40.3,-82.8|OK:35.6,-97.5|OR:43.9,-120.6|PA:40.9,-77.8|RI:41.7,-71.5|SC:33.9,-80.9|SD:44.4,-100.2|TN:35.9,-86.4|TX:31.5,-99.3|' +
  'UT:39.3,-111.7|VT:44.1,-72.7|VA:37.5,-78.9|WA:47.4,-120.5|WV:38.6,-80.6|WI:44.6,-89.9|WY:43.0,-107.6|DC:38.9,-77.0')
  .split('|').map(p => { const [k, v] = p.split(':'); return [k, v.split(',').map(Number)]; }));
const inLL = city => IN_CITIES[norm(city)] || IN_CITIES[norm(city).split(' ')[0]] || null;
const usLL = b => US_CITIES[norm(b.hq_city) + '|' + (b.hq_state || '').toUpperCase()] || US_STATES[(b.hq_state || '').toUpperCase()] || [39.0, -98.0];

const IN_PORTS = {
  nhava:  {n:'Nhava Sheva',  ll:[18.95,72.95], sea:[[12.3,52.0]]},
  kochi:  {n:'Kochi',        ll:[9.97,76.24],  sea:[[11.5,60.0],[12.3,52.0]]},
  vizag:  {n:'Visakhapatnam',ll:[17.69,83.29], sea:[[10.0,82.6],[5.6,80.6],[7.5,76.5],[11.5,60.0],[12.3,52.0]]},
  haldia: {n:'Haldia',       ll:[22.03,88.06], sea:[[20.2,88.2],[14.0,85.5],[8.5,82.6],[5.6,80.6],[7.5,76.5],[11.5,60.0],[12.3,52.0]]}
};
const inPort = ([lat, lon]) => lon >= 80.5 ? (lat > 21 ? IN_PORTS.haldia : IN_PORTS.vizag) : (lat < 13 ? IN_PORTS.kochi : IN_PORTS.nhava);
const SUEZ = [[12.6,43.4],[20.0,38.6],[27.6,33.9],[29.95,32.56],[31.4,32.35],[33.8,26.0],[37.2,11.5],[37.3,1.0],[35.95,-5.6]];
const US_PORTS = {
  nyc: {n:'New York / NJ',   ll:[40.60,-74.00], sea:[[38.5,-40],[40.3,-70.5]]},
  sav: {n:'Savannah',        ll:[32.03,-80.85], sea:[[34,-40],[31.9,-79.5]]},
  hou: {n:'Houston',         ll:[29.40,-94.70], sea:[[29,-40],[26.2,-76.8],[25.9,-79.0],[24.3,-81.5],[25.5,-87],[28.6,-93.5]]},
  lax: {n:'Los Angeles',     ll:[33.72,-118.26], sea:[[22,-40],[18.4,-65.5],[12.5,-76.0],[9.38,-79.92],[8.93,-79.56],[7.2,-80.5],[14.5,-98],[22.5,-110.8],[30.0,-117.5]]}
};
const US_WEST = 'CA OR WA NV AZ UT ID HI AK CO NM MT WY'.split(' ');
const US_GULF = 'TX LA OK AR KS MS'.split(' ');
const US_SE = 'GA FL SC NC AL TN'.split(' ');
const usPortKey = st => { st = (st || '').toUpperCase(); return US_WEST.includes(st) ? 'lax' : US_GULF.includes(st) ? 'hou' : US_SE.includes(st) ? 'sav' : 'nyc'; };
const flip = ([lat, lon]) => [lon, lat];
const originLL = () => inLL(FC) || [22.5, 79.0];

/* ==================================================================
   API
   ================================================================== */
const api = async (url, o) => {
  const r = await fetch(url, o);
  if (!r.ok) {
    let msg = 'HTTP ' + r.status;
    try { const j = await r.json(); if (j.detail) msg = typeof j.detail === 'string' ? j.detail : j.detail.map(d => d.loc.slice(-1)[0] + ': ' + d.msg).join('; '); } catch (_) {}
    throw new Error(msg);
  }
  return r.json();
};

/* ==================================================================
   Load buyers
   ================================================================== */
const load = async (sector, pickId) => {
  S = sector;
  sel = null;
  $('sector').value = S;
  $('addSec').value = S;
  syncUrl();
  try {
    B = await api('/api/buyers?category=' + encodeURIComponent(S));
  } catch (err) { toast('Could not load buyers: ' + err.message, 4000); return; }
  B.sort((a,b) => b.match_score - a.match_score);
  B.forEach((b, i) => { b._rank = i + 1; });
  renderKpis();
  renderList();
  await renderMap();
  const first = pickId || (visible()[0] && visible()[0].id);
  if (first && !isMobile()) pick(first, {instant: true});
  else if (pickId) pick(pickId, {instant: true});
  else { closeDetail(true); }
};

/* ==================================================================
   Toolbar KPIs
   ================================================================== */
const renderKpis = () => {
  const c = B.reduce((a, b) => a + b.containers_12m, 0);
  const v = B.reduce((a, b) => a + b.est_annual_usd, 0);
  tween($('kComm'), v * 0.05 * 95, inrShort, 800);
  tween($('kDem'), v, vol, 800);
  tween($('kCtr'), c, x => Math.round(x).toLocaleString('en-US'), 800);
  const o = inLL(FC);
  $('oCoord').textContent = o ? dms(o[0], o[1]) : '';
};

/* ==================================================================
   Filters + importer list
   ================================================================== */
const matchesQ = (b, q) => {
  if (!q) return true;
  const port = US_PORTS[usPortKey(b.hq_state)].n;
  return [b.us_buyer, b.hq_city, b.hq_state, b.hs_code, b.product_spec, b.decision_maker_role, port]
    .some(f => (f || '').toLowerCase().includes(q));
};
const isRecent = b => { const d = daysAgo(b.last_arrival_date); return d != null && d <= 30; };
const visible = () => B.filter(b =>
  (!FILT.recent || isRecent(b)) && (!FILT.top || b.match_score >= 85) && matchesQ(b, FILT.q));

const scoreCls = s => s >= 85 ? 'hi' : s >= 70 ? 'md' : 'lo';
const renderList = () => {
  const qOnly = B.filter(b => matchesQ(b, FILT.q));
  $('cAll').textContent = qOnly.length;
  $('cRecent').textContent = qOnly.filter(isRecent).length;
  $('cTop').textContent = qOnly.filter(b => b.match_score >= 85).length;
  document.querySelectorAll('.fchip').forEach(c => {
    const f = c.dataset.f;
    c.classList.toggle('on', f === 'all' ? (!FILT.recent && !FILT.top) : FILT[f]);
  });
  const V = visible();
  if (!B.length) {
    $('tb').innerHTML = '<div class="empty">No importers in this sector yet. Add them from Manage data.</div>';
    return;
  }
  if (!V.length) {
    $('tb').innerHTML = '<div class="empty">No importers match these filters.</div>';
    return;
  }
  $('tb').innerHTML = V.map(b => `
    <button class="imp${sel && sel.id === b.id ? ' on' : ''}" data-id="${esc(b.id)}">
      <span class="badge">${b._rank}</span>
      <span style="min-width:0"><b>${esc(b.us_buyer)}</b><small>${esc(b.hq_city)}${b.hq_state ? ', ' + esc(b.hq_state) : ''} · last arrival ${esc(fmtShort(b.last_arrival_date))}</small></span>
      <span class="imp-side"><span class="score ${scoreCls(b.match_score)}">${b.match_score}</span><small>${b.containers_12m} ctr</small></span>
    </button>`).join('');
};

const applyFilters = () => {
  renderList();
  renderMap().then(() => {
    if (sel && !visible().some(b => b.id === sel.id)) closeDetail();
    else fitView(true);
  });
};
document.querySelectorAll('.fchip').forEach(c => c.addEventListener('click', () => {
  const f = c.dataset.f;
  if (f === 'all') { FILT.recent = false; FILT.top = false; } else FILT[f] = !FILT[f];
  applyFilters();
}));
$('q').addEventListener('input', debounce(e => { FILT.q = e.target.value.trim().toLowerCase(); applyFilters(); }, 160));
$('tb').addEventListener('click', e => { const r = e.target.closest('.imp'); if (r) pick(r.dataset.id); });
$('tb').addEventListener('mouseover', e => { const r = e.target.closest('.imp'); if (r) hover(r.dataset.id); });
$('tb').addEventListener('mouseleave', () => hover(null));

/* ==================================================================
   Map: d3-geo Mercator + our own camera (scale/translate, no extra library)
   ================================================================== */
const WORLD_URL = 'https://cdn.jsdelivr.net/npm/world-atlas@2.0.2/countries-110m.json';
const MAP = {world: null, proj: null, path: null, routes: {}, W: 0, H: 0, ok: false, overlay: []};
const CAM = {k: 1, x: 0, y: 0, raf: 0};
const K_MIN = 0.3;
const MAP_MAX = 30;
const WATERS = [
  ['NORTH ATLANTIC OCEAN', [33,-46]], ['INDIAN OCEAN', [-2,76]], ['NORTH PACIFIC OCEAN', [22,-132]],
  ['ARABIAN SEA', [15.5,63.5]], ['GULF OF MEXICO', [24.6,-91]], ['MEDITERRANEAN SEA', [34.4,19.5]], ['BAY OF BENGAL', [14,88.5]]
];

const loadWorld = async () => {
  if (MAP.world) return MAP.world;
  const r = await fetch(WORLD_URL);
  if (!r.ok) throw new Error('map ' + r.status);
  const topo = await r.json();
  MAP.world = topojson.feature(topo, topo.objects.countries).features;
  return MAP.world;
};

const routeFor = b => {
  const o = originLL(), ip = inPort(o), key = usPortKey(b.hq_state), up = US_PORTS[key];
  return {key, ip, up, hq: usLL(b), o, sea: [ip.ll, ...ip.sea, ...SUEZ, ...up.sea, up.ll]};
};
const line = pts => ({type: 'LineString', coordinates: pts.map(flip)});
const NS = 'http://www.w3.org/2000/svg';

const mapFallback = msg => {
  MAP.ok = false;
  const st = $('stage');
  $('base').innerHTML = '';
  $('overlay').innerHTML = `<text class="m-off" x="${st.clientWidth / 2}" y="${st.clientHeight / 2}" text-anchor="middle">${esc(msg)}</text>`;
  $('base').removeAttribute('transform');
};

const renderMap = async () => {
  const st = $('stage');
  const W = st.clientWidth, H = st.clientHeight;
  if (!W || !H) return;
  if (!window.d3 || !d3.geoMercator || !window.topojson) return mapFallback('The map needs an internet connection. The importer list still works.');
  let feats;
  try { feats = await loadWorld(); } catch (_) { return mapFallback('The map could not load. The importer list still works.'); }
  MAP.W = W; MAP.H = H; MAP.ok = true;

  /* base projection covers the whole India–US trade band at camera scale 1 */
  const proj = d3.geoMercator().rotate([20, 0]);
  proj.fitExtent([[0, 0], [W, H]], {type: 'MultiPoint', coordinates: [[-140, 58], [100, 58], [-140, -12], [100, -12]]});
  const path = d3.geoPath(proj);
  MAP.proj = proj; MAP.path = path;
  const P = ll => proj(flip(ll));

  const V = visible().slice(0, MAP_MAX);
  const o = originLL(), ip = inPort(o);
  const routes = {};
  B.forEach(b => { routes[b.id] = routeFor(b); });
  MAP.routes = routes;
  const lanes = {};
  V.forEach(b => { const r = routes[b.id]; lanes[r.key] = r; });

  const landPaths = feats.map(f => { const d = path(f); return d ? `<path d="${d}"${f.id === '356' || f.id === '840' ? ' class="home"' : ''}/>` : ''; }).join('');
  const shoal = feats.map(f => { const d = path(f); return d ? `<path d="${d}"/>` : ''; }).join('');
  const grat = `<path class="m-grat" d="${path(d3.geoGraticule().step([10, 10])())}"/>`;
  const laneSvg = Object.values(lanes).map(r => `<path class="lane" d="${path(line(r.sea))}"/>`).join('');
  let legs = V.length ? `<path class="leg" d="${path(line([o, ip.ll]))}"/>` : '';
  V.forEach(b => { const r = routes[b.id]; legs += `<path class="leg" d="${path(line([r.up.ll, r.hq]))}"/>`; });
  $('base').innerHTML = `
    <rect x="${-W * 4}" y="${-H * 4}" width="${W * 9}" height="${H * 9}" fill="#E2ECEC"/>
    <g class="m-shoal">${shoal}</g><g class="m-land">${landPaths}</g>${grat}
    <g class="fade-in">${laneSvg}${legs}</g>
    <path class="lane-on" id="laneOn" d=""/><path class="leg-on" id="legOn" d=""/>`;

  /* overlay items live in screen space so text and markers stay crisp at any zoom */
  const items = [];
  WATERS.forEach(([t, ll]) => items.push({kind: 'water', p: P(ll), t}));
  items.push({kind: 'port', p: P(ip.ll), t: ip.n.toUpperCase(), dx: -7, dy: 3, anchor: 'end'});
  Object.values(lanes).forEach(r => items.push({kind: 'port', us: r.key, p: P(r.up.ll), t: r.up.n.toUpperCase(),
    dx: r.key === 'lax' ? 4 : 8, dy: r.key === 'lax' ? 20 : 3, anchor: 'start'}));
  items.push({kind: 'origin', p: P(o)});
  const maxC = Math.max(...V.map(b => b.containers_12m), 1);
  V.forEach(b => items.push({kind: 'mk', b, p: P(routes[b.id].hq), r: 8 + 9 * Math.sqrt(b.containers_12m / maxC)}));
  MAP.overlay = items;
  buildOverlay();
  applyCam();
  highlightRoute();
};

const buildOverlay = () => {
  const ov = $('overlay');
  ov.innerHTML = '';
  MAP.overlay.forEach(it => {
    const g = document.createElementNS(NS, 'g');
    it.el = g;
    if (it.kind === 'water') {
      g.innerHTML = `<text class="m-water">${it.t}</text>`;
    } else if (it.kind === 'port') {
      g.setAttribute('class', 'port');
      g.innerHTML = `<rect x="-3" y="-3" width="6" height="6"/><text class="halo" x="${it.dx}" y="${it.dy}" text-anchor="${it.anchor}">${esc(it.t)}</text>`;
    } else if (it.kind === 'origin') {
      g.innerHTML = `<circle class="org-dot" r="5"/><text class="org-name halo" y="-12" text-anchor="middle">${esc(trunc(FN, 30))}</text><text class="org-sub halo" y="20" text-anchor="middle">${esc(trunc(FC.toUpperCase(), 18))}</text>`;
    } else {
      it.lead = document.createElementNS(NS, 'line');
      it.lead.setAttribute('class', 'mk-lead');
      ov.appendChild(it.lead);
      g.setAttribute('class', 'mk' + (sel && sel.id === it.b.id ? ' on' : ''));
      g.dataset.id = it.b.id;
      g.setAttribute('tabindex', '0');
      g.setAttribute('role', 'button');
      g.setAttribute('aria-label', `${it.b._rank}. ${it.b.us_buyer}, ${it.b.containers_12m} containers`);
      g.innerHTML = `<title>${esc(it.b.us_buyer)} · ${esc(it.b.hq_city)} · ${it.b.containers_12m} containers</title><circle class="mk-c" r="${it.r.toFixed(1)}"/><text class="mk-n">${it.b._rank}</text>`;
    }
    ov.appendChild(g);
  });
};

/* place overlay items for the current camera; nudge clustered markers apart */
const placeOverlay = () => {
  const {k, x, y} = CAM;
  const mks = [];
  const selPort = sel && MAP.routes[sel.id] ? MAP.routes[sel.id].key : null;
  MAP.overlay.forEach(it => {
    it.sx = it.p[0] * k + x; it.sy = it.p[1] * k + y;
    if (it.kind === 'mk') { it.nx = it.sx; it.ny = it.sy; mks.push(it); }
    else it.el.setAttribute('transform', `translate(${it.sx.toFixed(1)},${it.sy.toFixed(1)})`);
    /* zoomed out, US port names crowd the markers: keep only the selected route's port */
    if (it.us) it.el.querySelector('text').style.display = k >= 0.75 || it.us === selPort ? '' : 'none';
    /* keep the factory's labels inside the map when its city sits near the right edge */
    if (it.kind === 'origin') {
      const near = it.sx > MAP.W - 120;
      it.el.querySelectorAll('text').forEach(t => { t.setAttribute('text-anchor', near ? 'end' : 'middle'); t.setAttribute('x', near ? 10 : 0); });
    }
  });
  for (let n = 0; n < 40; n++) for (let a = 0; a < mks.length; a++) for (let c = a + 1; c < mks.length; c++) {
    const p = mks[a], q = mks[c];
    const dx = q.nx - p.nx, dy = q.ny - p.ny, d = Math.hypot(dx, dy) || 0.01, min = p.r + q.r + 3;
    if (d < min) { const s = (min - d) / 2 / d; p.nx -= dx * s; p.ny -= dy * s; q.nx += dx * s; q.ny += dy * s; }
  }
  mks.forEach(it => {
    it.el.setAttribute('transform', `translate(${it.nx.toFixed(1)},${it.ny.toFixed(1)})`);
    const moved = Math.hypot(it.nx - it.sx, it.ny - it.sy) > 3;
    it.lead.setAttribute('x1', it.sx); it.lead.setAttribute('y1', it.sy);
    it.lead.setAttribute('x2', it.nx); it.lead.setAttribute('y2', it.ny);
    it.lead.style.display = moved ? '' : 'none';
  });
};

const applyCam = () => {
  if (!MAP.ok) return;
  $('base').setAttribute('transform', `translate(${CAM.x},${CAM.y}) scale(${CAM.k})`);
  placeOverlay();
};

const animateCam = (to, instant) => {
  cancelAnimationFrame(CAM.raf);
  if (instant || RM) { CAM.k = to.k; CAM.x = to.x; CAM.y = to.y; applyCam(); return; }
  const from = {k: CAM.k, x: CAM.x, y: CAM.y}, t0 = performance.now(), ms = 650;
  const step = now => {
    const p = Math.min(1, (now - t0) / ms), e = p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2;
    CAM.k = from.k + (to.k - from.k) * e;
    CAM.x = from.x + (to.x - from.x) * e;
    CAM.y = from.y + (to.y - from.y) * e;
    applyCam();
    if (p < 1) CAM.raf = requestAnimationFrame(step);
  };
  CAM.raf = requestAnimationFrame(step);
};

/* the part of the stage not covered by floating panels */
const viewArea = () => {
  const W = MAP.W, H = MAP.H;
  if (isMobile()) return [16, 16, W - 16, H - 52];
  const left = document.querySelector('.left').offsetWidth + 36;
  const right = $('detail').classList.contains('open') ? W - $('detail').offsetWidth - 36 : W - 60;
  return [left, 24, right, H - 60];
};

const fitPoints = (pts, instant) => {
  if (!MAP.ok || !pts.length) return;
  const xs = pts.map(p => p[0]), ys = pts.map(p => p[1]);
  const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
  const [ax0, ay0, ax1, ay1] = viewArea();
  const pad = 28;
  const k = Math.max(K_MIN, Math.min(7, Math.min((ax1 - ax0 - pad * 2) / Math.max(1, x1 - x0), (ay1 - ay0 - pad * 2) / Math.max(1, y1 - y0))));
  const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
  animateCam({k, x: (ax0 + ax1) / 2 - cx * k, y: (ay0 + ay1) / 2 - cy * k}, instant);
};

/* legend and zoom controls slide aside so floating panels never cover them */
const updateChrome = () => {
  const lg = $('legend'), zm = $('zoom');
  if (isMobile()) { lg.style.left = ''; zm.style.right = ''; return; }
  lg.style.left = (document.querySelector('.left').offsetWidth + 24) + 'px';
  zm.style.right = ($('detail').classList.contains('open') ? $('detail').offsetWidth + 24 : 12) + 'px';
};

const routePoints = r => [r.o, ...r.sea, r.hq].map(ll => MAP.proj(flip(ll)));
const fitView = instant => {
  if (!MAP.ok) return;
  if (sel && MAP.routes[sel.id]) return fitPoints(routePoints(MAP.routes[sel.id]), instant);
  const V = visible();
  const pts = V.length ? V.flatMap(b => routePoints(MAP.routes[b.id])) : routePoints(routeFor({hq_state: 'NY', hq_city: 'New York'}));
  fitPoints(pts, instant);
};

const zoomBy = f => {
  if (!MAP.ok) return;
  const [ax0, ay0, ax1, ay1] = viewArea();
  const cx = (ax0 + ax1) / 2, cy = (ay0 + ay1) / 2;
  const k = Math.max(K_MIN, Math.min(12, CAM.k * f));
  animateCam({k, x: cx - (cx - CAM.x) * (k / CAM.k), y: cy - (cy - CAM.y) * (k / CAM.k)});
};

/* drag to pan, wheel to zoom */
(() => {
  const svg = $('map');
  let drag = null;
  svg.addEventListener('pointerdown', e => {
    if (e.target.closest('.mk') || !MAP.ok) return;
    drag = {x: e.clientX, y: e.clientY, cx: CAM.x, cy: CAM.y, moved: false};
    svg.setPointerCapture(e.pointerId);
  });
  svg.addEventListener('pointermove', e => {
    if (!drag) return;
    const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
    if (Math.abs(dx) + Math.abs(dy) > 3) { drag.moved = true; svg.classList.add('dragging'); }
    cancelAnimationFrame(CAM.raf);
    CAM.x = drag.cx + dx; CAM.y = drag.cy + dy;
    applyCam();
  });
  const end = () => { drag = null; svg.classList.remove('dragging'); };
  svg.addEventListener('pointerup', end);
  svg.addEventListener('pointercancel', end);
  svg.addEventListener('wheel', e => {
    if (!MAP.ok) return;
    e.preventDefault();
    const r = svg.getBoundingClientRect(), mx = e.clientX - r.left, my = e.clientY - r.top;
    const k = Math.max(K_MIN, Math.min(12, CAM.k * Math.exp(-e.deltaY * 0.0015)));
    cancelAnimationFrame(CAM.raf);
    CAM.x = mx - (mx - CAM.x) * (k / CAM.k); CAM.y = my - (my - CAM.y) * (k / CAM.k); CAM.k = k;
    applyCam();
  }, {passive: false});
})();

/* selected route, or a lighter preview while hovering another importer */
const drawRoute = (id, preview) => {
  const on = $('laneOn'), lg = $('legOn');
  if (!on || !MAP.path) return;
  const r = id && MAP.routes[id];
  on.setAttribute('d', r ? MAP.path(line(r.sea)) : '');
  lg.setAttribute('d', r ? MAP.path(line([r.o, r.ip.ll])) + MAP.path(line([r.up.ll, r.hq])) : '');
  on.classList.toggle('preview', !!preview);
};
const highlightRoute = () => {
  drawRoute(sel && sel.id, false);
  document.querySelectorAll('#overlay .mk').forEach(g => g.classList.toggle('on', !!sel && g.dataset.id === sel.id));
  if (MAP.ok) placeOverlay();
};
const hover = id => {
  document.querySelectorAll('#overlay .mk').forEach(g => g.classList.toggle('hov', g.dataset.id === id));
  document.querySelectorAll('#tb .imp').forEach(r => r.classList.toggle('hov', r.dataset.id === id));
  if (id && (!sel || id !== sel.id)) drawRoute(id, true); else drawRoute(sel && sel.id, false);
};

$('overlay').addEventListener('click', e => { const g = e.target.closest('.mk'); if (g) pick(g.dataset.id); });
$('overlay').addEventListener('keydown', e => {
  const g = e.target.closest('.mk');
  if (g && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); pick(g.dataset.id); }
});
$('overlay').addEventListener('mouseover', e => { const g = e.target.closest('.mk'); if (g) hover(g.dataset.id); });
$('overlay').addEventListener('mouseout', e => { const g = e.target.closest('.mk'); if (g && !g.contains(e.relatedTarget)) hover(null); });

let lastSize = '';
new ResizeObserver(debounce(() => {
  const st = $('stage'), size = st.clientWidth + 'x' + st.clientHeight;
  updateChrome();
  if (size !== lastSize) { lastSize = size; renderMap().then(() => fitView(true)); }
}, 160)).observe($('stage'));

/* ==================================================================
   Detail panel
   ================================================================== */
const showTab = t => {
  TAB = t;
  document.querySelectorAll('.tabs button').forEach(b => { const on = b.dataset.t === t; b.classList.toggle('on', on); b.setAttribute('aria-selected', String(on)); });
  document.querySelectorAll('.tp').forEach(p => { p.hidden = p.dataset.tp !== t; });
};
document.querySelectorAll('.tabs button').forEach(b => b.addEventListener('click', () => showTab(b.dataset.t)));

const closeDetail = instant => {
  sel = null;
  $('detail').classList.remove('open');
  updateChrome();
  document.querySelectorAll('#tb .imp').forEach(r => r.classList.remove('on'));
  highlightRoute();
  fitView(instant === true);
};

const renderOverview = () => {
  const d = daysAgo(sel.last_arrival_date);
  $('selName').textContent = sel.us_buyer;
  $('selMeta').textContent = `#${sel._rank} · ${sel.hq_city}${sel.hq_state ? ', ' + sel.hq_state : ''} · HS ${sel.hs_code}`;
  $('fCtr').textContent = sel.containers_12m;
  $('fVol').textContent = vol(sel.est_annual_usd);
  $('fLast').textContent = fmtShort(sel.last_arrival_date);
  $('fLastS').textContent = (parseDate(sel.last_arrival_date) ? parseDate(sel.last_arrival_date).getFullYear() + ' · ' : '') + relText(d);
  $('fMatch').textContent = sel.match_score + ' / 100';
  $('fProd').innerHTML = `<span class="hs">HS ${esc(sel.hs_code)}</span>${esc(sel.product_spec)}`;
  $('fRole').textContent = sel.decision_maker_role;
  const hq = usLL(sel);
  $('fHq').innerHTML = `${esc(sel.hq_city)}${sel.hq_state ? ', ' + esc(sel.hq_state) : ''} <span class="mono" style="font-size:11px;color:var(--muted)">${dms(hq[0], hq[1])}</span>`;
  const why = $('fWhy');
  why.hidden = !sel.vulnerability_signal;
  why.innerHTML = sel.vulnerability_signal
    ? `<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M13 2 4 14h7l-1 8 9-12h-7z"/></svg><span>${esc(sel.vulnerability_signal)}</span>` : '';
};

const renderLegs = () => {
  if (!sel) return;
  const o = originLL(), ip = inPort(o), up = US_PORTS[usPortKey(sel.hq_state)], hq = usLL(sel);
  const vias = up === US_PORTS.lax ? ['Suez Canal', 'Panama Canal'] : ['Suez Canal'];
  $('legs').innerHTML = `
    <li><b>${esc(FC)}, India</b><span>${inLL(FC) ? dms(o[0], o[1]) : 'factory'}</span></li>
    <li><b>${esc(ip.n)}</b><span>export port</span></li>
    ${vias.map(v => `<li class="via">via ${v}</li>`).join('')}
    <li><b>${esc(up.n)}</b><span>US port of entry</span></li>
    <li class="end"><b>${esc(sel.hq_city)}${sel.hq_state ? ', ' + esc(sel.hq_state) : ''}</b><span>${dms(hq[0], hq[1])}</span></li>`;
};

const pick = (id, opts = {}) => {
  sel = B.find(b => b.id === id);
  if (!sel) return;
  document.querySelectorAll('#tb .imp').forEach(r => r.classList.toggle('on', r.dataset.id === id));
  $('detail').classList.add('open');
  updateChrome();
  renderOverview();
  renderLegs();
  showTab(TAB);
  const comp = sel.competitor_fob_usd;
  const rng = $('fobRange');
  rng.min = (comp * 0.6).toFixed(2);
  rng.max = (comp * 1.1).toFixed(2);
  $('fobMark').style.setProperty('--m', ((comp - comp * 0.6) / (comp * 0.5) * 100).toFixed(2));
  $('fobMarkL').textContent = 'Their ' + usd(comp);
  setFob(comp * 0.90);
  OD = null;
  CT = 0;
  $('oc').innerHTML = '<div class="wait">Writing the sequence…</div>';
  highlightRoute();
  fitView(opts.instant);
  refreshCost();
  refreshOut();
  if (isMobile() && !opts.instant) setTimeout(() => $('detail').scrollIntoView({behavior: RM ? 'auto' : 'smooth', block: 'start'}), 60);
};

const syncRange = v => {
  const rng = $('fobRange');
  rng.value = v;
  const pct = (Math.min(Math.max(v, +rng.min), +rng.max) - rng.min) / (rng.max - rng.min) * 100;
  rng.style.setProperty('--pct', pct.toFixed(2));
};
const setFob = v => {
  const val = Math.max(0.01, v).toFixed(2);
  $('fobIn').value = val;
  syncRange(+val);
};
const curFob = () => {
  const v = parseFloat($('fobIn').value);
  return v > 0 ? v : null;
};

const refreshCost = async () => {
  const fob = curFob();
  if (!sel || fob === null) return;
  const my = ++costSeq;
  try {
    const c = await api('/api/cost-calc/' + encodeURIComponent(sel.id) + '?your_fob_usd=' + fob);
    if (my === costSeq) renderCost(c);
  } catch (err) { toast('Calculator error: ' + err.message, 4000); }
};

const refreshOut = async () => {
  const fob = curFob();
  if (!sel || fob === null) return;
  const my = ++outSeq;
  try {
    const out = await api('/api/outreach', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({buyer_id:sel.id, factory_name:FN, factory_city:FC, your_fob_usd:fob})
    });
    if (my !== outSeq) return;
    OD = out;
    renderOut();
  } catch (err) { toast('Outreach error: ' + err.message, 4000); }
};
const refreshOutSoon = debounce(refreshOut, 250);
const onFobChange = () => { refreshCost(); refreshOutSoon(); };

const renderCost = c => {
  const mx = Math.max(c.competitor_landed_usd, c.your_landed_usd) || 1;
  tween($('compLanded'), c.competitor_landed_usd, usd, 400);
  tween($('youLanded'), c.your_landed_usd, usd, 400);
  $('barComp').style.width = (c.competitor_landed_usd / mx * 100) + '%';
  $('barYou').style.width = (c.your_landed_usd / mx * 100) + '%';
  const neg = c.annual_savings_10k_usd < 0;
  $('lcDelta').classList.toggle('neg', neg);
  $('lcDelta').textContent = neg
    ? `${Math.abs(c.landed_savings_pct)}% above their landed cost`
    : `${c.landed_savings_pct}% lower landed cost · ${usd(c.savings_per_unit_usd)} per unit`;
  $('lcNote').textContent = `Includes ${c.us_duty_pct}% US duty and 8% freight & insurance.`;
  tween($('saveAnnual'), c.annual_savings_10k_usd, usd0);
  $('saveSub').textContent = neg ? 'your quote is higher' : `${c.landed_savings_pct}% lower landed`;
  tween($('commInr'), c.agent_commission_saved_inr, inrShort);
  $('commSub').textContent = 'per year';
  $('tSave').classList.toggle('neg', neg);
};

$('fobDn').addEventListener('click', () => { setFob((curFob() || 0) - 0.05); onFobChange(); });
$('fobUp').addEventListener('click', () => { setFob((curFob() || 0) + 0.05); onFobChange(); });
$('fobIn').addEventListener('input', () => { const v = curFob(); if (v) syncRange(v); onFobChange(); });
$('fobRange').addEventListener('input', e => { setFob(+e.target.value); onFobChange(); });

/* ==================================================================
   Factory / City (pre-filled from ?factory= & ?city=)
   ================================================================== */
const waHref = () => {
  const text = encodeURIComponent(`Hi, I'd like the full ExportPulse US buyer list for ${FN} (${FC}).`);
  return 'https://wa.me/' + SELLER_WA + '?text=' + text;
};
const renderMapSoon = debounce(() => renderMap().then(() => fitView(true)), 300);
const onIdentity = () => {
  FN = $('fnIn').value.trim() || 'Your Export Company';
  FC = $('fcIn').value.trim() || 'India';
  document.querySelectorAll('[data-bind="factory"]').forEach(el => el.textContent = FN);
  document.querySelectorAll('[data-bind="city"]').forEach(el => el.textContent = FC);
  const o = inLL(FC);
  $('oCoord').textContent = o ? dms(o[0], o[1]) : '';
  $('waBtn').href = waHref();
  document.title = 'ExportPulse AI — ' + FN;
  syncUrl();
  renderLegs();
  renderMapSoon();
  refreshOutSoon();
};
$('fnIn').addEventListener('input', onIdentity);
$('fcIn').addEventListener('input', onIdentity);

/* ==================================================================
   Outreach
   ================================================================== */
const OTABS = [
  {d:'D1', l:'Cold email', s:'cold_email_subject', b:'cold_email_body'},
  {d:'D3', l:'Samples', s:'followup_subject', b:'followup_body'},
  {d:'', l:'WhatsApp', s:null, b:'linkedin_whatsapp'}
];

const renderOut = () => {
  if (!OD) return;
  const gem = OD.engine === 'gemini';
  $('engTag').textContent = gem ? 'Gemini' : 'Template · ₹0';
  $('engTag').classList.toggle('ai', gem);
  const a = OTABS[CT];
  const subj = a.s ? `<div class="subj">${esc(OD[a.s])}</div>` : '';
  $('oc').innerHTML = `
    <div class="otabs" role="tablist">${OTABS.map((t,i)=>
      `<button class="${i===CT?'on':''}" role="tab" aria-selected="${i===CT}" onclick="swTab(${i})">${t.d ? `<span class="d">${t.d}</span>` : ''}${t.l}</button>`
    ).join('')}</div>
    <div class="msg">${subj}<div class="mbody">${esc(OD[a.b])}</div></div>
    <button class="copy" id="cpBtn" onclick="copyMsg()">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
      <span>Copy message</span>
    </button>`;
};

const swTab = i => { CT = i; renderOut(); };

/* ==================================================================
   Copy to Clipboard (with fallback for plain-http hosts)
   ================================================================== */
const copyText = async t => {
  try { await navigator.clipboard.writeText(t); return true; }
  catch (_) {
    const ta = document.createElement('textarea');
    ta.value = t; ta.style.position = 'fixed'; ta.style.opacity = '0';
    document.body.appendChild(ta); ta.select();
    const ok = document.execCommand('copy');
    ta.remove();
    return ok;
  }
};

const copyMsg = async () => {
  if (!OD) return;
  const a = OTABS[CT];
  const text = a.s ? 'Subject: ' + OD[a.s] + '\n\n' + OD[a.b] : OD[a.b];
  const ok = await copyText(text);
  const b = $('cpBtn');
  if (!ok) {
    const range = document.createRange();
    range.selectNodeContents(document.querySelector('.msg .mbody'));
    const s = getSelection(); s.removeAllRanges(); s.addRange(range);
    toast('Clipboard blocked — message selected, press Ctrl+C');
    return;
  }
  b.querySelector('span').textContent = 'Copied';
  b.classList.add('ok');
  toast('Message copied');
  setTimeout(() => { if (b.isConnected) { b.querySelector('span').textContent = 'Copy message'; b.classList.remove('ok'); } }, 1800);
};

/* ==================================================================
   Export / Add Buyer / CSV Upload
   ================================================================== */
const exportCsv = () => { location.href = '/api/export-csv?category=' + encodeURIComponent(S); };

const addBuyer = async e => {
  e.preventDefault();
  const fd = Object.fromEntries(new FormData(e.target).entries());
  fd.containers_12m = parseInt(fd.containers_12m, 10);
  fd.est_annual_usd = parseFloat(fd.est_annual_usd);
  fd.match_score = parseInt(fd.match_score, 10);
  fd.competitor_fob_usd = parseFloat(fd.competitor_fob_usd);
  fd.us_duty_pct = parseFloat(fd.us_duty_pct || '0');
  try {
    const nb = await api('/api/buyers/add', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify(fd)
    });
    closeM('mAdd');
    e.target.reset();
    setDefaultDate();
    toast('Added ' + nb.us_buyer);
    load(nb.sector, nb.id);
  } catch (err) { toast('Could not add buyer: ' + err.message, 5000); }
};

const uploadCsv = async () => {
  const inp = $('csvIn');
  if (!inp.files.length) { toast('Choose a CSV file first'); return; }
  try {
    const text = await inp.files[0].text();
    const r = await api('/api/buyers/import-csv', {
      method:'POST', headers:{'Content-Type':'text/csv'}, body:text
    });
    closeM('mCsv');
    inp.value = '';
    let msg = 'Imported ' + r.added + ' buyers (' + r.total_in_db + ' total)';
    if (r.errors.length) msg += ' · ' + r.errors.length + ' rows skipped: ' + r.errors[0];
    toast(msg, r.errors.length ? 7000 : 3000);
    load(r.sectors.length && !r.sectors.includes(S) ? r.sectors[0] : S);
  } catch (err) { toast('Import failed: ' + err.message, 5000); }
};

/* ==================================================================
   Init
   ================================================================== */
const setDefaultDate = () => {
  const di = document.querySelector('input[name="last_arrival_date"]');
  if (di) di.value = new Date().toISOString().split('T')[0];
};

$('sector').addEventListener('change', e => load(e.target.value));
$('fnIn').value = FN;
$('fcIn').value = FC;
$('waBtn').href = waHref();
$('waBtn').hidden = !DEMO;
setDefaultDate();
lastSize = $('stage').clientWidth + 'x' + $('stage').clientHeight;
updateChrome();
load(S);
</script>
</body>
</html>"""


def _js_str(value: str) -> str:
    """JSON-encode for safe embedding inside a <script> block."""
    return json.dumps(value).replace("<", "\\u003c")


@app.get("/", response_class=HTMLResponse)
async def dashboard(
    factory: str = Query(DEFAULT_FACTORY, description="Factory name"),
    city: str = Query(DEFAULT_CITY, description="City"),
    category: str = Query(DEFAULT_CATEGORY, description="Default sector"),
):
    """Serve the white-label ExportPulse AI dashboard."""
    factory = factory.strip()[:80] or DEFAULT_FACTORY
    city = city.strip()[:60] or DEFAULT_CITY
    category = category.strip().lower()
    if category not in SECTORS:
        category = "handicrafts"

    values = {
        "FACTORY": factory,
        "CITY": city,
        "CATEGORY": category,
        "SELLER": SELLER_WHATSAPP,
    }
    # Demo pages (no client buyer file) carry the closing "get the full list" band.
    is_demo = not os.path.isfile(BUYERS_CSV)

    def _sub(m: "re.Match") -> str:
        if m.group(1) == "DEMO":
            return "true" if is_demo else "false"
        raw = values[m.group(1)]
        return html.escape(raw) if m.group(2) == "HTML" else _js_str(raw)

    page = re.sub(
        r"__(FACTORY|CITY|CATEGORY|SELLER|DEMO)_(HTML|JS)__", _sub, DASHBOARD_HTML
    )
    return HTMLResponse(content=page)


# ---------------------------------------------------------------------------
# Static assets and marketing pages (Meridian; see INTEGRATION-PLAN.md)
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
# Styles, scripts and self-hosted photos used by the dashboard and the marketing pages.
app.mount("/static", StaticFiles(directory=os.path.join(_HERE, "static")), name="static")
# The marketing pages describe the demo dataset, so only demo deployments (no client CSV) serve them.
if not os.path.isfile(BUYERS_CSV):
    app.mount("/site", StaticFiles(directory=os.path.join(_HERE, "site"), html=True), name="site")


# ---------------------------------------------------------------------------
# Section 4: Server Startup
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "8000")),
    )
