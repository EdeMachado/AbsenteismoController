// ==================== VARIÁVEIS GLOBAIS ====================
let slides = [];
let slideAtual = 0;
let charts = {};

// Funções para obter cores do cliente (carregadas dinamicamente)
function getCoresApresentacao() {
    if (typeof getCoresCliente === 'function') {
        return getCoresCliente();
    }
    // Fallback para cores padrão
    return {
    primary: '#1a237e',
    primaryDark: '#0d47a1',
    primaryLight: '#3949ab',
    secondary: '#556B2F',
    secondaryDark: '#4a5d23',
    secondaryLight: '#6B8E23',
};
}

function getPaletaApresentacao() {
    if (typeof getPaletaCliente === 'function') {
        return getPaletaCliente();
    }
    // Fallback para paleta padrão
    return ['#1a237e', '#556B2F', '#3949ab', '#6B8E23', '#0d47a1', '#808000'];
}

// Mantém compatibilidade com código existente
const CORES_EMPRESA = new Proxy({}, {
    get: (target, prop) => {
        const cores = getCoresApresentacao();
        return cores[prop] || cores.primary;
    }
});

const PALETA_EMPRESA = new Proxy([], {
    get: (target, prop) => {
        const paleta = getPaletaApresentacao();
        if (prop === 'slice') {
            return (...args) => paleta.slice(...args);
        }
        if (prop === 'length') {
            return paleta.length;
        }
        if (typeof prop === 'string' && !isNaN(prop)) {
            return paleta[parseInt(prop)];
        }
        return paleta[prop];
    }
});

// ==================== INICIALIZAÇÃO ====================
document.addEventListener('DOMContentLoaded', () => {
    // Aguarda um pouco para garantir que auth.js e cores-cliente.js carregaram
    setTimeout(async () => {
        console.log('Inicializando apresentação...');
        // Carrega cores do cliente primeiro
        if (typeof carregarCoresCliente === 'function') {
            const clientId = typeof window.getCurrentClientId === 'function' ? window.getCurrentClientId(null) : null;
            if (clientId) {
                await carregarCoresCliente(clientId);
            }
        }
        carregarApresentacao();
        
        // Ajusta header para RODA DE OURO (preto-cinza)
        setTimeout(() => {
            const clientId = typeof window.getCurrentClientId === 'function' ? window.getCurrentClientId(null) : null;
            if (clientId === 4) {
                const header = document.querySelector('.apresentacao-header');
                if (header) {
                    header.style.background = 'linear-gradient(135deg, #000000, #808080)';
                }
            }
        }, 100);
    }, 500);
    
    // Navegação por teclado
    document.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowLeft') slideAnterior();
        if (e.key === 'ArrowRight') proximoSlide();
        if (e.key === 'Escape') {
            // Se estiver em fullscreen, sai do fullscreen primeiro
            if (document.fullscreenElement || document.webkitFullscreenElement || document.mozFullScreenElement || document.msFullscreenElement) {
                exitFullscreen();
            } else {
                sairApresentacao();
            }
        }
        if (e.key === 'F11') {
            e.preventDefault();
            toggleFullscreen();
        }
    });
    
    // Detecta mudanças no estado de fullscreen
    document.addEventListener('fullscreenchange', atualizarIconeFullscreen);
    document.addEventListener('webkitfullscreenchange', atualizarIconeFullscreen);
    document.addEventListener('mozfullscreenchange', atualizarIconeFullscreen);
    document.addEventListener('MSFullscreenChange', atualizarIconeFullscreen);
});

// ==================== CARREGAR APRESENTAÇÃO ====================
async function carregarApresentacao(forceClientId = null) {
    // Mostra loading
    const container = document.getElementById('slideContent');
    if (container) {
        container.innerHTML = '<div style="display: flex; align-items: center; justify-content: center; height: 100%; flex-direction: column;"><div class="loading"><i class="fas fa-spinner fa-spin"></i><p>Carregando apresentação...</p></div></div>';
    }
    
    try {
        // Sempre obtém o client_id atual do localStorage (sem valor padrão)
        let clientId = forceClientId;
        
        if (!clientId) {
            if (typeof window.getCurrentClientId === 'function') {
                clientId = window.getCurrentClientId(null);
            } else {
                const stored = localStorage.getItem('cliente_selecionado');
                clientId = stored ? Number(stored) : null;
            }
        }
        
        // Converte para número se for string
        if (typeof clientId === 'string') {
            clientId = Number(clientId);
        }
        
        // Valida se é um número válido
        if (!clientId || !Number.isFinite(clientId) || clientId <= 0 || clientId === 'null' || clientId === 'undefined') {
            mostrarErro('Selecione um cliente para visualizar a apresentação');
            return;
        }
        
        console.log('Carregando apresentação para cliente ID:', clientId);
        
        // Adiciona timestamp para evitar cache
        const timestamp = new Date().getTime();
        
        // Cria um AbortController para timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 segundos
        
        let response;
        try {
            response = await fetch(`/api/apresentacao?client_id=${clientId}&_t=${timestamp}`, {
                signal: controller.signal
            });
            clearTimeout(timeoutId);
        } catch (error) {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                throw new Error('Timeout: A requisição demorou mais de 30 segundos. O servidor pode estar sobrecarregado.');
            }
            throw error;
        }
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('[APRESENTACAO] Erro na resposta:', response.status, errorText);
            throw new Error(`Erro ao carregar apresentação: ${response.status} - ${errorText}`);
        }
        
        const data = await response.json();
        console.log('[APRESENTACAO] Dados recebidos do backend:', data);
        slides = data.slides || [];
        
        console.log('[APRESENTACAO] Resposta completa:', data);
        console.log('[APRESENTACAO] Slides carregados:', slides.length, 'para cliente:', clientId);
        console.log('[APRESENTACAO] Primeiros 3 slides:', slides.slice(0, 3));
        
        // Ajusta header para RODA DE OURO (preto-cinza)
        if (clientId === 4) {
            const header = document.querySelector('.apresentacao-header');
            if (header) {
                header.style.background = 'linear-gradient(135deg, #000000, #808080)';
            }
        } else {
            // Restaura cores padrão para outras empresas
            const header = document.querySelector('.apresentacao-header');
            if (header) {
                header.style.background = 'linear-gradient(135deg, #1a237e, #3949ab)';
            }
        }
        
        const totalSlidesEl = document.getElementById('totalSlides');
        if (totalSlidesEl) {
            totalSlidesEl.textContent = slides.length;
        }
        
        if (slides.length > 0) {
            slideAtual = 0;
            console.log('[APRESENTACAO] Renderizando slide 0:', slides[0]);
            renderizarSlide(slides[0]);
            atualizarBotoes();
        } else {
            console.error('[APRESENTACAO] Nenhum slide retornado!');
            mostrarErro('Nenhum dado disponível para apresentação. Verifique se há dados cadastrados para este cliente.');
        }
    } catch (error) {
        console.error('Erro ao carregar apresentação:', error);
        mostrarErro('Erro ao carregar apresentação: ' + error.message);
    }
}

// Recarrega quando o cliente muda
if (typeof window !== 'undefined') {
    // Observa mudanças no localStorage
    window.addEventListener('storage', (e) => {
        if (e.key === 'cliente_selecionado') {
            console.log('Cliente mudou no storage, recarregando apresentação...');
            setTimeout(() => {
                carregarApresentacao();
            }, 300);
        }
    });
    
    // Observa mudanças diretas no localStorage (mesma aba)
    const originalSetItem = localStorage.setItem;
    localStorage.setItem = function(key, value) {
        originalSetItem.apply(this, arguments);
        if (key === 'cliente_selecionado') {
            console.log('Cliente mudou no localStorage, recarregando apresentação...');
            // Recarrega a apresentação quando o cliente muda
            setTimeout(() => {
                const newClientId = Number(value);
                if (newClientId && Number.isFinite(newClientId) && newClientId > 0) {
                    carregarApresentacao(newClientId);
                }
            }, 300);
        }
    };
}

// ==================== RENDERIZAR SLIDE ====================
function renderizarSlide(slide) {
    const container = document.getElementById('slideContent');
    if (!container) {
        console.error('[APRESENTACAO] Container slideContent não encontrado!');
        return;
    }
    
    if (!slide) {
        console.error('[APRESENTACAO] Slide é null ou undefined!');
        return;
    }
    
    console.log('[APRESENTACAO] Renderizando slide:', slide.id, slide.tipo);
    
    // Não mostra número para capa (id 0) e slides de ações (id >= 14)
    const slideAtualEl = document.getElementById('slideAtual');
    if (slideAtualEl) {
    if (slide.id === 0 || slide.id >= 14) {
            slideAtualEl.textContent = '-';
    } else {
            slideAtualEl.textContent = slide.id;
        }
    }
    
    // Limpa gráficos anteriores
    Object.values(charts).forEach(chart => {
        if (chart) chart.destroy();
    });
    charts = {};
    
    // Remove footer antigo se existir (antes de renderizar novo slide)
    // Procura em todos os containers possíveis
    const footerAntigo1 = document.querySelector('.slide-body div[style*="position: absolute"][style*="bottom: 0"]');
    const footerAntigo2 = document.querySelector('div[style*="position: fixed"][style*="bottom: 0"]');
    if (footerAntigo1) {
        footerAntigo1.remove();
    }
    if (footerAntigo2) {
        footerAntigo2.remove();
    }
    
    let html = '';
    
    // Renderiza conteúdo baseado no tipo
    if (slide.tipo === 'capa') {
        // Capa não tem header - renderiza de forma assíncrona
        container.innerHTML = '<div style="display: flex; align-items: center; justify-content: center; height: 100%;"><div class="loading"><i class="fas fa-spinner fa-spin"></i><p>Carregando capa...</p></div></div>';
        renderizarCapa().then(capaHTML => {
            if (capaHTML) {
                container.innerHTML = capaHTML;
            } else {
                container.innerHTML = '<div style="display: flex; align-items: center; justify-content: center; height: 100%;"><p>Erro ao carregar capa</p></div>';
            }
        }).catch(error => {
            console.error('[APRESENTACAO] Erro ao renderizar capa:', error);
            container.innerHTML = '<div style="display: flex; align-items: center; justify-content: center; height: 100%;"><p>Erro ao carregar capa: ' + error.message + '</p></div>';
        });
        return; // Retorna cedo para não processar o resto
    } else {
        // Outros slides têm header
        // Título sempre em preto
        html += `
            <div class="slide-header">
                <h2 style="color: #000000;">${slide.titulo}</h2>
                <p>${slide.subtitulo}</p>
            </div>
        `;
        
        if (slide.tipo === 'kpis') {
            html += `<div class="slide-body">`;
            html += renderizarKPIs(slide.dados);
            // Análise IA para KPIs
            html += `
                <div class="analise-container">
                    <h3>
                        <i class="fas fa-lightbulb"></i>
                        Análise e Insights
                    </h3>
                    <div class="analise-texto">${formatarAnalise(slide.analise)}</div>
                </div>
            `;
            html += `</div>`;
        } else if (slide.tipo === 'produtividade') {
            html += `<div class="slide-body">`;
            html += renderizarProdutividade(slide);
            html += `</div>`;
        } else if (slide.tipo === 'acoes_intro' || slide.tipo === 'acoes_saude_fisica' || slide.tipo === 'acoes_saude_emocional' || slide.tipo === 'acoes_saude_social') {
            // Slides de ações ocupam toda a altura (sem grid de análise)
            html += `<div class="slide-body" style="position: relative; display: flex; flex-direction: column;">`;
            html += `<div style="flex: 1; overflow: hidden; position: relative; height: 100%;">`;
            // Botões de edição (apenas para slides de saúde, não para introdução)
            if (slide.tipo !== 'acoes_intro') {
                html += `
                    <div style="position: absolute; top: 10px; right: 10px; z-index: 100; display: flex; gap: 8px;">
                        <button id="btnEditarAcoes" onclick="toggleEdicaoAcoes('${slide.tipo}')" style="padding: 8px 16px; background: #000000; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 600; display: flex; align-items: center; gap: 6px;">
                            <i class="fas fa-edit"></i> Editar
                        </button>
                        <button id="btnSalvarAcoes" onclick="salvarAcoes('${slide.tipo}')" style="padding: 8px 16px; background: #808080; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 600; display: none; align-items: center; gap: 6px;">
                            <i class="fas fa-save"></i> Salvar
                        </button>
                    </div>
                `;
            }
            if (slide.tipo === 'acoes_intro') {
                html += renderizarAcoesIntro(slide.tipo);
            } else if (slide.tipo === 'acoes_saude_fisica') {
                html += renderizarAcoesSaudeFisica(slide.tipo);
            } else if (slide.tipo === 'acoes_saude_emocional') {
                html += renderizarAcoesSaudeEmocional(slide.tipo);
            } else if (slide.tipo === 'acoes_saude_social') {
                html += renderizarAcoesSaudeSocial(slide.tipo);
            }
            html += `</div>`; // Fecha div position relative
            html += `</div>`; // Fecha slide-body
            
            // Footer dinâmico - adiciona no container interno
            setTimeout(async () => {
                try {
                    const footerHTML = await renderizarFooterAcoes();
                    // Procura o container interno (div com position: relative) dentro do slide-body
                    const slideBody = document.querySelector('.slide-body[style*="position: relative"]');
                    if (slideBody) {
                        const container = slideBody.querySelector('div[style*="position: relative"]');
                        if (container) {
                            // Garante que o container tenha altura completa
                            const slideBodyHeight = slideBody.offsetHeight;
                            container.style.height = slideBodyHeight + 'px';
                            container.style.position = 'relative';
                            
                            // Remove footer antigo
                            const footerAntigo = container.querySelector('div[style*="position: absolute"][style*="bottom: 0"]');
                            if (footerAntigo) footerAntigo.remove();
                            
                            // Adiciona footer no final
                            container.insertAdjacentHTML('beforeend', footerHTML);
                        }
                    }
                } catch (error) {
                    console.error('[FOOTER] Erro:', error);
                }
            }, 200);
        } else {
            html += `<div class="slide-body">`;
            html += `
                <div class="chart-container-wrapper">
                    <div class="chart-container">
                        <canvas id="chartSlide"></canvas>
                    </div>
                </div>
            `;
            // Análise IA para gráficos
            const analiseTexto = slide.analise || 'Análise não disponível.';
            console.log(`[APRESENTACAO] Slide ${slide.tipo} - Análise:`, analiseTexto);
            html += `
                <div class="analise-container">
                    <h3>
                        <i class="fas fa-lightbulb"></i>
                        Análise e Insights
                    </h3>
                    <div class="analise-texto">${formatarAnalise(analiseTexto)}</div>
                </div>
            `;
            html += `</div>`;
        }
    }
    
    container.innerHTML = html;
    
    // Renderiza gráfico se necessário
    if (slide.tipo !== 'kpis' && slide.tipo !== 'capa' && slide.tipo !== 'acoes_intro' && slide.tipo !== 'acoes_saude_fisica' && slide.tipo !== 'acoes_saude_emocional' && slide.tipo !== 'acoes_saude_social') {
        console.log(`[APRESENTACAO] Preparando para renderizar gráfico ${slide.tipo}...`);
        setTimeout(() => {
            renderizarGrafico(slide);
        }, 100);
    } else {
        console.log(`[APRESENTACAO] Slide ${slide.tipo} não requer gráfico`);
    }
}

