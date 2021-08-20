from flask import Flask

app = Flask(__name__)
app.config['EXTRACTED'] = 'extracted'
app.config['UPLOAD'] = 'upload'
app.config['PAGES'] = 'pages'

from QnA import views