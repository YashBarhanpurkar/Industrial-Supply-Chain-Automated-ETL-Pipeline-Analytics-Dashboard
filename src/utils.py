import pandas as pd
import sqlite3
import logging

# ─────────────────────────────────────────────────────────────────────────────
# TRANSLATION MAPS
# All 164 Spanish country names → English, plus key cities and states.
# Power BI map visuals require English names to geocode correctly.
# ─────────────────────────────────────────────────────────────────────────────

COUNTRY_TRANSLATION = {
    # A
    "Afganistán": "Afghanistan",
    "Albania": "Albania",
    "Alemania": "Germany",
    "Angola": "Angola",
    "Arabia Saudí": "Saudi Arabia",
    "Argelia": "Algeria",
    "Argentina": "Argentina",
    "Armenia": "Armenia",
    "Australia": "Australia",
    "Austria": "Austria",
    "Azerbaiyán": "Azerbaijan",
    # B
    "Bangladés": "Bangladesh",
    "Barbados": "Barbados",
    "Baréin": "Bahrain",
    "Belice": "Belize",
    "Benín": "Benin",
    "Bielorrusia": "Belarus",
    "Bolivia": "Bolivia",
    "Bosnia y Herzegovina": "Bosnia and Herzegovina",
    "Botsuana": "Botswana",
    "Brasil": "Brazil",
    "Bulgaria": "Bulgaria",
    "Burkina Faso": "Burkina Faso",
    "Burundi": "Burundi",
    "Bután": "Bhutan",
    "Bélgica": "Belgium",
    # C
    "Camboya": "Cambodia",
    "Camerún": "Cameroon",
    "Canada": "Canada",
    "Chad": "Chad",
    "Chile": "Chile",
    "China": "China",
    "Chipre": "Cyprus",
    "Colombia": "Colombia",
    "Corea del Sur": "South Korea",
    "Costa Rica": "Costa Rica",
    "Costa de Marfil": "Ivory Coast",
    "Croacia": "Croatia",
    "Cuba": "Cuba",
    # D
    "Dinamarca": "Denmark",
    # E
    "Ecuador": "Ecuador",
    "Egipto": "Egypt",
    "El Salvador": "El Salvador",
    "Emiratos Árabes Unidos": "United Arab Emirates",
    "Eritrea": "Eritrea",
    "Eslovaquia": "Slovakia",
    "Eslovenia": "Slovenia",
    "España": "Spain",
    "Estados Unidos": "United States",
    "EE. UU.": "United States",
    "Estonia": "Estonia",
    "Etiopía": "Ethiopia",
    # F
    "Filipinas": "Philippines",
    "Finlandia": "Finland",
    "Francia": "France",
    # G
    "Gabón": "Gabon",
    "Georgia": "Georgia",
    "Ghana": "Ghana",
    "Grecia": "Greece",
    "Guadalupe": "Guadeloupe",
    "Guatemala": "Guatemala",
    "Guayana Francesa": "French Guiana",
    "Guinea": "Guinea",
    "Guinea Ecuatorial": "Equatorial Guinea",
    "Guinea-Bissau": "Guinea-Bissau",
    "Guyana": "Guyana",
    # H
    "Haití": "Haiti",
    "Honduras": "Honduras",
    "Hong Kong": "Hong Kong",
    "Hungría": "Hungary",
    # I
    "India": "India",
    "Indonesia": "Indonesia",
    "Irak": "Iraq",
    "Irlanda": "Ireland",
    "Irán": "Iran",
    "Israel": "Israel",
    "Italia": "Italy",
    # J
    "Jamaica": "Jamaica",
    "Japón": "Japan",
    "Jordania": "Jordan",
    # K
    "Kazajistán": "Kazakhstan",
    "Kenia": "Kenya",
    "Kirguistán": "Kyrgyzstan",
    "Kuwait": "Kuwait",
    # L
    "Laos": "Laos",
    "Lesoto": "Lesotho",
    "Liberia": "Liberia",
    "Libia": "Libya",
    "Lituania": "Lithuania",
    "Luxemburgo": "Luxembourg",
    "Líbano": "Lebanon",
    # M
    "Macedonia": "North Macedonia",
    "Madagascar": "Madagascar",
    "Malasia": "Malaysia",
    "Mali": "Mali",
    "Marruecos": "Morocco",
    "Martinica": "Martinique",
    "Mauritania": "Mauritania",
    "Moldavia": "Moldova",
    "Mongolia": "Mongolia",
    "Montenegro": "Montenegro",
    "Mozambique": "Mozambique",
    "Myanmar (Birmania)": "Myanmar",
    "México": "Mexico",
    # N
    "Namibia": "Namibia",
    "Nepal": "Nepal",
    "Nicaragua": "Nicaragua",
    "Nigeria": "Nigeria",
    "Noruega": "Norway",
    "Nueva Zelanda": "New Zealand",
    "Níger": "Niger",
    # O
    "Omán": "Oman",
    # P
    "Pakistán": "Pakistan",
    "Panamá": "Panama",
    "Papúa Nueva Guinea": "Papua New Guinea",
    "Paraguay": "Paraguay",
    "Países Bajos": "Netherlands",
    "Perú": "Peru",
    "Polonia": "Poland",
    "Portugal": "Portugal",
    # Q
    "Qatar": "Qatar",
    # R
    "Reino Unido": "United Kingdom",
    "República Centroafricana": "Central African Republic",
    "República Checa": "Czech Republic",
    "República Democrática del Congo": "Democratic Republic of the Congo",
    "República Dominicana": "Dominican Republic",
    "República de Gambia": "Gambia",
    "República del Congo": "Republic of the Congo",
    "Ruanda": "Rwanda",
    "Rumania": "Romania",
    "Rusia": "Russia",
    # S
    "Senegal": "Senegal",
    "Serbia": "Serbia",
    "Sierra Leona": "Sierra Leone",
    "Singapur": "Singapore",
    "Siria": "Syria",
    "Somalia": "Somalia",
    "Sri Lanka": "Sri Lanka",
    "Suazilandia": "Eswatini",
    "SudAfrica": "South Africa",
    "Sudán": "Sudan",
    "Sudán del Sur": "South Sudan",
    "Suecia": "Sweden",
    "Suiza": "Switzerland",
    "Surinam": "Suriname",
    "Sáhara Occidental": "Western Sahara",
    # T
    "Tailandia": "Thailand",
    "Taiwán": "Taiwan",
    "Tanzania": "Tanzania",
    "Tayikistán": "Tajikistan",
    "Togo": "Togo",
    "Trinidad y Tobago": "Trinidad and Tobago",
    "Turkmenistán": "Turkmenistan",
    "Turquía": "Turkey",
    "Túnez": "Tunisia",
    # U
    "Ucrania": "Ukraine",
    "Uganda": "Uganda",
    "Uruguay": "Uruguay",
    "Uzbekistán": "Uzbekistan",
    # V
    "Venezuela": "Venezuela",
    "Vietnam": "Vietnam",
    # Y
    "Yemen": "Yemen",
    "Yibuti": "Djibouti",
    # Z
    "Zambia": "Zambia",
    "Zimbabue": "Zimbabwe",
    # Puerto Rico (customer country)
    "Puerto Rico": "Puerto Rico",
}

