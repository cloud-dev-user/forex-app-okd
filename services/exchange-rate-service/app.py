from flask import Flask, jsonify, request
app = Flask(__name__)
RATES={("USD","INR"):83.0,("USD","EUR"):0.92,("EUR","INR"):90.3,("INR","USD"):0.012,("JPY","USD"):0.0068}

@app.route("/health")
def health(): return jsonify({"status":"ok"})

@app.route("/rate")
def rate():
    s=request.args.get("from","USD"); d=request.args.get("to","INR")
    r=RATES.get((s,d))
    if r: return jsonify({"from":s,"to":d,"rate":r})
    inv=RATES.get((d,s))
    if inv: return jsonify({"from":s,"to":d,"rate":1.0/inv})
    return jsonify({"error":"rate not found"}),404

if __name__=="__main__": app.run(host="0.0.0.0",port=5001)
