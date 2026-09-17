import pandas as pd, glob, zipfile
COLS=["open_time","open","high","low","close","volume","close_time","quote_volume","trades","taker_buy_base","taker_buy_quote","ignore"]
def load(pattern):
    fr=[]
    for f in sorted(glob.glob(pattern)):
        with zipfile.ZipFile(f) as z:
            df=pd.read_csv(z.open(z.namelist()[0]),header=None)
        if isinstance(df.iloc[0,0],str): df=df.iloc[1:].reset_index(drop=True)  # header row in some files
        df.columns=COLS; fr.append(df)
    df=pd.concat(fr,ignore_index=True)
    t=df.open_time.astype("int64")
    unit=pd.Series(["ms"]*len(t)); 
    df["time"]=[pd.Timestamp(x,unit="us" if x>1e14 else "ms",tz="UTC") for x in t]
    for c in COLS[1:6]+["quote_volume","taker_buy_base","taker_buy_quote"]: df[c]=df[c].astype(float)
    df["trades"]=df.trades.astype(int)
    return df.set_index("time").drop(columns=["open_time","close_time","ignore"])
