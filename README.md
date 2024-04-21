RateMyDemo on sivusto, jossa muusikot voivat ladata demojaan tai julkaisujaan muiden kuunneltavaksi.
Oleellinen osa sivustoa on mahdollisuus arvioida näitä julkaisuja, jolloin käyttäjät voivat hakea esimerkiksi suosituimmat julkaisut sivustolta mm. genren tai julkaisuvuoden mukaan.
Sivustolla sekä artistit, että tavalliset käyttäjät käyttävät samanlaista käyttäjätiliä, joten kuka tahansa voi ladata musiikkiaan ja arvostella muiden musiikkia.

Tällä hetkellä sivustolla on mahdollisuus luoda käyttäjätili ja kirjautua sisään, julkaista äänitiedostoja sekä kuunnella ja arvostella muiden julkaisuja. Julkaisuja voi selata lajittelemalla ne eri tavoin, tai hakemalla niitä lataajan käyttäjänimen tai julkaisun nimen perusteella.

Projekti on css teemaa, sekä muutamaa ominaisuutta vaille valmis.

Ohjeet sivuston testaamiseen paikallisesti (olettaen, että Postgresql on jo valmiiksi asennettu ja toiminnassa):

Lataa tämä repo tietokoneellesi ja navigoi sen juurikansioon

Kirjoita nämä komennot terminaaliin:
$ python3 -m venv venv
$ source venv/bin/activate (käynnistää virtuaaliympäristön)
$ pip install -r ./requirements.txt (asentaa vaaditut kirjastot)
$ psql < schema.sql (luo vaaditut taulut tietokantaan)

Luo .env tiedosto ja määritä sen sisältö näin:
DATABASE_URL=<tietokannan-paikallinen-osoite>
SECRET_KEY=<salainen-avain>

Käynnistä sovellus komennolla:
$ flask run
