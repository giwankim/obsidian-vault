---
title: "Your Logitech mousekeyboardcamera,finally local."
source: "https://openlogi.org/en"
author:
published:
created: 2026-08-21
description: "A native, local-first alternative to Logitech Options+, written in Rust. Remap buttons, drive DPI and SmartShift over HID++ — no account, no telemetry."
tags:
  - "clippings"
---

> [!summary]
> OpenLogi is a native, local-first alternative to Logitech Options+, written in Rust, that drives Logitech devices directly over the HID++ protocol with no account, no telemetry, and no cloud.
> It remaps each physical button to any of 44 built-in actions (plus custom shortcuts, app launchers, and scripted actions), controls DPI presets and SmartShift wheel behavior, and shows live per-device battery and charge state over Bolt, Unifying, Lightspeed, Bluetooth, or USB.
> Bindings live in a plain config.toml you own, signed builds ship for macOS (Homebrew cask), Linux, and Windows, and per-application profiles are announced as coming in a later release.

## Click a button, bind an action.

The center of the app, working right here: a mouse diagram with clickable hotspots and a per-button action picker. Choose a hotspot, then bind any of the built-in actions.

![MX Master 4](https://assets.openlogi.org/v1/devices/mx_master_4/side_core.png)

~/.config/openlogi/config.tomllive

```
schema_version = 2selected_device = "2b042" [devices.2b042.bindings]MiddleClick   = "MissionControl"DpiToggle     = "CycleDpiPresets"Thumbwheel    = "VolumeUp"Forward       = "BrowserForward"Back          = "BrowserBack"GestureButton = "AppExpose"
```

MX Master 4Writes straight to `config.toml`, the file you own.

## Everything Options+ does, without the account.

OpenLogi drives your mouse over HID++ directly: buttons, DPI and SmartShift, from a native app that never phones home.

<svg viewBox="0 0 260 150" fill="none" preserveAspectRatio="xMidYMid meet" focusable="false" aria-hidden="true"><g><g><rect x="22" y="30" width="58" height="20" rx="4" fill="Canvas" stroke="currentColor" stroke-width="1"></rect><text font-family="var(--mono)" font-size="9" letter-spacing="0.02em" x="51" y="43" text-anchor="middle" fill="currentColor">Back</text></g> <path d="M84 40 H152" stroke="currentColor" stroke-width="1"></path><path d="M148 36 L154 40 L148 44" stroke="currentColor" stroke-width="1" fill="none"></path><g><rect x="156" y="30" width="92" height="20" rx="4" fill="Canvas" stroke="currentColor" stroke-width="1"></rect><text font-family="var(--mono)" font-size="9" letter-spacing="0.02em" x="202" y="43" text-anchor="middle" fill="currentColor">BrowserBack</text></g></g> <g><g><rect x="22" y="65" width="58" height="20" rx="4" fill="Canvas" stroke="currentColor" stroke-width="1"></rect><text font-family="var(--mono)" font-size="9" letter-spacing="0.02em" x="51" y="78" text-anchor="middle" fill="currentColor">Middle</text></g> <path d="M84 75 H152" stroke="currentColor" stroke-width="1.25"></path><path d="M148 71 L154 75 L148 79" stroke="currentColor" stroke-width="1.25" fill="none"></path><g><rect x="156" y="65" width="92" height="20" rx="4" fill="currentColor" stroke="currentColor" stroke-width="1.25"></rect><text font-family="var(--mono)" font-size="9" letter-spacing="0.02em" x="202" y="78" text-anchor="middle" fill="currentColor">MissionControl</text></g></g> <g><g><rect x="22" y="100" width="58" height="20" rx="4" fill="Canvas" stroke="currentColor" stroke-width="1"></rect><text font-family="var(--mono)" font-size="9" letter-spacing="0.02em" x="51" y="113" text-anchor="middle" fill="currentColor">Forward</text></g> <path d="M84 110 H152" stroke="currentColor" stroke-width="1"></path><path d="M148 106 L154 110 L148 114" stroke="currentColor" stroke-width="1" fill="none"></path><g><rect x="156" y="100" width="92" height="20" rx="4" fill="Canvas" stroke="currentColor" stroke-width="1"></rect><text font-family="var(--mono)" font-size="9" letter-spacing="0.02em" x="202" y="113" text-anchor="middle" fill="currentColor">NextTab</text></g></g></svg>

### Remap any button

Bind any of 44 built-in actions to each physical button, per device. Custom shortcuts, app launchers and scripted actions too.

<svg viewBox="0 0 260 150" fill="none" preserveAspectRatio="xMidYMid meet" focusable="false" aria-hidden="true"><path d="M26 92 H234" stroke="currentColor" stroke-width="1"></path><path d="M26 92 v6" stroke="currentColor" stroke-width="1"></path><path d="M42 92 v6" stroke="currentColor" stroke-width="1"></path><path d="M58 92 v6" stroke="currentColor" stroke-width="1"></path><path d="M74 92 v6" stroke="currentColor" stroke-width="1"></path><path d="M90 92 v6" stroke="currentColor" stroke-width="1"></path><path d="M106 92 v6" stroke="currentColor" stroke-width="1"></path><path d="M122 92 v6" stroke="currentColor" stroke-width="1"></path><path d="M138 92 v6" stroke="currentColor" stroke-width="1"></path><path d="M154 92 v6" stroke="currentColor" stroke-width="1"></path><path d="M170 92 v6" stroke="currentColor" stroke-width="1"></path><path d="M186 92 v6" stroke="currentColor" stroke-width="1"></path><path d="M202 92 v6" stroke="currentColor" stroke-width="1"></path><path d="M218 92 v6" stroke="currentColor" stroke-width="1"></path><path d="M234 92 v6" stroke="currentColor" stroke-width="1"></path><text font-family="var(--mono)" font-size="9" letter-spacing="0.02em" x="26" y="114" fill="currentColor">200</text> <text font-family="var(--mono)" font-size="9" letter-spacing="0.02em" x="234" y="114" text-anchor="end" fill="currentColor">8000</text> <g><path d="M42 87 l4 5 l-4 5 l-4 -5 Z" fill="Canvas" stroke="currentColor" stroke-width="1"></path></g><g><path d="M63.333333333333336 87 l4 5 l-4 5 l-4 -5 Z" fill="currentColor" stroke="currentColor" stroke-width="1"></path></g><g><path d="M106 87 l4 5 l-4 5 l-4 -5 Z" fill="Canvas" stroke="currentColor" stroke-width="1"></path></g><path d="M63.333333333333336 80 V58" stroke="currentColor" stroke-width="1.25"></path><text font-family="var(--mono)" font-size="9" letter-spacing="0.02em" x="63.333333333333336" y="52" text-anchor="middle" fill="currentColor">1600 DPI</text></svg>

### DPI control & presets

Set pointer resolution and cycle your own presets, written straight to the sensor over HID++.

<svg viewBox="0 0 260 150" fill="none" preserveAspectRatio="xMidYMid meet" focusable="false" aria-hidden="true"><circle cx="130" cy="72" r="34" stroke="currentColor" stroke-width="1"></circle><circle cx="130" cy="72" r="5" fill="Canvas" stroke="currentColor" stroke-width="1"></circle><path d="M130.0 42.0 L130.0 34.0" stroke="currentColor" stroke-width="1"></path><path d="M118.5 44.3 L115.5 36.9" stroke="currentColor" stroke-width="1"></path><path d="M108.8 50.8 L103.1 45.1" stroke="currentColor" stroke-width="1"></path><path d="M102.3 60.5 L94.9 57.5" stroke="currentColor" stroke-width="1"></path><path d="M100.0 72.0 L92.0 72.0" stroke="currentColor" stroke-width="1"></path><path d="M102.3 83.5 L94.9 86.5" stroke="currentColor" stroke-width="1"></path><path d="M108.8 93.2 L103.1 98.9" stroke="currentColor" stroke-width="1"></path><path d="M118.5 99.7 L115.5 107.1" stroke="currentColor" stroke-width="1"></path><path d="M130.0 102.0 L130.0 110.0" stroke="currentColor" stroke-width="1"></path><path d="M130 38 A34 34 0 0 1 130 106" stroke="currentColor" stroke-width="1.25"></path><path d="M154.48 97.84 l7 -1.5 l-3.5 6.5 Z" fill="currentColor"></path><text font-family="var(--mono)" font-size="9" letter-spacing="0.02em" x="88" y="75" text-anchor="end" fill="currentColor">Ratchet</text> <text font-family="var(--mono)" font-size="9" letter-spacing="0.02em" x="172" y="75" fill="currentColor">Free-spin</text> <text font-family="var(--mono)" font-size="9" letter-spacing="0.02em" x="130" y="130" text-anchor="middle" fill="currentColor">autoDisengage threshold</text></svg>

### SmartShift

Flip the wheel between ratchet and free-spin, or let it switch automatically by scroll speed.

<svg viewBox="0 0 260 150" fill="none" preserveAspectRatio="xMidYMid meet" focusable="false" aria-hidden="true"><g><rect x="62" y="96" width="136" height="20" rx="4" fill="Canvas" stroke="currentColor" stroke-width="1"></rect><text font-family="var(--mono)" font-size="9" letter-spacing="0.02em" x="130" y="109" text-anchor="middle" fill="currentColor">Global</text></g> <g><rect x="74" y="66" width="136" height="20" rx="4" fill="Canvas" stroke="currentColor" stroke-width="1"></rect><text font-family="var(--mono)" font-size="9" letter-spacing="0.02em" x="142" y="79" text-anchor="middle" fill="currentColor">"com.google.Chrome"</text></g> <g><rect x="86" y="36" width="136" height="20" rx="4" fill="currentColor" stroke="currentColor" stroke-width="1.25"></rect><text font-family="var(--mono)" font-size="9" letter-spacing="0.02em" x="154" y="49" text-anchor="middle" fill="currentColor">"com.figma.Desktop"</text></g> <path d="M52 46 H80" stroke="currentColor" stroke-width="1.25"></path><path d="M76 42 L82 46 L76 50" stroke="currentColor" stroke-width="1.25" fill="none"></path><text font-family="var(--mono)" font-size="9" letter-spacing="0.02em" x="20" y="30" fill="currentColor">Frontmost</text></svg>

### Per-app profilesComing soon

Per-application overlays that switch the moment your focused app does. Ships in a later release.

<svg viewBox="0 0 260 150" fill="none" preserveAspectRatio="xMidYMid meet" focusable="false" aria-hidden="true"><g><rect x="24" y="8" width="92" height="20" rx="4" fill="Canvas" stroke="currentColor" stroke-width="1"></rect><g transform="translate(32, 12) scale(0.375) translate(-7, -7)"><path fill-rule="evenodd" fill="currentColor" d="M25.5367 36.4498L15.7592 21.831H22.9999L15.7911 10.772L7.66663 23.3069L16.1851 36.4498H25.5367ZM29.8498 36.3957L38.3333 23.3069L29.8148 10.1641L20.0492 10.1641L29.3888 24.9927H22.361L29.8498 36.3957Z"></path></g><text font-family="var(--mono)" font-size="9" letter-spacing="0.02em" x="50" y="21" fill="currentColor">Bolt</text> <path d="M120 18 C146 18, 156 75, 182 75" stroke="currentColor" stroke-width="1"></path></g><g><rect x="24" y="36" width="92" height="20" rx="4" fill="Canvas" stroke="currentColor" stroke-width="1"></rect><g transform="translate(32, 40) scale(0.5) translate(-33.239067, -367.12994)"><path fill="currentColor" d="m 53.531063,377.8206 c -4.26933,0 -4.488,-0.38133 -4.708,-0.75866 -0.22,-0.38134 -0.43866,-0.76 1.696,-4.456 0.36267,-0.628 0.14667,-1.42934 -0.47866,-1.78934 -0.62667,-0.36266 -1.42667,-0.148 -1.78934,0.47867 -2.13333,3.69733 -2.57333,3.69733 -3.01066,3.69733 -0.44,0 -0.87734,0 -3.012,-3.69733 -0.36134,-0.62667 -1.16267,-0.84133 -1.78934,-0.47867 -0.62666,0.36 -0.84133,1.16134 -0.47866,1.78934 2.13333,3.696 1.91333,4.07466 1.696,4.456 -0.22134,0.37733 -0.44,0.75866 -4.70934,0.75866 -0.72266,0 -1.308,0.58534 -1.308,1.30934 0,0.724 0.58534,1.30933 1.308,1.30933 4.26934,0 4.488,0.38133 4.70934,0.75867 0.21733,0.38133 0.43733,0.76133 -1.696,4.46 -0.36267,0.624 -0.148,1.42666 0.47866,1.78533 0.62667,0.364 1.428,0.14667 1.78934,-0.47867 2.13466,-3.696 2.572,-3.696 3.012,-3.696 0.43733,0 0.87733,0 3.01066,3.696 0.36267,0.62534 1.16267,0.84267 1.78934,0.47867 0.62533,-0.35867 0.84133,-1.16133 0.47866,-1.78533 -2.13466,-3.69867 -1.916,-4.07867 -1.696,-4.46 0.22,-0.37734 0.43867,-0.75867 4.708,-0.75867 0.72134,0 1.30934,-0.58533 1.30934,-1.30933 0,-0.724 -0.588,-1.30934 -1.30934,-1.30934 m -9.792,2.80934 c -0.46133,-0.46134 -0.46133,-2.53867 0,-3 0.46134,-0.46134 2.53867,-0.46134 3,0 0.46134,0.46133 0.46134,2.53866 0,3 -0.46133,0.46266 -2.53866,0.46266 -3,0 m 1.50134,10.5 c -4.00134,0 -8.00134,0 -10.00134,-1.99867 -1.999996,-2 -1.999996,-6 -1.999996,-10.00133 0,-4 0,-8 1.999996,-10.00134 2,-1.99866 6,-1.99866 10.00134,-1.99866 4,0 7.99866,0 10,1.99866 2.00133,2.00134 2.00133,6.00134 2.00133,10.00134 0,4.00133 0,8.00133 -2.00133,10.00133 -2.00134,1.99867 -6,1.99867 -10,1.99867"></path></g><text font-family="var(--mono)" font-size="9" letter-spacing="0.02em" x="50" y="49" fill="currentColor">Unifying</text> <path d="M120 46 C146 46, 156 75, 182 75" stroke="currentColor" stroke-width="1"></path></g><g><rect x="24" y="64" width="92" height="20" rx="4" fill="Canvas" stroke="currentColor" stroke-width="1"></rect><g transform="translate(32, 68) scale(0.5)"><path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path></g><text font-family="var(--mono)" font-size="9" letter-spacing="0.02em" x="50" y="77" fill="currentColor">Lightspeed</text> <path d="M120 74 C146 74, 156 75, 182 75" stroke="currentColor" stroke-width="1"></path></g><g><rect x="24" y="92" width="92" height="20" rx="4" fill="Canvas" stroke="currentColor" stroke-width="1"></rect><g transform="translate(32, 96) scale(0.5)"><path d="m7 7 10 10-5 5V2l5 5L7 17" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path></g><text font-family="var(--mono)" font-size="9" letter-spacing="0.02em" x="50" y="105" fill="currentColor">Bluetooth</text> <path d="M120 102 C146 102, 156 75, 182 75" stroke="currentColor" stroke-width="1"></path></g><g><rect x="24" y="120" width="92" height="20" rx="4" fill="Canvas" stroke="currentColor" stroke-width="1"></rect><g transform="translate(32, 124) scale(0.5)" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="10" cy="7" r="1"></circle><circle cx="4" cy="20" r="1"></circle><path d="M4.7 19.3 19 5"></path><path d="m21 3-3 1 2 2Z"></path><path d="M9.26 7.68 5 12l2 5"></path><path d="m10 14 5 2 3.5-3.5"></path><path d="m18 12 1-1 1 1-1 1Z"></path></g><text font-family="var(--mono)" font-size="9" letter-spacing="0.02em" x="50" y="133" fill="currentColor">USB</text> <path d="M120 130 C146 130, 156 75, 182 75" stroke="currentColor" stroke-width="1"></path></g><circle cx="208" cy="75" r="24" fill="currentColor" stroke="currentColor" stroke-width="1.25"></circle><text font-family="var(--mono)" font-size="9" letter-spacing="0.02em" x="208" y="78" text-anchor="middle" fill="currentColor">HID++</text></svg>

### Bolt, Unifying, Lightspeed, Bluetooth or wired

Reach devices over a Logi Bolt, Unifying or Lightspeed receiver, a direct Bluetooth pairing, or a USB cable. No receiver required.

<svg viewBox="0 0 260 150" fill="none" preserveAspectRatio="xMidYMid meet" focusable="false" aria-hidden="true"><g><text font-family="var(--mono)" font-size="9" letter-spacing="0.02em" x="24" y="43" fill="currentColor">MX Master 4</text> <rect x="112" y="30" width="86" height="20" rx="4" stroke="currentColor" stroke-width="1.25"></rect><rect x="115" y="33" width="68.8" height="14" rx="2" fill="currentColor" stroke="currentColor" stroke-width="1"></rect><text font-family="var(--mono)" font-size="9" letter-spacing="0.02em" x="208" y="43" fill="currentColor">86%</text> <path d="M240 33 l-5 8 h4 l-3 7 l8 -9 h-4 l4 -6 Z" fill="currentColor"></path></g><g><text font-family="var(--mono)" font-size="9" letter-spacing="0.02em" x="24" y="78" fill="currentColor">MX Keys</text> <rect x="112" y="65" width="86" height="20" rx="4" stroke="currentColor" stroke-width="1"></rect><rect x="115" y="68" width="49.6" height="14" rx="2" fill="Canvas" stroke="currentColor" stroke-width="1"></rect><text font-family="var(--mono)" font-size="9" letter-spacing="0.02em" x="208" y="78" fill="currentColor">62%</text></g> <g><text font-family="var(--mono)" font-size="9" letter-spacing="0.02em" x="24" y="113" fill="currentColor">Litra Glow</text> <rect x="112" y="100" width="86" height="20" rx="4" stroke="currentColor" stroke-width="1"></rect><rect x="115" y="103" width="80" height="14" rx="2" fill="Canvas" stroke="currentColor" stroke-width="1"></rect><text font-family="var(--mono)" font-size="9" letter-spacing="0.02em" x="208" y="113" fill="currentColor">100%</text></g></svg>

### Live device view

A carousel of paired devices with battery percentage and charge state for everything online.

## Nothing between your mouse and your machine.

No account, no telemetry, no cloud. Bindings live in a plain TOML file you own, and every change goes straight to the device over HID++.

<svg viewBox="0 0 380 288" fill="none" preserveAspectRatio="xMidYMid meet" aria-hidden="true" focusable="false"><rect x="20" y="40" width="340" height="224" rx="10" stroke="currentColor" stroke-width="1" stroke-dasharray="5 5"></rect><text font-family="var(--mono)" font-size="10" letter-spacing="0.02em" x="32" y="28" fill="#888">Your machine</text> <path d="M140 112 H188" stroke="currentColor" stroke-width="1"></path><text font-family="var(--mono)" font-size="10" letter-spacing="0.02em" x="164" y="104" text-anchor="middle" fill="currentColor">IPC</text> <path d="M264 112 H296" stroke="currentColor" stroke-width="1"></path><text font-family="var(--mono)" font-size="10" letter-spacing="0.02em" x="283" y="104" text-anchor="middle" fill="currentColor">HID++</text> <path d="M220 132 V176" stroke="currentColor" stroke-width="1"></path><g><rect x="44" y="72" width="96" height="72" rx="6" fill="Canvas" stroke="currentColor" stroke-width="1"></rect><path d="M44 86 H140" stroke="currentColor" stroke-width="1"></path><circle cx="53" cy="79" r="1.6" fill="currentColor"></circle><circle cx="59" cy="79" r="1.6" fill="currentColor"></circle><circle cx="65" cy="79" r="1.6" fill="currentColor"></circle><rect x="53" y="100" width="30" height="15" rx="2.5" fill="Canvas" stroke="currentColor" stroke-width="1"></rect><path d="M57 105 H73" stroke="currentColor" stroke-width="1.4"></path><path d="M57 110 H68" stroke="currentColor" stroke-width="1.4"></path><rect x="109" y="95" width="17" height="32" rx="8.5" fill="Canvas" stroke="currentColor" stroke-width="1"></rect><path d="M117.5 95 V106" stroke="currentColor" stroke-width="1"></path><path d="M83 107 H104 L109 109" stroke="currentColor" stroke-width="1" fill="none"></path><circle cx="112" cy="110" r="2.2" fill="currentColor"></circle></g><g><rect x="188" y="92" width="76" height="40" rx="6" fill="Canvas" stroke="currentColor" stroke-width="1"></rect><circle cx="206" cy="112" r="5.5" fill="none" stroke="currentColor" stroke-width="1"></circle><circle cx="206" cy="112" r="2" fill="none" stroke="currentColor" stroke-width="1"></circle><path d="M211.08 114.10 L213.39 115.06 M208.10 117.08 L209.06 119.39 M203.90 117.08 L202.94 119.39 M200.92 114.10 L198.61 115.06 M200.92 109.90 L198.61 108.94 M203.90 106.92 L202.94 104.61 M208.10 106.92 L209.06 104.61 M211.08 109.90 L213.39 108.94" stroke="currentColor" stroke-width="1"></path><text font-family="var(--mono)" font-size="10" letter-spacing="0.02em" x="222" y="116" fill="currentColor">Agent</text> <circle cx="255" cy="100" r="1.8" fill="currentColor"></circle></g><g transform="translate(292, 72) scale(0.08536585365853659)"><path d="M300 8 C255 14, 238 60, 236 120 C233 200, 222 300, 205 350 C150 390, 60 480, 18 585 C5 620, 5 640, 15 665 C55 760, 150 900, 310 1000 C340 1020, 390 1022, 430 1000 C560 900, 640 720, 650 590 C656 500, 645 400, 610 300 C560 180, 480 100, 420 55 C395 30, 340 4, 300 8 Z" fill="Canvas" stroke="currentColor" stroke-width="1" vector-effect="non-scaling-stroke"></path><path d="M330 10 C355 60, 380 110, 400 150" fill="none" stroke="currentColor" stroke-width="1" vector-effect="non-scaling-stroke"></path><path d="M395 400 C500 390, 610 450, 654 550" fill="none" stroke="currentColor" stroke-width="1" vector-effect="non-scaling-stroke"></path><g transform="rotate(-15 470 240)"><rect x="430" y="150" width="80" height="180" rx="40" fill="Canvas" stroke="currentColor" stroke-width="1" vector-effect="non-scaling-stroke"></rect><path d="M440 200 H500 M436 240 H504 M440 280 H500" stroke="currentColor" stroke-width="1" vector-effect="non-scaling-stroke"></path></g><g transform="rotate(-15 534 431)"><rect x="505" y="395" width="58" height="72" rx="22" fill="Canvas" stroke="currentColor" stroke-width="1" vector-effect="non-scaling-stroke"></rect></g><circle cx="548" cy="505" r="9" fill="currentColor"></circle><g transform="rotate(-32 360 550)"><rect x="310" y="450" width="104" height="200" rx="52" fill="Canvas" stroke="currentColor" stroke-width="1" vector-effect="non-scaling-stroke"></rect><path d="M330 505 H396 M326 550 H400 M330 595 H396" stroke="currentColor" stroke-width="1" vector-effect="non-scaling-stroke"></path></g><g transform="rotate(-20 267 397)"><rect x="240" y="345" width="54" height="104" rx="27" fill="Canvas" stroke="currentColor" stroke-width="1" vector-effect="non-scaling-stroke"></rect></g><g transform="rotate(-25 297 517)"><rect x="270" y="462" width="54" height="112" rx="27" fill="Canvas" stroke="currentColor" stroke-width="1" vector-effect="non-scaling-stroke"></rect></g><path d="M62 448 L198 382 L308 690 L235 872 L60 752 Z" fill="none" stroke="currentColor" stroke-width="1" stroke-linejoin="round" vector-effect="non-scaling-stroke"></path><circle cx="200" cy="500" r="18" fill="none" stroke="currentColor" stroke-width="1" stroke-dasharray="2 3" vector-effect="non-scaling-stroke"></circle></g><g><path d="M192.5 176.5 H236 L249.5 190 V232.5 H192.5 Z" fill="Canvas" stroke="currentColor" stroke-width="1"></path><path d="M236 176.5 V190 H249.5" fill="none" stroke="currentColor" stroke-width="1"></path><path d="M201 196 H219" stroke="currentColor" stroke-width="1.6"></path><path d="M201 205 H238" stroke="currentColor" stroke-width="1.4"></path><path d="M201 212 H230" stroke="currentColor" stroke-width="1.4"></path><path d="M201 219 H238" stroke="currentColor" stroke-width="1.4"></path></g><path d="M192.5 176.5 H236 L249.5 190 V232.5 H192.5 Z" fill="none" stroke="currentColor" stroke-width="1"></path><text font-family="var(--mono)" font-size="10" letter-spacing="0.02em" x="92" y="160" text-anchor="middle" fill="currentColor">GUI</text> <text font-family="var(--mono)" font-size="10" letter-spacing="0.02em" x="320" y="174" text-anchor="middle" fill="currentColor">MX Master 4</text> <text font-family="var(--mono)" font-size="10" letter-spacing="0.02em" x="221" y="250" text-anchor="middle" fill="currentColor">config.toml</text><circle r="3" fill="currentColor" opacity="0" cy="112" cx="140" style="opacity: 0.2373;"></circle></svg>

## Up and running in a minute.

Signed builds for macOS, Linux and Windows. Pick your platform below. Step-by-step setup lives in the docs.

### macOS

$brew install --cask openlogi

Homebrew is recommended, or grab the signed.dmg for Apple silicon or Intel.

### Linux

Packages for amd64 and arm64, with.rpm and Arch.pkg.tar.zst builds also available.

### Windows

New

The newest port: signed x86\_64 and arm64 installers, validated on Windows 11.

Quit Logi Options+ before launching: the two fight over HID++ access, and only one app can own a receiver at a time. On Linux, the same applies to Solaar.

## Things you might ask.

Something else? Ask in [Telegram](https://t.me/+VDtkR5OSAT04NzVh) or open a [GitHub issue](https://github.com/AprilNEA/OpenLogi/issues).

Will OpenLogi support Logitech Flow?

It's on the roadmap, at the far end: a cross-computer pointer and clipboard bridge is a very large feature. The half that lives in the protocol already ships. OpenLogi drives Easy-Switch host switching over HID++ (0x1814/0x1815), and paired mice follow the keyboard when it switches hosts. If the rest lands, it will be opt-in and local-network only.

Can I pair a new device from OpenLogi?

Bolt pairing ships in the GUI, and Unifying and Lightspeed pairing is in progress. Until it lands, pair once with Logitech's tool or Solaar; OpenLogi drives the device from then on.

Can I import my Options+ settings?

Not yet, though an importer is in progress. In the meantime, bindings are a short TOML file you can rebuild in minutes, and unlike Options+ they stay in one portable, hand-editable file.

Why does macOS ask for Accessibility permission?

OpenLogi remaps the side buttons (Back, Forward, middle click) through a CGEventTap, and macOS puts event taps behind the Accessibility permission. The HID++ paths (gesture button, thumb wheel, DPI, SmartShift) don't need it.

How do updates work?

Only when you ask. The in-app update check is opt-in and off by default; new builds come from Homebrew (brew upgrade --cask openlogi) or the signed installers on the releases page.

Do my bindings move to another machine?

Copy the TOML file. Devices are keyed by physical identity (receiver serial and slot, or the device's own serial), so the same mouse keeps its bindings wherever the file goes. Built-in sync may come one day, but it's hard to square with the no-account principle.
