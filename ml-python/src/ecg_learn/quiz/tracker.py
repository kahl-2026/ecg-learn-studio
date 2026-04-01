"""Quiz Progress Tracker"""

from typing import Dict, List
from datetime import datetime


class QuizProgressTracker:
    """Track user's quiz progress and performance."""
    
    def __init__(self):
        """Initialize tracker."""
        self.history: List[Dict] = []
        self.current_streak = 0
        self.best_streak = 0
    
    def record_answer(
        self,
        question_id: str,
        category: str,
        correct: bool
    ):
        """Record a quiz answer."""
        self.history.append({
            'question_id': question_id,
            'category': category,
            'correct': correct,
            'timestamp': datetime.now().isoformat()
        })
        
        # Update streak
        if correct:
            self.current_streak += 1
            self.best_streak = max(self.best_streak, self.current_streak)
        else:
            self.current_streak = 0
    
    def get_statistics(self) -> Dict:
        """Get overall quiz statistics."""
        if not self.history:
            return {
                'total_questions': 0,
                'correct_count': 0,
                'accuracy': 0,
                'current_streak': 0,
                'best_streak': 0
            }
        
        total = len(self.history)
        correct = sum(1 for h in self.history if h['correct'])
        
        # Category performance
        category_stats = {}
        for record in self.history:
            cat = record['category']
            if cat not in category_stats:
                category_stats[cat] = {'total': 0, 'correct': 0}
            category_stats[cat]['total'] += 1
            if record['correct']:
                category_stats[cat]['correct'] += 1
        
        # Calculate category accuracies
        for cat in category_stats:
            stats = category_stats[cat]
            stats['accuracy'] = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
        
        return {
            'total_questions': total,
            'correct_count': correct,
            'accuracy': correct / total if total > 0 else 0,
            'current_streak': self.current_streak,
            'best_streak': self.best_streak,
            'by_category': category_stats
        }
    
    def get_weak_areas(self, threshold: float = 0.6) -> List[str]:
        """Identify categories where performance is below threshold."""
        stats = self.get_statistics()
        weak = []
        
        for category, cat_stats in stats.get('by_category', {}).items():
            if cat_stats['accuracy'] < threshold and cat_stats['total'] >= 3:
                weak.append(category)
        
        return weak
    
    def reset(self):
        """Reset progress tracker."""
        self.history = []
        self.current_streak = 0
        self.best_streak = 0
