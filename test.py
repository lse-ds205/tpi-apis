import requests

url = "http://127.0.0.1:8000/v1/country-data/Italy/2024"

response = requests.get(url)

# Confirm that the request was successful
assert response.status_code == 200

# Get the response as a JSON object
data = response.json()