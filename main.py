import sqlite3
import serial
import json
import sys
import time
from art import bem_perto_art

conn = sqlite3.connect("my.db")

def criar_tabela():
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS pessoas(uuid text primary key,nome text,idade integer, profissao text)")

def ler_rfid_arduino():
    """Lê dados do Arduino e aguarda especificamente uma mensagem de acesso RFID"""
    ser = None
    try:
        ser = serial.Serial("/dev/rfcomm0", baudrate=9600, timeout=1)
        ser.reset_input_buffer()
        print("\n🔍 Aguardando leitura do cartão RFID...")
        print("   (Aproxime o cartão no leitor)")

        import time
        inicio = time.time()
        timeout_total = 30  # 30 segundos para passar o cartão

        while time.time() - inicio < timeout_total:
            linha = ser.readline().decode('utf-8').strip()

            if linha:
                try:
                    dados = json.loads(linha)
                    tipo = dados.get('type')

                    # Ignora keepalives silenciosamente
                    if tipo == "keepalive":
                        print("   .", end='', flush=True)
                        continue

                    # Ignora debug do Arduino
                    elif linha.startswith("[ARDUINO DEBUG]"):
                        continue

                    # Ignora outras mensagens (ready, status, etc)
                    elif tipo not in ["access", "auth_request"]:
                        continue

                    # Encontrou requisição de leitura de cartão!
                    if "uid" in dados:
                        print(f"\n✓ Cartão detectado!")
                        print(f"  UID: {dados['uid']}")
                        # Retorna apenas o UID para o menu usar
                        return {"uid": dados['uid']}
                    else:
                        print("\n⚠ Mensagem sem UID")
                        return None

                except json.JSONDecodeError:
                    continue  # Ignora linhas com JSON inválido

        # Timeout atingido
        print(f"\n✗ Timeout: Nenhum cartão detectado em {timeout_total} segundos")
        return None

    except serial.SerialException as e:
        print(f"\n✗ Erro na conexão serial: {e}")
        print("   Verifique se o Bluetooth está conectado")
        return None
    except Exception as e:
        print(f"\n✗ Erro na leitura RFID: {e}")
        return None
    finally:
        if ser and ser.is_open:
            ser.close()

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
        dados_rfid = ler_rfid_arduino()

        if not dados_rfid:
            print("Falha na leitura do RFID. Tente novamente.")
            return

        uuid_usuario = dados_rfid["uid"]
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

def criar_tabela_logs():
    """Cria tabela de logs e índices"""
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS access_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uid TEXT NOT NULL,
            user_name TEXT,
            authorized BOOLEAN NOT NULL,
            reason TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_at INTEGER NOT NULL
        )
    """)

    # Criar índices
    cur.execute("CREATE INDEX IF NOT EXISTS idx_access_logs_uid ON access_logs(uid)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_access_logs_timestamp ON access_logs(timestamp DESC)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_access_logs_authorized ON access_logs(authorized)")

    conn.commit()

def check_user_access(uid):
    """Verifica se usuário está autorizado"""
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT uuid, nome, idade, profissao FROM pessoas WHERE uuid = ?",
            (uid,)
        )
        usuario = cur.fetchone()

        if usuario:
            return True, {
                "uuid": usuario[0],
                "nome": usuario[1],
                "idade": usuario[2],
                "profissao": usuario[3]
            }
        return False, None
    except sqlite3.Error as e:
        print(f"Erro no banco: {e}")
        return False, None

def log_access_attempt(uid, authorized, user_name=None, reason=None):
    """Registra tentativa de acesso no banco"""
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO access_logs (uid, user_name, authorized, reason, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (uid, user_name, authorized, reason, int(time.time())))
        conn.commit()

        status = "✓ AUTORIZADO" if authorized else "✗ NEGADO"
        print(f"[{status}] {uid} | {user_name or 'Desconhecido'}")
    except sqlite3.Error as e:
        print(f"Erro ao registrar log: {e}")

def send_auth_response(ser, uid, access, name=None, reason=None):
    """Envia resposta JSON ao Arduino"""
    response = {
        "type": "auth_response",
        "uid": uid,
        "access": access
    }

    if access and name:
        response["name"] = name
    elif not access and reason:
        response["reason"] = reason

    # JSON compacto (sem espaços) para Arduino parsear corretamente
    json_str = json.dumps(response, separators=(',', ':'))
    print(f"[DEBUG] Enviando resposta: {json_str}")
    print(f"[DEBUG] Tamanho: {len(json_str)} bytes")
    ser.write((json_str + "\n").encode('utf-8'))
    ser.flush()
    print(f"[DEBUG] Resposta enviada!")

def handle_auth_request(ser, request):
    """Processa requisição e responde ao Arduino"""
    uid = request.get("uid")

    if not uid:
        send_auth_response(ser, "", False, reason="invalid_request")
        log_access_attempt(uid="INVALID", authorized=False, reason="missing_uid")
        return

    # Consulta banco de dados
    authorized, user_data = check_user_access(uid)

    if authorized:
        send_auth_response(ser, uid, True, name=user_data["nome"])
        log_access_attempt(uid=uid, authorized=True, user_name=user_data["nome"])
    else:
        send_auth_response(ser, uid, False, reason="user_not_found")
        log_access_attempt(uid=uid, authorized=False, reason="user_not_found")

def run_access_control_service():
    """Serviço persistente de controle de acesso"""
    ser = None
    try:
        # Conexão Bluetooth via HC-05
        ser = serial.Serial("/dev/rfcomm0", baudrate=9600, timeout=0.5)
        ser.reset_input_buffer()

        print("🔐 Serviço de Controle de Acesso Iniciado")
        print("   Aguardando requisições do Arduino...")

        while True:
            try:
                linha = ser.readline().decode('utf-8', errors='ignore').strip()

                if not linha:
                    continue

                # DEBUG: Mostrar tudo que chega
                print(f"[DEBUG] Recebido: {linha}")

                try:
                    dados = json.loads(linha)
                    tipo = dados.get('type')

                    if tipo == "auth_request":
                        print(f"[DEBUG] Processando auth_request para UID: {dados.get('uid')}")
                        handle_auth_request(ser, dados)
                    elif tipo == "keepalive":
                        print("[DEBUG] Keepalive recebido")
                except json.JSONDecodeError:
                    print(f"JSON inválido: {linha}")

            except KeyboardInterrupt:
                print("\n\nEncerrando serviço...")
                break
            except Exception as e:
                print(f"Erro: {e}")
                time.sleep(1)

    except serial.SerialException as e:
        print(f"Erro na conexão serial: {e}")
        print("Verifique se o Bluetooth está conectado em /dev/rfcomm0")
    finally:
        if ser and ser.is_open:
            ser.close()

# Programa Bem Perto
criar_tabela()
criar_tabela_logs()

# Verificar modo de operação
if len(sys.argv) > 1 and sys.argv[1] == "--service":
    # Modo serviço (loop contínuo para controle de acesso)
    run_access_control_service()
else:
    # Modo menu interativo (padrão)
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
