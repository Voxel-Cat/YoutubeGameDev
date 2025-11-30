import json
import hashlib
import os
from typing import Dict, List

CHUNKS_DIR = "chunks"
CHUNK_WIDTH = 800
CHUNK_HEIGHT = 600
PLATFORM_HEIGHT = 20

os.makedirs(CHUNKS_DIR, exist_ok=True)


def hash_noise(x: int, y: int, seed: int = 0) -> float:
    """Deterministic noise using hash."""
    value = hashlib.md5(f"{x}_{y}_{seed}".encode()).hexdigest()
    return int(value[:8], 16) / 0xffffffff


def get_chunk_filename(chunk_x: int, chunk_y: int) -> str:
    """Get chunk file path."""
    return os.path.join(CHUNKS_DIR, f"terrain_{chunk_x}_{chunk_y}.json")


def generate_chunk(chunk_x: int, chunk_y: int) -> Dict:
    """Generate a screen-sized terrain chunk."""
    platforms = []
    world_x = chunk_x * CHUNK_WIDTH
    world_y = chunk_y * CHUNK_HEIGHT

    # Ground platform - always at bottom
    platforms.append({
        "x": world_x,
        "y": world_y + CHUNK_HEIGHT - PLATFORM_HEIGHT,
        "width": CHUNK_WIDTH,
        "height": PLATFORM_HEIGHT,
        "type": "ground"
    })

    # Generate floating platforms using noise
    grid_size = 100
    for gx in range(0, CHUNK_WIDTH, grid_size):
        for gy in range(50, CHUNK_HEIGHT - 100, grid_size):
            noise_val = hash_noise(chunk_x * 10 + gx // grid_size, chunk_y * 10 + gy // grid_size)

            if noise_val > 0.5:
                x_offset = int((noise_val - 0.5) * 80)
                platform_x = world_x + gx + x_offset
                platform_y = world_y + gy

                # Make sure platform is within bounds
                if 0 <= platform_x < world_x + CHUNK_WIDTH - 60:
                    platforms.append({
                        "x": platform_x,
                        "y": platform_y,
                        "width": 120,
                        "height": PLATFORM_HEIGHT,
                        "type": "platform"
                    })

    return {
        "chunk_x": chunk_x,
        "chunk_y": chunk_y,
        "width": CHUNK_WIDTH,
        "height": CHUNK_HEIGHT,
        "platforms": platforms
    }


def load_or_generate_chunk(chunk_x: int, chunk_y: int) -> Dict:
    """Load chunk from file or generate it."""
    filename = get_chunk_filename(chunk_x, chunk_y)

    if os.path.exists(filename):
        try:
            with open(filename, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to load chunk {chunk_x},{chunk_y}: {e}")

    chunk = generate_chunk(chunk_x, chunk_y)
    save_chunk(chunk)
    print(f"[TERRAIN] Generated chunk {chunk_x},{chunk_y}")
    return chunk


def save_chunk(chunk: Dict) -> None:
    """Save chunk to file."""
    filename = get_chunk_filename(chunk["chunk_x"], chunk["chunk_y"])
    try:
        with open(filename, "w") as f:
            json.dump(chunk, f, indent=2)
    except Exception as e:
        print(f"[ERROR] Failed to save chunk: {e}")
