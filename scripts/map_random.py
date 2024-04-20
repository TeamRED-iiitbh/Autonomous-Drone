import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

# Define the dimensions of the blank plane
plane_width = 50  # Width of the plane
plane_height = 50  # Height of the plane

# Define the number of random values you want to print
num_values = 15

# Generate random coordinates within the plane
x_values = np.random.uniform(0, plane_width, num_values)
y_values = np.random.uniform(0, plane_height, num_values)

# Calculate mean values
x_mean = x_values.mean()
y_mean = y_values.mean()

# Initialize variables to store the last highest x and y values
last_highest_x = 0
last_highest_y = 0

# Initialize variable to store the last highest result
last_highest_result = 0

# Create a scatter plot
plt.figure(figsize=(8, 6))
plt.scatter(x_values, y_values, c='blue', cmap='viridis', s=100, alpha=0.7)

# Plot the mean values
plt.scatter(x_mean, y_mean, c='red', marker='x', s=200, label='Mean')

previous_result = 0

for x, y in zip(x_values, y_values):
    dist = ((abs(x - x_mean)) ** 2 + (abs(y - y_mean)) ** 2) ** 0.5

    if dist > previous_result:
        last_highest_x = x
        last_highest_y = y
        last_highest_result = dist
        
    previous_result = dist

# Draw a circle around the mean point
radius = 1.5 * last_highest_result
circle = Circle((x_mean, y_mean), radius, color='green', fill=False)
plt.gca().add_patch(circle)

# Add color bar and labels
plt.colorbar(label='Color')
plt.xlabel('X')
plt.ylabel('Y')

# Add legend
plt.legend()

# Show the plot
plt.grid(True)
plt.gca().set_aspect('equal', adjustable='box')
plt.show()