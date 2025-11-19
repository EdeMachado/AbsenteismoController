# ✅ CORREÇÃO - BOTÕES SOBREPONDO CONTEÚDO

## 🐛 PROBLEMA

Os botões de navegação estão sobrepondo as análises porque o conteúdo não tem espaço suficiente na parte inferior.

---

## ✅ CORREÇÃO APLICADA

Adicionado `padding-bottom: 140px` no `.apresentacao-content` para criar espaço para:
- Botões de navegação (altura ~60px)
- Footer (altura ~60px)
- Espaçamento (20px)

---

## 📤 ENVIAR ARQUIVO CORRIGIDO

Execute no PowerShell:

```powershell
cd "C:\Users\Ede Machado\AbsenteismoConverplast"
scp frontend/apresentacao.html root@72.60.166.55:/var/www/absenteismo/frontend/apresentacao.html
```

---

## 🔄 REINICIAR SERVIÇO (se necessário)

Se já reiniciou antes, pode não precisar. Mas se quiser garantir:

```bash
cd /var/www/absenteismo
source venv/bin/activate
kill -HUP $(pgrep -f gunicorn)
```

---

## ✅ TESTAR

1. **Limpe o cache** (Ctrl+F5)
2. **Acesse a apresentação**
3. **Verifique:**
   - ✅ Botões de navegação aparecem na parte inferior
   - ✅ **NÃO sobrepõem mais o conteúdo**
   - ✅ Há espaço suficiente para rolar e ver tudo

---

## 💡 SOBRE OS SLIDES DE INTERVENÇÃO

Os slides de intervenção colaboradores foram adicionados no backend. Eles aparecem **após todos os gráficos**. 

Para verificar se estão sendo criados:
1. Abra o console do navegador (F12)
2. Procure por: `[APRESENTACAO] Slides carregados: X para cliente: Y`
3. O número X deve incluir os 4 slides de ações

Se não aparecerem, me envie o número total de slides que aparece no console.


