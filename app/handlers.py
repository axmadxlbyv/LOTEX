from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from sqlalchemy import select

from app.config import settings
from app.db.session import Session
from app.db.models import User, UCPackage, Order
from app.keyboards import main_menu, packages_keyboard


router = Router()


class Purchase(StatesGroup):
    player_id = State()


class AddPackage(StatesGroup):
    title = State()
    amount = State()
    price = State()


def is_admin(user_id: int) -> bool:
    return user_id in settings.admins


# /start — botni boshlash
@router.message(CommandStart())
async def start(message: Message):

    async with Session() as session:
        user = await session.get(User, message.from_user.id)

        if not user:
            session.add(
                User(
                    id=message.from_user.id,
                    username=message.from_user.username,
                    full_name=message.from_user.full_name or ""
                )
            )
            await session.commit()

    await message.answer(
        "💎 <b>LOTEX SHOP</b> ga xush kelibsiz!\n\n"
        "PUBG Mobile UC buyurtmangizni shu yerdan yuborishingiz mumkin.",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )


# UC paketlarini ko‘rsatish
@router.message(F.text == "🎮 UC sotib olish")
@router.message(F.text == "💎 UC narxlari")
async def show_packages(message: Message):

    async with Session() as session:
        packages = (
            await session.scalars(
                select(UCPackage)
                .where(UCPackage.is_active == True)
                .order_by(UCPackage.uc_amount)
            )
        ).all()

    if not packages:
        await message.answer(
            "⏳ Hozircha UC paketlari kiritilmagan. "
            "Admin tez orada qo‘shadi."
        )
        return

    await message.answer(
        "💎 Kerakli UC paketini tanlang:",
        reply_markup=packages_keyboard(packages)
    )


# Paket tanlash
@router.callback_query(F.data.startswith("buy:"))
async def choose_package(
    callback: CallbackQuery,
    state: FSMContext
):

    package_id = int(callback.data.split(":")[1])

    async with Session() as session:
        package = await session.get(UCPackage, package_id)

        if not package or not package.is_active:
            await callback.answer(
                "Bu paket hozir mavjud emas.",
                show_alert=True
            )
            return

    await state.update_data(package_id=package_id)
    await state.set_state(Purchase.player_id)

    await callback.message.answer(
        "🎮 PUBG Mobile Player ID raqamingizni yuboring:"
    )

    await callback.answer()


# Player ID qabul qilish
@router.message(Purchase.player_id)
async def receive_player_id(
    message: Message,
    state: FSMContext
):

    player_id = (message.text or "").strip()

    if not player_id.isdigit() or not 5 <= len(player_id) <= 20:
        await message.answer(
            "Player ID faqat raqamlardan iborat bo‘lishi kerak. "
            "Qayta yuboring:"
        )
        return

    data = await state.get_data()

    async with Session() as session:

        package = await session.get(
            UCPackage,
            data["package_id"]
        )

        if not package or not package.is_active:
            await state.clear()
            await message.answer(
                "Paket endi mavjud emas. Menyudan qayta tanlang."
            )
            return

        order = Order(
            user_id=message.from_user.id,
            package_id=package.id,
            game_player_id=player_id,
            status="pending"
        )

        session.add(order)
        await session.commit()

        order_id = order.id

        package_title = package.title
        package_price = package.price_uzs

    await state.clear()

    await message.answer(
        f"✅ Buyurtma so‘rovingiz qabul qilindi!\n\n"
        f"🧾 Buyurtma: #{order_id}\n"
        f"🎮 Player ID: {player_id}\n"
        f"💎 Paket: {package_title}\n"
        f"💰 Narx: {package_price:,} so‘m\n\n"
        "To‘lov va UC yetkazib berish bo‘yicha "
        "administrator siz bilan bog‘lanadi."
    )

    for admin_id in settings.admins:
        try:
            await message.bot.send_message(
                admin_id,
                f"🆕 <b>Yangi UC so‘rovi</b>\n\n"
                f"Buyurtma: #{order_id}\n"
                f"Foydalanuvchi ID: {message.from_user.id}\n"
                f"Player ID: {player_id}\n"
                f"Paket: {package_title}\n"
                f"Narx: {package_price:,} so‘m",
                parse_mode="HTML"
            )
        except Exception:
            pass


# Mening buyurtmalarim
@router.message(F.text == "📦 Buyurtmalarim")
async def my_orders(message: Message):

    async with Session() as session:
        rows = (
            await session.execute(
                select(Order, UCPackage)
                .join(
                    UCPackage,
                    Order.package_id == UCPackage.id
                )
                .where(Order.user_id == message.from_user.id)
                .order_by(Order.id.desc())
                .limit(10)
            )
        ).all()

    if not rows:
        await message.answer(
            "📦 Sizda hozircha buyurtmalar yo‘q."
        )
        return

    lines = ["📦 <b>Oxirgi buyurtmalaringiz:</b>"]

    for order, package in rows:
        lines.append(
            f"#{order.id} — {package.title} — {order.status}"
        )

    await message.answer(
        "\n".join(lines),
        parse_mode="HTML"
    )


