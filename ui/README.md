# Hatch Spirit Pet Preset Builder

Open `ui/index.html` in a browser to build a `prepare_pet_run.py` command.

The UI is static. It does not run scripts, call `$imagegen`, write files, or package pets.

## Use

1. Enter the pet name, description, concept notes, and output directory.
2. Pick an art style and action style.
3. Edit any row action that should differ from the selected action preset.
4. Copy the generated command.
5. Run it from the `hatch-spirit-pet` repo root or adapt the script path for an installed skill.

The generated command prepares the run folder, prompt files, layout guides, `pet_request.json`, and `imagegen-jobs.json`.
