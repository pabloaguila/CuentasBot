import logging
from telegram import Update
import mysql.connector as msc
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes
import os
from dotenv import load_dotenv
import SQL_utils #I wrote this module with the functions that can interact with a SQL database
import re
import pandas as pd
"""
This is a bot that helps you track your expenditures.
It's a personal project but I hope it will eventually be hosted on a server and available to everybody. 
"""
load_dotenv()
SQL_utils.SQL_USER=os.environ.get("SQL_USER")
SQL_utils.SQL_PASSWORD=os.environ.get("SQL_PASSWORD")
SQL_utils.SQL_DATABASE=os.environ.get("SQL_DATABASE")


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

async def create_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """This function receives the update from the handler as a command and gets the 
    information of a new account. If everything is ok it adds a new account to a SQL database.
    """
    account_data = context.args
    balance = 0
    
    try:
        name = str(account_data[0])
    except IndexError:
        await context.bot.send_message(chat_id=update.effective_chat.id, 
                                       text="You have to write the account name next to the /create_account command.")
        return
    except Exception as err:
        print(err)
        return
    
    try:#try to add the values to a database
        SQL_utils.add_account(name, balance)
    except SQL_utils.DuplicateAccountNameError:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="The account name already exists. Please choose a different name.")
    except Exception as err:
        print(err)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Account added successfully.")



async def add_debit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """This function receives the update from the handler as a command and gets the 
    information about the debit. Finally it adds that information
    to a SQL database.
    """
    try:#try to add the values to a database
        add_expenditure(update, context, trans_type="Debit")
    except SQL_utils.AccountNameError:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="The account doesn't exist. You can create a new account with the command /create_account.")
    except AmountTypeError:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"The value after the '$' symbol has to be an integer.")
    except Exception as err:
        print(err)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Debit registered successfully.")

async def add_credit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """This function receives the update from the handler as a command and gets the 
    information about the credit. Finally it adds that information
    to a SQL database.
    """
    try:#try to add the values to a database
        add_expenditure(update, context, trans_type="Credit")
    except SQL_utils.AccountNameError:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="The account doesn't exist. You can create a new account with the command /create_account.")
    except AmountTypeError:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"The value after the '$' symbol has to be an integer.")
    except Exception as err:
        print(err)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Credit registered successfully.")

if __name__ == '__main__':
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    start_handler = CommandHandler('start', start)
    debit_handler = CommandHandler("debit", add_debit)
    credit_handler = CommandHandler("credit", add_credit)
    create_account_handler = CommandHandler("create_account", create_account)
    
    application.add_handler(start_handler)
    application.add_handler(debit_handler)
    application.add_handler(credit_handler)
    application.add_handler(create_account_handler)
    
    application.run_polling()
