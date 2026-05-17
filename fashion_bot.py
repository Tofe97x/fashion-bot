import os
import logging
import httpx
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler
from datetime import datetime

BOT_TOKEN      = "8648262134:AAHN7ijGUaPTWpIclq3FeN01x-Z0eHCsE34"
OPENROUTER_KEY = "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"
MANAGER_ID     = 963733849

history = {}
orders  = []

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ══════════════════════════════════════════════
#  قائمة المنتجات — عدّليها حسب بيجك
# ══════════════════════════════════════════════
PRODUCTS = """
┌─────────────────────────────────────────┐
         قائمة منتجات البيج
└─────────────────────────────────────────┘

👗 فساتين:
• فستان سهرة كلوش — ألوان: أسود، أحمر، زيتي — مقاسات: S,M,L,XL — السعر: 95$
• فستان كاجوال قطن — ألوان: بيج، أبيض، وردي — مقاسات: S,M,L — السعر: 45$
• فستان ميدي فلوري — ألوان: أزرق، وردي، أخضر — مقاسات: S,M,L,XL — السعر: 65$
• فستان مناسبات ساتان — ألوان: شمبين، ذهبي، فضي — مقاسات: S,M,L — السعر: 120$
• فستان رياضي — ألوان: رصاصي، أسود — مقاسات: S,M,L,XL,XXL — السعر: 38$

🧕 عبايات:
• عباية كلاسيك — ألوان: أسود، كحلي، بني — مقاسات: 52,54,56,58,60 — السعر: 85$
• عباية فراشة مطرزة — ألوان: أسود، رمادي — مقاسات: 52,54,56,58 — السعر: 130$
• عباية كيمونو — ألوان: أسود، بيج، بردقان — مقاسات: 52,54,56,58,60 — السعر: 110$
• عباية دبل كريب — ألوان: أسود فقط — مقاسات: 52,54,56,58,60,62 — السعر: 95$

👚 بلوزات وتوبات:
• بلوزة شيفون — ألوان: أبيض، أسود، وردي فوشيا — مقاسات: S,M,L — السعر: 28$
• توب بيزيك — ألوان: كل الألوان الأساسية — مقاسات: S,M,L,XL — السعر: 18$
• بلوزة كورسيه — ألوان: أسود، أحمر، أبيض — مقاسات: S,M,L — السعر: 35$
• بلوزة كروشيه — ألوان: بيج، أبيض — مقاسات: S,M — السعر: 42$

👖 بناطيل وتنانير:
• بنطال كاروه واسع — ألوان: أسود×أبيض، بيج×بني — مقاسات: S,M,L,XL — السعر: 55$
• بنطال جينز هاي ويست — ألوان: أزرق، أسود، أبيض — مقاسات: 36,38,40,42,44 — السعر: 48$
• تنورة ميدي ساتان — ألوان: شمبين، وردي، أسود — مقاسات: S,M,L — السعر: 40$
• بنطال كتان مريح — ألوان: بيج، أبيض، أسود — مقاسات: S,M,L,XL,XXL — السعر: 35$

👘 طقم كاملة:
• طقم بدلة كلاسيك (جاكيت+بنطال) — ألوان: أسود، كريمي، رمادي — مقاسات: S,M,L,XL — السعر: 145$
• طقم شيفون (بلوزة+تنورة) — ألوان: وردي، أزرق سماوي — مقاسات: S,M,L — السعر: 85$
• طقم رياضي كاجوال — ألوان: رمادي، أسود، بيج — مقاسات: S,M,L,XL — السعر: 58$

📦 معلومات عامة:
• التوصيل: داخل المدينة 3$ — خارج المدينة 6$
• الدفع: كاش عند الاستلام أو تحويل بنكي
• الاستبدال: خلال 3 أيام من الاستلام (بدون استخدام)
• التوصيل: 2-4 أيام عمل
"""

