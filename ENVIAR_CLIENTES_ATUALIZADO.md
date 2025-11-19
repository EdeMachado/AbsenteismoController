# 📤 ENVIAR ARQUIVO ATUALIZADO

## Execute no PowerShell:

```powershell
scp frontend/clientes.html root@72.60.166.55:/var/www/absenteismo/frontend/
```

## Depois, no terminal da Hostinger:

```bash
# Reiniciar Gunicorn
ps aux | grep gunicorn | grep -v grep
# Pegue o PID do processo master (primeiro número)
kill -HUP PID
```

OU simplesmente recarregue a página no navegador (Ctrl+F5).

---

## O que foi adicionado:

- Botão "Baixar App" no header da página de clientes
- Botão "Dashboard" também no header (para voltar)

Agora você verá os botões no topo da página de clientes!



