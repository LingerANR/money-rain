import os
import requests
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)
BANK_URL = os.environ.get("BANK_URL", "http://localhost:5001")
portfolio = {"client": "Pedro Ramírez", "balance": 0, "movements": []}

PAGE = """
<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Inversiones</title>
<style>
body{margin:0;font-family:Inter,Arial,sans-serif;background:#f4f6f8;color:#111827}header{background:#111827;color:white;padding:18px 32px}main{max-width:960px;margin:32px auto;padding:0 20px}.card{background:white;border:1px solid #e5e7eb;border-radius:14px;padding:24px;margin-bottom:20px;box-shadow:0 8px 20px rgba(17,24,39,.06)}h1,h2{margin-top:0}.balance{font-size:42px;font-weight:800;color:#6d28d9;margin:12px 0}label{display:block;margin-bottom:8px;font-weight:600}input{width:100%;box-sizing:border-box;padding:13px;border-radius:10px;border:1px solid #cbd5e1;font-size:17px}button{margin-top:12px;padding:12px 18px;border:0;border-radius:10px;background:#6d28d9;color:white;font-weight:700;cursor:pointer}.secondary{background:#1d4ed8}.msg{margin-top:12px;min-height:20px}.ok{color:#047857}.err{color:#b91c1c}table{width:100%;border-collapse:collapse}th,td{padding:11px;border-bottom:1px solid #e5e7eb;text-align:left}a{color:#1d4ed8}
</style></head><body><header><h1>Inversiones</h1></header><main>
<section class="card"><h2>Cuenta de inversión</h2><p>Cliente: <strong id="client"></strong></p><p>Saldo disponible:</p><div class="balance" id="balance">$0 MXN</div></section>
<section class="card"><h2>Depositar a cuenta bancaria</h2><form id="withdrawForm"><label for="amount">Monto</label><input id="amount" type="number" step="1" required><button type="submit">Depositar</button></form><div id="message" class="msg"></div></section>
<section class="card"><h2>Movimientos recientes</h2><table><thead><tr><th>Operación</th><th>Monto</th><th>Saldo</th></tr></thead><tbody id="movements"></tbody></table><button class="secondary" id="resetButton">Restablecer demo</button></section>
</main><script>
async function loadState(){const res=await fetch('/api/state');const data=await res.json();document.getElementById('client').innerText=data.investment.client;document.getElementById('balance').innerText=`$${data.investment.balance} MXN`;document.getElementById('bankBalance').innerText=`$${data.bank.balance} MXN`;const tbody=document.getElementById('movements');tbody.innerHTML='';[...data.investment.movements].reverse().slice(0,10).forEach(m=>{const row=document.createElement('tr');row.innerHTML=`<td>${m.type}</td><td>${m.amount}</td><td>${m.balance}</td>`;tbody.appendChild(row);});}
document.getElementById('withdrawForm').addEventListener('submit',async(event)=>{event.preventDefault();const message=document.getElementById('message');message.className='msg';message.innerText='';const amount=Number(document.getElementById('amount').value);const res=await fetch('/api/withdrawals',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({amount})});const data=await res.json();if(res.ok&&data.status==='ok'){message.className='msg ok';message.innerText='Operación realizada correctamente.';document.getElementById('amount').value='';}else{message.className='msg err';message.innerText=data.message||'No fue posible completar la operación.';}await loadState();});
document.getElementById('resetButton').addEventListener('click',async()=>{await fetch('/api/reset-all',{method:'POST'});document.getElementById('message').innerText='';await loadState();});loadState();
</script></body></html>
"""

def get_bank():
    try: return requests.get(f"{BANK_URL}/api/state", timeout=5).json()
    except requests.RequestException: return {"balance":"N/A"}

def movement(mtype, amount):
    portfolio["movements"].append({"type": mtype, "amount": amount, "balance": portfolio["balance"]})

@app.route("/")
def index(): return render_template_string(PAGE)

@app.route("/api/state")
def state(): return jsonify({"investment": portfolio, "bank": get_bank()})

@app.route("/api/deposits", methods=["POST"])
def deposits():
    data = request.get_json(force=True, silent=True) or {}
    amount = data.get("amount")
    if not isinstance(amount, (int, float)): return jsonify({"status":"error","message":"Solicitud inválida."}),400
    if amount <= 0: return jsonify({"status":"error","message":"Monto inválido."}),400
    portfolio["balance"] += amount
    movement("Depósito recibido", amount)
    return jsonify({"status":"ok"})

@app.route("/api/withdrawals", methods=["POST"])
def withdrawals():
    data = request.get_json(force=True, silent=True) or {}
    amount = data.get("amount")
    if not isinstance(amount, (int, float)): return jsonify({"status":"error","message":"Solicitud inválida."}),400
    if portfolio["balance"] < amount: return jsonify({"status":"error","message":"Saldo insuficiente."}),400
    portfolio["balance"] = portfolio["balance"] - amount
    try:
        r = requests.post(f"{BANK_URL}/api/credits", json={"amount": abs(amount)}, timeout=5)
    except requests.RequestException:
        portfolio["balance"] = portfolio["balance"] + amount
        return jsonify({"status":"error","message":"Servicio no disponible."}),503
    if r.status_code != 200:
        portfolio["balance"] = portfolio["balance"] + amount
        return jsonify({"status":"error","message":"Operación rechazada."}),400
    movement("Depósito a banco", amount)
    return jsonify({"status":"ok"})

@app.route("/api/reset", methods=["POST"])
def reset():
    portfolio["balance"] = 0
    portfolio["movements"].clear()
    return jsonify({"status":"ok"})

@app.route("/api/reset-all", methods=["POST"])
def reset_all():
    portfolio["balance"] = 0
    portfolio["movements"].clear()
    try: requests.post(f"{BANK_URL}/api/reset", timeout=5)
    except requests.RequestException: pass
    return jsonify({"status":"ok"})

if __name__ == "__main__": app.run(host="0.0.0.0", port=5000, debug=False)
