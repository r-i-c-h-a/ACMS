from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/registration")
def usReg():
    return render_template("userRegistration.html")

@app.route("/product_details")
def prodDet():
    return render_template("productDetails.html")
