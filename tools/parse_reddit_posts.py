"""Parse raw r/collegeresults posts into applicant records and decisions.

SOURCE   Public Reddit posts (r/collegeresults, 2015-2024) as saved in the public GitHub file
         shreybirmiwal/college-predictor, 1-DataPrep/3-extract-values/in-cleaned.csv (columns: Upvotes, Date, Title,
         Body Text, Link).
PRIVACY  Everything written is "self-described in a public Reddit post; not verified". The activities summary and the
         essay topic are the applicant's own short description of what they did or wrote about, cut to a few hundred
         characters. They are NEVER essay text. Usernames, links, e-mails, people's names and high-school names are
         removed; a field that engine.privacy.looks_personal flags is dropped for that record (not kept in part).
         Race and gender lines are skipped at parse time; the words are also scrubbed from the stored free text.
         The record id is a hash of the post text; the Reddit id, the link and the username are never stored.
NOT      wired into the product. The adapter is engine/cases_parsed.py.

Run from the repo root:  python tools/parse_reddit_posts.py  [raw_csv]  [out_dir]
Standard library only (plus the repo's own engine package).
"""
from __future__ import annotations

import csv
import hashlib
import html
import json
import os
import random
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine import colleges as _colleges  # noqa: E402
from engine import privacy as _privacy  # noqa: E402
from engine.cases import major_group_for  # noqa: E402

csv.field_size_limit(10 ** 9)

SOURCE_NOTE = "self-described in a public Reddit post; not verified"
RAW_DEFAULT = (ROOT.parent.parent / "tracks" / "counselor_copilot" / "deep" / "G_essays" / "raw_download"
               / "shreybirmiwal_in-cleaned.csv")
RAW_URL = ("https://raw.githubusercontent.com/shreybirmiwal/college-predictor/main/1-DataPrep/"
           "3-extract-values/in-cleaned.csv")
OUT_DEFAULT = ROOT / "data" / "cases" / "parsed"

APPLICANT_FIELDS = [
    "record_id", "post_year", "application_year", "sat_total", "sat_superscore", "act_composite",
    "gpa_unweighted", "gpa_weighted", "gpa_unlabeled", "gpa_scale", "class_rank_top_pct", "class_rank_raw",
    "ap_ib_count", "major_text", "major_group", "home_state", "school_type", "hook_first_gen", "hook_legacy",
    "hook_recruited_athlete", "hook_low_income", "hooks", "activities_summary", "activities_tags", "essay_topic",
    "essay_themes", "essay_self_rating", "n_decisions", "n_mapped_decisions", "source_note",
]
DECISION_FIELDS = ["record_id", "college_as_written", "college_id", "college_name", "case_name", "outcome",
                   "round", "source_note"]

