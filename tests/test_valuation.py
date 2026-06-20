from src.data import DEFAULT_COMPS, DEFAULT_COMPANY_PROFILE, DEFAULT_DCF_INPUTS, DEFAULT_MERGER_INPUTS, SAMPLE_TRANSACTIONS
from src.valuation import build_comps_summary, build_dcf_model, build_merger_model, build_precedent_summary


def test_dcf_outputs_positive_enterprise_value():
    result = build_dcf_model(DEFAULT_DCF_INPUTS)
    assert result["enterprise_value"] > 0
    assert result["equity_value"] > 0
    assert result["implied_share_price"] > 0
    assert len(result["forecast"]) == 5


def test_comps_summary_builds_range():
    result = build_comps_summary(DEFAULT_COMPS, DEFAULT_COMPANY_PROFILE)
    assert result["valuation_low"] < result["valuation_high"]
    assert "EV/EBITDA" in result["stats"].columns


def test_precedent_summary_builds_range():
    result = build_precedent_summary(SAMPLE_TRANSACTIONS, DEFAULT_COMPANY_PROFILE)
    assert result["median_ebitda_multiple"] > 0
    assert result["valuation_low"] < result["valuation_high"]


def test_merger_model_flags_outcome():
    result = build_merger_model(DEFAULT_MERGER_INPUTS)
    assert result["recommendation"] in {"Accretive", "Dilutive", "Neutral"}
    assert result["pro_forma_eps"] > 0
