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
    welcome_text="I help you keep track of your expenses."
    await context.bot.send_message(chat_id=update.effective_chat.id, text=welcome_text)


async def add_expenditure(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """This function receives the update from the handler (which should've 
    filtered for text messages with a hashtag entity) and gets the 
    information about the expenditure. Finally it adds that information
    to a csv file (WIP: use a database).
    """
    expenditure_data = context.args
    price = float("NaN")
    category = ""
    description = ""
    for data in expenditure_data:
        if data.startswith("$"):
            price = int(data[1:])
        elif data.startswith("#"):
            category = data[1:]
        else:
            description += " "+data
    description = description.strip()        
    #match_price = re.search(r"(\$\d+)", text)#find the price
    #price = match_price.group()[1:]
    #price = int(price)
    
    #description = text[match_price.end():]+text[:match_price.start()]#remove price from string
    #match_category = re.search(r"(\#\w+)", description) #find the category
    #category = match_category.group()[1:]

    #description = description[match_category.end():]+description[:match_category.start()] #remove category from description
    #description = description.strip()

    date = update.message.date#find date
    
    #I want to implement this part with a database and not a .csv file
    df = pd.read_csv("gastos.csv")#find the expenditures file and add the new expenditure
    df.loc[len(df.index)] = [price, category, description, date]
    df.to_csv("gastos.csv", index=False)
    

if __name__ == '__main__':
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    start_handler = CommandHandler('start', start)
    expenditure_handler = CommandHandler("expenditure", add_expenditure)

    application.add_handler(start_handler)
    application.add_handler(expenditure_handler)
    
    application.run_polling()
