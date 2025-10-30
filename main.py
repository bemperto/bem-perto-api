import sqlite3
from art import bem_perto_art
conn = sqlite3.connect("my.db")

def criar_tabela():
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS pessoas(uuid text primary key,nome text,idade integer, profissao text)")

def adicionar_usuario_com_uuid(pulseira_uuid):
    try:
        nome = str(input("NOME: "))
        idade = int(input("IDADE: "))
        if idade >= 18:
            profissao = str(input("PROFISSÃO: "))
        else:
            profissao = "crianca"

        conn.execute("INSERT INTO pessoas(uuid,nome,idade,profissao) VALUES (?,?,?,?)", (pulseira_uuid, nome, idade, profissao))
        conn.commit()
        print("Usuário adicionado com sucesso!")
        return True
    except ValueError:
        print("Erro: Idade deve ser um número!")
        return False
    except sqlite3.IntegrityError:
        print("Erro: UUID já cadastrado!")
        return False

def ver_usuarios():
    cur = conn.cursor()
    cur.execute("SELECT uuid, nome, idade, profissao FROM pessoas")
    usuarios = cur.fetchall()
    
    if not usuarios:
        print("Nenhum usuário cadastrado!")
        return
    
    print("\n=== USUÁRIOS CADASTRADOS ===")
    for usuario in usuarios:
        print(f"UUID: {usuario[0]} | Nome: {usuario[1]} | Idade: {usuario[2]} | Profissão: {usuario[3]}")

def atualizar_usuario_por_uuid(uuid_busca):
    cur = conn.cursor()

    print("\nO que deseja atualizar?")
    print("1 - Nome")
    print("2 - Idade")
    print("3 - Profissão")
    print("4 - Todos os dados")
    opcao = input("Escolha uma opção: ")

    try:
        if opcao == "1":
            novo_nome = input("Novo nome: ")
            conn.execute("UPDATE pessoas SET nome = ? WHERE uuid = ?", (novo_nome, uuid_busca))

        elif opcao == "2":
            nova_idade = int(input("Nova idade: "))
            conn.execute("UPDATE pessoas SET idade = ? WHERE uuid = ?", (nova_idade, uuid_busca))

        elif opcao == "3":
            nova_profissao = input("Nova profissão: ")
            conn.execute("UPDATE pessoas SET profissao = ? WHERE uuid = ?", (nova_profissao, uuid_busca))

        elif opcao == "4":
            novo_nome = input("Novo nome: ")
            nova_idade = int(input("Nova idade: "))
            if nova_idade >= 18:
                nova_profissao = input("Nova profissão: ")
            else:
                nova_profissao = "crianca"
            conn.execute("UPDATE pessoas SET nome = ?, idade = ?, profissao = ? WHERE uuid = ?",
                        (novo_nome, nova_idade, nova_profissao, uuid_busca))
        else:
            print("Opção inválida!")
            return False

        conn.commit()
        print("Usuário atualizado com sucesso!")
        return True
    except ValueError:
        print("Erro: Idade deve ser um número!")
        return False

def gerenciar_usuario():
    """Função unificada: Adicionar/Atualizar/Visualizar usuário via RFID ou busca manual"""
    cur = conn.cursor()

    print("\n=== GERENCIAR USUÁRIO ===")
    print("Como deseja localizar o usuário?")
    print("[R]FID - Escanear cartão")
    print("[M]anual - Buscar por nome")
    metodo = input(">").upper()

    usuario = None
    uuid_usuario = None

    if metodo == "R":
        print("\nAguardando leitura do cartão RFID...")
        # TODO: INTEGRAÇÃO COM ARDUINO
        uuid_usuario = '31 CF 75 A4' #GENERICO SO PRA FUNCIONAR ESSA PORRA
        print(f"UUID lido: {uuid_usuario}")

        cur.execute("SELECT uuid, nome, idade, profissao FROM pessoas WHERE uuid = ?", (uuid_usuario,))
        usuario = cur.fetchone()

    elif metodo == "M":
        nome_busca = input("\nDigite o nome da pessoa: ")
        cur.execute("SELECT uuid, nome, idade, profissao FROM pessoas WHERE nome = ?", (nome_busca,))
        usuario = cur.fetchone()
        if usuario:
            uuid_usuario = usuario[0]
    else:
        print("Opção inválida!")
        return

    if usuario:
        print("\n=== USUÁRIO ENCONTRADO ===")
        print(f"UUID: {usuario[0]}")
        print(f"Nome: {usuario[1]}")
        print(f"Idade: {usuario[2]}")
        print(f"Profissão: {usuario[3]}")

        print("\nDeseja atualizar os dados? [S/N]")
        opcao = input(">").upper()
        if opcao == "S":
            atualizar_usuario_por_uuid(uuid_usuario)
        elif opcao == "N":
            print("Visualização concluída!")
        else:
            print("Opção inválida!")
    else:
        if metodo == "R":
            print("\n=== NOVO CARTÃO DETECTADO ===")
            print(f"UUID {uuid_usuario} não cadastrado.")
            print("Deseja cadastrar novo usuário? [S/N]")
            opcao = input(">").upper()
            if opcao == "S":
                adicionar_usuario_com_uuid(uuid_usuario)
            else:
                print("Operação cancelada!")
        else:
            print("Usuário não encontrado!")

def remover_usuario():
    """Remove um usuário via busca manual por nome"""
    ver_usuarios()
    cur = conn.cursor()

    nome_busca = input("\nDigite o nome da pessoa que deseja remover: ")

    cur.execute("SELECT * FROM pessoas WHERE nome = ?", (nome_busca,))
    if not cur.fetchone():
        print("Usuário não encontrado!")
        return
    print(f"\nDeseja remover {nome_busca}?")
    print(f"[S]im ou [N]ão")
    opcao = input(">").upper()
    if opcao == "S":
        cur.execute("DELETE FROM pessoas WHERE nome = ?", (nome_busca,))
        conn.commit()
        print("Usuário removido!")
    elif opcao == "N":
        print("Operação Cancelada!")
        return
    else:
        print("Opção inválida!")

# Programa Bem Perto
criar_tabela()

print(bem_perto_art)
print("Bem vindo ao BemPerto.")

while True:
    print("\n=== MENU PRINCIPAL ===")
    print("> O que deseja fazer:")
    print("> 1. Gerenciar usuário")
    print("> 2. Ver todos usuários")
    print("> 3. Remover usuário")
    print("> 4. Sair")

    try:
        usr_select = int(input(">"))

        if usr_select == 1:
            gerenciar_usuario()
        elif usr_select == 2:
            ver_usuarios()
        elif usr_select == 3:
            remover_usuario()
        elif usr_select == 4:
            print("Encerrando o programa...")
            break
        else:
            print("Opção inválida! Escolha entre 1 e 4.")
    except ValueError:
        print("Erro: Digite um número válido!")

conn.close()
