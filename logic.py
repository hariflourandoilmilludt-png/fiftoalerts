from datetime import datetime
from database import TradeState, Instrument
from telegram_bot import send_telegram_message

def process_signal(payload, db):
    """
    Process incoming webhook signal from TradingView.
    Payload expected format:
    {
        "symbol": "NIFTY",
        "signal": "ENTRY_LONG" | "ENTRY_SHORT" | "EXIT_LONG" | "EXIT_SHORT",
        "price": "19500",
        "timestamp": "2023-10-27T10:15:00Z" (Candle Time)
    }
    """
    symbol = payload.get("symbol")
    signal_type = payload.get("signal")
    price = payload.get("price")
    candle_timestamp = payload.get("timestamp") # This is crucial for FLIP detection
    
    if not all([symbol, signal_type, candle_timestamp]):
        return {"status": "error", "message": "Missing required fields"}

    # specific normalization for symbol if needed (e.g. remove exchange prefix)
    
    # 1. Check if Instrument is Active
    instrument = db.query(Instrument).filter(Instrument.symbol == symbol, Instrument.active == True).first()
    if not instrument:
        return {"status": "ignored", "message": f"Instrument {symbol} is not tracked or inactive."}

    # 2. Get Current State
    state = db.query(TradeState).filter(TradeState.symbol == symbol).first()
    if not state:
        state = TradeState(symbol=symbol)
        db.add(state)
        db.commit() # Ensure we have an ID
        db.refresh(state)

    timestamp_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    
    # --- FLIP ENTRY LOGIC ---
    # Detailed Requirement:
    # "if close at 10.15 ... after that again 10.15 candle show sell entry means we just closed that candle gives sell means called flip"
    # Action: DO NOT ENTER (Ignore Entry)
    
    is_entry = "ENTRY" in signal_type.upper()
    is_exit = "EXIT" in signal_type.upper()

    if is_exit:
        if state.current_status != "NONE":
            # Just Close
            old_status = state.current_status
            state.current_status = "NONE"
            state.last_action_time = datetime.utcnow()
            # RECORD THE CANDLE TIME OF CLOSE
            state.last_candle_timestamp = candle_timestamp 
            state.last_signal_price = price
            
            db.commit()
            
            # Send Notification
            msg = f"🔴 <b>TRADE CLOSED</b>\nSymbol: {symbol}\nAction: Closed {old_status}\nPrice: {price}\nCandle Time: {candle_timestamp}"
            send_telegram_message(msg)
            return {"status": "success", "message": "Trade Closed"}
        else:
             return {"status": "ignored", "message": "No open trade to close."}

    elif is_entry:
        # Check for FLIP (Entry on same candle as Close)
        if state.last_candle_timestamp == candle_timestamp:
            # This is a FLIP ENTRY - IGNORE IT
            warning_msg = f"⚠️ <b>FLIP ENTRY DETECTED - NO TRADE</b>\nSymbol: {symbol}\nReason: Signal on same candle as Exit ({candle_timestamp}).\nAction: IGNORED."
            send_telegram_message(warning_msg)
            return {"status": "ignored", "message": "Flip Entry Detected - Ignored"}
            
        # Normal Entry Logic
        new_status = "LONG" if "LONG" in signal_type.upper() else "SHORT"
        
        # If already in same trade, ignore or update? Assuming ignore for now unless "Add" logic needed.
        if state.current_status == new_status:
             return {"status": "ignored", "message": f"Already {new_status}."}
        
        # If in OPPOSITE trade (e.g. LONG -> SHORT switch without explicit exit first)
        # Some strategies send Reverse signal directly. User said: "close signal came... then entry". 
        # So we assume explicit close comes first. If we receive ENTRY while OPEN opposite, we might need to Auto-Close first.
        # For safety strictly following "Close then Entry" pattern from user description.
        if state.current_status != "NONE" and state.current_status != new_status:
             # Implicit Flip (Reversal) - If user sends just "ENTRY SHORT" while "LONG".
             # But user emphasized specific "Flip" logic relating to same candle.
             # I will treat this as a Reversal (Close + Open), unless timestamps match.
             pass 

        state.current_status = new_status
        state.last_action_time = datetime.utcnow()
        state.last_candle_timestamp = candle_timestamp
        state.last_signal_price = price
        
        db.commit()
        
        color_emoji = "🟢" if new_status == "LONG" else "🔴"
        msg = f"{color_emoji} <b>NEW TRADE ENTRY</b>\nSymbol: {symbol}\nDirection: {new_status}\nPrice: {price}\nCandle Time: {candle_timestamp}\nTime: {timestamp_str}"
        send_telegram_message(msg)
        
        return {"status": "success", "message": f"Entered {new_status}"}

    return {"status": "error", "message": "Unknown Signal Type"}
