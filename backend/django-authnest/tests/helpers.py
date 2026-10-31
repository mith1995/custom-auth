import io
import re
from urllib.parse import parse_qs, urlparse

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.test import APIClient

from authnest.services.tokens import issue_tokens

def extract_token(message):
    # Email ki body se link nikalo, phir link ke ?token=... ko decode karke wapas do
    link = re.search(r"https?://\S+", message.body).group(0)
    return parse_qs(urlparse(link).query)["token"][0]

def make_image(name="photo.png", size=(10, 10), fmt="PNG"):
    buffer = io.BytesIO()
    Image.new("RGB", size, "red").save(buffer, format=fmt)
    return SimpleUploadedFile(
        name, buffer.getvalue(), content_type=f"image/{fmt.lower()}"
    )


def client_for(user):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {issue_tokens(user)['access']}")
    return client