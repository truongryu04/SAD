(function () {
  function isCustomerPage() {
    return window.location.pathname.indexOf("/ui/customer/") === 0;
  }

  function getCustomerId() {
    if (typeof CUSTOMER_ID !== "undefined") {
      var parsed = Number(CUSTOMER_ID || 0);
      return Number.isFinite(parsed) ? parsed : 0;
    }
    return 0;
  }

  function getDefaultUrl() {
    var customerId = getCustomerId();
    return "http://localhost:8005/ai/chat/ui/?customer_id=" + encodeURIComponent(String(customerId));
  }

  function ensurePanel() {
    var existing = document.getElementById("customerChatPanel");
    if (existing) {
      return existing;
    }

    var panel = document.createElement("section");
    panel.id = "customerChatPanel";
    panel.className = "chat-panel";
    panel.innerHTML =
      '<div class="chat-panel-head">' +
        '<div>' +
          '<h3>Nova Assistant</h3>' +
          '<p>UI tu ai-service</p>' +
        '</div>' +
        '<div class="chat-head-actions">' +
          '<button id="customerChatOpenTab" class="chat-head-btn" type="button">Open tab</button>' +
          '<button id="customerChatClose" class="chat-head-btn" type="button">Close</button>' +
        '</div>' +
      '</div>' +
      '<iframe id="customerChatFrame" class="chat-frame" title="Nova Chatbot"></iframe>';

    document.body.appendChild(panel);

    var closeBtn = panel.querySelector("#customerChatClose");
    var openTabBtn = panel.querySelector("#customerChatOpenTab");

    closeBtn.addEventListener("click", function () {
      closePanel();
    });

    openTabBtn.addEventListener("click", function () {
      var frame = document.getElementById("customerChatFrame");
      var src = frame && frame.getAttribute("src");
      if (src) {
        window.open(src, "_blank", "noopener,noreferrer");
      }
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        closePanel();
      }
    });

    return panel;
  }

  function closePanel() {
    var panel = document.getElementById("customerChatPanel");
    if (!panel) {
      return;
    }
    panel.classList.remove("open");
  }

  function openPanel(url) {
    var panel = ensurePanel();
    var frame = document.getElementById("customerChatFrame");
    var nextUrl = url || getDefaultUrl();

    if (frame && frame.getAttribute("src") !== nextUrl) {
      frame.setAttribute("src", nextUrl);
    }

    panel.classList.add("open");
  }

  function bindFabButtons() {
    var fabs = document.querySelectorAll(".chat-fab");
    fabs.forEach(function (fab) {
      fab.addEventListener("click", function (event) {
        event.preventDefault();
        var url = fab.getAttribute("data-chat-url") || fab.getAttribute("href") || getDefaultUrl();
        openPanel(url);
      });
    });
  }

  window.openCustomerChatbot = function (url) {
    openPanel(url || getDefaultUrl());
  };

  function boot() {
    if (!isCustomerPage()) {
      return;
    }
    bindFabButtons();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
