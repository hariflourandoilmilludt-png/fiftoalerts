import os
import unittest
from datetime import datetime
from database import engine, SessionLocal, Base, Instrument, TradeState
from logic import process_signal

# Mock Telegram to avoid actual network calls
import telegram_bot
def mock_send_message(msg):
    print(f"[MOCK TELEGRAM] {msg}")
    return True
telegram_bot.send_telegram_message = mock_send_message

class TestTradingLogic(unittest.TestCase):
    def setUp(self):
        # Create in-memory DB for testing
        Base.metadata.create_all(bind=engine)
        self.db = SessionLocal()
        
        # Add Instrument
        inst = Instrument(symbol="NIFTY", timeframe="15m")
        self.db.add(inst)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=engine)

    def test_normal_cycle(self):
        print("\n--- TEST NORMAL CYCLE ---")
        # 1. Entry
        payload = {
            "symbol": "NIFTY",
            "signal": "ENTRY_LONG",
            "price": "19500",
            "timestamp": "2023-10-27T10:00:00Z"
        }
        res = process_signal(payload, self.db)
        self.assertEqual(res['status'], 'success')
        self.assertIn("Entered LONG", res['message'])

        # 2. Exit (Different Candle)
        payload['signal'] = "EXIT_LONG"
        payload['timestamp'] = "2023-10-27T10:15:00Z" # Next candle
        res = process_signal(payload, self.db)
        self.assertEqual(res['status'], 'success')
        self.assertIn("Trade Closed", res['message'])

    def test_flip_scenario(self):
        print("\n--- TEST FLIP SCENARIO (Same Candle) ---")
        # 1. Start with OPEN Trade
        state = TradeState(symbol="NIFTY", current_status="LONG")
        self.db.add(state)
        self.db.commit()

        # 2. Receive Close Signal at 10:15
        close_time = "2023-10-27T10:15:00Z"
        payload_close = {
            "symbol": "NIFTY",
            "signal": "EXIT_LONG",
            "price": "19600",
            "timestamp": close_time
        }
        res = process_signal(payload_close, self.db)
        self.assertEqual(res['status'], 'success')

        # 3. Receive Entry Signal at same 10:15 candle (FLIP)
        payload_entry = {
            "symbol": "NIFTY",
            "signal": "ENTRY_SHORT",
            "price": "19580",
            "timestamp": close_time # SAME TIMESTAMP
        }
        res_flip = process_signal(payload_entry, self.db)
        
        # EXPECTATION: IGNORED
        self.assertEqual(res_flip['status'], 'ignored')
        self.assertIn("Flip Entry Detected", res_flip['message'])
        print(f"Flip Test Result: {res_flip['message']}")

if __name__ == '__main__':
    unittest.main()
