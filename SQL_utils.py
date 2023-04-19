import mysql.connector as msc
SQL_USER=""
SQL_PASSWORD=""
SQL_DATABASE=""

def update_account_balance(cursor,account_id, trans_type, amount):
    """Function that updates the account balance after a transaction"""
    if(trans_type=="Debit"):
        SQL_statement = ("""UPDATE account  """
                         """SET balance = balance - %(amount)s WHERE account_id = %(account_id)s""")
    elif(trans_type=="Credit"):
        SQL_statement = ("""UPDATE account  """
                         """SET balance = balance + %(amount)s WHERE account_id = %(account_id)s""")
    account_data = {"amount":amount,"account_id":account_id}
    cursor.execute(SQL_statement, account_data)

class AccountNameError(TypeError):
    pass

def find_account_id(cursor, account_name):
    SQL_statement = """SELECT account_id FROM account  WHERE name = %(account_name)s"""
    cursor.execute(SQL_statement, {"account_name":account_name})
    try:
        account_id = cursor.fetchone()[0]
    except Exception as err:
        print("The following SQL error ocurred while trying to find the account_id:")
        print('"',err,'"',sep="")
        raise AccountNameError
    else:
        return account_id

def add_transaction(amount, category, description, date, account_name, trans_type):
    """Function that adds a new row to the transaction table in a database
    cursor:the mysql cursor currently being used
    amount: the amount of the new transaction as an integer
    category: to what category the transaction belongs (for example: Groceries)
    description: a more detailed explanation of the transaction belongs
    date: the date when the transaction was made
    account_name: which account was affected by the transaction as an integer
    trans_type: Debit or Credit
    """
    SQL_statement = ("""INSERT INTO transaction (amount, category, description, date, account_id, trans_type) """
            """VALUES (%(amount)s, %(category)s, %(description)s, %(date)s, %(account_id)s, %(trans_type)s)""")

    cnx = msc.connect(user=SQL_USER, password=SQL_PASSWORD, database=SQL_DATABASE)
    cur = cnx.cursor()
    account_id = find_account_id(cur, account_name)
    transaction_data = {"amount":amount, "category":category, "description":description, 
                        "date":date.strftime('%Y-%m-%d %X'), "account_id":account_id, "trans_type":trans_type}
    #now try to update the account data
    try:
        cur.execute(SQL_statement, transaction_data)
    except msc.Error as transaction_err:
        print("The following SQL error ocurred while trying to add a transaction:")
        print('"',transaction_err,'"',sep="")
        cur.close()
        cnx.close()
        raise
    else:
        try:
            update_account_balance(cur, account_id, trans_type, amount)
        except msc.Error as account_err:
            print("The following SQL error ocurred while trying to update the account data")
            print('"',account_err,'"',sep="")
            cur.close()
            cnx.close()
            raise
        else:
            cnx.commit()
    cur.close()
    cnx.close()
