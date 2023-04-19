import logging
from telegram import Update
import mysql.connector as msc
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes
#this is my config.py file which is in .gitignore so that people don't see my credentials
from config import BOT_TOKEN, SQL_USER, SQL_PASSWORD, SQL_DATABASE
import SQL_utils #I wrote this module with the functions that can interact with a SQL database
import re
import pandas as pd
"""
This is a bot that helps you track your expenditures.
It's a personal project but I hope it will eventually be hosted on a server and available to everybody. 
"""

SQL_utils.SQL_USER=SQL_USER
SQL_utils.SQL_PASSWORD=SQL_PASSWORD
SQL_utils.SQL_DATABASE=SQL_DATABASE


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text="I help you keep track of your expenses."
    await context.bot.send_message(chat_id=update.effective_chat.id, text=welcome_text)


def add_expenditure(update: Update, context: ContextTypes.DEFAULT_TYPE, trans_type):
    """This function receives the update from the handler as a command and gets the 
    information about the expenditure. Finally it adds that information
    to a SQL database.
    """
    expenditure_data = context.args
    amount = 0
    category = ""
    description = ""
    account = ""
    for data in expenditure_data:
        if data.startswith("$"):
            try:
                amount = int(data[1:])
            except:
                print("What comes right after the '$' symbol has to be an integer$")
                return
        elif data.startswith("#"):
            category = data[1:]
        elif data.startswith("@"):
            account = data[1:]
        else:
            description += " "+data
    description = description.strip()          
    date = update.message.date#find date

    try:#try to add the values to a database
        SQL_utils.add_transaction(amount, category, description, date, account, trans_type)
        print("Transacción añadida")
    except SQL_utils.AccountNameError:
        print("The account doesn't exist. You can create a new account with the command", "\create_account.")
    except msc.errors.DatabaseError as db_err:
        err_code = db_err.args[0]
        #este código se podría usar para mandarle un mensaje al usuario en lugar del print
        if err_code == 1366:
            err_msg = db_err.args[1]
            column = re.findall(r"'(\w+)'",err_msg)[1]
            value = re.findall(r"'(\w+)'",err_msg)[0]
            print(f"El valor '{value}' no es un valor válido para usar como {column}.")
        else:
            print(db_err)
    except Exception as err:
        print(err)

async def add_debit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    add_expenditure(update, context, trans_type="Debit")

async def add_credit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    add_expenditure(update, context, trans_type="Credit")

if __name__ == '__main__':
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    start_handler = CommandHandler('start', start)
    debit_handler = CommandHandler("debit", add_debit)
    credit_handler = CommandHandler("credit", add_credit)

    application.add_handler(start_handler)
    application.add_handler(debit_handler)
    application.add_handler(credit_handler)
    
    application.run_polling()
