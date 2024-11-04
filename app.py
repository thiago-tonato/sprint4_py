from flask import Flask, request, jsonify
import requests
import oracledb 
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

API_KEY = "6e3346034fe8483bd104df262b4f1cc95214bd4b"


def verificar_email(email):
    url = f"https://api.hunter.io/v2/email-verifier?email={email}&api_key={API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        try:
            data = response.json() 
            if data["data"]["result"] == "deliverable":
                return {"email": email, "status": "válido"}
            else:
                return {"email": email, "status": "inválido"}
        except ValueError:
            return {"erro": "Erro ao decodificar a resposta JSON"}
    else:
        return {
            "erro": "Erro ao verificar o email",
            "status_code": response.status_code,
            "response_text": response.text 
        }


def carregar_credenciais():
    credenciais = {}
    with open("credenciais.txt", "r") as file:
        for line in file:
            key, value = line.strip().split("=")
            credenciais[key] = value
    return credenciais


def conectar_oracle():
    credenciais = carregar_credenciais()
    conn = oracledb.connect(
        user=credenciais["user"],
        password=credenciais["password"],
        dsn=f"{credenciais['host']}:{credenciais['port']}/{credenciais['sid']}"
    )
    return conn


@app.route("/api/usuarios", methods=["POST"])
def cadastrar_usuario():
    dados = request.get_json()
    print("Dados recebidos:", dados) 
    login = dados.get("login")
    email = dados.get("email")
    senha = dados.get("senha")

    
    if not login or not email or not senha:
        return jsonify({"erro": "Campos 'login', 'email' e 'senha' são obrigatórios"}), 400

    resultado = verificar_email(email)
    if resultado.get("status") != "válido":
        return jsonify({"erro": "Email inválido"}), 400

    conn = None 
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
    except oracledb.IntegrityError:
        return {"status": "erro", "mensagem": "Usuário já cadastrado."}
    except Exception as e:
        return {"status": "erro", "mensagem": f"Erro: {str(e)}"}
    finally:
        if conn:
            conn.close()


@app.route("/api/usuarios/<login>", methods=["GET"])
def consultar_usuario(login):
    print(f"Consultando usuário com login: {login}") 
    conn = None
    try:
        conn = conectar_oracle()
        cursor = conn.cursor()
        cursor.execute("SELECT login, email FROM usuarios_1 WHERE login = :login", {"login": login})
        resultado = cursor.fetchone()

        if resultado:
            usuario = {"login": resultado[0], "email": resultado[1]}
            return jsonify(usuario), 200
        else:
            return jsonify({"erro": "Usuário não encontrado"}), 404
    except Exception as e:
        print(f"Erro ao consultar usuário: {e}")  
        return jsonify({"erro": f"Erro ao consultar usuário: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()
            
@app.route("/api/usuarios/<login>", methods=["PUT"])
def alterar_usuario(login):
    conn = None
    try:
        conn = conectar_oracle()
        cursor = conn.cursor()

        dados = request.get_json()
        email = dados.get("email")
        senha = dados.get("senha")
        
        if email:
            cursor.execute("UPDATE usuarios_1 SET email = :1 WHERE login = :2", (email, login))
        if senha:
            senha_hash = generate_password_hash(senha)
            cursor.execute("UPDATE usuarios_1 SET senha = :1 WHERE login = :2", (senha_hash, login))

        conn.commit()

        return jsonify({"mensagem": "Usuário alterado com sucesso."}), 200
    except Exception as e:
        return jsonify({"erro": f"Erro ao alterar usuário: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()
            
@app.route("/api/usuarios/<login>", methods=["DELETE"])
def excluir_usuario(login):
    print(f"Excluindo usuário: {login}") 
    conn = None
    try:
        conn = conectar_oracle()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM usuarios_1 WHERE login = :1", (login,))
        if cursor.rowcount == 0:
            return jsonify({"erro": "Usuário não encontrado."}), 404

        conn.commit()
        return jsonify({"mensagem": "Usuário excluído com sucesso."}), 200
    except Exception as e:
        print(f"Erro ao excluir usuário: {e}")
        return jsonify({"erro": f"Erro ao excluir usuário: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

@app.route("/api/usuarios/login", methods=["POST"])
def login_usuario():
    dados = request.get_json()
    login = dados.get("login")
    senha = dados.get("senha")
    
    if not login or not senha:
        return jsonify({"erro": "Campos 'login' e 'senha' são obrigatórios"}), 400

    conn = None
    try:
        conn = conectar_oracle()
        cursor = conn.cursor()
        
        cursor.execute("SELECT senha FROM usuarios_1 WHERE login = :login", {"login": login})
        resultado = cursor.fetchone()
        
        if resultado:
            senha_hash = resultado[0]
            print(f"Senha armazenada (hash): {senha_hash}")
            print(f"Senha fornecida: {senha}")

            if check_password_hash(senha_hash, senha):
                return jsonify({"mensagem": "Login realizado com sucesso."}), 200
            else:
                return jsonify({"erro": "Senha incorreta"}), 401
        else:
            return jsonify({"erro": "Usuário não encontrado"}), 404
    except Exception as e:
        print(f"Erro ao realizar login: {e}")
        return jsonify({"erro": f"Erro ao realizar login: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    app.run(debug=True)
