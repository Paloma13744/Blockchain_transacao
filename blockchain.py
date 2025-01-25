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
        self.propagate_transaction(transaction)  # Propagar transação para os outros nós
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
            response = requests.post(f'{central_node}/nodes/register', json={'nodes': [this_node]})
            if response.status_code == 201:
                print(f'Nó registrado com sucesso em {central_node}')
            else:
                print(f'Falha ao registrar o nó em {central_node}')
        except requests.exceptions.RequestException as e:
            print(f'Erro ao tentar se conectar ao nó central: {e}')
    
    
    
    def resolve_conflicts(self):
        neighbours = self.nodes
        new_chain = None

        max_length = len(self.chain)

        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        if new_chain:
            self.chain = new_chain
            return True

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
        blockchain.new_transaction(sender="0", recipient=node_identifier, amount=1)  # Criação da transação de recompensa
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
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

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
    Resolves conflicts by checking the chains of neighboring nodes.
    If a longer valid chain is found, it replaces the current chain.
    Returns a message indicating if conflicts were resolved.
    """
    neighbours = blockchain.nodes
    new_chain = None
    max_length = len(blockchain.chain)

    for node in neighbours:
        try:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Verifica se a cadeia recebida é válida e mais longa que a local
                if length > max_length and blockchain.valid_chain(chain):
                    max_length = length
                    new_chain = chain
        except requests.exceptions.RequestException as e:
            print(f'Erro ao tentar se conectar ao nó {node}: {e}')

    # Se encontrar uma cadeia mais longa, substitui a cadeia local
    if new_chain:
        blockchain.chain = new_chain
        return jsonify({'resolved': True}), 200

    return jsonify({'resolved': False}), 200


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='Porta para escutar')
    args = parser.parse_args()
    port = args.port

    central_node = "http://127.0.0.1:5000"
    this_node = f"http://127.0.0.1:{port}"

    if port != 5000:  # Evita que o nó central tente se registrar nele mesmo
        Thread(target=Blockchain.register_to_central_node, args=(central_node, this_node)).start()

    app.run(host='0.0.0.0', port=port)
