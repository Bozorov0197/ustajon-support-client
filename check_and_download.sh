#!/bin/bash
echo "🔍 Checking for latest release..."

# Wait for build
for i in {1..20}; do
    RELEASE=$(curl -s "https://api.github.com/repos/Bozorov0197/ustajon-support-client/releases/latest" 2>/dev/null)
    TAG=$(echo "$RELEASE" | grep '"tag_name"' | cut -d'"' -f4)
    
    if [[ "$TAG" == *"8.0"* ]]; then
        echo "✅ Found v8.0 release: $TAG"
        
        # Get download URL
        URL=$(echo "$RELEASE" | grep '"browser_download_url"' | grep '.exe' | cut -d'"' -f4 | head -1)
        
        if [ -n "$URL" ]; then
            echo "📥 Downloading from: $URL"
            curl -L -o UstajonSupport_v8.exe "$URL"
            
            if [ -f "UstajonSupport_v8.exe" ]; then
                echo "✅ Downloaded! Size: $(du -h UstajonSupport_v8.exe | cut -f1)"
                
                # Upload to server
                echo "📤 Uploading to VPS..."
                sshpass -p "Bozorov0197" scp UstajonSupport_v8.exe root@31.220.75.75:/root/remote-support/static/scripts/UstajonSupport.exe
                echo "🎉 Done! Check http://31.220.75.75/download"
                exit 0
            fi
        fi
    fi
    
    echo "⏳ Waiting... ($i/20)"
    sleep 30
done

echo "❌ Timeout - check GitHub manually"
