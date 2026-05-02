const rows = [
  ["idle", 6],
  ["running-right", 8],
  ["running-left", 8],
  ["waving", 4],
  ["jumping", 5],
  ["failed", 8],
  ["waiting", 6],
  ["running", 6],
  ["review", 6],
];

const artStyles = {
  "pixel-art": {
    label: "Pixel Art",
    hint: "Crisp stepped edges, limited palette, chunky readable sprite forms.",
  },
  "stylized-3d": {
    label: "Stylized 3D Cartoon",
    hint: "Rounded toy-like avatar cues translated into a flat sprite strip.",
  },
  "soft-clay": {
    label: "Soft Clay Avatar",
    hint: "Matte rounded clay-like forms without studio lighting or floor shadows.",
  },
  anime: {
    label: "Anime Sprite",
    hint: "Expressive anime-inspired compact sprite, not cinematic key art.",
  },
  custom: {
    label: "Custom",
    hint: "Use style notes while preserving Codex sprite constraints.",
  },
};

const actionStyles = {
  fighter: {
    label: "Fighter Moves",
    states: {
      idle: "combat stance breathing loop with guard up and small weight shifts",
      "running-right": "rightward fighting-game dash loop",
      "running-left": "leftward fighting-game dash loop",
      waving: "taunt or stance flourish with gesture and return",
      jumping: "fighting leap with anticipation, lift, aerial peak, descent, settle",
      failed: "hit-stun, KO, or defeated reaction",
      waiting: "charge-up or power idle loop",
      running: "forward rush or in-place attack run loop",
      review: "special power or finisher loop",
    },
  },
  superhero: {
    label: "Superhero Moves",
    states: {
      idle: "heroic ready stance, cape/cloth lift, chest emblem or motif subtly pulsing",
      "running-right": "rightward heroic sprint, flight glide, or power-assisted dash",
      "running-left": "leftward heroic sprint, flight glide, or power-assisted dash",
      waving: "hero greeting, salute, confident point, or cape flourish",
      jumping: "hero takeoff, hover, leap, or landing-ready aerial pose",
      failed: "hero stagger, cape droop, dimmed emblem, or kneeling recovery",
      waiting: "power-up anticipation with contained energy around body, hands, emblem, or prop",
      running: "urgent rescue rush, patrol loop, or forward charge",
      review: "signature heroic power pose, contained burst, emblem glow, or victory reveal",
    },
  },
  cozy: {
    label: "Cozy Companion",
    states: {
      idle: "calm breathing, blink, sway, tiny bounce, or sleepy hover",
      "running-right": "rightward toddle, scamper, float, roll, or gentle glide",
      "running-left": "leftward toddle, scamper, float, roll, or gentle glide",
      waving: "friendly wave, shy hello, small bow, sparkle-free charm, or happy wiggle",
      jumping: "small hop, buoyant bob, excited pop-up, or floaty lift",
      failed: "sad slump, sleepy droop, startled blink, wilt, or tiny wobble",
      waiting: "listening, thinking, idle fidget, warm pulse, or patient attention loop",
      running: "busy little work loop, eager hurry, or in-place trot",
      review: "happy celebration, delighted glow, bow, tiny spin, or proud reveal",
    },
  },
  ghostly: {
    label: "Ghostly Motion",
    states: {
      idle: "slow hover, sheet/body sway, blink, wisp pulse, or gentle bob",
      "running-right": "rightward drift, glide, phase-like float, or bobbing travel",
      "running-left": "leftward drift, glide, phase-like float, or bobbing travel",
      waving: "spectral greeting, shy peek, swirl-in-place, or playful haunting gesture",
      jumping: "buoyant rise, pop-up float, vanish-and-return pose beat, or airy lift",
      failed: "faded slump, startled poof, dimmed face, or drooping wisp reaction",
      waiting: "quiet hovering attention, contained mist pulse, or listening loop",
      running: "eager haunt patrol, quick float loop, or in-place drifting motion",
      review: "spooky reveal, contained wisp flare, moonlit charm, or playful spectral flourish",
    },
  },
  magical: {
    label: "Magical Spirit",
    states: {
      idle: "mystic idle, breathing, blink, wand/prop hum, or motif shimmer",
      "running-right": "rightward enchanted glide, scamper, dash, or charm-assisted travel",
      "running-left": "leftward enchanted glide, scamper, dash, or charm-assisted travel",
      waving: "spell gesture, charm flourish, wand/hand motion, or ritual greeting",
      jumping: "levitation hop, magic lift, transformation beat, or aerial spell-ready pose",
      failed: "spell fizzles, startled recoil, dimmed aura, or tired slump",
      waiting: "spell charge, quiet ritual, listening to magic, or contained aura loop",
      running: "urgent spellcasting loop, active ritual motion, or pursuit with attached magic",
      review: "signature spell reveal, transformation, contained aura bloom, or magical celebration",
    },
  },
  utility: {
    label: "Utility / Work Loop",
    states: {
      idle: "focused idle, blink, tool-ready stance, screen/face pulse, or attentive breathing",
      "running-right": "rightward purposeful travel, roll, hover, walk, or task dash",
      "running-left": "leftward purposeful travel, roll, hover, walk, or task dash",
      waving: "acknowledgement gesture, ready signal, tool flourish, or friendly check-in",
      jumping: "quick hop, tool reach, pop-up notification beat, or active reposition",
      failed: "error wobble, tired slump, dimmed display, tool drop, or confused blink",
      waiting: "thinking, scanning, loading, listening, charging, or standby loop",
      running: "busy work loop, typing/tooling motion, patrol, or focused task cycle",
      review: "task complete flourish, check-ready reveal, success pulse, or proud presentation",
    },
  },
  custom: {
    label: "Custom Actions",
    states: {
      idle: "signature idle loop with breathing, hover, pulse, blink, or weight shift",
      "running-right": "rightward travel loop: glide, scamper, dash, float, roll, or stride",
      "running-left": "leftward travel loop: glide, scamper, dash, float, roll, or stride",
      waving: "greeting, charm, flourish, ritual gesture, taunt, or stance change",
      jumping: "hop, float, leap, pop-up, aerial pose, or transformation beat",
      failed: "startled, sad, tired, dispelled, knocked-back, or defeated reaction",
      waiting: "anticipation, charge, listening, thinking, ambient power, or quiet readiness loop",
      running: "active work loop, hurry, patrol, pursuit, forward rush, or in-place motion loop",
      review: "special moment, reveal, spell, flourish, celebration, finisher, or power loop",
    },
  },
};

