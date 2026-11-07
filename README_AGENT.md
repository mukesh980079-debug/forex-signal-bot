BTC AI Agent signal-only starter

Uses public Binance USD-M Futures candles, current open-interest snapshot and funding snapshot. Computes EMA 5/10/20, RSI, volume average, simple 20-candle sweep/reclaim, range break and three-candle FVG approximation.

Safety: no exchange keys, no order execution. BUY/SELL only when sweep + matching range break + EMA alignment + above-average volume + matching FVG agree; otherwise NO TRADE. Experimental, not proven profitable. Test on demo. OI is only a snapshot, not a trend. Liquidation feed, order-book depth, CVD/true order flow, news and robust order-block detection are NOT connected. SL/TP are ATR reference levels, not guaranteed fills.

Run with Python 3.10+: pip install -r requirements-agent.txt ; python agent.py

Optional Telegram: set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID as private environment variables in your host. Never commit real tokens. This branch is not deployed or running 24/7; a host/worker with outbound HTTPS and private environment variables is still required.
