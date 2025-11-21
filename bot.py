import os
import subprocess
from git import Repo
from telegram.ext import Updater, CommandHandler

# ---- SETTING ----
TOKEN = "7667348960:AAFRluFJp6Oy0vBY6DVWSWh1M6L4bE6cmRM"
WORKDIR = "https://github.com/buruhkulit/xlku"

current_repo = None


# --- COMMAND: /setrepo ---
def set_repo(update, context):
    global current_repo
    url = " ".join(context.args)

    if not url:
        update.message.reply_text("❌ Kirim URL repo GitHub.\nContoh: /setrepo https://github.com/user/repo")
        return

    # Hapus repo lama
    if os.path.exists(WORKDIR):
        subprocess.call(["rm", "-rf", WORKDIR])

    try:
        update.message.reply_text("📥 Clone repository...")
        Repo.clone_from(url, WORKDIR)
        current_repo = url
        update.message.reply_text("✅ Repository berhasil di-clone!")
    except Exception as e:
        update.message.reply_text(f"❌ Error clone repo:\n{e}")


# --- COMMAND: /update ---
def update_repo(update, context):
    if not current_repo:
        update.message.reply_text("❌ Repo belum diset. Pakai /setrepo dulu.")
        return

    try:
        repo = Repo(WORKDIR)
        o = repo.remotes.origin
        o.pull()
        update.message.reply_text("🔄 Repo berhasil di-update!")
    except Exception as e:
        update.message.reply_text(f"❌ Error pulling repo:\n{e}")


# --- COMMAND: /run ---
def run_python(update, context):
    filename = " ".join(context.args)

    if not filename:
        update.message.reply_text("❌ Beri nama file.\nContoh: /run main.py")
        return

    filepath = os.path.join(WORKDIR, filename)
    if not os.path.exists(filepath):
        update.message.reply_text(f"❌ File '{filename}' tidak ditemukan di repo.")
        return

    try:
        update.message.reply_text(f"🚀 Menjalankan `{filename}`...")

        result = subprocess.check_output(
            ["python3", filepath], stderr=subprocess.STDOUT, text=True
        )

        update.message.reply_text(f"✅ Output:\n```\n{result}\n```", parse_mode="Markdown")
    except subprocess.CalledProcessError as e:
        update.message.reply_text(f"❌ Error saat menjalankan:\n```\n{e.output}\n```", parse_mode="Markdown")


# ---- START BOT ----
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("setrepo", set_repo))
    dp.add_handler(CommandHandler("update", update_repo))
    dp.add_handler(CommandHandler("run", run_python))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
