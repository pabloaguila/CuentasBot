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

class AmountTypeError(TypeError):
    pass

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
                raise AmountTypeError
        elif data.startswith("#"):
            category = data[1:]
        elif data.startswith("@"):
            account = data[1:]
        else:
            description += " "+data
    description = description.strip()          
    date = update.message.date#find date
    SQL_utils.add_transaction(amount, category, description, date, account, trans_type)


async def add_debit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:#try to add the values to a database
        add_expenditure(update, context, trans_type="Debit")
    except SQL_utils.AccountNameError:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="The account doesn't exist. You can create a new account with the command \create_account.")
    except AmountTypeError:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"The value after the '$' symbol has to be an integer.")
    except Exception as err:
        print(err)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Debit registered successfully.")

async def add_credit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:#try to add the values to a database
        add_expenditure(update, context, trans_type="Credit")
    except SQL_utils.AccountNameError:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="The account doesn't exist. You can create a new account with the command \create_account.")
    except AmountTypeError:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"The value after the '$' symbol has to be an integer.")
    except Exception as err:
        print(err)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Credit registered successfully.")

if __name__ == '__main__':
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    start_handler = CommandHandler('start', start)
    debit_handler = CommandHandler("debit", add_debit)
    credit_handler = CommandHandler("credit", add_credit)

    application.add_handler(start_handler)
    application.add_handler(debit_handler)
    application.add_handler(credit_handler)
    
    application.run_polling()