# Key city name translations (Spanish → English).
# Most cities are language-neutral; this covers the explicitly translated ones
# that Power BI would fail to geocode.
CITY_TRANSLATION = {
    "Tokio": "Tokyo",
    "Seúl": "Seoul",
    "Pekín": "Beijing",
    "Shanghái": "Shanghai",
    "Berlín": "Berlin",
    "Dublín": "Dublin",
    "Jerusalén": "Jerusalem",
    "Los Ángeles": "Los Angeles",
    "Montréal": "Montreal",
    "Rangún": "Yangon",
    "Teherán": "Tehran",
    "Túnez": "Tunis",
    "Astracán": "Astrakhan",
}

# Order Region cleanup: strip whitespace + normalise US region names
REGION_MAPPING = {
    "South of  USA": "South US",   # double-space typo
    "South of USA": "South US",
    "West of USA": "West US",
    "West of USA ": "West US",     # trailing space variant
    "East of USA": "East US",
    "East of USA ": "East US",
    "US Center": "Central US",
    "US Center ": "Central US",
}


# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def clean_logistics_data(df, config):
    """Applies all cleaning rules: dates, strings, drops, deduplication,
    anomaly fixes, region normalisation, and full Spanish→English translation."""

    # ── 1. Dates ──────────────────────────────────────────────────────────────
    for col in config['cleaning_rules']['date_cols']:
        df[col] = pd.to_datetime(df[col])

    # ── 2. String cast ────────────────────────────────────────────────────────
    for col in config['cleaning_rules']['str_cols']:
        df[col] = df[col].astype(str)

    # ── 3. Drop dead / duplicate columns ─────────────────────────────────────
    df.drop(columns=config['cleaning_rules']['drop_cols'], inplace=True, errors='ignore')

    # ── 4. Fix rows where Customer State holds a zip code (EDA finding) ──────
    df['Customer Zipcode'] = df['Customer Zipcode'].astype(str)
    for bad_zip in ['95758', '91732']:
        mask = df['Customer State'] == bad_zip
        df.loc[mask, 'Customer Zipcode'] = bad_zip
        df.loc[mask, 'Customer City'] = 'Unknown'
        df.loc[mask, 'Customer State'] = 'CA'

    # ── 5. Fill missing last names ────────────────────────────────────────────
    df['Customer Lname'] = df['Customer Lname'].fillna('Unknown')

    # ── 6. Derived feature ────────────────────────────────────────────────────
    df['Lead_Time_Deviation'] = (
        df['Days for shipping (real)'] - df['Days for shipment (scheduled)']
    )

    # ── 7. Region normalisation (strip + map) ─────────────────────────────────
    df['Order Region'] = df['Order Region'].str.strip().replace(REGION_MAPPING)

    # ── 8. Translate Spanish location names → English ─────────────────────────
    df['Order Country'] = (
        df['Order Country'].map(COUNTRY_TRANSLATION).fillna(df['Order Country'])
    )
    df['Customer Country'] = (
        df['Customer Country'].map(COUNTRY_TRANSLATION).fillna(df['Customer Country'])
    )
    df['Order City'] = (
        df['Order City'].map(CITY_TRANSLATION).fillna(df['Order City'])
    )
    # Order State: keep as-is — states are used as labels in Power BI slicers,
    # not for geocoding. Add a state_translation dict here if needed later.

    return df


