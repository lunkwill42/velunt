# Velunt

> Drik, venner kjære, mitt øl velunt skal være

Dette skal bli et system som skal bidra til å gjennomføre ølsmakinger (typisk
blindsmaking), der deltakerne kan gi hvert øl poeng etter gitte regler, og hvor
systemet til slutt kan presentere rangerte lister og statistikk.

## Bakgrunn

En gjeng tidligere Uninett-ansatte har over mange år hatt som tradisjon å samle
seg i november/desember for å smake seg gjennom et utvalg av årets juleøl fra
Vinmonopolet (men også hjemmebrygg), for så å kåre et vinnerøl. Dette er for
det meste et sosialt arrangement blant ølinteresserte venner.

I moderne tid slippes det et sted mellom 200-300 sesongøl, "juleøl", på
Vinmonopolet før jul, noe man ikke har sjanse i havet til å smake seg gjennom
og vurdere på noen som helst fornuftig måte. Gjengen gjør derfor i forkant av
smaksarrangementet et utvalg av ca. 20 øl fra årets juleølslipp, ved hjelp av
en enkel avstemning, basert på et regneark med lister fra årets slipp.

Vegard har i mange år stilt som vertskap. Han tar ansvaret for innkjøp, og
sammen med sin kone, Marit, sørger de for en tilrettelegging for blindsmaking
av ølet. Blindsmakingen er ikke av "profesjonell" karakter: Alt ølet skjenkes
stort sett i deltakernes glass direkte fra originalemballasje, i påsyn av
deltakerne, men flaskene og boksene blir pakket nennsomt i aluminiumsfolie i et
forsøk på skjule kjennemerker ved emballasjen.  For at også Vegard skal være
nogenlunde "blindet", tar Marit av seg å sette nummer på ølene, samtidig som at
numrene registreres på riktig øl i et regneark over de "konkurrerende" ølene
(altså "fasiten").

Morten (undertegnede) har i mange år fungert som "beregningsutvalg". Han lager
"dommerskjema", som hver deltaker får utdelt sin egen kopi av. Her er det plass
til å notere ølnummer, poeng og smaksnotater eller generelle kommentarer om
ølet. I etterkant av arrangementet bruker Morten en god del tid på å preparere
et stort regneark og taster inn poengene fra de individuelle "dommernes"
skjemaer i dette regnearket, som så brukes til ikke bare kåre et vinnerøl, men
også til å hente ut litt gøyal statistikk: Hvilken dommer var mest positiv
(høyest gjennomsnittsscore), hvilken dommer var mest negativ (lavest
gjennomsnittsscore), eller utviser de mest stabile smaksløkene (som regel
serveres 1-2 av ølene flere ganger som "kontrolløl", for å se hvor mye
dommernes poengavgivning avviker ift. serveringsrekkefølgen). Ofte kastes det
også litt ære på det hjemmebrygget som fikk høyest plassering.

### Poengberegning

