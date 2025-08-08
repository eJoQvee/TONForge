from utils.i18n import t

def test_fallback_error_translations():
    assert t('en', 'fallback_error')
    assert t('ru', 'fallback_error')
