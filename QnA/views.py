from QnA import app
from flask import render_template, request, flash, url_for, redirect
import json

@app.route("/", methods = ["POST", "GET"])
def root():
    if (request.method == "POST"):
        data = json.loads(list(request.form)[0])
        print(type(data))
        return str(data), 200
    return render_template("main.html")

# @app.route("/edit")
# def editor():
#     return render_template("editor.html")
