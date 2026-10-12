"""Reproducible GA tuning using a documented synthetic design objective."""

import json
import os

import numpy as np
import pandas as pd

from fuzzy_controller import DEFAULT_PARAMS, fuzzy_controller, fuzzy_cooling


SEED = 42
POPULATION_SIZE = 24
GENERATIONS = 20
MUTATION_RATE = 0.25
SAMPLE_SIZE = 400


def repair(chromosome):
    """Keep thresholds and cooling consequents in valid ordered ranges."""
    x = np.asarray(chromosome, dtype=float).copy()

    x[:3] = np.sort(x[:3])
    x[0] = np.clip(x[0], 20, 27)
    x[1] = np.clip(x[1], x[0] + 2, 35)
    x[2] = np.clip(x[2], x[1] + 2, 43)

    x[3] = np.clip(x[3], 0, 35)
    x[4] = np.clip(x[4], x[3] + 10, 80)
    x[5] = np.clip(x[5], x[4] + 5, 100)

    return x


def as_params(chromosome):
    keys = ["t1", "t2", "t3", "cool_low", "cool_medium", "cool_high"]
    return dict(zip(keys, map(float, chromosome)))


def synthetic_target(row):
    """Heuristic reference demand; not measured HVAC data."""
    temperature = float(row.temperature_c)
    humidity = float(row.humidity_pct)
    occupancy = float(row.occupancy_count)

    if occupancy == 0:
        return 0.0

    demand = (
        3.0 * (temperature - 18)
        + 0.15 * occupancy
        + 0.15 * max(0.0, humidity - 60)
    )
    return float(np.clip(demand, 0, 100))


def fitness(chromosome, rows, targets):
    params = as_params(chromosome)
    predictions = []

    for row in rows.itertuples(index=False):
        if row.occupancy_count == 0:
            prediction = 0.0
        else:
            prediction = fuzzy_cooling(
                row.temperature_c,
                row.humidity_pct,
                row.occupancy_count,
                params,
            )
        predictions.append(prediction)

    predictions = np.asarray(predictions)
    rmse = float(np.sqrt(np.mean((predictions - targets) ** 2)))

    # Small synthetic penalty for cooling demand during high-tariff scenarios.
    high_tariff = rows["tariff_level"].to_numpy() == "high"
    tariff_penalty = (
        0.05 * float(predictions[high_tariff].mean())
        if high_tariff.any()
        else 0.0
    )

    return rmse + tariff_penalty


def random_chromosome(rng):
    return repair([
        rng.uniform(20, 27),
        rng.uniform(27, 35),
        rng.uniform(35, 43),
        rng.uniform(0, 30),
        rng.uniform(40, 75),
        rng.uniform(75, 100),
    ])


def tournament(population, scores, rng, size=3):
    candidates = rng.choice(len(population), size=size, replace=False)
    winner = min(candidates, key=lambda i: scores[i])
    return population[winner].copy()


def mutate(child, rng):
    ranges = np.array([3, 4, 4, 12, 15, 12], dtype=float)
    for i in range(len(child)):
        if rng.random() < MUTATION_RATE:
            child[i] += rng.normal(0, ranges[i] * 0.2)
    return repair(child)


def main():
    rng = np.random.default_rng(SEED)

    data_path = "data/processed/cleaned_input.csv"
    if not os.path.isfile(data_path):
        data_path = "data/sample_input.csv"

    data = pd.read_csv(data_path)
    sample = data.sample(
        n=min(SAMPLE_SIZE, len(data)),
        random_state=SEED,
    ).reset_index(drop=True)

    targets = np.array([synthetic_target(row) for row in sample.itertuples(index=False)])

    population = [random_chromosome(rng) for _ in range(POPULATION_SIZE)]
    history = []
    best = None
    best_score = float("inf")

    for generation in range(GENERATIONS):
        scores = [fitness(ind, sample, targets) for ind in population]
        order = np.argsort(scores)

        if scores[order[0]] < best_score:
            best_score = scores[order[0]]
            best = population[order[0]].copy()

        history.append({
            "generation": generation + 1,
            "best_fitness": float(scores[order[0]]),
            "generation_mean_fitness": float(np.mean(scores)),
            "best_so_far_fitness": best_score,
        })

        # Elitism preserves the best candidate found so far.
        next_population = [population[order[0]].copy()]

        while len(next_population) < POPULATION_SIZE:
            parent_a = tournament(population, scores, rng)
            parent_b = tournament(population, scores, rng)
            mask = rng.random(len(parent_a)) < 0.5
            child = np.where(mask, parent_a, parent_b)
            next_population.append(mutate(child, rng))

        population = next_population

    params = as_params(best)
    os.makedirs("results/step6", exist_ok=True)

    with open("results/step6/ga_best_params.json", "w") as file:
        json.dump({
            "seed": SEED,
            "population_size": POPULATION_SIZE,
            "generations": GENERATIONS,
            "sample_size": len(sample),
            "fitness_definition": (
                "RMSE against a synthetic temperature/occupancy/humidity "
                "cooling-demand heuristic plus a 0.05 mean-cooling penalty "
                "for high-tariff scenarios. Not measured energy savings."
            ),
            "best_fitness": best_score,
            "parameters": params,
        }, file, indent=2)

    pd.DataFrame(history).to_csv(
        "results/step6/ga_fitness_history.csv", index=False
    )

    output_data = pd.read_csv(data_path)
    ga_results = output_data.apply(
        lambda row: fuzzy_controller(row, params=params), axis=1
    )
    pd.concat([output_data, ga_results], axis=1).to_csv(
        "results/step6/ga_fuzzy_results.csv", index=False
    )

    print("GA tuning completed.")
    print(f"Training scenarios: {len(sample)}")
    print(f"Best fitness: {best_score:.4f}")
    print(f"Best parameters: {params}")
    print("Saved: results/step6/ga_best_params.json")
    print("Saved: results/step6/ga_fitness_history.csv")
    print("Saved: results/step6/ga_fuzzy_results.csv")


if __name__ == "__main__":
    main()
