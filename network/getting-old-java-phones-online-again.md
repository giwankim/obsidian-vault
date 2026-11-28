---
title: "Getting old Java phones online again"
source: "https://antcating.github.io/2026/11/23/getting-old-java-phones-online-again.html"
author:
  - "[[Antcating's Chaos Lab]]"
published: 2026-11-23
created: 2026-11-26
description: "Sony Ericsson S500i accessing FrogFind."
tags:
  - "clippings"
---

> [!summary]
> With 2G shut down, the author gets a Sony Ericsson S500i back online by reversing the usual direction of Bluetooth PAN: a Raspberry Pi 5 acts as the Network Access Point (NAP) and the phone connects as a PAN User, even though the phone's documentation never mentions PANU support. The guide walks through creating a shared-IPv4 NAP profile with modern BlueZ and NetworkManager (`nmcli`), pairing via `bluetoothctl`, and configuring the phone's Internet profile. For browsing, it covers FrogFind, the ProtoWeb proxy, Opera Mini 4.5 (which reaches HTTPS sites through Opera's proxy servers), and surviving WAP/WML sites.

![Sony Ericsson S500i showing FrogFind](https://antcating.github.io/assets/images/s500i/hero.jpg)

Sony Ericsson S500i accessing FrogFind.

## Background

Recently, I bought a used Sony Ericsson S500i – one of the most beautiful phones IMO. I vividly remember getting online on this phone while away from home and downloading games from the Sony Ericsson shop (and the exorbitant mobile data charges that came with it!).

But when I tried using it again in 2026, I couldn’t connect to the mobile network. Even though I had a SIM card compatible with the phone, 2G had been shut down for some time, leaving no way to access the Internet over a mobile connection.

USB wasn’t an option either. On many phones of this era, USB tethering was designed to share the phone’s Internet connection with a computer, not the other way around[^1]. But there is a way…

## Getting online via Bluetooth

Bluetooth supports various profiles, which define how devices use Bluetooth for specific purposes. One of these is Personal Area Networking (PAN), which allows devices to communicate over Bluetooth as if they were connected to an Ethernet network.

PAN carries Ethernet frames over Bluetooth, including IP traffic. This allows a device acting as a PAN User (PANU) to access the Internet through another device acting as a Network Access Point (NAP). The NAP forwards the traffic to the Internet, much like a Wi-Fi hotspot, but over Bluetooth instead[^2].

Although Bluetooth PAN is much less common nowadays, many devices still support the profile. One common use case was sharing a phone’s mobile Internet connection with a laptop. But why not reverse the direction? We can use a network-connected computer as a NAP and access the Internet from an old Java phone, provided the phone supports PANU[^3].

### Setting up Bluetooth NAP on Raspberry Pi 5

From what I’ve seen on forums, many older Sony Ericsson, Nokia, and other phones seem to **support PANU even if it is not mentioned in the documentation**. I couldn’t find any confirmation for the S500i, so I decided to give it a try by setting up a Bluetooth NAP and seeing whether the phone could connect.

I used Linux for this, but I’m sure you Windows and Mac wizards can figure out how to make it work on your systems too.

> Note: After finishing this blog, I found out that there is a way to do the same thing on Windows, see: [Getting old Java phones online again (Windows Edition)](https://antcating.github.io/2026/11/23/getting-old-java-phones-online-again-windows.html).

I found an old guide showing how to get a Sony Ericsson K800i online over Bluetooth using Debian Etch[^3]. While the basic idea still works, the guide relies on tools and configurations that are long obsolete. I worked out a different approach using modern BlueZ and NetworkManager, without the old scripts and manual network configuration.

I bought a Raspberry Pi 5 a few years ago to run small services at home, and it turned out to be a great fit for this project. Raspberry Pi boards have had built-in Bluetooth since the Raspberry Pi 3 Model B, so there’s no need for any additional Bluetooth hardware[^4].

Modern devices mostly don’t advertise the Bluetooth NAP service by default, so the following steps show how to enable it explicitly.

> Note: This guide is written for Raspberry Pi OS based on Debian 13 (Trixie), but I also tested the setup on my ThinkPad E14 running Arch Linux, and it worked there too. It should work on any other Linux distribution with BlueZ and NetworkManager, although package installation and service management may differ.

1. Install Bluez and NetworkManager (usually, installed by default).
	```bash
	sudo apt update
	sudo apt install -y bluez network-manager
	```
2. Enable Bluetooth.
	```bash
	sudo systemctl enable --now bluetooth
	```
3. Create a Bluetooth NAP profile and share the Internet connection.
	```bash
	sudo nmcli connection add \
	    type bluetooth \
	    con-name "Bluetooth-NAP" \
	    ifname btnap0 \
	    bluetooth.type nap \
	    ipv4.method shared \
	    ipv6.method disabled
	```

	This configuration enables IPv4 sharing through NetworkManager. The Raspberry Pi acts as a gateway for devices connected over Bluetooth, assigning IP addresses and forwarding their traffic to the Internet. It works with either an Ethernet or Wi-Fi connection.
4. Activate the created profile.
	```bash
	sudo nmcli connection up "Bluetooth-NAP"
	```
5. (Optionally) Enable automatic activation on boot.
	```bash
	sudo nmcli connection modify "Bluetooth-NAP" connection.autoconnect yes
	```
6. Verify that the NAP service is available.

	```bash
	bluetoothctl show
	```

	Look for:

	```
	UUID: NAP (00001116-0000-1000-8000-00805f9b34fb)
	```

	This indicates that BlueZ has registered the NAP service.

### Connecting the S500i

1. Enable Bluetooth on the phone and make it discoverable.
2. Pair the Raspberry Pi with the phone using bluetoothctl.
	- Start the Bluetooth control utility:
		```bash
		bluetoothctl
		```
	- Configure the Raspberry Pi to accept pairing requests:

		```
		power on
		agent off
		agent KeyboardDisplay
		default-agent
		pairable on
		discoverable on
		```

		> Note: Run each command separately in the interactive bluetoothctl prompt
	- Start scanning for nearby Bluetooth devices:
		```
		scan on
		```
	- Look for your phone in the output.

		It should appear under the name configured on the phone. For example:

		```
		[NEW] Device 00:23:F1:XX:XX:XX S500i
		```
	- Disable the scanning:
		```
		scan off
		```
	- Pair the Raspberry Pi with the phone.

		```
		pair 00:23:F1:XX:XX:XX
		```

		Replace the example address with your phone’s actual Bluetooth address. Enter the same PIN on both devices. If everything goes well, bluetoothctl will report that pairing was successful.
	- Mark the phone as trusted on the Raspberry Pi:

		```
		trust 00:23:F1:XX:XX:XX
		```

		This allows the Raspberry Pi to authorize future supported connections from the phone without repeatedly asking for approval.

### Accessing the Internet from a Java phone

This part is phone-specific because it requires changing the phone’s Internet settings. The menu names and available options may differ between models.

1. Check that the phone can discover the NAP service.

	On the S500i, select Raspberry Pi under `Connectivity / Bluetooth / My devices` and browse its services.

	Look for `Network access`.

	If it appears, the phone can discover the Raspberry Pi’s NAP service.
2. Configure the phone’s Internet connection.

	Go to `Connectivity / Internet settings / Internet profiles`.

	Create an Internet profile using the Bluetooth connection if one is available.

	> Some phones automatically create a Bluetooth data account when a PAN connection is established. The exact behavior varies between models and firmware versions.
3. Test the connection.

	Open the phone’s browser and try loading a simple website, like [frogfind.com](https://frogfind.com/).

	While the phone is attempting to connect, run the following command on the Raspberry Pi:

	```bash
	bridge link show master btnap0
	```

	If you see an interface named bnep0 with state forwarding, the phone has successfully established a Bluetooth PAN connection to the Raspberry Pi.
[![S500i displaying the Raspberry Pi's Network access Bluetooth service](https://antcating.github.io/assets/images/s500i/detail-nap-services.jpg)](https://antcating.github.io/assets/images/s500i/nap-services.jpg)

[![S500i data accounts menu with a Bluetooth account for Raspberry Pi](https://antcating.github.io/assets/images/s500i/detail-data-account.jpg)](https://antcating.github.io/assets/images/s500i/data-account.jpg)

The Raspberry Pi's Network access service and the corresponding Bluetooth data account.

*Hooray! We are on the net!*

### Browsing the web on the Java phone

You can now go and browse the Web. Well, at least a very small part of it.

Most of the default links in the Sony Ericsson browser no longer work, but, for example, good old [frogfind.com](https://frogfind.com/) works just fine.

If you want a more modern, feature-rich alternative to the default browser, there is another option. By some miracle, Opera still provides [download links](https://www.opera.com/download/mobile-versions) ([archive](https://web.archive.org/web/20261116100558/https://www.opera.com/download/mobile-versions)) for Opera Mini 4.5 for Java phones on its official website, which is just incredible. Even better, many of its default links still work and serve today’s news!

Unlike the Sony Ericsson’s built-in browser, Opera Mini 4.5 can also access modern HTTPS websites through Opera’s proxy servers, which handle encryption and process webpages before sending them to the phone[^5]. This makes a surprisingly large portion of the modern web accessible, although many websites remain out of reach due to modern web standards, the phone’s limited hardware, and, well, the web being the web.

[![Sony Ericsson S500i displaying xkcd #386 in Opera Mini](https://antcating.github.io/assets/images/s500i/detail-xkcd-duty-calls.jpg)](https://antcating.github.io/assets/images/s500i/xkcd-duty-calls.jpg)

[![S500i showing the HTTPS-only HTTP Minimal website](https://antcating.github.io/assets/images/s500i/detail-https-test.jpg)](https://antcating.github.io/assets/images/s500i/https-test.jpg)

Reading [xkcd #386, “Duty Calls”](https://xkcd.com/386/) and accessing an HTTPS-only website using Opera Mini 4.5.

Even with Opera Mini (while it still works), browsing the modern web on a phone this old is still pretty hit-or-miss. Fortunately, there are a couple of projects that make life easier for old browsers:

- [FrogFind](https://frogfind.com/about) – simplifies modern webpages into basic HTML that vintage computers can handle. It turns out to be pretty handy for an underpowered phone from almost 20 years ago, too.
- [ProtoWeb proxy](https://protoweb.org/about/) – takes a different approach, bringing back websites from the mid-to-late 1990s through a proxy. Those pages aren’t always convenient to navigate on the S500i’s tiny screen, but then again, browsing the web on phones back then wasn’t exactly convenient either. So it’s a pretty authentic experience!

### And then there’s WAP!

There’s another little corner of the web that’s still alive: a small community of enthusiasts keeping old WAP websites running, serving WML pages designed for early mobile browsers. These sites can still be browsed on compatible phones, without relying on an emulator! And maybe it’s time to bring a few more WML sites online…

## Closing Words

I watched Action Retro’s video[^6] about bringing FrogFind to WAP, where he converts the FrogFind homepage into WML for older mobile browsers. Building a small HTML-to-WML converter could be a really cool project. And with Internet access already working over Bluetooth, developing and testing it on physical hardware should be much easier, without having to build an entire 2G network like dosdude1 did[^7]. Of course, this approach won’t work for every old phone, but for those that support Bluetooth networking, it doesn’t require any additional radio hardware.

I’d also love to see a community-maintained list of phones that support Bluetooth PANU, since many manufacturers never bothered to document it (including Sony Ericsson with the S500i). It would make it much easier for anyone to figure out whether their phone can get online this way or whether they’ll need to get a bit more creative;-)

P.S. Have fun and happy hacking!

## Changelog

2026/11/24: Added mention of Windows method

## Sources

[^1]: [Sony Ericsson S500i documentation](https://www-support-downloads.sonymobile.com/s500/userguide_EN_S500.pdf) ([archive](https://web.archive.org/web/20251023010349/https://www-support-downloads.sonymobile.com/s500/userguide_EN_S500.pdf)).

[^2]: [Gentoo Wiki - Bluetooth Network Aggregation Point](https://wiki.gentoo.org/wiki/Bluetooth_Network_Aggregation_Point) ([archive](https://web.archive.org/web/20260725024820/https://wiki.gentoo.org/wiki/Bluetooth_Network_Aggregation_Point)).

[^3]: [Bluetooth PAND (Personal Area Network) Howto For Debian Etch](https://www.howtoforge.com/bluetooth_pand_debian_etch/) ([archive](https://web.archive.org/web/20260718000238/https://www.howtoforge.com/bluetooth_pand_debian_etch)).

[^4]: [Raspberry Pi product series explained](https://www.raspberrypi.com/news/raspberry-pi-product-series-explained/) ([archive](https://web.archive.org/web/20261030065658/https://www.raspberrypi.com/news/raspberry-pi-product-series-explained/))

[^5]: [Opera Mini Takes Care of Your Security — Opera Blog](https://blogs.opera.com/mobile/2016/03/opera-mini-takes-care-security/) ([archive](https://web.archive.org/web/20260719040428/https://blogs.opera.com/mobile/2016/03/opera-mini-takes-care-security/)).

[^6]: [Is WAP dead?](https://www.youtube.com/watch?v=D62ZsVZCjAA)

[^7]: [Building a CUSTOM 2G GSM Cellular Base Station](https://www.youtube.com/watch?v=CMWvA4Ty1Wk)
