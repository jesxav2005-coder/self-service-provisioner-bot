from automation.ai_analysis import generate_report


def test_generate_report_contains_policy_summary():
    report = generate_report()
    assert "Policy engine analysis summary:" in report
    assert "- Allowed types:" in report
    assert "- Authorized users:" in report
    assert "Template analysis:" in report
