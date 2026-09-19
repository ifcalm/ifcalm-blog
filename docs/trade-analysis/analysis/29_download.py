"""第 29 篇要用的新数据：无风险利率。其余数据在第 3、19、28 篇已经下载过。"""
from talab import data as D

path = D.download_fred_series("DTB3", start="2016-01-01")
series = D.load_fred_series(path)
print(f"{path}：{path.stat().st_size / 1024:.1f} KB，{len(series)} 个工作日，"
      f"{series.index[0].date()} 到 {series.index[-1].date()}")
print(f"最低 {series.min():.2%}（{series.idxmin().date()}）、最高 {series.max():.2%}（{series.idxmax().date()}）")
print(series.resample("1YE").mean().to_frame("当年平均").round(4).to_string())
