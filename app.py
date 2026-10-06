import hashlib
import html
import os
import random
import sqlite3
import time
from datetime import date, datetime

import pandas as pd
import plotly.express as px
import streamlit as st

# ============================================================
# PAGE SETUP
# ============================================================
st.set_page_config(page_title="ExamAce AI", page_icon="🎓", layout="wide")

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "examace.db")

CSS = """
<style>
.stApp { background-color: #050505; color: #EDEDED; }
[data-testid="stSidebar"] { background-color: #0B0B0B; border-right: 1px solid #292929; }
[data-testid="stHeader"] { background: #050505; }
h1, h2, h3, h4, p, label, span, div { color: #EDEDED; }
.hero { background: linear-gradient(135deg, #101010, #1a1a1a); border: 1px solid #292929;
        border-radius: 18px; padding: 28px; margin-bottom: 20px; text-align: center; }
.hero h1 { margin: 0; font-size: 2.4rem; }
.hero p { color: #A0A0A0; margin: 6px 0 0 0; font-size: 1.05rem; }
.card { background: #101010; border: 1px solid #292929; border-radius: 14px;
        padding: 18px; margin-bottom: 14px; }
.card h3 { margin-top: 0; }
.card ul { margin: 0; padding-left: 18px; color: #B5B5B5; }
.qcard { background: #101010; border: 1px solid #292929; border-radius: 14px;
         padding: 18px; margin: 10px 0; font-size: 1.15rem; }
.badge { display: inline-block; background: #1f1f1f; border: 1px solid #333;
         border-radius: 999px; padding: 2px 10px; margin-right: 6px; font-size: 0.8rem; color: #B5B5B5; }
.timer { background: #101010; border: 1px solid #292929; border-radius: 14px;
         padding: 10px 16px; font-size: 1.3rem; font-weight: 700; text-align: center; }
[data-testid="stMetric"] { background: #101010; border: 1px solid #292929;
                           border-radius: 14px; padding: 14px; }
.stButton > button { border-radius: 10px; border: 1px solid #333; background: #1a1a1a;
                     color: #EDEDED; padding: 8px 18px; }
.stButton > button:hover { border-color: #4f8cff; color: #ffffff; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ============================================================
# QUESTION BANK  (subject, topic, difficulty, question, options, answer, explanation)
# ============================================================
RAW_QUESTIONS = [
    # ---------------- APTITUDE ----------------
    ("Aptitude", "Percentages", "Easy", "What is 20% of 250?",
     ["40", "50", "60", "70"], "50", "20/100 × 250 = 50."),
    ("Aptitude", "Percentages", "Medium", "40 is what percent of 160?",
     ["20%", "25%", "30%", "40%"], "25%", "(40/160) × 100 = 25%."),
    ("Aptitude", "Ratio", "Easy", "Divide 60 in the ratio 2:3. What is the larger part?",
     ["24", "30", "36", "40"], "36", "Total parts = 5. Larger part = 3/5 × 60 = 36."),
    ("Aptitude", "Ratio", "Medium", "If A:B = 3:4 and B:C = 8:9, then A:C = ?",
     ["2:3", "3:4", "1:2", "4:5"], "2:3", "A/C = (3/4) × (8/9) = 24/36 = 2/3."),
    ("Aptitude", "Average", "Easy", "What is the average of 10, 20, 30, 40 and 50?",
     ["25", "30", "35", "40"], "30", "Sum = 150, and 150 / 5 = 30."),
    ("Aptitude", "Average", "Medium",
     "The average of 5 numbers is 18. If one number, 10, is removed, what is the average of the rest?",
     ["19", "20", "21", "22"], "20", "Total = 90. After removing 10, total = 80. 80 / 4 = 20."),
    ("Aptitude", "Profit & Loss", "Easy", "Cost price is 200 and selling price is 250. What is the profit percent?",
     ["20%", "25%", "30%", "50%"], "25%", "Profit = 50. (50/200) × 100 = 25%."),
    ("Aptitude", "Profit & Loss", "Hard", "An article is sold at a 20% loss for 480. What was its cost price?",
     ["500", "576", "600", "620"], "600", "SP = 80% of CP, so CP = 480 / 0.8 = 600."),
    ("Aptitude", "Simple Interest", "Easy", "What is the simple interest on 1000 at 10% per year for 2 years?",
     ["100", "150", "200", "250"], "200", "SI = (1000 × 10 × 2) / 100 = 200."),
    ("Aptitude", "Simple Interest", "Medium", "A sum of 2000 becomes 2600 in 3 years at simple interest. What is the rate?",
     ["8%", "10%", "12%", "15%"], "10%", "SI = 600. Rate = (600 × 100) / (2000 × 3) = 10%."),
    ("Aptitude", "Time & Work", "Hard", "A can finish a job in 10 days and B in 15 days. Working together, how many days do they need?",
     ["5", "6", "7", "8"], "6", "Combined rate = 1/10 + 1/15 = 1/6, so 6 days."),
    ("Aptitude", "Time Speed Distance", "Medium", "A train 150 m long crosses a pole in 15 seconds. What is its speed in km/h?",
     ["30", "36", "40", "45"], "36", "Speed = 150/15 = 10 m/s = 10 × 18/5 = 36 km/h."),
    # ---------------- REASONING ----------------
    ("Reasoning", "Number Series", "Easy", "Find the next number: 2, 4, 8, 16, ?",
     ["24", "30", "32", "64"], "32", "Each number is double the previous one."),
    ("Reasoning", "Number Series", "Medium", "Find the next number: 3, 6, 11, 18, 27, ?",
     ["36", "38", "40", "42"], "38", "Differences are 3, 5, 7, 9, so the next difference is 11. 27 + 11 = 38."),
    ("Reasoning", "Number Series", "Hard", "Find the next number: 2, 6, 12, 20, 30, ?",
     ["38", "40", "42", "44"], "42", "Differences are 4, 6, 8, 10, so the next is 12. 30 + 12 = 42."),
    ("Reasoning", "Coding-Decoding", "Easy", "If CAT is coded as DBU (each letter moves +1), how is DOG coded?",
     ["EPH", "EPI", "DPH", "FPH"], "EPH", "D→E, O→P, G→H."),
    ("Reasoning", "Coding-Decoding", "Medium", "If A=1, B=2, C=3 and so on, what is the value of CAB?",
     ["5", "6", "7", "8"], "6", "C + A + B = 3 + 1 + 2 = 6."),
    ("Reasoning", "Analogy", "Easy", "Pen : Writing :: Knife : ?",
     ["Cutting", "Cooking", "Sharp", "Kitchen"], "Cutting", "A pen is used for writing; a knife is used for cutting."),
    ("Reasoning", "Odd One Out", "Easy", "Find the odd one out: Apple, Mango, Carrot, Banana",
     ["Apple", "Mango", "Carrot", "Banana"], "Carrot", "Carrot is a vegetable; the others are fruits."),
    ("Reasoning", "Direction Sense", "Easy", "A person faces North and turns right twice. Which direction is he facing now?",
     ["East", "West", "South", "North"], "South", "North → East → South."),
    ("Reasoning", "Blood Relations", "Medium", "Pointing to a man, a woman says, \"He is the son of my mother's only brother.\" How is the man related to her?",
     ["Brother", "Cousin", "Uncle", "Nephew"], "Cousin", "Her mother's brother is her maternal uncle, and his son is her cousin."),
    ("Reasoning", "Alphabet", "Easy", "Which letter is 4th to the right of E in the alphabet?",
     ["H", "I", "J", "K"], "I", "E(5) + 4 = 9, which is I."),
    ("Reasoning", "Classification", "Medium", "Which one does not belong to the group: Square, Triangle, Circle, Cube?",
     ["Square", "Triangle", "Circle", "Cube"], "Cube", "Cube is three-dimensional; the others are two-dimensional."),
    ("Reasoning", "Syllogism", "Hard",
     "Statements: All cats are animals. All animals are living beings. Conclusion: All cats are living beings.",
     ["Definitely true", "Definitely false", "Cannot be determined", "Partly true"], "Definitely true",
     "If cats ⊂ animals ⊂ living beings, then cats ⊂ living beings."),
    # ---------------- ENGLISH ----------------
    ("English", "Grammar", "Easy", "Choose the correct word: She ___ to school every day.",
     ["go", "goes", "going", "gone"], "goes", "A singular subject in the present tense takes 'goes'."),
    ("English", "Synonyms", "Easy", "Choose the synonym of 'Happy'.",
     ["Sad", "Joyful", "Angry", "Tired"], "Joyful", "Joyful means feeling happiness."),
    ("English", "Antonyms", "Easy", "Choose the antonym of 'Ancient'.",
     ["Old", "Modern", "Historic", "Aged"], "Modern", "Ancient means very old; modern is its opposite."),
    ("English", "Vocabulary", "Medium", "What does 'Benevolent' mean?",
     ["Cruel", "Kind and generous", "Lazy", "Clever"], "Kind and generous", "Benevolent describes someone who is well-meaning and kind."),
    ("English", "Articles", "Easy", "Fill in the blank: ___ apple a day keeps the doctor away.",
     ["A", "An", "The", "No article"], "An", "'Apple' begins with a vowel sound, so we use 'An'."),
    ("English", "Prepositions", "Easy", "Fill in the blank: She is very good ___ mathematics.",
     ["at", "in", "on", "for"], "at", "The correct phrase is 'good at'."),
    ("English", "Tenses", "Medium", "Choose the correct option: By next year, he ___ his degree.",
     ["will complete", "will have completed", "has completed", "completes"], "will have completed",
     "An action finished before a future time uses the future perfect tense."),
    ("English", "Spelling", "Easy", "Choose the correct spelling.",
     ["Acommodation", "Accomodation", "Accommodation", "Acomodation"], "Accommodation", "Accommodation has double 'c' and double 'm'."),
    ("English", "Sentence Completion", "Medium", "Despite the heavy rain, the match ___ on time.",
     ["started", "cancels", "will stopping", "have begin"], "started", "'Started' fits the past-tense sentence and its meaning."),
    ("English", "Voice", "Medium", "Change to passive voice: She writes a letter.",
     ["A letter is written by her.", "A letter was written by her.", "A letter writes her.", "A letter is being write by her."],
     "A letter is written by her.", "Present simple active becomes 'is/are + past participle' in passive."),
    ("English", "Grammar", "Hard", "Choose the correct word: Neither of the boys ___ present.",
     ["were", "was", "are", "have been"], "was", "'Neither' takes a singular verb, so 'was'."),
    ("English", "Vocabulary", "Hard", "What does 'Ephemeral' mean?",
     ["Lasting forever", "Very large", "Lasting a very short time", "Very strange"], "Lasting a very short time",
     "Ephemeral things last only for a short time."),
]

QUESTIONS = [
    {"subject": r[0], "topic": r[1], "difficulty": r[2], "question": r[3],
     "options": r[4], "answer": r[5], "explanation": r[6]}
    for r in RAW_QUESTIONS
]

SUBJECTS = ["Aptitude", "Reasoning", "English"]
MENU_ITEMS = ["📊 Dashboard", "🧮 Practice", "📝 Mock Test",
              "🔥 Daily Challenge", "📈 Performance", "👤 Profile"]


# ============================================================
# DATABASE FUNCTIONS
# ============================================================
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    conn = get_connection()
    try:
        conn.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            mode TEXT NOT NULL,
            subject TEXT NOT NULL,
            score REAL NOT NULL,
            correct INTEGER NOT NULL,
            wrong INTEGER NOT NULL,
            skipped INTEGER NOT NULL,
            total INTEGER NOT NULL,
            created_at TEXT NOT NULL)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS daily_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            challenge_date TEXT NOT NULL,
            score REAL NOT NULL,
            correct INTEGER NOT NULL,
            wrong INTEGER NOT NULL,
            completed INTEGER NOT NULL,
            UNIQUE(user_id, challenge_date))""")
        conn.commit()
    finally:
        conn.close()


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def register_user(name, username, password):
    """Returns (success, message)."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (name, username, password, created_at) VALUES (?, ?, ?, ?)",
            (name, username, hash_password(password), now_text()))
        conn.commit()
        return True, "Registration successful! Please go to the Login tab."
    except sqlite3.IntegrityError:
        return False, "That username is already taken."
    finally:
        conn.close()


def login_user(username, password):
    """Returns a user dict if credentials are correct, otherwise None."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, name, username FROM users WHERE username = ? AND password = ?",
            (username, hash_password(password))).fetchone()
        if row is None:
            return None
        return {"id": row["id"], "name": row["name"], "username": row["username"]}
    finally:
        conn.close()


