# crm2/handlers/admin/broadcast.py
# Назначение: Обработчики админ-панели для массовой рассылки сообщений пользователям
# Классы:
# - BroadcastFSM - FSM состояния для создания рассылки (audience, cohort, text, attach, confirm)
# Функции:
# - audience_kb - Клавиатура выбора аудитории рассылки
# - cohorts_kb - Клавиатура выбора когорты для рассылки
# - confirm_kb - Клавиатура подтверждения рассылки
# - preview - Предпросмотр рассылки перед отправкой
# Обработчики:
# - start_broadcast - Начало создания рассылки
# - choose_audience - Выбор аудитории (всем или по когорте)
# - set_cohort - Установка когорты для рассылки
# - set_text - Получение текста рассылки
# - no_attach - Подтверждение отсутствия файла
# - with_attach - Обработка прикрепленного файла
# - back_to_text - Возврат к редактированию текста
# - do_send - Выполнение рассылки с троттлингом
# - cancel_bc - Отмена рассылки
# - back_bc - Возврат к выбору аудитории
from __future__ import annotations
import asyncio, json, math
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
                           ReplyKeyboardRemove)
from crm2.db.core import get_db_connection

router = Router()

class BroadcastFSM(StatesGroup):
    audience = State()
    cohort   = State()
    text     = State()
    attach   = State()
    confirm  = State()

def audience_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Всем", callback_data="bc:a:all"),
         InlineKeyboardButton(text="К потоку…", callback_data="bc:a:cohort")],
        [InlineKeyboardButton(text="Отмена", callback_data="bc:cancel")]
    ])

def cohorts_kb():
    with get_db_connection() as con:
        rows = con.execute("SELECT id, name FROM cohorts ORDER BY id").fetchall()
    buttons = [[InlineKeyboardButton(text=r[1], callback_data=f"bc:c:{r[0]}")] for r in rows] or \
              [[InlineKeyboardButton(text="Без потоков", callback_data="bc:c:null")]]
    buttons.append([InlineKeyboardButton(text="Назад", callback_data="bc:back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def confirm_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Отправить", callback_data="bc:send"),
         InlineKeyboardButton(text="✏️ Править текст", callback_data="bc:edit")],
        [InlineKeyboardButton(text="Отмена", callback_data="bc:cancel")]
    ])

