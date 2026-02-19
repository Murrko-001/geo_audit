# Komentár k vypracovanému zadaniu

V niektorých prípadoch som považoval za vhodné mierne sa odkloniť od zadania.
V tomto krátkom komentári by som chcel vysvetliť dôvody týchto rozhodnutí.

## GEO kritérium #2: Obsahuje definíciu

Každý článok je písaný trochu inak a hlavný pojem nebýva vždy explicitne
vymedzený. Z tohto dôvodu bolo v niektorých prípadoch obtiažne jednoznačne
určiť pojem ```X```. Hľadanie vzorov typu
```"X je...", "X znamená...", "X predstavuje..."```
preto nebolo vždy praktické.

Na druhej strane, ignorovanie pojmu ```X``` a vyhľadávanie iba vzorov
```"je...", "znamená...", "predstavuje..."```
by viedlo k veľkému množstvu falošne pozitívnych výsledkov,
keďže tieto výrazy sa v texte bežne vyskytujú.

Z tohto dôvodu som sa pri vyhodnocovaní kritéria riadil nasledujúcimi pravidlami:

* ak bolo možné identifikovať hlavný pojem (nadpis obsahoval dvojbodku a text pred dvojbodkou nepresahoval dve slová),
  postupoval som podľa pôvodných pokynov zo zadania,

* ak článok obsahoval segment typu ```Čo je ... ?```, kritérium bolo automaticky splnené,

* v ostatných prípadoch článok kritérium nesplnil.

## GEO kritérium #5: Citácie zdrojov

Na blogu GymBeam sa sekcia so zdrojmi spravidla nachádza až za samotným obsahom
článku, pričom WordPress REST API túto časť neposkytuje. Z tohto dôvodu je
vyhodnocovanie citácií obmedzené na odkazy prítomné priamo v texte článku.

Zoznam požadovaných domén som rozšíril aj o
```pmc.ncbi.nlm.nih.gov```, keďže sa táto doména v analyzovaných článkoch
pravidelne vyskytovala ako zdroj vedeckých referencií.

—
Martin Murár