# ---------------------------------------------------------------- college aliases (kept HERE, not in engine)
# lowercase normalised string -> full Scorecard name (checked at start-up; entries that do not resolve are dropped)
COLLEGE_ALIASES = {
    "wesleyan": "Wesleyan University", "cal poly slo": "California Polytechnic State University-San Luis Obispo",
    "cal poly": "California Polytechnic State University-San Luis Obispo",
    "slo": "California Polytechnic State University-San Luis Obispo",
    "michigan state": "Michigan State University", "msu": "Michigan State University",
    "uf": "University of Florida", "ufl": "University of Florida", "gwu": "George Washington University",
    "gw": "George Washington University", "umass amherst": "University of Massachusetts-Amherst",
    "umass": "University of Massachusetts-Amherst", "rpi": "Rensselaer Polytechnic Institute",
    "wpi": "Worcester Polytechnic Institute", "rit": "Rochester Institute of Technology",
    "nc state": "North Carolina State University at Raleigh", "ncsu": "North Carolina State University at Raleigh",
    "wustl": "Washington University in St Louis", "wash u": "Washington University in St Louis",
    "washu": "Washington University in St Louis", "wake": "Wake Forest University",
    "wake forest": "Wake Forest University", "fsu": "Florida State University", "ucf": "University of Central Florida",
    "usf": "University of South Florida", "uconn": "University of Connecticut", "umn": "University of Minnesota-Twin Cities",
    "umd": "University of Maryland-College Park", "uiuc": "University of Illinois Urbana-Champaign",
    "ucb": "University of California-Berkeley", "uc berkeley": "University of California-Berkeley",
    "berkeley": "University of California-Berkeley", "uc davis": "University of California-Davis",
    "uc irvine": "University of California-Irvine", "uc santa barbara": "University of California-Santa Barbara",
    "uc santa cruz": "University of California-Santa Cruz", "uc riverside": "University of California-Riverside",
    "uc san diego": "University of California-San Diego", "uc merced": "University of California-Merced",
    "ucla": "University of California-Los Angeles", "ucsd": "University of California-San Diego",
    "ucsb": "University of California-Santa Barbara", "ucsc": "University of California-Santa Cruz",
    "uci": "University of California-Irvine", "ucd": "University of California-Davis",
    "ucr": "University of California-Riverside", "ucm": "University of California-Merced",
    "university of california los angeles": "University of California-Los Angeles",
    "university of california san diego": "University of California-San Diego",
    "university of california berkeley": "University of California-Berkeley",
    "university of california davis": "University of California-Davis",
    "university of california irvine": "University of California-Irvine",
    "university of california santa barbara": "University of California-Santa Barbara",
    "university of california santa cruz": "University of California-Santa Cruz",
    "university of california riverside": "University of California-Riverside",
    "university of california merced": "University of California-Merced",
    "texas a m": "Texas A&M University-College Station", "tamu": "Texas A&M University-College Station",
    "a m": "Texas A&M University-College Station",
    "ut austin": "The University of Texas at Austin", "ut dallas": "The University of Texas at Dallas",
    "utd": "The University of Texas at Dallas", "uta": "The University of Texas at Arlington",
    "ut": "The University of Texas at Austin", "uva": "University of Virginia-Main Campus",
    "umich": "University of Michigan-Ann Arbor", "u mich": "University of Michigan-Ann Arbor",
    "michigan": "University of Michigan-Ann Arbor", "unc": "University of North Carolina at Chapel Hill",
    "unc chapel hill": "University of North Carolina at Chapel Hill", "ohio state": "Ohio State University-Main Campus",
    "osu": "Ohio State University-Main Campus", "the ohio state": "Ohio State University-Main Campus",
    "ohio state university": "Ohio State University-Main Campus",
    "penn state": "Pennsylvania State University-Main Campus", "psu": "Pennsylvania State University-Main Campus",
    "pitt": "University of Pittsburgh-Pittsburgh Campus", "uw madison": "University of Wisconsin-Madison",
    "wisconsin": "University of Wisconsin-Madison", "uw": "University of Washington-Seattle Campus",
    "university of washington": "University of Washington-Seattle Campus", "gt": "Georgia Institute of Technology-Main Campus",
    "georgia tech": "Georgia Institute of Technology-Main Campus", "gatech": "Georgia Institute of Technology-Main Campus",
    "vt": "Virginia Polytechnic Institute and State University", "virginia tech": "Virginia Polytechnic Institute and State University",
    "cmu": "Carnegie Mellon University", "carnegie mellon": "Carnegie Mellon University",
    "jhu": "Johns Hopkins University", "johns hopkins": "Johns Hopkins University", "hopkins": "Johns Hopkins University",
    "uchicago": "University of Chicago", "u chicago": "University of Chicago", "chicago": "University of Chicago",
    "upenn": "University of Pennsylvania", "penn": "University of Pennsylvania", "u penn": "University of Pennsylvania",
    "nyu": "New York University", "bu": "Boston University", "bc": "Boston College", "neu": "Northeastern University",
    "gtown": "Georgetown University", "georgetown": "Georgetown University", "usc": "University of Southern California",
    "tufts": "Tufts University", "tulane": "Tulane University of Louisiana", "mit": "Massachusetts Institute of Technology",
    "caltech": "California Institute of Technology", "cal tech": "California Institute of Technology",
    "harvey mudd": "Harvey Mudd College", "hmc": "Harvey Mudd College", "cmc": "Claremont McKenna College",
    "claremont mckenna": "Claremont McKenna College", "pomona": "Pomona College", "uiuc engineering": "University of Illinois Urbana-Champaign",
    "illinois": "University of Illinois Urbana-Champaign", "university of illinois": "University of Illinois Urbana-Champaign",
    "umass boston": "University of Massachusetts-Boston", "stony brook": "Stony Brook University",
    "suny stony brook": "Stony Brook University", "binghamton": "Binghamton University", "suny binghamton": "Binghamton University",
    "suny binghamton university": "Binghamton University", "bing": "Binghamton University",
    "suny buffalo": "University at Buffalo", "buffalo": "University at Buffalo", "ub": "University at Buffalo", "colby": "Colby College", "bates": "Bates College",
    "bowdoin": "Bowdoin College", "middlebury": "Middlebury College", "amherst": "Amherst College",
    "williams": "Williams College", "swarthmore": "Swarthmore College", "vassar": "Vassar College",
    "carleton": "Carleton College", "macalester": "Macalester College", "grinnell": "Grinnell College",
    "oberlin": "Oberlin College", "kenyon": "Kenyon College", "davidson": "Davidson College", "wellesley": "Wellesley College",
    "barnard": "Barnard College", "haverford": "Haverford College", "bryn mawr": "Bryn Mawr College",
    "hamilton": "Hamilton College", "colgate": "Colgate University", "brandeis": "Brandeis University",
    "northeastern": "Northeastern University", "rice": "Rice University", "emory": "Emory University",
    "case western": "Case Western Reserve University", "cwru": "Case Western Reserve University",
    "lehigh": "Lehigh University", "villanova": "Villanova University", "notre dame": "University of Notre Dame",
    "nd": "University of Notre Dame", "fordham": "Fordham University", "syracuse": "Syracuse University",
    "purdue": "Purdue University-Main Campus", "rutgers": "Rutgers University-New Brunswick",
    "umd college park": "University of Maryland-College Park", "maryland": "University of Maryland-College Park",
    "university of maryland": "University of Maryland-College Park", "minnesota": "University of Minnesota-Twin Cities",
    "university of minnesota": "University of Minnesota-Twin Cities", "iowa": "University of Iowa",
    "uiowa": "University of Iowa", "indiana": "Indiana University-Bloomington", "iu": "Indiana University-Bloomington",
    "iu bloomington": "Indiana University-Bloomington", "miami": "University of Miami", "um": "University of Miami",
    "uga": "University of Georgia", "georgia": "University of Georgia", "alabama": "The University of Alabama",
    "auburn": "Auburn University", "clemson": "Clemson University", "usc columbia": "University of South Carolina-Columbia",
    "south carolina": "University of South Carolina-Columbia", "uofsc": "University of South Carolina-Columbia",
    "uvm": "University of Vermont", "unh": "University of New Hampshire-Main Campus", "umaine": "University of Maine",
    "uri": "University of Rhode Island", "du": "University of Denver", "cu boulder": "University of Colorado Boulder",
    "colorado boulder": "University of Colorado Boulder", "university of colorado boulder": "University of Colorado Boulder",
    "asu": "Arizona State University Campus Immersion", "arizona state": "Arizona State University Campus Immersion",
    "ua": "University of Arizona", "arizona": "University of Arizona", "oregon": "University of Oregon",
    "oregon state": "Oregon State University", "washington state": "Washington State University", "wsu": "Washington State University",
    "sdsu": "San Diego State University", "sjsu": "San Jose State University", "sfsu": "San Francisco State University",
    "csulb": "California State University-Long Beach", "cal state long beach": "California State University-Long Beach",
    "cpp": "California State Polytechnic University-Pomona", "cal poly pomona": "California State Polytechnic University-Pomona",
    "loyola marymount": "Loyola Marymount University", "lmu": "Loyola Marymount University", "pepperdine": "Pepperdine University",
    "santa clara": "Santa Clara University", "scu": "Santa Clara University", "occidental": "Occidental College",
    "oxy": "Occidental College", "uop": "University of the Pacific", "smu": "Southern Methodist University",
    "tcu": "Texas Christian University", "baylor": "Baylor University", "texas tech": "Texas Tech University",
    "uh": "University of Houston", "ut dallas": "The University of Texas at Dallas", "ut arlington": "The University of Texas at Arlington",
    "ut san antonio": "The University of Texas at San Antonio", "utsa": "The University of Texas at San Antonio",
    "tulane university": "Tulane University of Louisiana", "lsu": "Louisiana State University and Agricultural & Mechanical College",
    "vanderbilt": "Vanderbilt University", "vandy": "Vanderbilt University", "duke": "Duke University",
    "wfu": "Wake Forest University", "elon": "Elon University", "william mary": "William & Mary", "william and mary": "William & Mary",
    "w m": "William & Mary", "wm": "William & Mary", "vcu": "Virginia Commonwealth University", "gmu": "George Mason University",
    "jmu": "James Madison University", "howard": "Howard University", "american": "American University",
    "au": "American University", "cua": "The Catholic University of America", "drexel": "Drexel University",
    "temple": "Temple University", "penn state behrend": "Pennsylvania State University-Penn State Erie-Behrend College",
    "cooper union": "The Cooper Union for the Advancement of Science and Art",
    "stevens": "Stevens Institute of Technology", "njit": "New Jersey Institute of Technology", "rowan": "Rowan University",
    "tcnj": "The College of New Jersey", "cornell university": "Cornell University", "cornell": "Cornell University",
    "cornell engineering": "Cornell University", "cornell cals": "Cornell University", "dartmouth": "Dartmouth College",
    "brown": "Brown University", "yale": "Yale University", "harvard": "Harvard University", "princeton": "Princeton University",
    "stanford": "Stanford University", "columbia": "Columbia University in the City of New York",
    "columbia gs": "Columbia University in the City of New York", "columbia university": "Columbia University in the City of New York",
    "rochester": "University of Rochester", "u rochester": "University of Rochester", "ur": "University of Rochester",
    "scripps": "Scripps College", "pitzer": "Pitzer College",
    "mudd": "Harvey Mudd College", "trinity": "Trinity University", "tufts university": "Tufts University",
    "gw university": "George Washington University", "uconn storrs": "University of Connecticut",
    "ucsd": "University of California-San Diego", "cu": "University of Colorado Boulder",
    # sub-schools and common spellings found in the first parse's most frequent misses
    "university of pittsburgh": "University of Pittsburgh-Pittsburgh Campus", "upitt": "University of Pittsburgh-Pittsburgh Campus",
    "university of pitt": "University of Pittsburgh-Pittsburgh Campus", "umiami": "University of Miami", "u miami": "University of Miami",
    "university of miami": "University of Miami", "nyu stern": "New York University", "nyu cas": "New York University",
    "nyu tandon": "New York University", "nyu tisch": "New York University", "nyu abu dhabi": "New York University",
    "urochester": "University of Rochester", "gtech": "Georgia Institute of Technology-Main Campus",
    "ga tech": "Georgia Institute of Technology-Main Campus", "georgia institute of technology": "Georgia Institute of Technology-Main Campus",
    "boston u": "Boston University", "boston uni": "Boston University", "csu long beach": "California State University-Long Beach",
    "uc los angeles": "University of California-Los Angeles", "irvine": "University of California-Irvine",
    "davis": "University of California-Davis", "riverside": "University of California-Riverside",
    "merced": "University of California-Merced", "santa barbara": "University of California-Santa Barbara",
    "santa cruz": "University of California-Santa Cruz", "los angeles": "University of California-Los Angeles",
    "san diego": "University of California-San Diego", "rose hulman": "Rose-Hulman Institute of Technology",
    "umichigan": "University of Michigan-Ann Arbor", "cmu scs": "Carnegie Mellon University", "cmu tepper": "Carnegie Mellon University",
    "cmu cs": "Carnegie Mellon University", "cmu ece": "Carnegie Mellon University", "ann arbor": "University of Michigan-Ann Arbor",
    "umich ross": "University of Michigan-Ann Arbor", "umich lsa": "University of Michigan-Ann Arbor", "umich engineering": "University of Michigan-Ann Arbor",
    "loyola chicago": "Loyola University Chicago", "uw seattle": "University of Washington-Seattle Campus", "udub": "University of Washington-Seattle Campus",
    "uwash": "University of Washington-Seattle Campus", "iu kelley": "Indiana University-Bloomington", "risd": "Rhode Island School of Design",
    "umbc": "University of Maryland-Baltimore County", "csuf": "California State University-Fullerton", "csu fullerton": "California State University-Fullerton",
    "csun": "California State University-Northridge", "csus": "California State University-Sacramento", "sacramento state": "California State University-Sacramento",
    "unc charlotte": "The University of North Carolina at Charlotte", "uncc": "The University of North Carolina at Charlotte",
    "john hopkins": "Johns Hopkins University", "uc berkley": "University of California-Berkeley", "uc berk": "University of California-Berkeley",
    "ucberkeley": "University of California-Berkeley", "university of oklahoma": "University of Oklahoma-Norman Campus", "ou": "University of Oklahoma-Norman Campus",
    "north carolina state university": "North Carolina State University at Raleigh", "chapel hill": "University of North Carolina at Chapel Hill",
    "unc ch": "University of North Carolina at Chapel Hill", "wharton": "University of Pennsylvania", "penn wharton": "University of Pennsylvania",
    "umn twin cities": "University of Minnesota-Twin Cities", "colorado state university": "Colorado State University-Fort Collins",
    "colorado state": "Colorado State University-Fort Collins", "csu": "Colorado State University-Fort Collins", "suny oswego": "State University of New York at Oswego",
    "embry riddle": "Embry-Riddle Aeronautical University-Daytona Beach", "umaryland": "University of Maryland-College Park",
    "suny purchase": "SUNY at Purchase College", "usc marshall": "University of Southern California", "college park": "University of Maryland-College Park",
    "umd cs": "University of Maryland-College Park", "umd smith": "University of Maryland-College Park", "university of tennessee": "The University of Tennessee-Knoxville",
    "utk": "The University of Tennessee-Knoxville", "tennessee": "The University of Tennessee-Knoxville", "uic": "University of Illinois Chicago",
    "hunter college": "CUNY Hunter College", "hunter": "CUNY Hunter College", "baruch": "CUNY Bernard M Baruch College",
    "baruch college": "CUNY Bernard M Baruch College", "suny geneseo": "SUNY College at Geneseo", "geneseo": "SUNY College at Geneseo",
    "suny new paltz": "State University of New York at New Paltz", "clarkson": "Clarkson University", "college of william and mary": "William & Mary",
    "urbana champaign": "University of Illinois Urbana-Champaign", "university of illinois at urbana champaign": "University of Illinois Urbana-Champaign",
    "university of illinois urbana champaign": "University of Illinois Urbana-Champaign", "u of i": "University of Illinois Urbana-Champaign",
    "urichmond": "University of Richmond", "richmond": "University of Richmond", "university of richmond": "University of Richmond",
    "union": "Union College", "vtech": "Virginia Polytechnic Institute and State University", "asu barrett": "Arizona State University Campus Immersion",
    "uni of rochester": "University of Rochester", "usd": "University of San Diego", "university of san diego": "University of San Diego",
    "ucsf": "University of California-San Francisco", "uw bothell": "University of Washington-Bothell Campus",
    "virginia commonwealth": "Virginia Commonwealth University", "johns hopkins university": "Johns Hopkins University",
    "pittsburgh": "University of Pittsburgh-Pittsburgh Campus", "pratt": "Pratt Institute", "calpoly slo": "California Polytechnic State University-San Luis Obispo",
    "california polytechnic state university": "California Polytechnic State University-San Luis Obispo", "sf state": "San Francisco State University",
    "uoregon": "University of Oregon", "udel": "University of Delaware", "university of delaware": "University of Delaware",
    "uflorida": "University of Florida", "uwisconsin": "University of Wisconsin-Madison", "uwisconsin madison": "University of Wisconsin-Madison",
    "u michigan": "University of Michigan-Ann Arbor", "mizzou": "University of Missouri-Columbia", "georgiatech": "Georgia Institute of Technology-Main Campus",
    "michigan tech": "Michigan Technological University", "florida tech": "Florida Institute of Technology", "scad": "Savannah College of Art and Design",
    "suny albany": "University at Albany", "albany": "University at Albany", "uwashington": "University of Washington-Seattle Campus",
    "loyola maryland": "Loyola University Maryland", "john s hopkins": "Johns Hopkins University", "california state university": "California State University-Fullerton",
    "cal berkeley": "University of California-Berkeley", "cal": "University of California-Berkeley", "gw honors": "George Washington University",
    "uofpenn": "University of Pennsylvania", "u of penn": "University of Pennsylvania", "u of illinois": "University of Illinois Urbana-Champaign",
    "u of maryland": "University of Maryland-College Park", "u of michigan": "University of Michigan-Ann Arbor",
    "u of minnesota": "University of Minnesota-Twin Cities", "u of arizona": "University of Arizona",
    "u of tennessee": "The University of Tennessee-Knoxville", "u of florida": "University of Florida",
    "umd cp": "University of Maryland-College Park", "uoregon": "University of Oregon", "uwashington": "University of Washington-Seattle Campus",
    "northwestern": "Northwestern University", "nu": "Northwestern University", "ucla anderson": "University of California-Los Angeles",
}

# Words that are never part of a college name once a college has been found at the start of a phrase.
_DROP_WORDS = {"the", "a", "an"}
_BLOCK_TRAIL = {"state", "tech", "polytechnic", "a&m", "am", "poly", "northern", "southern", "eastern", "western",
                "central", "international", "christian", "baptist", "catholic", "methodist", "online", "at"}
_JUNK_RX = re.compile(
    r"^(god bless|good luck|thanks?|hope|feel free|pm me|ama\b|none\b.*|n/?a\b.*|macaulay.*|awaiting|honors|honors program|all|overall|safeties|safety|reaches|reach|targets?|etc|and|withdrawals?|state school|state schools|in state safety|"
    r"n/?a|nan|tbd|tba|will update|list here|college(s)? (names?|here)|rest of|the rest|all (the )?(others?|other)|"
    r"others?|ivies|the ivies|every(thing| other)|still waiting|waiting|pending|no decision|not (yet )?(received|released)|"
    r"yet to|\.\.\.|-+|\d+)$|^(rest of|all other|the rest|still waiting|waiting (on|for)|will |didn'?t|did not|"
    r"haven'?t|have not|not applied|never|no |i |my |thanks|thank you|edit|update)", re.I)

