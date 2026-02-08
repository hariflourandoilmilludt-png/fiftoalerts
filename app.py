from flask import Flask, request, jsonify, render_template, redirect, url_for
from database import engine, SessionLocal, init_db, Instrument, TradeState
from logic import process_signal
import os

app = Flask(__name__)
init_db()

def get_db_session():
    return SessionLocal()

@app.route('/')
def dashboard():
    db = get_db_session()
    instruments = db.query(Instrument).all()
    # Get status for each
    data = []
    for inst in instruments:
        state = db.query(TradeState).filter(TradeState.symbol == inst.symbol).first()
        status = state.current_status if state else "NONE"
        last_update = state.last_action_time if state else "N/A"
        data.append({
            "id": inst.id,
            "symbol": inst.symbol,
            "timeframe": inst.timeframe,
            "status": status,
            "last_update": last_update
        })
    db.close()
    return render_template('index.html', instruments=data)

@app.route('/add_instrument', methods=['POST'])
def add_instrument():
    symbol = request.form.get('symbol')
    timeframe = request.form.get('timeframe')
    if symbol and timeframe:
        db = get_db_session()
        # Check if exists
        exists = db.query(Instrument).filter(Instrument.symbol == symbol).first()
        if not exists:
            new_inst = Instrument(symbol=symbol, timeframe=timeframe)
            db.add(new_inst)
            db.commit()
        db.close()
    return redirect(url_for('dashboard'))

@app.route('/delete_instrument/<int:id>')
def delete_instrument(id):
    db = get_db_session()
    inst = db.query(Instrument).filter(Instrument.id == id).first()
    if inst:
        db.delete(inst)
        db.commit()
    db.close()
    return redirect(url_for('dashboard'))

@app.route('/edit_instrument/<int:id>', methods=['POST'])
def edit_instrument(id):
    db = get_db_session()
    inst = db.query(Instrument).filter(Instrument.id == id).first()
    if inst:
        inst.quantman_buy_url = request.form.get('quantman_buy_url')
        inst.quantman_sell_url = request.form.get('quantman_sell_url')
        inst.quantman_close_url = request.form.get('quantman_close_url')
        db.commit()
    db.close()
    return redirect(url_for('dashboard'))

@app.route('/webhook', methods=['POST'])
def webhook():
    payload = request.json
    if not payload:
        return jsonify({"status": "error", "message": "No payload received"}), 400
    
    db = get_db_session()
    try:
        result = process_signal(payload, db)
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        db.close()

@app.route('/webhook/<symbol>/<action>', methods=['POST', 'GET'])
def webhook_simplified(symbol, action):
    """
    Simplified endpoint for users who want to use direct URLs.
    Example: POST /webhook/NIFTY/long
    Query Params (Optional): ?price=19500&timestamp=2023...
    """
    # Map action to signal
    action = action.lower()
    if action in ['long', 'buy', 'entry_long']:
        signal = "ENTRY_LONG"
    elif action in ['short', 'sell', 'entry_short']:
        signal = "ENTRY_SHORT"
    elif action in ['close', 'exit']:
        signal = "EXIT_LONG" # Logic handles this as generic close usually
    else:
        return jsonify({"status": "error", "message": f"Invalid action: {action}"}), 400

    # Get optional params from Query String (for GET/POST)
    price = request.args.get('price', '0')
    timestamp = request.args.get('timestamp')
    
    # If using TradingView placeholders {{timenow}}, they might come as literal strings if not replaced, 
    # but usually TV replaces them. If not provided, use server time? 
    # Logic.py relies on timestamp for Flip detection.
    from datetime import datetime
    if not timestamp:
         timestamp = datetime.utcnow().isoformat()

    payload = {
        "symbol": symbol.upper(),
        "signal": signal,
        "price": price,
        "timestamp": timestamp
    }

    db = get_db_session()
    try:
        result = process_signal(payload, db)
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        db.close()

@app.route('/health')
def health_check():
    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
