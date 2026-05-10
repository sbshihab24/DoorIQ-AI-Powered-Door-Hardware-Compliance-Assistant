const prompts = [
  "Can I use a maglock and a panic bar together?",
  "Do I need an automatic operator on a hospital entrance door?",
  "What products fit a 90-minute corridor pair?",
  "What information do you need for an exact answer?"
];

let sessionId = null;

const elements = {
  application: document.querySelector("#application"),
  buildingType: document.querySelector("#buildingType"),
  confidence: document.querySelector("#confidence"),
  flags: document.querySelector("#flags"),
  form: document.querySelector("#chatForm"),
  intent: document.querySelector("#intent"),
  leadState: document.querySelector("#leadState"),
  messageInput: document.querySelector("#messageInput"),
  messages: document.querySelector("#messages"),
  missingInfo: document.querySelector("#missingInfo"),
  products: document.querySelector("#products"),
  quickPrompts: document.querySelector("#quickPrompts"),
  resetButton: document.querySelector("#resetButton"),
  sendButton: document.querySelector("#sendButton"),
  sessionId: document.querySelector("#sessionId"),
  sources: document.querySelector("#sources"),
  state: document.querySelector("#state"),
  zipCode: document.querySelector("#zipCode"),
  egressPath: document.querySelector("#egressPath"),
  ratedOpening: document.querySelector("#ratedOpening"),
  accessibleRoute: document.querySelector("#accessibleRoute")
};

function appendMessage(role, text) {
  const article = document.createElement("article");
  article.className = `message ${role}`;
  const paragraph = document.createElement("p");
  appendTextWithLinks(paragraph, text);
  article.append(paragraph);
  elements.messages.append(article);
  elements.messages.scrollTop = elements.messages.scrollHeight;
}

function appendTextWithLinks(container, text) {
  const urlPattern = /(https?:\/\/[^\s)]+)/g;
  let lastIndex = 0;
  for (const match of text.matchAll(urlPattern)) {
    if (match.index > lastIndex) {
      container.append(document.createTextNode(text.slice(lastIndex, match.index)));
    }

    const link = document.createElement("a");
    link.href = match[0];
    link.target = "_blank";
    link.rel = "noreferrer";
    link.textContent = match[0];
    container.append(link);
    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < text.length) {
    container.append(document.createTextNode(text.slice(lastIndex)));
  }
}

function requestPayload(message) {
  const building = {};
  const location = {};

  if (elements.buildingType.value) building.building_type = elements.buildingType.value;
  if (elements.application.value.trim()) building.application = elements.application.value.trim();
  if (elements.egressPath.checked) building.is_egress_path = true;
  if (elements.ratedOpening.checked) building.fire_rating_required = true;
  if (elements.accessibleRoute.checked) building.accessibility_required = true;
  if (elements.state.value.trim()) location.state = elements.state.value.trim().toUpperCase();
  if (elements.zipCode.value.trim()) location.zip_code = elements.zipCode.value.trim();

  return {
    session_id: sessionId,
    message,
    building: Object.keys(building).length ? building : null,
    location: Object.keys(location).length ? location : null
  };
}

function renderResponse(data) {
  sessionId = data.session_id;
  elements.sessionId.textContent = sessionId.slice(0, 8);
  elements.confidence.textContent = data.confidence || "-";
  elements.leadState.textContent = data.should_capture_lead ? "Capture" : "Not needed";
  elements.intent.textContent = data.intent || "Intent";
  elements.flags.textContent = data.human_review_recommended ? "Human review" : "Self-serve";
  elements.missingInfo.textContent = (data.missing_information || []).join(", ");
  elements.products.textContent = (data.recommended_products || []).map((product) => product.name).join(", ");
  elements.sources.textContent = [
    ...(data.code_references || []),
    ...(data.knowledge_references || [])
  ].map((source) => source.title).join(", ");
}

async function sendMessage(message) {
  appendMessage("user", message);
  elements.sendButton.disabled = true;
  elements.sendButton.textContent = "Sending";

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(requestPayload(message))
    });
    if (!response.ok) {
      throw new Error(`Request failed with ${response.status}`);
    }
    const data = await response.json();
    appendMessage("assistant", data.answer);
    renderResponse(data);
  } catch (error) {
    appendMessage("assistant", `Could not reach the chatbot API. ${error.message}`);
  } finally {
    elements.sendButton.disabled = false;
    elements.sendButton.textContent = "Send";
  }
}

elements.form.addEventListener("submit", (event) => {
  event.preventDefault();
  const message = elements.messageInput.value.trim();
  if (!message) return;
  elements.messageInput.value = "";
  sendMessage(message);
});

elements.resetButton.addEventListener("click", () => {
  sessionId = null;
  elements.sessionId.textContent = "New";
  elements.confidence.textContent = "-";
  elements.leadState.textContent = "Not needed";
  elements.intent.textContent = "Intent";
  elements.flags.textContent = "";
  elements.missingInfo.textContent = "";
  elements.products.textContent = "";
  elements.sources.textContent = "";
  elements.messages.replaceChildren();
  appendMessage("assistant", "Hi, how can I help you?");
});

prompts.forEach((prompt) => {
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = prompt;
  button.title = prompt;
  button.addEventListener("click", () => {
    elements.messageInput.value = prompt;
    elements.messageInput.focus();
  });
  elements.quickPrompts.append(button);
});