# ---------------------------------------------------------------- tag tables
ACTIVITY_TAGS = {
    "research": r"research|\blab\b|laborator|publication|published (a|in|my)|science fair|\bisef\b|\breu\b|\bsts\b|"
                r"\bregeneron|\bjshs\b|\bpaper\b",
    "sports": r"varsity|captain|swim|soccer|basketball|football|tennis|\btrack\b|cross[- ]country|lacrosse|baseball|"
              r"softball|volleyball|wrestl|\bgolf|hockey|rowing|\bcrew\b|fencing|athlet|\bsports?\b|gymnast|cheer|"
              r"martial arts|karate|taekwondo|badminton|ultimate frisbee|\bpolo\b|skiing|rugby|boxing|\bnike\b",
    "music": r"orchestra|\bband\b|choir|violin|piano|cello|guitar|jazz|\bmusic|drum|flute|trumpet|saxophone|singer|"
             r"symphony|chorus|marching|clarinet|bassoon|\bviola\b|trombone|a cappella|acapella|composition|\bbass\b|"
             r"\bsing(ing)?\b",
    "debate": r"debate|model un\b|\bmun\b|speech|forensic|mock trial|moot court|\bnsda\b|extemp|congressional debate",
    "robotics": r"robot|\bfrc\b|\bftc\b|\bvex\b|first tech|first robotics|\bfll\b",
    "volunteering": r"volunteer|community service|non-?profit|charity|food bank|food pantry|soup kitchen|"
                    r"habitat for humanity|red cross|fundrais|\bngo\b|key club|\bnhs\b|service hours|mission trip",
    "work": r"\bjob\b|work(ed|ing)? (at|as|for|in|part|full)|employ|barista|cashier|waiter|waitress|retail|restaurant|"
            r"part[- ]time|lifeguard|\bsummer job|babysit|server at|grocery|camp counselor|internship|\bintern\b|"
            r"paid (position|work)|\bshift",
    "student government": r"student council|student government|\bsga\b|\basb\b|class (president|officer|rep|board)|"
                          r"\bstuco\b|class senate|student body|student senate|school board|\bsenate\b|"
                          r"student representative|grade rep",
    "family care": r"sibling|babysit|care ?giver|take care of|taking care of|care for (my|a)|raising my|raise my|"
                   r"translat\w+ for (my|the) (family|parents|mom|dad)|younger (brother|sister|sibling)|grandparent|"
                   r"grandmother|grandfather|cook(ing)? for (my )?family|help(ing|ed)? (my|raise)|family (business|duties|responsib)|"
                   r"look after (my )?(brother|sister|siblings)|my (brother|sister)'?s? (care|needs|disab)",
    "arts": r"\bart\b|\barts\b|painting|drawing|theat(er|re)|drama|\bfilm|photograph|\bdance|ballet|sculpt|ceramic|"
            r"\bdesign|musical|animation|illustrat|cinemat|sketch|crochet|knit|poetry slam|pottery|\bcraft",
    "writing": r"writing|newspaper|journalis|\beditor|\bauthor\b|novel|poetry|\bpoem|\bblog|magazine|yearbook|literary|"
               r"wrote (a|my)|\bessay contest|scholastic|creative writing|columnist|short stor",
    "business": r"business|entrepreneur|start-?up|founded|\bdeca\b|\bfbla\b|co-?found|own company|marketing|\bstocks?\b|"
                r"\binvest|my own (brand|company|store|shop|business)|sold|e-?commerce|\betsy\b|\bshopify\b|"
                r"\bventure|\bsales\b|finance club|\bceo\b",
    "coding": r"\bcod(e|ing)\b|programm|software|app (dev|develop)|developer|hackathon|python|\bjava\b|website|web dev|"
              r"\bgithub|computer science|\bcs club|usaco|machine learning|\bai\b|\bapp\b|unity|\bc\+\+|javascript|"
              r"cyberpatriot|game dev|\bcompsci|\bcs\b",
}
ESSAY_THEMES = {
    "family": r"mother|father|\bmom\b|\bdad\b|parent|grandm|grandf|grandpa|grandma|sibling|brother|sister|\bfamily|"
              r"\bmy (twin|aunt|uncle|cousin)",
    "immigration": r"immigra|refugee|moved (here )?to (the )?(us|u\.s\.|america|states)|came to (the )?(us|u\.s\.|america|states)|"
                   r"citizen|\bvisa\b|green card|undocumented|first generation american|asylum|moving to (the )?(us|america)",
    "identity": r"identity|heritage|who i am|\bqueer|\blgbt|gender|religio|\bfaith\b|ethnic|\brace\b|racial|"
                r"bicultural|biracial|coming out|jewish|muslim|hindu|christian|sikh|catholic|\bgay\b|bisexual|"
                r"transgender|\btrans\b|being (an? )?(asian|black|latin|hispanic|indian|arab|chinese|korean)|"
                r"third culture|two worlds|belong",
    "failure and persistence": r"\bfail|setback|struggl|persever|resilien|overcame|overcome|rejection|mistake|"
                               r"challeng|obstacle|adversit|\bgrit\b|hardship|difficult|hard time|bounced back|"
                               r"learn(ed|ing)? from",
    "illness": r"\bill(ness)?\b|disease|cancer|diabet|disabilit|mental health|depress|anxiety|chronic|hospital|surgery|"
               r"autis|\badhd|cystic|crohn|\bmedical|therap|sick|epilep|eating disorder|\bocd\b|injur|\bptsd|"
               r"dyslex|stutter|anorexi|cerebral palsy|illnesses",
    "work": r"\bjobs?\b|\bwork(ed|ing)?\b|employ|restaurant|barista|cashier|family business|part[- ]time|summer job|"
            r"my (first )?job|\bshift|waiter|waitress|labor|\bfarm",
    "sport": r"\bsports?\b|swim|soccer|basketball|football|tennis|\btrack\b|athlet|running|cross[- ]country|\bcoach|"
             r"\bgolf|wrestl|volleyball|lacrosse|baseball|softball|\browing|\bcrew\b|fencing|gymnast|hockey|\bskat|\bski",
    "curiosity": r"curios|intellectual|love of learning|passion for learning|\bscience|\bmath|\bwhy\b|wonder|"
                 r"explor|fascinat|research|philosoph|\bquestion|discover|\bphysics|\bchemistry|\bbiology|"
                 r"\bengineering|\bcoding|\bcode\b|\bcs\b|computer",
    "community": r"communit|volunteer|\bservice\b|neighborhood|hometown|help(ing)? others|activis|giving back|"
                 r"\bserve|small town|\btown\b|\bcity\b|church|temple|mosque|nonprofit|non-profit|club",
    "culture": r"cultur|tradition|language|bilingual|\bfood\b|\bcook|\bfestival|\bcustoms?\b|ancestr|homeland|"
               r"native country|my country|\bhome country|diaspora|grew up (in|between)|translat|\bnames?\b",
    "loss": r"death|\bdied\b|\bdie\b|passed away|\bloss\b|grief|\blost my|funeral|mourn|\blate (father|mother|grand)|"
            r"\bdeceased|bereave|suicide|passing of|\bwidow",
    "hobby": r"hobb(y|ies)|chess|\bknit|\bbak(e|ing)\b|garden|collect|photograph|gaming|video games?|\bdrawing|painting|"
             r"fishing|origami|rubik|\blego|\bread(ing)?\b|cooking|piano|guitar|\bmusic|\bart\b|\bhike|\bhiking|"
             r"\bpuzzle|\bcar(s)?\b|\bfashion|\bthrift|\bdance|\bbook",
}
_ACT_RX = {k: re.compile(v, re.I) for k, v in ACTIVITY_TAGS.items()}
_ESS_RX = {k: re.compile(v, re.I) for k, v in ESSAY_THEMES.items()}

# Race / gender words scrubbed from stored free text (the template lines for them are skipped outright).
_SCRUB_RX = re.compile(
    r"\b(asian|african[- ]american|black(?! belt| box| hole| out)|hispanic|latino|latina|latinx|caucasian|"
    r"white|native american|pacific islander|middle eastern|south asian|east asian|southeast asian|"
    r"female|male|nonbinary|non-binary|woman|man)\b", re.I)

US_STATES = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR", "california": "CA", "colorado": "CO",
    "connecticut": "CT", "delaware": "DE", "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
    "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS", "kentucky": "KY", "louisiana": "LA",
    "maine": "ME", "maryland": "MD", "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
    "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV", "new hampshire": "NH", "new jersey": "NJ",
    "new mexico": "NM", "new york": "NY", "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
    "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC", "south dakota": "SD",
    "tennessee": "TN", "texas": "TX", "utah": "UT", "vermont": "VT", "virginia": "VA", "washington": "WA",
    "west virginia": "WV", "wisconsin": "WI", "wyoming": "WY", "district of columbia": "DC",
}
_STATE_NAMES_RX = re.compile(r"\b(" + "|".join(sorted((re.escape(s) for s in US_STATES), key=len, reverse=True)) + r")\b",
                             re.I)
_ABBR = set(US_STATES.values())
_AMBIG_ABBR = {"IN", "OR", "ME", "OK", "HI", "ID", "DE", "LA", "PA", "MA", "AL"}
_NON_US = re.compile(r"\b(india|china|canada|uk|england|kuwait|korea|japan|singapore|vietnam|nigeria|ghana|pakistan|"
                     r"bangladesh|dubai|uae|saudi|egypt|turkey|mexico|brazil|germany|france|spain|italy|hong kong|taiwan|"
                     r"philippines|indonesia|malaysia|thailand|nepal|sri lanka|kenya|ethiopia|israel|australia|"
                     r"new zealand|ireland|europe|asia|africa|international)\b", re.I)

# ---------------------------------------------------------------- text cleaning


_PLACEHOLDER_RX = re.compile(
    r"\(\s*(?:write|list|put|type|enter|insert)\s+(?:here|them here|all here)\s*\)|\(briefly reflect/?rate\)|"
    r"\(?\s*indicate ED/EA/REA/SCEA/RD\s*\)?|\(or percentile\)|\(optional\)", re.I)
_INSTRUCTION_LINE_RX = re.compile(
    r"^\s*(?:list (?:all|the highest|the awards|your|any|everything|extracurricular)|include (?:all|any)|"
    r"please (?:list|include|fill)|(?:example|ex)\s*[:.]|insert |note: (?:this|please)|"
    r"all scores that were reported|highest scores earned)", re.I)


def clean_text(t: str) -> str:
    """Decode entities, drop links, usernames, e-mails, zero-width characters and markdown decoration."""
    t = html.unescape(html.unescape(t or ""))
    t = t.replace("\u200b", "").replace("\ufe0f", "").replace("\ufffd", "'").replace("\r\n", "\n").replace("\r", "\n")
    t = t.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')
    t = re.sub(r"\[([^\]]*)\]\((?:https?://|www\.)[^)]*\)", r"\1", t)
    t = re.sub(r"(?:https?://|www\.)\S+", "", t)
    t = re.sub(r"(?<![\w/])/?[ur]/[A-Za-z0-9_\-]{2,}", "", t)
    t = re.sub(r"\S+@\S+\.\S+", "", t)
    t = re.sub(r"(?<=\w)@\w+", "", t)  # a handle glued to a word, e.g. "Club@XYZ"
    t = re.sub(r"(?<![\w])@[A-Za-z0-9_.]{2,}", "", t)
    t = re.sub(r"\\([#*_\-.()\[\]>~|!+&])", r"\1", t)
    t = t.replace("**", "").replace("__", "").replace("~~", "").replace(">!", "").replace("!<", "")
    t = re.sub(r"(?<![\w*])\*+(?=\S)|(?<=\S)\*+(?![\w*])", "", t)
    t = re.sub(r"(?<![\w])_+(?=\S)|(?<=\S)_+(?![\w])", "", t)
    t = _PLACEHOLDER_RX.sub(" ", t)
    t = "\n".join(l for l in t.split("\n") if not _INSTRUCTION_LINE_RX.match(l))
    return t


def scrub_free_text(s: str) -> tuple[str, int]:
    """Remove race and gender words from text that will be stored. Returns (text, number removed)."""
    out, n = _SCRUB_RX.subn("", s)
    return re.sub(r"\s{2,}", " ", out).strip(), n


_BULLET_RX = re.compile(r"^\s*(?:[-\u2022\u00b7\u25aa\u25e6>+]+|#+(?!\s*of\b)|L?#\s?\d{1,2}[.):]?|\d{1,2}[.)]\s+|\(\d{1,2}\)|\[\d{1,2}\])\s*")
_EMOJI_RX = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\u2190-\u21FF\u2300-\u23FF\U0001F000-\U0001F2FF]")
_OUTCOME_EMOJI = {"\u2705": "admitted", "\u2714": "admitted", "\u2713": "admitted", "\U0001F7E2": "admitted",
                  "\U0001F389": None, "\u274C": "denied", "\u2716": "denied", "\u2717": "denied", "\u274E": "denied",
                  "\U0001F534": "denied", "\u26D4": "denied", "\U0001F6AB": "denied", "\u23F3": "waitlisted",
                  "\U0001F7E1": "waitlisted", "\u231B": "waitlisted", "\U0001F551": "waitlisted"}

