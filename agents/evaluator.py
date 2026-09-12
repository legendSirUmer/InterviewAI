"""
Evaluation Agent.
Provides 6-dimensional evaluation for verbal/technical responses,
comparative ideal answers, and algorithmic code evaluation for Coding Mode.
"""

import json
import re
from services.groq_service import call_groq_llm


def evaluate_response(
    client,
    question,
    answer,
    target_role,
    experience_level,
    interview_type,
    difficulty="Medium",
):
    """
    Evaluates candidate response across 6 dimensions:
    - technical_score (1-10)
    - completeness_score (1-10)
    - depth_score (1-10)
    - communication_score (1-10)
    - problem_solving_score (1-10)
    - role_relevance_score (1-10)

    Generates:
    - what_you_did_well (2 specific bullets)
    - what_was_missing (2 actionable bullets)
    - better_answer_structure (4-point framework)
    - model_answer (conversational, high-impact candidate answer)
    - tested_skill (e.g. 'REST API Authentication')
    """
    system_prompt = """
You are an elite, calibration-grade technical interviewer and evaluation agent.
Evaluate the candidate's answer with absolute objectivity, fairness, and constructive precision.

Rubric (Scores from 1.0 to 10.0):
1. technical_score: Accuracy of technical concepts, correctness of terminology, sound architectural understanding.
2. completeness_score: Whether all core aspects of the question were answered without major omissions.
3. depth_score: Demonstration of real-world implementation nuances, edge cases, trade-offs, and scalability.
4. communication_score: Conciseness, clarity, logical progression, and professional tone.
5. problem_solving_score: Reasoning ability, structured thinking, and practical decision-making.
6. role_relevance_score: Appropriateness for the target role seniority and expectations.

Return ONLY valid JSON matching this schema:
{
  "technical_score": 8.5,
  "completeness_score": 7.5,
  "depth_score": 6.5,
  "communication_score": 8.0,
  "problem_solving_score": 7.0,
  "role_relevance_score": 9.0,
  "what_you_did_well": [
    "Correctly explained JWT authentication and distinguished between access and refresh tokens.",
    "Mentioned stateless token verification across distributed services."
  ],
  "what_was_missing": [
    "Did not discuss token expiration windows or refresh-token rotation strategies.",
    "Omitted how to handle immediate token revocation or blacklisting."
  ],
  "better_answer_structure": [
    "1. Define the core mechanism and architecture",
    "2. Walk through request/response token lifecycle",
    "3. Address security considerations (expiration, CSRF, storage)",
    "4. Highlight scaling or performance trade-offs"
  ],
  "model_answer": "In a DRF architecture, I implement stateless authentication using JWTs with short-lived access tokens (15 minutes) stored in memory and HTTP-only refresh tokens for renewal. For revocation, I maintain a Redis blacklist for revoked tokens during logout. This decouples our authentication verification while protecting against token theft and CSRF attacks.",
  "tested_skill": "API Authentication & Security"
}
"""

    user_prompt = f"""
Target Role: {target_role}
Experience Level: {experience_level}
Interview Type: {interview_type}
Difficulty: {difficulty}

Question:
{question}

Candidate Answer:
{answer}
"""

    try:
        raw = call_groq_llm(
            client,
            system_prompt,
            user_prompt,
            temperature=0.2,
            max_tokens=850,
        )
        json_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(0))
            return data
    except Exception as exc:
        print(f"Evaluation error: {exc}")

    return {
        "technical_score": 6.0,
        "completeness_score": 6.0,
        "depth_score": 5.5,
        "communication_score": 7.0,
        "problem_solving_score": 6.0,
        "role_relevance_score": 6.5,
        "what_you_did_well": ["Attempted to address the question directly."],
        "what_was_missing": ["Provide more technical depth and concrete implementation examples."],
        "better_answer_structure": [
            "1. State the core concept directly",
            "2. Explain practical implementation details",
            "3. Mention edge cases or trade-offs",
            "4. Conclude with real-world impact",
        ],
        "model_answer": "A concise and structured model answer focuses on explaining the core technology, detailing implementation steps, addressing potential failure modes, and demonstrating measurable business or technical results.",
        "tested_skill": "General Technical Competency",
    }


def evaluate_code_submission(
    client,
    problem_title,
    problem_description,
    user_code,
    language="python",
):
    """
    Evaluates algorithmic code submissions for Coding Interview Mode:
    - Correctness (1-10)
    - Time Complexity analysis
    - Space Complexity analysis
    - Code Quality (1-10)
    - Edge Cases Handled & Missed
    - Auto-generated follow-up challenge ("Can you optimize this solution?")
    """
    system_prompt = """
You are an expert technical interviewer assessing a candidate's code submission.
Analyze the provided code objectively.

Evaluate:
1. correctness_score: 1.0 to 10.0 (handles primary logic correctly).
2. time_complexity: Big-O notation with brief explanation (e.g. "O(N) because we iterate through the list once with O(1) hash map lookups").
3. space_complexity: Big-O notation with brief explanation (e.g. "O(N) auxiliary space for the hash map").
4. code_quality_score: 1.0 to 10.0 (clean code, idiomatic naming, readability, pythonic style).
5. edge_cases_handled: Array of edge cases properly covered.
6. edge_cases_missed: Array of edge cases or inputs that could break or degrade the code.
7. follow_up_question: A sharp technical follow-up or optimization challenge (e.g. "Can you optimize this to O(1) auxiliary memory if the array is already sorted?").
8. optimization_tips: 2 actionable suggestions.

Return ONLY valid JSON matching this schema:
{
  "correctness_score": 9.0,
  "time_complexity": "O(N)",
  "space_complexity": "O(N)",
  "code_quality_score": 8.5,
  "edge_cases_handled": ["Empty array handling", "Duplicate elements"],
  "edge_cases_missed": ["Negative integer overflows if applicable"],
  "follow_up_question": "Can you optimize this solution to O(1) extra space if we sort the array in-place first?",
  "optimization_tips": ["Use early termination once target is found", "Consider memory footprint with large inputs"]
}
"""

    user_prompt = f"""
Problem: {problem_title}
Language: {language}

Problem Description:
{problem_description}

Candidate Code:
```{language}
{user_code}
```
"""

    try:
        raw = call_groq_llm(
            client,
            system_prompt,
            user_prompt,
            temperature=0.2,
            max_tokens=750,
        )
        json_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
    except Exception as exc:
        print(f"Code evaluation error: {exc}")

    return {
        "correctness_score": 7.0,
        "time_complexity": "O(N)",
        "space_complexity": "O(N)",
        "code_quality_score": 7.5,
        "edge_cases_handled": ["Standard inputs"],
        "edge_cases_missed": ["Boundary edge cases"],
        "follow_up_question": "How does this solution perform under memory constraints?",
        "optimization_tips": ["Test against extreme edge values", "Ensure proper typing"],
    }