// ==================== RENDERIZAR CAPA ====================
async function renderizarCapa() {
    // Busca dados do cliente atual
    let clienteInfo = {
        nome: 'Empresa',
        nome_fantasia: '',
        logo_url: null
    };
    
    const clientId = typeof window.getCurrentClientId === 'function' ? window.getCurrentClientId(null) : null;
    if (clientId) {
        try {
            const response = await fetch(`/api/clientes/${clientId}`);
            if (response.ok) {
                const cliente = await response.json();
                clienteInfo = {
                    nome: cliente.nome || 'Empresa',
                    nome_fantasia: cliente.nome_fantasia || cliente.nome || 'Empresa',
                    logo_url: cliente.logo_url || null
                };
            }
        } catch (error) {
            console.error('Erro ao buscar dados do cliente:', error);
        }
    }
    
    // Obtém cores do cliente
    const cores = getCoresApresentacao();
    const corPrimaria = cores.primary || '#1a237e';
    const corSecundaria = cores.secondary || '#556B2F';
    
    // Gera nome da empresa para exibição
    const nomeExibicao = clienteInfo.nome_fantasia || clienteInfo.nome || 'Empresa';
    
    // Formata data atual
    const agora = new Date();
    const meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                   'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'];
    const mesAtual = meses[agora.getMonth()];
    const anoAtual = agora.getFullYear();
    const dataFormatada = agora.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' });
    
    // Renderiza logo ou nome
    // Para RODA DE OURO (client_id = 4): retangular (64px altura x 128px largura)
    // Para outras empresas: mantém formato original
    const isRodaOuro = clientId === 4;
    
    let logoHTML = '';
    if (clienteInfo.logo_url) {
        // Adiciona timestamp para evitar cache
        const logoUrlComCache = clienteInfo.logo_url + (clienteInfo.logo_url.includes('?') ? '&' : '?') + '_t=' + Date.now();
        
        if (isRodaOuro) {
            // RODA DE OURO: formato HORIZONTAL/RETANGULAR FORÇADO (120px altura x 360px largura) - 3:1 HORIZONTAL
            logoHTML = `
                <div style="margin-bottom: 80px; display: flex; align-items: center; justify-content: center; width: 100%;">
                    <div style="height: 120px !important; width: 360px !important; min-width: 360px !important; max-width: 360px !important; min-height: 120px !important; max-height: 120px !important; aspect-ratio: 3 / 1 !important; overflow: hidden !important; background: transparent !important; display: flex !important; align-items: center !important; justify-content: center !important; box-sizing: border-box !important;">
                        <img src="${logoUrlComCache}" alt="${nomeExibicao}" style="width: 360px !important; height: 120px !important; max-width: 360px !important; max-height: 120px !important; aspect-ratio: 3 / 1 !important; object-fit: contain !important; object-position: center !important; display: block !important;">
                    </div>
                </div>
            `;
        } else {
            // Converplast e outras: formato original (aumentado)
            logoHTML = `
                <div style="margin-bottom: 80px; display: flex; align-items: center; justify-content: center;">
                    <img src="${logoUrlComCache}" alt="${nomeExibicao}" style="max-height: 200px; max-width: 600px; object-fit: contain;">
                </div>
            `;
        }
    } else {
        if (isRodaOuro) {
            // RODA DE OURO: nome completo em formato HORIZONTAL (100px altura x 300px largura)
            const tamanhoFonte = nomeExibicao.length > 20 ? 16 : (nomeExibicao.length > 15 ? 18 : 20);
            logoHTML = `
                <div style="margin-bottom: 80px; display: flex; align-items: center; justify-content: center;">
                    <div style="height: 100px !important; width: 300px !important; min-width: 300px !important; max-width: 300px !important; background: ${corPrimaria}; border-radius: 4px; padding: 8px 12px; box-sizing: border-box; overflow: hidden; display: flex; align-items: center; justify-content: center;">
                        <span style="font-size: ${tamanhoFonte}px; font-weight: 700; color: white; letter-spacing: 0.5px; line-height: 1.2; text-align: center; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; text-overflow: ellipsis; word-break: break-word; max-width: 100%;">${nomeExibicao}</span>
                    </div>
                </div>
            `;
        } else {
            // Converplast e outras: iniciais no formato original
            const iniciais = gerarIniciaisCapa(nomeExibicao);
            logoHTML = `
                <div style="margin-bottom: 80px; display: flex; align-items: center; justify-content: center;">
                    <div style="width: 180px; height: 180px; border-radius: 50%; background: linear-gradient(135deg, ${corPrimaria}, ${corSecundaria}); display: flex; align-items: center; justify-content: center; box-shadow: 0 8px 24px rgba(0,0,0,0.2);">
                        <span style="font-size: 72px; font-weight: 700; color: white; letter-spacing: 2px;">${iniciais}</span>
                    </div>
                </div>
            `;
        }
    }
    
    const htmlCapa = `
        <div style="display: flex; flex-direction: column; height: 100%; width: 100%; background: white; position: relative;">
            <!-- Linha decorativa no topo -->
            <div style="height: 4px; background: linear-gradient(to right, ${corSecundaria} 0%, ${corSecundaria} 50%, ${corPrimaria} 50%, ${corPrimaria} 100%);"></div>
            
            <!-- Conteúdo principal -->
            <div style="flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 60px 40px; position: relative;">
                ${logoHTML}
                
                <!-- Título principal -->
                <div style="text-align: center; margin-bottom: 60px;">
                    <h1 style="font-size: 48px; font-weight: 700; color: ${corPrimaria}; margin: 0 0 30px 0; letter-spacing: 1px; line-height: 1.4;">
                        SAÚDE CORPORATIVA - MEDICINA DO TRABALHO
                    </h1>
                    <h2 style="font-size: 42px; font-weight: 600; color: ${corPrimaria}; margin: 0; letter-spacing: 0.5px;">
                        INDICADORES DE SAÚDE
                    </h2>
                </div>
                
                <!-- Data no canto inferior direito -->
                <div style="position: absolute; bottom: 50px; right: 80px; text-align: right;">
                    <div style="font-size: 32px; font-weight: 600; color: ${corPrimaria}; margin-bottom: 10px; letter-spacing: 0.5px;">
                        ${mesAtual.toUpperCase()}, ${anoAtual}
                    </div>
                    <div style="font-size: 26px; font-weight: 500; color: ${corPrimaria}; letter-spacing: 0.5px;">
                        ${dataFormatada}
                    </div>
                </div>
            </div>
            
            <!-- Linha decorativa na parte inferior -->
            <div style="height: 4px; background: linear-gradient(to right, ${corPrimaria} 0%, ${corPrimaria} 50%, ${corSecundaria} 50%, ${corSecundaria} 100%);"></div>
        </div>
    `;
    
    return htmlCapa;
}

function gerarIniciaisCapa(nome) {
    if (!nome) return 'AC';
    const palavras = nome.trim().split(/\s+/);
    if (palavras.length >= 2) {
        return (palavras[0][0] + palavras[palavras.length - 1][0]).toUpperCase();
    }
    return nome.substring(0, 2).toUpperCase();
}

function renderizarKPIs(dados) {
    // Total de Atestados = número de registros (total_atestados)
    // Dias Perdidos = soma dos dias_atestados
    // Horas Perdidas = soma das horas_perdi
    const totalAtestados = Math.round(dados.total_atestados || dados.total_registros || 0);
    const totalDias = Math.round(dados.total_dias_perdidos || 0);
    const totalHoras = Math.round(dados.total_horas_perdidas || 0);
    
    // Obtém client_id atual para determinar cores
    const clientId = typeof window.getCurrentClientId === 'function' ? window.getCurrentClientId(null) : null;
    const isRodaOuro = clientId === 4;
    
    // Cores para Roda de Ouro (preto e cinza)
    const coresRO = {
        card1: '#000000',  // Preto
        card2: '#404040',  // Cinza escuro
        card3: '#808080'   // Cinza
    };
    
    // Cores padrão (Converplast e outras)
    const coresPadrao = {
        card1: '#1a237e',  // Azul escuro
        card2: '#3949ab',  // Azul médio
        card3: '#5c6bc0'   // Azul claro
    };
    
    const cores = isRodaOuro ? coresRO : coresPadrao;
    
    return `
        <div class="kpis-grid">
            <div class="kpi-card" style="background: linear-gradient(135deg, ${cores.card1}, ${cores.card2}); border-left: 4px solid ${cores.card1};">
                <h3>Total de Atestados</h3>
                <div class="valor">${totalAtestados}</div>
                <div class="label">Atestados</div>
            </div>
            <div class="kpi-card" style="background: linear-gradient(135deg, ${cores.card2}, ${cores.card3}); border-left: 4px solid ${cores.card2};">
                <h3>Dias Perdidos</h3>
                <div class="valor">${totalDias}</div>
                <div class="label">Dias</div>
            </div>
            <div class="kpi-card" style="background: linear-gradient(135deg, ${cores.card3}, ${cores.card2}); border-left: 4px solid ${cores.card3};">
                <h3>Horas Perdidas</h3>
                <div class="valor">${totalHoras}</div>
                <div class="label">Horas</div>
            </div>
        </div>
    `;
}

