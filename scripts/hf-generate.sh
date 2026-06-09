#!/bin/bash
# Higgsfield CLI wrapper — generates images and auto-downloads to the client's folder
#
# Usage:
#   ./scripts/hf-generate.sh <client-folder> <model> [--prompt "..."] [other flags]
#
# Examples:
#   ./scripts/hf-generate.sh AstroPaws marketing_studio_image --prompt "A 1080x1080 ad..." --aspect-ratio 1:1 --image ./photo.png
#   ./scripts/hf-generate.sh FoundationsTreeExperts nano_banana_2 --prompt "Before and after tree removal" --wait
#
# Outputs are saved to: <client-folder>/ads/creatives/generated/

HF_CLI="C:/Users/joshh/AppData/Roaming/npm/node_modules/@higgsfield/cli/vendor/hf.exe"

CLIENT_DIR="$1"
shift

if [ -z "$CLIENT_DIR" ]; then
    echo "Usage: ./scripts/hf-generate.sh <client-folder> <model> [flags]"
    echo ""
    echo "Available client folders:"
    ls -d */ 2>/dev/null | grep -v scripts | grep -v .git
    exit 1
fi

OUTPUT_DIR="${CLIENT_DIR}/ads/creatives/generated"
mkdir -p "$OUTPUT_DIR"

echo "Generating for: $CLIENT_DIR"
echo "Output dir: $OUTPUT_DIR"
echo ""

# Run the generation with --wait and --json to get the result URL
RESULT=$("$HF_CLI" generate create "$@" --wait --json 2>&1)

if [ $? -ne 0 ]; then
    echo "Generation failed:"
    echo "$RESULT"
    exit 1
fi

# Extract result URLs and download each one
echo "$RESULT" | python3 -c "
import sys, json

try:
    data = json.load(sys.stdin)
except:
    print('Could not parse JSON response')
    sys.exit(1)

# Handle both single job and array response
jobs = data if isinstance(data, list) else [data]

for job in jobs:
    url = job.get('result_url', '')
    job_id = job.get('id', 'unknown')
    model = job.get('job_set_type', job.get('display_name', 'unknown'))
    status = job.get('status', 'unknown')

    if status != 'completed':
        print(f'  Job {job_id}: {status} (skipped)')
        continue

    if url:
        # Extract extension from URL
        ext = url.split('.')[-1].split('?')[0]
        if ext not in ('png', 'jpg', 'jpeg', 'webp', 'mp4'):
            ext = 'png'
        filename = f'{model}-{job_id[:8]}.{ext}'
        print(f'  Downloading: {filename}')
        print(f'  URL: {url}')
        print(f'  FILENAME:{filename}')
        print(f'  URL_RAW:{url}')
" | while IFS= read -r line; do
    if [[ "$line" == *"URL_RAW:"* ]]; then
        URL="${line#*URL_RAW:}"
        # Get the filename from the previous line
        FILENAME="$LAST_FILENAME"
        if [ -n "$URL" ] && [ -n "$FILENAME" ]; then
            curl -4 -L -s -o "${OUTPUT_DIR}/${FILENAME}" "$URL"
            echo "  Saved: ${OUTPUT_DIR}/${FILENAME}"
        fi
    elif [[ "$line" == *"FILENAME:"* ]]; then
        LAST_FILENAME="${line#*FILENAME:}"
    else
        echo "$line"
    fi
done

echo ""
echo "Done. Files in: $OUTPUT_DIR"
ls -la "$OUTPUT_DIR"/*.{png,jpg,mp4} 2>/dev/null | tail -5
