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
        "deposit_min": "Minimum deposit is {min_deposit} TON or {min_deposit} USDT.",
        "deposit_success": "Deposit added successfully",
        "withdraw_min": "Minimum withdrawal amount is {min_withdraw} TON or {min_withdraw} USDT.",
        "withdraw_requested": (
            "Withdrawal request submitted. Please wait up to {hours} hours."
        ),
        "withdraw_pending": (
            "You already have a pending withdrawal. Please wait until it is processed."
        ),
        "referral_stats": (
            "Invited: {invited}\n"
            "TON bonus: {bonus_ton}\n"
            "USDT bonus: {bonus_usdt}"
        ),
        "blocked": "Your account is blocked.",
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
        "deposit_min": "Минимальный депозит {min_deposit} TON или {min_deposit} USDT.",
        "deposit_success": "Депозит успешно добавлен",
        "withdraw_min": "Минимальная сумма для вывода {min_withdraw} TON или {min_withdraw} USDT.",
        "withdraw_requested": (
            "Заявка на вывод отправлена. Ожидайте обработки в течение {hours} часов."
        ),
         "withdraw_pending": (
            "У вас уже есть заявка на вывод. Пожалуйста, дождитесь её обработки."
        ),
        "referral_stats": (
            "Приглашено: {invited}\n"
            "Бонус TON: {bonus_ton}\n"
            "Бонус USDT: {bonus_usdt}"
        ),
        "blocked": "Ваш аккаунт заблокирован.",
    },
}


def t(lang: str, key: str, **kwargs) -> str:
    """Return translated string by key for given language."""
    lang = lang if lang in MESSAGES else "en"
    template = MESSAGES.get(lang, {}).get(key, "")
    return template.format(**kwargs)
