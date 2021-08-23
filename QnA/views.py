import json
import os
import random

from flask import render_template, request, flash, url_for, redirect
from PIL import Image
import fitz #pymupdf legacy name is fitz
from docx2pdf import convert

from QnA import app, db
from QnA.models import DocumentUploads, Pages, ExtractedImages


def cropImage(rootImage, coords):
    original = Image.open(rootImage)
    return original.crop((coords['startX'], coords['startY'], coords['endX'], coords['endY']))

def generateRandomName(length=100):
    return ''.join(random.choice('abcdefghijklmnopqrstuvwxyz1234567890') for i in range(length))

def extractPdfPages(pdfPath, documentID):
    doc = fitz.open(pdfPath)
    pagesFilenames = []
    for pageNo, page in enumerate(doc, start=1):
        pix = page.get_pixmap()
        name = generateRandomName() + '.png'
        pagesFilenames.append(name)
        pix.save(os.path.join(os.path.dirname(__file__), app.config['PAGES'], name))
        page = Pages(documentID=documentID, pageNo=pageNo, databaseName=name)
        db.session.add(page)
        db.session.commit()
    return pagesFilenames
        
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
    pages = request.args.get('pages')
    return render_template("editor.html", pages=pages)

@app.route("/uploadFiles", methods=["GET", "POST"])
def uploadFiles():
    files = request.files.getlist('filepicker')
    pages = []
    for file in files:
        originalName, ext = file.filename.split('.')
        newName = generateRandomName()
        filePath = os.path.join(os.path.dirname(__file__), app.config ['UPLOAD'], newName + '.' + ext)
        file.save(filePath)
        if ext == 'doc' or ext == 'docx':
           newPath = filePath.replace('.' + ext, ".pdf")
           convert(filePath, newPath)
           filePath = newPath
        document = DocumentUploads(userID=1, originalName=originalName + '.' + ext, databaseName=newName + '.pdf')
        db.session.add(document)
        db.session.commit()
        pages.append([document.id, extractPdfPages(filePath, documentID=document.id)])
            
    return redirect(url_for("editor", pages=pages))

@app.route("/")
def root():
    return render_template("main.html")
    
# @app.route("/edit")
# def editor():
#     return render_template("editor.html")
