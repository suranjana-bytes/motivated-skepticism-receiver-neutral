const instructionScreens = [
  {
    title: "Welcome",
    body: [
      "Welcome to this study on decision-making.",
      "During this experiment, you will make several decisions. Please read the instructions carefully. Your decisions may determine your payoff.",
      "All decisions are anonymous."
    ]
  },
  {
    title: "Your Role",
    body: [
      "In this experiment, you are assigned the role of Receiver.",
      "Another participant, called the Sender, will observe a number and send you a message containing one or more numbers.",
      "Your task will be to guess the number that the Sender observed."
    ]
  },
  {
    title: "The Sender's Number",
    body: [
      "In each round, the Sender observes a number between 1 and 3.",
      "This number represents the Sender's type.",
      "The Sender can see the number, but you cannot."
    ]
  },
  {
    title: "The Message",
    body: [
      "After observing the number, the Sender sends you one message.",
      "The message will be containing one or more of the following:"
    ],
    bullets: ["The number is 1", "The number is 2", "The number is 3"],
    footer:
      "The message may contain numbers other than the Sender's true number, but it will surely contain the true number in it."
  },
  {
    title: "Sender Status",
    body: ["Each Sender is assigned a status.", "The status can be either:"],
    bullets: ["High Status", "Low Status"],
    footer:
      "Before making your decision, you will be informed about the Sender's status."
  },
  {
    title: "Your Decision",
    body: [
      "After observing the message sent by the Sender and the Sender's status, you must choose which number you believe the Sender observed.",
      "You will choose one of the following options:"
    ],
    bullets: ["1", "2", "3"]
  },
  {
    title: "Payment",
    body: [
      "Your payoff will depend on the decisions made during the experiment.",
      "The exact payment rules will be explained before the decision stage.",
      "Please make your decisions carefully."
    ]
  }
];

const rounds = [
  { senderStatus: "High Status", message: "The number is 1" },
  { senderStatus: "Low Status", message: "The number is 2" },
  { senderStatus: "High Status", message: "The number is 3" },
  { senderStatus: "Low Status", message: "The number is 1 or 2" },
  { senderStatus: "High Status", message: "The number is 2 or 3" },
  { senderStatus: "Low Status", message: "The number is 1 or 3" },
  { senderStatus: "High Status", message: "The number is 1 or 2 or 3" },
  { senderStatus: "Low Status", message: "The number is 2" },
  { senderStatus: "High Status", message: "The number is 1" },
  { senderStatus: "Low Status", message: "The number is 3" }
];

const appState = {
  phase: "instructions",
  instructionIndex: 0,
  roundIndex: 0,
  decisionStep: 0,
  selectedChoice: null,
  submittedChoices: []
};

const phaseLabel = document.getElementById("phase-label");
const screenCounter = document.getElementById("screen-counter");
const progressFill = document.getElementById("progress-fill");
const screenContent = document.getElementById("screen-content");
const actionRow = document.getElementById("action-row");

function render() {
  if (appState.phase === "instructions") {
    renderInstructionScreen();
    return;
  }

  if (appState.phase === "decision") {
    renderDecisionScreen();
    return;
  }

  renderEndScreen();
}

function renderInstructionScreen() {
  const screen = instructionScreens[appState.instructionIndex];
  phaseLabel.textContent = "Receiver Experiment";
  screenCounter.textContent = `Screen ${appState.instructionIndex + 1} of ${instructionScreens.length}`;
  progressFill.style.width = `${((appState.instructionIndex + 1) / instructionScreens.length) * 100}%`;

  screenContent.innerHTML = `
    <span class="eyebrow">Participant Instructions</span>
    <h1>${screen.title}</h1>
    ${screen.body.map((paragraph) => `<p>${paragraph}</p>`).join("")}
    ${
      screen.bullets
        ? `<ul class="info-list">${screen.bullets.map((bullet) => `<li>${bullet}</li>`).join("")}</ul>`
        : ""
    }
    ${screen.footer ? `<p>${screen.footer}</p>` : ""}
  `;

  actionRow.innerHTML = "";
  actionRow.appendChild(
    createButton(
      appState.instructionIndex === instructionScreens.length - 1 ? "Begin Experiment" : "Next",
      "btn-primary",
      advanceInstructions
    )
  );
}

function advanceInstructions() {
  if (appState.instructionIndex < instructionScreens.length - 1) {
    appState.instructionIndex += 1;
    render();
    return;
  }

  appState.phase = "decision";
  render();
}

