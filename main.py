from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

API_KEY = '6e3346034fe8483bd104df262b4f1cc95214bd4b'

# Função que verifica e-mail usando API Externa do Hunter.IO
def verificar_email(email):
    url = f"https://api.hunter.io/v2/email-verifier?email={email}&api_key={API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        if data['data']['result'] == 'deliverable':
            return {"email": email, "status": "válido"}
        else:
            return {"email": email, "status": "inválido"}
    else:
        return {"erro": "Erro ao verificar o email", "status_code": response.status_code}

# Endpoint para verificar o email via POST
@app.route('/api/verificar-email', methods=['POST'])
def verificar_email_api():
    # Extraindo o email do corpo da requisição POST
    dados = request.get_json()
    email = dados.get('email')

    if not email:
        return jsonify({"erro": "Nenhum email fornecido"}), 400

    # Verificando o email
    resultado = verificar_email(email)
    return jsonify(resultado)

# Executar o servidor Flask
if __name__ == '__main__':
    app.run(debug=True)
