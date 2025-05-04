import streamlit as st
import pandas as pd
import random
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st

def send_to_gsheet(data_dict):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        dict(st.secrets["gcp_service_account"]), scope
    )
    client = gspread.authorize(creds)

    sheet = client.open("ma206review").worksheet("Submissions")
    sheet.append_row(list(data_dict.values()))

# ---- CONFIG ----
st.set_page_config(page_title="Cadet Review Quiz", layout="wide")
st.title("⚾ STATBALL ⚾")

st.markdown("""
### 📝 Instructions

1. **Quiz Tab**:  
   - Select your section, enter your team name, and everyone in the group's last names.  
   - Answer all 25 multiple-choice questions.  
   - When finished, click **"Score My Answers"** to reveal your **Salary Cap** based on correct answers.

2. **Draft Tab**:  
   - Use your Salary Cap to bid on players by entering amounts in the **Your Bid** column.  
   - Ensure the **Total Bid** stays within your cap limit.  
   - Once finalized, click **"Submit Bids"** to send to the league commissioner.

🛑 You **cannot edit** your submission after submitting, so double-check before finalizing!
""")

def run_quiz_form(team_name, members, section, salary_per_question=400_000):
    responses = {}

    with st.form("salary_quiz_form"):
        # 1) Quiz questions

        # ---- QUESTIONS ----
        questions = {
            1: {"question": "A platoon leader models ruck march times with a normal distribution. Which assumption is most crucial to using the normal model for probability estimates?",
                "options": ["The population distribution is unimodal and symmetric", "The sample mean equals the population mean", "The standard deviation is unknown", "The data has no outliers"],
                "answer": "The population distribution is unimodal and symmetric",
                "explanation": "The normal model applies best when data is symmetric and unimodal."},
            2: {"question": "You're comparing heights of cadets from two companies. Which test is most appropriate if the samples are independent and quantitative?",
                "options": ["Paired t-test", "Two-sample t-test", "One-sample t-test", "Chi-square test"],
                "answer": "Two-sample t-test",
                "explanation": "Use two-sample t-tests to compare means between independent groups."},
            3: {"question": "In a survey, 62% of cadets said they prefer field training. For n = 100, what is the standard error of the proportion?",
                "options": ["0.048", "0.061", "0.39", "0.24"],
                "answer": "0.048",
                "explanation": "Standard error = sqrt(p*(1-p)/n) = sqrt(0.62*0.38/100)."},
            4: {"question": "A 95% CI for cadet GPA is (2.9, 3.3). Which interpretation is correct?",
                "options": ["We are 95% confident the population mean GPA is between 2.9 and 3.3", "There is a 95% chance an individual GPA falls in that range", "95% of cadets have GPAs in that range", "Only 5% of cadets fall outside this range"],
                "answer": "We are 95% confident the population mean GPA is between 2.9 and 3.3",
                "explanation": "Confidence intervals refer to population parameters, not individuals."},
            5: {"question": "Which null hypothesis is valid when comparing PT scores across two platoons?",
                "options": ["μ₁ = μ₂", "μ₁ > μ₂", "μ₁ ≠ 0.5", "μ₁ + μ₂ = 1"],
                "answer": "μ₁ = μ₂",
                "explanation": "The null hypothesis always assumes equality between group means."},
            6: {"question": "You measure pushups before and after training for each cadet. Which analysis is appropriate?",
                "options": ["Paired t-test", "Two-sample t-test", "One-proportion z-test", "Chi-square test"],
                "answer": "Paired t-test",
                "explanation": "A paired t-test handles repeated measures on the same subjects."},
            7: {"question": "Your p-value is 0.004. What conclusion is most justified?",
                "options": ["Reject the null hypothesis", "Fail to reject the null hypothesis", "Accept the alternative hypothesis", "Your sample is biased"],
                "answer": "Reject the null hypothesis",
                "explanation": "A small p-value indicates strong evidence against H₀."},
            8: {
                "question": "A fair coin is flipped 4 times. What is the probability of getting exactly 2 heads?",
                "options": ["0.25", "0.375", "0.5", "0.75"],
                "answer": "0.375",
                "explanation": "Use the binomial formula: P(X = 2) = C(4,2) * (0.5)^2 * (0.5)^2 = 6 * 0.25 * 0.25 = 0.375."
            },
            9: {"question": "You record whether cadets pass their ACFT. What type of variable is this?",
                "options": ["Categorical", "Quantitative", "Continuous", "Interval"],
                "answer": "Categorical",
                "explanation": "Pass/fail is a binary categorical variable."},
            10: {"question": "If P(Female)=0.2 and P(Passed|Female)=0.9, what is P(Female AND Passed)?",
                "options": ["0.18", "0.02", "0.70", "0.11"],
                "answer": "0.18",
                "explanation": "Joint probability = P(A)*P(B|A) = 0.2*0.9."},
            11: {"question": "If two events cannot occur simultaneously, they are:",
                "options": ["Mutually exclusive", "Independent", "Complementary", "Joint"],
                "answer": "Mutually exclusive",
                "explanation": "Mutually exclusive events have no overlap."},
            12: {"question": "Which distribution models the number of trials until the first success?",
                "options": ["Geometric", "Binomial", "Poisson", "Normal"],
                "answer": "Geometric",
                "explanation": "The geometric distribution describes trials until first success."},
            13: {"question": "Which distribution counts the number of successes in a fixed number of trials?",
                "options": ["Binomial", "Geometric", "Poisson", "Uniform"],
                "answer": "Binomial",
                "explanation": "The binomial distribution counts successes in n independent trials."},
            14: {"question": "Which value is always at the center of a confidence interval for a mean?",
                "options": ["Sample mean", "Population mean", "Standard error", "Population SD"],
                "answer": "Sample mean",
                "explanation": "CIs are constructed around the sample mean."},
            15: {"question": "A rare illness affects 2% of cadets. A test is 95% sensitive and 90% specific. What is P(disease|positive)?",
                "options": ["16%", "32%", "68%", "95%"],
                "answer": "16%",
                "explanation": "Bayes’ Rule: (0.02*0.95)/((0.02*0.95)+(0.98*0.10)) ≈ 0.162."},
            16: {"question": "Regression slope = 0.12 for GPA vs hours studied. What does this mean?",
                "options": ["Each extra hour increases GPA by 0.12 on average", "Intercept is 0.12", "Prediction error is 12%", "R² is 0.12"],
                "answer": "Each extra hour increases GPA by 0.12 on average",
                "explanation": "Slope indicates the change in response per unit predictor."},
            17: {"question": "Which study design best supports causal conclusions?",
                "options": ["Random Assignment", "Observational study", "Cohort study", "Cross-sectional survey"],
                "answer": "Randomized experiment",
                "explanation": "Only random assignment in experiments can establish causation."},
            18: {"question": "R² = 0.85 in a regression model means what?",
                "options": ["85% of variance in the response is explained by the predictor", "The predictor explains 85% of cases", "Slope=0.85", "Intercept=0.85"],
                "answer": "85% of variance in the response is explained by the predictor",
                "explanation": "R² measures the proportion of variance explained."},
            19: {"question": "Why does margin of error decrease as sample size increases?",
                "options": ["Standard error decreases", "Z* increases", "P-value drops", "CI widens"],
                "answer": "Standard error decreases",
                "explanation": "SE ∝ 1/√n, so larger n yields smaller SE."},
            20: {"question": "Which scenario uses a paired design?",
                "options": ["Pre-test and post-test on same cadets", "Two independent squads compared", "Comparing platoons", "Gender comparison"],
                "answer": "Pre-test and post-test on same cadets",
                "explanation": "Paired designs use the same subjects measured twice."},
            21: {"question": "What does variance measure?",
                "options": ["Spread around the mean", "Center of data", "Slope of regression", "Probability of success"],
                "answer": "Spread around the mean",
                "explanation": "Variance quantifies how far values deviate from the mean."},
            22: {"question": "When can you generalize from a sample to a population?",
                "options": ["Sample is randomly selected", "Sample size is large", "Null is true", "CI is narrow"],
                "answer": "Sample is randomly selected",
                "explanation": "Random sampling justifies inference to the population."},
            23: {"question": "Compare male vs female ACFT scores. Which test should you use?",
                "options": ["Two-sample t-test", "One-sample t-test", "Chi-square test", "Geometric test"],
                "answer": "Two-sample t-test",
                "explanation": "Use two-sample t-test for comparing means of two independent groups."},
            24: {"question": "Cadets are classified as pass or fail on an event. What type of variable is this?",
                "options": ["Categorical", "Quantitative", "Continuous", "Discrete"],
                "answer": "Categorical",
                "explanation": "Pass/fail is a binary categorical variable."},
            25: {"question": "What is the expected value of a fair six-sided die?",
                "options": ["3.5", "3", "4", "2"],
                "answer": "3.5",
                "explanation": "E[X] = (1+2+3+4+5+6)/6 = 3.5."}
        }

        if "shuffled_questions" not in st.session_state:
            question_order = list(questions.keys())
            random.shuffle(question_order)
            st.session_state["shuffled_questions"] = question_order
        
        if "shuffled_options" not in st.session_state:
            st.session_state["shuffled_options"] = {}
            for q_num, q_data in questions.items():
                opts = q_data["options"][:]
                random.shuffle(opts)
                st.session_state["shuffled_options"][q_num] = opts

        st.subheader("Answer the following questions:")
        for q_num in st.session_state["shuffled_questions"]:
            q_data = questions[q_num]
            sel = st.radio(
                f"Q{q_num}: {q_data['question']}",
                st.session_state["shuffled_options"][q_num],
                key=f"q{q_num}"
            )
            responses[q_num] = sel

        # 2) Disable submit until user-info are nonempty
        disable_submit = not (team_name.strip() and members.strip())
        if disable_submit:
            st.warning("Please enter team name and member names to submit.")
        submitted = st.form_submit_button(
            "Score My Answers",
            disabled=disable_submit
        )

    # scoring
    if submitted:
        score = sum(responses[q] == questions[q]["answer"] for q in st.session_state["shuffled_questions"])
        cap = score * salary_per_question

        # After calculating score and cap
        results_dict = {}
        for q_num, q_data in questions.items():
            is_correct = responses[q_num] == q_data["answer"]
            results_dict[f"Q{q_num}"] = "✅" if is_correct else "❌"

        st.session_state.update({
            "salary_cap": cap,
            "section": section,
            "team_name": team_name,
            "members": members,
            "quiz_results": results_dict
        })

        # show results
        st.subheader("Results:")
        for q_num, q_data in questions.items():
            if responses[q_num] == q_data["answer"]:
                st.markdown(f"✅ Q{q_num}: Correct")
            else:
                st.markdown(f"❌ Q{q_num}: Incorrect — **Correct: {q_data['answer']}**")
                st.caption(q_data["explanation"])

        st.markdown(f"### 🎯 Total Salary Cap: ${cap:,}")
        return cap

    return None

