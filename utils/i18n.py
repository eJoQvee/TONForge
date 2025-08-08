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
            "/deposit &lt;amount&gt; &lt;TON|USDT&gt; - deposit funds\n"
            "/withdraw - withdraw funds\n"
            "/referrals - referral stats"
        ),
        "deposit_usage": "Usage: /deposit &lt;amount&gt; &lt;TON|USDT&gt;",
        "deposit_invalid_amount": "Invalid amount",
        "deposit_invalid_currency": "Currency must be TON or USDT",
        "deposit_min": "Minimum deposit is {min_deposit} TON or {min_deposit} USDT.",
        "deposit_success": "Deposit added successfully",
        "deposit_address": (
            "Please transfer {amount} {currency} to {address} with comment {label}."
        ),
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
        "fallback_error": "An unexpected error occurred. Please try again later.",
        "notify_deposit": "New deposit: {amount} {currency} from user {user_id}",
        "notify_withdraw": "Withdrawal requested: {amount} {currency} from user {user_id}",
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
            "/deposit &lt;сумма&gt; &lt;TON|USDT&gt; - пополнить\n"
            "/withdraw - вывести средства\n"
            "/referrals - партнёрская статистика"
        ),
        "deposit_usage": "Использование: /deposit &lt;сумма&gt; &lt;TON|USDT&gt;",,
        "deposit_invalid_amount": "Некорректная сумма",
        "deposit_invalid_currency": "Валюта должна быть TON или USDT",
        "deposit_min": "Минимальный депозит {min_deposit} TON или {min_deposit} USDT.",
        "deposit_success": "Депозит успешно добавлен",
        "deposit_address": (
            "Переведите {amount} {currency} на {address} с комментарием {label}."
        ),
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
        "fallback_error": "Произошла неожиданная ошибка. Пожалуйста, попробуйте позже.",
        "notify_deposit": "Новый депозит: {amount} {currency} от пользователя {user_id}",
        "notify_withdraw": "Запрошен вывод: {amount} {currency} от пользователя {user_id}",
    },
}


def t(lang: str, key: str, **kwargs) -> str:
    """Return translated string by key for given language."""
    lang = lang if lang in MESSAGES else "en"
    template = MESSAGES.get(lang, {}).get(key, "")
    return template.format(**kwargs)