function renderizarGrafico(slide) {
    const ctx = document.getElementById('chartSlide');
    if (!ctx) {
        console.warn('[APRESENTACAO] Canvas chartSlide não encontrado');
        return;
    }
    
    const tipo = slide.tipo;
    const dados = slide.dados;
    
    // Validação mais flexível: aceita arrays e objetos
    if (!dados) {
        console.warn(`[APRESENTACAO] Slide ${tipo} sem dados`);
        return;
    }
    
    // Verifica se é array vazio
    if (Array.isArray(dados) && dados.length === 0) {
        console.warn(`[APRESENTACAO] Slide ${tipo} com array vazio`);
        return;
    }
    
    // Verifica se é objeto vazio (para gráficos como dias_ano_coerencia, analise_coerencia)
    if (typeof dados === 'object' && !Array.isArray(dados)) {
        const temDados = Object.keys(dados).some(key => {
            const valor = dados[key];
            if (Array.isArray(valor)) return valor.length > 0;
            if (typeof valor === 'number') return valor > 0;
            return valor != null && valor !== '';
        });
        if (!temDados) {
            console.warn(`[APRESENTACAO] Slide ${tipo} com objeto sem dados válidos`);
            return;
        }
    }
    
    console.log(`[APRESENTACAO] Renderizando gráfico ${tipo} com dados:`, dados);
    
    let config = {};
    
    // Obtém client_id atual para determinar cores
    const clientId = typeof window.getCurrentClientId === 'function' ? window.getCurrentClientId(null) : null;
    const clientIdNum = clientId ? Number(clientId) : null;
    
    // Cores da RODA DE OURO (preto e cinza) - apenas se for RODA DE OURO (client_id = 4)
    const coresRO = { preto: '#000000', cinza: '#808080', cinzaEscuro: '#404040', cinzaClaro: '#A0A0A0' };
    
    // Obtém cores dinâmicas do cliente
    const coresCliente = getCoresApresentacao();
    
    switch(tipo) {
        case 'funcionarios_dias':
            // TOP 10 funcionários ordenados por dias perdidos
            const top10Func = dados.slice(0, 10).sort((a, b) => (b.dias_perdidos || 0) - (a.dias_perdidos || 0));
            config = {
                type: 'bar',
                data: {
                    labels: top10Func.map(d => truncate(d.nome || d.nomecompleto || 'N/A', 25)),
                    datasets: [{
                        label: 'Dias Perdidos',
                        data: top10Func.map(d => d.dias_perdidos || 0),
                        backgroundColor: CORES_EMPRESA.primaryDark,
                        borderRadius: 6
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const index = context.dataIndex;
                                    const func = top10Func[index];
                                    return [
                                        `Dias Perdidos: ${context.parsed.x}`,
                                        `Atestados: ${func.quantidade || 0}`,
                                        `Setor: ${func.setor || 'N/A'}`
                                    ];
                                }
                            }
                        }
                    },
                    scales: {
                        x: { beginAtZero: true },
                        y: { ticks: { font: { size: 11 } } }
                    }
                }
            };
            break;
            
        case 'top_cids':
            // Ordena por quantidade (decrescente) - MESMA LÓGICA DO DASHBOARD
            const cidsOrdenados = [...dados].sort((a, b) => (b.quantidade || 0) - (a.quantidade || 0));
            config = {
                type: 'bar',
                data: {
                    labels: cidsOrdenados.map(d => truncate(d.descricao || d.cid, 28)),
                    datasets: [{
                        label: 'Atestados',
                        data: cidsOrdenados.map(d => d.quantidade),
                        backgroundColor: CORES_EMPRESA.primary,
                        borderRadius: 6,
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                title: function(context) {
                                    const index = context[0].dataIndex;
                                    const item = cidsOrdenados[index];
                                    const diagnostico = item.descricao || item.diagnostico || item.cid || 'Não especificado';
                                    return diagnostico;
                                },
                                label: function(context) {
                                    const index = context.dataIndex;
                                    const item = cidsOrdenados[index];
                                    
                                    // Mostra CIDs relacionados se houver múltiplos
                                    let cid_info = '';
                                    if (item.cids_relacionados && item.cids_relacionados.length > 1) {
                                        cid_info = `CIDs: ${item.cids_relacionados.join(', ')}`;
                                    } else if (item.cid) {
                                        cid_info = `CID: ${item.cid}`;
                                    }
                                    
                                    return [
                                        cid_info,
                                        `Quantidade: ${item.quantidade || 0} atestados`,
                                        `Dias perdidos: ${item.dias_perdidos || 0}`
                                    ];
                                }
                            }
                        }
                    },
                    scales: {
                        x: { beginAtZero: true },
                        y: { ticks: { font: { size: 11 } } }
                    }
                }
            };
            break;
            
        case 'evolucao_mensal':
            config = {
                type: 'line',
                data: {
                    labels: dados.map(d => d.mes || 'N/A'),
                    datasets: [
                        {
                            label: 'Dias Perdidos',
                            data: dados.map(d => d.dias_perdidos || 0),
                            borderColor: CORES_EMPRESA.primary,
                            backgroundColor: CORES_EMPRESA.primaryLight + '40',
                            fill: true,
                            tension: 0.4,
                            yAxisID: 'y'
                        },
                        {
                            label: 'Quantidade de Atestados',
                            data: dados.map(d => d.quantidade || 0),
                            borderColor: CORES_EMPRESA.secondary,
                            backgroundColor: CORES_EMPRESA.secondaryLight + '40',
                            fill: true,
                            tension: 0.4,
                            yAxisID: 'y1'
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: { mode: 'index', intersect: false },
                    plugins: {
                        legend: { 
                            display: true,
                            position: 'top',
                            labels: { font: { size: 11 } }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const index = context.dataIndex;
                                    const item = dados[index];
                                    if (context.datasetIndex === 0) {
                                        return `Dias Perdidos: ${item.dias_perdidos || 0}`;
                                    } else {
                                        return `Atestados: ${item.quantidade || 0}`;
                                    }
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            type: 'linear',
                            display: true,
                            position: 'left',
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Dias Perdidos',
                                color: CORES_EMPRESA.primary
                            }
                        },
                        y1: {
                            type: 'linear',
                            display: true,
                            position: 'right',
                            beginAtZero: true,
                            grid: { drawOnChartArea: false },
                            title: {
                                display: true,
                                text: 'Quantidade de Atestados',
                                color: CORES_EMPRESA.secondary
                            }
                        }
                    }
                }
            };
            break;
            
        case 'top_setores':
            // Ordena por quantidade (decrescente) - MESMA LÓGICA DO DASHBOARD
            const setoresTopOrdenados = [...dados].sort((a, b) => (b.quantidade || 0) - (a.quantidade || 0));
            const top5Setores = setoresTopOrdenados.slice(0, 5);
            config = {
                type: 'line',
                data: {
                    labels: top5Setores.map(d => truncate(d.setor, 20)),
                    datasets: [{
                        label: 'Quantidade de Atestados',
                        data: top5Setores.map(d => d.quantidade),
                        borderColor: CORES_EMPRESA.primary,
                        backgroundColor: 'rgba(26, 35, 126, 0.1)',
                        tension: 0.4,
                        fill: true,
                        pointRadius: 5,
                        pointHoverRadius: 7,
                        pointBackgroundColor: CORES_EMPRESA.primary,
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { 
                            display: true, 
                            position: 'top',
                            labels: { font: { size: 11 } }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const index = context.dataIndex;
                                    const setor = top5Setores[index];
                                    return [
                                        `Atestados: ${setor.quantidade || 0}`,
                                        `Dias perdidos: ${setor.dias_perdidos || 0}`,
                                        `Horas perdidas: ${setor.horas_perdidas || 0}`
                                    ];
                                }
                            }
                        }
                    },
                    scales: {
                        y: { 
                            beginAtZero: true,
                            ticks: { font: { size: 11 }, stepSize: 1 }
                        },
                        x: { 
                            ticks: { 
                                font: { size: 11 },
                                maxRotation: 0,
                                autoSkip: false
                            }
                        }
                    }
                }
            };
            break;
            
        case 'genero':
            const totalGenero = dados.reduce((sum, d) => sum + (d.quantidade || 0), 0);
            config = {
                type: 'doughnut',
                data: {
                    labels: dados.map(d => d.genero === 'M' ? 'Masculino' : 'Feminino'),
                    datasets: [{
                        data: dados.map(d => d.quantidade || 0),
                        backgroundColor: [CORES_EMPRESA.primary, CORES_EMPRESA.secondary]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { 
                            display: true, 
                            position: 'bottom',
                            labels: { font: { size: 11 } }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const index = context.dataIndex;
                                    const item = dados[index];
                                    const pct = totalGenero > 0 ? ((item.quantidade || 0) / totalGenero * 100).toFixed(1) : 0;
                                    return [
                                        `${item.genero === 'M' ? 'Masculino' : 'Feminino'}: ${item.quantidade || 0} atestados`,
                                        `Percentual: ${pct}%`
                                    ];
                                }
                            }
                        }
                    }
                }
            };
            break;
            
        case 'dias_doenca':
            // Ordena por dias perdidos (decrescente) - MESMA LÓGICA DO DASHBOARD
            const doencasOrdenadas = [...dados].sort((a, b) => (b.dias_perdidos || 0) - (a.dias_perdidos || 0));
            const top5Cids = doencasOrdenadas.slice(0, 5);
            config = {
                type: 'bar',
                data: {
                    labels: top5Cids.map(d => truncate(d.descricao || d.cid, 18)),
                    datasets: [{
                        label: 'Dias',
                        data: top5Cids.map(d => d.dias_perdidos),
                        backgroundColor: CORES_EMPRESA.secondary
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            };
            break;
            
        case 'escalas':
            // Ordena por quantidade (decrescente) - MESMA LÓGICA DO DASHBOARD
            const escalasOrdenadas = [...dados].sort((a, b) => (b.quantidade || 0) - (a.quantidade || 0));
            const top10Escalas = escalasOrdenadas.slice(0, 10);
            config = {
                type: 'bar',
                data: {
                    labels: top10Escalas.map(d => d.escala || 'N/A'),
                    datasets: [{
                        label: 'Atestados',
                        data: top10Escalas.map(d => d.quantidade || 0),
                        backgroundColor: PALETA_EMPRESA
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const index = context.dataIndex;
                                    const escala = escalasOrdenadas[index];
                                    return `Atestados: ${escala.quantidade || 0}`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: { beginAtZero: true },
                        y: {
                            ticks: {
                                font: { size: 11 },
                                maxRotation: 0,
                                autoSkip: false
                            }
                        }
                    }
                }
            };
            break;
            
        case 'motivos':
            // Ordena por quantidade (decrescente) - MESMA LÓGICA DO DASHBOARD
            const motivosOrdenados = [...dados].sort((a, b) => (b.quantidade || 0) - (a.quantidade || 0));
            const top10Motivos = motivosOrdenados.slice(0, 10);
            const totalMotivos = top10Motivos.reduce((sum, m) => sum + (m.quantidade || 0), 0);
            config = {
                type: 'pie',
                data: {
                    labels: top10Motivos.map(d => d.motivo || 'N/A'),
                    datasets: [{
                        data: top10Motivos.map(d => d.quantidade || 0),
                        backgroundColor: PALETA_EMPRESA
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { 
                            display: true, 
                            position: 'right',
                            labels: {
                                generateLabels: function(chart) {
                                    const data = chart.data;
                                    if (data.labels.length && data.datasets.length) {
                                        return data.labels.map((label, i) => {
                                            const dataset = data.datasets[0];
                                            const motivo = top10Motivos[i];
                                            const quantidade = motivo.quantidade || 0;
                                            const percentual = totalMotivos > 0 ? ((quantidade / totalMotivos) * 100).toFixed(1) : 0;
                                            return {
                                                text: `${label} - ${percentual}% (${quantidade})`,
                                                fillStyle: dataset.backgroundColor[i],
                                                hidden: false,
                                                index: i
                                            };
                                        });
                                    }
                                    return [];
                                }
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const index = context.dataIndex;
                                    const motivo = top10Motivos[index];
                                    const quantidade = motivo.quantidade || 0;
                                    const percentual = totalMotivos > 0 ? ((quantidade / totalMotivos) * 100).toFixed(1) : 0;
                                    return [
                                        `Motivo: ${motivo.motivo || 'N/A'}`,
                                        `Quantidade: ${quantidade} atestados`,
                                        `Percentual: ${percentual}%`
                                    ];
                                }
                            }
                        }
                    }
                }
            };
            break;
            
        case 'centro_custo':
            // Ordena por dias perdidos (decrescente) - MESMA LÓGICA DO DASHBOARD
            const centrosOrdenados = [...dados].sort((a, b) => (b.dias_perdidos || 0) - (a.dias_perdidos || 0));
            const top10Setores = centrosOrdenados.slice(0, 10);
            config = {
                type: 'bar',
                data: {
                    labels: top10Setores.map(d => truncate(d.centro_custo || d.setor || 'N/A', 25)),
                    datasets: [{
                        label: 'Dias Perdidos',
                        data: top10Setores.map(d => d.dias_perdidos || 0),
                        backgroundColor: CORES_EMPRESA.primaryDark,
                        borderRadius: 6
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const index = context.dataIndex;
                                    const item = top10Setores[index];
                                    return [
                                        `Dias Perdidos: ${context.parsed.x}`,
                                        `Atestados: ${item.quantidade || 0}`,
                                        `Horas Perdidas: ${item.horas_perdidas || 0}`
                                    ];
                                }
                            }
                        }
                    },
                    scales: {
                        x: { beginAtZero: true },
                        y: { ticks: { font: { size: 11 } } }
                    }
                }
            };
            break;
            
        case 'distribuicao_dias':
            config = {
                type: 'bar',
                data: {
                    labels: dados.map(d => `${d.faixa || d.dias || 'N/A'}`),
                    datasets: [{
                        label: 'Quantidade',
                        data: dados.map(d => d.quantidade || 0),
                        backgroundColor: CORES_EMPRESA.primaryLight
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const index = context.dataIndex;
                                    const item = dados[index];
                                    return `Quantidade: ${item.quantidade || 0} atestados`;
                                }
                            }
                        }
                    },
                    scales: {
                        y: { beginAtZero: true },
                        x: { ticks: { font: { size: 11 } } }
                    }
                }
            };
            break;
            
        case 'media_cid':
            // Ordena por média de dias (decrescente) - MESMA LÓGICA DO DASHBOARD
            const mediaCidOrdenados = [...dados].sort((a, b) => (b.media_dias || 0) - (a.media_dias || 0));
            const top10MediaCid = mediaCidOrdenados.slice(0, 10);
            config = {
                type: 'bar',
                data: {
                    labels: top10MediaCid.map(d => truncate(d.cid + ' - ' + (d.diagnostico || d.descricao || ''), 30)),
                    datasets: [{
                        label: 'Média de Dias',
                        data: top10MediaCid.map(d => d.media_dias || 0),
                        backgroundColor: CORES_EMPRESA.primary,  // Azul Marinho
                        borderRadius: 6
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const index = context.dataIndex;
                                    const item = top10MediaCid[index];
                                    return [
                                        `Média: ${item.media_dias || 0} dias`,
                                        `Total de dias: ${item.total_dias || 0}`,
                                        `Quantidade: ${item.quantidade || 0} atestados`,
                                        `Diagnóstico: ${item.diagnostico || item.descricao || 'N/A'}`
                                    ];
                                }
                            }
                        }
                    },
                    scales: {
                        x: { beginAtZero: true },
                        y: { ticks: { font: { size: 11 } } }
                    }
                }
            };
            break;
            
        case 'setor_genero':
            // Calcula total geral para calcular percentuais
            const totalGeralSetorGenero = dados.reduce((sum, d) => sum + (d.dias_perdidos || 0), 0);
            
            // Agrupa por setor e calcula total por setor
            const setoresMap = {};
            dados.forEach(d => {
                if (!setoresMap[d.setor]) {
                    setoresMap[d.setor] = {
                        setor: d.setor,
                        total: 0,
                        M: 0,
                        F: 0
                    };
                }
                const dias = d.dias_perdidos || 0;
                setoresMap[d.setor].total += dias;
                if (d.genero === 'M') {
                    setoresMap[d.setor].M += dias;
                } else if (d.genero === 'F') {
                    setoresMap[d.setor].F += dias;
                }
            });
            
            // Converte para array e ordena por total (incidência)
            const setoresOrdenados = Object.values(setoresMap)
                .sort((a, b) => b.total - a.total)
                .slice(0, 10); // TOP 10
            
            const setoresLabels = setoresOrdenados.map(s => s.setor);
            const generos = ['M', 'F'];
            // Azul Marinho para Masculino, Verde Oliva para Feminino
            const cores = { 'M': CORES_EMPRESA.primary, 'F': CORES_EMPRESA.secondary };
            
            // Prepara dados com percentuais
            const datasetsSetorGenero = generos.map(genero => {
                const label = genero === 'M' ? 'Masculino' : 'Feminino';
                const data = setoresLabels.map(setor => {
                    const item = setoresOrdenados.find(s => s.setor === setor);
                    return item ? (item[genero] || 0) : 0;
                });
                
                // Calcula percentuais para tooltip
                const percentuais = data.map(valor => {
                    return totalGeralSetorGenero > 0 ? ((valor / totalGeralSetorGenero) * 100).toFixed(2) : '0.00';
                });
                
                return {
                    label: label,
                    data: data,
                    backgroundColor: cores[genero],
                    borderRadius: 6,
                    percentuais: percentuais
                };
            });
            
            config = {
                type: 'bar',
                data: {
                    labels: setoresLabels.map(s => truncate(s, 25)),
                    datasets: datasetsSetorGenero
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { 
                            position: 'top', 
                            labels: { 
                                font: { size: 12 },
                                padding: 15,
                                boxWidth: 20,
                                boxHeight: 12
                            } 
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            padding: 12,
                            titleFont: { size: 13, weight: 'bold' },
                            bodyFont: { size: 12 },
                            callbacks: {
                                label: function(context) {
                                    const datasetIndex = context.datasetIndex;
                                    const dataIndex = context.dataIndex;
                                    const valor = context.parsed.y;
                                    const percentual = context.dataset.percentuais[dataIndex];
                                    const totalSetor = setoresOrdenados[dataIndex].total;
                                    const percentualSetor = totalGeralSetorGenero > 0 ? ((totalSetor / totalGeralSetorGenero) * 100).toFixed(2) : '0.00';
                                    
                                    return [
                                        `${context.dataset.label}: ${valor} dias`,
                                        `Percentual do Total: ${percentual}%`,
                                        `Total do Setor: ${totalSetor} dias (${percentualSetor}%)`
                                    ];
                                }
                            }
                        }
                    },
                    scales: {
                        y: { 
                            beginAtZero: true,
                            ticks: { 
                                font: { size: 11 },
                                stepSize: 1,
                                precision: 0
                            },
                            grid: {
                                color: 'rgba(0, 0, 0, 0.05)',
                                lineWidth: 1
                            },
                            title: {
                                display: true,
                                text: 'Dias Perdidos',
                                font: { size: 12, weight: 'bold' }
                            }
                        },
                        x: {
                            ticks: { 
                                font: { size: 11 }
                            },
                            grid: {
                                display: false
                            },
                            title: {
                                display: true,
                                text: 'Setor',
                                font: { size: 12, weight: 'bold' }
                            }
                        }
                    }
                }
            };
            break;
        
        // ==================== GRÁFICOS RODA DE OURO ====================
        case 'classificacao_funcionarios_ro':
            const top15FuncRO = dados.slice(0, 15).sort((a, b) => (b.quantidade || 0) - (a.quantidade || 0));
            config = {
                type: 'bar',
                data: {
                    labels: top15FuncRO.map(d => truncate(d.nome || 'N/A', 25)),
                    datasets: [{
                        label: 'Dias de Atestados',
                        data: top15FuncRO.map(d => d.quantidade || 0),
                        backgroundColor: function(context) {
                            const chart = context.chart;
                            const {ctx, chartArea} = chart;
                            if (!chartArea) return coresRO.preto;
                            const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
                            gradient.addColorStop(0, '#000000');
                            gradient.addColorStop(1, '#808080');
                            return gradient;
                        },
                        borderColor: coresRO.preto,
                        borderWidth: 1
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return `Dias de Atestados: ${context.parsed.x}`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: { beginAtZero: true },
                        y: { ticks: { font: { size: 11 } } }
                    }
                }
            };
            break;
        
        case 'classificacao_setores_ro':
            const top15SetoresRO = dados.slice(0, 15).sort((a, b) => (b.dias_afastamento || 0) - (a.dias_afastamento || 0));
            config = {
                type: 'bar',
                data: {
                    labels: top15SetoresRO.map(d => truncate(d.setor || 'N/A', 25)),
                    datasets: [{
                        label: 'Dias de Afastamento',
                        data: top15SetoresRO.map(d => d.dias_afastamento || 0),
                        backgroundColor: coresRO.cinza,
                        borderColor: coresRO.cinzaEscuro,
                        borderWidth: 1
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return `Dias de Afastamento: ${context.parsed.x}`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: { beginAtZero: true },
                        y: { ticks: { font: { size: 11 } } }
                    }
                }
            };
            break;
        
        case 'classificacao_doencas_ro':
            const top15DoencasRO = dados.slice(0, 15).sort((a, b) => (b.quantidade || 0) - (a.quantidade || 0));
            config = {
                type: 'bar',
                data: {
                    labels: top15DoencasRO.map(d => truncate(d.tipo_doenca || 'N/A', 30)),
                    datasets: [{
                        label: 'Dias de Afastamento',
                        data: top15DoencasRO.map(d => d.quantidade || 0),
                        backgroundColor: function(context) {
                            const chart = context.chart;
                            const {ctx, chartArea} = chart;
                            if (!chartArea) return coresRO.preto;
                            const gradient = ctx.createLinearGradient(0, chartArea.bottom, 0, chartArea.top);
                            gradient.addColorStop(0, '#000000');
                            gradient.addColorStop(1, '#808080');
                            return gradient;
                        },
                        borderColor: coresRO.preto,
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                title: function(context) {
                                    const index = context[0].dataIndex;
                                    return top15DoencasRO[index].tipo_doenca || 'N/A';
                                },
                                label: function(context) {
                                    return `Dias de Afastamento: ${context.parsed.y}`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            ticks: { maxRotation: 45, minRotation: 45, font: { size: 11 } },
                            grid: { display: false }
                        },
                        y: {
                            beginAtZero: true,
                            title: { display: true, text: 'Dias de Afastamento' }
                        }
                    }
                }
            };
            break;
        
        case 'dias_ano_coerencia':
            // Verifica se dados é objeto (formato correto)
            if (dados && typeof dados === 'object' && !Array.isArray(dados)) {
                const usarMensal = dados.meses && dados.meses.length > 0;
                const labelsCoerencia = usarMensal ? dados.meses : (dados.anos || []);
                const dadosCoerente = usarMensal ? dados.coerente_mensal : (dados.coerente || []);
                const dadosSemCoerencia = usarMensal ? dados.sem_coerencia_mensal : (dados.sem_coerencia || []);
                
                if (labelsCoerencia.length === 0) {
                    return; // Sem dados
                }
                
                // Formata labels
                const labelsFormatados = labelsCoerencia.map(label => {
                    if (label.includes('-') && label.length === 7) {
                        const [ano, mes] = label.split('-');
                        const meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];
                        const mesNum = parseInt(mes) - 1;
                        return `${meses[mesNum]}/${ano}`;
                    }
                    return label;
                });
                
                config = {
                    type: 'bar',
                    data: {
                        labels: labelsFormatados,
                        datasets: [
                            {
                                label: 'Coerente',
                                data: dadosCoerente,
                                backgroundColor: coresRO.preto,
                                borderColor: coresRO.preto,
                                borderWidth: 1
                            },
                            {
                                label: 'Sem Coerência',
                                data: dadosSemCoerencia,
                                backgroundColor: coresRO.cinza,
                                borderColor: coresRO.cinzaEscuro,
                                borderWidth: 1
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: true, position: 'top' },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        return `${context.dataset.label}: ${context.parsed.y} dias`;
                                    }
                                }
                            }
                        },
                        scales: {
                            x: { stacked: true, grid: { display: false } },
                            y: { stacked: true, beginAtZero: true }
                        }
                    }
                };
            }
            break;
        
        case 'analise_coerencia':
            // Verifica se dados é objeto e tem total > 0
            if (dados && typeof dados === 'object' && !Array.isArray(dados) && dados.total > 0) {
                config = {
                    type: 'doughnut',
                    data: {
                        labels: ['Coerente', 'Sem Coerência'],
                        datasets: [{
                            data: [dados.coerente || 0, dados.sem_coerencia || 0],
                            backgroundColor: [coresRO.preto, coresRO.cinza],
                            borderColor: ['#fff', '#fff'],
                            borderWidth: 2
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: true, position: 'bottom' },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        const label = context.label || '';
                                        const value = context.parsed || 0;
                                        const total = dados.total || 0;
                                        const percent = total > 0 ? ((value / total) * 100).toFixed(2) : 0;
                                        return `${label}: ${value} dias (${percent}%)`;
                                    }
                                }
                            }
                        }
                    }
                };
            }
            break;
        
        case 'tempo_servico_atestados':
            // Ordena por dias de afastamento (decrescente) - MESMA LÓGICA DO DASHBOARD
            const tempoOrdenado = [...dados].sort((a, b) => (b.dias_afastamento || 0) - (a.dias_afastamento || 0));
            const labelsTempo = tempoOrdenado.map(d => d.faixa_tempo_servico || 'Não informado');
            const dadosDiasTempo = tempoOrdenado.map(d => d.dias_afastamento || 0);
            config = {
                type: 'bar',
                data: {
                    labels: labelsTempo,
                    datasets: [{
                        label: 'Dias de Afastamento',
                        data: dadosDiasTempo,
                        backgroundColor: coresRO.preto,
                        borderColor: coresRO.preto,
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const index = context.dataIndex;
                                    const item = dados[index];
                                    return [
                                        `Dias de Afastamento: ${item.dias_afastamento || 0}`,
                                        `Quantidade de Atestados: ${item.quantidade_atestados || 0}`
                                    ];
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            ticks: { maxRotation: 45, minRotation: 45, font: { size: 11 } },
                            grid: { display: false }
                        },
                        y: {
                            beginAtZero: true,
                            title: { display: true, text: 'Dias de Afastamento' }
                        }
                    }
                }
            };
            break;
        
        // ==================== NOVOS GRÁFICOS DE HORAS PERDIDAS (RODA DE OURO) ====================
        case 'horas_perdidas_genero':
            // Cor dourada para feminino: #FFD700 (gold), preto para masculino
            const coresGenero = dados.map(d => d.genero === 'M' ? coresRO.preto : '#FFD700');
            config = {
                type: 'pie',
                data: {
                    labels: dados.map(d => `${d.genero_label} (${d.semanas_perdidas.toFixed(1)} semanas)`),
                    datasets: [{
                        label: 'Horas Perdidas',
                        data: dados.map(d => d.horas_perdidas),
                        backgroundColor: coresGenero,
                        borderWidth: 2,
                        borderColor: '#fff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: { padding: 15, font: { size: 12 } }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const label = context.label || '';
                                    const value = context.parsed || 0;
                                    const dataIndex = context.dataIndex;
                                    const semanas = dados[dataIndex]?.semanas_perdidas || 0;
                                    return `${label}: ${value.toFixed(1)}h (${semanas.toFixed(1)} semanas)`;
                                }
                            }
                        }
                    }
                }
            };
            break;
        
        case 'horas_perdidas_setor':
            // Ordena por horas perdidas (decrescente) - MESMA LÓGICA DO DASHBOARD
            const setoresHorasOrdenados = [...dados].sort((a, b) => (b.horas_perdidas || 0) - (a.horas_perdidas || 0));
            const top10SetoresHoras = setoresHorasOrdenados.slice(0, 10);
            config = {
                type: 'bar',
                data: {
                    labels: top10SetoresHoras.map(d => truncate(d.setor, 20)),
                    datasets: [{
                        label: 'Horas Perdidas',
                        data: top10SetoresHoras.map(d => d.horas_perdidas),
                        backgroundColor: coresRO.preto,
                        borderColor: coresRO.cinzaEscuro,
                        borderWidth: 1
                    }, {
                        label: 'Semanas Perdidas',
                        data: top10SetoresHoras.map(d => d.semanas_perdidas),
                        backgroundColor: coresRO.cinza,
                        borderColor: coresRO.cinzaEscuro,
                        borderWidth: 1,
                        yAxisID: 'y1'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'top' },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const label = context.dataset.label || '';
                                    const value = context.parsed.y || 0;
                                    if (label === 'Semanas Perdidas') {
                                        return `${label}: ${value.toFixed(1)} semanas`;
                                    }
                                    return `${label}: ${value.toFixed(1)}h`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: { display: false },
                            ticks: { maxRotation: 45, minRotation: 45 }
                        },
                        y: {
                            beginAtZero: true,
                            title: { display: true, text: 'Horas' },
                            grid: { color: '#f0f0f0' }
                        },
                        y1: {
                            type: 'linear',
                            position: 'right',
                            beginAtZero: true,
                            title: { display: true, text: 'Semanas (44h)' },
                            grid: { drawOnChartArea: false }
                        }
                    }
                }
            };
            break;
        
        case 'evolucao_mensal_horas':
            config = {
                type: 'line',
                data: {
                    labels: dados.map(d => d.mes),
                    datasets: [{
                        label: 'Horas Perdidas',
                        data: dados.map(d => d.horas_perdidas),
                        borderColor: coresRO.preto,
                        backgroundColor: coresRO.preto + '20',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4
                    }, {
                        label: 'Semanas Perdidas (44h)',
                        data: dados.map(d => d.semanas_perdidas),
                        borderColor: coresRO.cinza,
                        backgroundColor: coresRO.cinza + '20',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4,
                        yAxisID: 'y1'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'top' },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const label = context.dataset.label || '';
                                    const value = context.parsed.y || 0;
                                    if (label.includes('Semanas')) {
                                        return `${label}: ${value.toFixed(1)} semanas`;
                                    }
                                    return `${label}: ${value.toFixed(1)}h`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: { grid: { display: false } },
                        y: {
                            beginAtZero: true,
                            title: { display: true, text: 'Horas' },
                            grid: { color: '#f0f0f0' }
                        },
                        y1: {
                            type: 'linear',
                            position: 'right',
                            beginAtZero: true,
                            title: { display: true, text: 'Semanas (44h)' },
                            grid: { drawOnChartArea: false }
                        }
                    }
                }
            };
            break;
        
        case 'comparativo_dias_horas_genero':
            // Ordena: Masculino primeiro, depois ordena por dias perdidos (decrescente)
            const dadosCompOrdenados = [...dados].sort((a, b) => {
                // Primeiro: Masculino (M) vem antes de Feminino (F)
                if (a.genero === 'M' && b.genero !== 'M') return -1;
                if (a.genero !== 'M' && b.genero === 'M') return 1;
                // Se ambos são do mesmo gênero, ordena por dias perdidos (decrescente)
                return (b.dias_perdidos || 0) - (a.dias_perdidos || 0);
            });
            
            config = {
                type: 'bar',
                data: {
                    labels: dadosCompOrdenados.map(d => d.genero_label),
                    datasets: [{
                        label: 'Dias Perdidos',
                        data: dadosCompOrdenados.map(d => d.dias_perdidos),
                        backgroundColor: coresRO.preto,
                        borderColor: coresRO.cinzaEscuro,
                        borderWidth: 1
                    }, {
                        label: 'Horas Perdidas',
                        data: dadosCompOrdenados.map(d => d.horas_perdidas),
                        backgroundColor: coresRO.cinza,
                        borderColor: coresRO.cinzaEscuro,
                        borderWidth: 1,
                        yAxisID: 'y1'
                    }, {
                        label: 'Semanas Perdidas',
                        data: dadosCompOrdenados.map(d => d.semanas_perdidas),
                        backgroundColor: coresRO.cinzaClaro,
                        borderColor: coresRO.cinza,
                        borderWidth: 1,
                        yAxisID: 'y1'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'top' },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const label = context.dataset.label || '';
                                    const value = context.parsed.y || 0;
                                    if (label.includes('Semanas')) {
                                        return `${label}: ${value.toFixed(1)} semanas`;
                                    } else if (label.includes('Horas')) {
                                        return `${label}: ${value.toFixed(1)}h`;
                                    }
                                    return `${label}: ${value.toFixed(1)} dias`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: { grid: { display: false } },
                        y: {
                            beginAtZero: true,
                            title: { display: true, text: 'Dias' },
                            grid: { color: '#f0f0f0' }
                        },
                        y1: {
                            type: 'linear',
                            position: 'right',
                            beginAtZero: true,
                            title: { display: true, text: 'Horas / Semanas' },
                            grid: { drawOnChartArea: false }
                        }
                    }
                }
            };
            break;
        
        case 'analise_detalhada_genero':
            if (dados && dados.generos && Array.isArray(dados.generos)) {
                // Ordena: Masculino primeiro
                const generos = [...dados.generos].sort((a, b) => {
                    // Masculino (M) vem antes de Feminino (F)
                    if (a.genero === 'M' && b.genero !== 'M') return -1;
                    if (a.genero !== 'M' && b.genero === 'M') return 1;
                    return 0;
                });
                config = {
                    type: 'bar',
                    data: {
                        labels: generos.map(g => g.genero_label),
                        datasets: [{
                            label: 'Percentual de Dias',
                            data: generos.map(g => g.percentual_dias),
                            backgroundColor: coresRO.preto,
                            borderColor: coresRO.cinzaEscuro,
                            borderWidth: 1
                        }, {
                            label: 'Percentual de Horas',
                            data: generos.map(g => g.percentual_horas),
                            backgroundColor: coresRO.cinza,
                            borderColor: coresRO.cinzaEscuro,
                            borderWidth: 1
                        }, {
                            label: 'Percentual de Registros',
                            data: generos.map(g => g.percentual_registros),
                            backgroundColor: coresRO.cinzaClaro,
                            borderColor: coresRO.cinza,
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { position: 'top' },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        const label = context.dataset.label || '';
                                        const value = context.parsed.y || 0;
                                        return `${label}: ${value.toFixed(1)}%`;
                                    }
                                }
                            }
                        },
                        scales: {
                            x: { grid: { display: false } },
                            y: {
                                beginAtZero: true,
                                max: 100,
                                title: { display: true, text: 'Percentual (%)' },
                                grid: { color: '#f0f0f0' }
                            }
                        }
                    }
                };
            }
            break;
        
        default:
            console.warn(`[APRESENTACAO] Tipo de gráfico não reconhecido: ${tipo}`);
            // Tenta renderizar como gráfico genérico se tiver dados
            if (Array.isArray(dados) && dados.length > 0) {
                config = {
                    type: 'bar',
                    data: {
                        labels: dados.map((d, i) => d.label || d.nome || d.setor || `Item ${i + 1}`),
                        datasets: [{
                            label: 'Valor',
                            data: dados.map(d => d.quantidade || d.dias_afastamento || d.dias_perdidos || 0),
                            backgroundColor: CORES_EMPRESA.primary
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false
                    }
                };
            }
            break;
    }
    
    if (config && config.type) {
        // Destrói gráfico anterior se existir
        if (charts['chartSlide']) {
            try {
                charts['chartSlide'].destroy();
            } catch (e) {
                console.warn('[APRESENTACAO] Erro ao destruir gráfico anterior:', e);
            }
        }
        
        try {
        charts['chartSlide'] = new Chart(ctx, config);
            console.log(`[APRESENTACAO] Gráfico ${tipo} renderizado com sucesso`);
        } catch (error) {
            console.error(`[APRESENTACAO] Erro ao criar gráfico ${tipo}:`, error);
        }
    } else {
        console.warn(`[APRESENTACAO] Configuração de gráfico não criada para ${tipo}`);
    }
}

