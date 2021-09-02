import json
import os
import random
import string
import logging
from collections import namedtuple

from flask import render_template, request, flash, url_for, redirect, make_response, session, jsonify
from flask_login import login_required, login_user, logout_user
from PIL import Image
import fitz #pymupdf legacy name is fitz
from docx2pdf import convert

from QnA import app, db, sess, login
from QnA.models import Users, DocumentUploads, Pages, ExtractedImages
from QnA.forms import LoginForm, SignupForm

logging.basicConfig(level=logging.DEBUG)

def cropImage(rootImage, coords):
    # coords = (startX, startY, endX, endY)
    original = Image.open(rootImage)
    return original.crop(coords)

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
    logging.info(pages)
    # Returns a list of tuples (pageID, pageNo, databaseName)
    return pages

def saveAnnotationsToSession(data):
    canvasID = list(data.keys())[1] #first key is always '_currDocumentID'
    annotations = data[canvasID]["annotations"]
    session['edit']['curAnnotations'][canvasID] = annotations

def loginUser(username, remember_me):
    user = Users.query.filter_by(username=username).first()
    login_user(user, remember=remember_me)
    next_page = request.args.get("next")
    if not next_page or url_parse(next_page).netloc != "":
        next_page = url_for('home', _scheme="https", _external=True)
    return redirect(next_page)
      
@login.unauthorized_handler
def unauthorised():
    return redirect(url_for('root', _scheme="https", _external=True))

@app.route("/tag", methods=["GET", "POST"])
@login_required
def tag():
    images = request.args.get("croppedImages")
    documentID = request.args.get("documentID")
    if images is None:
        return "server error: 'croppedImages' not found", 500
    if documentID is None:
        return "server error: 'documentID' not found", 500
    images = json.loads(images)
    logging.info(images)
    session['tag']['documentID'] = documentID
    session['tag']['croppedImages'] = images
    return render_template("tag.html", images=images, documentID=documentID, pageNum=session['tag']['pageNum'])
  
@app.route("/saveTaggedData", methods=["GET", "POST"])
@login_required
def saveTaggedData():
    data = request.form
    print("Received: ", data["question"], data["topic"])
    return redirect(url_for('tag', documentID=session['tag']['documentID'], croppedImages=json.dumps(session['tag']['croppedImages'])))
    
@app.route("/edit", methods=["POST", "GET"])
@login_required
def editor():
    if request.method == "POST":
        scriptDir = os.path.dirname(__file__)
        # Handle data submitted from current page (the page user is at when he clicks submit)
        # We can do so by saving data here to sessions, then extract from there
        data = json.loads(list(request.form)[0])
        documentID = data['_currDocumentID']
        saveAnnotationsToSession(data)
        annotationsData = session['edit']['curAnnotations']
        croppedImages = []
        for canvasID in annotationsData:
            if canvasID == '_currDocumentID':
                continue
            pageID = int(canvasID.split('-')[1])
            baseImageDir = os.path.join(scriptDir, 'static/pages', Pages.query.filter_by(id=pageID).first().databaseName)
            logging.info(baseImageDir)
            submittedAnnotations = {}
            databaseAnnotations = {}
            for rects in annotationsData[canvasID]:
                submittedAnnotations[(rects['startX'], rects['startY'], rects['endX'], rects['endY'])] = None
            for annotation in ExtractedImages.query.filter_by(pageID=pageID).all():
                if (annotation.topX, annotation.topY, annotation.bottomX, annotation.bottomY) not in submittedAnnotations:
                    fileDir = annotation.databaseName
                    os.remove(os.path.join(scriptDir, app.config['EXTRACTED'], fileDir))
                    db.session.delete(annotation)
                else:
                    databaseAnnotations[(annotation.topX, annotation.topY, annotation.bottomX, annotation.bottomY)] = (annotation.id, annotation.databaseName)
            db.session.commit()
            for rects in submittedAnnotations:
                if rects in databaseAnnotations:
                    croppedImages.append(databaseAnnotations[rects])
                else:
                    img = cropImage(baseImageDir, rects)
                    # Save images
                    randomName = generateRandomName() + '.png'
                    imageDir = os.path.join(scriptDir, app.config['EXTRACTED'], randomName)
                    img.save(imageDir)
                    extractedImage = ExtractedImages(pageID=pageID, databaseName=randomName,
                                                    topX=rects[0], topY=rects[1], 
                                                    bottomX=rects[2], bottomY=rects[3])
                    db.session.add(extractedImage)
                    db.session.commit()
                    croppedImages.append((extractedImage.id, randomName))
        
        session['tag'] = {}
        session['tag']['pageNum'] = 0
        return redirect(url_for('tag', croppedImages=json.dumps(croppedImages), documentID=documentID))

    document = request.args.get('document')
    if document is None:
        return "server error: 'document' not found", 500
    logging.info(session)
    return render_template("editor.html", document=json.loads(document), pageNum = session['edit']['curPageNum'], 
                                           annotations = session['edit']['curAnnotations'])

@app.route("/nextPage", methods=["POST"])
@login_required
def nextPage():
    if (session['edit']['curPageNum'] < len(session['edit']['curDoc'][1])):
        data = json.loads(list(request.form)[0])
        saveAnnotationsToSession(data)
        session['edit']['curPageNum'] += 1
    return redirect(url_for("editor", document=json.dumps(session['edit']['curDoc'])))
  
