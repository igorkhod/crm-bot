1. Динамическое меню с изменяемыми кнопками


@bot.message_handler(commands=['dynamic'])
def dynamic_menu(message):
    markup = types.InlineKeyboardMarkup()

    # Кнопки генерируются динамически
    for i in range(1, 4):
        markup.add(types.InlineKeyboardButton(
            f"Вариант {i}",
            callback_data=f"option_{i}"
        ))

    bot.send_message(
        message.chat.id,
        "🔄 Меню с динамическими кнопками:",
        reply_markup=markup
    )
   -------------------------------------------------
2. Меню с эмодзи-анимацией


@bot.message_handler(commands=['emoji'])
def emoji_menu(message):
    markup = types.InlineKeyboardMarkup()

    buttons = [
        ("🌅 Утро", "morning"),
        ("🌇 Вечер", "evening"),
        ("🌃 Ночь", "night")
    ]

    for text, data in buttons:
        markup.add(types.InlineKeyboardButton(text, callback_data=data))

    bot.send_message(
        message.chat.id,
        "✨ Выберите время суток:",
        reply_markup=markup
    )
    ----------------------------------------
    3.Многоуровневое вложенное меню

    @bot.callback_query_handler(func=lambda call: call.data.startswith('menu_'))
    def handle_menu(call):
        if call.data == "menu_main":
            markup = types.InlineKeyboardMarkup()
            markup.row(
                types.InlineKeyboardButton("Настройки", callback_data="menu_settings"),
                types.InlineKeyboardButton("Помощь", callback_data="menu_help")
            )
            bot.edit_message_text(
                "Главное меню:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup
            )

        elif call.data == "menu_settings":
            markup = types.InlineKeyboardMarkup()
            markup.row(
                types.InlineKeyboardButton("🔙 Назад", callback_data="menu_main"),
                types.InlineKeyboardButton("Язык", callback_data="menu_lang")
            )
            bot.edit_message_text(
                "Настройки:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup
            )
            -------------------------------------------------
            4.Кнопки с web - предпросмотром


@bot.message_handler(commands=['preview'])
def preview_menu(message):
    markup = types.InlineKeyboardMarkup()

    btn = types.InlineKeyboardButton(
        "Открыть сайт с предпросмотром",
        url="https://example.com",
        callback_data="dont_click"  # Просто заглушка
    )

    markup.add(btn)
    bot.send_message(
        message.chat.id,
        "Сайт с красивым превью:",
        reply_markup=markup
    )
----------------------------------------
5. Мини-игра в меню


@bot.message_handler(commands=['game'])
def number_game(message):
    markup = types.InlineKeyboardMarkup()

    for i in range(1, 6):
        markup.add(types.InlineKeyboardButton(
            f"Кнопка {i}",
            callback_data=f"guess_{i}"
        ))

    bot.send_message(
        message.chat.id,
        "Угадай счастливую кнопку (1-5):",
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith('guess_'))
def check_guess(call):
    chosen = int(call.data.split('_')[1])
    if chosen == 3:  # Счастливая кнопка
        bot.answer_callback_query(call.id, "🎉 Вы угадали!", show_alert=True)
    else:
        bot.answer_callback_query(call.id, "Попробуйте ещё раз!")