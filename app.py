from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from src.data import (
    DEFAULT_COMPS,
    DEFAULT_COMPANY_PROFILE,
    DEFAULT_DCF_INPUTS,
    DEFAULT_MERGER_INPUTS,
    SAMPLE_TRANSACTIONS,
    fetch_company_profile,
)
from src.research import build_research_pack
from src.reporting import build_pitchbook_html
from src.valuation import (
    build_comps_summary,
    build_dcf_model,
    build_exit_multiple_sensitivity,
    build_merger_model,
    build_precedent_summary,
    build_wacc_growth_sensitivity,
)


APP_TITLE = "Financial Analysis & Valuation Platform"


st.set_page_config(
    page_title=APP_TITLE,
    layout="wide",
    initial_sidebar_state="expanded",
)


def load_css() -> None:
    css_path = Path(__file__).parent / "assets" / "styles.css"
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def format_currency(value: float, currency: str = "USD", decimals: int = 1) -> str:
    if pd.isna(value):
        return "n/a"
    abs_value = abs(value)
    if abs_value >= 1_000_000:
        return f"{currency} {value / 1_000_000:.{decimals}f}T"
    if abs_value >= 1_000:
        return f"{currency} {value / 1_000:.{decimals}f}B"
    return f"{currency} {value:.{decimals}f}m"


def format_multiple(value: float) -> str:
    if pd.isna(value):
        return "n/a"
    return f"{value:.1f}x"


