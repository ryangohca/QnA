import json
import os
import random

from flask import render_template, request, flash, url_for, redirect
from PIL import Image

from QnA import app

def cropImage(rootImage, coords):
    original = Image.open(rootImage)
    return original.crop((coords['startX'], coords['startY'], coords['endX'], coords['endY']))

@app.route("/", methods = ["POST", "GET"])
def root():
    if (request.method == "POST"):
        scriptDir = os.path.dirname(__file__)
        data = json.loads(list(request.form)[0])
        croppedImages = []
        for pageID in data:
            if pageID == "filename":
                continue
            imageDir = os.path.join(scriptDir, data[pageID]['baseImageName'])
            for rects in data[pageID]['annotations']:
                croppedImages.append(cropImage(imageDir, rects))

        #Save images
        for img in croppedImages:
            randomName = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz1234567890') for i in range(100)) + '.png'
            imageDir = os.path.join(scriptDir, 'storage/' + randomName)
            img.save(imageDir)

        return str(croppedImages), 200
    return render_template("main.html")

# @app.route("/edit")
# def editor():
#     return render_template("editor.html")
