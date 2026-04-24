import os
import json
import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ADMIN_IDS = list(map(int, os.environ.get("ADMIN_CHAT_IDS", "").split(","))) if os.environ.get("ADMIN_CHAT_IDS") else []

USERS_FILE = "users.json"
TASKS_FILE = "tasks.json"

def load_json(file):
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_main_menu():
    keyboard = [
        [KeyboardButton("💰 Gəlir/Xərc Hesabatı"), KeyboardButton("📊 Aylıq Xülasə")],
        [KeyboardButton("📦 Gömrük Məlumatı"), KeyboardButton("✅ Tapşırıqlar")],
        [KeyboardButton("🤖 AI ilə Danış"), KeyboardButton("👤 Hesabım")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def normalize_voen(voen):
    return voen.replace("-", "").replace(" ", "").upper().strip()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    users = load_json(USERS_FILE)
    
    if user_id in users.get("approved", {}):
        name = update.effective_user.first_name
        await update.message.reply_text(
            f"👋 Xoş gəldiniz, {name}!\n\n"
            "🏢 AI VIP BROKER Ofis sisteminə daxil oldunuz.\n"
            "Aşağıdakı xidmətlərdən istifadə edə bilərsiniz:",
            reply_markup=get_main_menu()
        )
    elif user_id in users.get("pending", {}):
        await update.message.reply_text(
            "⏳ Qeydiyyatınız admin tərəfindən yoxlanılır.\n"
            "Təsdiqlənəndə bildiriş alacaqsınız."
        )
    else:
        context.user_data["registering"] = "voen"
        await update.message.reply_text(
            "👋 Salam! AI VIP BROKER botuna xoş gəldiniz.\n\n"
            "🔐 Botdan istifadə üçün qeydiyyatdan keçməlisiniz.\n\n"
            "Zəhmət olmasa şirkətinizin VOEN-ini yazın:"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = str(update.effective_user.id)
    users = load_json(USERS_FILE)
    
    # Registration flow
    if context.user_data.get("registering") == "voen":
        context.user_data["voen"] = normalize_voen(text)
        context.user_data["registering"] = "company"
        await update.message.reply_text("İndi şirkətinizin tam adını yazın:")
        return
    
    if context.user_data.get("registering") == "company":
        voen = context.user_data.get("voen")
        company = text
        context.user_data["registering"] = None
        
        approved = users.get("approved", {})
        
        if voen in [v.get("voen") for v in approved.values()]:
            if "pending" not in users:
                users["pending"] = {}
            users["pending"][user_id] = {"voen": voen, "company": company, "name": update.effective_user.first_name}
            save_json(USERS_FILE, users)
            
            for admin_id in ADMIN_IDS:
                try:
                    await context.bot.send_message(
                        admin_id,
                        f"🔔 Yeni qeydiyyat:\n"
                        f"Ad: {update.effective_user.first_name}\n"
                        f"VOEN: {voen}\n"
                        f"Şirkət: {company}\n\n"
                        f"Təsdiq: /adduser {voen} {company}\n"
                        f"Rədd: /removeuser {voen}"
                    )
                except:
                    pass
            
            await update.message.reply_text(
                f"✅ Qeydiyyat göndərildi!\n\n"
                f"VOEN: {voen}\n"
                f"Şirkət: {company}\n\n"
                "Admin tərəfindən yoxlanılır. Gözləyin..."
            )
        else:
            if "pending" not in users:
                users["pending"] = {}
            users["pending"][user_id] = {"voen": voen, "company": company, "name": update.effective_user.first_name}
            save_json(USERS_FILE, users)
            
            for admin_id in ADMIN_IDS:
                try:
                    await context.bot.send_message(
                        admin_id,
                        f"💰 Yeni ödənişli müştəri:\n"
                        f"Ad: {update.effective_user.first_name}\n"
                        f"VOEN: {voen}\n"
                        f"Şirkət: {company}\n\n"
                        f"Təsdiq üçün: /adduser {voen} {company}"
                    )
                except:
                    pass
            
            await update.message.reply_text(
                "🚫 Sizin VOEN-iniz təsdiqlənmiş istifadəçilər siyahısında deyil.\n\n"
                "💳 Bu botdan istifadə üçün aylıq abunəlik tələb olunur:\n"
                "• 12 AZN / ay\n\n"
                "Abunə olmaq üçün admin ilə əlaqə saxlayın.\n"
                "Ödənişdən sonra admin sizin VOEN-inizi sistemə əlavə edəcək."
            )
        return
    
    # Check if approved
    if user_id not in users.get("approved", {}):
        await update.message.reply_text(
            "🔐 Botdan istifadə üçün qeydiyyat lazımdır.\n"
            "/start yazın."
        )
        return
    
    # Menu handlers
    if text == "💰 Gəlir/Xərc Hesabatı":
        await update.message.reply_text(
            "💰 Bu Ay Maliyyə Hesabatı\n\n"
            "📈 Gəlir: ₼48,320\n"
            "📉 Xərc: ₼19,840\n"
            "✅ Mənfəət: ₼28,480\n\n"
            "📊 Ötən aya nisbət:\n"
            "• Gəlir: +12.4% ↑\n"
            "• Xərc: +3.1% ↑\n"
            "• Mənfəət: +18.2% ↑",
            reply_markup=get_main_menu()
        )
    
    elif text == "📊 Aylıq Xülasə":
        await update.message.reply_text(
            "📊 Aylıq İş Xülasəsi\n\n"
            "✅ Tamamlanan işlər: 142\n"
            "🔄 Davam edən: 8\n"
            "⚡ Effektivlik: 98.4%\n\n"
            f"📅 Tarix: {datetime.now().strftime('%d.%m.%Y')}",
            reply_markup=get_main_menu()
        )
    
    elif text == "📦 Gömrük Məlumatı":
        await update.message.reply_text(
            "📦 Gömrük Məlumatı\n\n"
            "🔍 Son yoxlamalar: 18 bəyannamə\n"
            "⚠️ Uyğunsuzluq: 3 hal\n"
            "✅ Təsdiqləndi: 15 bəyannamə\n\n"
            "🌐 Portal: customs.gov.az",
            reply_markup=get_main_menu()
        )
    
    elif text == "✅ Tapşırıqlar":
        tasks = load_json(TASKS_FILE)
        user_tasks = tasks.get(user_id, [])
        active = [t for t in user_tasks if not t.get("done")]
        
        if not active:
            msg = "✅ Aktiv tapşırıq yoxdur!\n\nYeni tapşırıq əlavə etmək üçün yazın:\n/addtask Tapşırığın mətni"
        else:
            msg = f"✅ Tapşırıqlar ({len(active)}):\n\n"
            for i, t in enumerate(active, 1):
                msg += f"{i}. {t['text']}\n"
            msg += "\nTamamlamaq üçün: /done 1"
        
        await update.message.reply_text(msg, reply_markup=get_main_menu())
    
    elif text == "🤖 AI ilə Danış":
        context.user_data["ai_mode"] = True
        await update.message.reply_text(
            "🤖 AI ilə söhbət rejimi açıldı!\n\n"
            "İstənilən sualınızı yazın.\n"
            "Çıxmaq üçün: /start",
            reply_markup=get_main_menu()
        )
    
    elif text == "👤 Hesabım":
        user_info = users["approved"].get(user_id, {})
        await update.message.reply_text(
            f"👤 Hesab məlumatları:\n\n"
            f"Ad: {update.effective_user.first_name}\n"
            f"VOEN: {user_info.get('voen', 'N/A')}\n"
            f"Şirkət: {user_info.get('company', 'N/A')}\n"
            f"Status: ✅ Aktiv",
            reply_markup=get_main_menu()
        )
    
    else:
        await update.message.reply_text(
            "Menüdən seçim edin 👆",
            reply_markup=get_main_menu()
        )

async def cmd_adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    if len(context.args) < 2:
        await update.message.reply_text("İstifadə: /adduser VOEN ŞirkətAdı")
        return
    
    voen = normalize_voen(context.args[0])
    company = " ".join(context.args[1:])
    users = load_json(USERS_FILE)
    
    if "approved" not in users:
        users["approved"] = {}
    
    # Find user in pending
    for uid, info in users.get("pending", {}).items():
        if normalize_voen(info.get("voen", "")) == voen:
            users["approved"][uid] = {"voen": voen, "company": company}
            del users["pending"][uid]
            save_json(USERS_FILE, users)
            
            try:
                await context.bot.send_message(uid, 
                    f"✅ Qeydiyyatınız təsdiqləndi!\n"
                    f"Şirkət: {company}\n\n"
                    "Botdan istifadə etmək üçün /start yazın.")
            except:
                pass
            
            await update.message.reply_text(f"✅ {company} ({voen}) əlavə edildi!")
            return
    
    users["approved"][f"manual_{voen}"] = {"voen": voen, "company": company}
    save_json(USERS_FILE, users)
    await update.message.reply_text(f"✅ {company} ({voen}) əlavə edildi!")

async def cmd_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    users = load_json(USERS_FILE)
    approved = users.get("approved", {})
    pending = users.get("pending", {})
    
    msg = f"👥 Təsdiqlənmiş: {len(approved)}\n"
    for uid, info in approved.items():
        msg += f"• {info.get('company')} ({info.get('voen')})\n"
    
    msg += f"\n⏳ Gözləyən: {len(pending)}\n"
    for uid, info in pending.items():
        msg += f"• {info.get('name')} - {info.get('company')} ({info.get('voen')})\n"
    
    await update.message.reply_text(msg)

async def cmd_myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Sizin ID: `{update.effective_user.id}`", parse_mode="Markdown")

async def cmd_addtask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("İstifadə: /addtask Tapşırığın mətni")
        return
    
    user_id = str(update.effective_user.id)
    tasks = load_json(TASKS_FILE)
    if user_id not in tasks:
        tasks[user_id] = []
    
    task_text = " ".join(context.args)
    tasks[user_id].append({"text": task_text, "done": False, "created": str(datetime.now())})
    save_json(TASKS_FILE, tasks)
    await update.message.reply_text(f"✅ Tapşırıq əlavə edildi: {task_text}", reply_markup=get_main_menu())

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("adduser", cmd_adduser))
    app.add_handler(CommandHandler("users", cmd_users))
    app.add_handler(CommandHandler("myid", cmd_myid))
    app.add_handler(CommandHandler("addtask", cmd_addtask))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ AI VIP BROKER botu işə düşdü!")
    app.run_polling()

if __name__ == "__main__":
    main()
