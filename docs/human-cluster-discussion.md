## Changes needed:
- On the Pure Flavor page, as far as I can tell, all of the images are exactly the same.
- The legend on the graphs isn't necessary because you have the label now, and what's worse is that it actually obscures the data.
- The shape around the drinks is no longer accurate. It's kind of all over the place and doesn't actually go around the drinks.
- The baseline display size for the images is too small. They should be at least readable without having to click on them, and they're just not at this point. Even if we were to stretch it sideways, that would be nice if it adapted to the larger part. It seems like when you go small, it gets really good up to a point, but then when you try to go large, it makes the wrong assumption.
- The new heatmap is good. Only issue is that there is actually a lot more range than the map is showing because 4, 6, and 8 are all the same color, despite the fact that you now have 8 different clustering strategies. So it would be good to see some more color range there.
- There isn't any difference between intensity-weighted and flavor structure blends views, from a practical perspective. There are three groups in each.

Here's how I see it:
## Perceptual blend
- At the lowest end, it seems like there are two groups, maybe three, with some outliers, but if you actually drill down into that, what you see is you've got, again, you've got your sours, mostly, you've got your sours in one huge cluster, and then your spirit forward in the other. But you have these little clusters where one is, it has lime and the other one is, it has chartreuse and another one where they have absinthe. But as soon as you crank tau up even just a little bit to 0.14, those tiny little offshoots merge back in.
- The perceptual blend at tau = 0.38, there are pretty clearly three groups. They cluster pretty nicely into sour and two different clusters of spirit forward that seem to be either whiskey or gin-based. That's pretty interesting.
- When you get up to .75, you have 4 very clear clusters, two sour clusters and two spirit forward clusters. Those segregate by base spirit, but the Whiskey Sours are close to some other ones that are not Whiskey Sours, like rum and cognac base.
- There also seems to be sort of a spectrum in that sour family where one side vs. the other tends to have a bit more gin drinks vs. other.
- As we move up to about tau = 4 (the middle here), there's a lot less clear division. I think it's interesting that the sours sit in the middle, but the spirit forwards are much more spread out. They're much closer, so you could almost say, "Well, you've got the sours that go towards the rum direction and then the sours that are more of the whiskey right?" And I think that's interesting.
- As you get higher, not a lot changes! One thing that's notable is this little whiskey sour island that seems to keep popping up but really stays separate from about tau=4 upward.

## Taste and structure
- At alpha = 0, it's actually really interesting because the clusters are so tight. I see 8 really clear clusters in here. And so I'm curious about what those clusters are. Is it just the mix of the ingredients? What is it about those clusters that are so clear?
- At alpha = 0.3, you start to see some of the clusters coalesce. Now I think there's maybe arguably 5.
- I think probably the most interesting point on all of these is alpha at 0.55, where there are clearly three clusters, and none of them is strictly a sour or spirit-forward cluster.
- And then on your way up from there to alpha=1, there's just all this shifting and reshuffling that's like, "What is actually happening? What's going on? Where are the territories? Where are things?" It's really hard to get a grasp on it, so that's maybe one of the interesting places to analyze in all this.
- When you get up to alpha = 1, it seems like we're basically recapitulating the sours are in one place, and then you have your whiskey drinks and your gin drinks, and it looks like a perceptual blend.
- And then Recipe Grammar has 5 clusters, with one of the clusters having a few distinct regions within it very clearly.

