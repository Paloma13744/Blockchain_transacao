from flask import Flask, jsonify, request, render_template
from uuid import uuid4
import hashlib
import json
from time import time
from urllib.parse import urlparse
import requests
from flask_cors import CORS
from threading import Thread


class Blockchain:
    def __init__(self):
        self.current_transactions = []
        self.chain = []
        self.nodes = set()

        # Criação do bloco Gênesis
        self.new_block(previous_hash='1', proof=100)

        # Geração de um identificador único para este nó
        self.node_identifier = str(uuid4()).replace('-', '')

    def new_block(self, proof, previous_hash=None):  # Cria um novo bloco e adiciona à cadeia
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        self.current_transactions = []  # Redefine as transações atuais
        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        transaction = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        }
        self.current_transactions.append(transaction)
        # Propagar transação para os outros nós
        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]

    def proof_of_work(self, last_block):
        last_proof = last_block['proof']
        last_hash = self.hash(last_block)
        proof = 0
        while not self.valid_proof(last_proof, proof, last_hash):
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof, proof, last_hash):
        guess = f'{last_proof}{proof}{last_hash}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash.startswith("0000")

    @staticmethod
    def register_to_central_node(central_node, this_node):
        try:
            response = requests.post(
                f'{central_node}/nodes/register', json={'nodes': [this_node]})
            if response.status_code == 201:
                print(f'Nó registrado com sucesso em {central_node}')
            else:
                print(f'Falha ao registrar o nó em {central_node}')
        except requests.exceptions.RequestException as e:
            print(f'Erro ao tentar se conectar ao nó central: {e}')

    def resolve_conflicts(self):
        """
        Implementa o consenso "50% + 1":
        - Coleta as blockchains de todos os nós
        - Conta quantos nós possuem cada blockchain
        - Substitui a blockchain local apenas se uma cadeia for aceita pela maioria
        """
        chains = {}  # Dicionário para armazenar diferentes versões das blockchains
        node_count = len(self.nodes) + 1  # Inclui o próprio nó

        for node in self.nodes:
            try:
                response = requests.get(f'http://{node}/chain')
                if response.status_code == 200:
                    chain = response.json()['chain']
                    # Obtém o hash do último bloco
                    chain_hash = self.hash(chain[-1])

                    # Conta quantos nós possuem essa blockchain específica
                    if chain_hash not in chains:
                        chains[chain_hash] = []
                    chains[chain_hash].append(chain)
            except Exception as e:
                print(f"⚠️ Erro ao obter a blockchain do nó {node}: {e}")
                continue  # Continua para o próximo nó

        # Encontrar a blockchain com mais votos
        majority_chain = None
        majority_count = 0

        for chain_hash, chain_list in chains.items():
            if len(chain_list) > majority_count:
                majority_count = len(chain_list)
                majority_chain = chain_list[0]

        # Verifica se a blockchain escolhida tem a maioria (50% + 1)
        if majority_chain and majority_count > node_count // 2:
            self.chain = majority_chain  # Substitui pela cadeia com consenso
            print(
                f"🔄 Blockchain substituída com base no consenso (50% + 1): {majority_count}/{node_count} nós")
            return True

        print("✅ Nenhuma substituição necessária. A blockchain local já está correta.")
        return False

    def propagate_transaction(self, transaction):
        for node in self.nodes:
            try:
                response = requests.post(
                    f'http://{node}/transactions/new', json=transaction)
                if response.status_code == 201:
                    print(f'Transação propagada para {node}')
                else:
                    print(f'Falha ao propagar transação para {node}')
            except requests.exceptions.RequestException as e:
                print(f'Erro ao tentar se conectar ao nó {node}: {e}')

    def register_node(self, address):
        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('URL inválido')


# Definição das rotas
app = Flask(__name__)
CORS(app)
node_identifier = str(uuid4()).replace('-', '')
blockchain = Blockchain()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/nodes', methods=['GET'])
def get_nodes():
    response = {
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 200


@app.route('/mine', methods=['GET'])
def mine():
    if blockchain.current_transactions:  # Garante que há transações para minerar
        last_block = blockchain.last_block
        proof = blockchain.proof_of_work(last_block)
        # Criação da transação de recompensa
        blockchain.new_transaction(
            sender="0", recipient=node_identifier, amount=1)
        block = blockchain.new_block(proof)
        response = {
            'message': "Novo bloco minerado com sucesso!",
            'index': block['index'],
            'transactions': block['transactions'],
            'proof': block['proof'],
            'previous_hash': block['previous_hash'],
        }
        return jsonify(response), 200
    else:
        return jsonify({'message': 'Nenhuma transação pendente para minerar.'}), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Valores ausentes', 400

    # Criação da transação
    index = blockchain.new_transaction(
        values['sender'], values['recipient'], values['amount'])

    # Minerar um novo bloco após a transação
    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block)
    blockchain.new_block(proof)

    response = {
        'message': "Transação criada e bloco minerado com sucesso!",
        'index': blockchain.last_block['index'],
        'transactions': blockchain.last_block['transactions'],
        'proof': blockchain.last_block['proof'],
        'previous_hash': blockchain.last_block['previous_hash'],
    }
    return jsonify(response), 201


@app.route('/transactions/propagate', methods=['POST'])
def propagate_transaction_route():
    values = request.get_json()
    required = ['sender', 'recipient', 'amount']

    if not all(k in values for k in required):
        return jsonify({'error': 'Valores ausentes'}), 400

    transaction = {
        'sender': values['sender'],
        'recipient': values['recipient'],
        'amount': values['amount']
    }

    blockchain.propagate_transaction(transaction)

    return jsonify({'message': 'Transação propagada para os nós'}), 200


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()
    nodes = values.get('nodes')
    if nodes is None:
        return 'Erro: Lista de nós não fornecida', 400
    for node in nodes:
        blockchain.register_node(node)
    response = {
        'message': 'Nós registrados com sucesso',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route('/resolve', methods=['GET'])
def resolve():
    """
    Rota para resolver conflitos entre nós da blockchain.
    Esta função chama `resolve_conflicts()` da classe Blockchain.
    """
    resolved = blockchain.resolve_conflicts()
    if resolved:
        return jsonify({'message': '🔄 Conflitos resolvidos! A blockchain foi atualizada.'}), 200
    else:
        return jsonify({'message': '✅ Nenhuma atualização necessária. A blockchain já está sincronizada.'}), 200


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000,
                        type=int, help='Porta para escutar')
    args = parser.parse_args()
    port = args.port

    central_node = "http://127.0.0.1:5000"
    this_node = f"http://127.0.0.1:{port}"

    if port != 5000:  # Evita que o nó central tente se registrar nele mesmo
        Thread(target=Blockchain.register_to_central_node,
               args=(central_node, this_node)).start()

    app.run(host='0.0.0.0', port=port)
