import requests
import json

def menu_principal():
    while True:
        print("\n--- Menu Principal ---")
        print("1. Inserir Usuário")
        print("2. Consultar Usuário")
        print("3. Alterar Usuário")
        print("4. Excluir Usuário")
        print("5. Sair")

        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            inserir_usuario()
        elif opcao == "2":
            consultar_usuario()
        elif opcao == "3":
            alterar_usuario()
        elif opcao == "4":
            excluir_usuario()
        elif opcao == "5":
            print("Saindo do programa...")
            break
        else:
            print("Opção inválida! Tente novamente.")

def inserir_usuario():
    print("\n--- Inserir Usuário ---")
    login = input("Digite o login: ")
    email = input("Digite o email: ")
    senha = input("Digite a senha: ")

    dados = {"login": login, "email": email, "senha": senha}

    resposta = requests.post("http://localhost:5000/api/usuarios", json=dados)
    print(resposta.json().get("mensagem", resposta.json().get("erro")))

def consultar_usuario():
    print("\n--- Consultar Usuário ---")
    login = input("Digite o login do usuário: ")

    resposta = requests.get(f"http://localhost:5000/api/usuarios/{login}")
    
    if resposta.status_code == 200:
        try:
            dados = resposta.json()
            print(f"Login: {dados['login']}\nEmail: {dados['email']}")

            nome_arquivo = f"usuario_{login}.json"
            with open(nome_arquivo, "w") as file:
                json.dump(dados, file, indent=4)
            
            print(f"Dados exportados para o arquivo {nome_arquivo}")
        except ValueError:
            print("Erro: resposta não contém um JSON válido.")
    else:
        try:
            erro = resposta.json().get("erro", "Erro desconhecido")
            print(erro)
        except ValueError:
            print("Erro ao consultar usuário: resposta não contém JSON.")


def alterar_usuario():
    print("\n--- Alterar Usuário ---")
    login = input("Digite o login do usuário: ")
    email = input("Digite o novo email (deixe vazio para não alterar): ")
    senha = input("Digite a nova senha (deixe vazio para não alterar): ")

    dados = {}
    if email:
        dados["email"] = email
    if senha:
        dados["senha"] = senha

    resposta = requests.put(f"http://localhost:5000/api/usuarios/{login}", json=dados)
    
    if resposta.status_code == 200:
        print(resposta.json().get("mensagem", "Alteração realizada com sucesso."))
    else:
        try:
            erro = resposta.json().get("erro", "Erro desconhecido")
            print(erro)
        except ValueError:
            print("Erro ao alterar usuário: resposta não contém JSON.")

def excluir_usuario():
    print("\n--- Excluir Usuário ---")
    login = input("Digite o login do usuário: ")

    resposta = requests.delete(f"http://localhost:5000/api/usuarios/{login}")
    
    if resposta.status_code == 200:
        print(resposta.json().get("mensagem", "Usuário excluído com sucesso."))
    else:
        try:
            erro = resposta.json().get("erro", "Erro desconhecido")
            print(erro)
        except ValueError:
            print("Erro ao excluir usuário: resposta não contém JSON.")

if __name__ == "__main__":
    menu_principal()
