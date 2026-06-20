from __future__ import annotations

import numpy as np
import pandas as pd


def _pct(value: float) -> float:
    return value / 100


def build_dcf_model(inputs: dict) -> dict:
    growth = _pct(inputs["revenue_growth"])
    ebitda_margin = _pct(inputs["ebitda_margin"])
    da_pct = _pct(inputs["da_percent_revenue"])
    tax_rate = _pct(inputs["tax_rate"])
    capex_pct = _pct(inputs["capex_percent_revenue"])
    nwc_pct = _pct(inputs["nwc_percent_revenue"])
    wacc = _pct(inputs["wacc"])
    terminal_growth = _pct(inputs["terminal_growth"])

    rows = []
    previous_revenue = inputs["starting_revenue"]
    for year in range(1, 6):
        revenue = previous_revenue * (1 + growth)
        ebitda = revenue * ebitda_margin
        da = revenue * da_pct
        ebit = ebitda - da
        tax = max(0, ebit * tax_rate)
        capex = revenue * capex_pct
        change_nwc = revenue * nwc_pct
        fcf = ebit - tax + da - capex - change_nwc
        discount_factor = 1 / ((1 + wacc) ** year)
        rows.append(
            {
                "Year": f"Year {year}",
                "Revenue": round(revenue, 1),
                "EBITDA": round(ebitda, 1),
                "D&A": round(da, 1),
                "EBIT": round(ebit, 1),
                "Tax": round(tax, 1),
                "Capex": round(capex, 1),
                "Change in NWC": round(change_nwc, 1),
                "Free Cash Flow": round(fcf, 1),
                "Discount Factor": round(discount_factor, 3),
                "PV of FCF": fcf * discount_factor,
            }
        )
        previous_revenue = revenue

    forecast = pd.DataFrame(rows)
    year_5_fcf = forecast.iloc[-1]["Free Cash Flow"]
    if wacc <= terminal_growth:
        terminal_value = np.nan
        pv_terminal_value = np.nan
        enterprise_value = np.nan
    else:
        terminal_value = year_5_fcf * (1 + terminal_growth) / (wacc - terminal_growth)
        pv_terminal_value = terminal_value / ((1 + wacc) ** 5)
        enterprise_value = forecast["PV of FCF"].sum() + pv_terminal_value

    equity_value = enterprise_value - inputs["net_debt"]
    implied_share_price = equity_value / inputs["shares_outstanding"]

    return {
        "forecast": forecast.drop(columns=["PV of FCF"]),
        "enterprise_value": float(enterprise_value),
        "equity_value": float(equity_value),
        "terminal_value": float(terminal_value),
        "pv_terminal_value": float(pv_terminal_value),
        "implied_share_price": float(implied_share_price),
    }


def build_wacc_growth_sensitivity(inputs: dict) -> pd.DataFrame:
    wacc_values = [inputs["wacc"] - 1.0, inputs["wacc"] - 0.5, inputs["wacc"], inputs["wacc"] + 0.5, inputs["wacc"] + 1.0]
    growth_values = [
        inputs["terminal_growth"] - 0.5,
        inputs["terminal_growth"],
        inputs["terminal_growth"] + 0.5,
        inputs["terminal_growth"] + 1.0,
    ]
    rows = []
    for wacc in wacc_values:
        row = {"WACC": f"{wacc:.1f}%"}
        for growth in growth_values:
            scenario = inputs.copy()
            scenario["wacc"] = wacc
            scenario["terminal_growth"] = growth
            value = build_dcf_model(scenario)["implied_share_price"]
            row[f"{growth:.1f}% g"] = round(value, 2) if not np.isnan(value) else "n/a"
        rows.append(row)
    return pd.DataFrame(rows).set_index("WACC")