// ==================== NAVEGAÇÃO ====================
function proximoSlide() {
    if (slideAtual < slides.length - 1) {
        slideAtual++;
        renderizarSlide(slides[slideAtual]);
        atualizarBotoes();
    }
}

function slideAnterior() {
    if (slideAtual > 0) {
        slideAtual--;
        renderizarSlide(slides[slideAtual]);
        atualizarBotoes();
    }
}

function atualizarBotoes() {
    document.getElementById('btnPrev').disabled = slideAtual === 0;
    document.getElementById('btnNext').disabled = slideAtual === slides.length - 1;
}

function sairApresentacao() {
    if (confirm('Deseja sair da apresentação?')) {
        // Sai do fullscreen se estiver ativo
        if (document.fullscreenElement || document.webkitFullscreenElement || document.mozFullScreenElement || document.msFullscreenElement) {
            exitFullscreen();
        }
        window.location.href = '/';
    }
}

// ==================== FUNÇÕES DE TELA CHEIA ====================
function toggleFullscreen() {
    if (!document.fullscreenElement && !document.webkitFullscreenElement && !document.mozFullScreenElement && !document.msFullscreenElement) {
        entrarFullscreen();
    } else {
        exitFullscreen();
    }
}

function entrarFullscreen() {
    const elem = document.documentElement;
    
    if (elem.requestFullscreen) {
        elem.requestFullscreen();
    } else if (elem.webkitRequestFullscreen) {
        elem.webkitRequestFullscreen();
    } else if (elem.mozRequestFullScreen) {
        elem.mozRequestFullScreen();
    } else if (elem.msRequestFullscreen) {
        elem.msRequestFullscreen();
    }
    
    document.body.classList.add('fullscreen-mode');
}

