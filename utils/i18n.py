"""Telegram bot handlers package."""
MESSAGES = {
    "en": {
        "welcome": "Welcome to TONForge! Use /profile to view your profile.",
        "not_registered": "You are not registered. Use /start.",
        "profile": "TON balance: {ton}\nUSDT balance: {usdt}",
        "admin_panel": "Admin panel: {url}",
        "open_app": "Open app",
    },
    "ru": {
        "welcome": "Добро пожаловать в TONForge! Используйте /profile для просмотра профиля.",
        "not_registered": "Вы не зарегистрированы. Используйте /start.",
        "profile": "Баланс TON: {ton}\nБаланс USDT: {usdt}",
        "admin_panel": "Админ-панель: {url}",
        "open_app": "Открыть приложение",
    },
}


def t(lang: str, key: str, **kwargs) -> str:
    """Return translated string by key for given language."""
    lang = lang if lang in MESSAGES else "en"
    template = MESSAGES.get(lang, {}).get(key, "")
    return template.format(**kwargs)