# ---------------------------------------------------------------- label classification
_LABELS = [
    ("essays", r"(?:essays?\b|personal statement|common app|\bps\b|supplements?)"),
    ("acc", r"(?:accept\w*|admits?|admitted)\b"),
    ("wl", r"(?:wait ?list\w*|\bwl\b)"),
    ("rej", r"(?:reject\w*|denial\w*|denied|deny)\b"),
    ("defer", r"(?:defer\w*|withdr\w*|waiting|awaiting|pending|still waiting|yet to hear|no decision|haven'?t heard|"
              r"committed to|final (?:choice|decision)|decisions? (?:pending|coming)|not applied|did not apply|"
              r"didn'?t apply)"),
    ("dec", r"(?:decisions?|results?|college results|final results|outcomes?|admissions? (?:results|decisions)|schools?"
            r" (?:applied|applying)|where i applied)\b"),
    ("add", r"(?:additional|addtl|extra info|other\b|notes?\b|comments?\b|advice|reflections?|hindsight|final\b|summary|"
            r"tl;?dr|conclusion|updates?\b|edit\b|thoughts|what i would|if i could|retrospect|overall|post[- ]?decision|"
            r"committed|financial|scholarships?)"),
    ("interviews", r"interviews?"),
    ("lor", r"(?:letters?|lors?\b|recs?\b|recommend|teacher rec|counselor rec)"),
    ("ec", r"(?:extra[- ]?curriculars?|activities|activity|ecs?\b|ec's|ecs\b|top extracurriculars|honors/ecs|"
           r"ec/|ec and|summer (?:activities|programs?))"),
    ("awards", r"(?:awards?|honors\b|achievements|accolades)"),
    ("major", r"(?:intended|planned|prospective|potential|major|proposed|desired|field of study|area of study|intend)"),
    ("skip", r"(?:gender|sex\b|race|ethnic\w*|pronouns|sexuality|orientation)"),
    ("gpa", r"(?:gpa|uw(?=\s*(?:/|:|-|gpa|$))|u\.w|w gpa|weighted|unweighted|grades?\b|cumulative|uw/w)"),
    ("rank", r"(?:class rank|rank\b|percentile)"),
    ("test", r"(?:sat|act\b|psat|standardi[sz]ed|test scores?|testing|tests?\b|scores?\b|sat/act|act/sat)"),
    ("courses", r"(?:aps?\b|ib\b|apib|ap/ib|courses?|coursework|course load|rigor|dual|honors/ap|# of|number of|classes|"
                r"curriculum|senior year|schedule)"),
    ("academics", r"academics?\b"),
    ("demographics", r"(?:demographics?|background|about me|stats|profile)"),
    ("residence", r"(?:residence|location|state\b|region|home\b|from\b|hometown|city|geograph\w*|country|where)"),
    ("income", r"(?:income|family income|income bracket|efc|budget|socio)"),
    ("school", r"(?:type of school|school type|high school|school\b|hs\b)"),
    ("hooks", r"hooks?"),
]
_LABELS_C = [(k, re.compile(r"^(?:" + p + ")", re.I)) for k, p in _LABELS]


def classify_label(label: str) -> str | None:
    lab = _EMOJI_RX.sub("", label)
    lab = re.sub(r"\([^)]*\)", " ", lab)
    lab = re.sub(r"[^A-Za-z0-9/#&' ;\-]", " ", lab).strip()
    lab = re.sub(r"\s+", " ", lab)
    if not lab or len(lab) > 70 or len(lab.split()) > 9:
        return None
    low = lab.lower()
    if re.match(r"^(?:[a-z]+\W+){0,1}essays?\b|^personal statement|^common app|^(?:lors?|letters?|recs?)\W+(?:and\W+)?essays?\b", low) \
            and not low.startswith(("accept", "reject", "wait")):
        return "essays"
    if re.match(r"^(?:uw|w|unweighted|weighted)\W*(?:/\W*(?:uw|w))?\W*(?:gpa|and|&)", low):
        return "gpa"
    for key, rx in _LABELS_C:
        if rx.match(low):
            if key == "dec" and low.startswith("school"):
                continue
            if key == "ec" and low.startswith("ec") and len(low.split()) > 4:
                continue
            return key
    return None


def split_label(line: str):
    """(key, label, value) when the line starts a known template field, else None."""
    s = _BULLET_RX.sub("", line).strip()
    s = _EMOJI_RX.sub(lambda m: m.group(0) if m.group(0) in _OUTCOME_EMOJI else "", s).strip()
    if not s:
        return None
    m = re.match(r"^([^:]{1,90}):\s*(.*)$", s)
    if m and not re.search(r"https?$", m.group(1)):
        key = classify_label(m.group(1))
        if key:
            return key, m.group(1), m.group(2).strip()
    m = re.match(r"^(.{1,40}?)\s+(?:-|\u2013|\u2014|=)\s+(\S.*)$", s)
    if m:
        key = classify_label(m.group(1))
        if key in ("test", "gpa", "major", "rank", "courses", "hooks", "residence", "school", "income", "skip"):
            return key, m.group(1), m.group(2).strip()
    if len(s) <= 45 and len(s.split()) <= 5 and ":" not in s[:-1]:
        key = classify_label(s.rstrip(":"))
        bare_ok = {"acc", "wl", "rej", "defer", "dec", "add", "interviews", "lor", "ec", "awards", "essays", "academics", "demographics"}
        if key in bare_ok or (key == "test" and re.match(r"(?i)^(?:standardi[sz]ed|test scores?|testing)", s))                 or (key == "major" and re.match(r"(?i)^intended", s)):
            return key, s.rstrip(":"), ""
    return None


def sectionize(text: str):
    """Ordered list of [key, label, [value lines]] plus the preamble lines (before the first field)."""
    fields = []
    pre = []
    cur = None
    for raw in text.split("\n"):
        line = raw.strip()
        if not line:
            if cur is not None:
                cur[3] += 1  # blank-line count since the field started
            continue
        sp = split_label(line)
        if sp:
            key, label, value = sp
            cur = [key, label, [value] if value else [], 0]
            fields.append(cur)
        elif cur is not None:
            cur[2].append(_BULLET_RX.sub("", line).strip())
        else:
            pre.append(line)
    return fields, pre


def gather(fields, *keys) -> list:
    """Lines (label + value) of every field with one of the keys, label kept so keywords survive."""
    out = []
    for key, label, vals, _b in fields:
        if key in keys:
            out.append(label + ": " + " ".join(v for v in vals if v) if vals else label)
    return out


def field_body(fields, *keys) -> str:
    out = []
    for key, label, vals, _b in fields:
        if key in keys:
            out.append("\n".join(v for v in vals if v))
    return "\n".join(o for o in out if o).strip()


# ---------------------------------------------------------------- numbers
def extract_sat(text: str, year_hint: int | None):
    """(sat_total or None, superscore flag). Handles 1500+, ranges, 'a -> b', components, 2400-scale (dropped)."""
    if not text:
        return None, False
    text = "\n".join(re.sub(r"^([^:\n]*?)\bSAT\s*(?:II|2|subject tests?)\b", r"\1", ln, flags=re.I) if ":" in ln else ln
                     for ln in text.split("\n"))
    t = re.sub(r"\b(SAT\s*(?:II|2|subject)|subject tests?|SAT\s*math\s*[12]|math\s*[12]c?\b)[^\n,;]*", " ", text, flags=re.I)
    t = re.sub(r"\b(PSAT|NMSQT)[^\n]*", " ", t, flags=re.I)
    t = re.sub(r"\(([^()]*(?:SAT|ACT)[^()]*)\)", r" \1 ", t, flags=re.I)  # keep parentheses that name a test
    t = re.sub(r"\([^()]*\)", " ", t)  # sections: (780/780), (770 x2), (690RW, 610M)
    sup = bool(re.search(r"super\s?-?score", text, re.I))
    nums = []
    for m in re.finditer(r"(?<![\d.$/])(1[0-6]\d0|[6-9]\d0)(?![\d])\s*(\+)?(?!\s*(?:/|x\s*2|%))", t):
        v = int(m.group(1))
        if 400 <= v <= 1600 and v % 10 == 0:
            if v < 900:
                continue  # a section score or a very low total: not stated as a reliable total
            nums.append((v, m.start(), m.end()))
    if not nums:
        m = re.search(r"(?<![\d.])([2-8]\d0|[4-8]\d0)\s*(?:EBRW|ERW|RW|R/W|reading|verbal|ev)[^\d]{0,12}?([4-8]\d0)\s*(?:M\b|math)", t, re.I) \
            or re.search(r"(?<![\d.])([4-8]\d0)\s*(?:M\b|math)[^\d]{0,12}?([4-8]\d0)\s*(?:EBRW|ERW|RW|R/W|reading|verbal)", t, re.I)
        if m and "ACT" not in t.upper():
            tot = int(m.group(1)) + int(m.group(2))
            if 800 <= tot <= 1600:
                return tot, sup
        return None, sup
    rng = re.search(r"(?<![\d])(1[0-6]\d0)\s*(?:-|\u2013|to)\s*(1[0-6]\d0)(?![\d])", t)
    if rng:
        a, b = int(rng.group(1)), int(rng.group(2))
        if 0 < b - a <= 100:
            return (a + b) // 2 // 10 * 10, sup
        return None, sup  # a wide range: not a score
    return max(v for v, _s, _e in nums), sup


def extract_act(text: str):
    if not text:
        return None
    t = re.sub(r"\(([^()]*(?:SAT|ACT)[^()]*)\)", r" \1 ", text, flags=re.I)
    t = re.sub(r"\([^()]*\)", " ", t)
    vals = []
    for m in re.finditer(r"\bACT\b[^0-9\n]{0,18}?(?<![\d.])(\d{2})(?![\d.]|\s*/\s*36\s*e)", t, re.I):
        vals.append(int(m.group(1)))
    for m in re.finditer(r"(?<![\d.])(\d{2})(?![\d.])\s*(?:composite|on (?:the )?act|act\b)", t, re.I):
        vals.append(int(m.group(1)))
    for m in re.finditer(r"(?<![\d.])(\d{2})(?![\d.])\s*(?:->|\u2192|\u2014>|then|to)\s*(\d{2})(?![\d.])", t):
        if re.search(r"\bact\b", t, re.I):
            vals += [int(m.group(1)), int(m.group(2))]
    # bare composite in a field that is only about the ACT or SAT/ACT: "SAT/ACT: 35"
    if not vals and re.match(r"^\s*(?:sat\s*/\s*act|act\s*/\s*sat|act)\s*[^0-9]{0,6}(\d{2})\b", t, re.I):
        vals.append(int(re.match(r"^\s*(?:sat\s*/\s*act|act\s*/\s*sat|act)\s*[^0-9]{0,6}(\d{2})\b", t, re.I).group(1)))
    vals = [v for v in vals if 12 <= v <= 36]
    return max(vals) if vals else None


_SCALES = {"4", "4.0", "4.00", "5", "5.0", "5.00", "100", "4.33", "4.3", "6", "6.0", "4.2", "4.4"}