function exitFullscreen() {
    if (document.exitFullscreen) {
        document.exitFullscreen();
    } else if (document.webkitExitFullscreen) {
        document.webkitExitFullscreen();
    } else if (document.mozCancelFullScreen) {
        document.mozCancelFullScreen();
    } else if (document.msExitFullscreen) {
        document.msExitFullscreen();
    }
    
    document.body.classList.remove('fullscreen-mode');
}

function atualizarIconeFullscreen() {
    const icon = document.getElementById('fullscreenIcon');
    const btn = document.getElementById('btnFullscreen');
    const span = btn.querySelector('span');
    
    if (document.fullscreenElement || document.webkitFullscreenElement || document.mozFullScreenElement || document.msFullscreenElement) {
        // Está em fullscreen
        if (icon) icon.className = 'fas fa-compress';
        if (span) span.textContent = 'Sair Tela Cheia';
        document.body.classList.add('fullscreen-mode');
    } else {
        // Não está em fullscreen
        if (icon) icon.className = 'fas fa-expand';
        if (span) span.textContent = 'Tela Cheia';
        document.body.classList.remove('fullscreen-mode');
    }
}

// ==================== RENDERIZAR SLIDES DE AÇÕES ====================
function renderizarAcoesIntro(tipo) {
    // Carrega conteúdo salvo do localStorage
    const conteudoSalvo = localStorage.getItem(`acoes_${tipo}`);
    const dados = conteudoSalvo ? JSON.parse(conteudoSalvo) : {
        texto: "INTERVENÇÕES JUNTO<br>AOS COLABORADORES"
    };
    
    // Obtém cores do cliente
    const cores = getCoresApresentacao();
    const corPrimaria = cores.primary || '#1a237e';
    const corSecundaria = cores.secondary || '#556B2F';
    
    return `
        <div style="display: flex; flex-direction: column; height: 100%; padding: 40px; padding-bottom: 0;">
            <!-- Linha decorativa no topo -->
            <div style="height: 3px; background: linear-gradient(to right, ${corSecundaria} 0%, ${corPrimaria} 50%, ${corSecundaria} 100%); margin-bottom: 30px;"></div>
            
            <div style="flex: 1; display: flex; align-items: center; justify-content: center; position: relative; min-height: 500px;">
                <!-- Texto editável centralizado -->
                <div style="text-align: center; background: linear-gradient(135deg, ${corSecundaria}, ${corPrimaria}); color: white; padding: 60px 80px; border-radius: 16px; box-shadow: 0 8px 24px rgba(0,0,0,0.25); border: 3px solid rgba(255,255,255,0.2); max-width: 800px;">
                    <div id="textoAcoesIntro" class="conteudo-editavel" contenteditable="false" style="font-size: 40px; font-weight: 700; margin: 0; line-height: 1.4; outline: none; min-height: 90px; text-shadow: 0 2px 4px rgba(0,0,0,0.2); letter-spacing: 2px;">${dados.texto}</div>
                </div>
            </div>
        </div>
    `;
}

