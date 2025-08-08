from utils.i18n import t


def test_fallback_error_translations():
    assert t('en', 'fallback_error')
    assert t('ru', 'fallback_error')


def test_notify_translations():
    for key in ["deposit_address", "notify_deposit", "notify_withdraw"]:
        assert t("en", key)
        assert t("ru", key)
