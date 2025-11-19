# 📱 AbsenteismoController - App Desktop

Aplicativo desktop para o sistema AbsenteismoController.

## 🚀 Instalação

### Opção 1: Usar versão pré-compilada (Recomendado)

1. Baixe o arquivo `.exe` da pasta `dist/`
2. Execute o instalador
3. O app será instalado e aparecerá no menu Iniciar

### Opção 2: Compilar você mesmo

#### Pré-requisitos:
- Node.js 18+ instalado
- npm ou yarn

#### Passos:

1. **Instalar dependências:**
```bash
cd app-desktop
npm install
```

2. **Executar em modo desenvolvimento:**
```bash
npm start
```

3. **Compilar para Windows:**
```bash
npm run build-win
```

O executável estará em `app-desktop/dist/`

## 📋 Funcionalidades

- ✅ Acesso direto ao sistema sem abrir navegador
- ✅ Interface nativa do Windows
- ✅ Atalhos de teclado (F5 para recarregar)
- ✅ Menu completo
- ✅ Abre links externos no navegador padrão
- ✅ Suporte a tela cheia

## ⌨️ Atalhos de Teclado

- **F5**: Recarregar página
- **Ctrl+Shift+R**: Recarregar (forçar, limpa cache)
- **Ctrl+Q**: Sair do aplicativo
- **F11**: Tela cheia

## 🔧 Configuração

O app está configurado para acessar:
- **Produção**: https://www.absenteismocontroller.com.br
- **Desenvolvimento**: http://localhost:8000 (quando `NODE_ENV=development`)

Para alterar, edite o arquivo `main.js`:

```javascript
const PRODUCTION_URL = 'https://www.absenteismocontroller.com.br';
const DEV_URL = 'http://localhost:8000';
```

## 📦 Estrutura

```
app-desktop/
├── main.js          # Código principal do Electron
├── package.json     # Configuração do projeto
├── assets/          # Ícones e recursos
│   └── icon.png     # Ícone do aplicativo
└── dist/            # Executáveis compilados (gerado)
```

## 🐛 Solução de Problemas

### App não abre
- Verifique se tem conexão com internet
- Verifique se o site está online

### Erro ao compilar
- Certifique-se de ter Node.js 18+ instalado
- Execute `npm install` novamente

## 📝 Notas

- O app é basicamente um navegador que carrega o site
- Todos os dados ficam no servidor
- Requer conexão com internet para funcionar



