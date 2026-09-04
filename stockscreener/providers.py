from __future__ import annotations

import os
import json
from pathlib import Path
from threading import Lock
from threading import Event
from time import sleep, monotonic, time

import pandas as pd
import requests

SEC_HEADERS = {"User-Agent": os.getenv("SEC_USER_AGENT", "QualityDipScanner contact@example.com")}
CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache"
SEC_CACHE_TTL = 24 * 60 * 60
UNIVERSE_CACHE_TTL = 60 * 60
NDX_FALLBACK_TICKERS = "AAPL ABNB ADBE ADI ADP ADSK AEP AMAT AMD AMGN AMZN ANSS ARM ASML AVGO AXON AZN BIIB BKNG BKR CDNS CCEP CDW CEG CHTR CMCSA COST CPRT CRWD CSCO CSGP CSX CTAS CTSH DASH DDOG DXCM EA EXC FANG FAST FER FTNT GEHC GFS GILD GOOG GOOGL HON IDXX ILMN INTC INTU ISRG KDP KHC KLAC LIN LRCX LULU MAR MCHP MDB MDLZ MELI META MNST MPWR MRVL MSFT MSTR MU NFLX NTES NVDA NXPI ODFL ON ORLY PANW PAYX PCAR PDD PEP PLTR PYPL QCOM REGN ROP ROST SBUX SHOP SNPS TEAM TMUS TTD TMO TMUS TSLA TTWO TXN VRSK VRTX WBA WBD WDAY XEL ZS".split()

