#!/bin/bash

# AEM Intelligence Engine - Security Audit Script

PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo ".")
CORE_PATH="$PROJECT_ROOT/core/src/main/java"
DISPATCHER_PATH="$PROJECT_ROOT/dispatcher"

echo "=========================================="
echo "    AEM SECURITY AUDIT - INTELLIGENCE     "
echo "=========================================="
echo "Scanning: $PROJECT_ROOT"
echo ""

FAILURES=0
WARNINGS=0

# 1. Check for AuthorOnlyFilter existence and scope
echo "[CHECK] Verifying AuthorOnlyFilter..."
FILTER_FILE=$(find "$CORE_PATH" -name "AuthorOnlyFilter.java")

if [ -z "$FILTER_FILE" ]; then
    echo "  [FAIL] AuthorOnlyFilter.java not found in core module!"
    FAILURES=$((FAILURES+1))
else
    # Check if it targets /bin/ollama
    if grep -q "/bin/ollama" "$FILTER_FILE"; then
        echo "  [PASS] AuthorOnlyFilter exists and targets /bin/ollama"
    else
        echo "  [FAIL] AuthorOnlyFilter found but does not seem to target /bin/ollama"
        FAILURES=$((FAILURES+1))
    fi
    
    # Check for AIConfiguration usage
    if grep -q "AIConfiguration" "$FILTER_FILE"; then
        echo "  [PASS] AuthorOnlyFilter uses AIConfiguration"
    else
        echo "  [WARN] AuthorOnlyFilter might not be using AIConfiguration for toggles."
        WARNINGS=$((WARNINGS+1))
    fi
fi

echo ""

# 2. Scan for Public Servlets (Basic Regex)
echo "[CHECK] Scanning for potentially exposed servlets..."
# Grep for sling.servlet.paths property
SERVLETS=$(grep -r "sling.servlet.paths" "$CORE_PATH" | grep -v "test")

if [ -z "$SERVLETS" ]; then
    echo "  [INFO] No explicit paths found (Resource Types used? Good)."
else
    echo "$SERVLETS" | while read -r line ; do
        if [[ "$line" == *"/bin/ollama"* ]]; then
             echo "  [INFO] Found Ollama Servlet: $line"
             echo "         -> Relies on AuthorOnlyFilter. Verified in step 1."
        elif [[ "$line" == *"/bin/"* ]]; then
             echo "  [WARN] Potential Public Servlet found: $line"
             echo "         Ensure this is protected or intended for public access."
             WARNINGS=$((WARNINGS+1))
        fi
    done
fi

echo ""

# 3. Check OSGi Configs for Publish Safety
echo "[CHECK] Checking Author OSGi Config..."
AUTHOR_CONFIG=$(find "$PROJECT_ROOT/ui.apps" -name "com.aem.intelligence.core.conf.AIConfiguration.config" | grep "config.author")

if [ -z "$AUTHOR_CONFIG" ]; then
    echo "  [WARN] Author OSGi config not found in config.author!"
    WARNINGS=$((WARNINGS+1))
else
    echo "  [PASS] Author OSGi config checked."
fi

echo ""

# Summary
echo "=========================================="
echo "AUDIT COMPLETE"
echo "Failures: $FAILURES"
echo "Warnings: $WARNINGS"

if [ $FAILURES -gt 0 ]; then
    exit 1
else
    exit 0
fi
