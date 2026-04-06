---
title: "An interactive intro to Elliptic Curve Cryptography (ECC)"
source: "https://growingswe.com/blog/elliptic-curve-cryptography"
author:
  - "[[growingSWE]]"
published: 2026-02-28
created: 2026-03-04
description: "A hands-on introduction to elliptic curve cryptography. Start with curve geometry, build point addition and scalar multiplication, see why ECDLP is hard, and then use that math in ECDH, ECDSA, and ECIES."
tags:
  - "clippings"
  - "cryptography"
  - "security"
---

> [!summary]
> Interactive tutorial covering elliptic curve cryptography from curve geometry through point addition, scalar multiplication, and the ECDLP trapdoor, then applies these to ECDH key exchange, ECDSA signatures, and ECIES encryption. Explains why ECC achieves equivalent security to RSA with much smaller keys (256-bit vs 3072-bit for 128-bit security).

## An interactive intro to Elliptic Curve Cryptography

*For my Master's program, I recently took a course on Applied Cryptography which I really enjoyed. I will be writing several posts on various cryptography concepts to cement what I learned*

Suppose two people want to communicate privately over the internet. They could encrypt their messages, scrambling them so that only someone with the right secret key can read them. But that raises an immediate problem: how do they agree on that secret key in the first place? They can't whisper it to each other. Every message between them passes through the open internet, where anyone could be listening.

One solution is **public-key cryptography**: each person has two linked keys, a **private key** they keep secret and a **public key** they share openly. The keys are mathematically related, but computing the private key from the public key is so hard it's effectively impossible. That one-way relationship is what lets you encrypt messages, agree on shared secrets, and sign data to prove authorship.

The first widely used public-key systems were built on the difficulty of specific math problems. **RSA** relies on the fact that multiplying two large prime numbers is easy, but factoring the result back into those primes is extremely hard. **Diffie-Hellman** relies on a similar idea using exponents in modular arithmetic (clock arithmetic where numbers wrap around at a fixed value).

Both systems work, and both are still in use. But they share a practical problem: the keys are enormous. A commonly recommended minimum for RSA today is 2048 bits (about 617 decimal digits), but for 128-bit security equivalence RSA needs 3072 bits. As we push for stronger security, the numbers grow fast: RSA key sizes grow much faster than security targets, because the underlying factoring attacks are sub-exponential.

What if a different mathematical structure could give us the same guarantees (easy in one direction, effectively impossible in reverse) but with much smaller numbers? That structure exists, and it comes from the geometry of curves.

## Drawing the curve

A mathematical equation can define a shape. Take the equation $y = x^2$ , which says "y equals x squared." To draw it, you pick values of $x$ , compute $y$ , and plot each resulting point on a grid. Step through the process below:

