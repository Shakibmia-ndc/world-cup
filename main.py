import os
import requests
from flask import Flask, Response, stream_with_context, request

app = Flask(__name__)

# এই ভেরিয়েবলে আপনার লোকাল পিসির টানেল ইউআরএল সেট হবে (আমরা পার্ট ২-এ এটি পাবো)
TUNNEL_URL = os.environ.get("TUNNEL_URL", "http://localhost:8090")

@app.route('/live/tsports.m3u8')
def proxy_m3u8():
    # মেইন প্লেলিস্ট ফাইলটি রিকোয়েস্ট করা
    target_url = f"{TUNNEL_URL}/hls/tsportshd3rd.m3u8"
    try:
        req = requests.get(target_url, timeout=10)
        content = req.text
        
        # গুরুত্বপূর্ণ ট্রিকস: .ts ফাইলগুলোর পাথ যেন আমাদের রেলওয়ে সার্ভার হয়ে যায়
        base_proxy_url = request.host_url + "live/"
        modified_content = content.replace("tsportshd3rd", f"{base_proxy_url}tsportshd3rd")
        
        response = Response(modified_content, content_type='application/x-mpegURL')
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    except Exception as e:
        return f"Source Offline: {str(e)}", 502

@app.route('/live/<filename>')
def proxy_segments(filename):
    # ভিডিওর ছোট টুকরোগুলো (.ts) প্রক্সি করা
    target_url = f"{TUNNEL_URL}/hls/{filename}"
    try:
        req = requests.get(target_url, stream=True, timeout=10)
        def generate():
            for chunk in req.iter_content(chunk_size=4096):
                yield chunk
        
        response = Response(stream_with_context(generate()), status=req.status_code)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Content-Type'] = 'video/MP2T'
        return response
    except Exception as e:
        return f"Segment Error: {str(e)}", 502

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
