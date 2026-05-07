import os
import difflib
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

from PyPDF2 import PdfReader

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)

from reportlab.lib.styles import getSampleStyleSheet

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

TOKEN = "8792686474:AAFmWTm7If7pDpHy0_8M3cJT1YvlyO5RZjI"

user_files = {}


def extract_text(pdf_path):
    text = ""

    reader = PdfReader(pdf_path)

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text


def create_pdf(diff_lines, output_file):

    pdfmetrics.registerFont(
        UnicodeCIDFont('HYSMyeongJo-Medium')
    )

    doc = SimpleDocTemplate(output_file)

    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph(
            "نتيجة مقارنة ملفات PDF",
            styles['Title']
        )
    )

    elements.append(Spacer(1, 20))

    for line in diff_lines:

        safe_line = (
            line.replace("<", "&lt;")
            .replace(">", "&gt;")
        )

        if line.startswith("+"):
            safe_line = f"<font color='green'>{safe_line}</font>"

        elif line.startswith("-"):
            safe_line = f"<font color='red'>{safe_line}</font>"

        elements.append(
            Paragraph(
                f"<font name='HYSMyeongJo-Medium'>{safe_line}</font>",
                styles['BodyText']
            )
        )

    doc.build(elements)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "ارسل الملف PDF الاول"
    )


async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id

    file = await update.message.document.get_file()

    file_name = f"{user_id}_{update.message.document.file_name}"

    await file.download_to_drive(file_name)

    if user_id not in user_files:

        user_files[user_id] = [file_name]

        await update.message.reply_text(
            "تم استلام الملف الاول، ارسل الملف الثاني"
        )

    else:

        user_files[user_id].append(file_name)

        pdf1 = user_files[user_id][0]
        pdf2 = user_files[user_id][1]

        text1 = extract_text(pdf1).splitlines()
        text2 = extract_text(pdf2).splitlines()

        diff = list(
            difflib.unified_diff(
                text1,
                text2,
                lineterm=''
            )
        )

        if not diff:
            diff = ["لا يوجد اختلاف"]

        output_pdf = f"{user_id}_differences.pdf"

        create_pdf(diff, output_pdf)

        with open(output_pdf, "rb") as pdf_file:

            await update.message.reply_document(
                document=pdf_file,
                filename="differences.pdf",
                caption="تم إنشاء ملف الاختلافات"
            )

        os.remove(pdf1)
        os.remove(pdf2)
        os.remove(output_pdf)

        del user_files[user_id]


app = Application.builder().token(TOKEN).build()

app.add_handler(
    CommandHandler("start", start)
)

app.add_handler(
    MessageHandler(
        filters.Document.PDF,
        handle_pdf
    )
)

print("Bot Running...")

app.run_polling()
