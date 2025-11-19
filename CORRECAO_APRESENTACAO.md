# ✅ CORREÇÃO - MÓDULO APRESENTAÇÃO

## 🐛 PROBLEMAS IDENTIFICADOS

1. **Botões de navegação não aparecem** - Footer estava cobrindo os botões
2. **Página de intervenção colaboradores não aparece** - Slides de ações foram removidos do backend

---

## ✅ CORREÇÕES APLICADAS

### 1. Botões de Navegação
- Adicionado `position: fixed` e `z-index: 200` aos botões
- Posicionados acima do footer (`bottom: 80px`)
- Centralizados horizontalmente

### 2. Slide de Intervenção Colaboradores
- Adicionados 4 slides de ações de volta no backend:
  - `acoes_intro` - "Intervenções Junto aos Colaboradores"
  - `acoes_saude_fisica` - "Saúde Física"
  - `acoes_saude_emocional` - "Saúde Emocional"
  - `acoes_saude_social` - "Saúde Social"

---

## 📤 ENVIAR ARQUIVOS CORRIGIDOS

Execute no PowerShell:

```powershell
cd "C:\Users\Ede Machado\AbsenteismoConverplast"
scp frontend/apresentacao.html root@72.60.166.55:/var/www/absenteismo/frontend/apresentacao.html
scp backend/main.py root@72.60.166.55:/var/www/absenteismo/backend/main.py
```

---

## 🔄 REINICIAR SERVIÇO

No terminal SSH:

```bash
cd /var/www/absenteismo
source venv/bin/activate
pkill -9 gunicorn
sleep 2
gunicorn -c gunicorn_config.py backend.main:app --daemon
sleep 2
ps aux | grep gunicorn | grep -v grep
```

---

## ✅ TESTAR

1. **Limpe o cache** (Ctrl+F5)
2. **Acesse a apresentação**
3. **Verifique:**
   - ✅ Botões de navegação aparecem na parte inferior (acima do footer)
   - ✅ Slide "Intervenções Junto aos Colaboradores" aparece após os gráficos
   - ✅ Slides de Saúde Física, Emocional e Social aparecem

---

## 💡 O QUE FOI CORRIGIDO

**CSS dos botões:**
- Agora estão fixos na parte inferior
- Aparecem acima do footer
- Centralizados

**Backend:**
- Slides de ações foram adicionados de volta
- Incluem o slide de intervenção colaboradores

**Agora deve funcionar corretamente!**


