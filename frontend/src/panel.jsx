// Entry point for the Intentsity sidebar panel.
//
// Home Assistant loads this file as an ES module and then creates an
// <intentsity-panel> element, assigning `hass`, `narrow`, `route` and `panel`
// properties to it. React renders inside a shadow root so the design system's
// reset and token declarations cannot leak into the rest of the frontend.
import React from "react";
import { createRoot } from "react-dom/client";

import { App } from "./App.jsx";
import { FONT_HREF, tokensCss } from "./ds/tokens.js";
import appCss from "./styles/app.css";

// Token declarations first: the panel styles below build on them.
const panelCss = `${tokensCss}\n${appCss}`;

const TAG = "intentsity-panel";
const FONT_LINK_ID = "intentsity-fonts";

/**
 * Link the webfont into document.head. An @import inside a shadow root is
 * ignored by the browser, and a font loaded in the document is usable by shadow
 * trees, so this is the one style the panel deliberately puts in global scope.
 */
function loadFonts() {
  if (document.getElementById(FONT_LINK_ID)) return;
  const link = document.createElement("link");
  link.id = FONT_LINK_ID;
  link.rel = "stylesheet";
  link.href = FONT_HREF;
  document.head.appendChild(link);
}

let sharedSheet = null;

/** One constructed stylesheet shared by every instance of the panel. */
function tokenSheet() {
  if (sharedSheet) return sharedSheet;
  if (typeof CSSStyleSheet !== "undefined" && "replaceSync" in CSSStyleSheet.prototype) {
    sharedSheet = new CSSStyleSheet();
    sharedSheet.replaceSync(panelCss);
  }
  return sharedSheet;
}

class IntentsityPanel extends HTMLElement {
  #root = null;
  #mount = null;
  #hass = null;
  #narrow = false;
  #panel = null;
  #route = null;

  connectedCallback() {
    if (this.#root) {
      this.#render();
      return;
    }
    loadFonts();

    const shadow = this.attachShadow({ mode: "open" });
    const sheet = tokenSheet();
    if (sheet) {
      shadow.adoptedStyleSheets = [sheet];
    } else {
      // Safari < 16.4 and other engines without adoptedStyleSheets support.
      const style = document.createElement("style");
      style.textContent = panelCss;
      shadow.appendChild(style);
    }

    this.#mount = document.createElement("div");
    // The panel occupies the whole content area; HA gives the host no height.
    this.#mount.style.height = "100%";
    shadow.appendChild(this.#mount);
    this.style.display = "block";
    this.style.height = "100%";

    this.#root = createRoot(this.#mount);
    this.#render();
  }

  disconnectedCallback() {
    // React must unmount asynchronously: disconnectedCallback can run during a
    // React commit of the parent tree, and unmounting synchronously there warns.
    const root = this.#root;
    this.#root = null;
    if (root) setTimeout(() => root.unmount(), 0);
  }

  set hass(value) {
    this.#hass = value;
    this.#render();
  }

  get hass() {
    return this.#hass;
  }

  set narrow(value) {
    this.#narrow = Boolean(value);
    this.#render();
  }

  set panel(value) {
    this.#panel = value;
  }

  set route(value) {
    this.#route = value;
  }

  #render() {
    if (!this.#root || !this.#hass) return;
    this.#root.render(
      <App
        hass={this.#hass}
        narrow={this.#narrow}
        panel={this.#panel}
        route={this.#route}
      />,
    );
  }
}

if (!customElements.get(TAG)) {
  customElements.define(TAG, IntentsityPanel);
}
