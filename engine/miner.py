import requests
import re

def extract_email(url):
    try:
        if not url: return None
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, timeout=5, headers=headers)
        # Regex profissional de email
        pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        matches = re.findall(pattern, response.text)
        return matches[0] if matches else None
    except:
        return None