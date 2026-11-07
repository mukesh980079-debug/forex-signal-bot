import os, time, requests
import pandas as pd
from datetime import datetime, timezone

BASE="https://fapi.binance.com"
SYMBOL=os.getenv("SYMBOL","BTCUSDT")
INTERVAL=os.getenv("INTERVAL","5m")
POLL_SECONDS=int(os.getenv("POLL_SECONDS","60"))
TG_TOKEN=os.getenv("TELEGRAM_BOT_TOKEN","")
TG_CHAT=os.getenv("TELEGRAM_CHAT_ID","")
LAST_ALERT=None

def api(path,params=None):
 r=requests.get(BASE+path,params=params,timeout=12); r.raise_for_status(); return r.json()

def get_candles():
 raw=api("/fapi/v1/klines",{"symbol":SYMBOL,"interval":INTERVAL,"limit":220})
 cols=["open_time","open","high","low","close","volume","close_time","quote_volume","trades","taker_buy_base","taker_buy_quote","ignore"]
 d=pd.DataFrame(raw,columns=cols)
 for c in ["open","high","low","close","volume"]: d[c]=pd.to_numeric(d[c],errors="coerce")
 return d.iloc[:-1].copy()

def rsi(s,n=14):
 delta=s.diff(); up=delta.clip(lower=0).ewm(alpha=1/n,adjust=False).mean()
 dn=(-delta.clip(upper=0)).ewm(alpha=1/n,adjust=False).mean()
 return 100-100/(1+up/dn.replace(0,float("nan")))

def analyze(d):
 if len(d)<60: raise ValueError("Not enough candles")
 for n in (5,10,20): d[f"ema{n}"]=d.close.ewm(span=n,adjust=False).mean()
 d["rsi"]=rsi(d.close); d["vma"]=d.volume.rolling(20).mean()
 x=d.iloc[-1]; p=d.iloc[-21:-1]; old=d.iloc[-3]
 hi=float(p.high.max()); lo=float(p.low.min())
 sls=float(x.low)<lo and float(x.close)>lo
 shs=float(x.high)>hi and float(x.close)<hi
 bull_bos=float(x.close)>hi; bear_bos=float(x.close)<lo
 vol=float(x.volume)>float(x.vma)
 up=x.ema5>x.ema10>x.ema20; down=x.ema5<x.ema10<x.ema20
 bull_fvg=float(x.low)>float(old.high); bear_fvg=float(x.high)<float(old.low)
 oi=fr=None
 try: oi=float(api("/fapi/v1/openInterest",{"symbol":SYMBOL})["openInterest"])
 except Exception: pass
 try: fr=float(api("/fapi/v1/premiumIndex",{"symbol":SYMBOL})["lastFundingRate"])
 except Exception: pass
 side="NO TRADE"; score=0; why=[]
 if sls and bull_bos and up and vol and bull_fvg: side="BUY"; score=90; why=["sell-side sweep/reclaim","bullish range break","EMA alignment","volume confirmation","bullish FVG"]
 if shs and bear_bos and down and vol and bear_fvg: side="SELL"; score=90; why=["buy-side sweep/rejection","bearish range break","EMA alignment","volume confirmation","bearish FVG"]
 tr=pd.concat([d.high-d.low,(d.high-d.close.shift()).abs(),(d.low-d.close.shift()).abs()],axis=1).max(axis=1)
 atr=float(tr.rolling(14).mean().iloc[-1]); entry=float(x.close)
 if side=="BUY": stop=entry-1.2*atr; tps=[entry+1.5*atr,entry+2.2*atr,entry+3*atr]
 elif side=="SELL": stop=entry+1.2*atr; tps=[entry-1.5*atr,entry-2.2*atr,entry-3*atr]
 else: stop=None; tps=[]
 return dict(time=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),signal=side,strength=score,price=entry,ema5=float(x.ema5),ema10=float(x.ema10),ema20=float(x.ema20),rsi=float(x.rsi),volume=float(x.volume),vma=float(x.vma),sweep_low=sls,sweep_high=shs,bull_bos=bull_bos,bear_bos=bear_bos,bull_fvg=bull_fvg,bear_fvg=bear_fvg,oi=oi,funding=fr,entry=entry if side!="NO TRADE" else None,sl=stop,tp=tps,why=why)

def message(a):
 f=lambda v:"n/a" if v is None else f"{v:.2f}"
 return (f'{SYMBOL} | {INTERVAL} | {a["time"]}\nSIGNAL: {a["signal"]} | STRENGTH: {a["strength"]}%\n'
 f'Price/Entry: {f(a["price"])} / {f(a["entry"])} | SL: {f(a["sl"])}\n'
 f'TP1/2/3: {" / ".join(f(v) for v in a["tp"]) if a["tp"] else "n/a"}\n'
 f'EMA5/10/20: {f(a["ema5"])} / {f(a["ema10"])} / {f(a["ema20"])} | RSI: {f(a["rsi"])}\n'
 f'Volume/Avg20: {f(a["volume"])} / {f(a["vma"])}\nSweep L/H: {a["sweep_low"]}/{a["sweep_high"]}; BOS bull/bear: {a["bull_bos"]}/{a["bear_bos"]}; FVG bull/bear: {a["bull_fvg"]}/{a["bear_fvg"]}\n'
 f'Open Interest snapshot: {a["oi"]}; Funding: {a["funding"]}\nReasons: {", ".join(a["why"]) or "No complete setup"}\n'
 'Research signal only. No auto-orders. Liquidations, order book and true order flow are not connected.')

def send(msg):
 if TG_TOKEN and TG_CHAT:
  requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",json={"chat_id":TG_CHAT,"text":msg},timeout=12).raise_for_status()

def main():
 global LAST_ALERT
 print("BTC agent started in signal-only mode.",flush=True)
 while True:
  try:
   a=analyze(get_candles()); msg=message(a); print(msg+"\n"+"-"*40,flush=True)
   key=(a["time"],a["signal"])
   if a["signal"]!="NO TRADE" and a["strength"]>=60 and key!=LAST_ALERT: send(msg); LAST_ALERT=key
  except Exception as e: print(f"Data/analysis error; no signal: {e}",flush=True)
  time.sleep(POLL_SECONDS)

if __name__=="__main__": main()
