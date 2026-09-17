import pandas as pd, json
def nas(f):
    r=json.load(open(f))["data"]["tradesTable"]["rows"]; df=pd.DataFrame(r)
    df["date"]=pd.to_datetime(df.date,format="%m/%d/%Y")
    for c in ["close","open","high","low","volume"]:
        df[c]=pd.to_numeric(df[c].str.replace("$","").str.replace(",",""),errors="coerce")
    return df.set_index("date").sort_index()
