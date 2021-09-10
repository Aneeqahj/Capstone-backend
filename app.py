#  All Imports
import hmac
import sqlite3
import cloudinary
import cloudinary.uploader
from datetime import timedelta, date

from flask_cors import CORS, cross_origin
from flask import Flask, request, jsonify
from flask_mail import Mail, Message
from flask_jwt import JWT, jwt_required


# Creating a class for the user
class User(object):
    def __init__(self, id, username, password, is_admin):
        self.id = id
        self.username = username
        self.password = password
        self.is_admin = is_admin


# database for the users
def fetch_users():
    with sqlite3.connect('database.db') as connection:
        connection.row_factory = dict_factory
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM user")
        users = cursor.fetchall()

        new_data = []

        for data in users:
            print(data)
            new_data.append(User(data["user_id"], data["username"], data["password"], data["is_admin"]))
    return new_data


# This function create dictionaries out of SQL rows, so that the data follows JSON format
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def get_user(username, password):
    with sqlite3.connect("database.db") as connection:
        connection.row_factory = dict_factory
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
    connection = sqlite3.connect('database.db')
    print('Database opened successfully')

    connection.execute("CREATE TABLE IF NOT EXISTS user("
                       "user_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                       "full_name TEXT NOT NULL,"
                       "email TEXT NOT NULL,"
                       "username TEXT NOT NULL,"
                       "password TEXT NOT NULL,"
                       "is_admin TEXT NOT NULL)")
    print("user table created successfully")


class Review(object):
    def __init__(self, review_id, review, date, book_id):
        self.review_id = review_id
        self.review = review
        self.date = date
        self.book_id = book_id


# creating a  Database for reviews
def init_review_table():
    connection = sqlite3.connect('database.db')
    print('Database opened successfully')

    connection.execute("CREATE TABLE IF NOT EXISTS review(review_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                       "user_id INTEGER NULL,"
                       "review TEXT NOT NULL,"
                       "date TEXT NOT NULL,"
                       "book_id INTEGER NOT NULL,"
                       "FOREIGN KEY (user_id) REFERENCES user(user_id),"
                       "FOREIGN KEY (book_id) REFERENCES book(book_id))")
    print("user table created successfully")


class Book(object):
    def __init__(self, id, name, price, format, synopsis):
        self.id = id
        self.name = name
        self.price = price
        self.format = format
        self.synopsis = synopsis


# Creating a database for books
def init_book_table():
    connection = sqlite3.connect('database.db')
    print('Database opened successfully')

    connection.execute("CREATE TABLE IF NOT EXISTS book("
                       "book_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                       "name TEXT NOT NULL,"
                       "price TEXT NOT NULL,"
                       "format TEXT NOT NULL, "
                       "genre TEXT NOT NULL, "
                       "image_url TEXT NOT NULL, "
                       "synopsis TEXT NOT NULL)")
    print("book table created successfully")
    connection.close()


init_user_table()
init_book_table()
init_review_table()

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
                print("user")

                with sqlite3.connect("database.db") as connection:
                    connection.row_factory = dict_factory
                    cursor = connection.cursor()
                    # cursor.execute("INSERT INTO user("
                    #                "email,"
                    #                "full_name,"
                    #                "username,"
                    #                "password) VALUES(?, ?, ?, ?)", (email, full_name, username, password))
                    print(
                        "INSERT INTO user ( email, full_name, username, password, is_admin ) VALUES ( '" + email + "', '" + full_name + "', '" + username + "', '" + password + "' )")
                    cursor.execute(
                        "INSERT INTO user ( email, full_name, username, password, is_admin ) VALUES ( '" + email + "', '" + full_name + "', '" + username + "', '" + password + "', 'false' )")
                    connection.commit()

                    global users
                    users = fetch_users()
                    print(users)

                #   SEND THE USER AN EMAIL INFORMING THEM ABOUT THEIR REGISTRATION
                # msg = Message('Success', sender='aneeqahlotto@gmail.com', recipients=[email])
                # msg.body = "Your registration was successful."
                # mail.send(msg)
                # email_to_send = Message('Welcome to the Only Books.', sender='aneeqahlotto@gmail.com',
                #                         recipients=[email])
                # email_to_send.body = f"Congratulations {full_name} on a successful registration. \n\n" \
                #                      f"Welcome to the Only books family, browse around and make sure to enjoy the " \
                #                      f"experience. "
                #
                # mail.send(email_to_send)
                response["description"] = "Message sent"

                #   GET THE NEWLY REGISTERED USER
                user = get_user(username, password)
                print(user)
                #   UPDATE THE response
                response["status_code"] = 201
                response["current_user"] = user
                response["message"] = "registration successful"
                response["email_status"] = "Email was successfully sent"
                return response
    except Exception as e:
        print(e.message)
        #   UPDATE THE response
        response["status_code"] = 409
        response["current_user"] = "none"
        response["message"] = "inputs are not valid"
        response["email_status"] = "email not sent"
        return response
    finally:
        #   RETURN THE response
        return response