def create_dim_geography(df, config):
    """Builds Dim_Geography with a surrogate key from unique location combos."""
    geo_cols = config['cleaning_rules']['geo_cols']
    dim_geo = (
        df[geo_cols]
        .drop_duplicates()
        .fillna("Unknown")
        .reset_index(drop=True)
    )
    dim_geo['Geography_Key'] = dim_geo.index + 1
    return dim_geo


def map_geography_to_facts(df, dim_geo, config):
    """Joins the Geography_Key surrogate back to the main dataframe,
    then drops the raw geo columns (they now live only in Dim_Geography)."""
    geo_cols = config['cleaning_rules']['geo_cols']
    df = df.merge(dim_geo, on=geo_cols, how='left')
    df.drop(columns=geo_cols, inplace=True)
    return df


def validate_data(df):
    """Isolates any remaining anomalous rows into a quarantine dataframe.
    Currently flags records whose Customer City is still 'Unknown' after
    the zip-code fix, which is the only residual anomaly found in EDA."""
    if 'Customer City' in df.columns:
        mask = df['Customer City'] == 'Unknown'
        quarantine_df = df[mask].copy()
        clean_df = df[~mask].copy()
        if not quarantine_df.empty:
            logging.warning(
                f"{len(quarantine_df)} records quarantined (Customer City = 'Unknown'). "
                "These are likely the legacy zip-code-in-state-field anomaly rows."
            )
    else:
        clean_df = df
        quarantine_df = pd.DataFrame()

    return clean_df, quarantine_df


