/**
 * Módulo INSS - Frontend
 * Versão: 2.1 - 2024
 */

console.log('📦 Carregando inss.js v2.1');

let currentClientId = null;

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Módulo INSS inicializado');
    
    // Carrega menu
    if (typeof loadMenu === 'function') {
        loadMenu();
    }
    
    // Event listener para upload
    const fileInput = document.getElementById('fileInput');
    if (fileInput) {
        fileInput.addEventListener('change', handleFileUpload);
    }
    
    // Aguarda cliente ser selecionado (mais tempo para garantir que o DOM está pronto)
    setTimeout(() => {
        currentClientId = getCurrentClientId();
        if (currentClientId) {
            loadData(currentClientId);
        } else {
            const loadingContainer = document.getElementById('loadingContainer');
            if (loadingContainer) {
                loadingContainer.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-info-circle"></i>
                        <p>Selecione um cliente para visualizar os dados INSS</p>
                    </div>
                `;
            }
        }
    }, 1000);
});

/**
 * Obtém o ID do cliente atual
 */
function getCurrentClientId() {
    // Tenta obter do localStorage (método principal)
    const clientId = localStorage.getItem('selectedClientId');
    if (clientId) {
        return parseInt(clientId);
    }
    
    return null;
}

/**
 * Carrega dados INSS
 */
async function loadData(clientId) {
    console.log('🔑 Carregando dados INSS para client_id:', clientId);
    
    if (!clientId) {
        showError('Cliente não selecionado');
        return;
    }
    
    const loadingContainer = document.getElementById('loadingContainer');
    const tableContainer = document.getElementById('tableContainer');
    
    if (!loadingContainer || !tableContainer) {
        console.error('❌ Elementos do DOM não encontrados');
        return;
    }
    
    loadingContainer.style.display = 'block';
    tableContainer.style.display = 'none';
    
    try {
        const token = localStorage.getItem('token');
        if (!token) {
            window.location.href = '/login';
            return;
        }
        
        const response = await fetch(`/api/inss/todos?client_id=${clientId}`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`Erro ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('📊 Dados recebidos:', data);
        console.log('📊 Estatísticas:', data.estatisticas);
        
        // Atualiza estatísticas
        if (data.estatisticas) {
            updateStats(data.estatisticas);
        }
        
        // Renderiza tabela
        if (data.dados) {
            renderTable(data.dados);
        }
        
        if (loadingContainer) loadingContainer.style.display = 'none';
        if (tableContainer) tableContainer.style.display = 'block';
        
    } catch (error) {
        console.error('❌ Erro ao carregar dados:', error);
        loadingContainer.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-circle"></i>
                <p>Erro ao carregar dados: ${error.message}</p>
                <button class="btn btn-primary" onclick="location.reload()">
                    <i class="fas fa-sync"></i> Tentar Novamente
                </button>
            </div>
        `;
    }
}

/**
 * Atualiza cards de estatísticas
 */
function updateStats(stats) {
    console.log('📊 Atualizando estatísticas:', stats);
    
    const statTotal = document.getElementById('statTotal');
    const statAfastados = document.getElementById('statAfastados');
    const statRetornando = document.getElementById('statRetornando');
    const statAposentados = document.getElementById('statAposentados');
    
    console.log('📊 Elementos encontrados:', {
        statTotal: !!statTotal,
        statAfastados: !!statAfastados,
        statRetornando: !!statRetornando,
        statAposentados: !!statAposentados
    });
    
    if (statTotal) statTotal.textContent = stats.total || 0;
    if (statAfastados) statAfastados.textContent = stats.afastados || 0;
    if (statRetornando) statRetornando.textContent = stats.retornando || 0;
    if (statAposentados) statAposentados.textContent = stats.aposentados || 0;
    
    console.log('✅ Estatísticas atualizadas com sucesso');
}

/**
 * Renderiza tabela de dados
 */
function renderTable(dados) {
    const tbody = document.getElementById('tableBody');
    
    if (!dados || dados.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="14" style="text-align: center; padding: 40px;">
                    <div class="empty-state">
                        <i class="fas fa-inbox"></i>
                        <p>Nenhum dado encontrado</p>
                        <p style="font-size: 13px; margin-top: 8px;">Faça upload de uma planilha INSS para começar</p>
                    </div>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = dados.map(item => `
        <tr>
            <td>${item.cont || '-'}</td>
            <td>${item.re || '-'}</td>
            <td>${item.nome || '-'}</td>
            <td>${item.id_colaborador || '-'}</td>
            <td>${item.setor || '-'}</td>
            <td>${item.funcao || '-'}</td>
            <td>${item.data_de_afast || '-'}</td>
            <td>${item.acid_trab || '-'}</td>
            <td>${item.cid10 || '-'}</td>
            <td>${item.inicio_do_inss || '-'}</td>
            <td>${item.fim_do_beneficio || '-'}</td>
            <td>${item.motivo || '-'}</td>
            <td style="max-width: 200px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" 
                title="${item.parecer_medico || '-'}">
                ${item.parecer_medico || '-'}
            </td>
            <td>
                <button class="action-btn delete" onclick="deletarColaborador(${item.id})">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
    
    console.log(`✅ Tabela renderizada com ${dados.length} registros`);
}

/**
 * Handle do upload de arquivo
 */
async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    console.log('📤 Iniciando upload:', file.name);
    
    const clientId = getCurrentClientId();
    if (!clientId) {
        showError('Selecione um cliente primeiro');
        event.target.value = '';
        return;
    }
    
    const uploadStatus = document.getElementById('uploadStatus');
    if (!uploadStatus) {
        console.error('❌ Elemento uploadStatus não encontrado');
        return;
    }
    
    uploadStatus.style.display = 'block';
    uploadStatus.className = 'upload-status';
    uploadStatus.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processando planilha...';
    
    try {
        const token = localStorage.getItem('token');
        if (!token) {
            window.location.href = '/login';
            return;
        }
        
        const formData = new FormData();
        formData.append('file', file);
        formData.append('client_id', clientId);
        
        const response = await fetch('/api/inss/upload', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Erro ${response.status}`);
        }
        
        const result = await response.json();
        console.log('✅ Upload concluído:', result);
        
        uploadStatus.className = 'upload-status';
        uploadStatus.innerHTML = `
            <i class="fas fa-check-circle"></i> 
            ${result.message} - 
            Criados: ${result.total_criados}, 
            Atualizados: ${result.total_atualizados}
        `;
        
        // Recarrega dados
        setTimeout(() => {
            loadData(clientId);
            uploadStatus.style.display = 'none';
        }, 3000);
        
    } catch (error) {
        console.error('❌ Erro no upload:', error);
        uploadStatus.className = 'upload-status error';
        uploadStatus.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${error.message}`;
        
        setTimeout(() => {
            uploadStatus.style.display = 'none';
        }, 5000);
    }
    
    // Limpa input
    event.target.value = '';
}

/**
 * Deletar todos os dados
 */
async function deletarTodosDados() {
    if (!confirm('⚠️ ATENÇÃO: Isso irá deletar TODOS os dados INSS do cliente selecionado.\n\nEsta ação não pode ser desfeita!\n\nDeseja continuar?')) {
        return;
    }
    
    const clientId = getCurrentClientId();
    if (!clientId) {
        showError('Selecione um cliente primeiro');
        return;
    }
    
    const uploadStatus = document.getElementById('uploadStatus');
    if (!uploadStatus) {
        console.error('❌ Elemento uploadStatus não encontrado');
        return;
    }
    
    uploadStatus.style.display = 'block';
    uploadStatus.className = 'upload-status';
    uploadStatus.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deletando dados...';
    
    try {
        const token = localStorage.getItem('token');
        if (!token) {
            window.location.href = '/login';
            return;
        }
        
        console.log('[INFO] Deletando todos os dados INSS para client_id:', clientId);
        
        const response = await fetch(`/api/inss/todos?client_id=${clientId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Erro ${response.status}`);
        }
        
        const result = await response.json();
        console.log('[OK] Resultado:', result);
        
        uploadStatus.className = 'upload-status';
        uploadStatus.innerHTML = `<i class="fas fa-check-circle"></i> ${result.message}`;
        
        // Recarrega dados
        setTimeout(() => {
            loadData(clientId);
            uploadStatus.style.display = 'none';
        }, 2000);
        
    } catch (error) {
        console.error('[ERRO] Erro ao deletar:', error);
        uploadStatus.className = 'upload-status error';
        uploadStatus.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${error.message}`;
        
        setTimeout(() => {
            uploadStatus.style.display = 'none';
        }, 5000);
    }
}

/**
 * Deletar colaborador individual
 */
async function deletarColaborador(colaboradorId) {
    if (!confirm('Deseja realmente excluir este colaborador?')) {
        return;
    }
    
    try {
        const token = localStorage.getItem('token');
        if (!token) {
            window.location.href = '/login';
            return;
        }
        
        const response = await fetch(`/api/inss/${colaboradorId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Erro ${response.status}`);
        }
        
        const result = await response.json();
        console.log('✅ Colaborador excluído:', result);
        
        // Recarrega dados
        const clientId = getCurrentClientId();
        if (clientId) {
            loadData(clientId);
        }
        
    } catch (error) {
        console.error('❌ Erro ao excluir:', error);
        showError(`Erro ao excluir: ${error.message}`);
    }
}

/**
 * Exibe mensagem de erro
 */
function showError(message) {
    console.error('❌ Erro:', message);
    
    const uploadStatus = document.getElementById('uploadStatus');
    if (uploadStatus) {
        uploadStatus.style.display = 'block';
        uploadStatus.className = 'upload-status error';
        uploadStatus.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
        
        setTimeout(() => {
            uploadStatus.style.display = 'none';
        }, 5000);
    } else {
        alert(message);
    }
}