function renderDecisionScreen() {
  const currentRound = rounds[appState.roundIndex];
  const totalScreens = 7;
  const screenNumber = appState.decisionStep + 1;

  phaseLabel.textContent = `Decision Stage`;
  screenCounter.textContent = `Round ${appState.roundIndex + 1} of ${rounds.length} • Screen ${screenNumber} of ${totalScreens}`;
  progressFill.style.width = `${((appState.roundIndex * totalScreens + screenNumber) / (rounds.length * totalScreens)) * 100}%`;

  if (appState.decisionStep === 0) {
    screenContent.innerHTML = `
      <span class="eyebrow">Round Start</span>
      <div class="round-chip">Round ${appState.roundIndex + 1} of ${rounds.length}</div>
      <h2>A new round is starting.</h2>
      <p>In this round, you will observe information sent by another participant (the Sender).</p>
      <p>Your task will be to guess the number that the Sender observed.</p>
    `;
    setActions([{ label: "Next", variant: "btn-primary", handler: nextDecisionStep }]);
    return;
  }

  if (appState.decisionStep === 1) {
    screenContent.innerHTML = `
      <span class="eyebrow">Sender Information</span>
      <h2>You are paired with a Sender.</h2>
      <p>The Sender has the following status:</p>
      <div class="status-badge">${currentRound.senderStatus}</div>
    `;
    setActions([
      { label: "Back", variant: "btn-secondary", handler: previousDecisionStep },
      { label: "Next", variant: "btn-primary", handler: nextDecisionStep }
    ]);
    return;
  }

  if (appState.decisionStep === 2) {
    screenContent.innerHTML = `
      <span class="eyebrow">Message from the Sender</span>
      <h2>The Sender sent the following message:</h2>
      <div class="message-box">"${currentRound.message}"</div>
      <p>Remember: the Sender was free to send any message, regardless of the number they actually observed.</p>
    `;
    setActions([
      { label: "Back", variant: "btn-secondary", handler: previousDecisionStep },
      { label: "Next", variant: "btn-primary", handler: nextDecisionStep }
    ]);
    return;
  }

  if (appState.decisionStep === 3) {
    screenContent.innerHTML = `
      <span class="eyebrow">Your Decision</span>
      <h2>Based on the information you observed, please guess the number that the Sender saw.</h2>
      <p>Choose one option:</p>
      <form id="decision-form">
        <div class="radio-group">
          ${[1, 2, 3]
            .map(
              (value) => `
                <div class="choice-card">
                  <input type="radio" id="choice-${value}" name="decision" value="${value}" ${
                    appState.selectedChoice === String(value) ? "checked" : ""
                  } />
                  <label for="choice-${value}">${value}</label>
                </div>
              `
            )
            .join("")}
        </div>
      </form>
    `;

    const radioButtons = screenContent.querySelectorAll('input[name="decision"]');
    radioButtons.forEach((radio) => {
      radio.addEventListener("change", (event) => {
        appState.selectedChoice = event.target.value;
        renderDecisionScreen();
      });
    });

    setActions([
      { label: "Back", variant: "btn-secondary", handler: previousDecisionStep },
      {
        label: "Submit",
        variant: appState.selectedChoice ? "btn-primary" : "btn-primary btn-disabled",
        handler: submitDecision,
        disabled: !appState.selectedChoice
      }
    ]);
    return;
  }

  if (appState.decisionStep === 4) {
    screenContent.innerHTML = `
      <span class="eyebrow">Decision Confirmation</span>
      <h2>You selected: ${appState.selectedChoice}</h2>
      <div class="choice-summary">Press Confirm to continue.</div>
    `;
    setActions([
      { label: "Back", variant: "btn-secondary", handler: previousDecisionStep },
      { label: "Confirm", variant: "btn-primary", handler: confirmDecision }
    ]);
    return;
  }

  if (appState.decisionStep === 5) {
    screenContent.innerHTML = `
      <span class="eyebrow">Round Finished</span>
      <h2>Your decision has been recorded.</h2>
      <p>Your payoff may depend on whether your guess matches the number observed by the Sender.</p>
    `;
    setActions([{ label: "Next", variant: "btn-primary", handler: nextDecisionStep }]);
    return;
  }

  const isLastRound = appState.roundIndex === rounds.length - 1;
  screenContent.innerHTML = `
    <span class="eyebrow">${isLastRound ? "Final Round" : "Next Round"}</span>
    <h2>${isLastRound ? "This part of the experiment is now finished." : "Another round will now begin."}</h2>
    <p>${isLastRound ? "Thank you for your participation." : `${rounds.length} rounds are scheduled in total.`}</p>
  `;
  setActions([
    {
      label: isLastRound ? "Finish" : "Next",
      variant: "btn-primary",
      handler: isLastRound ? finishExperiment : nextRound
    }
  ]);
}

function nextDecisionStep() {
  if (appState.decisionStep < 6) {
    appState.decisionStep += 1;
    render();
  }
}

function previousDecisionStep() {
  if (appState.decisionStep > 0) {
    appState.decisionStep -= 1;
    render();
  }
}

function submitDecision() {
  if (!appState.selectedChoice) {
    return;
  }

  appState.decisionStep = 4;
  render();
}

function confirmDecision() {
  const currentRound = rounds[appState.roundIndex];
  appState.submittedChoices[appState.roundIndex] = {
    round: appState.roundIndex + 1,
    senderStatus: currentRound.senderStatus,
    message: currentRound.message,
    choice: appState.selectedChoice
  };
  appState.decisionStep = 5;
  render();
}

function nextRound() {
  appState.roundIndex += 1;
  appState.decisionStep = 0;
  appState.selectedChoice = null;
  render();
}

function finishExperiment() {
  appState.phase = "complete";
  render();
}

function renderEndScreen() {
  phaseLabel.textContent = "Receiver Experiment";
  screenCounter.textContent = "Completed";
  progressFill.style.width = "100%";

  screenContent.innerHTML = `
    <span class="eyebrow">Final Round</span>
    <h1>This part of the experiment is now finished.</h1>
    <p>Thank you for your participation.</p>
    <p>${appState.submittedChoices.length} decisions were recorded in this demo flow.</p>
  `;

  setActions([
    {
      label: "Restart",
      variant: "btn-secondary",
      handler: restartExperiment
    }
  ]);
}

function restartExperiment() {
  appState.phase = "instructions";
  appState.instructionIndex = 0;
  appState.roundIndex = 0;
  appState.decisionStep = 0;
  appState.selectedChoice = null;
  appState.submittedChoices = [];
  render();
}

function setActions(buttons) {
  actionRow.innerHTML = "";

  buttons.forEach(({ label, variant, handler, disabled = false }) => {
    actionRow.appendChild(createButton(label, variant, handler, disabled));
  });
}

function createButton(label, className, handler, disabled = false) {
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = label;
  button.className = className;
  button.disabled = disabled;
  if (!disabled) {
    button.addEventListener("click", handler);
  }
  return button;
}

render();
