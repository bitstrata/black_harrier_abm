from scipy.stats import beta
import numpy as np
import random

# Bayesian Update for Collision Probability
def bayesian_update_collision_prob(prior_prob, gps_data, turbines):
    near_turbine = 0
    collisions = 0
    for _, row in gps_data.iterrows():
        if row['alt'] >= BSA_HEIGHT[0] and row['alt'] <= BSA_HEIGHT[1]:
            for _, t in turbines.iterrows():
                if Point(row['lon'], row['lat']).within(t['collision_zone']):
                    near_turbine += 1
                    collisions += 1 if random.random() < prior_prob else 0
    a, b = 14, 86
    a += collisions
    b += near_turbine - collisions
    posterior_prob = a / (a + b)
    return posterior_prob