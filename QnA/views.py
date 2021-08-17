from QnA import app
from flask import render_template, request, flash, url_for, redirect

@app.route("/", methods = ["POST", "GET"])
def root():
    if (request.method == "POST"):
        return "OK", 200
    return render_template("main.html")

# @app.route("/edit")
# def editor():
#     return render_template("editor.html")
