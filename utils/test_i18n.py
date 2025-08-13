from utils.i18n import t


def test_fallback_error_translations():
    assert t('en', 'fallback_error')
    assert t('ru', 'fallback_error')


def test_notify_translations():
     placeholders = {
        "deposit_address": dict(amount=1, currency="TON", address="addr", label="lbl"),
        "notify_deposit": dict(amount=1, currency="TON", user_id=1),
        "notify_withdraw": dict(amount=1, currency="TON", user_id=1),
    }
    for key, kwargs in placeholders.items():
        assert t("en", key, **kwargs)
        assert t("ru", key, **kwargs)
