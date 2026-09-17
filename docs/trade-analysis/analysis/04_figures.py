import sys, glob
import numpy as np, pandas as pd, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from talab import data as D, plot as P
out=sys.argv[1]; P.use_chinese_font()
btc=D.load_binance_klines(glob.glob("data/binance/spot/BTCUSDT/1d/*.zip"))
agg={"open":"first","high":"max","low":"min","close":"last","volume":"sum"}
wk=btc.resample("W-MON",label="left",closed="left").agg(agg).dropna()
for log,name,title in [(False,"bear-linear.png","BTCUSDT 周线（2017-08 至 2026-08）"),(True,"bear-log.png","BTCUSDT 周线，对数坐标（2017-08 至 2026-08）")]:
    fig,ax,av=P.plot_candles(wk,title=title,volume=False,log=log,figsize=(10,5))
    if log:
        for t,p,txt in [("2017-12-11",19798.68*1.3,"跌 84.1%"),("2021-11-08",69000*1.3,"跌 77.6%"),("2025-10-06",126199.63*1.3,"跌 54.2%")]:
            i=wk.index.get_indexer([pd.Timestamp(t,tz="UTC")])[0]; ax.text(i,p,txt,ha="center",fontsize=10,color="#333")
        ax.set_ylim(top=126199.63*1.6)
    fig.savefig(f"{out}/{name}"); plt.close(fig)
open(f"{out}/hand-drawn.svg","w").write(P.candles_svg(btc.loc["2020-03-01":"2020-03-31"]))
x=btc.loc["2025-09-01":"2026-05-15"]
t1,p1=pd.Timestamp("2025-10-06",tz="UTC"),btc.high["2025-10-06"]; t2,p2=pd.Timestamp("2026-01-14",tz="UTC"),btc.high["2026-01-14"]
a=(x.index-t1)/(t2-t1); lin=pd.Series(p1+(p2-p1)*a,index=x.index); lg=pd.Series(np.exp(np.log(p1)+(np.log(p2)-np.log(p1))*a),index=x.index)
lin[x.index<t1]=np.nan; lg[x.index<t1]=np.nan
for log,name,line,brk,lab in [(False,"trend-linear.png",lin,"2026-04-13","两点连线（算术坐标下的直线）"),(True,"trend-log.png",lg,"2026-04-22","两点连线（对数坐标下的直线）")]:
    fig,ax,av=P.plot_candles(x,title=f"BTCUSDT 日线：连接 2025-10-06 与 2026-01-14 两个高点（{'对数' if log else '算术'}坐标）",volume=False,log=log,overlays={lab:line},marks=[(brk,x.low[brk],f"{brk} 收盘突破")],figsize=(10,5))
    fig.savefig(f"{out}/{name}"); plt.close(fig)
spy=D.load_nasdaq_daily("data/nasdaq/SPY_historical.json").loc["2025-12-15":"2026-01-16"]
for ta,name in [("real","spy-real-time.png"),("bars","spy-bars.png")]:
    fig,ax,av=P.plot_candles(spy,title=f"SPY 日线（{'按真实时间排列' if ta=='real' else '每根 K 线等距排列'}）",time_axis=ta,figsize=(10,5))
    fig.savefig(f"{out}/{name}"); plt.close(fig)
fig,ax,av=P.plot_candles(btc.loc["2020-03-01":"2020-03-31"],title="BTCUSDT 日线（2020 年 3 月），用 talab.plot 画",figsize=(10,5))
fig.savefig(f"{out}/talab-plot.png"); plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(10,3.5),dpi=150)
sm=btc.loc["2020-03-05":"2020-03-20"]
for ax,st,tt in [(axs[0],"international","国际惯例：涨绿跌红"),(axs[1],"china","中国大陆惯例：涨红跌绿")]:
    c=P.STYLES[st]
    for i,(o,h,l,cl) in enumerate(sm[["open","high","low","close"]].itertuples(index=False)):
        col=c["up"] if cl>=o else c["down"]; ax.vlines(i,l,h,color=col,lw=0.8); ax.add_patch(matplotlib.patches.Rectangle((i-0.35,min(o,cl)),0.7,abs(cl-o),color=col))
    ax.autoscale_view(); ax.set_title(tt,fontsize=11); ax.set_xticks([]); ax.grid(alpha=.25)
fig.tight_layout(); fig.savefig(f"{out}/color-styles.png"); plt.close(fig)
print("ok")