def get_user_info(user_id):
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT name, username, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
    finally:
        conn.close()


def calculate_score(correct, wrong):
    """+1 for correct, -0.25 for wrong, 0 for skipped."""
    return round(correct - (wrong * 0.25), 2)


def save_attempt(user_id, mode, subject, correct, wrong, skipped, total):
    score = calculate_score(correct, wrong)
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO attempts (user_id, mode, subject, score, correct, wrong, skipped, total, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, mode, subject, score, correct, wrong, skipped, total, now_text()))
        conn.commit()
    finally:
        conn.close()
    return score


def get_attempts(user_id, limit=None):
    sql = "SELECT * FROM attempts WHERE user_id = ? ORDER BY id DESC"
    params = [user_id]
    if limit:
        sql += " LIMIT ?"
        params.append(limit)
    conn = get_connection()
    try:
        return pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()


def get_stats(user_id):
    df = get_attempts(user_id)
    if df.empty:
        return {"tests": 0, "attempted": 0, "correct": 0, "wrong": 0,
                "skipped": 0, "accuracy": 0.0, "total_score": 0.0, "avg_score": 0.0}
    correct = int(df["correct"].sum())
    wrong = int(df["wrong"].sum())
    attempted = correct + wrong
    accuracy = round(correct / attempted * 100, 1) if attempted > 0 else 0.0
    return {"tests": len(df), "attempted": attempted, "correct": correct, "wrong": wrong,
            "skipped": int(df["skipped"].sum()), "accuracy": accuracy,
            "total_score": round(float(df["score"].sum()), 2),
            "avg_score": round(float(df["score"].mean()), 2)}


