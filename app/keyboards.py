from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)


MAIN_BUTTONS = [
    ["💳 Hisob to‘ldirish", "🎮 UC sotib olish"],
    ["📦 Buyurtmalarim", "💎 UC narxlari"],
    ["🎁 Referal", "📚 Qo‘llanma"],
    ["🆘 Yordam", "👤 Profilim"],
    ["🏆 Reyting", "📞 Administrator"],
]


def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=x) for x in row]
            for row in MAIN_BUTTONS
        ],
        resize_keyboard=True,
        input_field_placeholder="LOTEX SHOP — bo‘limni tanlang"
    )


def packages_keyboard(packages):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{p.title} — {p.price_uzs:,} so‘m",
                    callback_data=f"buy:{p.id}"
                )
            ]
            for p in packages
        ]
    )
