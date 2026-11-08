# -*- coding: utf-8 -*-
"""
Curated canonical tables for mauritania-geo.

Sources used to build and verify these tables:
  * OCHA COD-AB "Mauritania - Subnational Administrative Boundaries" (Jan 2026)
    - structure, P-codes, areas, centroids
  * ISO 3166-2:MR (via ISO OBP, cross-checked on en/fr Wikipedia)
    - ISO codes; ISO numeric parts match OCHA P-code numbering (MR-01..MR-15)
  * Arabic Wikipedia wilaya/moughataa/commune articles (fetched Nov 2026)
    - Arabic names
  * French Wikipedia region/departement articles + citypopulation.de
    - canonical French spellings, verification of the 63 moughataas
  * decrees: décret 90-124 (10/09/1990, Nouakchott district, 9 moughataas);
    Conseil des ministres 25/11/2014 split of Nouakchott into 3 wilayas
    (ISO newsletter 27/11/2015 added MR-13/14/15, deleted MR-NKC);
    2018/2021 decrees creating new moughataas and communes.

`OCHA` spellings are kept as aliases whenever the canonical name differs,
so cross-script search keeps working with either convention.
"""

# ---------------------------------------------------------------------------
# WILAYAS  (code, iso_code, p_code, name_fr, name_ar, capital, capital_ar,
#           aliases_fr)
# Areas / centroids / capital coordinates come from COD-AB at import time.
# ---------------------------------------------------------------------------
WILAYAS = [
    ("01", "MR-01", "MR01", "Hodh Ech Chargui", "الحوض الشرقي", "Néma",
     "النعمة", ["Hodh El Chargui", "Hodh Chargui", "Hodh ech Chargui"]),
    ("02", "MR-02", "MR02", "Hodh El Gharbi", "الحوض الغربي", "Aïoun El Atrouss",
     "عيون العتروس", ["Hodh el Gharbi"]),
    ("03", "MR-03", "MR03", "Assaba", "العصابة", "Kiffa", "كيفة", []),
    ("04", "MR-04", "MR04", "Gorgol", "كوركول", "Kaédi", "كيهيدي", []),
    ("05", "MR-05", "MR05", "Brakna", "البراكنة", "Aleg", "ألاك", []),
    ("06", "MR-06", "MR06", "Trarza", "الترارزة", "Rosso", "روصو", []),
    ("07", "MR-07", "MR07", "Adrar", "أدرار", "Atar", "أطار", ["آدرار"]),
    ("08", "MR-08", "MR08", "Dakhlet Nouadhibou", "داخلة نواذيبو", "Nouadhibou",
     "نواذيبو", ["Dakhlet Nouâdhibou", "Dakhlet Nouadhibou"]),
    ("09", "MR-09", "MR09", "Tagant", "تكانت", "Tidjikja", "تجكجة", []),
    ("10", "MR-10", "MR10", "Guidimakha", "كيدي ماغا", "Sélibaby",
     "سيليبابي", ["Guidimaka", "Guidimagha", "كيديماكا"]),
    ("11", "MR-11", "MR11", "Tiris Zemmour", "تيرس زمور", "Zouérat", "الزويرات", []),
    ("12", "MR-12", "MR12", "Inchiri", "إينشيري", "Akjoujt", "أكجوجت", ["إنشيري"]),
    ("13", "MR-13", "MR13", "Nouakchott-Ouest", "نواكشوط الغربية", "Nouakchott",
     "نواكشوط", ["Nouakchott Ouest"]),
    ("14", "MR-14", "MR14", "Nouakchott-Nord", "نواكشوط الشمالية", "Nouakchott",
     "نواكشوط", ["Nouakchott Nord"]),
    ("15", "MR-15", "MR15", "Nouakchott-Sud", "نواكشوط الجنوبية", "Nouakchott",
     "نواكشوط", ["Nouakchott Sud"]),
]

# Pre-2014 unified Nouakchott district (era 13).
# Origin: décret n° 90-124 du 10 septembre 1990 ; split on 25/11/2014.
NKC_HISTORICAL = {
    "code": "13",
    "iso_code": "MR-NKC",
    "p_code": "MR13",
    "name_fr": "Nouakchott",
    "name_ar": "نواكشوط",
    "capital": "Nouakchott",
}

