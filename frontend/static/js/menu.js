/**
 * Menu Component - Componente reutilizável de menu
 */

// Carrega alertas e exibe badge
async function carregarAlertasMenu() {
    try {
        const mesInicio = document.getElementById('mesInicio')?.value || '';
        const mesFim = document.getElementById('mesFim')?.value || '';
        
        let url = '/api/alertas?client_id=1';
        if (mesInicio) url += `&mes_inicio=${encodeURIComponent(mesInicio)}`;
        if (mesFim) url += `&mes_fim=${encodeURIComponent(mesFim)}`;
        
        const response = await fetch(url);
        if (!response.ok) return;
        
        const data = await response.json();
        const total = data.total || 0;
        
        // Atualiza badge
        const badge = document.getElementById('alertasBadge');
        if (badge) {
            if (total > 0) {
                badge.textContent = total;
                badge.style.display = 'inline-block';
            } else {
                badge.style.display = 'none';
            }
        }
        
        // Armazena alertas para o dropdown
        window.alertasData = data.alertas || [];
        
    } catch (error) {
        console.error('Erro ao carregar alertas:', error);
    }
}

// Renderiza menu com alertas
function renderizarMenu() {
    const menuHTML = `
        <nav class="sidebar-nav">
            <a href="/" class="nav-item">
                <i class="fas fa-chart-line"></i>
                <span>Dashboard</span>
            </a>
            <a href="/clientes" class="nav-item">
                <i class="fas fa-building"></i>
                <span>🏢 Clientes</span>
            </a>
            <a href="/apresentacao" class="nav-item">
                <i class="fas fa-tv"></i>
                <span>📊 Apresentação</span>
            </a>
            <div class="nav-item" style="position: relative;">
                <a href="/upload" style="display: flex; align-items: center; width: 100%; text-decoration: none; color: inherit;">
                    <i class="fas fa-cloud-upload-alt"></i>
                    <span>📤 Upload Planilha</span>
                </a>
                <div class="alertas-menu" onclick="toggleAlertasDropdown(event)" style="position: relative; cursor: pointer; margin-left: auto; padding: 0 8px;">
                    <i class="fas fa-bell" style="color: #666; font-size: 18px;"></i>
                    <span id="alertasBadge" class="alertas-badge" style="display: none; position: absolute; top: -6px; right: 2px; background: #f44336; color: white; border-radius: 50%; width: 20px; height: 20px; font-size: 11px; display: flex; align-items: center; justify-content: center; font-weight: bold;">0</span>
                </div>
                <div id="alertasDropdown" class="alertas-dropdown" style="display: none; position: absolute; top: 100%; left: 0; right: 0; background: white; border: 1px solid #ddd; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); z-index: 1000; margin-top: 4px; max-height: 400px; overflow-y: auto;">
                    <div style="padding: 12px; border-bottom: 1px solid #eee; font-weight: 600; font-size: 14px;">
                        <i class="fas fa-bell"></i> Alertas (<span id="alertasCount">0</span>)
                    </div>
                    <div id="alertasList" style="padding: 8px;">
                        <div style="text-align: center; padding: 20px; color: #999;">
                            <i class="fas fa-spinner fa-spin"></i> Carregando...
                        </div>
                    </div>
                </div>
            </div>
            <a href="/dados_powerbi" class="nav-item">
                <i class="fas fa-table"></i>
                <span>📋 Meus Dados</span>
            </a>
            <a href="/funcionarios" class="nav-item">
                <i class="fas fa-users"></i>
                <span>👥 Funcionários</span>
            </a>
            <a href="/comparativos" class="nav-item">
                <i class="fas fa-balance-scale"></i>
                <span>⚖️ Comparativos</span>
            </a>
            <a href="/relatorios" class="nav-item">
                <i class="fas fa-file-alt"></i>
                <span>📄 Relatórios</span>
            </a>
            <a href="/configuracoes" class="nav-item">
                <i class="fas fa-cog"></i>
                <span>⚙️ Configurações</span>
            </a>
        </nav>
    `;
    
    const navContainer = document.querySelector('.sidebar-nav');
    if (navContainer) {
        navContainer.outerHTML = menuHTML;
    }
}

// Toggle dropdown de alertas
function toggleAlertasDropdown(event) {
    event.stopPropagation();
    const dropdown = document.getElementById('alertasDropdown');
    if (!dropdown) return;
    
    if (dropdown.style.display === 'none' || !dropdown.style.display) {
        dropdown.style.display = 'block';
        renderizarAlertasDropdown();
    } else {
        dropdown.style.display = 'none';
    }
}

// Renderiza alertas no dropdown
function renderizarAlertasDropdown() {
    const container = document.getElementById('alertasList');
    const countEl = document.getElementById('alertasCount');
    const alertas = window.alertasData || [];
    
    if (countEl) countEl.textContent = alertas.length;
    
    if (!container) return;
    
    if (alertas.length === 0) {
        container.innerHTML = '<div style="text-align: center; padding: 20px; color: #999;">Nenhum alerta</div>';
        return;
    }
    
    // Ordena por severidade
    const severidades = {'alta': 3, 'media': 2, 'baixa': 1};
    const alertasOrdenados = [...alertas].sort((a, b) => 
        (severidades[b.severidade] || 0) - (severidades[a.severidade] || 0)
    );
    
    container.innerHTML = alertasOrdenados.map(alerta => {
        const icone = alerta.severidade === 'alta' ? 'fa-exclamation-circle' : 
                     alerta.severidade === 'media' ? 'fa-exclamation-triangle' : 'fa-info-circle';
        const cor = alerta.severidade === 'alta' ? '#f44336' : 
                   alerta.severidade === 'media' ? '#ff9800' : '#2196f3';
        
        let acaoBtn = '';
        if (alerta.tipo === 'funcionario_alto_absenteismo' || alerta.tipo === 'funcionario_frequente') {
            acaoBtn = `<a href="/perfil_funcionario?nome=${encodeURIComponent(alerta.dados.nome)}" style="display: inline-block; margin-top: 8px; padding: 4px 12px; background: #1a237e; color: white; border-radius: 4px; text-decoration: none; font-size: 12px;">
                <i class="fas fa-user-circle"></i> Ver Perfil
            </a>`;
        }
        
        return `
            <div style="padding: 12px; border-bottom: 1px solid #f0f0f0; cursor: pointer;" onclick="toggleAlertasDropdown(event)">
                <div style="display: flex; align-items: flex-start; gap: 8px;">
                    <i class="fas ${icone}" style="color: ${cor}; margin-top: 4px; font-size: 16px;"></i>
                    <div style="flex: 1;">
                        <div style="font-weight: 600; font-size: 13px; color: #333; margin-bottom: 4px;">${alerta.titulo}</div>
                        <div style="font-size: 12px; color: #666; line-height: 1.4;">${alerta.mensagem}</div>
                        ${acaoBtn}
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// Fecha dropdown ao clicar fora
document.addEventListener('click', function(event) {
    if (!event.target.closest('.alertas-menu') && !event.target.closest('.alertas-dropdown')) {
        const dropdown = document.getElementById('alertasDropdown');
        if (dropdown) dropdown.style.display = 'none';
    }
});

// Carrega alertas ao inicializar
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        carregarAlertasMenu();
        // Recarrega alertas a cada 5 minutos
        setInterval(carregarAlertasMenu, 5 * 60 * 1000);
    }, 1000);
});

