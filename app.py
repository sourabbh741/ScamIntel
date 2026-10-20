
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="ScamIntel | Intelligence Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------- PREMIUM UI ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');

:root {
    --ink:#17212f;
    --muted:#718096;
    --paper:#f5f7fb;
    --line:#e7ebf2;
    --blue:#5267e8;
    --mint:#19b89a;
}
html, body, [class*="css"] {
    font-family:'DM Sans',sans-serif;
}
.stApp {background:var(--paper); color:var(--ink);}
header[data-testid="stHeader"] {background:transparent;}
.block-container {padding-top:1.5rem; padding-bottom:3rem; max-width:1500px;}

section[data-testid="stSidebar"] {
    background:#111827;
    border-right:1px solid #253044;
}
section[data-testid="stSidebar"] * {color:#e8edf7;}
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    color:#aab6ca;
}

.hero {
    background:linear-gradient(115deg,#141e35,#253c65 62%,#5267e8);
    padding:34px 36px;
    border-radius:24px;
    color:white;
    margin-bottom:24px;
    box-shadow:0 16px 38px rgba(30,48,85,.13);
}
.eyebrow {
    text-transform:uppercase;
    letter-spacing:2px;
    font-size:11px;
    font-weight:700;
    color:#a8b8ff;
    margin-bottom:10px;
}
.hero h1 {
    font-family:'Manrope',sans-serif;
    font-size:clamp(28px,4vw,42px);
    line-height:1.15;
    letter-spacing:-1.3px;
    margin:0 0 12px;
    color:white;
}
.hero p {
    font-size:14px;
    color:#d4def2;
    max-width:780px;
    line-height:1.8;
}
.pill {
    display:inline-block;
    background:rgba(255,255,255,.12);
    border:1px solid rgba(255,255,255,.17);
    border-radius:100px;
    padding:7px 12px;
    font-size:11px;
    margin:8px 6px 0 0;
}
.section-title {
    font-family:'Manrope',sans-serif;
    font-size:21px;
    font-weight:800;
    letter-spacing:-.5px;
    margin:12px 0 4px;
}
.section-sub {
    color:#77849a;
    font-size:13px;
    margin-bottom:15px;
}
.metric {
    background:white;
    border:1px solid var(--line);
    border-radius:18px;
    padding:20px;
    min-height:125px;
    box-shadow:0 4px 16px rgba(30,48,85,.025);
}
.metric-label {
    font-size:11px;
    color:#758197;
    font-weight:700;
    margin-bottom:12px;
}
.metric-value {
    font-family:'Manrope',sans-serif;
    font-size:clamp(21px,2vw,28px);
    font-weight:800;
    letter-spacing:-1px;
    color:#17212f;
    overflow-wrap:anywhere;
}
.metric-foot {
    font-size:11px;
    color:#8793a6;
    margin-top:8px;
}
.panel {
    background:white;
    border:1px solid var(--line);
    border-radius:20px;
    padding:20px;
    box-shadow:0 4px 16px rgba(30,48,85,.025);
    margin-bottom:12px;
}
.note {
    background:#edf3ff;
    border-left:3px solid #5267e8;
    padding:14px 16px;
    border-radius:8px;
    color:#52617a;
    font-size:12px;
    line-height:1.7;
    margin-top:15px;
}
.footer {
    border-top:1px solid #e4e9f1;
    margin-top:35px;
    padding-top:18px;
    color:#8994a7;
    font-size:11px;
}
div[data-testid="stDataFrame"] {
    border:1px solid #e7ebf2;
    border-radius:12px;
    overflow:hidden;
}
h2,h3 {font-family:'Manrope',sans-serif!important;}
.stButton button, .stDownloadButton button {
    border-radius:10px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- LOAD EXCEL DATA ----------------
DATA_PATH = Path(__file__).resolve().parent / "Data_Matrix_P1.xlsx"

@st.cache_data(show_spinner="Loading ScamIntel datasets...")
def load_data(path):
    workbook = pd.ExcelFile(path)
    return {
        sheet: pd.read_excel(path, sheet_name=sheet)
        for sheet in workbook.sheet_names
    }

if not DATA_PATH.exists():
    st.error(
        "Workbook not found. Place Data_Matrix_P1.xlsx "
        "in the same folder as app.py."
    )
    st.stop()

try:
    data = load_data(str(DATA_PATH))
except Exception as exc:
    st.error(f"Unable to load workbook: {exc}")
    st.stop()

required_sheets = [
    "FBI_Age_Data",
    "FBI_State_Data",
    "Scam_Tactics",
    "FTC_Payment_Methods",
    "FTC_Contact_Methods",
    "Government_Actions",
]

missing_sheets = [s for s in required_sheets if s not in data]

if missing_sheets:
    st.error("Missing worksheets: " + ", ".join(missing_sheets))
    st.info("Available worksheets: " + ", ".join(data.keys()))
    st.stop()

# Define every dataset before using it.
age = data["FBI_Age_Data"].copy()
state = data["FBI_State_Data"].copy()
tactics = data["Scam_Tactics"].copy()
payments = data["FTC_Payment_Methods"].copy()
contacts = data["FTC_Contact_Methods"].copy()
gov = data["Government_Actions"].copy()

# Safely convert numeric columns.
for frame, columns in [
    (age, ["Year", "Complaints/Victims", "Reported Loss (USD)"]),
    (state, ["Year", "Complaints/Victims"]),
    (payments, ["Loss_USD", "# of Reports"]),
    (contacts, ["# of Reports"]),
    (gov, ["Est_Funds_Recovered_USD", "Reported_Recovery_USD", "Year"]),
]:
    for column in columns:
        if column in frame.columns:
            frame[column] = pd.to_numeric(
                frame[column].astype(str).str.replace(",", "", regex=False),
                errors="coerce",
            )

# ---------------- REUSABLE UI HELPERS ----------------
def section(title, subtitle=""):
    st.markdown(
        f'<div class="section-title">{title}</div>'
        f'<div class="section-sub">{subtitle}</div>',
        unsafe_allow_html=True,
    )

def metric(label, value, foot=""):
    st.markdown(
        f'<div class="metric">'
        f'<div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div>'
        f'<div class="metric-foot">{foot}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

def hero(kicker, title, description, pills=""):
    st.markdown(
        f'<div class="hero">'
        f'<div class="eyebrow">{kicker}</div>'
        f'<h1>{title}</h1>'
        f'<p>{description}</p>{pills}</div>',
        unsafe_allow_html=True,
    )

def chart_style(fig, height=360):
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=15, t=30, b=10),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="DM Sans", color="#637086", size=12),
        title_font=dict(family="Manrope", size=15, color="#1c2940"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        xaxis=dict(showgrid=False, zeroline=False, linecolor="#e8edf4"),
        yaxis=dict(gridcolor="#edf1f6", zeroline=False),
    )
    return fig

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.markdown("# 🛡️ ScamIntel")
    st.caption("SCAM ANALYTICS WORKSPACE")
    st.markdown("---")

    page = st.radio(
        "WORKSPACE",
        [
            "Overview",
            "Victim demographics",
            "Geographic hotspots",
            "Scam tactics",
            "Payment & contact",
            "Government response",
            "Data explorer",
        ],
    )

    st.markdown("---")
    st.caption("PROJECT 01 · PSYLIQ")
    st.caption("Analysis window: 2020–2024")
    st.caption("Prepared by Sourabh Awasthi")

# ---------------- OVERVIEW ----------------
if page == "Overview":
    hero(
        "Investigative data analysis · 2020—2024",
        "Understand the patterns.<br>Interrupt the scam.",
        "An interactive intelligence dashboard exploring reported cybercrime, "
        "victim demographics, geographic patterns, scam tactics and prevention.",
        '<span class="pill">FBI IC3</span>'
        '<span class="pill">Scam intelligence</span>'
        '<span class="pill">FTC 2024 data</span>',
    )

    total_victims = age["Complaints/Victims"].fillna(0).sum()
    total_loss = age["Reported Loss (USD)"].fillna(0).sum()

    older = age[
        age["Age Group"].astype(str).str.contains(
            r"60\+|Over 60", case=False, regex=True
        )
    ]
    older_count = older["Complaints/Victims"].fillna(0).sum()

    c = st.columns(4)
    with c[0]:
        metric("AGE-CLASSIFIED REPORTS", f"{total_victims:,.0f}", "FBI IC3 · 2020–2024")
    with c[1]:
        metric("REPORTED FINANCIAL LOSS", f"${total_loss / 1e9:.2f}B", "Reported loss in age dataset")
    with c[2]:
        share = older_count / total_victims if total_victims else 0
        metric("60+ REPORTS", f"{older_count:,.0f}", f"{share:.1%} of age-classified reports")
    with c[3]:
        metric("SCAM TACTIC RECORDS", f"{len(tactics):,}", "Profiles in supplied workbook")

    st.markdown("")
    left, right = st.columns([1.25, 1])

    with left:
        section("Victim reports over time", "Annual reports by age group")
        fig = px.line(
            age,
            x="Year",
            y="Complaints/Victims",
            color="Age Group",
            markers=True,
            color_discrete_sequence=[
                "#5367e8", "#19b89a", "#f4a261",
                "#8b5cf6", "#ef6b73", "#64748b",
            ],
        )
        st.plotly_chart(chart_style(fig, 350), use_container_width=True)

    with right:
        section("Reported victims by age", "Cumulative total · 2020–2024")
        grouped = (
            age.groupby("Age Group", as_index=False)["Complaints/Victims"]
            .sum()
            .sort_values("Complaints/Victims")
        )
        fig = px.bar(
            grouped,
            x="Complaints/Victims",
            y="Age Group",
            orientation="h",
            color="Complaints/Victims",
            color_continuous_scale=["#dbe4ff", "#5267e8"],
        )
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(chart_style(fig, 350), use_container_width=True)

    section("Signals worth attention", "Key findings from the project")
    a, b, c = st.columns(3)

    with a:
        st.markdown("""
        <div class="panel">
        <div class="eyebrow" style="color:#5267e8">01 · VICTIM PROFILE</div>
        <h3>Age matters</h3>
        <p>Older victims account for the largest cumulative reported losses
        in the age-classified project data.</p>
        </div>
        """, unsafe_allow_html=True)

    with b:
        st.markdown("""
        <div class="panel">
        <div class="eyebrow" style="color:#19a88e">02 · EXECUTION</div>
        <h3>Pressure is a signal</h3>
        <p>Scam profiles include urgency, threats, instructions to act,
        and demands for payment.</p>
        </div>
        """, unsafe_allow_html=True)

    with c:
        st.markdown("""
        <div class="panel">
        <div class="eyebrow" style="color:#b7791f">03 · INTERVENTION</div>
        <h3>Before payment</h3>
        <p>Earlier warning signals and human review are possible directions
        for future anti-scam tools.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="note">
    Data note: age and state datasets are analyzed separately because their
    annual totals do not reconcile in the project report. Scam tactic records
    are a manually compiled sample and are not nationally representative.
    </div>
    """, unsafe_allow_html=True)

# ---------------- VICTIM DEMOGRAPHICS ----------------
elif page == "Victim demographics":
    hero(
        "01 / Victim profile",
        "Who is being affected?",
        "Compare reported complaint counts and losses across age groups.",
    )

    years = sorted(age["Year"].dropna().astype(int).unique())

    if not years:
        st.warning("No usable year values were found in the age dataset.")
    else:
        selected = st.slider(
            "Year range",
            min_value=min(years),
            max_value=max(years),
            value=(min(years), max(years)),
        )

        filtered = age[age["Year"].between(*selected)]

        left, right = st.columns(2)

        with left:
            section("Reported victims by age", "Across the selected years")
            grouped = (
                filtered.groupby("Age Group", as_index=False)["Complaints/Victims"]
                .sum()
                .sort_values("Complaints/Victims", ascending=False)
            )
            fig = px.bar(
                grouped,
                x="Age Group",
                y="Complaints/Victims",
                color="Age Group",
                color_discrete_sequence=px.colors.qualitative.Pastel,
            )
            st.plotly_chart(chart_style(fig), use_container_width=True)

        with right:
            section("Reported losses by age", "USD · selected years")
            grouped = (
                filtered.groupby("Age Group", as_index=False)["Reported Loss (USD)"]
                .sum()
                .sort_values("Reported Loss (USD)")
            )
            fig = px.bar(
                grouped,
                x="Reported Loss (USD)",
                y="Age Group",
                orientation="h",
                color="Reported Loss (USD)",
                color_continuous_scale=["#dbe4ff", "#5267e8"],
            )
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(chart_style(fig), use_container_width=True)

        section("Detailed records", "Source data for the selected years")
        st.dataframe(filtered, use_container_width=True, hide_index=True)

# ---------------- GEOGRAPHIC HOTSPOTS ----------------
elif page == "Geographic hotspots":
    hero(
        "02 / Geographic patterns",
        "Where complaints concentrate",
        "Explore reported complaint volume by state. Raw counts do not account for population.",
    )

    years = sorted(state["Year"].dropna().astype(int).unique())

    if not years:
        st.warning("No usable year values were found in the state dataset.")
    else:
        year = st.select_slider("Select year", options=years, value=max(years))
        filtered = state[state["Year"] == year].sort_values(
            "Complaints/Victims", ascending=False
        )

        section(f"Top 15 states · {year}", "Ranked by reported complaints")
        fig = px.bar(
            filtered.head(15).sort_values("Complaints/Victims"),
            x="Complaints/Victims",
            y="State",
            orientation="h",
            color="Complaints/Victims",
            color_continuous_scale=["#dbe4ff", "#5267e8"],
        )
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(chart_style(fig, 480), use_container_width=True)

        section("State trend comparison", "Compare selected states")
        states = sorted(state["State"].dropna().astype(str).unique())
        defaults = [
            s for s in ["California", "Texas", "Florida", "Ohio", "Arizona"]
            if s in states
        ]
        chosen = st.multiselect("Choose states", states, default=defaults)

        if chosen:
            fig = px.line(
                state[state["State"].isin(chosen)],
                x="Year",
                y="Complaints/Victims",
                color="State",
                markers=True,
            )
            st.plotly_chart(chart_style(fig, 380), use_container_width=True)

    st.markdown("""
    <div class="note">
    These are reported complaint counts, not population-adjusted individual risk.
    State and age totals are not directly interchangeable.
    </div>
    """, unsafe_allow_html=True)

# ---------------- SCAM TACTICS ----------------
elif page == "Scam tactics":
    hero(
        "03 / Scam execution",
        "Recognize the playbook.",
        "Explore scam types, contact platforms, tactics and urgency keywords "
        "in the supplied project sample.",
    )

    left, right = st.columns(2)

    with left:
        section("Scam types", "Records in the workbook sample")
        counts = (
            tactics["Scam Type"].fillna("Not specified")
            .value_counts()
            .rename_axis("Scam Type")
            .reset_index(name="Records")
        )
        fig = px.bar(
            counts.sort_values("Records"),
            x="Records",
            y="Scam Type",
            orientation="h",
            color="Records",
            color_continuous_scale=["#dbe4ff", "#5267e8"],
        )
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(chart_style(fig, 380), use_container_width=True)

    with right:
        section("Contact platforms", "Mentions in the supplied sample")
        platforms = (
            tactics["Platform"].fillna("Not specified").astype(str)
            .str.split(r"\s*/\s*|,\s*")
            .explode()
            .str.strip()
            .value_counts()
            .rename_axis("Platform")
            .reset_index(name="Mentions")
        )
        fig = px.bar(
            platforms.sort_values("Mentions"),
            x="Mentions",
            y="Platform",
            orientation="h",
            color="Mentions",
            color_continuous_scale=["#c9f3e9", "#19b89a"],
        )
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(chart_style(fig, 380), use_container_width=True)

    section("The six-stage scam script", "A pattern described in the project report")
    stages = [
        ("01", "Initial contact", "Impersonates a trusted organization or person."),
        ("02", "Create a problem", "Claims there is an account, security or financial issue."),
        ("03", "Create urgency", "Uses fear, threats or artificial deadlines."),
        ("04", "Give instructions", "Requests payment, credentials, clicks or remote access."),
        ("05", "Maintain control", "Continues pressure during the interaction."),
        ("06", "Extract value", "Obtains money, information, credentials or access."),
    ]

    cols = st.columns(3)
    for i, (number, title, description) in enumerate(stages):
        with cols[i % 3]:
            st.markdown(
                f'<div class="panel">'
                f'<div class="eyebrow" style="color:#5267e8">{number} / STAGE</div>'
                f'<h3>{title}</h3><p>{description}</p></div>',
                unsafe_allow_html=True,
            )

    section("Search scam profiles", "Find a tactic, platform or payment keyword")
    query = st.text_input("Search", placeholder="e.g. arrest, phone, gift card")
    view = tactics.copy()

    if query:
        mask = view.astype(str).apply(
            lambda col: col.str.contains(query, case=False, na=False)
        ).any(axis=1)
        view = view[mask]

    st.dataframe(view, use_container_width=True, hide_index=True)

# ---------------- PAYMENT & CONTACT ----------------
elif page == "Payment & contact":
    hero(
        "04 / Payment & contact",
        "How the scam reaches its target.",
        "Explore the FTC 2024 payment and contact datasets included in your workbook.",
    )

    left, right = st.columns(2)

    with left:
        section("Reported losses by payment method", "FTC 2024 · USD")
        if "Loss_USD" in payments.columns:
            valid = payments.dropna(subset=["Loss_USD"]).sort_values("Loss_USD")
            fig = px.bar(
                valid,
                x="Loss_USD",
                y="Payment Method",
                orientation="h",
                color="Loss_USD",
                color_continuous_scale=["#dbe4ff", "#5267e8"],
            )
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(chart_style(fig, 400), use_container_width=True)
        else:
            st.info("The payment worksheet has no Loss_USD column.")

    with right:
        section("Contact methods", "Reported contact records")
        if "# of Reports" in contacts.columns:
            con = contacts.copy()
            con["Report_Count"] = pd.to_numeric(
                con["# of Reports"].astype(str).str.replace(",", "", regex=False),
                errors="coerce",
            )
            con = con.dropna(subset=["Report_Count"]).sort_values("Report_Count")
            fig = px.bar(
                con,
                x="Report_Count",
                y="Contact Method",
                orientation="h",
                color="Report_Count",
                color_continuous_scale=["#c9f3e9", "#19b89a"],
            )
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(chart_style(fig, 400), use_container_width=True)
        else:
            st.info("The contact worksheet has no '# of Reports' column.")

    section("Payment method data")
    st.dataframe(payments, use_container_width=True, hide_index=True)

    section("Contact method data")
    st.dataframe(contacts, use_container_width=True, hide_index=True)

# ---------------- GOVERNMENT RESPONSE ----------------
elif page == "Government response":
    hero(
        "05 / Enforcement response",
        "What happens after a scam?",
        "Explore the selected government actions included in the project workbook. "
        "This is an illustrative dataset, not a complete census of enforcement.",
    )

    g = gov.copy()
    recovery_column = "Est_Funds_Recovered_USD"

    if recovery_column in g.columns:
        g[recovery_column] = pd.to_numeric(g[recovery_column], errors="coerce")
        total_recovery = g[recovery_column].fillna(0).sum()
    else:
        total_recovery = 0

    c1, c2 = st.columns(2)
    with c1:
        metric("SELECTED ACTIONS", f"{len(g):,}", "Records in the workbook")
    with c2:
        metric("ESTIMATED RECOVERY", f"${total_recovery / 1e6:,.1f}M", "Workbook estimate")

    section("Estimated recovery by agency")

    if "Agency" in g.columns and recovery_column in g.columns:
        grouped = (
            g.groupby("Agency", as_index=False)[recovery_column]
            .sum()
            .sort_values(recovery_column)
        )
        fig = px.bar(
            grouped,
            x=recovery_column,
            y="Agency",
            orientation="h",
            color=recovery_column,
            color_continuous_scale=["#dbe4ff", "#5267e8"],
        )
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(chart_style(fig, 380), use_container_width=True)

    st.dataframe(g, use_container_width=True, hide_index=True)

    st.markdown("""
    <div class="note">
    The workbook's estimated recovery field may reflect different forms of
    enforcement relief. It should not automatically be interpreted as money
    returned directly to victims.
    </div>
    """, unsafe_allow_html=True)

# ---------------- DATA EXPLORER ----------------
else:
    hero(
        "06 / Data explorer",
        "Explore the source matrix.",
        "Inspect every worksheet and download data for further analysis.",
    )

    sheet = st.selectbox("Choose a dataset", list(data.keys()))
    df = data[sheet]

    c1, c2 = st.columns(2)
    with c1:
        metric("ROWS", f"{len(df):,}", f"Worksheet: {sheet}")
    with c2:
        metric("COLUMNS", f"{len(df.columns):,}", "Available fields")

    st.dataframe(df, use_container_width=True, hide_index=True)

    st.download_button(
        "⬇ Download this dataset as CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=f"{sheet.lower()}.csv",
        mime="text/csv",
    )

    summary = pd.DataFrame({
        "Worksheet": list(data.keys()),
        "Rows": [len(frame) for frame in data.values()],
        "Columns": [len(frame.columns) for frame in data.values()],
    })

    section("Workbook summary", "Available source tables")
    st.dataframe(summary, use_container_width=True, hide_index=True)

    st.markdown("""
    <div class="note">
    Review the project's methodology and limitations before interpreting
    or combining data from different worksheets.
    </div>
    """, unsafe_allow_html=True)

# ---------------- FOOTER ----------------
st.markdown("""
<div class="footer">
SCAMINTEL · PSYLIQ PROJECT SHOWCASE · Prepared by Sourabh Awasthi<br>
Analysis window: 2020–2024 · Interactive investigative data analytics
</div>
""", unsafe_allow_html=True)
