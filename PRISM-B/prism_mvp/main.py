import os
import sys
import json
import subprocess

print("🤖 Generating Advanced Neural Network Lesson Suite...")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# 1. Define the Scenario
scene_data = {
    "title": "Deep Learning Logic",
    "layer_sizes": [3, 5, 5, 2], # Deeper network
    "inputs": [1.0, 0.2, 0.5],
    "expected_output": [1.0, 0.0]
}

# 2. Save Data
data_path = os.path.join(PROJECT_ROOT, "data.json")
with open(data_path, "w") as f:
    json.dump(scene_data, f, indent=4)

# 3. Render helper
env = os.environ.copy()
existing_pythonpath = env.get("PYTHONPATH", "")
pythonpath_entries = [SCRIPT_DIR, PROJECT_ROOT, existing_pythonpath]
env["PYTHONPATH"] = os.pathsep.join(filter(None, pythonpath_entries))


def render_scene(template_file: str, scene_name: str, label: str) -> None:
    print(f"🎬 Rendering {label} ...")
    cmd = [
        sys.executable,
        "-m",
        "manim",
        "-pql",
        os.path.join(SCRIPT_DIR, "templates", template_file),
        scene_name,
    ]
    subprocess.run(cmd, check=True, env=env)


scenes = [
    ("concept_scene.py", "ConceptScene", "Concept Scene"),
    ("neural_showcase.py", "NeuralShowcase", "Neural Showcase Test"),
    ("interactive_neural.py", "PrismInteractiveNeuralScene", "Interactive Neural Demo"),
]

try:
    for template_file, scene_name, label in scenes:
        render_scene(template_file, scene_name, label)
    print("\n🎉 Videos ready!")
    print("   • media/videos/concept_scene/480p15/ConceptScene.mp4")
    print("   • media/videos/neural_showcase/480p15/NeuralShowcase.mp4")
    print("   • media/videos/interactive_neural/480p15/PrismInteractiveNeuralScene.mp4")
except subprocess.CalledProcessError as exc:
    print(f"❌ Error while rendering {exc}")