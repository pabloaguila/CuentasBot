import logging
from telegram import Update
import mysql.connector as msc
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes
import os
from datetime import timedelta
# I wrote this module with the functions that can interact with a SQL database
import SQL_utils
import re
import pandas as pd
import boto3
from botocore.exceptions import ClientError
import json

"""
This is a bot that helps you track your expenditures.
It's a personal project but I hope it will eventually be hosted on a server and available to everybody.
"""
chat_id = int(os.environ.get("CHAT_ID"))
timedelta_utc_hours = timedelta(hours=-3)

# Get credetianls from AWS
def get_secret():
    secret_name = os.environ.get("SECRET_NAME")
    region_name = os.environ.get("REGION_NAME")
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e
    # Decrypts secret using the associated KMS key.
    secret = get_secret_value_response['SecretString']
    return secret

secret = get_secret()
secret = json.loads(secret)

# Set Database credential
SQL_utils.SQL_USER = secret["username"]
SQL_utils.SQL_PASSWORD = secret["password"]
SQL_utils.SQL_DATABASE = secret["dbname"]
SQL_utils.SQL_HOST = secret["host"]

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if (update.effective_chat.id != chat_id):
        return False

    welcome_text = "I help you keep track of your expenses."
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=welcome_text)


class AmountTypeError(TypeError):
    pass


def add_expenditure(update: Update,
                    context: ContextTypes.DEFAULT_TYPE,
                    trans_type):
    """This function receives the update from the handler as a command and gets
    the information about the expenditure. Finally it adds that information
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
            except Exception:
                raise AmountTypeError
        elif data.startswith("#"):
            category = data[1:]
        elif data.startswith("@"):
            account = data[1:]
        else:
            description += " "+data
    description = description.strip()
    date = update.message.date  # find date
    date = date+timedelta_utc_hours  # change dateime according to timezone
    SQL_utils.add_transaction(amount, category, description, date, account, trans_type)


async def create_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """This function receives the update from the handler as a command and gets the
    information of a new account. If everything is ok it adds a new account to a SQL database.
    """
    if (update.effective_chat.id != chat_id):
        return False

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

    try:  # try to add the values to a database
        SQL_utils.add_account(name, balance)
    except SQL_utils.DuplicateAccountNameError:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="The account name already exists. Please choose a different name.")
    except Exception as err:
        print(err)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Account added successfully.")


async def add_debit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """This function receives the update from the handler as a command
    and gets the information about the debit. Finally it adds that
    information to a SQL database.
    """
    if (update.effective_chat.id != chat_id):
        return False

    try:  # try to add the values to a database
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
    """This function receives the update from the handler as a command
    and gets the information about the debit. Finally it adds that
    information to a SQL database.
    """
    if (update.effective_chat.id != chat_id):
        return False

    try:  # try to add the values to a database
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
