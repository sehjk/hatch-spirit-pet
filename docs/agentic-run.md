# Agentic Runs And Sub-Agents

`prepare_pet_run.py` does not create a finished pet. It creates a run folder with prompts, layout guides, `pet_request.json`, and `imagegen-jobs.json`.

Sub-agents are only available inside Codex. A plain Python process cannot spawn Codex sub-agents, call the built-in `$imagegen` skill, or record built-in image outputs from the conversation runtime.

## Responsibility Split

The parent Codex agent owns:

- reading the prepared run manifest
- generating and recording the base pet
- deciding whether `running-left` can be mirrored
- recording selected generated images into `decoded/`
- running repairs, finalization, atlas validation, previews, and packaging

Sub-agents may only:

- generate assigned row-strip images
- use the row prompt plus required reference images
- return the selected original `$CODEX_HOME/generated_images/.../ig_*.png` path
- include a short QA note

Sub-agents must not edit the manifest, write `decoded/`, finalize, package, repair, or mirror rows.

## Prompt To Run

After preparing a run, paste this into Codex:

```text
Use hatch-spirit-pet to finish this run with sub-agents: /absolute/path/to/run
```

For repair:

```text
Repair failed rows and finalize this pet: /absolute/path/to/run
```
