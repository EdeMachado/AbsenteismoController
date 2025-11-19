/**
 * Upload JavaScript - AbsenteismoController v2.0
 */

let selectedFile = null;
let currentClient = {
    id: null,
    name: '',
    cnpj: '',
    logo: ''
};

document.addEventListener('DOMContentLoaded', () => {
    initializeClientContext();
    setupDragDrop();
    loadUploads();
    inicializarAnosReferencia();
});

function inicializarAnosReferencia() {
    const anoSelect = document.getElementById('anoReferencia');
    if (!anoSelect) return;
    
    const anoAtual = new Date().getFullYear();
    // Adiciona anos de 2020 até 5 anos no futuro
    for (let ano = 2020; ano <= anoAtual + 5; ano++) {
        const option = document.createElement('option');
        option.value = ano;
        option.textContent = ano;
        if (ano === anoAtual) {
            option.selected = true;
        }
        anoSelect.appendChild(option);
    }
}

function setupDragDrop() {
    const uploadZone = document.getElementById('uploadZone');
    
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadZone.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });
    
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadZone.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        uploadZone.addEventListener(eventName, unhighlight, false);
    });
    
    uploadZone.addEventListener('drop', handleDrop, false);
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function highlight(e) {
    document.getElementById('uploadZone').classList.add('dragover');
}

function unhighlight(e) {
    document.getElementById('uploadZone').classList.remove('dragover');
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;

    if (!currentClient.id) {
        alert('Selecione um cliente na aba "Clientes" antes de enviar planilhas.');
        return;
    }
    
    if (files.length > 0) {
        selectedFile = files[0];
        showFileSelected();
    }
}

function handleFileSelect(event) {
    if (!currentClient.id) {
        alert('Selecione um cliente na aba "Clientes" antes de enviar planilhas.');
        event.target.value = '';
        return;
    }
    const files = event.target.files;
    if (files.length > 0) {
        selectedFile = files[0];
        showFileSelected();
    }
}

function showFileSelected() {
    if (!selectedFile || !currentClient.id) return;
    
    document.getElementById('fileName').textContent = selectedFile.name;
    document.getElementById('fileSize').textContent = formatFileSize(selectedFile.size);
    document.getElementById('fileSelectedDiv').style.display = 'flex';
    document.getElementById('uploadZone').style.display = 'none';
    
    // Tenta detectar mês/ano do nome do arquivo ou usa valores padrão
    const nomeArquivo = selectedFile.name.toLowerCase();
    const mesAtual = new Date().getMonth() + 1;
    const anoAtual = new Date().getFullYear();
    
    // Tenta detectar mês no nome do arquivo
    const meses = {
        'jan': '01', 'january': '01', 'janeiro': '01',
        'fev': '02', 'february': '02', 'fevereiro': '02',
        'mar': '03', 'march': '03', 'março': '03',
        'abr': '04', 'april': '04', 'abril': '04',
        'mai': '05', 'may': '05', 'maio': '05',
        'jun': '06', 'june': '06', 'junho': '06',
        'jul': '07', 'july': '07', 'julho': '07',
        'ago': '08', 'august': '08', 'agosto': '08',
        'set': '09', 'september': '09', 'setembro': '09',
        'out': '10', 'october': '10', 'outubro': '10',
        'nov': '11', 'november': '11', 'novembro': '11',
        'dez': '12', 'december': '12', 'dezembro': '12'
    };
    
    let mesDetectado = null;
    for (const [key, value] of Object.entries(meses)) {
        if (nomeArquivo.includes(key)) {
            mesDetectado = value;
            break;
        }
    }
    
    // Tenta detectar ano no nome do arquivo (4 dígitos)
    const anoMatch = nomeArquivo.match(/\b(20\d{2})\b/);
    const anoDetectado = anoMatch ? anoMatch[1] : null;
    
    // Preenche os campos se detectou algo
    const mesSelect = document.getElementById('mesReferencia');
    const anoSelect = document.getElementById('anoReferencia');
    
    if (mesSelect && mesDetectado) {
        mesSelect.value = mesDetectado;
    } else if (mesSelect) {
        // Se não detectou, sugere o mês anterior (comum em planilhas mensais)
        // Ex: se estamos em novembro, a planilha provavelmente é de outubro
        let mesAnterior = mesAtual - 1;
        if (mesAnterior === 0) {
            mesAnterior = 12;
            // Se for janeiro, o mês anterior seria dezembro do ano anterior
            // Mas mantemos o ano atual por enquanto
        }
        mesSelect.value = String(mesAnterior).padStart(2, '0');
    }
    
    if (anoSelect && anoDetectado) {
        anoSelect.value = anoDetectado;
    } else if (anoSelect) {
        anoSelect.value = anoAtual;
    }
}

