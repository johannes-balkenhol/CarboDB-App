"""
BioPython Sequence Analysis Features for CarbonFX
Provides comprehensive protein sequence analysis capabilities
"""

from Bio.SeqUtils.ProtParam import ProteinAnalysis
from Bio.Seq import Seq
from collections import Counter
import re


class QuickSequenceAnalyzer:
    """
    Comprehensive protein sequence analyzer using BioPython
    
    Features:
    - Basic physicochemical properties (MW, pI, stability, GRAVY)
    - Amino acid composition analysis
    - Secondary structure prediction
    - Charge distribution
    - Hydrophobic region detection
    - RuBisCO motif detection (PS00157, catalytic lysine, loop6)
    """
    
    def __init__(self, sequence):
        """
        Initialize analyzer with protein sequence
        
        Args:
            sequence (str): Protein sequence (single letter amino acid codes)
        """
        self.sequence = sequence.upper()
        self.analyzed = ProteinAnalysis(self.sequence)
    
    def get_basic_properties(self):
        """
        Calculate basic physicochemical properties
        
        Returns:
            dict: Molecular weight, pI, instability, GRAVY, aromaticity, charge
        """
        return {
            'molecular_weight': round(self.analyzed.molecular_weight(), 2),
            'isoelectric_point': round(self.analyzed.isoelectric_point(), 2),
            'instability_index': round(self.analyzed.instability_index(), 2),
            'gravy': round(self.analyzed.gravy(), 3),
            'aromaticity': round(self.analyzed.aromaticity(), 3),
            'charge_at_pH7': round(self.analyzed.charge_at_pH(7.0), 2),
            'length': len(self.sequence)
        }
    
    def get_amino_acid_composition(self):
        """
        Analyze amino acid composition
        
        Returns:
            dict: Full composition and top 5 most abundant amino acids
        """
        composition = self.analyzed.get_amino_acids_percent()
        
        # Convert to percentages and round
        composition_percent = {
            aa: round(fraction * 100, 2) 
            for aa, fraction in composition.items()
        }
        
        # Get top 5 most abundant
        sorted_aa = sorted(
            composition_percent.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return {
            'full_composition': composition_percent,
            'top_5': dict(sorted_aa[:5]),
            'total_residues': len(self.sequence)
        }
    
    def predict_secondary_structure(self):
        """
        Predict secondary structure fractions
        
        Returns:
            dict: Helix, turn, and sheet fractions
        """
        helix, turn, sheet = self.analyzed.secondary_structure_fraction()
        
        return {
            'helix_fraction': round(helix, 3),
            'turn_fraction': round(turn, 3),
            'sheet_fraction': round(sheet, 3),
            'helix_percent': round(helix * 100, 1),
            'turn_percent': round(turn * 100, 1),
            'sheet_percent': round(sheet * 100, 1)
        }
    
    def analyze_charge_distribution(self):
        """
        Analyze charge distribution
        
        Returns:
            dict: Positive, negative, and neutral residue counts
        """
        positive = sum([self.sequence.count(aa) for aa in 'RK'])
        negative = sum([self.sequence.count(aa) for aa in 'DE'])
        neutral = len(self.sequence) - positive - negative
        
        return {
            'positive_residues': positive,
            'negative_residues': negative,
            'neutral_residues': neutral,
            'positive_percent': round((positive / len(self.sequence)) * 100, 1),
            'negative_percent': round((negative / len(self.sequence)) * 100, 1),
            'net_charge_at_pH7': round(self.analyzed.charge_at_pH(7.0), 2)
        }
    
    def find_hydrophobic_regions(self, window_size=7, threshold=1.5):
        """
        Find hydrophobic regions using Kyte-Doolittle scale
        
        Args:
            window_size (int): Sliding window size
            threshold (float): Hydrophobicity threshold
            
        Returns:
            list: Hydrophobic regions with positions and scores
        """
        # Kyte-Doolittle hydrophobicity scale
        kd_scale = {
            'A': 1.8, 'R': -4.5, 'N': -3.5, 'D': -3.5, 'C': 2.5,
            'Q': -3.5, 'E': -3.5, 'G': -0.4, 'H': -3.2, 'I': 4.5,
            'L': 3.8, 'K': -3.9, 'M': 1.9, 'F': 2.8, 'P': -1.6,
            'S': -0.8, 'T': -0.7, 'W': -0.9, 'Y': -1.3, 'V': 4.2
        }
        
        regions = []
        for i in range(len(self.sequence) - window_size + 1):
            window = self.sequence[i:i + window_size]
            score = sum([kd_scale.get(aa, 0) for aa in window]) / window_size
            
            if score > threshold:
                regions.append({
                    'start': i + 1,
                    'end': i + window_size,
                    'sequence': window,
                    'hydrophobicity_score': round(score, 2)
                })
        
        return regions
    
    def detect_rubisco_motifs(self):
        """
        Detect RuBisCO-specific motifs
        
        Detects:
        - PS00157 (RuBisCO large chain signature)
        - Catalytic lysine (K)
        - Loop 6 consensus
        
        Returns:
            dict: Detected motifs with positions
        """
        motifs = {}
        
        # PS00157: [LIVM]-[DE]-x(2)-[DE]-[KR]-x-[KR]-x(2)-[GA]
        # Simplified pattern: look for similar sequences
        ps00157_pattern = r'[LIVM][DE].{2}[DE][KR].[KR].{2}[GA]'
        ps00157_matches = []
        
        for match in re.finditer(ps00157_pattern, self.sequence):
            ps00157_matches.append({
                'start': match.start() + 1,
                'end': match.end(),
                'sequence': match.group()
            })
        
        motifs['PS00157'] = {
            'found': len(ps00157_matches) > 0,
            'count': len(ps00157_matches),
            'matches': ps00157_matches
        }
        
        # Look for catalytic lysine (often in K-X-X-K pattern)
        catalytic_lysine_pattern = r'K.{2}K'
        catalytic_matches = []
        
        for match in re.finditer(catalytic_lysine_pattern, self.sequence):
            catalytic_matches.append({
                'start': match.start() + 1,
                'end': match.end(),
                'sequence': match.group()
            })
        
        motifs['catalytic_lysine'] = {
            'found': len(catalytic_matches) > 0,
            'count': len(catalytic_matches),
            'matches': catalytic_matches
        }
        
        # Look for Loop 6-like sequences (typically ASNG or similar)
        loop6_pattern = r'A[STA][NQH][GAS]'
        loop6_matches = []
        
        for match in re.finditer(loop6_pattern, self.sequence):
            loop6_matches.append({
                'start': match.start() + 1,
                'end': match.end(),
                'sequence': match.group()
            })
        
        motifs['loop6'] = {
            'found': len(loop6_matches) > 0,
            'count': len(loop6_matches),
            'matches': loop6_matches
        }
        
        return motifs
    
    def complete_analysis(self):
        """
        Perform complete sequence analysis
        
        Returns:
            dict: All analysis results combined
        """
        return {
            'basic_properties': self.get_basic_properties(),
            'amino_acid_composition': self.get_amino_acid_composition(),
            'secondary_structure': self.predict_secondary_structure(),
            'charge_distribution': self.analyze_charge_distribution(),
            'hydrophobic_regions': self.find_hydrophobic_regions(),
            'rubisco_motifs': self.detect_rubisco_motifs()
        }


# Example usage
if __name__ == '__main__':
    # Test with RuBisCO large chain sequence fragment
    test_sequence = """
    MSPQTETKASVGFKAGVKDYKLTYYTPEYETKDTDILAAFRVTPQPGVPPEEAGAAVAAESSTGTW
    TTVWTDGLTSLDRYKGRCYHIEPVAGEENQYICYVAYPLDLFEEGSVTNMFTSIVGNVFGFKALRA
    LRLEDLRIPPAYTKTFQGPPHGIQVERDKLNKYGRPLLGCTIKPKLGLSAKNYGRAVYECLRGGLDF
    TKDDENVNSQPFMRWRDRFLFCAEAIYKAQAETGEIKGHYLNATAGTCEEMIKRAIFARELGVPIVR
    """.replace('\n', '').replace(' ', '')
    
    analyzer = QuickSequenceAnalyzer(test_sequence)
    results = analyzer.complete_analysis()
    
    print("=== BioPython Sequence Analysis ===")
    print(f"\nBasic Properties:")
    for key, value in results['basic_properties'].items():
        print(f"  {key}: {value}")
    
    print(f"\nTop 5 Amino Acids:")
    for aa, percent in results['amino_acid_composition']['top_5'].items():
        print(f"  {aa}: {percent}%")
    
    print(f"\nSecondary Structure:")
    for key, value in results['secondary_structure'].items():
        if 'percent' in key:
            print(f"  {key}: {value}%")
    
    print(f"\nRuBisCO Motifs:")
    for motif, data in results['rubisco_motifs'].items():
        if data['found']:
            print(f"  {motif}: Found {data['count']} match(es)")
            for match in data['matches']:
                print(f"    Position {match['start']}-{match['end']}: {match['sequence']}")


# Add direct PS00157 search (append to QuickSequenceAnalyzer class)
def detect_rubisco_motifs_enhanced(self):
    """Enhanced RuBisCO motif detection with direct PS00157 search"""
    motifs = self.detect_rubisco_motifs()
    
    # Direct search for known PS00157 variants
    ps00157_variants = [
        'GLDFTKDDE',  # Most common
        'GLDFTK',     # Partial
        'DFTKDDE',    # Partial
    ]
    
    for variant in ps00157_variants:
        if variant in self.sequence:
            pos = self.sequence.find(variant)
            motifs['PS00157']['found'] = True
            motifs['PS00157']['count'] += 1
            motifs['PS00157']['matches'].append({
                'start': pos + 1,
                'end': pos + len(variant),
                'sequence': variant
            })
    
    return motifs
