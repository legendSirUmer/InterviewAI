"""
Interview Report Generation Service.
Generates comprehensive AI Interview Performance Reports in both
Markdown format and print-ready styled HTML/CSS.
"""

from datetime import datetime
from utils.helpers import get_score_color


def generate_markdown_report(
    candidate_name,
    target_role,
    experience_level,
    interview_type,
    difficulty,
    personality,
    overall_score,
    feedback_history,
    interview_state=None,
):
    """Generates an extensive Markdown report of the interview performance."""
    interview_state = interview_state or {}
    strong_areas = interview_state.get("strong_areas", ["Core Concepts", "Communication"])
    weak_areas = interview_state.get("weak_areas", ["Edge Case Handling", "Scale Considerations"])

    lines = [
        "# 🎯 AI Interview Performance & Coaching Report",
        "",
        f"**Candidate:** {candidate_name or 'Candidate'}  ",
        f"**Target Role:** {target_role}  ",
        f"**Experience Level:** {experience_level}  ",
        f"**Interview Type:** {interview_type}  ",
        f"**Interviewer Style:** {personality}  ",
        f"**Difficulty Level:** {difficulty}  ",
        f"**Date:** {datetime.now().strftime('%B %d, %Y - %H:%M')}  ",
        f"**Overall Score:** **{overall_score}%**  ",
        "",
        "---",
        "",
        "## 🏆 Executive Summary",
        "",
    ]

    if overall_score >= 80:
        summary_text = "Outstanding performance! The candidate demonstrated deep technical mastery, structured articulation, and sound architectural judgment. Ready for high-bar technical loops."
    elif overall_score >= 65:
        summary_text = "Solid interview demonstration. Shows good foundational competency and practical awareness, but needs more depth on trade-offs, edge cases, and quantifiable impact."
    else:
        summary_text = "Foundational stage. We recommend structured revision on core architecture, clarity of explanation, and technical precision before formal interviews."

    lines.extend([
        f"> {summary_text}",
        "",
        "### Strongest Areas",
    ])
    for s in strong_areas[:4]:
        lines.append(f"- ✓ **{s}**")

    lines.extend([
        "",
        "### Key Focus & Development Areas",
    ])
    for w in weak_areas[:4]:
        lines.append(f"- ⚠ **{w}**")

    lines.extend([
        "",
        "---",
        "",
        "## ⏱️ Personalized 3–5 Hour Preparation Roadmap",
        "",
        f"To elevate your interview readiness for **{target_role}**, complete this high-impact action plan:",
        "",
        "1. **Hour 1: Core Trade-Offs & Architecture Drill**  ",
        f"   - Practice breaking down {weak_areas[0] if weak_areas else 'system design'} concepts using whiteboard or block diagrams.",
        "2. **Hour 2: Structuring Explanations (STAR & Google XYZ)**  ",
        "   - Frame every project discussion around: Context → Technical Hurdle → Your Concrete Action → Quantified Outcome.",
        "3. **Hour 3: Edge Case & Failure Mode Analysis**  ",
        "   - For every solution you propose, proactively analyze concurrency, error handling, and high-load bottlenecks.",
        "4. **Hour 4-5: Mock Simulation Drill**  ",
        "   - Re-run an InterviewAI session on 'Strict' or 'FAANG-style' to stress-test your revised answers.",
        "",
        "---",
        "",
        "## 📝 Question-by-Question Deep Dive",
        "",
    ])

    for i, item in enumerate(feedback_history, start=1):
        fb = item.get("feedback", {})
        voice = item.get("voice_metrics", {})
        lines.extend([
            f"### Question {i}",
            "",
            f"**Question:** *{item.get('question', '')}*",
            "",
            f"**Your Answer:**",
            f"> {item.get('answer', 'No answer recorded.')}",
            "",
        ])

        if voice and voice.get("speaking_pace_wpm"):
            lines.append(
                f"*🎙️ Voice Metrics:* Speaking Pace: **{voice.get('speaking_pace_wpm')} WPM** | "
                f"Filler Words: **{voice.get('filler_words_count')}** | "
                f"Clarity: **{voice.get('clarity_score')}/10**\n"
            )

        lines.extend([
            "**Dimensional Evaluation:**",
            f"- Technical Accuracy: {fb.get('technical_score', 0)}/10",
            f"- Completeness: {fb.get('completeness_score', 0)}/10",
            f"- Depth: {fb.get('depth_score', 0)}/10",
            f"- Communication: {fb.get('communication_score', 0)}/10",
            f"- Problem Solving: {fb.get('problem_solving_score', 0)}/10",
            f"- Role Relevance: {fb.get('role_relevance_score', 0)}/10",
            "",
            "**What You Did Well:**",
        ])
        for st_point in fb.get("what_you_did_well", fb.get("strengths", [])):
            lines.append(f"- {st_point}")

        lines.extend(["", "**What Was Missing:**"])
        for imp_point in fb.get("what_was_missing", fb.get("improvements", [])):
            lines.append(f"- {imp_point}")

        if fb.get("model_answer"):
            lines.extend([
                "",
                "**✨ Recommended Model Answer:**",
                f"> {fb.get('model_answer')}",
                "",
            ])

        lines.append("---\n")

    return "\n".join(lines)


