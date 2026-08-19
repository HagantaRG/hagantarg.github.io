# It Works!
19 August 2026

I finally managed to get the TfL Rust app to work as a web app! Hurray! Hopefully, you should be able to see that [here.](https://hagantarg.github.io/london-trains-eframe/) That was the thing I expected to be easier. The next part will be a bit trickier since I now want to
display some kind of approximation of each in-flight train's positions on the map. 

I will need to be able to roughly guesstimate where a train is from the data that TfL's API provides, and that isn't directly available. So! What I will be trying to do is to get
average travel times between any two stations on the TfL line. Which is tricky, since that also isn't data that TfL provides particularly nicely.

Notable problems:
- I do not know when trains depart from a station. This is the biggest problem, and what will require the most work. I will probably try to update this blog with some details
of how I actually resolve this since I think that will necessarily be some kind of. Hacky monstrosity.

- I do not *easily* know which station a train has departed from. That data is not *directly* available in the TfL API, but I think I can finagle it. Sort of. Will be a little hacky, though.
