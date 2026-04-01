"""Quiz Question Bank"""

from typing import Dict, List, Optional
import random


class QuizQuestionBank:
    """Manage quiz questions."""
    
    def __init__(self, seed: int = 42):
        """Initialize question bank."""
        self.questions = self._load_questions()
        self.rng = random.Random(seed)
    
    def _load_questions(self) -> Dict:
        """Load quiz questions."""
        return {
            'basics_001': {
                'id': 'basics_001',
                'category': 'ECG Basics',
                'difficulty': 'easy',
                'question': 'What does ECG stand for?',
                'options': [
                    'Electrocardiogram',
                    'Electrocardiac Generator',
                    'Electronic Cardiac Graph',
                    'Electro Chest Graph'
                ],
                'correct_answer': 0,
                'explanation': 'ECG stands for Electrocardiogram (or EKG from German Elektrokardiogramm). It records the electrical activity of the heart.'
            },
            'basics_002': {
                'id': 'basics_002',
                'category': 'ECG Basics',
                'difficulty': 'easy',
                'question': 'What is a normal resting heart rate for adults?',
                'options': [
                    '40-50 beats per minute',
                    '60-100 beats per minute',
                    '100-120 beats per minute',
                    '120-150 beats per minute'
                ],
                'correct_answer': 1,
                'explanation': 'Normal resting heart rate for adults is 60-100 beats per minute. Athletes may have lower rates due to conditioning.'
            },
            'waves_001': {
                'id': 'waves_001',
                'category': 'Wave Identification',
                'difficulty': 'easy',
                'question': 'What does the P wave represent?',
                'options': [
                    'Ventricular depolarization',
                    'Atrial depolarization',
                    'Ventricular repolarization',
                    'Atrial repolarization'
                ],
                'correct_answer': 1,
                'explanation': 'The P wave represents atrial depolarization - the electrical activation and contraction of the atria (upper chambers).'
            },
            'waves_002': {
                'id': 'waves_002',
                'category': 'Wave Identification',
                'difficulty': 'easy',
                'question': 'Which part of the ECG represents ventricular contraction?',
                'options': [
                    'P wave',
                    'PR interval',
                    'QRS complex',
                    'T wave'
                ],
                'correct_answer': 2,
                'explanation': 'The QRS complex represents ventricular depolarization, which causes the ventricles (main pumping chambers) to contract.'
            },
            'waves_003': {
                'id': 'waves_003',
                'category': 'Wave Identification',
                'difficulty': 'medium',
                'question': 'What is the normal duration of a QRS complex?',
                'options': [
                    '0.02-0.04 seconds',
                    '0.06-0.10 seconds',
                    '0.12-0.20 seconds',
                    '0.20-0.30 seconds'
                ],
                'correct_answer': 1,
                'explanation': 'A normal QRS complex is 0.06-0.10 seconds (narrow). A wide QRS (>0.12s) suggests abnormal ventricular conduction.'
            },
            'intervals_001': {
                'id': 'intervals_001',
                'category': 'Intervals',
                'difficulty': 'medium',
                'question': 'What does a prolonged PR interval indicate?',
                'options': [
                    'Fast heart rate',
                    'First-degree AV block',
                    'Atrial fibrillation',
                    'Ventricular tachycardia'
                ],
                'correct_answer': 1,
                'explanation': 'A PR interval >0.20 seconds indicates first-degree AV block - delayed conduction through the AV node.'
            },
            'rhythm_001': {
                'id': 'rhythm_001',
                'category': 'Rhythm Recognition',
                'difficulty': 'easy',
                'question': 'What is the main characteristic of atrial fibrillation on ECG?',
                'options': [
                    'Very slow heart rate',
                    'Irregular rhythm with no clear P waves',
                    'Wide QRS complexes',
                    'Elevated ST segments'
                ],
                'correct_answer': 1,
                'explanation': 'Atrial fibrillation shows an irregularly irregular rhythm with absent P waves, replaced by fibrillatory waves.'
            },
            'rhythm_002': {
                'id': 'rhythm_002',
                'category': 'Rhythm Recognition',
                'difficulty': 'easy',
                'question': 'What defines bradycardia?',
                'options': [
                    'Heart rate below 50 bpm',
                    'Heart rate below 60 bpm',
                    'Irregular heart rhythm',
                    'Heart rate above 100 bpm'
                ],
                'correct_answer': 1,
                'explanation': 'Bradycardia is defined as a heart rate below 60 beats per minute. It may be normal for athletes or indicate pathology.'
            },
            'rhythm_003': {
                'id': 'rhythm_003',
                'category': 'Rhythm Recognition',
                'difficulty': 'medium',
                'question': 'How can you identify a PVC (Premature Ventricular Contraction)?',
                'options': [
                    'Narrow QRS complex occurring early',
                    'Wide bizarre QRS complex occurring early',
                    'Absent P wave with normal QRS',
                    'Inverted T wave only'
                ],
                'correct_answer': 1,
                'explanation': 'PVCs appear as wide (>0.12s), bizarre QRS complexes that occur earlier than expected, without a preceding P wave.'
            },
            'metrics_001': {
                'id': 'metrics_001',
                'category': 'ML Metrics',
                'difficulty': 'easy',
                'question': 'What does accuracy measure in ML classification?',
                'options': [
                    'Only correct positive predictions',
                    'Proportion of all correct predictions',
                    'Ability to find all positive cases',
                    'Confidence of predictions'
                ],
                'correct_answer': 1,
                'explanation': 'Accuracy is the proportion of correct predictions out of all predictions: (TP + TN) / (TP + TN + FP + FN).'
            },
            'metrics_002': {
                'id': 'metrics_002',
                'category': 'ML Metrics',
                'difficulty': 'medium',
                'question': 'What does recall (sensitivity) measure?',
                'options': [
                    'Proportion of predicted positives that are correct',
                    'Proportion of actual positives that were found',
                    'Overall accuracy of the model',
                    'Confidence in predictions'
                ],
                'correct_answer': 1,
                'explanation': 'Recall measures the proportion of actual positive cases that the model correctly identified: TP / (TP + FN).'
            },
            'metrics_003': {
                'id': 'metrics_003',
                'category': 'ML Metrics',
                'difficulty': 'medium',
                'question': 'What is the F1 score?',
                'options': [
                    'Average of accuracy and recall',
                    'Harmonic mean of precision and recall',
                    'Product of precision and recall',
                    'Maximum of precision and recall'
                ],
                'correct_answer': 1,
                'explanation': 'F1 score is the harmonic mean of precision and recall: 2 * (precision * recall) / (precision + recall).'
            },
            'arrhythmia_001': {
                'id': 'arrhythmia_001',
                'category': 'Arrhythmias',
                'difficulty': 'medium',
                'question': 'In atrial fibrillation, why are there no P waves?',
                'options': [
                    'The atria are not working',
                    'The atria are fibrillating (quivering) chaotically',
                    'The signal is blocked at AV node',
                    'The ventricles are taking over'
                ],
                'correct_answer': 1,
                'explanation': 'In AFib, the atria fibrillate (quiver) chaotically at 350-600 bpm, producing no organized P waves, only irregular fibrillatory waves.'
            },
            'arrhythmia_002': {
                'id': 'arrhythmia_002',
                'category': 'Arrhythmias',
                'difficulty': 'hard',
                'question': 'What is the main risk of untreated atrial fibrillation?',
                'options': [
                    'Immediate cardiac arrest',
                    'Blood clots and stroke',
                    'Heart stops beating',
                    'Always causes chest pain'
                ],
                'correct_answer': 1,
                'explanation': 'AFib causes blood pooling in atria, increasing risk of clot formation. These clots can travel to the brain causing stroke.'
            }
        }
    
    def get_questions(
        self,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
        count: int = 10
    ) -> List[Dict]:
        """Get quiz questions with optional filtering."""
        # Filter questions
        filtered = []
        for q in self.questions.values():
            if category and q['category'] != category:
                continue
            if difficulty and q['difficulty'] != difficulty:
                continue
            filtered.append(q)
        
        # Shuffle and limit
        self.rng.shuffle(filtered)
        return filtered[:count]
    
    def check_answer(self, question_id: str, answer_index: int) -> Dict:
        """Check if answer is correct."""
        question = self.questions.get(question_id)
        if not question:
            return {'error': 'Question not found'}
        
        correct = answer_index == question['correct_answer']
        
        return {
            'correct': correct,
            'correct_answer_index': question['correct_answer'],
            'correct_answer_text': question['options'][question['correct_answer']],
            'explanation': question['explanation']
        }
    
    def get_categories(self) -> List[str]:
        """Get list of categories."""
        categories = set(q['category'] for q in self.questions.values())
        return sorted(list(categories))