@app.route("/prevPage", methods=["POST"])
@login_required
def prevPage():
    if (session['curPageNum'] > 1):
        data = json.loads(list(request.form)[0])
        saveAnnotationsToSession(data)
        session['curPageNum'] -= 1
    return redirect(url_for("editor", document=json.dumps(session['curDoc'])))

@app.route("/nextImage", methods=["POST"])
@login_required
def nextImage():
    if (session['tag']['pageNum'] + 1 < len(session['tag']['croppedImages'])):
        session['tag']['pageNum'] += 1
    return redirect(url_for("tag", croppedImages=json.dumps(session['tag']['croppedImages']), documentID=session['tag']['documentID'], _scheme="https", _external=True))

@app.route("/prevImage", methods=["POST"])
@login_required
def prevImage():
    if (session['tag']['pageNum'] > 0):
        session['tag']['pageNum'] -= 1
    return redirect(url_for("tag", croppedImages=json.dumps(session['tag']['croppedImages']), documentID=session['tag']['documentID'], _scheme="https", _external=True))

@app.route("/uploadFiles", methods=["POST"])
@login_required
def uploadFiles():
    files = request.files.getlist('filepicker')
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
        extractPdfPages(filePath, documentID=document.id)
    
    return redirect(url_for("manage", _scheme="https", _external=True))

@app.route("/manage", methods=["GET", "POST"])
@login_required
def manage():
    allDocuments = DocumentUploads.query.all()
    completed = []
    uncompleted = []
    for document in allDocuments:
        # Get first page for preview
        firstPage = Pages.query.filter_by(documentID=document.id).first().databaseName
        if document.percentageCompleted == 100:
            CompletedDocument = namedtuple('CompletedDocument', ['id', 'name', 'previewPageName', 'warnings'])
            warnings = []
            # Add code to fill warnings here
            completed.append(CompletedDocument(id=document.id, name=document.originalName, previewPageName=firstPage, warnings=warnings))
        else:
            UncompletedDocument = namedtuple('UncompletedDocument', ['id', 'name', 'previewPageName', 'percentageCompleted'])
            uncompleted.append(UncompletedDocument(id=document.id, name=document.originalName, previewPageName=firstPage, percentageCompleted=document.percentageCompleted))
    logging.info(completed)
    return render_template("manage.html", completed=completed, uncompleted=uncompleted)

@app.route("/redirectEdit", methods=["GET", "POST"])
@login_required
def redirectEdit():
    if request.method == "POST":
        data = json.loads(list(request.form)[0])
        thisDocumentObj = DocumentUploads.query.filter_by(id=data['documentID']).first()
        allPages = Pages.query.filter_by(documentID=data['documentID']).all()
        essentialPagesInfo = [(page.id, page.pageNo, page.databaseName) for page in allPages]
        document = [thisDocumentObj.originalName, essentialPagesInfo, thisDocumentObj.id]
        for key in list(session.keys()):
            session.pop(key)
        session['edit'] = {}
        session['edit']['curDoc'] = document
        session['edit']['curPageNum'] = 1
        session['edit']['curAnnotations'] = {}
        # Load annotations that had already been done before
        for page in allPages:
            alreadyExtracted = ExtractedImages.query.filter_by(pageID=page.id).all()
            if len(alreadyExtracted) != 0:
                canvasID = "page-" + str(page.id)
                session['edit']['curAnnotations'][canvasID] = []
            for extracted in alreadyExtracted:
                rect = {}
                rect['startX'] = extracted.topX
                rect['startY'] = extracted.topY
                rect['endX'] = extracted.bottomX
                rect['endY'] = extracted.bottomY
                session['edit']['curAnnotations'][canvasID].append(rect)
        logging.info("session" + str(session))
        logging.info("DOCUMENT: \n " + str(document))
        return redirect(url_for("editor", document=json.dumps(session['edit']['curDoc']),
                                          annotations=session['edit']['curAnnotations']))
    else:
        return "Unauthorised Access", 503
      

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("root", _scheme="https", _external=True))
  
@app.route("/home")
@login_required
def home():
    return render_template("home.html")
    
@app.route("/", methods=["GET", "POST"])
def root():
    if request.method == "POST":
        if request.form['formName'] == 'signup':
            signupForm = SignupForm(request.form)
            if signupForm.validate_on_submit():
                newUser = Users(username=signupForm.username.data.strip())
                newUser.set_password(signupForm.password.data)
                db.session.add(newUser)
                db.session.commit()
                return loginUser(signupForm.username.data.strip(), signupForm.remember_me.data)
            else:
                return render_template("index.html", loginForm=LoginForm(), signupForm=signupForm)
        elif request.form['formName'] == 'login':
            loginForm = LoginForm(request.form)
            if loginForm.validate_on_submit():
                return loginUser(loginForm.username.data.strip(), loginForm.remember_me.data)
            else:
                return render_template("index.html", loginForm=loginForm, signupForm=SignupForm())
        else:
            print("Shouldn't be here.")
    else:
        return render_template("index.html", loginForm=LoginForm(), signupForm=SignupForm())