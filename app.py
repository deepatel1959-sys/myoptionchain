from flask import Flask, render_template, jsonify, request, redirect, session
import requests, hashlib, os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'myoptionchain_2024_deep')

APP_ID = "AUW6SUUH3O-100"
SECRET_ID = "YOSOH2F02W"
CLIENT_ID = "FAI59204"
REDIRECT_URI = os.environ.get('REDIRECT_URI', 'https://myoptionchain.onrender.com/callback')
BASE = "https://api-t1.fyers.in/api/v3"

def get_headers():
    return {"Authorization": f"{APP_ID}:{session.get('token', '')}"}

def get_app_hash():
    return hashlib.sha256(f"{APP_ID}:{SECRET_ID}".encode()).hexdigest()

@app.route('/')
def index():
    logged_in = bool(session.get('token'))
    return render_template('index.html', logged_in=logged_in)

@app.route('/auth')
def auth():
    h = get_app_hash()
    auth_url = (
        f"https://api-t1.fyers.in/api/v3/generate-authcode"
        f"?client_id={APP_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&state=myapp"
        f"&nonce={h}"
    )
    return redirect(auth_url)

@app.route('/callback')
def callback():
    auth_code = request.args.get('auth_code') or request.args.get('code')
    if not auth_code:
        return redirect('/?error=nocode')
    try:
        h = get_app_hash()
        response = requests.post(
            f"{BASE}/validate-authcode",
            json={
                "grant_type": "authorization_code",
                "appIdHash": h,
                "code": auth_code
            },
            timeout=15
        )
        data = response.json()
        if data.get('s') == 'ok':
            session['token'] = data['access_token']
            return redirect('/')
        else:
            return redirect(f'/?error={data.get("message", "loginfailed")}')
    except Exception as e:
        return redirect(f'/?error={str(e)}')

@app.route('/set_token', methods=['POST'])
def set_token():
    token = request.json.get('token', '').strip()
    if token:
        session['token'] = token
        return jsonify({"ok": True})
    return jsonify({"ok": False})

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/api/chain')
def chain():
    try:
        sym = request.args.get('sym', 'NSE:NIFTY50-INDEX')
        exp = request.args.get('exp', '')
        params = {"symbol": sym, "strikecount": 20}
        if exp:
            params['timestamp'] = exp
        r = requests.get(f"{BASE}/options/chain", headers=get_headers(), params=params, timeout=10)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"s": "error", "message": str(e)})

@app.route('/api/quote')
def quote():
    try:
        syms = request.args.get('syms', 'NSE:NIFTY50-INDEX')
        r = requests.get(f"{BASE}/quotes", headers=get_headers(), params={"symbols": syms}, timeout=10)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"s": "error", "message": str(e)})

@app.route('/api/history')
def history():
    try:
        params = {k: request.args.get(k) for k in ['symbol', 'resolution', 'date_format', 'range_from', 'range_to']}
        params['cont_flag'] = '1'
        r = requests.get(f"{BASE}/data/history", headers=get_headers(), params=params, timeout=15)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"s": "error", "message": str(e)})

@app.route('/api/status')
def status():
    return jsonify({"logged_in": bool(session.get('token')), "app_id": APP_ID})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"\n✅ App chal rahi hai: http://localhost:{port}\n")
    app.run(host='0.0.0.0', port=port, debug=False)
