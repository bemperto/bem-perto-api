# BemPerto - Backend/API

Backend Python para sistema de monitoramento de presença via RFID em instituições de ensino.

## Setup

```bash
# Criar ambiente virtual
python -m venv .venv

# Ativar ambiente
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Instalar dependências
pip install pyserial
```

## Uso

### Modo Interativo (Menu)
```bash
python main.py
```
Interface CLI para gerenciar usuários (adicionar, visualizar, atualizar, remover).

### Modo Serviço (Controle de Acesso)
```bash
python main.py --service
```
Executa serviço persistente que aguarda requisições do Arduino e processa autenticações RFID automaticamente.

## Comunicação com Arduino

### Conexão Linux
- **Bluetooth**: `/dev/rfcomm0` (HC-05)
- **USB Serial**: `/dev/ttyACM0`
- **Baudrate**: 9600

### Conexão Windows
- **Bluetooth HC-05**: `COM3`, `COM4`, `COM5`, etc.
- **USB Serial**: `COM3`, `COM4`, etc.
- **Baudrate**: 9600

**Como descobrir a porta COM no Windows:**
1. Abra o Gerenciador de Dispositivos
2. Expanda "Portas (COM e LPT)"
3. Procure por "HC-05" ou "USB Serial Port"
4. Anote o número da porta (ex: COM4)

**Modificação necessária no código (Windows):**

No arquivo `main.py`, altere as linhas:
```python
# Linux:
ser = serial.Serial("/dev/rfcomm0", baudrate=9600, timeout=1)

# Windows:
ser = serial.Serial("COM4", baudrate=9600, timeout=1)  # Substitua COM4 pela sua porta
```

Isso se aplica às funções:
- `ler_rfid_arduino()` (linha ~18)
- `run_access_control_service()` (linha ~344)

### Protocolo JSON

**Requisição de autenticação (Arduino → Python):**
```json
{"type": "auth_request", "uid": "A1B2C3D4"}
```

**Resposta de autorização (Python → Arduino):**
```json
{"type": "auth_response", "uid": "A1B2C3D4", "access": true, "name": "João Silva"}
```

**Resposta de negação:**
```json
{"type": "auth_response", "uid": "A1B2C3D4", "access": false, "reason": "user_not_found"}
```

## Arquivos

- `main.py` - Backend principal com CRUD e controle de acesso
- `art.py` - Arte ASCII do logo BemPerto
- `my.db` - Banco de dados SQLite
