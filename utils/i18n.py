"""Telegram bot handlers package."""
MESSAGES = {
    "en": {
        "welcome": "Welcome to TONForge! Use /profile to view your profile.",
        "not_registered": "You are not registered. Use /start.",
        "profile": "TON balance: {ton}\nUSDT balance: {usdt}",
        "admin_panel": "Admin panel: {url}",
        "open_app": "Open app",
        "help": (
            "/start - register\n"
            "/profile - profile and balance\n"
            "/deposit <amount> <TON|USDT> - deposit funds\n"
            "/withdraw - withdraw funds\n"
            "/referrals - referral stats"
        ),
        "deposit_usage": "Usage: /deposit <amount> <TON|USDT>",
        "deposit_invalid_amount": "Invalid amount",
        "deposit_invalid_currency": "Currency must be TON or USDT",
        "deposit_success": "Deposit added successfully",
        "withdraw_min": "Minimum withdrawal amount is 50 TON or 50 USDT.",
        "withdraw_requested": (
            "Withdrawal request submitted. Please wait up to 24 hours."
        ),
        "referral_stats": (
            "Invited: {invited}\n"
            "TON bonus: {bonus_ton}\n"
            "USDT bonus: {bonus_usdt}"
        ),
    },
    "ru": {
        "welcome": "Добро пожаловать в TONForge! Используйте /profile для просмотра профиля.",
        "not_registered": "Вы не зарегистрированы. Используйте /start.",
        "profile": "Баланс TON: {ton}\nБаланс USDT: {usdt}",
        "admin_panel": "Админ-панель: {url}",
        "open_app": "Открыть приложение",
        "help": (
            "/start - регистрация\n"
            "/profile - профиль и баланс\n"
            "/deposit <сумма> <TON|USDT> - пополнить\n"
            "/withdraw - вывести средства\n"
            "/referrals - партнёрская статистика"
        ),
        "deposit_usage": "Использование: /deposit <сумма> <TON|USDT>",
        "deposit_invalid_amount": "Некорректная сумма",
        "deposit_invalid_currency": "Валюта должна быть TON или USDT",
        "deposit_success": "Депозит успешно добавлен",
        "withdraw_min": "Минимальная сумма для вывода 50 TON или 50 USDT.",
        "withdraw_requested": (
            "Заявка на вывод отправлена. Ожидайте обработки в течение 24 часов."
        ),
        "referral_stats": (
            "Приглашено: {invited}\n"
            "Бонус TON: {bonus_ton}\n"
            "Бонус USDT: {bonus_usdt}"
        ),
    },
}


def t(lang: str, key: str, **kwargs) -> str:
    """Return translated string by key for given language."""
    lang = lang if lang in MESSAGES else "en"
    template = MESSAGES.get(lang, {}).get(key, "")
    return template.format(**kwargs)
