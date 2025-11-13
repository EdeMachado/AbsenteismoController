/**
 * Mapeamento de Colunas - JavaScript
 * Gerencia a configuração de mapeamento de colunas por cliente
 */

// Funções de drag and drop
function handleDragOver(event) {
    event.preventDefault();
    event.stopPropagation();
    event.currentTarget.style.borderColor = '#4CAF50';
    event.currentTarget.style.background = 'rgba(76, 175, 80, 0.1)';
}

function handleDragLeave(event) {
    event.preventDefault();
    event.stopPropagation();
    event.currentTarget.style.borderColor = 'var(--border)';
    event.currentTarget.style.background = 'var(--surface-hover)';
}

function handleDrop(event) {
    event.preventDefault();
    event.stopPropagation();
    event.currentTarget.style.borderColor = 'var(--border)';
    event.currentTarget.style.background = 'var(--surface-hover)';
    
    const files = event.dataTransfer.files;
    if (files.length > 0) {
        const file = files[0];
        if (file.name.toLowerCase().endsWith('.xlsx') || file.name.toLowerCase().endsWith('.xls')) {
            planilhaExemploFile = file;
            // Cria um evento sintético para processar
            const syntheticEvent = {
                target: {
                    files: files
                }
            };
            processarPlanilhaExemplo(syntheticEvent);
        } else {
            mostrarMensagemMapeamento('Por favor, selecione um arquivo Excel (.xlsx ou .xls)', 'erro');
        }
    }
}

let clienteMapeamentoId = null;
let colunasPlanilha = [];
let mapeamentoAtual = {};
let passoAtual = 1;
let planilhaExemploFile = null;
let camposPersonalizados = []; // Campos adicionados pelo usuário

// Campos do sistema disponíveis para mapeamento
const CAMPOS_SISTEMA = [
    { value: 'nomecompleto', label: 'Nome Completo', descricao: 'Nome do funcionário', obrigatorio: true },
    { value: 'cpf', label: 'CPF', descricao: 'CPF do funcionário', obrigatorio: false },
    { value: 'matricula', label: 'Matrícula', descricao: 'Matrícula do funcionário', obrigatorio: false },
    { value: 'setor', label: 'Setor', descricao: 'Setor/Departamento', obrigatorio: false },
    { value: 'centro_custo', label: 'Centro de Custo', descricao: 'Centro de custo', obrigatorio: false },
    { value: 'cargo', label: 'Cargo', descricao: 'Cargo do funcionário', obrigatorio: false },
    { value: 'data_afastamento', label: 'Data de Afastamento', descricao: 'Data de início do afastamento', obrigatorio: false },
    { value: 'data_retorno', label: 'Data de Retorno', descricao: 'Data de retorno ao trabalho', obrigatorio: false },
    { value: 'cid', label: 'CID', descricao: 'Código CID', obrigatorio: false },
    { value: 'diagnostico', label: 'Diagnóstico', descricao: 'Descrição do diagnóstico', obrigatorio: false },
    { value: 'descricao_cid', label: 'Descrição do CID', descricao: 'Descrição completa do CID', obrigatorio: false },
    { value: 'dias_atestados', label: 'Dias Atestados', descricao: 'Quantidade de dias de atestado', obrigatorio: false },
    { value: 'numero_dias_atestado', label: 'Número de Dias', descricao: 'Número de dias (alternativo)', obrigatorio: false },
    { value: 'horas_dia', label: 'Horas por Dia', descricao: 'Horas de atestado por dia', obrigatorio: false },
    { value: 'horas_perdi', label: 'Horas Perdidas', descricao: 'Total de horas perdidas', obrigatorio: false },
    { value: 'numero_horas_atestado', label: 'Número de Horas', descricao: 'Número de horas (alternativo)', obrigatorio: false },
    { value: 'motivo_atestado', label: 'Motivo do Atestado', descricao: 'Motivo do afastamento', obrigatorio: false },
    { value: 'escala', label: 'Escala', descricao: 'Escala de trabalho', obrigatorio: false },
    { value: 'tipo_atestado', label: 'Tipo de Atestado', descricao: 'Tipo do atestado', obrigatorio: false },
    { value: 'descricao_atestad', label: 'Descrição do Atestado', descricao: 'Descrição do atestado', obrigatorio: false }
];

// Função global para abrir modal de mapeamento direto no passo 4 (gráficos)
window.configurarGraficos = async function(clientId) {
    clienteMapeamentoId = clientId;
    passoAtual = 4;
    colunasPlanilha = [];
    mapeamentoAtual = {};
    planilhaExemploFile = null;
    camposPersonalizados = []; // Reseta campos personalizados
    graficosConfigurados = []; // Reseta gráficos configurados
    
    // Busca campos personalizados se existirem
    try {
        const response = await fetch(`/api/clientes/${clientId}/column-mapping`);
        if (response.ok) {
            const data = await response.json();
            if (data.custom_fields && Array.isArray(data.custom_fields)) {
                camposPersonalizados = data.custom_fields;
            }
        }
    } catch (error) {
        console.error('Erro ao carregar campos personalizados:', error);
    }
    
    // Busca mapeamento existente para carregar campos disponíveis
    try {
        const responseMapping = await fetch(`/api/clientes/${clientId}/column-mapping`);
        if (responseMapping.ok) {
            const dataMapping = await responseMapping.json();
            if (dataMapping.column_mapping && Object.keys(dataMapping.column_mapping).length > 0) {
                mapeamentoAtual = dataMapping.column_mapping;
            }
            if (dataMapping.custom_fields && Array.isArray(dataMapping.custom_fields)) {
                camposPersonalizados = dataMapping.custom_fields;
            }
        }
    } catch (error) {
        console.error('Erro ao carregar mapeamento:', error);
    }
    
    // Busca gráficos configurados
    await carregarGraficosConfigurados();
    
    // Busca nome do cliente
    const clientesList = window.clientes || (typeof clientes !== 'undefined' ? clientes : []);
    const cliente = clientesList.find(c => c.id === clientId);
    const nomeCliente = cliente ? (cliente.nome_fantasia || cliente.nome) : 'Cliente';
    
    document.getElementById('modalMapeamentoTitle').textContent = `Configurar Gráficos - ${nomeCliente}`;
    document.getElementById('modalMapeamento').style.display = 'flex';
    
    mostrarPassoMapeamento(4);
};

// Função global para abrir modal de mapeamento
window.configurarMapeamento = async function(clientId) {
    clienteMapeamentoId = clientId;
    passoAtual = 1;
    colunasPlanilha = [];
    mapeamentoAtual = {};
    planilhaExemploFile = null;
    camposPersonalizados = []; // Reseta campos personalizados
    graficosConfigurados = []; // Reseta gráficos configurados
    
    // Busca mapeamento existente
    try {
        const response = await fetch(`/api/clientes/${clientId}/column-mapping`);
        if (response.ok) {
            const data = await response.json();
            if (data.column_mapping && Object.keys(data.column_mapping).length > 0) {
                mapeamentoAtual = data.column_mapping;
                mostrarMensagemMapeamento('Mapeamento existente encontrado. Você pode editá-lo ou criar um novo.', 'info');
            }
            // Carrega campos personalizados se existirem
            if (data.custom_fields && Array.isArray(data.custom_fields)) {
                camposPersonalizados = data.custom_fields;
            }
        }
    } catch (error) {
        console.error('Erro ao carregar mapeamento:', error);
    }
    
    // Busca gráficos configurados
    await carregarGraficosConfigurados();
    
    // Busca nome do cliente
    const clientesList = window.clientes || (typeof clientes !== 'undefined' ? clientes : []);
    const cliente = clientesList.find(c => c.id === clientId);
    const nomeCliente = cliente ? (cliente.nome_fantasia || cliente.nome) : 'Cliente';
    
    document.getElementById('modalMapeamentoTitle').textContent = `Configurar Mapeamento - ${nomeCliente}`;
    document.getElementById('modalMapeamento').style.display = 'flex';
    
    mostrarPassoMapeamento(1);
};

function fecharModalMapeamento() {
    document.getElementById('modalMapeamento').style.display = 'none';
    clienteMapeamentoId = null;
    colunasPlanilha = [];
    mapeamentoAtual = {};
    passoAtual = 1;
    planilhaExemploFile = null;
}