async function renderizarFooterAcoes() {
    // Busca dados do cliente atual
    let clienteInfo = {
        nome: 'Empresa',
        nome_fantasia: '',
        logo_url: null
    };
    
    const clientId = typeof window.getCurrentClientId === 'function' ? window.getCurrentClientId(null) : null;
    if (clientId) {
        try {
            const response = await fetch(`/api/clientes/${clientId}`);
            if (response.ok) {
                const cliente = await response.json();
                clienteInfo = {
                    nome: cliente.nome || 'Empresa',
                    nome_fantasia: cliente.nome_fantasia || cliente.nome || 'Empresa',
                    logo_url: cliente.logo_url || null
                };
            }
        } catch (error) {
            console.error('Erro ao buscar dados do cliente para footer:', error);
        }
    }
    
    // Obtém cores do cliente
    const cores = getCoresApresentacao();
    const corPrimaria = cores.primary || '#1a237e';
    const corSecundaria = cores.secondary || '#556B2F';
    
    // Gera nome da empresa para exibição
    const nomeExibicao = clienteInfo.nome_fantasia || clienteInfo.nome || 'Empresa';
    const iniciais = gerarIniciaisCapa(nomeExibicao);
    
    // Renderiza logo ou iniciais
    // Para RODA DE OURO (client_id = 4): retangular (64px altura x 128px largura)
    // Para outras empresas: mantém formato original
    const isRodaOuro = clientId === 4;
    
    let logoHTML = '';
    if (clienteInfo.logo_url) {
        // Adiciona timestamp para evitar cache
        const logoUrlComCache = clienteInfo.logo_url + (clienteInfo.logo_url.includes('?') ? '&' : '?') + '_t=' + Date.now();
        
        if (isRodaOuro) {
            // RODA DE OURO: formato HORIZONTAL/RETANGULAR FORÇADO (120px altura x 360px largura) - 3:1 HORIZONTAL
            logoHTML = `
                <div style="display: flex !important; align-items: center !important; justify-content: center !important; gap: 0 !important; flex-shrink: 0 !important; margin-bottom: 0 !important; height: 120px !important; width: 360px !important; min-width: 360px !important; max-width: 360px !important; min-height: 120px !important; max-height: 120px !important; aspect-ratio: 3 / 1 !important; overflow: hidden !important; background: transparent !important; box-sizing: border-box !important;">
                    <img src="${logoUrlComCache}" alt="${nomeExibicao}" style="width: 360px !important; height: 120px !important; max-width: 360px !important; max-height: 120px !important; aspect-ratio: 3 / 1 !important; object-fit: contain !important; object-position: center !important; display: block !important;">
                </div>
            `;
        } else {
            // Converplast e outras: formato original (aumentado)
            logoHTML = `
                <div style="display: flex; align-items: center; gap: 0; flex-shrink: 0; margin-bottom: 0;">
                    <img src="${logoUrlComCache}" alt="${nomeExibicao}" style="max-height: 200px; max-width: 800px; object-fit: contain;">
                </div>
            `;
        }
    } else {
        if (isRodaOuro) {
            // RODA DE OURO: nome completo em formato HORIZONTAL (100px altura x 300px largura)
            const tamanhoFonte = nomeExibicao.length > 20 ? 16 : (nomeExibicao.length > 15 ? 18 : 20);
            logoHTML = `
                <div style="display: flex !important; align-items: center !important; justify-content: center !important; flex-shrink: 0 !important; margin-bottom: 0 !important; height: 100px !important; width: 300px !important; min-width: 300px !important; max-width: 300px !important; background: ${corPrimaria} !important; border-radius: 4px !important; padding: 8px 12px !important; box-sizing: border-box !important; overflow: hidden !important;">
                    <span style="font-size: ${tamanhoFonte}px; font-weight: 700; color: white; letter-spacing: 0.5px; line-height: 1.2; text-align: center; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; text-overflow: ellipsis; word-break: break-word; max-width: 100%;">${nomeExibicao}</span>
                </div>
            `;
        } else {
            // Converplast e outras: iniciais no formato original (aumentado)
            logoHTML = `
                <div style="display: flex; align-items: center; gap: 4px; flex-shrink: 0; margin-bottom: 0;">
                    <span style="font-size: 192px; font-weight: 700; color: ${corPrimaria}; letter-spacing: 1px; line-height: 1;">${iniciais}</span>
                </div>
            `;
        }
    }
    
    // Para RODA DE OURO: remove o logo, mostra apenas a faixa (sem sobrepor barra de rolagem)
    if (isRodaOuro) {
        return `
            <div style="position: absolute; bottom: 0; left: 0; right: 17px; height: 60px; display: flex; align-items: center; justify-content: flex-end; padding: 0 40px 0 40px; gap: 20px; z-index: 10; box-sizing: border-box;">
                <!-- Barra gradiente (apenas a faixa, sem logo) - não sobrepõe barra de rolagem -->
                <div style="flex: 1; height: 32px; background: linear-gradient(to right, ${corSecundaria} 0%, ${corPrimaria} 50%, ${corSecundaria} 100%);"></div>
            </div>
        `;
    }
    
    // Para outras empresas: mostra logo + faixa
    return `
        <div style="position: absolute; bottom: 0; left: 0; right: 0; height: 60px; display: flex; align-items: center; justify-content: flex-end; padding: 0 40px; gap: 20px; z-index: 10; padding-right: 200px;">
            <!-- Barra gradiente que vai até o limite do nome -->
            <div style="flex: 1; height: 32px; background: linear-gradient(to right, ${corSecundaria} 0%, ${corPrimaria} 50%, ${corSecundaria} 100%); margin-right: 20px;"></div>
            
            <!-- Logo da empresa (à direita, acima da barra) -->
            ${logoHTML}
        </div>
    `;
}

function renderizarAcoesSaudeFisica(tipo) {
    // Carrega conteúdo salvo do localStorage
    const conteudoSalvo = localStorage.getItem(`acoes_${tipo}`);
    const dados = conteudoSalvo ? JSON.parse(conteudoSalvo) : {
        texto: "A saúde deve ser compreendida, primordialmente, como uma responsabilidade individual. Nesse sentido, este eixo tem como foco a promoção da saúde preventiva, por meio da disseminação de informações, orientações e ações que estimulem a adoção de hábitos saudáveis. Busca-se, assim, fortalecer o autocuidado e proporcionar uma melhoria contínua na qualidade de vida, abaixo algumas ações:",
        acoes: [
            "Alimentação saudável;",
            "Atividade Física;",
            "Qualidade do sono;",
            "Comportamento preventivo e cuidados médicos/saúde;",
            "Álcool e tabagismo;",
            "Exames periódicos;",
            "Programa de acompanhamento e monitoramento em saúde;",
            "Grupos de interesse;",
            "Campanhas de vacinação, segurança no trabalho e afastamento;"
        ]
    };
    
    // Obtém cores do cliente
    const cores = getCoresApresentacao();
    const corPrimaria = cores.primary || '#1a237e';
    const corSecundaria = cores.secondary || '#556B2F';
    
    const acoesHTML = dados.acoes.map(acao => `
        <li class="acao-item" style="padding: 12px 0; padding-left: 30px; position: relative; font-size: 16px; line-height: 1.8; color: #333; border-bottom: 1px solid #f0f0f0;">
            <span style="position: absolute; left: 0; color: ${corSecundaria}; font-weight: bold;">•</span>
            <span class="conteudo-editavel" contenteditable="false" style="outline: none;">${acao}</span>
        </li>
    `).join('');
    
    return `
        <div style="display: flex; flex-direction: column; height: 100%; padding: 40px; padding-bottom: 0;">
            <!-- Linha decorativa no topo -->
            <div style="height: 3px; background: linear-gradient(to right, ${corSecundaria} 0%, ${corPrimaria} 50%, ${corSecundaria} 100%); margin-bottom: 30px;"></div>
            
            <!-- Tabs -->
            <div style="display: flex; gap: 8px; margin-bottom: 30px; border-bottom: 3px solid ${corSecundaria};">
                <div style="background: ${corSecundaria}; color: white; padding: 12px 24px; border-radius: 8px 8px 0 0; font-weight: 600; font-size: 14px;">
                    SAÚDE FÍSICA
                </div>
                <div style="background: white; color: ${corPrimaria}; padding: 12px 24px; border: 2px dashed #dee2e6; border-bottom: none; border-radius: 8px 8px 0 0; font-weight: 500; font-size: 14px; cursor: pointer;">
                    SAÚDE EMOCIONAL
                </div>
                <div style="background: white; color: ${corPrimaria}; padding: 12px 24px; border: 2px dashed #dee2e6; border-bottom: none; border-radius: 8px 8px 0 0; font-weight: 500; font-size: 14px; cursor: pointer;">
                    SAÚDE SOCIAL
                </div>
            </div>
            
            <!-- Conteúdo -->
            <div style="flex: 1; overflow-y: auto; padding-right: 20px; padding-bottom: 60px; margin-bottom: 0;">
                <p class="conteudo-editavel" id="textoAcoesSaudeFisica" contenteditable="false" style="font-size: 16px; line-height: 1.8; color: #333; margin-bottom: 30px; text-align: justify; outline: none; min-height: 100px;">${dados.texto}</p>
                
                <ul id="listaAcoesSaudeFisica" style="list-style: none; padding: 0; margin: 0;">
                    ${acoesHTML}
                </ul>
            </div>
        </div>
    `;
}

function renderizarAcoesSaudeEmocional(tipo) {
    // Carrega conteúdo salvo do localStorage
    const conteudoSalvo = localStorage.getItem(`acoes_${tipo}`);
    const dados = conteudoSalvo ? JSON.parse(conteudoSalvo) : {
        texto: "A saúde emocional refere-se à capacidade de gerenciar sentimentos, enfrentar desafios e manter o equilíbrio psicológico. Este eixo visa promover o bem-estar emocional através de ações que fortaleçam a resiliência, a inteligência emocional e o suporte psicossocial. Abaixo algumas ações:",
        acoes: [
            "Gestão do estresse e ansiedade;",
            "Programas de mindfulness e relaxamento;",
            "Acompanhamento psicológico e suporte emocional;",
            "Treinamento em inteligência emocional;",
            "Espaços de escuta e acolhimento;",
            "Prevenção e combate ao assédio moral;",
            "Balanceamento entre vida pessoal e profissional;",
            "Programas de desenvolvimento pessoal;",
            "Campanhas de conscientização sobre saúde mental;"
        ]
    };
    
    // Obtém cores do cliente
    const cores = getCoresApresentacao();
    const corPrimaria = cores.primary || '#1a237e';
    const corSecundaria = cores.secondary || '#556B2F';
    
    const acoesHTML = dados.acoes.map(acao => `
        <li class="acao-item" style="padding: 12px 0; padding-left: 30px; position: relative; font-size: 16px; line-height: 1.8; color: #333; border-bottom: 1px solid #f0f0f0;">
            <span style="position: absolute; left: 0; color: ${corSecundaria}; font-weight: bold;">•</span>
            <span class="conteudo-editavel" contenteditable="false" style="outline: none;">${acao}</span>
        </li>
    `).join('');
    
    return `
        <div style="display: flex; flex-direction: column; height: 100%; padding: 40px; padding-bottom: 0;">
            <!-- Linha decorativa no topo -->
            <div style="height: 3px; background: linear-gradient(to right, ${corSecundaria} 0%, ${corPrimaria} 50%, ${corSecundaria} 100%); margin-bottom: 30px;"></div>
            
            <!-- Tabs -->
            <div style="display: flex; gap: 8px; margin-bottom: 30px; border-bottom: 3px solid ${corSecundaria};">
                <div style="background: white; color: ${corPrimaria}; padding: 12px 24px; border: 2px dashed #dee2e6; border-bottom: none; border-radius: 8px 8px 0 0; font-weight: 500; font-size: 14px; cursor: pointer;">
                    SAÚDE FÍSICA
                </div>
                <div style="background: ${corSecundaria}; color: white; padding: 12px 24px; border-radius: 8px 8px 0 0; font-weight: 600; font-size: 14px;">
                    SAÚDE EMOCIONAL
                </div>
                <div style="background: white; color: ${corPrimaria}; padding: 12px 24px; border: 2px dashed #dee2e6; border-bottom: none; border-radius: 8px 8px 0 0; font-weight: 500; font-size: 14px; cursor: pointer;">
                    SAÚDE SOCIAL
                </div>
            </div>
            
            <!-- Conteúdo -->
            <div style="flex: 1; overflow-y: auto; padding-right: 20px; padding-bottom: 60px; margin-bottom: 0;">
                <p class="conteudo-editavel" id="textoAcoesSaudeEmocional" contenteditable="false" style="font-size: 16px; line-height: 1.8; color: #333; margin-bottom: 30px; text-align: justify; outline: none; min-height: 100px;">${dados.texto}</p>
                
                <ul id="listaAcoesSaudeEmocional" style="list-style: none; padding: 0; margin: 0;">
                    ${acoesHTML}
                </ul>
            </div>
        </div>
    `;
}

