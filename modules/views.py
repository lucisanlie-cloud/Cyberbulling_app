"""
views.py
--------
Views module for CyberShield AI.
Updated version with real metrics, history, full profile and improved home.

Author: Luci Jabba
Copyright (c) 2026 Luci Jabba
"""

import random
import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from .ai_models import analyze_toxicity, analyze_batch
from .database import (
    save_report, get_all_reports, get_all_users, is_admin,
    save_analysis, get_user_history, get_all_history,
    count_users, count_reports, count_analyses, count_toxic_analyses,
    get_reports_by_day,
)
from .export_pdf import generate_reports_pdf
from .email_alerts import send_alert_email, is_email_configured

# Predefined anti-bullying responses
ANTI_BULLYING_RESPONSES = [
    "Please communicate with respect.",
    "Everyone deserves kindness online.",
    "Let's keep conversations positive.",
    "Words can hurt. Let's be respectful.",
    "Respect is essential in any digital community.",
]

# Coordinates for the toxicity map
TOXICITY_MAP_LOCATIONS = pd.DataFrame({
    "lat": [40.7128, 51.5074, 40.4168, 35.6762, 4.7110, -33.8688],
    "lon": [-74.0060, -0.1278, -3.7038, 139.6503, -74.0721, 151.2093],
    "city": ["New York", "London", "Madrid", "Tokyo", "Bogotá", "Sydney"],
})


# ─────────────────────────────────────────────
# HOME (WITH REAL METRICS)
# ─────────────────────────────────────────────