# Profil
@router.message(F.text == "👤 Profilim")
async def profile(message: Message):

    await message.answer(
        f"👤 Telegram ID: <code>{message.from_user.id}</code>\n"
        f"Ism: {message.from_user.full_name}",
        parse_mode="HTML"
    )


# Yordam va administrator
@router.message(F.text == "📞 Administrator")
@router.message(F.text == "🆘 Yordam")
async def help_user(message: Message):

    await message.answer(
        "🆘 Yordam olish uchun administratorga murojaat qiling."
    )


# Qo‘llanma
@router.message(F.text == "📚 Qo‘llanma")
async def guide(message: Message):

    await message.answer(
        "📚 Qo‘llanmalar hozircha admin tomonidan kiritilmagan."
    )


# Referal
@router.message(F.text == "🎁 Referal")
async def referral(message: Message):

    me = await message.bot.get_me()

    await message.answer(
        "🎁 Do‘stlaringizni taklif qiling:\n\n"
        f"https://t.me/{me.username}?start={message.from_user.id}"
    )


# Reyting
@router.message(F.text == "🏆 Reyting")
async def rating(message: Message):

    await message.answer(
        "🏆 Reyting bo‘limi keyingi versiyada ishga tushadi."
    )


# Hisob to‘ldirish
@router.message(F.text == "💳 Hisob to‘ldirish")
async def balance(message: Message):

    await message.answer(
        "💳 To‘lov usullari keyingi bosqichda ulanadi."
    )


# ADMIN PANEL
@router.message(F.text == "/admin")
async def admin_panel(message: Message):

    if not is_admin(message.from_user.id):
        await message.answer("⛔ Sizda admin huquqi yo‘q.")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ UC paket qo‘shish",
                    callback_data="admin:add_package"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 Paketlarni ko‘rish",
                    callback_data="admin:packages"
                )
            ]
        ]
    )

    await message.answer(
        "⚙️ <b>LOTEX SHOP — Admin panel</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


# Admin paketlarni ko‘rishi
@router.callback_query(F.data == "admin:packages")
async def admin_packages(callback: CallbackQuery):

    if not is_admin(callback.from_user.id):
        await callback.answer(
            "Ruxsat yo‘q",
            show_alert=True
        )
        return

    async with Session() as session:
        packages = (
            await session.scalars(
                select(UCPackage).order_by(UCPackage.id)
            )
        ).all()

    if not packages:
        await callback.message.answer(
            "Paketlar hali kiritilmagan."
        )
    else:
        text = "\n".join(
            f"#{p.id} {p.title}: "
            f"{p.uc_amount} UC / {p.price_uzs:,} so‘m"
            for p in packages
        )

        await callback.message.answer(text)

    await callback.answer()


# Yangi paket qo‘shish
@router.callback_query(F.data == "admin:add_package")
async def add_package_start(
    callback: CallbackQuery,
    state: FSMContext
):

    if not is_admin(callback.from_user.id):
        await callback.answer(
            "Ruxsat yo‘q",
            show_alert=True
        )
        return

    await state.set_state(AddPackage.title)

    await callback.message.answer(
        "Paket nomini yuboring. Masalan: 60 UC"
    )

    await callback.answer()


@router.message(AddPackage.title)
async def add_title(
    message: Message,
    state: FSMContext
):

    if not is_admin(message.from_user.id):
        return

    title = (message.text or "").strip()

    if not title:
        await message.answer("Paket nomini yuboring.")
        return

    await state.update_data(title=title[:80])
    await state.set_state(AddPackage.amount)

    await message.answer(
        "UC miqdorini faqat raqamda yuboring:"
    )


@router.message(AddPackage.amount)
async def add_amount(
    message: Message,
    state: FSMContext
):

    if not is_admin(message.from_user.id):
        return

    value = (message.text or "").strip()

    if not value.isdigit() or int(value) <= 0:
        await message.answer(
            "Musbat butun son yuboring:"
        )
        return

    await state.update_data(amount=int(value))
    await state.set_state(AddPackage.price)

    await message.answer(
        "Narxni so‘mda yuboring (faqat raqam):"
    )


@router.message(AddPackage.price)
async def add_price(
    message: Message,
    state: FSMContext
):

    if not is_admin(message.from_user.id):
        return

    value = (message.text or "").strip()

    if not value.isdigit() or int(value) <= 0:
        await message.answer(
            "Musbat butun son yuboring:"
        )
        return

    data = await state.get_data()

    async with Session() as session:
        package = UCPackage(
            title=data["title"],
            uc_amount=data["amount"],
            price_uzs=int(value),
            is_active=True
        )

        session.add(package)
        await session.commit()

    await state.clear()

    await message.answer(
        "✅ UC paketi muvaffaqiyatli qo‘shildi!"
    )
