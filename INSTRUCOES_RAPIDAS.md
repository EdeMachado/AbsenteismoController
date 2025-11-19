# Instruções Rápidas - Configuração de Segurança

## ⚡ Configuração Rápida (2 minutos)

### 1. Gerar SECRET_KEY
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Criar arquivo .env
Crie um arquivo `.env` na raiz do projeto com:
```env
SECRET_KEY=sua-chave-gerada-aqui
```

### 3. Validar
```bash
python validar_seguranca.py
```

### 4. Testar Isolamento
```bash
python test_isolamento_dados.py
```

## ✅ Checklist Rápido

- [ ] Arquivo `.env` criado
- [ ] SECRET_KEY definida no `.env`
- [ ] `validar_seguranca.py` passa sem erros
- [ ] `test_isolamento_dados.py` passa sem erros

## 📚 Documentação Completa

- `GUIA_CONFIGURACAO_SEGURANCA.md` - Guia detalhado
- `RELATORIO_AUDITORIA_SEGURANCA.md` - Relatório de auditoria
- `RESUMO_PROXIMOS_PASSOS.md` - Resumo das implementações

## ⚠️ Importante

- **NUNCA** commite o arquivo `.env`
- Use SECRET_KEY diferente em produção
- Monitore `logs/security.log` regularmente



