// ==================== SISTEMA DE CORES POR CLIENTE ====================

// Cores padrão (fallback)
const CORES_PADRAO = {
    primary: '#1a237e',
    primaryDark: '#0d47a1',
    primaryLight: '#3949ab',
    primaryLighter: '#5c6bc0',
    secondary: '#556B2F',
    secondaryDark: '#4a5d23',
    secondaryLight: '#6B8E23',
    secondaryLighter: '#808000',
    paleta: ['#1a237e', '#556B2F', '#0d47a1', '#6B8E23', '#3949ab', '#808000', '#5c6bc0', '#4a5d23']
};

// Variáveis globais para cores do cliente atual
let CORES_CLIENTE = { ...CORES_PADRAO };
let PALETA_CLIENTE = [...CORES_PADRAO.paleta];

// ==================== CARREGAR CORES DO CLIENTE ====================
async function carregarCoresCliente(clientId) {
    return new Promise(async (resolve) => {
        if (!clientId) {
            // Se não tem cliente, usa cores padrão
            CORES_CLIENTE = { ...CORES_PADRAO };
            PALETA_CLIENTE = [...CORES_PADRAO.paleta];
            resolve();
            return;
        }
        
        try {
            const response = await fetch(`/api/clientes/${clientId}/cores`);
            if (!response.ok) {
                console.warn('Erro ao carregar cores do cliente, usando padrão');
                CORES_CLIENTE = { ...CORES_PADRAO };
                PALETA_CLIENTE = [...CORES_PADRAO.paleta];
                resolve();
                return;
            }
            
            const data = await response.json();
            if (data.success && data.cores) {
                // Mescla cores personalizadas com padrão (para garantir que todos os campos existam)
                CORES_CLIENTE = {
                    ...CORES_PADRAO,
                    ...data.cores
                };
                
                // Se tiver paleta personalizada, usa ela; senão, gera da estrutura de cores
                if (data.cores.paleta && Array.isArray(data.cores.paleta) && data.cores.paleta.length > 0) {
                    PALETA_CLIENTE = [...data.cores.paleta];
                } else {
                    // Gera paleta a partir das cores principais
                    PALETA_CLIENTE = [
                        CORES_CLIENTE.primary,
                        CORES_CLIENTE.secondary,
                        CORES_CLIENTE.primaryDark,
                        CORES_CLIENTE.secondaryLight,
                        CORES_CLIENTE.primaryLight,
                        CORES_CLIENTE.secondaryLighter,
                        CORES_CLIENTE.primaryLighter,
                        CORES_CLIENTE.secondaryDark
                    ];
                }
                
                console.log('Cores do cliente carregadas:', CORES_CLIENTE);
            } else {
                // Sem cores configuradas, usa padrão
                CORES_CLIENTE = { ...CORES_PADRAO };
                PALETA_CLIENTE = [...CORES_PADRAO.paleta];
            }
            resolve();
        } catch (error) {
            console.error('Erro ao carregar cores do cliente:', error);
            CORES_CLIENTE = { ...CORES_PADRAO };
            PALETA_CLIENTE = [...CORES_PADRAO.paleta];
            resolve();
        }
    });
}

// ==================== OBSERVAR MUDANÇAS DE CLIENTE ====================
if (typeof window !== 'undefined') {
    // Carrega cores quando o cliente muda
    const observer = new MutationObserver(() => {
        const clientId = typeof window.getCurrentClientId === 'function' ? window.getCurrentClientId(null) : null;
        if (clientId) {
            carregarCoresCliente(clientId);
        }
    });
    
    // Observa mudanças no localStorage
    window.addEventListener('storage', (e) => {
        if (e.key === 'cliente_selecionado') {
            const clientId = e.newValue ? Number(e.newValue) : null;
            if (clientId) {
                carregarCoresCliente(clientId);
            }
        }
    });
    
    // Carrega cores na inicialização
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(() => {
            const clientId = typeof window.getCurrentClientId === 'function' ? window.getCurrentClientId(null) : null;
            if (clientId) {
                carregarCoresCliente(clientId);
            }
        }, 500);
    });
}

// ==================== FUNÇÕES AUXILIARES ====================
function getCoresCliente() {
    return CORES_CLIENTE;
}

function getPaletaCliente() {
    return PALETA_CLIENTE;
}

// Exporta para uso global
if (typeof window !== 'undefined') {
    window.CORES_CLIENTE = CORES_CLIENTE;
    window.PALETA_CLIENTE = PALETA_CLIENTE;
    window.carregarCoresCliente = carregarCoresCliente;
    window.getCoresCliente = getCoresCliente;
    window.getPaletaCliente = getPaletaCliente;
}