function cancelFile() {
    selectedFile = null;
    document.getElementById('fileInput').value = '';
    
    // Limpa campos de período
    const mesSelect = document.getElementById('mesReferencia');
    const anoSelect = document.getElementById('anoReferencia');
    if (mesSelect) mesSelect.value = '';
    if (anoSelect) {
        const anoAtual = new Date().getFullYear();
        anoSelect.value = anoAtual; // Mantém o ano atual como padrão
    }
    
    document.getElementById('fileSelectedDiv').style.display = 'none';
    document.getElementById('uploadZone').style.display = 'block';
}

async function uploadFile() {
    if (!selectedFile) {
        alert('Selecione um arquivo primeiro');
        return;
    }

    if (!currentClient.id) {
        alert('Selecione um cliente na aba "Clientes" antes de enviar planilhas.');
        return;
    }
    
    // Valida período de referência
    const mesRef = document.getElementById('mesReferencia')?.value;
    const anoRef = document.getElementById('anoReferencia')?.value;
    
    if (!mesRef || !anoRef) {
        alert('Por favor, selecione o mês e ano de referência da planilha.\n\nExemplo: Se a planilha contém dados de outubro/2025, selecione Outubro e 2025.');
        return;
    }
    
    const mesReferencia = `${anoRef}-${mesRef}`;
    
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('client_id', currentClient.id);
    formData.append('mes_referencia', mesReferencia);
    
    // Show progress
    document.getElementById('progressContainer').style.display = 'block';
    document.getElementById('progressFill').style.width = '0%';
    document.getElementById('progressText').textContent = 'Enviando arquivo...';
    
    try {
        // Simula progresso
        let progress = 0;
        const interval = setInterval(() => {
            progress += 10;
            if (progress <= 50) {
                document.getElementById('progressFill').style.width = progress + '%';
            }
        }, 200);
        
        // Obtém token de autenticação
        const token = localStorage.getItem('access_token');
        const headers = {};
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        const response = await fetch('/api/upload', {
            method: 'POST',
            headers: headers,
            body: formData
        });
        
        clearInterval(interval);
        
        if (response.ok) {
            const result = await response.json();
            
            document.getElementById('progressFill').style.width = '100%';
            document.getElementById('progressText').textContent = `Sucesso! ${result.total_registros} registros processados`;
            document.getElementById('progressFill').style.background = 'var(--success)';
            
            setTimeout(() => {
                cancelFile();
                document.getElementById('progressContainer').style.display = 'none';
                document.getElementById('progressFill').style.background = 'var(--success)';
                loadUploads();
                
                // Recarrega dashboard automaticamente se estiver na página do dashboard
                if (window.location.pathname === '/' || window.location.pathname === '/index.html') {
                    // Se já está no dashboard, recarrega os dados
                    if (typeof carregarDashboard === 'function') {
                        console.log('🔄 Recarregando dashboard após upload...');
                        setTimeout(async () => {
                            try {
                                await carregarDashboard();
                                mostrarMensagemSucesso('Upload realizado com sucesso! Dashboard atualizado automaticamente.');
                            } catch (error) {
                                console.error('Erro ao recarregar dashboard:', error);
                                mostrarMensagemSucesso('Upload realizado com sucesso! Recarregue a página para ver os gráficos.');
                            }
                        }, 500);
                    }
                } else {
                    // Se não está no dashboard, pergunta se quer ir
                    if (confirm('Upload realizado com sucesso! Deseja ir para o dashboard para ver os gráficos e análises?')) {
                        window.location.href = '/';
                    }
                }
            }, 2000);
            
        } else {
            // Tenta obter a mensagem de erro do servidor
            let errorMessage = 'Erro no upload';
            let errorDetails = '';
            let errorData = null;
            
            // Clona a resposta para poder ler múltiplas vezes
            const responseClone = response.clone();
            
            try {
                // Tenta ler como JSON primeiro
                errorData = await response.json();
                errorMessage = errorData.detail || errorData.message || errorData.error || errorMessage;
                errorDetails = JSON.stringify(errorData, null, 2);
                console.log('Erro do servidor (JSON):', errorData);
            } catch (e) {
                // Se não conseguir ler JSON, tenta ler como texto
                try {
                    const textError = await responseClone.text();
                    console.log('Erro do servidor (texto):', textError);
                    errorMessage = textError || `Erro ${response.status}: ${response.statusText}`;
                    errorDetails = textError;
                    
                    // Tenta parsear como JSON se for texto JSON
                    try {
                        const parsed = JSON.parse(textError);
                        errorMessage = parsed.detail || parsed.message || errorMessage;
                        errorDetails = JSON.stringify(parsed, null, 2);
                    } catch (parseError) {
                        // Não é JSON, mantém como texto
                    }
                } catch (e2) {
                    errorMessage = `Erro ${response.status}: ${response.statusText}`;
                    console.error('Erro ao ler resposta:', e2);
                }
            }
            
            // Log detalhado no console para debug
            console.error('Erro no upload - Detalhes completos:', {
                status: response.status,
                statusText: response.statusText,
                url: response.url,
                message: errorMessage,
                details: errorDetails,
                headers: Object.fromEntries(response.headers.entries())
            });
            
            // Tenta extrair mensagem mais específica
            if (errorMessage === 'Erro 500: Internal Server Error' || errorMessage === 'Erro no upload') {
                errorMessage = 'Erro interno no servidor. Verifique os logs do servidor ou entre em contato com o suporte.';
            }
            
            throw new Error(errorMessage);
        }
        
    } catch (error) {
        console.error('Erro completo no upload:', error);
        const errorMessage = error.message || 'Erro ao processar arquivo';
        
        // Mostra erro no console com mais detalhes
        console.error('Detalhes do erro:', {
            message: errorMessage,
            stack: error.stack,
            name: error.name
        });
        
        document.getElementById('progressFill').style.width = '100%';
        document.getElementById('progressFill').style.background = 'var(--danger)';
        document.getElementById('progressText').textContent = errorMessage;
        
        // Mostra alerta com detalhes do erro
        alert(`Erro no upload:\n\n${errorMessage}\n\nVerifique:\n- Se o arquivo é um Excel válido (.xlsx ou .xls)\n- Se o cliente está selecionado\n- Se a planilha tem o formato correto\n- Abra o console do navegador (F12) para mais detalhes`);
        
        setTimeout(() => {
            document.getElementById('progressContainer').style.display = 'none';
            document.getElementById('progressFill').style.background = 'var(--success)';
        }, 8000);
    }
}