function renderizarAcoesSaudeSocial(tipo) {
    // Carrega conteúdo salvo do localStorage
    const conteudoSalvo = localStorage.getItem(`acoes_${tipo}`);
    const dados = conteudoSalvo ? JSON.parse(conteudoSalvo) : {
        texto: "A saúde social está relacionada à qualidade das relações interpessoais, à integração no ambiente de trabalho e à construção de um ambiente colaborativo e respeitoso. Este eixo busca fortalecer os vínculos sociais e promover um clima organizacional saudável. Abaixo algumas ações:",
        acoes: [
            "Programas de integração e acolhimento;",
            "Atividades de team building;",
            "Comunicação eficaz e transparente;",
            "Resolução de conflitos;",
            "Valorização da diversidade e inclusão;",
            "Eventos sociais e culturais;",
            "Grupos de trabalho colaborativos;",
            "Programas de reconhecimento e valorização;",
            "Espaços de convivência e interação;"
        ]
    };
    
    // Obtém cores do cliente
    const cores = getCoresApresentacao();
    const corPrimaria = cores.primary || '#1a237e';
    const corSecundaria = cores.secondary || '#556B2F';
    
    const acoesHTML = dados.acoes.map(acao => `
        <li class="acao-item" style="padding: 12px 0; padding-left: 30px; position: relative; font-size: 16px; line-height: 1.8; color: #333; border-bottom: 1px solid #f0f0f0;">
            <span style="position: absolute; left: 0; color: ${corSecundaria}; font-weight: bold;">•</span>
            <span class="conteudo-editavel" contenteditable="false" style="outline: none;">${acao}</span>
        </li>
    `).join('');
    
    return `
        <div style="display: flex; flex-direction: column; height: 100%; padding: 40px; padding-bottom: 0;">
            <!-- Linha decorativa no topo -->
            <div style="height: 3px; background: linear-gradient(to right, ${corSecundaria} 0%, ${corPrimaria} 50%, ${corSecundaria} 100%); margin-bottom: 30px;"></div>
            
            <!-- Tabs -->
            <div style="display: flex; gap: 8px; margin-bottom: 30px; border-bottom: 3px solid ${corSecundaria};">
                <div style="background: white; color: ${corPrimaria}; padding: 12px 24px; border: 2px dashed #dee2e6; border-bottom: none; border-radius: 8px 8px 0 0; font-weight: 500; font-size: 14px; cursor: pointer;">
                    SAÚDE FÍSICA
                </div>
                <div style="background: white; color: ${corPrimaria}; padding: 12px 24px; border: 2px dashed #dee2e6; border-bottom: none; border-radius: 8px 8px 0 0; font-weight: 500; font-size: 14px; cursor: pointer;">
                    SAÚDE EMOCIONAL
                </div>
                <div style="background: ${corSecundaria}; color: white; padding: 12px 24px; border-radius: 8px 8px 0 0; font-weight: 600; font-size: 14px;">
                    SAÚDE SOCIAL
                </div>
            </div>
            
            <!-- Conteúdo -->
            <div style="flex: 1; overflow-y: auto; padding-right: 20px; padding-bottom: 60px; margin-bottom: 0;">
                <p class="conteudo-editavel" id="textoAcoesSaudeSocial" contenteditable="false" style="font-size: 16px; line-height: 1.8; color: #333; margin-bottom: 30px; text-align: justify; outline: none; min-height: 100px;">${dados.texto}</p>
                
                <ul id="listaAcoesSaudeSocial" style="list-style: none; padding: 0; margin: 0;">
                    ${acoesHTML}
                </ul>
            </div>
        </div>
    `;
}

// ==================== PRODUTIVIDADE ====================
function renderizarProdutividade(slide) {
    const dados = slide.dados || [];
    
    if (!dados || dados.length === 0) {
        return '<div class="empty-state"><p>Nenhum dado de produtividade disponível</p></div>';
    }
    
    let html = '';
    
    // Layout com 3 gráficos: 2 em cima (lado a lado) e 1 embaixo (linha de evolução mensal)
    html = `<div style="display: flex; flex-direction: column; gap: 24px; height: 100%;">`;
    // Primeira linha: dois gráficos lado a lado
    html += `<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; flex: 1;">`;
    html += `<div><canvas id="chartProdutividadeCategoriaAgendadosFaltas"></canvas></div>`;
    html += `<div><canvas id="chartProdutividadeMensalCategoria"></canvas></div>`;
    html += `</div>`;
    // Segunda linha: gráfico de linha de evolução mensal
    html += `<div style="flex: 1; min-height: 300px;">`;
    html += `<canvas id="graficoEvolucaoProdutividade"></canvas>`;
    html += `</div>`;
    html += `</div>`;
    
    // Renderiza gráficos após o HTML ser inserido
    setTimeout(() => {
        renderizarGraficoProdutividadeCategoriaAgendadosFaltas(dados);
        renderizarGraficoProdutividadeMensalCategoria(dados);
        renderizarGraficoEvolucaoMensal('line'); // Gráfico de linha de evolução mensal
    }, 100);
    
    return html;
}

// ==================== GRÁFICO PRODUTIVIDADE POR CATEGORIA (AGENDADOS/FALTAS) ====================
function renderizarGraficoProdutividadeCategoriaAgendadosFaltas(dados) {
    const ctx = document.getElementById('chartProdutividadeCategoriaAgendadosFaltas');
    if (!ctx || !dados || dados.length === 0) return;
    
    if (charts['produtividade_categoria_agendados_faltas']) {
        charts['produtividade_categoria_agendados_faltas'].destroy();
    }
    
    // Agrupa por mês
    const dadosPorMes = {};
    dados.forEach(d => {
        const mesRef = d.mes_referencia || 'sem-mes';
        if (!dadosPorMes[mesRef]) {
            dadosPorMes[mesRef] = [];
        }
        dadosPorMes[mesRef].push(d);
    });
    
    // Calcula totais de Agendados e Faltas por categoria (soma de todos os meses)
    const totaisAgendados = {
        ocupacionais: 0, assistenciais: 0, acidente_trabalho: 0, inss: 0,
        sinistralidade: 0, absenteismo: 0, pericia_indireta: 0
    };
    
    const totaisFaltas = {
        ocupacionais: 0, assistenciais: 0, acidente_trabalho: 0, inss: 0,
        sinistralidade: 0, absenteismo: 0, pericia_indireta: 0
    };
    
    Object.values(dadosPorMes).forEach(dadosMes => {
        const agendados = dadosMes.find(d => d.tipo_consulta === 'Agendados');
        const compareceram = dadosMes.find(d => d.tipo_consulta === 'Compareceram');
        
        if (agendados) {
            totaisAgendados.ocupacionais += (agendados.ocupacionais || 0);
            totaisAgendados.assistenciais += (agendados.assistenciais || 0);
            totaisAgendados.acidente_trabalho += (agendados.acidente_trabalho || 0);
            totaisAgendados.inss += (agendados.inss || 0);
            totaisAgendados.sinistralidade += (agendados.sinistralidade || 0);
            totaisAgendados.absenteismo += (agendados.absenteismo || 0);
            totaisAgendados.pericia_indireta += (agendados.pericia_indireta || 0);
        }
        
        if (agendados && compareceram) {
            totaisFaltas.ocupacionais += Math.max(0, (agendados.ocupacionais || 0) - (compareceram.ocupacionais || 0));
            totaisFaltas.assistenciais += Math.max(0, (agendados.assistenciais || 0) - (compareceram.assistenciais || 0));
            totaisFaltas.acidente_trabalho += Math.max(0, (agendados.acidente_trabalho || 0) - (compareceram.acidente_trabalho || 0));
            totaisFaltas.inss += Math.max(0, (agendados.inss || 0) - (compareceram.inss || 0));
            totaisFaltas.sinistralidade += Math.max(0, (agendados.sinistralidade || 0) - (compareceram.sinistralidade || 0));
            totaisFaltas.absenteismo += Math.max(0, (agendados.absenteismo || 0) - (compareceram.absenteismo || 0));
            totaisFaltas.pericia_indireta += Math.max(0, (agendados.pericia_indireta || 0) - (compareceram.pericia_indireta || 0));
        }
    });
    
    const totaisCompareceram = {
        ocupacionais: totaisAgendados.ocupacionais - totaisFaltas.ocupacionais,
        assistenciais: totaisAgendados.assistenciais - totaisFaltas.assistenciais,
        acidente_trabalho: totaisAgendados.acidente_trabalho - totaisFaltas.acidente_trabalho,
        inss: totaisAgendados.inss - totaisFaltas.inss,
        sinistralidade: totaisAgendados.sinistralidade - totaisFaltas.sinistralidade,
        absenteismo: totaisAgendados.absenteismo - totaisFaltas.absenteismo,
        pericia_indireta: totaisAgendados.pericia_indireta - totaisFaltas.pericia_indireta
    };
    
    const meses = Object.keys(dadosPorMes).sort();
    let periodoTexto = '';
    if (meses.length > 0) {
        const mesMaisRecente = meses[meses.length - 1];
        const [ano, mes] = mesMaisRecente.split('-');
        const mesesNomes = {
            '01': 'Janeiro', '02': 'Fevereiro', '03': 'Março', '04': 'Abril',
            '05': 'Maio', '06': 'Junho', '07': 'Julho', '08': 'Agosto',
            '09': 'Setembro', '10': 'Outubro', '11': 'Novembro', '12': 'Dezembro'
        };
        periodoTexto = `Ano ${ano} até ${mesesNomes[mes] || mes}`;
    }
    
    const categorias = [
        { nome: 'Ocupacionais', key: 'ocupacionais' },
        { nome: 'Assistenciais', key: 'assistenciais' },
        { nome: 'Acidente de Trabalho', key: 'acidente_trabalho' },
        { nome: 'INSS', key: 'inss' },
        { nome: 'Sinistralidade', key: 'sinistralidade' },
        { nome: 'Absenteísmo', key: 'absenteismo' },
        { nome: 'Perícia Indireta', key: 'pericia_indireta' }
    ];
    
    categorias.sort((a, b) => {
        const totalA = totaisAgendados[a.key] || 0;
        const totalB = totaisAgendados[b.key] || 0;
        return totalB - totalA;
    });
    
    const labelsOrdenados = categorias.map(c => c.nome);
    const dataCompareceram = categorias.map(c => Math.max(0, totaisCompareceram[c.key]));
    const dataFaltas = categorias.map(c => totaisFaltas[c.key]);
    
    charts['produtividade_categoria_agendados_faltas'] = new Chart(ctx, {
        type: 'bar',
                data: {
            labels: labelsOrdenados,
            datasets: [
                {
                    label: 'Compareceram',
                    data: dataCompareceram,
                    backgroundColor: getCoresApresentacao().primary || '#0056b3',
                    borderRadius: { topLeft: 6, topRight: 6, bottomLeft: 0, bottomRight: 0 }
                },
                {
                    label: 'Faltas',
                    data: dataFaltas,
                    backgroundColor: getCoresApresentacao().secondary || '#dc3545',
                    borderRadius: { topLeft: 0, topRight: 0, bottomLeft: 6, bottomRight: 6 }
                }
            ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                title: {
                    display: true,
                    text: periodoTexto || 'Produtividade - Consultas por Categoria',
                    font: { size: 14, weight: 'bold' },
                    padding: { top: 10, bottom: 20 }
                },
                        legend: { 
                    display: true,
                    position: 'top',
                    labels: { font: { size: 11 }, usePointStyle: true, padding: 12 }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.dataset.label || '';
                            const value = context.parsed.y || 0;
                            const index = context.dataIndex;
                            const categoriaKey = categorias[index].key;
                            const total = totaisAgendados[categoriaKey];
                            const percent = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                            return `${label}: ${value} consultas (${percent}%)`;
                        },
                        footer: function(tooltipItems) {
                            if (tooltipItems.length > 0) {
                                const index = tooltipItems[0].dataIndex;
                                const categoriaKey = categorias[index].key;
                                const total = totaisAgendados[categoriaKey];
                                const compareceram = totaisCompareceram[categoriaKey];
                                const faltas = totaisFaltas[categoriaKey];
                                const percentCompareceram = total > 0 ? ((compareceram / total) * 100).toFixed(1) : 0;
                                const percentFaltas = total > 0 ? ((faltas / total) * 100).toFixed(1) : 0;
                                return [
                                    `Total Agendados: ${total} consultas`,
                                    `Comparecimento: ${percentCompareceram}%`,
                                    `Faltas: ${percentFaltas}%`
                                ];
                            }
                            return '';
                        }
                    }
                }
            },
            scales: {
                y: { 
                    beginAtZero: true,
                    stacked: true,
                    ticks: { font: { size: 10 }, stepSize: 5 }
                },
                x: { 
                    stacked: true,
                    ticks: { font: { size: 10 } },
                    grid: { display: false }
                }
            }
        }
    });
}

