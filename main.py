
import random
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# قاموس لتتبع عدد مرات الفوز لكل اسم
winners = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""
اهلا بك!
ارسل الأسماء مفصولة بمسافات
مثال: محمد أحمد علي عمر
    
استخدم /stats لعرض إحصائيات الفائزين
""")

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not winners:
        await update.message.reply_text("لا يوجد فائزين حتى الآن")
        return
    
    stats = "\n".join([f"{name}: {count} مرة" for name, count in sorted(winners.items(), key=lambda x: x[1], reverse=True)])
    await update.message.reply_text(f"إحصائيات الفائزين:\n\n{stats}")

def get_replay_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🔄 إعادة السحب", callback_data='replay'),
            InlineKeyboardButton("✨ بدء لعبة جديدة", callback_data='new_game')
        ],
        [
            InlineKeyboardButton("👑 عرض الفائزين", callback_data='show_winners')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'replay':
        # إعادة السحب بنفس الأسماء
        names = context.user_data.get('current_names', [])
        if names:
            await spin_wheel_with_names(names, update.callback_query.message)
    elif query.data == 'new_game':
        # حذف البيانات السابقة
        context.user_data.clear()
        winners.clear()
        await query.message.reply_text("تم بدء لعبة جديدة. أرسل الأسماء للبدء!")
    elif query.data == 'show_winners':
        if not winners:
            await query.message.reply_text("لا يوجد فائزين حتى الآن")
            return
        stats = "\n".join([f"{name}: {count} مرة" for name, count in sorted(winners.items(), key=lambda x: x[1], reverse=True)])
        await query.message.reply_text(f"📊 إحصائيات الفائزين:\n\n{stats}")

async def spin_wheel_with_names(names, message):
    msg = await message.reply_text("جاري الاختيار...")
    
    # دوران لمدة أطول
    for _ in range(8):
        try:
            current_name = random.choice(names)
            await msg.edit_text(f"🎲 جاري الاختيار...\n{current_name}")
            await asyncio.sleep(0.7)
        except Exception:
            continue
    
    chosen_name = random.choice(names)
    winners[chosen_name] = winners.get(chosen_name, 0) + 1
    
    winner_message = (
        f"🌟 *النتيجة النهائية* 🌟\n\n"
        f"🎯 *الفائز هو:* `{chosen_name}`\n"
        f"🏆 *عدد مرات الفوز:* `{winners[chosen_name]}`"
    )
    try:
        await msg.edit_text(
            winner_message,
            reply_markup=get_replay_keyboard(),
            parse_mode='Markdown'
        )
    except Exception:
        await message.reply_text(
            winner_message,
            reply_markup=get_replay_keyboard(),
            parse_mode='Markdown'
        )

async def spin_wheel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    names = update.message.text.split()
    if not names:
        await update.message.reply_text("الرجاء إدخال أسماء للاختيار من بينها!")
        return
    
    # حفظ الأسماء للاستخدام لاحقاً
    context.user_data['current_names'] = names
    await spin_wheel_with_names(names, update.message)

def main():
    application = Application.builder().token("7600264808:AAG2eMehDeiYYSBbFCYtlKse1cpGZdZtErg").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", show_stats))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, spin_wheel))
    application.add_handler(CallbackQueryHandler(button_callback))

    from flask import Flask
    from threading import Thread

    web_app = Flask(__name__)

    @web_app.route('/')
    def home():
        return "Bot is running!"

    def run():
        web_app.run(host='0.0.0.0', port=8080)

    Thread(target=run).start()
    
    application.run_polling()

if __name__ == "__main__":
    main()
