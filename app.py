import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Mutual Fund Overview & Insights", layout="wide")

st.title("📈 Mutual Fund Overview & Insights")
st.write("Finding funds with high return and low risk")

# ---------- Step 1: Find and read the data file ----------
files = [f for f in os.listdir(".") if f.lower().endswith(".csv")]

if len(files) == 0:
    st.error("No CSV file found. Please upload comprehensive_mutual_funds_data.csv to GitHub next to app.py")
    st.stop()

@st.cache_data
def load_data(name):
    data = pd.read_csv(name)
    data.columns = data.columns.str.strip().str.lower().str.replace(" ", "_")
    return data

df = load_data(files[0])

# ---------- Step 2: Pick columns (guessed automatically) ----------
cols = list(df.columns)
num_cols = list(df.select_dtypes("number").columns)

def guess(words, options, fallback=0):
    for w in words:
        for c in options:
            if w in c:
                return options.index(c)
    return min(fallback, len(options) - 1)

st.sidebar.header("Choose columns")
name_col = st.sidebar.selectbox("Fund name", cols, index=guess(["scheme", "name"], cols))
ret_col = st.sidebar.selectbox("Return column", num_cols, index=guess(["return", "3yr", "cagr"], num_cols))
risk_col = st.sidebar.selectbox("Risk column", num_cols, index=guess(["sd", "risk", "std", "volatil"], num_cols, 1))

cat_options = ["(none)"] + [c for c in cols if df[c].nunique() < 60 and c not in num_cols]
cat_col = st.sidebar.selectbox("Category column (optional)", cat_options, index=guess(["category"], cat_options))

# ---------- Step 3: Clean the data ----------
df = df.dropna(subset=[ret_col, risk_col]).copy()

if cat_col != "(none)":
    chosen = st.sidebar.multiselect("Filter by category", df[cat_col].unique(), default=df[cat_col].unique())
    df = df[df[cat_col].isin(chosen)]

# ---------- Step 4: Score = return divided by risk ----------
df["score"] = df[ret_col] / df[risk_col].replace(0, pd.NA)
top30 = df.sort_values("score", ascending=False).head(30)

# ---------- Step 5: Big numbers ----------
c1, c2, c3 = st.columns(3)
c1.metric("Total Funds", f"{len(df):,}")
c2.metric("Average Return", f"{df[ret_col].mean():.2f}")
c3.metric("Average Risk", f"{df[risk_col].mean():.2f}")

st.divider()

# ---------- Step 6: Charts ----------
st.subheader("Return vs Risk (every dot is one fund)")
st.scatter_chart(df, x=risk_col, y=ret_col)

st.subheader("Top 30 Funds (high return, low risk)")
st.bar_chart(top30.set_index(name_col)["score"])

if cat_col != "(none)":
    st.subheader("Average Return by Category")
    st.bar_chart(df.groupby(cat_col)[ret_col].mean().sort_values(ascending=False))

# ---------- Step 7: Top 30 table + download ----------
st.subheader("Top 30 Funds Table")
st.dataframe(top30)

st.download_button(
    "⬇️ Download Top 30 as CSV",
    top30.to_csv(index=False).encode("utf-8"),
    "top_30_funds.csv",
    "text/csv",
)
