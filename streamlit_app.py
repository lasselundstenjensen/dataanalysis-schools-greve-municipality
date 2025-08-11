
import streamlit as st
import pandas as pd
import numpy as np
import io
import matplotlib.pyplot as plt

st.set_page_config(page_title="Trivsel på skoler – sammenligning", layout="wide")

st.title("Trivsel på skoler – sammenligning")
st.markdown("Upload andet Excel/CSV-datasæt (samme struktur).")

# Data loading
uploaded = st.file_uploader("Upload Excel (.xlsx) eller CSV", type=["xlsx", "csv"], accept_multiple_files=False)
if uploaded is not None:
    if uploaded.name.lower().endswith(".xlsx"):
        df = pd.read_excel(uploaded)
    else:
        df = pd.read_csv(uploaded)
else:
    # Fallback to the bundled CSV
    df = pd.read_csv("school_survey_data.csv")

# Basic validation
expected_cols = {"School", "Category", "Question", "PercentNegative"}
if not expected_cols.issubset(set(df.columns)):
    st.error(f"Datasættet skal have kolonnerne: {sorted(expected_cols)}")
    st.stop()

# Controls
with st.sidebar:
    st.header("Filtre")
    schools = sorted(df["School"].unique().tolist())
    selected_schools = st.multiselect("Vælg skoler", schools, default=schools)
    categories = df["Category"].unique().tolist()
    selected_categories = st.multiselect("Vælg kategorier", categories, default=categories)

df = df[df["School"].isin(selected_schools) & df["Category"].isin(selected_categories)]

st.subheader("Søjlediagrammer (procent negative svar)")
for category in selected_categories:
    subset = df[df["Category"] == category].copy()
    if subset.empty:
        continue
    questions = subset["Question"].unique().tolist()
    schools = subset["School"].unique().tolist()

    # Pivot to wide: rows=questions, cols=schools
    table = subset.pivot_table(index="Question", columns="School", values="PercentNegative", aggfunc="mean").reindex(questions)

    fig = plt.figure(figsize=(14, 6))
    ax = fig.add_subplot(111)

    x = np.arange(len(questions))
    n = len(schools)
    width = min(0.8 / max(n,1), 0.18)  # ensure bars are visible
    for i, school in enumerate(schools):
        vals = table[school].values
        ax.bar(x + (i - (n-1)/2)*width, vals, width=width, label=school)

    ax.set_title(f"{category} - Procent negative svar (alle skoler)")
    ax.set_ylabel("Procent negative svar (%)")
    ax.set_xlabel("Spørgsmål")
    ax.set_xticks(x)
    ax.set_xticklabels(questions, rotation=65, ha="right")
    ax.legend()
    st.pyplot(fig)

st.subheader("Radardiagrammer")
for category in selected_categories:
    subset = df[df["Category"] == category].copy()
    if subset.empty:
        continue
    questions = subset["Question"].unique().tolist()
    angles = np.linspace(0, 2*np.pi, len(questions), endpoint=False).tolist()
    angles += angles[:1]

    fig = plt.figure(figsize=(7,7))
    ax = fig.add_subplot(111, polar=True)
    for school in subset["School"].unique():
        vals = subset[subset["School"] == school]["PercentNegative"].tolist()
        vals += vals[:1]
        ax.plot(angles, vals, label=school)
        ax.fill(angles, vals, alpha=0.1)

    ax.set_theta_offset(np.pi/2)
    ax.set_theta_direction(-1)
    ax.set_thetagrids(np.degrees(angles[:-1]), questions, fontsize=9)
    ax.set_title(f"{category} - Radar Chart", y=1.1)
    ax.legend(loc="upper right", bbox_to_anchor=(1.2, 1.1), fontsize=8)
    st.pyplot(fig)

st.subheader("Heatmap (alle valgte skoler og kategorier)")
# Build heatmap using matplotlib's imshow (no seaborn)
heat = df.pivot_table(index=["Category","Question"], columns="School", values="PercentNegative")
heat = heat.sort_index()

fig = plt.figure(figsize=(12, 14))
ax = fig.add_subplot(111)
im = ax.imshow(heat.values, aspect="auto")

# Axis ticks
ax.set_yticks(np.arange(heat.shape[0]))
ax.set_yticklabels([f"{idx[0]} – {idx[1]}" for idx in heat.index], fontsize=8)
ax.set_xticks(np.arange(len(heat.columns)))
ax.set_xticklabels(heat.columns, rotation=45, ha="right")

ax.set_title("Negativt svar - Heatmap for valgte kategorier og skoler")
ax.set_xlabel("Skole")
ax.set_ylabel("Kategori og spørgsmål")

# Colorbar
cbar = fig.colorbar(im, ax=ax)
cbar.set_label("Procent negative svar")

# Annotate cells
for i in range(heat.shape[0]):
    for j in range(heat.shape[1]):
        val = heat.values[i, j]
        if pd.notna(val):
            ax.text(j, i, f"{val:.1f}", ha="center", va="center", fontsize=7, color="white" if val>15 else "black")

st.pyplot(fig)

st.caption("Bygget med Streamlit + Matplotlib. Tip: Brug sidepanelet til at filtrere skoler og kategorier.")
