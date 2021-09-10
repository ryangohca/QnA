import json
import os
import random
import string
import logging
from collections import namedtuple

from flask import render_template, request, flash, url_for, redirect, make_response, session, jsonify
from flask_login import current_user, login_required, login_user, logout_user
from PIL import Image
import fitz #pymupdf legacy name is fitz
from docx2pdf import convert
from werkzeug.routing import BuildError
from werkzeug.datastructures import MultiDict

from QnA import app, db, sess, login
from QnA.models import Users, DocumentUploads, Pages, ExtractedImages, Questions, Answers, getAllPaperTitles
from QnA.forms import LoginForm, SignupForm, TagForm

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

def clearSession(key):
    session.pop(key)

def loginUser(username, remember_me):
    user = Users.query.filter_by(username=username).first()
    login_user(user, remember=remember_me)
    next_page = request.args.get("next")
    if not next_page:
        next_page = 'home'
    try:
        return redirect(url_for(next_page, _scheme="https", _external=True))
    except BuildError: #User tries to manually key in next, but no defined route here
        return redirect(url_for('home', _scheme="https", _external=True))

def getTaggingData(imageID):
    question = Questions.query.get(imageID)
    if question is not None:
        data = {}
        data['imageType'] = 'question'
        data['subject'] = question.subject
        data['topic'] = question.topic
        data['year'] = question.year
        data['paper'] = question.paper
        data['questionNo'] = question.questionNo
        data['questionPart'] = question.questionPart
        return MultiDict(data)
    answer = Answers.query.get(imageID)
    if answer is not None:
        data = {}
        data['imageType'] = 'answer'
        data['answer'] = answer.answerText
        data['questionDocument'] = answer.questionDocumentID
        if answer.questionID is not None:
            question = Questions.query.get(answer.questionID)
            data['paperSelect'] = str(question.year) + '^%$' + question.paper
            data['questionNo'] = question.questionNo
            data['questionPart'] = question.questionPart
        else:
            if answer.qnPaper is not None:
                if answer.qnYear is None:
                    data['paperSelect'] = "noyear^%$" + answer.qnPaper
                else:
                    data['paperSelect'] = str(answer.qnYear) + '^%$' + answer.qnPaper
                data['questionNo'] = question.questionNo
                data['questionPart'] = question.questionPart
        return MultiDict(data)
    return None

@login.unauthorized_handler
def unauthorised():
    return redirect(url_for('root', next=request.endpoint, _scheme="https", _external=True))

@app.errorhandler(404)
def notFound(e):
    return render_template("404.html"), 404
  
