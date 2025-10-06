# 📊 AbsenteismoController v2.0

Sistema profissional de gestão e análise de absenteísmo empresarial.

## 🚀 Funcionalidades

### ✅ Implementado

- **Upload de Planilhas**: Drag-and-drop de arquivos Excel
- **Processamento Automático**: Limpeza e padronização de dados
- **Dashboard Interativo**: Métricas e gráficos em tempo real
- **Análises Detalhadas**: 
  - TOP CIDs mais frequentes
  - TOP setores com mais atestados
  - Evolução mensal (12 meses)
  - Distribuição por gênero
- **Modo Apresentação**: Tela cheia para reuniões
- **Filtros Avançados**: Por período, setor, CID
- **Histórico Completo**: Todos os uploads salvos
- **Design Profissional**: Baseado nos princípios Cole/CRAP

### 🔨 Em Desenvolvimento

- Preview detalhado dos dados
- Análises por funcionário
- Tendências e projeções
- Relatórios comparativos (mensal, trimestral, anual)
- Export PDF/PowerPoint

## 💻 Requisitos

- Python 3.10+
- Windows 10/11

## 📦 Instalação

### 1. Clone o repositório
```bash
git clone https://github.com/seu-usuario/AbsenteismoController.git
cd AbsenteismoController
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Inicie o sistema
Clique duas vezes em `INICIAR_SISTEMA.bat`

Ou execute manualmente:
```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Acesse no navegador
```
http://localhost:8000
```

## 📋 Como Usar

### Passo 1: Upload da Planilha
1. Acesse a página "Upload"
2. Arraste a planilha Excel ou clique para selecionar
3. Aguarde o processamento
4. Pronto! Os dados foram importados

### Passo 2: Visualize o Dashboard
- Métricas principais (atestados, dias, horas, taxa)
- Gráficos interativos
- Filtros por período

### Passo 3: Modo Apresentação
- Clique em "Apresentação" no menu
- Tela cheia otimizada para reuniões
- Gráficos grandes e KPIs destacados

## 🎨 Design

O sistema segue os princípios CRAP (Cole):
- **Contraste**: Hierarquia visual clara
- **Repetição**: Padrões consistentes
- **Alinhamento**: Grid system organizado
- **Proximidade**: Elementos relacionados juntos

### Paleta de Cores
- Primária: #1976D2 (Azul profissional)
- Sucesso: #4CAF50 (Verde positivo)
- Alerta: #F44336 (Vermelho atenção)
- Aviso: #FF9800 (Laranja destaque)

## 📁 Estrutura do Projeto

```
AbsenteismoController/
├── backend/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── database.py          # Database config
│   ├── models.py            # SQLAlchemy models
│   ├── excel_processor.py   # Excel processing
│   └── analytics.py         # Analytics engine
├── frontend/
│   ├── index.html           # Dashboard principal
│   ├── upload.html          # Upload page
│   ├── apresentacao.html    # Presentation mode
│   └── static/
│       ├── css/
│       │   └── main.css     # Estilos principais
│       └── js/
│           ├── dashboard.js
│           └── upload.js
├── database/
│   └── absenteismo.db       # SQLite database
├── uploads/                 # Uploaded files
├── exports/                 # Exported files
├── requirements.txt
├── INICIAR_SISTEMA.bat
└── README.md
```

## 🔧 Tecnologias

- **Backend**: FastAPI + Python
- **Frontend**: HTML5 + CSS3 + JavaScript
- **Database**: SQLite + SQLAlchemy
- **Charts**: Chart.js
- **Processamento**: Pandas + OpenPyXL

## 📊 Métricas Calculadas

- **Total de Atestados**: Contagem de registros
- **Dias Perdidos**: Soma de dias de afastamento
- **Horas Perdidas**: Cálculo baseado em jornada + horas avulsas
- **Taxa de Absenteísmo**: (Horas perdidas / Horas disponíveis) × 100

## 🤝 Contribuindo

1. Fork o projeto
2. Crie sua feature branch (`git checkout -b feature/NovaFeature`)
3. Commit suas mudanças (`git commit -m 'Add NovaFeature'`)
4. Push para a branch (`git push origin feature/NovaFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto é proprietário - © 2025 GrupoBiomed

## 📧 Contato

Para suporte ou dúvidas, entre em contato.

---

**Desenvolvido com ❤️ por GrupoBiomed**