def save_daily_result(user_id, challenge_date, score, correct, wrong):
    conn = get_connection()
    try:
        conn.execute(
            """INSERT OR IGNORE INTO daily_results
               (user_id, challenge_date, score, correct, wrong, completed) VALUES (?, ?, ?, ?, ?, 1)""",
            (user_id, challenge_date, score, correct, wrong))
        conn.commit()
    finally:
        conn.close()


def get_daily_result(user_id, challenge_date):
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM daily_results WHERE user_id = ? AND challenge_date = ?",
            (user_id, challenge_date)).fetchone()
    finally:
        conn.close()


# ============================================================
# QUESTION HELPERS
# ============================================================
def get_topics(subject):
    topics = []
    for q in QUESTIONS:
        if q["subject"] == subject and q["topic"] not in topics:
            topics.append(q["topic"])
    return topics


def filtered_questions(subject="Mixed", topic="All", difficulty="All"):
    result = []
    for q in QUESTIONS:
        if subject != "Mixed" and q["subject"] != subject:
            continue
        if topic != "All" and q["topic"] != topic:
            continue
        if difficulty != "All" and q["difficulty"] != difficulty:
            continue
        result.append(q)
    return result


def prepare_questions(questions, rng):
    """Copy questions and shuffle their order and their options."""
    prepared = []
    for q in questions:
        item = dict(q)
        item["options"] = list(q["options"])
        rng.shuffle(item["options"])
        prepared.append(item)
    rng.shuffle(prepared)
    return prepared