<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="280" viewBox="0 0 420 280" preserveAspectRatio="xMidYMid meet" style="min-width: 460px;"><circle cx="30" cy="250" r="1" fill="#e2e8f0"></circle><circle cx="30" cy="230" r="1" fill="#e2e8f0"></circle><circle cx="30" cy="210" r="1" fill="#e2e8f0"></circle><circle cx="30" cy="190" r="1" fill="#e2e8f0"></circle><circle cx="30" cy="170" r="1" fill="#e2e8f0"></circle><circle cx="30" cy="150" r="1" fill="#e2e8f0"></circle><circle cx="30" cy="130" r="1" fill="#e2e8f0"></circle><circle cx="30" cy="110" r="1" fill="#e2e8f0"></circle><circle cx="30" cy="90" r="1" fill="#e2e8f0"></circle><circle cx="30" cy="70" r="1" fill="#e2e8f0"></circle><circle cx="30" cy="50" r="1" fill="#e2e8f0"></circle><circle cx="30" cy="30" r="1" fill="#e2e8f0"></circle><circle cx="75" cy="250" r="1" fill="#e2e8f0"></circle><circle cx="75" cy="230" r="1" fill="#e2e8f0"></circle><circle cx="75" cy="210" r="1" fill="#e2e8f0"></circle><circle cx="75" cy="190" r="1" fill="#e2e8f0"></circle><circle cx="75" cy="170" r="1" fill="#e2e8f0"></circle><circle cx="75" cy="150" r="1" fill="#e2e8f0"></circle><circle cx="75" cy="130" r="1" fill="#e2e8f0"></circle><circle cx="75" cy="110" r="1" fill="#e2e8f0"></circle><circle cx="75" cy="90" r="1" fill="#e2e8f0"></circle><circle cx="75" cy="70" r="1" fill="#e2e8f0"></circle><circle cx="75" cy="50" r="1" fill="#e2e8f0"></circle><circle cx="75" cy="30" r="1" fill="#e2e8f0"></circle><circle cx="120" cy="250" r="1" fill="#e2e8f0"></circle><circle cx="120" cy="230" r="1" fill="#e2e8f0"></circle><circle cx="120" cy="210" r="1" fill="#e2e8f0"></circle><circle cx="120" cy="190" r="1" fill="#e2e8f0"></circle><circle cx="120" cy="170" r="1" fill="#e2e8f0"></circle><circle cx="120" cy="150" r="1" fill="#e2e8f0"></circle><circle cx="120" cy="130" r="1" fill="#e2e8f0"></circle><circle cx="120" cy="110" r="1" fill="#e2e8f0"></circle><circle cx="120" cy="90" r="1" fill="#e2e8f0"></circle><circle cx="120" cy="70" r="1" fill="#e2e8f0"></circle><circle cx="120" cy="50" r="1" fill="#e2e8f0"></circle><circle cx="120" cy="30" r="1" fill="#e2e8f0"></circle><circle cx="165" cy="250" r="1" fill="#e2e8f0"></circle><circle cx="165" cy="230" r="1" fill="#e2e8f0"></circle><circle cx="165" cy="210" r="1" fill="#e2e8f0"></circle><circle cx="165" cy="190" r="1" fill="#e2e8f0"></circle><circle cx="165" cy="170" r="1" fill="#e2e8f0"></circle><circle cx="165" cy="150" r="1" fill="#e2e8f0"></circle><circle cx="165" cy="130" r="1" fill="#e2e8f0"></circle><circle cx="165" cy="110" r="1" fill="#e2e8f0"></circle><circle cx="165" cy="90" r="1" fill="#e2e8f0"></circle><circle cx="165" cy="70" r="1" fill="#e2e8f0"></circle><circle cx="165" cy="50" r="1" fill="#e2e8f0"></circle><circle cx="165" cy="30" r="1" fill="#e2e8f0"></circle><circle cx="210" cy="250" r="1" fill="#e2e8f0"></circle><circle cx="210" cy="230" r="1" fill="#e2e8f0"></circle><circle cx="210" cy="210" r="1" fill="#e2e8f0"></circle><circle cx="210" cy="190" r="1" fill="#e2e8f0"></circle><circle cx="210" cy="170" r="1" fill="#e2e8f0"></circle><circle cx="210" cy="150" r="1" fill="#e2e8f0"></circle><circle cx="210" cy="130" r="1" fill="#e2e8f0"></circle><circle cx="210" cy="110" r="1" fill="#e2e8f0"></circle><circle cx="210" cy="90" r="1" fill="#e2e8f0"></circle><circle cx="210" cy="70" r="1" fill="#e2e8f0"></circle><circle cx="210" cy="50" r="1" fill="#e2e8f0"></circle><circle cx="210" cy="30" r="1" fill="#e2e8f0"></circle><circle cx="255" cy="250" r="1" fill="#e2e8f0"></circle><circle cx="255" cy="230" r="1" fill="#e2e8f0"></circle><circle cx="255" cy="210" r="1" fill="#e2e8f0"></circle><circle cx="255" cy="190" r="1" fill="#e2e8f0"></circle><circle cx="255" cy="170" r="1" fill="#e2e8f0"></circle><circle cx="255" cy="150" r="1" fill="#e2e8f0"></circle><circle cx="255" cy="130" r="1" fill="#e2e8f0"></circle><circle cx="255" cy="110" r="1" fill="#e2e8f0"></circle><circle cx="255" cy="90" r="1" fill="#e2e8f0"></circle><circle cx="255" cy="70" r="1" fill="#e2e8f0"></circle><circle cx="255" cy="50" r="1" fill="#e2e8f0"></circle><circle cx="255" cy="30" r="1" fill="#e2e8f0"></circle><circle cx="300" cy="250" r="1" fill="#e2e8f0"></circle><circle cx="300" cy="230" r="1" fill="#e2e8f0"></circle><circle cx="300" cy="210" r="1" fill="#e2e8f0"></circle><circle cx="300" cy="190" r="1" fill="#e2e8f0"></circle><circle cx="300" cy="170" r="1" fill="#e2e8f0"></circle><circle cx="300" cy="150" r="1" fill="#e2e8f0"></circle><circle cx="300" cy="130" r="1" fill="#e2e8f0"></circle><circle cx="300" cy="110" r="1" fill="#e2e8f0"></circle><circle cx="300" cy="90" r="1" fill="#e2e8f0"></circle><circle cx="300" cy="70" r="1" fill="#e2e8f0"></circle><circle cx="300" cy="50" r="1" fill="#e2e8f0"></circle><circle cx="300" cy="30" r="1" fill="#e2e8f0"></circle><circle cx="345" cy="250" r="1" fill="#e2e8f0"></circle><circle cx="345" cy="230" r="1" fill="#e2e8f0"></circle><circle cx="345" cy="210" r="1" fill="#e2e8f0"></circle><circle cx="345" cy="190" r="1" fill="#e2e8f0"></circle><circle cx="345" cy="170" r="1" fill="#e2e8f0"></circle><circle cx="345" cy="150" r="1" fill="#e2e8f0"></circle><circle cx="345" cy="130" r="1" fill="#e2e8f0"></circle><circle cx="345" cy="110" r="1" fill="#e2e8f0"></circle><circle cx="345" cy="90" r="1" fill="#e2e8f0"></circle><circle cx="345" cy="70" r="1" fill="#e2e8f0"></circle><circle cx="345" cy="50" r="1" fill="#e2e8f0"></circle><circle cx="345" cy="30" r="1" fill="#e2e8f0"></circle><circle cx="390" cy="250" r="1" fill="#e2e8f0"></circle><circle cx="390" cy="230" r="1" fill="#e2e8f0"></circle><circle cx="390" cy="210" r="1" fill="#e2e8f0"></circle><circle cx="390" cy="190" r="1" fill="#e2e8f0"></circle><circle cx="390" cy="170" r="1" fill="#e2e8f0"></circle><circle cx="390" cy="150" r="1" fill="#e2e8f0"></circle><circle cx="390" cy="130" r="1" fill="#e2e8f0"></circle><circle cx="390" cy="110" r="1" fill="#e2e8f0"></circle><circle cx="390" cy="90" r="1" fill="#e2e8f0"></circle><circle cx="390" cy="70" r="1" fill="#e2e8f0"></circle><circle cx="390" cy="50" r="1" fill="#e2e8f0"></circle><circle cx="390" cy="30" r="1" fill="#e2e8f0"></circle><line x1="30" y1="230" x2="390" y2="230" stroke="#cbd5e1" stroke-width="1"></line><line x1="210" y1="250" x2="210" y2="30" stroke="#cbd5e1" stroke-width="1"></line><text x="380" y="222" fill="#94a3b8" font-size="10" font-family="ui-monospace, SFMono-Regular, &quot;SF Mono&quot;, Menlo, Consolas, monospace">x</text> <text x="218" y="44" fill="#94a3b8" font-size="10" font-family="ui-monospace, SFMono-Regular, &quot;SF Mono&quot;, Menlo, Consolas, monospace">y</text> <line x1="75" y1="230" x2="75" y2="50" stroke="#3b82f6" stroke-width="1" stroke-dasharray="3 3" opacity="0.4"></line><line x1="210" y1="50" x2="75" y2="50" stroke="#3b82f6" stroke-width="1" stroke-dasharray="3 3" opacity="0.4"></line><g><circle cx="75" cy="50" r="5" fill="#3b82f6"></circle><text x="83" y="42" fill="#3b82f6" font-size="9" font-weight="700" font-family="ui-monospace, SFMono-Regular, &quot;SF Mono&quot;, Menlo, Consolas, monospace">(-3, 9)</text></g> <text x="75" y="244" fill="#3b82f6" font-size="9" font-weight="600" font-family="ui-monospace, SFMono-Regular, &quot;SF Mono&quot;, Menlo, Consolas, monospace" text-anchor="middle">-3</text></svg>

