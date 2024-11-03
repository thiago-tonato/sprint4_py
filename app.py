from flask import Flask, request, jsonify
import requests
import cx_Oracle
from werkzeug.security import generate_password_hash

app = Flask(__name__)

API_KEY = "6e3346034fe8483bd104df262b4f1cc95214bd4b"

# Função que verifica e-mail usando API Externa do Hunter.IO
def verificar_email(email):
    url = f"https://api.hunter.io/v2/email-verifier?email={email}&api_key={API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        if data["data"]["result"] == "deliverable":
            return {"email": email, "status": "válido"}
        else:
            return {"email": email, "status": "inválido"}
    else:
        return {
            "erro": "Erro ao verificar o email",
            "status_code": response.status_code,
        }

# Função para carregar as credenciais do banco de dados a partir de um arquivo .txt
def carregar_credenciais():
    credenciais = {}
    with open("db_credentials.txt", "r") as file:
        for line in file:
            key, value = line.strip().split("=")
            credenciais[key] = value
    return credenciais

# Função para conectar ao Oracle Database usando as credenciais do arquivo .txt
def conectar_oracle():
    credenciais = carregar_credenciais()
    dsn_tns = cx_Oracle.makedsn(
        host=credenciais["host"],
        port=credenciais["port"],
        sid=credenciais["sid"]
    )
    conn = cx_Oracle.connect(
        user=credenciais["user"],
        password=credenciais["password"],
        dsn=dsn_tns
    )
    return conn

# Função para cadastrar o usuário no banco de dados Oracle
@app.route("/api/usuarios", methods=["POST"])
def cadastrar_usuario():
    dados = request.get_json()
    login = dados.get("login")
    email = dados.get("email")
    senha = dados.get("senha")

    resultado = verificar_email(email)
    if resultado["status"] != "válido":
        return jsonify({"erro": "Email inválido"}), 400

    try:
        conn = conectar_oracle()
        cursor = conn.cursor()
        senha_hash = generate_password_hash(senha)

        cursor.execute(
            "INSERT INTO usuarios_1 (login, email, senha) VALUES (:1, :2, :3)",
            (login, email, senha_hash),
        )
        conn.commit()

        return {"status": "sucesso", "mensagem": "Usuário cadastrado com sucesso."}
    except cx_Oracle.IntegrityError:
        return {"status": "erro", "mensagem": "Usuário já cadastrado."}
    except Exception as e:
        return {"status": "erro", "mensagem": f"Erro: {str(e)}"}
    finally:
        if conn:
            conn.close()

# Consultar usuários
@app.route("/api/usuarios/<login>", methods=["GET"])
def consultar_usuario(login):
    try:
        conn = conectar_oracle()
        cursor = conn.cursor()
        cursor.execute("SELECT login, email FROM usuarios WHERE login = :1", (login,))
        row = cursor.fetchone()

        if row:
            return jsonify({"login": row[0], "email": row[1]})
        else:
            return jsonify({"erro": "Usuário não encontrado"}), 404
    finally:
        if conn:
            conn.close()

# Atualizar usuário
@app.route("/api/usuarios/<login>", methods=["PUT"])
def atualizar_usuario(login):
    dados = request.get_json()
    email = dados.get("email")
    senha = dados.get("senha")

    try:
        conn = conectar_oracle()
        cursor = conn.cursor()

        if email:
            cursor.execute("UPDATE usuarios SET email = :1 WHERE login = :2", (email, login))

        if senha:
            senha_hash = generate_password_hash(senha)
            cursor.execute("UPDATE usuarios SET senha = :1 WHERE login = :2", (senha_hash, login))

        conn.commit()
        return jsonify({"mensagem": "Usuário atualizado com sucesso"})
    except Exception as e:
        return jsonify({"erro": f"Erro ao atualizar usuário: {str(e)}"})
    finally:
        if conn:
            conn.close()

# Excluir usuário
@app.route("/api/usuarios/<login>", methods=["DELETE"])
def excluir_usuario(login):
    try:
        conn = conectar_oracle()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM usuarios WHERE login = :1", (login,))
        conn.commit()

        return jsonify({"mensagem": "Usuário excluído com sucesso"})
    except Exception as e:
        return jsonify({"erro": f"Erro ao excluir usuário: {str(e)}"})
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    app.run(debug=True)
