#  All Imports
import hmac
import sqlite3
from datetime import timedelta

from flask_cors import CORS
from flask import Flask, request, jsonify
from flask_mail import Mail, Message
from flask_jwt import JWT, jwt_required


# Creating a class for the user
class User(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password


# database for the users
def fetch_users():
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user")
        users = cursor.fetchall()

        new_data = []

        for data in users:
            print(data)
            new_data.append(User(data[0], data[2], data[3]))
    return new_data


def get_user(username, password):
    with sqlite3.connect("database.db") as connection:
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM user WHERE username = '{username}' AND password = '{password}'")

        return cursor.fetchall()


# Authentication
def authenticate(username, password):
    user = username_table.get(username, None)
    if user and hmac.compare_digest(user.password.encode('utf-8'), password.encode('utf-8')):
        return user


# function for identity
def identity(payload):
    user_id = payload['identity']
    return userid_table.get(user_id, None)


# creating a  Database for users
def init_user_table():
    conn = sqlite3.connect('database.db')
    print('Database opened successfully')

    conn.execute("CREATE TABLE IF NOT EXISTS user(user_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "full_name TEXT NOT NULL,"
                 "username TEXT NOT NULL,"
                 "password TEXT NOT NULL)")
    print("user table created successfully")


class Book(object):
    def __init__(self, id, name, price, format):
        self.id = id
        self.name = name
        self.price = price
        self.format = format


# Creating a database for products
def init_book_table():
    conn = sqlite3.connect('database.db')
    print('Database opened successfully')

    conn.execute("CREATE TABLE IF NOT EXISTS book("
                 "book_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "name TEXT NOT NULL,"
                 "price TEXT NOT NULL,"
                 "format TEXT NOT NULL)")
    print("book table created successfully")
    conn.close()


init_user_table()
init_book_table()



users = fetch_users()

username_table = {u.username: u for u in users}
userid_table = {u.id: u for u in users}


# Email
app = Flask(__name__)
app.debug = True
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'aneeqahlotto@gmail.com'
app.config['MAIL_PASSWORD'] = 'lotto2021'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)
app.config['JWT_EXPIRATION_DELTA'] = timedelta(seconds=86400)
app.config['SECRET_KEY'] = 'super-secret'
CORS(app)

jwt = JWT(app, authenticate, identity)


# creating a route for registration
@app.route('/user-registration/', methods=["POST"])
def user_registration():
    #   CREATE AN EMPTY OBJECT THAT WILL HOLD THE response OF THE PROCESS
    response = {}

    try:
        #   MAKE SURE THE request.method IS A POST
        if request.method == "POST":
            #   GET THE FORM DATA TO BE SAVED
            email = request.json['email']
            full_name = request.json['full_name']
            username = request.json['username']
            password = request.json['password']

            #   CALL THE get_user FUNCTION TO GET THE user
            user = get_user(username, password)

            #   IF user EXISTS, THEN LOG THE IN
            if user:
                response["status_code"] = 409
                response["message"] = "user already exists"
                response["email_status"] = "email not sent"
            else:
                #   CALL THE register_user FUNCTION TO REGISTER THE USER
                with sqlite3.connect("database.db") as connection:
                    cursor = connection.cursor()
                    cursor.execute("INSERT INTO user("
                                   "full_name,"
                                   "username,"
                                   "password) VALUES(?, ?, ?)", (email, full_name, username, password))
                    connection.commit()

                #   SEND THE USER AN EMAIL INFORMING THEM ABOUT THEIR REGISTRATION
                    msg = Message('Success', sender='aneeqahlotto@gmail.com', recipients=[email])
                    response["user"] = user
                    msg.body = "Your registration was successful."
                    mail.send(msg)
                    response["description"] = "Message sent"
                #   GET THE NEWLY REGISTERED USER
                user = get_user(username, password)
                #   UPDATE THE response
                response["status_code"] = 201
                response["current_user"] = user
                response["message"] = "registration successful"
                response["email_status"] = "Email was successfully sent"
    except ValueError:
        #   UPDATE THE response
        response["status_code"] = 409
        response["current_user"] = "none"
        response["message"] = "inputs are not valid"
        response["email_status"] = "email not sent"
    finally:
        #   RETURN THE response
        return response


# creating a route for adding a product
@app.route('/adding/', methods=['POST'])
# @jwt_required()
def add_books():
    try:
        response = {}

        if request.method == "POST":
            name = request.json['name']
            price = request.json['price']
            format = request.json['format']

            with sqlite3.connect("database.db") as connection:
                cursor = connection.cursor()
                cursor.execute("INSERT INTO book("
                               "name,"
                               "price,"
                               "format"
                               ") VALUES(?, ?, ?)", (name, price, format))
                connection.commit()
                response["message"] = "success"
                response["status_code"] = 201
            return response
    except:
        response["message"] = "Enter correct details"
        response["description"] = Exception

        return response


# creating a route to view products
@app.route('/view/', methods=['GET'])
def view_books():
    try:
        response = {}

        with sqlite3.connect("database.db") as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM book")

            products = cursor.fetchall()

        response['status_code'] = 200
        response['data'] = products
        return jsonify(response)
    except:
        response["message"] = "Enter correct details"
        response["description"] = Exception

        return response