Each step picks an $x$ value, squares it to get $y$ , and places a dot at that coordinate. As the points accumulate, a curve appears: the parabola. The equation defined the shape all along; we just needed enough points to see it.

Different equations produce different shapes. The equation $x^2 + y^2 = 1$ gives a circle (every point at distance 1 from the center). Toggle between these below:

An **elliptic curve** is another equation of this kind:

$$
y^2 = x^3 + ax + b
$$

Select $y^2 = x^3 - x + 1$ in the demo above to see one. The $x^3$ term makes the right side grow much faster than the left, giving the curve its distinctive looping shape, different from the smooth symmetry of a circle or the open bowl of a parabola.

Despite the name, elliptic curves have nothing to do with ellipses. The name comes from elliptic integrals, which arose historically when computing the arc length of an ellipse. The connection is purely mathematical and not worth worrying about.

The constants $a$ and $b$ determine the curve's shape. Adjust the sliders below and watch the curve change. Click anywhere on the curve to place a point:

Click a few different spots. Every point you place has a mirror: if $(x, y)$ is on the curve, then $(x, -y)$ is too, because squaring a negative number gives the same result as squaring its positive counterpart ( $(-y)^2 = y^2$ ). The curve is always symmetric across the x-axis. This symmetry will matter when we define addition.