tab_quiz, tab_draft = st.tabs(["🧮 Quiz", "💰 Draft"])

with tab_quiz:
    # 1) Top-level inputs (live)
    section   = st.selectbox("Select Your Section:", ["G1","I1","G2","I2"])
    team_name = st.text_input("Enter Your Team Name:")
    members   = st.text_input("Enter Team Members' Last Names:")

    # Clear submitted_bids if team name or section has changed
    if (
        ("team_name" in st.session_state and team_name != st.session_state["team_name"]) or
        ("section" in st.session_state and section != st.session_state["section"])
    ):
        st.session_state["submitted_bids"] = False

    cap = run_quiz_form(team_name, members, section)   # returns cap or None

with tab_draft:
    if "salary_cap" in st.session_state:
        cap = st.session_state["salary_cap"]
        section = st.session_state["section"]
        team_name = st.session_state["team_name"]
        members = st.session_state["members"]

        df = pd.read_csv("player_stats.csv")

        st.subheader(f"Your Salary Cap: ${cap:,}")
        header_cols = st.columns([4,1,1,1,1,2])
        headers = ["Player", "Pos", "OBP", "SLG", "ERA", "Your Bid"]
        for col, h in zip(header_cols, headers):
            col.markdown(f"**{h}**")

        bids = []
        for i, row in df.iterrows():
            cols = st.columns([4,1,1,1,1,2])
            cols[0].markdown(f"{row.Player}")
            cols[1].markdown(f"{row.Position}")
            cols[2].markdown(f"{row.OBP:.3f}" if not pd.isna(row.OBP) else "")
            cols[3].markdown(f"{row.SLG:.3f}" if not pd.isna(row.SLG) else "")
            cols[4].markdown(f"{row.ERA:.2f}" if not pd.isna(row.ERA) else "")

            bid = cols[5].number_input(
                label="",
                min_value=0,
                max_value=cap,
                value=0,
                step=1,
                key=f"bid_{i}"
            )
            bids.append(bid)

        df["Your Bid"] = bids
        st.markdown("---")
        st.write(f"**Total Bid:** ${sum(bids):,} of ${cap:,}")
        if sum(bids) > cap:
            st.error("You’ve exceeded your Salary Cap!")
        else:
            st.success("All bids are within your cap.")

            if st.session_state.get("submitted_bids", False):
                st.info("✅ You’ve already submitted your bids.")
            else:
                # Construct dictionary
                data_dict = {
                    "Section": section,
                    "Team Name": team_name,
                    "Members": members,
                    "Salary Cap": f"${cap:,}",
                    "Total Bid": f"${sum(bids):,}"
                }

                # Add player bid columns
                for player, bid in zip(df["Player"], bids):
                    data_dict[f"Bid: {player}"] = bid

                # Add quiz correctness columns Q1–Q25
                data_dict.update(st.session_state.get("quiz_results", {}))

                if st.button("Submit Bids to Google Sheet"):
                    send_to_gsheet(data_dict)
                    st.session_state["submitted_bids"] = True
                    st.success("✅ Bids submitted to Google Sheets!")
    else:
        st.info("Finish the quiz first to unlock your Salary Cap.")