COMPANY_PROFILES = {
    "AAPL": ("Consumer Technology", "Integrated hardware, software and subscription ecosystem", "Designs and sells devices such as iPhone, Mac and iPad, complemented by operating systems, accessories and services such as the App Store and iCloud."),
    "ABNB": ("Travel Platform", "Commission-based accommodation and experience marketplace", "Connects guests with hosts offering homes, rooms and experiences and earns service fees on completed bookings."),
    "ADBE": ("Software", "Subscription creative and document software", "Provides subscription software for creative work, digital documents, marketing automation and customer experience management."),
    "ADI": ("Semiconductors", "High-margin analog and mixed-signal chip design", "Develops analog, power-management and mixed-signal semiconductors used to measure, process and control real-world signals."),
    "ADP": ("Business Services", "Recurring payroll and human-capital software services", "Processes payroll and provides cloud tools for human resources, benefits, tax compliance and workforce administration."),
    "ADSK": ("Software", "Subscription design and engineering software", "Sells design, engineering, construction and media software used to create and manage digital 3D models and workflows."),
    "AEP": ("Utilities", "Regulated electricity generation and distribution", "Owns regulated electric generation, transmission and distribution infrastructure serving customers across several US states."),
    "AMAT": ("Semiconductors", "Chip-fabrication equipment", "Builds deposition, etch, inspection and other equipment used by semiconductor manufacturers to produce advanced chips and displays."),
    "AMD": ("Semiconductors", "Fabless CPUs, GPUs and data-center accelerators", "Designs processors and accelerators for PCs, servers, gaming consoles and embedded systems, while manufacturing is outsourced."),
    "AMGN": ("Biotechnology", "Patent-protected biologic medicines", "Discovers, develops and sells biologic therapies for serious illnesses, with revenue driven by product portfolios and patents."),
    "AMZN": ("Consumer & Cloud Technology", "Marketplace, logistics and cloud infrastructure", "Combines an online marketplace and fulfillment network with advertising, subscriptions and the AWS cloud platform."),
    "ARM": ("Semiconductors", "Processor architecture licensing", "Licenses energy-efficient CPU architectures and related designs to chipmakers, earning upfront fees and royalties."),
    "ASML": ("Semiconductor Equipment", "Lithography systems for advanced chips", "Builds highly specialized lithography machines that semiconductor manufacturers use to print ever-smaller circuit patterns."),
    "AVGO": ("Semiconductors", "Diversified connectivity chips and infrastructure software", "Designs chips for networking, broadband, wireless and storage markets and sells infrastructure software after major acquisitions."),
    "AXON": ("Public Safety Technology", "Connected hardware and subscription evidence platform", "Sells body cameras, conducted-energy devices and cloud software that help public-safety agencies manage evidence and operations."),
    "AZN": ("Pharmaceuticals", "Research-based prescription medicines", "Develops and commercializes prescription medicines across oncology, cardiovascular, respiratory and immunology markets."),
    "BIIB": ("Biotechnology", "Specialty medicines for neurological disease", "Develops and sells therapies primarily for neurological and neurodegenerative conditions."),
    "BKNG": ("Travel Platform", "Commission-based global travel marketplace", "Operates online travel brands for accommodation, flights, car rental and restaurants and earns commissions from bookings."),
    "BKR": ("Energy Technology", "Equipment and services for oil and gas production", "Supplies drilling, completion, production and digital services to energy producers across the upstream value chain."),
    "CCEP": ("Consumer Staples", "Bottling and distribution of beverages", "Manufactures, distributes and markets branded non-alcoholic beverages across Europe, Australia and other markets."),
    "CDNS": ("Software", "Electronic-design automation subscriptions", "Provides software, hardware emulation and IP that semiconductor and systems companies use to design and verify electronics."),
    "CDW": ("IT Services", "Business technology procurement and integration", "Resells hardware, software and services and helps organizations design, deploy and manage their technology environments."),
    "CEG": ("Utilities", "Carbon-free power generation", "Owns and operates nuclear and renewable power assets and sells electricity and clean-energy products."),
    "CHTR": ("Telecommunications", "Cable broadband and pay-TV subscriptions", "Operates cable networks that provide broadband, video, voice and mobile services to households and businesses."),
    "CMCSA": ("Media & Telecommunications", "Broadband, media and theme-park conglomerate", "Combines broadband and wireless connectivity with NBCUniversal media, streaming, film, television and theme parks."),
    "COST": ("Consumer Staples", "Membership warehouse retail", "Charges recurring membership fees and sells a curated range of merchandise at low margins and high volumes."),
    "CPRT": ("Business Services", "Online vehicle salvage auction marketplace", "Operates auctions that connect insurers and vehicle sellers with dismantlers, dealers, exporters and repair buyers."),
    "CRWD": ("Cybersecurity", "Cloud-native endpoint and security platform", "Uses a cloud platform and threat intelligence to protect endpoints, identities, workloads and data for organizations."),
    "CSCO": ("Networking Technology", "Enterprise networking hardware and software", "Sells networking, security, collaboration and observability products, increasingly with recurring software and services revenue."),
    "CSGP": ("Real Estate Data", "Subscription property data and marketplace", "Provides commercial real-estate listings, analytics, software and marketing services to industry participants."),
    "CSX": ("Transportation", "Rail freight infrastructure", "Operates a rail network transporting coal, intermodal containers, chemicals, agricultural products and industrial goods."),
    "CTAS": ("Business Services", "Recurring workplace uniform and facility services", "Rents and services uniforms, mats, restroom supplies, first-aid products and other workplace essentials."),
    "CTSH": ("IT Services", "Outsourced digital and business-process services", "Helps enterprises modernize technology and operations through consulting, systems integration and managed services."),
    "DASH": ("Delivery Platform", "Commission-based local commerce marketplace", "Connects consumers with restaurants and retailers through an ordering and delivery network and earns commissions and fees."),
    "DDOG": ("Software", "Cloud monitoring and observability subscriptions", "Provides developers and operations teams with monitoring, security and analytics for cloud applications and infrastructure."),
    "DXCM": ("Medical Devices", "Recurring continuous glucose monitoring", "Develops wearable glucose sensors and software that help people with diabetes monitor and manage their condition."),
    "EXC": ("Utilities", "Regulated electric and gas utility", "Operates regulated electric and gas generation, transmission and distribution networks in the United States."),
    "FANG": ("Energy", "Permian Basin oil and gas producer", "Explores, develops and produces oil and natural gas, primarily from unconventional acreage in the Permian Basin."),
    "FAST": ("Industrial Distribution", "Branch-based industrial supply distribution", "Distributes fasteners and industrial supplies through a network of stores, sales teams and vending solutions."),
    "FER": ("Construction Materials", "Building products and infrastructure materials", "Produces and distributes materials used in construction and infrastructure projects, with a focus on aggregates and related products."),
    "FTNT": ("Cybersecurity", "Integrated network security appliances and subscriptions", "Sells firewalls, secure networking and cloud security products supported by subscriptions and threat intelligence."),
    "GEHC": ("Medical Technology", "Imaging and healthcare equipment", "Develops medical imaging, ultrasound, patient monitoring and pharmaceutical diagnostic technologies for healthcare providers."),
    "GFS": ("Semiconductors", "Specialty semiconductor foundry", "Manufactures chips for automotive, communications, industrial and consumer applications under contract for fabless customers."),
    "GILD": ("Biotechnology", "Antiviral and specialty medicines", "Develops and sells medicines, especially antiviral treatments, for infectious disease, oncology and inflammation."),
    "GOOG": ("Internet Platforms", "Advertising-funded internet ecosystem", "Generates most revenue from digital advertising across Search, YouTube and partner sites, with cloud and subscription businesses as additional engines."),
    "GOOGL": ("Internet Platforms", "Advertising-funded internet ecosystem", "Generates most revenue from digital advertising across Search, YouTube and partner sites, with cloud and subscription businesses as additional engines."),
    "HON": ("Industrial Technology", "Diversified automation and aerospace equipment", "Sells control systems, sensors, aerospace components, safety products and building technologies to industrial and commercial customers."),
    "IDXX": ("Medical Technology", "Veterinary diagnostics and software subscriptions", "Sells diagnostic instruments, consumables, laboratory services and practice-management software to veterinary clinics."),
    "ILMN": ("Life Sciences", "Genomic sequencing instruments and consumables", "Develops sequencing platforms and recurring consumables used by research, pharmaceutical and clinical laboratories."),
    "INTC": ("Semiconductors", "Integrated chip design and manufacturing", "Designs and manufactures processors and other semiconductors and is building foundry capacity for external customers."),
    "INTU": ("Financial Software", "Subscription accounting and personal-finance software", "Provides software for tax filing, accounting, payroll, personal finance and small-business payments."),
    "ISRG": ("Medical Devices", "Robotic surgery systems and recurring instruments", "Sells robotic surgical systems and earns recurring revenue from instruments, accessories, service and training."),
    "KDP": ("Consumer Staples", "Beverage manufacturing and distribution", "Owns beverage brands and produces, distributes and markets coffee, soft drinks, water and other packaged beverages."),
    "KHC": ("Consumer Staples", "Branded packaged food", "Sells branded sauces, cheese, meals, meats and other packaged foods through grocery and food-service channels."),
    "KLAC": ("Semiconductor Equipment", "Process-control and inspection equipment", "Provides inspection, metrology and data systems that semiconductor manufacturers use to improve yield and quality."),
    "LIN": ("Industrial Gases", "Industrial and medical gas supply", "Produces and distributes industrial, medical and specialty gases through onsite plants, pipelines and delivered supply."),
    "LRCX": ("Semiconductor Equipment", "Wafer fabrication equipment", "Supplies etch, deposition, cleaning and related equipment used to manufacture semiconductor memory and logic chips."),
    "LULU": ("Consumer Discretionary", "Premium athletic apparel direct-to-consumer brand", "Designs and sells premium athletic apparel and accessories through stores, e-commerce and selected wholesale partners."),
    "MAR": ("Travel & Hospitality", "Franchised hotel network", "Franchises and manages a global portfolio of hotel brands, earning fees while asset ownership is largely with franchisees."),
    "MCHP": ("Semiconductors", "Embedded-control microcontrollers and analog chips", "Designs microcontrollers, connectivity, analog and timing products embedded in automotive, industrial and consumer equipment."),
    "MDB": ("Software", "Cloud database developer platform", "Provides a document database and developer tools through a subscription cloud service and self-managed deployments."),
    "MDLZ": ("Consumer Staples", "Global snack brands", "Manufactures and markets chocolate, biscuits, baked snacks and other branded packaged foods worldwide."),
    "MELI": ("Internet Platforms", "Latin American commerce and fintech ecosystem", "Operates an online marketplace, payments network, logistics service and credit products across Latin America."),
    "META": ("Internet Platforms", "Advertising-funded social and messaging networks", "Operates social, messaging and virtual-reality products and monetizes primarily through targeted advertising."),
    "MNST": ("Consumer Staples", "Branded energy drinks", "Develops and markets energy drinks and related beverages through a global distributor and retail network."),
    "MPWR": ("Semiconductors", "Power-management chip design", "Develops high-performance power-management solutions used in computing, automotive, communications and industrial systems."),
    "MRVL": ("Semiconductors", "Data-infrastructure chip design", "Builds custom and standard chips for cloud, networking, storage, carrier and automotive infrastructure."),
    "MSFT": ("Software & Cloud", "Enterprise software, cloud and productivity subscriptions", "Combines Windows and devices with Office subscriptions, Azure cloud infrastructure, business software, gaming and advertising."),
    "MSTR": ("Enterprise Software", "Bitcoin treasury and software strategy", "Provides enterprise analytics software while using capital markets and corporate treasury to hold a large bitcoin position."),
    "MU": ("Semiconductors", "Memory chip manufacturing", "Manufactures DRAM, NAND and other memory products whose demand follows computing, data-center and mobile cycles."),
    "NFLX": ("Media", "Subscription video streaming", "Produces and licenses films and series and distributes them globally through recurring streaming memberships."),
    "NTES": ("Interactive Entertainment", "Online games and digital content", "Develops and operates online games and related digital services, primarily for users in China and international markets."),
    "NVDA": ("Semiconductors", "Accelerated computing platforms", "Designs GPUs, networking and software platforms that power AI, data centers, gaming, professional visualization and automotive systems."),
    "NXPI": ("Semiconductors", "Automotive and industrial connectivity chips", "Supplies secure connectivity, processors, analog and power semiconductors for automotive, industrial and communication applications."),
    "ODFL": ("Transportation", "Less-than-truckload freight network", "Moves smaller freight shipments through a regional trucking network and earns revenue per shipment and service."),
    "ON": ("Semiconductors", "Power and sensing chips", "Designs power semiconductors and sensors for automotive electrification, industrial automation and energy infrastructure."),
    "ORLY": ("Consumer Discretionary", "Automotive aftermarket parts retail", "Sells replacement parts, tools and accessories to do-it-yourself customers and professional repair shops."),
    "PANW": ("Cybersecurity", "Platform-based enterprise security subscriptions", "Provides network, cloud and security-operations products increasingly bundled into recurring platform subscriptions."),
    "PAYX": ("Business Services", "Payroll and human-capital subscriptions", "Provides payroll processing, HR administration, benefits and compliance services to small and medium-sized businesses."),
    "PCAR": ("Industrial Manufacturing", "Heavy truck manufacturing and finance", "Designs and manufactures heavy trucks and earns additional revenue from parts, financing and leasing."),
    "PDD": ("Internet Platforms", "Value-focused e-commerce marketplaces", "Operates online marketplaces that connect consumers and merchants, with a focus on value discovery and agricultural commerce."),
    "PEP": ("Consumer Staples", "Global beverages and convenient foods", "Sells beverages and convenient food brands through company and franchise bottling, retail and food-service channels."),
    "PLTR": ("Software", "Data integration and decision software", "Provides data platforms that integrate complex information and support analytics, operations and AI for governments and enterprises."),
    "PYPL": ("Financial Technology", "Digital payments network", "Operates branded and unbranded digital wallets and payment services, earning transaction fees from consumers and merchants."),
    "QCOM": ("Semiconductors", "Wireless chipsets and patent licensing", "Sells wireless and edge-computing chips while licensing essential mobile communications intellectual property."),
    "REGN": ("Biotechnology", "Innovative biologic medicines", "Discovers and commercializes biologic therapies for eye disease, inflammation, cancer and other serious conditions."),
    "ROP": ("Industrial Technology", "Decentralized niche software and equipment", "Owns specialized software and engineered-product businesses with recurring revenue and strong positions in focused markets."),
    "ROST": ("Consumer Discretionary", "Off-price apparel and home retail", "Buys branded merchandise opportunistically and sells it through discount stores and e-commerce at attractive prices."),
    "SBUX": ("Consumer Discretionary", "Global coffeehouse retail", "Operates and licenses coffee shops that sell beverages, food and packaged products through stores and consumer channels."),
    "SHOP": ("Software", "Merchant commerce platform subscriptions", "Provides storefront, payments, marketing, fulfillment and financial tools to merchants through subscriptions and transaction fees."),
    "SNPS": ("Software", "Electronic-design automation and semiconductor IP", "Sells design, verification, testing and intellectual-property tools used to develop complex chips and systems."),
    "TEAM": ("Software", "Collaboration and workflow subscriptions", "Provides cloud tools for software development, project management, service management and team collaboration."),
    "TMO": ("Life Sciences", "Laboratory instruments and services", "Supplies analytical instruments, consumables, diagnostics and contract services to research, clinical and industrial laboratories."),
    "TMUS": ("Telecommunications", "Wireless connectivity subscriptions", "Operates a mobile network and sells voice, data, broadband and related services to consumers and businesses."),
    "TSLA": ("Automotive & Energy", "Electric vehicles and energy systems", "Designs electric vehicles, batteries, charging products and solar-energy systems, with software and services as additional revenue streams."),
    "TTD": ("Advertising Technology", "Independent programmatic advertising platform", "Provides software that lets advertisers plan, buy and measure digital advertising across channels and publishers."),
    "TTWO": ("Interactive Entertainment", "Premium video-game publishing", "Develops, publishes and monetizes console, PC and mobile games through full-price sales, downloadable content and virtual goods."),
    "TXN": ("Semiconductors", "Analog and embedded processing chips", "Designs analog and embedded chips used to sense, process, power and control equipment across industrial and automotive markets."),
    "VRSK": ("Data & Analytics", "Subscription risk and decision analytics", "Provides proprietary data, analytics and workflow software to insurers and other risk-focused businesses."),
    "VRTX": ("Biotechnology", "Specialty medicines for serious disease", "Develops and sells medicines, particularly for cystic fibrosis, while expanding into other serious diseases."),
    "WBD": ("Media", "Film, television and streaming content", "Owns entertainment networks, studios and streaming services and monetizes content through advertising, licensing and subscriptions."),
    "WDAY": ("Software", "Cloud human-capital and finance software", "Provides subscription enterprise software for human resources, payroll, finance and planning."),
    "XEL": ("Utilities", "Regulated electric and gas utility", "Generates, transmits and distributes electricity and natural gas through regulated utility operations in the central United States."),
    "ZS": ("Cybersecurity", "Cloud-delivered secure access platform", "Protects users, applications and data through cloud-based secure access, internet security and zero-trust services."),
}