def generate_html_report(
    candidate_name,
    target_role,
    experience_level,
    interview_type,
    difficulty,
    personality,
    overall_score,
    feedback_history,
    interview_state=None,
):
    """Generates a self-contained, beautifully styled HTML report for print/save."""
    interview_state = interview_state or {}
    strong_areas = interview_state.get("strong_areas", ["Core Concepts", "Communication"])
    weak_areas = interview_state.get("weak_areas", ["Edge Case Handling", "Scale Considerations"])
    color = get_score_color(overall_score)

    questions_html = ""
    for i, item in enumerate(feedback_history, start=1):
        fb = item.get("feedback", {})
        voice = item.get("voice_metrics", {})
        
        voice_badge = ""
        if voice and voice.get("speaking_pace_wpm"):
            voice_badge = f"""
            <div style="background:#1e293b; padding:8px 12px; border-radius:6px; margin:10px 0; font-size:12px; color:#94a3b8;">
                🎙️ <b>Voice Analysis:</b> {voice.get('speaking_pace_wpm')} WPM &nbsp;|&nbsp;
                Fillers: {voice.get('filler_words_count')} &nbsp;|&nbsp;
                Duration: {voice.get('duration_seconds')}s &nbsp;|&nbsp;
                Clarity: {voice.get('clarity_score')}/10
            </div>
            """

        strengths_li = "".join(f"<li>{s}</li>" for s in fb.get("what_you_did_well", fb.get("strengths", [])))
        missing_li = "".join(f"<li>{m}</li>" for m in fb.get("what_was_missing", fb.get("improvements", [])))

        questions_html += f"""
        <div class="q-block">
            <div class="q-title">Q{i}: {item.get('question', '')}</div>
            {voice_badge}
            <div class="answer-box"><b>Candidate Answer:</b><br>{item.get('answer', '')}</div>
            
            <div class="grid-6">
                <div class="score-pill">Tech: <b>{fb.get('technical_score',0)}/10</b></div>
                <div class="score-pill">Complete: <b>{fb.get('completeness_score',0)}/10</b></div>
                <div class="score-pill">Depth: <b>{fb.get('depth_score',0)}/10</b></div>
                <div class="score-pill">Comm: <b>{fb.get('communication_score',0)}/10</b></div>
                <div class="score-pill">Problem: <b>{fb.get('problem_solving_score',0)}/10</b></div>
                <div class="score-pill">Relevance: <b>{fb.get('role_relevance_score',0)}/10</b></div>
            </div>

            <div class="feedback-columns">
                <div class="feedback-col good">
                    <b>✓ What You Did Well:</b>
                    <ul>{strengths_li}</ul>
                </div>
                <div class="feedback-col missing">
                    <b>⚠ What Was Missing:</b>
                    <ul>{missing_li}</ul>
                </div>
            </div>

            <div class="ideal-box">
                <b>✨ Model Answer:</b><br>{fb.get('model_answer', '')}
            </div>
        </div>
        """

    strong_badges = "".join(f"<span class='badge strong'>✓ {s}</span> " for s in strong_areas[:5])
    weak_badges = "".join(f"<span class='badge weak'>⚠ {w}</span> " for w in weak_areas[:5])

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>InterviewAI Performance Report - {candidate_name or 'Candidate'}</title>
<style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 40px; line-height: 1.6; }}
    .container {{ max-width: 900px; margin: 0 auto; background: #1e293b; border-radius: 16px; padding: 40px; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5); }}
    .header {{ border-bottom: 2px solid #334155; padding-bottom: 24px; margin-bottom: 30px; }}
    .title {{ font-size: 28px; font-weight: 800; color: #ffffff; margin: 0 0 10px 0; }}
    .meta-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; font-size: 14px; color: #94a3b8; }}
    .score-banner {{ background: linear-gradient(135deg, #1e1b4b, #312e81); border: 2px solid {color}; border-radius: 12px; padding: 24px; text-align: center; margin-bottom: 30px; }}
    .score-banner .num {{ font-size: 56px; font-weight: 900; color: {color}; line-height: 1; }}
    .score-banner .sub {{ font-size: 14px; color: #c7d2fe; text-transform: uppercase; letter-spacing: 1px; margin-top: 6px; }}
    .q-block {{ background: #0f172a; border: 1px solid #334155; border-radius: 12px; padding: 20px; margin-bottom: 24px; }}
    .q-title {{ font-size: 17px; font-weight: 700; color: #38bdf8; margin-bottom: 12px; }}
    .answer-box {{ background: #1e293b; padding: 12px 16px; border-radius: 8px; font-size: 14px; border-left: 4px solid #64748b; margin-bottom: 14px; }}
    .grid-6 {{ display: grid; grid-template-columns: repeat(6, 1fr); gap: 8px; margin-bottom: 14px; }}
    .score-pill {{ background: #1e293b; border: 1px solid #475569; padding: 6px 4px; border-radius: 6px; font-size: 11px; text-align: center; color: #cbd5e1; }}
    .feedback-columns {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 14px; }}
    .feedback-col {{ padding: 14px; border-radius: 8px; font-size: 13px; }}
    .feedback-col.good {{ background: rgba(16, 185, 129, 0.1); border: 1px solid #10b981; color: #a7f3d0; }}
    .feedback-col.missing {{ background: rgba(239, 68, 68, 0.1); border: 1px solid #ef4444; color: #fecdd3; }}
    .ideal-box {{ background: rgba(99, 102, 241, 0.1); border: 1px solid #6366f1; border-radius: 8px; padding: 14px; font-size: 13px; color: #c7d2fe; }}
    .badge {{ display: inline-block; padding: 4px 10px; border-radius: 20px; font-size: 12px; margin-right: 6px; margin-bottom: 6px; }}
    .badge.strong {{ background: rgba(16, 185, 129, 0.2); color: #6ee7b7; border: 1px solid #10b981; }}
    .badge.weak {{ background: rgba(239, 68, 68, 0.2); color: #fca5a5; border: 1px solid #ef4444; }}
    ul {{ margin: 6px 0 0 0; padding-left: 20px; }}
    li {{ margin-bottom: 4px; }}
    @media print {{
        body {{ background: white; color: black; padding: 0; }}
        .container {{ box-shadow: none; padding: 20px; }}
    }}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1 class="title">🎯 AI Interview Performance Report</h1>
        <div class="meta-grid">
            <div>Candidate: <b>{candidate_name or 'Candidate'}</b></div>
            <div>Target Role: <b>{target_role}</b></div>
            <div>Experience: <b>{experience_level}</b></div>
            <div>Type: <b>{interview_type}</b></div>
            <div>Interviewer: <b>{personality}</b></div>
            <div>Difficulty: <b>{difficulty}</b></div>
        </div>
    </div>

    <div class="score-banner">
        <div class="num">{overall_score}%</div>
        <div class="sub">Overall Interview Performance Score</div>
    </div>

    <div style="margin-bottom: 30px;">
        <h3>💪 Strong Areas</h3>
        <div>{strong_badges}</div>
        <h3 style="margin-top:16px;">🔍 Priority Improvement Areas</h3>
        <div>{weak_badges}</div>
    </div>

    <div style="background:#0f172a; border: 1px solid #334155; border-radius:12px; padding:20px; margin-bottom:30px;">
        <h3 style="margin-top:0;">⏱️ 3–5 Hour Targeted Action Plan</h3>
        <ol style="padding-left:20px; font-size:14px; color:#cbd5e1;">
            <li><b>Hour 1: Core Trade-Offs & Architecture Drill:</b> Focus directly on {weak_areas[0] if weak_areas else 'key technical concepts'}.</li>
            <li><b>Hour 2: Answer Structuring:</b> Practice the STAR method (Situation, Task, Action, Result) with quantifiable impact.</li>
            <li><b>Hour 3: Production Bottlenecks & Failure Modes:</b> Analyze how your solutions handle scale, concurrency, and fault recovery.</li>
            <li><b>Hour 4-5: Live Stress-Testing:</b> Re-run an InterviewAI simulation under strict evaluator mode.</li>
        </ol>
    </div>

    <h2>Detailed Q&A Evaluation</h2>
    {questions_html}
</div>
</body>
</html>
"""