window.fecharModalMapeamento = fecharModalMapeamento;

let graficosConfigurados = []; // Armazena gráficos configurados pelo usuário

function mostrarPassoMapeamento(passo) {
    passoAtual = passo;
    
    // Oculta todos os passos
    document.getElementById('mapeamentoPasso1').style.display = passo === 1 ? 'block' : 'none';
    document.getElementById('mapeamentoPasso2').style.display = passo === 2 ? 'block' : 'none';
    document.getElementById('mapeamentoPasso3').style.display = passo === 3 ? 'block' : 'none';
    document.getElementById('mapeamentoPasso4').style.display = passo === 4 ? 'block' : 'none';
    
    // Controla botões
    document.getElementById('btnVoltarMapeamento').style.display = passo > 1 ? 'inline-flex' : 'none';
    // Mostra "Avançar" apenas se houver planilha processada no passo 1, ou se estiver no passo 2 ou 3
    const temPlanilha = passo === 1 ? planilhaExemploFile !== null : true;
    document.getElementById('btnAvancarMapeamento').style.display = (passo < 4 && temPlanilha) ? 'inline-flex' : 'none';
    document.getElementById('btnSalvarMapeamento').style.display = passo === 4 ? 'inline-flex' : 'none';
    
    // Se for passo 4, renderiza gráficos configurados
    if (passo === 4) {
        renderizarGraficosConfigurados();
    }
}

function voltarPassoMapeamento() {
    if (passoAtual > 1) {
        mostrarPassoMapeamento(passoAtual - 1);
    }
}

window.voltarPassoMapeamento = voltarPassoMapeamento;

async function processarPlanilhaExemplo(event) {
    const file = event.target.files ? event.target.files[0] : planilhaExemploFile;
    if (!file) return;
    
    if (!file.name.toLowerCase().endsWith('.xlsx') && !file.name.toLowerCase().endsWith('.xls')) {
        mostrarMensagemMapeamento('Por favor, selecione um arquivo Excel (.xlsx ou .xls)', 'erro');
        return;
    }
    
    planilhaExemploFile = file;
    
    try {
        // Mostra loading
        const uploadZone = document.getElementById('uploadZoneMapeamento');
        uploadZone.innerHTML = '<div style="text-align: center; padding: 40px;"><i class="fas fa-spinner fa-spin" style="font-size: 48px; color: var(--primary);"></i><p style="margin-top: 16px;">Processando planilha...</p></div>';
        
        // Envia para preview (sem mapeamento ainda)
        const formData = new FormData();
        formData.append('file', file);
        formData.append('column_mapping', JSON.stringify({}));
        
        const response = await fetch(`/api/clientes/${clienteMapeamentoId}/column-mapping/preview`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Erro ao processar planilha');
        }
        
        const data = await response.json();
        colunasPlanilha = data.columns_original || [];
        
        if (colunasPlanilha.length === 0) {
            throw new Error('Nenhuma coluna encontrada na planilha');
        }
        
        // Mostra sucesso e avança para passo 2
        uploadZone.innerHTML = `
            <div style="text-align: center; padding: 20px; background: #e8f5e9; border-radius: 8px; border: 2px solid #4caf50;">
                <i class="fas fa-check-circle" style="font-size: 48px; color: #4caf50; margin-bottom: 16px;"></i>
                <p style="font-weight: 600; color: #2e7d32;">Planilha processada com sucesso!</p>
                <p style="font-size: 14px; color: #666; margin-top: 8px;">${colunasPlanilha.length} coluna(s) encontrada(s)</p>
            </div>
        `;
        
        // Aguarda um pouco e avança
        setTimeout(() => {
            renderizarMapeamentoColunas();
            mostrarPassoMapeamento(2);
            // Atualiza botão avançar para aparecer
            document.getElementById('btnAvancarMapeamento').style.display = 'inline-flex';
        }, 1000);
        
    } catch (error) {
        console.error('Erro ao processar planilha:', error);
        mostrarMensagemMapeamento('Erro ao processar planilha: ' + error.message, 'erro');
        
        // Restaura upload zone
        const uploadZone = document.getElementById('uploadZoneMapeamento');
        uploadZone.innerHTML = `
            <input type="file" id="planilhaExemplo" accept=".xlsx,.xls" style="display: none;" onchange="processarPlanilhaExemplo(event)">
            <div style="text-align: center; padding: 40px;">
                <i class="fas fa-file-excel" style="font-size: 64px; color: #4CAF50; margin-bottom: 16px;"></i>
                <p style="margin-bottom: 16px; font-size: 16px; font-weight: 600;">Arraste uma planilha aqui ou clique para selecionar</p>
                <button type="button" class="btn btn-primary" onclick="document.getElementById('planilhaExemplo').click()">
                    <i class="fas fa-folder-open"></i> Selecionar Planilha
                </button>
            </div>
        `;
    }
}

window.processarPlanilhaExemplo = processarPlanilhaExemplo;

