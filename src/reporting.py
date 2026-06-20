from __future__ import annotations


def build_pitchbook_html(profile: dict, dcf: dict, comps: dict, precedents: dict, merger: dict) -> str:
    forecast_html = dcf["forecast"].to_html(index=False, classes="table", border=0)
    comps_html = comps["multiples_table"].to_html(index=False, classes="table", border=0)
    precedents_html = precedents["summary_table"].head(6).to_html(index=False, classes="table", border=0)

    return f"""
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>{profile['ticker']} Pitchbook Summary</title>
      <style>
        body {{
          margin: 0;
          padding: 32px;
          background: #f7f8fa;
          color: #0e1726;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }}
        .page {{
          max-width: 1120px;
          margin: 0 auto;
          background: #fbfcfe;
          border: 1px solid #d9dee8;
          border-radius: 10px;
          padding: 30px;
        }}
        h1 {{ margin: 0 0 4px; font-size: 28px; }}
        h2 {{ margin: 28px 0 10px; font-size: 17px; }}
        p {{ line-height: 1.5; color: #445064; }}
        .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-top: 18px; }}
        .metric {{ border: 1px solid #d9dee8; border-radius: 8px; padding: 14px; background: #ffffff; }}
        .label {{ color: #667085; font-size: 12px; }}
        .value {{ font-weight: 700; font-size: 18px; margin-top: 5px; }}
        .table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
        .table th, .table td {{ border-bottom: 1px solid #e4e8ef; padding: 8px; text-align: left; }}
        .table th {{ background: #f0f3f7; color: #263449; }}
        .two {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
      </style>
    </head>
    <body>
      <main class="page">
        <h1>{profile['name']} Valuation Summary</h1>
        <p>{profile['sector']} | {profile['ticker']} | All figures in {profile['currency']}m unless noted</p>
        <div class="grid">
          <div class="metric"><div class="label">Market Cap</div><div class="value">{profile['currency']} {profile['market_cap']:,.0f}m</div></div>
          <div class="metric"><div class="label">Enterprise Value</div><div class="value">{profile['currency']} {profile['enterprise_value']:,.0f}m</div></div>
          <div class="metric"><div class="label">DCF Share Price</div><div class="value">{profile['currency']} {dcf['implied_share_price']:,.2f}</div></div>
          <div class="metric"><div class="label">Merger Impact</div><div class="value">{merger['recommendation']} {merger['accretion_dilution_pct']:.1f}%</div></div>
        </div>
        <h2>Company Profile</h2>
        <p>{profile['description']}</p>
        <div class="two">
          <section>
            <h2>DCF Forecast</h2>
            {forecast_html}
          </section>
          <section>
            <h2>Comparable Companies</h2>
            {comps_html}
          </section>
        </div>
        <h2>Precedent Transactions</h2>
        {precedents_html}
        <h2>Strategic Rationale</h2>
        <p>{precedents['rationale_summary']}</p>
        <h2>Risks and Diligence Focus</h2>
        <p>Key diligence areas include revenue durability, normalized margin profile, synergy credibility, integration risk, customer concentration, and sensitivity to valuation assumptions.</p>
      </main>
    </body>
    </html>
    """