Poengsystemet til gjengen er litt sært. Da vi først begynte med disse
arrangementene, var det noen som forsøkte å bruke dommerskjema fra Norbrygg,
hjemmebryggerforeningen i Norge. Disse brukes vanligvis til flaskekonkurranser,
og i disse konkurransene dreier det seg mest om å avgjøre hvor bra et øl scorer
opp mot en stildefinisjon i den kategorien ølet konkurrerer i. Man kan ikke si
at "juleøl" fra Vinmonpolet passer inn i en enkelt kategori i Norbryggs
stildefinisjoner (en definisjon gjengen opererer med er ofte "Står det 'jul' på
etiketten er det et juleøl"), så dette ga ikke mye mening. Man gikk derfor over
til en enklere skala, som mange deltakere kjente seg igjen i: Untappd-skalen,
0-5 stjerner (eller strengt tatt, "ølkapsler"), der 5 er best mulig score, og 0
er "bånn i bøtta". Dette fungert helt ok, men ikke alle var fornøyde: Denne
skalaen førte som regel til at det alltid var en eller annen IPA-variant som
gikk av med seieren hvert år (det er flere "humlehoder" i gjengen), mens en
andel av gjengen synes IPA har lite med "jul" å gjøre. Som eneveldig
beregningsansvarlig gikk derfor Morten inn for en to-delt skala: Ett tall for
Untappd-score, og ett tall for "Julescore", altså hvor "julete" man synes ølet
er (en minst like subjektiv vurdering som Untappd-score). Ved å multiplisere
disse to tallene med hverandre, kommer man fram til dommerens sammenlagte score
for et øl. For at dette skal fungere, ble skalaen endret fra 0-5 til 1-5, slik
at en dommer ikke kan redusere sin totalscore for et øl ved å velge tall under
1 på skalaen.

Untappd tillater forskjellig presisjon i sin poengskala ut i fra om man er
betalende bruker av Untappd eller ikke, så vi bruker "gratisbruker"-skalen: Man
kan gi kvarte poeng: 1,0 og 1,25 og 1,50 og 1,75 er gyldige poeng, men 1,1 er
ikke det.

# Velunt-systemet

## Gnisten

Som "beregningsutvalg" har jeg i flere omganger tenkt på å finne eller lage et
system som gjør beregningsjobben litt enklere. Selv om det kanskje er
sjarmerende med et papirbasert system, er det et kjedelig stykke arbeid å sette
opp et regneark med matrisen over konkurrerende øl og deltakere, og å tolke
berusede menneskers håndsskrift og taste dette inn i et datasystem.

På den andre siden, på tross at av vi alle jobber i IT-bransjen og flere av oss
lager slike systemer på jobb, så har vi ofte begrenset med fritid tilgjengelig
til å holde på med sånt - spesielt for et arrangement som avholdes bare én gang
for året.

Men, med fremveksten av AI-verktøy i vår bransje ser jeg, som systemutvikler
med mange års erfaring, muligheten til å lage noe som fungerer bra uten å
investere alt for mye av fritiden min i det. En kveld i januar 2026 ramlet
plutselig idéen inn i hodet mitt igjen, og hodet ble plutselig fylt av så mange
implementasjonsidéer at det ble vanskelig å få sove for natten.

## Idéer og krav

- Jeg ser for meg et web-basert system basert på, for meg, kjent teknologi:
  Python, Django, HTMX (eller kanskje Datastar?) og PostgreSQL.  De samme
  kodestandardene som vi benytter i f.eks. NAV-prosjektet (
  https://github.com/Uninett/nav ).

- Applikasjonen skal først og fremst være tilpasset bruk fra
  mobiltelefonen.

- Jeg ser for meg et scenario hvor deltakerne kommer til arrangementet og får
  en QR-kode, som representerer det aktuelle smaksarrangementet i Velunt. Ved å
  scanne denne med mobiltelefonen sin, kommer de til en side hvor de
  umiddelbart får opp et dommerskjema for arrangementet. I skjemaet trenger de
  kun å registrere navnet sitt og begynne å fylle ut (uten noen annen form for
  registrering).

### Datamodell

- Arrangement

  - En administrator i Velunt kan opprette smaksarrangementer (eller "event",
    om man vil).

  - Et arrangement skal ha noen data knyttet til seg:

    - En unik ID som ikke er et gjettbart løpenummer (en form for forkortet
      UUID som kan brukes som referanse i URL-er)

    - En kobling til Django-brukeren som opprettet arrangementet.

    - En dato for når arrangementet ble opprettet i Velunt.

    - En dato for når arrangementet forventes gjennomført.

    - En menneskelig lesbar beskrivelse av arrangementet (f.eks. "juleølsmaking
      hos Vegard").

    - Hvorvidt arrangementet er åpent for nye registreringer (altså, om det
      fremdeles er tillatt å tilføye nye dommerskjema, eller gjøre endringer på
      dommerskjema tilknyttet arrangementet).

    - En referanse til hva slags poengsystem som benyttes i arrangementet.

  - Det skal være mulig å få generert en QR-kode for et arrangement. Denne
    QR-koden skal være en hyperlenke til en informasjonsside om arrangementet,
    hvor den som besøker siden enten kan opprette et nytt dommerskjema
    tilknyttet arrangementet - eller hvis nettleserhistorikken tilsier at de
    allerede har et aktivt skjema tilknyttet dette arrangementet så kan de
    fortsette å fylle ut det samme skjemaet.  Ingen endringer eller nye
    dommerskjema tillates opprettet dersom arrangementet har blitt lukket for
    nye registreringer, men da kan man få tilgang til eventuelle resultater.

- Dommerskjema

  - Et dommerskjema trenger en rekke metadata:

    - En unik ID som ikke er et gjettbart løpenummer (en form for forkortet
      UUID som kan brukes som referanse i URL-er)

    - En referanse til arrangementet skjemaet gjelder for.

    - Dommerens navn (dette kan være fritekst, "Morten B" eller bare "Morten"
      er ok som navn, men det kan ikke leveres to dommerskjema med identisk
      navn til samme arrangement, så om det er to Morten som deltar må de oppgi
      noe mer enn bare "Morten" som navn for å skille seg ut).

    - Tidspunkt dommerskjemaet ble opprettet på.

  - Hvert dommerskjema kan inneholde 0 til mange linjer. Hver linje
    representerer et øl det er avgitt poeng på. Hver linje må inneholde:

    - Tidspunkt linjen ble opprettet.

    - Tidspunkt linjen sist ble endret.

    - Ølnummer (integer) linjen gjelder. Dette må være unikt innenfor samme
      dommerskjema.

    - Et eller flere poeng, avhengig av hva slags poengsystem som benyttes på
      arrangementet.

    - Fritekstfelt for kommentarer og andre notater dommeren gjør seg ifm. det
      aktuelle ølet.

- Fasit

  - Våre smaksarrangementer er litt dynamiske: Det er ikke alltid et fastsatt
    antall øl i det arrangementet starter, og det er ikke alltid ølene blir
    servert i nummerrekkefølge, slik at jeg ønsker ikke å legge begrensninger på
    hvor mange øl man får registrere underveis.

  - Fasit er ikke alltid tilgjengelig i forkant av smakingen (det er heller
    ikke riktig), men fasit må kunne legges inn etter at arrangementet er
    avsluttet.

  - Fasiten sier egentlig bare hvilke øl som ble servert i smakingen, og
    hvilket nummer ølet hadde fått tildelt i smakingen.

  - Fasiten må nødvendigvis legges inn av noen som har brukerkonto i systemet.

  - Fasiten foreligger ofte i form av et regneark, så det kan være interessant
    å tilby funksjonalitet for å laste opp et regneark og gjøre automatiske
    registreringer fra det.

  - En fasit trenger noen metadata:

    - Referanse til arrangementet dette er en fasit for.

    - Tidsstempel for når den ble lagt inn.

    - Referanse til brukeren som la inn fasiten.

  - Fasiten består altså av en liste av øl. Hvert innslag i listen må ha:

    - Ølets nummer i arrangementet

    - Et navn (ofte brukes både bryggeriets og ølets navn i samme tekst)

    - Eventuelt en URL til utsalgsstedet (Vinmonopolet, i de fleste tilfeller,
      eller ingenting for hjemmebrygg).

    - Eventuelt en URL til Untappd dersom ølet fins der (ofte er dette bare en
      lenke til et Untappd-søk).

    - Det kan være aktuelt å legge inn vilkårlige URLer etter hvert, slik at
      det bør være mulig å registrere flere URLer, der hver har en beskrivelse
      av hva den peker til av Vinmonpol, Untappd eller andre nettsteder -
      kanskje til og med oppskrift i Brewfather eller Brewer's Friend for
      hjemmebrygg).

- Poengsystem

  - Selv om vi i vår gjeng har et sært poengsystem for våre juleølsmakinger,
    ser jeg for meg at Velunt kan brukes til å arrangere andre typer smakinger
    hvor man ønsker andre typer poengsystemer.

  - Et poengsystem må nødvendigvis kodes inn i systemet som et valgbart system
    per arrangement. Et system vil nødvendigvis bestå av 1 til flere
    dimensjoner, der poeng må angis i form av flyttall. Systemet må kunne sette
    begrensninger for hver dimensjon, f.eks. minste tillatte tall, høyest
    tillatte tall, hvorvidt tallet må være heltall, og om flyttall er tillatt,
    hvilke inkrementer er tillatt (f.eks.  inkrementer på 0.1 eller 0.25).  Til
    syvende og sist må systemet ha en algoritme for hvordan et endelig score
    beregnes ut i fra alle dimensjonene.

  - Vårt juleølsystem er beskrevet over, og må være del av systemet i første
    versjon: To flyttall, ett kalt "Untappd" og ett kalt "Julete", fra og med
    1.0 til og med 5.0, inkrementer på 0.25 er tillatt. Totalscore beregnes ved
    å multiplisere de to tallene.

  - Første versjon av systemet kan også tilby et enklere system som
    moteksempel: Et system som bare har 1 dimensjon, Untappd-skalaen fra 0-5 i
    0.1-inkrementer, der totalscore beregnes som summen av den ene dimensjonen.

### Brukergrensesnitt

- Det er et viktig krav at vanlige "dommere" ikke skal trenge å gå gjennom en
  registreringsprosess for å ta i bruk systemet.  Ved å få en QR-kode eller URL
  (som det ikke skal være lett å gjette seg til) som representerer et
  smaksarrangement, skal de få tilgang til å opprette et dommerskjema.  Et
  dommerskjema skal være mulig å hente tilbake om man kjenner ID-en til
  skjemaet, og så lenge et smaksarrangement fremdeles er åpent kan den som har
  denne "hemmelige" URL-en gjøre registreringer på skjemaet.  Ved å ta i bruk
  cookies eller "local storage" skal systemet kunne hente fram dommerskjema du
  tidligere har opprettet i denne nettleseren. Man kan også se for seg at det
  tilbys funksjonalitet for å kopiere ut URL til dommerskjemaet, eller å sende
  URL til dommerskjema til en oppgitt epostadresse.  Det er derfor også viktig
  at utvendig ID for et dommerskjema heller ikke er løpenummer som man kan
  gjette seg til.

- Det er et krav at systemet hovedsakelig skal være tilpasset små skjermer,
  altså bruk på mobiltelefon.

- De som trenger faktiske Django-brukere i systemet er de som skal ha tilgang
  til å opprette nye smakinger. Jeg ser for meg at flere kan få tilgang til å
  opprette smakinger, men de må da ikke få tilgang til å gjøre endringer eller
  se på smaksarrangement andre har laget (dette kan bare admins gjøre).  Det er
  ikke i første omgang behov for et spesialtilpasset grensesnitt for å opprette
  smakinger, dette kan gjøres via Djangos admin-grensesnitt.

- De som skal ha tilgang til å laste opp en fasit for et smaksarrangement
  trenger kanskje også en Django-bruker. Enten det, eller så kan det opprettes
  en "hemmelig" URL som arrangementets eier kan dele med den som skal legge inn
  fasiten.

- Jeg er ikke noen designer, men ser for meg at duse farger med gode
  kontrastforhold for alle synstyper må være tingen. Kanskje inspirert av
  Untappds fargeskjema, eller til og med Uninetts gamle designmal :-)

- Arrangementssiden skal vise tilgjengelig informasjon om et arrangement: Dato,
  beskrivelser og hvorvidt arrangement er åpent for nye registreringer. Når et
  arrangement er avsluttet er det viktig å vise dette.  Et avsluttet
  arrangement har egentlig to tilstander: Fasit foreligger eller fasit
  foreligger enda ikke.  Når fasit foreligger, skal arrangementssiden vise all
  mulig statistikk over arrangementet, med fokus på den rangerte listen over øl
  og poengene de mottok. Dette er den siden jeg har rukket å tenke minst over
  foreløpig, så her må det jobbes frem en bedre kravspesifikasjon.

- Språk: Appen/nettstedet skal ha norsk som hovedspråk, og Norge som tidssone,
  da det i første omgang er norske brukere som vil bli utsatt for
  det. Datamodeller, attributter og kode kan med fordel ha engelske navn, men
  alle tekster i brukergrensesnitt skal være original norske. Systemet kan godt
  forberedes for oversettelser, slik at engelske oversettelser kan legges inn
  på et senere tidspunkt, om det skulle være aktuelt.

### UUID til smaksarrangement og dommerskjema

- UUID har vært nevnt som det som skal identifisere arrangementer og
  dommerskjema unikt, uten mulighet til å gjette seg til disse ID-ene (slik
  løpenummer ville gitt).  Men UUID-er er ikke menneskevennlige - de er alt for
  lange til å tastes inn. Det faktiske ID-systemet må ha ID-er som er korte nok
  til at det er overkommelig for mennesker å taste dem inn.  Det er ikke å
  forvente at systemet kommer til å inneholde tusenvis eller eller millioner av
  skjema og arrangementer (det er et sjeldent under om vi kommer over 100
  arrangementer), så det trengs en avveining mellom lengde og hvor lett det er
  å gjette seg til ID-er.