def extract_gpa(text: str):
    """(uw, w, unlabeled, scale) - only what the post states."""
    if not text:
        return None, None, None, None
    t_alt = re.sub(r"\([^()\d]*\)", lambda m: m.group(0) if re.search(r"\b(?:UW|W|weighted|unweighted)\b", m.group(0), re.I) else " ", text)
    t = re.sub(r"\([^()\d]*\)", " ", text)
    scale = None
    if ":" in t and re.search(r"\b(?:UW|unweighted|weighted|W)\b", t.split(":", 1)[1], re.I):
        t = t.split(":", 1)[1]  # the post labels its own numbers: ignore the template label "UW/W GPA"
        t_alt = t
    _den = re.compile(r"(?<![\d.])(\d(?:\.\d{1,3})?)\s*(?:/|out of|on a)\s*(4\.0+|4\.33|4\.3|5\.0+|6\.0+|100|4|5|6)(?![\d.])")
    for ms in list(_den.finditer(t)):
        if ms.group(2) in _SCALES and not re.search(r"\b(uw|w)\b", t[max(0, ms.start() - 4):ms.start()], re.I):
            scale = scale or ms.group(2)
    t = _den.sub(lambda m: m.group(1) + " " if (m.group(2) in _SCALES) else m.group(0), t)
    for ms in re.finditer(r"(?:out of|on a)\s*(4\.0+|4\.33|4\.3|5\.0+|6\.0+|100|4|5|6)(?![\d.])", t, re.I):
        scale = scale or ms.group(1)
    t = re.sub(r"\(?\s*(?:out of|on a)\s*(?:4\.0+|4\.33|4\.3|5\.0+|6\.0+|100|4|5|6)(?![\d.])\s*(?:scale)?\s*\)?", " ", t, flags=re.I)
    if scale is None:
        m2 = re.search(r"(?:scale|out of|/)\s*(?:of\s*)?(4\.0+|5\.0+|4\.33|6\.0+|100)\b", t, re.I)
        if m2:
            scale = m2.group(1)
    toks = []
    for m in re.finditer(r"(?<![\d.])([0-6]\.\d{1,3})(?![\d])|(?<![A-Za-z])(UW|unweighted|un-weighted|W|wtd|weighted)(?![A-Za-z])", t, re.I):
        if m.group(1):
            toks.append(("n", float(m.group(1)), m.start()))
        else:
            lab = m.group(2).lower()
            toks.append(("l", "uw" if lab in ("uw", "unweighted", "un-weighted") else "w", m.start()))
    if not any(x[0] == "l" for x in toks) and t_alt != t:  # labels only inside a parenthesis, e.g. "3.58/3.78 (UW/W)"
        t = t_alt
        if ":" in t and re.search(r"\b(?:UW|W|weighted|unweighted)\b", t.split(":", 1)[1], re.I):
            t = t.split(":", 1)[1]
        toks = []
        for m in re.finditer(r"(?<![\d.])([0-6]\.\d{1,3})(?![\d])|(?<![A-Za-z])(UW|unweighted|un-weighted|W|wtd|weighted)(?![A-Za-z])", t, re.I):
            if m.group(1):
                toks.append(("n", float(m.group(1)), m.start()))
            else:
                lab = m.group(2).lower()
                toks.append(("l", "uw" if lab in ("uw", "unweighted", "un-weighted") else "w", m.start()))
    nums = [x for x in toks if x[0] == "n" and 1.0 <= x[1] <= 6.0]
    labs = [x for x in toks if x[0] == "l"]
    if not nums:
        return None, None, None, scale
    uw = w = un = None

    def put(label, v):
        nonlocal uw, w, un
        if label == "uw":
            if v <= 4.35:
                uw = uw or v
        elif label == "w":
            w = w or v
        else:
            un = un or v

    if labs and len(labs) == len(nums):
        for (_k, v, _p), (_k2, lab, _p2) in zip(nums, labs):
            put(lab, v)
    elif labs and len(nums) == 1:
        put(labs[0][1], nums[0][1])
    elif labs:
        taken = set()
        before_style = labs[0][2] < nums[0][2]  # "UW- 3.7 W- 4.2": each label names the number after it
        pairs = sorted(((((N[2] - L[2]) if N[2] >= L[2] else 99) if before_style else min(abs(L[2] - N[2]), abs(L[2] - (N[2] + 4))), li, ni)
                        for li, L in enumerate(labs) for ni, N in enumerate(nums)))
        done_l = set()
        for dist, li, ni in pairs:
            if li in done_l or ni in taken or dist > 12:
                continue
            done_l.add(li)
            taken.add(ni)
            put(labs[li][1], nums[ni][1])
    else:
        vs = [x[1] for x in nums]
        if len(vs) == 2 and vs[0] <= 4.0 < vs[1]:
            put("uw", vs[0]); put("w", vs[1])
        else:
            for v in vs[:1]:
                if v > 4.0:
                    put("w", v)
                else:
                    put(None, v)
    return uw, w, un, scale


def extract_rank(text: str):
    """(top_percent, raw) from 'top 5%', '8/65', '95th percentile'. Empty when not stated."""
    if not text:
        return None, ""
    t = re.sub(r"(?<![\d.])\d\.\d{1,3}\b", " ", text)
    m = re.search(r"top\s*~?(\d{1,2}(?:\.\d+)?)\s*(?:ish|-ish)?\s*(?:%|percent)", t, re.I)
    if m:
        return float(m.group(1)), "top %s%%" % m.group(1)
    m = re.search(r"(?<![\d.])(\d{1,2}(?:\.\d+)?)\s*(?:st|nd|rd|th)\s*percentile", t, re.I)
    if m and 50 <= float(m.group(1)) <= 100:
        return round(100 - float(m.group(1)), 1), "%sth percentile" % m.group(1)
    m = re.search(r"(?<![\d./])(\d{1,4})\s*(?:/|out of|of)\s*(\d{2,4})(?![\d.])", t)
    if m:
        r, n = int(m.group(1)), int(m.group(2))
        if 1 <= r <= n and n >= 15 and not (n <= 36 and r >= 20):
            return round(100.0 * r / n, 1), "%d/%d" % (r, n)
    # a bare "92%" next to the word rank is more often a grade than a class rank: left empty on purpose
    return None, ""


def extract_ap_count(text: str):
    """Number of AP/IB courses, only when stated as a count ('11 APs', '9 AP / 7 IB', '# of ...: 11'). Never a score."""
    if not text:
        return None
    ap = [int(m.group(1)) for m in re.finditer(r"(?<![\d.#(])(\d{1,2})\s*\+?\s*(?:x\s*)?(?:APs?\b|AP's|AP (?:classes|courses))(?!\s*[A-Z][a-z]+\s*\()", text, re.I)]
    ib = [int(m.group(1)) for m in re.finditer(r"(?<![\d.#(])(\d{1,2})\s*\+?\s*(?:[A-Za-z-]+\s+){0,2}(?:IBs?\b|IB (?:classes|courses|subjects)|HL\b)", text, re.I)]
    vals = []
    if ap and ib:
        vals.append(max(ap) + max(ib))
    else:
        vals += ap + ib
    for m in re.finditer(r"(?:^|\n)\s*(?:#|number)\s*(?:of)?\s*[^:\n]{0,60}:\s*(\d{1,2})\s*(?=$|\n|\()", text, re.I):
        vals.append(int(m.group(1)))
    for m in re.finditer(r"(?:^|\n)\s*(?:APs?|AP courses|AP classes|IB courses)\s*:\s*(\d{1,2})\b(?!\s*[%/,(])", text, re.I):
        vals.append(int(m.group(1)))
    vals = [v for v in vals if 1 <= v <= 30]
    return max(vals) if vals else None


# ---------------------------------------------------------------- small attributes
def extract_major(text: str):
    if not text:
        return "", None
    s = re.sub(r"\s+", " ", text).strip(" -:;*.")
    s = re.split(r"\s{2,}|\.\s|\n", s)[0][:100].strip()
    low = s.lower()
    if low in ("", "undecided", "undeclared", "unknown", "n/a", "na", "none", "?", "undecided/undeclared"):
        return "" if low in ("", "?", "none", "n/a", "na") else s, None
    if _privacy.looks_personal(s):
        return "", None
    s, _n = scrub_free_text(s)
    return s, major_group_for(s)


def extract_state(text: str):
    if not text or _NON_US.search(text):
        return ""
    for m in re.finditer(r"(?:^|[\s,(/])([A-Z]{2})(?=$|[\s,).;/])", text):
        ab = m.group(1)
        if ab in _ABBR and ab not in _AMBIG_ABBR:
            return ab
        if ab in _ABBR and ab in _AMBIG_ABBR and (text.strip() == ab or "," in text[:m.start() + 1]) and ab != "LA":
            return ab
    m = _STATE_NAMES_RX.search(text)
    if m:
        return US_STATES[m.group(1).lower()]
    return ""


def extract_school_type(text: str):
    if not text:
        return ""
    low = text.lower()
    if "charter" in low:
        return "charter"
    if re.search(r"international (school|baccalaureate)|\bint'?l school|\bib school|american school|british school", low):
        return "international"
    if re.search(r"private|prep school|preparatory|parochial|catholic|boarding|independent|religious|christian school", low):
        return "private"
    if re.search(r"public|magnet|title ?i|comprehensive|zoned|\bpublic\b", low):
        return "public"
    return ""


_NEG = re.compile(r"\b(no|not|non|without|n/a|none|zero)\b[\s-]{0,3}$", re.I)


def extract_hooks(text: str):
    """Hooks stated: first_gen, legacy, recruited athlete, low income. Race / URM is never read."""
    out = {"first_gen": False, "legacy": False, "recruited_athlete": False, "low_income": False}
    if not text:
        return out
    low = text.lower()

    def pos(rx):
        for m in re.finditer(rx, low):
            before = low[max(0, m.start() - 14):m.start()]
            if not _NEG.search(before) and not re.search(r"(no|not|non)[- ]?$", before):
                return True
        return False

    if pos(r"first[- ]?gen(eration)?\b|\bfgli\b|\bfg\b|\bfgl\b|first in my family|first to go to college|first-?gen"):
        out["first_gen"] = True
    if pos(r"\blegacy\b|\blegacies\b"):
        out["legacy"] = True
    if pos(r"recruit(ed)?\b|\brecruited athlete|d1 athlete|d3 athlete|nli\b|athletic recruit"):
        if not re.search(r"\b(un|not )recruited\b", low):
            out["recruited_athlete"] = True
    if pos(r"low[- ]income|\bfli\b|\bfgli\b|\bpell\b|\bfree lunch|financial need|\bfree/reduced"):
        out["low_income"] = True
    return out


def tag_list(text: str, table: dict) -> list:
    return [k for k, rx in table.items() if rx.search(text)]


# ---------------------------------------------------------------- colleges
_NORM = _colleges._norm
_VARIANTS = {}
_ALIASES = {}


def _build_college_index():
    """Variants of each Scorecard name that are unique across all colleges (drop 'University of', 'University')."""
    seen = {}
    for c in _colleges.load_colleges():
        n = _NORM(c["name"])
        forms = {n}
        base = re.sub(r"^the ", "", n)
        forms.add(base)
        base2 = re.sub(r"^university of ", "", base)
        forms.add(base2)
        forms.add(re.sub(r" (university|college)$", "", base2))
        forms.add(re.sub(r" (university|college)$", "", base))
        forms.add(re.sub(r"^(university|college) of ", "", base))
        forms.add(re.sub(r" in the city of new york$", "", base))
        forms.add(re.sub(r" (main campus|campus immersion)$", "", base))
        forms.add(base.replace(" and ", " "))
        forms.add(base.replace(" at ", " "))
        for f in forms:
            if len(f) >= 4:
                seen.setdefault(f, set()).add(c["id"])
    by_id = {c["id"]: c for c in _colleges.load_colleges()}
    for f, ids in seen.items():
        if len(ids) == 1:
            _VARIANTS[f] = by_id[next(iter(ids))]
    dropped = []
    for alias, full in COLLEGE_ALIASES.items():
        c = _colleges.find_college(full)
        if c is None:
            dropped.append(alias)
        else:
            _ALIASES[_NORM(alias)] = c
    return dropped


_ALIAS_DROPPED = _build_college_index()
_ROUND_RX = re.compile(
    r"(?<![A-Za-z])(ED\s?(?:I{1,2}|[12])?|EA\s?[12]?|REA|SCEA|RD|RA|ED2|EDII|EDI|early decision(?: ?(?:1|2|i|ii))?|"
    r"early action|restrictive early action|single[- ]choice early action|regular decision|regular|rolling)(?![A-Za-z])")
