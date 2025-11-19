#!/bin/bash
# Script para verificar logs de erro do upload

echo "=========================================="
echo "🔍 VERIFICANDO LOGS DE ERRO - UPLOAD"
echo "=========================================="
echo ""

cd /var/www/absenteismo || exit 1

echo "📋 Últimos 50 erros relacionados a upload:"
echo "-------------------------------------------"
tail -100 logs/errors.log | grep -i -A 10 "upload\|Upload\|UPLOAD" | tail -50
echo ""

echo "📋 Últimos 20 erros gerais:"
echo "-------------------------------------------"
tail -20 logs/errors.log
echo ""

echo "📋 Verificando permissões da pasta uploads:"
echo "-------------------------------------------"
ls -la uploads/ 2>/dev/null || echo "❌ Pasta uploads não existe!"
echo ""

echo "📋 Verificando processos Gunicorn:"
echo "-------------------------------------------"
ps aux | grep gunicorn | grep -v grep
echo ""

echo "✅ Verificação concluída!"
echo ""
echo "💡 Para ver logs em tempo real, execute:"
echo "   tail -f /var/www/absenteismo/logs/errors.log"


