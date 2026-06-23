const OPEN_WORDBOOK_MESSAGE = "OPEN_WORDBOOK";
const ADD_WORD_MESSAGE = "TRIGGER_ADD_WORD";

function openWordbookPage() {
  chrome.tabs.create({ url: chrome.runtime.getURL("wordbook.html") });
}

async function sendAddRequestToActiveTab() {
  try {
    const tabs = await chrome.tabs.query({ active: true, lastFocusedWindow: true });
    if (!tabs.length || !tabs[0].id) return;
    await chrome.tabs.sendMessage(tabs[0].id, { type: ADD_WORD_MESSAGE });
  } catch (error) {
    // No content script on unsupported pages, ignore silently.
  }
}

chrome.action.onClicked.addListener(() => {
  openWordbookPage();
});

chrome.commands.onCommand.addListener((command) => {
  if (command === "add_selected_word") {
    sendAddRequestToActiveTab();
  } else if (command === OPEN_WORDBOOK_MESSAGE) {
    openWordbookPage();
  }
});