One constraint on the parameters: certain combinations of $a$ and $b$ produce a curve with a cusp or a self-intersection (a sharp point where the curve crosses itself). These are called **singular curves**, and they break the algebraic structure we need. Toggle between the three cases below to see what goes wrong:

At a cusp, the curve comes to a sharp point where the tangent line is undefined. At a self-intersection, two branches of the curve cross, giving two tangent lines at one point. Both situations break the point addition we're about to define, which depends on there being exactly one tangent line at every point. The mathematical condition for avoiding singularities is that the discriminant $4a^3 + 27b^2 \neq 0$ . Cryptographic curves always satisfy this.

We have a curve. Now what? The idea that turned this into cryptography was to define an *arithmetic* on the points of the curve: a way to "add" two points together and get a third point, also on the curve.

## Adding points on a curve

The geometric construction goes like this. Take two points $P$ and $Q$ on the curve. Draw a straight line through them. Because the equation is cubic (the $x^3$ term), this line will generally intersect the curve at exactly one more point, call it $R'$ (special cases like vertical lines or tangencies are handled by the point at infinity and the doubling rule). Now reflect $R'$ over the x-axis, which means flipping its y-coordinate from positive to negative or vice versa. The reflected point $R$ is the result. We define $P + Q = R$ .

Move the sliders below to slide $P$ and $Q$ along the curve and watch the addition happen:

The dashed line goes through $P$ and $Q$ . It hits the curve at $R'$ (the unfilled circle). Reflecting $R'$ over the x-axis gives us $P + Q$ (the red point).

This "addition" isn't ordinary addition. We're not adding the coordinates together. We're using a geometric recipe (draw a line, find the intersection, reflect) to produce a new point from two existing ones. But mathematicians call it addition because it behaves like addition in the ways that matter.

It's **associative**, meaning that $P + (Q + R) = (P + Q) + R$ . There's an **identity element** called the "point at infinity" $O$ , which acts like zero: $P + O = P$ for any point $P$ . And every point has an **inverse**: the point directly below (or above) it, the reflection, since $P + (-P)$ gives the point at infinity. These properties make the curve's points a mathematical **group**. That's the algebraic structure the rest of this article depends on.

The algebra behind this construction uses the line's slope. For two distinct points $P = (x_1, y_1)$ and $Q = (x_2, y_2)$ , the slope of the line through them is:

$$
m = \frac{y_2 - y_1}{x_2 - x_1}
$$

And the result point $(x_3, y_3)$ is:

$$
x_3 = m^2 - x_1 - x_2, \quad y_3 = m(x_1 - x_3) - y_1
$$

But what happens when $P$ and $Q$ are the same point? You can't draw a line through a single point. Instead, you use the tangent line, the line that just touches the curve at $P$ . Its slope comes from calculus (implicit differentiation of the curve equation):

$$
m = \frac{3x_1^2 + a}{2y_1}
$$

The rest of the formula is the same. This operation, adding a point to itself, is called **point doubling**, and it's the building block for everything that follows.

## Climbing the curve

With point doubling, we can compute $2P = P + P$ . Then $3P = 2P + P$ . Then $4P$ , $5P$ , and so on. Computing $nP$ for some integer $n$ is called **scalar multiplication**: we're multiplying a point by a number to get another point.

