from decision import decide_action


def test_storm_triggers_free_payout():
    result = decide_action(rain_mm=80, aqi=450, predicted_income=207.3)
    assert result == {
        "action": "TRIGGER_PAYOUT",
        "loan_amount": 0,
        "sweep_amount": 0,
        "shortfall": 292.7,
    }


def test_rainy_shortfall_offers_loan():
    result = decide_action(rain_mm=45, aqi=250, predicted_income=483)
    assert result == {
        "action": "OFFER_LOAN",
        "loan_amount": 17,
        "sweep_amount": 0,
        "shortfall": 17,
    }


def test_clear_income_has_no_action():
    result = decide_action(rain_mm=5, aqi=120, predicted_income=814)
    assert result == {
        "action": "NONE",
        "loan_amount": 0,
        "sweep_amount": 0,
        "shortfall": 0,
    }


def test_high_income_sweeps_ten_percent():
    result = decide_action(rain_mm=5, aqi=120, predicted_income=1100)
    assert result == {
        "action": "NONE",
        "loan_amount": 0,
        "sweep_amount": 110,
        "shortfall": 0,
    }
