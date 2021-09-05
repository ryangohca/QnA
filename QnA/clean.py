import os

def clean_directories(delete_session_only=True):
    dir = os.path.dirname(__file__)
    pages = f"{dir}/static/pages"
    upload = f"{dir}/static/upload"
    extracted = f"{dir}/static/extracted"

    parent = os.path.dirname(dir)
    sessions = f"{parent}/flask_session"

    for directory in ([sessions] if delete_session_only else [pages, upload, extracted, sessions]):
        for filename in os.listdir(directory):
            f = os.path.join(directory, filename)
            if not filename.endswith('.txt'):
                os.remove(f)
                print(f)
