import os

from QnA import app

@app.route('/')
def test():
    return "hi!", 200
 
# Bind to PORT if defined, otherwise default to 5000.
port = int(os.environ.get('PORT', 5000))
app.run(host='0.0.0.0', port=port)
