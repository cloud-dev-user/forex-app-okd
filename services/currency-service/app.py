from flask import Flask, jsonify, request, render_template
import os, requests

app = Flask(__name__)
SUPPORTED = ["USD","EUR","INR","JPY","GBP"]
EXCHANGE_RATE_URL = os.getenv("EXCHANGE_RATE_URL","http://exchange-rate-service:5001")

@app.route("/")
def home(): return render_template("index.html")

@app.route("/health")
def health(): return jsonify({"status":"ok"})

@app.route("/currencies")
def currencies(): return jsonify({"currencies":SUPPORTED})

@app.route("/convert")
def convert():
    src=request.args.get("from","USD"); dst=request.args.get("to","INR")
    amt=float(request.args.get("amount","1"))
    try:
        r=requests.get(f"{EXCHANGE_RATE_URL}/rate?from={src}&to={dst}",timeout=2)
        if r.status_code==200: rate=r.json().get("rate",1.0); return jsonify({"from":src,"to":dst,"amount":amt,"converted":amt*rate})
    except Exception as e: return jsonify({"error":str(e)}),502
    return jsonify({"error":"rate unavailable"}),502

if __name__=="__main__": app.run(host="0.0.0.0",port=5000)
