const prompts = [
  "What code applies to a school entrance in my state?",
  "Can I use a maglock and a panic bar together?",
  "What products on your site fit a 90-minute corridor pair?",
  "Do I need an automatic operator on a hospital entrance door?",
  "Can I electrify this fire-rated opening?",
  "What information do you need before giving an exact answer?"
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

function textOrDash(value) {
  return value || "-";
}

function appendMessage(role, text) {
  const article = document.createElement("article");
  article.className = `message ${role}`;
  const paragraph = document.createElement("p");
  paragraph.textContent = text;
  article.append(paragraph);
  elements.messages.append(article);
  elements.messages.scrollTop = elements.messages.scrollHeight;
}

function pill(text, tone = "") {
  const span = document.createElement("span");
  span.className = `pill ${tone}`.trim();
  span.textContent = text;
  return span;
}

function renderList(container, values, emptyText) {
  container.replaceChildren();
  if (!values || values.length === 0) {
    const empty = document.createElement("p");
    empty.className = "empty";
    empty.textContent = emptyText;
    container.append(empty);
    return;
  }
  values.forEach((value) => container.append(pill(value.replaceAll("_", " "))));
}

function renderCards(container, items, emptyText, mapItem) {
  container.replaceChildren();
  if (!items || items.length === 0) {
    const empty = document.createElement("p");
    empty.className = "empty";
    empty.textContent = emptyText;
    container.append(empty);
    return;
  }
  items.forEach((item) => {
    const card = document.createElement("article");
    card.className = "card";
    const title = document.createElement("strong");
    const body = document.createElement("p");
    const mapped = mapItem(item);
    title.textContent = mapped.title;
    body.textContent = mapped.body;
    card.append(title, body);
    container.append(card);
  });
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
  elements.confidence.textContent = textOrDash(data.confidence);
  elements.leadState.textContent = data.should_capture_lead ? "Capture" : "Not needed";
  elements.intent.textContent = textOrDash(data.intent);

  elements.flags.replaceChildren(
    pill(data.human_review_recommended ? "Human review" : "Self-serve", data.human_review_recommended ? "danger" : "ok"),
    pill(data.should_capture_lead ? "Lead prompt" : "No lead prompt", data.should_capture_lead ? "warn" : ""),
    pill(data.lead_capture_status?.lead_created ? "Lead saved" : "No lead saved", data.lead_capture_status?.lead_created ? "ok" : "")
  );

  renderList(elements.missingInfo, data.missing_information, "No missing information.");
  renderCards(
    elements.products,
    data.recommended_products,
    "No product matches yet.",
    (product) => ({
      title: product.name,
      body: `${product.category}: ${product.reason}`
    })
  );
  renderCards(
    elements.sources,
    [...(data.code_references || []), ...(data.knowledge_references || [])],
    "No sources returned yet.",
    (source) => ({
      title: source.title,
      body: source.summary || source.section || source.source || ""
    })
  );
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
  elements.flags.replaceChildren();
  elements.missingInfo.replaceChildren();
  elements.products.replaceChildren();
  elements.sources.replaceChildren();
  elements.messages.replaceChildren();
  appendMessage("assistant", "New session ready. Ask a DoorIQ question.");
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