@app.route("/tag", methods=["GET", "POST"])
@login_required
def tag():
    if request.method == "POST":
        documentID = session['tag']['documentID']
        images = session['tag']['croppedImages']
        pageNum = session['tag']['pageNum']
        currImageID = images[pageNum][0]
        tagform = TagForm(request.form, currImageID=currImageID)
        if tagform.validate_on_submit():
            if tagform.imageType.data == "question":
                currQnRow = Questions.query.get(currImageID)
                if currQnRow is None:
                    currQnRow = Questions(id=currImageID, subject=tagform.subject.data, topic=tagform.topic.data, year=tagform.year.data,
                                        paper=tagform.paper.data, questionNo=tagform.questionNo.data, questionPart=tagform.questionPart.data)
                    db.session.add(currQnRow)
                    db.session.commit()
                else:
                    currQnRow.subject=tagform.subject.data
                    currQnRow.topic=tagform.topic.data
                    currQnRow.year=tagform.year.data
                    currQnRow.paper=tagform.paper.data
                    currQnRow.questionNo=tagform.questionNo.data
                    currQnRow.questionPart=tagform.questionPart.data
                    db.session.commit()
                if tagform.paper.data is not None and tagform.questionNo.data is not None:
                    possibleAnsMatches = Answers.query.filter_by(qnYear=currQnRow.year, qnPaper=currQnRow.paper, questionNo=currQnRow.questionNo, questionPart=currQnRow.questionPart).all()
                    for match in possibleAnsMatches:
                        pageID = ExtractedImages.query.get(match.id).pageID
                        documentID = Pages.query.get(pageID).documentID
                        userID = DocumentUploads.query.get(documentID).userID
                        if userID == current_user.id:
                            match.questionID = currQnRow.id
                            db.session.commit()
                            break
            elif tagform.imageType.data == "answer":
                currAnsRow = Answers.query.get(currImageID)
                if currAnsRow is None:
                    currAnsRow = Answers(id=currImageID, answerText=tagform.answer.data, questionDocumentID=tagform.questionDocument.data, 
                                     questionNo=tagform.questionNo.data, questionPart=tagform.questionPart.data)
                    db.session.add(currAnsRow)
                else:
                    currAnsRow.answer = tagform.answer.data
                    currAnsRow.questionDocumentID=tagform.questionDocument.data 
                    currAnsRow.questionNo=tagform.questionNo.data
                    currAnsRow.questionPart=tagform.questionPart.data
                qnID = None
                if tagform.paperSelect.data != "none" and tagform.questionNo.data is not None:
                    qnYear, qnPaper = tagform.paperSelect.data.split('^%$')
                    print(qnYear, qnPaper)
                    if qnYear == "noyear":
                        qnYear = None
                    else:
                        qnYear = int(qnYear)
                    currAnsRow.qnYear = qnYear
                    currAnsRow.qnPaper = qnPaper
                    possibleQnMatches = Questions.query.filter_by(year=qnYear, paper=qnPaper, questionNo=tagform.questionNo.data, questionPart=tagform.questionPart.data).all()
                    for match in possibleQnMatches:
                        pageID = ExtractedImages.query.get(match.id).pageID
                        documentID = Pages.query.get(pageID).documentID
                        userID = DocumentUploads.query.get(documentID).userID
                        if userID == current_user.id:
                            qnID = match.id
                            break
                currAnsRow.questionID = qnID
                db.session.commit()
        allPaperTitles = getAllPaperTitles(current_user.id)
        return render_template("tag.html", images=images, documentID=documentID, allPaperTitles=allPaperTitles, pageNum=pageNum, form=tagform)
    
    images = request.args.get("croppedImages")
    documentID = request.args.get("documentID")
    if images is None or documentID is None:
        return redirect(url_for('manage', _scheme="https", _external=True))
    images = json.loads(images)
    logging.info(images)
    session['tag']['documentID'] = documentID
    session['tag']['croppedImages'] = images
    pageNum = session['tag']['pageNum']
    currImageID = images[pageNum][0]
    prefill = getTaggingData(currImageID)
    tagform = TagForm(formdata=prefill, currImageID=currImageID)
    allPaperTitles = getAllPaperTitles(current_user.id)
    return render_template("tag.html", images=images, documentID=documentID, allPaperTitles=allPaperTitles, pageNum=pageNum, form=tagform)

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
                    qn = Questions.query.get(annotation.id)
                    if qn is not None:
                        db.session.delete(qn)
                    ans = Answers.query.get(annotation.id)
                    if ans is not None:
                        db.session.delete(ans)
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
        clearSession('edit') 
        session['tag'] = {}
        session['tag']['pageNum'] = 0
        croppedImages.sort(key=lambda item: (Pages.query.filter_by(id=ExtractedImages.query.filter_by(id=item[0]).first().pageID).first().pageNo, ExtractedImages.query.filter_by(id=item[0]).first().topY))
        return redirect(url_for('tag', croppedImages=json.dumps(croppedImages), documentID=documentID))

    document = request.args.get('document')
    if document is None:
        return redirect(url_for('manage', _scheme="https", _external=True))
    logging.info(session)
    return render_template("editor.html", document=json.loads(document), pageNum = session['edit']['curPageNum'], 
                                           annotations = session['edit']['curAnnotations'])

