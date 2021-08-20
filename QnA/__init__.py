from flask import Flask

app = Flask(__name__)
app.config['PHOTO_STORAGE'] = 'storage'
app.config['UPLOAD'] = 'upload'

from QnA import views