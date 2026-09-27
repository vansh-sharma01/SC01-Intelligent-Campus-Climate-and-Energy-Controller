import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

fig, ax = plt.subplots(figsize=(16, 9))

ax.set_xlim(0, 16)
ax.set_ylim(0, 9)
ax.axis("off")


# ============================================================
# TITLE
# ============================================================

ax.text(
    8, 8.5,
    "SC01 – Intelligent Campus Climate & Energy Controller",
    ha="center",
    va="center",
    fontsize=20,
    fontweight="bold"
)

ax.text(
    8, 8.05,
    "Product V1 Screen Sketch",
    ha="center",
    va="center",
    fontsize=12
)


# ============================================================
# INPUT PANEL
# ============================================================

ax.add_patch(Rectangle((0.5, 4.3), 4.5, 3.3, fill=False, linewidth=2))

ax.text(
    2.75, 7.25,
    "INPUTS",
    ha="center",
    va="center",
    fontsize=15,
    fontweight="bold"
)

ax.text(0.9, 6.75, "Temperature (°C):   24",
        ha="left", va="center", fontsize=10.5)

ax.text(0.9, 6.30, "Humidity (%):       50",
        ha="left", va="center", fontsize=10.5)

ax.text(0.9, 5.85, "Occupancy:           20",
        ha="left", va="center", fontsize=10.5)

ax.text(0.9, 5.40, "Tariff:              LOW",
        ha="left", va="center", fontsize=10.5)

# Separate button
ax.add_patch(Rectangle(
    (1.15, 4.55),
    3.2,
    0.42,
    fill=False,
    linewidth=2
))

ax.text(
    2.75, 4.76,
    "RUN RECOMMENDATION",
    ha="center",
    va="center",
    fontsize=9,
    fontweight="bold"
)


# ============================================================
# OUTPUT PANEL
# ============================================================

ax.add_patch(Rectangle((5.5, 4.3), 4.5, 3.3, fill=False, linewidth=2))

ax.text(
    7.75, 7.25,
    "OUTPUTS",
    ha="center",
    va="center",
    fontsize=15,
    fontweight="bold"
)

ax.text(5.9, 6.75, "Cooling:          50%",
        ha="left", va="center", fontsize=10.5)

ax.text(5.9, 6.30, "Fan level:        MEDIUM",
        ha="left", va="center", fontsize=10.5)

ax.text(5.9, 5.85, "Energy action:    NORMAL",
        ha="left", va="center", fontsize=10.5)

ax.text(5.9, 5.40, "Baseline result:  READY",
        ha="left", va="center", fontsize=10.5)

ax.text(5.9, 4.90, "Explanation:",
        ha="left", va="center", fontsize=9.5, fontweight="bold")

ax.text(5.9, 4.58, "Temperature is moderate.",
        ha="left", va="center", fontsize=9)


# ============================================================
# ANALYSIS PANEL
# ============================================================

ax.add_patch(Rectangle((10.5, 4.3), 5.0, 3.3, fill=False, linewidth=2))

ax.text(
    13.0, 7.25,
    "ANALYSIS",
    ha="center",
    va="center",
    fontsize=15,
    fontweight="bold"
)

# Temperature
ax.text(10.85, 6.55, "Temperature",
        ha="left", va="center", fontsize=9.5)

ax.add_patch(Rectangle(
    (12.3, 6.43), 2.5, 0.24,
    fill=False, linewidth=1
))

ax.add_patch(Rectangle(
    (12.3, 6.43), 1.25, 0.24,
    fill=False, linewidth=1
))

# Humidity
ax.text(10.85, 5.85, "Humidity",
        ha="left", va="center", fontsize=9.5)

ax.add_patch(Rectangle(
    (12.3, 5.73), 2.5, 0.24,
    fill=False, linewidth=1
))

ax.add_patch(Rectangle(
    (12.3, 5.73), 1.25, 0.24,
    fill=False, linewidth=1
))

# Occupancy
ax.text(10.85, 5.15, "Occupancy",
        ha="left", va="center", fontsize=9.5)

ax.add_patch(Rectangle(
    (12.3, 5.03), 2.5, 0.24,
    fill=False, linewidth=1
))

ax.add_patch(Rectangle(
    (12.3, 5.03), 1.0, 0.24,
    fill=False, linewidth=1
))


# ============================================================
# VALIDATION PANEL
# ============================================================

ax.add_patch(Rectangle((0.5, 0.9), 4.5, 2.9, fill=False, linewidth=2))

ax.text(
    2.75, 3.45,
    "VALIDATION",
    ha="center",
    va="center",
    fontsize=14,
    fontweight="bold"
)

ax.text(0.9, 2.90, "✓ Required fields present",
        ha="left", va="center", fontsize=10)

ax.text(0.9, 2.45, "✓ Values within valid ranges",
        ha="left", va="center", fontsize=10)

ax.text(0.9, 1.90, "Error message area:",
        ha="left", va="center", fontsize=10)

ax.text(0.9, 1.50, "Invalid input shown here",
        ha="left", va="center", fontsize=9.5)


# ============================================================
# CONTROLLER MODE PANEL
# ============================================================

ax.add_patch(Rectangle((5.5, 0.9), 4.5, 2.9, fill=False, linewidth=2))

ax.text(
    7.75, 3.45,
    "CONTROLLER MODE",
    ha="center",
    va="center",
    fontsize=14,
    fontweight="bold"
)

ax.text(
    7.75, 2.85,
    "CURRENT",
    ha="center",
    va="center",
    fontsize=10,
    fontweight="bold"
)

ax.text(
    7.75, 2.45,
    "Baseline Rules",
    ha="center",
    va="center",
    fontsize=10
)

ax.text(
    7.75, 1.95,
    "FUTURE",
    ha="center",
    va="center",
    fontsize=10,
    fontweight="bold"
)

ax.text(
    7.75, 1.55,
    "Soft Computing Controller",
    ha="center",
    va="center",
    fontsize=10
)

ax.text(
    7.75, 1.20,
    "Comparison results",
    ha="center",
    va="center",
    fontsize=9
)


# ============================================================
# SYSTEM STATUS PANEL
# ============================================================

ax.add_patch(Rectangle((10.5, 0.9), 5.0, 2.9, fill=False, linewidth=2))

ax.text(
    13.0, 3.45,
    "SYSTEM STATUS",
    ha="center",
    va="center",
    fontsize=14,
    fontweight="bold"
)

ax.text(
    13.0, 2.85,
    "STATUS: READY",
    ha="center",
    va="center",
    fontsize=10.5,
    fontweight="bold"
)

ax.text(
    13.0, 2.35,
    "Scenario: SC01-001",
    ha="center",
    va="center",
    fontsize=10
)

ax.text(
    13.0, 1.80,
    "Next: Compare with",
    ha="center",
    va="center",
    fontsize=9.5
)

ax.text(
    13.0, 1.45,
    "Soft Computing",
    ha="center",
    va="center",
    fontsize=9.5
)


# ============================================================
# SAVE
# ============================================================

plt.savefig(
    "docs/product-v1-sketch.png",
    dpi=200,
    bbox_inches="tight"
)

plt.close()

print("Product V1 sketch created successfully:")
print("docs/product-v1-sketch.png")
