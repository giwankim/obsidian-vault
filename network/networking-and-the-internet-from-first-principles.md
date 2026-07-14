---
title: "Networking and the Internet, from First Principles"
source: "https://fazamhd.com/mental-models/networking/"
author:
published: 2026-07-11
created: 2026-07-13
description: "How controlled disturbances of electricity, light, and radio, cooperatively routed across a web of independent networks, deliver data across the world in milliseconds."
tags:
  - "clippings"
---

> [!summary]
> A first-principles walkthrough of how the internet works, tracing networking history from the telegraph and circuit-switched telephone calls to packet switching, ARPANET, and Ethernet. It then builds up the modern protocol stack layer by layer — IP addressing and routing, TCP reliability, BGP, NAT and home networks, DNS, HTTP, and TLS encryption. The article closes by assembling everything into a single mental model of what actually happens, step by step, when you click a link.

Have you ever wondered what happens when we text, call, or video chat with a friend or a colleague on another continent, and their reply arrives in a fraction of a second, as though they were in the same room? Behind the scenes, a chain of invisible conversions takes place: your voice, video, or message is translated into radio waves crossing the room to your Wi-Fi router, then electrical pulses in copper (or light, if you have a fiber connection), and then flashes of light inside a glass strand thinner than a hair lying deep on the ocean floor, only for the entire sequence to play in reverse at the other end. I find it mind-boggling that we can communicate instantly with anyone in the world by doing nothing more than creating controlled, patterned disturbances of electricity, light, and radio.

The message passes through equipment owned by dozens of independent companies in different countries. None of them coordinated with the others specifically for this message transfer, and none of them knows the full path your data took, they just hand it off to the next closest route. There is no central computer directing the traffic, and no single company owns the internet infrastructure. Yet it works, billions of times every second, so reliably that we only notice it when a call stutters or video buffers.

sending a message over the Internet

Connection:

t = 0.3 ms2/6 · across the room

<svg viewBox="0 0 760 232" preserveAspectRatio="xMidYMid meet" aria-hidden="true"><g opacity="1"><g><g><rect x="87.12" y="74" width="45.760000000000005" height="88" rx="7.04" fill="currentColor" stroke="currentColor" stroke-width="1.6" vector-effect="non-scaling-stroke"></rect><rect x="91.12" y="81" width="37.760000000000005" height="70" rx="2" fill="none" stroke="currentColor" stroke-width="1" vector-effect="non-scaling-stroke"></rect><line x1="105" y1="157" x2="115" y2="157" stroke="currentColor" stroke-width="1"></line><text x="110" y="177" text-anchor="middle" font-size="10" fill="currentColor">your phone</text></g> <circle cx="118" cy="104" r="71.82545454545445" fill="none" stroke="currentColor" stroke-width="1" opacity="0.10223181818181877"></circle><circle cx="118" cy="104" r="18.492121212121102" fill="none" stroke="currentColor" stroke-width="1" opacity="0.4022318181818188"></circle><circle cx="118" cy="104" r="45.15878787878776" fill="none" stroke="currentColor" stroke-width="1" opacity="0.25223181818181883"></circle><g><rect x="603" y="114" width="38" height="16" rx="2" fill="currentColor" stroke="currentColor" stroke-width="1.4" vector-effect="non-scaling-stroke"></rect><line x1="613" y1="114" x2="608" y2="98" stroke="currentColor" stroke-width="1.2"></line><circle cx="608" cy="97" r="1.6" fill="currentColor"></circle><line x1="631" y1="114" x2="636" y2="98" stroke="currentColor" stroke-width="1.2"></line><circle cx="636" cy="97" r="1.6" fill="currentColor"></circle><text x="622" y="144" text-anchor="middle" font-size="10" fill="currentColor">your router</text></g> <g><g><rect x="227.18711551606265" y="102.98221666023802" width="8" height="8" fill="currentColor" stroke="currentColor" stroke-width="0.8" vector-effect="non-scaling-stroke"></rect><rect x="207.61211551606266" y="102.86947772151295" width="8" height="8" fill="currentColor" stroke="currentColor" stroke-width="0.8" vector-effect="non-scaling-stroke"></rect><rect x="188.03711551606264" y="102.29247104467466" width="8" height="8" fill="currentColor" stroke="currentColor" stroke-width="0.8" vector-effect="non-scaling-stroke"></rect></g><g><line x1="231.18711551606265" y1="98.98221666023802" x2="154.18711551606265" y2="67" stroke="currentColor" stroke-width="1"></line><line x1="231.18711551606265" y1="98.98221666023802" x2="308.18711551606265" y2="67" stroke="currentColor" stroke-width="1"></line><circle cx="231.18711551606265" cy="106.98221666023802" r="8" fill="none" stroke="currentColor" stroke-width="1.2"></circle><rect x="140.18711551606265" y="9" width="182" height="58" rx="3" fill="currentColor" stroke="currentColor" stroke-width="1.2" vector-effect="non-scaling-stroke"></rect><polyline points="153.2,37.1 154.4,41.4 155.6,41.4 156.8,37.0 158.0,30.1 159.2,28.6 160.4,27.6 161.6,27.9 162.8,29.6 164.0,31.8 165.2,33.7 166.4,34.5 167.6,33.8 168.8,31.9 170.0,29.6 171.2,28.0 172.4,27.5 173.6,28.6 174.8,30.6 176.0,32.8 177.2,34.3 178.4,34.3 179.6,33.0 180.8,30.8 182.0,28.7 183.2,27.6 184.4,27.9 185.6,26.2 186.8,33.3 188.0,39.4 189.2,42.0 190.4,39.9 191.6,34.1 192.8,27.0 194.0,21.6 195.2,20.1 196.4,23.2 197.6,30.5 198.8,32.8 200.0,34.2 201.2,34.4 202.4,33.1 203.6,30.9 204.8,28.8 206.0,27.6 207.2,27.8 208.4,29.4 209.6,31.7 210.8,39.2 212.0,42.0 213.2,40.1 214.4,34.4 215.6,27.3 216.8,21.7 218.0,20.0 219.2,23.0 220.4,29.3 221.6,36.3 222.8,41.1 224.0,41.7 225.2,37.7 226.4,31.0 227.6,24.2 228.8,20.3 230.0,20.9 231.2,25.7 232.4,32.8 233.6,39.0 234.8,42.0 236.0,40.3 237.2,34.7 238.4,27.6 239.6,21.9 240.8,20.0 242.0,22.8 243.2,29.0 244.4,36.1 245.6,41.0 246.8,41.7 248.0,38.0 249.2,31.3 250.4,28.9 251.6,27.6 252.8,27.8 254.0,29.2 255.2,31.5 256.4,33.5 257.6,34.5 258.8,34.0 260.0,32.3 261.2,30.0 262.4,28.1 263.6,20.0 264.8,22.6 266.0,28.7 267.2,35.8 268.4,40.9 269.6,41.8 270.8,38.2 272.0,31.6 273.2,24.7 274.4,20.5 275.6,27.7 276.8,29.2 278.0,31.4 279.2,33.4 280.4,34.5 281.6,34.0 282.8,32.3 284.0,30.1 285.2,28.2 286.4,27.5 287.6,28.3 288.8,30.2 290.0,32.4 291.2,34.1 292.4,34.4 293.6,33.4 294.8,31.3 296.0,29.1 297.2,27.7 298.4,27.7 299.6,29.1 300.8,31.3 302.0,38.4 303.2,41.8 304.4,40.7 305.6,35.5 306.8,28.4 308.0,22.4 309.2,20.0" fill="none" stroke="currentColor" stroke-width="1.3" vector-effect="non-scaling-stroke"></polyline><text x="231.18711551606265" y="59" text-anchor="middle" font-size="9" fill="currentColor">the bytes, as a shaped radio wave</text></g></g></g></g></svg>

Radio waves carry the bytes across the room to your router in about a millisecond.

Radio to your router, copper and fiber across your city, light in a submarine cable, a data center at the far end, and a separate, often different path back for the reply. The faint dots are everyone else's traffic; every wire, cable, and machine here is shared by millions of conversations at once. How this can possibly work with nobody in charge is the subject of this article.

