---
title: "How Bluesky draws its logo on screenshots"
source: "https://timmarinin.net/2026/bluesky-screenshots/"
author:
  - "[[mt]]"
published: 2026-08-16
created: 2026-08-23
description: "The secret is humble UITextField."
tags:
  - "clippings"
---

> [!summary]
> Bluesky's iOS app swaps the "Follow" button for its logo in screenshots by rendering the button into the layer of a `UITextField` with `isSecureTextEntry` set, which iOS blanks during screen capture. The author traced the behaviour to `GrowthHack.tsx` and the `expo-privacy-sensitive` package in the open-source app, and notes it fails mid-app-switch because iOS uses its own earlier snapshot. Telegram and Signal use the same screenshot-blocking trick for private chats, so Apple is unlikely to close it.

Sometimes I take a screenshot of a post I like, either to send it to friends/meme channel or to save a “durable” copy. Like this one (I’ve cropped out the rest of the interface):

![A screenshot of Bluesky post by @eroston.bsky.social, the important part is that Bluesky logo is visible in the top right corner](https://timmarinin.net/2026/bluesky-screenshots/skeet.jpg)

Original, if you want to reskeet it

I noticed the Bluesky logo in the right corner and thought that it was weird that the logo doesn’t bother me when I use the app. Then I looked at the post in the app again—logo wasn’t there, replaced by the “Follow” button.

I remembered that a few apps hide their logo where the iPhone notch is, so that it doesn’t stick out, unless you take a screenshot. But here the logo is placed in the open, so how do they do it?

I tried to take another screenshot, this time mid-switching to the other app:

![Screenshot of zoomed out version of Bluesky app mid-switching, Follow button is visible](https://timmarinin.net/2026/bluesky-screenshots/mid-switch.png)

The “Follow” button is visible when I take the screenshot mid-switch.

Did they somehow set up a listener for two buttons I’m pressing to take a screenshot and do a switcheroo at the last moment? I’m not an iOS developer, so I’m not sure what’s possible and what is not over there.

At this point I was mildly intrigued. Thankfully, I remembered that Bluesky app is open source (or at least the code is available to look at).

The answer was in the file literally called [GrowthHack.tsx](https://github.com/bluesky-social/social-app/blob/main/src/screens/PostThread/components/GrowthHack.tsx), introduced in January 2026 by [mozzius](https://github.com/mozzius). But it merely used a dependency, so to understand I looked into package [expo-privacy-sensitive](https://github.com/mozzius/expo-privacy-sensitive), also by them.

The package creates `UITextField` with `isSecureTextEntry` property set to true and renders the actual content (the button) into that field’s `.layer`. When I take the screenshot, iOS hides this UITextField by blanking the layer, allowing the Bluesky logo to flutter its wings through (it was here the whooole time). For other platforms it simply renders content as-is, without masking.

Why doesn’t it work when I switch between the apps? I suppose that iOS takes a snapshot itself at the start of the gesture (without triggering blanking), and when I do a screenshot, there is no live UITextField instance to react to that, only the inert snapshot. But once again, I’m not an iOS developer.

Nifty trick or an abuse of API meant for privacy? The people in [the thread adding the behavior](https://github.com/bluesky-social/social-app/pull/9637) mostly didn’t like it, before the thread got locked. I think it’s cute.

I googled a bit, and the trick is well-known. Telegram implemented [similar thing for its "secret" chats](https://github.com/TelegramMessenger/Telegram-iOS/blob/master/submodules/UIKitRuntimeUtils/Source/UIKitRuntimeUtils/UIKitUtils.m#L299-L328), as did [Signal](https://github.com/signalapp/Signal-iOS/blob/a9f55ea599561e6d3bcee87d4f1540a7191b28dc/Signal/util/ScreenshotBlocking.swift), so I don’t expect it to be patched by Apple any time soon.
