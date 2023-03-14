import logging
from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes
#this is my config.py file which is in .gitignore so that people don't see my bot's token
from config import BOT_TOKEN
import re
import pandas as pd
"""
This is a bot that helps you track your expenditures.
It's a personal project but I hope it will eventually be hosted on a server and available to everybody. 
"""


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Soy un bot que te permite llevar registro de tus gastos.")


async def add_expenditure(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Descripción de la función
    """
    texto_mensaje = update.message.text
    match_precio = re.search(r"(\$\d+)", texto_mensaje)#busca donde aparece el precio
    precio = match_precio.group()[1:]
    precio = int(precio)
    descripcion = texto_mensaje[match_precio.span()[1]+1:]#dos lugares después del precio está la descripción
    fecha = update.message.date
    
    #diría de sacar esto y buscar en el texto del mensaje. Lo que sobra del hashtag y el precio es la descripcion 
    entidad_hashtag = update.message.parse_entities() #busca el hashtag que es un tipo especial en telegram
    tipo = list(entidad_hashtag.items())[0][1][1:] 
    
    #I want to implement this part with a database and not a .csv file
    df = pd.read_csv("gastos.csv")#find the expenditures file and add the new expenditure
    df.loc[len(df.index)] = [precio, tipo, descripcion, fecha]
    df.to_csv("gastos.csv", index=False)
    


if __name__ == '__main__':
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    start_handler = CommandHandler('start', start)
    expenditure_handler = MessageHandler(filters.TEXT & (~filters.COMMAND) & filters.Entity("hashtag"), add_expenditure)

    application.add_handler(start_handler)
    application.add_handler(expenditure_handler)
    
    application.run_polling()