The [software article](https://fazamhd.com/mental-models/software) followed the story of a single machine, from electrons in silicon up to the software you run. This article follows the story of the connections between those machines. Like the layers of computing, the internet was not designed in one stroke; it accumulated over decades, and each protocol makes sense only once you see the concrete limitation it was invented to fix. It is easy to mistake the result for something engineered to a finished blueprint, because failures are rare enough to feel like the system was always this reliable. In reality, every mechanism in this article, packet switching, TCP, DNS, and TLS, was a patch for a specific problem, deployed decades after the internet already “worked”, and the pressure that produced them hasn’t stopped: it now comes from new physical links, new failure scenarios, and new demands from software that didn’t exist when the layer beneath it was designed.

My aim is to build this understanding from first principles. By the end, many of the everyday mysteries of using the internet will make intuitive sense under a single, coherent mental model: how the padlock in your address bar protects your credit card details, whether a dead page is the website’s fault or a failure at your own end, why a webpage can feel sluggish even on a “gigabit” connection, and how your data dynamically reroutes around a failing undersea cable half a world away.

## We Were Sending Bits Even Before Computers Existed

Networking is much older than computing, and older than electricity too. The word **network** itself originally meant exactly what it sounds like, a net-like fabric of threads or cords crossing at regular intervals. In the early 19th century, engineers borrowed the term to describe interconnected transit routes like canals and railways. When the electrical telegraph arrived in the 1840s, the word drifted naturally to describe the systems of wires and stations that carried its signals.

Yet the basic physical principle of a network link remains the same as the simplest mechanical connection. Knot a string tight between two tin cans, speak into one, and the string carries the vibration of your voice to the other as mechanical motion with no amplifier or relay, just a wave losing energy to friction and slack with every meter it crosses. That is already the whole principle behind every link built since, vary a physical quantity at one end and measure it at the other. What the string can’t do is carry a signal any real distance without it dying in the line. The telegraph’s true breakthrough wasn’t just replacing string with electrical wire, but overcoming this physical limit of distance.

In 1844, Samuel Morse sent the message “What hath God wrought” from Washington to Baltimore over a copper wire, using Morse code, a system of short and long electrical pulses. Notice what the telegraph actually was, a **digital** network. It did not transmit the sound of a voice; it transmitted discrete symbols from a fixed alphabet. That choice had an advantage the Victorians understood well. An electromechanical relay along the line didn’t need to pass the wave itself; it only needed to detect whether a pulse was present, and then recreate a brand new, clean copy of that pulse to send down the next segment of wire. Discrete symbols plus regeneration meant a message could cross a continent without degrading, something no analog signal could do.

Notice also what had to exist before the wire could carry anything, an agreement between sender and receiver. The telegraph only worked because both ends held the same table in advance, which pulses stood for which letters, and how operators signaled “received” or “repeat.” This shared rulebook is a **protocol**. Every protocol in this article (IP, TCP, DNS, TLS) is the same, a published agreement on message formats and who says what when, allowing independent machines to communicate with each other.

The simulator below sends Morse’s message down that historic line. Watch the pulses fade and pick up noise along each span of wire, and what the relays do about it, then switch the relays to bare amplification and see why the discrete alphabet (which modern computing simplified even further into binary bits) was such a smart choice.

telegraph relaydiscrete symbols, regenerated at each relay

<svg viewBox="0 0 800 270" preserveAspectRatio="xMidYMid meet" aria-hidden="true"><line x1="80" y1="104" x2="720" y2="104" stroke="currentColor" stroke-width="1"></line><polyline points="80.0,73.9 82.5,74.1 85.0,103.4 87.5,103.7 90.0,104.4 92.5,104.2 95.0,75.5 97.5,76.1 100.0,75.2 102.5,75.1 105.0,103.8 107.5,103.2 110.0,104.0 112.5,105.1 115.0,77.1 117.5,77.5 120.0,77.5 122.5,76.0 125.0,103.2 127.5,103.7 130.0,103.3 132.5,105.2 135.0,105.4 137.5,104.1 140.0,104.7 142.5,103.2 145.0,101.9 147.5,103.8 150.0,103.9 152.5,104.1 155.0,82.1 157.5,81.1 160.0,79.5 162.5,80.3 165.0,79.1 167.5,78.4 170.0,81.5 172.5,82.6 175.0,81.9 177.5,83.6 180.0,82.9 182.5,79.7 185.0,102.2 187.5,103.5 190.0,102.6 192.5,104.6 195.0,86.3 197.5,84.4 200.0,82.9 202.5,83.8 205.0,81.5 207.5,80.5 210.0,84.6 212.5,85.6 215.0,85.2 217.5,87.9 220.0,86.2 222.5,82.4 225.0,102.7 227.5,102.2 230.0,101.3 232.5,106.3 235.0,88.8 237.5,87.1 240.0,89.1 242.5,85.5 245.0,100.0 247.5,103.1 250.0,101.9 252.5,103.8 255.0,108.6 257.5,105.7 260.0,105.0 262.5,105.2 265.0,99.6 267.5,100.8 270.0,104.1 272.5,102.7 275.0,107.0 277.5,109.1 280.0,103.8 282.5,103.7 285.0,103.1 287.5,98.4 290.0,101.9 292.5,106.6 295.0,104.1 297.5,104.3 300.0,104.5 302.5,103.8 305.0,103.5 307.5,103.8 310.0,103.6 312.5,103.7 315.0,104.8 317.5,104.8 320.0,104.0 322.5,104.2 325.0,103.8 327.5,102.6 330.0,103.5 332.5,104.5 335.0,104.1 337.5,104.9 340.0,105.4 342.5,103.6 345.0,103.1 347.5,103.6 350.0,102.5 352.5,103.6 355.0,105.6 357.5,104.6 360.0,105.0 362.5,105.0 365.0,102.4 367.5,102.7 370.0,103.5 372.5,102.7 375.0,105.3 377.5,106.1 380.0,104.3 382.5,105.2 385.0,103.4 387.5,101.2 390.0,103.4 392.5,103.4 395.0,103.9 397.5,107.0 400.0,105.5 402.5,103.7 405.0,104.4 407.5,101.8 410.0,101.0 412.5,104.6 415.0,104.7 417.5,104.8 420.0,107.4 422.5,105.1 425.0,101.7 427.5,102.8 430.0,102.5 432.5,101.3 435.0,105.3 437.5,107.6 440.0,105.0 442.5,105.0 445.0,105.0 447.5,100.6 450.0,100.4 452.5,104.4 455.0,104.2 457.5,104.9 460.0,108.5 462.5,105.6 465.0,101.6 467.5,103.1 470.0,101.4 472.5,100.3 475.0,106.0 477.5,106.9 480.0,105.2 482.5,107.7 485.0,103.8 487.5,99.5 490.0,102.7 492.5,101.5 495.0,102.6 497.5,108.9 500.0,106.5 502.5,105.3 505.0,106.3 507.5,103.6 510.0,103.6 512.5,104.0 515.0,103.7 517.5,104.3 520.0,104.8 522.5,104.1 525.0,104.1 527.5,103.9 530.0,102.9 532.5,103.6 535.0,104.3 537.5,104.0 540.0,104.9 542.5,105.1 545.0,103.6 547.5,103.4 550.0,103.6 552.5,102.7 555.0,103.6 557.5,105.3 560.0,104.8 562.5,104.4 565.0,105.0 567.5,103.4 570.0,102.0 572.5,103.5 575.0,104.0 577.5,103.8 580.0,105.7 582.5,106.0 585.0,103.5 587.5,103.4 590.0,103.4 592.5,101.6 595.0,103.3 597.5,105.8 600.0,104.7 602.5,105.5 605.0,105.8 607.5,102.3 610.0,102.2 612.5,103.3 615.0,102.0 617.5,105.0 620.0,106.8 622.5,104.6 625.0,105.6 627.5,104.0 630.0,100.6 632.5,102.9 635.0,103.1 637.5,103.2 640.0,107.4 642.5,106.1 645.0,104.1 647.5,105.1 650.0,101.4 652.5,100.4 655.0,104.3 657.5,103.9 660.0,105.0 662.5,108.4 665.0,105.1 667.5,102.2 670.0,103.5 672.5,101.1 675.0,100.5 677.5,105.8 680.0,106.8 682.5,105.0 685.0,107.0 687.5,105.1 690.0,99.7 692.5,101.0 695.0,103.7 697.5,102.4 700.0,105.6 702.5,109.5 705.0,105.4 707.5,102.6 710.0,103.9 712.5,100.2 715.0,99.4 717.5,105.8 720.0,106.4" fill="none" stroke="currentColor" stroke-width="1.4" vector-effect="non-scaling-stroke"></polyline><g><rect x="73" y="97" width="14" height="14" fill="currentColor" stroke="currentColor" stroke-width="1.8" vector-effect="non-scaling-stroke"></rect><text x="80" y="134" text-anchor="middle" font-size="11" fill="currentColor">Washington</text> <text x="80" y="148" text-anchor="middle" font-size="10" fill="currentColor">keying H</text></g> <g><rect x="286.33333333333337" y="97" width="14" height="14" fill="currentColor" stroke="currentColor" stroke-width="1.2" vector-effect="non-scaling-stroke"></rect><text x="293.33333333333337" y="134" text-anchor="middle" font-size="11" fill="currentColor">relay station</text> <text x="293.33333333333337" y="148" text-anchor="middle" font-size="10" fill="currentColor">regenerates</text></g> <g><rect x="499.6666666666667" y="97" width="14" height="14" fill="currentColor" stroke="currentColor" stroke-width="1.2" vector-effect="non-scaling-stroke"></rect><text x="506.6666666666667" y="134" text-anchor="middle" font-size="11" fill="currentColor">relay station</text> <text x="506.6666666666667" y="148" text-anchor="middle" font-size="10" fill="currentColor">regenerates</text></g> <g><rect x="713" y="97" width="14" height="14" fill="currentColor" stroke="currentColor" stroke-width="1.8" vector-effect="non-scaling-stroke"></rect><text x="720" y="134" text-anchor="middle" font-size="11" fill="currentColor">Baltimore</text></g> <text x="186.66666666666669" y="52" text-anchor="middle" font-size="10" fill="currentColor">pulses fade, noise creeps in →</text> <g><line x1="154.26799999999974" y1="116" x2="243.36799999999974" y2="116" stroke="currentColor" stroke-width="1" vector-effect="non-scaling-stroke"></line><line x1="154.26799999999974" y1="113" x2="154.26799999999974" y2="116" stroke="currentColor" stroke-width="1" vector-effect="non-scaling-stroke"></line><line x1="243.36799999999974" y1="113" x2="243.36799999999974" y2="116" stroke="currentColor" stroke-width="1" vector-effect="non-scaling-stroke"></line><text x="198.81799999999976" y="128" text-anchor="middle" font-size="11" font-family="ui-monospace, monospace" fill="currentColor">W</text></g> <g><line x1="80" y1="116" x2="124.56799999999973" y2="116" stroke="currentColor" stroke-width="1" vector-effect="non-scaling-stroke"></line><line x1="80" y1="113" x2="80" y2="116" stroke="currentColor" stroke-width="1" vector-effect="non-scaling-stroke"></line><line x1="124.56799999999973" y1="113" x2="124.56799999999973" y2="116" stroke="currentColor" stroke-width="1" vector-effect="non-scaling-stroke"></line><text x="102.28399999999986" y="128" text-anchor="middle" font-size="11" font-family="ui-monospace, monospace" fill="currentColor">H</text></g> <g font-family="ui-monospace, monospace" font-size="13"><text x="73" y="192" font-size="10" fill="currentColor">SENT FROM WASHINGTON</text> <text x="73" y="212" fill="currentColor" text-decoration="none">W</text> <text x="84" y="212" fill="currentColor" text-decoration="underline">H</text> <text x="95" y="212" fill="currentColor" text-decoration="none">A</text> <text x="106" y="212" fill="currentColor" text-decoration="none">T</text> <text x="128" y="212" fill="currentColor" text-decoration="none">H</text> <text x="139" y="212" fill="currentColor" text-decoration="none">A</text> <text x="150" y="212" fill="currentColor" text-decoration="none">T</text> <text x="161" y="212" fill="currentColor" text-decoration="none">H</text> <text x="183" y="212" fill="currentColor" text-decoration="none">G</text> <text x="194" y="212" fill="currentColor" text-decoration="none">O</text> <text x="205" y="212" fill="currentColor" text-decoration="none">D</text> <text x="227" y="212" fill="currentColor" text-decoration="none">W</text> <text x="238" y="212" fill="currentColor" text-decoration="none">R</text> <text x="249" y="212" fill="currentColor" text-decoration="none">O</text> <text x="260" y="212" fill="currentColor" text-decoration="none">U</text> <text x="271" y="212" fill="currentColor" text-decoration="none">G</text> <text x="282" y="212" fill="currentColor" text-decoration="none">H</text> <text x="293" y="212" fill="currentColor" text-decoration="none">T</text> <text x="73" y="238" font-size="10" fill="currentColor">RECEIVED AT BALTIMORE</text></g></svg>

An electromechanical relay along the line didn't need to pass the wave itself; it only needed to detect whether a pulse was present, and then recreate a brand new, clean copy of that pulse to send down the next segment of wire.

relays

Morse pulses fade and pick up noise along every span of wire. Because the network transmits discrete symbols, a relay doesn't need to pass the wave itself; it only needs to detect whether a pulse is present, and recreate a brand new, clean copy of that pulse. Switch the relays to bare amplification and the noise of each span rides into the next, until Baltimore misreads the message. Discrete symbols plus regeneration is why a message could cross a continent without degrading, something no analog signal could do.

The telegraph network even solved routing, with people. A message from a small town to another small town passed through relay offices, where operators received it, punched it onto paper tape, and retransmitted it down whichever outgoing line led closer to the destination when that line became free. Messages queued in bins during busy hours. Hold onto this idea, a hundred years later we will rebuild it with electronics and call it a router.

![Engraving of the operators' room at the central telegraph exchange in Paris, dozens of operators working telegraph instruments at rows of tables](https://fazamhd.com/_astro/telegraph-operating-room.ot-zxkfk.jpg)

The operators’ room of the great telegraph exchange in Paris, 1890s. Every table ends a line; the operators receiving, queuing, and retransmitting messages toward their destinations were the network’s routers. (Source: Popular Science Monthly, 1894, public domain)

Morse’s own line only had to cross one state. Crossing an ocean took longer, requiring a decade of costly setbacks and a painful education in the physics of underwater cables. Cyrus Field’s first transatlantic telegraph cable went live in August 1858, carrying a congratulatory exchange between Queen Victoria and President Buchanan; three weeks later it was dead, its insulation damaged in handling and, some think, finished off by an engineer’s overvoltage trying to push a signal through it. The successful cable came in 1866, laid by the SS Great Eastern, at the time the largest ship ever built and the only one that could carry the roughly 4,000 kilometers of cable in a single piece. The ocean floor has carried communication cables ever since, a story we will return to when telegraph wires evolve into coaxial copper and, eventually, glass fiber.

The underlying trick generalizes to every link ever built since. To move **bits** between two points, you vary some physical quantity at one end and measure it at the other, on an agreed schedule. A bit, short for “binary digit,” is the smallest possible piece of information there is, a single choice between exactly two states, conventionally written `1` or `0`, and everything this article measures, sends, or stores is ultimately some number of these (the [software article](https://fazamhd.com/mental-models/software) builds this up from transistors and logic gates, if you want to understand that too). Group eight of them together and you have a **byte**, enough states, 256 of them, to stand for one character of text or one small number, which is why sizes throughout this article, a packet header, a frame, a file, all get counted in bytes rather than bits.

Put voltage on a wire for a `1`, leave it off for a `0`, measure a million times per second, and the wire carries a million bits per second. Optical fiber does it by switching a laser on and off inside the glass strand, light for a `1`, darkness for a `0`, millions of times per second; Wi-Fi does it by varying the shape of a radio wave (how exactly is the subject of the upcoming wireless article).

Two numbers characterize every such link, and keeping them separate resolves a lot of everyday confusion.

- **Bandwidth** is how many bits per second the link carries.
- **Latency** is how long one bit takes to get from one end to the other.

Bandwidth is an engineering problem, and engineers keep winning it. A single modern fiber strand carries terabits per second by sending many wavelengths of light at once. Latency is physics, light in glass covers about 200,000 kilometers per second, two-thirds of its speed in vacuum, so New York to London has a hard floor of roughly 28 milliseconds one way (twice that for a round trip) that no amount of money or engineering can lower. This is why a video stream and a video call feel so different, the stream needs bandwidth and tolerates latency (it buffers seconds ahead), while the call needs low latency and only modest bandwidth. When a page feels slow on a fast connection, latency is usually the culprit. As we’ll see later, a single page load requires multiple round trips (for DNS, TCP, and TLS) before any content actually starts moving.

The two numbers never trade off against each other, because they come from different places, bandwidth from the sender’s schedule, latency from the wire’s length. The simulator below sends the same 8 bits down one link, adjust the bandwidth and only the spacing between pulses changes, adjust the distance and only the delay before the first pulse arrives changes.

bandwidth and latency in signal propagationdrag to seek

<svg viewBox="0 0 760 190" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Slowed replay of one byte of pulses crossing a link; drag horizontally to seek through the replay" style="cursor:pointer"><line x1="70" y1="55" x2="530" y2="55" stroke="currentColor" stroke-width="5" stroke-linecap="round" opacity="0.35"></line><line x1="70" y1="55" x2="530" y2="55" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"></line><line x1="70" y1="55" x2="530" y2="55" stroke="currentColor" stroke-width="1" stroke-dasharray="2,3" opacity="0.6"></line><circle cx="70" cy="55" r="14" fill="currentColor" opacity="0.08"></circle><circle cx="70" cy="55" r="5.5" fill="currentColor"></circle><circle cx="530" cy="55" r="5.5" fill="currentColor"></circle><path d="M 70.0,55.0 L 72.3,55.0 L 74.6,55.0 L 76.9,55.0 L 79.2,55.0 L 81.5,55.0 L 83.8,55.0 L 86.1,51.9 L 88.4,38.9 L 90.7,35.0 L 93.0,35.0 L 95.3,35.0 L 97.6,35.0 L 99.9,35.0 L 102.2,35.0 L 104.5,35.0 L 106.8,35.0 L 109.1,35.0 L 111.4,35.0 L 113.7,35.0 L 116.0,35.0 L 118.3,35.0 L 120.6,35.0 L 122.9,35.0 L 125.2,35.0 L 127.5,35.0 L 129.8,35.0 L 132.1,35.0 L 134.4,35.0 L 136.7,35.0 L 139.0,35.0 L 141.3,35.0 L 143.6,35.0 L 145.9,35.0 L 148.2,42.2 L 150.5,54.1 L 152.8,55.0 L 155.1,55.0 L 157.4,55.0 L 159.7,55.0 L 162.0,55.0 L 164.3,55.0 L 166.6,55.0 L 168.9,55.0 L 171.2,55.0 L 173.5,55.0 L 175.8,55.0 L 178.1,51.9 L 180.4,38.9 L 182.7,35.0 L 185.0,35.0 L 187.3,35.0 L 189.6,35.0 L 191.9,35.0 L 194.2,35.0 L 196.5,35.0 L 198.8,35.0 L 201.1,35.0 L 203.4,35.0 L 205.7,35.0 L 208.0,35.5 L 210.3,46.8 L 212.6,55.0 L 214.9,55.0 L 217.2,55.0 L 219.5,55.0 L 221.8,55.0 L 224.1,55.0 L 226.4,55.0 L 228.7,55.0 L 231.0,55.0 L 233.3,55.0 L 235.6,55.0 L 237.9,55.0 L 240.2,55.0 L 242.5,55.0 L 244.8,55.0 L 247.1,55.0 L 249.4,55.0 L 251.7,55.0 L 254.0,55.0 L 256.3,55.0 L 258.6,55.0 L 260.9,55.0 L 263.2,55.0 L 265.5,55.0 L 267.8,55.0 L 270.1,55.0 L 272.4,55.0 L 274.7,55.0 L 277.0,55.0 L 279.3,55.0 L 281.6,55.0 L 283.9,55.0 L 286.2,55.0 L 288.5,55.0 L 290.8,55.0 L 293.1,55.0 L 295.4,55.0 L 297.7,55.0 L 300.0,55.0 L 302.3,55.0 L 304.6,55.0 L 306.9,55.0 L 309.2,55.0 L 311.5,55.0 L 313.8,55.0 L 316.1,55.0 L 318.4,55.0 L 320.7,55.0 L 323.0,55.0 L 325.3,55.0 L 327.6,55.0 L 329.9,55.0 L 332.2,55.0 L 334.5,55.0 L 336.8,55.0 L 339.1,55.0 L 341.4,55.0 L 343.7,55.0 L 346.0,55.0 L 348.3,55.0 L 350.6,55.0 L 352.9,55.0 L 355.2,55.0 L 357.5,55.0 L 359.8,55.0 L 362.1,55.0 L 364.4,55.0 L 366.7,55.0 L 369.0,55.0 L 371.3,55.0 L 373.6,55.0 L 375.9,55.0 L 378.2,55.0 L 380.5,55.0 L 382.8,55.0 L 385.1,55.0 L 387.4,55.0 L 389.7,55.0 L 392.0,55.0 L 394.3,55.0 L 396.6,55.0 L 398.9,55.0 L 401.2,55.0 L 403.5,55.0 L 405.8,55.0 L 408.1,55.0 L 410.4,55.0 L 412.7,55.0 L 415.0,55.0 L 417.3,55.0 L 419.6,55.0 L 421.9,55.0 L 424.2,55.0 L 426.5,55.0 L 428.8,55.0 L 431.1,55.0 L 433.4,55.0 L 435.7,55.0 L 438.0,55.0 L 440.3,55.0 L 442.6,55.0 L 444.9,55.0 L 447.2,55.0 L 449.5,55.0 L 451.8,55.0 L 454.1,55.0 L 456.4,55.0 L 458.7,55.0 L 461.0,55.0 L 463.3,55.0 L 465.6,55.0 L 467.9,55.0 L 470.2,55.0 L 472.5,55.0 L 474.8,55.0 L 477.1,55.0 L 479.4,55.0 L 481.7,55.0 L 484.0,55.0 L 486.3,55.0 L 488.6,55.0 L 490.9,55.0 L 493.2,55.0 L 495.5,55.0 L 497.8,55.0 L 500.1,55.0 L 502.4,55.0 L 504.7,55.0 L 507.0,55.0 L 509.3,55.0 L 511.6,55.0 L 513.9,55.0 L 516.2,55.0 L 518.5,55.0 L 520.8,55.0 L 523.1,55.0 L 525.4,55.0 L 527.7,55.0 L 530.0,55.0" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" opacity="0.1"></path><path d="M 70.0,55.0 L 72.3,55.0 L 74.6,55.0 L 76.9,55.0 L 79.2,55.0 L 81.5,55.0 L 83.8,55.0 L 86.1,51.9 L 88.4,38.9 L 90.7,35.0 L 93.0,35.0 L 95.3,35.0 L 97.6,35.0 L 99.9,35.0 L 102.2,35.0 L 104.5,35.0 L 106.8,35.0 L 109.1,35.0 L 111.4,35.0 L 113.7,35.0 L 116.0,35.0 L 118.3,35.0 L 120.6,35.0 L 122.9,35.0 L 125.2,35.0 L 127.5,35.0 L 129.8,35.0 L 132.1,35.0 L 134.4,35.0 L 136.7,35.0 L 139.0,35.0 L 141.3,35.0 L 143.6,35.0 L 145.9,35.0 L 148.2,42.2 L 150.5,54.1 L 152.8,55.0 L 155.1,55.0 L 157.4,55.0 L 159.7,55.0 L 162.0,55.0 L 164.3,55.0 L 166.6,55.0 L 168.9,55.0 L 171.2,55.0 L 173.5,55.0 L 175.8,55.0 L 178.1,51.9 L 180.4,38.9 L 182.7,35.0 L 185.0,35.0 L 187.3,35.0 L 189.6,35.0 L 191.9,35.0 L 194.2,35.0 L 196.5,35.0 L 198.8,35.0 L 201.1,35.0 L 203.4,35.0 L 205.7,35.0 L 208.0,35.5 L 210.3,46.8 L 212.6,55.0 L 214.9,55.0 L 217.2,55.0 L 219.5,55.0 L 221.8,55.0 L 224.1,55.0 L 226.4,55.0 L 228.7,55.0 L 231.0,55.0 L 233.3,55.0 L 235.6,55.0 L 237.9,55.0 L 240.2,55.0 L 242.5,55.0 L 244.8,55.0 L 247.1,55.0 L 249.4,55.0 L 251.7,55.0 L 254.0,55.0 L 256.3,55.0 L 258.6,55.0 L 260.9,55.0 L 263.2,55.0 L 265.5,55.0 L 267.8,55.0 L 270.1,55.0 L 272.4,55.0 L 274.7,55.0 L 277.0,55.0 L 279.3,55.0 L 281.6,55.0 L 283.9,55.0 L 286.2,55.0 L 288.5,55.0 L 290.8,55.0 L 293.1,55.0 L 295.4,55.0 L 297.7,55.0 L 300.0,55.0 L 302.3,55.0 L 304.6,55.0 L 306.9,55.0 L 309.2,55.0 L 311.5,55.0 L 313.8,55.0 L 316.1,55.0 L 318.4,55.0 L 320.7,55.0 L 323.0,55.0 L 325.3,55.0 L 327.6,55.0 L 329.9,55.0 L 332.2,55.0 L 334.5,55.0 L 336.8,55.0 L 339.1,55.0 L 341.4,55.0 L 343.7,55.0 L 346.0,55.0 L 348.3,55.0 L 350.6,55.0 L 352.9,55.0 L 355.2,55.0 L 357.5,55.0 L 359.8,55.0 L 362.1,55.0 L 364.4,55.0 L 366.7,55.0 L 369.0,55.0 L 371.3,55.0 L 373.6,55.0 L 375.9,55.0 L 378.2,55.0 L 380.5,55.0 L 382.8,55.0 L 385.1,55.0 L 387.4,55.0 L 389.7,55.0 L 392.0,55.0 L 394.3,55.0 L 396.6,55.0 L 398.9,55.0 L 401.2,55.0 L 403.5,55.0 L 405.8,55.0 L 408.1,55.0 L 410.4,55.0 L 412.7,55.0 L 415.0,55.0 L 417.3,55.0 L 419.6,55.0 L 421.9,55.0 L 424.2,55.0 L 426.5,55.0 L 428.8,55.0 L 431.1,55.0 L 433.4,55.0 L 435.7,55.0 L 438.0,55.0 L 440.3,55.0 L 442.6,55.0 L 444.9,55.0 L 447.2,55.0 L 449.5,55.0 L 451.8,55.0 L 454.1,55.0 L 456.4,55.0 L 458.7,55.0 L 461.0,55.0 L 463.3,55.0 L 465.6,55.0 L 467.9,55.0 L 470.2,55.0 L 472.5,55.0 L 474.8,55.0 L 477.1,55.0 L 479.4,55.0 L 481.7,55.0 L 484.0,55.0 L 486.3,55.0 L 488.6,55.0 L 490.9,55.0 L 493.2,55.0 L 495.5,55.0 L 497.8,55.0 L 500.1,55.0 L 502.4,55.0 L 504.7,55.0 L 507.0,55.0 L 509.3,55.0 L 511.6,55.0 L 513.9,55.0 L 516.2,55.0 L 518.5,55.0 L 520.8,55.0 L 523.1,55.0 L 525.4,55.0 L 527.7,55.0 L 530.0,55.0" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"></path><text x="58" y="59" text-anchor="end" font-size="10.5" font-weight="bold" fill="currentColor">Tx (Sender)</text> <text x="542" y="59" text-anchor="start" font-size="10.5" font-weight="bold" fill="currentColor">Rx (Receiver)</text> <g><rect x="70.5" y="10" width="13" height="17" rx="2" fill="none" stroke="currentColor" stroke-width="1"></rect><text x="77" y="22" text-anchor="middle" font-size="9.5" font-weight="normal" fill="currentColor">1</text></g> <g><rect x="84.5" y="10" width="13" height="17" rx="2" fill="none" stroke="currentColor" stroke-width="1"></rect><text x="91" y="22" text-anchor="middle" font-size="9.5" font-weight="normal" fill="currentColor">0</text></g> <g><rect x="98.5" y="10" width="13" height="17" rx="2" fill="none" stroke="currentColor" stroke-width="1"></rect><text x="105" y="22" text-anchor="middle" font-size="9.5" font-weight="normal" fill="currentColor">1</text></g> <g><rect x="112.5" y="10" width="13" height="17" rx="2" fill="none" stroke="currentColor" stroke-width="1"></rect><text x="119" y="22" text-anchor="middle" font-size="9.5" font-weight="normal" fill="currentColor">1</text></g> <g><rect x="126.5" y="10" width="13" height="17" rx="2" fill="currentColor" stroke="none" stroke-width="1"></rect><text x="133" y="22" text-anchor="middle" font-size="9.5" font-weight="bold" fill="currentColor">0</text></g> <g><rect x="140.5" y="10" width="13" height="17" rx="2" fill="none" stroke="currentColor" stroke-width="1"></rect><text x="147" y="22" text-anchor="middle" font-size="9.5" font-weight="normal" fill="currentColor">0</text></g> <g><rect x="154.5" y="10" width="13" height="17" rx="2" fill="none" stroke="currentColor" stroke-width="1"></rect><text x="161" y="22" text-anchor="middle" font-size="9.5" font-weight="normal" fill="currentColor">1</text></g> <g><rect x="168.5" y="10" width="13" height="17" rx="2" fill="none" stroke="currentColor" stroke-width="1"></rect><text x="175" y="22" text-anchor="middle" font-size="9.5" font-weight="normal" fill="currentColor">0</text></g> <g><rect x="418.5" y="83" width="13" height="17" rx="2" fill="none" stroke="currentColor" stroke-width="1" stroke-dasharray="2,2"></rect></g><g><rect x="432.5" y="83" width="13" height="17" rx="2" fill="none" stroke="currentColor" stroke-width="1" stroke-dasharray="2,2"></rect></g><g><rect x="446.5" y="83" width="13" height="17" rx="2" fill="none" stroke="currentColor" stroke-width="1" stroke-dasharray="2,2"></rect></g><g><rect x="460.5" y="83" width="13" height="17" rx="2" fill="none" stroke="currentColor" stroke-width="1" stroke-dasharray="2,2"></rect></g><g><rect x="474.5" y="83" width="13" height="17" rx="2" fill="none" stroke="currentColor" stroke-width="1" stroke-dasharray="2,2"></rect></g><g><rect x="488.5" y="83" width="13" height="17" rx="2" fill="none" stroke="currentColor" stroke-width="1" stroke-dasharray="2,2"></rect></g><g><rect x="502.5" y="83" width="13" height="17" rx="2" fill="none" stroke="currentColor" stroke-width="1" stroke-dasharray="2,2"></rect></g><g><rect x="516.5" y="83" width="13" height="17" rx="2" fill="none" stroke="currentColor" stroke-width="1" stroke-dasharray="2,2"></rect></g><line x1="70" y1="116" x2="590" y2="116" stroke="currentColor" stroke-width="3" stroke-linecap="round"></line><line x1="70" y1="116" x2="210" y2="116" stroke="currentColor" stroke-width="3" stroke-linecap="round"></line><polygon points="210,111 206,105 214,105" fill="currentColor"></polygon><text x="58" y="119" text-anchor="end" font-size="8.5" fill="currentColor">replay</text> <text x="70" y="134" font-size="8.5" letter-spacing="0.08em" fill="currentColor">TOTAL DELIVERY TIME · REAL PROPORTIONS</text> <text x="690" y="134" text-anchor="end" font-size="10" font-weight="bold" fill="currentColor">30.01 ms</text> <rect x="70" y="140" width="618" height="12" fill="none" stroke="currentColor" stroke-width="1.2"></rect><rect x="688" y="140" width="2" height="12" fill="currentColor" opacity="0.85"></rect><rect x="70" y="161" width="9" height="9" fill="none" stroke="currentColor" stroke-width="1.2"></rect><text x="84" y="169" font-size="10" fill="currentColor">propagation (latency): 30 ms</text> <rect x="290" y="161" width="9" height="9" fill="currentColor" opacity="0.85"></rect><text x="304" y="169" font-size="10" fill="currentColor">transmission: 8 μs</text></svg>

Status:Transmitter is keying the bit sequence onto the link.

Analysis:The propagation delay dominates here, latency dwarfs how long sending actually takes.

bandwidth1 Mbps · early broadband

distance6,000 km · transatlantic cable

Bandwidth sets only how wide each pulse is; distance sets only how long the wave takes to slide down the wire. The bar shows the two delays in real proportion, the replay above is slowed and not to scale.

## A Dedicated Circuit for Every Conversation

The telegraph carried text between offices. The telephone, from 1876 onward, carried live voice into homes, and to do it, the network worked on a completely different principle called **circuit switching**. When you placed a call, the system assembled a dedicated electrical path between your telephone and the receiver’s, originally by human operators plugging patch cords into switchboards, later by electromechanical relays doing the same thing automatically. For the duration of the call, that chain of copper belonged exclusively to your conversation, end to end.

![Women working at a Bell System international telephone switchboard, 1943](https://fazamhd.com/_astro/telephone-switchboard.Nt9Xql2T.jpg)

Women working at a Bell System international telephone switchboard, 1943. Human operators manually connected circuit switches by plugging patch cords into switchboards, establishing a temporary dedicated electrical path for each conversation. (Source: U.S. National Archives, Public Domain)

For speech, this is a reasonable design, a phone call is a continuous signal flowing nearly the whole time, so the reserved line is actually used. So when computers first needed to talk over distance in the 1950s and 60s, they did the only thing possible, they dialed each other over phone lines. But because telephone lines were built to carry human voices, analog sound waves, rather than direct digital electrical pulses; computers had to use a **modem** (short for **modulator-demodulator**). The modem translated the computer’s digital binary bits into analog audio tones, audible as the chirps, beeps, and static of a dial-up handshake, that could travel over the voice network, and translated those sounds back into digital bits at the other end.

The earliest modems, like the 300-baud Bell 103, did this with **FSK** (Frequency-Shift Keying), the same trick as the telegraph’s on/off pulses, but with a wire that could only carry a continuous tone, not a clean on/off voltage. Every `1` bit plays one steady tone for its whole duration, every `0` bit plays a different, lower tone, and the modem on the other end just listens for which tone is present and reads back the bit. Watch one byte, the letter ‘A’, get modulated into tone and demodulated back into bits:

modemmodulation / demodulation, one byte

sending 'A' as bits 01000001

0

1

0

0

0

0

0

1

higher-frequency tone (mark) = 1, lower-frequency tone (space) = 0

received

·

·

·

·

·

·

·

·

Sending bit 0, the modem plays the lower "space" tone for this bit's whole duration.

Before any data moved over that reserved line, the two modems first had to agree, over that same voice-grade circuit, on how fast they could talk and how they’d correct the errors a noisy copper pair was bound to introduce. Modems since the 1981 Hayes Smartmodem left a speaker wired in so a human could hear the call connect, dial tone through ringing, and confirm it hadn’t hit a busy signal or a wrong number before the computer took over; the speaker stayed on into the handshake and only cut out once the negotiation finished, which is why that negotiation was audible too. If you were using the internet during the 1990s and early 2000s, do you remember this tone?

audio recording of a dial-up handshake

<audio src="https://fazamhd.com/audio/dial-up-handshake.ogg"></audio>

<svg viewBox="0 0 700 128" preserveAspectRatio="xMidYMid meet" aria-hidden="true"><line x1="70" y1="54" x2="630" y2="54" stroke="currentColor" stroke-width="1"></line><polyline points="70.0,38.0 73.5,38.0 77.0,38.0 80.5,38.0 84.0,38.0 87.5,38.0 91.0,38.0 94.5,38.0 98.0,38.0 101.5,38.0 105.0,38.0 108.5,38.0 112.0,38.0 115.5,38.0 119.0,38.0 122.5,38.0 126.0,38.0 129.5,38.0 133.0,38.0 136.5,38.0 140.0,38.0 143.5,38.0 147.0,38.0 150.5,38.0 154.0,38.0 157.5,38.0 161.0,38.0 164.5,38.0 168.0,38.0 171.5,38.0 175.0,38.0 178.5,38.0 182.0,38.0 185.5,38.0 189.0,38.0 192.5,38.0 196.0,38.0 199.5,38.0 203.0,38.0 206.5,38.0 210.0,38.0 213.5,38.0 217.0,38.0 220.5,38.0 224.0,38.0 227.5,38.0 231.0,38.0 234.5,38.0 238.0,38.0 241.5,38.0 245.0,38.0 248.5,38.0 252.0,38.0 255.5,38.0 259.0,38.0 262.5,38.0 266.0,38.0 269.5,38.0 273.0,38.0 276.5,38.0 280.0,38.0 283.5,38.0 287.0,38.0 290.5,38.0 294.0,38.0 297.5,38.0 301.0,38.0 304.5,38.0 308.0,38.0 311.5,38.0 315.0,38.0 318.5,38.0 322.0,38.0 325.5,38.0 329.0,38.0 332.5,38.0 336.0,38.0 339.5,38.0 343.0,38.0 346.5,38.0 350.0,38.0 353.5,38.0 357.0,38.0 360.5,38.0 364.0,38.0 367.5,38.0 371.0,38.0 374.5,38.0 378.0,38.0 381.5,38.0 385.0,38.0 388.5,38.0 392.0,38.0 395.5,38.0 399.0,38.0 402.5,38.0 406.0,38.0 409.5,38.0 413.0,38.0 416.5,38.0 420.0,38.0 423.5,38.0 427.0,38.0 430.5,38.0 434.0,38.0 437.5,38.0 441.0,38.0 444.5,38.0 448.0,38.0 451.5,38.0 455.0,38.0 458.5,38.0 462.0,38.0 465.5,38.0 469.0,38.0 472.5,38.0 476.0,38.0 479.5,38.0 483.0,38.0 486.5,38.0 490.0,38.0 493.5,38.0 497.0,38.0 500.5,38.0 504.0,38.0 507.5,38.0 511.0,38.0 514.5,38.0 518.0,38.0 521.5,38.0 525.0,38.0 528.5,38.0 532.0,38.0 535.5,38.0 539.0,38.0 542.5,38.0 546.0,38.0 549.5,38.0 553.0,38.0 556.5,38.0 560.0,38.0 563.5,38.0 567.0,38.0 570.5,38.0 574.0,38.0 577.5,38.0 581.0,38.0 584.5,38.0 588.0,38.0 591.5,38.0 595.0,38.0 598.5,38.0 602.0,38.0 605.5,38.0 609.0,38.0 612.5,38.0 616.0,38.0 619.5,38.0 623.0,38.0 626.5,38.0 630.0,38.0" fill="none" stroke="currentColor" stroke-width="1.3" vector-effect="non-scaling-stroke"></polyline><polyline points="630.0,70.0 626.5,70.0 623.0,70.0 619.5,70.0 616.0,70.0 612.5,70.0 609.0,70.0 605.5,70.0 602.0,70.0 598.5,70.0 595.0,70.0 591.5,70.0 588.0,70.0 584.5,70.0 581.0,70.0 577.5,70.0 574.0,70.0 570.5,70.0 567.0,70.0 563.5,70.0 560.0,70.0 556.5,70.0 553.0,70.0 549.5,70.0 546.0,70.0 542.5,70.0 539.0,70.0 535.5,70.0 532.0,70.0 528.5,70.0 525.0,70.0 521.5,70.0 518.0,70.0 514.5,70.0 511.0,70.0 507.5,70.0 504.0,70.0 500.5,70.0 497.0,70.0 493.5,70.0 490.0,70.0 486.5,70.0 483.0,70.0 479.5,70.0 476.0,70.0 472.5,70.0 469.0,70.0 465.5,70.0 462.0,70.0 458.5,70.0 455.0,70.0 451.5,70.0 448.0,70.0 444.5,70.0 441.0,70.0 437.5,70.0 434.0,70.0 430.5,70.0 427.0,70.0 423.5,70.0 420.0,70.0 416.5,70.0 413.0,70.0 409.5,70.0 406.0,70.0 402.5,70.0 399.0,70.0 395.5,70.0 392.0,70.0 388.5,70.0 385.0,70.0 381.5,70.0 378.0,70.0 374.5,70.0 371.0,70.0 367.5,70.0 364.0,70.0 360.5,70.0 357.0,70.0 353.5,70.0 350.0,70.0 346.5,70.0 343.0,70.0 339.5,70.0 336.0,70.0 332.5,70.0 329.0,70.0 325.5,70.0 322.0,70.0 318.5,70.0 315.0,70.0 311.5,70.0 308.0,70.0 304.5,70.0 301.0,70.0 297.5,70.0 294.0,70.0 290.5,70.0 287.0,70.0 283.5,70.0 280.0,70.0 276.5,70.0 273.0,70.0 269.5,70.0 266.0,70.0 262.5,70.0 259.0,70.0 255.5,70.0 252.0,70.0 248.5,70.0 245.0,70.0 241.5,70.0 238.0,70.0 234.5,70.0 231.0,70.0 227.5,70.0 224.0,70.0 220.5,70.0 217.0,70.0 213.5,70.0 210.0,70.0 206.5,70.0 203.0,70.0 199.5,70.0 196.0,70.0 192.5,70.0 189.0,70.0 185.5,70.0 182.0,70.0 178.5,70.0 175.0,70.0 171.5,70.0 168.0,70.0 164.5,70.0 161.0,70.0 157.5,70.0 154.0,70.0 150.5,70.0 147.0,70.0 143.5,70.0 140.0,70.0 136.5,70.0 133.0,70.0 129.5,70.0 126.0,70.0 122.5,70.0 119.0,70.0 115.5,70.0 112.0,70.0 108.5,70.0 105.0,70.0 101.5,70.0 98.0,70.0 94.5,70.0 91.0,70.0 87.5,70.0 84.0,70.0 80.5,70.0 77.0,70.0 73.5,70.0 70.0,70.0" fill="none" stroke="currentColor" stroke-width="1.1" stroke-dasharray="3,2" vector-effect="non-scaling-stroke"></polyline><g><rect x="60" y="47" width="20" height="14" fill="currentColor" stroke="currentColor" stroke-width="1.6" vector-effect="non-scaling-stroke"></rect><rect x="63" y="49.5" width="14" height="9" fill="none" stroke="currentColor" stroke-width="1" vector-effect="non-scaling-stroke"></rect><rect x="65" y="61" width="10" height="2.5" fill="currentColor" stroke="currentColor" stroke-width="1" vector-effect="non-scaling-stroke"></rect><text x="70" y="98" text-anchor="middle" font-size="11" fill="currentColor">your modem</text></g> <g><g><rect x="619" y="50" width="22" height="4.5" fill="currentColor" stroke="currentColor" stroke-width="1.4" vector-effect="non-scaling-stroke"></rect><circle cx="637" cy="52.25" r="0.9" fill="currentColor"></circle></g><g><rect x="619" y="56" width="22" height="4.5" fill="currentColor" stroke="currentColor" stroke-width="1.4" vector-effect="non-scaling-stroke"></rect><circle cx="637" cy="58.25" r="0.9" fill="currentColor"></circle></g><g><rect x="619" y="62" width="22" height="4.5" fill="currentColor" stroke="currentColor" stroke-width="1.4" vector-effect="non-scaling-stroke"></rect><circle cx="637" cy="64.25" r="0.9" fill="currentColor"></circle></g><text x="630" y="98" text-anchor="middle" font-size="11" fill="currentColor">ISP modem</text></g></svg>

solid: downstream (ISP → you) · dashed: upstream (you → ISP), simultaneous, full duplex

dial tone & dialing

call answered

capability handshake

modulation negotiation

equalizer training

connected

A real handshake between two dial-up modems, sped through six phases in under thirty seconds. Press play to hear it, and watch which phase is making that sound.

What sounds like noise is a protocol running in full: capability lists, line probes, and equalizer training, all audible because early modems left the speaker on by default so a human could hear whether the call was progressing normally. Recording: "Dial up modem noises," public domain, Wikimedia Commons.

That noisy handshake remained the way most people reached the internet well into the early 2000s, until broadband retired it. DSL and cable reused the same telephone and television wires, but as always-on digital links with no call to place, and fiber to the home dropped the voice network’s wires entirely.

The deeper mismatch, though, was never the modem’s translation, and it was clear decades before broadband. Computer traffic is **bursty**, a terminal sends a keystroke or a request in milliseconds, then the line sits silent while a human reads or a processor computes. (Even streaming a video today, which feels continuous, is actually delivered in short, intense bursts of packets that fill a playback buffer, followed by silence while you watch.) Measured over a session, a circuit reserved for a computer conversation is idle the vast majority of the time, yet it blocks that capacity for everyone else. Worse, the path is fixed at call setup, so one broken link or switching office anywhere along it kills the connection outright.

By the early 1960s, three pressures were converging on this circuit-switched design. Research computers were multiplying and needed to share expensive long-distance lines efficiently. Interactive computing made the burstiness extreme. And the United States military, in the middle of the Cold War, wanted a command network that could keep functioning after losing large pieces of itself, which a network of fixed paths through central switching offices could never do.

## Splitting Messages into Packets

The alternative was worked out independently by two people who did not know of each other’s work, **Paul Baran** at the RAND Corporation, designing for survivability, and **Donald Davies** at the UK’s National Physical Laboratory, designing for line sharing, who gave the idea its name, the **packet**.

Instead of reserving a path and streaming data down it, split every message into small, self-contained units. Each **packet** carries a **header**, a few bytes of control information including the source and destination addresses, followed by the **payload**, the chunk of data itself. Every switching point along the way, a **router**, receives a packet in full, reads the destination address in its header, consults its own table of which outgoing line leads closer to that destination, and forwards the packet down it. This is **store-and-forward** switching, the telegraph relay office rebuilt in electronics, with the paper tape replaced by memory and the operator replaced by a lookup table.

To scale to billions of machines, routers don’t list individual addresses. Instead, their tables list *networks*, ranges of addresses grouped under a single next hop. The exact structure of these addresses, and how they are compared against ranges, depends on the protocol in the packet header (Baran and Davies each designed their own). We will explore the internet’s version, IP, in detail in [Connecting the Networks](#connecting-the-networks).

With this design, packets from thousands of unrelated conversations interleave on the same wires, so no line sits idle while anyone has data to send. And because each packet is routed independently, the network flows around damage. If a router dies mid-conversation, subsequent packets simply travel through its neighbors. Baran called this a **distributed** network, one with no point whose loss can cut it in two.

The simulator below is a small packet-switched mesh. Clients on the left exchange packets with servers on the right. Both are examples of a **host**, the generic name for any addressable device on a network, computer, phone, server, whatever it is. The two roles themselves matter enough that this article will keep coming back to them, a **client** initiates a conversation, a **server** sits at a known, fixed address and waits to be reached. Each router in between makes only local decisions, forwarding each packet toward its destination while steering around links that are already busy. Watch how packets from the same conversation take different paths, and how congestion reshapes routes in real time. And click a router to kill it, notice the healing is not instant, for a few seconds its neighbors keep forwarding into the gap on stale information and those packets are lost, until news of the failure spreads and routes settle around it, a catching-up process called **convergence** that we will explore when we look at [routing protocols](#where-routes-come-from-and-who-carries-your-packets).

SWITCHING MODE:

R1

R2

R3

R4

R5

R6

R7

R8

R9

R10

R11

R12

A

B

1

2

clients

servers

Two clients, two servers, a dozen routers between them, every packet routed hop by hop.

best-effort delivery0 arrived0 dropped

A toy mesh of a dozen routers; click any router to destroy/disable it. For a few seconds its neighbors keep forwarding into the gap and those packets are lost, then routes settle around the failure, while reserved circuits stay broken. Hover routers to inspect local lookup tables.

Notice one more thing in the simulator, occasionally a packet is simply **dropped**. When packets arrive at a router faster than an outgoing line can drain them, the router queues them in memory, and when the queue is full, it discards what it cannot hold. This is not a failure of the design; it *is* the design. The network promises only **best-effort** delivery, packets may be lost, duplicated, or arrive out of order, and the network itself does nothing to correct it. Keeping the middle of the network this simple, and pushing all responsibility for reliability out to the computers at the edges, is the single most consequential decision in the internet’s architecture, and the key to how it scaled to a global network.

## The First Packet Network

In 1969, ARPA, the US Advanced Research Projects Agency, funded the first real packet-switching network, the **ARPANET**, to connect the research computers it was already paying for at universities across the country.

There was an immediate, mundane obstacle. The mainframes at each site came from different manufacturers, ran incompatible operating systems, and had no spare capacity for the real-time work of switching packets. The engineering firm Bolt Beranek and Newman (BBN) solved this with a dedicated machine, the **Interface Message Processor (IMP)**, a ruggedized minicomputer whose only job was to break messages into packets, route them, and reassemble them at the far end. Each site plugged its mainframe into its local IMP, and the IMPs talked to each other over leased telephone lines. ARPANET’s own protocol documents drew a sharp line between the two machines at each site, the IMP, dumb switching hardware with one job, and the mainframe behind it, which they called the **Host**, the machine that actually *hosted* the computation anyone cared about. That word outlived the hardware, a host today is any computer, phone, or server sending or receiving traffic, and a router or switch is whatever inherited the IMP’s old job of being infrastructure, not a host itself. The IMP was the first router, and its pattern, a dedicated box that speaks the network’s protocol so the computers behind it don’t have to, is sitting in your home right now with antennas on it.

![BBN Interface Message Processor (IMP), a refrigerator-sized cabinet with a front panel of toggle switches and indicator lights](https://fazamhd.com/_astro/bbn-imp.DAdAw1QX.jpg)

A BBN Interface Message Processor (IMP) at the Computer History Museum. Built from a hardened Honeywell DDP-516 minicomputer, the IMP was the first generation of packet routers. (Photo: Steve Jurvetson, CC BY 2.0, via Wikimedia Commons)

The first transmission took place on October 29, 1969, from UCLA to the Stanford Research Institute. A student programmer, Charley Kline, began typing `LOGIN` to log into the remote machine. He typed `L`, confirmed by phone that it had arrived, typed `O`, and the receiving system crashed. The first message ever carried by the internet’s ancestor was `LO`. By December the network had four nodes; by 1973 it crossed the Atlantic to Norway and London.

![ARPANET logical map from December 1969](https://fazamhd.com/_astro/arpanet-map-1969.60wiPUZF.jpg)

The logical map of the ARPANET in December 1969: UCLA, Stanford Research Institute, UC Santa Barbara, and the University of Utah. The entire internet started here. (Source: DARPA, public domain)

## One Shared Wire for the Whole Office

The packet-switching network built for the ARPANET connected distant sites over leased point-to-point lines, forming a **WAN** (Wide Area Network). The same core idea of packet transmission also solved a smaller, far more local problem, how do you connect the dozens of machines in one office, a **LAN** (Local Area Network), without running a dedicated wire between every pair?

In 1973, **Robert Metcalfe** at Xerox PARC designed **Ethernet**. Its collision handling drew directly on **ALOHAnet**, an earlier radio network linking the Hawaiian islands, whose core idea was refreshingly blunt, a station just transmits whenever it has something to send, and listens for whether it collided with someone else’s transmission, rather than asking permission first. Metcalfe’s design connected every computer in a building to one shared coaxial cable, which he called “the ether.” **Coaxial** means two conductors on the same central axis, a single copper core carrying the signal, wrapped in an insulating layer, then a cylindrical braided or foil shield, then a plastic jacket. The shield doubles as the return path and blocks outside interference from reaching the core, which is what let one long cable carry a clean signal past every desk in the building. Any machine could transmit onto the cable, and every machine received everything, keeping only the packets addressed to it.

A shared medium has an obvious flaw, if two machines transmit at once, they garble each other, a **collision**. Ethernet handled it with a few purely local rules, listen before transmitting, and wait if the cable is busy; keep listening *while* transmitting, and stop the instant you hear a collision; then retry after a random delay. By doubling the range of that random delay with each repeated collision, a strategy called **exponential backoff**, colliding machines spread themselves apart instead of jamming the line forever. This scheme is called **CSMA/CD** (Carrier Sense Multiple Access with Collision Detection), “carrier sense” is listening before you talk, and “collision detection” is stopping the instant you hear noise. As with packet routing, orderly sharing emerges from identical local rules, with no coordinator required.

The shared cable itself didn’t survive, offices moved to **switches**, and the coax went with it, replaced by twisted-pair copper terminating in an **RJ-45** connector, a clear plastic clip slightly wider than a phone jack, one dedicated run from each device back to the switch instead of one wire threaded past every desk.

A switch solves the same problem as a router, delivering data only to its destination, but operates on local hardware addresses rather than global network addresses, and by a different mechanism entirely. A router reads a packet’s destination address and picks a line from a table someone configured. A switch reads a **frame’s** (Ethernet’s own name for its unit of data, a packet’s counterpart one layer down) **MAC (Media Access Control) address**, the identifier burned into a device’s network hardware, and picks a port from a table it built entirely by itself, by watching traffic go by.

A MAC address is written as six pairs of **hexadecimal** digits separated by colons, for example, `00:1A:2B:3C:4D:5E`.

Hexadecimal just means base 16 instead of base 10, sixteen digits per place, `0` through `9` and then `A` through `F` standing in for ten through fifteen. It was chosen for a reason more specific than tradition, 16 is a power of 2, so one hex digit always encodes exactly four bits, no remainder, and two hex digits always encode exactly one byte, `1A` is one byte with the value 26. Decimal has no such alignment, three decimal digits sometimes hold a byte and sometimes don’t, which is why engineers reach for hex anywhere they’re really looking at raw bits but want something more compact than writing them out as 1s and 0s. That’s the same reason it resurfaces later in this article, in packet header bytes and protocol numbers, it’s binary in fewer characters, not a different kind of number.

By dividing this 48-bit address into a manufacturer prefix (the first three pairs, known as an **OUI** or Organizationally Unique Identifier) and a serial number (the last three pairs), they ensured every network interface card on Earth gets a globally unique ID. Every connected device, including your smartphone, carries these identifiers for both its Wi-Fi and Bluetooth chips.

Manufacturer (OUI)

00:1A:2B

Identifies the hardware vendor (e.g., Apple, Intel, Cisco)

Serial Number (NIC)

3C:4D:5E

Unique identifier assigned to this specific chip

Because a permanent hardware address never changes, anyone operating public Wi-Fi networks (like in a shopping mall) could log your MAC address to track your physical movements over time. To prevent this, modern operating systems now generate temporary, randomized MAC addresses when scanning for networks or connecting to public Wi-Fi. The switch doesn’t mind; it only needs your address to be unique among the few devices currently in the room, which a randomly generated 48-bit number easily guarantees.

![RJ-45 Ethernet ports on an unmanaged switch, some with patch cables plugged in and link lights lit, others empty](https://fazamhd.com/_astro/ethernet-switch-ports.duXMJGbN.jpg)

The physical side of the mechanism below, each port on a switch is a wire to one device (or one more switch), and the switch’s only job is picking the right one. (Photo: ProjectManhattan, CC BY-SA 3.0, via Wikimedia Commons)

When a switch is powered on, its forwarding table starts empty. Every time a frame arrives, before the switch even checks where it is *going*, it notes where it came *from*. By pairing that source MAC address with the port it arrived on, the switch records a new entry. This process is called **learning**. It happens on every passing frame, not just those addressed to the switch, because the switch builds its table by passively observing traffic rather than being told the network’s layout. Only then does it check the table for the frame’s *destination* MAC, with two possible outcomes:

- If the destination is unknown, because that device hasn’t sent a frame yet, the switch **floods** the frame out of all other ports, guaranteeing it reaches the target while other devices ignore it.
- If the destination is known, the switch forwards the frame out of that single port only, keeping the other ports silent.

A switch learns the location of every device after just a few frames of traffic, making flooding the exception rather than the rule. Watch a switch build its table below, forwarding directly when it knows the destination and flooding when it doesn’t.

network switch

switch

—

A1:11:1A

1unlearned

B2:22:2B

2unlearned

C3:33:3C

3unlearned

D4:44:4D

4unlearned

forwarding table, built by watching, not configured

source mac seen

port

A1:11:1A

—

B2:22:2B

—

C3:33:3C

—

D4:44:4D

—

A frame arrives on a port. Watch the switch learn who is where, and decide whether it can forward directly or must guess by flooding.

Both devices share the same core goal, making correct forwarding decisions locally without consulting a central authority, but they build their tables through completely different mechanisms. While a router’s table must be explicitly populated, either by manual configuration or by [routing protocols](#where-routes-come-from-and-who-carries-your-packets) that map the network, a switch’s table is filled in passively, by inference from traffic that was headed somewhere else anyway. And a switch’s table is strictly local in a way a router’s is not, a MAC address has meaning only within the local network segment where it was learned. This is exactly why the two devices divide the internet’s addressing between them, switches move frames within a network using addresses that never leave it, while routers move packets between networks using addresses that do.

One more thing quietly changed once switches took over, CSMA/CD’s whole reason for existing was a cable shared by many machines, where a collision was always possible. That shared cable was **half-duplex** (one signal on the wire at a time), so send and receive had to take turns, and a collision meant both signals collided on the wire, garbling the data. A switch gives every device its own private wire, so two machines wanting to talk at the same instant don’t collide. Instead, the switch holds one frame in a queue for a few microseconds while it sends the other. Modern Ethernet ports also run **full-duplex**, sending and receiving on separate internal paths at once, so there’s nothing to collide with even in principle. Collision detection became obsolete, a vestigial mechanism with no remaining use on modern full-duplex links.

Then Wi-Fi brought the shared medium back, in the form of air, where the same contention problem returns in a harder form; the upcoming wireless article will talk about that in detail.

## Connecting the Networks

The ARPANET proved packet switching worked, and its success created the next problem. Through the 1970s, other packet networks appeared on entirely different physical media, satellite links (SATNET), packet radio for vehicles (PRNET), local cables inside buildings (the Ethernet you just met). Each had its own packet format, its own maximum packet size, its own addressing scheme. A machine on one network could not reach a machine on another, and demanding that every network rip out its internals and adopt identical ones was never going to happen.

In 1973, **Vint Cerf** and **Bob Kahn** designed the architecture that connected them all without unifying any of them. Rather than one network, they proposed an *internetwork*, a network of networks, which is literally what “the **Internet** ” means. Routers called **gateways** would sit at the borders between networks, and the whole scheme rested on splitting the problem into two layers with sharply different jobs.

**IP (Internet Protocol)** is the one thing everyone must agree on, and it is deliberately tiny. It defines a universal address, the **IP address**, identifying every machine on any participating network, and a universal packet format that every network agrees to carry, tucked inside whatever local format that network uses internally. Crucially, IP promises almost nothing. It is **stateless**, no router remembers anything about your conversation from one packet to the next, and **unreliable**, it forwards each packet toward its destination as best it can, and if the packet is lost, IP does not notice or care. Together, those two properties are what **connectionless** means, there’s no setup phase and nothing shared between one packet and the next, every packet is handled as if it were the only one IP has ever seen. Because the bar is set so low, *any* network can clear it, copper, fiber, radio, satellite, anything that moves bytes can carry IP. This architecture creates an hourglass shape, with every physical medium on the bottom and every application on the top, interoperating because they all meet at one thin, simple protocol in the middle.

<svg viewBox="0 0 400 240" fill="none" xmlns="http://www.w3.org/2000/svg"><g><line x1="20" y1="36" x2="380" y2="36" stroke="currentColor" stroke-opacity="0.2"></line><text x="200" y="26" text-anchor="middle" fill="currentColor">Applications</text> <rect x="30" y="46" width="56" height="22" rx="2" fill="none" stroke="currentColor"></rect><text x="58" y="60" text-anchor="middle" fill="currentColor">HTTP</text> <rect x="98" y="46" width="56" height="22" rx="2" fill="none" stroke="currentColor"></rect><text x="126" y="60" text-anchor="middle" fill="currentColor">DNS</text> <rect x="166" y="46" width="68" height="22" rx="2" fill="none" stroke="currentColor"></rect><text x="200" y="60" text-anchor="middle" fill="currentColor">WebRTC</text> <rect x="246" y="46" width="56" height="22" rx="2" fill="none" stroke="currentColor"></rect><text x="274" y="60" text-anchor="middle" fill="currentColor">SMTP</text> <rect x="314" y="46" width="56" height="22" rx="2" fill="none" stroke="currentColor"></rect><text x="342" y="60" text-anchor="middle" fill="currentColor">SSH</text></g> <path d="M 58,68 L 182,108" fill="none" stroke="currentColor"></path><path d="M 126,68 L 191,108" fill="none" stroke="currentColor"></path><path d="M 200,68 L 200,108" fill="none" stroke="currentColor"></path><path d="M 274,68 L 209,108" fill="none" stroke="currentColor"></path><path d="M 342,68 L 218,108" fill="none" stroke="currentColor"></path><g><rect x="177" y="108" width="46" height="20" rx="3" fill="none" stroke="currentColor"></rect><text x="200" y="121" text-anchor="middle" fill="currentColor">IP</text></g> <path d="M 182,130 L 58,170" fill="none" stroke="currentColor"></path><path d="M 191,130 L 126,170" fill="none" stroke="currentColor"></path><path d="M 200,130 L 200,170" fill="none" stroke="currentColor"></path><path d="M 209,130 L 274,170" fill="none" stroke="currentColor"></path><path d="M 218,130 L 342,170" fill="none" stroke="currentColor"></path><g><line x1="20" y1="202" x2="380" y2="202" stroke="currentColor" stroke-opacity="0.2"></line><text x="200" y="213" text-anchor="middle" fill="currentColor">Physical Links</text> <rect x="30" y="170" width="56" height="22" rx="2" fill="none" stroke="currentColor"></rect><text x="58" y="184" text-anchor="middle" fill="currentColor">Fiber</text> <rect x="98" y="170" width="56" height="22" rx="2" fill="none" stroke="currentColor"></rect><text x="126" y="184" text-anchor="middle" fill="currentColor">Wi-Fi</text> <rect x="166" y="170" width="68" height="22" rx="2" fill="none" stroke="currentColor"></rect><text x="200" y="184" text-anchor="middle" fill="currentColor">Ethernet</text> <rect x="246" y="170" width="56" height="22" rx="2" fill="none" stroke="currentColor"></rect><text x="274" y="184" text-anchor="middle" fill="currentColor">LTE / 5G</text> <rect x="314" y="170" width="56" height="22" rx="2" fill="none" stroke="currentColor"></rect><text x="342" y="184" text-anchor="middle" fill="currentColor">Satellite</text></g></svg>

Here’s what that address, and the router’s table matching against it, actually look like. An IP address is nothing more than 32 bits, four bytes, **octets** in networking tradition, written in decimal and separated by dots, and a route in a router’s table names a network by a prefix, a claim about how many of those leading bits are fixed. `/24` means the first 24 bits are fixed and the remaining 8 are free, so matching a route is just comparing bits, an address matches a route if its leading bits, up to the prefix length, equal the route’s leading bits. Router hardware does this comparison as one operation, **XOR** the address against the route, mask off everything past the prefix length, and check whether what’s left is all zero, XOR gives a 1 at every bit position where the two disagree, so a match is nothing more than “no disagreements inside the fixed part.” This is the same claim an older notation, the **subnet mask**, makes by spelling out which bits are fixed as a separate dotted-decimal number; `255.255.255.0` marks the same leading 24 bits as `/24`, just written one octet at a time instead of as a count. The simulator below expands one address, octet by octet, into its 32 bits and runs exactly that comparison against several candidate routes.

IP route lookup

destination address 91.198.174.192 · 32 bits

91

0

1

0

1

1

0

1

1

198

1

1

0

0

0

1

1

0

174

1

0

1

0

1

1

1

0

192

1

1

0

0

0

0

0

0

checking route 1 of 4

0

1

0

1

1

0

1

1

1

1

0

0

0

1

1

0

1

0

1

0

1

1

1

0

91.198.174.0/24 · checking…

0

1

0

1

1

0

1

1

1

1

0

0

0

1

1

0

91.198.0.0/16

0

0

0

0

1

0

1

0

10.0.0.0/8

0 bits fixed0.0.0.0/0

The router compares the destination address, bit by bit, against every route it knows.

That comparison is the whole mechanism, and a real table runs it against every route it holds at once, taking the **longest prefix match**, whichever matching row fixes the most bits, and falling through to a catch-all default (`0.0.0.0/0`) only when nothing more specific matches. This single rule is what lets one table stay small: a router doesn’t need one row per address on Earth, only one row per network it has a more specific reason to know about; everything else rides the default toward whichever neighbor is closer to “the rest of the internet.” No router ever needs the whole picture; it only needs to know its own neighborhood plus one direction that’s more likely than the others, and forwarding on that alone is enough, because the next router applies the same partial knowledge, and the one after that, until the packet is close enough for someone to know it exactly. Correct delivery across a network no one fully maps is an emergent property of every hop doing this same small, local thing.

That freely-sized prefix wasn’t the original design. When IP addressing was formalized in 1981, it used a scheme called **classful addressing**, where an address’s network portion wasn’t an adjustable prefix, but one of three fixed sizes baked into the address itself. A Class A address gave an organization 16 million host addresses, a Class B gave 65,536, and a Class C gave only 256, with nothing in between. Most organizations needed only a few thousand addresses. Under this rigid system, they had to choose: either take a whole Class B (wasting tens of thousands of addresses) or collect multiple separate Class C networks. But because classful routing couldn’t group these separate networks together, every single Class C block had to be listed as a separate entry in the routing tables of every core router on the internet. By the early 1990s, the global routing table was growing faster than router memory could track, and free address space was draining fast. The fix, in 1993, was **CIDR** (Classless Inter-Domain Routing). This allowed the network portion to be any length rather than just three fixed sizes, so a network could be sized to exactly what an organization needed, and adjacent blocks could collapse into a single routing table entry. The `/24` prefix in the simulator above is a CIDR prefix, and this has been the internet’s standard routing scheme ever since.

classful, three fixed sizes, baked into the address's leading bits

Class A

first bits: 0

first octet: 1–126

/8

16,777,216 addresses

Class B

first bits: 10

first octet: 128–191

/16

65,536 addresses

Class C

first bits: 110

first octet: 192–223

/24

256 addresses

one organization needing ~4,000 addresses

classful → one Class B65,536 given

≈ 94% of the block sits unused

classful → sixteen Class C's16 × 256 = 4,096 given

right size, but sixteen blocks, 16 rows in every router's table

CIDR → /204,096 given

sized to the actual need, one table row

Where do those blocks actually come from? They follow the same hierarchical delegation as DNS (which we’ll explore in [Remembering Names Instead of Numbers](#remembering-names-instead-of-numbers)), just applied to numbers instead of names. **IANA** (Internet Assigned Numbers Authority), the same body that oversees the DNS root, holds the entire 32-bit address space. It distributes large blocks of addresses to five regional registries, one for each of North America, Europe, Asia-Pacific, Africa, and Latin America. Each registry carves its share into smaller blocks for the internet service providers in its region, who then slice those blocks further to hand out `/24` s or smaller to businesses and homes. In fact, your home router’s public IP address is drawn from one of these very blocks. Nobody holds the entire map; each registry only ever needs to know its own corner. This hierarchical delegation is the exact same design that allowed DNS to scale past a single file at Stanford, here applied to the administrative challenge of IP address allocation.

None of this says where the rows themselves come from, the simulator below just hands the router a finished table and watches it get used. The simplest source is a **static route**, configured manually, “anything for `10.0.0.0/8` goes out line 5,” which is exactly what that row is. That doesn’t scale to a network of any size, so real routers fill most of the table automatically instead, one mechanism for routers inside the same organization, comparing notes on a topology they can all see directly, and a different one for routers in different organizations that share no such trust, each simply announcing to its neighbors what it can reach. Both of those get their full explanation, and the table finally stops being a given, in [Where Routes Come From, and Who Carries Your Packets](#where-routes-come-from-and-who-carries-your-packets). For now, treat the table as fixed and watch what the router does with it once a packet arrives.

Watch the same rule run inside one router’s hardware, a packet lands on an interface, its header is read, its TTL is decremented, the table is checked, and it goes out the matched line, cycling through a few different destinations to see the match change each time.

router

previous hop

in

router

—

3

line 3

91.198.174.0/24

2

line 2

91.198.0.0/16

5

line 5

10.0.0.0/8

1

line 1

0.0.0.0/0

routing table — configured or learned elsewhere, just matched here

network

line

91.198.174.0/24

line 3

91.198.0.0/16

line 2

10.0.0.0/8

line 5

0.0.0.0/0

line 1

A packet arrives on an interface, gets its header read, and is forwarded, watch the router do it.

One field in that header deserves its own explanation, the **time-to-live (TTL)**, a number the sender sets and every router along the way decrements by one before forwarding. Reach zero, and a router discards the packet on the spot. The value has nothing to do with clock time, it is a hop count, and it exists because in a network with no central authority, a routing table can develop a loop, two routers each honestly believing the other is closer to a destination, forwarding a packet back and forth forever, doubling the load with every unlucky arrival. TTL guarantees that no packet can circulate indefinitely.

When a router kills a TTL-expired packet, it doesn’t just drop it silently, it sends back a small **ICMP** (Internet Control Message Protocol) message, “Time Exceeded,” to whoever sent the original packet. ICMP is IP’s own maintenance channel, the protocol routers use to report problems back to a source rather than just discarding traffic into the void, and the same channel carries the internet’s simplest diagnostic, **ping**. Ping sends one kind of ICMP message, an “Echo Request,” to an address, and asks for nothing more than an ICMP “Echo Reply” sent straight back. There’s no port, no handshake, no payload that means anything, just a question (“are you there?”) and an answer, and the round-trip time between sending the request and receiving the reply is the number everyone means when they say “ping” as a noun, a direct, unfiltered measurement of latency to one machine. Here it is running against a real address, eight requests, eight replies, each stamped with how long it took.

terminal recordingping · ICMP echo request/reply

That same ICMP Time Exceeded behavior described above is the entire mechanism behind **traceroute**, a diagnostic tool available on every operating system. It sends the same packet multiple times with TTL set to 1, then 2, then 3, and so on. The TTL=1 packet always dies at the very first router, which obligingly reports itself in the Time Exceeded reply; the TTL=2 packet dies at the second router, and so on, until a packet finally survives long enough to reach the destination itself. Nobody designed traceroute into the protocol, it falls entirely out of a hop counter that was only ever meant to kill loops, run against a real address, and it lists every router between you and it, one line per TTL, each one a little further from you.

terminal recordingtraceroute

That still leaves the other half of the problem flagged above unresolved, every network’s own “maximum packet size.” Each link technology imposes a ceiling on how many bytes it will carry in one unit, its **MTU** (maximum transmission unit), Ethernet’s is 1500 bytes, and it varies elsewhere. A packet built for a generous link can easily be too large for a stingier one further along the path, and IP’s answer, historically, was **fragmentation**, a router facing a packet bigger than the next link’s MTU slices it into smaller pieces, each a valid packet in its own right, and the destination reassembles them by the fragment numbers in their headers. It works, but it is expensive, the router has to do real work per fragment, and losing even one fragment means the whole original packet has to be resent.

Modern IP mostly avoids it instead, a sender marks its packets “don’t fragment,” and a router that can’t forward one whole sends back an ICMP message saying so, “packet is too big, try this MTU instead.” The source then shrinks what it sends for the rest of the conversation, a process called **Path MTU Discovery**, pushing the size problem back to the one place that can actually fix it, the sender. IPv6 goes further and removes router fragmentation from the protocol entirely, PMTUD is the only mechanism left. Watch the same oversized packet meet a narrow link both ways, the old fragmenting router and the modern one that just says no.

MTUfragmentation · MTU 1500B

sender

router

idle

destination

the constraint the router just hit

packet size

3000B

next-hop link MTU

1500B

outcome

—

A packet larger than the next link can carry reaches a router.

Everything so far has assumed one sender, one receiver, **unicast**, which covers nearly all traffic, but not quite. Your own address’s prefix, the `/24` or whatever length from the CIDR discussion above, names your **subnet**, and a subnet is a physical neighborhood as much as a numeric one, the set of devices sharing one wire or radio channel directly, reachable by MAC address alone, no router in between. A packet addressed to every host on the subnet at once, no exceptions, is a **broadcast**, useful for the rare cases where a host doesn’t yet know who to ask, **DHCP** (Dynamic Host Configuration Protocol), handing out an address to a device that has none yet, is one, and **ARP** (Address Resolution Protocol), asking “who owns this IP on our subnet” to learn a MAC address, is another. A broadcast stops at the boundary of the subnet, routers refuse to forward them. If they did, a single broadcast would flood the entire internet, forcing every computer on Earth to process it.

ARP is worth pausing on, because it’s the exact joint between the two addresses this article has spent so long building separately. Your machine builds an IP packet addressed to some IP, but that packet still has to leave over Ethernet or Wi-Fi, and a frame needs a destination MAC address, not an IP address; IP has no idea a MAC address even exists. So before the first frame of a new conversation can go anywhere, your machine broadcasts a question the entire subnet hears, “Who has this IP? Reply to my IP.” Every other host checks the question against its own address and, unless it’s the one being asked for, says nothing at all; only the owner replies, and it replies unicast, straight back to the asker, not to the whole subnet. The answer is cached for a few minutes, so this whole exchange happens once per neighbor, not once per packet.

And notice which IP address you actually resolve, if the destination IP is outside your own subnet, which almost every request is, you don’t ARP for that distant server’s MAC at all, that would be meaningless, since no frame from your machine can reach a MAC address that isn’t on your own wire. You ARP for your **default gateway** ’s MAC instead, the everyday name for the same border router Cerf and Kahn called a gateway at the top of this section, hand the frame to it, and let it take over from there, one hop at a time, exactly like the router-hop simulator above, just with the very first hop’s address filled in by this mechanism. Watch one host resolve a neighbor’s MAC, then resolve it again already cached, then do the same for a gateway, since off-subnet traffic only ever needs the next hop’s address, not the final one’s.

ARP, resolving an IP to a MAC

segment

host 1

203.0.113.10

1A:2B:3C

host 2

203.0.113.20

4D:5E:6F

host 3

203.0.113.30

7A:8B:9C

gateway

203.0.113.1

AA:BB:CC

host 1's ARP cache, built by asking, not configured

ip address

mac address

203.0.113.20

—

203.0.113.30

—

203.0.113.1

—

A host wants to send an IP packet to a neighbor on its own segment, but a frame needs a MAC address, and all it has is an IP address.

There is also a middle ground between one recipient and every recipient, **multicast**, one packet addressed to a group, forwarded only toward the hosts that asked to join that group. It’s the natural shape for feeds like IPTV, with many interested receivers but far fewer than everyone, and routing protocols lean on it internally, though on the public internet you will rarely meet it directly.

The original design gave addresses 32 bits, about 4.3 billion possible values, which seemed inexhaustible for a research network and has haunted the internet ever since, we will meet the consequences (and the workaround running in your home) later in this article. The successor, **IPv6**, with its effectively unlimited 128-bit addresses, written in the same hexadecimal as MAC addresses, eight colon-separated groups like `2607:f8b0:4004:c07::66`, has been rolling out for two decades and now carries almost half of all traffic, the two versions running side by side, another thing the layered design quietly permits.

## Making Packet Delivery Reliable

**TCP (Transmission Control Protocol)** is where all the reliability that IP refused to provide actually lives, and it runs *only* on the two computers at the ends of the conversation. The routers in between don’t even know it exists. TCP numbers every byte it sends, and the receiver continuously reports back the next byte it expects to receive, an acknowledgment, or **ACK**. Whatever isn’t acknowledged in time, the sender sends again. Packets that arrive out of order are put back in sequence by their numbers before the data is handed upward. Out of best-effort chaos, TCP manufactures the abstraction every networked program is written against, a reliable, ordered stream of bytes. Doing that requires both ends to remember where they are in the exchange for as long as it lasts, which is why TCP is called **connection-oriented**, the opposite of IP’s amnesia, and why a TCP conversation has an explicit beginning and an explicit end, while a single IP packet has neither.

One naming note before going further, this article has been saying “packet” for any unit of data at any layer, since the distinction rarely matters for the point being made, but TCP’s own unit does have a name, a **segment**, the chunk of the byte stream TCP hands down to IP for one trip, sitting alongside “frame” for Ethernet’s unit and “packet” for IP’s.

The explicit beginning is the **three-way handshake**, a three-segment exchange that synchronizes both sides’ byte numbering before any data flows. Each side picks a random starting sequence number for the bytes it’s about to send, then they trade them, the client sends `SYN, seq=5000` (“I’ll start counting my bytes from 5000”), the server replies `SYN-ACK, seq=9000, ack=5001` (“I’ll start from 9000; I have everything of yours up to 5000, send 5001 next”), the client replies `ACK, ack=9001` (“send me 9001 next”). Three segments, and both sides now agree on where the byte count starts, which is what lets TCP later say precisely which bytes are missing when one goes astray. Watch that exchange run.

TCP, the three-way handshake

client

server

seq —

seq —

Before any HTTP request goes out, both sides synchronize their byte numbering, watch the three segments that do it.

ACKs and retransmission answer “did it arrive,” but a packet can arrive without being *correct*, electrical noise, a bad connector, cosmic radiation hitting a memory chip, can flip a bit in flight without dropping the packet at all. Catching that is a separate, older, and much simpler mechanism, the **checksum**. The sender runs a small arithmetic function over the bytes it’s sending and appends the result; the receiver runs the identical function over the bytes it received and compares. Any disagreement means something changed in transit, and the receiver just discards the packet, silently, exactly as if it had never arrived, so the sender’s ordinary retransmission machinery, seeing no acknowledgment, sends it again.

It is deliberately not built to identify or repair the error, only to notice one, cheaply, on every single frame and packet, which is why the same idea reappears at almost every layer, Ethernet’s frame check sequence, IP’s header checksum, TCP’s own checksum over the segment. Notice what this does and doesn’t protect against, it catches accidental corruption from a noisy link, not a deliberate tamperer who recomputes the checksum to match their own forged bytes, that threat is what TLS, much later in this article, actually solves. Watch a clean transmission and a corrupted one side by side, and see the receiver catch the second:

checksum, detecting corruption

sender

0x48 0x65 0x6c 0x6c 0x6f

0x48 + 0x65 + 0x6c + 0x6c + 0x6f = 0x1f4 mod 256 = 0xf4

receiver

— — — — —

awaiting bytes

A sender computes a checksum over the data and ships both. Watch what happens when a bit flips in transit.

TCP also decides *how much* to keep in flight. The sender maintains a **sliding window**, a cap on how many unacknowledged packets it may have outstanding at once; hit the cap, and it must pause and wait. The window doesn’t move on its own, an ACK moves it, each one confirming the oldest outstanding packet lets a new one take its place at the far edge, which is the literal reason it’s called sliding, advancing one confirmed packet at a time, and that discipline is what keeps a fast sender from drowning a slow receiver. And when packets go missing, TCP reads the loss as a signal, some router’s queue along the path is overflowing, and shrinks its window to back off. This reflex, **congestion control**, was added the hard way. In October 1986, the link between Lawrence Berkeley Lab and UC Berkeley, 400 meters apart, collapsed from 32,000 bits per second to 40, a thousandfold drop, as every sender responded to loss by retransmitting harder, a feedback spiral called **congestion collapse**. Van Jacobson’s fix, back off multiplicatively on loss, probe forward gently on success, still runs in essentially every TCP implementation on Earth. Billions of connections, each following this same local rule with no coordinator, is what keeps the shared network from strangling itself, the same emergent cooperation we saw in packet routing, applied to capacity.

The simulator below shows a TCP sender streaming packets under a sliding window. Watch what happens when a packet is lost, the receiver keeps acknowledging the last in-order byte it has, and that burst of duplicate ACKs tips off the sender to retransmit the missing packet without waiting for a timeout.

TCP, reliable delivery

sender window: 4 packets in flight at once, sliding forward as ACKs confirm the oldest

1

2

3

4

5

6

7

8

sender

server

receiver, buffered until the gap fills, then delivered in order

·

·

·

·

·

·

·

·

Several packets in flight at once; lost ones are resent, and the far end delivers them in order.

Two refinements complete the transport picture. An IP address identifies a machine, but a machine runs many programs at once, so TCP adds a **port** number, and the combination of address and port delivers each byte stream to the right program; a web server conventionally listens on port 443 for encrypted traffic. That combination, an IP address plus a port plus the protocol, is what a **socket** names, the actual endpoint an application opens rather than merely the machine it lives on. The server’s port is fixed so clients know where to knock, but the client side needs a port too, since a reply has to come back to something more specific than just your machine, so your operating system picks one at random from a range set aside for exactly this, an **ephemeral port**, borrowed for the life of one connection and handed back afterward. That’s the `54211` sitting in the source port field of the packet diagram near the end of this article, not a port anything was listening on, just the number your machine happened to draw for that one request.

And for applications where retransmitting stale data is worse than losing it, a live video call has no use for a frame from two seconds ago, there is **UDP** (User Datagram Protocol), a thin alternative that adds ports to IP and nothing else, leaving each application to handle loss in whatever way suits it. UDP’s own unit is a **datagram** (joining Ethernet’s frame, IP’s packet, and TCP’s segment). The word itself doubles as a description, a self-contained parcel with everything it needs addressed on it, sent with no setup and no memory of the one before it. UDP is connectionless for the same reason IP is, it keeps no state and requires no setup, simply adding enough addressing to reach the right program. That’s the whole tradeoff, not a lesser version of TCP, but a different bet. TCP for a web page, an email, or a file, where an incomplete copy is worse than a slightly late one; UDP for a video call, a multiplayer game, or a DNS query, where a late answer is worse than a missing one (or where the application will just request the latest state anyway).

TCP vs UDP

TCPreliable, ordered

sender

receiver

1

2

3

4

5

Sending 5 segments; 3 is about to drop.

UDPbest-effort, no resend

sender

receiver

1

2

3

4

5

Sending 5 datagrams; 3 is about to drop.

TCP/IP became the ARPANET’s official protocol on January 1, 1983, and the definition of the internet has been simple ever since, it is the set of all networks that agree to carry IP packets. There is no membership office. You join the internet by speaking its protocol.

## Where Routes Come From, and Who Carries Your Packets

One question has been quietly deferred since the packet-switching section, a router forwards each packet down “the line that leads closer to the destination,” but how does it *know* which line that is? The answer splits cleanly along the same boundary as everything else in this article, one set of rules for inside an organization, a different one for between organizations.

Inside one organization’s network, routers run an **Interior Gateway Protocol (IGP)**, exchanging their own directly observed topology, which links are up, how congested each one is, and computing routes automatically. Two families dominate, and they disagree about a basic question, does a router need to see the whole network, or is a secondhand number enough?

**Link-state** protocols like **OSPF** (Open Shortest Path First) answer “see the whole network.” Every router floods a description of its own local connections to every other router, so each one ends up holding an identical map of the whole topology and runs the same shortest-path calculation independently.

**Distance-vector** protocols like the older **RIP** (Routing Information Protocol) answer “a number is enough.” Each router tells its neighbors only “I can reach this network in *N* hops,” never seeing the map itself, just trusting the secondhand count and adding one. It’s a far smaller exchange than flooding a map, but it also means a router has no way to check whether a neighbor’s number is still true. Try both below. Each cycle opens with an ordinary packet crossing all three routers first, the same longest prefix match lookup as the single router simulator earlier, just run three times in a row by three routers that never compare notes, so watch how little any one of them actually knows.

Interior Gateway Protocol

steady state

R1

R2

R3

net N

Steady state, every router already knows its hop count to net N.

each router's current belief about its distance to net N

R1

R2

R3

3 hops

2 hops

1 hop

When a link fails, every router’s table is briefly wrong until the new state finishes propagating; as we saw in the packet-switching mesh, **convergence** is the industry’s word for that catching-up process. Link-state converges in exactly the two flooded messages you just watched, because a flood carries the actual topology change, not a guess. Distance-vector has no such certainty to fall back on, and the RIP tab shows the failure mode: two neighbors briefly routing through each other, each trusting the other’s now-stale number, while a real packet for that destination bounces between them until its TTL kills it. Production deployments bolt mitigations onto RIP, but none of them makes a secondhand number converge as fast as a verified map, which is why OSPF displaced it in most production networks. Either way, this is a single administrator’s problem to solve, one company’s routers, one company’s decision about which protocol to run.

Things get much harder *between* organizations. Without a single administrator or shared trust, the solution is where the internet’s decentralized character actually takes shape.

That patchwork of organizations didn’t exist yet when TCP/IP became official in 1983, the network was still essentially one federally funded system. What actually split it apart was the **National Science Foundation’s NSFNET**, built in 1985 as a backbone connecting regional academic networks, each already run by a different university consortium, into one national network. For its first several years, NSFNET’s Acceptable Use Policy barred commercial traffic outright, no business email, no advertising, research and education only. That restriction lifted in 1991, and when NSFNET itself was shut down in 1995, its backbone role passed not to one successor but to several competing commercial carriers, who had no reason to merge and every reason to stay separate, rival companies selling the same service to the same customers. That handoff, a government network dissolving into a market of competitors, is the moment the internet stopped having an owner and became the patchwork BGP now holds together.

The internet is physically a patchwork of tens of thousands of independently operated networks, called **autonomous systems**, your home internet provider, a university, a national telecom, a cloud company. They exchange routes using the **Border Gateway Protocol (BGP)**. Each network announces to its neighbors, “I can reach these blocks of addresses,” and passes along, with itself appended to the path, the announcements it hears from others. Routes to every corner of the internet propagate from network to network, and each network chooses among the paths it has heard based not on speed but on *business policy*, money changes hands. Strip the business policy away and the shortest-path tiebreaker underneath it is simple enough to watch directly, one route, spreading hop by hop, each hop appending itself to the path, until a router two different ways away has to pick between them.

Border Gateway Protocol

waiting to originate

AS1 · origin

announces \[1\]

AS2

\-

AS3

\-

AS4

\-

AS5 · table

\-

AS1 originates a route to 91.198.174.0/24 and announces it to every neighboring network. Watch the announcement spread, and see how AS5 picks between two AS-level paths.

A small provider pays a larger one for **transit**, carriage to the whole internet, while networks of similar size **peer**, exchanging traffic between their customers for free, **settlement-free** in the industry’s terms, because it saves both sides transit fees, often meeting at **internet exchange points**, buildings where hundreds of networks plug into a common switching fabric, the largest, like DE-CIX in Frankfurt and AMS-IX in Amsterdam, connect on the order of a thousand. These two contracts are exactly what “business policy” meant in the route selection above. For any destination, a route through a neighbor falls into one of three cost classes, via a customer, that customer pays you to carry the traffic; via a peer, free; via a provider, you pay for every byte. So networks configure BGP to prefer customer routes over peer routes over provider routes, even when the paying route is longer, and shortest AS path decides only among routes of equal business standing.

At the top sit a handful of tier-1 backbones that peer with each other and pay no one, companies most people have never heard of, Lumen, Arelion, NTT, and a few others, and across the oceans run roughly 600 submarine fiber cables carrying essentially all intercontinental traffic. The internet holds together not by any authority, but by this mesh of contracts, handshakes, and BGP announcements.

<svg viewBox="0 -6 400 291" fill="none" xmlns="http://www.w3.org/2000/svg"><defs><marker id="tp-arrow" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 8 4 L 0 8 z" fill="currentColor"></path></marker></defs><text x="200" y="6" text-anchor="middle" fill="currentColor">Tier-1 backbones · peer, pay no one</text> <rect x="60" y="28" width="72" height="22" rx="2" fill="none" stroke="currentColor"></rect><text x="96" y="42" text-anchor="middle" fill="currentColor">Backbone A</text> <rect x="164" y="28" width="72" height="22" rx="2" fill="none" stroke="currentColor"></rect><text x="200" y="42" text-anchor="middle" fill="currentColor">Backbone B</text> <rect x="268" y="28" width="72" height="22" rx="2" fill="none" stroke="currentColor"></rect><text x="304" y="42" text-anchor="middle" fill="currentColor">Backbone C</text> <line x1="132" y1="39" x2="164" y2="39" stroke="currentColor" stroke-opacity="0.2"></line><line x1="236" y1="39" x2="268" y2="39" stroke="currentColor" stroke-opacity="0.2"></line><path d="M 96,28 C 140,8 260,8 304,28" fill="none" stroke="currentColor"></path><path d="M 122,118 C 100,40 300,40 278,118" fill="none" stroke="currentColor"></path><text x="200" y="100" text-anchor="middle" fill="currentColor">the paid detour peering avoids</text> <line x1="112" y1="118" x2="112" y2="54" marker-end="url(#tp-arrow)" stroke="currentColor" stroke-opacity="0.2"></line><text x="102" y="90" text-anchor="end" fill="currentColor">$ transit</text> <line x1="288" y1="118" x2="288" y2="54" marker-end="url(#tp-arrow)" stroke="currentColor" stroke-opacity="0.2"></line><text x="298" y="90" fill="currentColor">$ transit</text> <rect x="52" y="118" width="120" height="22" rx="2" fill="none" stroke="currentColor"></rect><text x="112" y="132" text-anchor="middle" fill="currentColor">Provider X</text> <rect x="228" y="118" width="120" height="22" rx="2" fill="none" stroke="currentColor"></rect><text x="288" y="132" text-anchor="middle" fill="currentColor">Provider Y</text> <rect x="182" y="121" width="36" height="16" rx="2" fill="none" stroke="currentColor"></rect><text x="200" y="132" text-anchor="middle" style="font-size:8px" fill="currentColor">IXP</text> <line x1="172" y1="129" x2="182" y2="129" stroke="currentColor" stroke-opacity="0.2"></line><line x1="218" y1="129" x2="228" y2="129" stroke="currentColor" stroke-opacity="0.2"></line><text x="200" y="152" text-anchor="middle" fill="currentColor">peer · similar size, no money</text> <text x="200" y="163" text-anchor="middle" fill="currentColor">saves both transit fees</text> <line x1="70" y1="208" x2="100" y2="144" marker-end="url(#tp-arrow)" stroke="currentColor" stroke-opacity="0.2"></line><text x="72" y="180" text-anchor="end" fill="currentColor">$</text> <line x1="152" y1="208" x2="124" y2="144" marker-end="url(#tp-arrow)" stroke="currentColor" stroke-opacity="0.2"></line><text x="148" y="180" fill="currentColor">$</text> <line x1="248" y1="208" x2="276" y2="144" marker-end="url(#tp-arrow)" stroke="currentColor" stroke-opacity="0.2"></line><text x="250" y="180" text-anchor="end" fill="currentColor">$</text> <line x1="330" y1="208" x2="300" y2="144" marker-end="url(#tp-arrow)" stroke="currentColor" stroke-opacity="0.2"></line><text x="326" y="180" fill="currentColor">$</text> <rect x="30" y="208" width="72" height="22" rx="2" fill="none" stroke="currentColor"></rect><text x="66" y="222" text-anchor="middle" fill="currentColor">Your ISP</text> <rect x="120" y="208" width="72" height="22" rx="2" fill="none" stroke="currentColor"></rect><text x="156" y="222" text-anchor="middle" fill="currentColor">University</text> <rect x="210" y="208" width="72" height="22" rx="2" fill="none" stroke="currentColor"></rect><text x="246" y="222" text-anchor="middle" fill="currentColor">Business</text> <rect x="300" y="208" width="72" height="22" rx="2" fill="none" stroke="currentColor"></rect><text x="336" y="222" text-anchor="middle" fill="currentColor">Telecom</text> <text x="200" y="245" text-anchor="middle" fill="currentColor">Edge networks · each pays the network above it</text> <line x1="88" y1="266" x2="112" y2="266" marker-end="url(#tp-arrow)" stroke="currentColor" stroke-opacity="0.2"></line><text x="118" y="269" fill="currentColor">money for transit</text> <line x1="216" y1="266" x2="240" y2="266" stroke="currentColor" stroke-opacity="0.2"></line><text x="246" y="269" fill="currentColor">settlement-free peering</text></svg>

Those cables are the telegraph’s ocean-floor wire, several generations on. The first transatlantic *telephone* cable, TAT-1, went into service in 1956, coaxial copper carrying 36 voice circuits, with an amplifier spliced in roughly every 70 kilometers to boost the signal before it faded into noise. That’s the telegraph section’s analog problem all over again, an amplifier can’t tell signal from noise, so it boosts both, and unlike a telegraph pulse, a voice waveform can’t be cleanly regenerated back to its original shape at each hop. Fiber broke that tradeoff. TAT-8, laid in 1988, was the first transatlantic fiber cable, and it didn’t just improve on TAT-1, it made it obsolete overnight, two glass strands carrying tens of thousands of voice-equivalent circuits, because light in glass can be sliced into far more independent channels than voltage on copper ever could. Every transatlantic cable built since has been fiber; the roughly 600 running today are TAT-8’s descendants, not TAT-1’s.

![Cut samples of four submarine fiber cable types, layers stepped back to show glass fibers, copper conductor, and steel armor, with a coin for scale](https://fazamhd.com/_astro/submarine-cable-samples.C85IdU0F.jpg)

Modern submarine fiber cable, cut open. At the center of each sample sit a few glass fibers; around them a copper power conductor for the amplifiers and layers of steel armor, double-wrapped near shore, bare in the deep sea, where the coin gives the scale. (Photo: Lonnie Hagadorn, CC BY-SA 4.0, via Wikimedia Commons)

None of this works unless the light actually stays in the glass. A fiber’s core is glass of a slightly higher refractive index than the cladding wrapped around it, and light traveling down the core meets that boundary at a glancing angle, shallower than the **critical angle**, so instead of refracting through, it reflects back in, completely. That completeness is the whole trick. An ordinary mirror absorbs a fraction of a percent per bounce, which would extinguish a signal that bounces millions of times per kilometer; **total internal reflection** loses nothing at the boundary, which is why a hair-thin glass thread can guide a pulse for around a hundred kilometers, through every sag and curve of the seabed, before an amplifier needs to touch it.

<svg viewBox="0 0 404 152" fill="none" xmlns="http://www.w3.org/2000/svg"><defs><marker id="tir-arrow" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 8 4 L 0 8 z" fill="currentColor"></path></marker><marker id="tir-arrow-faint" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 8 4 L 0 8 z" fill="currentColor" opacity="0.7"></path></marker></defs><text x="200" y="10" text-anchor="middle" fill="currentColor">Total internal reflection</text> <path d="M16.0,57.0 L207.1,57.1 L214.2,57.2 L221.2,57.5 L228.3,58.0 L235.4,58.5 L242.4,59.2 L249.5,60.0 L256.5,60.9 L263.5,61.9 L270.5,63.0 L277.5,64.3 L284.4,65.7 L291.3,67.2 L298.2,68.8 L305.1,70.5 L312.0,72.4 L318.8,74.4 L325.5,76.4 L332.3,78.6 L339.0,81.0 L345.6,83.4 L352.2,85.9 L358.8,88.6 L365.3,91.3 L371.8,94.2 L378.2,97.2 L384.6,100.3 L390.9,103.5 L377.1,130.2 L371.2,127.2 L365.3,124.3 L359.4,121.5 L353.4,118.9 L347.3,116.3 L341.2,113.8 L335.1,111.5 L328.9,109.2 L322.7,107.1 L316.5,105.0 L310.2,103.1 L303.9,101.3 L297.5,99.6 L291.1,97.9 L284.7,96.4 L278.3,95.1 L271.9,93.8 L265.4,92.6 L258.9,91.5 L252.4,90.6 L245.9,89.7 L239.4,89.0 L232.8,88.4 L226.3,87.9 L219.7,87.5 L213.1,87.2 L206.6,87.1 L16.0,87.0 Z" fill="none"></path><path d="M16.0,45.0 L207.3,45.1 L214.6,45.2 L221.9,45.6 L229.1,46.0 L236.4,46.6 L243.7,47.2 L250.9,48.0 L258.1,49.0 L265.3,50.0 L272.5,51.2 L279.7,52.5 L286.9,53.9 L294.0,55.5 L301.1,57.1 L308.2,58.9 L315.2,60.8 L322.2,62.9 L329.2,65.0 L336.1,67.3 L343.0,69.6 L349.8,72.1 L356.6,74.8 L363.4,77.5 L370.1,80.3 L376.8,83.3 L383.4,86.4 L389.9,89.6 L396.4,92.9" fill="none" stroke="currentColor"></path><path d="M16.0,99.0 L206.4,99.1 L212.7,99.2 L219.1,99.5 L225.5,99.9 L231.8,100.4 L238.1,101.0 L244.5,101.7 L250.8,102.5 L257.1,103.4 L263.4,104.4 L269.6,105.6 L275.9,106.8 L282.1,108.1 L288.3,109.6 L294.5,111.2 L300.6,112.8 L306.7,114.6 L312.8,116.5 L318.9,118.4 L324.9,120.5 L330.9,122.7 L336.8,125.0 L342.7,127.4 L348.6,129.9 L354.4,132.5 L360.2,135.1 L365.9,137.9 L371.6,140.8" fill="none" stroke="currentColor"></path><path d="M16.0,57.0 L207.1,57.1 L214.2,57.2 L221.2,57.5 L228.3,58.0 L235.4,58.5 L242.4,59.2 L249.5,60.0 L256.5,60.9 L263.5,61.9 L270.5,63.0 L277.5,64.3 L284.4,65.7 L291.3,67.2 L298.2,68.8 L305.1,70.5 L312.0,72.4 L318.8,74.4 L325.5,76.4 L332.3,78.6 L339.0,81.0 L345.6,83.4 L352.2,85.9 L358.8,88.6 L365.3,91.3 L371.8,94.2 L378.2,97.2 L384.6,100.3 L390.9,103.5" fill="none" stroke="currentColor"></path><path d="M16.0,87.0 L206.6,87.1 L213.1,87.2 L219.7,87.5 L226.3,87.9 L232.8,88.4 L239.4,89.0 L245.9,89.7 L252.4,90.6 L258.9,91.5 L265.4,92.6 L271.9,93.8 L278.3,95.1 L284.7,96.4 L291.1,97.9 L297.5,99.6 L303.9,101.3 L310.2,103.1 L316.5,105.0 L322.7,107.1 L328.9,109.2 L335.1,111.5 L341.2,113.8 L347.3,116.3 L353.4,118.9 L359.4,121.5 L365.3,124.3 L371.2,127.2 L377.1,130.2" fill="none" stroke="currentColor"></path><line x1="16" y1="45" x2="16" y2="99" stroke="currentColor" stroke-opacity="0.2"></line><line x1="371.6" y1="140.8" x2="396.4" y2="92.9" stroke="currentColor" stroke-opacity="0.2"></line><path d="M16.0,62.0 L87.4,87.0 L173.1,57.0 L287.9,97.2 L387.7,109.6 L397.7,110.9" marker-end="url(#tir-arrow)" fill="none" stroke="currentColor"></path><path d="M16,66 L31,87 L43,99 L72,128" marker-end="url(#tir-arrow-faint)" fill="none" stroke="currentColor"></path><line x1="248" y1="36" x2="241" y2="52" stroke="currentColor" stroke-opacity="0.2"></line><text x="250" y="34" text-anchor="middle" fill="currentColor">cladding · less dense glass</text> <line x1="175" y1="117" x2="175" y2="82" stroke="currentColor" stroke-opacity="0.2"></line><text x="175" y="126" text-anchor="middle" fill="currentColor">core · denser glass</text> <text x="118" y="112" text-anchor="middle" fill="currentColor">glancing hit: 100% reflected</text> <text x="78" y="140" fill="currentColor">too steep: refracts out and is lost</text> <text x="290" y="133" text-anchor="middle" fill="currentColor">trapped even in the bend</text></svg>

The slicing of light into independent channels has a name, **wavelength-division multiplexing**, and the simulator below shows it in action. Each laser keys its own bit stream onto its own wavelength of light, and a combiner feeds them all into one strand. Because the glass acts as a linear medium, the different waves superpose, literally adding their amplitudes together, and travel through the same core without mixing or interfering, allowing a splitter at the far end to filter each wavelength back out intact. Rather than trying to make a single laser blink faster, the strand simply carries several streams in parallel using different colors. Adding a wavelength multiplies the throughput of glass that is already lying on the seabed.

wavelength-division multiplexing

<svg viewBox="0 0 760 230" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Several lasers key independent bit streams onto carriers of different wavelengths; inside the shared fiber strand the waves superpose into one combined waveform, and a splitter filters each wavelength back out intact at the far end"><rect x="262" y="94" width="236" height="22" rx="11" fill="none" stroke="currentColor" stroke-width="1.5"></rect><text x="380" y="87" text-anchor="middle" font-size="9.5" fill="currentColor">one fiber strand, the waves add</text> <rect x="250" y="86" width="12" height="38" rx="2" fill="currentColor" stroke="currentColor" stroke-width="1.3"></rect><rect x="498" y="86" width="12" height="38" rx="2" fill="currentColor" stroke="currentColor" stroke-width="1.3"></rect><text x="256" y="138" text-anchor="middle" font-size="9" fill="currentColor">combine</text> <text x="504" y="138" text-anchor="middle" font-size="9" fill="currentColor">split</text> <line x1="262" y1="105" x2="498" y2="105" stroke="currentColor" stroke-width="1" stroke-dasharray="1.5,4" opacity="0.7"></line><g opacity="1"><line x1="95" y1="50" x2="250" y2="105" stroke="currentColor" stroke-width="1.2"></line><line x1="510" y1="105" x2="665" y2="50" stroke="currentColor" stroke-width="1.2"></line><circle cx="95" cy="50" r="5.5" fill="currentColor"></circle><circle cx="665" cy="50" r="5.5" fill="none" stroke="currentColor" stroke-width="1.5"></circle><text x="95" y="38" text-anchor="middle" font-size="10" font-weight="bold" fill="currentColor">λ1</text> <text x="665" y="38" text-anchor="middle" font-size="10" font-weight="bold" fill="currentColor">λ1</text> <g><rect x="11.5" y="42" width="11" height="16" rx="2" fill="currentColor" stroke="none" stroke-width="1"></rect><text x="17" y="53.5" text-anchor="middle" font-size="9" font-weight="bold" fill="currentColor">1</text></g> <g><rect x="24.5" y="42" width="11" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="1"></rect><text x="30" y="53.5" text-anchor="middle" font-size="9" font-weight="normal" fill="currentColor">0</text></g> <g><rect x="37.5" y="42" width="11" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="1"></rect><text x="43" y="53.5" text-anchor="middle" font-size="9" font-weight="normal" fill="currentColor">1</text></g> <g><rect x="50.5" y="42" width="11" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="1"></rect><text x="56" y="53.5" text-anchor="middle" font-size="9" font-weight="normal" fill="currentColor">1</text></g> <g><rect x="63.5" y="42" width="11" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="1"></rect><text x="69" y="53.5" text-anchor="middle" font-size="9" font-weight="normal" fill="currentColor">0</text></g> <g><rect x="679.5" y="42" width="11" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="1" stroke-dasharray="2,2"></rect></g><g><rect x="692.5" y="42" width="11" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="1" stroke-dasharray="2,2"></rect></g><g><rect x="705.5" y="42" width="11" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="1" stroke-dasharray="2,2"></rect></g><g><rect x="718.5" y="42" width="11" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="1" stroke-dasharray="2,2"></rect></g><g><rect x="731.5" y="42" width="11" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="1" stroke-dasharray="2,2"></rect></g></g><g opacity="1"><line x1="95" y1="105" x2="250" y2="105" stroke="currentColor" stroke-width="1.2"></line><line x1="510" y1="105" x2="665" y2="105" stroke="currentColor" stroke-width="1.2"></line><circle cx="95" cy="105" r="5.5" fill="currentColor"></circle><circle cx="665" cy="105" r="5.5" fill="none" stroke="currentColor" stroke-width="1.5"></circle><text x="95" y="93" text-anchor="middle" font-size="10" font-weight="bold" fill="currentColor">λ2</text> <text x="665" y="93" text-anchor="middle" font-size="10" font-weight="bold" fill="currentColor">λ2</text> <g><rect x="11.5" y="97" width="11" height="16" rx="2" fill="currentColor" stroke="none" stroke-width="1"></rect><text x="17" y="108.5" text-anchor="middle" font-size="9" font-weight="bold" fill="currentColor">0</text></g> <g><rect x="24.5" y="97" width="11" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="1"></rect><text x="30" y="108.5" text-anchor="middle" font-size="9" font-weight="normal" fill="currentColor">1</text></g> <g><rect x="37.5" y="97" width="11" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="1"></rect><text x="43" y="108.5" text-anchor="middle" font-size="9" font-weight="normal" fill="currentColor">1</text></g> <g><rect x="50.5" y="97" width="11" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="1"></rect><text x="56" y="108.5" text-anchor="middle" font-size="9" font-weight="normal" fill="currentColor">0</text></g> <g><rect x="63.5" y="97" width="11" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="1"></rect><text x="69" y="108.5" text-anchor="middle" font-size="9" font-weight="normal" fill="currentColor">1</text></g> <g><rect x="679.5" y="97" width="11" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="1" stroke-dasharray="2,2"></rect></g><g><rect x="692.5" y="97" width="11" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="1" stroke-dasharray="2,2"></rect></g><g><rect x="705.5" y="97" width="11" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="1" stroke-dasharray="2,2"></rect></g><g><rect x="718.5" y="97" width="11" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="1" stroke-dasharray="2,2"></rect></g><g><rect x="731.5" y="97" width="11" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="1" stroke-dasharray="2,2"></rect></g></g><g opacity="1"><line x1="95" y1="160" x2="250" y2="105" stroke="currentColor" stroke-width="1.2"></line><line x1="510" y1="105" x2="665" y2="160" stroke="currentColor" stroke-width="1.2"></line><circle cx="95" cy="160" r="5.5" fill="currentColor"></circle><circle cx="665" cy="160" r="5.5" fill="none" stroke="currentColor" stroke-width="1.5"></circle><text x="95" y="148" text-anchor="middle" font-size="10" font-weight="bold" fill="currentColor">λ3</text> <text x="665" y="148" text-anchor="middle" font-size="10" font-weight="bold" fill="currentColor">λ3</text> <g><rect x="11.5" y="152" width="11" height="16" rx="2" fill="currentColor" stroke="none" stroke-width="1"></rect><text x="17" y="163.5" text-anchor="middle" font-size="9" font-weight="bold" fill="currentColor">1</text></g> <g><rect x="24.5" y="152" width="11" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="1"></rect><text x="30" y="163.5" text-anchor="middle" font-size="9" font-weight="normal" fill="currentColor">1</text></g> <g><rect x="37.5" y="152" width="11" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="1"></rect><text x="43" y="163.5" text-anchor="middle" font-size="9" font-weight="normal" fill="currentColor">0</text></g> <g><rect x="50.5" y="152" width="11" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="1"></rect><text x="56" y="163.5" text-anchor="middle" font-size="9" font-weight="normal" fill="currentColor">1</text></g> <g><rect x="63.5" y="152" width="11" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="1"></rect><text x="69" y="163.5" text-anchor="middle" font-size="9" font-weight="normal" fill="currentColor">0</text></g> <g><rect x="679.5" y="152" width="11" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="1" stroke-dasharray="2,2"></rect></g><g><rect x="692.5" y="152" width="11" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="1" stroke-dasharray="2,2"></rect></g><g><rect x="705.5" y="152" width="11" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="1" stroke-dasharray="2,2"></rect></g><g><rect x="718.5" y="152" width="11" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="1" stroke-dasharray="2,2"></rect></g><g><rect x="731.5" y="152" width="11" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="1" stroke-dasharray="2,2"></rect></g></g><g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="" stroke-width="1.3"></path><path d="" stroke-width="1.3"></path><path d="" stroke-width="1" opacity="0.22"></path></g><g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="" stroke-width="1.3"></path><path d="" stroke-width="1.3"></path><path d="" stroke-width="1" opacity="0.22"></path></g><g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="" stroke-width="1.3"></path><path d="" stroke-width="1.3"></path><path d="" stroke-width="1" opacity="0.22"></path></g><path d="" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"></path><g><path d="M17.0 216.8L17.6 216.8L18.2 216.5L18.8 216.1L19.4 215.4L20.0 214.7L20.6 213.9L21.2 213.1L21.8 212.4L22.4 211.8L23.0 211.4L23.6 211.2L24.2 211.3L24.8 211.6L25.4 212.0L26.0 212.7L26.6 213.5L27.2 214.3L27.8 215.1L28.4 215.8L29.0 216.3L29.6 216.7L30.2 216.8L30.8 216.7L31.4 216.4L32.0 215.9L32.6 215.2L33.2 214.4L33.8 213.6L34.4 212.8L35.0 212.1L35.6 211.6L36.2 211.3L36.8 211.2" fill="none" stroke="currentColor" stroke-width="1.2"></path><path d="M43.0 216.4L43.6 215.1L44.2 213.4L44.8 211.9L45.4 211.2L46.0 211.6L46.6 212.9L47.2 214.6L47.8 216.1L48.4 216.8L49.0 216.4L49.6 215.1L50.2 213.4L50.8 211.9L51.4 211.2L52.0 211.6L52.6 212.9L53.2 214.6L53.8 216.1L54.4 216.8L55.0 216.4L55.6 215.1L56.2 213.4L56.8 211.9L57.4 211.2L58.0 211.6L58.6 212.9L59.2 214.6L59.8 216.1L60.4 216.8L61.0 216.4L61.6 215.1L62.2 213.4L62.8 211.9" fill="none" stroke="currentColor" stroke-width="1.2"></path><text x="69" y="217.5" font-size="9" fill="currentColor">laser on = 1, laser off = 0, each channel its own wavelength, bold line in the strand = sum of the carriers</text></g></svg>

Status:Each laser keys its own bit stream onto its own wavelength of light.

Capacity:3 wavelengths, the same strand now carries 3× the bits per second.

wavelengths3 lasers, same strand

Every stream keeps its own bit rate; adding a wavelength adds a whole extra stream through glass that is already there. Real systems pack about a hundred wavelengths into each strand.

![World map showing the routes of submarine communication cables as thin lines connecting continents across every ocean](https://fazamhd.com/_astro/submarine-cable-map.CDu555vY.png)

The submarine cable network as of 2015, nearly every populated coastline stitched to every other by fiber laid along the ocean floor. (Cable data: Greg Mahlknecht, map: OpenStreetMap contributors, CC BY-SA 2.0)

Nothing in BGP’s mechanism says an address has to be announced from only one place, and giving that up on purpose is how **anycast** works. Multiple servers, often on different continents, are all configured with the identical IP address, and each one’s network announces a route to it exactly as if it were the sole owner. BGP doesn’t know or care that it’s hearing the same address from São Paulo, London, and Tokyo at once, it just does what it always does, keeps whichever announcement has the shortest path, which in practice means each client’s traffic lands on whichever copy is topologically nearest to it. Two people in different cities, requesting the same address, get routed to different physical machines, with nothing about the DNS lookup or the client’s own configuration hinting that this happened. Watch three clients, on three different continents, send to the same address and each land on a different server.

anycast, one address, many machines

client · Lisbon

edge · São Paulo

203.0.113.5

edge · London

203.0.113.5

edge · Tokyo

203.0.113.5

Every edge server on the map answers to the same address, 203.0.113.5. Watch clients on three continents reach three different machines without knowing it.

This routing-level approach, directing traffic to the nearest machine sharing a single IP address, is one of two key techniques behind a **content delivery network (CDN)**. CDNs like Cloudflare (this site included) or Akamai run copies of the same content, video, images, whole websites, on servers scattered across the globe specifically so requests get answered from nearby hardware instead of one, possibly distant, origin server. The other technique, often layered on top or used instead is simpler, geo-aware name servers that look at where a query came from and hand back the address of a nearby data center rather than the same answer to everyone, a trick that lives inside DNS, the naming system in [Remembering Names Instead of Numbers](#remembering-names-instead-of-numbers). Either way, the payoff traces straight back to the very first idea in this article, latency is a floor set by the speed of light, and the only way to beat it is to move the data closer to the reader before they ask.

BGP’s design is startlingly trusting, networks largely believe what their neighbors announce. In 2008, Pakistan Telecom, intending to block YouTube domestically, announced a more specific route to YouTube’s addresses than YouTube’s own. The announcement leaked past its borders, propagated worldwide in minutes, and much of the planet’s YouTube traffic obediently flowed into Pakistan and vanished. Incidents like this are why a service can occasionally disappear from half the world at once. They are also why engineers have spent years building cryptographic verification into BGP, an effort called **RPKI** (Resource Public Key Infrastructure) that lets a router check a route announcement against a signed registry rather than taking it on faith. What a cryptographic signature is, and why it can be checked but not forged, is exactly the machinery we’ll build up in [Exchanging Secrets over Public Wires](#exchanging-secrets-over-public-wires).

## Your Private Home Network

Your home compresses several of these ideas into one plastic box. The router on your shelf runs a small Ethernet switch, the same MAC-learning trick from [One Shared Wire for the Whole Office](#one-shared-wire-for-the-whole-office), plus a Wi-Fi radio for the wireless side; it hands each device an address when it joins, via the DHCP broadcast from [Connecting the Networks](#connecting-the-networks), and the same reply carries the two other things a fresh device needs and nobody ever types in, the gateway to send off-subnet traffic to and the address of a DNS resolver (the name-lookup system we will explore in [Remembering Names Instead of Numbers](#remembering-names-instead-of-numbers)). And, because 32-bit IPv4 addresses ran scarce, those are *private* addresses that mean nothing outside your home. A handful of blocks are set aside by convention for exactly this, never handed out publicly and never routed across the internet, which is what lets every one of them be reused endlessly. One more reserved block rides along in the table below, addresses your machine keeps entirely to itself, and we’ll come back to it in a moment.

block

block size

scope

typical use

where packets go

10.0.0.0/8

16,777,216

private

large organizations

stays inside one private network

172.16.0.0/12

1,048,576

private

mid-sized networks

stays inside one private network

192.168.0.0/16

65,536

private

home routers

stays inside one private network

127.0.0.0/8

16,777,216

loopback

this machine

never reaches the network card

None of the first three is ever routed on the public internet, so your router’s `192.168.1.5` and a stranger’s `192.168.1.5` on the other side of the planet are different devices that never once collide, because neither packet carrying that address ever leaves the private network it was issued on. The router shares its single public address, itself assigned by your ISP’s DHCP, the same mechanism one network up, among all your devices by rewriting the addresses on packets as they pass through, **NAT** (Network Address Translation), keeping a table of which inside conversation each outside reply belongs to. Watch two unrelated homes reuse the identical private address and see why NAT keeps them from ever colliding, then watch a second device in one home share its router’s single public address.

NAT

private lan a

private lan b

public internet

laptop192.168.1.5

phone192.168.1.23

router · nat203.0.113.7

laptop192.168.1.5

router · nat198.51.100.42

web server

nat table empty

nat table empty

Two unrelated homes. Both laptops were handed the identical private address 192.168.1.5 by their own router; home A has a second device besides.

two homes behind NAT, src is each packet's source address and port

NAT has a blind spot that quietly reshaped the internet. Because the router only records conversations started from the inside, it drops all unsolicited incoming traffic. This kills the symmetrical server role, your laptop can reach any server, but nothing can reach your laptop uninvited. It is why hosting from home requires manually setting up “port forwarding” (telling the router which internal machine should receive outside traffic on a specific port), and tracking your public IP address as your ISP periodically rotates it to save addresses. It is also why peer-to-peer apps like video calls must use complex workarounds (like having both sides send packets at once so both routers think their user started the conversation) to connect directly. A temporary workaround for address scarcity ended up sorting the internet into two classes, those that serve, and those that only ask.

The last row, `127.0.0.0/8`, is more local still, a packet sent to `127.0.0.1`, conventionally called **localhost**, never reaches your network card at all. Your own operating system loops it straight back to whatever is listening on your own machine, which is why a development server you start on your laptop answers at `127.0.0.1:3000` from that laptop, and nowhere else on Earth. And it isn’t just `127.0.0.1`, the entire block loops back, all 16.7 million addresses of it, the same size as the largest private block, reserved for talking to exactly one machine, an extravagance from an era when nobody imagined 32 bits of address space could run out.

One layering detail is worth keeping, your device carries two addresses at once, a **MAC address** belonging to its network hardware, saying *which machine on this cable or channel*, and an IP address, assigned by whichever network you join, meaningful end to end. The MAC address never leaves your local network; the IP address is what the far end of the world routes on. We will see both riding in the same packet when we trace a click end to end in [What Actually Happens When You Click a Link](#what-actually-happens-when-you-click-a-link).

## Remembering Names Instead of Numbers

Routers deliver packets to numeric addresses like `208.80.154.224`, but those numbers are nearly impossible for us to memorize. Without names, you would need a personal diary just to keep track of the IP addresses of websites you like to visit. In the ARPANET days, the entire mapping lived in one file, `HOSTS.TXT`, maintained by hand at the Stanford Research Institute under Elizabeth Feinler, and every computer on the network periodically downloaded a fresh copy. By the early 1980s this was failing exactly as you’d expect, one office editing one file could not keep pace with an exponentially growing network, and everyone fetching that file from one place was itself a bottleneck.

These are a few lines from the 27 March 1984 version of that file, one entry per machine, listing its address (or addresses), its names, its hardware and operating system, and the protocols it spoke, every field curated by hand.

```txt
; DoD Internet Host Table
;  27-Mar-84
;
; Changes, corrections, comments or questions to (HOSTMASTER@SRI-NIC)

NET : 10.0.0.0 : ARPANET :
HOST : 10.0.0.51, 26.0.0.73 : SRI-NIC.ARPA,SRI-NIC,NIC : DEC-2060 : TOPS20 : TCP/TELNET,TCP/SMTP,TCP/TIME,TCP/FTP,TCP/ECHO,ICMP :
HOST : 10.0.0.1 : UCLA-CS.ARPA,UCLA-CS,UCLA-CECS : VAX-11/750 : LOCUS : TCP/TELNET,TCP/FTP,TCP/SMTP :
HOST : 10.0.0.6 : MIT-MULTICS.ARPA,MIT-MULTICS,MULTICS : HONEYWELL-DPS-8/70M : MULTICS : TCP/TELNET,TCP/SMTP,TCP/FTP,TCP/FINGER,TCP/ECHO,TCP/DISCARD,ICMP :
HOST : 10.0.0.4, 192.5.12.21 : UTAH-CS.ARPA,UTAH-CS : VAX-11/750 : UNIX : TCP/TELNET,TCP/FTP,TCP/SMTP :
```

The first entry is the file describing its own home: `SRI-NIC` is the very machine everyone fetched `HOSTS.TXT` from, and `HOSTMASTER@SRI-NIC` in the header was Feinler’s group. To look up a name, a computer simply searched its local copy of this file, and any machine missing from the file effectively did not exist.

In 1983, **Paul Mockapetris** designed its replacement, the **Domain Name System (DNS)**, built on delegation. The namespace is a hierarchy read right to left, for `en.wikipedia.org`, the root of the hierarchy knows only who runs top-level domains like `org`; the `org` servers know only who runs `wikipedia.org`; and Wikipedia’s own name servers hold the actual answer for `en.wikipedia.org`. Nobody stores the whole map; instead, the namespace is partitioned into administrative boundaries called **zones**. Each organization controls the authoritative name servers for its own zone (e.g., a company managing `yourdomain.com`) and can change its records or delegate sub-zones (like `sub.yourdomain.com`) to others without asking anyone. To look up a name, your device asks a **recursive resolver**, typically run by your internet provider or a public one like Cloudflare’s `1.1.1.1`, which walks the chain of delegations on your behalf and returns the final address.

Walking that chain for `en.wikipedia.org` looks like this, each answer telling the resolver exactly one step further down:

1. Resolver asks a **root server**: “who is `en.wikipedia.org`?” Root doesn’t know, but answers: “I don’t hold `org`, but here’s who does,” and hands back the address of the `.org` name servers.
2. Resolver asks an **`.org` server** the same question. It doesn’t know `en.wikipedia.org` either, but answers: “Wikipedia runs its own servers, here they are,” and hands back the address of `wikipedia.org` ’s name servers.
3. Resolver asks **Wikipedia’s own name server**, the last delegation in the chain, and finally gets a real answer: `en.wikipedia.org` is at `91.198.174.192`, valid for 3600 seconds.

That `3600` is also called a **TTL**, confusingly, the same three letters as the IP hop counter earlier, but here it means a lifetime in seconds, not a number of routers, permission to cache the answer for an hour before asking again. The resolver hands `91.198.174.192` back to your browser, and every other request for `en.wikipedia.org` from anyone using that resolver is answered instantly from the cache, no chain to walk, until the hour is up.

At the internet’s scale, walking that chain for every lookup would crush the upper levels, so every answer carries a TTL and is **cached** close to the asker, by the browser or operating system, and especially by the recursive resolver serving many people. A home router may forward DNS or run a resolver too, but ordinary packet routing has nothing to do with the cache. Popular names are almost always answered from a cache a few milliseconds away, and the root servers rarely hear about anything twice.

DNS, name resolution

another device

your device

resolver

root ns

.org ns

wikipedia ns

web server91.198.174.192

cache empty

cache empty

One lookup walks the chain of delegations; every lookup after it, from this device or any other behind the same resolver, is answered from a cache, until the TTL runs out.

resolving en.wikipedia.org, the one-hour ttl runs accelerated

That walk isn’t hidden machinery, you can run it yourself. Below, the same three delegations are asked by hand with `dig`, the standard DNS query tool, one question per server, the root answers with the `.org` servers, `.org` answers with Wikipedia’s own name servers, and those finally answer with an address, exactly the chain the simulator just walked.

terminal recordingdig en.wikipedia.org

DNS has done exactly one job, turn the name into a number. With `91.198.174.192` in hand, your browser can finally open a connection to that address, conventionally on port `443` for the encrypted web. The next packets are no longer DNS questions; they are TCP packets addressed to the web server, which is the handoff the simulator shows at the end.

None of that hierarchy is automatic to join, and it’s worth seeing how a name gets onto it, since the mechanism is just more delegation. You buy `yourdomain.com` from a **registrar**, an accredited reseller for whichever **registry** runs that top-level domain, Verisign for `.com`. The registrar’s actual job is one write into the registry’s zone, an **NS record** naming the name servers you’ve designated as authoritative for your domain, the exact delegation a resolver follows when it asks the `.com` servers who runs your name. Those name servers, run by your registrar, a provider like Cloudflare or Route 53, or a machine of your own, hold your domain’s **zone file**, records you control directly. The one that answers “how do I point my domain at my server” is the **A record** (or **AAAA** for IPv6), a line stating that `yourdomain.com` lives at, say, `192.0.2.7`. Add it, wait out whatever TTL the last answer was cached under, and every resolver on Earth starts sending traffic for your name to your machine; no approval needed, just one write into a chain of delegations built for exactly this. This last step is also where a CDN’s geo-aware trick from the anycast section lives, nothing forces a name server to give every asker the same answer, so it’s free to reply with whichever data center’s address sits closest to the query.

The price of caching is staleness. When a site moves to a new address, the old answer lingers in caches worldwide until its TTL runs out. This lag is why DNS changes take time to propagate, and why a surprising fraction of mysterious outages, in home networks and billion-dollar clouds alike, trace back to DNS. Because a name lookup is the first step of nearly every connection, it remains the silent, load-bearing foundation of the entire internet.

DNS as designed in 1983 carries the same unguarded trust BGP does, when a resolver asks a question, it simply believes whichever answer arrives first, matching the query it sent. In 2008, researcher Dan Kaminsky showed just how little it took to abuse that. A resolver identifies which answer belongs to which question with a 16-bit transaction ID, only 65,536 possibilities, and an attacker who can guess it before the real answer arrives can hand the resolver a forged reply instead, one that doesn’t just answer the question asked, but tacks on an unrequested bonus, “and by the way, here are the real name servers for the rest of `yourbank.com`, from now on, ask them.” A resolver has no reason to be suspicious of a gift it didn’t ask for and takes it anyway. Get there first, and the resolver caches the lie for as long as its attacker-chosen TTL says to, quietly redirecting every one of that resolver’s users, for that entire domain, not just the one name that was queried.

The fix, **DNSSEC** (Domain Name System Security Extensions), closes the gap, each zone cryptographically signs its own records, and a resolver validates the signature chain up to a root key it already trusts (using the same signature concepts we will cover in [Exchanging Secrets over Public Wires](#exchanging-secrets-over-public-wires)). A forged answer without a valid signature is simply discarded, unbelieved. It has been available for over a decade, and like IPv6, adoption is still catching up to the incentive to run it.

Crucially, DNSSEC only guarantees *authenticity* (that the answer wasn’t tampered with); it does not encrypt the query, so anyone along the path can still see which domains you are looking up. To close this privacy gap, modern operating systems and browsers increasingly encrypt the lookup itself by wrapping DNS queries inside TLS or HTTP, protocols known as **DNS over TLS (DoT)** and **DNS over HTTPS (DoH)**.

## Creating a User Interface for the Internet

By the end of the 1980s the plumbing was complete, IP routed packets worldwide, TCP made delivery reliable, Ethernet wired up buildings, DNS resolved names. Yet the internet remained a specialist’s tool. Retrieving information meant knowing which machine held it, then driving command-line tools to log in or transfer files. The infrastructure could move bytes anywhere; what it lacked was a way for a non-expert to *find and read* anything.

In 1989, **Tim Berners-Lee**, a software engineer at CERN, the European particle physics laboratory, proposed a document-sharing system for scientists, and by 1991 the **World Wide Web** was running. It rested on three deliberately simple inventions:

1. **HTML** (HyperText Markup Language), a document format whose defining feature is the *link*, any word in any document can point at any other document, anywhere on the internet.
2. **URL** (Uniform Resource Locator), a global address for a document (like `https://en.wikipedia.org/wiki/Internet`), naming the protocol (`https`), the server (`en.wikipedia.org`, resolved via DNS), and the document’s path on it (`/wiki/Internet`). One piece is missing on purpose, the port. Each protocol carries a **default port**, `443` for `https` and `80` for plain `http`, so the browser fills it in from the scheme, and `https://en.wikipedia.org:443/wiki/Internet` is the same address written out in full. That’s why typing a bare address into a browser just works, the scheme alone tells it which door to knock on.
3. **HTTP** (HyperText Transfer Protocol), a minimal request-response protocol on top of TCP, the client says `GET /page`, and the server’s reply opens with a **status code** before the document itself, `200 OK` when it succeeds, `404 Not Found` when the requested document does not exist, and `500 Internal Server Error` when the server itself runs into a problem.

Each piece leans on a layer we have already built, URLs lean on DNS, HTTP leans on TCP, TCP leans on IP. Berners-Lee didn’t have to ask permission or upgrade a single router; the layers below were already there, and anyone was free to build on top of them. That permissionless quality, a direct consequence of keeping the network’s middle simple and its intelligence at the edges, is why the web went from one machine at CERN to the world in a few years, and why a student’s video-calling experiment or a new webapp can deploy globally today without anyone’s approval.

The openness runs deeper than the architecture, it’s written down. Every protocol in this article, IP, TCP, DNS, HTTP, is specified in an **RFC** (Request for Comments), a freely readable document anyone can implement without paying a fee or asking a license. The modest name is original, the first RFCs in 1969 really were memos circulated among the ARPANET’s builders inviting comment, and the culture they set persisted as the informal process hardened into the **IETF** (Internet Engineering Task Force), the volunteer body that has standardized internet protocols since 1986. Even the well-known defaults are just RFC text made habit, port `80` and port `443` are simply the numbers the relevant RFCs registered with IANA for HTTP and HTTPS. This is what “open standard” means concretely, the complete rules of the internet sit in public documents, and a compatible implementation, whether a browser, a server, or an operating system’s TCP stack, is anyone’s to write.

![The first web server, Tim Berners-Lee's NeXT computer at CERN](https://fazamhd.com/_astro/first-web-server.DQcHJQTe.jpg)

Tim Berners-Lee’s NeXT workstation at CERN, the world’s first web server. The note reads: “This machine is a server. DO NOT POWER IT DOWN!!” (Source: CERN)

The web reached the public through graphical browsers, **NCSA Mosaic** (1993), built by Marc Andreessen and Eric Bina at the University of Illinois, put images alongside text and made the web feel like a place rather than a protocol, and **Netscape Navigator** (1994), from the same team gone commercial, carried it into homes and set off the dot-com boom. What browsers themselves grew into, a second operating system running strangers’ code safely, is the subject of the upcoming web browser article; here, one more problem the web’s success exposed needs solving first.

![NCSA Mosaic Browser (1993)](https://fazamhd.com/_astro/ncsa-mosaic.7yiernKp.png)

NCSA Mosaic (1993)

![Netscape Navigator (1994)](https://fazamhd.com/_astro/netscape-navigator.DwunNccB.png)

Netscape Navigator (1994)

The graphical browsers that turned the web from a research utility into a consumer phenomenon. (Source: Wikimedia Commons)

## Exchanging Secrets over Public Wires

Commerce followed the browsers, and commerce collided with an assumption baked in from the ARPANET days, every protocol so far sends data as plain, readable bytes. Your packets pass through your router, your internet provider, and a dozen networks owned by strangers, and any machine along the path can read every byte, or quietly alter it in transit. That was tolerable among research labs sharing physics papers. It is intolerable for a credit card number.

Strip the problem to first principles and it looks unsolvable, two parties who have never met must agree on a secret, while communicating only over a channel that everyone can read. Anything one sends the other to establish the secret, an eavesdropper sees too.

The way out is **public-key cryptography**, developed in the 1970s. Certain mathematical operations are easy to perform but computationally infeasible to reverse, and from these you can build a **key pair**, two linked keys where data encrypted with one can only be decrypted with the other. The **public key** you hand to the world; the **private key** never leaves your server. Now anyone can encrypt a message that only you can read, with no prior secret, the eavesdropper sees the public key and the scrambled traffic and can do nothing with either. The same pair works in reverse: instead of encrypting a message that only the private key can decrypt, you can use the private key to generate a proof that anyone holding the public key can verify. Useless for secrecy, but it proves the private key’s holder issued it, because nobody else could have. That is a **signature**, a statement only you could have made and anyone can check. Two details separate this picture from real signatures, you sign a **hash** of the message, a short fingerprint computed from every byte of it, so the signature also proves nothing was altered along the way; and modern schemes, ECDSA and Ed25519 among them, reach the same guarantee through different mathematics than traditional RSA. The contract is what survives every change of scheme, the private key signs, the public key verifies, and the signature binds the exact bytes signed.

One gap remains. When your browser receives a public key claiming to belong to your bank, who vouches for that claim? An attacker sitting in the middle could present *their* key instead and decrypt everything. This is closed by **certificates**. A small set of organizations called **certificate authorities**, whose own public keys ship inside every browser, verify a server’s identity and cryptographically sign a statement binding that identity to its public key; that signed statement is the certificate. A certificate is rarely signed directly by one of those, instead it’s signed by an intermediate authority, whose own certificate is signed by the root, so your browser doesn’t check one signature, it **checks a chain**, climbing from the certificate in hand up through each issuer until it either reaches a root it already carries, verified, or runs out of chain to climb, which produces the full-page security warnings you have seen. Watch the browser walk that chain, once when it succeeds and once when it doesn’t.

TLS certificate chain of trust

en.wikipedia.org

the certificate the server presents

signed by

DigiCert TLS Hybrid ECC SHA384 2020 CA1

intermediate authority, not itself trusted

signed by

DigiCert Global Root CA

ships inside the browser, already trusted

✓ chain verified

browser trust store

DigiCert Global Root CA

GlobalSign Root R1

ISRG Root X1

When a server presents a certificate, the browser doesn't trust it directly, it climbs the signing chain until it reaches something it already trusts, or runs out of chain.

Netscape assembled these pieces into **SSL** (Secure Sockets Layer) in 1994, later standardized as **TLS** (Transport Layer Security). It slots cleanly between TCP and HTTP: at the start of a connection, browser and server perform a **handshake**. The key agreement at its heart is **Diffie-Hellman**, and I’ll explain the concept using small numbers.

Both sides start from two public constants, here g = 5 and p = 23. The browser opens with a `ClientHello` proposing ciphers, and alongside it a **key share**, computed from a private number it picks and never sends, say a = 6, giving the share A = 5⁶ mod 23 = 8. The server picks its own private number, say b = 15, and answers with its chosen cipher, its certificate, and its own share B = 5¹⁵ mod 23 = 19, signed with the certificate’s private key, so a machine in the middle cannot swap in a share it controls. Then each side raises the share it received to its own private number, the browser computes 19⁶ mod 23 = 2, the server computes 8¹⁵ mod 23 = 2, and they land on the same value because both are 5⁹⁰ mod 23. That value is the **session key**, computed independently at both ends and never sent across a wire that carried only 8 and 19.

An eavesdropper holding both shares must recover a private number to get any further, which power of 5 gives 8, mod 23? That is the **discrete logarithm problem**, answerable by trial at this size, computationally infeasible at real sizes, where p runs to hundreds of digits. What browsers actually run is the elliptic-curve variant of the same exchange, which swaps modular exponentiation for point arithmetic on a curve, a different one-way operation that reaches equivalent security with far smaller numbers, and changes nothing else, the same private numbers kept, the same shares exchanged, the same key derived independently at both ends. Watch the exchange run with an eavesdropper on the wire, recording every number that crosses and still ending up with nothing.

Diffie-Hellman, the key exchange

browser

server

g = 5, p = 23 · public

a = 6 · private

A = 5⁶ mod 23 = 8

Bᵃ = 19⁶ mod 23 = 2

b = 15 · private

B = 5¹⁵ mod 23 = 19

Aᵇ = 8¹⁵ mod 23 = 2

eavesdropper · reads everything on the wire

g = 5, p = 23

A = 8

B = 19

✕ 5ˣ mod 23 = 8 → x =? · infeasible at real sizes

Two machines that have never met must land on the same secret number, over a wire someone else reads end to end. Watch the arithmetic pull it off.

Public-key math is too slow to run on every byte of a conversation, so it is only ever used for this one exchange; the session key is a plain **symmetric key**, the same key encrypts and decrypts, cheap enough to run on the full request and response, and both sides encrypt everything both ways with it from here on.

HTTP spoken through this channel is **HTTPS**, and the padlock in your address bar means exactly this and no more, the machines between you and the server can still see *which* server you talk to, when, and how much data moves, but not *what* is said. Your passwords and messages cross hostile territory unreadable, which is why the web has moved almost entirely to HTTPS and browsers now flag plain HTTP as a defect. Here is that whole exchange, ending in the encrypted request and response it exists to protect.

TLS, the handshake

browser

server

g = 5, p = 23 · public

a = 6 · private, never sent

Bᵃ = 19⁶ mod 23 = 2

b = 15 · private, never sent

Aᵇ = 8¹⁵ mod 23 = 2

Before any HTTP request goes out, browser and server must agree on an encryption key over a wire anyone can read, starting from no shared secret. Watch how.

Notice what’s actually happening to the bytes as they leave your machine to make this possible. Each layer wraps the layer above it in its own header, and unwraps only its own layer on arrival. An HTTP request ends up riding inside a TLS record, inside a TCP segment, inside an IP packet, inside an Ethernet or Wi-Fi frame, one parcel inside another, and at every hop along the way, a router or switch touches only the outermost wrapper. The simulator below builds up that nesting layer by layer.

your device

home router

server

GET /wiki/…

A request is wrapped in one header per layer, carried hop by hop, and unwrapped at the far end.

The same machinery, pushed one layer down, gives you the **VPN** (Virtual Private Network). Where TLS encrypts one application’s byte stream, a VPN encrypts entire IP packets and wraps each one inside a new packet addressed to the VPN server, encapsulation again, a whole packet riding as the payload of another. All your traffic detours through that server, which unwraps each packet and forwards it onward as if it had originated there. Notice precisely what this changes, your internet provider now sees only encrypted traffic to one address, and the sites you visit see the VPN server’s address instead of yours, but the VPN operator inherits exactly the view your provider used to have. A VPN does not add security in some absolute sense; it relocates the point of trust, which is why *who runs the server* matters more than any encryption claim in the marketing.

The construction’s original purpose was corporate, and still is, a remote laptop tunneling into the office network behaves as though it were plugged in at a desk there, private addresses and all. The simulator below traces one request through the tunnel, watch what each party along the path can actually read.

vpn, a packet inside a packet

your device

your isp

vpn server

the site

IP·site

TCP·443

TLS

▚▞▚▞▚

A VPN encrypts your entire packet and hides it inside a second packet addressed to the VPN server.

## What Actually Happens When You Click a Link

All of these protocols run, essentially unchanged, every time you load a page. Tracing one click from end to end:

1. You click a link pointing to `https://en.wikipedia.org`. Your browser extracts the hostname and asks DNS for its IP address, which is answered in milliseconds from a nearby cache or by walking the hierarchy.
2. Your browser opens a TCP connection to that address on port 443, the same three-way handshake from the reliability section, three segments agreeing on byte numbering before any data flows.
3. The TLS handshake runs over that connection, the certificate is checked, a session key agreed.
4. The browser sends its encrypted request, `GET /wiki/Internet`.
5. The response, hundreds of kilobytes of HTML, returns as dozens of IP packets, individually routed, possibly reordered, occasionally lost and retransmitted, reassembled by TCP into an exact byte stream, decrypted by TLS, and parsed and painted by the browser.

recap

t = 0 ms1/7 · the click

round trips 0 · page 0 of 560 KB <svg viewBox="0 0 760 240" preserveAspectRatio="xMidYMid meet" aria-hidden="true"><g opacity="1"><line x1="204" y1="130" x2="682" y2="130" stroke="currentColor" stroke-width="1.2" vector-effect="non-scaling-stroke"></line><rect x="316" y="126" width="8" height="8" fill="currentColor" stroke="currentColor" stroke-width="1.1" vector-effect="non-scaling-stroke"></rect><rect x="406" y="126" width="8" height="8" fill="currentColor" stroke="currentColor" stroke-width="1.1" vector-effect="non-scaling-stroke"></rect><rect x="496" y="126" width="8" height="8" fill="currentColor" stroke="currentColor" stroke-width="1.1" vector-effect="non-scaling-stroke"></rect><rect x="586" y="126" width="8" height="8" fill="currentColor" stroke="currentColor" stroke-width="1.1" vector-effect="non-scaling-stroke"></rect><polyline points="204,130 248,130 300,74" fill="none" stroke="currentColor" stroke-width="1" stroke-dasharray="3 3" vector-effect="non-scaling-stroke"></polyline><rect x="290" y="50" width="20" height="20" fill="currentColor" stroke="currentColor" stroke-width="1.4" vector-effect="non-scaling-stroke"></rect><text x="300" y="42" text-anchor="middle" font-size="10" fill="currentColor">DNS resolver, nearby</text> <g><rect x="695" y="114" width="22" height="32" fill="currentColor" stroke="currentColor" stroke-width="1.4" vector-effect="non-scaling-stroke"></rect><line x1="699" y1="122" x2="713" y2="122" stroke="currentColor" stroke-width="1"></line><line x1="699" y1="130" x2="713" y2="130" stroke="currentColor" stroke-width="1"></line><line x1="699" y1="138" x2="713" y2="138" stroke="currentColor" stroke-width="1"></line><text x="706" y="160" text-anchor="middle" font-size="10" fill="currentColor">nearest data center</text> <text x="706" y="173" text-anchor="middle" font-size="9" fill="currentColor" style="font-variant-numeric:tabular-nums">198.35.26.96</text></g> <g><rect x="24" y="34" width="180" height="178" rx="3" fill="currentColor" stroke="currentColor" stroke-width="1.6" vector-effect="non-scaling-stroke"></rect><line x1="24" y1="52" x2="204" y2="52" stroke="currentColor" stroke-width="1"></line><circle cx="34" cy="43" r="2.2" fill="none" stroke="currentColor" stroke-width="1"></circle><circle cx="43" cy="43" r="2.2" fill="none" stroke="currentColor" stroke-width="1"></circle><circle cx="52" cy="43" r="2.2" fill="none" stroke="currentColor" stroke-width="1"></circle><rect x="34" y="59" width="160" height="15" rx="2" fill="none" stroke="currentColor" stroke-width="1" vector-effect="non-scaling-stroke"></rect><g stroke="currentColor" stroke-width="1.1" fill="none"><rect x="39" y="65" width="6" height="5" fill="currentColor" stroke="none"></rect><path d="M 40.5 65 v -2 a 1.5 1.5 0 0 1 3 0 v 2"></path></g><text x="50" y="70" font-size="9" fill="currentColor">google.com</text> <g><rect x="34" y="86" width="160" height="13" rx="6.5" fill="none" stroke="currentColor" stroke-width="1" vector-effect="non-scaling-stroke"></rect><text x="42" y="95.5" font-size="8.5" fill="currentColor">internet</text> <text x="36" y="118" font-size="8.5" fill="currentColor" text-decoration="underline">Internet — Wikipedia</text><rect x="36" y="124" width="140" height="3.5" fill="currentColor"></rect><rect x="36" y="132" width="116" height="3.5" fill="currentColor"></rect><g><rect x="36" y="148" width="94" height="5" fill="currentColor"></rect><rect x="36" y="158" width="144" height="3.5" fill="currentColor"></rect></g><g><rect x="36" y="178" width="94" height="5" fill="currentColor"></rect><rect x="36" y="188" width="118" height="3.5" fill="currentColor"></rect></g></g></g></g></svg>

You click a search result. This browser has never talked to en.wikipedia.org, nothing cached, no connection open, so every layer must run once.

A first visit to a new site, clicked from a search results page, the one case where every layer runs. Each message crosses the same routers, cables, and owners as the opening simulation (the small unlabeled squares stand in for them). Outlined packets are plaintext handshakes; filled ones are ciphertext. Timings assume a cached DNS answer and a ~24 ms round trip to the server, real numbers vary, but the idea is same.

![Aerial view of a Google data center campus in Mayes County, Oklahoma, a vast white-roofed server building dwarfing the roads and fields around it](https://fazamhd.com/_astro/google-datacenter-aerial.DdQp6_r-.jpg)

Google’s data center campus in Mayes County, Oklahoma. (Photo: Xpda, CC BY-SA 4.0)

![Densely populated rows of server racks with flashing indicators and green/yellow network cables in a large server room at CERN](https://fazamhd.com/_astro/datacenter-server-racks.B2pSHxG_.jpg)

Server room in CERN (Switzerland). (Photo: Florian Hirzinger / www.fh-ap.com, CC BY-SA 3.0)

The physical scale of the internet: Google’s Mayes County campus holds tens of thousands of servers inside its massive halls, organized into dense rows of server racks similar to the CERN computer centre above. Somewhere inside a facility like this, one of these machines receives the request in step 4 and sends back the page in step 5. (Photos: Wikimedia Commons)

This chain is also the diagnostic the introduction promised, whether a dead page is the website’s fault or something local, because each step fails in its own recognizable way. If nothing loads on any site, the failure sits in front of step 1, your Wi-Fi, your router, or your provider’s link, and a `ping` to an address you know, like `1.1.1.1`, tells you in one round trip whether you can reach past your own walls. If other sites work but this name won’t resolve, the problem is DNS, a stale cache or the site’s own records. If the name resolves but the connection in step 2 times out, the server or a network on the way to it is down, and `traceroute` shows how far your packets get before they die. A full-page certificate warning is step 3 failing, the chain climb from the certificate section refusing to reach a trusted root. And if all of it succeeds and the reply comes back `500`, your request crossed the world intact; the failure is finally, provably, inside the server itself.

Notice steps 1 through 3 are pure round trips, latency paid before a single byte of the page moves, which is why even a fast connection can feel sluggish to start. And notice that the `GET` request in step 4 is riding inside exactly the nesting the earlier simulator built up, HTTP inside TLS inside TCP inside IP inside an Ethernet or Wi-Fi frame, unwrapped one layer at a time as it arrives. If we peel back the encryption, the headers on that single packet, just a sequence of raw bytes, contain every instruction needed to guide it across the world.

ver/ihl

45

IPv4

tos

00

···

total length

00 3C

60 bytes

identification

1C 46

···

flags/offset

40 00

don't fragment

ttl

36

54 hops left

protocol

06

6 = TCP

source address

CB 00 71 07

203.0.113.7

destination address

5B C6 AE C0

91.198.174.192

source port

D3 C3

54211

destination port

01 BB

443

sequence number

00 00 13 89

byte offset 5001

ack number

00 00 23 29

next byte expected: 9001

offset/flags

50 18

ACK, PSH set

window size

FF FF

sliding window

checksum

8A 2F

catches corruption

urgent ptr

00 00

···

highlighted fields are the ones this article names — the rest are real bytes every packet carries, just not ones we've had a reason to open yet

Every router between you and Wikipedia reads only the IP row, matches the destination address against its table, and forwards, exactly as the routing-table example above, it never looks past byte 20. TCP’s row is invisible to them, opened only at the two endpoints; TLS encrypts the payload those headers are wrapped around, but never the headers themselves, which is why an eavesdropper can see *which server* and *how much data*, the point made earlier about HTTPS, without seeing the request.

layer

protocols

unit

job

origin

Application

HTTP, DNS

—

user-facing meaning: documents, lookups

Berners-Lee, 1991

Security

TLS

—

encrypt & authenticate the wire

Netscape (SSL), 1994

Transport

TCP, UDP

segment (TCP) · datagram (UDP)

reliable streams; deliver to the right program

Cerf & Kahn, 1973

Network

IP

packet

route hop by hop across any set of networks

Baran & Davies, 1960s

Link / Physical

Ethernet, Wi-Fi, fiber

frame

move bits across one local medium

Metcalfe, 1973

Reading the table bottom-up summarizes this article, each layer exists to hide a specific limitation of the layer beneath it. The link layer hides the physics of shared cables and crowded airwaves. IP hides the boundaries between thousands of separately owned networks. TCP hides loss, duplication, and reordering. TLS hides the conversation from eavesdroppers. HTTP hides all of it behind a request and a response.

You will also hear this same stack described with different names and more boxes, the **OSI model**, seven layers instead of five. In 1984 the International Organization for Standardization set out to define a vendor-neutral network architecture by committee, before TCP/IP had already won in practice, and split things more finely than the running internet ended up needing, physical and data link where this article has one link layer, and session, presentation, and application where this article has one application layer. TCP/IP shipped first, ran the actual internet, and never adopted OSI’s extra seams. What survived from OSI is its vocabulary, not its architecture, engineers still say “layer 2” for switching, “layer 3” for routing, and “layer 7” for anything application-aware, like a firewall that reads HTTP headers, because those numbers became industry shorthand long after the model itself was bypassed in practice.

This layering is also why the internet can evolve while running. Because each layer depends only on the interface of the one below, any layer can be swapped without touching the others. Physical links can upgrade from copper to fiber, or wires to Wi-Fi, without requiring any changes to the applications on top. The web’s newest protocol, HTTP/3, even replaced TCP itself, rebuilding reliability and encryption together on top of UDP in a protocol called **QUIC** (originally short for Quick UDP Internet Connections, though the standard now treats it as a name rather than an acronym). Two specific costs justified that, both visible in what you’ve already seen. First, a browser opens one connection and multiplexes dozens of requests over it, but TCP’s reliability is a single ordered byte stream, so one lost packet stalls *every* request behind it on that connection, even ones that have nothing to do with the missing bytes; QUIC gives each request its own independently-acknowledged stream, so a loss only stalls the stream it belongs to. Second, the handshake in step 2 and the TLS handshake in step 3 above ran one after the other, two round trips of pure latency before a single HTTP byte moved; QUIC folds transport setup and encryption into a single handshake, and on a repeat visit to a server it remembers, into none at all. It also stops keying a connection to the IP and port tuple the way TCP does, so it survives your phone switching from Wi-Fi to cellular mid-download, something the three-way handshake above has no way to do, since a new IP means a new tuple means, to TCP, a new connection.

The simulator below runs all three comparisons in sequence, the same client and server, first setting up a connection, then losing one packet out of three multiplexed requests, then switching networks mid-download.

TCP + TLS vs QUIC1 · connection setup2 · one lost packet3 · switching networks

TCP + TLStwo protocols, stacked

client

server

round trips before first HTTP byte → 0

TCP first: nothing moves until its handshake finishes, then TLS runs its own on top.

QUICone protocol over UDP

client

server

round trips before first HTTP byte → 0

QUIC folds transport setup and encryption into a single handshake.

None of this required anyone’s permission. IP’s only promise is to deliver a payload to a port; it has no opinion on what’s inside, which means the application layer was never a fixed list, HTTP is simply the protocol that happened to win for browsing documents. Anyone who controls both endpoints is free to define their own framing over TCP or UDP when the existing options don’t fit, and plenty have, SSH defines its own protocol for remote shells, SMTP for mail, MQTT is a deliberately tiny publish-subscribe protocol built for IoT devices too constrained to parse HTTP headers, WebRTC lets two browsers exchange audio and video directly over UDP without a server relaying it, and multiplayer game engines routinely write custom UDP protocols that, like the tradeoff above, discard stale position updates rather than retransmit them. QUIC itself is the clearest case, Google first deployed it as a proprietary protocol running only between Chrome and Google’s own servers, over ordinary UDP, years before the IETF standardized it as HTTP/3; nothing about the internet’s architecture had to change to allow that, which is exactly the point, the same freedom is available to anyone with two machines and a socket.

The internet is constantly changing with new demands and bottlenecks. IPv4’s address space ran out years ago, and IPv6 is still only partway rolled out because swapping the foundation everyone depends on is incredibly slow. Real-time video, cloud gaming, and remote collaboration keep pushing the limits of latency, which is why low-orbit satellite constellations now compete with undersea cables on round-trip time, and why QUIC’s redesign happened at all. The next protocol, the one nobody has agreed on yet, will exist because some application running today is straining against a limitation that can only be solved with a new protocol and a new set of tradeoffs.
