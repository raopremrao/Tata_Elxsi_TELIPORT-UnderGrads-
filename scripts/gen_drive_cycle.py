"""Script to generate a deterministic synthetic urban two-wheeler drive cycle.

Generates a 30-minute (1800 s, 1 Hz) power profile simulating an electric scooter
commuting through urban Indian traffic with stops, cruising, and acceleration bursts.
"""

import numpy as np
import pandas as pd


def generate_drive_cycle(duration_s: int = 1800, seed: int = 42, output_csv: str = "data/drive_cycle_urban.csv") -> pd.DataFrame:
    np.random.seed(seed)
    time = np.arange(0, duration_s, dtype=int)
    power_W = np.zeros(duration_s, dtype=float)
    speed_kmh = np.zeros(duration_s, dtype=float)

    # Commute schedule: alternating between traffic stops, accelerations, cruising
    t = 0
    current_speed = 0.0

    while t < duration_s:
        mode = np.random.choice(["stop", "cruise", "accelerate", "burst"], p=[0.20, 0.45, 0.25, 0.10])
        block_len = int(np.random.randint(15, 60))
        t_end = min(t + block_len, duration_s)

        if mode == "stop":
            # Vehicle stopped at red light / junction
            power_W[t:t_end] = 20.0  # auxiliary load (lights, display)
            speed_kmh[t:t_end] = 0.0
            current_speed = 0.0

        elif mode == "cruise":
            # Steady city speed: 30 - 45 km/h, ~1200 - 2200 W
            target_speed = np.random.uniform(30.0, 45.0)
            target_power = 1500.0 + (target_speed - 30.0) * 50.0 + np.random.normal(0, 80, t_end - t)
            power_W[t:t_end] = np.clip(target_power, 800.0, 2600.0)
            speed_kmh[t:t_end] = target_speed
            current_speed = target_speed

        elif mode == "accelerate":
            # Normal acceleration: 2500 - 4200 W
            accel_power = np.linspace(current_speed * 40.0, 3800.0, t_end - t) + np.random.normal(0, 100, t_end - t)
            power_W[t:t_end] = np.clip(accel_power, 1000.0, 4500.0)
            current_speed = min(50.0, current_speed + 15.0)
            speed_kmh[t:t_end] = np.linspace(speed_kmh[max(0, t - 1)], current_speed, t_end - t)

        elif mode == "burst":
            # Overtaking / steep incline peak burst: up to 6000 W (for ~10-15s)
            burst_len = min(12, t_end - t)
            power_W[t:t + burst_len] = np.linspace(4500.0, 6000.0, burst_len)
            speed_kmh[t:t + burst_len] = np.linspace(current_speed, min(65.0, current_speed + 20.0), burst_len)
            current_speed = speed_kmh[t + burst_len - 1]
            if t + burst_len < t_end:
                power_W[t + burst_len:t_end] = 2200.0
                speed_kmh[t + burst_len:t_end] = current_speed

        t = t_end

    df = pd.DataFrame({
        "time_s": time,
        "power_W": np.round(power_W, 1),
        "speed_kmh": np.round(speed_kmh, 1),
        "is_synthetic": True,
    })

    df.to_csv(output_csv, index=False)
    print(f"Generated synthetic urban drive cycle ({duration_s} s) -> {output_csv}")
    print(f"Peak Power: {df['power_W'].max()} W, Mean Power: {df['power_W'].mean():.1f} W")
    return df


if __name__ == "__main__":
    generate_drive_cycle()

