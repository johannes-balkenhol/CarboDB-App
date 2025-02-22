from dna_features_viewer import GraphicFeature, GraphicRecord
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec



def plot_hmmer_results(hits, sequences, save_file_location, image_name="/test.png"):
    # Dynamically set figure height based on the number of hits
    fig_height = max(6, len(hits) * 1.5)  # 1.5 inches per hit, minimum height of 6 inches
    fig = plt.figure(figsize=(12, fig_height))

    # Use GridSpec for better control over subplot spacing
    gs = GridSpec(len(hits), 1, figure=fig, hspace=0.5)  # hspace controls vertical space between plots

    # create an index to retrieve sequences by name
    seq_index = {seq.name: seq for seq in sequences}

    for i, hit in enumerate(hits):
        ax = fig.add_subplot(gs[i])

        # add one feature per domain, with unique colors and labels
        features = [
            GraphicFeature(
                start=d.alignment.target_from - 1,
                end=d.alignment.target_to,
                color="#ffcccc" if j % 2 == 0 else "#ccffcc",  # alternate colors for visibility
                label=f"Domain {j + 1}"
            )
            for j, d in enumerate(hit.domains)
        ]
        length = len(seq_index[hit.name])
        desc = seq_index[hit.name].name.decode()

        # render the feature records with appropriate length
        record = GraphicRecord(sequence_length=length, features=features)
        record.plot(ax=ax)

        # Set a descriptive title for each subplot
        ax.set_title(f"{desc} | E-value: {hit.evalue:.2e}", fontsize=10)

    # Improve layout
    fig.tight_layout(pad=2.0)  # increase padding for better readability

    # Show the final figure
    plt.savefig(save_file_location+image_name)