# Wilaya-number (as int) -> list of new moughataas created after the classic
# 44-department layout, with the year of creation (2018/2021 reforms).
NEW_MOUGHATAAS = {
    1: [("Adel Bagrou", 2021), ("N'Beiket Lehwach", 2021)],
    2: [("Touil", 2021)],
    3: [("Kankossa", 2018)],
    4: [("Lexeiba 1", 2021)],
    5: [("Mal", 2021)],
    6: [("Tékane", 2021)],
    8: [("Chami", 2012)],
    10: [("Ghabou", 2018), ("Wompou", 2021)],
    12: [("Bennechab", 2021)],
}

# ---------------------------------------------------------------------------
# MOUGHATAAS: (wilaya_code, p_code_suffix, name_fr, name_ar, aliases_fr)
# p_code = wilaya p_code + suffix (e.g. "MR01" + "1"); the 4-digit library
# code is "<wilaya_code><suffix 0-padded to 2>" -> "0101" .. "1512".
# ---------------------------------------------------------------------------
MOUGHATAAS = [
    # Hodh Ech Chargui
    ("01", 1, "Amourj", "آمرج", ["Amourj"]),
    ("01", 2, "Bassikounou", "باسكنو", ["Bassiknou", "Basseknou"]),
    ("01", 3, "Djiguenni", "جكني", []),
    ("01", 4, "Néma", "النعمة", ["Nema"]),
    ("01", 5, "Oualata", "ولاتة", ["Walata"]),
    ("01", 6, "Timbedra", "تمبدغة", ["Timbédra", "Tembedgha", "Timbedgha"]),
    ("01", 7, "N'Beiket Lehwach", "انبيكت لحواش", ["Nbeiket Lahouach", "N'Beiket Lehwach"]),
    ("01", 8, "Adel Bagrou", "عدل بكرو", ["Edel Bagrou"]),
    # Hodh El Gharbi
    ("02", 1, "Aïoun", "العيون", ["Aioun", "Aïoun El Atrouss"]),
    ("02", 2, "Kobeni", "كوبني", ["Koubeni", "Kobenni"]),
    ("02", 3, "Tamchekett", "تامشكط", ["Tamcheket"]),
    ("02", 4, "Tintane", "الطينطان", ["Tintan"]),
    ("02", 5, "Touil", None, []),
    # Assaba
    ("03", 1, "Barkewol", "باركيول", ["Barkéol", "Barkeol"]),
    ("03", 2, "Boumdeid", "بومديد", ["Boumdeid"]),
    ("03", 3, "Guerou", "كرو", ["Guérou"]),
    ("03", 4, "Kankossa", "كنكوصة", ["Kankoussa"]),
    ("03", 5, "Kiffa", "كيفة", []),
    # Gorgol
    ("04", 1, "Kaédi", "كيهيدي", ["Kaedi"]),
    ("04", 2, "Maghama", "مقامة", []),
    ("04", 3, "M'Bout", "امبود", ["M'Boud", "Mbout"]),
    ("04", 4, "Monguel", "مونكل", ["Mounguel"]),
    ("04", 5, "Lexeiba 1", "لكصيبة", ["Lexeibe 1", "Lexeiba", "Lexeibe"]),
    # Brakna
    ("05", 1, "Aleg", "ألاك", []),
    ("05", 2, "Bababé", "بابابي", ["Bababe"]),
    ("05", 3, "Boghé", "بوغي", ["Boghe", "Boké"]),
    ("05", 4, "Magta-Lahjar", "مقطع لحجار", ["Magtalahjar", "Moughataa Magta-Lahjar"]),
    ("05", 5, "M'Bagne", "أمباني", ["Mbagne"]),
    ("05", 6, "Mal", "مال", ["Maal", "Male"]),
    # Trarza
    ("06", 1, "Boutilimit", "بوتلميت", []),
    ("06", 2, "Keur Macène", "كرمسين", ["Keur Macen", "Keurmassene", "Keur Massene", "Keur-Macene"]),
    ("06", 3, "Mederdra", "المذرذرة", ["Mederdrea"]),
    ("06", 4, "Ouad Naga", "واد الناقة", ["Wad Naga"]),
    ("06", 5, "R'Kiz", "الركيز", ["RKiz"]),
    ("06", 6, "Rosso", "روصو", []),
    ("06", 7, "Tékane", "تيكان", ["Tekane", "Tekani"]),
    # Adrar
    ("07", 1, "Aoujeft", "أوجفت", []),
    ("07", 2, "Atar", "أطار", []),
    ("07", 3, "Chinguetti", "شنقيط", ["Chinguitti", "Shinqit"]),
    ("07", 4, "Ouadane", "وادان", ["Wadan"]),
    # Dakhlet Nouadhibou
    ("08", 1, "Nouadhibou", "نواذيبو", ["Nouadhibou"]),
    ("08", 2, "Chami", "الشامي", []),
    # Tagant
    ("09", 1, "Tidjikja", "تجكجة", ["Tidjikdja"]),
    ("09", 2, "Tichitt", "تيشيت", ["Tichit"]),
    ("09", 3, "Moudjeria", "المجرية", ["Moudjeria"]),
    # Guidimakha
    ("10", 1, "Sélibaby", "سيليبابي", ["Selibaby", "Sélibabi"]),
    ("10", 2, "Ould Yengé", "ولد ينج", ["Ould Yenge"]),
    ("10", 3, "Ghabou", "غابو", []),
    ("10", 4, "Wompou", "وامبو", ["Wompou"]),
    # Tiris Zemmour
    ("11", 1, "Bir Moghreïn", "بير أم اكرين", ["Bir Moghrein", "Bir Moughrein", "Birmoguren"]),
    ("11", 2, "F'Derick", "افديرك", ["F'Dérik", "F'Derick", "Fderick"]),
    ("11", 3, "Zouerate", "الزويرات", ["Zouérat", "Zoueirat", "Zoueratt"]),
    # Inchiri
    ("12", 1, "Akjoujt", "أكجوجت", ["Akjoujt"]),
    ("12", 2, "Bennechab", "بنشاب", []),
    # Nouakchott-Ouest
    ("13", 1, "Ksar", "لكصر", ["Kiyar", "القصر"]),
    ("13", 2, "Tevragh Zeina", "تفرغ زينة", ["Tevragh Zeïna", "Tefragh Zeina"]),
    ("13", 3, "Sebkha", "السبخة", []),
    # Nouakchott-Nord
    ("14", 1, "Toujounine", "توجنين", ["Toujounine"]),
    ("14", 2, "Dar Naim", "دار النعيم", ["Dar Naïm"]),
    ("14", 3, "Teyarett", "تيارت", ["Teyaret", "Teyarett"]),
    # Nouakchott-Sud
    ("15", 1, "El Mina", "الميناء", ["Elmina"]),
    ("15", 2, "Arafat", "عرفات", []),
    ("15", 3, "Riad", "الرياض", ["Riyadh"]),
]

