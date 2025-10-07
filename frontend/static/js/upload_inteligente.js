/**
 * Upload Inteligente - Sistema de Análise Automática de Planilhas
 */

let selectedFile = null;
let columnAnalysis = [];
let processingSteps = [
    'Analisando estrutura da planilha...',
    'Detectando padrões nos dados...',
    'Aplicando IA para gênero e categorias...',
    'Calculando métricas automáticas...',
    'Gerando análises e insights...',
    'Finalizando processamento...'
];

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    setupUploadArea();
});

// Configurar área de upload
function setupUploadArea() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    
    // Clique na área
    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });
    
    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelect(files[0]);
        }
    });
    
    // Seleção de arquivo
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });
}

// Manipular seleção de arquivo
function handleFileSelect(file) {
    selectedFile = file;
    
    // Validar tipo de arquivo
    const allowedTypes = [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-excel',
        'text/csv'
    ];
    
    if (!allowedTypes.includes(file.type) && !file.name.match(/\.(xlsx|xls|csv)$/i)) {
        alert('Por favor, selecione um arquivo Excel (.xlsx, .xls) ou CSV válido.');
        return;
    }
    
    // Mostrar informações do arquivo
    document.getElementById('fileName').textContent = file.name;
    document.getElementById('fileSize').textContent = formatFileSize(file.size);
    document.getElementById('fileInfo').style.display = 'block';
}

// Analisar arquivo
async function analyzeFile() {
    if (!selectedFile) return;
    
    try {
        // Mostrar loading
        const analyzeBtn = document.querySelector('button[onclick="analyzeFile()"]');
        const originalText = analyzeBtn.innerHTML;
        analyzeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analisando...';
        analyzeBtn.disabled = true;
        
        // Criar FormData
        const formData = new FormData();
        formData.append('file', selectedFile);
        
        // Enviar para análise
        const response = await fetch('/api/upload/analyze', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Erro ao analisar arquivo');
        }
        
        const analysis = await response.json();
        columnAnalysis = analysis.columns;
        
        // Mostrar análise
        displayColumnAnalysis();
        
        // Restaurar botão
        analyzeBtn.innerHTML = originalText;
        analyzeBtn.disabled = false;
        
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao analisar arquivo: ' + error.message);
        
        // Restaurar botão
        const analyzeBtn = document.querySelector('button[onclick="analyzeFile()"]');
        analyzeBtn.innerHTML = '<i class="fas fa-search"></i> Analisar Planilha';
        analyzeBtn.disabled = false;
    }
}

// Exibir análise das colunas
function displayColumnAnalysis() {
    const container = document.getElementById('columnsList');
    container.innerHTML = '';
    
    columnAnalysis.forEach((column, index) => {
        const columnDiv = document.createElement('div');
        columnDiv.className = 'column-analysis';
        columnDiv.innerHTML = `
            <div class="column-header">
                <div>
                    <div class="column-name">${column.name}</div>
                    <div class="column-preview">Exemplo: ${column.preview}</div>
                </div>
                <div class="column-controls">
                    <label class="checkbox-item">
                        <input type="checkbox" id="include_${index}" ${column.include ? 'checked' : ''}>
                        <label for="include_${index}">Incluir</label>
                    </label>
                </div>
            </div>
            <div class="column-body">
                <div class="form-group">
                    <label>Esta coluna se refere a:</label>
                    <select class="form-control" id="type_${index}">
                        <option value="nome_funcionario" ${column.suggested_type === 'nome_funcionario' ? 'selected' : ''}>Nome do Funcionário</option>
                        <option value="cpf" ${column.suggested_type === 'cpf' ? 'selected' : ''}>CPF</option>
                        <option value="matricula" ${column.suggested_type === 'matricula' ? 'selected' : ''}>Matrícula</option>
                        <option value="setor" ${column.suggested_type === 'setor' ? 'selected' : ''}>Setor</option>
                        <option value="cargo" ${column.suggested_type === 'cargo' ? 'selected' : ''}>Cargo</option>
                        <option value="data_afastamento" ${column.suggested_type === 'data_afastamento' ? 'selected' : ''}>Data de Afastamento</option>
                        <option value="data_retorno" ${column.suggested_type === 'data_retorno' ? 'selected' : ''}>Data de Retorno</option>
                        <option value="cid" ${column.suggested_type === 'cid' ? 'selected' : ''}>CID</option>
                        <option value="descricao_cid" ${column.suggested_type === 'descricao_cid' ? 'selected' : ''}>Descrição do CID</option>
                        <option value="dias_atestado" ${column.suggested_type === 'dias_atestado' ? 'selected' : ''}>Dias de Atestado</option>
                        <option value="horas_atestado" ${column.suggested_type === 'horas_atestado' ? 'selected' : ''}>Horas de Atestado</option>
                        <option value="outro" ${column.suggested_type === 'outro' ? 'selected' : ''}>Outro</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>É interessante para análise?</label>
                    <div class="checkbox-group">
                        <label class="checkbox-item">
                            <input type="radio" name="analysis_${index}" value="sim" ${column.analysis_important ? 'checked' : ''}>
                            <label>Sim, importante</label>
                        </label>
                        <label class="checkbox-item">
                            <input type="radio" name="analysis_${index}" value="nao" ${!column.analysis_important ? 'checked' : ''}>
                            <label>Não, pode excluir</label>
                        </label>
                    </div>
                </div>
                
                <div class="form-group">
                    <label>Observações da IA:</label>
                    <div style="background: #f8f9fa; padding: 10px; border-radius: 4px; font-size: 14px; color: #6c757d;">
                        ${column.ai_notes}
                    </div>
                </div>
            </div>
        `;
        
        container.appendChild(columnDiv);
    });
    
    // Mostrar container de análise
    document.getElementById('analysisContainer').style.display = 'block';
}

