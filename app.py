import streamlit as st
import pickle
import pandas as pd
import plotly.graph_objects as go
import time, random

st.set_page_config(page_title="IPL Predictor Pro", layout="wide")

# ---------------- UI ----------------
st.markdown("""
<style>

.stApp {
    background: linear-gradient(135deg,#020617,#0f172a);
    color: #e2e8f0;
    font-family: 'Inter', sans-serif;
}

/* HEADER */
h1 { text-align:center; color:#facc15; }
h2 { color:#38bdf8; margin-top:20px; }

/* CARD */
.card {
    background: rgba(30,41,59,0.95);
    padding:25px;
    border-radius:20px;
    margin-bottom:20px;
    border:1px solid rgba(255,255,255,0.08);
    box-shadow: 0 0 25px rgba(0,0,0,0.7);
}

/* SCORE */
.score {
    text-align:center;
}
.score h1 {
    font-size:52px;
    color:#38bdf8;
    margin-bottom:10px;
}
.score p {
    font-size:18px;
}

/* COMMENTARY COLORS */
.wicket {color:#ef4444; font-weight:bold;}
.boundary {color:#22c55e; font-weight:bold;}
.normal {color:#e2e8f0;}

/* BUTTON */
.stButton>button {
    background: linear-gradient(90deg,#fb7185,#f43f5e);
    color:white;
    border-radius:12px;
    height:50px;
    font-size:16px;
    box-shadow: 0 0 15px rgba(244,63,94,0.5);
}

/* INPUT */
.stNumberInput input, .stSelectbox div[data-baseweb="select"] {
    background-color:#020617 !important;
    color:white !important;
}

/* PROGRESS */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg,#22c55e,#4ade80);
}

</style>
""", unsafe_allow_html=True)

# ---------------- MODEL ----------------
@st.cache_resource
def load_model():
    return pickle.load(open('ipl_model.pkl', 'rb'))

model = load_model()

teams = ['Mumbai Indians','Chennai Super Kings','Royal Challengers Bangalore',
         'Kolkata Knight Riders','Delhi Capitals','Sunrisers Hyderabad',
         'Rajasthan Royals','Punjab Kings','Lucknow Super Giants','Gujarat Titans']

cities = ['Mumbai','Delhi','Chennai','Kolkata','Hyderabad','Bangalore','Jaipur','Ahmedabad','Lucknow']

# ---------------- HEADER ----------------
st.markdown("<h1>🏏 IPL Win Predictor Pro</h1>", unsafe_allow_html=True)
st.markdown('<div class="card">AI predicts match outcome dynamically based on live match conditions.</div>', unsafe_allow_html=True)

st.markdown("---")

# ---------------- INPUT ----------------
c1,c2,c3 = st.columns(3)
batting_team = c1.selectbox("Batting Team", teams)
bowling_team = c2.selectbox("Bowling Team", teams)
city = c3.selectbox("City", cities)

if batting_team == bowling_team:
    st.warning("Select different teams")
    st.stop()

c1,c2 = st.columns(2)
target = c1.number_input("Target Runs",1,300,150)
score = c1.number_input("Current Score",0,300,50)

overs = c2.number_input("Overs",0,20,10)
balls = c2.number_input("Balls",0,5,0)
wickets_left = c2.slider("Wickets Left",0,10,5)

total_balls = overs*6 + balls

if total_balls >= 120:
    st.error("Match finished")
    st.stop()

st.markdown("---")

# ---------------- SIMULATION ----------------
if st.button("🚀 Start Match Analysis"):

    st.markdown("## 🎮 Live Match Simulation")

    sim_score = score
    sim_wickets = 10 - wickets_left
    sim_balls = total_balls
    wickets_remaining = wickets_left

    live_box = st.empty()
    commentary_box = st.empty()
    prob_bar = st.progress(0)

    history = []
    prob_history = []
    ball_history = []

    while sim_balls < 120 and sim_score < target and wickets_remaining > 0:

        time.sleep(0.03)

        runs_left = max(target - sim_score, 0)
        balls_left = max(120 - sim_balls, 1)

        df = pd.DataFrame({
            'batting_team':[batting_team],
            'bowling_team':[bowling_team],
            'city':[city],
            'runs_left':[runs_left],
            'balls_left':[balls_left],
            'wickets_left':[wickets_remaining],
            'crr':[sim_score/(sim_balls/6) if sim_balls>0 else 0],
            'rrr':[(runs_left*6)/balls_left]
        })

        prob = model.predict_proba(df)[0][1]
        prob_percent = int(prob * 100)

        prob_bar.progress(prob_percent)
        prob_history.append(prob_percent)
        ball_history.append(sim_balls)

        pressure = runs_left / balls_left

        if wickets_remaining <= 2:
            outcome = random.choices([0,1,'W'], weights=[60,30,10])[0]
        elif pressure > 2:
            outcome = random.choices([0,1,2,'W'], weights=[40,30,10,20])[0]
        elif pressure > 1.2:
            outcome = random.choices([0,1,2,4,'W'], weights=[25,30,20,15,10])[0]
        else:
            outcome = random.choices([1,2,3,4,6], weights=[30,25,10,25,10])[0]

        # COMMENTARY STYLE
        if outcome == 'W':
            text = "<span class='wicket'>WICKET! 💥</span>"
        elif outcome in [4,6]:
            text = "<span class='boundary'>FOUR/SIX! 🔥</span>"
        else:
            text = "<span class='normal'>Run scored</span>"

        history.append(text)

        if outcome == 'W':
            sim_wickets += 1
            wickets_remaining -= 1
        else:
            sim_score += outcome

        sim_balls += 1

        over = sim_balls // 6
        ball = sim_balls % 6

        color = "#22c55e" if prob_percent > 50 else "#ef4444"

        live_box.markdown(f"""
        <div class="card score">
        <h1>{sim_score}/{sim_wickets}</h1>
        <p>Overs: {over}.{ball}</p>
        <p>Need {target - sim_score} in {120 - sim_balls} balls</p>
        <p style="color:{color}; font-size:20px;">Win Probability: {prob_percent}%</p>
        </div>
        """, unsafe_allow_html=True)

        commentary_box.markdown(
            "<div class='card'><h3>🗣️ Commentary</h3>" +
            "<br>".join(history[-6:][::-1]) +
            "</div>",
            unsafe_allow_html=True
        )

    st.markdown("---")

    st.markdown("## 🏆 Match Result")

    if sim_score >= target:
        st.success(f"{batting_team} WON!")
    else:
        st.error(f"{bowling_team} WON!")

    # SUMMARY
    st.markdown("### 📊 Match Summary")
    st.write(f"Final Score: {sim_score}/{sim_wickets}")
    st.write(f"Total Balls Played: {sim_balls}")
    st.write(f"Final Run Rate: {round(sim_score/(sim_balls/6),2)}")

    # GRAPH
    st.markdown("## 📈 Win Probability Trend")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ball_history,
        y=prob_history,
        mode='lines',
        line=dict(width=4, color='#22c55e'),
        fill='tozeroy',
        fillcolor='rgba(34,197,94,0.25)'
    ))

    fig.update_layout(
        plot_bgcolor='#020617',
        paper_bgcolor='#020617',
        font=dict(color='#e2e8f0'),
        xaxis_title="Balls",
        yaxis_title="Win %",
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
    )

    st.plotly_chart(fig, use_container_width=True)