function renderizarMapeamentoColunas() {
    const container = document.getElementById('mapeamentoColunas');
    
    if (colunasPlanilha.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: var(--text-secondary);">Nenhuma coluna encontrada</p>';
        return;
    }
    
    // Combina campos do sistema com campos personalizados
    const todosCampos = [...CAMPOS_SISTEMA, ...camposPersonalizados];
    
    container.innerHTML = `
        <div style="margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
            <h4 style="margin: 0;"><i class="fas fa-table"></i> Mapear Colunas da Planilha</h4>
            <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                <button type="button" onclick="mapearTodasColunas()" class="btn btn-secondary" style="display: inline-flex; align-items: center; gap: 8px; padding: 10px 16px; font-size: 14px;">
                    <i class="fas fa-check-double"></i> Mapear Todas Automaticamente
                </button>
                <button type="button" onclick="limparTodosMapeamentos()" class="btn btn-secondary" style="display: inline-flex; align-items: center; gap: 8px; padding: 10px 16px; font-size: 14px;">
                    <i class="fas fa-eraser"></i> Limpar Todos
                </button>
                <button type="button" onclick="abrirModalAdicionarCampo()" class="btn btn-primary" style="display: inline-flex; align-items: center; gap: 8px; padding: 10px 16px; font-size: 14px;">
                    <i class="fas fa-plus"></i> Adicionar Campo Personalizado
                </button>
            </div>
        </div>
        ${colunasPlanilha.map((coluna, index) => {
        // Tenta detectar automaticamente o campo sugerido
        const campoSugerido = detectarCampoSugerido(coluna);
        const valorAtual = mapeamentoAtual[coluna] || campoSugerido || '';
        
        return `
            <div class="mapeamento-item" style="background: var(--surface); border-radius: 12px; padding: 20px; border: 2px solid var(--border);">
                <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 16px; align-items: center;">
                    <div>
                        <label style="font-weight: 600; color: var(--text-primary); margin-bottom: 8px; display: block;">
                            <i class="fas fa-columns"></i> Coluna da Planilha
                        </label>
                        <div style="padding: 12px; background: var(--surface-hover); border-radius: 8px; font-family: monospace; font-size: 14px;">
                            ${coluna}
                        </div>
                    </div>
                    <div>
                        <label style="font-weight: 600; color: var(--text-primary); margin-bottom: 8px; display: block;">
                            <i class="fas fa-link"></i> Mapear para Campo do Sistema
                        </label>
                        <select class="campo-mapeamento-select" data-coluna="${coluna}" onchange="atualizarMapeamento('${coluna}', this.value)" style="width: 100%; padding: 12px; border: 2px solid var(--border); border-radius: 8px; background: var(--surface); color: var(--text-primary); font-size: 14px;">
                            <option value="">-- Não mapear (ignorar) --</option>
                            ${todosCampos.map(campo => `
                                <option value="${campo.value}" ${valorAtual === campo.value ? 'selected' : ''} 
                                    data-descricao="${campo.descricao}" 
                                    ${campo.obrigatorio ? 'data-obrigatorio="true"' : ''}
                                    ${campo.personalizado ? 'data-personalizado="true"' : ''}>
                                    ${campo.label} ${campo.obrigatorio ? '(Recomendado)' : ''} ${campo.personalizado ? '(Personalizado)' : ''}
                                </option>
                            `).join('')}
                        </select>
                        <div class="campo-descricao" style="margin-top: 6px; font-size: 12px; color: var(--text-secondary);">
                            ${valorAtual ? todosCampos.find(c => c.value === valorAtual)?.descricao || '' : 'Selecione um campo para ver a descrição'}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('')}
    `;
    
    // Adiciona listeners para mostrar descrição ao selecionar
    container.querySelectorAll('.campo-mapeamento-select').forEach(select => {
        select.addEventListener('change', function() {
            const descricaoDiv = this.parentElement.querySelector('.campo-descricao');
            const selectedOption = this.options[this.selectedIndex];
            const descricao = selectedOption.getAttribute('data-descricao') || '';
            descricaoDiv.textContent = descricao || 'Selecione um campo para ver a descrição';
        });
    });
}

function detectarCampoSugerido(nomeColuna) {
    const nomeLower = nomeColuna.toLowerCase();
    
    // Mapeamento inteligente baseado no nome da coluna
    if (nomeLower.includes('nome') && (nomeLower.includes('funcionario') || nomeLower.includes('funcionário') || nomeLower.includes('completo'))) {
        return 'nomecompleto';
    }
    if (nomeLower.includes('cpf')) {
        return 'cpf';
    }
    if (nomeLower.includes('matricula') || nomeLower.includes('matrícula')) {
        return 'matricula';
    }
    if (nomeLower.includes('setor') || nomeLower.includes('departamento')) {
        return 'setor';
    }
    if (nomeLower.includes('centro') && nomeLower.includes('custo')) {
        return 'centro_custo';
    }
    if (nomeLower.includes('cargo')) {
        return 'cargo';
    }
    if (nomeLower.includes('afastamento') || nomeLower.includes('inicio') || nomeLower.includes('início')) {
        return 'data_afastamento';
    }
    if (nomeLower.includes('retorno') || nomeLower.includes('fim')) {
        return 'data_retorno';
    }
    if (nomeLower.includes('cid') && !nomeLower.includes('descricao') && !nomeLower.includes('descrição')) {
        return 'cid';
    }
    if (nomeLower.includes('diagnostico') || nomeLower.includes('diagnóstico') || (nomeLower.includes('descricao') && nomeLower.includes('cid'))) {
        return 'diagnostico';
    }
    if (nomeLower.includes('dias') && (nomeLower.includes('atestado') || nomeLower.includes('perdido'))) {
        return 'dias_atestados';
    }
    if (nomeLower.includes('horas') && (nomeLower.includes('perdida') || nomeLower.includes('atestado'))) {
        return 'horas_perdi';
    }
    if (nomeLower.includes('motivo')) {
        return 'motivo_atestado';
    }
    if (nomeLower.includes('escala')) {
        return 'escala';
    }
    
    return '';
}

function atualizarMapeamento(coluna, campo) {
    if (campo) {
        mapeamentoAtual[coluna] = campo;
    } else {
        delete mapeamentoAtual[coluna];
    }
}

window.atualizarMapeamento = atualizarMapeamento;

async function avancarPassoMapeamento() {
    if (passoAtual === 1) {
        if (!planilhaExemploFile) {
            mostrarMensagemMapeamento('Por favor, envie uma planilha de exemplo primeiro', 'erro');
            return;
        }
        mostrarPassoMapeamento(2);
    } else if (passoAtual === 2) {
        // Valida se pelo menos o nome foi mapeado
        const nomeMapeado = Object.values(mapeamentoAtual).includes('nomecompleto');
        if (!nomeMapeado) {
            if (!confirm('Nenhuma coluna foi mapeada para "Nome Completo". Isso pode causar problemas. Deseja continuar mesmo assim?')) {
                return;
            }
        }
        
        // Gera preview
        await gerarPreviewMapeamento();
        mostrarPassoMapeamento(3);
    } else if (passoAtual === 3) {
        // Carrega gráficos existentes se houver
        await carregarGraficosConfigurados();
        mostrarPassoMapeamento(4);
    }
}

window.avancarPassoMapeamento = avancarPassoMapeamento;

async function gerarPreviewMapeamento() {
    const previewContainer = document.getElementById('previewMapeamento');
    previewContainer.innerHTML = '<div style="text-align: center; padding: 20px;"><i class="fas fa-spinner fa-spin"></i> Gerando preview...</div>';
    
    try {
        if (!planilhaExemploFile) {
            throw new Error('Planilha de exemplo não encontrada');
        }
        
        const formData = new FormData();
        formData.append('file', planilhaExemploFile);
        formData.append('column_mapping', JSON.stringify(mapeamentoAtual));
        
        const response = await fetch(`/api/clientes/${clienteMapeamentoId}/column-mapping/preview`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Erro ao gerar preview');
        }
        
        const data = await response.json();
        
        // Renderiza preview
        let previewHTML = `
            <div style="margin-bottom: 20px;">
                <h4 style="margin-bottom: 12px;"><i class="fas fa-info-circle"></i> Resumo do Mapeamento</h4>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-bottom: 20px;">
                    <div style="background: var(--surface); padding: 12px; border-radius: 8px;">
                        <div style="font-size: 12px; color: var(--text-secondary);">Colunas Originais</div>
                        <div style="font-size: 20px; font-weight: 700; color: var(--primary);">${data.columns_original?.length || 0}</div>
                    </div>
                    <div style="background: var(--surface); padding: 12px; border-radius: 8px;">
                        <div style="font-size: 12px; color: var(--text-secondary);">Colunas Mapeadas</div>
                        <div style="font-size: 20px; font-weight: 700; color: var(--success);">${Object.keys(mapeamentoAtual).length}</div>
                    </div>
                    <div style="background: var(--surface); padding: 12px; border-radius: 8px;">
                        <div style="font-size: 12px; color: var(--text-secondary);">Registros de Preview</div>
                        <div style="font-size: 20px; font-weight: 700; color: var(--info);">${data.total_rows || 0}</div>
                    </div>
                </div>
            </div>
        `;
        
        if (data.preview && data.preview.length > 0) {
            previewHTML += `
                <div style="margin-bottom: 20px;">
                    <h4 style="margin-bottom: 12px;"><i class="fas fa-table"></i> Preview dos Dados (primeiras 3 linhas)</h4>
                    <div style="overflow-x: auto;">
                        <table style="width: 100%; border-collapse: collapse; background: var(--surface); border-radius: 8px; overflow: hidden;">
                            <thead>
                                <tr style="background: var(--surface-hover);">
                                    ${data.columns_mapped?.map(col => `<th style="padding: 12px; text-align: left; border-bottom: 2px solid var(--border); font-weight: 600;">${col}</th>`).join('')}
                                </tr>
                            </thead>
                            <tbody>
                                ${data.preview.map(row => `
                                    <tr style="border-bottom: 1px solid var(--border);">
                                        ${data.columns_mapped?.map(col => {
                                            const valor = row[col];
                                            return `<td style="padding: 10px; font-size: 13px;">${valor !== null && valor !== undefined ? String(valor).substring(0, 50) : '-'}</td>`;
                                        }).join('')}
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        }
        
        // Lista mapeamentos
        previewHTML += `
            <div>
                <h4 style="margin-bottom: 12px;"><i class="fas fa-list"></i> Mapeamentos Configurados</h4>
                <div style="display: flex; flex-direction: column; gap: 8px;">
                    ${Object.entries(mapeamentoAtual).map(([coluna, campo]) => {
                        const todosCampos = [...CAMPOS_SISTEMA, ...camposPersonalizados];
                        const campoInfo = todosCampos.find(c => c.value === campo);
                        return `
                            <div style="display: flex; align-items: center; gap: 12px; padding: 10px; background: var(--surface); border-radius: 8px; border-left: 4px solid var(--primary);">
                                <div style="flex: 1;">
                                    <div style="font-weight: 600; font-size: 13px; color: var(--text-primary);">${coluna}</div>
                                    <div style="font-size: 11px; color: var(--text-secondary);">Coluna da planilha</div>
                                </div>
                                <div style="color: var(--text-secondary);"><i class="fas fa-arrow-right"></i></div>
                                <div style="flex: 1;">
                                    <div style="font-weight: 600; font-size: 13px; color: var(--primary);">${campoInfo?.label || campo} ${campoInfo?.personalizado ? '(Personalizado)' : ''}</div>
                                    <div style="font-size: 11px; color: var(--text-secondary);">${campoInfo?.descricao || 'Campo do sistema'}</div>
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        `;
        
        previewContainer.innerHTML = previewHTML;
        
    } catch (error) {
        console.error('Erro ao gerar preview:', error);
        previewContainer.innerHTML = `
            <div style="text-align: center; padding: 20px; background: #ffebee; border-radius: 8px; border: 2px solid #f44336;">
                <i class="fas fa-exclamation-triangle" style="font-size: 48px; color: #f44336; margin-bottom: 16px;"></i>
                <p style="font-weight: 600; color: #c62828;">Erro ao gerar preview</p>
                <p style="font-size: 14px; color: #666; margin-top: 8px;">${error.message}</p>
            </div>
        `;
    }
}

async function salvarMapeamento() {
    // Se estiver no passo 4 (gráficos), pode salvar apenas os gráficos
    if (passoAtual === 4) {
        return await salvarApenasGraficos();
    }
    
    // Para os outros passos, valida mapeamento
    if (Object.keys(mapeamentoAtual).length === 0) {
        if (!confirm('Nenhum mapeamento foi configurado. Deseja salvar mesmo assim? (Isso removerá o mapeamento existente)')) {
            return;
        }
    }
    
    try {
        // Salva mapeamento
        const response = await fetch(`/api/clientes/${clienteMapeamentoId}/column-mapping`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                column_mapping: mapeamentoAtual,
                custom_fields: camposPersonalizados
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Erro ao salvar mapeamento');
        }
        
        // Salva gráficos configurados
        try {
            const responseGraficos = await fetch(`/api/clientes/${clienteMapeamentoId}/graficos`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    graficos: graficosConfigurados
                })
            });
            
            if (!responseGraficos.ok) {
                console.warn('Erro ao salvar gráficos, mas mapeamento foi salvo');
            }
        } catch (error) {
            console.warn('Erro ao salvar gráficos:', error);
        }
        
        mostrarMensagemMapeamento('Mapeamento e gráficos salvos com sucesso! Agora você pode fazer upload de planilhas e visualizar os gráficos no dashboard.', 'sucesso');
        
        // Fecha modal após 2 segundos
        setTimeout(() => {
            fecharModalMapeamento();
        }, 2000);
        
    } catch (error) {
        console.error('Erro ao salvar mapeamento:', error);
        mostrarMensagemMapeamento('Erro ao salvar mapeamento: ' + error.message, 'erro');
    }
}

