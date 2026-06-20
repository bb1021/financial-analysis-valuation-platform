from __future__ import annotations


def build_research_pack(profile: dict, dcf: dict, comps: dict, precedents: dict, prompt: str) -> dict[str, list[str]]:
    company = profile["name"]
    sector = profile["sector"]
    currency = profile["currency"]
    dcf_price = dcf["implied_share_price"]
    comps_range = comps["share_price_range_label"]
    tx_range = precedents["share_price_range_label"]

    return {
        "Company Overview": [
            f"{company} operates in {sector}, with revenue of approximately {currency} {profile['revenue']:,.0f}m and EBITDA of {currency} {profile['ebitda']:,.0f}m.",
            f"The current sample profile implies an EBITDA margin of {profile['ebitda_margin']:.1f}% and an enterprise value of {currency} {profile['enterprise_value']:,.0f}m.",
            "The platform treats missing market data as manual inputs, which mirrors the need to reconcile source data in real banking analysis.",
        ],
        "Investment Highlights": [
            "Scaled enterprise client base and recurring digital transformation demand can support resilient revenue visibility.",
            "Margin expansion may be available through delivery mix, automation, utilization discipline, and offshore leverage.",
            "Technology & Services exposure gives the company relevance to cloud migration, AI implementation, cybersecurity, and data modernization budgets.",
        ],
        "Key Risks": [
            "Discretionary technology consulting budgets can weaken if enterprise clients delay transformation programmes.",
            "Pricing pressure, wage inflation, and utilization volatility can compress EBITDA margins.",
            "Large acquisitions can create integration risk, cultural friction, and slower synergy realization than modeled.",
        ],
        "Sector Backdrop": [
            "Technology & Services M&A is driven by cloud migration, software modernization, security, data infrastructure, and vertical specialization.",
            "Strategic buyers typically pay for differentiated capabilities, enterprise account access, and recurring or managed services revenue.",
            "Private equity interest remains strongest where revenue visibility, margin improvement, and clear exit comparables are present.",
        ],
        "Acquisition Rationale": [
            "A buyer could use the asset to add delivery capability, deepen enterprise relationships, or accelerate exposure to higher-growth service lines.",
            "Potential synergies include cross-selling into existing clients, consolidating delivery operations, and reducing duplicative corporate costs.",
            "The strongest pitch angle would connect operating capabilities to specific buyer gaps rather than relying on broad scale logic.",
        ],
        "Valuation Summary": [
            f"The base-case DCF indicates an implied share price of {currency} {dcf_price:,.2f}.",
            f"Comparable company analysis indicates an implied share price range of {comps_range}.",
            f"Precedent transaction analysis indicates an implied share price range of {tx_range}.",
        ],
        "Questions a Banker Would Ask": [
            "Which revenue streams are recurring, project-based, or usage-driven, and how does this affect valuation multiple selection?",
            "What is the normalized EBITDA margin after removing one-off costs, restructuring items, and unusual utilization effects?",
            "Which strategic buyers would have the clearest synergy case, and what evidence supports those synergies?",
            "How sensitive is valuation to WACC, terminal growth, and exit multiple assumptions?",
            f"Prompt considered: {prompt}",
        ],
    }
