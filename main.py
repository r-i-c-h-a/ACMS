from flask import *
import sqlite3, hashlib, os
from werkzeug.utils import secure_filename
import pandas as pd
import datetime
from datetime import timedelta
from flask import session, app

app = Flask(__name__)
app.secret_key = 'random string'
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = set(['jpeg', 'jpg', 'png', 'gif'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def getLoginDetails():
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        if 'email' not in session:
            loggedIn = False
            firstName = ''
        else:
            loggedIn = True
            cur.execute("SELECT userId, firstName FROM users WHERE email = ?", (session['email'], ))
            userId, firstName = cur.fetchone()
    conn.close()
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=15)
    return (loggedIn, firstName)

@app.route("/")
def root():
    loggedIn, firstName = getLoginDetails()
    return render_template('home1.html',loggedIn=loggedIn, firstName=firstName)

@app.route("/about_us")
def about_us():
    return render_template('about-us.html')

@app.route("/account/profile")
def profileHome():
    if 'email' not in session:
        return redirect(url_for('root'))
    loggedIn, firstName= getLoginDetails()
    return render_template("profilehome1.html", loggedIn=loggedIn, firstName=firstName)

@app.route("/account/profile/edit")
def editProfile():
    if 'email' not in session:
        return redirect(url_for('root'))
    loggedIn, firstName = getLoginDetails()
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT userId, email, firstName, lastName, address1, address2, zipcode, city, state, country, phone FROM users WHERE email = ?", (session['email'], ))
        profileData = cur.fetchone()
    conn.close()
    return render_template("editProfile.html", profileData=profileData, loggedIn=loggedIn, firstName=firstName)

@app.route("/account/profile/changePassword", methods=["GET", "POST"])
def changePassword():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    if request.method == "POST":
        oldPassword = request.form['oldpassword']
        oldPassword = hashlib.md5(oldPassword.encode()).hexdigest()
        newPassword = request.form['newpassword']
        newPassword = hashlib.md5(newPassword.encode()).hexdigest()
        with sqlite3.connect('database.db') as conn:
            cur = conn.cursor()
            cur.execute("SELECT userId, password FROM users WHERE email = ?", (session['email'], ))
            userId, password = cur.fetchone()
            if (password == oldPassword):
                try:
                    cur.execute("UPDATE users SET password = ? WHERE userId = ?", (newPassword, userId))
                    conn.commit()
                    msg="Changed successfully"
                except:
                    conn.rollback()
                    msg = "Failed"
                return render_template("changePassword1.html", msg=msg)
            else:
                msg = "Wrong password"
        conn.close()
        return render_template("changePassword1.html", msg=msg)
    else:
        return render_template("changePassword1.html")

@app.route("/updateProfile", methods=["GET", "POST"])
def updateProfile():
    if request.method == 'POST':
        email = request.form['email']
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        address1 = request.form['address1']
        address2 = request.form['address2']
        zipcode = request.form['zipcode']
        city = request.form['city']
        state = request.form['state']
        country = request.form['country']
        phone = request.form['phone']
        with sqlite3.connect('database.db') as con:
                try:
                    cur = con.cursor()
                    cur.execute('UPDATE users SET firstName = ?, lastName = ?, address1 = ?, address2 = ?, zipcode = ?, city = ?, state = ?, country = ?, phone = ? WHERE email = ?', (firstName, lastName, address1, address2, zipcode, city, state, country, phone, email))

                    con.commit()
                    msg = "Saved Successfully"
                except:
                    con.rollback()
                    msg = "Error occured"
        con.close()
        return redirect(url_for('editProfile'))

@app.route("/loginForm")
def loginForm():
    if 'email' in session:
        return redirect(url_for('root'))
    else:
        return render_template('login.html', error='')

@app.route("/login", methods = ['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if is_valid(email, password):
            session['email'] = email
            return redirect(url_for('root'))
        else:
            error = 'Invalid UserId / Password'
            return render_template('login.html', error=error)

@app.route("/logout")
def logout():
    session.pop('email', None)
    return redirect(url_for('root'))

def is_valid(email, password):
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute('SELECT email, password FROM users')
    data = cur.fetchall()
    for row in data:
        if row[0] == email and row[1] == hashlib.md5(password.encode()).hexdigest():
            return True
    return False

@app.route("/register", methods = ['GET', 'POST'])
def register():
    if request.method == 'POST':
        #Parse form data
        password = request.form['password']
        email = request.form['email']
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        address1 = request.form['address1']
        address2 = request.form['address2']
        zipcode = request.form['zipcode']
        city = request.form['city']
        state = request.form['state']
        country = request.form['country']
        phone = request.form['phone']

        with sqlite3.connect('database.db') as con:
            try:
                cur = con.cursor()
                cur.execute('INSERT INTO users (password, email, firstName, lastName, address1, address2, zipcode, city, state, country, phone) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (hashlib.md5(password.encode()).hexdigest(), email, firstName, lastName, address1, address2, zipcode, city, state, country, phone))

                con.commit()

                msg = "Registered Successfully"
            except:
                con.rollback()
                msg = "Error occured"
        con.close()
        return render_template("login.html", error=msg)

@app.route("/registerationForm")
def registrationForm():
    return render_template("register.html")

def allowed_file(filename):
    return '.' in filename and \
            filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def parse(data):
    ans = []
    i = 0
    while i < len(data):
        curr = []
        for j in range(7):
            if i >= len(data):
                break
            curr.append(data[i])
            i += 1
        ans.append(curr)
    return ans

@app.route("/account/list_ecommerce",methods=['GET'])
def list_ecomm():
    if 'email' not in session:
        return redirect(url_for('root'))
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT name,link from ecomm;")
        ecommData = cur.fetchall()
    conn.close()
    return render_template("list_ecommerces.html", ecommData=ecommData)

@app.route("/registration",methods=['GET'])
def usReg():
    if 'email' not in session:
        return redirect(url_for('root'))
    loggedIn, firstName= getLoginDetails()
    return render_template("userRegistration.html", firstName=firstName)

@app.route("/account/list_ecommerce",methods=['POST'])
def update_ecomm():
    if 'email' not in session:
        return redirect(url_for('root'))
    ecomm_list=request.get_json()
    ecomm_list=ecomm_list['companies']
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute("UPDATE users SET ecomm_names= ? WHERE email = ?",(str(ecomm_list),session['email']))
        conn.commit()
        msg="update ecommerce list successfully"
    conn.close()

    return render_template("home1.html", msg=msg)   #need to redirect to the desired page

@app.route("/registration",methods=['POST'])
def update_company():
    if 'email' not in session:
        return redirect(url_for('root'))
    company_name=request.form['cname']
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute("UPDATE users SET company_name= ? WHERE email = ?",(company_name,session['email']))
        conn.commit()
        msg="updated company name successfully"
    conn.close()

    return render_template("home1.html", msg=msg)   #need to redirect to the desired page

@app.route("/product", methods=['GET'])
def proDet():
    if 'email' not in session:
        return redirect(url_for('root'))
    loggedIn, firstName= getLoginDetails()
    return render_template("productDetails.html", firstName=firstName)



@app.route("/checkout")
def checkout():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    loggedIn, firstName, noOfItems = getLoginDetails()
    email = session['email']
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT userId FROM users WHERE email = ?", (email, ))
        userId = cur.fetchone()[0]
        cur.execute("SELECT * FROM users WHERE email = ?", (email, ))
        userInfo = cur.fetchone()
        cur.execute("SELECT products.productId, products.name, products.price, products.image FROM products, cart WHERE products.productId = cart.productId AND cart.userId = ?", (userId, ))
        products = cur.fetchall()
    totalPrice = 0
    for row in products:
        totalPrice += row[2]
    return render_template("checkout.html", products = products, totalPrice=totalPrice, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems,userInfo=userInfo)



if __name__ == '__main__':
    app.run(debug=True,port=4000)