def build_exit_multiple_sensitivity(inputs: dict) -> pd.DataFrame:
    base = build_dcf_model(inputs)
    forecast = base["forecast"]
    year_5_ebitda = float(forecast.iloc[-1]["EBITDA"])
    wacc_values = [inputs["wacc"] - 1.0, inputs["wacc"], inputs["wacc"] + 1.0]
    multiple_values = [
        inputs["exit_ebitda_multiple"] - 1.0,
        inputs["exit_ebitda_multiple"],
        inputs["exit_ebitda_multiple"] + 1.0,
        inputs["exit_ebitda_multiple"] + 2.0,
    ]
    rows = []
    for wacc in wacc_values:
        row = {"WACC": f"{wacc:.1f}%"}
        for multiple in multiple_values:
            pv_fcf = 0
            for i, fcf in enumerate(forecast["Free Cash Flow"], start=1):
                pv_fcf += fcf / ((1 + _pct(wacc)) ** i)
            terminal_value = year_5_ebitda * multiple
            ev = pv_fcf + terminal_value / ((1 + _pct(wacc)) ** 5)
            equity = ev - inputs["net_debt"]
            row[f"{multiple:.1f}x"] = round(equity / inputs["shares_outstanding"], 2)
        rows.append(row)
    return pd.DataFrame(rows).set_index("WACC")


