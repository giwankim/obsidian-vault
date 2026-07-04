---
title: "Building an Open-Source Robot Vacuum — Meet OOMWOO"
source: "https://makerspet.com/blog/building-an-open-source-robot-vacuum-meet-oomwoo/"
author:
  - "[[Ilia O.]]"
published: 2026-06-15
created: 2026-07-04
description: "I’m starting a new build-in-public project: oomwoo, an open-source robot vacuum you build yourself. Raspberry Pi, ROS 2, 2D LiDAR, Home Assistant, 3D printed, local-first — and open from the first commit."
tags:
  - "clippings"
---

> [!summary]
> Announcement of OOMWOO, an open-source build-it-yourself robot vacuum from Maker's Pet: Raspberry Pi, ROS 2/Nav2, 2D LiDAR mapping, 3D-printed chassis, native Home Assistant integration, and local-first operation with no cloud required. Hardware is at the early parts-sourcing stage, but the ROS 2 dev environment and Gazebo simulation are already usable — you can even contribute using a consumer vacuum as a placeholder. Community work is organized as parallel, self-contained Requests-for-Contribution modules on GitHub.

![OOMWOO open-source robot vacuum reference design, top view](https://makerspet.com/wp-content/uploads/2026/06/oomwoo-vacuum_model_top.webp)

OOMWOO open-source robot vacuum reference design, top view

Today I’m kicking off my most ambitious Maker’s Pet project yet: **OOMWOO**, an open-source home robot vacuum that *you* can build yourself. Open hardware, open firmware, open software — and built in public, from the first commit.

No cloud required. No vendor lock-in. It maps your home with an affordable 2D LiDAR and navigates on its own, runs locally, and integrates natively with Home Assistant. If you’re into making a vacuum that cleans well, Raspberry Pi, ROS 2, 3D printing, or just the idea of owning a vacuum you fully understand and control — this one’s for you.

*About the name: “OOMWOO” is a rotational ambigram — it reads the same flipped 180°, just like the robot itself roaming your floor in every direction.*

![oomwoo open-source robot vacuum reference design, top view](https://makerspet.com/wp-content/uploads/2026/06/oomwoo-vacuum_model_top.webp)

Reference design — roughly how the finished OOMWOO will look.

## What OOMWOO is

OOMWOO is a build-it-yourself robot vacuum designed for the maker community:

- **Affordable and fully open** — hardware, software, and firmware
- **2D LiDAR mapping and autonomous navigation** with ROS 2 / Nav2
- **Native Home Assistant integration** for local control
- **3D-printable, documented, hackable chassis**
- **Local-first** — no cloud needed for everyday cleaning, ever
- **Home-appliance quality** — not a throwaway build
- **Step-by-step, zero-to-hero build instructions**, with a complete bill of materials so you can source every part yourself

Optional extras — cloud features, and eventually an app store of ROS 2 apps to customize how your vacuum behaves — will layer on top. But the core promise never changes: **the vacuum always works cloud-free and local, out of the box.**

![oomwoo open-source robot vacuum reference design, bottom view](https://makerspet.com/wp-content/uploads/2026/06/oomwoo-vacuum_model_bottom.webp)

The underside of the reference design.

## Where the project is today

This is genuinely early hardware-wise — and that’s the point of building in public. I’m in the process of sourcing key parts at the moment. You can follow my parts sourcing progress [here](https://makerspet.com/blog/how-to-source-bom-for-oomwoo-open-source-vacuum-robot/).

Software-wise, the software development environment is ready. You can [install](https://github.com/makerspet/oomwoo-install) it and run OOMWOO (in simulation, no hardware) in, say, 15 minutes. Please follow this [tutorial](https://makerspet.com/blog/simulate-oomwoo-one-robot-vacuum-in-gazebo-with-ros-2/). You can contribute robot software to the project – and test it at home with a real vacuum cleaner – without waiting for the hardware is being developed. How? By using another real consumer vacuum cleaner as a “placeholder”. Please see [this](https://makerspet.com/blog/tutorial-connect-robot-vacuum-cleaner-to-ros-2-proscenic-m6-pro/), [this](https://makerspet.com/blog/simulate-the-proscenic-m6-pro-robot-vacuum-in-gazebo-with-ros-2/) and [this](https://makerspet.com/blog/tutorial-part-2-drive-map-navigate-your-proscenic-m6-pro-in-ros-2/) tutorial for instructions.

The first milestone (**v0**) is a bare-bones, working build:

- 3D-printed chassis
- ROS 2 Gazebo simulation
- LiDAR with manual SLAM
- ROS 2 on a Raspberry Pi 5 and/or ESP32 running micro-ROS (final architecture still being decided)

The open-source deliverables include:

- [Bill of materials](https://github.com/makerspet/oomwoo/blob/main/BOM.md), early work-in-progress
- 3D-printable files (not available yet)
- [Software development environment](https://github.com/makerspet/oomwoo-install) – ready to use, install today
- Firmware (not available yet)
- A motor-driver and sensor I/O PCB (repo to be announced shortly)
- Build instructions (not available yet)
- Full build-along, bring-up, troubleshooting docs demo videos (not available yet)
![oomwoo open-source robot vacuum with top cover removed, internal layout](https://makerspet.com/wp-content/uploads/2026/06/oomwoo-vacuum-no-top-back.webp)

Top cover removed — a peek at the reference design internal layout.

## Build it with me — massively in parallel

OOMWOO is organized so the community can build it **in parallel**. The robot and its software are split into self-contained modules (also known as Requests for Contributions). You pick whatever module interests you, work on it whenever you want, and submit your work as a pull request. Multiple people can tackle the same module — the best solution surfaces over time.

Please find the list of Requests-for-Contribution (RFC) [here](https://github.com/makerspet/oomwoo/tree/main/contributions). Here are a few RFC examples:

- **Create 3D STEP models of sourced parts** — drive wheel assemblies, caster wheel assembly, fans, main brushes and so on
- **Map-and-clean** — code to perform the first clean while mapping while SLAM-mapping and exploring
- **Research specs of sourced parts** — many sourced parts lack datasheets, so their specs and electrical interfaces have to be researched and sometimes reverse-engineered

Here is OOMWOO’s main [GitHub repo](https://github.com/makerspet/oomwoo/) where 3D files will be published.

## Follow along

I’ll be sharing progress as they happen:

- **GitHub:** [github.com/makerspet/oomwoo](https://github.com/makerspet/oomwoo/) — code, docs, and discussions
- **Discord:** [join the build chat](https://discord.gg/3y2JKz5T25) — twice-a-week updates in #general
- **YouTube:** [build-in-public channel](https://www.youtube.com/@makerspet)
- **X:** [@0OMWO0](https://x.com/0OMWO0) — I will be setting it up by mid-July.

### Follow OOMWOO build

Open-source robot vacuum community build updates

## Parts Kit

Everything about OOMWOO stays open — you can source every part yourself. If you’d rather skip the parts hunt, a convenience kit (motors, PCB, brushes, gaskets, LiDAR) will be available here at Maker’s Pet, from the same maker behind this project. The kit is a convenience, **never a requirement.**

Tags
