# setplayer
An AI that can play online [set](https://en.wikipedia.org/wiki/Set_(card_game)).

This AI can play single player and multiplayer set on [smart-games.org](https://smart-games.org/en/set/open_cards).
The solver itself was easy to build and detecting matches just needed modular arithmetic.
It was much harder to to manage information transfer to and from the website. 
I used [requests](https://requests.readthedocs.io/en/master/), [regex](https://docs.python.org/3/library/re.html), and [lxml](https://lxml.de/) to manage REST transactions.
However, the website also used [realplexor](https://github.com/DmitryKoterov/dklab_realplexor) to manage push messaging from the server to the client.
The hard part was that [realplexor](https://github.com/DmitryKoterov/dklab_realplexor) is a streaming [Comet](https://en.wikipedia.org/wiki/Comet_(programming)) server from 2009, 
predating [websockets](https://en.wikipedia.org/wiki/WebSocket) and [server-sent-events](https://en.wikipedia.org/wiki/Server-sent_events). 
I had to reverse engineer the [hidden iframe](https://en.wikipedia.org/wiki/Comet_(programming)#Hidden_iframe) used by this system to intercept the push messages.

I built this system to beat my girlfriend at online Set while we were separated because of Covid-19 Quarantine :)
