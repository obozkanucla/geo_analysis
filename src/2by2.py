import matplotlib.pyplot as plt

# Create figure
fig, ax = plt.subplots(figsize=(8,6))

# Axes setup
ax.axhline(0.5, color='grey', linewidth=1)
ax.axvline(0.5, color='grey', linewidth=1)

ax.set_xlim(0,1)
ax.set_ylim(0,1)

# Labels for axes
ax.set_xlabel("Episodic  →  Continuous", fontsize=12, labelpad=10)
ax.set_ylabel("Clinical  →  Household", fontsize=12, labelpad=10)

# Quadrant annotations
ax.text(0.25, 0.95, "Clinical + Episodic\n(Post-discharge, chronic)", ha='center', va='top', fontsize=10, color='dimgray')
ax.text(0.75, 0.95, "Clinical + Continuous\n(Hospital-at-home, RPM)", ha='center', va='top', fontsize=10, color='dimgray')
ax.text(0.25, 0.05, "Household + Episodic\n(Panic buttons, check-ins)", ha='center', va='bottom', fontsize=10, color='dimgray')
ax.text(0.75, 0.05, "Household + Continuous\n(Ambient IoTH + AI)", ha='center', va='bottom', fontsize=10, color='dimgray')

# Plot Doccla
ax.scatter(0.25, 0.75, s=200, c='royalblue', label='Doccla')
ax.text(0.25, 0.78, "Doccla", ha='center', fontsize=11, weight='bold', color='royalblue')

# Plot SAB Care Vision
ax.scatter(0.75, 0.25, s=200, c='darkorange', label='SAB Care Vision')
ax.text(0.75, 0.28, "SAB Care Vision", ha='center', fontsize=11, weight='bold', color='darkorange')

# Style
ax.set_xticks([])
ax.set_yticks([])
ax.set_title("Positioning Map: Doccla vs SAB Care", fontsize=14, weight='bold')

plt.show()