// Sistema Automático de Processamento
let selectedFile = null;
let processingData = null;

document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Sistema Automático iniciado');
    
    initializeUpload();
    setupEventListeners();
});

// ==================== INICIALIZAÇÃO ====================

function initializeUpload() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const btnUpload = document.getElementById('btnUpload');
    
    // Drag and Drop
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
    
    // Click to select
    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });
    
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });
    
    // Upload button
    btnUpload.addEventListener('click', processFile);
}

function setupEventListeners() {
    // Event listeners para outras funcionalidades
    console.log('✅ Event listeners configurados');
}

// ==================== SELEÇÃO DE ARQUIVO ====================

function handleFileSelect(file) {
    console.log('📁 Arquivo selecionado:', file.name);
    
    // Validação do arquivo
    const allowedTypes = [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // .xlsx
        'application/vnd.ms-excel', // .xls
        'text/csv' // .csv
    ];
    
    if (!allowedTypes.includes(file.type) && !file.name.match(/\.(xlsx|xls|csv)$/i)) {
        showError('Por favor, selecione um arquivo Excel (.xlsx, .xls) ou CSV válido.');
        return;
    }
    
    // Validação do tamanho (máximo 10MB)
    if (file.size > 10 * 1024 * 1024) {
        showError('Arquivo muito grande. Tamanho máximo: 10MB');
        return;
    }
    
    selectedFile = file;
    showFileInfo(file);
    enableUploadButton();
    hideMessages();
}

