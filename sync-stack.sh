#!/bin/bash
echo "⚔️ Initializing Sovereign Stack Sync..."

# Verify Types
if [ -f "src/x402/types.ts" ]; then
    echo "✅ Types detected."
else
    echo "❌ Missing types.ts - check your mount points."
    exit 1
fi

# Atomic Push
git add .
git commit -m "feat: upgrade x402 facilitator to class-based engine & harden tracking"
git push origin patch-2

echo "🚀 Stack synchronized. Monitor Cursor Bugbot for green checks."