const $ = (id) => document.getElementById(id);

function shellQuote(value) {
  if (!value) return "''";
  return `'${value.replaceAll("'", `'\\''`)}'`;
}

function populateSelect(select, presets) {
  Object.entries(presets).forEach(([value, preset]) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = preset.label;
    select.append(option);
  });
}

function createStateControls() {
  const grid = $("state-grid");
  rows.forEach(([state]) => {
    const label = document.createElement("label");
    label.htmlFor = `state-${state}`;
    label.textContent = state;
    const input = document.createElement("textarea");
    input.id = `state-${state}`;
    input.name = state;
    input.rows = 2;
    label.append(input);
    grid.append(label);
  });
}

function setPresetActions() {
  const selected = $("action-style").value;
  const actions = actionStyles[selected].states;
  rows.forEach(([state]) => {
    $(`state-${state}`).value = actions[state];
  });
  render();
}

function buildCommand() {
  const args = [
    "python scripts/prepare_pet_run.py",
    "--pet-name",
    shellQuote($("pet-name").value.trim()),
    "--description",
    shellQuote($("description").value.trim()),
    "--pet-notes",
    shellQuote($("pet-notes").value.trim()),
    "--art-style",
    shellQuote($("art-style").value),
    "--action-style",
    shellQuote($("action-style").value),
  ];

  const styleNotes = $("style-notes").value.trim();
  const actionNotes = $("action-notes").value.trim();
  const outputDir = $("output-dir").value.trim();
  if (styleNotes) args.push("--style-notes", shellQuote(styleNotes));
  if (actionNotes) args.push("--action-notes", shellQuote(actionNotes));

  const presetActions = actionStyles[$("action-style").value].states;
  rows.forEach(([state]) => {
    const value = $(`state-${state}`).value.trim();
    if (value && value !== presetActions[state]) {
      args.push("--state-action", shellQuote(`${state}=${value}`));
    }
  });

  if (outputDir) args.push("--output-dir", shellQuote(outputDir));
  args.push("--force");

  const lines = [args[0]];
  for (let index = 1; index < args.length; index += 2) {
    const flag = args[index];
    const value = args[index + 1];
    lines.push(value ? `  ${flag} ${value}` : `  ${flag}`);
  }
  return lines.join(" \\\n");
}

function renderSummary() {
  const summary = $("summary");
  summary.innerHTML = "";
  const items = [
    ["Pet", $("pet-name").value.trim() || "Untitled"],
    ["Art", artStyles[$("art-style").value].label],
    ["Action", actionStyles[$("action-style").value].label],
    ["Output", $("output-dir").value.trim() || "default timestamped folder"],
  ];
  items.forEach(([key, value]) => {
    const dt = document.createElement("dt");
    const dd = document.createElement("dd");
    dt.textContent = key;
    dd.textContent = value;
    summary.append(dt, dd);
  });
}

function renderRows() {
  const tbody = $("row-preview");
  tbody.innerHTML = "";
  rows.forEach(([state, frames]) => {
    const tr = document.createElement("tr");
    const stateCell = document.createElement("td");
    const frameCell = document.createElement("td");
    const actionCell = document.createElement("td");
    stateCell.textContent = state;
    frameCell.textContent = frames;
    actionCell.textContent = $(`state-${state}`).value.trim();
    tr.append(stateCell, frameCell, actionCell);
    tbody.append(tr);
  });
}

function render() {
  $("command-output").textContent = buildCommand();
  renderSummary();
  renderRows();
}

populateSelect($("art-style"), artStyles);
populateSelect($("action-style"), actionStyles);
$("art-style").value = "pixel-art";
$("action-style").value = "superhero";
createStateControls();
setPresetActions();

document.querySelectorAll("input, select, textarea").forEach((element) => {
  element.addEventListener("input", render);
  element.addEventListener("change", render);
});

$("action-style").addEventListener("change", setPresetActions);

$("copy-command").addEventListener("click", async () => {
  const command = $("command-output").textContent;
  await navigator.clipboard.writeText(command);
  $("copy-command").textContent = "Copied";
  window.setTimeout(() => {
    $("copy-command").textContent = "Copy";
  }, 1200);
});
