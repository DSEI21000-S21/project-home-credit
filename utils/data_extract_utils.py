import io
import zipfile

def extract_zip(content):
    with zipfile.ZipFile(io.BytesIO(content)) as thezip:
        for zipinfo in thezip.infolist():
            with thezip.open(zipinfo) as thefile:
                yield zipinfo.filename, thefile