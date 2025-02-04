import requests

url = "https://https://d6de82e178c9b5659adbffefc2a1952a.app.az.nuvolos.cloud/proxy/8000//v1/country-data/Italy/2024"

response = requests.get(url)

# Confirm that the request was successful
assert response.status_code == 200

# Get the response as a JSON object
data = response.json()

print(data)