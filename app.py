from flask import Flask, jsonify, request
from flask_cors import CORS
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
import re
import os

app = Flask(__name__)
CORS(app)

def extract_video_id(url):
    patterns = [
        r'(?:v=)([a-zA-Z0-9_-]{11})',
        r'(?:youtu\.be\/)([a-zA-Z0-9_-]{11})',
        r'(?:embed\/)([a-zA-Z0-9_-]{11})',
        r'(?:shorts\/)([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

@app.route('/transcript', methods=['GET'])
def get_transcript():
    url = request.args.get('url', '')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    video_id = extract_video_id(url)
    if not video_id:
        return jsonify({'error': 'Invalid YouTube URL'}), 400
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        try:
            transcript = transcript_list.find_manually_created_transcript(['en', 'en-US', 'en-GB'])
        except Exception:
            try:
                transcript = transcript_list.find_generated_transcript(['en', 'en-US', 'en-GB'])
            except Exception:
                transcript = transcript_list.find_generated_transcript(
                    [t.language_code for t in transcript_list]
                )
        data = transcript.fetch()
        formatter = TextFormatter()
        text = formatter.format_transcript(data)
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return jsonify({
            'success': True,
            'transcript': text,
            'word_count': len(text.split()),
            'video_id': video_id,
            'language': transcript.language,
        })
    except Exception as e:
        return jsonify({'error': f'No transcript available: {str(e)}'}), 404

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'Recast API'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
