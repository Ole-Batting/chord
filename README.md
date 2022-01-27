# chord

Guitar chord diagram generator

Intended for notebook usage in root directory.

Basic example

```
from chord import Guitar
guitar = Guitar() # creates a guitar object with default settings
guitar('Bm7') # will print all voicings for B minor 7th
```

Tonewise example
```
from chord import Guitar
guitar = Guitar()
guitar.chord_print(['C','E','G']) # will print all voicings for C major
```

Tuning example
```
from chord import Guitar
guitar = Guitar(tuning=['E4','B3','G3','D3','A2','D2']) # drop d tuning instead of standard
guitar('DM') # will print all voicings for D major
```