@router.callback_query(F.data == "adm:broadcast")
async def start_broadcast(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(BroadcastFSM.audience)
    await cb.message.answer("Выберите аудиторию:", reply_markup=audience_kb())
    await cb.answer()

@router.callback_query(BroadcastFSM.audience, F.data.startswith("bc:a:"))
async def choose_audience(cb: CallbackQuery, state: FSMContext):
    k = cb.data.split(":")[-1]
    if k == "all":
        await state.update_data(audience="all", cohort_id=None)
        await state.set_state(BroadcastFSM.text)
        await cb.message.answer("Введите текст рассылки (Markdown разрешён):", reply_markup=ReplyKeyboardRemove())
    elif k == "cohort":
        await state.update_data(audience="cohort")
        await state.set_state(BroadcastFSM.cohort)
        await cb.message.answer("Выберите поток:", reply_markup=cohorts_kb())
    await cb.answer()

@router.callback_query(BroadcastFSM.cohort, F.data.startswith("bc:c:"))
async def set_cohort(cb: CallbackQuery, state: FSMContext):
    val = cb.data.split(":")[-1]
    cohort_id = None if val == "null" else int(val)
    await state.update_data(cohort_id=cohort_id)
    await state.set_state(BroadcastFSM.text)
    await cb.message.answer("Введите текст рассылки (Markdown разрешён):", reply_markup=ReplyKeyboardRemove())
    await cb.answer()

@router.message(BroadcastFSM.text)
async def set_text(msg: Message, state: FSMContext):
    await state.update_data(body=msg.text or "")
    await state.set_state(BroadcastFSM.attach)
    await msg.answer("Пришлите файл (документ/фото/видео) *или* напишите «без файла».", parse_mode="Markdown")

@router.message(BroadcastFSM.attach, F.text.casefold() == "без файла")
async def no_attach(msg: Message, state: FSMContext):
    await state.update_data(attachment_file_id=None, attachment_mime=None)
    await state.set_state(BroadcastFSM.confirm)
    await preview(msg, state)

@router.message(BroadcastFSM.attach, F.content_type.in_({"document","photo","video","audio"}))
async def with_attach(msg: Message, state: FSMContext):
    file_id = mime = None
    if msg.document:
        file_id, mime = msg.document.file_id, msg.document.mime_type
    elif msg.photo:
        file_id, mime = msg.photo[-1].file_id, "image/jpeg"
    elif msg.video:
        file_id, mime = msg.video.file_id, "video/mp4"
    elif msg.audio:
        file_id, mime = msg.audio.file_id, "audio/mpeg"
    await state.update_data(attachment_file_id=file_id, attachment_mime=mime)
    await state.set_state(BroadcastFSM.confirm)
    await preview(msg, state)

async def preview(msg: Message, state: FSMContext):
    data = await state.get_data()
    aud = "Всем" if data.get("audience") == "all" else f"Поток id={data.get('cohort_id')}"
    att = "с файлом" if data.get("attachment_file_id") else "без файла"
    await msg.answer(f"Предпросмотр:\n— Аудитория: {aud}\n— Рассылка: {att}\n\nТекст:\n{data.get('body')}",
                     reply_markup=confirm_kb())

@router.callback_query(BroadcastFSM.confirm, F.data == "bc:edit")
async def back_to_text(cb: CallbackQuery, state: FSMContext):
    await state.set_state(BroadcastFSM.text)
    await cb.message.answer("Введите текст заново:")
    await cb.answer()

@router.callback_query(BroadcastFSM.confirm, F.data == "bc:send")
async def do_send(cb: CallbackQuery, state: FSMContext):
    from aiogram import Bot
    bot: Bot = cb.bot
    data = await state.get_data()
    audience, cohort_id = data["audience"], data.get("cohort_id")
    body = data.get("body") or ""
    file_id, mime = data.get("attachment_file_id"), data.get("attachment_mime")
    admin_tg = cb.from_user.id

    # 1) создаём запись рассылки
    with get_db_connection() as con:
        cur = con.cursor()
        cur.execute("""
          INSERT INTO broadcasts(title, body, attachment_file_id, attachment_mime, audience, cohort_id, created_by)
          VALUES(?,?,?,?,?,?,?)
        """, ("Рассылка", body, file_id, mime, audience, cohort_id, admin_tg))
        bc_id = cur.lastrowid

        # 2) получатели
        if audience == "all":
            users = con.execute("SELECT telegram_id FROM users WHERE telegram_id IS NOT NULL").fetchall()
        else:
            users = con.execute("""
               SELECT u.telegram_id
               FROM users u
               WHERE (u.cohort_id IS ? OR u.cohort_id = ?) AND u.telegram_id IS NOT NULL
            """, (None if cohort_id is None else None, cohort_id)).fetchall()
        users = [u[0] for u in users]
        cur.executemany("INSERT OR IGNORE INTO broadcast_recipients(broadcast_id, user_id) VALUES(?,?)",
                        [(bc_id, uid) for uid in users])
        con.commit()

    total = len(users)
    if total == 0:
        await cb.message.answer("Получателей нет.")
        await cb.answer(); return

    await cb.message.answer(f"Отправляю ({total} получателей)… Это может занять немного времени.")

    # 3) отправка (мягкий троттлинг)
    sent = failed = 0
    for i, uid in enumerate(users, 1):
        try:
            if file_id:
                if mime and mime.startswith("image/"):
                    await bot.send_photo(uid, file_id, caption=body)
                elif mime and mime.startswith("video/"):
                    await bot.send_video(uid, file_id, caption=body)
                elif mime and (mime.startswith("audio/") or mime == "audio/mpeg"):
                    await bot.send_audio(uid, file_id, caption=body)
                else:
                    await bot.send_document(uid, file_id, caption=body)
            else:
                await bot.send_message(uid, body)
            status, err = "sent", None
            sent += 1
        except Exception as e:
            status, err = "failed", str(e)[:300]
            failed += 1

        # записываем статус
        with get_db_connection() as con:
            con.execute("""
              UPDATE broadcast_recipients
              SET status=?, error=?, sent_at=CURRENT_TIMESTAMP
              WHERE broadcast_id=? AND user_id=?
            """, (status, err, bc_id, uid))
            con.commit()

        # троттлинг: ~20/сек (0.05с)
        if i % 20 == 0:
            await asyncio.sleep(1.0)
        else:
            await asyncio.sleep(0.05)

    # 4) финал
    stats = {"total": total, "sent": sent, "failed": failed}
    with get_db_connection() as con:
        con.execute("""
          UPDATE broadcasts
          SET status='done', sent_at=CURRENT_TIMESTAMP, stats_json=?
          WHERE id=?
        """, (json.dumps(stats, ensure_ascii=False), bc_id))
        con.commit()

    await cb.message.answer(f"Готово. Отправлено: {sent}/{total}. Ошибок: {failed}.")
    await state.clear()
    await cb.answer()

@router.callback_query(F.data == "bc:cancel")
async def cancel_bc(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.answer("Рассылка отменена.", reply_markup=None)
    await cb.answer()

@router.callback_query(F.data == "bc:back")
async def back_bc(cb: CallbackQuery, state: FSMContext):
    await state.set_state(BroadcastFSM.audience)
    await cb.message.answer("Выберите аудиторию:", reply_markup=audience_kb())
    await cb.answer()