def summary_card(label: str, value: str, detail: str | None = None, positive: bool | None = None) -> None:
    tone = ""
    if positive is True:
        tone = "positive"
    elif positive is False:
        tone = "negative"

    detail_html = f"<div class='metric-detail {tone}'>{detail}</div>" if detail else ""
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            {detail_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(title: str, subtitle: str | None = None) -> None:
    st.markdown(f"<h1 class='page-title'>{title}</h1>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<p class='page-subtitle'>{subtitle}</p>", unsafe_allow_html=True)


def company_profile_panel() -> dict:
    st.sidebar.markdown("### Company")
    profile = st.session_state.get("profile", DEFAULT_COMPANY_PROFILE.copy()).copy()
    ticker = st.sidebar.text_input("Ticker", value=profile.get("ticker", "ACN")).strip().upper()
    company_name = st.sidebar.text_input(
        "Company name",
        value=profile.get("name", DEFAULT_COMPANY_PROFILE["name"]),
    )
    use_live_data = st.sidebar.checkbox("Attempt live market data", value=False)

    profile["ticker"] = ticker or profile["ticker"]
    profile["name"] = company_name or profile["name"]

    if use_live_data and ticker:
        live_profile = fetch_company_profile(ticker)
        profile.update({k: v for k, v in live_profile.items() if v not in [None, "", 0]})

    st.session_state["profile"] = profile
    return profile


def sidebar_nav() -> str:
    st.sidebar.markdown(
        """
        <div class="sidebar-brand">
            <div class="brand-mark">FAV</div>
            <div>
                <div class="brand-title">Financial Analysis</div>
                <div class="brand-subtitle">Technology & Services</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    return st.sidebar.radio(
        "Navigation",
        [
            "Dashboard",
            "Company Overview",
            "DCF Valuation",
            "Comparable Companies",
            "Precedent Transactions",
            "Merger Analysis",
            "AI Research Assistant",
            "Pitchbook Summary",
        ],
        label_visibility="collapsed",
    )


def render_dashboard(profile: dict, dcf: dict, comps: dict, precedents: dict, merger: dict) -> None:
    section_header("Dashboard", "Technology & Services analysis workspace")

    cols = st.columns(6)
    metrics = [
        ("Company", profile["name"], profile["ticker"], None),
        ("Share Price", f"{profile['currency']} {profile['share_price']:.2f}", "latest available or manual", None),
        ("Market Cap", format_currency(profile["market_cap"], profile["currency"]), None, None),
        ("Enterprise Value", format_currency(profile["enterprise_value"], profile["currency"]), None, None),
        ("Sector", profile["sector"], None, None),
        ("Currency", profile["currency"], None, None),
    ]
    for col, (label, value, detail, tone) in zip(cols, metrics):
        with col:
            summary_card(label, value, detail, tone)

    left, right = st.columns([1.05, 0.95], gap="large")
    with left:
        st.markdown("### Valuation Summary (Indicative)")
        valuation_summary = pd.DataFrame(
            [
                {
                    "Method": "DCF",
                    "Equity Value": format_currency(dcf["equity_value"], profile["currency"]),
                    "Implied Share Price": f"{profile['currency']} {dcf['implied_share_price']:.2f}",
                    "Notes": "Base case",
                },
                {
                    "Method": "Comparable Companies",
                    "Equity Value": comps["valuation_range_label"],
                    "Implied Share Price": comps["share_price_range_label"],
                    "Notes": "EV/EBITDA",
                },
                {
                    "Method": "Precedent Transactions",
                    "Equity Value": precedents["valuation_range_label"],
                    "Implied Share Price": precedents["share_price_range_label"],
                    "Notes": "EV/EBITDA",
                },
            ]
        )
        st.dataframe(valuation_summary, use_container_width=True, hide_index=True)

    with right:
        st.markdown("### Valuation Football Field")
        football = pd.DataFrame(
            [
                {
                    "Method": "Current Market Cap",
                    "Low": profile["market_cap"],
                    "High": profile["market_cap"],
                    "Mid": profile["market_cap"],
                },
                {"Method": "DCF", "Low": dcf["equity_value"], "High": dcf["equity_value"], "Mid": dcf["equity_value"]},
                {
                    "Method": "Comparable Companies",
                    "Low": comps["valuation_low"],
                    "High": comps["valuation_high"],
                    "Mid": comps["valuation_mid"],
                },
                {
                    "Method": "Precedent Transactions",
                    "Low": precedents["valuation_low"],
                    "High": precedents["valuation_high"],
                    "Mid": precedents["valuation_mid"],
                },
            ]
        )
        fig = go.Figure()
        for _, row in football.iterrows():
            fig.add_trace(
                go.Scatter(
                    x=[row["Low"], row["High"]],
                    y=[row["Method"], row["Method"]],
                    mode="lines+markers",
                    line=dict(width=6),
                    marker=dict(size=9),
                    name=row["Method"],
                    showlegend=False,
                )
            )
        fig.update_layout(
            height=290,
            margin=dict(l=8, r=8, t=10, b=20),
            xaxis_title=f"Equity value ({profile['currency']}m)",
            yaxis_title=None,
            template="plotly_white",
        )
        st.plotly_chart(fig, use_container_width=True)

    c1, c2, c3 = st.columns(3, gap="large")
    with c1:
        st.markdown("### DCF Summary")
        dcf_preview = dcf["forecast"][["Year", "Revenue", "EBITDA", "EBIT", "Free Cash Flow"]].copy()
        st.dataframe(dcf_preview, use_container_width=True, hide_index=True)
        summary_card("Enterprise Value", format_currency(dcf["enterprise_value"], profile["currency"]))
    with c2:
        st.markdown("### Comparable Companies")
        st.dataframe(comps["multiples_table"], use_container_width=True, hide_index=True)
    with c3:
        st.markdown("### Precedent Transactions")
        st.dataframe(precedents["summary_table"], use_container_width=True, hide_index=True)

    lower_left, lower_right = st.columns([0.8, 1.2], gap="large")
    with lower_left:
        st.markdown("### Merger Analysis")
        summary_card("Standalone EPS", f"{profile['currency']} {merger['standalone_eps']:.2f}")
        summary_card("Pro Forma EPS", f"{profile['currency']} {merger['pro_forma_eps']:.2f}", merger["recommendation"], merger["accretion_dilution_pct"] >= 0)
    with lower_right:
        st.markdown("### Research Assistant")
        st.info("Generate structured company, sector, M&A rationale, valuation, risk, and banker-question output from the Research Assistant page.")


def render_company_overview(profile: dict) -> None:
    section_header("Company Overview", "Profile, market data, and manually adjustable fundamentals")
    st.caption("Live data is optional. Missing values are kept editable and should be treated as manual inputs.")

    col1, col2 = st.columns([0.68, 0.32], gap="large")
    with col1:
        st.markdown("### Business Description")
        profile["description"] = st.text_area("Description", value=profile["description"], height=170)
    with col2:
        st.markdown("### Profile")
        profile["sector"] = st.text_input("Sector", value=profile["sector"])
        profile["currency"] = st.text_input("Currency", value=profile["currency"])
        profile["share_price"] = st.number_input("Share price", value=float(profile["share_price"]), min_value=0.0, step=1.0)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        profile["market_cap"] = st.number_input("Market cap", value=float(profile["market_cap"]), min_value=0.0, step=100.0)
    with c2:
        profile["enterprise_value"] = st.number_input("Enterprise value", value=float(profile["enterprise_value"]), min_value=0.0, step=100.0)
    with c3:
        profile["revenue"] = st.number_input("Revenue", value=float(profile["revenue"]), min_value=0.0, step=100.0)
    with c4:
        profile["ebitda"] = st.number_input("EBITDA", value=float(profile["ebitda"]), min_value=0.0, step=50.0)

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        profile["net_income"] = st.number_input("Net income", value=float(profile["net_income"]), min_value=-100_000.0, step=50.0)
    with c6:
        profile["net_debt"] = st.number_input("Net debt", value=float(profile["net_debt"]), step=50.0)
    with c7:
        profile["shares_outstanding"] = st.number_input("Shares outstanding", value=float(profile["shares_outstanding"]), min_value=0.1, step=10.0)
    with c8:
        profile["ebitda_margin"] = st.number_input("EBITDA margin", value=float(profile["ebitda_margin"]), min_value=-100.0, max_value=100.0, step=0.5)

    st.session_state["profile"] = profile


def render_dcf(profile: dict) -> dict:
    section_header("DCF Valuation", "Five-year unlevered free cash flow model with sensitivity analysis")

    defaults = DEFAULT_DCF_INPUTS.copy()
    defaults.update(
        {
            "starting_revenue": profile.get("revenue", defaults["starting_revenue"]),
            "ebitda_margin": profile.get("ebitda_margin", defaults["ebitda_margin"]),
            "net_debt": profile.get("net_debt", defaults["net_debt"]),
            "shares_outstanding": profile.get("shares_outstanding", defaults["shares_outstanding"]),
        }
    )
    defaults.update(st.session_state.get("dcf_inputs", {}))

    with st.expander("Model Inputs", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        inputs = {}
        with c1:
            inputs["starting_revenue"] = st.number_input("Starting revenue", value=float(defaults["starting_revenue"]), min_value=0.0)
            inputs["revenue_growth"] = st.number_input("Annual revenue growth %", value=float(defaults["revenue_growth"]), step=0.5)
            inputs["ebitda_margin"] = st.number_input("EBITDA margin %", value=float(defaults["ebitda_margin"]), step=0.5)
        with c2:
            inputs["da_percent_revenue"] = st.number_input("D&A % of revenue", value=float(defaults["da_percent_revenue"]), step=0.25)
            inputs["tax_rate"] = st.number_input("Tax rate %", value=float(defaults["tax_rate"]), step=0.5)
            inputs["capex_percent_revenue"] = st.number_input("Capex % of revenue", value=float(defaults["capex_percent_revenue"]), step=0.25)
        with c3:
            inputs["nwc_percent_revenue"] = st.number_input("Change in NWC % of revenue", value=float(defaults["nwc_percent_revenue"]), step=0.25)
            inputs["wacc"] = st.number_input("WACC %", value=float(defaults["wacc"]), step=0.25)
            inputs["terminal_growth"] = st.number_input("Terminal growth %", value=float(defaults["terminal_growth"]), step=0.25)
        with c4:
            inputs["net_debt"] = st.number_input("Net debt", value=float(defaults["net_debt"]), step=100.0)
            inputs["shares_outstanding"] = st.number_input("Shares outstanding", value=float(defaults["shares_outstanding"]), min_value=0.1)
            inputs["exit_ebitda_multiple"] = st.number_input("Exit EBITDA multiple", value=float(defaults["exit_ebitda_multiple"]), step=0.25)

    dcf = build_dcf_model(inputs)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        summary_card("Enterprise Value", format_currency(dcf["enterprise_value"], profile["currency"]))
    with c2:
        summary_card("Equity Value", format_currency(dcf["equity_value"], profile["currency"]))
    with c3:
        summary_card("Implied Share Price", f"{profile['currency']} {dcf['implied_share_price']:.2f}")
    with c4:
        summary_card("Terminal Value", format_currency(dcf["terminal_value"], profile["currency"]))

    st.markdown("### Forecast")
    st.dataframe(dcf["forecast"], use_container_width=True, hide_index=True)

    chart_df = dcf["forecast"].melt(
        id_vars="Year",
        value_vars=["Revenue", "EBITDA", "Free Cash Flow"],
        var_name="Metric",
        value_name="Value",
    )
    fig = px.bar(chart_df, x="Year", y="Value", color="Metric", barmode="group", template="plotly_white")
    fig.update_layout(height=360, yaxis_title=f"{profile['currency']}m", margin=dict(l=8, r=8, t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

    s1, s2 = st.columns(2, gap="large")
    with s1:
        st.markdown("### WACC vs Terminal Growth")
        sensitivity = build_wacc_growth_sensitivity(inputs)
        st.dataframe(sensitivity, use_container_width=True)
    with s2:
        st.markdown("### Exit EBITDA Multiple vs WACC")
        exit_sensitivity = build_exit_multiple_sensitivity(inputs)
        st.dataframe(exit_sensitivity, use_container_width=True)

    st.session_state["dcf_inputs"] = inputs
    st.session_state["dcf"] = dcf
    return dcf


def render_comps(profile: dict) -> dict:
    section_header("Comparable Companies Analysis", "Peer trading multiples and implied valuation range")
    st.caption("Default peer data is sample data for demonstration and should be refreshed before investment use.")

    edited = st.data_editor(DEFAULT_COMPS, num_rows="dynamic", use_container_width=True, hide_index=True)
    comps = build_comps_summary(edited, profile)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        summary_card("Mean EV/EBITDA", format_multiple(comps["stats"].loc["Mean", "EV/EBITDA"]))
    with c2:
        summary_card("Median EV/EBITDA", format_multiple(comps["stats"].loc["Median", "EV/EBITDA"]))
    with c3:
        summary_card("Implied Equity Low", format_currency(comps["valuation_low"], profile["currency"]))
    with c4:
        summary_card("Implied Equity High", format_currency(comps["valuation_high"], profile["currency"]))

    left, right = st.columns([0.58, 0.42], gap="large")
    with left:
        st.markdown("### Peer Multiples")
        st.dataframe(comps["multiples_table"], use_container_width=True, hide_index=True)
    with right:
        st.markdown("### EV/EBITDA Distribution")
        fig = px.bar(
            comps["peer_table"],
            x="Company",
            y="EV/EBITDA",
            template="plotly_white",
            color_discrete_sequence=["#163b63"],
        )
        fig.update_layout(height=360, xaxis_tickangle=-30, margin=dict(l=8, r=8, t=20, b=80))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Implied Valuation Range")
    st.dataframe(comps["implied_range"], use_container_width=True, hide_index=True)
    st.session_state["comps"] = comps
    return comps


def render_precedents(profile: dict) -> dict:
    section_header("Precedent Transactions", "Editable Technology & Services transaction database")
    st.caption("Sample data only. It is included to demonstrate transaction screening and valuation methodology.")

    sectors = ["All"] + sorted(SAMPLE_TRANSACTIONS["Sector"].unique().tolist())
    selected_sector = st.selectbox("Sector filter", sectors)
    table = SAMPLE_TRANSACTIONS.copy()
    if selected_sector != "All":
        table = table[table["Sector"] == selected_sector]

    edited = st.data_editor(table, num_rows="dynamic", use_container_width=True, hide_index=True)
    precedents = build_precedent_summary(edited, profile)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        summary_card("Median EV/Revenue", format_multiple(precedents["median_revenue_multiple"]))
    with c2:
        summary_card("Median EV/EBITDA", format_multiple(precedents["median_ebitda_multiple"]))
    with c3:
        summary_card("Implied Equity Low", format_currency(precedents["valuation_low"], profile["currency"]))
    with c4:
        summary_card("Implied Equity High", format_currency(precedents["valuation_high"], profile["currency"]))

    st.markdown("### Transaction Rationale Themes")
    st.write(precedents["rationale_summary"])

    fig = px.scatter(
        edited,
        x="Revenue Multiple",
        y="EBITDA Multiple",
        size="Transaction Value",
        color="Sector",
        hover_name="Target",
        template="plotly_white",
    )
    fig.update_layout(height=380, margin=dict(l=8, r=8, t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)
    st.session_state["precedents"] = precedents
    return precedents


def render_merger(profile: dict) -> dict:
    section_header("Merger Model / Accretion-Dilution", "High-level pro forma EPS impact analysis")
    defaults = DEFAULT_MERGER_INPUTS.copy()
    defaults.update(
        {
            "acquirer_share_price": profile["share_price"],
            "acquirer_shares": profile["shares_outstanding"],
            "acquirer_net_income": profile["net_income"],
        }
    )

    c1, c2, c3 = st.columns(3)
    inputs = {}
    with c1:
        inputs["acquirer_share_price"] = st.number_input("Acquirer share price", value=float(defaults["acquirer_share_price"]), min_value=0.01)
        inputs["acquirer_shares"] = st.number_input("Acquirer shares outstanding", value=float(defaults["acquirer_shares"]), min_value=0.1)
        inputs["acquirer_net_income"] = st.number_input("Acquirer net income", value=float(defaults["acquirer_net_income"]))
    with c2:
        inputs["target_purchase_price"] = st.number_input("Target purchase price", value=float(defaults["target_purchase_price"]), min_value=0.0)
        inputs["target_net_income"] = st.number_input("Target net income", value=float(defaults["target_net_income"]))
        inputs["expected_synergies"] = st.number_input("Pre-tax expected synergies", value=float(defaults["expected_synergies"]))
    with c3:
        inputs["cash_percent"] = st.slider("Cash financing %", 0.0, 100.0, float(defaults["cash_percent"]), 1.0)
        inputs["debt_percent"] = st.slider("Debt financing %", 0.0, 100.0, float(defaults["debt_percent"]), 1.0)
        inputs["stock_percent"] = max(0.0, 100.0 - inputs["cash_percent"] - inputs["debt_percent"])
        st.metric("Stock financing %", f"{inputs['stock_percent']:.1f}%")
        inputs["interest_rate"] = st.number_input("Interest rate on debt %", value=float(defaults["interest_rate"]), step=0.25)
        inputs["tax_rate"] = st.number_input("Tax rate %", value=float(defaults["tax_rate"]), step=0.5)

    merger = build_merger_model(inputs)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        summary_card("Standalone EPS", f"{profile['currency']} {merger['standalone_eps']:.2f}")
    with c2:
        summary_card("Pro Forma EPS", f"{profile['currency']} {merger['pro_forma_eps']:.2f}")
    with c3:
        summary_card("Accretion / Dilution", f"{merger['accretion_dilution_pct']:.1f}%", merger["recommendation"], merger["accretion_dilution_pct"] >= 0)
    with c4:
        summary_card("New Shares Issued", f"{merger['new_shares_issued']:.1f}m")

    st.markdown("### Sources and Uses")
    st.dataframe(merger["sources_uses"], use_container_width=True, hide_index=True)
    st.session_state["merger"] = merger
    return merger


def render_research(profile: dict, dcf: dict, comps: dict, precedents: dict) -> None:
    section_header("AI Corporate Finance Research Assistant", "Template-based output for banker-style analysis")
    prompt = st.text_area(
        "Research question or pitch angle",
        value=f"Prepare a Technology & Services investment banking summary for {profile['name']}.",
        height=90,
    )
    pack = build_research_pack(profile, dcf, comps, precedents, prompt)
    for heading, bullets in pack.items():
        st.markdown(f"### {heading}")
        for bullet in bullets:
            st.markdown(f"- {bullet}")


def render_pitchbook(profile: dict, dcf: dict, comps: dict, precedents: dict, merger: dict) -> None:
    section_header("Pitchbook Summary", "Printable report page for interview discussion and screenshots")
    html = build_pitchbook_html(profile, dcf, comps, precedents, merger)

    c1, c2, c3 = st.columns(3)
    with c1:
        summary_card("DCF Implied Price", f"{profile['currency']} {dcf['implied_share_price']:.2f}")
    with c2:
        summary_card("Comps Range", comps["share_price_range_label"])
    with c3:
        summary_card("Transaction Range", precedents["share_price_range_label"])

    components.html(html, height=760, scrolling=True)
    st.download_button(
        "Download printable HTML pitchbook",
        data=html,
        file_name=f"{profile['ticker']}_pitchbook_summary.html",
        mime="text/html",
        use_container_width=True,
    )


def main() -> None:
    load_css()
    nav = sidebar_nav()
    profile = company_profile_panel()

    dcf_inputs = DEFAULT_DCF_INPUTS.copy()
    dcf_inputs.update(
        {
            "starting_revenue": profile.get("revenue", dcf_inputs["starting_revenue"]),
            "ebitda_margin": profile.get("ebitda_margin", dcf_inputs["ebitda_margin"]),
            "net_debt": profile.get("net_debt", dcf_inputs["net_debt"]),
            "shares_outstanding": profile.get("shares_outstanding", dcf_inputs["shares_outstanding"]),
        }
    )
    dcf_inputs.update(st.session_state.get("dcf_inputs", {}))
    base_dcf = build_dcf_model(dcf_inputs)
    base_comps = build_comps_summary(DEFAULT_COMPS, profile)
    base_precedents = build_precedent_summary(SAMPLE_TRANSACTIONS, profile)
    base_merger = build_merger_model(DEFAULT_MERGER_INPUTS | {
        "acquirer_share_price": profile["share_price"],
        "acquirer_shares": profile["shares_outstanding"],
        "acquirer_net_income": profile["net_income"],
    })

    if nav == "Dashboard":
        render_dashboard(profile, base_dcf, base_comps, base_precedents, base_merger)
    elif nav == "Company Overview":
        render_company_overview(profile)
    elif nav == "DCF Valuation":
        render_dcf(profile)
    elif nav == "Comparable Companies":
        render_comps(profile)
    elif nav == "Precedent Transactions":
        render_precedents(profile)
    elif nav == "Merger Analysis":
        render_merger(profile)
    elif nav == "AI Research Assistant":
        render_research(profile, base_dcf, base_comps, base_precedents)
    elif nav == "Pitchbook Summary":
        render_pitchbook(profile, base_dcf, base_comps, base_precedents, base_merger)

    st.sidebar.markdown("<div class='sidebar-footer'>Sample analysis. Not investment advice.</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