// ==================== GRÁFICO PRODUTIVIDADE MENSAL POR CATEGORIA ====================
function renderizarGraficoProdutividadeMensalCategoria(dados) {
    const ctx = document.getElementById('chartProdutividadeMensalCategoria');
    if (!ctx || !dados || dados.length === 0) return;
    
    if (charts['produtividade_mensal_categoria']) {
        charts['produtividade_mensal_categoria'].destroy();
    }
    
    // Agrupa por mês (dados anuais mês a mês)
    const dadosPorMes = {};
    dados.forEach(d => {
        const mesRef = d.mes_referencia || 'sem-mes';
        if (!dadosPorMes[mesRef]) {
            dadosPorMes[mesRef] = [];
        }
        dadosPorMes[mesRef].push(d);
    });
    
    const mesesOrdenados = Object.keys(dadosPorMes).sort();
    
    // Formata labels de mês
    const mesesNomes = {
        '01': 'Jan', '02': 'Fev', '03': 'Mar', '04': 'Abr',
        '05': 'Mai', '06': 'Jun', '07': 'Jul', '08': 'Ago',
        '09': 'Set', '10': 'Out', '11': 'Nov', '12': 'Dez'
    };
    
    const labels = mesesOrdenados.map(mesRef => {
        const [ano, mes] = mesRef.split('-');
        return `${mesesNomes[mes] || mes}/${ano}`;
    });
    
    // Gera gradiente de cores baseado nas cores do cliente
    const cores = getCoresApresentacao();
    const paleta = getPaletaApresentacao();
    
    const categorias = [
        { nome: 'Ocupacionais', key: 'ocupacionais', cor: cores.primary },
        { nome: 'Assistenciais', key: 'assistenciais', cor: cores.primaryLight },
        { nome: 'Acidente de Trabalho', key: 'acidente_trabalho', cor: paleta[2] || cores.primaryDark },
        { nome: 'INSS', key: 'inss', cor: paleta[3] || cores.secondaryLight },
        { nome: 'Sinistralidade', key: 'sinistralidade', cor: paleta[4] || cores.secondary },
        { nome: 'Absenteísmo', key: 'absenteismo', cor: cores.secondary },
        { nome: 'Perícia Indireta', key: 'pericia_indireta', cor: cores.secondaryDark }
    ];
    
    const datasets = categorias.map(categoria => {
        const data = mesesOrdenados.map(mesRef => {
            const dadosMes = dadosPorMes[mesRef];
            const agendados = dadosMes.find(d => d.tipo_consulta === 'Agendados');
            return agendados ? (agendados[categoria.key] || 0) : 0;
        });
        
        return {
            label: categoria.nome,
            data: data,
            backgroundColor: categoria.cor,
            borderRadius: 4
        };
    });
    
    charts['produtividade_mensal_categoria'] = new Chart(ctx, {
        type: 'bar',
                data: {
            labels: labels,
            datasets: datasets
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                title: {
                    display: true,
                    text: 'Produtividade - Distribuição Anual (Mês a Mês) por Categoria',
                    font: { size: 14, weight: 'bold' },
                    padding: { top: 10, bottom: 20 }
                },
                        legend: {
                    display: true,
                    position: 'top',
                    labels: { font: { size: 10 }, usePointStyle: true, padding: 10 }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.dataset.label || '';
                            const value = context.parsed.y || 0;
                            const mesIndex = context.dataIndex;
                            const mesRef = mesesOrdenados[mesIndex];
                            const dadosMes = dadosPorMes[mesRef];
                            const agendados = dadosMes.find(d => d.tipo_consulta === 'Agendados');
                            
                            let totalMes = 0;
                            if (agendados) {
                                categorias.forEach(cat => {
                                    totalMes += (agendados[cat.key] || 0);
                                });
                            }
                            
                            const percent = totalMes > 0 ? ((value / totalMes) * 100).toFixed(1) : 0;
                            return `${label}: ${value} consultas (${percent}%)`;
                        },
                        footer: function(tooltipItems) {
                            if (tooltipItems.length > 0) {
                                const mesIndex = tooltipItems[0].dataIndex;
                                const mesRef = mesesOrdenados[mesIndex];
                                const dadosMes = dadosPorMes[mesRef];
                                const agendados = dadosMes.find(d => d.tipo_consulta === 'Agendados');
                                
                                let totalMes = 0;
                                if (agendados) {
                                    categorias.forEach(cat => {
                                        totalMes += (agendados[cat.key] || 0);
                                    });
                                }
                                
                                return `Total do Mês: ${totalMes} consultas`;
                            }
                            return '';
                        }
                    }
                }
            },
            scales: {
                x: {
                    stacked: true,
                    ticks: { font: { size: 10 } },
                    grid: { display: false }
                },
                y: {
                    stacked: true,
                    beginAtZero: true,
                    ticks: { font: { size: 10 }, stepSize: 5 },
                    title: {
                        display: true,
                        text: 'Quantidade de Consultas',
                        font: { size: 11, weight: 'bold' }
                    }
                }
            }
        }
    });
}

function renderizarGraficoEvolucaoMensal(tipoGrafico) {
    // Busca dados dos últimos 12 meses usando a nova API
    const clientId = typeof window.getCurrentClientId === 'function' ? window.getCurrentClientId(null) : null;
    if (!clientId) return;
    
    fetch(`/api/produtividade/evolucao?client_id=${clientId}&agrupar_por=mes`)
        .then(response => response.json())
        .then(data => {
            const dadosAgregados = data.data || [];
            
            // Pega últimos 12 meses
            const dadosRecentes = dadosAgregados.slice(-12);
            
            // Formata labels
            const meses = {
                '01': 'Jan', '02': 'Fev', '03': 'Mar', '04': 'Abr',
                '05': 'Mai', '06': 'Jun', '07': 'Jul', '08': 'Ago',
                '09': 'Set', '10': 'Out', '11': 'Nov', '12': 'Dez'
            };
            
            const labels = dadosRecentes.map(d => {
                if (d.periodo && d.periodo.includes('-')) {
                    const [ano, mes] = d.periodo.split('-');
                    return `${meses[mes] || mes}/${ano.slice(-2)}`;
                }
                return d.periodo;
            });
            
            const dadosEvolucao = {
                ocupacionais: dadosRecentes.map(d => d.ocupacionais || 0),
                assistenciais: dadosRecentes.map(d => d.assistenciais || 0),
                acidente_trabalho: dadosRecentes.map(d => d.acidente_trabalho || 0),
                inss: dadosRecentes.map(d => d.inss || 0),
                absenteismo: dadosRecentes.map(d => d.absenteismo || 0),
                total: dadosRecentes.map(d => d.total || 0)
            };
            
            setTimeout(() => {
                const ctx = document.getElementById('graficoEvolucaoProdutividade');
                if (ctx && !charts['produtividade_evolucao']) {
                    const isArea = tipoGrafico === 'area';
                    charts['produtividade_evolucao'] = new Chart(ctx, {
                        type: isArea ? 'line' : tipoGrafico,
                        data: {
                            labels: labels,
                            datasets: [
                                {
                                    label: 'Ocupacionais',
                                    data: dadosEvolucao.ocupacionais,
                                    borderColor: CORES_EMPRESA.primary,
                                    backgroundColor: isArea ? (CORES_EMPRESA.primary + '33') : CORES_EMPRESA.primary,
                                    fill: isArea,
                                    tension: 0.4
                                },
                                {
                                    label: 'Assistenciais',
                                    data: dadosEvolucao.assistenciais,
                                    borderColor: CORES_EMPRESA.secondary,
                                    backgroundColor: isArea ? (CORES_EMPRESA.secondary + '33') : CORES_EMPRESA.secondary,
                                    fill: isArea,
                                    tension: 0.4
                                },
                                {
                                    label: 'Acidente de Trabalho',
                                    data: dadosEvolucao.acidente_trabalho,
                                    borderColor: '#ff9800',
                                    backgroundColor: isArea ? 'rgba(255, 152, 0, 0.2)' : '#ff9800',
                                    fill: isArea,
                                    tension: 0.4
                                },
                                {
                                    label: 'INSS',
                                    data: dadosEvolucao.inss,
                                    borderColor: '#9c27b0',
                                    backgroundColor: isArea ? 'rgba(156, 39, 176, 0.2)' : '#9c27b0',
                                    fill: isArea,
                                    tension: 0.4
                                },
                                {
                                    label: 'Absenteísmo',
                                    data: dadosEvolucao.absenteismo,
                                    borderColor: '#f44336',
                                    backgroundColor: isArea ? 'rgba(244, 67, 54, 0.2)' : '#f44336',
                                    fill: isArea,
                                    tension: 0.4
                                }
                            ]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: {
                                    position: 'bottom'
                                }
                            },
                            scales: {
                                y: { beginAtZero: true }
                            }
                        }
                    });
                }
            }, 100);
        })
        .catch(error => {
            console.error('Erro ao carregar dados de evolução:', error);
        });
}

// ==================== EDIÇÃO DE AÇÕES ====================
let modoEdicaoAcoes = false;

function toggleEdicaoAcoes(tipo) {
    modoEdicaoAcoes = !modoEdicaoAcoes;
    const editaveis = document.querySelectorAll('.conteudo-editavel');
    const btnEditar = document.getElementById('btnEditarAcoes');
    const btnSalvar = document.getElementById('btnSalvarAcoes');
    
    // Obtém cores do cliente para borda de edição
    const cores = getCoresApresentacao();
    const corSecundaria = cores.secondary || '#556B2F';
    
    editaveis.forEach(el => {
        el.contentEditable = modoEdicaoAcoes;
        if (modoEdicaoAcoes) {
            el.style.border = `2px dashed ${corSecundaria}`;
            el.style.borderRadius = '4px';
            el.style.padding = '4px';
            el.style.backgroundColor = '#f9f9f9';
        } else {
            el.style.border = 'none';
            el.style.padding = '0';
            el.style.backgroundColor = 'transparent';
        }
    });
    
    if (modoEdicaoAcoes) {
        btnEditar.style.display = 'none';
        btnSalvar.style.display = 'flex';
    } else {
        btnEditar.style.display = 'flex';
        btnSalvar.style.display = 'none';
    }
}

function salvarAcoes(tipo) {
    const dados = {};
    
    if (tipo === 'acoes_intro') {
        const textoEl = document.getElementById('textoAcoesIntro');
        if (textoEl) {
            dados.texto = textoEl.innerHTML;
        }
    } else {
        // Para os outros slides (saude_fisica, saude_emocional, saude_social)
        const textoEl = document.querySelector(`#textoAcoes${tipo.replace('acoes_', '').split('_').map(s => s.charAt(0).toUpperCase() + s.slice(1)).join('')}`);
        const acoesItems = document.querySelectorAll(`#listaAcoes${tipo.replace('acoes_', '').split('_').map(s => s.charAt(0).toUpperCase() + s.slice(1)).join('')} .acao-item .conteudo-editavel`);
        
        if (textoEl) {
            dados.texto = textoEl.innerHTML;
        }
        
        if (acoesItems.length > 0) {
            dados.acoes = Array.from(acoesItems).map(item => item.textContent.trim());
        }
    }
    
    // Salva no localStorage
    localStorage.setItem(`acoes_${tipo}`, JSON.stringify(dados));
    
    // Desativa modo de edição
    toggleEdicaoAcoes(tipo);
    
    // Mostra mensagem de sucesso
    const btnSalvar = document.getElementById('btnSalvarAcoes');
    const textoOriginal = btnSalvar.innerHTML;
    
    btnSalvar.innerHTML = '<i class="fas fa-check"></i> Salvo!';
    btnSalvar.style.background = '#28a745';
    
    setTimeout(() => {
        btnSalvar.innerHTML = textoOriginal;
        btnSalvar.style.background = '#808080'; // Cinza para RODA DE OURO
    }, 2000);
}

// ==================== UTILITÁRIOS ====================
function truncate(str, maxLen) {
    if (!str) return 'N/A';
    return str.length > maxLen ? str.substring(0, maxLen) + '...' : str;
}

function formatarAnalise(texto) {
    if (!texto) return 'Análise não disponível.';
    
    // Converte **texto** para <strong>texto</strong>
    texto = texto.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Converte quebras de linha para <br>
    texto = texto.replace(/\n/g, '<br>');
    
    return texto;
}

function mostrarErro(mensagem) {
    const container = document.getElementById('slideContent');
    container.innerHTML = `
        <div class="empty-state">
            <i class="fas fa-exclamation-triangle"></i>
            <h3>Erro</h3>
            <p>${mensagem}</p>
        </div>
    `;
}

// ==================== EXPORTAÇÃO ====================

function toggleExportMenu() {
    const menu = document.getElementById('exportMenu');
    if (menu) {
        menu.classList.toggle('show');
    }
}

// Fecha o menu quando clica fora
document.addEventListener('click', (e) => {
    const menu = document.getElementById('exportMenu');
    const btn = document.querySelector('.btn-export');
    if (menu && btn && !menu.contains(e.target) && !btn.contains(e.target)) {
        menu.classList.remove('show');
    }
});

// Função exportarPDF REMOVIDA COMPLETAMENTE

async function exportarPowerPoint() {
    try {
        // Fecha o menu
        const menu = document.getElementById('exportMenu');
        if (menu) menu.classList.remove('show');
        
        // Verifica autenticação
        if (typeof checkAuth === 'function' && !checkAuth()) {
            return;
        }
        
        // Obtém client_id
        let clientId = null;
        if (typeof window.getCurrentClientId === 'function') {
            clientId = window.getCurrentClientId(null);
        } else {
            const stored = localStorage.getItem('cliente_selecionado');
            clientId = stored ? Number(stored) : null;
        }
        
        if (!clientId || !Number.isFinite(clientId) || clientId <= 0) {
            alert('Selecione um cliente para exportar o relatório.');
            return;
        }
        
        // Mostra loading
        const btn = document.querySelector('.btn-export');
        const originalHTML = btn ? btn.innerHTML : '';
        if (btn) {
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i><span>Gerando PPTX...</span>';
            btn.disabled = true;
        }
        
        // Obtém token
        const token = typeof getAccessToken === 'function' ? getAccessToken() : localStorage.getItem('access_token');
        if (!token) {
            alert('Você precisa estar logado para exportar relatórios.');
            window.location.href = '/login';
            return;
        }
        
        // Faz requisição
        const timestamp = new Date().getTime();
        const url = `/api/export/pptx?client_id=${clientId}&_t=${timestamp}`;
        
        const response = await fetch(url, {
            headers: {'Authorization': `Bearer ${token}`}
        });
        
        if (!response.ok) {
            if (response.status === 401) {
                alert('Sessão expirada. Por favor, faça login novamente.');
                window.location.href = '/login';
                return;
            }
            const errorText = await response.text();
            throw new Error(`Erro ao gerar PowerPoint: ${response.status} ${response.statusText}`);
        }
        
        // Faz download
        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = `apresentacao_absenteismo_${new Date().toISOString().split('T')[0]}.pptx`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(downloadUrl);
        
        // Restaura botão
        if (btn) {
            btn.innerHTML = originalHTML;
            btn.disabled = false;
        }
        
    } catch (error) {
        console.error('Erro ao exportar PowerPoint:', error);
        alert(`Erro ao exportar PowerPoint: ${error.message}`);
        
        // Restaura botão
        const btn = document.querySelector('.btn-export');
        if (btn) {
            btn.innerHTML = '<i class="fas fa-download"></i><span>Exportar</span>';
            btn.disabled = false;
        }
    }
}

// Função de impressão REMOVIDA

