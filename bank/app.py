import os
import requests
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)
INVESTMENT_APP_URL = os.environ.get("INVESTMENT_APP_URL", "http://investment-app:5000")
INITIAL_BALANCE = 1000
account = {"holder": "Pedro Ramírez", "balance": INITIAL_BALANCE, "movements": []}

PAGE = """
<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Banca Personal</title>
<style>
body{margin:0;font-family:Inter,Arial,sans-serif;background:#f4f6f8;color:#111827}header{background:#0f172a;color:white;padding:18px 32px}main{max-width:960px;margin:32px auto;padding:0 20px}.card{background:white;border:1px solid #e5e7eb;border-radius:14px;padding:24px;margin-bottom:20px;box-shadow:0 8px 20px rgba(15,23,42,.06)}h1,h2{margin-top:0}.balance{font-size:42px;font-weight:800;color:#065f46;margin:12px 0}label{display:block;margin-bottom:8px;font-weight:600}input{width:100%;box-sizing:border-box;padding:13px;border-radius:10px;border:1px solid #cbd5e1;font-size:17px}button{margin-top:12px;padding:12px 18px;border:0;border-radius:10px;background:#1d4ed8;color:white;font-weight:700;cursor:pointer}.msg{margin-top:12px;min-height:20px}.ok{color:#047857}.err{color:#b91c1c}table{width:100%;border-collapse:collapse}th,td{padding:11px;border-bottom:1px solid #e5e7eb;text-align:left}a{color:#1d4ed8}
</style></head><body><header><h1>Banca Personal</h1></header><main>
<section class="card"><h2>Cuenta bancaria</h2><p>Titular: <strong id="holder"></strong></p><p>Saldo disponible:</p><div class="balance" id="balance">$0 MXN</div></section>
<section class="card"><h2>Transferir a inversiones</h2><form id="transferForm"><label for="amount">Monto</label><input id="amount" type="number" step="1" required><button type="submit">Transferir</button></form><div id="message" class="msg"></div></section>
<section class="card"><h2>Movimientos recientes</h2><table><thead><tr><th>Operación</th><th>Monto</th><th>Saldo</th></tr></thead><tbody id="movements"></tbody></table></section>
</main><script>
async function loadState(){const res=await fetch('/api/state');const data=await res.json();document.getElementById('holder').innerText=data.holder;document.getElementById('balance').innerText=`$${data.balance} MXN`;const tbody=document.getElementById('movements');tbody.innerHTML='';[...data.movements].reverse().slice(0,10).forEach(m=>{const row=document.createElement('tr');row.innerHTML=`<td>${m.type}</td><td>${m.amount}</td><td>${m.balance}</td>`;tbody.appendChild(row);});}
document.getElementById('transferForm').addEventListener('submit',async(event)=>{event.preventDefault();const message=document.getElementById('message');message.className='msg';message.innerText='';const amount=Number(document.getElementById('amount').value);const res=await fetch('/api/transfer-to-investment',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({amount})});const data=await res.json();if(res.ok&&data.status==='ok'){message.className='msg ok';message.innerText='Operación realizada correctamente.';document.getElementById('amount').value='';}else{message.className='msg err';message.innerText=data.message||'No fue posible completar la operación.';}await loadState();});loadState();
</script></body></html>
"""

def movement(mtype, amount):
    account["movements"].append({"type": mtype, "amount": amount, "balance": account["balance"]})

@app.route("/")
def index(): return render_template_string(PAGE)

@app.route("/api/state")
def state(): return jsonify(account)

@app.route("/api/transfer-to-investment", methods=["POST"])
def transfer_to_investment():
    data = request.get_json(force=True, silent=True) or {}
    amount = data.get("amount")
    if not isinstance(amount, (int, float)): return jsonify({"status":"error","message":"Solicitud inválida."}),400
    if amount <= 0: return jsonify({"status":"error","message":"Monto inválido."}),400
    if account["balance"] < amount: return jsonify({"status":"error","message":"Saldo insuficiente."}),400
    account["balance"] -= amount
    try:
        r = requests.post(f"{INVESTMENT_APP_URL}/api/deposits", json={"amount": amount}, timeout=5)
    except requests.RequestException:
        account["balance"] += amount
        return jsonify({"status":"error","message":"Servicio no disponible."}),503
    if r.status_code != 200:
        account["balance"] += amount
        return jsonify({"status":"error","message":"Operación rechazada."}),400
    movement("Transferencia a inversiones", amount)
    return jsonify({"status":"ok"})

@app.route("/api/credits", methods=["POST"])
def credits():
    data = request.get_json(force=True, silent=True) or {}
    amount = data.get("amount")
    if not isinstance(amount, (int, float)): return jsonify({"status":"error","message":"Solicitud inválida."}),400
    if amount <= 0: return jsonify({"status":"error","message":"Monto inválido."}),400
    account["balance"] += amount
    movement("Abono recibido", amount)
    return jsonify({"status":"ok"})

@app.route("/api/reset", methods=["POST"])
def reset():
    account["balance"] = INITIAL_BALANCE
    account["movements"].clear()
    return jsonify({"status":"ok"})

if __name__ == "__main__": app.run(host="0.0.0.0", port=5001, debug=False)
