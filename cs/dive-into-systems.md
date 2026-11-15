---
title: "Dive into Systems"
source: "https://diveintosystems.org/"
author:
published:
created: 2026-11-13
description:
tags:
  - "clippings"
---

> [!summary]
> Landing page for Dive into Systems, a free online textbook from West Point and Swarthmore faculty that introduces computer systems, organization, and parallel computing to readers with only a CS1 background. It covers C and assembly, binary representation and architecture, the OS and memory hierarchy, and shared-memory parallelism with pthreads, with appendices for Java programmers and Unix. The site also links interactive tools such as an assembly visualizer and practice exercises, plus the No Starch print edition.

[Suzanne J. Matthews](http://www.suzannejmatthews.com/), West Point
[Tia Newhall](https://www.cs.swarthmore.edu/~newhall/), Swarthmore College
[Kevin C. Webb](https://www.cs.swarthmore.edu/~kwebb/), Swarthmore College

The Dive into Systems project develops and evaluates teaching resources specifically for introductory computer systems, computer organization, and parallel computing courses. Our primary projects include:

- *Dive into Systems*: our free, online textbook (also available is a low cost print version from No Starch Press).
- Interactive, online learning tools.
- Interactive, online exercises.

## The Textbook

*Dive into Systems* is a **free, online textbook** that serves as a gentle introduction to computer systems, computer organization, and parallel computing. The book is intended for an audience that has only a CS1 background. It guides readers through a vertical slice of a computer to develop an understanding of a variety of systems topics, including:

- how a computer runs a program, from a program expressed in a high-level language to low-level binary representation and circuits
- programming in C and Assembly (assuming a CS1 background)
- introduction to operating systems and the systems costs that affect program performance (the memory hierarchy, caching, and code optimization)
- introduction to parallel computing with shared memory and pthreads

*Dive into Systems* is designed to be present topics in as independent manner as possible so that it can be used as a primary textbook for a wide range of introductory-level computer systems courses, or as a supplemental background textbook for upper-level courses that cover Operating Systems, Computer Architecture, Compilers, Networks, Databases, and Parallel Computing.

*Dive into Systems* includes one or more chapters on the following topics: **Introduction to Computer Systems**; **C Programming** (covers most of the C language, debugging with gdb and valgrind, and code optimization); **Computer Organization and Architecture** (includes binary representation, computer architecture, memory hierarchy, and caching); **Assembly Programming** (covers 64-bit x86, 32-bit x86, and 64-bit ARM); **The Operating System**; and **Parallel Computing** (focus on shared memory and threads, and also looking ahead to others).

---

### Read The Book

Our textbook is available free, on-line in two different formats (mult-page, and single page). Additionally, a low-cost print version of our textbook is available from No Starch Press (note that **our textbook will always remain free on-line here**). Instructors, if you are using our textbook for your course, please let us know (please email us at [authors@diveintosystems.org](mailto:authors@diveintosystems.org) sharing this information with us).

#### Free On-line Version

| [As a collection of documents (easier to navigate)](https://diveintosystems.org/book/) | [As a single-page document](https://diveintosystems.org/singlepage/) |
| --- | --- |

This is release of Version 1.2 of the Dive into Systems textbook that was updated on *August 25, 2023*. This version includes two new appendices and links to early versions of interactive exercises.

The two Appendices added since Version 1.0 of our book are:

- [Appendix 1: "Chapter 1 for Java Programers"](https://diveintosystems.org/book/Appendix1/index.html). This is a version of Chapter 1 that uses Java code examples to compare to C code (Python examples are used in Chapter 1).
- [Appendix 2: "Using Unix"](https://diveintosystems.org/book/Appendix2/index.html). This starts with the basics of Unix command line and Unix file system, and then covers a wide range of Unix commands and utilities (e.g., tar, make and Makefiles, editors, chmod, ssh, man, io redirection, …). It also introduces some more advanced features like pipes, getting system state, and writing shell scripts. With each topic we include links to resources for further information.

If you find any errors, typos, etc., please contact us. We appreciate your feedback!

**Instructors: if you are using our textbook for your course, please let us know.** Please email us at [authors@diveintosystems.org](mailto:authors@diveintosystems.org) sharing this information with us.

#### Print Version

[![Cover art](https://diveintosystems.org/Diveintosystemscover.jpeg)](https://nostarch.com/dive-systems)

A low cost print version of our textbook is available by purchase directly from [No Starch Press](https://nostarch.com/dive-systems), and from numerous other sellers including [Amazon](https://www.amazon.com/Dive-Into-Systems-Introduction-Computer/dp/1718501366/ref=sr_1_1?crid=YIK9MEFTDHXF&keywords=dive+into+systems&qid=1664204099&qu=eyJxc2MiOiIwLjYzIiwicXNhIjoiMC4yNCIsInFzcCI6IjAuMzEifQ%3D%3D&sprefix=dive+into+%2Caps%2C892&sr=8-1).

**Please keep in mind that the online version of our textbook will always remain free from our website.**

[Dive into Systems Print Version](https://nostarch.com/dive-systems), No Starch Press, August 2022 (ISBN-13: 9781718501362).

---

### Chapter Reviewers

Each chapter of Dive into Systems was peer-reviewed by faculty and other experts from across the United States. We are extremely grateful to those who served as our formal reviewers. Their insight, time, and recommendations improved the rigor and precision of Dive into Systems. Chapter reviewers include:

| Jeannie Albrecht (Williams College) | John Barr (Ithaca College) |
| --- | --- |
| Jon Bentley | Anu G. Bourgeois (Georgia State Univ.) |
| Martina Barnas (Indiana Univ. Bloomington) | David Bunde (Knox College) |
| Stephen Carl (Sewanee: Univ. of the South) | Bryan Chin (U.C. San Diego) |
| Amy Csizmar Dalal (Carleton College) | Debzani Deb (Winston-Salem State Univ.) |
| Saturnino Garcia (Univ. of San Diego) | Tim Haines (Univ. of Wisconsin) |
| Bill Jannen (Williams College) | Ben Marks (Swarthmore College) |
| Alexander Mentis (West Point) | Rick Ord (U.C. San Diego) |
| Joe Politz (U.C. San Diego) | Brad Richards (Univ. of Puget Sound) |
| Kelly Shaw (Williams College) | Simon Sultana (Fresno Pacific Univ.) |
| Cynthia Taylor (Oberlin College) | David Toth (Centre College) |
| Bryce Wiedenbeck (Davidson College) | Daniel Zingaro (Univ. of Toronto Mississauga) |

## Interactive Tools

As part of our NSF funded project, we are developing interactive book exercises and related interactive learning tools.

### ASM Visualizer

[ASM Visualizer](https://asm.diveintosystems.org/) is our assembly visualization tool. It is designed to help students learn assembly programming, aiding in their understanding of how assembly instructions are executed and the relationship between assembly and equivalent high-level language code. Our tool allows a user to step both forward and backward through the execution of an assembly program, one instruction at a time, seeing how instructions use and modify values in stack memory and CPU registers.

ASM Visualizer supports three user-interface modes for different stages of learning assembly programming.

1. **Arithmetic Mode** is designed for beginners. It hides the assembly code for the containing function’s stack set up and return, allowing the user to to enter basic arithmetic and control instructions, and to set some initial values in registers and on the stack (for local variables), used by their instructions.
2. **Function Mode** is for users who want practice with function call/return and stack set-up and tear-down, and with writing functions in assembly. This mode provides the start of a `main` function with some stack set up and tear down and return instructions added. A user adds additional instructions to `main`, including support for adding calls to additional functions that they add.
3. **Full Program Mode** is for users who want to write a full program to trace through. This mode does not provide any starting point assembly scaffolding code like the other two modes.

See our [SIGCSE'25 paper](#papers) for more information about this tool, including an evaluation of its use in introductory systems courses.

### Interactive Exercises

With external exercise developers and our students, we are currently adding interactive exercises to our online textbook. Some of these also include our development of new interactive exercise tools specifically for exercises on computer systems topics, most notabily our "Ask me Another" components.

This work is currently under development. Our in-progress exercises are available online (and are also linked to from our online textbook chapters): [Dive into Systems Interactive Exercises](https://diveintosystems.org/exercises/frontmatter.html)

#### Exercise Developers

Our NSF sponsored project supports experts from our community to help develop book exercises, and supports [students](#people) to help with the development of interative tools and with the implementation of the exercises in their interactive, online form.

We are grateful to our team of exercise developers for their work in helping to create these exercises:

| Tanya Amert, Carleton College | Jeannie Albrecht, Williams College |
| --- | --- |
| John Barr, Ithaca College | David Bunde, Knox College |
| Danielle Ellsworth, Colorado College | Sat Garcia, Univ. of San Diego |
| Roberto Hoyle, Oberlin College | Bill Kerney, Clovis Community College |
| Zachary Kurmas, Grand Valley State Univ. | Sunjae Park, Wentworth Institute of Technology |
| Crystal Peng, Park Univ. | Christine Reily, Skidmore College |
| John Rieffel, Union College | Kathleen Riley, American Univ. |
| John Stratton, Whitman College | Brian Toone, Samford Univ. |
| Dee Weikle, James Madison Univ. | Richard Weiss, The Evergreen State College |
| Bryce Wiedenbeck, Davidson Univ. |  |

### Curated Ask me Another Exercises

[Curated Ask me Another Component Exercises](https://diveintosystems.org/askmeanother)

These are a set of exercises created from some of our "Ask me Another" interactive components (see our SIGCSE'27 paper for more details). They are desgined for an instructor to deliver as in-class activities, each one as a 10-15 activity.

These are created from versions of the some of our "Ask me Another" interactive components, **all of which are also available from the Dive into Systems interactive exercises linked to from the end of every chapter**. These are currently under development (we plan to add more)

## Activities

### Announcements

We are delighted to announce our **NSF sponsored project to add interactive content to our textbook**. We are adding interactive exercises to the end of textbook chapters, many of which have been completed. Exercise questions were developed with the help of the larger community as part of our Exercise Developers program (2022-2026). The interactive chapter exercises also includes our novel "Ask me Another" components, developed with Swarthmore students. Additionally, we are expanding our intructor portal contents as part of this effort.

To hear information about our book and updates to our book, please subscribe to our low-volume [Mailing List](#mailinglist).

### Events

- [SIGCSE'27 Affiliated Event: Diving into the Future of Computer Systems Education](https://diveintosystems.org/sigcse27/). **Wednesday, February 17, 2027**, 2-5:15 PM, See the link for more details, and to fill out the RSVP form to register for this event.
- Paper Presentation: "A Free Online Textbook and Interactive Exercises for Introducing Parallel Computing", [EduHPC-26](https://cdercenter.org/eduhpc-2026-technical-program/), (in conjunction with [SC'26](https://sc26.supercomputing.org/)) Nov. 15, 2026
- Paper Presentation: "Ask me Another: Generating Infinite Systems Practice Exercises", [SIGCSE'27](https://2027.sigcse-ts.acm.org/program/program-sigcse-ts-2027/?date=Thu%2018%20Feb%202027), Feb. 18, 2027

##### Past Events/Presentations

- [SIGCSE'25 Affiliated Event: Collaboratively Developing Dynamic and Interactive Materials for Dive into Systems](https://diveintosystems.org/sigcse25/). **Wednesday, February 26, 2025**, 1-5:45 PM,
- [SIGCSE'25 Paper Presentation: "ASM Visualizer: a Learning Tool for Assembly Programming"](https://sigcse2025.sigcse.org/details/sigcse-ts-2025-Papers/21/ASM-Visualizer-a-Learning-Tool-for-Assembly-Programming) Sat, March 1, 10:45 AM EST
- Presentation, NSF June 2024.
- [SIGCSE'24 Affiliated Event: Building interactivity into Dive into Systems](https://diveintosystems.org/sigcse24/). Wednesday, March 20, 2023, 1-5:45 PM, See the link for more details.
- Presentation, [WCAE'23](https://www.csc2.ncsu.edu/faculty/efg/people/www/wcae2023.html) "A Free Online Textbook Introducing Computer Architecture Topics", Tia Newhall, Suzanne Matthews, Kevin Webb, Orlando, FL, USA, June 17 2023. ([paper](https://dl.acm.org/doi/10.1145/3605507.3610627), [talk slides](https://www.cs.swarthmore.edu/~newhall/papers/wcae23talk.pdf))
- [SIGCSE'23 Affiliated Event: Building interactivity into Dive into Systems](https://diveintosystems.org/sigcse23/). Wednesday, March 15, 2023, Toronto, CA. ([program link](https://sigcse2023.sigcse.org/details/sigcse-ts-2023-affiliated-events/8/Collaboratively-Developing-Dynamic-and-Interactive-Materials-for-Dive-into-Systems))
- Presentation, [CCSC Eastern'22](https://sites.google.com/site/ccsceastern/conference-info): " *Adding Interactive Content to Dive into Systems, a free online textbook for introducing students to computer systems* ". ([talk slides](https://www.cs.swarthmore.edu/~newhall/papers/ccsce22_talk.pdf))
- Panel: " *How do you write an open-access textbook and why should you do it?*". Panelists: Carmelo Galanti, Temple University, Donald Wargo, Temple University, Tia Newhall, Swarthmore College. Moderated by Suzanne J. Matthews, West Point. Oct. 13, 2022, Friends Center, Philadelphia, PA. Sonsored by the Aydolotte Foundation and Swarthmore College Libraries.
- Presentation, [SIGCSE'21](https://sigcse2021.sigcse.org/schedule/): " *Dive into Systems: A Free, Online, Textbook for Introducing Computer Systems* ". ([open access paper](https://dl.acm.org/doi/abs/10.1145/3408877.3432514), [talk slides](https://www.cs.swarthmore.edu/~newhall/papers/sigcse21_talk.pdf))
- Panel, [SIGCSE'21](https://sigcse2021.sigcse.org/schedule/): " *TextbooksForAll: Free textbooks and their place in computer science education* ". Suzanne Matthews, Chris Mayfield, Remzi Arpaci-Dusseau, Kevin Webb. ([abstract](https://dl.acm.org/doi/10.1145/3408877.3432567))

### Papers

See our [open-access paper from SIGCSE'21](https://dl.acm.org/doi/abs/10.1145/3408877.3432514) for more information about our textbook, including an evaluation from student and faculty participants in our [2019-2020 Early Adopters](#earlyadopt) Program.

- "Ask me Another: Generating Infinite Systems Practice Exercises", Kevin Webb, Tia Newhall, Suzanne Matthews. To appear in ACM Technical Symposium on Computer Science Education [SIGCSE'27](https://2027.sigcse-ts.acm.org/), February 2027
- "A Free Online Textbook and Interactive Exercises for Introducing Parallel Computing", Suzanne Matthews, Tia Newhall, Kevin Webb. To appear in the Workshop on Education for High-Performance Computing [EduHPC-26](https://cdercenter.org/eduhpc-2026/) in conjunction with the ACM-IEEE International Conference for High Performance Computing, Networking, Storage and Analysis ([SC'26](https://sc26.supercomputing.org/)
- ["ASM Visualizer: a Learning Tool for Assembly Programming"](https://dl.acm.org/doi/10.1145/3641554.3701793) Tia Newhall, Kevin Webb, Isabel Romea, Emma Stavis, Suzanne Matthews, To appear in Proceedings of the 56th ACM Technical Symposium on Computer Science Education (SIGCSE'25), March 2025.
- ["A free Online Textbook Introducing Computer Architecture Topics"](https://dl.acm.org/doi/10.1145/3605507.3610627), Tia Newhall, Suzanne Matthews, Kevin Webb. In Proceedings of the Workshop on Computer Architecture Education ([WCAE'23](https://www.csc2.ncsu.edu/faculty/efg/people/www/wcae2023.html)) in conjunction with the 50th International Symposium on Computer Architecture ([ISCA](https://iscaconf.org/isca2023/)), June 2023. ([talk slides](https://www.cs.swarthmore.edu/~newhall/papers/wcae23talk.pdf))
- ["Dive into Systems: A Free, Online Textbook for Introducing Computer Systems"](https://dl.acm.org/doi/abs/10.1145/3408877.3432514), Suzanne J. Matthews, Tia Newhall, Kevin C. Webb. In Proceedings of the 52nd ACM Technical Symposium on Computer Science Education (SIGCSE '21), March, 2021. ([talk slides](https://www.cs.swarthmore.edu/~newhall/papers/sigcse21_talk.pdf))

## Using Dive into Systems

Everyone is free to use *Dive into Systems* in their course! The book will remain free online. If you are using *Dive into Systems* at your institution, please reach out and let us know ([authors@diveintosystems.org](mailto:authors@diveintosystems.org))! This information will really help us continue to expand the book.

### 2019-2020 Early Adopters

*Dive into Systems* was first piloted as a textbook in the Computer Organization course at West Point in Fall 2018 and in the ([Intro to Computer Systems](https://www.cs.swarthmore.edu/~newhall/cs31)) at Swarthmore College in Spring 2019. In Fall 2019, *Dive into Systems* launched its Early Adopter Program, which enabled faculty around the United States to pilot the stable release of *Dive into Systems* at their institutions. The Early Adopter Program was a huge help to the authors, as it helped us get valuable insight into student and faculty experiences with the textbook. We used the feedback we receive to improve and strengthen the content of *Dive into Systems*, and are very thankful to everyone who completed our student and faculty surveys.

The following individuals piloted *Dive into Systems* as a textbook at their institutions during the 2019-2020 Academic Year:

| [John Barr](https://faculty.ithaca.edu/barr/) (Ithaca College) | [Chris Branton](https://www.drury.edu/math-and-computer-science/christopher-branton) (Drury Univ.) |
| --- | --- |
| [Dick Brown](https://www.stolaf.edu/profile/rab) (St. Olaf College) | [David Bunde](http://faculty.knox.edu/dbunde/) (Knox College) |
| [Bruce Char](https://www.cs.drexel.edu/~bchar/) (Drexel Univ.) | [Bryan Chin](https://sites.google.com/eng.ucsd.edu/bryan-chins-page/home) (U.C. San Diego) |
| [Stephen Carl](https://www.sewanee.edu/academics/computer-science/facstaff/carl.html) (Sewanee: The Univ. of the South) | [John Dougherty](https://johnpdougherty.com/) (Haverford College) |
| [John Foley](https://jjfoley.me/) (Smith College) | [Elizabeth Johnson](https://www.xavier.edu/computer-science-department/directory/liz-johnson) (Xavier Univ.) |
| [Bill Kerney](https://www.cloviscollege.edu/directory/william-kerney.html) (Clovis Community College) | [Deborah Knox](https://computerscience.tcnj.edu/faculty-staff/faculty/dr-deborah-knox/) (The College of New Jersey) |
| [Doug MacGregor](https://western.edu/people/doug-macgregor-phd/) (Western Colorado Univ.) | Jeff Matocha (Ouachita Baptist Univ.) |
| [Keith Muller](https://cseweb.ucsd.edu/~muller/) (U.C. San Diego) | Crystal Peng (Park Univ.) |
| [Leo Porter](https://cseweb.ucsd.edu/~leporter/) (U.C. San Diego) | [Lauren Provost](https://www.simmons.edu/academics/faculty/lauren-provost) (Simmons Univ.) |
| Kathleen Riley (Bryn Mawr College) | [Roger Shore](http://www.highpoint.edu/engineering/rshore/) (High Point Univ.) |
| [Tony Tong](http://cs.wheatoncollege.edu/~ttong/) (Wheaton College, Norton MA) | [Brian Toone](https://www.samford.edu/arts-and-sciences/directory/Toone-Brian-R) (Samford Univ.) |
| [David Toth](https://www.centre.edu/directory/name/david-toth/) (Centre College) | [Bryce Wiedenbeck](https://www.davidson.edu/people/bryce-wiedenbeck) (Davidson College) |

### Current Adopters

The following institutions are currently using *Dive into Systems*. **If you don’t see your institution listed, please reach out to us ([authors@diveintosystems.org](mailto:authors@diveintosystems.org))!**

**U.S. Adopters**

![_Dive into Systems_ adopters around the United States](https://diveintosystems.org/institutions.png)

| **Alabama**  - Samford University - The Altamont School  **Arkansas**  - Ouachita Baptist University  **California**  - California Institute of Technology - Clovis Community College - U.C. San Diego - University of San Diego  **Colorado**  - Colorado College - Western Colorado University  **District of Columbia**  - American University  **Delaware**  - University of Delaware  **Florida**  - University of Florida  **Illinois**  - Knox College  **Indiana**  - Earlham College - Hanover College - Indiana University South Bend  **Iowa**  - Kirkwood Community College  **Kentucky**  - Centre College  **Massachusettes**  - Amherst College - Northeastern University - Simmons University - Smith College - Wentworth Institute of Technology - Wheaton College - Worcester Polytechnic Institute  **Minnesota**  - Carleton College - Macalester College - St. Cloud State University - St. Olaf College  **Missouri**  - Drury University - Park University | **New Jersey**  - The College of New Jersey  **New York**  - Barnard College - Colgate University - CUNY - College of Staten Island - CUNY - Hunter College - Hofstra University - Ithaca College - Pace University - Skidmore College - St. Lawrence University - West Point  **North Carolina**  - Davidson College - Duke University - High Point University - UNC Charlotte - Wake Forest University  **Ohio**  - Lakeland Community College - Xavier University  **Oregon**  - Lewis and Clark - Portland State University - Pactific University  **Pennsylvania**  - Bryn Mawr College - Drexel University - Haverford College - Kutztown University - Lafayette College - Lehigh University - Misericordia University - Swarthmore College - University of Pennsylvania - Widener University  **Tennesee**  - Rhodes College - Sewanee: University of the South  **Washington**  - Evergreen State College - University of Puget Sound  **Wisconsin**  - Marquette University - University of Wisconsin - Eu Claire |
| --- | --- |

**International Adopters**

- NYU Paris - Paris, France
- Polish-Japanese Academy of Computer Science - Warsaw, Poland
- IT University of Copenhagen - Copenhagen, Denmark

## People

**Principle Investigators**

- [Suzanne J. Matthews](http://www.suzannejmatthews.com/), West Point
- [Tia Newhall](https://www.cs.swarthmore.edu/~newhall/), Swarthmore College
- [Kevin C. Webb](https://www.cs.swarthmore.edu/~kwebb/), Swarthmore College

**Current Students:**

- Akiva Sherin, Swarthmore College
- Bohou Zhang, Swarthmore College

**Past Students:**

| Jay Iyer, Swarthmore College | Jasmine Fan, Swarthmore College |
| --- | --- |
| Zhengfei (Alex) Li, Swarthmore College | Khang (Tony) Cao, Swarthmore College |
| Xiaoya (Yana) Yuan, Swarthmore College | Yue Zhang, Swarthmore College |
| Emily Dai, Swarthmore College | Noor Ali, Swarthmore College |
| Grace Kim, West Point | Arys Aikyn, Swarthmore College |
| D’Angelo Gourdine, West Point | Kuzivakwashe Mavera, Swarthmore College |
| Dylan Green, West Point | Sigrid Lokensgard, Swarthmore College |
| Isabel Romea, Swarthmore College | Paulina Trifonova, Swarthmore College |
| Emma Stavis, Swarthmore College | Rezhwan Kamal, Swarthmroe College |
