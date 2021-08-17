from QnA import app
from flask import render_template, request, flash, url_for, redirect

@app.route("/")
def root():
    return render_template("main.html")

# @app.route("/edit")
# def editor():
#     return render_template("editor.html")

