I've been trying to improve the rendering on the map in the Rust trains app. I had originally wanted to just shove *some* semblance of
multi-color line rendering in and so asked Codex to draw up a very quick implementation. I have since gotten *very* annoyed at
the provided implementation.

There's a few problems. One is that the way lines are grouped together means that some valid rail segments just get "deleted."
Which is very annoying, since it makes the map just flat out wrong:

![This is bad!][problem-1.png]

The other problem is that for rail segments that are *really* close to each bother but not joining the same two stations (such as
the section of the Jubilee/Metropolitan line below) it also renders wrong! Gah!

![This is annoying, but less bad.][problem-2.png]

The problem here, that I did not *realise* was the problem here until a few hours ago, was that I naively assumed that only
segments of track spanning two stations would be close to each other. Which. Honestly. Why did I assume that?

I've spent the last few days trying to fix this. Unfortunately, my initial implementation of a fix had yet to realise that the
assumption I made above was just *wrong.* Now, I will need to rip out the very-very-nice segment painting functionality I had made,
and shove in basically a totally new one. 

BUT. By god these lines will draw nicely.