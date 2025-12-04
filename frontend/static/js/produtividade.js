/**
 * Produtividade - JavaScript
 * Sistema com Modal para Consolidado Mensal
 */

let allData = [];
let registroEditando = null; // ID do registro sendo editado

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    const clientId = getCurrentClientId();
    if (!clientId) {
        showError('Selecione um cliente na aba "Clientes" para visualizar os dados.');
        renderEmptyTable();
        return;
    }
    
    inicializarAnos();
    carregarDados();
});

function inicializarAnos() {
    const select = document.getElementById('modalAno');
    if (!select) return;
    
    const anoAtual = new Date().getFullYear();
    
    // Limpa opções existentes (exceto "Selecione o ano")
    while (select.children.length > 1) {
        select.removeChild(select.lastChild);
    }
    
    // Adiciona os anos
    for (let ano = anoAtual; ano >= 2020; ano--) {
        const option = document.createElement('option');
        option.value = ano;
        option.textContent = ano;
        select.appendChild(option);
    }
}

function getCurrentClientId() {
    const clienteLocalStorage = localStorage.getItem('cliente_selecionado');
    if (clienteLocalStorage) {
        return parseInt(clienteLocalStorage);
    }
    
    if (typeof window.getCurrentClientId === 'function' && window.getCurrentClientId !== getCurrentClientId) {
        try {
            const clientId = window.getCurrentClientId(null);
            if (clientId) return clientId;
        } catch (e) {
            console.warn('Erro ao chamar getCurrentClientId global:', e);
        }
    }
    
    return 1;
}

// Carregar dados do backend
async function carregarDados() {
    try {
        const clientId = getCurrentClientId();
        if (!clientId) {
            showError('Selecione um cliente primeiro.');
            return;
        }
        
        const response = await fetch(`/api/produtividade?client_id=${clientId}`);
        if (!response.ok) {
            throw new Error(`Erro ${response.status}: ${await response.text()}`);
        }
        
        const responseData = await response.json();
        console.log('Dados recebidos da API:', responseData);
        
        // A API retorna {success: true, data: [...]} ou pode retornar array direto
        let data = responseData;
        if (responseData && responseData.data) {
            data = responseData.data;
        } else if (responseData && Array.isArray(responseData)) {
            data = responseData;
        }
        
        // Garante que allData seja sempre um array
        allData = Array.isArray(data) ? data : [];
        
        console.log('allData após processamento:', allData);
        console.log('Quantidade de registros:', allData.length);
        
        renderTable();
    } catch (error) {
        console.error('Erro ao carregar dados:', error);
        showError('Erro ao carregar dados: ' + error.message);
    }
}

