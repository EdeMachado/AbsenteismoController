#!/bin/bash

# Script de Deploy - Correção Produtividade + Filtro Ordenação
# Este script faz commit, push e deploy no servidor

echo "========================================"
echo "  DEPLOY - Correções e Melhorias"
echo "========================================"
echo ""

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configurações do servidor (ajuste conforme necessário)
SERVIDOR_IP="72.60.166.55"
SERVIDOR_PORTA="65002"
SERVIDOR_CAMINHO="~/domains/absenteismocontroller.com.br/public_html/absenteismo"

# Verifica se está no diretório correto
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo -e "${RED}[ERRO] Execute este script na raiz do projeto!${NC}"
    exit 1
fi

echo -e "${CYAN}[1/5] Verificando status do Git...${NC}"
git status --short

echo ""
echo -e "${YELLOW}[2/5] Preparando commit...${NC}"

# Adiciona arquivos modificados
git add frontend/static/js/produtividade.js
git add frontend/dados_powerbi.html
git add frontend/static/js/dados_powerbi.js

# Faz commit
COMMIT_MESSAGE="Correção: Edição produtividade + Filtro ordenação em Meus Dados

- Corrigido problema de edição no módulo produtividade (client_id faltando)
- Adicionado filtro de ordenação crescente/decrescente no módulo Meus Dados
- Melhorias na interface de ordenação"

git commit -m "$COMMIT_MESSAGE"

if [ $? -ne 0 ]; then
    echo -e "${YELLOW}[AVISO] Nenhuma alteração para commitar ou commit já existe${NC}"
fi

echo ""
echo -e "${CYAN}[3/5] Fazendo push para GitHub...${NC}"
git push origin main

if [ $? -ne 0 ]; then
    echo -e "${RED}[ERRO] Falha ao fazer push!${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Push concluído com sucesso!${NC}"
echo ""

# Pergunta se deseja fazer deploy no servidor
echo -e "${YELLOW}Deseja fazer deploy no servidor agora? (s/n)${NC}"
read -r resposta

if [ "$resposta" != "s" ] && [ "$resposta" != "S" ]; then
    echo ""
    echo -e "${YELLOW}Deploy no servidor cancelado.${NC}"
    echo -e "${CYAN}Para fazer deploy manualmente, execute:${NC}"
    echo "  ssh -p $SERVIDOR_PORTA SEU_USUARIO@$SERVIDOR_IP"
    echo "  cd $SERVIDOR_CAMINHO"
    echo "  git pull origin main"
    echo ""
    exit 0
fi

# Solicita credenciais SSH
echo ""
echo -e "${CYAN}[4/5] Configurando conexão SSH...${NC}"
echo -e "${YELLOW}Digite o usuário SSH:${NC}"
read -r USUARIO_SSH

if [ -z "$USUARIO_SSH" ]; then
    echo -e "${RED}[ERRO] Usuário SSH é obrigatório!${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Digite o caminho do sistema no servidor [${SERVIDOR_CAMINHO}]:${NC}"
read -r caminho_input

if [ ! -z "$caminho_input" ]; then
    SERVIDOR_CAMINHO="$caminho_input"
fi

echo ""
echo -e "${CYAN}[5/5] Conectando ao servidor e fazendo deploy...${NC}"
echo -e "${YELLOW}Você será solicitado a inserir a senha SSH${NC}"
echo ""

# Comando SSH para fazer pull
COMANDO_SSH="cd $SERVIDOR_CAMINHO && git pull origin main && echo '=== DEPLOY CONCLUIDO ==='"

echo -e "${CYAN}Executando no servidor:${NC}"
echo "  $COMANDO_SSH"
echo ""

# Executa SSH
ssh -p $SERVIDOR_PORTA $USUARIO_SSH@$SERVIDOR_IP "$COMANDO_SSH"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}========================================"
    echo -e "  ✅ DEPLOY CONCLUÍDO COM SUCESSO!"
    echo -e "========================================${NC}"
    echo ""
    echo -e "${GREEN}O servidor foi atualizado!${NC}"
    echo -e "${CYAN}Verifique o site: https://www.absenteismocontroller.com.br${NC}"
    echo ""
else
    echo ""
    echo -e "${RED}========================================"
    echo -e "  ⚠️  FALHA NO DEPLOY"
    echo -e "========================================${NC}"
    echo ""
    echo -e "${YELLOW}Possíveis causas:${NC}"
    echo "  - Senha incorreta"
    echo "  - Caminho incorreto"
    echo "  - Git não configurado no servidor"
    echo ""
    echo -e "${CYAN}Tente manualmente:${NC}"
    echo "  ssh -p $SERVIDOR_PORTA $USUARIO_SSH@$SERVIDOR_IP"
    echo "  cd $SERVIDOR_CAMINHO"
    echo "  git pull origin main"
    echo ""
fi

echo ""

