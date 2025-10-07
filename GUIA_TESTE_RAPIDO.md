# 🚀 GUIA DE TESTE RÁPIDO - AbsenteismoController v2.0

## ⚡ TESTE EM 5 MINUTOS:

---

### **1️⃣ INICIAR SISTEMA (10 segundos)**

**Clique 2x:**
```
C:\Users\Ede Machado\AbsenteismoController\INICIAR_SISTEMA.bat
```

**Aguarde aparecer:**
```
INFO: Uvicorn running on http://0.0.0.0:8000
```

---

### **2️⃣ ACESSAR NO NAVEGADOR (5 segundos)**

**Abra:**
```
http://localhost:8000
```

**Você verá:**
- Menu lateral azul
- 5 cards de métricas (se já fez upload)
- 6 gráficos (se já fez upload)

---

### **3️⃣ TESTAR UPLOAD (30 segundos)**

**Passo a passo:**
1. Clique em **"Upload"** no menu
2. Arraste o arquivo:
   ```
   C:\Users\Ede Machado\AbsenteismoController\Dados\Atestados 09.2025.xlsx
   ```
3. Clique em **"Enviar"**
4. Aguarde a barra de progresso (5-10 segundos)
5. Clique em **"Dashboard"** no menu

**Resultado esperado:**
- Atestados DIAS: 282
- Atestados HORAS: 133
- Dias Perdidos: 618
- Horas Perdidas: 6.396

---

### **4️⃣ TESTAR FUNCIONÁRIOS (20 segundos)**

1. Clique em **"Funcionários"** no menu
2. Veja a tabela completa
3. Digite um nome na busca
4. Selecione um setor no filtro
5. Clique em "Filtrar"

---

### **5️⃣ TESTAR COMPARATIVOS (30 segundos)**

1. Clique em **"Comparativos"** no menu
2. Clique em **"Último Mês"** (atalho rápido)
3. Clique em **"Comparar"**
4. Veja as variações e gráfico comparativo

---

### **6️⃣ TESTAR EXPORT EXCEL (15 segundos)**

1. Clique em **"Relatórios"** no menu
2. Clique em **"Exportar Excel"**
3. Arquivo será baixado automaticamente
4. Abra o Excel e veja os dados tratados

---

### **7️⃣ TESTAR MODO APRESENTAÇÃO (15 segundos)**

1. Clique em **"Apresentação"** no menu
2. Veja a tela cheia com KPIs grandes
3. Clique em **"Sair da Apresentação"**

---

## ✅ CHECKLIST DE TESTE:

```
[ ] Sistema iniciou sem erros?
[ ] Dashboard abriu?
[ ] Upload funcionou?
[ ] Valores corretos aparecem?
[ ] Gráficos carregaram?
[ ] Página Funcionários funciona?
[ ] Comparativos funciona?
[ ] Export Excel funciona?
[ ] Modo Apresentação funciona?
[ ] Navegação entre páginas funciona?
```

---

## 🔴 SE DER ERRO:

### **Erro: "Erro ao carregar dados"**
```
Solução: Faça um upload primeiro!
```

### **Erro: "Erro 500 ao fazer upload"**
```
Solução: 
1. Pare o servidor (Ctrl+C)
2. Delete: database/absenteismo.db
3. Reinicie: INICIAR_SISTEMA.bat
```

### **Erro: "Página não carrega"**
```
Solução: Verifique se o servidor está rodando
```

---

## 💡 DICAS:

1. **Sempre deixe a janela CMD do servidor aberta**
2. **Use F5 para recarregar a página**
3. **Use F12 para ver erros no console**
4. **Aguarde o servidor recarregar após edições** (5 segundos)

---

## 📊 DADOS DE TESTE:

Se não tiver planilha, use:
```
C:\Users\Ede Machado\AbsenteismoController\planilha_exemplo.xlsx
```

Ou faça upload de qualquer Excel com colunas similares!

---

## 🎯 TESTE COMPLETO OK?

Se todos os testes passarem:

**🎊 SISTEMA ESTÁ 100% FUNCIONAL!**

Pode começar a usar e mostrar para clientes! 💪

---

## 📞 PRECISA DE AJUDA?

Se algum teste falhar, anote:
- Qual página
- Qual ação
- Qual erro (F12 console)

E me avise para corrigir! 😊

---

**BOA SORTE NOS TESTES!** 🚀