def enrich_company_profiles(companies: pd.DataFrame) -> pd.DataFrame:
    enriched = companies.copy()
    profiles = enriched["ticker"].map(COMPANY_PROFILES)
    enriched["sector"] = profiles.map(lambda profile: profile[0] if profile else "Diversified Technology")
    enriched["business_model"] = profiles.map(lambda profile: profile[1] if profile else "Diversified products and services for business and consumer markets")
    enriched["business_description"] = profiles.map(lambda profile: profile[2] if profile else "Provides technology-enabled products and services to business and consumer customers.")
    enriched["industry"] = enriched["sector"]
    return enriched


def universe() -> pd.DataFrame:
    cache_path = CACHE_DIR / "nasdaq100.json"
    if cache_path.exists() and time() - cache_path.stat().st_mtime < UNIVERSE_CACHE_TTL:
        return enrich_company_profiles(pd.DataFrame(json.loads(cache_path.read_text(encoding="utf-8"))))
    try:
        response = requests.get(
            "https://api.nasdaq.com/api/quote/list-type/nasdaq100",
            headers={**SEC_HEADERS, "Accept": "application/json"},
            timeout=15,
        )
        response.raise_for_status()
        constituents = pd.DataFrame(response.json()["data"]["rows"])
        tickers = constituents["symbol"].astype(str).str.replace(".", "-", regex=False)
    except requests.RequestException:
        constituents = pd.DataFrame({"symbol": NDX_FALLBACK_TICKERS, "companyName": NDX_FALLBACK_TICKERS})
        tickers = constituents["symbol"]
    sec_tickers = requests.get("https://www.sec.gov/files/company_tickers.json", headers=SEC_HEADERS, timeout=30).json()
    sec_map = pd.DataFrame.from_dict(sec_tickers, orient="index")
    sec_map["ticker"] = sec_map["ticker"].str.upper()
    result = constituents.assign(ticker=tickers).merge(sec_map[["ticker", "cik_str", "title"]], on="ticker", how="inner")
    result = result.rename(columns={"cik_str": "cik", "title": "company_name"})[
        ["ticker", "company_name", "cik"]
    ]
    result = enrich_company_profiles(result)
    CACHE_DIR.mkdir(exist_ok=True)
    cache_path.write_text(result.to_json(orient="records"), encoding="utf-8")
    return result