@app.route("/nextPage", methods=["GET", "POST"])
@login_required
def nextPage():
    if request.method == "POST":
        if (session['edit']['curPageNum'] < len(session['edit']['curDoc'][1])):
            data = json.loads(list(request.form)[0])
            saveAnnotationsToSession(data)
            session['edit']['curPageNum'] += 1
        return redirect(url_for("editor", document=json.dumps(session['edit']['curDoc'])))
    else:
        return redirect(url_for("manage", _scheme="https", _external=True))
  
@app.route("/prevPage", methods=["GET", "POST"])
@login_required
def prevPage():
    if request.method == "POST":
        if (session['edit']['curPageNum'] > 1):
            data = json.loads(list(request.form)[0])
            saveAnnotationsToSession(data)
            session['edit']['curPageNum'] -= 1
        return redirect(url_for("editor", document=json.dumps(session['edit']['curDoc'])))
    else:
        return redirect(url_for("home", _scheme="https", _external=True))

@app.route("/nextImage", methods=["GET", "POST"])
@login_required
def nextImage():
    if request.method == "POST":
        if (session['tag']['pageNum'] + 1 < len(session['tag']['croppedImages'])):
            session['tag']['pageNum'] += 1
        return redirect(url_for("tag", croppedImages=json.dumps(session['tag']['croppedImages']), documentID=session['tag']['documentID'], _scheme="https", _external=True))
    else:
        return redirect(url_for('home', _scheme="https", _external=True))
      
@app.route("/prevImage", methods=["GET", "POST"])
@login_required
def prevImage():
    if request.method == "POST":
        if (session['tag']['pageNum'] > 0):
            session['tag']['pageNum'] -= 1
        return redirect(url_for("tag", croppedImages=json.dumps(session['tag']['croppedImages']), documentID=session['tag']['documentID'], _scheme="https", _external=True))
    else:
        return redirect(url_for('home', _scheme="https", _external=True))
      
@app.route("/uploadFiles", methods=["GET", "POST"])
@login_required
def uploadFiles():
    if request.method == "POST":
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
            document = DocumentUploads(userID=current_user.id, originalName=file.filename, databaseName=newName + '.pdf')
            db.session.add(document)
            db.session.commit()
            extractPdfPages(filePath, documentID=document.id)
        return redirect(url_for("manage", _scheme="https", _external=True))
    else:
        return redirect(url_for("home", _scheme="https", _external=True))

@app.route("/manage", methods=["GET", "POST"])
@login_required
def manage():
    allDocuments = DocumentUploads.query.filter_by(userID=current_user.id).all()
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
        return redirect(url_for("manage", _scheme="https", _external=True))
      
@app.route("/library", methods=["GET", "POST"])
@login_required
def library():
    return render_template("library.html")
  
@app.route("/create", methods=["GET", "POST"])
@login_required
def create():
    return render_template("create.html")
      
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("root", _scheme="https", _external=True))
  
@app.route("/home")
@login_required
def home():
    print(session)
    return render_template("home.html")
    
@app.route("/", methods=["GET", "POST"])
def root():
    if current_user.is_authenticated:
        return redirect(url_for('home', _scheme="https", _external=True))
    if request.method == "POST":
        print(request.form)
        if request.form['formName'] == 'signup':
            signupForm = SignupForm(request.form)
            if signupForm.validate_on_submit():
                newUser = Users(username=signupForm.username.data.strip())
                newUser.set_password(signupForm.password.data)
                db.session.add(newUser)
                db.session.commit()
                return loginUser(signupForm.username.data.strip(), signupForm.remember_me.data)
            else:
                return render_template("index.html", loginForm=LoginForm(formdata=None), signupForm=signupForm)
        elif request.form['formName'] == 'login':
            loginForm = LoginForm(request.form)
            if loginForm.validate_on_submit():
                return loginUser(loginForm.username.data.strip(), loginForm.remember_me.data)
            else:
                return render_template("index.html", loginForm=loginForm, signupForm=SignupForm(formdata=None))
        else:
            print("Shouldn't be here.")
    else:
        return render_template("index.html", loginForm=LoginForm(formdata=None), signupForm=SignupForm(formdata=None))