_OUTCOME_RX = re.compile(
    r"(?<![A-Za-z])(accepted|acceptance|admitted|admit|accept|got in|in!|rejected|rejection|reject|denied|deny|denial|"
    r"waitlisted|waitlist|wait ?list|wl|deferred|deferral|defer|withdrew|withdrawn|committed)(?![A-Za-z])", re.I)
_OUT_MAP = {"accepted": "admitted", "acceptance": "admitted", "admitted": "admitted", "admit": "admitted",
            "accept": "admitted", "got in": "admitted", "in!": "admitted", "rejected": "denied", "rejection": "denied",
            "reject": "denied", "denied": "denied", "deny": "denied", "denial": "denied", "waitlisted": "waitlisted",
            "waitlist": "waitlisted", "wait list": "waitlisted", "waitlist": "waitlisted", "waitlist ": "waitlisted",
            "wl": "waitlisted"}
_ARROW = re.compile(r"\s*(?:-+>|=+>|\u2014+>|\u2013+>|\u2192|\u279c|\u27a1|>>|\bthen\b|\bturned (?:in)?to\b|\bturned\b)\s*", re.I)


def resolve_college(text: str):
    """Scorecard college dict or None. Alias table first, then the engine's finder, then unique name variants."""
    n = _NORM(text)
    if not n:
        return None
    cands = [n]
    n2 = re.sub(r"^(the|university of|uni of|u of)\s+", "", n)
    cands.append(n2)
    cands.append(re.sub(r"\s+(university|college|univ|u)$", "", n2))
    for c in cands:
        if c in _ALIASES:
            return _ALIASES[c]
    for c in cands:
        hit = _colleges.find_college(c)
        if hit:
            return hit
    for c in cands:
        if c in _VARIANTS:
            return _VARIANTS[c]
    return None


_BRANCH_RX = re.compile(r"\b(greensburg|bradford|johnstown|titusville|regional|branch|satellite|extension|nus|kunshan|"
                        r"abu dhabi|shanghai|qatar|kuwait|dubai|singapore|oxford college|oxford at emory)\b", re.I)


def resolve_phrase(text: str):
    """Try the whole phrase, the part before ' - ', then shrinking word prefixes (never dropping 'state'/'tech')."""
    if _BRANCH_RX.search(text):
        return None
    parts = [text]
    for sep in (" - ", " \u2013 ", " \u2014 ", " / ", ": ", ", ", " | "):
        if sep in text:
            parts.append(text.split(sep)[0])
    for part in parts:
        c = resolve_college(part)
        if c:
            return c
    words = _NORM(parts[-1] if len(parts) > 1 else text).split()
    for k in range(len(words) - 1, 0, -1):
        dropped = words[k:]
        if any(w in _BLOCK_TRAIL for w in dropped[:1]):
            continue
        c = resolve_college(" ".join(words[:k]))
        if c and len(" ".join(words[:k])) >= 4:
            return c
    return None


def parse_item(item: str, mode):
    """One list item -> (college_text, outcome or None, round) or None when it is not a college string."""
    s = item.strip()
    em = None
    for ch in s:
        if ch in _OUTCOME_EMOJI:
            em = _OUTCOME_EMOJI[ch] or em
    s = _EMOJI_RX.sub("", s)
    s = re.sub(r"\s*\|?\s*\b(?:prediction|predicted|my guess|expected)\b.*$", "", s, flags=re.I)
    if mode is not None and " | " in s and not _OUTCOME_RX.search(s.split(" | ", 1)[0]):
        s = s.split(" | ", 1)[0]
    s = re.sub(r"[*_`]", "", s).strip()
    s = re.sub(r"^(?:cuny|suny|csu|uc)\s*:\s*", "", s, flags=re.I)
    s = re.sub(r"\b(?:accepted|admitted|got in|got|came|moved)\s+(?:off|from)\s+(?:of\s+)?(?:the\s+)?wait ?list(?:ed)?\b", "accepted", s, flags=re.I)
    s = re.sub(r"\b(?:off|from)\s+(?:of\s+)?(?:the\s+)?wait ?list\b", "accepted", s, flags=re.I)
    s = re.sub(r"\bwait ?list(?:ed)?\s*(?:to|then|and then|turned)\s*(?:accepted|admitted|admit)\b", "accepted", s, flags=re.I)
    outs_body = re.sub(r"\([^)]*\)|\[[^\]]*\]", lambda m: m.group(0) if (_ARROW.search(m.group(0)) or re.search(r"accepted", m.group(0), re.I)
                                                                          and re.search(r"wait", m.group(0), re.I)) else " ", s)
    s = re.sub(r"^(?:(?:safet(?:y|ies)|hard targets?|soft targets?|targets?|reach(?:es)?|likel(?:y|ies)|lottery|"
               r"super reach(?:es)?|far reach(?:es)?|ivies?|t\d+s?|top \d+)\s*[:\-\u2013]\s*)", "", s, flags=re.I)
    outs = [_OUT_MAP.get(m.group(1).lower().replace("  ", " ")) for m in _OUTCOME_RX.finditer(outs_body)
            if _OUT_MAP.get(m.group(1).lower().replace("  ", " "))]
    out = outs[-1] if outs else em
    rnd = ""
    rm = _ROUND_RX.search(s)
    if rm:
        tok = rm.group(1).lower().replace(" ", "")
        if tok.startswith(("ed", "earlydecision")):
            rnd = "ED"
        elif tok in ("ea", "ea1", "ea2", "rea", "scea", "earlyaction", "restrictiveearlyaction", "singlechoiceearlyaction"):
            rnd = "EA"
        elif tok in ("rd", "ra", "regulardecision", "regular"):
            rnd = "RD"
    s = re.sub(r"\([^)]*\)|\[[^\]]*\]", " ", s)
    s = _ARROW.split(s)[0] if _ARROW.search(s) else s
    s = _ROUND_RX.sub(" ", s)
    s = _OUTCOME_RX.sub(" ", s)
    s = re.sub(r"(?:^|\s)(?:w/|with)\s.*$", "", s, flags=re.I)
    s = re.sub(r"\b(merit|scholarship|honors college|full ride|aid|\$[\d,k.]+)\b.*$", "", s, flags=re.I)
    s = re.sub(r"^(?:ED|EA|RD|REA|SCEA|ED2|ED1|EA2)\s*(?:\([^)]*\))?\s*:\s*", "", s)
    s = re.sub(r"[:;|]+\s*$", "", s)
    s = re.sub(r"\s+", " ", s).strip(" .:-\u2013\u2014*_\"'!?,;/&+")
    s = re.sub(r"^(?:the )?(?:\d+[.)]|[-\u2022*])\s*", "", s).strip()
    if s and (len(s) > 55 or len(s.split()) > 8):
        head = re.split(r"\s[-–—:]\s", s, 1)[0].strip()
        if head and head != s and resolve_phrase(head) is not None:
            s = head
    if not s or len(s) > 55 or len(s.split()) > 8 or not _NORM(s):
        return None
    if _JUNK_RX.search(s) or re.search(r"\b(summer|fly[- ]?in|semi-?finalist|finalist|questbridge|"
                                       r"fellowship|competition|award|perspectives on|preview|camp|ask me|anything|questions?|"
                                       r"internship|stamps|posse|mentorship|oh boy|aka|get ready)\b", s, re.I) or re.search(r"\b(every|except|others?|rest of|all of|any of|ivies|ivy)\b", s, re.I) \
            or re.fullmatch(r"all [a-z]+", s, re.I):
        return None
    return s, (out or mode), rnd


def split_items(chunk: str) -> list:
    """Split a list chunk on commas (outside brackets), semicolons, bullets, slashes between names, ' and ' later."""
    chunk = re.sub(r"(University of (?:California|Texas|Illinois|Maryland|Massachusetts|Wisconsin|Colorado|Minnesota|"
                   r"Tennessee|North Carolina|South Carolina|Missouri))\s*,\s*(?!University|The |UC |UT )", r"\1 ", chunk)
    chunk = re.sub(r"\(([^()]*)\)", lambda m: "(" + m.group(1).replace(",", "\u0001").replace(";", "\u0002").replace("+", "\u0003") + ")", chunk)
    parts = re.split(r"[,;\u2022\u00b7|]|\s{3,}|\s+\+\s+", chunk)
    return [p.replace("\u0001", ",").replace("\u0002", ";").replace("\u0003", "+").strip() for p in parts if p.strip()]


def parse_decisions(fields, pre_lines, stats):
    """All (college text, outcome, round) triples in the decision sections of one post."""
    out = []
    started = False
    for key, label, vals, blanks in fields:
        pass
    mode = None
    for key, label, vals, _b in fields:
        if key in ("acc", "wl", "rej", "defer", "dec"):
            started = True
            mode = {"acc": "admitted", "wl": "waitlisted", "rej": "denied", "defer": "deferred", "dec": None}[key]
            if key == "wl" and re.search(r"(?:later|then|eventually|all|ended|turned)\W+(?:\w+\W+){0,3}(?:reject|denied|denial)", label, re.I):
                mode = "denied"
            lines = [l for l in vals if l.strip()]
            one = sum(1 for l in lines if l.strip()) >= 3
            # a header with trailing outcome words ("Accepted to: X, Y")
            for line in lines:
                if re.match(r"^(?:\W*)(?:also applied|i also applied|applied to|other schools|other applications|schools i|didn'?t apply|"
                            r"withdrew|withdrawn|withdraw|declined)", line.strip(), re.I):
                    break
                ma = re.match(r"^[\s\-]*(?:-+>|\u2192|=+>)\s*(accepted|admitted|rejected|denied|waitlisted)\b", line.strip(), re.I)
                if ma and out:
                    out[-1] = (out[-1][0], _OUT_MAP.get(ma.group(1).lower(), out[-1][1]), out[-1][2])
                    continue
                if re.match(r"^[A-Za-z' ]{2,30}\s*:\s*$", line.strip()) and not resolve_phrase(line.strip(" :")):
                    break  # an unknown heading such as "Mini Rant :" ends the list
                out += _lines_to_items(line, mode, stats, one)
        elif key in ("add", "ec", "essays", "interviews", "lor", "awards", "academics", "gpa", "test", "major",
                     "demographics", "courses", "rank", "income", "school", "hooks", "residence", "skip"):
            if started and key in ("add",):
                mode = None
            elif started:
                mode = None
    return out