def live_prices(tickers: list[str], period: str = "2y") -> tuple[pd.DataFrame, pd.Series]:
    import yfinance as yf
    data = yf.download(tickers + ["QQQ"], period=period, auto_adjust=False, progress=False, group_by="ticker")
    rows = []
    for ticker in tickers:
        frame = data[ticker].dropna()
        rows.extend({"ticker": ticker, "date": index, "adjusted_close": row["Adj Close"], "volume": row["Volume"]} for index, row in frame.iterrows())
    benchmark = data["QQQ"]["Adj Close"].dropna()
    return pd.DataFrame(rows), benchmark


def _annual_values(payload: dict, tags: tuple[str, ...], unit: str = "USD") -> list[tuple[pd.Timestamp, float]]:
    facts = payload.get("facts", {}).get("us-gaap", {})
    for tag in tags:
        units = facts.get(tag, {}).get("units", {})
        values = units.get(unit) or next(iter(units.values()), [])
        annual = [item for item in values if item.get("form") == "10-K" and item.get("fp") == "FY" and item.get("val") is not None]
        if annual:
            by_end = {item["end"]: float(item["val"]) for item in annual}
            return sorted((pd.Timestamp(end), value) for end, value in by_end.items())
    return []


def _latest_value(payload: dict, tags: tuple[str, ...], unit: str) -> float:
    facts = payload.get("facts", {}).get("dei", {}) | payload.get("facts", {}).get("us-gaap", {})
    candidates = []
    for tag in tags:
        units = facts.get(tag, {}).get("units", {})
        values = units.get(unit) or next(iter(units.values()), [])
        candidates.extend(item for item in values if item.get("val") is not None)
    if not candidates:
        return 0
    latest = max(candidates, key=lambda item: (item.get("end", ""), item.get("filed", "")))
    return float(latest["val"])