# ---------------------------------------------------------------------------
# COMMUNES
# Rename map: OCHA COD-AB name -> canonical French name (transliteration
# verified on fr.wikipedia / citypopulation.de / ar.wikipedia).
# ---------------------------------------------------------------------------
COMMUNE_RENAMES = {
    # Hodh Ech Chargui
    "Basseknou": "Bassikounou",
    "Vessale": "Fassale",
    "Achemime": "Achemine",
    "Jreif": "Jerif",
    "Beribavat": "Beribavar",
    "Tembedgha": "Timbedra",
    "Bousteile": "Bousteille",
    "Kasr El Barke": "Ksar El Barka",
    "Nbeikett Lehwache": "N'Beiket Lehwach",
    # Hodh El Gharbi
    "Leghlig": "Ghlig Ehl Beye",
    "Gougui Zemmal": "Gougui Ehl Zemal",
    "Voullaniya": "Voulaniya",
    "Oum Lahyadh": "Oum Lahyad",
    "Tintan": "Tintane",
    "Aïn Varbe": "Aïn Farba",
    # Assaba
    "Barkeiwel": "Barkewol",
    "Gueller": "Guever",
    "Lebheir": "Lebhir",
    "R'Dheidhie": "R'Dheidhi",
    "Lavtah": "Laftah",
    "Hseiy Tin": "Hsey Tin",
    "El Ghaira": "El Ghayra",
    "Oudeiy Jrid": "Oudey Jrid",
    "Aghorat": "Aghoratt",
    "Nouamlein": "Nouamline",
    "Bou Lahrath": "Boulahrath",
    "Kankoussa": "Kankossa",
    # Gorgol
    "Bokhol": "Bakhel",
    "Toghomadi": "Tokomadji",
    "Tifondé Civé": "Toufoundé Civé",
    "M'Boud": "M'Bout",
    "N'Djadjbenni Gandéga": "Diadjibine Gandéga",
    "Edebaye Ehel Guelaye": "Edbaye Ehl Guelaye",
    "Voum Legleite": "Foum Gleita",
    "Terenguel Ehel Moulaye Ely": "Terguent Ehl Moulaye Ely",
    "Doo": "Daw",
    "Vrea Litame": "Vréa Litama",
    "Lexeiba 1": "Lexeiba 1",
    # Brakna
    "Maal": "Mal",
    "Djelwar": "Djellwar",
    "Aghchourguit": "Aghchorguitt",
    "Chegar": "Cheggar",
    "Djonabe": "Djonaba",
    "Ouad Emmour": "Ouad Emour",
    "Edebaye El Hejjaj": "Edbaye El Hijaj",
    "Dar El Aviye": "Dar El Aviya",
    "Dar El Barke": "Dar El Barka",
    # Trarza
    "Ajoueir": "Ajouir",
    "El Mouyessar": "El Moyesser",
    "Nebaghiye": "Nebaghiya",
    "Tenghadej": "Tenghadi",
    "Keurmacen": "Keur Macène",
    "M'Balal": "M'Balel",
    "N'Diago": "Ndiago",
    "Beir Taouress": "Bei Taouress",
    "Tiguent (El Jedide)": "Tiguent El Jedid",
    "Aouleiygat": "Aouleigatt",
    "Bareine": "Bareina",
    "Jedrel Mouhguen": "Jedr El Moubghuen",
    "Teikane": "Tékane",
    "Lexelbe 2": "Lexeiba 2",
    # Adrar
    "Maeden": "Maaden",
    "N'Teirguent": "N'Terguent",
    "Chinguitti": "Chinguetti",
    # Dakhlet Nouadhibou
    "Tmeimichat": "Tmeimichatt",
    # Tagant
    "N'Beike": "Nbeika",
    "Tichit": "Tichitt",
    "El Wahat": "El Wahatt",
    "Lehsira": "Lehseira",
    "Tidjikdja": "Tidjikja",
    # Guidimakha
    "Bouanz": "Bouanzé",
    "Lehraj": "Lahraj",
    "Hassi Chegar": "Hassi Cheggar",
    "Tachout": "Tachott",
    "Bayediam": "Baydam",
    "Soufi": "Souvi",
    "Ejar": "Ajar",
    # Tiris Zemmour
    "Birmoughrein": "Bir Moghreïn",
    "F'Deirick": "F'Derick",
    "Zoueirat": "Zouerate",
    # Nouakchott
    "Tefragh Zeina": "Tevragh Zeina",
    "Teyaret": "Teyarett",
    "Dar Naïm": "Dar Naim",
    "Riyad": "Riad",
    "Sélibabi": "Sélibaby",
}

