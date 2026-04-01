"""ECG Glossary - Medical terms and definitions"""

from typing import Dict, List, Optional


class ECGGlossary:
    """ECG terminology glossary with beginner and intermediate definitions."""
    
    def __init__(self):
        """Initialize glossary."""
        self.terms = self._load_terms()
    
    def _load_terms(self) -> Dict:
        """Load glossary terms."""
        return {
            'ecg': {
                'term': 'ECG / EKG',
                'beginner': 'A test that records the electrical activity of your heart over time.',
                'intermediate': 'Electrocardiogram: graphical representation of cardiac electrical activity recorded via skin electrodes.',
                'category': 'basics'
            },
            'arrhythmia': {
                'term': 'Arrhythmia',
                'beginner': 'An irregular heartbeat - when your heart beats too fast, too slow, or irregularly.',
                'intermediate': 'Deviation from normal cardiac rhythm, including abnormalities in rate, regularity, site of origin, or conduction.',
                'category': 'conditions'
            },
            'atrial_fibrillation': {
                'term': 'Atrial Fibrillation (AFib)',
                'beginner': 'A condition where the upper chambers of your heart quiver instead of beating normally, causing an irregular pulse.',
                'intermediate': 'Supraventricular tachyarrhythmia characterized by uncoordinated atrial activation and irregular ventricular response.',
                'category': 'arrhythmias'
            },
            'p_wave': {
                'term': 'P Wave',
                'beginner': 'The first small bump in each heartbeat on an ECG, showing the top chambers contracting.',
                'intermediate': 'Represents atrial depolarization; normal duration <0.12s, amplitude <2.5mm.',
                'category': 'waves'
            },
            'qrs_complex': {
                'term': 'QRS Complex',
                'beginner': 'The tall spike in the ECG showing the main pumping chambers contracting.',
                'intermediate': 'Represents ventricular depolarization; normal duration 0.06-0.10s with characteristic morphology.',
                'category': 'waves'
            },
            't_wave': {
                'term': 'T Wave',
                'beginner': 'The rounded bump after the QRS, showing the heart muscle recovering.',
                'intermediate': 'Represents ventricular repolarization; normally upright in most leads, follows ST segment.',
                'category': 'waves'
            },
            'pr_interval': {
                'term': 'PR Interval',
                'beginner': 'Time from when the top chambers start to when bottom chambers start - should be 0.12-0.20 seconds.',
                'intermediate': 'Measured from start of P to start of QRS; represents atrial depolarization and AV nodal conduction delay.',
                'category': 'intervals'
            },
            'qt_interval': {
                'term': 'QT Interval',
                'beginner': 'Total time for the bottom chambers to contract and recover.',
                'intermediate': 'From start of QRS to end of T wave; represents total ventricular depolarization and repolarization.',
                'category': 'intervals'
            },
            'rr_interval': {
                'term': 'RR Interval',
                'beginner': 'Time between heartbeats - used to calculate heart rate.',
                'intermediate': 'Time between successive R waves; variability indicates autonomic tone and rhythm regularity.',
                'category': 'intervals'
            },
            'heart_rate': {
                'term': 'Heart Rate',
                'beginner': 'How many times your heart beats per minute. Normal is 60-100 bpm.',
                'intermediate': 'Ventricular rate calculated as 60/RR interval or 300/large squares between R waves.',
                'category': 'measurements'
            },
            'bradycardia': {
                'term': 'Bradycardia',
                'beginner': 'When your heart beats slower than normal (less than 60 beats per minute).',
                'intermediate': 'Heart rate <60 bpm; may be physiological or pathological depending on context.',
                'category': 'arrhythmias'
            },
            'tachycardia': {
                'term': 'Tachycardia',
                'beginner': 'When your heart beats faster than normal (more than 100 beats per minute).',
                'intermediate': 'Heart rate >100 bpm; classified as supraventricular or ventricular based on QRS width.',
                'category': 'arrhythmias'
            },
            'pvc': {
                'term': 'PVC (Premature Ventricular Contraction)',
                'beginner': 'An extra heartbeat that starts in the wrong place, making a wide unusual spike on the ECG.',
                'intermediate': 'Ectopic beat originating from ventricles; wide QRS (>0.12s), no preceding P wave, compensatory pause.',
                'category': 'arrhythmias'
            },
            'depolarization': {
                'term': 'Depolarization',
                'beginner': 'When heart muscle cells get electrically activated, causing them to contract.',
                'intermediate': 'Rapid reversal of membrane potential from negative to positive, triggering myocardial contraction.',
                'category': 'physiology'
            },
            'repolarization': {
                'term': 'Repolarization',
                'beginner': 'When heart muscle cells reset after contracting, getting ready for the next beat.',
                'intermediate': 'Return of membrane potential to resting state following depolarization; vulnerable period for arrhythmias.',
                'category': 'physiology'
            },
            'lead': {
                'term': 'Lead',
                'beginner': 'A specific view of the heart\'s electrical activity from different angles.',
                'intermediate': 'Recording of electrical potential difference between two electrodes; standard 12-lead provides spatial orientation.',
                'category': 'basics'
            },
            'av_node': {
                'term': 'AV Node',
                'beginner': 'A relay station that slows down electrical signals between top and bottom heart chambers.',
                'intermediate': 'Atrioventricular node; provides physiological conduction delay allowing ventricular filling.',
                'category': 'anatomy'
            },
            'bundle_branch_block': {
                'term': 'Bundle Branch Block',
                'beginner': 'When the electrical signal takes an abnormal path through the heart, making a wide QRS complex.',
                'intermediate': 'Conduction delay in right or left bundle branch; QRS >0.12s with characteristic morphology.',
                'category': 'conditions'
            },
            'st_segment': {
                'term': 'ST Segment',
                'beginner': 'The flat line between the QRS and T wave - elevation or depression can indicate heart problems.',
                'intermediate': 'Isoelectric segment from J-point to T wave onset; elevation/depression suggests ischemia or injury.',
                'category': 'segments'
            },
            'sinus_rhythm': {
                'term': 'Sinus Rhythm',
                'beginner': 'Normal heartbeat pattern starting from the heart\'s natural pacemaker.',
                'intermediate': 'Normal rhythm originating from SA node; regular P waves preceding each QRS, rate 60-100 bpm.',
                'category': 'rhythms'
            }
        }
    
    def get_definition(self, term_id: str, difficulty: str = 'beginner') -> Optional[Dict]:
        """Get term definition."""
        term = self.terms.get(term_id.lower())
        if term:
            definition = term.get(difficulty, term['beginner'])
            return {
                'term': term['term'],
                'definition': definition,
                'category': term['category'],
                'difficulty': difficulty
            }
        return None
    
    def search(self, query: str) -> List[Dict]:
        """Search glossary."""
        query_lower = query.lower()
        results = []
        
        for term_id, term in self.terms.items():
            if query_lower in term['term'].lower() or query_lower in term_id:
                results.append({
                    'id': term_id,
                    'term': term['term'],
                    'category': term['category']
                })
        
        return results
    
    def get_all_terms(self) -> List[Dict]:
        """Get all glossary terms."""
        return [
            {
                'id': term_id,
                'term': term['term'],
                'category': term['category']
            }
            for term_id, term in self.terms.items()
        ]
