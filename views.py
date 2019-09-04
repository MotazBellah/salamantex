from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import *
from time import gmtime, strftime
from flask_login import LoginManager, login_user, current_user, login_required, logout_user
from flask import session as login_session
from wtform_fields import *
import os
# import threading
# from concurrent.futures import ThreadPoolExecutor
from time import sleep
from flask_executor import Executor

# DOCS https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ThreadPoolExecutor
# executor = ThreadPoolExecutor(2)

# from apscheduler.schedulers.background import BackgroundScheduler
# from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
# from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor


app = Flask(__name__)
app.secret_key="sdfdsuperfdlkngflkjnlkbgirlsdhjdrefsdfucfgfgfhhyah!!!!!dfghhm;glhjkhjl,.jk"
app.config['WTF_CSRF_SECRET_KEY'] = "b'f\xfa\x8b{X\x8b\x9eM\x83l\x19\xad\x84\x08\xaa"

app.config['SQLALCHEMY_DATABASE_URI']=os.environ.get('DATABASE_URL')
# app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///currency.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# configure flask_login
login = LoginManager()
login.init_app(app)

executor = Executor(app)
app.config['EXECUTOR_TYPE'] = 'thread'
app.config['EXECUTOR_MAX_WORKERS'] = 25

def transaction_run():
    print('working...')
    x = Transaction.query.filter_by(done=False).all()
    for i in x:
        i.done = True
        db.merge(x)
        db.commit()
    print('Done!!!!')

futures = []
for i in range(4):
    # note the lack of () after ".all", as we're passing the function object, not calling it ourselves
    future = executor.submit(Transaction.query.filter_by(done=False).all())
    futures.append(future)

for future in futures:
    print(future.result())





# manage a database connection
# To avaid  connection time out errors
@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.route('/')
@app.route('/register', methods=['GET', 'POST'])
def login_form():
    reg_form = RegistartionForm()
    if reg_form.validate_on_submit():
        username = reg_form.username.data
        email = reg_form.email.data
        password = reg_form.password.data
        hashed_pswd = pbkdf2_sha256.hash(password)
        # Add user to DB
        user = User(name=username, email=email, password=hashed_pswd)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('log.html', form=reg_form)



@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()

    # Allow login if validation success
    if login_form.validate_on_submit():
        user_object = User.query.filter_by(email=login_form.email.data).first()
        login_user(user_object)
        login_session['user_id'] = user_object.id
        # return redirect(url_for('show_tasks'))
        return redirect(url_for('mainPage'))

    return render_template("login.html", form=login_form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/user', methods=['GET', 'POST'])
@login_required
def mainPage():
    user_id = login_session['user_id']
    currency = Currency.query.filter_by(user_id=user_id).all()
    return render_template('user_page.html', user_id=user_id)


@app.route('/currency-account/<int:user_id>', methods=['GET', 'POST'])
@login_required
def currencyAccount(user_id):
    currency_form = CurrencyForm()

    # Allow login if validation success
    if currency_form.validate_on_submit():
        bitcoin_id = currency_form.bitcoin_id.data
        bitcoin_balance = currency_form.bitcoin_balance.data
        ethereum_id = currency_form.ethereum_id.data
        ethereum_balance = currency_form.ethereum_balance.data
        max_amount = currency_form.max_amount.data
        # Add currency to DB
        currency = Currency(bitcoin_id=bitcoin_id, bitcoin_balance=bitcoin_balance,
                            ethereum_id=ethereum_id, ethereum_balance=ethereum_balance,
                            max_amount=max_amount, user_id=user_id)
        db.session.add(currency)
        db.session.commit()
        return redirect(url_for('mainPage'))
    return render_template("currency_account.html",
                           form=currency_form,
                           user_id=login_session['user_id']
                           )


@app.route('/transaction/<int:user_id>', methods=['GET', 'POST'])
@login_required
def transaction(user_id):
    trans_form = TransactionForm()

    # Allow login if validation success
    if trans_form.validate_on_submit():
        currency_amount = trans_form.currency_amount.data
        currency_Type = trans_form.currency_Type.data
        target_user = trans_form.target_user.data
        # Add currency to DB
        transaction = Transaction(currency_amount=currency_amount,
                               currency_Type=currency_Type,
                               target_user=target_user,
                               user_id=user_id)
        db.session.add(transaction)
        db.session.commit()
        return redirect(url_for('mainPage'))
    return render_template("transaction.html",
                           form=trans_form,
                           user_id=login_session['user_id']
                           )


@app.route('/transaction-history', methods=['GET', 'POST'])
@login_required
def transaction_history():

    executor.submit(transaction_run)
    # user_id = login_session['user_id']
    transactions = Transaction.query.filter_by(done=False).all()
    return render_template('trans_history.html', transactions=transactions)

if __name__ == '__main__':
    # app.secret_key = 'super_secret_key'
    PORT = int(os.environ.get('PORT', 5000))
    app.debug = True
    # t1= threading.Thread(target=transaction_run)
    # t1.start()
    # t1.join()

    app.run(host='0.0.0.0', port=PORT)