# Commune Arabic names gathered from Arabic Wikipedia (wilaya/moughataa
# articles, fetched November 2026).  Keyed by OCHA name (before renaming).
# Missing entries are exported as null — contributions welcome.
COMMUNE_ARABIC = {
    # Amourj
    "Amourj": "آمرج", "Bougadoum": "بوقادوم", "Adel Bagrou": "عدل بكرو",
    # Bassiknou
    "Basseknou": "باسكنو", "Vessale": "فصالة", "El Megve": "المقفة",
    # Djiguenni
    "Djiguenni": "جكني", "El Mabrouk 1": "مبروك", "Beneamane": "بالنعمان",
    "Aoueinat Ez Bel": "عوينات الزبل", "Ghlig Ehel Beye": "اقليك اهل بية",
    "Kasr El Barke": "قصر البركة", "Feirenni": "فيرني",
    # Néma
    "Néma": "النعمة", "Achemime": "أشميم", "Jreif": "الجريف", "Bangou": "بانكو",
    "Hassi Etile": "حاسي أتيلة", "Oum Avnadech": "أم آفنادش",
    "Agoueinit": "أقوينيت", "El Mabrouk 2": "المبروك", "Beribavat": "بايريفار",
    "Noual": "نوال",
    # Oualata / Timbedra / Adel Bagrou
    "Oualata": "ولاتة",
    "Tembedgha": "تمبدغة", "Touil 1": "الطويل", "Koumbi Saleh": "كمبي صالح",
    "Bousteile": "بوسطيلة", "Hassi M'Hadi": "حاس إمهادي",
    "Nbeikett Lehwache": "انبيكت لحواش",
    "Elmessgoul": "المسكول", "Sivane": "صيوان",
    # Aïoun
    "Aïoun El Atrouss": "عيون العتروس", "Doueirare": "دويرارة", "Egjert": "اقجرت",
    "N'Savenni": "انصفني", "Ten Hamadi": "تنحماد",
    # Kobeni
    "Koubenni": "كوبني", "Hassi Ehel Ahmed Bechne": "حاسي اهل أحمد بشنة",
    "Leghlig": "لغليك", "Modibougou": "مدبوكو", "Timzine": "تمزين",
    "Voullaniya": "الفلانية",
    # Tamchekett
    "Tamchekett": "تامشكط", "Radhi": "الرظي", "Sava": "الصفا",
    "Guetae-Teidoume": "قظاي التيدوم", "El Mabrouk 3": "المبروك",
    # Tintane
    "Tintan": "الطينطان", "Aïn Varbe": "عين فربة",
    "Hassi Abdallah": "حاسي عبد الله", "Aweinat Thalle": "عوينات الطل",
    # Barkéol
    "Barkeiwel": "باركيول", "Bou Lahrath": "بولحراث", "Daghveg": "دغفك",
    "El Ghabra": "الغبرة", "Gueller": "كلير", "Lebheir": "لبحير",
    "Laweissi": "العويسي", "R'Dheidhie": "إرظيظيع",
    # Boumdeid / Guerou / Kankoussa / Kiffa
    "Boumdeid": "بومديد", "Hseiy Tin": "احسي الطين", "Lavtah": "لفتاح",
    "Guerou": "كرو", "El Ghaira": "الغايرة", "Kamour": "كامور",
    "Oudeiy Jrid": "ودي الجريد",
    "Kankoussa": "كنكوصة", "Blajmil": "بلاجميل", "Sani": "ساني",
    "Hamed": "هامد", "Tenaha": "تناها",
    "Kiffa": "كيفة", "Aghorat": "آغورط", "El Melgue": "الملك",
    "Kouroudjel": "كروجل", "Legrane": "لكران", "Nouamlein": "انواملين",
    # Gorgol
    "Kaedi": "كيهيدي", "Néré Walo": "نير والو", "Tifondé Civé": "تفوند سيفي",
    "Toghomadi": "توكومادي", "Ganki": "كانكي", "Lexeiba 1": "لكصيبة 1",
    "Maghama": "مقامة", "Beilouguet Litame": "بيلكت ليتامة",
    "Dolol Civé": "دولول سيفي", "Doo": "داوو", "Sagné": "صانيي",
    "Toulel": "تولل", "Wali Djantang": "والي جاتانغ",
    "Chelkhet Tiyab": "اشليخت التياب",
    "Edebaye Ehel Guelaye": "أدباي أهل كلاي",
    "N'Djadjbenni Gandéga": "انجاجبني كانديكا",
    "Terenguel Ehel Moulaye Ely": "تاركنت أهل مولاي اعل",
    "Tikobra": "تيكوبرا", "Voum Legleite": "فم لكليتة",
    "Azgueilem Tiyab": "أزكليم التياب", "Bathet Moït": "بطحت ميت",
    "Bokhol": "بكل", "Melzem Teichet": "ملزم تيشط", "Mounguel": "مونكل",
    # Brakna (article lists no communes; only Maal found)
    "Maal": "مال",
    # Trarza
    "Boutilimit": "بوتلميت", "Ajoueir": "آجوير", "Elb Adress": "علب آدرس",
    "El Mouyessar": "الميسر", "Nebaghiye": "النباغية", "N'Teichet": "انتيشط",
    "Tenghadej": "تنغدج",
    "Keurmacen": "كرمسين", "M'Balal": "امبلل", "N'Diago": "انجاكو",
    "Mederdra": "المذرذرة", "Beir Taouress": "بير التورس", "El Khat": "الخط",
    "Tiguent (El Jedide)": "تكنت الجديدة", "Taguilalet": "التاكيلالت",
    "Ouad Naga": "واد الناقة", "Aouleiygat": "آوليكات", "El Ariye": "العرية",
    "R'Kiz": "الركيز", "Bareine": "برينة", "Boutalhaye": "أبو طلحاية",
    "Rosso": "روصو", "Jedrel Mouhguen": "جدر المحقن",
    "Teikane": "تيكان", "Lexelbe 2": "القصيبة",
    # Adrar
    "Atar": "أطار", "Aïn Ehel Taya": "عين أهل الطايع", "Tawaz": "الطواز",
    "Choum": "شوم",
    "Aoujeft": "أوجفت", "Maeden": "معدن العرفان",
    "N'Teirguent": "انتيركنت", "El Medah": "المداح",
    "Chinguitti": "شنقيط", "Aïn Savra": "عين الصفرة", "Ouadane": "وادان",
    # Dakhlet Nouadhibou
    "Nouadhibou": "نواذيبو", "Inal": "إنال",
    "Chami": "الشامي", "Tmeimichat": "التميميشات", "Nouamghar": "نوامغار",
    # Tagant
    "Tidjikdja": "تجكجة", "El Wahat": "الواحات", "Tensigh": "تنسيغ",
    "Boubacar Ben Amer": "بوبكر بن عامر", "Lehsira": "لحصيرة",
    "Moudjeria": "المجرية", "N'Beike": "النبيكة", "Soudoud": "السدود",
    "Tichit": "تيشيت", "Lekhcheb": "لخشب",
    # Guidimakha
    "Sélibabi": "سيليبابي",
    "Ould Yengé": "ولد ينج", "Tektake": "التكتاكه", "Davoue": "دافور",
    "Bouanz": "بوعنز", "Lehraj": "لحرج", "Leaweinat": "لعوينات",
    "Leebelli": "لعبلي",
    "Hassi Chegar": "حاسي شكار", "Ould M'Bonny": "ولد بوني",
    "Tachout": "التاشوط",
    "Ghabou": "غابو", "Bayediam": "بايديام", "Soufi": "الصوفي",
    "Wompou": "وامبو", "Arr": "عار", "Ejar": "اجار",
    # Tiris Zemmour / Inchiri
    "Birmoughrein": "بير أم اكرين", "F'Deirick": "افديرك", "Zoueirat": "الزويرات",
    "Akjoujt": "أكجوجت", "Bennechab": "بنشاب",
    # Nouakchott (9 communes)
    "Ksar": "لكصر", "Tevragh Zeina": "تفرغ زينة", "Sebkha": "السبخة",
    "Toujounine": "توجنين", "Dar Naïm": "دار النعيم", "Teyarett": "تيارت",
    "El Mina": "الميناء", "Arafat": "عرفات", "Riad": "الرياض",
}

