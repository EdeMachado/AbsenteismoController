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
});

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
}

function cancelFile() {
    selectedFile = null;
    document.getElementById('fileInput').value = '';
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
    
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('client_id', currentClient.id);
    
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
        
        const response = await fetch('/api/upload', {
            method: 'POST',
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
                
                if (confirm('Upload realizado com sucesso! Deseja ir para o dashboard?')) {
                    window.location.href = '/';
                }
            }, 2000);
            
        } else {
            throw new Error('Erro no upload');
        }
        
    } catch (error) {
        console.error('Erro:', error);
        document.getElementById('progressFill').style.width = '100%';
        document.getElementById('progressFill').style.background = 'var(--danger)';
        document.getElementById('progressText').textContent = 'Erro ao processar arquivo';
        
        setTimeout(() => {
            document.getElementById('progressContainer').style.display = 'none';
            document.getElementById('progressFill').style.background = 'var(--success)';
        }, 3000);
    }
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
    
    try {
        const response = await fetch(`/api/uploads/${id}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            alert('Upload deletado com sucesso');
            loadUploads();
        } else {
            alert('Erro ao deletar upload');
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao deletar upload');
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
    const storedId = typeof window.getCurrentClientId === 'function' ? window.getCurrentClientId(null) : null;
    const numericId = Number(storedId);
    currentClient = {
        id: Number.isFinite(numericId) && numericId > 0 ? numericId : null,
        name: localStorage.getItem('cliente_nome') || '',
        cnpj: localStorage.getItem('cliente_cnpj') || '',
        logo: localStorage.getItem('cliente_logo_url') || ''
    };
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


