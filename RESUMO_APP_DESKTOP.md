# 📱 App Desktop - AbsenteismoController

## ✅ O que foi criado:

1. **Página de Download** (`/download_app`)
   - Design azul bonito
   - Informações sobre o app
   - Botão de download
   - Requisitos do sistema

2. **App Electron** (`app-desktop/`)
   - Tema azul (#1a237e)
   - Interface nativa
   - Menu completo
   - Atalhos de teclado

3. **Rota de Download** (`/api/download/app`)
   - Serve arquivo ZIP com o app
   - Requer autenticação

4. **Link no Menu**
   - Adicionado em todas as páginas principais
   - Ícone de download

---

## 🚀 Como usar:

### Para os usuários:

1. Acesse o sistema: https://www.absenteismocontroller.com.br
2. Faça login
3. Clique em "📱 Baixar App" no menu
4. Clique no botão "Baixar App Desktop"
5. Extraia o ZIP baixado
6. Siga as instruções na pasta

### Para compilar o app:

1. Instale Node.js: https://nodejs.org/
2. Abra terminal na pasta `app-desktop/`
3. Execute: `npm install`
4. Execute: `npm run build-win`
5. O instalador estará em `app-desktop/dist/`

OU simplesmente execute: `INSTALADOR.bat`

---

## 📦 Estrutura:

```
app-desktop/
├── main.js              # Código do app Electron
├── package.json          # Configuração
├── INSTALADOR.bat        # Script de instalação
├── README.md             # Documentação
└── assets/               # Ícones (criar se necessário)
    └── icon.png          # Ícone do app
```

---

## 🎨 Características:

- ✅ Design azul (#1a237e) - cor do sistema
- ✅ Interface bonita e moderna
- ✅ App nativo do Windows
- ✅ Menu completo
- ✅ Atalhos de teclado (F5, F11, etc)
- ✅ Conecta-se ao servidor em produção

---

## 📝 Próximos passos:

1. **Criar ícone do app:**
   - Criar pasta `app-desktop/assets/`
   - Adicionar `icon.png` (256x256 ou maior)
   - Ícone azul com logo do AbsenteismoController

2. **Compilar e testar:**
   - Executar `INSTALADOR.bat`
   - Testar o app instalado
   - Verificar se tudo funciona

3. **Fazer upload para o servidor:**
   - Enviar pasta `app-desktop/` completa
   - Testar download pelo sistema

---

## 🔧 Notas técnicas:

- O app é basicamente um navegador Electron que carrega o site
- Requer conexão com internet
- Todos os dados ficam no servidor
- O app apenas exibe a interface web

---

## ✅ Status:

- ✅ Página de download criada
- ✅ Rota de download criada
- ✅ Link no menu adicionado
- ✅ App Electron configurado
- ⏳ Ícone do app (criar)
- ⏳ Compilar e testar
- ⏳ Upload para servidor