The naive approach takes $n - 1$ additions: add $P$ to itself $n$ times. But there's a much faster method. To compute $100P$ , observe that $100 = 64 + 32 + 4$ in binary. So compute $2P$ , $4P$ , $8P$ , $16P$ , $32P$ , $64P$ by repeated doubling (six doublings), then add $64P + 32P + 4P$ (two additions). That's eight operations instead of 99. In general, computing $nP$ takes roughly $\log_2(n)$ operations using this **double-and-add** algorithm. Even for a 256-bit number (roughly $10^{77}$ ), that's only about 256 doublings and additions, which a computer does in a fraction of a second.

Step through the computation of $nG$ on a small curve:

Watch the points hop around in what looks like a random pattern. Even on this small curve, there's no visible relationship between $n$ and the position of $nG$ . The points don't march along the curve in any recognizable order. They scatter unpredictably.

Elliptic curve cryptography depends on that apparent randomness.

## The trapdoor

Going forward is easy: given $P$ and $n$ , computing $Q = nP$ takes roughly $\log_2(n)$ steps using double-and-add. Going backward is hard: given $P$ and $Q$ , finding $n$ such that $Q = nP$ has no known shortcut on a well-chosen curve.

This is a **one-way function** (sometimes called a trapdoor): easy to compute forward, practically impossible to reverse. Every public-key system has one. For RSA, multiplying two large primes is easy but factoring their product is hard. For elliptic curves, scalar multiplication is easy but recovering the scalar is hard.

The problem of recovering $n$ is called the **Elliptic Curve Discrete Logarithm Problem** (ECDLP). The name "discrete logarithm" comes from an analogy with regular logarithms: in regular math, if $b^n = x$ , then $n = \log_b(x)$ . Here, if $nP = Q$ , we're looking for a kind of "logarithm" in the world of elliptic curve points. "Discrete" means we're working with integers, not continuous numbers.

Step through a brute-force search to see what "going backward" looks like:

On the small curve in this demo, the search finishes quickly because $n$ is small. In real cryptography, $n$ is roughly $2^{256}$ (a number with 77 digits). Even the best known algorithms would need about $2^{128}$ operations. If every computer on Earth worked on the problem, it would take longer than the age of the universe.

## From smooth curves to scattered dots

Everything so far used real-number coordinates like smooth curves, infinite precision and irrational slopes. Real cryptography can't work this way. Computers represent real numbers with floating-point arithmetic, which introduces tiny rounding errors. In cryptography, a single wrong bit means the wrong answer. We need exact arithmetic.

The fix is to work over a **finite field**. Instead of using all real numbers, we use only the integers from $0$ to $p - 1$ , where $p$ is a prime number. All arithmetic wraps around at $p$ , the same way a clock wraps around at 12.

This is called **modular arithmetic** (written $\bmod p$ ). For example, if $p = 7$ , then $5 + 4 = 9 \equiv 2 \pmod{7}$ because 9 divided by 7 has remainder 2.

The curve equation becomes:

$$
y^2 \equiv x^3 + ax + b \pmod{p}
$$

Now $x$ and $y$ are integers from $0$ to $p - 1$ . Division is replaced by **modular inverse**, a number that, when multiplied, gives 1 modulo $p$ . (For example, the inverse of 3 modulo 7 is 5, because $3 \times 5 = 15 \equiv 1 \pmod{7}$ .) The point addition formulas stay exactly the same, just computed mod $p$ .

The visual result is completely different. The smooth curve becomes a scattered cloud of dots:

Click any point to see its inverse (the point with the same x-coordinate but negated y-coordinate, mod $p$ ). Despite looking random, these points satisfy the same equation and obey the same addition rules. The algebraic structure is fully preserved even though the geometry is gone. It's this version of the curve (over a finite field with a very large prime) that real cryptographic systems use.

