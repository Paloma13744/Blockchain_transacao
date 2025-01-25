$(document).ready(function () {
    $('#transactionForm').submit(function (event) {
        event.preventDefault();
        const sender = $('#sender').val();
        const recipient = $('#recipient').val();
        const amount = $('#amount').val();
    
        const transaction = {
            sender: sender,
            recipient: recipient,
            amount: amount
        };
    
        // Enviar a transação para o servidor
        $.ajax({
            url: '/transactions/new',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(transaction),
            success: function (response) {
                alert('Transação criada com sucesso!'); // Alerta adicionado
    
                // Chama a rota /mine para minerar o bloco
                $.ajax({
                    url: '/mine',
                    type: 'GET',
                    success: function (mineResponse) {
                        alert('Novo bloco minerado com sucesso!');
                    },
                    error: function () {
                        alert('Erro ao minerar o novo bloco');
                    }
                });
            },
            error: function () {
                alert('Erro ao criar transação');
            }
        });
    });

    $('#loadChainBtn').click(function () {
        loadChain();
    });
    
    function loadChain() {
        $.ajax({
            url: '/chain',
            type: 'GET',
            success: function (response) {
                const chain = response.chain;
                let chainHistory = '';
                chain.forEach(block => {
                    chainHistory += `<div class="block">
                        <p><strong>Índice:</strong> ${block.index}</p>
                        <p><strong>Timestamp:</strong> ${new Date(block.timestamp * 1000).toLocaleString()}</p>
                        <p><strong>Transações:</strong></p>
                        <ul>`;
                    block.transactions.forEach(tx => {
                        chainHistory += `<li>${tx.sender} -> ${tx.recipient}: ${tx.amount}</li>`;
                    });
                    chainHistory += `</ul>
                        <p><strong>Prova:</strong> ${block.proof}</p>
                        <p><strong>Hash Anterior:</strong> ${block.previous_hash}</p>
                        <hr>
                    </div>`;
                });
                $('#chainHistory').html(chainHistory); // Certifique-se de que o elemento #chainHistory existe no HTML
            },
            error: function (error) {
                alert('Erro ao carregar histórico');
            }
        });
    }
   

   // Carregar a lista de nós registrados
   function loadNodeSelect() {
    $.get('/nodes', function (data) {
        const nodes = data.total_nodes; // Usar a chave correta
        $('#nodeSelect').html('<option value="">Selecione um nó</option>'); // Limpar e adicionar opção de seleção
        nodes.forEach(node => {
            $('#nodeSelect').append(`<option value="${node}">${node}</option>`);
        });
    });
}

loadNodeSelect(); // Carregar os nós registrados ao carregar a página

// Carregar histórico de um nó específico e resolver conflitos antes de exibir o histórico
$('#loadNodeHistoryBtn').click(function () {
    const selectedNode = $('#nodeSelect').val();
    if (selectedNode) {
        // Chama a rota de resolver conflitos para garantir que o nó tenha o blockchain mais atualizado
        $.ajax({
            url: `http://${selectedNode}/resolve`,
            type: 'GET',
            success: function (resolveResponse) {
                if (resolveResponse.resolved) {
                    alert('Conflitos resolvidos! O blockchain foi atualizado.');
                } else {
                    alert('Nenhum conflito detectado.');
                }

                // Após resolver conflitos, carrega o histórico do nó
                $.get(`http://${selectedNode}/chain`, function (response) {
                    let nodeHistoryHtml = `<h3>Histórico de ${selectedNode}:</h3>`;
                    response.chain.forEach(block => {
                        nodeHistoryHtml += `
                            <p><strong>Bloco ${block.index}:</strong><br>
                            Prova: ${block.proof}<br>
                            Transações: ${JSON.stringify(block.transactions)}<br>
                            Anterior Hash: ${block.previous_hash}</p>
                        `;
                    });
                    $('#nodeHistory').html(nodeHistoryHtml);
                }).fail(function () {
                    $('#nodeHistory').html(`<p>Erro ao carregar o histórico de ${selectedNode}</p>`);
                });
            },
            error: function () {
                alert('Erro ao resolver conflitos no nó');
            }
        });
    } else {
        alert('Selecione um nó para visualizar o histórico.');
    }
});
});