function showFileInfo(file) {
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const fileDetails = document.getElementById('fileDetails');
    
    fileName.textContent = file.name;
    fileDetails.innerHTML = `
        <strong>Tamanho:</strong> ${formatFileSize(file.size)}<br>
        <strong>Tipo:</strong> ${file.type || 'Arquivo Excel/CSV'}<br>
        <strong>Última modificação:</strong> ${new Date(file.lastModified).toLocaleString()}
    `;
    
    fileInfo.style.display = 'block';
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function enableUploadButton() {
    document.getElementById('btnUpload').disabled = false;
}

function hideMessages() {
    document.getElementById('errorMessage').style.display = 'none';
    document.getElementById('successMessage').style.display = 'none';
}

// ==================== PROCESSAMENTO AUTOMÁTICO ====================

async function processFile() {
    if (!selectedFile) {
        showError('Nenhum arquivo selecionado.');
        return;
    }
    
    console.log('🚀 Iniciando processamento automático...');
    
    // Mostra seção de processamento
    showProcessingSection();
    
    try {
        // PASSO 1: Análise da Planilha
        await executeStep(1, 'Analisando estrutura da planilha...', 1000);
        const analysisResult = await analyzeSpreadsheet();
        
        // PASSO 2: Processamento IA
        await executeStep(2, 'Processando dados com IA...', 2000);
        const aiResult = await processWithAI(analysisResult);
        
        // PASSO 3: Geração de Dashboards
        await executeStep(3, 'Criando dashboards automáticos...', 1500);
        const dashboardResult = await generateDashboards(aiResult);
        
        // PASSO 4: Relatórios de Análise
        await executeStep(4, 'Gerando relatórios de análise...', 2000);
        const reportResult = await generateReports(aiResult);
        
        // PASSO 5: Apresentação Final
        await executeStep(5, 'Preparando apresentação executiva...', 1500);
        const presentationResult = await generatePresentation(aiResult);
        
        // Finaliza processamento
        await finalizeProcessing();
        
        // Salva dados para uso posterior
        processingData = {
            analysis: analysisResult,
            ai: aiResult,
            dashboard: dashboardResult,
            report: reportResult,
            presentation: presentationResult
        };
        
        // Mostra resultados
        showResults();
        
        console.log('✅ Processamento automático concluído!');
        
    } catch (error) {
        console.error('❌ Erro no processamento:', error);
        showError('Erro no processamento: ' + error.message);
        hideProcessingSection();
    }
}

async function executeStep(stepNumber, message, duration) {
    console.log(`📊 Passo ${stepNumber}: ${message}`);
    
    // Ativa o passo atual
    const step = document.getElementById(`step${stepNumber}`);
    step.classList.add('active');
    
    // Atualiza progresso
    const progress = (stepNumber / 5) * 100;
    document.getElementById('progressFill').style.width = progress + '%';
    
    // Simula processamento
    await new Promise(resolve => setTimeout(resolve, duration));
    
    // Completa o passo
    step.classList.remove('active');
    step.classList.add('completed');
}

async function analyzeSpreadsheet() {
    console.log('📊 Analisando planilha...');
    
    const formData = new FormData();
    formData.append('file', selectedFile);
    
    const response = await fetch('/api/upload/analyze', {
        method: 'POST',
        body: formData
    });
    
    if (!response.ok) {
        throw new Error('Erro ao analisar planilha');
    }
    
    const result = await response.json();
    console.log('✅ Análise da planilha concluída:', result);
    
    return result;
}

async function processWithAI(analysisResult) {
    console.log('🤖 Processando com IA...');
    
    // Simula processamento IA
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    const aiResult = {
        totalRecords: Math.floor(Math.random() * 1000) + 100,
        detectedPatterns: [
            'Padrão sazonal detectado',
            'Picos de absenteísmo identificados',
            'Correlação com períodos específicos'
        ],
        insights: [
            'Taxa de absenteísmo acima da média',
            'Setores críticos identificados',
            'Tendência crescente observada'
        ],
        recommendations: [
            'Implementar programa de bem-estar',
            'Revisar políticas de RH',
            'Monitorar setores específicos'
        ]
    };
    
    console.log('✅ Processamento IA concluído:', aiResult);
    return aiResult;
}

async function generateDashboards(aiResult) {
    console.log('📈 Gerando dashboards...');
    
    // Simula geração de dashboards
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    const dashboardResult = {
        charts: [
            'Gráfico de absenteísmo por setor',
            'Tendência temporal',
            'Análise por funcionário',
            'Distribuição por CID'
        ],
        metrics: {
            totalAbsences: aiResult.totalRecords,
            averageDays: 3.2,
            topSector: 'Produção',
            criticalPeriod: 'Janeiro-Março'
        }
    };
    
    console.log('✅ Dashboards gerados:', dashboardResult);
    return dashboardResult;
}

async function generateReports(aiResult) {
    console.log('📄 Gerando relatórios...');
    
    // Simula geração de relatórios
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    const reportResult = {
        executiveSummary: 'Análise completa do absenteísmo com insights e recomendações',
        detailedAnalysis: 'Relatório detalhado com gráficos e estatísticas',
        recommendations: aiResult.recommendations,
        charts: ['Gráficos de tendência', 'Análise comparativa', 'Projeções futuras']
    };
    
    console.log('✅ Relatórios gerados:', reportResult);
    return reportResult;
}

async function generatePresentation(aiResult) {
    console.log('🎯 Gerando apresentação...');
    
    // Simula geração de apresentação
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    const presentationResult = {
        slides: [
            'Slide 1: Resumo Executivo',
            'Slide 2: Principais Métricas',
            'Slide 3: Análise por Setor',
            'Slide 4: Tendências Temporais',
            'Slide 5: Recomendações',
            'Slide 6: Próximos Passos'
        ],
        keyPoints: aiResult.insights,
        recommendations: aiResult.recommendations
    };
    
    console.log('✅ Apresentação gerada:', presentationResult);
    return presentationResult;
}

async function finalizeProcessing() {
    console.log('🎉 Finalizando processamento...');
    
    // Atualiza progresso para 100%
    document.getElementById('progressFill').style.width = '100%';
    
    // Aguarda um pouco para mostrar o progresso completo
    await new Promise(resolve => setTimeout(resolve, 500));
}

// ==================== INTERFACE ====================

function showProcessingSection() {
    document.getElementById('processingSection').style.display = 'block';
    document.getElementById('resultsSection').style.display = 'none';
    
    // Reseta steps
    for (let i = 1; i <= 5; i++) {
        const step = document.getElementById(`step${i}`);
        step.classList.remove('active', 'completed');
    }
    
    // Reseta progresso
    document.getElementById('progressFill').style.width = '0%';
}

function hideProcessingSection() {
    document.getElementById('processingSection').style.display = 'none';
}

function showResults() {
    document.getElementById('processingSection').style.display = 'none';
    document.getElementById('resultsSection').style.display = 'block';
    
    showSuccess('Processamento concluído com sucesso! Todos os resultados estão prontos.');
}

function showError(message) {
    const errorDiv = document.getElementById('errorMessage');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    
    // Auto-hide após 5 segundos
    setTimeout(() => {
        errorDiv.style.display = 'none';
    }, 5000);
}

function showSuccess(message) {
    const successDiv = document.getElementById('successMessage');
    successDiv.textContent = message;
    successDiv.style.display = 'block';
    
    // Auto-hide após 5 segundos
    setTimeout(() => {
        successDiv.style.display = 'none';
    }, 5000);
}

// ==================== AÇÕES DOS RESULTADOS ====================

function openDashboard() {
    console.log('📊 Abrindo dashboard...');
    
    if (processingData && processingData.dashboard) {
        // Redireciona para o dashboard com os dados processados
        window.open('/dashboard_powerbi', '_blank');
    } else {
        alert('Dashboard ainda não está disponível. Processe uma planilha primeiro.');
    }
}

function downloadReport() {
    console.log('📄 Baixando relatório...');
    
    if (processingData && processingData.report) {
        // Simula download do relatório
        const reportContent = generateReportContent(processingData.report);
        downloadFile(reportContent, 'relatorio_absenteismo.pdf', 'application/pdf');
    } else {
        alert('Relatório ainda não está disponível. Processe uma planilha primeiro.');
    }
}

function openPresentation() {
    console.log('🎯 Abrindo apresentação...');
    
    if (processingData && processingData.presentation) {
        // Redireciona para a apresentação
        window.open('/apresentacao', '_blank');
    } else {
        alert('Apresentação ainda não está disponível. Processe uma planilha primeiro.');
    }
}

function downloadData() {
    console.log('📊 Baixando dados tratados...');
    
    if (processingData && processingData.ai) {
        // Simula download dos dados tratados
        const dataContent = generateDataContent(processingData.ai);
        downloadFile(dataContent, 'dados_tratados.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
    } else {
        alert('Dados tratados ainda não estão disponíveis. Processe uma planilha primeiro.');
    }
}

// ==================== UTILITÁRIOS ====================

function generateReportContent(reportData) {
    // Simula geração de conteúdo do relatório
    return `Relatório de Análise de Absenteísmo\n\n${reportData.executiveSummary}\n\nRecomendações:\n${reportData.recommendations.join('\n')}`;
}

function generateDataContent(aiData) {
    // Simula geração de conteúdo dos dados
    return `Dados Tratados\n\nTotal de Registros: ${aiData.totalRecords}\nInsights: ${aiData.insights.join(', ')}`;
}

function downloadFile(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

// ==================== INICIALIZAÇÃO FINAL ====================

console.log('🎯 Sistema Automático carregado e pronto!');