def _lines_to_items(line: str, mode, stats, one_per_line=False):
    res = []
    if not line.strip():
        return res
    if len(line) > 160 and not _OUTCOME_RX.search(line):
        return res
    if line.count("|") >= 2:
        cells = [c.strip() for c in line.strip("|").split("|")]
        line = " ".join(cells[:1]) + " " + " ".join(cells[1:])
    line_np = re.sub(r"\([^)]*\)|\[[^\]]*\]", " ", line)
    words = len(line_np.split())
    if re.search(r"\b(thanks|thank you|good luck|hope you|feel free|pm me|dm me|any questions|ama\b|let me know|"
                 r"overall|in conclusion|i will|i'll|i am|i'm|i was|i got|i didn't|my )", line_np, re.I) and words > 7:
        return res
    mo = re.match(r"^[^:]{0,45}?\b(accepted|admitted|rejected|denied|waitlisted|waitlist)\b[^:]{0,25}:\s*(\S.*)$", line, re.I)
    if mo and len(mo.group(2).strip()) >= 3:
        mode = _OUT_MAP.get(mo.group(1).lower())
        line = mo.group(2)
    chunks = [line]
    if one_per_line and re.search(r"[,|]", line):
        pieces = split_items(line.replace(" | ", " ")) if "," in line or ";" in line else [line.replace(" | ", " ")]
        def _res(c):
            c = re.sub(r"^(?:ED|EA|RD|REA|SCEA|ED2|EA2)" + chr(92) + r"s*:?" + chr(92) + "s*", "", re.sub(r"\([^)]*\)", " ", c).strip(" ."))
            return resolve_phrase(c)
        chunks = [pieces[0]] + [c for c in pieces[1:] if _res(c) is not None and _res(pieces[0]) is not None]
        line = " ".join(chunks)
    # a line with several comma-separated names
    elif "," in line or ";" in line:
        chunks = split_items(line)
        if mode is not None and not _OUTCOME_RX.search(line_np) and any(len(re.sub(r"\([^)]*\)", " ", c).split()) > 7 for c in chunks):
            return res
    elif mode is not None and not _OUTCOME_RX.search(line_np) and (words > 12 or (words > 8 and re.search(
            r"\b(i|my|me|we|is|was|are|were|the|this|that|it|because|but)\b", line_np, re.I))) \
            and resolve_phrase(re.split(r"\s[-–—:]\s", line_np.strip(" -*"))[0]) is None:
        return res
    # "Harvard, Yale, MIT - rejected": trailing outcome applies to the list
    trailing = None
    mt = re.search(r"\s[-:\u2013\u2014]\s*(accepted|admitted|rejected|denied|waitlisted|waitlist|deferred)\b[^,]*$", line, re.I)
    if mt and len(chunks) > 1:
        trailing = _OUT_MAP.get(mt.group(1).lower())
    for ch in chunks:
        pi = parse_item(ch, mode)
        if pi is None:
            continue
        text, outcome, rnd = pi
        if re.search(r"\b(programs?|scholars?|honors)\b", text, re.I) and resolve_phrase(text) is None:
            continue
        if outcome is None and trailing:
            outcome = trailing
        if outcome == "deferred":
            stats["deferred_only"] += 1
            continue
        if outcome is None and mode is None:
            if words > 6:
                continue
            stats["no_outcome"] += 1
            continue
        if outcome is None:
            continue
        res.append((text, outcome, rnd))
    return res


# ---------------------------------------------------------------- one post -> record
def post_year_of(ts: str):
    try:
        d = datetime.fromtimestamp(int(ts), timezone.utc)
        return d.year, d.month
    except (ValueError, OverflowError, OSError):
        return None, None


def parse_post(title: str, body: str, ts: str, stats: Counter):
    """Return (record dict, [decision dicts]) or (None, reason)."""
    raw = body or ""
    if len(raw) < 250:
        return None, "too_short"
    rid = "R-" + hashlib.sha256(raw.encode("utf-8", "replace")).hexdigest()[:12]
    t = clean_text(raw)
    title_c = clean_text(title or "")
    if re.search(r"\btransfer\b", title_c, re.I) and re.search(r"\btransfer\b", t[:600], re.I):
        return None, "transfer_applicant"
    fields, pre = sectionize(t)
    keys = Counter(k for k, _l, _v, _b in fields)
    template_hits = sum(1 for k in ("major", "ec", "awards", "essays", "gpa", "test", "acc", "rej", "wl", "dec", "interviews", "lor")
                        if keys.get(k))
    if template_hits < 3:
        return None, "not_template_post"
    dec_raw = parse_decisions(fields, pre, stats)
    if not dec_raw:
        return None, "no_decisions_found"

    year, month = post_year_of(ts)
    app_year = None
    if year:
        app_year = year if (month or 1) <= 8 else year + 1

    # academics
    test_lines = gather(fields, "test")
    test_text = "\n".join(test_lines)
    acad_lines = gather(fields, "gpa", "rank", "academics", "courses")
    if not test_text:
        test_text = "\n".join(l for l in pre + [l for k, lb, v, _b in fields if k in ("academics", "demographics")
                                                  for l in v] if re.search(r"\b(SAT|ACT)\b", l))[:600]
    sat, sup = extract_sat(test_text, year)
    act = extract_act(test_text)
    gpa_text = "\n".join(gather(fields, "gpa", "academics"))
    if not re.search(r"gpa|uw|weighted|\d\.\d", gpa_text, re.I):
        gpa_text = "\n".join(l for l in pre if re.search(r"\bgpa\b", l, re.I))
    uw, w, un, scale = extract_gpa(gpa_text)
    rank_text = "\n".join(gather(fields, "rank")) or "\n".join(l for l in gpa_text.split("\n") if re.search(r"rank|percentile|top ", l, re.I))
    rank_pct, rank_raw = extract_rank(rank_text)
    ap = extract_ap_count("\n".join(l for l in gather(fields, "courses", "academics", "gpa")
                                    if not re.match(r"\s*(?:senior year|ap scores?|ap exam|ap/ib scores?|aps?: )", l, re.I)))

    mtext, mgroup = extract_major(field_body(fields, "major") or "")
    if not mtext:
        mm = re.search(r"(?im)^[^\n]*\bintended major\(?s?\)?[^:\n]*:\s*(.+)$", t)
        if mm:
            mtext, mgroup = extract_major(mm.group(1))

    res_text = field_body(fields, "residence")
    state = extract_state(res_text)
    if not state:
        demo_unl = "\n".join(l for k, lb, v, _b in fields if k == "demographics" for l in v)
        m = _STATE_NAMES_RX.search(demo_unl + "\n" + "\n".join(pre[:2]))
        if m and not _NON_US.search(demo_unl):
            state = US_STATES[m.group(1).lower()]
    school_text = field_body(fields, "school")
    stype = extract_school_type(school_text)
    if not stype:
        stype = extract_school_type(" ".join(l for k, lb, v, _b in fields if k == "demographics" for l in v) + " "
                                    + " ".join(pre[:3]))

    hooks_src = "\n".join(field_body(fields, "hooks").split("\n") + [title_c]
                          + [l for k, lb, v, _b in fields if k == "demographics" for l in v]
                          + field_body(fields, "income").split("\n") + pre[:3])
    hk = extract_hooks(hooks_src)

    # activities
    ec_body = field_body(fields, "ec")
    act_summary = ""
    act_tags = []
    if ec_body:
        flat = re.sub(r"\s+", " ", " ; ".join(l for l in ec_body.split("\n") if l.strip()))
        flat = re.sub(r"\s*;\s*;\s*", " ; ", flat).lstrip("*-\u2022> ;")
        scrubbed, nscrub = scrub_free_text(flat)
        stats["scrubbed_words"] += nscrub
        cut = scrubbed[:300].rsplit(" ", 1)[0] if len(scrubbed) > 300 else scrubbed
        cut = cut.strip(" ;")
        if _privacy.looks_personal(cut) or re.search(r"high school|\bHS\b|academy|\bprep\b", cut, re.I) \
                or _privacy.looks_personal(flat[:400]):
            stats["activities_dropped_personal"] += 1
        elif len(cut) >= 8:
            act_summary = cut
            act_tags = tag_list(ec_body, _ACT_RX)

    # essay
    ess_body = field_body(fields, "essays")
    ess_labels = " ".join(lb for k, lb, v, _b in fields if k == "essays")
    ess_topic = ""
    ess_themes = []
    rating = ""
    if ess_body or re.search(r"/\s*10", ess_labels):
        flat = re.sub(r"\s+", " ", ess_body.replace("\n", " ")).strip()
        flat = re.split(r"(?:Decisions?|Acceptances?|Results)\s*[:(]", flat, 1, flags=re.I)[0]
        rm = re.search(r"(?<![\d.])(\d{1,2}(?:\.\d)?)\s*(?:/|out of)\s*10\b", ess_labels + " " + flat)
        if rm and float(rm.group(1)) <= 10:
            rating = rm.group(1)
        topic = re.sub(r"(?<![\d.])\d{1,2}(?:\.\d)?\s*(?:/|out of)\s*10\b", "", flat)
        topic = re.sub(r"\(?\s*briefly (?:reflect|rate|describe)[^)]*\)?:?", "", topic, flags=re.I)
        topic = re.sub(r"^[\s*\-\u2022>]+", "", topic)
        topic = re.sub(r"\s+", " ", topic).strip(" -:;,.")
        if len(topic) >= 15:
            scrubbed, nscrub = scrub_free_text(topic)
            stats["scrubbed_words"] += nscrub
            cut = scrubbed[:240].rsplit(" ", 1)[0] if len(scrubbed) > 240 else scrubbed
            if _privacy.looks_personal(cut) or _privacy.looks_personal(topic[:400]) or \
                    re.search(r"high school|\bHS\b|academy|\bprep\b", cut, re.I):
                stats["essay_dropped_personal"] += 1
            else:
                ess_topic = cut.strip()
                ess_themes = tag_list(topic, _ESS_RX)

    # decisions
    decisions = []
    seen = set()
    for text, outcome, rnd in dec_raw:
        c = resolve_phrase(text)
        key = (c["id"] if c else _NORM(text), outcome)
        if key in seen:
            continue
        seen.add(key)
        decisions.append({
            "record_id": rid, "college_as_written": text[:55], "college_id": c["id"] if c else "",
            "college_name": c["name"] if c else "", "case_name": (_colleges.case_name_for(c) or "") if c else "",
            "outcome": outcome, "round": rnd, "source_note": SOURCE_NOTE,
        })
    # An admitted/denied pair for one college inside one post is a waitlist or defer that resolved: keep the latest.
    if any(d["college_id"] for d in decisions) is False and not decisions:
        return None, "no_decisions_found"

    rec = {
        "record_id": rid, "post_year": year or "", "application_year": app_year or "",
        "sat_total": sat or "", "sat_superscore": "Y" if (sat and sup) else "", "act_composite": act or "",
        "gpa_unweighted": uw or "", "gpa_weighted": w or "", "gpa_unlabeled": un or "", "gpa_scale": scale or "",
        "class_rank_top_pct": rank_pct if rank_pct is not None else "", "class_rank_raw": rank_raw,
        "ap_ib_count": ap or "", "major_text": mtext, "major_group": mgroup or "", "home_state": state,
        "school_type": stype, "hook_first_gen": "Y" if hk["first_gen"] else "", "hook_legacy": "Y" if hk["legacy"] else "",
        "hook_recruited_athlete": "Y" if hk["recruited_athlete"] else "", "hook_low_income": "Y" if hk["low_income"] else "",
        "hooks": ";".join(n for n, k in (("FIRST-GEN", "first_gen"), ("LEGACY", "legacy"), ("ATHLETE", "recruited_athlete"),
                                           ("LOW-INCOME", "low_income")) if hk[k]),
        "activities_summary": act_summary, "activities_tags": ";".join(act_tags) if act_summary else "",
        "essay_topic": ess_topic, "essay_themes": ";".join(ess_themes) if ess_topic else "",
        "essay_self_rating": rating, "n_decisions": len(decisions),
        "n_mapped_decisions": sum(1 for d in decisions if d["college_id"]), "source_note": SOURCE_NOTE,
    }
    return rec, decisions


# ---------------------------------------------------------------- batch run
def read_raw(path: Path):
    with open(path, encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))
    return rows[1:]