async function salvarApenasGraficos() {
    console.log('💾 Salvando gráficos...', graficosConfigurados);
    
    if (graficosConfigurados.length === 0) {
        if (!confirm('Nenhum gráfico foi configurado. Deseja salvar mesmo assim? (Isso removerá os gráficos existentes)')) {
            return;
        }
    }
    
    if (!clienteMapeamentoId) {
        alert('Erro: Cliente não identificado. Por favor, feche e abra novamente o modal.');
        console.error('❌ clienteMapeamentoId não definido ao salvar');
        return;
    }
    
    try {
        console.log('🌐 Enviando gráficos para salvar...', {
            clienteId: clienteMapeamentoId,
            quantidade: graficosConfigurados.length,
            graficos: graficosConfigurados
        });
        
        // Salva apenas gráficos configurados
        const responseGraficos = await fetch(`/api/clientes/${clienteMapeamentoId}/graficos`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                graficos: graficosConfigurados
            })
        });
        
        console.log('📡 Resposta do servidor:', responseGraficos.status);
        
        if (!responseGraficos.ok) {
            let errorData;
            try {
                errorData = await responseGraficos.json();
            } catch (e) {
                errorData = { detail: `Erro ${responseGraficos.status}: ${responseGraficos.statusText}` };
            }
            console.error('❌ Erro ao salvar:', errorData);
            throw new Error(errorData.detail || 'Erro ao salvar gráficos');
        }
        
        const result = await responseGraficos.json();
        console.log('✅ Gráficos salvos com sucesso!', result);
        
        mostrarMensagemMapeamento(`${graficosConfigurados.length} gráfico(s) salvo(s) com sucesso! Eles aparecerão no dashboard após você fazer upload de dados.`, 'sucesso');
        
        // Fecha modal após 2 segundos
        setTimeout(() => {
            fecharModalMapeamento();
        }, 2000);
        
    } catch (error) {
        console.error('❌ Erro ao salvar gráficos:', error);
        mostrarMensagemMapeamento('Erro ao salvar gráficos: ' + error.message, 'erro');
    }
}

window.salvarMapeamento = salvarMapeamento;

// ==================== GERENCIAR CAMPOS PERSONALIZADOS ====================