// Renderizar tabela de registros salvos
function renderTable() {
    const tableBodySalvos = document.getElementById('tableBodySalvos');
    if (!tableBodySalvos) {
        console.error('tableBodySalvos não encontrado!');
        return;
    }
    
    // Garante que allData seja sempre um array
    if (!Array.isArray(allData)) {
        allData = [];
    }
    
    console.log('renderTable - allData:', allData);
    console.log('renderTable - quantidade:', allData.length);
    
    const contador = document.getElementById('contadorRegistros');
    if (contador) {
        contador.textContent = `(${allData.length} registro${allData.length !== 1 ? 's' : ''})`;
    }
    
    if (allData.length === 0) {
        tableBodySalvos.innerHTML = `
            <tr>
                <td colspan="18" style="text-align: center; padding: 40px; color: #6c757d;">
                    Nenhum registro salvo ainda
                </td>
            </tr>
        `;
        return;
    }
    
    // Agrupa por mês
    const dadosPorMes = {};
    allData.forEach(d => {
        const mesRef = d.mes_referencia || 'sem-mes';
        if (!dadosPorMes[mesRef]) {
            dadosPorMes[mesRef] = [];
        }
        dadosPorMes[mesRef].push(d);
    });
    
    let html = '';
    
    console.log('dadosPorMes:', dadosPorMes);
    
    Object.keys(dadosPorMes).sort().reverse().forEach(mesRef => {
        const dadosMes = dadosPorMes[mesRef];
        console.log(`Processando mês ${mesRef}:`, dadosMes);
        
        // Busca registros de "Agendados" e "Compareceram"
        const agendados = dadosMes.find(d => d.tipo_consulta === 'Agendados');
        const compareceram = dadosMes.find(d => d.tipo_consulta === 'Compareceram');
        
        console.log(`Agendados encontrados:`, agendados);
        console.log(`Compareceram encontrados:`, compareceram);
        
        if (!agendados || !compareceram) {
            console.warn(`Registro incompleto para ${mesRef} - pulando`);
            return;
        }
        
        // Calcula faltas para cada campo
        const calcularFaltas = (agendado, compareceu) => Math.max(0, (agendado || 0) - (compareceu || 0));
        
        const faltas = {
            ocupacionais: calcularFaltas(agendados.ocupacionais, compareceram.ocupacionais),
            assistenciais: calcularFaltas(agendados.assistenciais, compareceram.assistenciais),
            acidente_trabalho: calcularFaltas(agendados.acidente_trabalho, compareceram.acidente_trabalho),
            inss: calcularFaltas(agendados.inss, compareceram.inss),
            sinistralidade: calcularFaltas(agendados.sinistralidade, compareceram.sinistralidade),
            absenteismo: calcularFaltas(agendados.absenteismo, compareceram.absenteismo),
            pericia_indireta: calcularFaltas(agendados.pericia_indireta, compareceram.pericia_indireta)
        };
        
        // Calcula totais
        const totalAgendados = (agendados.ocupacionais || 0) + 
                               (agendados.assistenciais || 0) + 
                               (agendados.acidente_trabalho || 0) + 
                               (agendados.inss || 0) + 
                               (agendados.sinistralidade || 0) + 
                               (agendados.absenteismo || 0) + 
                               (agendados.pericia_indireta || 0);
        
        const totalFaltas = faltas.ocupacionais + 
                           faltas.assistenciais + 
                           faltas.acidente_trabalho + 
                           faltas.inss + 
                           faltas.sinistralidade + 
                           faltas.absenteismo + 
                           faltas.pericia_indireta;
        
        const percentualFaltas = totalAgendados > 0 ? Math.round((totalFaltas / totalAgendados) * 100) : 0;
        
        html += `
            <tr data-mes="${mesRef}">
                <td style="font-weight: 600; font-size: 12px;">${mesRef}</td>
                <td style="text-align: right; font-size: 12px;">${agendados.ocupacionais || 0}</td>
                <td style="text-align: right; color: #dc3545; font-weight: 600; font-size: 12px;">${faltas.ocupacionais}</td>
                <td style="text-align: right; font-size: 12px;">${agendados.assistenciais || 0}</td>
                <td style="text-align: right; color: #dc3545; font-weight: 600; font-size: 12px;">${faltas.assistenciais}</td>
                <td style="text-align: right; font-size: 12px;">${agendados.acidente_trabalho || 0}</td>
                <td style="text-align: right; color: #dc3545; font-weight: 600; font-size: 12px;">${faltas.acidente_trabalho}</td>
                <td style="text-align: right; font-size: 12px;">${agendados.inss || 0}</td>
                <td style="text-align: right; color: #dc3545; font-weight: 600; font-size: 12px;">${faltas.inss}</td>
                <td style="text-align: right; font-size: 12px;">${agendados.sinistralidade || 0}</td>
                <td style="text-align: right; color: #dc3545; font-weight: 600; font-size: 12px;">${faltas.sinistralidade}</td>
                <td style="text-align: right; font-size: 12px;">${agendados.absenteismo || 0}</td>
                <td style="text-align: right; color: #dc3545; font-weight: 600; font-size: 12px;">${faltas.absenteismo}</td>
                <td style="text-align: right; font-size: 12px;">${agendados.pericia_indireta || 0}</td>
                <td style="text-align: right; color: #dc3545; font-weight: 600; font-size: 12px;">${faltas.pericia_indireta}</td>
                <td style="text-align: right; font-weight: 700; color: #00bcf2; font-size: 12px;">${totalAgendados}</td>
                <td style="text-align: right; font-weight: 700; color: #dc3545; font-size: 12px;">${totalFaltas}</td>
                <td style="text-align: right; font-weight: 700; color: #dc3545; font-size: 12px;">${percentualFaltas}%</td>
                <td>
                    <div style="display: flex; gap: 6px; justify-content: center;">
                        <button class="btn btn-warning" style="padding: 6px 12px; font-size: 11px; min-width: 60px;" 
                                onclick="editarRegistroModal('${mesRef}')" title="Editar">
                            <i class="fas fa-edit"></i> Editar
                        </button>
                        <button class="btn btn-danger" style="padding: 6px 12px; font-size: 11px; min-width: 60px;" 
                                onclick="excluirRegistroModal('${mesRef}')" title="Excluir">
                            <i class="fas fa-trash"></i> Excluir
                        </button>
                    </div>
                </td>
            </tr>
        `;
    });
    
    console.log('HTML gerado:', html);
    console.log('Quantidade de linhas HTML:', (html.match(/<tr/g) || []).length);
    
    tableBodySalvos.innerHTML = html;
    
    console.log('Tabela renderizada com sucesso!');
}

