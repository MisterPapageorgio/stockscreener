from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Bewertungslogik | Quality Dip Scanner",
    page_icon=":material/rule:",
    layout="wide",
)

st.html(
    """
    <style>
    .logic-kicker {
        color: #ff7058;
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.14em;
        text-transform: uppercase;
    }
    .logic-title {
        font-size: 2rem;
        font-weight: 780;
        letter-spacing: -0.04em;
        margin: 0.25rem 0 0.4rem;
    }
    .logic-intro {
        color: #9aa9a8;
        font-size: 1rem;
        margin-bottom: 1.6rem;
        max-width: 760px;
    }
    .weight {
        color: #55c2ae;
        font-size: 1.8rem;
        font-weight: 800;
    }
    .muted {
        color: #9aa9a8;
    }
    .brandbar {
        margin-bottom: 1.25rem;
        margin-top: -5.5rem;
        padding-top: 0.5rem;
    }
    .brand {
        align-items: center;
        display: flex;
        gap: 0.7rem;
    }
    .brand-mark {
        align-items: center;
        background: #ff7058;
        border-radius: 9px;
        color: #ffffff;
        display: flex;
        font-size: 0.75rem;
        font-weight: 800;
        height: 30px;
        justify-content: center;
        width: 30px;
    }
    .brand-name {
        color: #eef5f1;
        font-size: 0.92rem;
        font-weight: 800;
    }
    .brand-context {
        color: #9aa9a8;
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        margin-top: 0.12rem;
        text-transform: uppercase;
    }
    [data-testid="stSidebarNav"] {
        display: none;
    }
    [data-testid="stSidebar"] {
        background: #141b1d;
        border-right: 1px solid #2d393b;
    }
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 0.5rem;
    }
    [data-testid="stSidebar"] [data-testid="stHtml"] {
        pointer-events: none;
    }
    .sidebar-nav-label {
        color: #9aa9a8;
        font-size: 0.66rem;
        font-weight: 800;
        letter-spacing: 0.12em;
        margin: 0.6rem 0 0.35rem;
        text-transform: uppercase;
    }
    .sidebar-nav-divider {
        border-top: 1px solid #2d393b;
        margin: 0.75rem 0 1.15rem;
    }
    [data-testid="stSidebar"] a[data-testid="stPageLink"] {
        border-radius: 8px;
        padding: 0.45rem 0.55rem;
    }
    [data-testid="stSidebar"] a[data-testid="stPageLink"]:hover {
        background: #202a2c;
    }
    </style>
    """
)

with st.sidebar:
    st.html(
        """
        <div class="brandbar">
            <div class="brand">
                <div class="brand-mark">QD</div>
                <div>
                    <div class="brand-name">Quality Dip Scanner</div>
                    <div class="brand-context">Nasdaq-100 signal desk</div>
                </div>
            </div>
        </div>
        """
    )
    st.markdown('<div class="sidebar-nav-label">Workspace</div>', unsafe_allow_html=True)
    st.page_link("app.py", label="Scanner", icon=":material/dashboard:")
    st.page_link(
        "pages/Bewertungslogik.py",
        label="Bewertungslogik",
        icon=":material/rule:",
    )
    st.markdown('<div class="sidebar-nav-divider"></div>', unsafe_allow_html=True)

st.markdown(
    """
    <div class="logic-kicker">Methodik</div>
    <div class="logic-title">Wie entsteht der Score?</div>
    <div class="logic-intro">
        Der Scanner sucht Qualitätsunternehmen, deren Aktie ungewöhnlich gefallen ist.
        Dafür werden Kursbewegung, Geschäftsqualität und Bewertung getrennt betrachtet
        und anschließend zu einem Gesamtscore von 0 bis 100 kombiniert. Zusätzlich zeigen
        zwei Sektortrend-Signale, ob die aktuelle Bewegung kurzfristig oder über mehrere
        Monate breit im jeweiligen Sektor getragen wird.
    </div>
    """,
    unsafe_allow_html=True,
)

logic_cols = st.columns(3)
with logic_cols[0].container(border=True):
    st.markdown('<div class="weight">35 %</div>', unsafe_allow_html=True)
    st.subheader("Dip")
    st.caption("Wie ungewöhnlich ist der Kursrückgang?")
with logic_cols[1].container(border=True):
    st.markdown('<div class="weight">45 %</div>', unsafe_allow_html=True)
    st.subheader("Quality")
    st.caption("Wie robust und profitabel ist das Unternehmen?")
with logic_cols[2].container(border=True):
    st.markdown('<div class="weight">20 %</div>', unsafe_allow_html=True)
    st.subheader("Value")
    st.caption("Wie attraktiv ist der Preis im Verhältnis zum Geschäft?")

