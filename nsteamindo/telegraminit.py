import sys
import pickle

from telegram.ext import Updater, MessageHandler, Filters, CallbackContext
from telegram import Update


if len(sys.argv) > 2:
    print("Error: terlalu banyak argumen")
    exit(1)
elif len(sys.argv) < 2:
    print("Error: tidak ada token yang dimasukkan")
    exit(1)

TOKEN = sys.argv[1]


def on_message(update: Update, ctx: CallbackContext):
    with open("telegramdata", 'wb') as f:
        data = {
            "token": TOKEN,
            "chatid": update.effective_chat.id
        }
        pickle.dump(data, f)
    print("Info: Sukses")
    update.effective_chat.send_message("Inisialisasi Sukses")
    exit(0)


updater = Updater(TOKEN)
updater.dispatcher.add_handler(MessageHandler(Filters.text, on_message))
print("Silahkan kirimkan pesan teks ke bot anda di telegram")
updater.start_polling()
