# crm2/services/chatgpt_status.py
# Назначение модуля
# Модуль отвечает за проверку доступности платного сервиса ChatGPT в CRM-боте. Его задача — определить, «открыт» ли платный доступ (есть средства и сервис отвечает) или «закрыт» (средства закончились, квота исчерпана). Баланс в долларах не вычисляется, лишь бинарный результат.
# Что делает
# Проверяет наличие API-ключа в окружении.
# Выполняет минимальный пробный запрос к модели (1–3 токена).
# По результату/ошибке определяет состояние:
# 🟢 open — платный сервис открыт;
# 🔴 closed — платный сервис закрыт (insufficient_quota);
# 🟡 unknown — невозможно однозначно определить (неверный ключ, сетевые ошибки и т. п.).
# Возвращает словарь со статусом и вспомогательной информацией.
# Формирует читаемое сообщение в формате Markdown для вывода в чат.
# Расположение в проекте
# crm2/
#  └── services/
#       └── chatgpt_status.py   ← модуль диагностики ChatGPT
import os, time
from typing import Dict, Any, Literal

PaidState = Literal["open", "closed", "unknown"]

def _decide_state_from_error(msg: str) -> PaidState:
    m = msg.lower()
    # ключевые признаки "денег нет / квота исчерпана"
    if "insufficient_quota" in m or "billing_hard_limit_reached" in m or "account_deactivated" in m:
        return "closed"
    # типовые ошибки, при которых нельзя судить о балансе
    if any(x in m for x in ["invalid_api_key", "authentication", "api key not found"]):
        return "unknown"
    if any(x in m for x in ["rate_limit", "overloaded", "server error", "timeout", "connection"]):
        # сервис жив, но сейчас недоступен — считаем, что оплаченная зона существует
        return "open"
    return "unknown"
# IGOR_OPENAI_API=
def probe_paid_access() -> Dict[str, Any]:
    """
    Пробуем сделать МИНИ-комплишн (1–3 токена) на дешёвой модели.
    Условия:
      - если успех → 'open'
      - если ошибка 'insufficient_quota' → 'closed'
      - иное → 'unknown'
    """
    model = os.getenv("OPENAI_MODEL") or "gpt-4o-mini"
    info: Dict[str, Any] = {
        "IGOR_OPENAI_API_present": bool(os.getenv("IGOR_OPENAI_API")),
        "model": model,
        "api_ping_ms": "—",
        "state": "unknown",
        "last_error": "—",
        "note": "Проверка делает крошечный платный запрос (пара токенов).",
    }

    if not info["IGOR_OPENAI_API_present"]:
        info["last_error"] = "IGOR_OPENAI_API не найден"
        return info

    try:
        from openai import OpenAI
        client = OpenAI()
        start = time.monotonic()

        # ультра-дешёвый вызов
        _ = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "ok"}],
            max_tokens=1,
            temperature=0.0,
        )
        info["api_ping_ms"] = int((time.monotonic() - start) * 1000)
        info["state"] = "open"
        return info

    except Exception as e:
        msg = str(e)
        info["last_error"] = msg[:600]
        info["state"] = _decide_state_from_error(msg)
        return info

def render_binary_md(d: Dict[str, Any]) -> str:
    state = d["state"]
    if state == "open":
        head = "🟢 *Платный сервис: ОТКРЫТ*"
    elif state == "closed":
        # уточняем причину, если ошибка говорит о квоте
        note = d.get("last_error", "").lower()
        if "insufficient_quota" in note or "billing_hard_limit_reached" in note:
            head = "🔴 *Платный сервис: ЗАКРЫТ (баланс 0)*"
        else:
            head = "🔴 *Платный сервис: ЗАКРЫТ*"
    else:
        head = "🟡 *Платный сервис: НЕ ОПРЕДЕЛЁН*"

    lines = [
        head,
        f"• Модель: `{d.get('model', '—')}`",
        f"• Пинг: {d.get('api_ping_ms', '—')} ms",
    ]
    if d.get("last_error") and d["last_error"] != "—":
        lines.append(f"• Техн. примечание: `{d['last_error']}`")
    lines.append(f"_{d.get('note','')}_")
    return "\n".join(lines)