function renderEmptyTable() {
    const tableBodySalvos = document.getElementById('tableBodySalvos');
    if (tableBodySalvos) {
        tableBodySalvos.innerHTML = `
            <tr>
                <td colspan="16" style="text-align: center; padding: 40px; color: #6c757d;">
                    Nenhum registro salvo ainda
                </td>
            </tr>
        `;
    }
}

function showError(message) {
    const tableBodySalvos = document.getElementById('tableBodySalvos');
    if (tableBodySalvos) {
        tableBodySalvos.innerHTML = `
            <tr>
                <td colspan="18" style="text-align: center; padding: 40px; color: #dc3545;">
                    ${message}
                </td>
            </tr>
        `;
    }
}

// Abrir modal (novo registro)
function abrirModal() {
    registroEditando = null;
    limparModal();
    
    const modal = document.getElementById('modalProdutividade');
    if (modal) {
        modal.classList.add('show');
        
        // Esconde botões de editar/excluir quando é novo registro
        document.getElementById('btnEditar').style.display = 'none';
        document.getElementById('btnExcluir').style.display = 'none';
        document.getElementById('btnSalvar').style.display = 'inline-block';
    }
}

// Fechar modal
function fecharModal() {
    const modal = document.getElementById('modalProdutividade');
    if (modal) {
        modal.classList.remove('show');
    }
    registroEditando = null;
    limparModal();
}

// Limpar campos do modal
function limparModal() {
    document.getElementById('modalAno').value = '';
    document.getElementById('modalMes').value = '';
    
    // Limpa todos os inputs
    ['agendados', 'compareceram'].forEach(tipo => {
        ['ocupacionais', 'assistenciais', 'acidente_trabalho', 'inss', 'sinistralidade', 'absenteismo', 'pericia_indireta'].forEach(campo => {
            const input = document.getElementById(`${tipo}_${campo}`);
            if (input) input.value = '';
        });
    });
    
    calcularConsolidado();
}

// Calcular faltas e percentuais
function calcularConsolidado() {
    const campos = ['ocupacionais', 'assistenciais', 'acidente_trabalho', 'inss', 'sinistralidade', 'absenteismo', 'pericia_indireta'];
    
    let totalAgendados = 0;
    let totalCompareceram = 0;
    let totalFaltas = 0;
    
    campos.forEach(campo => {
        const agendados = parseInt(document.getElementById(`agendados_${campo}`).value) || 0;
        const compareceram = parseInt(document.getElementById(`compareceram_${campo}`).value) || 0;
        const faltas = Math.max(0, agendados - compareceram);
        
        // Atualiza faltas
        const inputFaltas = document.getElementById(`faltas_${campo}`);
        if (inputFaltas) {
            inputFaltas.value = faltas;
        }
        
        // Calcula percentual
        const percentual = agendados > 0 ? Math.round((faltas / agendados) * 100) : 0;
        const percentualCell = document.getElementById(`percentual_${campo}`);
        if (percentualCell) {
            percentualCell.textContent = `${percentual}%`;
        }
        
        totalAgendados += agendados;
        totalCompareceram += compareceram;
        totalFaltas += faltas;
    });
    
    // Atualiza totais
    document.getElementById('total_agendados').textContent = totalAgendados;
    document.getElementById('total_compareceram').textContent = totalCompareceram;
    document.getElementById('total_faltas').textContent = totalFaltas;
    
    // Percentual total
    const percentualTotal = totalAgendados > 0 ? Math.round((totalFaltas / totalAgendados) * 100) : 0;
    document.getElementById('percentual_total').textContent = `${percentualTotal}%`;
}