def build_comps_summary(peer_df: pd.DataFrame, profile: dict) -> dict:
    df = peer_df.copy()
    for column in ["Market Cap", "Enterprise Value", "Revenue", "EBITDA", "Net Income"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df["EV/Revenue"] = df["Enterprise Value"] / df["Revenue"]
    df["EV/EBITDA"] = df["Enterprise Value"] / df["EBITDA"]
    df["P/E"] = df["Market Cap"] / df["Net Income"]

    stats = pd.DataFrame(
        {
            "EV/Revenue": [df["EV/Revenue"].mean(), df["EV/Revenue"].median(), df["EV/Revenue"].min(), df["EV/Revenue"].max()],
            "EV/EBITDA": [df["EV/EBITDA"].mean(), df["EV/EBITDA"].median(), df["EV/EBITDA"].min(), df["EV/EBITDA"].max()],
            "P/E": [df["P/E"].mean(), df["P/E"].median(), df["P/E"].min(), df["P/E"].max()],
        },
        index=["Mean", "Median", "Low", "High"],
    )

    valuation_low = profile["ebitda"] * stats.loc["Low", "EV/EBITDA"] - profile["net_debt"]
    valuation_high = profile["ebitda"] * stats.loc["High", "EV/EBITDA"] - profile["net_debt"]
    valuation_mid = profile["ebitda"] * stats.loc["Median", "EV/EBITDA"] - profile["net_debt"]
    share_low = valuation_low / profile["shares_outstanding"]
    share_high = valuation_high / profile["shares_outstanding"]

    display = df[["Company", "EV/Revenue", "EV/EBITDA", "P/E"]].copy()
    display = pd.concat([display, stats.reset_index(names="Company")], ignore_index=True)
    for col in ["EV/Revenue", "EV/EBITDA", "P/E"]:
        display[col] = display[col].map(lambda x: f"{x:.1f}x" if pd.notna(x) else "n/a")

    implied_range = pd.DataFrame(
        [
            ["Low", stats.loc["Low", "EV/EBITDA"], valuation_low, share_low],
            ["Median", stats.loc["Median", "EV/EBITDA"], valuation_mid, valuation_mid / profile["shares_outstanding"]],
            ["High", stats.loc["High", "EV/EBITDA"], valuation_high, share_high],
        ],
        columns=["Case", "EV/EBITDA", "Implied Equity Value", "Implied Share Price"],
    )

    currency = profile.get("currency", "USD")
    return {
        "peer_table": df,
        "multiples_table": display,
        "stats": stats,
        "implied_range": implied_range,
        "valuation_low": float(valuation_low),
        "valuation_mid": float(valuation_mid),
        "valuation_high": float(valuation_high),
        "valuation_range_label": f"{currency} {valuation_low:,.0f}m to {currency} {valuation_high:,.0f}m",
        "share_price_range_label": f"{currency} {share_low:,.2f} to {currency} {share_high:,.2f}",
    }


def build_precedent_summary(transaction_df: pd.DataFrame, profile: dict) -> dict:
    df = transaction_df.copy()
    df["Revenue Multiple"] = pd.to_numeric(df["Revenue Multiple"], errors="coerce")
    df["EBITDA Multiple"] = pd.to_numeric(df["EBITDA Multiple"], errors="coerce")
    median_revenue_multiple = df["Revenue Multiple"].median()
    median_ebitda_multiple = df["EBITDA Multiple"].median()
    low_ebitda_multiple = df["EBITDA Multiple"].quantile(0.25)
    high_ebitda_multiple = df["EBITDA Multiple"].quantile(0.75)

    valuation_low = profile["ebitda"] * low_ebitda_multiple - profile["net_debt"]
    valuation_mid = profile["ebitda"] * median_ebitda_multiple - profile["net_debt"]
    valuation_high = profile["ebitda"] * high_ebitda_multiple - profile["net_debt"]
    share_low = valuation_low / profile["shares_outstanding"]
    share_high = valuation_high / profile["shares_outstanding"]

    summary_table = df[["Target", "Acquirer", "Announcement Date", "Revenue Multiple", "EBITDA Multiple"]].copy()
    summary_table["Revenue Multiple"] = summary_table["Revenue Multiple"].map(lambda x: f"{x:.1f}x")
    summary_table["EBITDA Multiple"] = summary_table["EBITDA Multiple"].map(lambda x: f"{x:.1f}x")
    rationale_summary = (
        "Common strategic themes include expanding enterprise software capabilities, adding recurring revenue, "
        "strengthening cloud or data analytics coverage, and using scale to improve distribution or margins."
    )
    currency = profile.get("currency", "USD")
    return {
        "transaction_table": df,
        "summary_table": summary_table,
        "median_revenue_multiple": float(median_revenue_multiple),
        "median_ebitda_multiple": float(median_ebitda_multiple),
        "valuation_low": float(valuation_low),
        "valuation_mid": float(valuation_mid),
        "valuation_high": float(valuation_high),
        "valuation_range_label": f"{currency} {valuation_low:,.0f}m to {currency} {valuation_high:,.0f}m",
        "share_price_range_label": f"{currency} {share_low:,.2f} to {currency} {share_high:,.2f}",
        "rationale_summary": rationale_summary,
    }


def build_merger_model(inputs: dict) -> dict:
    cash_used = inputs["target_purchase_price"] * _pct(inputs["cash_percent"])
    debt_raised = inputs["target_purchase_price"] * _pct(inputs["debt_percent"])
    stock_value = max(0.0, inputs["target_purchase_price"] - cash_used - debt_raised)
    new_shares = stock_value / inputs["acquirer_share_price"]
    interest_expense = debt_raised * _pct(inputs["interest_rate"])
    after_tax_interest = interest_expense * (1 - _pct(inputs["tax_rate"]))
    after_tax_synergies = inputs["expected_synergies"] * (1 - _pct(inputs["tax_rate"]))

    standalone_eps = inputs["acquirer_net_income"] / inputs["acquirer_shares"]
    pro_forma_net_income = inputs["acquirer_net_income"] + inputs["target_net_income"] + after_tax_synergies - after_tax_interest
    pro_forma_shares = inputs["acquirer_shares"] + new_shares
    pro_forma_eps = pro_forma_net_income / pro_forma_shares
    accretion_dilution_pct = (pro_forma_eps / standalone_eps - 1) * 100
    if accretion_dilution_pct > 1:
        recommendation = "Accretive"
    elif accretion_dilution_pct < -1:
        recommendation = "Dilutive"
    else:
        recommendation = "Neutral"

    sources_uses = pd.DataFrame(
        [
            ["Cash Used", cash_used],
            ["Debt Raised", debt_raised],
            ["Stock Issued", stock_value],
            ["New Shares Issued", new_shares],
            ["After-Tax Synergies", after_tax_synergies],
            ["After-Tax Interest Expense", after_tax_interest],
        ],
        columns=["Item", "Amount"],
    )

    return {
        "standalone_eps": float(standalone_eps),
        "pro_forma_eps": float(pro_forma_eps),
        "accretion_dilution_pct": float(accretion_dilution_pct),
        "recommendation": recommendation,
        "new_shares_issued": float(new_shares),
        "sources_uses": sources_uses,
    }
