#!/bin/bash
# Script para forçar reinício completo do Gunicorn

echo "=========================================="
echo "🔄 REINICIANDO GUNICORN COMPLETAMENTE"
echo "=========================================="
echo ""

cd /var/www/absenteismo || exit 1
source venv/bin/activate

# 1. Matar TODOS os processos Gunicorn
echo "1. Matando processos Gunicorn..."
pkill -9 gunicorn
sleep 2

# 2. Verificar se realmente parou
echo ""
echo "2. Verificando processos..."
PROCESSOS=$(ps aux | grep gunicorn | grep -v grep)
if [ -z "$PROCESSOS" ]; then
    echo "✅ Nenhum processo Gunicorn encontrado"
else
    echo "⚠️  Ainda há processos:"
    echo "$PROCESSOS"
    echo "Tentando matar novamente..."
    pkill -9 gunicorn
    sleep 2
fi

# 3. Limpar cache Python
echo ""
echo "3. Limpando cache Python..."
find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
echo "✅ Cache limpo"

# 4. Verificar se arquivo foi atualizado
echo ""
echo "4. Verificando arquivo main.py..."
if grep -q "error_traceback" backend/main.py; then
    echo "✅ Arquivo main.py está atualizado (tem 'error_traceback')"
else
    echo "❌ Arquivo main.py NÃO está atualizado!"
    echo "   Execute: scp backend/main.py root@72.60.166.55:/var/www/absenteismo/backend/main.py"
    exit 1
fi

# 5. Iniciar Gunicorn novamente
echo ""
echo "5. Iniciando Gunicorn..."
gunicorn -c gunicorn_config.py backend.main:app --daemon

# 6. Aguardar e verificar
sleep 3
echo ""
echo "6. Verificando se iniciou..."
PROCESSOS=$(ps aux | grep gunicorn | grep -v grep)
if [ -z "$PROCESSOS" ]; then
    echo "❌ Gunicorn não iniciou!"
    echo "Verifique os logs:"
    echo "   tail -50 logs/errors.log"
    exit 1
else
    echo "✅ Gunicorn iniciado:"
    echo "$PROCESSOS" | head -3
fi

echo ""
echo "=========================================="
echo "✅ REINÍCIO COMPLETO CONCLUÍDO!"
echo "=========================================="
echo ""
echo "Agora teste o upload novamente."


