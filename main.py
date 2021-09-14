import os

from QnA import app

# Bind to PORT if defined, otherwise default to 5000.
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