SYSTEM_PROMPT = f"""
أنتِ مساعدة بيج ملابس نسائية راقية على تلغرام. اسمك "لمى" ✨
أسلوبك: أنثوي، ودود، ذوق عالي، إيموجي خفيف.
لغتك: عربي خليجي أنيق.
لا تذكري أنكِ بوت أو ذكاء اصطناعي أبداً.
خاطبي الزبونة بـ "حبيبتي" أو باسمها.

━━━ قائمة المنتجات الحالية ━━━
{PRODUCTS}

━━━ قواعد الرد ━━━
١- للأسئلة عن منتج موجود بالقائمة: ردّي بتفاصيله مباشرة (السعر، الألوان، المقاسات) بأسلوب مشوّق.
٢- إذا سألت عن منتج مو بالقائمة: قولي "هذا المنتج غير متوفر حالياً" واقترحي بديلاً مشابهاً.
٣- إذا أرادت الشراء: اجمعي (الاسم، القطعة، المقاس، اللون، توصيل/استلام، رقم الهاتف) واحدة واحدة بأسلوب ودود. بعد اكتمالها اكتبي: [ORDER_CONFIRMED] ثم ملخص الطلب.
٤- إذا سألت عن توفر لون/مقاس معين غير مذكور: اكتبي [CHECK_AVAILABILITY] ثم تفاصيل السؤال.
٥- للشكاوى أو الاستفسارات الخاصة: اكتبي [ESCALATE].
٦- قدّمي المنتجات بأسلوب يشجع على الشراء — صفي الجمال والأناقة.
"""

async def ask_ai(messages: list) -> str:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://fashion-page.com",
                "X-Title": "بيج ملابس نسائية"
            },
            json={
                "model": "anthropic/claude-sonnet-4-5",
                "max_tokens": 800,
                "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages
            }
        )
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()

async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_chat.id
    name = update.effective_user.first_name or "حبيبتي"
    text = update.message.text.strip()

    # رد المدير
    if uid == MANAGER_ID and text.startswith("رد:") and "|" in text:
        try:
            _, cid, reply = text.split("|", 2)
            await ctx.bot.send_message(int(cid), reply.strip())
            await update.message.reply_text("✅ تم إرسال ردك للزبونة")
        except:
            await update.message.reply_text("⚠️ الصيغة:\nرد:|معرف_الزبونة|ردك هنا")
        return

    if uid not in history:
        history[uid] = []
    history[uid].append({"role": "user", "content": text})

    try:
        reply = await ask_ai(history[uid][-14:])
    except Exception as e:
        logging.error(f"AI error: {e}")
        await update.message.reply_text("آسفة، حاولي مرة ثانية 🙏")
        return

    if "[ORDER_CONFIRMED]" in reply:
        clean = reply.replace("[ORDER_CONFIRMED]", "").strip()
        orders.append({"user": name, "uid": uid, "details": text, "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
        await ctx.bot.send_message(
            MANAGER_ID,
            f"🛍️ *طلب جديد!*\n\n👤 {name}\n📋 {text}\n⏰ {datetime.now().strftime('%H:%M')}\n\n`رد:|{uid}|ردك`",
            parse_mode="Markdown"
        )
        reply = clean if clean else "تم تسجيل طلبك حبيبتي ✅ سنتواصل معك قريباً 🌸"

    elif "[CHECK_AVAILABILITY]" in reply:
        item = reply.replace("[CHECK_AVAILABILITY]", "").strip()
        await ctx.bot.send_message(
            MANAGER_ID,
            f"🔍 *استعلام توفر*\n\n👤 {name}\n❓ {item or text}\n\n`رد:|{uid}|ردك`",
            parse_mode="Markdown"
        )
        reply = "سأتحقق لك الآن حبيبتي وأرد عليك خلال دقائق ✨"

    elif "[ESCALATE]" in reply:
        await ctx.bot.send_message(
            MANAGER_ID,
            f"🔺 *تحويل*\n\n👤 {name}\n💬 {text}\n\n`رد:|{uid}|ردك`",
            parse_mode="Markdown"
        )
        reply = "شكراً حبيبتي 🌸 سيتواصل معك فريقنا قريباً"

    history[uid].append({"role": "assistant", "content": reply})
    await update.message.reply_text(reply)

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name or "حبيبتي"
    await update.message.reply_text(
        f"أهلاً {name}! ✨\n\n"
        "أنا لمى، مساعدتك في بيج الملابس 👗\n\n"
        "عندنا اليوم:\n"
        "👗 فساتين سهرة وكاجوال\n"
        "🧕 عبايات راقية\n"
        "👚 بلوزات وتوبات\n"
        "👖 بناطيل وتنانير\n"
        "👘 طقم كاملة\n\n"
        "شو يعجبك اليوم؟ 😊"
    )

async def show_orders(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != MANAGER_ID:
        return
    if not orders:
        await update.message.reply_text("لا يوجد طلبات بعد.")
        return
    text = f"📋 *الطلبات ({len(orders)}):*\n\n"
    for i, o in enumerate(orders[-10:], 1):
        text += f"{i}. {o['user']} — {o['time']}\n"
    await update.message.reply_text(text, parse_mode="Markdown")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("orders", show_orders))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("👗 لمى تعمل الآن!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
