# ✅ CORREÇÃO - BARRA DE ROLAGEM ACIMA DA FAIXA

## 🐛 PROBLEMA

A barra de rolagem dos slides de intervenção estava muito longa, ultrapassando a faixa com o logo "conver". Ela deve parar acima da faixa.

---

## ✅ CORREÇÃO APLICADA

Adicionado `max-height: calc(100% - 60px)` no container de rolagem para que:
- ✅ A barra de rolagem pare **exatamente acima da faixa** (60px de altura)
- ✅ O conteúdo não ultrapasse a área da faixa
- ✅ O padding-bottom foi reduzido de 80px para 20px (já que o max-height já limita)

**Slides corrigidos:**
- ✅ Saúde Física
- ✅ Saúde Emocional  
- ✅ Saúde Social

---

## 📤 ENVIAR ARQUIVO CORRIGIDO

Execute no PowerShell:

```powershell
cd "C:\Users\Ede Machado\AbsenteismoConverplast"
scp frontend/static/js/apresentacao.js root@72.60.166.55:/var/www/absenteismo/frontend/static/js/apresentacao.js
```

---

## ✅ TESTAR

1. **Limpe o cache** (Ctrl+F5)
2. **Acesse a apresentação**
3. **Navegue até os slides de intervenção** (Saúde Física, Emocional, Social)
4. **Verifique:**
   - ✅ A barra de rolagem para **acima da faixa**
   - ✅ A faixa com o logo "conver" fica visível
   - ✅ Nenhum conteúdo fica escondido atrás da faixa
   - ✅ A rolagem funciona corretamente

---

## 💡 RESULTADO ESPERADO

Agora o container de rolagem tem:
- **max-height: calc(100% - 60px)** - Limita altura para parar antes da faixa
- **padding-bottom: 20px** - Espaço mínimo no final
- **Faixa: 60px de altura** (position: absolute; bottom: 0)
- **Barra de rolagem para antes da faixa!**

**Teste e me diga se ficou bom!**


