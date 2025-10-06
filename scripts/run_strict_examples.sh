#!/bin/bash
# Quick usage examples for strict_populate_training.py

echo "=========================================="
echo "STRICT TRAINING DATA POPULATION EXAMPLES"
echo "=========================================="
echo ""

# Navigate to project directory
cd /Users/Gilby/Projects/MLAudioClassifier

echo "1. VALIDATION ONLY (Preview Results)"
echo "   Shows what would be copied without making changes"
echo ""
echo "   Command: python3 scripts/strict_populate_training.py --validate-only"
echo ""
read -p "Press Enter to run validation..."
python3 scripts/strict_populate_training.py --validate-only

echo ""
echo ""
echo "=========================================="
echo "2. VALIDATION WITH DETAILED LOGS"
echo "   Saves detailed acceptance/rejection logs"
echo ""
echo "   Command: python3 scripts/strict_populate_training.py --validate-only --save-logs"
echo ""
read -p "Press Enter to run with logs..."
python3 scripts/strict_populate_training.py --validate-only --save-logs

echo ""
echo ""
echo "=========================================="
echo "3. COPY FILES TO TRAINING DATA"
echo "   This will actually copy files!"
echo ""
echo "   Command: python3 scripts/strict_populate_training.py --copy"
echo ""
read -p "Press Enter to COPY FILES (or Ctrl+C to cancel)..."
python3 scripts/strict_populate_training.py --copy

echo ""
echo "=========================================="
echo "COMPLETED!"
echo "=========================================="
