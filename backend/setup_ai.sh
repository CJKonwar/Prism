#!/bin/bash

echo "🚀 Setting up AI Assistant for Prism..."
echo ""

# Check if we're in the correct directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found. Please run from backend directory."
    exit 1
fi

# Install google-genai
echo "📦 Installing google-genai..."
pip install google-genai

if [ $? -ne 0 ]; then
    echo "❌ Failed to install google-genai"
    exit 1
fi

echo "✓ google-genai installed successfully"
echo ""

# Check for API key
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "⚠️  GOOGLE_API_KEY not set!"
    echo ""
    echo "To set your API key:"
    echo "1. Get your key from: https://aistudio.google.com/apikey"
    echo "2. Run: export GOOGLE_API_KEY='your-api-key-here'"
    echo "3. Add to ~/.zshrc to make it permanent:"
    echo "   echo 'export GOOGLE_API_KEY=\"your-key\"' >> ~/.zshrc"
    echo ""
    read -p "Enter your Google API key now (or press Enter to skip): " api_key
    
    if [ ! -z "$api_key" ]; then
        export GOOGLE_API_KEY="$api_key"
        echo "✓ API key set for this session"
        echo ""
        echo "To make it permanent, add to ~/.zshrc:"
        echo "export GOOGLE_API_KEY=\"$api_key\""
    else
        echo "⏭️  Skipped. Set GOOGLE_API_KEY before running Prism."
    fi
else
    echo "✓ GOOGLE_API_KEY is already set"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Make sure GOOGLE_API_KEY is set (if not already done)"
echo "2. Run Prism: python run_with_gui.py"
echo "3. AI assistant will analyze your productivity every 30 seconds"
echo ""
echo "For more info, see AI_SETUP.md"