// Salvar registro
async function salvarRegistro() {
    try {
        const ano = document.getElementById('modalAno').value;
        const mes = document.getElementById('modalMes').value;
        
        if (!ano || !mes) {
            alert('Por favor, selecione o ano e mês.');
            return;
        }
        
        const mesRef = `${ano}-${mes}`;
        const clientId = getCurrentClientId();
        
        if (!clientId) {
            alert('Selecione um cliente primeiro.');
            return;
        }
        
        // Coleta dados de Agendados e Compareceram
        const agendados = {
            ocupacionais: parseInt(document.getElementById('agendados_ocupacionais').value) || 0,
            assistenciais: parseInt(document.getElementById('agendados_assistenciais').value) || 0,
            acidente_trabalho: parseInt(document.getElementById('agendados_acidente_trabalho').value) || 0,
            inss: parseInt(document.getElementById('agendados_inss').value) || 0,
            sinistralidade: parseInt(document.getElementById('agendados_sinistralidade').value) || 0,
            absenteismo: parseInt(document.getElementById('agendados_absenteismo').value) || 0,
            pericia_indireta: parseInt(document.getElementById('agendados_pericia_indireta').value) || 0
        };
        
        const compareceram = {
            ocupacionais: parseInt(document.getElementById('compareceram_ocupacionais').value) || 0,
            assistenciais: parseInt(document.getElementById('compareceram_assistenciais').value) || 0,
            acidente_trabalho: parseInt(document.getElementById('compareceram_acidente_trabalho').value) || 0,
            inss: parseInt(document.getElementById('compareceram_inss').value) || 0,
            sinistralidade: parseInt(document.getElementById('compareceram_sinistralidade').value) || 0,
            absenteismo: parseInt(document.getElementById('compareceram_absenteismo').value) || 0,
            pericia_indireta: parseInt(document.getElementById('compareceram_pericia_indireta').value) || 0
        };
        
        if (registroEditando) {
            // Atualizar registro existente
            // Busca os IDs dos registros de Agendados e Compareceram
            if (!Array.isArray(allData)) {
                allData = [];
            }
            const dadosMes = allData.filter(d => d.mes_referencia === mesRef);
            const agendadosReg = dadosMes.find(d => d.tipo_consulta === 'Agendados');
            const compareceramReg = dadosMes.find(d => d.tipo_consulta === 'Compareceram');
            
            if (agendadosReg && agendadosReg.id) {
                const response = await fetch(`/api/produtividade/${agendadosReg.id}?client_id=${clientId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        numero_tipo: agendadosReg.numero_tipo || '',
                        tipo_consulta: 'Agendados',
                        ...agendados
                    })
                });
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Erro ao atualizar registro de Agendados');
                }
            }
            
            if (compareceramReg && compareceramReg.id) {
                const response = await fetch(`/api/produtividade/${compareceramReg.id}?client_id=${clientId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        numero_tipo: compareceramReg.numero_tipo || '',
                        tipo_consulta: 'Compareceram',
                        ...compareceram
                    })
                });
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Erro ao atualizar registro de Compareceram');
                }
            }
        } else {
            // Criar novo registro
        const response = await fetch('/api/produtividade', {
            method: 'POST',
                headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                client_id: clientId,
                mes_referencia: mesRef,
                    registros: [
                        {
                            numero_tipo: '',
                            tipo_consulta: 'Agendados',
                            ...agendados
                        },
                        {
                            numero_tipo: '',
                            tipo_consulta: 'Compareceram',
                            ...compareceram
                        }
                    ]
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
                throw new Error(errorData.detail || 'Erro ao salvar registro');
            }
        }
        
        // Recarrega os dados do servidor
        await carregarDados();
        
        // Fecha o modal
        fecharModal();
        
        // Mostra mensagem de sucesso
        alert('Registro salvo com sucesso!');
    } catch (error) {
        console.error('Erro ao salvar:', error);
        alert('Erro ao salvar registro: ' + error.message);
    }
}