def sec_fundamentals(companies: pd.DataFrame, prices: pd.DataFrame, cancel_event: Event | None = None) -> pd.DataFrame:
    provider = SecCompanyFactsProvider()
    def build_row(company):
        facts = provider.fetch(str(company.cik))
        revenue = _annual_values(facts, ("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet"))
        operating_income = _annual_values(facts, ("OperatingIncomeLoss",))
        net_income = _annual_values(facts, ("NetIncomeLoss", "ProfitLoss"))
        operating_cash = _annual_values(facts, ("NetCashProvidedByUsedInOperatingActivities",))
        capex = _annual_values(facts, ("PaymentsToAcquirePropertyPlantAndEquipment",))
        assets = _annual_values(facts, ("Assets",))
        share_count = _latest_value(
            facts,
            (
                "EntityCommonStockSharesOutstanding",
                "CommonStockSharesOutstanding",
                "WeightedAverageNumberOfDilutedSharesOutstanding",
            ),
            unit="shares",
        )
        latest_price = prices.loc[prices["ticker"] == company.ticker, "adjusted_close"].iloc[-1]
        revenue_latest = revenue[-1][1] if revenue else 0
        revenue_previous = revenue[-2][1] if len(revenue) > 1 else revenue_latest
        operating = operating_income[-1][1] if operating_income else 0
        cash_flow = operating_cash[-1][1] if operating_cash else 0
        capital_expenditure = abs(capex[-1][1]) if capex else 0
        free_cash_flow = cash_flow - capital_expenditure
        return {
            "ticker": company.ticker, "revenue_growth": revenue_latest / max(revenue_previous, 1) - 1,
            "eps_growth": net_income[-1][1] / max(net_income[-2][1], 1) - 1 if len(net_income) > 1 else 0,
            "fcf_growth": 0, "roic": operating / max(assets[-1][1], 1) if assets else 0,
            "fcf_margin": free_cash_flow / max(revenue_latest, 1), "operating_margin": operating / max(revenue_latest, 1),
            "fcf_yield": free_cash_flow / max(latest_price * share_count, 1),
            "pe_discount": 0, "ev_ebit_discount": 0, "peg_discount": 0,
        }

    rows = []
    for company in companies.itertuples(index=False):
        if cancel_event is not None and cancel_event.is_set():
            from .pipeline import ScanCancelled
            raise ScanCancelled("Scan abgebrochen")
        rows.append(build_row(company))
    return pd.DataFrame(rows)


class SecCompanyFactsProvider:
    """Fetches SEC companyfacts; raw payloads can be persisted before normalization."""

    def __init__(self, user_agent: str | None = None):
        self.user_agent = user_agent or os.getenv("SEC_USER_AGENT", "QualityDipScanner contact@example.com")
        self._request_lock = Lock()
        self._last_request = 0.0

    def fetch(self, cik: str) -> dict:
        cache_path = CACHE_DIR / "sec" / f"{int(cik):010d}.json"
        if cache_path.exists() and time() - cache_path.stat().st_mtime < SEC_CACHE_TTL:
            return json.loads(cache_path.read_text(encoding="utf-8"))
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{int(cik):010d}.json"
        for attempt in range(3):
            with self._request_lock:
                wait = 0.6 - (monotonic() - self._last_request)
                if wait > 0:
                    sleep(wait)
                response = requests.get(url, headers={"User-Agent": self.user_agent}, timeout=30)
                self._last_request = monotonic()
            if response.status_code != 429:
                response.raise_for_status()
                payload = response.json()
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(json.dumps(payload), encoding="utf-8")
                return payload
            sleep(5 * (attempt + 1))
        return {}
