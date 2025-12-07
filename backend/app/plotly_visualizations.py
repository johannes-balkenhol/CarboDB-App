"""
Plotly Visualization Module for CarbonFX
Creates interactive charts for protein sequence analysis
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots


class SequenceVisualizer:
    """
    Create interactive Plotly visualizations for protein sequences
    
    Charts:
    1. Amino acid composition bar chart
    2. Secondary structure pie chart
    3. Charge distribution grouped bars
    4. Hydrophobicity sliding window plot
    5. Property gauges (stability, pI)
    6. Motif position visualization
    """
    
    def __init__(self, sequence, analysis_results):
        """
        Initialize visualizer
        
        Args:
            sequence (str): Protein sequence
            analysis_results (dict): Results from QuickSequenceAnalyzer
        """
        self.sequence = sequence
        self.analysis = analysis_results
    
    def create_amino_acid_composition_chart(self):
        """
        Create bar chart of amino acid composition
        
        Returns:
            str: Plotly JSON
        """
        composition = self.analysis['amino_acid_composition']['full_composition']
        
        # Sort by percentage
        sorted_aa = sorted(composition.items(), key=lambda x: x[1], reverse=True)
        amino_acids = [aa for aa, _ in sorted_aa]
        percentages = [pct for _, pct in sorted_aa]
        
        # Color by property
        colors = []
        for aa in amino_acids:
            if aa in 'RK':  # Positive
                colors.append('#3498db')
            elif aa in 'DE':  # Negative
                colors.append('#e74c3c')
            elif aa in 'FYWH':  # Aromatic
                colors.append('#9b59b6')
            elif aa in 'ILVM':  # Hydrophobic
                colors.append('#f39c12')
            elif aa in 'STNQ':  # Polar
                colors.append('#1abc9c')
            else:
                colors.append('#95a5a6')
        
        fig = go.Figure(data=[
            go.Bar(
                x=amino_acids,
                y=percentages,
                marker_color=colors,
                text=[f'{p:.1f}%' for p in percentages],
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>%{y:.2f}%<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title='Amino Acid Composition',
            xaxis_title='Amino Acid',
            yaxis_title='Percentage (%)',
            template='plotly_white',
            height=500,
            showlegend=False
        )
        
        return fig.to_json()
    
    def create_secondary_structure_chart(self):
        """
        Create pie chart of secondary structure prediction
        
        Returns:
            str: Plotly JSON
        """
        ss = self.analysis['secondary_structure']
        
        labels = ['Helix', 'Sheet', 'Turn']
        values = [
            ss['helix_percent'],
            ss['sheet_percent'],
            ss['turn_percent']
        ]
        colors = ['#e74c3c', '#3498db', '#f39c12']
        
        fig = go.Figure(data=[
            go.Pie(
                labels=labels,
                values=values,
                marker_colors=colors,
                hole=0.3,
                textinfo='label+percent',
                hovertemplate='<b>%{label}</b><br>%{value:.1f}%<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title='Secondary Structure Prediction',
            template='plotly_white',
            height=500
        )
        
        return fig.to_json()
    
    def create_charge_distribution_chart(self):
        """
        Create grouped bar chart of charge distribution
        
        Returns:
            str: Plotly JSON
        """
        charge = self.analysis['charge_distribution']
        
        categories = ['Positive<br>(R, K)', 'Negative<br>(D, E)', 'Neutral']
        counts = [
            charge['positive_residues'],
            charge['negative_residues'],
            charge['neutral_residues']
        ]
        percentages = [
            charge['positive_percent'],
            charge['negative_percent'],
            100 - charge['positive_percent'] - charge['negative_percent']
        ]
        colors = ['#3498db', '#e74c3c', '#95a5a6']
        
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Residue Count', 'Percentage'),
            specs=[[{'type': 'bar'}, {'type': 'bar'}]]
        )
        
        # Count bars
        fig.add_trace(
            go.Bar(
                x=categories,
                y=counts,
                marker_color=colors,
                text=counts,
                textposition='outside',
                name='Count',
                hovertemplate='<b>%{x}</b><br>Count: %{y}<extra></extra>'
            ),
            row=1, col=1
        )
        
        # Percentage bars
        fig.add_trace(
            go.Bar(
                x=categories,
                y=percentages,
                marker_color=colors,
                text=[f'{p:.1f}%' for p in percentages],
                textposition='outside',
                name='Percentage',
                hovertemplate='<b>%{x}</b><br>%{y:.1f}%<extra></extra>'
            ),
            row=1, col=2
        )
        
        fig.update_layout(
            title=f'Charge Distribution (Net charge at pH 7: {charge["net_charge_at_pH7"]:+.2f})',
            template='plotly_white',
            height=500,
            showlegend=False
        )
        
        fig.update_yaxes(title_text='Count', row=1, col=1)
        fig.update_yaxes(title_text='Percentage (%)', row=1, col=2)
        
        return fig.to_json()
    
    def create_hydrophobicity_plot(self):
        """
        Create line plot of hydrophobicity along sequence
        
        Returns:
            str: Plotly JSON
        """
        # Kyte-Doolittle scale
        kd_scale = {
            'A': 1.8, 'R': -4.5, 'N': -3.5, 'D': -3.5, 'C': 2.5,
            'Q': -3.5, 'E': -3.5, 'G': -0.4, 'H': -3.2, 'I': 4.5,
            'L': 3.8, 'K': -3.9, 'M': 1.9, 'F': 2.8, 'P': -1.6,
            'S': -0.8, 'T': -0.7, 'W': -0.9, 'Y': -1.3, 'V': 4.2
        }
        
        window_size = 7
        positions = []
        scores = []
        
        for i in range(len(self.sequence) - window_size + 1):
            window = self.sequence[i:i + window_size]
            score = sum([kd_scale.get(aa, 0) for aa in window]) / window_size
            positions.append(i + window_size // 2)
            scores.append(score)
        
        fig = go.Figure()
        
        # Main hydrophobicity line
        fig.add_trace(go.Scatter(
            x=positions,
            y=scores,
            mode='lines',
            name='Hydrophobicity',
            line=dict(color='#3498db', width=2),
            hovertemplate='Position: %{x}<br>Score: %{y:.2f}<extra></extra>'
        ))
        
        # Zero line
        fig.add_hline(y=0, line_dash='dash', line_color='gray', opacity=0.5)
        
        # Hydrophobic threshold
        fig.add_hline(
            y=1.5, 
            line_dash='dot', 
            line_color='red', 
            opacity=0.5,
            annotation_text='Hydrophobic threshold'
        )
        
        # Highlight hydrophobic regions
        hydrophobic_regions = self.analysis['hydrophobic_regions']
        for region in hydrophobic_regions:
            fig.add_vrect(
                x0=region['start'],
                x1=region['end'],
                fillcolor='yellow',
                opacity=0.2,
                layer='below',
                line_width=0
            )
        
        fig.update_layout(
            title=f'Hydrophobicity Plot (Kyte-Doolittle, window={window_size})',
            xaxis_title='Sequence Position',
            yaxis_title='Hydrophobicity Score',
            template='plotly_white',
            height=500
        )
        
        return fig.to_json()
    
    def create_property_gauges(self):
        """
        Create gauge charts for key properties
        
        Returns:
            str: Plotly JSON
        """
        props = self.analysis['basic_properties']
        
        # Stability gauge (instability index < 40 is stable)
        stability_score = 100 - min(props['instability_index'], 100)
        
        fig = make_subplots(
            rows=1, cols=2,
            specs=[[{'type': 'indicator'}, {'type': 'indicator'}]],
            subplot_titles=('Stability', 'Isoelectric Point')
        )
        
        # Stability gauge
        fig.add_trace(
            go.Indicator(
                mode='gauge+number',
                value=stability_score,
                title={'text': f'Stability<br><span style="font-size:0.8em">Index: {props["instability_index"]:.1f}</span>'},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': 'darkblue'},
                    'steps': [
                        {'range': [0, 40], 'color': '#e74c3c'},
                        {'range': [40, 70], 'color': '#f39c12'},
                        {'range': [70, 100], 'color': '#2ecc71'}
                    ],
                    'threshold': {
                        'line': {'color': 'red', 'width': 4},
                        'thickness': 0.75,
                        'value': 60
                    }
                }
            ),
            row=1, col=1
        )
        
        # pI gauge
        fig.add_trace(
            go.Indicator(
                mode='gauge+number',
                value=props['isoelectric_point'],
                title={'text': 'pI'},
                number={'suffix': ''},
                gauge={
                    'axis': {'range': [0, 14]},
                    'bar': {'color': 'darkgreen'},
                    'steps': [
                        {'range': [0, 3], 'color': '#e74c3c'},
                        {'range': [3, 6], 'color': '#f39c12'},
                        {'range': [6, 8], 'color': '#2ecc71'},
                        {'range': [8, 11], 'color': '#f39c12'},
                        {'range': [11, 14], 'color': '#3498db'}
                    ],
                    'threshold': {
                        'line': {'color': 'black', 'width': 4},
                        'thickness': 0.75,
                        'value': 7
                    }
                }
            ),
            row=1, col=2
        )
        
        fig.update_layout(
            template='plotly_white',
            height=400
        )
        
        return fig.to_json()
    
    def create_motif_position_chart(self):
        """
        Create visualization of motif positions on sequence
        
        Returns:
            str: Plotly JSON
        """
        motifs_data = self.analysis['rubisco_motifs']
        
        fig = go.Figure()
        
        # Sequence background
        fig.add_trace(go.Scatter(
            x=[0, len(self.sequence)],
            y=[0, 0],
            mode='lines',
            line=dict(color='lightgray', width=20),
            showlegend=False,
            hoverinfo='skip'
        ))
        
        colors = {
            'PS00157': '#e74c3c',
            'catalytic_lysine': '#3498db',
            'loop6': '#2ecc71'
        }
        
        y_offset = 0
        for motif_name, motif_info in motifs_data.items():
            if motif_info['found']:
                for match in motif_info['matches']:
                    # Add motif region
                    fig.add_trace(go.Scatter(
                        x=[match['start'], match['end']],
                        y=[y_offset, y_offset],
                        mode='lines+markers',
                        line=dict(color=colors.get(motif_name, '#95a5a6'), width=15),
                        marker=dict(size=10),
                        name=motif_name.replace('_', ' ').title(),
                        legendgroup=motif_name,
                        showlegend=(match == motif_info['matches'][0]),
                        hovertemplate=(
                            f'<b>{motif_name.replace("_", " ").title()}</b><br>'
                            f'Position: {match["start"]}-{match["end"]}<br>'
                            f'Sequence: {match["sequence"]}<extra></extra>'
                        )
                    ))
                y_offset += 0.5
        
        fig.update_layout(
            title='Motif Positions on Sequence',
            xaxis_title='Sequence Position',
            yaxis=dict(visible=False),
            template='plotly_white',
            height=400,
            showlegend=True,
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1
            )
        )
        
        fig.update_xaxes(range=[0, len(self.sequence)])
        
        return fig.to_json()
    
    def create_all_charts(self):
        """
        Create all visualization charts
        
        Returns:
            dict: All charts as Plotly JSON
        """
        return {
            'amino_acid_composition': self.create_amino_acid_composition_chart(),
            'secondary_structure': self.create_secondary_structure_chart(),
            'charge_distribution': self.create_charge_distribution_chart(),
            'hydrophobicity': self.create_hydrophobicity_plot(),
            'property_gauges': self.create_property_gauges(),
            'motif_positions': self.create_motif_position_chart()
        }


# Example usage
if __name__ == '__main__':
    from biopython_features import QuickSequenceAnalyzer
    
    # Test sequence
    test_sequence = "MSPQTETKASVGFKAGVKDYKLTYYTPEYETKDTDILAAFRVTPQPGVPPEEAGAAVAAESSTGTWTTVWTDGLTSLDRYKGRCYHIEPVAGEENQYICYVAYPLDLFEEGSVTNMFTSIVGNVFGFKALRALRLEDLRIPPAYTKTFQGPPHGIQVERDKLNKYGRPLLGCTIKPKLGLSAKNYGRAVYECLRGGLDFTKDDENVNSQPFMRWRDRFLFCAEAIYKAQAETGEIKGHYLNATAGTCEEMIKRAIFARELGVPIVR"
    
    # Analyze
    analyzer = QuickSequenceAnalyzer(test_sequence)
    analysis = analyzer.complete_analysis()
    
    # Create visualizations
    visualizer = SequenceVisualizer(test_sequence, analysis)
    charts = visualizer.create_all_charts()
    
    print("=== Plotly Visualizations Created ===")
    print(f"Number of charts: {len(charts)}")
    for chart_name in charts.keys():
        print(f"  - {chart_name}")