def load_to_sqlite(df_dict, db_name="data/processed/SupplyChainOps.db"):
    """Writes all star-schema tables to SQLite, recreating them on each run."""
    logging.info(f"Connecting to database: {db_name}")
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = OFF;")

    table_schema = {
        "Dim_Product_Category": """
            CREATE TABLE IF NOT EXISTS Dim_Product_Category (
            [Category Id]   INTEGER PRIMARY KEY,
            [Category Name] TEXT
            )""",
        "Dim_Product_Department": """
            CREATE TABLE IF NOT EXISTS Dim_Product_Department (
            [Department Id]   INTEGER PRIMARY KEY,
            [Department Name] TEXT
            )""",
        "Dim_Geography": """
            CREATE TABLE IF NOT EXISTS Dim_Geography (
            Geography_Key   INTEGER PRIMARY KEY,
            Market          TEXT,
            [Order Region]  TEXT,
            [Order Country] TEXT,
            [Order State]   TEXT,
            [Order City]    TEXT,
            [Order Zipcode] TEXT
            )""",
        "Dim_Customer": """
            CREATE TABLE IF NOT EXISTS Dim_Customer (
            [Customer Id]       INTEGER PRIMARY KEY,
            [Customer Segment]  TEXT,
            [Customer Fname]    TEXT,
            [Customer Lname]    TEXT,
            [Customer Zipcode]  TEXT,
            [Customer City]     TEXT,
            [Customer State]    TEXT,
            [Customer Country]  TEXT,
            Latitude            REAL,
            Longitude           REAL
            )""",
        "Dim_Product": """
            CREATE TABLE IF NOT EXISTS Dim_Product (
            [Product Card Id]      INTEGER PRIMARY KEY,
            [Product Category Id]  INTEGER,
            [Department Id]        INTEGER,
            [Product Name]         TEXT,
            [Product Price]        REAL,
            FOREIGN KEY ([Product Category Id]) REFERENCES Dim_Product_Category([Category Id]),
            FOREIGN KEY ([Department Id])       REFERENCES Dim_Product_Department([Department Id])
            )""",
        "Fact_Order_Header": """
            CREATE TABLE IF NOT EXISTS Fact_Order_Header (
            [Order Id]                      INTEGER PRIMARY KEY,
            [Order Customer Id]             INTEGER,
            Geography_Key                   INTEGER,
            [Type]                          TEXT,
            [Order Profit Per Order]        REAL,
            [Shipping Mode]                 TEXT,
            [Days for shipping (real)]      INTEGER,
            [Days for shipment (scheduled)] INTEGER,
            Lead_Time_Deviation             INTEGER,
            [order date (DateOrders)]       TEXT,
            [shipping date (DateOrders)]    TEXT,
            [Delivery Status]               TEXT,
            [Order Status]                  TEXT,
            Late_delivery_risk              INTEGER,
            [Sales per customer]            REAL,
            FOREIGN KEY ([Order Customer Id]) REFERENCES Dim_Customer([Customer Id]),
            FOREIGN KEY (Geography_Key)       REFERENCES Dim_Geography(Geography_Key)
            )""",
        "Fact_Order_LineItem": """
            CREATE TABLE IF NOT EXISTS Fact_Order_LineItem (
            [Order Item Id]            INTEGER PRIMARY KEY,
            [Order Id]                 INTEGER,
            [Order Item Cardprod Id]   INTEGER,
            [Order Item Quantity]      INTEGER,
            [Product Price]            REAL,
            [Order Item Discount Rate] REAL,
            [Order Item Discount]      REAL,
            Sales                      REAL,
            [Order Item Profit Ratio]  REAL,
            FOREIGN KEY ([Order Id])               REFERENCES Fact_Order_Header([Order Id]),
            FOREIGN KEY ([Order Item Cardprod Id]) REFERENCES Dim_Product([Product Card Id])
            )""",
    }

    for table_name, schema in table_schema.items():
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        cursor.execute(schema)

    cursor.execute("PRAGMA foreign_keys = ON;")

    for table_name, dataframe in df_dict.items():
        logging.info(f"Writing {len(dataframe)} rows → {table_name}")
        dataframe.to_sql(table_name, conn, if_exists='append', index=False)

    conn.commit()
    conn.close()
    logging.info("All tables loaded into SQLite star schema.")