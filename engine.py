"""
Инженерный генератор ТЗ для Cursor, Claude и вайбкодинга.
Формирует кристально чистое ТЗ с блоком ограничений и .cursorrules.
"""

STACK_PRESETS = {
    "tg_bot": {
        "title": "🤖 Telegram Bot (Python / aiogram 3)",
        "tech": "Python 3.11+, aiogram 3.x, aiosqlite / SQLAlchemy, pydantic-settings",
        "rules": [
            "Использовать ТОЛЬКО aiogram версии 3.x (никаких aiogram 2.x, никаких Dispatcher(bot)).",
            "Все хэндлеры регистрировать через Router(), а не в одном общем файле main.py.",
            "Для хранения состояний FSM использовать StateFilter и явные стейты.",
            "Никаких синхронных time.sleep() или requests, только asyncio.sleep() и aiohttp.",
            "База данных асинхронная, транзакции должны всегда коммититься."
        ],
        "scaffold": "bot/\n├── handlers/\n│   ├── start.py\n│   └── menu.py\n├── keyboards/\n├── database.py\n├── config.py\n└── main.py"
    },
    "web_saas": {
        "title": "🚀 Web App / SaaS (Next.js 14/15, Tailwind, Supabase)",
        "tech": "Next.js 14+ (App Router), TypeScript, Tailwind CSS, Lucide-react, Supabase",
        "rules": [
            "Использовать исключительно App Router (папка app/), не создавать pages/.",
            "Все компоненты по умолчанию Server Components, директиву 'use client' ставить только там, где есть хуки (useState, useEffect, onClick).",
            "Не выносить мелкие вспомогательные утилиты в 10 разрозненных файлов без прямого запроса.",
            "Не оставлять заглушки 'TODO: implement logic here'. Код обязан быть рабочим с первой попытки.",
            "Стилизация только через utility-классы Tailwind. Дизайн: чистый современный dark/light режим с аккуратными скруглениями."
        ],
        "scaffold": "src/\n├── app/\n│   ├── layout.tsx\n│   ├── page.tsx\n│   └── api/\n├── components/\n├── lib/\n└── types/"
    },
    "fastapi_backend": {
        "title": "⚡ Micro-service / API (FastAPI, Docker)",
        "tech": "FastAPI, Python 3.11+, Pydantic v2, Uvicorn, Docker",
        "rules": [
            "Использовать Pydantic v2 (model_config, field_validator вместо устаревших v1 методов).",
            "Четкое разделение на routers, schemas, services, models.",
            "Все эндпоинты должны возвращать строго типизированные схемы response_model.",
            "Обработка ошибок через HTTPException с понятными статус-кодами и сообщениями.",
            "Готовый Dockerfile со сборкой multi-stage для минимального веса образа."
        ],
        "scaffold": "app/\n├── api/\n│   └── v1/\n├── schemas/\n├── services/\n├── config.py\n└── main.py"
    },
    "mobile_expo": {
        "title": "📱 Mobile App (React Native / Expo)",
        "tech": "React Native, Expo SDK 50+, TypeScript, Expo Router",
        "rules": [
            "Использовать Expo Router (файловая маршрутизация app/).",
            "Строгая типизация TypeScript, никаких 'any'.",
            "Не использовать устаревшие зависимости, не совместимые с новым Expo SDK.",
            "Использовать безопасные области Safe Area Context во всех экранах."
        ],
        "scaffold": "app/\n├── (tabs)/\n│   ├── index.tsx\n│   └── profile.tsx\n├── components/\n└── constants/"
    }
}

UNIVERSAL_NEGATIVE_CONSTRAINTS = [
    "❌ ЗАПРЕЩЕНО использовать устаревшие или deprecated методы библиотек.",
    "❌ ЗАПРЕЩЕНО дробить логику на 10 мелких абстрактных файлов без запроса (держи контекст в 1-2 сфокусированных файлах).",
    "❌ ЗАПРЕЩЕНО оставлять комментарии вроде '// TODO: implement later' или плейсхолдеры вместо готового кода.",
    "❌ ЗАПРЕЩЕНО генерировать выдуманные пакеты (проверять реальное существование импортов).",
    "✅ ОБЯЗАТЕЛЬНО: код должен компилироваться и запускаться с ПЕРВОЙ попытки."
]

def generate_specification(stack_key: str, raw_idea: str, constraints_mode: str = "strict") -> str:
    preset = STACK_PRESETS.get(stack_key, STACK_PRESETS["web_saas"])
    
    spec = []
    spec.append("═" * 38)
    spec.append(f"📋 ИНЖЕНЕРНОЕ ТЗ ДЛЯ CURSOR / CLAUDE")
    spec.append("═" * 38)
    spec.append("")
    spec.append(f"📌 **1. ЦЕЛЬ ПРОЕКТА:**")
    spec.append(f"{raw_idea.strip()}")
    spec.append("")
    spec.append(f"🛠️ **2. ТЕХНОЛОГИЧЕСКИЙ СТЕК:**")
    spec.append(f"• Направление: {preset['title']}")
    spec.append(f"• Стек: `{preset['tech']}`")
    spec.append("")
    spec.append("🛡️ **3. БЛОК ЖЕСТКИХ ОГРАНИЧЕНИЙ (NEGATIVE CONSTRAINTS):**")
    for neg in UNIVERSAL_NEGATIVE_CONSTRAINTS:
        spec.append(f"  {neg}")
    spec.append("")
    spec.append("⚙️ **4. СПЕЦИФИКАЦИЯ СТЕКА:**")
    for r in preset["rules"]:
        spec.append(f"  • {r}")
    spec.append("")
    spec.append("📂 **5. РЕКОМЕНДУЕМАЯ СТРУКТУРА ФАЙЛОВ:**")
    spec.append("```text")
    spec.append(preset["scaffold"])
    spec.append("```")
    spec.append("")
    spec.append("💬 **6. ГОТОВЫЙ СТАРТОВЫЙ ПРОМПТ (Скопируй в Cursor / Claude):**")
    spec.append("```markdown")
    spec.append(f"Ты — Senior Software Engineer. Твоя задача: реализовать проект согласно спецификации ниже.")
    spec.append(f"Стек: {preset['tech']}")
    spec.append(f"Суть задачи: {raw_idea.strip()}")
    spec.append(f"\nКРИТИЧЕСКИЕ ПРАВИЛА:")
    for neg in UNIVERSAL_NEGATIVE_CONSTRAINTS[:3]:
        spec.append(f"{neg}")
    spec.append(f"\nШаг 1: Создай базовую структуру файлов и конфигурацию проекта.")
    spec.append(f"Выведи только полный, рабочий код первого шага без пропусков.")
    spec.append("```")
    
    return "\n".join(spec)