The number of points on the curve is close to $p$ (more precisely $p + 1 - t$ , where $|t| \le 2\sqrt{p}$ by Hasse's theorem, so the count is close to $p$ in relative terms). Cryptographic systems typically use a large prime-order subgroup of size $n$ close to $p$ . For curves using 256-bit primes, this gives roughly $2^{256}$ points to work in.

The trapdoor still applies. Scalar multiplication over a finite field is just as fast ( $\log_2(n)$ steps via double-and-add), and the ECDLP is at least as hard as it was over real numbers. It is harder, in fact, because the scattered-dot structure removes geometric intuition an attacker might exploit. All the constructions that follow (key exchange, signatures, encryption) work over this finite field.

## Exchanging secrets on a curve

With a set of points, an addition operation, and a one-way function (scalar multiplication that's easy to compute but hard to reverse), we can build a protocol for two people to agree on a shared secret over an open channel, without ever sending the secret itself.

This protocol is called **ECDH** (Elliptic Curve Diffie-Hellman). Alice and Bob agree publicly on a curve and a starting point $G$ called the **generator**. If you compute $G, 2G, 3G, \ldots$ , the points eventually cycle back to the start.

The number of steps before the points cycle is called the **order** of $G$ , written $n$ . For cryptographic curves, $n$ is roughly $2^{256}$ , so the generator produces an enormous set of distinct points before repeating. Private keys are random scalars in the range $[1, n-1]$ . (Some curves like X25519 accept 32 random bytes and deterministically "clamp" the bits into a safe scalar, simplifying key validation.)

1. Alice picks a random secret integer $a$ as her private key. She computes $aG$ (her public key) and sends it to Bob.
2. Bob picks a random secret integer $b$ as his private key. He computes $bG$ (his public key) and sends it to Alice.
3. Alice takes Bob's public key $bG$ and multiplies it by her private key: $a(bG) = abG$ .
4. Bob takes Alice's public key $aG$ and multiplies it by his private key: $b(aG) = baG$ .

Since scalar multiplication is associative, $abG = baG$ . Both arrive at the same point, the shared secret. An eavesdropper sees $G$ , $aG$ , and $bG$ (all sent over the public channel), but computing $abG$ from those values requires solving the ECDLP: finding $a$ from $G$ and $aG$ , or $b$ from $G$ and $bG$ .

Adjust the private keys below and watch the shared secret update:

Both sides always arrive at the same point. In practice, the shared secret (usually just the x-coordinate of this point) is fed through a key derivation function to produce a symmetric encryption key, which is then used to encrypt the actual conversation.

## Signing with curves

Key exchange lets two people establish a shared secret. But cryptography also needs **digital signatures**: a way to prove that a message came from a specific person and hasn't been tampered with. This is what you use when you sign a software update, authenticate a TLS certificate, or authorize a cryptocurrency transaction.

**ECDSA** (Elliptic Curve Digital Signature Algorithm) works like this. The signer has a private key $d$ (a secret integer) and a public key $Q = dG$ (a point on the curve, published for anyone to see).

To sign a message:

1. Hash the message to get a number $m$ (a hash function, like SHA-256, turns any input into a fixed-size number)
2. Pick a random secret nonce $k$ (a one-time random number, never reused)
3. Compute the point $R = kG$ on the curve
4. Set $r = R_x \bmod n$ (the x-coordinate of $R$ , taken modulo the group order $n$ )
5. Compute $s = k^{-1}(m + r \cdot d) \bmod n$ (using the modular inverse of $k$ )
6. If $r = 0$ or $s = 0$ , a new $k$ must be generated and the process repeated
7. The signature is the pair $(r, s)$

To verify the signature against the signer's public key $Q$ :

1. Compute $u_1 = m \cdot s^{-1} \bmod n$ and $u_2 = r \cdot s^{-1} \bmod n$
2. Compute the point $R' = u_1 G + u_2 Q$
3. If the x-coordinate of $R'$ modulo $n$ equals $r$ , the signature is valid

The math works out so that only someone who knows $d$ can produce a valid $(r, s)$ for a given message, but anyone who knows the public key $Q$ can verify it. Adjust the parameters below to see signing and verification with small numbers:

There are two security requirements: the nonce $k$ must never be reused across different messages, and $k$ and its inverse must be protected like the private key itself. If an attacker sees two signatures that used the same $k$ with different messages, the two equations leak enough information to compute the private key $d$ directly. In 2010, Sony's PlayStation 3 code signing key was extracted because they used the same nonce for every signature.

## Encrypting with curves

ECDH gives us key agreement and ECDSA gives us signatures. But what about encryption? If Alice wants to send an encrypted message to Bob using his public key, she needs ECIES (Elliptic Curve Integrated Encryption Scheme).

ECIES is a hybrid encryption scheme that combines elliptic curve cryptography with symmetric encryption:

1. Alice generates a random **ephemeral keypair**: a private key $r$ and public key $R = rG$
2. Alice computes the shared secret: $S = r \cdot Q_B$ (where $Q_B$ is Bob's public key)
3. Alice derives a symmetric key from $S$ (usually from the x-coordinate, often through a key derivation function)
4. Alice encrypts the message using the symmetric key (with AES or similar)
5. Alice sends $(R, \text{ciphertext})$ to Bob (the ephemeral public key and the encrypted message)

Bob decrypts by computing the same shared secret:

1. Bob receives $(R, \text{ciphertext})$
2. Bob computes the shared secret: $S = d_B \cdot R$ (where $d_B$ is his private key)
3. Bob derives the same symmetric key from $S$
4. Bob decrypts the ciphertext

The math ensures both arrive at the same shared secret because $r \cdot Q_B = r \cdot (d_B G) = (r \cdot d_B) G = (d_B \cdot r) G = d_B \cdot (rG) = d_B \cdot R$ .

The ephemeral key $r$ is generated fresh for every message, which means the same plaintext encrypted twice produces different ciphertexts. An eavesdropper sees $R$ and the ciphertext, but computing $r$ from $R = rG$ requires solving the ECDLP.

Try the demo below (using simplified XOR encryption instead of AES to keep the demonstration clear):

ECIES lets you encrypt a message directly to someone's public key without a prior key exchange. Full ECIES specifications also include a key derivation function (KDF) and a MAC or AEAD scheme for integrity. Ethereum's devp2p/RLPx protocol uses ECIES during the handshake to establish shared session keys; the ongoing transport then uses symmetric encryption. Signal Protocol uses a variant called the X3DH key agreement protocol that builds on similar elliptic curve principles.

## Why curves win

The practical advantage of elliptic curve cryptography comes down to key size. For the same level of security, ECC keys are much smaller than RSA or Diffie-Hellman keys:

| Security level | ECC key | RSA key | DH key |
| --- | --- | --- | --- |
| 80 bits | 160 bits | 1,024 bits | 1,024 bits |
| 112 bits | 224 bits | 2,048 bits | 2,048 bits |
| **128 bits** | **256 bits** | **3,072 bits** | **3,072 bits** |
| 192 bits | 384 bits | 7,680 bits | 7,680 bits |
| 256 bits | 512+ bits (e.g., P-521) | 15,360 bits | 15,360 bits |

"Security level" means the number of operations an attacker would need to break the system. At 128-bit security (the standard for most applications today, meaning an attacker would need $2^{128}$ operations), an ECC key is 256 bits while an RSA key is 3,072 bits. That's a 12x difference. At higher security levels the gap grows: 256-bit security needs 512+-bit ECC keys (e.g., P-521) versus 15,360-bit RSA keys.

Smaller keys are faster to compute and cheaper to transmit, which matters especially on constrained devices like smart cards. This is why TLS 1.3, Signal, SSH, and Bitcoin all use ECC.

TLS 1.3 dropped static RSA key transport and uses only ephemeral (EC)DHE for forward secrecy. Signal and WhatsApp use Curve25519 for all key agreement. SSH supports ECDSA and Ed25519 keys. Bitcoin and Ethereum both use secp256k1, though Bitcoin now uses Schnorr signatures (BIP340) for Taproot outputs alongside ECDSA for legacy and SegWit transactions.

The two most common curves are NIST P-256 (from FIPS 186-2, published in 2000) and Curve25519 (designed by Daniel Bernstein in 2006). X25519, the Diffie-Hellman function on Curve25519, was designed to resist implementation mistakes: it accepts any 32 bytes of secret material and deterministically clamps the bits into a valid scalar, so there are fewer ways to mishandle keys.

Elliptic curves give us key exchange and digital signatures with keys that fit comfortably in a text message. There is a caveat, though. All public-key cryptography, including ECC, is theoretically vulnerable to quantum computing: an algorithm called Shor's algorithm can solve the ECDLP efficiently on a sufficiently powerful quantum computer. No such computer exists yet, but the threat has motivated work on post-quantum cryptography, which uses different mathematical structures (lattices, error-correcting codes, hash trees) that quantum computers can't efficiently break.
