"""
Interviewer Agent.
Supports 6 distinct interviewer personalities and 6 interview types.
Generates razor-sharp, humanized questions that directly probe the candidate's
specific projects, tech stack, and experiences extracted via Categorized RAG.
"""

from services.groq_service import call_groq_llm


PERSONALITY_PROMPTS = {
    "Friendly & Encouraging": """
Tone: Warm, supportive, conversational, and encouraging.
Style: You invite the candidate to share their thought process and guide them naturally.
Example phrasing: "Good to hear that! Could you walk me through how you handled...", "That sounds interesting—what was the most exciting challenge when you built...?"
""",
    "Professional & Structured": """
Tone: Objective, articulate, structured, and balanced.
Style: You sound like an experienced corporate hiring director or senior engineering lead.
Example phrasing: "Let's discuss your experience with X. How did you design the interface between...", "What criteria did you use to select Y over alternative solutions?"
""",
    "Strict & Demanding": """
Tone: Direct, unyielding, rigorous, and skeptical of vague buzzwords.
Style: You demand exact technical depth, metrics, and production edge cases.
Example phrasing: "That sounds fine in theory, but explain how this handles 10 million concurrent writes without data loss.", "Why wouldn't this approach introduce a major latency bottleneck at scale?"
""",
    "FAANG-Style": """
Tone: Intellectually rigorous, focused on distributed systems, trade-offs, and Big-O efficiency.
Style: You probe system boundaries, concurrency, consistency vs availability, and microservice trade-offs.
Example phrasing: "At scale, network partitions and failovers are inevitable. How does your service maintain data consistency across distributed replicas?", "What are the time and space complexity bottlenecks of that algorithm?"
""",
    "Startup CTO": """
Tone: Fast-paced, pragmatic, product-minded, and scrappy.
Style: You focus on rapid execution, balancing technical debt with shipping speed, and practical trade-offs.
Example phrasing: "If we need to get an MVP of this deployed by next Tuesday, what would you strip out and what must stay?", "How would you monitor and debug this in production without an enterprise observability suite?"
""",
    "HR Manager": """
Tone: Empathetic, culturally observant, collaborative, and situational.
Style: You probe behavioral dynamics, conflict resolution, teamwork, ownership, and communication.
Example phrasing: "Can you tell me about a time when you strongly disagreed with a team decision? How did you navigate that?", "Describe a situation where a project deadline slipped and how you communicated that to stakeholders."
""",
}

INTERVIEW_TYPE_GUIDES = {
    "Technical & System Design": "Focus on core concepts, frameworks, data pipelines, database models, and scalable architectures.",
    "Behavioral (STAR Method)": "Focus on past experiences using the STAR method (Situation, Task, Action, Result). Ask for specific real-world examples.",
    "HR & Culture Fit": "Focus on motivation, cross-functional collaboration, adaptability, and personal values.",
    "System Design": "Focus exclusively on distributed systems, data storage, caching layers, load balancers, and failure modes.",
    "Coding & Algorithms": "Focus on algorithmic problem solving, edge case identification, and computational complexity.",
    "Mixed Technical & Behavioral": "Alternate seamlessly between technical execution depth and team/ownership behavior.",
}


def generate_interview_question(
    client,
    target_role,
    experience_level,
    interview_type,
    difficulty,
    question_number,
    personality="Professional & Structured",
    interview_state=None,
    previous_question="",
    previous_answer="",
    previous_feedback=None,
    rag_context="",
):
    """
    Generates a single, direct, humanized interview question.
    Adapts based on current state (recent weaknesses, target skills, difficulty).
    """
    interview_state = interview_state or {}
    personality_prompt = PERSONALITY_PROMPTS.get(
        personality, PERSONALITY_PROMPTS["Professional & Structured"]
    )
    type_guide = INTERVIEW_TYPE_GUIDES.get(
        interview_type, INTERVIEW_TYPE_GUIDES["Technical & System Design"]
    )

    is_follow_up = False
    drill_concept = ""
    if previous_feedback:
        tech_score = previous_feedback.get("technical_score", 10)
        if tech_score < 6.5 and previous_feedback.get("what_was_missing"):
            is_follow_up = True
            drill_concept = previous_feedback.get("what_was_missing")[0]

    system_prompt = f"""
You are an expert, live human interviewer conducting an interview.
{personality_prompt}

Interview Domain Focus:
{type_guide}

STRICT INSTRUCTIONS:
- Ask exactly ONE short, natural, conversational question (1 to 2 sentences maximum).
- NEVER include preamble, greetings ("Hello", "Thank you"), bullet points, or multiple sub-questions.
- DO NOT explain why you are asking the question or provide hints in the question itself.
- If the candidate's resume/JD context mentions a specific technology or project (e.g. "Django REST APIs and Docker"), cite it directly!
  Example: "You mentioned deploying Django applications with Docker. Walk me through how you containerized the application and handled production configuration."
- Output ONLY the question itself. No quotes, no markdown headers.
"""

    user_prompt = f"""
Target Role: {target_role}
Experience Level: {experience_level}
Current Difficulty: {difficulty}
Question Number: #{question_number}
Skills Already Tested: {', '.join(interview_state.get('skills_tested', [])) or 'None yet'}
Identified Weak Areas: {', '.join(interview_state.get('weak_areas', [])) or 'None yet'}

Candidate Document & RAG Context:
{rag_context or "No specific document context."}

Previous Question: {previous_question or "None (start of interview)"}
Previous Candidate Answer: {previous_answer or "None"}
{'Special Follow-up Goal: Candidate had gaps regarding: ' + drill_concept if is_follow_up else ''}

Ask the next question now:
"""

    return call_groq_llm(
        client,
        system_prompt,
        user_prompt,
        temperature=0.65,
        max_tokens=150,
    )