function abrirModalAdicionarCampo() {
    // Cria modal se não existir
    let modal = document.getElementById('modalAdicionarCampo');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'modalAdicionarCampo';
        modal.className = 'modal';
        modal.style.display = 'none';
        modal.innerHTML = `
            <div class="modal-content" style="max-width: 600px;">
                <div class="modal-header">
                    <h2>Adicionar Campo Personalizado</h2>
                    <button class="modal-close" onclick="fecharModalAdicionarCampo()">&times;</button>
                </div>
                <div class="modal-body">
                    <form id="formAdicionarCampo" onsubmit="salvarCampoPersonalizado(event)">
                        <div class="form-group">
                            <label class="form-label">Nome do Campo (ex: telefone, email, observacao)</label>
                            <input type="text" id="campoNome" class="form-input" required 
                                   placeholder="telefone" pattern="[a-z0-9_]+" 
                                   title="Use apenas letras minúsculas, números e underscore">
                            <small style="color: var(--text-secondary); font-size: 12px;">
                                Use apenas letras minúsculas, números e underscore (sem espaços)
                            </small>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Rótulo (Nome de Exibição)</label>
                            <input type="text" id="campoLabel" class="form-input" required 
                                   placeholder="Telefone">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Descrição</label>
                            <textarea id="campoDescricao" class="form-input" rows="3" 
                                      placeholder="Telefone de contato do funcionário"></textarea>
                        </div>
                        <div class="form-group">
                            <label class="checkbox-item">
                                <input type="checkbox" id="campoObrigatorio">
                                <span>Campo obrigatório (recomendado)</span>
                            </label>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" onclick="fecharModalAdicionarCampo()">Cancelar</button>
                    <button type="submit" form="formAdicionarCampo" class="btn btn-primary">
                        <i class="fas fa-save"></i> Adicionar Campo
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }
    
    // Limpa formulário
    document.getElementById('campoNome').value = '';
    document.getElementById('campoLabel').value = '';
    document.getElementById('campoDescricao').value = '';
    document.getElementById('campoObrigatorio').checked = false;
    
    modal.style.display = 'flex';
}

window.abrirModalAdicionarCampo = abrirModalAdicionarCampo;

function fecharModalAdicionarCampo() {
    const modal = document.getElementById('modalAdicionarCampo');
    if (modal) {
        modal.style.display = 'none';
    }
}

window.fecharModalAdicionarCampo = fecharModalAdicionarCampo;

function salvarCampoPersonalizado(event) {
    event.preventDefault();
    
    const nome = document.getElementById('campoNome').value.trim().toLowerCase();
    const label = document.getElementById('campoLabel').value.trim();
    const descricao = document.getElementById('campoDescricao').value.trim();
    const obrigatorio = document.getElementById('campoObrigatorio').checked;
    
    // Valida nome
    if (!/^[a-z0-9_]+$/.test(nome)) {
        alert('O nome do campo deve conter apenas letras minúsculas, números e underscore');
        return;
    }
    
    // Verifica se já existe
    const existe = CAMPOS_SISTEMA.find(c => c.value === nome) || camposPersonalizados.find(c => c.value === nome);
    if (existe) {
        alert('Este campo já existe! Escolha outro nome.');
        return;
    }
    
    // Adiciona campo personalizado
    const novoCampo = {
        value: nome,
        label: label || nome,
        descricao: descricao || `Campo personalizado: ${label || nome}`,
        obrigatorio: obrigatorio,
        personalizado: true
    };
    
    camposPersonalizados.push(novoCampo);
    
    // Atualiza renderização
    renderizarMapeamentoColunas();
    
    // Fecha modal
    fecharModalAdicionarCampo();
    
    mostrarMensagemMapeamento(`Campo "${label}" adicionado com sucesso!`, 'sucesso');
}

window.salvarCampoPersonalizado = salvarCampoPersonalizado;

// ==================== MAPEAR TODAS AS COLUNAS ====================

function mapearTodasColunas() {
    if (colunasPlanilha.length === 0) {
        mostrarMensagemMapeamento('Nenhuma coluna disponível para mapear', 'erro');
        return;
    }
    
    if (!confirm(`Deseja mapear automaticamente todas as ${colunasPlanilha.length} colunas? O sistema tentará detectar o melhor campo para cada coluna.`)) {
        return;
    }
    
    // Mapeia todas as colunas automaticamente
    colunasPlanilha.forEach(coluna => {
        const campoSugerido = detectarCampoSugerido(coluna);
        if (campoSugerido) {
            mapeamentoAtual[coluna] = campoSugerido;
        } else {
            // Se não detectar, cria um campo personalizado baseado no nome da coluna
            const nomeCampo = coluna.toLowerCase()
                .replace(/[^a-z0-9]/g, '_')
                .replace(/_+/g, '_')
                .replace(/^_|_$/g, '');
            
            // Verifica se já existe um campo personalizado com esse nome
            let campoPersonalizado = camposPersonalizados.find(c => c.value === nomeCampo);
            
            if (!campoPersonalizado && nomeCampo) {
                // Cria campo personalizado automaticamente
                campoPersonalizado = {
                    value: nomeCampo,
                    label: coluna,
                    descricao: `Campo personalizado para a coluna "${coluna}"`,
                    obrigatorio: false,
                    personalizado: true
                };
                camposPersonalizados.push(campoPersonalizado);
            }
            
            if (campoPersonalizado) {
                mapeamentoAtual[coluna] = campoPersonalizado.value;
            }
        }
    });
    
    // Re-renderiza para atualizar os selects
    renderizarMapeamentoColunas();
    
    mostrarMensagemMapeamento(`Todas as ${colunasPlanilha.length} colunas foram mapeadas automaticamente!`, 'sucesso');
}

window.mapearTodasColunas = mapearTodasColunas;

function limparTodosMapeamentos() {
    if (Object.keys(mapeamentoAtual).length === 0) {
        mostrarMensagemMapeamento('Nenhum mapeamento para limpar', 'info');
        return;
    }
    
    if (!confirm('Deseja limpar todos os mapeamentos? Esta ação não pode ser desfeita.')) {
        return;
    }
    
    mapeamentoAtual = {};
    
    // Re-renderiza para atualizar os selects
    renderizarMapeamentoColunas();
    
    mostrarMensagemMapeamento('Todos os mapeamentos foram limpos', 'sucesso');
}

window.limparTodosMapeamentos = limparTodosMapeamentos;

// ==================== CONFIGURAR GRÁFICOS PERSONALIZADOS ====================

async function carregarGraficosConfigurados() {
    if (!clienteMapeamentoId) return;
    
    try {
        const response = await fetch(`/api/clientes/${clienteMapeamentoId}/graficos`);
        if (response.ok) {
            const data = await response.json();
            if (data.graficos && Array.isArray(data.graficos)) {
                graficosConfigurados = data.graficos;
            }
        }
    } catch (error) {
        console.error('Erro ao carregar gráficos configurados:', error);
        graficosConfigurados = [];
    }
}

function renderizarGraficosConfigurados() {
    const container = document.getElementById('graficosConfigurados');
    if (!container) return;
    
    if (graficosConfigurados.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 40px; background: var(--surface-hover); border-radius: 8px; border: 2px dashed var(--border);">
                <i class="fas fa-chart-bar" style="font-size: 48px; color: var(--text-secondary); margin-bottom: 16px;"></i>
                <p style="color: var(--text-secondary); font-size: 14px;">Nenhum gráfico configurado ainda.</p>
                <p style="color: var(--text-secondary); font-size: 12px; margin-top: 8px;">Clique em "Adicionar Gráfico" para começar.</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = graficosConfigurados.map((grafico, index) => {
        const tipoIcone = {
            'bar': 'fa-chart-bar',
            'line': 'fa-chart-line',
            'pie': 'fa-chart-pie',
            'doughnut': 'fa-circle',
            'area': 'fa-chart-area',
            'scatter': 'fa-chart-scatter'
        }[grafico.tipo] || 'fa-chart-bar';
        
        return `
            <div class="grafico-config-item" style="background: var(--surface); border-radius: 12px; padding: 20px; border: 2px solid var(--border);">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
                    <div style="flex: 1;">
                        <h4 style="margin: 0 0 8px 0; color: var(--text-primary); display: flex; align-items: center; gap: 8px;">
                            <i class="fas ${tipoIcone}"></i> ${grafico.titulo || 'Gráfico sem título'}
                        </h4>
                        <div style="font-size: 12px; color: var(--text-secondary);">
                            <span style="background: var(--surface-hover); padding: 4px 8px; border-radius: 4px; margin-right: 8px;">
                                Tipo: ${grafico.tipo || 'bar'}
                            </span>
                            <span style="background: var(--surface-hover); padding: 4px 8px; border-radius: 4px; margin-right: 8px;">
                                Campo: ${grafico.campo || 'N/A'}
                            </span>
                            ${grafico.campos_agrupar && grafico.campos_agrupar.length > 0 ? 
                                `<span style="background: var(--surface-hover); padding: 4px 8px; border-radius: 4px;">
                                    Agrupar: ${grafico.campos_agrupar.join(', ')}
                                </span>` : 
                                (grafico.agrupar_por ? 
                                    `<span style="background: var(--surface-hover); padding: 4px 8px; border-radius: 4px;">
                                        Agrupar: ${grafico.agrupar_por}
                                    </span>` : '')
                            }
                        </div>
                    </div>
                    <div style="display: flex; gap: 8px;">
                        <button type="button" onclick="editarGrafico(${index})" class="btn btn-secondary" style="padding: 6px 12px; font-size: 12px;">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button type="button" onclick="removerGrafico(${index})" class="btn btn-secondary" style="padding: 6px 12px; font-size: 12px; background: #dc3545;">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
                ${grafico.descricao ? `<p style="font-size: 13px; color: var(--text-secondary); margin: 0;">${grafico.descricao}</p>` : ''}
            </div>
        `;
    }).join('');
}

let camposAgruparCount = 0; // Contador para campos de agrupar

function adicionarCampoAgrupar(campoSelecionado = '') {
    camposAgruparCount++;
    const container = document.getElementById('camposAgruparContainer');
    if (!container) return;
    
    const todosCampos = [...CAMPOS_SISTEMA, ...camposPersonalizados];
    const camposOptions = todosCampos.map(c => 
        `<option value="${c.value}" ${campoSelecionado === c.value ? 'selected' : ''}>${c.label}</option>`
    ).join('');
    
    const campoDiv = document.createElement('div');
    campoDiv.id = `campoAgrupar_${camposAgruparCount}`;
    campoDiv.style.display = 'flex';
    campoDiv.style.gap = '8px';
    campoDiv.style.alignItems = 'center';
    campoDiv.innerHTML = `
        <select class="form-input campo-agrupar-select" style="flex: 1;">
            <option value="">-- Selecione um campo --</option>
            ${camposOptions}
        </select>
        <button type="button" onclick="removerCampoAgrupar('campoAgrupar_${camposAgruparCount}')" class="btn btn-secondary" style="padding: 8px 12px; background: #dc3545;">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    container.appendChild(campoDiv);
}

window.adicionarCampoAgrupar = adicionarCampoAgrupar;

function removerCampoAgrupar(id) {
    const campoDiv = document.getElementById(id);
    if (campoDiv) {
        campoDiv.remove();
    }
}

window.removerCampoAgrupar = removerCampoAgrupar;

