"""
Feedback & Answer Comparison Component.
Renders the side-by-side comparative review cards:
Candidate Answer vs 6-Dimension Evaluation vs Model Ideal Answer vs What Was Missed.
"""

import html
import streamlit as st


def render_comparative_feedback(qa_item, index, total_items):
    """
    Renders an expandable comparison card for a completed question/answer interaction.
    """
    fb = qa_item.get("feedback", {})
    voice = qa_item.get("voice_metrics", {})
    q_num = total_items - index + 1

    tech_score = fb.get("technical_score", 0)
    avg_score = round(
        sum([
            fb.get("technical_score", 0),
            fb.get("completeness_score", 0),
            fb.get("depth_score", 0),
            fb.get("communication_score", 0),
            fb.get("problem_solving_score", 0),
            fb.get("role_relevance_score", 0),
        ]) / 6.0,
        1,
    )

    badge_emoji = "🟢" if avg_score >= 8.0 else "🟡" if avg_score >= 6.5 else "🔴"

    with st.expander(
        f"{badge_emoji} Q{q_num}: {qa_item.get('question', '')[:95]}... [Score: {avg_score}/10]",
        expanded=(index == 1),
    ):
        # Voice analysis banner if available
        if voice and voice.get("speaking_pace_wpm"):
            st.markdown(
                f"""
                <div style="background: rgba(56, 189, 248, 0.08); border: 1px solid #0284C7; border-radius: 8px; padding: 10px 14px; margin-bottom: 12px; font-size: 13px;">
                    🎙️ <b>Speech Analysis:</b> Pace: <span style="color:#38BDF8; font-weight:700;">{voice.get('speaking_pace_wpm')} WPM</span> ({voice.get('pace_rating', 'Optimal')}) &nbsp;|&nbsp;
                    Fillers: <span style="color:#FBBF24; font-weight:700;">{voice.get('filler_words_count')}</span> &nbsp;|&nbsp;
                    Duration: <span>{voice.get('duration_seconds')}s</span> &nbsp;|&nbsp;
                    Clarity: <span style="color:#34D399; font-weight:700;">{voice.get('clarity_score')}/10</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # 6-Dimensional Score Pills
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col1.metric("Technical", f"{fb.get('technical_score', 0)}/10")
        col2.metric("Completeness", f"{fb.get('completeness_score', 0)}/10")
        col3.metric("Depth", f"{fb.get('depth_score', 0)}/10")
        col4.metric("Communication", f"{fb.get('communication_score', 0)}/10")
        col5.metric("Problem Solving", f"{fb.get('problem_solving_score', 0)}/10")
        col6.metric("Role Relevance", f"{fb.get('role_relevance_score', 0)}/10")

        st.markdown("<br>", unsafe_allow_html=True)

        # Side-by-Side: Your Answer vs Model Ideal Answer
        c_left, c_right = st.columns(2)

        with c_left:
            st.markdown(
                f"""
                <div class="comparison-box box-user-answer">
                    <b style="color:#94A3B8;">YOUR ANSWER:</b><br>
                    {html.escape(qa_item.get('answer', ''))}
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                """
                <div class="comparison-box box-missing">
                    <b style="color:#F87171;">WHAT WAS MISSING:</b><br>
                """
                + "".join([f"• {html.escape(m)}<br>" for m in fb.get("what_was_missing", fb.get("improvements", []))])
                + "</div>",
                unsafe_allow_html=True,
            )

        with c_right:
            st.markdown(
                f"""
                <div class="comparison-box box-ideal-answer">
                    <b style="color:#34D399;">✨ IDEAL MODEL ANSWER:</b><br>
                    {html.escape(fb.get('model_answer', ''))}
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                """
                <div class="comparison-box box-structure">
                    <b style="color:#818CF8;">🎯 BETTER ANSWER STRUCTURE:</b><br>
                """
                + "".join([f"• {html.escape(s)}<br>" for s in fb.get("better_answer_structure", [])])
                + "</div>",
                unsafe_allow_html=True,
            )

        # Strengths bullet points
        st.markdown("**✓ What You Did Well:**")
        for s in fb.get("what_you_did_well", fb.get("strengths", [])):
            st.write(f"• {s}")