@app.route("/get-users/")
def get_users():
    response = {}

    #   CALL THE register_user FUNCTION TO REGISTER THE USER
    with sqlite3.connect("database.db") as connection:
        connection.row_factory = dict_factory
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM user")

        users = cursor.fetchall()
        response["users"] = users

    return response


@app.route("/user-login/", methods=["POST"])
def login():
    response = {}

    if request.method == "POST":

        username = request.json['username']
        password = request.json['password']

        with sqlite3.connect("database.db") as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM user WHERE username = '{username}' AND password = '{password}'")
            user_information = cursor.fetchone()

        if user_information:
            response["user_info"] = user_information
            response["message"] = "Success"
            response["status_code"] = 201
            return jsonify(response)

        else:
            response['message'] = "Login Unsuccessful, please try again"
            response['status_code'] = 401
            return jsonify(response)


@app.route('/admin/', methods=["POST"])
def admin():
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
            is_admin = request.json['is_admin']

            #   CALL THE register_user FUNCTION TO REGISTER THE USER
            with sqlite3.connect("database.db") as connection:
                connection.row_factory = dict_factory
                cursor = connection.cursor()
                cursor.execute("INSERT INTO user("
                               "email,"
                               "full_name,"
                               "username,"
                               "password,"
                               "is_admin) VALUES(?, ?, ?, ?, ?)", (email, full_name, username, password, is_admin))
                connection.commit()

            global users
            users = fetch_users()
            print(users)

            response["message"] = "admin created"

            return response
    except Exception as e:
        print(e.message)
        #   UPDATE THE response
    finally:
        #   RETURN THE response
        return response


# creating a route for adding a books
@app.route('/adding/', methods=['POST'])
# @jwt_required()
def add_books():
    try:
        response = {}

        if request.method == "POST":
            name = request.json['name']
            price = request.json['price']
            format = request.json['format']
            genre = request.json['genre']
            synopsis = request.json['synopsis']
            url = request.json['image_url']

            with sqlite3.connect("database.db") as connection:
                connection.row_factory = dict_factory
                cursor = connection.cursor()
                cursor.execute("INSERT INTO book("
                               "name,"
                               "price,"
                               "genre,"
                               "format,"
                               "synopsis,"
                               "image_url"
                               ") VALUES(?, ?, ?, ?, ?, ?)", (name, price, genre, format, synopsis, url))
                connection.commit()

                response["message"] = "success"
                response["status_code"] = 201
            return response
    except:
        response["message"] = "Enter correct details"
        response["description"] = Exception

        return response


# creating a route to view books
@app.route('/viewing/', methods=['GET'])
def view_books():
    try:
        response = {}

        with sqlite3.connect("database.db") as connection:
            connection.row_factory = dict_factory
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


@app.route('/view-one/<int:book_id>/', methods=['GET'])
def view_book(book_id):
    try:
        response = {}

        with sqlite3.connect("database.db") as connection:
            connection.row_factory = dict_factory
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM book WHERE book_id=?", str(book_id))
            products = cursor.fetchall()

        response['status_code'] = 200
        response['data'] = products
        return response
    except:
        response["message"] = "Enter correct details"
        response["description"] = Exception

        return response


# creating a route to update books
@app.route('/update/<int:book_id>/', methods=['PUT'])
# @jwt_required()
def update_book(book_id):
    try:
        response = {}

        if request.method == "PUT":
            with sqlite3.connect('database.db') as connection:
                print(request.json)
                incoming_data = dict(request.json)
                put_data = {}

                if incoming_data.get("name") is not None:
                    put_data["name"] = incoming_data.get("name")
                    with sqlite3.connect('database.db') as connection:
                        connection.row_factory = dict_factory
                        cursor = connection.cursor()
                        cursor.execute("UPDATE book SET name =? WHERE book_id=?", (put_data["name"], book_id))
                        connection.commit()
                        response['message'] = "Update was successful"
                        response['status_code'] = 200

                elif incoming_data.get("price") is not None:
                    put_data["price"] = incoming_data.get("price")
                    with sqlite3.connect('database.db') as connection:
                        connection.row_factory = dict_factory
                        cursor = connection.cursor()
                        cursor.execute("UPDATE book SET price =? WHERE book_id=?",
                                       (put_data["price"], book_id))
                        connection.commit()
                        response['message'] = "Update was successful"
                        response['status_code'] = 200

                elif incoming_data.get("format") is not None:
                    put_data["format"] = incoming_data.get("format")
                    with sqlite3.connect('database.db') as connection:
                        connection.row_factory = dict_factory
                        cursor = connection.cursor()
                        cursor.execute("UPDATE book SET category =? WHERE book_id=?", (put_data["book"],
                                                                                       book_id))
                        connection.commit()
                        response['message'] = "Update was successful"
                        response['status_code'] = 200

                elif incoming_data.get("synopsis") is not None:
                    put_data["synopsis"] = incoming_data.get("synopsis")
                    with sqlite3.connect('database.db') as connection:
                        connection.row_factory = dict_factory
                        cursor = connection.cursor()
                        cursor.execute("UPDATE book SET synopsis =? WHERE book_id=?", (put_data["synopsis"],
                                                                                       book_id))
                        connection.commit()
                        response['message'] = "Update was successful"
                        response['status_code'] = 200
                return response
    except:
        response["message"] = "Enter correct details"
        response["description"] = Exception

        return response