function obterCamposAgrupar() {
    const selects = document.querySelectorAll('.campo-agrupar-select');
    const campos = [];
    selects.forEach(select => {
        if (select.value) {
            campos.push(select.value);
        }
    });
    return campos;
}

function abrirModalAdicionarGrafico(graficoIndex = null) {
    const grafico = graficoIndex !== null ? graficosConfigurados[graficoIndex] : null;
    
    // Busca campos disponíveis
    const todosCampos = [...CAMPOS_SISTEMA, ...camposPersonalizados];
    const camposOptions = todosCampos.map(c => 
        `<option value="${c.value}" ${grafico && grafico.campo === c.value ? 'selected' : ''}>${c.label}</option>`
    ).join('');
    
    // Cria modal se não existir
    let modal = document.getElementById('modalAdicionarGrafico');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'modalAdicionarGrafico';
        modal.className = 'modal';
        modal.style.display = 'none';
        modal.innerHTML = `
            <div class="modal-content" style="max-width: 700px;">
                <div class="modal-header">
                    <h2>${grafico ? 'Editar' : 'Adicionar'} Gráfico Personalizado</h2>
                    <button class="modal-close" onclick="fecharModalAdicionarGrafico()">&times;</button>
                </div>
                <div class="modal-body">
                    <form id="formAdicionarGrafico" onsubmit="salvarGraficoPersonalizado(event)">
                        <input type="hidden" id="graficoIndex" value="${graficoIndex !== null ? graficoIndex : ''}">
                        
                        <div class="form-group">
                            <label class="form-label">Título do Gráfico *</label>
                            <input type="text" id="graficoTitulo" class="form-input" required 
                                   placeholder="Ex: Top 10 CIDs mais Frequentes" 
                                   value="${grafico ? grafico.titulo : ''}">
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Descrição (opcional)</label>
                            <textarea id="graficoDescricao" class="form-input" rows="2" 
                                      placeholder="Descreva o que este gráfico mostra">${grafico ? (grafico.descricao || '') : ''}</textarea>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Tipo de Gráfico *</label>
                            <select id="graficoTipo" class="form-input" required>
                                <option value="bar" ${grafico && grafico.tipo === 'bar' ? 'selected' : ''}>Barra (Vertical)</option>
                                <option value="bar-horizontal" ${grafico && grafico.tipo === 'bar-horizontal' ? 'selected' : ''}>Barra (Horizontal)</option>
                                <option value="line" ${grafico && grafico.tipo === 'line' ? 'selected' : ''}>Linha</option>
                                <option value="pie" ${grafico && grafico.tipo === 'pie' ? 'selected' : ''}>Pizza</option>
                                <option value="doughnut" ${grafico && grafico.tipo === 'doughnut' ? 'selected' : ''}>Rosca</option>
                                <option value="area" ${grafico && grafico.tipo === 'area' ? 'selected' : ''}>Área</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Campo Principal (Medida) *</label>
                            <select id="graficoCampo" class="form-input" required>
                                <option value="">-- Selecione o campo principal --</option>
                                ${camposOptions}
                            </select>
                            <small style="color: var(--text-secondary); font-size: 12px;">
                                Campo que será medido/contado no gráfico (ex: CID, Setor, Dias Perdidos)
                            </small>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Campos para Agrupar/Filtrar (múltiplos)</label>
                            <div id="camposAgruparContainer" style="display: flex; flex-direction: column; gap: 8px;">
                                <!-- Será preenchido dinamicamente -->
                            </div>
                            <button type="button" onclick="adicionarCampoAgrupar()" class="btn btn-secondary" style="margin-top: 8px; padding: 8px 12px; font-size: 12px;">
                                <i class="fas fa-plus"></i> Adicionar Campo
                            </button>
                            <small style="color: var(--text-secondary); font-size: 12px; display: block; margin-top: 8px;">
                                Adicione campos para cruzar dados (ex: "CID por Setor" = CID principal + Setor para agrupar)
                            </small>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Ordenar Por</label>
                            <select id="graficoOrdenarPor" class="form-input">
                                <option value="quantidade" ${grafico && grafico.ordenar_por === 'quantidade' ? 'selected' : 'selected'}>Quantidade (maior para menor)</option>
                                <option value="nome" ${grafico && grafico.ordenar_por === 'nome' ? 'selected' : ''}>Nome (A-Z)</option>
                                <option value="valor" ${grafico && grafico.ordenar_por === 'valor' ? 'selected' : ''}>Valor (maior para menor)</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Limite de Itens (Top N)</label>
                            <input type="number" id="graficoLimite" class="form-input" min="1" max="50" 
                                   value="${grafico ? (grafico.limite || 10) : 10}">
                            <small style="color: var(--text-secondary); font-size: 12px;">
                                Mostra apenas os N primeiros itens (ex: Top 10)
                            </small>
                        </div>
                        
                        <div style="margin-top: 24px; padding-top: 24px; border-top: 2px solid var(--border);">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                                <h3 style="margin: 0; font-size: 16px; color: var(--text-primary);">
                                    <i class="fas fa-eye" style="margin-right: 8px;"></i>Preview do Gráfico
                                </h3>
                                <button type="button" onclick="gerarPreviewGrafico()" class="btn btn-secondary" style="padding: 8px 16px; font-size: 12px;">
                                    <i class="fas fa-sync"></i> Atualizar Preview
                                </button>
                            </div>
                            <div id="previewGraficoContainer" style="background: var(--surface-hover); border-radius: 8px; padding: 20px; min-height: 300px; display: flex; align-items: center; justify-content: center;">
                                <div style="text-align: center; color: var(--text-secondary);">
                                    <i class="fas fa-chart-bar" style="font-size: 48px; margin-bottom: 16px; opacity: 0.5;"></i>
                                    <p style="margin: 0; font-weight: 600; margin-bottom: 8px;">Preview do Gráfico</p>
                                    <p style="margin: 0; font-size: 13px;">Preencha os campos acima e clique em "Atualizar Preview" para visualizar</p>
                                    <p style="margin: 8px 0 0 0; font-size: 12px; color: #666;">
                                        <i class="fas fa-info-circle"></i> O preview usa dados reais do banco. Se não houver dados, o gráfico aparecerá vazio.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" onclick="fecharModalAdicionarGrafico()">Cancelar</button>
                    <button type="button" onclick="gerarPreviewGrafico(true)" class="btn btn-secondary" style="margin-right: 8px;">
                        <i class="fas fa-eye"></i> Ver Preview
                    </button>
                    <button type="submit" form="formAdicionarGrafico" class="btn btn-primary">
                        <i class="fas fa-save"></i> ${grafico ? 'Salvar Alterações' : 'Adicionar Gráfico'}
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    } else {
        // Atualiza campos disponíveis
        const selectCampo = document.getElementById('graficoCampo');
        if (selectCampo) {
            const todosCampos = [...CAMPOS_SISTEMA, ...camposPersonalizados];
            selectCampo.innerHTML = `
                <option value="">-- Selecione um campo --</option>
                ${todosCampos.map(c => 
                    `<option value="${c.value}" ${grafico && grafico.campo === c.value ? 'selected' : ''}>${c.label}</option>`
                ).join('')}
            `;
        }
        
        // Limpa campos de agrupar
        camposAgruparCount = 0;
        const containerAgrupar = document.getElementById('camposAgruparContainer');
        if (containerAgrupar) {
            containerAgrupar.innerHTML = '';
        }
        
        // Preenche formulário se for edição
        if (grafico) {
            document.getElementById('graficoIndex').value = graficoIndex;
            document.getElementById('graficoTitulo').value = grafico.titulo || '';
            document.getElementById('graficoDescricao').value = grafico.descricao || '';
            document.getElementById('graficoTipo').value = grafico.tipo || 'bar';
            document.getElementById('graficoCampo').value = grafico.campo || '';
            document.getElementById('graficoOrdenarPor').value = grafico.ordenar_por || 'quantidade';
            document.getElementById('graficoLimite').value = grafico.limite || 10;
            
            // Preenche campos de agrupar (suporta array ou string única para compatibilidade)
            const camposAgrupar = grafico.campos_agrupar || (grafico.agrupar_por ? [grafico.agrupar_por] : []);
            if (Array.isArray(camposAgrupar)) {
                camposAgrupar.forEach(campo => {
                    if (campo) {
                        adicionarCampoAgrupar(campo);
                    }
                });
            }
        } else {
            document.getElementById('graficoIndex').value = '';
            document.getElementById('formAdicionarGrafico').reset();
            document.getElementById('graficoLimite').value = 10;
            document.getElementById('graficoOrdenarPor').value = 'quantidade';
        }
        
        // Configura auto-preview
        setTimeout(() => {
            configurarAutoPreview();
        }, 200);
    }
    
    modal.style.display = 'flex';
}

window.abrirModalAdicionarGrafico = abrirModalAdicionarGrafico;

function fecharModalAdicionarGrafico() {
    const modal = document.getElementById('modalAdicionarGrafico');
    if (modal) {
        modal.style.display = 'none';
    }
    
    // Destrói gráfico de preview
    if (previewGraficoInstance) {
        previewGraficoInstance.destroy();
        previewGraficoInstance = null;
    }
}

window.fecharModalAdicionarGrafico = fecharModalAdicionarGrafico;

function salvarGraficoPersonalizado(event) {
    event.preventDefault();
    
    const index = document.getElementById('graficoIndex').value;
    const titulo = document.getElementById('graficoTitulo').value.trim();
    const descricao = document.getElementById('graficoDescricao').value.trim();
    const tipo = document.getElementById('graficoTipo').value;
    const campo = document.getElementById('graficoCampo').value;
    const camposAgrupar = obterCamposAgrupar(); // Array de campos para agrupar
    const ordenarPor = document.getElementById('graficoOrdenarPor').value;
    const limite = parseInt(document.getElementById('graficoLimite').value) || 10;
    
    if (!titulo || !tipo || !campo) {
        alert('Preencha todos os campos obrigatórios');
        return;
    }
    
    const novoGrafico = {
        titulo,
        descricao,
        tipo,
        campo,
        campos_agrupar: camposAgrupar, // Array de campos para agrupar
        ordenar_por: ordenarPor || 'quantidade',
        limite: limite || 10
    };
    
    if (index !== '' && index !== null) {
        // Edita gráfico existente
        graficosConfigurados[parseInt(index)] = novoGrafico;
        mostrarMensagemMapeamento(`Gráfico "${titulo}" atualizado com sucesso!`, 'sucesso');
    } else {
        // Adiciona novo gráfico
        graficosConfigurados.push(novoGrafico);
        mostrarMensagemMapeamento(`Gráfico "${titulo}" adicionado com sucesso!`, 'sucesso');
    }
    
    renderizarGraficosConfigurados();
    fecharModalAdicionarGrafico();
}

window.salvarGraficoPersonalizado = salvarGraficoPersonalizado;

function editarGrafico(index) {
    abrirModalAdicionarGrafico(index);
}

window.editarGrafico = editarGrafico;

function removerGrafico(index) {
    if (!confirm('Deseja remover este gráfico?')) {
        return;
    }
    
    graficosConfigurados.splice(index, 1);
    renderizarGraficosConfigurados();
    mostrarMensagemMapeamento('Gráfico removido com sucesso!', 'sucesso');
}

window.removerGrafico = removerGrafico;

// ==================== PREVIEW DO GRÁFICO ====================

let previewGraficoInstance = null; // Instância do gráfico de preview

async function gerarPreviewGrafico(salvarAposPreview = false) {
    console.log('🔍 Iniciando geração de preview...');
    
    const titulo = document.getElementById('graficoTitulo')?.value.trim();
    const tipo = document.getElementById('graficoTipo')?.value;
    const campo = document.getElementById('graficoCampo')?.value;
    const limite = parseInt(document.getElementById('graficoLimite')?.value) || 10;
    const ordenarPor = document.getElementById('graficoOrdenarPor')?.value || 'quantidade';
    
    console.log('📋 Dados do formulário:', { titulo, tipo, campo, limite, ordenarPor });
    
    if (!campo) {
        alert('Selecione o campo principal para gerar o preview');
        return;
    }
    
    if (!clienteMapeamentoId) {
        alert('Cliente não identificado. Por favor, feche e abra novamente o modal de configuração.');
        console.error('❌ clienteMapeamentoId não definido');
        return;
    }
    
    console.log('✅ Cliente ID:', clienteMapeamentoId);
    
    const camposAgrupar = obterCamposAgrupar();
    console.log('📊 Campos para agrupar:', camposAgrupar);
    
    const config = {
        titulo: titulo || 'Preview do Gráfico',
        tipo: tipo || 'bar',
        campo: campo,
        campos_agrupar: camposAgrupar,
        ordenar_por: ordenarPor,
        limite: limite
    };
    
    console.log('⚙️ Configuração do gráfico:', config);
    
    const container = document.getElementById('previewGraficoContainer');
    if (!container) return;
    
    // Mostra loading
    container.innerHTML = `
        <div style="text-align: center; color: var(--text-secondary);">
            <i class="fas fa-spinner fa-spin" style="font-size: 32px; margin-bottom: 16px;"></i>
            <p style="margin: 0;">Gerando preview...</p>
        </div>
    `;
    
    try {
        console.log('🌐 Enviando requisição para gerar dados...');
        // Gera dados do gráfico
        const response = await fetch(`/api/clientes/${clienteMapeamentoId}/graficos/gerar-dados`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ config })
        });
        
        console.log('📡 Resposta recebida:', response.status, response.statusText);
        
        if (!response.ok) {
            let errorData;
            try {
                errorData = await response.json();
            } catch (e) {
                errorData = { detail: `Erro ${response.status}: ${response.statusText}` };
            }
            console.error('❌ Erro na resposta:', errorData);
            throw new Error(errorData.detail || `Erro ${response.status} ao gerar preview`);
        }
        
        const data = await response.json();
        console.log('📦 Dados recebidos:', data);
        
        if (!data.success) {
            container.innerHTML = `
                <div style="text-align: center; color: var(--text-secondary);">
                    <i class="fas fa-exclamation-triangle" style="font-size: 32px; margin-bottom: 16px; color: #f9a825;"></i>
                    <p style="margin: 0; font-weight: 600;">Erro ao processar dados</p>
                    <p style="margin: 8px 0 0 0; font-size: 13px;">${data.detail || 'Erro desconhecido'}</p>
                </div>
            `;
            return;
        }
        
        if (!data.labels || data.labels.length === 0) {
            console.warn('⚠️ Nenhum dado encontrado');
            let mensagemDetalhada = 'Não há registros com os critérios selecionados.';
            
            if (data.message) {
                mensagemDetalhada = data.message;
            } else {
                mensagemDetalhada = `O campo "${campo}" não possui dados no banco para este cliente.`;
                if (camposAgrupar.length > 0) {
                    mensagemDetalhada += ` Campos de agrupar: ${camposAgrupar.join(', ')}.`;
                }
            }
            
            container.innerHTML = `
                <div style="text-align: center; color: var(--text-secondary);">
                    <i class="fas fa-exclamation-triangle" style="font-size: 32px; margin-bottom: 16px; color: #f9a825;"></i>
                    <p style="margin: 0; font-weight: 600;">Nenhum dado encontrado</p>
                    <p style="margin: 8px 0 0 0; font-size: 13px;">${mensagemDetalhada}</p>
                    <div style="margin-top: 16px; padding: 12px; background: #fff3cd; border-radius: 6px; text-align: left; font-size: 12px;">
                        <p style="margin: 0 0 8px 0; font-weight: 600; color: #856404;">💡 Dicas:</p>
                        <ul style="margin: 0; padding-left: 20px; color: #856404;">
                            <li>Verifique se o campo "${campo}" está mapeado corretamente nas colunas da planilha</li>
                            <li>Confirme se você já fez upload de planilhas com dados para este cliente</li>
                            <li>Tente usar outro campo que você sabe que tem dados (ex: setor, cid)</li>
                            <li>Verifique o mapeamento de colunas no Passo 2</li>
                        </ul>
                    </div>
                    <p style="margin: 12px 0 0 0; font-size: 11px; color: #666;">
                        Campo: ${campo} | Cliente ID: ${clienteMapeamentoId}
                    </p>
                </div>
            `;
            return;
        }
        
        console.log('✅ Dados válidos recebidos:', data.labels.length, 'itens');
        
        // Cria canvas para o gráfico
        container.innerHTML = `
            <div style="width: 100%;">
                <h4 style="margin: 0 0 16px 0; color: var(--text-primary); font-size: 14px; font-weight: 600;">
                    ${config.titulo}
                </h4>
                <div style="position: relative; height: 300px;">
                    <canvas id="canvasPreviewGrafico"></canvas>
                </div>
                <div style="margin-top: 12px; font-size: 12px; color: var(--text-secondary); text-align: center;">
                    <span>Total de itens: ${data.labels.length}</span>
                </div>
            </div>
        `;
        
        // Aguarda um pouco para o DOM atualizar
        await new Promise(resolve => setTimeout(resolve, 100));
        
        const canvas = document.getElementById('canvasPreviewGrafico');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        // Destrói gráfico anterior se existir
        if (previewGraficoInstance) {
            previewGraficoInstance.destroy();
        }
        
        // Carrega cores do cliente se disponível
        let cores = {
            primary: '#1a237e',
            secondary: '#556B2F'
        };
        let paleta = ['#1a237e', '#556B2F', '#0d47a1', '#6B8E23', '#3949ab', '#808000'];
        
        try {
            if (typeof getCoresCliente === 'function') {
                cores = getCoresCliente();
            }
            if (typeof getPaletaCliente === 'function') {
                paleta = getPaletaCliente();
            }
        } catch (e) {
            console.warn('Erro ao carregar cores do cliente, usando padrão:', e);
        }
        
        // Verifica se Chart está disponível
        if (typeof Chart === 'undefined') {
            throw new Error('Chart.js não está carregado. Por favor, recarregue a página.');
        }
        
        // Decide qual dado usar (valores numéricos ou quantidades)
        // Se o campo principal for numérico OU houver campos numéricos para agrupar, usa valores
        const camposNumericos = ['dias_atestados', 'horas_perdi', 'numero_dias_atestado', 'horas_perdidas', 'dias_perdidos'];
        const temCampoNumerico = camposNumericos.includes(config.campo) || 
                                 config.campos_agrupar.some(c => camposNumericos.includes(c));
        const dadosParaGrafico = temCampoNumerico && data.valores && data.valores.length > 0 ? data.valores : data.quantidades;
        
        console.log('📊 Dados para gráfico:', {
            temCampoNumerico,
            usaValores: temCampoNumerico,
            valores: data.valores,
            quantidades: data.quantidades,
            dadosFinais: dadosParaGrafico
        });
        
        // Configuração base do gráfico
        const chartConfig = {
            data: {
                labels: data.labels,
                datasets: [{
                    label: config.titulo,
                    data: dadosParaGrafico,
                    backgroundColor: paleta.slice(0, data.labels.length),
                    borderColor: cores.primary,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: config.tipo === 'pie' || config.tipo === 'doughnut',
                        position: 'bottom'
                    },
                    tooltip: {
                        enabled: true
                    },
                    title: {
                        display: false
                    }
                }
            }
        };
        
        // Ajusta configuração baseado no tipo
        if (config.tipo === 'bar-horizontal') {
            chartConfig.type = 'bar';
            chartConfig.options.indexAxis = 'y';
        } else if (config.tipo === 'line') {
            chartConfig.type = 'line';
            chartConfig.data.datasets[0].fill = false;
            chartConfig.data.datasets[0].tension = 0.4;
        } else if (config.tipo === 'pie') {
            chartConfig.type = 'pie';
        } else if (config.tipo === 'doughnut') {
            chartConfig.type = 'doughnut';
        } else if (config.tipo === 'area') {
            chartConfig.type = 'line';
            chartConfig.data.datasets[0].fill = true;
        } else {
            chartConfig.type = 'bar';
        }
        
        // Cria instância do gráfico
        try {
            console.log('🎨 Criando gráfico Chart.js...');
            previewGraficoInstance = new Chart(ctx, chartConfig);
            console.log('✅ Gráfico criado com sucesso!');
        } catch (error) {
            console.error('❌ Erro ao criar gráfico:', error);
            throw new Error('Erro ao renderizar gráfico: ' + error.message);
        }
        
        // Se for para salvar após preview, salva automaticamente
        if (salvarAposPreview) {
            // Não salva automaticamente, apenas mostra o preview
            // O usuário precisa clicar em "Adicionar Gráfico" para salvar
        }
        
    } catch (error) {
        console.error('Erro ao gerar preview:', error);
        let mensagemErro = error.message || 'Erro desconhecido';
        
        // Mensagens mais amigáveis
        if (mensagemErro.includes('Chart.js')) {
            mensagemErro = 'Chart.js não está carregado. Por favor, recarregue a página.';
        } else if (mensagemErro.includes('fetch')) {
            mensagemErro = 'Erro ao conectar com o servidor. Verifique sua conexão.';
        } else if (mensagemErro.includes('404')) {
            mensagemErro = 'Endpoint não encontrado. Verifique se o servidor está rodando.';
        } else if (mensagemErro.includes('500')) {
            mensagemErro = 'Erro no servidor ao processar os dados. Verifique os campos selecionados.';
        }
        
        container.innerHTML = `
            <div style="text-align: center; color: #d32f2f;">
                <i class="fas fa-exclamation-circle" style="font-size: 32px; margin-bottom: 16px;"></i>
                <p style="margin: 0; font-weight: 600;">Erro ao gerar preview</p>
                <p style="margin: 8px 0 0 0; font-size: 13px;">${mensagemErro}</p>
                <p style="margin: 12px 0 0 0; font-size: 11px; color: #666;">
                    Detalhes técnicos: ${error.message}
                </p>
            </div>
        `;
    }
}

window.gerarPreviewGrafico = gerarPreviewGrafico;

// Atualiza preview automaticamente quando campos mudam
function configurarAutoPreview() {
    const campos = ['graficoTitulo', 'graficoTipo', 'graficoCampo', 'graficoLimite', 'graficoOrdenarPor'];
    campos.forEach(campoId => {
        const campo = document.getElementById(campoId);
        if (campo) {
            campo.addEventListener('change', () => {
                // Debounce: aguarda 500ms após a última mudança
                clearTimeout(window.previewTimeout);
                window.previewTimeout = setTimeout(() => {
                    if (document.getElementById('graficoCampo')?.value) {
                        gerarPreviewGrafico();
                    }
                }, 500);
            });
        }
    });
    
    // Observa mudanças nos selects de agrupar
    const observer = new MutationObserver(() => {
        clearTimeout(window.previewTimeout);
        window.previewTimeout = setTimeout(() => {
            if (document.getElementById('graficoCampo')?.value) {
                gerarPreviewGrafico();
            }
        }, 500);
    });
    
    const containerAgrupar = document.getElementById('camposAgruparContainer');
    if (containerAgrupar) {
        observer.observe(containerAgrupar, { childList: true, subtree: true });
    }
}

function mostrarMensagemMapeamento(mensagem, tipo) {
    // Remove mensagens anteriores
    const mensagensExistentes = document.querySelectorAll('.mensagem-mapeamento');
    mensagensExistentes.forEach(msg => msg.remove());
    
    const cores = {
        sucesso: { bg: '#e8f5e9', border: '#4caf50', icon: 'fa-check-circle', cor: '#2e7d32' },
        erro: { bg: '#ffebee', border: '#f44336', icon: 'fa-exclamation-circle', cor: '#c62828' },
        info: { bg: '#e3f2fd', border: '#2196f3', icon: 'fa-info-circle', cor: '#1565c0' }
    };
    
    const cor = cores[tipo] || cores.info;
    
    const mensagemDiv = document.createElement('div');
    mensagemDiv.className = 'mensagem-mapeamento';
    mensagemDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${cor.bg};
        border: 2px solid ${cor.border};
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
        <i class="fas ${cor.icon}" style="font-size: 24px; color: ${cor.cor};"></i>
        <div style="flex: 1; color: ${cor.cor}; font-size: 14px; line-height: 1.4;">${mensagem}</div>
    `;
    
    document.body.appendChild(mensagemDiv);
    
    // Remove após 5 segundos
    setTimeout(() => {
        mensagemDiv.remove();
    }, 5000);
}