def run(raw_path: Path, out_dir: Path, seed: int = 11):
    if not raw_path.exists():
        import urllib.request
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(RAW_URL, str(raw_path))  # the single permitted download
    rows = read_raw(raw_path)
    stats = Counter()
    dropped = Counter()
    records, decisions, raws = [], [], {}
    seen_ids = set()
    for upv, ts, title, body, _link in rows:
        rec, dec = parse_post(title, body, ts, stats)
        if rec is None:
            dropped[dec] += 1
            continue
        if rec["record_id"] in seen_ids:
            dropped["duplicate_text"] += 1
            continue
        has_info = any(rec[k] for k in ("sat_total", "act_composite", "gpa_unweighted", "gpa_weighted", "gpa_unlabeled",
                                        "major_text", "activities_summary", "essay_topic"))
        if not has_info:
            dropped["no_profile_fields"] += 1
            continue
        seen_ids.add(rec["record_id"])
        records.append(rec)
        decisions.extend(dec)
        raws[rec["record_id"]] = (title, body)
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "applicants.csv", "w", encoding="utf-8", newline="") as fh:
        fh.write("# " + SOURCE_NOTE + ". Activities and essay fields are the applicant's own short self-description of"
                 " what they did or wrote about; they are never essay text. Usernames, links and names removed.\n")
        w = csv.DictWriter(fh, fieldnames=APPLICANT_FIELDS)
        w.writeheader()
        w.writerows(records)
    with open(out_dir / "decisions.csv", "w", encoding="utf-8", newline="") as fh:
        fh.write("# " + SOURCE_NOTE + ". One row per college decision stated in a post; round is blank when not stated.\n")
        w = csv.DictWriter(fh, fieldnames=DECISION_FIELDS)
        w.writeheader()
        w.writerows(decisions)
    return rows, records, decisions, raws, dropped, stats



# ---------------------------------------------------------------- the report
def _overlap_estimate(records, decisions):
    """Estimate how many parsed records are people already in the 2,247-row national file (an estimate)."""
    from engine import cases as _cases
    base = ROOT / "data" / "cases"
    old = {}
    with open(base / "applicants_wide.csv", encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            sat = None if r["SAT"] in ("-1", "") else int(float(r["SAT"]))
            act = None if r["ACT"] in ("-1", "") else int(float(r["ACT"]))
            old[r["applicant_id"]] = [sat, act, _cases._case_major_group(r["Major"]), set()]
    with open(base / "decisions_long.csv", encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            out = _cases._OUTCOME_WORD.get(r["outcome"].strip().lower())
            if r["applicant_id"] in old and out:
                old[r["applicant_id"]][3].add((r["college"], out))
    short_names = {c for v in old.values() for c, _o in v[3]}
    by_rec = {}
    for d in decisions:
        if d["case_name"] and d["case_name"] in short_names:
            by_rec.setdefault(d["record_id"], set()).add((d["case_name"], d["outcome"]))
    index = {}
    for aid, (sat, act, grp, decs) in old.items():
        index.setdefault((sat, act), []).append((grp, frozenset(decs)))
    strict = loose = comparable = 0
    for r in records:
        sat = int(r["sat_total"]) if r["sat_total"] != "" else None
        act = int(r["act_composite"]) if r["act_composite"] != "" else None
        decs = by_rec.get(r["record_id"], set())
        if (sat is None and act is None) or not decs:
            continue
        comparable += 1
        grp = r["major_group"] or None
        cands = index.get((sat, act), [])
        if any(g == grp and d == frozenset(decs) for g, d in cands):
            strict += 1
        if any(g == grp and len(d & decs) / max(1, len(d | decs)) >= 0.7 and len(decs) >= 3 for g, d in cands):
            loose += 1
    return {"existing": len(old), "comparable": comparable, "strict": strict, "loose": loose}


def write_report(rows, records, decisions, raws, dropped, stats, out_dir: Path, hand_check: str = ""):
    n = len(records)
    L = []
    L.append("# PARSE_REPORT: r/collegeresults posts parsed into applicant records and decisions\n")
    L.append("Every value below is **" + SOURCE_NOTE + "**. Activities summaries and essay topics are the applicant's own short "
             "description (first 300 / 240 characters), never essay text. Usernames, links, e-mails, people's names and "
             "high-school names are removed; a field that `engine.privacy.looks_personal` flags is dropped for that "
             "record. Race and gender lines are skipped and those words are scrubbed from stored free text. Record ids are a "
             "hash of the post text. Source: public GitHub file `shreybirmiwal/college-predictor` "
             "`1-DataPrep/3-extract-values/in-cleaned.csv` (raw text of 2015-2024 posts). Built by `tools/parse_reddit_posts.py`.\n")
    L.append("## 1. Posts read, kept, dropped\n")
    L.append("- Posts read: **%d**" % len(rows))
    L.append("- Records kept: **%d**" % n)
    why = {"too_short": "body under 250 characters (a question or a one-liner, no profile)",
           "not_template_post": "fewer than 3 recognised template headings (Major, Activities, Essays, GPA, Decisions ...)",
           "no_decisions_found": "template heading found but no parseable college decision",
           "transfer_applicant": "transfer applicant (college GPA, different pool)",
           "duplicate_text": "same post text seen before", "no_profile_fields": "decisions found but no score, GPA, major, activities or essay field"}
    L.append("- Records dropped: **%d**" % sum(dropped.values()))
    for k, v in dropped.most_common():
        L.append("  - %s: %d (%s)" % (k, v, why.get(k, "")))
    L.append("- Items skipped inside kept records: %d deferred-only entries (no final outcome, not counted); %d list items with "
             "no outcome that could be told; activities summary dropped as personal in %d records; essay topic dropped as "
             "personal in %d records; %d race/gender words scrubbed from stored text."
             % (stats["deferred_only"], stats["no_outcome"], stats["activities_dropped_personal"],
                stats["essay_dropped_personal"], stats["scrubbed_words"]))
    L.append("")
    L.append("## 2. Fill rate of every field (share of the %d records with a value)\n" % n)
    L.append("| field | records | share |\n|---|---|---|")
    for f in APPLICANT_FIELDS:
        if f == "n_mapped_decisions":
            c = sum(1 for r in records if int(r[f]) > 0)
        else:
            c = sum(1 for r in records if str(r[f]) != "")
        L.append("| %s | %d | %.1f%% |" % (f, c, 100.0 * c / max(1, n)))
    L.append("")
    L.append("Notes: `gpa_unlabeled` is a GPA the post gave without saying weighted or unweighted. `sat_total` for a range is the "
             "midpoint; 'a -> b' retakes take the higher; 2400-scale scores are left empty. `class_rank_top_pct` is 100 x rank / "
             "class size, or the stated top-percent.\n")
    L.append("## 3. Decisions and colleges\n")
    mapped = [d for d in decisions if d["college_id"]]
    oc = Counter(d["outcome"] for d in decisions)
    L.append("- Decisions parsed: **%d** (mapped to a Scorecard college: %d = %.1f%%)" % (len(decisions), len(mapped), 100.0 * len(mapped) / max(1, len(decisions))))
    L.append("- Outcomes: admitted **%d**, denied **%d**, waitlisted **%d**" % (oc["admitted"], oc["denied"], oc["waitlisted"]))
    L.append("- Rounds stated: " + ", ".join("%s %d" % (k or "not stated", v) for k, v in Counter(d["round"] for d in decisions).most_common()))
    distinct = {d["college_id"] for d in mapped}
    with_case = {d["case_name"] for d in mapped if d["case_name"]}
    L.append("- Distinct mapped colleges: **%d** (today's national pool has 58; %d of the 58 case-file names appear here)" % (len(distinct), len(with_case)))
    L.append("- Colleges with at least 30 decisions: %d; at least 15: %d" % (
        sum(1 for v in Counter(d["college_id"] for d in mapped).values() if v >= 30),
        sum(1 for v in Counter(d["college_id"] for d in mapped).values() if v >= 15)))
    L.append("\n### Top 40 colleges by decisions\n")
    L.append("| # | college | decisions | admitted | denied | waitlisted |\n|---|---|---|---|---|---|")
    per = {}
    for d in mapped:
        e = per.setdefault(d["college_name"], Counter())
        e[d["outcome"]] += 1
        e["n"] += 1
    for i, (name, e) in enumerate(sorted(per.items(), key=lambda kv: -kv[1]["n"])[:40], 1):
        L.append("| %d | %s | %d | %d | %d | %d |" % (i, name, e["n"], e["admitted"], e["denied"], e["waitlisted"]))
    un = Counter(_NORM(d["college_as_written"]) for d in decisions if not d["college_id"])
    L.append("\n### Top 30 unmapped college strings (candidates for COLLEGE_ALIASES in this tool; many are non-US schools not in the Scorecard file)\n")
    L.append("| # | string (normalised) | count |\n|---|---|---|")
    for i, (k, v) in enumerate(un.most_common(30), 1):
        L.append("| %d | %s | %d |" % (i, k or "(empty)", v))
    L.append("\n- Distinct unmapped strings: %d (%d decisions). Alias entries dropped at start-up because the target name is not in the Scorecard file: %s"
             % (len(un), sum(un.values()), ", ".join(_ALIAS_DROPPED) or "none"))
    L.append("")
    L.append("## 4. Overlap with the existing 2,247-applicant national file (ESTIMATE)\n")
    ov = _overlap_estimate(records, decisions)
    L.append("The existing file has no post id, so identity cannot be checked. Match rule: same SAT and ACT, same major group, and the same set of "
             "(college, outcome) pairs over the colleges the old file covers. %d parsed records have a score and at least one decision at those colleges. "
             "Strict match (all four equal): **%d** records. Looser match (same SAT/ACT/major group, at least 3 shared decisions, decision-set overlap "
             ">= 70%%): **%d**. So roughly **%d to %d records (%.0f%% to %.0f%% of those comparable, %.0f%% to %.0f%% of all kept)** probably describe someone already in the old file. "
             "This is an estimate: the old file's ACT column is noisy, its colleges are only 58, and two different people can share a profile."
             % (ov["comparable"], ov["strict"], ov["loose"], ov["strict"], ov["loose"], 100.0 * ov["strict"] / max(1, ov["comparable"]),
                100.0 * ov["loose"] / max(1, ov["comparable"]), 100.0 * ov["strict"] / max(1, n), 100.0 * ov["loose"] / max(1, n)))
    L.append("")
    L.append("## 5. Ten random parsed records beside the first 400 characters of the raw post\n")
    L.append("(Raw text is shown after link/username cleaning and `engine.privacy.mask`. Seed 2026.)\n")
    rnd = random.Random(2026)
    by_rec = {}
    for d in decisions:
        by_rec.setdefault(d["record_id"], []).append(d)
    for r in rnd.sample(records, min(10, n)):
        title, body = raws[r["record_id"]]
        raw400 = _privacy.mask(clean_text(body)[:400])["text"].replace("\n", " / ")
        L.append("### " + r["record_id"])
        L.append("RAW (first 400 chars): " + raw400 + "\n")
        L.append("PARSED:")
        for k in APPLICANT_FIELDS:
            if k not in ("record_id", "source_note") and str(r[k]) != "":
                L.append("- %s: %s" % (k, r[k]))
        L.append("- decisions: " + "; ".join("%s -> %s%s [%s]" % (d["college_as_written"], d["outcome"], (" " + d["round"]) if d["round"] else "",
                                                                  d["college_name"] or "UNMAPPED") for d in by_rec.get(r["record_id"], [])))
        L.append("")
    L.append("## 6. Hand check of thirty records\n")
    L.append(hand_check.strip() if hand_check.strip() else "(not yet filled: see hand_check.md in this folder)")
    L.append("")
    (out_dir / "PARSE_REPORT.md").write_text("\n".join(L), encoding="utf-8")


def read_parsed(path: Path) -> list:
    """Read a parsed CSV written by run() (skips the leading '#' comment line)."""
    with open(path, encoding="utf-8", newline="") as fh:
        lines = [l for l in fh if not l.startswith("#")]
    return list(csv.DictReader(lines))


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    raw = Path(argv[0]) if argv else RAW_DEFAULT
    out = Path(argv[1]) if len(argv) > 1 else OUT_DEFAULT
    rows, records, decisions, raws, dropped, stats = run(raw, out)
    hc = out / "hand_check.md"
    write_report(rows, records, decisions, raws, dropped, stats, out, hc.read_text(encoding="utf-8") if hc.exists() else "")
    print("posts read", len(rows), "records kept", len(records), "decisions", len(decisions))
    print("dropped", dict(dropped))
    print("stats", dict(stats))
    return rows, records, decisions, raws, dropped, stats


if __name__ == "__main__":
    main()
