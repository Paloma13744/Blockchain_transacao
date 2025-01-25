# Blockchain Transação
![image](https://github.com/user-attachments/assets/e9847b5c-c370-411a-a112-f4766a2c5314)

Este projeto implementa um sistema de blockchain para gerenciamento de transações digitais, com a capacidade de minerar blocos, resolver conflitos automaticamente e permitir a criação e validação de transações entre nós conectados. 
Ele foi desenvolvido para simular o funcionamento básico de uma blockchain descentralizada, onde múltiplos nós podem interagir, e um nó central é responsável por iniciar e coordenar o processo.

## Funcionalidades

- **Criação de Blocos**: Cada bloco armazena informações de transações, sendo adicionado à cadeia de forma segura.
- **Transações Digitais**: Permite simular transações entre diferentes usuários.
- **Minerar Blocos**: Processo de mineração que inclui a resolução de problemas computacionais para adicionar um novo bloco à cadeia.
- **Resolução Automática de Conflitos**: O sistema é capaz de resolver automaticamente conflitos que surgem quando diferentes nós possuem versões divergentes da blockchain.
- **Nó Central**: O nó central, em execução na porta 5000, gerencia o registro dos nós participantes e coordena a rede. Os outros nós se registram no nó central.
- **Verificação de Blockchain**: Validação da integridade da cadeia de blocos para garantir que não houve alteração nas transações.
- **Controle de Transações**: Gerencia as transações, validando e minerando novos blocos conforme as transações são feitas.

## Tecnologias Utilizadas

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=flat-square&logo=flask&logoColor=white)
![SHA256](https://img.shields.io/badge/SHA--256-003B57?style=flat-square&logo=hashicorp&logoColor=white)
![Socket](https://img.shields.io/badge/Socket-555555?style=flat-square&logo=python&logoColor=white)

- **Python**: Linguagem de programação usada para implementar a lógica da blockchain.
- **Flask**: Framework para criação de APIs RESTful.
- **Hashing (SHA-256)**: Usado para garantir a integridade dos blocos e transações.
- **Sockets (para comunicação entre nós)**: Para estabelecer conexões entre os nós da rede.

## Instalação

Para rodar este projeto localmente, siga os passos abaixo:

### 1. Clone o repositório:

```bash
git clone https://github.com/Paloma13744/Blockchain_transacao.git
```

### 2. Acesse o diretório do projeto:

```bash
cd Blockchain_transacao
```

### 3. Instale as dependências:
```bash
pip install flask flask-cors requests
```
### 4. Inicie o nó central:
```bash
python blockchain.py -p 5000
```

### 5. Inicie os nós registrados:
```bash
python blockchain.py -p 5001
python blockchain.py -p 5002
(Adicione quantos nós que desejar)
```

### Autora:
https://github.com/Paloma13744 🌸