st.subheader("1. Dip-Score")
st.write(
    "Der Dip-Score steigt, wenn eine Aktie gegenüber dem Nasdaq-100 zurückbleibt, "
    "über mehrere Wochen fällt oder deutlich unter ihrem 52-Wochen-Hoch notiert. "
    "Ein erhöhtes Handelsvolumen und ein ungewöhnlicher kurzfristiger Schock fließen ebenfalls ein."
)
with st.container(border=True):
    st.markdown(
        """
        **Gewichtung innerhalb des Dip-Scores**

        - 40 %: Abstand zum 52-Wochen-Hoch
        - 30 %: 20-Tage-Kursrückgang
        - 15 %: relative 5-Tage-Performance zum Nasdaq-100
        - 10 %: ungewöhnlicher Kurs-Schock
        - 5 %: Handelsvolumen gegenüber dem 20-Tage-Durchschnitt
        """
    )

st.subheader("2. Quality-Score")
st.write(
    "Der Quality-Score misst nicht die Kursbewegung, sondern die wirtschaftliche Substanz. "
    "Wachstum, Cashflow, Kapitalrendite und Margen werden jeweils auf eine gemeinsame Skala von 0 bis 100 normiert."
)
with st.container(border=True):
    st.markdown(
        """
        **Verwendete Qualitätskennzahlen**

        - Umsatzwachstum: 15 %
        - EPS-Wachstum: 15 %
        - Free-Cashflow-Wachstum: 15 %
        - ROIC: 20 %
        - Free-Cashflow-Marge: 20 %
        - Operative Marge: 15 %
        """
    )

st.subheader("3. Value-Score")
st.write(
    "Der Value-Score beschreibt, wie günstig der Markt das Unternehmen im Verhältnis zu seiner Ertragskraft bewertet. "
    "Ein höherer Wert bedeutet im Modell eine attraktivere Bewertung."
)
with st.container(border=True):
    st.markdown(
        """
        **Verwendete Bewertungskennzahlen**

        - Free-Cashflow-Rendite: 45 %
        - KGV-Abschlag: 25 %
        - EV/EBIT-Abschlag: 20 %
        - PEG-Abschlag: 10 %
        """
    )

st.info(
    "Aktueller Datenstand: Die SEC liefert bereits Free Cashflow, Margen und ROIC. "
    "KGV-, EV/EBIT- und PEG-Abschläge sind derzeit neutral mit 0 vorbelegt. "
    "Der Value-Score basiert deshalb momentan praktisch auf der Free-Cashflow-Rendite.",
    icon=":material/info:",
)

st.subheader("4. Sektortrend: kurzfristig und über 6 Monate")
st.write(
    "Die beiden Sektortrend-Signale sind separate Marktbreite-Signale und fließen nicht in den Overall-Score ein. "
    "Er vergleicht die mediane 20-Tage-Performance eines Sektors mit dem Nasdaq-100 "
    "und betrachtet zusätzlich, wie viele Titel positiv relativ zum Index liegen. "
    "Dadurch wird sichtbar, ob eine Bewegung nur von einzelnen Aktien getragen wird "
    "oder den gesamten Sektor betrifft."
)
with st.container(border=True):
    st.markdown(
        """
        **Berechnung**

        Für jeden Sektor werden zwei Werte ermittelt:

        - **Relative Performance**: Median der 20-Tage-Renditen gegenüber dem Nasdaq-100
        - **Marktbreite**: Anteil der Sektortitel mit positiver relativer Performance

        **Interpretation der Labels**

        - **Überhitzt**: mindestens 8 % relative Performance und mindestens 65 % positive Titel
        - **Stark**: mindestens 3 % relative Performance und mindestens 55 % positive Titel
        - **Neutral**: kein eindeutiger Sektortrend
        - **Schwach**: höchstens -3 % relative Performance und höchstens 45 % positive Titel
        - **Geschwächt**: höchstens -8 % relative Performance und höchstens 40 % positive Titel

        Beispiel: Steigen die meisten Halbleiteraktien deutlich stärker als der Nasdaq-100,
        wird **Semiconductors** als **Überhitzt** markiert. Fallen Softwaretitel dagegen
        geschlossen hinter den Index zurück, lautet das Signal **Geschwächt**.

        **Sektortrend 6M**

        Zusätzlich wird derselbe Vergleich über rund sechs Monate beziehungsweise 126 Handelstage
        berechnet. Die längere Sicht filtert kurzfristiges Rauschen: Ab **+6 %** relativer
        Performance gilt ein Sektor bei ausreichender Breite als **Stark**, ab **+15 %** als
        **Überhitzt**. Entsprechend beginnen **Schwach** und **Geschwächt** bei **-6 %** und
        **-15 %**. Der Mehrmonatstrend ist ebenfalls ein Kontextsignal und verändert den Overall-Score nicht.

        Stimmen beide Signale überein, ist der Trend robuster. Weichen sie voneinander ab,
        deutet das häufig auf eine kurzfristige Beschleunigung oder eine nachlassende Bewegung hin.
        """
    )

st.subheader("Gesamtscore")
st.latex(r"\text{Overall} = 0{,}35 \cdot \text{Dip} + 0{,}45 \cdot \text{Quality} + 0{,}20 \cdot \text{Value}")
st.caption(
    "Die Scores sind Orientierungswerte für das Ranking und ersetzen keine eigene Analyse. "
    "Sie sind relativ zur gewählten Skalierung und den verfügbaren Daten zu verstehen."
)
