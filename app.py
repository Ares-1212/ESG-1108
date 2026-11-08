import io

import pandas as pd
import requests
import streamlit as st
import urllib3

# verify=False 會產生警告，這裡關閉警告訊息
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="公開資訊觀測站資料", page_icon="📊", layout="wide")

DEFAULT_URL = "https://mopsfin.twse.com.tw/opendata/t187ap46_O_1.csv"  # 換連結


@st.cache_data(ttl=3600, show_spinner="資料下載中...")
def load_data(url: str, verify_ssl: bool) -> pd.DataFrame:
    """下載 CSV 並轉成 DataFrame（直接從記憶體讀取，不寫入檔案）"""
    response = requests.get(url, verify=verify_ssl, timeout=30)
    response.raise_for_status()
    df = pd.read_csv(io.BytesIO(response.content), encoding="utf-8-sig")  # 繁體中文
    df = df.dropna()
    return df


# ---------------------------- 側邊欄 ----------------------------
st.sidebar.header("設定")
url = st.sidebar.text_input("CSV 連結", value=DEFAULT_URL)
verify_ssl = st.sidebar.checkbox(
    "驗證 SSL 憑證", value=False, help="原程式使用 verify=False；若來源憑證正常可勾選"
)
if st.sidebar.button("🔄 重新載入資料"):
    st.cache_data.clear()
    st.rerun()

# ---------------------------- 主畫面 ----------------------------
st.title("📊 公開資訊觀測站 開放資料")
st.caption(f"資料來源：{url}")

try:
    df = load_data(url, verify_ssl)
except requests.exceptions.RequestException as e:
    st.error(f"下載資料失敗：{e}")
    st.stop()
except Exception as e:
    st.error(f"資料處理失敗：{e}")
    st.stop()

col1, col2 = st.columns(2)
col1.metric("資料筆數", f"{len(df):,}")
col2.metric("欄位數", f"{df.shape[1]:,}")

# 關鍵字搜尋（搜尋所有欄位）
keyword = st.text_input("🔍 關鍵字搜尋", placeholder="輸入公司代號、名稱或其他關鍵字")
if keyword:
    mask = df.astype(str).apply(
        lambda col: col.str.contains(keyword, case=False, na=False)
    ).any(axis=1)
    view_df = df[mask]
else:
    view_df = df

st.write(f"顯示 {len(view_df):,} 筆")
st.dataframe(view_df, use_container_width=True, hide_index=True)

# 下載按鈕（utf-8-sig 讓 Excel 開啟中文不亂碼）
st.download_button(
    label="⬇️ 下載 CSV",
    data=view_df.to_csv(index=False).encode("utf-8-sig"),
    file_name="data01.csv",
    mime="text/csv",
)
