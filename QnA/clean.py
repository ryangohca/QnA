import os

dir = os.path.dirname(__file__)
pages = f"{dir}/static/pages"
upload = f"{dir}/static/upload"
extracted = f"{dir}/static/extracted"

for directory in [pages, upload, extracted]:
    for filename in os.listdir(directory):
        f = os.path.join(directory, filename)
        if not filename.endswith('.txt'):
            os.remove(f)
            print(f)

    