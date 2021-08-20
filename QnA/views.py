import json
import os
import random

from flask import render_template, request, flash, url_for, redirect
from PIL import Image
import fitz #pymupdf legacy name is fitz
from docx2pdf import convert

from QnA import app

def cropImage(rootImage, coords):
    original = Image.open(rootImage)
    return original.crop((coords['startX'], coords['startY'], coords['endX'], coords['endY']))

def generateRandomName(length=100):
    return ''.join(random.choice('abcdefghijklmnopqrstuvwxyz1234567890') for i in range(length))

def extractPdfPages(pdfPath):
    doc = fitz.open(pdfPath)
    for page in doc:
        pix = page.get_pixmap()
        pix.save(os.path.join(os.path.dirname(__file__), app.config['PAGES'], generateRandomName() + '.png'))
        
@app.route("/edit", methods = ["POST", "GET"])
def editor():
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
            randomName = generateRandomName() + '.png'
            imageDir = os.path.join(scriptDir, app.config['EXTRACTED'], randomName)
            img.save(imageDir)

        return str(croppedImages), 200
    return render_template("editor.html")

@app.route("/uploadFiles", methods=["GET", "POST"])
def uploadFiles():
    files = request.files.getlist(('filepicker'))
    for file in files:
        ext = file.filename.split('.')[1]
        filePath = os.path.join(os.path.dirname(__file__), app.config['UPLOAD'], generateRandomName() + '.' + ext)
        print(os.path.dirname(__file__))
        file.save(filePath)
        if ext == 'doc' or ext == 'docx':
            convert(filePath)
            filePath.replace('.' + ext, '.pdf')
        extractPdfPages(filePath)
            
    return redirect(url_for("editor"))

@app.route("/")
def root():
    return render_template("main.html")
    
# @app.route("/edit")
# def editor():
#     return render_template("editor.html")