# Aliases (extra FR spellings accepted by search), keyed by OCHA name.
COMMUNE_ALIASES = {
    "Vessale": ["Fassala"],
    "Tembedgha": ["Timbedra"],
    "Basseknou": ["Bassiknou"],
    "Lexeiba 1": ["Lexeibe"],
    "Lexelbe 2": ["Lexeiba 2"],
    "Voum Legleite": ["Foum Gleita"],
    "Davoue": ["Dafort"],
    "Maal": ["Mal"],
    "N'Diago": ["Ndiago"],
}

# OCHA places two communes in the wrong moughataa (verified against
# fr.wikipedia "Nouakchott" + en.wikipedia "Departments of Mauritania"):
# commune "Toujounine" belongs to moughataa Teyarett and vice versa.
NKC_COMMUNE_SWAP = True

# Historical note for era views (JSON, embedded into data/meta.json).
HISTORY = {
    "1990": {
        "instrument": "décret n° 90-124 du 10 septembre 1990",
        "effect": "Nouakchott district organized into 9 moughataas",
    },
    "2014": {
        "instrument": "décret du 25 novembre 2014 (Conseil des ministres)",
        "effect": "Nouakchott district split into 3 wilayas: Nord, Ouest, Sud "
                  "(ISO 3166-2 newsletter 2015-11-27 added MR-13/14/15, deleted MR-NKC)",
    },
    "2018": {
        "instrument": "2018 decrees (moughataa/commune creations)",
        "effect": "new moughataas and communes across several wilayas",
    },
    "2021": {
        "instrument": "décret du 8 septembre 2021 and related decrees",
        "effect": "six new moughataas (Adel Bagrou, N'Beiket Lehwach, Touil, "
                  "Lexeiba 1, Mal, Tékane, Ghabou, Wompou, Bennechab) and new communes",
    },
}