async function mostrarMensagemSucesso(mensagem) {
    // Remove mensagens anteriores
    const mensagensExistentes = document.querySelectorAll('.mensagem-upload-sucesso');
    mensagensExistentes.forEach(msg => msg.remove());
    
    const mensagemDiv = document.createElement('div');
    mensagemDiv.className = 'mensagem-upload-sucesso';
    mensagemDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #e8f5e9;
        border: 2px solid #4caf50;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.15);
        z-index: 10000;
        max-width: 400px;
        display: flex;
        align-items: center;
        gap: 12px;
    `;
    mensagemDiv.innerHTML = `
        <i class="fas fa-check-circle" style="font-size: 24px; color: #2e7d32;"></i>
        <div style="flex: 1; color: #2e7d32; font-size: 14px; line-height: 1.4;">${mensagem}</div>
    `;
    
    document.body.appendChild(mensagemDiv);
    
    // Remove após 5 segundos
    setTimeout(() => {
        mensagemDiv.remove();
    }, 5000);
}

async function loadUploads() {
    const tbody = document.getElementById('uploadsTableBody');
    if (!currentClient.id) {
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" style="text-align: center; color: var(--text-secondary);">
                        Selecione um cliente para visualizar o histórico de uploads.
                    </td>
                </tr>
            `;
        }
        return;
    }

    try {
        const response = await fetch(`/api/uploads?client_id=${currentClient.id}`);
        const uploads = await response.json();
        
        if (!tbody) return;
        
        if (uploads.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" style="text-align: center; color: var(--text-secondary);">
                        Nenhum upload realizado ainda
                    </td>
                </tr>
            `;
            return;
        }
        
        tbody.innerHTML = uploads.map(u => `
            <tr>
                <td>
                    <i class="fas fa-file-excel" style="color: var(--success); margin-right: 8px;"></i>
                    ${u.filename}
                </td>
                <td>${formatMesReferencia(u.mes_referencia)}</td>
                <td>${formatDateTime(u.data_upload)}</td>
                <td>${u.total_registros}</td>
                <td>
                    <a href="/dados_powerbi?upload_id=${u.id}" class="btn btn-secondary btn-icon" title="Ver e editar dados">
                        <i class="fas fa-eye"></i>
                    </a>
                    <button onclick="deleteUpload(${u.id})" class="btn btn-secondary btn-icon" title="Deletar" style="margin-left: 8px;">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
        
    } catch (error) {
        console.error('Erro ao carregar uploads:', error);
    }
}

