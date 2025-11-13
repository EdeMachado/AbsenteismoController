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

// REMOVIDO: Função configurarGraficos removida - gráficos agora são programados diretamente no código

// Função global para abrir modal de mapeamento
window.configurarMapeamento = async function(clientId) {
    clienteMapeamentoId = clientId;
    passoAtual = 1;
    colunasPlanilha = [];
    mapeamentoAtual = {};
    planilhaExemploFile = null;
    camposPersonalizados = []; // Reseta campos personalizados
    
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


function mostrarPassoMapeamento(passo) {
    passoAtual = passo;
    
    // Oculta todos os passos
    document.getElementById('mapeamentoPasso1').style.display = passo === 1 ? 'block' : 'none';
    document.getElementById('mapeamentoPasso2').style.display = passo === 2 ? 'block' : 'none';
    document.getElementById('mapeamentoPasso3').style.display = passo === 3 ? 'block' : 'none';
    
    // Controla botões
    document.getElementById('btnVoltarMapeamento').style.display = passo > 1 ? 'inline-flex' : 'none';
    // Mostra "Avançar" apenas se houver planilha processada no passo 1, ou se estiver no passo 2 ou 3
    const temPlanilha = passo === 1 ? planilhaExemploFile !== null : true;
    document.getElementById('btnAvancarMapeamento').style.display = (passo < 3 && temPlanilha) ? 'inline-flex' : 'none';
    document.getElementById('btnSalvarMapeamento').style.display = passo === 3 ? 'inline-flex' : 'none';
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
    // Valida mapeamento
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
        
        
        mostrarMensagemMapeamento('Mapeamento salvo com sucesso! Agora você pode fazer upload de planilhas.', 'sucesso');
        
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
// REMOVIDO: Toda funcionalidade de gráficos personalizados foi removida
// Os gráficos agora são programados diretamente no código

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

// REMOVIDO: Toda funcionalidade de gráficos personalizados foi removida
// Os gráficos agora são programados diretamente no código

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

