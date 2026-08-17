import requests



if __name__ == '__main__':
    data = requests.post("http://10.100.5.154/node/api/v1/common/nacl-public-key").json()
    key = data.get("signSk")
    print(key)
    server_public_key_hex = key
    password = "tingyu@123"
    encrypted_password = encrypt(password,server_public_key_hex)
    username = "liyazhou"
    print(encrypted_password)
    login_url = 'http://10.100.5.154/node/api/v1/common/login'
    payload = {
        "mode":"password",
        "password":encrypted_password,
        "username":username
    }
    response = requests.post(login_url, json=payload)
    print(response.text)
    request = response.request
    print(request.body)