# creating a route to delete books
@app.route('/delete_book/<int:book_id>/')
# @jwt_required()
def delete_book(book_id):
    try:
        response = {}

        with sqlite3.connect("database.db") as connection:
            connection.row_factory = dict_factory
            cursor = connection.cursor()
            cursor.execute("DELETE FROM book WHERE book_id=" + str(book_id))
            connection.commit()
            response['status_code'] = 200
            response['message'] = "book deleted successfully."
        return response
    except:
        response["message"] = "Enter correct details"
        response["description"] = Exception

        return response


# REVIEW TABLE FUNCTIONS
# creating a route for adding reviews
@app.route('/add/', methods=['POST'])
# @jwt_required()
def add_review():
    try:
        response = {}

        if request.method == "POST":
            review = request.json['review']
            book_id = request.json['book_id']
            user_id = request.json['user_id']

            today = date.today()
            date_reviewed = today.strftime('%B %d, %Y')

            with sqlite3.connect("database.db") as connection:
                connection.row_factory = dict_factory
                cursor = connection.cursor()
                "user_id INTEGER NULL,"
                "review TEXT NOT NULL,"
                "date TEXT NOT NULL,"
                "book_id INTEGER NOT NULL,"
                cursor.execute("INSERT INTO review("
                               "user_id, "
                               "review,"
                               "date,"
                               "book_id"
                               ") VALUES(?, ?, ?, ?)", (user_id, review, date_reviewed, book_id))
                connection.commit()
                response["message"] = "success"
                response["status_code"] = 201
            return response
    except:
        response["message"] = "Enter correct details"
        response["description"] = Exception

        return response


# creating a route to view reviews
@app.route('/view/', methods=['GET'])
def view_reviews():
    try:
        response = {}

        with sqlite3.connect("database.db") as connection:
            connection.row_factory = dict_factory
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM review")

            products = cursor.fetchall()

        response['status_code'] = 200
        response['data'] = products
        return jsonify(response)
    except:
        response["message"] = "Enter correct details"
        response["description"] = Exception

        return response


@app.route('/view_one/<int:review_id>/', methods=['GET'])
def view_review(review_id):
    try:
        response = {}

        with sqlite3.connect("database.db") as connection:
            connection.row_factory = dict_factory
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM review WHERE review_id=?", str(review_id))
            products = cursor.fetchall()

        response['status_code'] = 200
        response['data'] = products
        return response
    except:
        response["message"] = "Enter correct details"
        response["description"] = Exception

        return response


# creating a route to delete reviews
@app.route('/delete_review/<int:review_id>/')
# @jwt_required()
def delete_review(review_id):
    try:
        response = {}

        with sqlite3.connect("database.db") as connection:
            connection.row_factory = dict_factory
            cursor = connection.cursor()
            cursor.execute("DELETE FROM review WHERE review_id=" + str(review_id))
            connection.commit()
            response['status_code'] = 200
            response['message'] = "book deleted successfully."
        return response
    except:
        response["message"] = "Enter correct details"
        response["description"] = Exception

        return response


# USER DETAILS
@app.route('/view_user/<int:user_id>/', methods=['GET'])
def view_user(user_id):
    try:
        response = {}

        with sqlite3.connect("database.db") as connection:
            connection.row_factory = dict_factory
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM user WHERE user_id=?", str(user_id))
            user = cursor.fetchall()

        response['status_code'] = 200
        response['data'] = user
        return response
    except:
        response["message"] = "Enter correct details"
        response["description"] = Exception

        return response


@app.route('/delete_user/<int:user_id>/')
# @jwt_required()
def delete_user(user_id):
    try:
        response = {}

        with sqlite3.connect("database.db") as connection:
            connection.row_factory = dict_factory
            cursor = connection.cursor()
            cursor.execute("DELETE FROM user WHERE user_id=" + str(user_id))
            connection.commit()
            response['status_code'] = 200
            response['message'] = "user deleted successfully."
        return response
    except:
        response["message"] = "Enter correct details"
        response["description"] = Exception

        return response


if __name__ == "__main__":
    app.run()
    app.debug = True
