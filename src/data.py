from __future__ import annotations

import pandas as pd
import streamlit as st


DEFAULT_COMPANY_PROFILE = {
    "name": "Accenture plc",
    "ticker": "ACN",
    "sector": "Technology & Services",
    "currency": "USD",
    "description": (
        "Accenture is a global professional services company providing strategy, consulting, "
        "technology, managed services, and digital transformation support to enterprise clients. "
        "The company is included as a sample Technology & Services case study for valuation analysis."
    ),
    "share_price": 302.0,
    "market_cap": 189_000.0,
    "enterprise_value": 186_500.0,
    "revenue": 64_900.0,
    "ebitda": 12_600.0,
    "net_income": 7_400.0,
    "net_debt": -2_500.0,
    "shares_outstanding": 626.0,
    "ebitda_margin": 19.4,
}


DEFAULT_DCF_INPUTS = {
    "starting_revenue": 64_900.0,
    "revenue_growth": 5.5,
    "ebitda_margin": 19.5,
    "da_percent_revenue": 2.5,
    "tax_rate": 24.0,
    "capex_percent_revenue": 2.4,
    "nwc_percent_revenue": 1.0,
    "wacc": 9.0,
    "terminal_growth": 2.5,
    "net_debt": -2_500.0,
    "shares_outstanding": 626.0,
    "exit_ebitda_multiple": 13.0,
}


DEFAULT_COMPS = pd.DataFrame(
    [
        ["Accenture", 189_000, 186_500, 64_900, 12_600, 7_400],
        ["Cognizant", 37_200, 36_100, 19_400, 3_250, 2_120],
        ["EPAM Systems", 10_900, 10_100, 4_700, 720, 420],
        ["Globant", 8_400, 8_000, 2_100, 360, 240],
        ["Capgemini", 35_500, 38_400, 24_300, 3_800, 1_900],
        ["Wipro", 29_300, 27_900, 10_800, 2_100, 1_360],
    ],
    columns=["Company", "Market Cap", "Enterprise Value", "Revenue", "EBITDA", "Net Income"],
)


SAMPLE_TRANSACTIONS = pd.DataFrame(
    [
        ["IBM", "HashiCorp", "Cloud Infrastructure Software", "2024-04-24", 6_400, 9.2, 31.5, "Expands hybrid cloud automation and developer infrastructure tooling."],
        ["Cisco", "Splunk", "Data & Security Software", "2023-09-21", 28_000, 7.4, 24.0, "Adds scaled observability, security analytics, and recurring software revenue."],
        ["Broadcom", "VMware", "Enterprise Software", "2022-05-26", 61_000, 8.1, 18.4, "Creates a larger infrastructure software platform with cross-sell opportunities."],
        ["Thoma Bravo", "Anaplan", "Enterprise SaaS", "2022-03-20", 10_700, 14.2, 38.0, "Private equity take-private focused on planning software growth and margin expansion."],
        ["Microsoft", "Nuance Communications", "Healthcare AI Software", "2021-04-12", 19_700, 12.8, 29.4, "Strengthens vertical AI capabilities in healthcare workflow software."],
        ["Salesforce", "Slack", "Collaboration Software", "2020-12-01", 27_700, 24.0, 45.0, "Adds collaboration layer to enterprise CRM and platform ecosystem."],
        ["S&P Global", "IHS Markit", "Data & Analytics", "2020-11-30", 44_000, 10.5, 26.5, "Combines scaled financial data assets with industry analytics and benchmarks."],
        ["Infosys", "GuideVision", "IT Services", "2020-09-14", 35, 2.1, 11.5, "Builds ServiceNow implementation capability across European enterprise clients."],
    ],
    columns=[
        "Acquirer",
        "Target",
        "Sector",
        "Announcement Date",
        "Transaction Value",
        "Revenue Multiple",
        "EBITDA Multiple",
        "Strategic Rationale",
    ],
)


DEFAULT_MERGER_INPUTS = {
    "acquirer_share_price": 302.0,
    "acquirer_shares": 626.0,
    "acquirer_net_income": 7_400.0,
    "target_purchase_price": 8_000.0,
    "target_net_income": 420.0,
    "cash_percent": 25.0,
    "debt_percent": 35.0,
    "interest_rate": 6.0,
    "tax_rate": 24.0,
    "expected_synergies": 180.0,
}


@st.cache_data(show_spinner=False)
def fetch_company_profile(ticker: str) -> dict:
    try:
        import yfinance as yf

        stock = yf.Ticker(ticker)
        info = stock.info or {}
        market_cap = (info.get("marketCap") or 0) / 1_000_000
        enterprise_value = (info.get("enterpriseValue") or 0) / 1_000_000
        revenue = (info.get("totalRevenue") or 0) / 1_000_000
        ebitda = (info.get("ebitda") or 0) / 1_000_000
        net_income = (info.get("netIncomeToCommon") or 0) / 1_000_000
        shares = (info.get("sharesOutstanding") or 0) / 1_000_000
        return {
            "name": info.get("longName"),
            "ticker": ticker,
            "sector": info.get("sector") or info.get("industry"),
            "currency": info.get("financialCurrency") or info.get("currency"),
            "description": info.get("longBusinessSummary"),
            "share_price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "market_cap": market_cap,
            "enterprise_value": enterprise_value,
            "revenue": revenue,
            "ebitda": ebitda,
            "net_income": net_income,
            "shares_outstanding": shares,
            "ebitda_margin": (ebitda / revenue * 100) if revenue else None,
        }
    except Exception:
        return {}