def render_home(conn, username: str) -> None:
    st.markdown(f"### 👋 Welcome, **{username}**")
    st.write("CyberShield AI detects cyberbullying using artificial intelligence.")
    st.markdown("---")

    st.markdown("#### 📊 Platform Statistics")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👥 Registered Users",   count_users(conn))
    col2.metric("🚨 Reported Incidents", count_reports(conn))
    col3.metric("🔍 Analyses Performed", count_analyses(conn))
    col4.metric("☠️ Danger Alerts",      count_toxic_analyses(conn))

    st.markdown("---")

    st.markdown("#### 📈 Reports from the last 30 days")
    df_days = get_reports_by_day(conn)
    if df_days.empty:
        st.info("No reports registered yet.")
    else:
        fig = px.bar(
            df_days, x="fecha", y="total",
            color_discrete_sequence=["#6B21A8"],
            labels={"fecha": "Date", "total": "Reports"},
        )
        fig.update_layout(showlegend=False, margin=dict(t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### 🕒 Your recent analyses")
    history = get_user_history(conn, username)
    if history.empty:
        st.info("You haven't performed any analyses yet.")
    else:
        st.dataframe(history.head(5), use_container_width=True)


# ─────────────────────────────────────────────
# CYBERBULLYING DETECTOR
# ─────────────────────────────────────────────

def render_cyberbullying_detector(model, conn, username: str) -> None:
    st.subheader("🤖 Cyberbullying Detector")
    text = st.text_area("Enter the message to analyze", height=150)

    if st.button("Analyze", key="analyze_single"):
        if not text.strip():
            st.warning("Please enter a message.")
            return

        result = analyze_toxicity(model, text)
        score  = result["score"]

        st.metric("Toxicity Score", f"{score}/100")

        if result["level"] == "safe":
            st.success("✅ Safe message")
        elif result["level"] == "warning":
            st.warning("⚠️ Possible toxicity — please review the content")
        else:
            st.error("🚨 Cyberbullying risk detected")

        save_analysis(conn, username, "text", text[:100], score, result["level"])


# ─────────────────────────────────────────────
# BATCH ANALYZER
# ─────────────────────────────────────────────

def render_batch_analyzer(model, conn, username: str) -> None:
    st.subheader("💬 Batch Comment Analyzer")
    st.info("Enter one comment per line.")
    raw_text = st.text_area("Comments", height=200)

    if st.button("Analyze batch", key="analyze_batch"):
        lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
        if not lines:
            st.warning("Please enter at least one comment.")
            return

        with st.spinner(f"Analyzing {len(lines)} comments…"):
            results = analyze_batch(model, lines)

        df = pd.DataFrame({
            "Comment": lines,
            "Score":   [r["score"] for r in results],
            "Level":   [r["level"] for r in results],
        })
        st.dataframe(df, use_container_width=True)

        avg = sum(r["score"] for r in results) // len(results)
        level = "danger" if avg >= 60 else "warning" if avg >= 30 else "safe"
        save_analysis(conn, username, "batch", f"{len(lines)} comments", avg, level)


# ─────────────────────────────────────────────
# SAFETY SCORE
# ─────────────────────────────────────────────

def render_user_safety_score(model, conn, username: str) -> None:
    st.subheader("🛡 User Safety Score")
    st.info("Analyzes real comments received by a public Instagram profile.")

    col1, col2 = st.columns([3, 1])
    with col1:
        ig_username = st.text_input("Instagram username to evaluate (without @)")
    with col2:
        max_posts = st.number_input("Posts to review", min_value=1, max_value=10, value=3)

    if st.button("Calculate score"):
        if not ig_username:
            st.warning("Please enter a username.")
            return

        from .instagram import get_recent_comments
        with st.spinner(f"Fetching comments from @{ig_username}…"):
            comments = get_recent_comments(ig_username, max_posts=max_posts)

        if not comments:
            st.warning("No comments found.")
            return

        with st.spinner("Analyzing toxicity with AI…"):
            results = analyze_batch(model, comments)

        avg_score = sum(r["score"] for r in results) // len(results)
        safety    = 100 - avg_score
        level     = "danger" if avg_score >= 60 else "warning" if avg_score >= 30 else "safe"

        st.metric(f"Safety score for @{ig_username}", f"{safety}/100")

        if safety >= 70:
            st.success("✅ This profile receives mostly safe comments.")
        elif safety >= 40:
            st.warning("⚠️ This profile receives comments with moderate toxicity.")
        else:
            st.error("🚨 This profile is receiving highly toxic comments.")

        df = pd.DataFrame({
            "Comment":       comments,
            "Toxic Score":   [r["score"] for r in results],
            "Level":         [r["level"] for r in results],
        })
        st.dataframe(df, use_container_width=True)
        save_analysis(conn, username, "instagram", f"@{ig_username}", avg_score, level)


# ─────────────────────────────────────────────
# FAKE ACCOUNT DETECTOR
# ─────────────────────────────────────────────

def render_fake_account_detector(conn, username: str) -> None:
    st.subheader("🕵 Fake Account Detector")
    st.info("Enter a public Instagram username to analyze it automatically.")
    ig_username = st.text_input("Instagram username (without @)")

    if st.button("Analyze account"):
        if not ig_username:
            st.warning("Please enter a username.")
            return

        from .instagram import get_profile_info, analyze_fake_account
        with st.spinner(f"Fetching profile @{ig_username}…"):
            profile = get_profile_info(ig_username)

        if profile is None:
            st.error("Profile not found.")
            return

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Followers",  f"{profile['followers']:,}")
        col2.metric("Following",  f"{profile['following']:,}")
        col3.metric("Posts",      f"{profile['posts']:,}")
        col4.metric("Ratio",      profile["ratio"])

        if profile["is_verified"]:
            st.success("✅ Verified account")
        if profile["is_private"]:
            st.warning("🔒 Private account")
        if profile["biography"]:
            st.caption(f"**Bio:** {profile['biography']}")

        result = analyze_fake_account(profile)
        st.metric("Fake account probability", f"{result['risk_score']}%")
        for indicator in result["indicators"]:
            st.write(indicator)

        if result["level"] == "low":
            st.success("✅ Account with normal indicators.")
        elif result["level"] == "medium":
            st.warning("⚠️ Account with suspicious indicators.")
        else:
            st.error("🚨 High probability of fake account.")

        save_analysis(conn, username, "fake_account", f"@{ig_username}",
                      result["risk_score"],
                      "danger" if result["level"] == "high" else result["level"])


# ─────────────────────────────────────────────
# FULL PROFILE ANALYSIS
# ─────────────────────────────────────────────

def render_full_profile_analysis(model, conn, username: str) -> None:
    st.subheader("🔎 Full Profile Analysis")
    st.info("Comprehensive analysis: profile data + toxicity + authenticity.")
    ig_username = st.text_input("Instagram username (without @)", key="full_profile")

    if st.button("Analyze full profile", type="primary"):
        if not ig_username:
            st.warning("Please enter a username.")
            return

        from .instagram import get_profile_info, get_recent_comments, analyze_fake_account

        with st.spinner("Fetching profile…"):
            profile = get_profile_info(ig_username)

        if not profile:
            st.error("Profile not found.")
            return

        st.markdown("### 👤 Profile Information")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Followers",  f"{profile['followers']:,}")
        col2.metric("Following",  f"{profile['following']:,}")
        col3.metric("Posts",      f"{profile['posts']:,}")
        col4.metric("Ratio",      profile["ratio"])

        if profile["full_name"]:
            st.caption(f"**Name:** {profile['full_name']}")
        if profile["biography"]:
            st.caption(f"**Bio:** {profile['biography']}")
        if profile["is_verified"]:
            st.success("✅ Verified account")
        if profile["is_private"]:
            st.warning("🔒 Private account — comment analysis limited")

        st.markdown("---")

        st.markdown("### 🕵 Authenticity Evaluation")
        fake = analyze_fake_account(profile)
        st.metric("Fake account probability", f"{fake['risk_score']}%")
        for ind in fake["indicators"]:
            st.write(ind)

        st.markdown("---")

        st.markdown("### ☠️ Comment Toxicity Analysis")
        if profile["is_private"]:
            st.warning("Private account — comments cannot be retrieved.")
        else:
            with st.spinner("Fetching comments…"):
                comments = get_recent_comments(ig_username, max_posts=2)

            if comments:
                with st.spinner("Analyzing toxicity…"):
                    results = analyze_batch(model, comments)

                avg_score = sum(r["score"] for r in results) // len(results)
                safety    = 100 - avg_score

                col1, col2 = st.columns(2)
                col1.metric("Safety Score",      f"{safety}/100")
                col2.metric("Average Toxicity",  f"{avg_score}/100")

                df = pd.DataFrame({
                    "Comment":  comments,
                    "Toxicity": [r["score"] for r in results],
                    "Level":    [r["level"] for r in results],
                })
                st.dataframe(df, use_container_width=True)

                fig = px.histogram(
                    df, x="Level", color="Level",
                    color_discrete_map={"safe": "#16A34A", "warning": "#D97706", "danger": "#DC2626"},
                    title="Toxicity level distribution",
                )
                st.plotly_chart(fig, use_container_width=True)

                level = "danger" if avg_score >= 60 else "warning" if avg_score >= 30 else "safe"
                save_analysis(conn, username, "full_profile", f"@{ig_username}", avg_score, level)
            else:
                st.info("No public comments found.")


# ─────────────────────────────────────────────
# ANALYSIS HISTORY
# ─────────────────────────────────────────────

def render_analysis_history(conn, username: str) -> None:
    st.subheader("🕒 My Analysis History")

    history = get_user_history(conn, username)

    if history.empty:
        st.info("You haven't performed any analyses yet.")
        return

    col1, col2, col3 = st.columns(3)
    col1.metric("Total analyses", len(history))
    col2.metric("Dangerous",      len(history[history["level"] == "danger"]))
    col3.metric("Safe",           len(history[history["level"] == "safe"]))

    types = ["All"] + history["type"].unique().tolist()
    filter_type = st.selectbox("Filter by type", types)
    if filter_type != "All":
        history = history[history["type"] == filter_type]

    def color_level(val):
        colors = {"safe": "background-color: #DCFCE7", "warning": "background-color: #FEF9C3", "danger": "background-color: #FEE2E2"}
        return colors.get(val, "")

    st.dataframe(
        history.style.applymap(color_level, subset=["level"]),
        use_container_width=True
    )


# ─────────────────────────────────────────────
# EMOTION ANALYSIS
# ─────────────────────────────────────────────

def render_emotion_analysis(model) -> None:
    st.subheader("🧠 Emotion Analysis")
    text = st.text_area("Text to analyze emotionally", height=120)

    if st.button("Analyze emotions"):
        if not text.strip():
            st.warning("Please enter a text.")
            return

        result = analyze_toxicity(model, text)
        score  = result["score"]

        emotions_data = pd.DataFrame({
            "Emotion":   ["Anger", "Sadness", "Fear", "Neutral"],
            "Intensity": [max(0, score - 10), max(0, score // 2), max(0, score // 3), max(0, 100 - score)],
        })
        fig = px.bar(emotions_data, x="Emotion", y="Intensity",
                     color="Emotion", title="Emotional Distribution")
        st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────
# STATISTICS
# ─────────────────────────────────────────────

def render_statistics(conn) -> None:
    st.subheader("📊 General Statistics")

    reports_df = get_all_reports(conn)
    history_df = get_all_history(conn)

    if reports_df.empty and history_df.empty:
        st.info("Not enough data to display statistics yet.")
        return

    col1, col2 = st.columns(2)

    with col1:
        if not reports_df.empty:
            top_aggressors = reports_df["aggressor"].value_counts().head(5).reset_index()
            top_aggressors.columns = ["Aggressor", "Reports"]
            fig = px.bar(top_aggressors, x="Aggressor", y="Reports",
                         title="Top reported aggressors",
                         color_discrete_sequence=["#6B21A8"])
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        if not history_df.empty:
            level_counts = history_df["level"].value_counts().reset_index()
            level_counts.columns = ["Level", "Total"]
            fig = px.pie(level_counts, names="Level", values="Total",
                         title="Toxicity level distribution",
                         color="Level",
                         color_discrete_map={"safe": "#16A34A", "warning": "#D97706", "danger": "#DC2626"})
            st.plotly_chart(fig, use_container_width=True)

    df_days = get_reports_by_day(conn)
    if not df_days.empty:
        fig = px.line(df_days, x="fecha", y="total",
                      title="Report trend (last 30 days)",
                      color_discrete_sequence=["#6B21A8"])
        st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────
# AI DASHBOARD
# ─────────────────────────────────────────────

def render_ai_dashboard(conn) -> None:
    st.subheader("📊 Artificial Intelligence Dashboard")

    history_df = get_all_history(conn)
    if history_df.empty:
        st.info("No analyses to display in the dashboard yet.")
        return

    col1, col2 = st.columns(2)
    with col1:
        type_counts = history_df["type"].value_counts().reset_index()
        type_counts.columns = ["Type", "Total"]
        fig = px.bar(type_counts, x="Type", y="Total",
                     color="Total", color_continuous_scale="Purples",
                     title="Analyses performed by type")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        avg_by_type = history_df.groupby("type")["score"].mean().reset_index()
        avg_by_type.columns = ["Type", "Average Score"]
        fig = px.bar(avg_by_type, x="Type", y="Average Score",
                     color="Average Score", color_continuous_scale="Reds",
                     title="Average toxicity by analysis type")
        st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────
# ANTI-BULLYING RESPONSE
# ─────────────────────────────────────────────

def render_anti_bullying_response() -> None:
    st.subheader("🤖 Anti-Bullying Response Generator")
    toxic_msg = st.text_area("Toxic message received", height=120)

    if st.button("Generate response"):
        if not toxic_msg.strip():
            st.warning("Please enter the toxic message.")
            return
        response = random.choice(ANTI_BULLYING_RESPONSES)
        st.success(f"**Suggested response:** {response}")


# ─────────────────────────────────────────────
# TOXICITY MAP
# ─────────────────────────────────────────────

def render_toxicity_map() -> None:
    st.subheader("🌍 Global Toxicity Map")
    st.info("Locations with the highest report incidence (demo data).")
    st.map(TOXICITY_MAP_LOCATIONS[["lat", "lon"]])
    st.dataframe(TOXICITY_MAP_LOCATIONS, use_container_width=True)


# ─────────────────────────────────────────────
# REPORT INCIDENT
# ─────────────────────────────────────────────

def render_report_incident(conn, username: str) -> None:
    st.subheader("🚨 Report Incident")

    aggressor = st.text_input("Aggressor's username")
    message   = st.text_area("Incident description", height=150)

    if st.button("Submit report"):
        if not aggressor or not message.strip():
            st.warning("Please fill in all fields.")
            return

        save_report(conn, reporter=username, aggressor=aggressor, message=message)
        st.success("✅ Report submitted successfully.")

        try:
            from .ai_models import load_toxicity_model
            model = load_toxicity_model()
            result = analyze_toxicity(model, message)
            if result["level"] == "danger":
                sent = send_alert_email(username, aggressor, message, result["score"])
                if sent:
                    st.info("📧 An alert email was sent to the administrator.")
        except Exception:
            pass


# ─────────────────────────────────────────────
# EDUCATION
# ─────────────────────────────────────────────

def render_education() -> None:
    st.subheader("📚 Cyberbullying Education")
    st.markdown("""
    ### What is cyberbullying?
    Cyberbullying is the use of digital technologies to harass, threaten,
    humiliate, or attack other people.

    ### Types of cyberbullying
    - **Direct harassment**: offensive messages sent directly to the victim.
    - **Exclusion**: deliberately excluding someone from online groups or activities.
    - **Doxing**: publishing someone's private information without their consent.
    - **Impersonation**: pretending to be someone else to damage their reputation.

    ### What to do if you are a victim?
    1. Do not respond to aggressive messages.
    2. Save evidence (screenshots).
    3. Block the aggressor.
    4. Report on the corresponding platform.
    5. Seek support from a trusted adult or authority.
    """)


# ─────────────────────────────────────────────
# ADMIN PANEL
# ─────────────────────────────────────────────

def render_admin_panel(conn, username: str) -> None:
    if not is_admin(conn, username):
        st.error("🚫 Access denied.")
        return

    st.subheader("⚙ Admin Panel")
    st.success(f"✅ Active admin session: **{username}**")

    tab1, tab2, tab3 = st.tabs(["👥 Users", "🚨 Reports", "🔍 Analysis History"])

    with tab1:
        users_df = get_all_users(conn)
        st.dataframe(users_df, use_container_width=True)

    with tab2:
        reports_df = get_all_reports(conn)
        if reports_df.empty:
            st.info("No reports registered yet.")
        else:
            st.dataframe(reports_df, use_container_width=True)
            if st.button("📥 Download PDF report", type="primary"):
                with st.spinner("Generating PDF…"):
                    try:
                        pdf_bytes = generate_reports_pdf(reports_df, total_users=len(users_df))
                        st.download_button(
                            label="⬇️ Click here to download",
                            data=pdf_bytes,
                            file_name=f"cybershield_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                            mime="application/pdf",
                        )
                        st.success("✅ PDF generated.")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")

    with tab3:
        history_df = get_all_history(conn)
        if history_df.empty:
            st.info("No analyses registered yet.")
        else:
            st.dataframe(history_df, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 📧 Email alert status")
    if is_email_configured():
        st.success("✅ Email notifications configured.")
    else:
        st.warning("⚠️ Email not configured. Add EMAIL_SENDER, EMAIL_PASSWORD and EMAIL_RECEIVER as environment variables.")


# ─────────────────────────────────────────────
# PRIVACY POLICY
# ─────────────────────────────────────────────

def render_privacy_policy():
    st.title("🔒 Privacy Policy")
    st.markdown("**Last updated: 03/09/2026**")
    st.divider()
    st.markdown("""
## Cyberbullying App

Cyberbullying App is a tool designed to help identify and analyze potentially harmful or abusive 
comments on social media platforms. The goal is to promote safer online environments by detecting 
possible cyberbullying patterns.

---

### Introduction
Cyberbullying App respects the privacy of its users. This Privacy Policy explains how we collect, 
use, and protect information when using our application.

---

### Information We Collect
- Public social media data that users choose to analyze.
- Basic technical information such as device type or operating system.
- User-provided content for cyberbullying detection.

**We do not collect sensitive personal information without user consent.**

---

### How We Use Information
- Analyze texts and comments to detect cyberbullying.
- Improve the functionality and security of the application.
- Enhance the user experience.

---

### Sharing of Information
**We do not sell, trade, or share users' personal information with third parties.**

---

### Data Security
We take reasonable measures to protect user information from unauthorized access or disclosure.

---

### Third-Party Services
Our app may interact with third-party services such as social media platforms. 
Their own privacy policies may apply.

---

### Changes to This Policy
We may update this Privacy Policy occasionally. Updates will be posted on this page.

---

### User Data Deletion
If you would like to request deletion of your data, follow these steps:
1. Send an email to: **lujabbali@gmail.com**
2. Subject: **"Data Deletion Request"**
3. Include your username or account identifier.

We will delete your data within a reasonable time after receiving your request.

---

### Contact
📧 **lujabbali@gmail.com**
    """)
