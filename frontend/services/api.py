import requests

BASE_URL = "http://127.0.0.1:8000"

def upload_pdf(file):

    files = {
        "file": (
            file.name,
            file,
            "application/pdf"
        )
    }

    response = requests.post(
        f"{BASE_URL}/upload",
        files=files
    )

    if response.status_code == 200:
        return response.json()

    return None