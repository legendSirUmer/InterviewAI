"""
Adaptive Interview Manager.
Maintains the dynamic interview state, updates difficulty levels,
tracks skills tested, records strong and weak competencies, and orchestrates
curriculum flow vs follow-up drill-downs.
"""

DIFFICULTY_LEVELS = ["Easy", "Medium", "Hard", "Expert"]


class AdaptiveInterviewManager:
    """
    Stateful controller managing an adaptive interview session.
    """

    def __init__(self, initial_difficulty="Medium", interview_plan=None):
        self.difficulty = initial_difficulty
        self.question_number = 1
        self.skills_tested = []
        self.weak_areas = []
        self.strong_areas = []
        self.recent_scores = []
        self.interview_plan = interview_plan or []

    def get_state(self):
        """Returns the serializable state dictionary."""
        return {
            "difficulty": self.difficulty,
            "question_number": self.question_number,
            "skills_tested": list(dict.fromkeys(self.skills_tested)),
            "weak_areas": list(dict.fromkeys(self.weak_areas)),
            "strong_areas": list(dict.fromkeys(self.strong_areas)),
            "recent_scores": self.recent_scores[-5:],
            "interview_plan": self.interview_plan,
        }

    def load_state(self, state_dict):
        """Restores manager from a state dictionary."""
        if not state_dict:
            return
        self.difficulty = state_dict.get("difficulty", self.difficulty)
        self.question_number = state_dict.get("question_number", self.question_number)
        self.skills_tested = state_dict.get("skills_tested", self.skills_tested)
        self.weak_areas = state_dict.get("weak_areas", self.weak_areas)
        self.strong_areas = state_dict.get("strong_areas", self.strong_areas)
        self.recent_scores = state_dict.get("recent_scores", self.recent_scores)
        self.interview_plan = state_dict.get("interview_plan", self.interview_plan)

    def process_evaluation(self, feedback):
        """
        Updates internal state based on the latest evaluation feedback:
        - Calculates average dimensional score
        - Classifies skill as strong or weak
        - Dynamically adapts difficulty up or down
        - Returns adaptive directive: 'increase_difficulty', 'drill_down_follow_up', or 'continue_curriculum'
        """
        if not feedback:
            return "continue_curriculum"

        dim_scores = [
            feedback.get("technical_score", 0),
            feedback.get("completeness_score", 0),
            feedback.get("depth_score", 0),
            feedback.get("communication_score", 0),
            feedback.get("problem_solving_score", 0),
            feedback.get("role_relevance_score", 0),
        ]
        valid_scores = [s for s in dim_scores if isinstance(s, (int, float)) and s > 0]
        avg_score = sum(valid_scores) / len(valid_scores) if valid_scores else 6.0
        self.recent_scores.append(round(avg_score, 2))

        tested_skill = feedback.get("tested_skill", "General Technical")
        if tested_skill and tested_skill not in self.skills_tested:
            self.skills_tested.append(tested_skill)

        # Categorize strengths & weaknesses
        if avg_score >= 8.0:
            if tested_skill not in self.strong_areas:
                self.strong_areas.append(tested_skill)
            if tested_skill in self.weak_areas:
                self.weak_areas.remove(tested_skill)
        elif avg_score < 6.0:
            if tested_skill not in self.weak_areas:
                self.weak_areas.append(tested_skill)
            for missing_item in feedback.get("what_was_missing", []):
                clean_item = missing_item.split(".")[0]
                if clean_item and clean_item not in self.weak_areas:
                    self.weak_areas.append(clean_item)

        # Adaptive difficulty scaling logic
        curr_idx = DIFFICULTY_LEVELS.index(self.difficulty) if self.difficulty in DIFFICULTY_LEVELS else 1

        # Check last 2 scores for trends
        last_two = self.recent_scores[-2:]
        if len(last_two) >= 2 and all(s >= 8.0 for s in last_two) and curr_idx < len(DIFFICULTY_LEVELS) - 1:
            self.difficulty = DIFFICULTY_LEVELS[curr_idx + 1]
            directive = "increase_difficulty"
        elif avg_score < 5.8:
            directive = "drill_down_follow_up"
        elif len(last_two) >= 2 and all(s < 5.5 for s in last_two) and curr_idx > 0:
            self.difficulty = DIFFICULTY_LEVELS[curr_idx - 1]
            directive = "decrease_difficulty"
        else:
            directive = "continue_curriculum"

        self.question_number += 1
        return directive
