"""Lesson Manager - ECG educational content"""

from typing import Dict, List, Optional


class LessonManager:
    """Manage ECG learning lessons."""
    
    def __init__(self):
        """Initialize lesson manager with content."""
        self.lessons = self._load_lessons()
    
    def _load_lessons(self) -> Dict:
        """Load all lesson content."""
        return {
            'ecg_basics': {
                'id': 'ecg_basics',
                'title': 'What is an ECG?',
                'category': 'basics',
                'difficulty': 'beginner',
                'duration_minutes': 5,
                'content': {
                    'beginner': """
# What is an ECG?

An **electrocardiogram (ECG or EKG)** is a test that records the electrical activity of your heart.

## How it works:
- Your heart produces electrical signals that cause it to beat
- These signals can be detected by sensors placed on your skin
- The ECG machine draws these signals as waves on paper or a screen

## What it shows:
- **Heart rate**: How fast your heart is beating
- **Rhythm**: Whether your heartbeat is regular or irregular
- **Heart health**: Signs of heart problems or damage

Think of it like listening to your heart's electrical conversation!
""",
                    'intermediate': """
# Electrocardiography Fundamentals

The ECG records the heart's electrical activity through the cardiac cycle.

## Physiological Basis:
- **Depolarization**: Electrical activation causes muscle contraction
- **Repolarization**: Return to resting state
- **Conduction system**: SA node → AV node → Bundle of His → Purkinje fibers

## Clinical Significance:
- Diagnose arrhythmias, ischemia, and structural abnormalities
- Monitor medication effects and pacemaker function
- Standard 12-lead provides comprehensive cardiac electrical map
"""
                }
            },
            
            'p_wave': {
                'id': 'p_wave',
                'title': 'The P Wave - Atrial Activation',
                'category': 'waves',
                'difficulty': 'beginner',
                'duration_minutes': 7,
                'content': {
                    'beginner': """
# The P Wave

The P wave is the first small bump you see in an ECG heartbeat.

## What it represents:
- **Atrial contraction**: The top chambers of your heart (atria) contracting
- **Beginning of heartbeat**: It starts each cardiac cycle

## Normal P wave:
- **Shape**: Smooth, rounded bump
- **Duration**: Less than 0.12 seconds (3 small squares)
- **Height**: Less than 2.5 mm

## What abnormalities mean:
- **No P wave**: Atria aren't working normally (like in atrial fibrillation)
- **Tall P wave**: Atria may be enlarged
- **Wide P wave**: Electrical signal is traveling slowly through atria
""",
                    'intermediate': """
# P Wave Analysis

## Electrophysiology:
- Represents atrial depolarization (right then left atrium)
- Originates from SA node in right atrium
- Duration: 0.06-0.11 seconds

## Morphology Assessment:
- **Amplitude**: <0.25 mV in limb leads, <0.15 mV in V1-V2
- **Axis**: Normally upright in leads I, II, aVF
- **Notching**: Bifid P wave suggests left atrial enlargement

## Pathological Findings:
- **P mitrale**: Notched P wave in left atrial enlargement
- **P pulmonale**: Peaked P wave in right atrial enlargement
- **Absent P waves**: AF, junctional rhythm, ventricular pacing
"""
                }
            },
            
            'qrs_complex': {
                'id': 'qrs_complex',
                'title': 'The QRS Complex - Ventricular Activation',
                'category': 'waves',
                'difficulty': 'beginner',
                'duration_minutes': 10,
                'content': {
                    'beginner': """
# The QRS Complex

The QRS complex is the tall, sharp spike in the ECG - the most noticeable part!

## What it represents:
- **Ventricular contraction**: The main pumping chambers contracting
- **The main heartbeat**: When blood is pumped out to your body

## Parts of QRS:
- **Q wave**: Small downward dip (not always present)
- **R wave**: Tall upward spike (the main peak)
- **S wave**: Downward dip after the R wave

## Normal QRS:
- **Duration**: 0.06 to 0.10 seconds (narrow and sharp)
- **Height**: Varies by lead, but typically 5-20 mm

## Why it matters:
- **Too wide**: Signal is taking abnormal path (bundle branch block)
- **Bizarre shape**: Could indicate ventricular problems
- **Too tall or too short**: May indicate heart chamber enlargement
""",
                    'intermediate': """
# QRS Complex Analysis

## Electrophysiology:
- Represents rapid ventricular depolarization
- Conducted via His-Purkinje system
- Normal duration: 0.06-0.10 seconds (<2.5 small squares)

## Components:
- **Q wave**: Septal depolarization (initial negative deflection)
- **R wave**: Ventricular free wall depolarization (positive deflection)
- **S wave**: Late ventricular depolarization (terminal negative deflection)

## Pathological Patterns:
- **Wide QRS (>0.12s)**: Bundle branch block, ventricular origin
- **Deep Q waves**: Prior myocardial infarction
- **Poor R wave progression**: Anterior MI or LVH
- **Delta wave**: Wolff-Parkinson-White pre-excitation

## Voltage Criteria:
- LVH: Sokolow-Lyon (S in V1 + R in V5/V6 > 35 mm)
- RVH: R wave in V1 > 7 mm
"""
                }
            },
            
            'pr_interval': {
                'id': 'pr_interval',
                'title': 'PR Interval - Conduction Time',
                'category': 'intervals',
                'difficulty': 'beginner',
                'duration_minutes': 6,
                'content': {
                    'beginner': """
# The PR Interval

The PR interval is the time from the start of the P wave to the start of the QRS complex.

## What it measures:
- **Conduction time**: How long it takes for the electrical signal to travel from atria to ventricles
- **AV node delay**: Built-in delay to allow atria to empty into ventricles

## Normal PR interval:
- **Duration**: 0.12 to 0.20 seconds (3-5 small squares)
- **Consistent**: Should be the same for each heartbeat

## Abnormalities:
- **Too short (<0.12s)**: Signal is bypassing normal path (pre-excitation)
- **Too long (>0.20s)**: First-degree AV block (delayed conduction)
- **Variable**: Second-degree AV block (intermittent conduction)
- **Unrelated P and QRS**: Third-degree AV block (complete block)
""",
                    'intermediate': """
# PR Interval Evaluation

## Measurement:
- Start of P wave to start of QRS complex
- Normal: 0.12-0.20 seconds (120-200 ms)
- Represents atrial depolarization + AV nodal conduction

## AV Conduction Abnormalities:
- **Short PR (<0.12s)**: 
  - WPW syndrome (delta wave present)
  - AV nodal reentry pathway
  - Junctional rhythm

- **Prolonged PR (>0.20s)**:
  - First-degree AV block (constant prolongation)
  - Drug effects (beta-blockers, calcium channel blockers, digoxin)
  - Structural AV nodal disease

- **Variable PR**:
  - Second-degree AV block Type I (Wenckebach)
  - Second-degree AV block Type II (Mobitz II)

- **No relationship**: Third-degree (complete) AV block
"""
                }
            },
            
            'arrhythmias': {
                'id': 'arrhythmias',
                'title': 'Understanding Arrhythmias',
                'category': 'advanced',
                'difficulty': 'intermediate',
                'duration_minutes': 15,
                'content': {
                    'beginner': """
# What Are Arrhythmias?

An arrhythmia is when your heart beats irregularly, too fast, or too slow.

## Types we'll study:

### 1. Normal Sinus Rhythm
- Regular heartbeat, 60-100 beats per minute
- This is what we want!

### 2. Atrial Fibrillation (AFib)
- Irregular, chaotic rhythm
- Atria quiver instead of contracting normally
- No clear P waves visible

### 3. Bradycardia
- Heart rate below 60 beats per minute
- Can be normal for athletes
- May cause dizziness if too slow

### 4. Tachycardia
- Heart rate above 100 beats per minute
- Can be normal during exercise
- May feel like racing heart

### 5. Premature Ventricular Contractions (PVCs)
- Extra heartbeats from ventricles
- Appear as wide, unusual QRS complexes
- Often feel like a "skipped beat"
""",
                    'intermediate': """
# Arrhythmia Classification

## By Origin:
- **Supraventricular**: Atrial or AV nodal origin
- **Ventricular**: Ventricular origin (wide QRS)

## Five Arrhythmias in This Course:

### 1. Normal Sinus Rhythm
- Rate: 60-100 bpm
- Regular RR intervals
- Each P wave followed by QRS

### 2. Atrial Fibrillation
- Irregularly irregular rhythm
- No discrete P waves (fibrillatory waves instead)
- Variable ventricular response
- Risk of thromboembolism

### 3. Bradycardia
- Rate < 60 bpm
- May be sinus bradycardia or AV block
- Physiological in athletes or during sleep

### 4. Tachycardia
- Rate > 100 bpm
- Narrow QRS: supraventricular
- Wide QRS: ventricular or aberrant conduction

### 5. PVCs
- Premature beats
- Wide QRS (>0.12s), bizarre morphology
- Compensatory pause
- Occasional PVCs usually benign
"""
                }
            }
        }
    
    def get_lesson(self, lesson_id: str, difficulty: str = 'beginner') -> Optional[Dict]:
        """
        Get lesson content.
        
        Args:
            lesson_id: Lesson identifier
            difficulty: 'beginner' or 'intermediate'
            
        Returns:
            Lesson dictionary or None
        """
        lesson = self.lessons.get(lesson_id)
        if lesson:
            return {
                **lesson,
                'content_text': lesson['content'].get(difficulty, lesson['content']['beginner'])
            }
        return None
    
    def list_lessons(self, category: Optional[str] = None) -> List[Dict]:
        """
        List available lessons.
        
        Args:
            category: Optional category filter
            
        Returns:
            List of lesson summaries
        """
        lessons = []
        for lesson_id, lesson in self.lessons.items():
            if category is None or lesson['category'] == category:
                lessons.append({
                    'id': lesson['id'],
                    'title': lesson['title'],
                    'category': lesson['category'],
                    'difficulty': lesson['difficulty'],
                    'duration_minutes': lesson['duration_minutes']
                })
        return lessons
    
    def get_categories(self) -> List[str]:
        """Get list of lesson categories."""
        categories = set(lesson['category'] for lesson in self.lessons.values())
        return sorted(list(categories))