// Processar dados
async function processData() {
    // Coletar configurações das colunas
    const columnConfigs = [];
    
    columnAnalysis.forEach((column, index) => {
        const include = document.getElementById(`include_${index}`).checked;
        const type = document.getElementById(`type_${index}`).value;
        const analysisImportant = document.querySelector(`input[name="analysis_${index}"]:checked`).value === 'sim';
        
        columnConfigs.push({
            name: column.name,
            include: include,
            type: type,
            analysis_important: analysisImportant
        });
    });
    
    // Mostrar processamento
    document.getElementById('analysisContainer').style.display = 'none';
    document.getElementById('processingContainer').style.display = 'block';
    
    // Simular progresso
    simulateProgress();
    
    try {
        // Criar FormData com configurações
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('config', JSON.stringify(columnConfigs));
        
        // Processar dados
        const response = await fetch('/api/upload/process', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Erro ao processar dados');
        }
        
        const result = await response.json();
        
        // Mostrar sucesso
        setTimeout(() => {
            document.getElementById('processingContainer').innerHTML = `
                <div style="color: #28a745; font-size: 48px; margin-bottom: 20px;">
                    <i class="fas fa-check-circle"></i>
                </div>
                <div style="font-size: 18px; color: #2c2c2c; margin-bottom: 10px;">
                    Processamento concluído com sucesso!
                </div>
                <div style="font-size: 14px; color: #6c757d; margin-bottom: 30px;">
                    ${result.total_records} registros processados e analisados
                </div>
                <button class="btn btn-primary" onclick="goToAnalysis()">
                    <i class="fas fa-chart-line"></i> Ver Análises
                </button>
            `;
        }, 2000);
        
    } catch (error) {
        console.error('Erro:', error);
        document.getElementById('processingContainer').innerHTML = `
            <div style="color: #dc3545; font-size: 48px; margin-bottom: 20px;">
                <i class="fas fa-exclamation-triangle"></i>
            </div>
            <div style="font-size: 18px; color: #2c2c2c; margin-bottom: 10px;">
                Erro no processamento
            </div>
            <div style="font-size: 14px; color: #6c757d; margin-bottom: 30px;">
                ${error.message}
            </div>
            <button class="btn btn-secondary" onclick="location.reload()">
                <i class="fas fa-redo"></i> Tentar Novamente
            </button>
        `;
    }
}

// Simular progresso
function simulateProgress() {
    let progress = 0;
    let stepIndex = 0;
    
    const interval = setInterval(() => {
        progress += Math.random() * 15;
        
        if (progress >= 100) {
            progress = 100;
            clearInterval(interval);
        }
        
        document.getElementById('progressFill').style.width = progress + '%';
        
        // Atualizar texto do passo
        if (stepIndex < processingSteps.length) {
            document.querySelector('.processing-subtext').textContent = processingSteps[stepIndex];
            stepIndex++;
        }
    }, 500);
}

// Ir para análise
function goToAnalysis() {
    window.location.href = '/dados_powerbi';
}

// Funções auxiliares
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}