def evaluate(questions, answers):
    """answers is a dict {question_index: selected_option}."""
    correct = 0
    wrong = 0
    for i, q in enumerate(questions):
        chosen = answers.get(i)
        if chosen is None:
            continue
        if chosen == q["answer"]:
            correct += 1
        else:
            wrong += 1
    skipped = len(questions) - correct - wrong
    return correct, wrong, skipped


def new_quiz_state(questions, subject):
    return {"id": int(time.time() * 1000), "questions": questions, "subject": subject,
            "index": 0, "submitted": False, "last_choice": None,
            "correct": 0, "wrong": 0, "skipped": 0, "finished": False, "score": 0.0}


# ============================================================
# UI HELPERS
# ============================================================
def show_hero(title="🎓 ExamAce AI", subtitle="Practice Smarter. Test Better. Get Job Ready."):
    st.markdown(f'<div class="hero"><h1>{title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)


def show_question_card(q, number, total):
    st.markdown(f"#### Question {number} / {total}")
    st.markdown(
        f'<div class="qcard"><span class="badge">{html.escape(q["subject"])}</span>'
        f'<span class="badge">{html.escape(q["topic"])}</span>'
        f'<span class="badge">{html.escape(q["difficulty"])}</span><br><br>'
        f'{html.escape(q["question"])}</div>', unsafe_allow_html=True)


def show_result(title, correct, wrong, skipped, total):
    score = calculate_score(correct, wrong)
    attempted = correct + wrong
    accuracy = round(correct / attempted * 100, 1) if attempted > 0 else 0.0
    st.success(title)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Final Score", f"{score:.2f}")
    c2.metric("Correct", correct)
    c3.metric("Wrong", wrong)
    c4.metric("Skipped", skipped)
    c5.metric("Accuracy", f"{accuracy}%")
    st.caption(f"Total questions: {total}   |   Score = correct − (wrong × 0.25)")


def advance(state, on_finish):
    state["index"] += 1
    state["submitted"] = False
    state["last_choice"] = None
    if state["index"] >= len(state["questions"]):
        state["finished"] = True
        on_finish()
    st.rerun()


def quiz_flow(state, prefix, on_finish):
    """Shows ONE question at a time with submit / skip / next (used by Practice and Daily)."""
    questions = state["questions"]
    total = len(questions)
    i = state["index"]
    q = questions[i]
    st.progress(i / total)
    show_question_card(q, i + 1, total)
    choice = st.radio("Select your answer:", q["options"], index=None,
                      key=f"{prefix}_{state['id']}_{i}", disabled=state["submitted"])

    if not state["submitted"]:
        col1, col2, _ = st.columns([1, 1, 3])
        if col1.button("✅ Submit Answer", key=f"{prefix}_submit_{i}"):
            if choice is None:
                st.warning("Please select an option first (or press Skip).")
            else:
                state["submitted"] = True
                state["last_choice"] = choice
                if choice == q["answer"]:
                    state["correct"] += 1
                else:
                    state["wrong"] += 1
                st.rerun()
        if col2.button("⏭️ Skip", key=f"{prefix}_skip_{i}"):
            state["skipped"] += 1
            advance(state, on_finish)
    else:
        if state["last_choice"] == q["answer"]:
            st.success("🎉 Correct!")
        else:
            st.error("❌ Wrong!")
        st.markdown(f"**Correct Answer:** {q['answer']}")
        st.markdown(f"**Explanation:** {q['explanation']}")
        m1, m2, m3 = st.columns(3)
        m1.metric("Score", f"{calculate_score(state['correct'], state['wrong']):.2f}")
        m2.metric("Correct", state["correct"])
        m3.metric("Wrong", state["wrong"])
        label = "➡️ Next Question" if i + 1 < total else "🏁 Finish"
        if st.button(label, key=f"{prefix}_next_{i}"):
            advance(state, on_finish)


# ============================================================
# SESSION STATE
# ============================================================
if "user" not in st.session_state:
    st.session_state.user = None
if "practice" not in st.session_state:
    st.session_state.practice = None
if "mock" not in st.session_state:
    st.session_state.mock = None
if "daily" not in st.session_state:
    st.session_state.daily = None

init_database()


# ============================================================
# PAGES (all functions are defined BEFORE the navigation logic)
# ============================================================
def show_auth_page():
    show_hero("🎓 ExamAce AI", "Your Smart Exam Preparation Platform")
    st.caption("Practice Smarter. Test Better. Get Job Ready.")
    tab_login, tab_register = st.tabs(["🔐 Login", "📝 Register"])

    with tab_login:
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login", key="login_btn"):
            user = login_user(username.strip().lower(), password)
            if user is None:
                st.error("Invalid username or password.")
            else:
                st.session_state.user = user
                st.rerun()

    with tab_register:
        name = st.text_input("Full Name", key="reg_name")
        new_username = st.text_input("Username", key="reg_username")
        new_password = st.text_input("Password", type="password", key="reg_password")
        confirm = st.text_input("Confirm Password", type="password", key="reg_confirm")
        if st.button("Create Account", key="register_btn"):
            if not name.strip():
                st.error("Name cannot be empty.")
            elif not new_username.strip():
                st.error("Username cannot be empty.")
            elif not new_password:
                st.error("Password cannot be empty.")
            elif len(new_password) < 4:
                st.error("Password must be at least 4 characters.")
            elif new_password != confirm:
                st.error("Password and confirm password must match.")
            else:
                ok, message = register_user(name.strip(), new_username.strip().lower(), new_password)
                if ok:
                    st.success(message)
                else:
                    st.error(message)


def show_dashboard():
    user = st.session_state.user
    show_hero()
    st.subheader(f"Welcome back, {user['name']} 👋")
    stats = get_stats(user["id"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tests Completed", stats["tests"])
    c2.metric("Questions Attempted", stats["attempted"])
    c3.metric("Accuracy", f"{stats['accuracy']}%")
    c4.metric("Total Score", f"{stats['total_score']:.2f}")

    cards = [
        ("🧮 Aptitude", ["Percentages", "Ratio", "Average", "Profit & Loss",
                         "Simple Interest", "Time & Work", "Time Speed Distance"]),
        ("🧠 Reasoning", ["Number Series", "Coding-Decoding", "Analogy", "Odd One Out", "Direction Sense",
                          "Blood Relations", "Alphabet", "Classification", "Syllogism"]),
        ("📚 English", ["Grammar", "Synonyms", "Antonyms", "Vocabulary", "Articles",
                        "Prepositions", "Tenses", "Spelling", "Sentence Completion", "Voice"]),
    ]
    cols = st.columns(3)
    for col, (title, topics) in zip(cols, cards):
        items = "".join(f"<li>{t}</li>" for t in topics)
        col.markdown(f'<div class="card"><h3>{title}</h3><ul>{items}</ul></div>', unsafe_allow_html=True)

    st.subheader("Recent Attempts")
    df = get_attempts(user["id"], limit=5)
    if df.empty:
        st.info("No attempts yet. Start a practice session or a mock test!")
    else:
        table = df[["created_at", "mode", "subject", "score", "correct", "wrong", "skipped", "total"]]
        table.columns = ["Date", "Mode", "Subject", "Score", "Correct", "Wrong", "Skipped", "Total"]
        st.dataframe(table, use_container_width=True, hide_index=True)


def finish_practice():
    state = st.session_state.practice
    user = st.session_state.user
    total = len(state["questions"])
    state["score"] = save_attempt(user["id"], "Practice", state["subject"],
                                  state["correct"], state["wrong"], state["skipped"], total)


def show_practice():
    user = st.session_state.user
    st.header("🧮 Practice Arena")
    state = st.session_state.practice

    if state is None:
        subject = st.selectbox("Subject", SUBJECTS, key="practice_subject")
        topic = st.selectbox("Topic", ["All"] + get_topics(subject), key="practice_topic")
        difficulty = st.selectbox("Difficulty", ["All", "Easy", "Medium", "Hard"], key="practice_diff")
        if st.button("🚀 Start New Practice", key="practice_start"):
            pool = filtered_questions(subject, topic, difficulty)
            if len(pool) == 0:
                st.error("No questions found for this selection. Try a different topic or difficulty.")
            else:
                questions = prepare_questions(pool, random.Random())
                st.session_state.practice = new_quiz_state(questions, subject)
                st.rerun()
    elif state["finished"]:
        show_result("🎉 Practice Completed!", state["correct"], state["wrong"],
                    state["skipped"], len(state["questions"]))
        st.caption("Your result has been saved.")
        if st.button("🔁 Start Another Practice", key="practice_again"):
            st.session_state.practice = None
            st.rerun()
    else:
        quiz_flow(state, "practice", finish_practice)
        st.divider()
        if st.button("❌ Quit this practice", key="practice_quit"):
            st.session_state.practice = None
            st.rerun()


def finish_mock():
    state = st.session_state.mock
    user = st.session_state.user
    if state["finished"]:
        return
    correct, wrong, skipped = evaluate(state["questions"], state["answers"])
    state["correct"] = correct
    state["wrong"] = wrong
    state["skipped"] = skipped
    state["score"] = save_attempt(user["id"], "Mock Test", state["subject"],
                                  correct, wrong, skipped, len(state["questions"]))
    state["finished"] = True


@st.fragment(run_every=1)
def mock_timer():
    """Refreshes only itself every second; asks for a full rerun when time is up."""
    state = st.session_state.mock
    if state is None or state["finished"]:
        return
    remaining = state["duration"] - (time.time() - state["start_time"])
    if remaining <= 0:
        st.rerun()
    remaining = int(remaining)
    st.markdown(f'<div class="timer">⏱️ Time Remaining: {remaining // 60:02d}:{remaining % 60:02d}</div>',
                unsafe_allow_html=True)


def show_mock():
    st.header("📝 Mock Test")
    state = st.session_state.mock

    if state is None:
        subject = st.selectbox("Subject", ["Mixed"] + SUBJECTS, key="mock_subject")
        count = st.selectbox("Number of Questions", [10, 20, 30], key="mock_count")
        minutes = st.selectbox("Time Limit (minutes)", [5, 10, 20, 30], key="mock_minutes")
        if st.button("🚀 Start Mock Test", key="mock_start"):
            pool = filtered_questions(subject)
            if count > len(pool):
                st.error(f"Only {len(pool)} questions are available for this selection.")
            else:
                chosen = random.Random().sample(pool, count)
                questions = prepare_questions(chosen, random.Random())
                st.session_state.mock = {
                    "id": int(time.time() * 1000), "questions": questions, "subject": subject,
                    "answers": {}, "index": 0, "start_time": time.time(),
                    "duration": minutes * 60, "finished": False,
                    "correct": 0, "wrong": 0, "skipped": 0, "score": 0.0}
                st.rerun()
        return

    if state["finished"]:
        show_result("🏁 Mock Test Finished!", state["correct"], state["wrong"],
                    state["skipped"], len(state["questions"]))
        st.caption("Your result has been saved.")
        if st.button("🔁 Take Another Mock Test", key="mock_again"):
            st.session_state.mock = None
            st.rerun()
        return

    # Test in progress: check the time first
    remaining = state["duration"] - (time.time() - state["start_time"])
    if remaining <= 0:
        finish_mock()
        st.rerun()

    mock_timer()
    questions = state["questions"]
    total = len(questions)
    i = state["index"]
    q = questions[i]
    st.progress((i + 1) / total)
    st.markdown(f"**Q{i + 1} / {total}**   |   Answered: {len(state['answers'])} / {total}")
    show_question_card(q, i + 1, total)

    saved = state["answers"].get(i)
    saved_index = q["options"].index(saved) if saved in q["options"] else None
    choice = st.radio("Select your answer:", q["options"], index=saved_index,
                      key=f"mock_{state['id']}_{i}")
    if choice is not None:
        state["answers"][i] = choice

    col1, col2, _ = st.columns([1, 1.4, 3])
    if col1.button("⬅️ Previous", key=f"mock_prev_{i}", disabled=(i == 0)):
        state["index"] -= 1
        st.rerun()
    if i < total - 1:
        if col2.button("➡️ Next Question", key=f"mock_next_{i}"):
            state["index"] += 1
            st.rerun()
    else:
        if col2.button("🏁 Finish Test", key="mock_finish"):
            finish_mock()
            st.rerun()


def finish_daily():
    state = st.session_state.daily
    user = st.session_state.user
    total = len(state["questions"])
    score = save_attempt(user["id"], "Daily Challenge", "Mixed",
                         state["correct"], state["wrong"], state["skipped"], total)
    state["score"] = score
    save_daily_result(user["id"], state["date"], score, state["correct"], state["wrong"])


def build_daily_questions(today_text):
    """Same date -> same 10 questions (4 Aptitude, 3 Reasoning, 3 English)."""
    rng = random.Random(today_text)
    picked = []
    for subject, amount in [("Aptitude", 4), ("Reasoning", 3), ("English", 3)]:
        pool = filtered_questions(subject)
        picked.extend(rng.sample(pool, min(amount, len(pool))))
    return prepare_questions(picked, rng)


def show_daily():
    user = st.session_state.user
    st.header("🔥 Daily Challenge")
    today = date.today().isoformat()
    state = st.session_state.daily

    # Just finished in this session
    if state is not None and state["finished"] and state["date"] == today and state["user_id"] == user["id"]:
        show_result("🔥 Daily Challenge Completed!", state["correct"], state["wrong"],
                    state["skipped"], len(state["questions"]))
        return

    # Already completed earlier today
    done = get_daily_result(user["id"], today)
    if done is not None and done["completed"] == 1:
        st.info("Today's challenge is already completed.")
        attempted = done["correct"] + done["wrong"]
        accuracy = round(done["correct"] / attempted * 100, 1) if attempted > 0 else 0.0
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Score", f"{done['score']:.2f}")
        c2.metric("Correct", done["correct"])
        c3.metric("Wrong", done["wrong"])
        c4.metric("Accuracy", f"{accuracy}%")
        return

    # Create today's challenge state if needed
    if state is None or state["date"] != today or state["user_id"] != user["id"]:
        state = new_quiz_state(build_daily_questions(today), "Mixed")
        state["date"] = today
        state["user_id"] = user["id"]
        st.session_state.daily = state

    st.caption(f"Challenge date: {today}")
    quiz_flow(state, "daily", finish_daily)


def show_performance():
    user = st.session_state.user
    st.header("📈 Performance")
    df = get_attempts(user["id"])
    if df.empty:
        st.info("No performance data available yet. Complete a test to see your analysis.")
        return

    stats = get_stats(user["id"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Tests", stats["tests"])
    c2.metric("Total Questions", int(df["total"].sum()))
    c3.metric("Accuracy", f"{stats['accuracy']}%")
    c4.metric("Average Score", f"{stats['avg_score']:.2f}")
    c5, c6, c7 = st.columns(3)
    c5.metric("Correct", stats["correct"])
    c6.metric("Wrong", stats["wrong"])
    c7.metric("Skipped", stats["skipped"])

    # Chart 1: score by test (oldest first)
    ordered = df.sort_values("id").reset_index(drop=True)
    ordered["Test No."] = ordered.index + 1
    fig1 = px.bar(ordered, x="Test No.", y="score", color="mode", title="Score by Test",
                  template="plotly_dark", labels={"score": "Score"})
    st.plotly_chart(fig1, use_container_width=True)

    # Chart 2: correct vs wrong
    totals = pd.DataFrame({"Result": ["Correct", "Wrong", "Skipped"],
                           "Count": [stats["correct"], stats["wrong"], stats["skipped"]]})
    fig2 = px.pie(totals, names="Result", values="Count", title="Correct vs Wrong",
                  template="plotly_dark", hole=0.4,
                  color="Result", color_discrete_map={"Correct": "#2ecc71", "Wrong": "#e74c3c", "Skipped": "#7f8c8d"})
    st.plotly_chart(fig2, use_container_width=True)

    # Chart 3: performance by subject (accuracy)
    by_subject = df.groupby("subject")[["correct", "wrong"]].sum().reset_index()
    by_subject["attempted"] = by_subject["correct"] + by_subject["wrong"]
    by_subject["Accuracy %"] = by_subject.apply(
        lambda r: round(r["correct"] / r["attempted"] * 100, 1) if r["attempted"] > 0 else 0.0, axis=1)
    fig3 = px.bar(by_subject, x="subject", y="Accuracy %", title="Performance by Subject",
                  template="plotly_dark", labels={"subject": "Subject"})
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Recent Test History")
    table = df.head(10)[["created_at", "mode", "subject", "score", "correct", "wrong", "skipped", "total"]]
    table.columns = ["Date", "Mode", "Subject", "Score", "Correct", "Wrong", "Skipped", "Total"]
    st.dataframe(table, use_container_width=True, hide_index=True)


def show_profile():
    user = st.session_state.user
    st.header("👤 Profile")
    info = get_user_info(user["id"])
    if info is None:
        st.error("Could not load your profile.")
        return
    st.markdown(
        f'<div class="card"><h3>{html.escape(info["name"])}</h3>'
        f'<p><b>Username:</b> {html.escape(info["username"])}</p>'
        f'<p><b>Account Created:</b> {html.escape(info["created_at"])}</p></div>',
        unsafe_allow_html=True)
    stats = get_stats(user["id"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tests Completed", stats["tests"])
    c2.metric("Questions Attempted", stats["attempted"])
    c3.metric("Accuracy", f"{stats['accuracy']}%")
    c4.metric("Total Score", f"{stats['total_score']:.2f}")


def logout():
    st.session_state.user = None
    st.session_state.practice = None
    st.session_state.mock = None
    st.session_state.daily = None
    st.rerun()


# ============================================================
# MAIN NAVIGATION
# ============================================================
if st.session_state.user is None:
    show_auth_page()
else:
    st.sidebar.markdown("## 🎓 ExamAce AI")
    st.sidebar.markdown(f"👤 Welcome, **{st.session_state.user['username']}**")
    menu = st.sidebar.radio("Navigation", MENU_ITEMS)
    st.sidebar.divider()
    if st.sidebar.button("🚪 Logout"):
        logout()

    if menu == "📊 Dashboard":
        show_dashboard()
    elif menu == "🧮 Practice":
        show_practice()
    elif menu == "📝 Mock Test":
        show_mock()
    elif menu == "🔥 Daily Challenge":
        show_daily()
    elif menu == "📈 Performance":
        show_performance()
    elif menu == "👤 Profile":
        show_profile()
