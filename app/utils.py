# File: ielts-scorer/app/utils.py
import shortuuid

def generate_short_id():
    """Generates a short, unique ID."""
    return shortuuid.uuid()