async function deleteUpload(id) {
    if (!confirm('Tem certeza que deseja deletar este upload? Todos os dados serão perdidos.')) {
        return;
    }
    
    // Obtém client_id
    let clientId = null;
    if (typeof getClientId === 'function') {
        clientId = getClientId();
    } else if (window.currentClient && window.currentClient.id) {
        clientId = window.currentClient.id;
    } else if (typeof window.getCurrentClientId === 'function') {
        clientId = window.getCurrentClientId();
    }
    
    if (!clientId) {
        alert('Erro: Cliente não selecionado. Selecione um cliente primeiro.');
        return;
    }
    
    try {
        const response = await fetch(`/api/uploads/${id}?client_id=${clientId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            alert('Upload deletado com sucesso');
            loadUploads();
        } else {
            const errorData = await response.json().catch(() => ({ detail: 'Erro desconhecido' }));
            alert(`Erro ao deletar upload: ${errorData.detail || 'Erro desconhecido'}`);
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao deletar upload: ' + error.message);
    }
}

// Utilities
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

function formatMesReferencia(mes) {
    const [ano, mesNum] = mes.split('-');
    const meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'];
    return `${meses[parseInt(mesNum) - 1]}/${ano}`;
}

function formatDateTime(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleString('pt-BR');
}

function initializeClientContext() {
    // Tenta obter o ID do cliente de várias formas
    let storedId = null;
    
    // Método 1: Função global getCurrentClientId
    if (typeof window.getCurrentClientId === 'function') {
        storedId = window.getCurrentClientId(null);
    }
    
    // Método 2: localStorage direto
    if (!storedId) {
        const stored = localStorage.getItem('cliente_selecionado');
        if (stored) {
            storedId = Number(stored);
        }
    }
    
    const numericId = Number(storedId);
    currentClient = {
        id: Number.isFinite(numericId) && numericId > 0 ? numericId : null,
        name: localStorage.getItem('cliente_nome') || '',
        cnpj: localStorage.getItem('cliente_cnpj') || '',
        logo: localStorage.getItem('cliente_logo_url') || ''
    };
    
    console.log('Cliente inicializado:', currentClient);
    renderCurrentClientBanner();
    setUploadAvailability(Boolean(currentClient.id));
}

function renderCurrentClientBanner() {
    const banner = document.getElementById('currentClientBanner');
    if (!banner) return;

    if (!currentClient.id) {
        banner.classList.add('warning');
        banner.innerHTML = `
            <div class="current-client-warning">
                <div class="warning-icon"><i class="fas fa-exclamation-triangle"></i></div>
                <div class="warning-content">
                    <strong>Nenhum cliente selecionado</strong>
                    <span>Escolha um cliente em "Clientes" para enviar a planilha correta.</span>
                </div>
            </div>
            <button class="btn btn-primary btn-sm" onclick="window.location.href='/clientes'">
                <i class="fas fa-users"></i> Selecionar cliente
            </button>
        `;
        return;
    }

    banner.classList.remove('warning');
    const displayCnpj = formatDisplayCnpj(currentClient.cnpj);
    const avatarContent = currentClient.logo
        ? `<img src="${currentClient.logo}" alt="Logo ${currentClient.name}" onerror="this.remove();">`
        : getInitials(currentClient.name);

    banner.innerHTML = `
        <div class="current-client-info">
            <div class="client-avatar">${avatarContent}</div>
            <div class="current-client-text">
                <strong>${currentClient.name || 'Cliente selecionado'}</strong>
                ${displayCnpj ? `<span class="current-client-meta">${displayCnpj}</span>` : ''}
            </div>
        </div>
        <button class="btn btn-secondary btn-sm" onclick="window.location.href='/clientes'">
            <i class="fas fa-exchange-alt"></i> Trocar
        </button>
    `;
}

function setUploadAvailability(enabled) {
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');
    if (!uploadZone || !fileInput) return;

    if (enabled) {
        uploadZone.classList.remove('disabled');
        fileInput.disabled = false;
    } else {
        cancelFile();
        uploadZone.classList.add('disabled');
        fileInput.disabled = true;
    }
}

function getInitials(name) {
    if (!name) return 'CL';
    const parts = name.trim().split(/\s+/).filter(Boolean);
    if (parts.length === 0) return 'CL';
    if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function formatDisplayCnpj(value) {
    if (!value) return '';
    const onlyDigits = value.replace(/\D/g, '');
    if (onlyDigits.length !== 14) return value;
    return onlyDigits.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, '$1.$2.$3/$4-$5');
}


