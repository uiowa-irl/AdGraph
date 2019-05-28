# AdGraph
Abstract—User demand for blocking advertising and tracking
online is large and growing. Existing tools, both deployed and
described in research, have proven useful, but lack either the
completeness or robustness needed for a general solution. Existing
detection approaches generally focus on only one aspect of
advertising or tracking (e.g. URL patterns, code structure),
making existing approaches susceptible to evasion.
In this work we present ADGRAPH, a novel graph-based
machine learning approach for detecting advertising and tracking
resources on the web. ADGRAPH differs from existing approaches
by building a graph representation of the HTML structure, network
requests, and JavaScript behavior of a webpage, and using
this unique representation to train a classifier for identifying
advertising and tracking resources. Because ADGRAPH considers
many aspects of the context a network request takes place in,
it is less susceptible to the single-factor evasion techniques that
flummox existing approaches.
We evaluate ADGRAPH on the Alexa top-10K websites, and
find that it is highly accurate, able to replicate the labels of
human-generated filter lists with 95.33% accuracy, and can even
identify many mistakes in filter lists. We implement ADGRAPH
as a modification to Chromium. ADGRAPH adds only minor
overhead to page loading and execution, and is actually faster
than stock Chromium on 42% of websites and AdBlock Plus
on 78% of websites. Overall, we conclude that ADGRAPH is
both accurate enough and performant enough for online use,
breaking comparable or fewer websites than popular filter list
based approaches.
