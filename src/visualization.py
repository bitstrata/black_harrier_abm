import solara
import matplotlib.pyplot as plt

@solara.component
def HarrierVisualization(model):
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_xlim(0, GRID_SIZE)
    ax.set_ylim(0, GRID_SIZE)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(f"Black Harrier Simulation (Month {model.month})")
   
    # Plot harriers
    for agent in model.agents:
        if agent.alive:
            color = 'green' if agent.breeding else 'blue'
            ax.scatter(agent.pos[0], agent.pos[1], c=color, s=50, label='Harrier (Breeding)' if agent.breeding else 'Harrier (Non-breeding)')
   
    # Plot turbines
    for tx, ty in model.turbines:
        ax.scatter(tx, ty, c='red', marker='^', s=100, label='Turbine')
   
    # Plot nests and roosts
    for nx, ny in model.nests:
        ax.scatter(nx, ny, c='yellow', marker='s', s=100, label='Nest')
    for rx, ry in model.communal_roosts:
        ax.scatter(rx, ry, c='purple', marker='o', s=100, label='Communal Roost')
    for rx, ry in model.single_roosts:
        ax.scatter(rx, ry, c='cyan', marker='o', s=50, label='Single Roost')
   
    # Add legend (avoid duplicates)
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), loc='upper right')
   
    plt.tight_layout()
    return solara.FigureMatplotlib(fig)