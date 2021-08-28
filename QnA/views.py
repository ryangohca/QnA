import json
import os
import random
import string
from collections import namedtuple

from flask import render_template, request, flash, url_for, redirect, make_response, session
from PIL import Image
import fitz #pymupdf legacy name is fitz
from docx2pdf import convert

from QnA import app, db, sess
from QnA.models import DocumentUploads, Pages, ExtractedImages

curDoc = []
pageAnnotationData = {}
curPageNum = 1

def cropImage(rootImage, coords):
    original = Image.open(rootImage)
    return original.crop((coords['startX'], coords['startY'], coords['endX'], coords['endY']))

def generateRandomName(length=100):
    return ''.join(random.choice(string.ascii_letters + string.digits) for i in range(length))

def extractPdfPages(pdfPath, documentID):
    doc = fitz.open(pdfPath)
    pages = []
    for pageNo, page in enumerate(doc, start=1):
        pix = page.get_pixmap()
        name = generateRandomName() + '.png'
        pix.save(os.path.join(os.path.dirname(__file__), app.config['PAGES'], name))
        page = Pages(documentID=documentID, pageNo=pageNo, databaseName=name)
        db.session.add(page)
        db.session.commit()
        pages.append((page.id, pageNo, name))
    # Returns a list of tuples (pageID, pageNo, databaseName)
    return pages
  
@app.route("/tag", methods=["GET", "POST"])
def tag():
    images = request.args.get("croppedImages")
    if images is None:
        return "server error: 'croppedImages' not found", 500
    images = json.loads(images)
    return render_template("tag.html", images=images)
    
@app.route("/edit", methods=["POST", "GET"])
def editor():
    if (request.method == "POST"):
        scriptDir = os.path.dirname(__file__)
        data = json.loads(list(request.form)[0])
        croppedImages = []
        for pageID in data:
            baseImageDir = os.path.join(scriptDir, data[pageID]['baseImageName'])
            for rects in data[pageID]['annotations']:
                img = cropImage(baseImageDir, rects)
                # Save images
                randomName = generateRandomName() + '.png'
                imageDir = os.path.join(scriptDir, app.config['EXTRACTED'], randomName)
                img.save(imageDir)
                extractedImage = ExtractedImages(pageID=data[pageID]['pageID'], databaseName=randomName,
                                                topX=rects['startX'], topY=rects['startY'], 
                                                bottomX=rects['endX'], bottomY=rects['endY'])
                db.session.add(extractedImage)
                db.session.commit()
                croppedImages.append((extractedImage.id, randomName))
        return redirect(url_for('tag', croppedImages=json.dumps(croppedImages)))

    documents = request.args.get('documents')
    if documents is None:
        return "server error: 'documents' not found", 500
    return render_template("editor.html", documents=json.loads(documents), pageNum = session['curPageNum'], 
                                           annotations = session['curAnnotations'])

@app.route("/nextPage", methods=["POST"])
def nextPage():
    data = json.loads(list(request.form)[0])
    pageID = list(data.keys())[0]
    annotations = data[pageID]["annotations"]
    session['curAnnotations'][pageID] = annotations
    session['curPageNum'] += 1
    return redirect(url_for("editor", documents = json.dumps(session['curDoc'])))
  
@app.route("/prevPage", methods=["POST"])
def prevPage():
    data = json.loads(list(request.form)[0])
    pageID = list(data.keys())[0]
    annotations = data[pageID]["annotations"]
    session['curAnnotations'][pageID] = annotations
    session['curPageNum'] -= 1
    return redirect(url_for("editor", documents = json.dumps(session['curDoc'])))

@app.route("/uploadFiles", methods=["GET", "POST"])
def uploadFiles():
    global curDoc, curPageNum
    
    files = request.files.getlist('filepicker')
    documents = []
    for file in files:
        originalName, ext = file.filename.split('.')
        newName = generateRandomName()
        filePath = os.path.join(os.path.dirname(__file__), app.config['UPLOAD'], newName + '.' + ext)
        file.save(filePath)
        if ext == 'doc' or ext == 'docx':
           newPath = filePath.replace('.' + ext, ".pdf")
           convert(filePath, newPath)
           filePath = newPath
        document = DocumentUploads(userID=1, originalName=file.filename, databaseName=newName + '.pdf')
        db.session.add(document)
        db.session.commit()
        documents.append([document.originalName, extractPdfPages(filePath, documentID=document.id)])
    
    for key in list(session.keys()):
      session.pop(key)
    
    session['curDoc'] = documents
    session['curPageNum'] = 1
    session['curAnnotations'] = {}
    
    return redirect(url_for("editor", documents=json.dumps(session['curDoc']), 
                                      annotations = session['curAnnotations']))

@app.route("/manage", methods=["GET", "POST"])
def manage():
    allDocuments = DocumentUploads.query.all()
    completed = []
    uncompleted = []
    for document in allDocuments:
        # Get first page for preview
        firstPage = Pages.query.filter_by(documentID=document.id).first().databaseName
        if document.percentageCompleted == 100:
            CompletedDocument = namedtuple('CompletedDocument', ['name', 'previewPageName', 'warnings'])
            warnings = []
            # Add code to fill warnings here
            completed.append(CompletedDocument(name=document.originalName, previewPageName=firstPage, warnings=warnings))
        else:
            UncompletedDocument = namedtuple('UncompletedDocument', ['name', 'previewPageName', 'percentageCompleted'])
            uncompleted.append(UncompletedDocument(name=document.originalName, previewPageName=firstPage, percentageCompleted=document.percentageCompleted))
    return render_template("manage.html", completed=completed, uncompleted=uncompleted)

@app.route("/")
def root():
    return render_template("main.html")