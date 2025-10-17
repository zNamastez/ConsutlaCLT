// Máscaras para os campos
document.getElementById('cpf').addEventListener('input', function (e) {
    let value = e.target.value.replace(/\D/g, '');
    if (value.length <= 11) {
        value = value.replace(/(\d{3})(\d)/, '$1.$2');
        value = value.replace(/(\d{3})(\d)/, '$1.$2');
        value = value.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
        e.target.value = value;
    }
});

document.getElementById('ddd').addEventListener('input', function (e) {
    e.target.value = e.target.value.replace(/\D/g, '');
});

document.getElementById('telefone').addEventListener('input', function (e) {
    let value = e.target.value.replace(/\D/g, '');
    if (value.length <= 9) {
        if (value.length > 4) {
            value = value.replace(/(\d{4,5})(\d{4})$/, '$1-$2');
        }
        e.target.value = value;
    }
});

// Submissão do formulário
document.getElementById('consultForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const cpf = document.getElementById('cpf').value.replace(/\D/g, '');
    const ddd = document.getElementById('ddd').value;
    const telefone = document.getElementById('telefone').value.replace(/\D/g, '');

    // Validações
    if (cpf.length !== 11) {
        alert('CPF deve conter 11 dígitos');
        return;
    }

    if (ddd.length !== 2) {
        alert('DDD deve conter 2 dígitos');
        return;
    }

    if (telefone.length < 8 || telefone.length > 9) {
        alert('Telefone deve conter 8 ou 9 dígitos');
        return;
    }

    // Mostrar loading
    const btnSubmit = document.getElementById('btnSubmit');
    const btnText = document.getElementById('btnText');
    const btnLoading = document.getElementById('btnLoading');
    
    btnSubmit.disabled = true;
    btnText.style.display = 'none';
    btnLoading.style.display = 'flex';

    // Ocultar resultado anterior
    document.getElementById('resultContainer').style.display = 'none';

    try {
        const response = await fetch('/consult', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                cpf: cpf,
                ddd: ddd,
                telefone: telefone
            })
        });

        const data = await response.json();
        displayResults(data);
    } catch (error) {
        alert('Erro ao realizar consulta: ' + error.message);
        console.error('Erro:', error);
    } finally {
        // Esconder loading
        btnSubmit.disabled = false;
        btnText.style.display = 'inline';
        btnLoading.style.display = 'none';
    }
});

function displayResults(data) {
    const resultContainer = document.getElementById('resultContainer');
    const authorizationStatus = document.getElementById('authorizationStatus');
    const authorizationBox = document.getElementById('authorizationBox');
    const offersContainer = document.getElementById('offersContainer');
    const offersList = document.getElementById('offersList');
    const noOffersMessage = document.getElementById('noOffersMessage');

    // Exibir status de autorização
    authorizationStatus.textContent = data.authorization || 'Desconhecido';
    
    // Remover classes anteriores
    authorizationStatus.className = 'authorization-status';
    
    // Adicionar classe baseada no status
    if (data.authorization === 'Aceito') {
        authorizationStatus.classList.add('accepted');
    } else if (data.authorization === 'Recusado' || data.authorization === 'Negado') {
        authorizationStatus.classList.add('rejected');
    } else {
        authorizationStatus.classList.add('pending');
    }

    // Exibir ofertas se houver
    if (data.result && Array.isArray(data.result) && data.result.length > 0) {
        offersContainer.style.display = 'block';
        noOffersMessage.style.display = 'none';
        
        offersList.innerHTML = '';
        data.result.forEach((offer, index) => {
            const offerItem = document.createElement('div');
            offerItem.className = 'offer-item';
            offerItem.innerHTML = `
                <div class="offer-item-header">
                    <div class="offer-prazo">📅 ${offer.prazo || 'N/A'}</div>
                    <div class="offer-parcela">💰 ${offer.liberado || 'N/A'}</div>
                </div>
                <div class="offer-liberado">
                    <strong>Valor da Parcela:</strong> ${offer.parcela || 'N/A'}
                </div>
            `;
            offersList.appendChild(offerItem);
        });
    } else if (typeof data.result === 'string') {
        // Se result for uma string (mensagem de erro do sistema)
        offersContainer.style.display = 'none';
        noOffersMessage.style.display = 'block';
        noOffersMessage.innerHTML = `<p>${data.result}</p>`;
    } else {
        // Sem ofertas disponíveis
        offersContainer.style.display = 'none';
        noOffersMessage.style.display = 'block';
    }

    // Mostrar container de resultados
    resultContainer.style.display = 'block';
    
    // Scroll suave até os resultados
    resultContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

