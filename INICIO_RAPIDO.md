# 🚀 Início Rápido - Upload e Deploy

## 📤 Upload de Planilhas (AGORA)

### Opção 1: Via Interface Web
1. Acesse o sistema: http://localhost:8000 (ou seu domínio)
2. Faça login
3. Vá em "Upload" ou "Upload Inteligente"
4. Selecione as planilhas e faça upload

### Opção 2: Via Script (Recomendado para múltiplas planilhas)

```bash
python upload_multiplas_planilhas.py
```

**O script irá:**
- ✅ Detectar mês de referência automaticamente
- ✅ Fazer upload de múltiplas planilhas de uma vez
- ✅ Mostrar progresso e resultados

**Exemplo de uso:**
1. Execute o script
2. Digite a URL (ex: `http://localhost:8000` ou `https://www.absenteismocontroller.com.br`)
3. Faça login
4. Selecione o cliente
5. Informe a pasta com as planilhas (ou use "Dados")
6. Confirme o upload

## 🌐 Deploy para Produção

### Passo 1: Preparar Configuração

```bash
# Atualizar .env
nano .env
```

Adicione:
```env
SECRET_KEY=sua-chave-secreta-aqui
ENVIRONMENT=production
ALLOWED_ORIGINS=https://www.absenteismocontroller.com.br,https://absenteismocontroller.com.br
```

### Passo 2: Escolher Método de Deploy

**Opção A: Linux com Nginx + Gunicorn (Recomendado)**
- Mais estável e performático
- Suporte a SSL fácil
- Ver: `GUIA_DEPLOY_PRODUCAO.md` seção "Opção 1"

**Opção B: Windows Server**
- Se já tem servidor Windows
- Ver: `GUIA_DEPLOY_PRODUCAO.md` seção "Opção 2"

**Opção C: Docker**
- Para escalabilidade
- Ver: `GUIA_DEPLOY_PRODUCAO.md` seção "Opção 3"

### Passo 3: Seguir Guia Completo

```bash
# Ler guia detalhado
cat GUIA_DEPLOY_PRODUCAO.md
```

## ✅ Checklist Rápido

### Upload de Planilhas
- [ ] Planilhas na pasta "Dados" ou outra pasta
- [ ] Sistema rodando (local ou produção)
- [ ] Login funcionando
- [ ] Cliente criado no sistema

### Deploy
- [ ] Servidor preparado
- [ ] .env configurado
- [ ] CORS configurado
- [ ] SSL configurado
- [ ] Testes realizados

## 📚 Documentação Completa

- `RESUMO_DEPLOY.md` - Resumo geral
- `GUIA_DEPLOY_PRODUCAO.md` - Guia completo passo a passo
- `upload_multiplas_planilhas.py` - Script de upload
- `GUIA_CONFIGURACAO_SEGURANCA.md` - Segurança

## 🆘 Precisa de Ajuda?

1. **Upload não funciona?**
   - Verifique se o sistema está rodando
   - Verifique formato da planilha
   - Veja logs em `logs/errors.log`

2. **Deploy com problemas?**
   - Siga o guia passo a passo
   - Verifique logs do servidor
   - Teste localmente primeiro

---

**Boa sorte!** 🎉