// Editar registro (abre modal com dados)
function editarRegistroModal(mesRef) {
    if (!Array.isArray(allData)) {
        allData = [];
    }
    const dadosMes = allData.filter(d => d.mes_referencia === mesRef);
    const agendados = dadosMes.find(d => d.tipo_consulta === 'Agendados');
    const compareceram = dadosMes.find(d => d.tipo_consulta === 'Compareceram');
    
    if (!agendados || !compareceram) {
        alert('Registro não encontrado.');
        return;
    }
    
    registroEditando = mesRef;
    
    // Preenche ano e mês
    const [ano, mes] = mesRef.split('-');
    document.getElementById('modalAno').value = ano;
    document.getElementById('modalMes').value = mes;
    
    // Preenche dados de Agendados
    document.getElementById('agendados_ocupacionais').value = agendados.ocupacionais || 0;
    document.getElementById('agendados_assistenciais').value = agendados.assistenciais || 0;
    document.getElementById('agendados_acidente_trabalho').value = agendados.acidente_trabalho || 0;
    document.getElementById('agendados_inss').value = agendados.inss || 0;
    document.getElementById('agendados_sinistralidade').value = agendados.sinistralidade || 0;
    document.getElementById('agendados_absenteismo').value = agendados.absenteismo || 0;
    document.getElementById('agendados_pericia_indireta').value = agendados.pericia_indireta || 0;
    
    // Preenche dados de Compareceram
    document.getElementById('compareceram_ocupacionais').value = compareceram.ocupacionais || 0;
    document.getElementById('compareceram_assistenciais').value = compareceram.assistenciais || 0;
    document.getElementById('compareceram_acidente_trabalho').value = compareceram.acidente_trabalho || 0;
    document.getElementById('compareceram_inss').value = compareceram.inss || 0;
    document.getElementById('compareceram_sinistralidade').value = compareceram.sinistralidade || 0;
    document.getElementById('compareceram_absenteismo').value = compareceram.absenteismo || 0;
    document.getElementById('compareceram_pericia_indireta').value = compareceram.pericia_indireta || 0;
    
    // Calcula faltas e percentuais
    calcularConsolidado();
    
    // Abre modal
    const modal = document.getElementById('modalProdutividade');
    if (modal) {
        modal.classList.add('show');
        
        // Mostra botões de editar/excluir quando está editando
        document.getElementById('btnEditar').style.display = 'inline-block';
        document.getElementById('btnExcluir').style.display = 'inline-block';
        document.getElementById('btnSalvar').style.display = 'inline-block';
    }
}

// Excluir registro
async function excluirRegistro() {
    if (!registroEditando) {
        alert('Nenhum registro selecionado para excluir.');
        return;
    }
    
    if (!confirm('Deseja realmente excluir este registro?')) {
        return;
    }
    
    try {
        const clientId = getCurrentClientId();
        if (!clientId) {
            alert('Selecione um cliente primeiro.');
            return;
        }
        
        if (!Array.isArray(allData)) {
            allData = [];
        }
        const dadosMes = allData.filter(d => d.mes_referencia === registroEditando);
        
        // Exclui todos os registros do mês
        for (const reg of dadosMes) {
            if (reg.id) {
                const response = await fetch(`/api/produtividade/${reg.id}?client_id=${clientId}`, {
                    method: 'DELETE'
                });
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Erro ao excluir registro');
                }
            }
        }
        
        await carregarDados();
        fecharModal();
        alert('Registro excluído com sucesso!');
    } catch (error) {
        console.error('Erro ao excluir:', error);
        alert('Erro ao excluir registro: ' + error.message);
    }
}

// Excluir registro do modal (chamado do botão na lista)
async function excluirRegistroModal(mesRef) {
    if (!confirm('Deseja realmente excluir este registro?')) {
        return;
    }
    
    try {
        const clientId = getCurrentClientId();
        if (!clientId) {
            alert('Selecione um cliente primeiro.');
            return;
        }
        
        if (!Array.isArray(allData)) {
            allData = [];
        }
        const dadosMes = allData.filter(d => d.mes_referencia === mesRef);
        
        // Exclui todos os registros do mês
        for (const reg of dadosMes) {
            if (reg.id) {
                const response = await fetch(`/api/produtividade/${reg.id}?client_id=${clientId}`, {
                    method: 'DELETE'
                });
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Erro ao excluir registro');
                }
            }
        }
        
        await carregarDados();
        alert('Registro excluído com sucesso!');
    } catch (error) {
        console.error('Erro ao excluir:', error);
        alert('Erro ao excluir registro: ' + error.message);
    }
}

// Editar registro (chamado do botão no modal)
function editarRegistro() {
    // Já está em modo de edição, apenas salva
    salvarRegistro();
}

// Fechar modal ao clicar fora
window.onclick = function(event) {
    const modal = document.getElementById('modalProdutividade');
    if (event.target === modal) {
        fecharModal();
    }
}

// Exporta funções globais
window.abrirModal = abrirModal;
window.fecharModal = fecharModal;
window.calcularConsolidado = calcularConsolidado;
window.salvarRegistro = salvarRegistro;
window.editarRegistro = editarRegistro;
window.excluirRegistro = excluirRegistro;
window.excluirRegistroModal = excluirRegistroModal;
window.editarRegistroModal = editarRegistroModal;
window.carregarDados = carregarDados;
