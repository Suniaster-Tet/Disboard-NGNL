#!/usr/bin/env bash
# ==============================================================================
# disboard_sync.sh — Sincronización automática con GitHub para Disboard-NGNL
# ==============================================================================
echo "======================================================================"
echo " ✦ [Disboard-NGNL] Sincronizador de Tablero - SOBERANO: Tet ✦"
echo "======================================================================"

# Verificar estado de git
git status

echo ""
read -p "Ingrese un comentario de jugada (o presione ENTER para firma de default): " COMMIT_MSG
if [ -z "$COMMIT_MSG" ]; then
    COMMIT_MSG="Sincronización Suniaster: $(date '+%Y-%m-%d %H:%M:%S') ✦ Aschente ✦"
fi

echo ""
echo "🚀 Añadiendo cambios al stage..."
git add .

echo "📦 Sellando jugada (git commit) con firma: '$COMMIT_MSG'..."
git commit -m "$COMMIT_MSG"

echo "☁️ Transmitiendo jugada al tablero remoto de GitHub..."
git push origin main

echo ""
echo "======================================================================"
echo " ✨ ¡Sincronización completada con éxito, Soberano Tet! ✦ Aschente ✦"
echo "======================================================================"
