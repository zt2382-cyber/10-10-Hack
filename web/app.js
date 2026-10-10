
/* Counselor Copilot: the one screen, told as a story in four chapters.
   1 Who you are -> 2 Where you stand -> 3 What is in your hands -> 4 Your plan.
   Part 1: pure helpers that take data and return HTML or SVG strings (no DOM; testable in Node).
   Part 2: the page wiring (runs only in a browser).
   Two views: the meeting view (default) and "Show the working" (body.show-working reveals .working-only).
   Every piece of data goes through esc() before it reaches HTML. */
(function (root) {
'use strict';

/* A copy of docs/fixture_result.json, used only when nothing else can be loaded. */
var FIXTURE = /*FIXTURE_START*/{"run_id":"fixture-0001","generated_at":"2026-10-10T12:30:00-04:00","synthetic":true,"student":{"label":"Student A (SYNTHETIC)","sat":1450,"act":null,"gpa":3.9,"gpa_scale":4.0,"home_state":"NJ","intended_major":"Computer Science","hooks":["first_gen"],"activities":[{"type":"Research","role":"Student researcher","description":"Summer lab program; co-author on a poster"}],"essay_words":612,"college_list":["Cornell University","Purdue University-Main Campus","Rutgers University-New Brunswick","Kenyon College","Some College Not In Our File"]},"steps":[{"step":"retrieve","what":"Looked up 5 colleges and 2,250 finished cases","ms":14,"by":"code"},{"step":"score","what":"Compared the student's SAT of 1450 with each college's published range","ms":2,"by":"code"},{"step":"bucket","what":"Labelled 4 colleges; 1 is outside our data","ms":1,"by":"code"},{"step":"explain","what":"Read the essay for themes and quotes; 3 notes kept, 1 dropped","ms":1840,"by":"anthropic/claude-haiku-4-5"},{"step":"log","what":"Recorded this run in PRISM","ms":220,"by":"code"}],"privacy":{"masked":[{"kind":"name","count":2},{"kind":"email","count":1}],"blocked":false,"reason":"","guard":"local, then PRISM","note":"3 personal details were masked before any model read the essay."},"reader":{"status":"ok","model":"anthropic/claude-haiku-4-5","second_model":"openai/gpt-5.5","tags":{"major_group":"CS","major_group_agreed":true,"activity_types":["research"],"essay_themes":["family","persistence"]},"notes":[{"observation":"The essay centres on translating for a parent at medical appointments.","quote":"I learned the word for kidney before I learned to drive","question":"Does the rest of the application show this responsibility anywhere else?","quote_found":true},{"observation":"It names a specific research task rather than a general interest in science.","quote":"I ran the same assay eleven times before it worked","question":"Can the research mentor's letter confirm this?","quote_found":true}],"dropped":1,"latency_ms":1840},"colleges":[{"id":"190415","name":"Cornell University","state":"NY","control":"private","admit_rate":0.0876,"sat25":1500,"sat75":1570,"act25":33,"act75":35,"cost_year":88140,"source":"US Department of Education, College Scorecard","in_data":true,"label":{"state":"reach_for_everyone","text":"Reach for everyone","rule_id":"R1","rule_text":"This college admits fewer than 15 in 100 applicants, so it is a reach for any student.","score_used":1450,"score_kind":"SAT","inputs":{"sat25":1500,"sat75":1570,"admit_rate":0.0876},"not_used":["GPA","activities","essay"],"caveats":["The score range covers only students who sent scores."],"steady":true,"flips":[],"publishers":[{"name":"BigFuture","label":"reach"},{"name":"Princeton Review","label":"reach"},{"name":"Scoir","label":"reach"},{"name":"Appily","label":"reach"},{"name":"CollegeVine","label":"reach"}],"publishers_disagree":false},"cases":{"needed":15,"own":{"source":"Your school's own finished cases (SYNTHETIC demo data)","verified":true,"status":"not_enough","n":4,"admitted":1,"denied":3,"waitlisted":0,"matched_on":["SAT within 100 points"],"relaxed":["hook status","major group","SAT widened to 100"],"examples":[{"case_id":"S-12","sat":1480,"act":null,"major":"CS","hooks":"first_gen","home_state":"NJ","activities_note":"Robotics captain; state finalist","essay_theme":"immigrant family","outcome":"denied","cycle_year":2025}]},"national":{"source":"Self-reported public posts (r/collegeresults)","verified":false,"status":"ok","n":23,"admitted":8,"denied":12,"waitlisted":3,"matched_on":["SAT within 50 points","same major group"],"relaxed":["hook status"],"examples":[{"case_id":"N-1042","sat":1460,"act":null,"major":"CS","hooks":"NONE","home_state":"CA","activities_rating":6.5,"outcome":"denied"},{"case_id":"N-377","sat":1440,"act":null,"major":"CS","hooks":"FIRST-GEN","home_state":"NY","activities_rating":7.5,"outcome":"admitted"},{"case_id":"N-1611","sat":1470,"act":null,"major":"CS","hooks":"NONE","home_state":"TX","activities_rating":5.5,"outcome":"waitlisted"}]},"official_admit_rate":0.0876,"pool_admit_share_all":0.251,"overcount":2.9,"caveat":"People who post their results are admitted far more often than applicants overall. Read these as examples, not odds."},"closeness":{"semantic":{"status":"off"},"essay_retrieval":[],"weights":{"score":0.45,"activities":0.2,"major":0.15,"hooks":0.1,"residency":0.1,"gpa":0.2,"essay":0.2,"activity_text":0.15},"needed":15,"neighbours":7,"student":{"score":1450,"converted":false,"activities":5.0,"activities_from":"estimated","activities_why":["1 activity listed","recognition beyond the school"],"activities_rule":"4 for one activity, +1 for each further activity up to 4, +1 for a leading role, +1 for recognition beyond the school, +1 for sustained commitment (years, or weekly hours); never over 10."},"national":{"source":"Public posts on Reddit (r/collegeresults), self-reported","verified":false,"status":"ok","n_admitted":206,"n_denied":440,"n_waitlisted":138,"groups":{"status":"ok","reason":"","sat25":1500,"sat75":1570,"act_mid":6,"act_high":8,"min_n":5,"few_n":15,"left_out":96,"capped":false,"student_note":"","cells":[{"score_band":"below","activities_band":"high","admitted":4,"waitlisted":2,"denied":10,"n":16,"state":"ok","is_student":false,"cases":[["N-1537",1450,8.5,"d","BUSINESS","NONE"],["N-2100",1450,8.5,"w","OTHER","NONE"],["N-1373",1460,8.5,"d","BUSINESS","FIRST-GEN"],["N-1477",1440,8.5,"d","CS","NONE"],["N-762",1430,8.5,"a","CS","NONE"],["N-1211",1470,8.5,"d","CS","NONE"],["N-1460",1430,8.5,"d","BIO","LGBT"],["N-191",1480,8.2,"w","CS","NONE"],["N-962",1480,8.5,"d","CS","FIRST-GEN"],["N-705",1490,8.5,"a","CS","URM"],["N-724",1490,8.5,"d","ARTS","NONE"],["N-125",1390,8.5,"a","ENG","FIRST-GEN"],["N-2209",1340,8.5,"d","CS","LEGACY"],["N-517",1310,8.5,"d","CS","NONE"],["N-970",1310,8.5,"d","CS","NONE"],["N-1724",1230,8.5,"a","BIO","FIRST-GEN"]]},{"score_band":"inside","activities_band":"high","admitted":9,"waitlisted":15,"denied":30,"n":54,"state":"ok","is_student":false,"cases":[["N-737",1500,8.5,"d","CS","NONE"],["N-786",1500,8.5,"d","CS","NONE"],["N-1374",1500,8.5,"d","BIO","NONE"],["N-1415",1500,8.5,"w","CS","NONE"],["N-1481",1500,8.5,"d","ENG","NONE"],["N-1631",1500,8.5,"d","CS","LEGACY"],["N-2019",1500,8.5,"a","CS","NONE"],["N-2188",1510,8.5,"d","CS","LEGACY"],["N-1801",1520,8.5,"d","CS","NONE"],["N-1922",1520,8.5,"d","CS","NONE"],["N-602",1530,8.5,"d","CS","NONE"],["N-913",1530,8.5,"d","CS","NONE"],["N-1441",1530,8.5,"w","CS","NONE"],["N-1796",1530,8.5,"d","CS","FIRST-GEN"],["N-1884",1530,8.5,"d","CS","NONE"],["N-44",1540,8.5,"a","CS","NONE"],["N-62",1540,8.5,"d","CS","NONE"],["N-254",1540,8.5,"d","CS","NONE"],["N-268",1540,8.5,"w","BUSINESS","NONE"],["N-367",1540,8.5,"w","CS","NONE"],["N-1222",1540,8.5,"d","ENG","NONE"],["N-1334",1540,8.5,"d","ENG","NONE"],["N-1470",1540,8.5,"d","CS","NONE"],["N-1555",1540,8.5,"a","CS","NONE"],["N-1861",1540,8.5,"d","CS","NONE"],["N-370",1550,8.5,"w","CS","NONE"],["N-389",1550,9.5,"w","ENG","LEGACY"],["N-433",1550,8.5,"w","BIO","NONE"],["N-1186",1550,8.5,"d","CS","NONE"],["N-1355",1550,8.5,"d","CS","NONE"],["N-1433",1550,8.5,"d","ENG","LEGACY"],["N-1566",1550,8.5,"w","CS","LEGACY"],["N-2068",1550,8.5,"a","CS","NONE"],["N-1044",1560,8.5,"a","BIO","NONE"],["N-1233",1560,8.5,"d","CS","NONE"],["N-1287",1560,9.5,"d","","NONE"],["N-1299",1560,8.5,"w","CS","NONE"],["N-1372",1560,8.5,"d","CS","NONE"],["N-1443",1560,8.5,"w","","NONE"],["N-1959",1560,8.5,"w","CS","NONE"],["N-2120",1560,8.5,"d","CS","NONE"],["N-2244",1560,8.5,"w","CS","NONE"],["N-42",1570,8.5,"d","CS","NONE"],["N-213",1570,8.5,"d","BUSINESS","NONE"],["N-282",1570,8.5,"a","CS","NONE"],["N-407",1570,8.5,"d","BIO","NONE"],["N-1376",1570,8.5,"w","MATH","NONE"],["N-1505",1570,8.5,"a","HUMANITIES","NONE"],["N-1559",1570,8.5,"d","CS","NONE"],["N-1721",1570,8.5,"a","CS","NONE"],["N-1722",1570,8.5,"a","CS","NONE"],["N-1932",1570,8.5,"w","CS","NONE"],["N-1933",1570,8.5,"w","CS","NONE"],["N-2174",1570,8.5,"d","CS","NONE"]]},{"score_band":"above","activities_band":"high","admitted":7,"waitlisted":6,"denied":13,"n":26,"state":"ok","is_student":false,"cases":[["N-835",1580,8.5,"a","CS","LEGACY"],["N-1035",1580,8.5,"w","","NONE"],["N-1295",1580,8.5,"d","CS","NONE"],["N-1424",1580,8.5,"a","BIO","NONE"],["N-1485",1580,8.5,"a","CS","NONE"],["N-1519",1580,8.5,"d","CS","NONE"],["N-1600",1580,8.5,"d","CS","NONE"],["N-1767",1580,8.5,"a","","URM"],["N-2178",1580,8.5,"a","CS","LEGACY"],["N-138",1590,8.5,"d","POLISCI","NONE"],["N-393",1590,8.5,"w","BIO","NONE"],["N-721",1590,8.5,"a","CS","FIRST-GEN"],["N-722",1590,8.5,"d","BIO","NONE"],["N-734",1590,9.5,"d","CS","NONE"],["N-758",1590,8.5,"d","ENG","NONE"],["N-1010",1590,8.5,"d","CS","NONE"],["N-1146",1590,8.5,"d","CS","NONE"],["N-1365",1590,8.5,"w","ENG","LEGACY"],["N-1382",1590,8.5,"w","CS","NONE"],["N-2037",1590,8.5,"a","CS","NONE"],["N-2192",1590,8.5,"w","PSYCH","NONE"],["N-261",1600,8.5,"w","CS","NONE"],["N-573",1600,8.5,"d","CS","NONE"],["N-911",1600,8.5,"d","CS","NONE"],["N-1727",1600,8.5,"d","BUSINESS","NONE"],["N-2177",1600,10.0,"d","CS","NONE"]]},{"score_band":"below","activities_band":"mid","admitted":26,"waitlisted":11,"denied":52,"n":89,"state":"ok","is_student":false,"cases":[["N-114",1450,6.5,"a","","URM"],["N-189",1450,6.5,"d","ENG","LEGACY"],["N-402",1450,6.5,"d","POLISCI","NONE"],["N-919",1450,6.5,"a","","URM"],["N-87",1460,7.5,"w","PSYCH","FIRST-GEN"],["N-123",1460,6.5,"d","ENG","FIRST-GEN"],["N-166",1440,7.5,"a","CS","NONE"],["N-194",1460,6.5,"a","","NONE"],["N-331",1440,7.5,"d","ENG","NONE"],["N-472",1460,6.5,"d","ENG","FIRST-GEN"],["N-533",1460,6.5,"d","POLISCI","NONE"],["N-1466",1440,6.5,"d","CS","NONE"],["N-1475",1460,6.5,"w","","NONE"],["N-1484",1460,6.5,"a","BIO","NONE"],["N-2127",1460,7.5,"d","CS","FIRST-GEN"],["N-2144",1460,6.5,"d","CS","NONE"],["N-2156",1460,7.5,"w","CS","FIRST-GEN"],["N-2186",1440,7.5,"d","","URM"],["N-2211",1440,6.5,"a","","NONE"],["N-225",1470,6.5,"d","POLISCI","URM"],["N-272",1430,6.5,"d","ENG","NONE"],["N-417",1430,6.5,"w","ENG","LEGACY"],["N-419",1470,6.5,"d","HUMANITIES","NONE"],["N-537",1430,6.0,"d","CS","FIRST-GEN"],["N-671",1470,7.5,"d","CS","LEGACY"],["N-678",1430,6.0,"d","CS","FIRST-GEN"],["N-777",1470,6.5,"a","CS","NONE"],["N-831",1470,6.5,"d","CS","LEGACY"],["N-834",1470,7.5,"w","CS","NONE"],["N-989",1470,7.5,"w","CS","NONE"],["N-1047",1470,6.5,"d","CS","LEGACY"],["N-1058",1470,7.5,"d","CS","URM"],["N-1061",1430,7.0,"a","ENG","FIRST-GEN"],["N-1360",1470,6.5,"d","CS","NONE"],["N-1377",1430,6.5,"a","CS","URM"],["N-1399",1430,7.5,"w","CS","NONE"],["N-1680",1470,6.5,"a","BIO","NONE"],["N-2092",1470,6.5,"d","CS","NONE"],["N-692",1480,6.5,"d","POLISCI","LEGACY"],["N-702",1480,6.5,"w","PREMED","NONE"],["N-720",1480,6.5,"d","ENG","NONE"],["N-965",1480,6.5,"w","CS","URM"],["N-1304",1420,6.5,"d","POLISCI","FIRST-GEN"],["N-1416",1480,7.5,"d","BUSINESS","NONE"],["N-1457",1420,6.5,"d","ENG","NONE"],["N-1790",1420,7.5,"a","BUSINESS","NONE"],["N-2233",1480,6.5,"d","ENG","NONE"],["N-171",1490,7.5,"d","POLISCI","LEGACY"],["N-968",1490,7.5,"d","","NONE"],["N-1002",1490,6.5,"w","POLISCI","FIRST-GEN"],["N-1003",1410,6.5,"d","CS","LEGACY"],["N-1239",1410,6.5,"a","CS","URM"],["N-1324",1410,6.5,"a","CS","URM"],["N-1337",1490,6.5,"a","CS","URM"],["N-1357",1490,6.5,"a","CS","LEGACY"],["N-1446",1410,7.5,"a","","URM"],["N-1679",1490,7.5,"d","CS","NONE"],["N-1939",1410,6.5,"d","ENG","NONE"],["N-2058",1410,7.5,"a","CS","FIRST-GEN"],["N-2102",1490,7.0,"d","PREMED","NONE"],["N-2134",1410,6.5,"d","","NONE"],["N-303",1400,6.5,"d","CS","URM"],["N-411",1400,6.5,"d","","NONE"],["N-1079",1400,7.5,"a","BUSINESS","NONE"],["N-1608",1400,7.5,"d","POLISCI","URM"],["N-1918",1400,6.5,"d","PSYCH","NONE"],["N-2051",1400,7.5,"a","BIO","FIRST-GEN"],["N-1153",1390,7.5,"a","CS","NONE"],["N-1619",1390,6.5,"d","BUSINESS","NONE"],["N-2110",1380,6.5,"d","ENG","URM"],["N-2111",1380,6.5,"d","ENG","URM"],["N-109",1370,6.5,"a","PREMED","URM"],["N-1501",1370,6.5,"a","CS","URM"],["N-599",1360,6.5,"a","BUSINESS","URM"],["N-1016",1360,6.5,"w","","NONE"],["N-794",1350,6.5,"d","ENG","NONE"],["N-764",1340,7.5,"d","BUSINESS","URM"],["N-1984",1340,6.5,"d","CS","URM"],["N-1989",1340,6.5,"d","CS","URM"],["N-629",1320,7.5,"d","CS","NONE"],["N-770",1320,6.5,"a","","NONE"],["N-1904",1310,6.5,"d","POLISCI","NONE"],["N-475",1300,6.5,"d","POLISCI","NONE"],["N-1549",1300,6.5,"d","CS","LEGACY"],["N-2190",1280,6.5,"a","CS","NONE"],["N-1390",1130,6.5,"d","CS","NONE"],["N-1886",670,7.5,"d","CS","NONE"],["N-46",630,6.5,"a","ENG","NONE"],["N-239",630,6.5,"d","CS","NONE"]]},{"score_band":"inside","activities_band":"mid","admitted":67,"waitlisted":57,"denied":133,"n":257,"state":"ok","is_student":false,"cases":[["N-19",1500,7.5,"d","HUMANITIES","URM"],["N-64",1500,6.5,"d","ENG","LEGACY"],["N-106",1500,6.5,"d","","NONE"],["N-149",1500,6.5,"a","HUMANITIES","URM"],["N-195",1500,6.5,"a","ENG","URM"],["N-324",1500,6.5,"a","POLISCI","NONE"],["N-399",1500,7.5,"d","","LEGACY"],["N-422",1500,7.5,"d","CS","NONE"],["N-456",1500,7.0,"w","ENG","NONE"],["N-557",1500,6.5,"d","","NONE"],["N-580",1500,6.5,"d","CS","NONE"],["N-612",1500,7.5,"a","BIO","NONE"],["N-649",1500,7.5,"d","BIO","NONE"],["N-677",1500,6.5,"d","CS","NONE"],["N-934",1500,7.5,"d","POLISCI","NONE"],["N-938",1500,7.5,"a","","LEGACY"],["N-961",1500,6.5,"w","POLISCI","FIRST-GEN"],["N-991",1500,7.5,"d","CS","NONE"],["N-1237",1500,6.5,"d","CS","NONE"],["N-1335",1500,6.5,"d","CS","NONE"],["N-1368",1500,7.5,"d","","NONE"],["N-1381",1500,7.5,"w","","URM"],["N-1395",1500,7.5,"d","ENG","FIRST-GEN"],["N-1422",1500,7.5,"d","CS","NONE"],["N-1425",1500,6.5,"d","BIO","NONE"],["N-1540",1500,7.5,"d","CS","NONE"],["N-1557",1500,6.5,"a","CS","NONE"],["N-1596",1500,6.5,"d","CS","NONE"],["N-1645",1500,7.5,"d","POLISCI","NONE"],["N-1760",1500,6.5,"d","CS","NONE"],["N-1824",1500,7.5,"d","PREMED","NONE"],["N-1863",1500,6.5,"d","CS","LEGACY"],["N-1911",1500,7.5,"d","CS","NONE"],["N-1913",1500,7.5,"w","BIO","NONE"],["N-1919",1500,7.5,"w","CS","URM"],["N-1987",1500,6.5,"d","CS","LEGACY"],["N-2072",1500,6.5,"a","ENG","FIRST-GEN"],["N-359",1510,6.5,"d","CS","NONE"],["N-415",1510,7.5,"w","CS","NONE"],["N-455",1510,6.5,"d","POLISCI","NONE"],["N-703",1510,7.5,"a","CS","URM"],["N-817",1510,6.5,"w","CS","NONE"],["N-928",1510,7.5,"d","CS","NONE"],["N-959",1510,6.5,"d","","LEGACY"],["N-1022",1510,6.5,"d","","FIRST-GEN"],["N-1370",1510,7.5,"w","CS","NONE"],["N-1420",1510,7.5,"a","CS","NONE"],["N-1434",1510,6.5,"d","CS","NONE"],["N-1452",1510,7.5,"d","CS","NONE"],["N-1503",1510,7.5,"w","CS","NONE"],["N-1754",1510,7.5,"a","CS","LEGACY"],["N-2123",1510,7.5,"d","CS","NONE"],["N-2193",1510,6.5,"a","BUSINESS","NONE"],["N-249",1520,6.5,"a","CS","URM"],["N-280",1520,6.5,"d","BUSINESS","NONE"],["N-312",1520,7.5,"d","CS","NONE"],["N-344",1520,6.5,"w","CS","NONE"],["N-560",1520,6.5,"d","ENG","LEGACY"],["N-661",1520,6.5,"d","PREMED","NONE"],["N-698",1520,6.0,"d","PREMED","FIRST-GEN"],["N-745",1520,7.5,"d","ENG","NONE"],["N-790",1520,6.5,"d","CS","NONE"],["N-839",1520,6.5,"a","ARTS","NONE"],["N-872",1520,7.5,"d","BUSINESS","NONE"],["N-896",1520,6.5,"a","CS","NONE"],["N-1125",1520,7.5,"d","BIO","NONE"],["N-1178",1520,7.5,"d","ENG","NONE"],["N-1258",1520,6.5,"d","CS","NONE"],["N-1323",1520,6.5,"d","CS","NONE"],["N-1384",1520,6.5,"d","CS","NONE"],["N-1450",1520,6.5,"a","POLISCI","NONE"],["N-1467",1520,6.5,"d","ENG","NONE"],["N-1831",1520,6.5,"d","ENG","NONE"],["N-1986",1520,7.5,"d","CS","LEGACY"],["N-1992",1520,7.5,"a","POLISCI","URM"],["N-1994",1520,7.0,"d","CS","LEGACY"],["N-2170",1520,7.5,"d","ENG","NONE"],["N-73",1530,7.5,"a","","NONE"],["N-184",1530,6.5,"d","CS","NONE"],["N-217",1530,6.5,"d","CS","URM"],["N-234",1530,6.5,"w","CS","NONE"],["N-273",1530,7.5,"a","ENG","FIRST-GEN"],["N-371",1530,7.5,"d","CS","URM"],["N-482",1530,6.5,"d","CS","LEGACY"],["N-648",1530,6.5,"d","CS","NONE"],["N-710",1530,6.5,"d","BIO","NONE"],["N-771",1530,6.5,"d","ENG","NONE"],["N-782",1530,7.5,"w","ENG","NONE"],["N-856",1530,6.5,"d","PREMED","NONE"],["N-875",1530,6.5,"a","PSYCH","LEGACY"],["N-926",1530,6.5,"a","ENG","NONE"],["N-1017",1530,6.5,"w","CS","NONE"],["N-1246",1530,7.5,"d","BIO","URM"],["N-1379",1530,7.5,"w","ENG","FIRST-GEN"],["N-1528",1530,6.5,"w","BIO","NONE"],["N-1664",1530,6.5,"d","CS","NONE"],["N-1696",1530,6.5,"d","ENG","LGBT"],["N-1716",1530,6.5,"d","ENG","NONE"],["N-1885",1530,6.5,"d","CS","NONE"],["N-1979",1530,7.5,"d","CS","NONE"],["N-2003",1530,7.5,"a","PREMED","URM"],["N-2052",1530,7.0,"a","CS","NONE"],["N-2086",1530,6.5,"d","CS","NONE"],["N-2094",1530,6.0,"d","CS","LEGACY"],["N-2112",1530,7.5,"w","CS","NONE"],["N-2125",1530,6.5,"d","CS","NONE"],["N-32",1540,6.5,"a","BIO","NONE"],["N-93",1540,6.5,"d","CS","FIRST-GEN"],["N-158",1540,6.5,"d","POLISCI","NONE"],["N-203",1540,6.5,"a","POLISCI","NONE"],["N-208",1540,7.5,"d","BIO","NONE"],["N-209",1540,6.5,"w","BUSINESS","NONE"],["N-260",1540,6.5,"w","BUSINESS","NONE"],["N-267",1540,6.5,"a","ENG","LEGACY"],["N-278",1540,6.5,"a","BIO","NONE"],["N-279",1540,6.5,"d","CS","NONE"],["N-306",1540,6.5,"w","CS","LEGACY"],["N-341",1540,6.5,"d","CS","FIRST-GEN"],["N-427",1540,7.5,"a","ENG","NONE"],["N-447",1540,7.5,"w","","NONE"],["N-510",1540,7.5,"d","CS","LEGACY"],["N-565",1540,6.5,"a","HUMANITIES","URM"],["N-776",1540,6.5,"d","PREMED","NONE"],["N-809",1540,6.5,"d","POLISCI","NONE"],["N-814",1540,6.5,"w","CS","NONE"],["N-869",1540,7.5,"d","CS","NONE"],["N-893",1540,6.5,"w","CS","NONE"],["N-895",1540,7.5,"d","CS","LEGACY"],["N-944",1540,6.5,"d","CS","NONE"],["N-1005",1540,7.5,"a","CS","NONE"],["N-1041",1540,6.5,"a","BUSINESS","FIRST-GEN"],["N-1111",1540,6.5,"d","ENG","NONE"],["N-1163",1540,6.5,"d","ENG","NONE"],["N-1191",1540,6.5,"d","CS","NONE"],["N-1192",1540,6.5,"a","CS","NONE"],["N-1307",1540,6.5,"a","CS","LEGACY"],["N-1316",1540,6.5,"a","PSYCH","NONE"],["N-1327",1540,7.5,"w","CS","NONE"],["N-1328",1540,7.5,"w","CS","NONE"],["N-1387",1540,7.0,"d","CS","NONE"],["N-1393",1540,6.0,"w","ENG","NONE"],["N-1455",1540,6.0,"a","CS","NONE"],["N-1479",1540,6.5,"a","ENG","NONE"],["N-1530",1540,6.5,"d","","NONE"],["N-1587",1540,6.5,"a","CS","LGBT"],["N-1672",1540,6.5,"a","","LEGACY"],["N-1717",1540,6.5,"d","ENG","NONE"],["N-1718",1540,6.5,"d","ENG","NONE"],["N-1773",1540,6.5,"d","CS","NONE"],["N-1788",1540,7.5,"d","ENG","FIRST-GEN"],["N-1850",1540,7.5,"d","CS","NONE"],["N-1891",1540,7.5,"d","CS","NONE"],["N-1892",1540,7.5,"d","CS","NONE"],["N-1957",1540,7.5,"a","CS","NONE"],["N-1996",1540,7.5,"d","ENG","NONE"],["N-2079",1540,6.5,"a","BIO","NONE"],["N-2159",1540,7.5,"d","POLISCI","NONE"],["N-2160",1540,7.5,"d","POLISCI","NONE"],["N-2180",1540,6.5,"w","POLISCI","NONE"],["N-2181",1540,7.5,"a","CS","NONE"],["N-2198",1540,7.5,"w","","NONE"],["N-2199",1540,6.5,"d","CS","NONE"],["N-2221",1540,7.5,"w","POLISCI","NONE"],["N-201",1550,6.5,"a","BUSINESS","NONE"],["N-212",1550,7.5,"d","CS","NONE"],["N-559",1550,7.5,"a","CS","FIRST-GEN"],["N-630",1550,6.5,"d","CS","NONE"],["N-688",1550,7.5,"w","ENG","LEGACY"],["N-699",1550,6.5,"a","","NONE"],["N-785",1550,6.0,"d","PHYSICS","NONE"],["N-815",1550,7.5,"w","CS","FIRST-GEN"],["N-892",1550,6.5,"d","BIO","NONE"],["N-932",1550,6.5,"w","CS","NONE"],["N-935",1550,6.5,"d","ENG","NONE"],["N-1032",1550,6.5,"d","CS","NONE"],["N-1045",1550,7.5,"w","PSYCH","NONE"],["N-1051",1550,6.5,"d","CS","NONE"],["N-1072",1550,7.5,"a","HUMANITIES","NONE"],["N-1127",1550,6.5,"a","","NONE"],["N-1139",1550,7.5,"a","PREMED","NONE"],["N-1147",1550,6.5,"w","ENG","NONE"],["N-1162",1550,6.0,"d","CS","NONE"],["N-1311",1550,7.5,"w","CS","NONE"],["N-1356",1550,6.5,"w","CS","NONE"],["N-1533",1550,6.5,"a","CS","NONE"],["N-1539",1550,6.5,"a","","NONE"],["N-1577",1550,6.5,"w","CS","NONE"],["N-1579",1550,7.0,"w","POLISCI","NONE"],["N-1618",1550,6.5,"a","CS","NONE"],["N-1947",1550,7.5,"w","","NONE"],["N-1976",1550,7.5,"w","ENG","NONE"],["N-1988",1550,7.5,"w","CS","NONE"],["N-2009",1550,7.5,"d","CS","NONE"],["N-2016",1550,6.5,"d","CS","NONE"],["N-2030",1550,6.5,"a","CS","NONE"],["N-2073",1550,7.5,"d","ENG","NONE"],["N-2165",1550,6.5,"d","BUSINESS","NONE"],["N-2218",1550,6.5,"d","CS","NONE"],["N-144",1560,6.5,"a","ENG","NONE"],["N-192",1560,6.5,"d","BUSINESS","NONE"],["N-251",1560,6.5,"w","CS","NONE"],["N-318",1560,7.5,"a","CS","NONE"],["N-346",1560,6.5,"d","BUSINESS","NONE"],["N-496",1560,6.5,"d","CS","NONE"],["N-689",1560,6.5,"w","ENG","NONE"],["N-708",1560,6.5,"w","ENG","NONE"],["N-727",1560,7.5,"a","CS","NONE"],["N-833",1560,6.5,"d","CS","LGBT"],["N-870",1560,7.5,"d","CS","NONE"],["N-883",1560,6.5,"w","CS","LEGACY"],["N-887",1560,7.5,"w","CS","NONE"],["N-888",1560,6.5,"w","BUSINESS","NONE"],["N-906",1560,6.5,"d","","NONE"],["N-942",1560,6.5,"a","BIO","NONE"],["N-964",1560,6.5,"d","CS","NONE"],["N-1094",1560,6.5,"a","CS","NONE"],["N-1114",1560,7.5,"d","BIO","NONE"],["N-1117",1560,6.5,"a","PREMED","NONE"],["N-1137",1560,7.5,"a","","NONE"],["N-1214",1560,7.5,"d","BIO","NONE"],["N-1292",1560,6.5,"d","ENG","NONE"],["N-1345",1560,7.5,"a","CS","URM"],["N-1397",1560,6.5,"d","BIO","NONE"],["N-1468",1560,7.5,"d","CS","NONE"],["N-1487",1560,7.5,"a","CS","FIRST-GEN"],["N-1552",1560,6.5,"w","BIO","NONE"],["N-1662",1560,6.5,"w","BIO","NONE"],["N-1785",1560,7.0,"d","CS","NONE"],["N-1875",1560,6.0,"d","CS","FIRST-GEN"],["N-1942",1560,7.5,"w","CS","NONE"],["N-1980",1560,6.5,"w","CS","NONE"],["N-2061",1560,7.5,"a","ENG","NONE"],["N-2065",1560,6.5,"d","CS","NONE"],["N-207",1570,6.5,"w","CS","NONE"],["N-214",1570,6.5,"a","CS","NONE"],["N-304",1570,6.5,"w","CS","NONE"],["N-355",1570,6.5,"w","POLISCI","LEGACY"],["N-404",1570,7.5,"a","ENG","NONE"],["N-439",1570,6.5,"w","ENG","LEGACY"],["N-464",1570,6.5,"a","ENG","LEGACY"],["N-780",1570,6.5,"w","BIO","NONE"],["N-791",1570,7.5,"w","POLISCI","FIRST-GEN"],["N-829",1570,7.0,"a","ENG","NONE"],["N-832",1570,6.5,"d","POLISCI","NONE"],["N-847",1570,6.5,"d","ENG","NONE"],["N-995",1570,6.5,"d","ENG","NONE"],["N-1135",1570,6.5,"a","BIO","NONE"],["N-1151",1570,6.0,"d","CS","NONE"],["N-1158",1570,6.5,"d","CS","LEGACY"],["N-1301",1570,6.0,"a","BIO","NONE"],["N-1437",1570,6.5,"w","","NONE"],["N-1581",1570,6.5,"d","CS","NONE"],["N-1620",1570,7.5,"a","CS","LGBT"],["N-1728",1570,7.5,"d","POLISCI","FIRST-GEN"],["N-1912",1570,7.0,"d","CS","URM"],["N-1951",1570,7.5,"d","CS","NONE"],["N-2136",1570,7.5,"d","BUSINESS","NONE"]]},{"score_band":"above","activities_band":"mid","admitted":12,"waitlisted":7,"denied":27,"n":46,"state":"ok","is_student":false,"cases":[["N-5",1580,7.5,"a","CS","NONE"],["N-235",1580,6.5,"d","CS","URM"],["N-468",1580,6.5,"d","","NONE"],["N-767",1580,6.5,"d","PREMED","NONE"],["N-860",1580,6.5,"d","CS","NONE"],["N-917",1580,7.5,"d","CS","LEGACY"],["N-1060",1580,6.5,"d","CS","NONE"],["N-1148",1580,6.5,"d","CS","NONE"],["N-1300",1580,6.5,"d","CS","NONE"],["N-1354",1580,7.5,"a","CS","NONE"],["N-1405",1580,7.5,"a","CS","URM"],["N-1636",1580,6.5,"a","PSYCH","LEGACY"],["N-1726",1580,6.0,"d","POLISCI","NONE"],["N-1893",1580,6.5,"d","BIO","NONE"],["N-2047",1580,6.5,"d","ENG","LEGACY"],["N-2119",1580,6.5,"d","CS","NONE"],["N-2128",1580,7.5,"a","CS","NONE"],["N-2200",1580,6.5,"d","CS","URM"],["N-2239",1580,6.5,"w","CS","NONE"],["N-14",1590,7.5,"w","CS","NONE"],["N-63",1590,6.5,"a","HUMANITIES","NONE"],["N-284",1590,6.5,"d","CS","NONE"],["N-383",1590,6.5,"a","ENG","LEGACY"],["N-587",1590,7.5,"d","CS","NONE"],["N-690",1590,6.5,"d","CS","LEGACY"],["N-760",1590,7.5,"d","ENG","NONE"],["N-765",1590,6.5,"w","BUSINESS","NONE"],["N-787",1590,6.5,"a","CS","NONE"],["N-801",1590,6.5,"d","CS","NONE"],["N-851",1590,7.5,"d","","NONE"],["N-894",1590,6.5,"d","","NONE"],["N-986",1590,7.5,"a","CS","NONE"],["N-1275",1590,6.5,"d","","NONE"],["N-1332",1590,6.5,"w","BUSINESS","LEGACY"],["N-1333",1590,6.5,"d","CS","NONE"],["N-1336",1590,6.5,"d","CS","NONE"],["N-1353",1590,6.0,"a","CS","NONE"],["N-1366",1590,6.5,"w","CS","NONE"],["N-1524",1590,7.5,"w","BUSINESS","NONE"],["N-1567",1590,7.5,"w","CS","NONE"],["N-1719",1590,6.5,"d","POLISCI","NONE"],["N-1768",1590,6.5,"d","CS","NONE"],["N-1943",1590,6.5,"d","CS","NONE"],["N-66",1600,6.5,"d","CS","NONE"],["N-927",1600,7.5,"a","HUMANITIES","NONE"],["N-2011",1600,7.5,"a","CS","FIRST-GEN"]]},{"score_band":"below","activities_band":"low","admitted":25,"waitlisted":5,"denied":53,"n":83,"state":"ok","is_student":true,"cases":[["N-522",1450,4.5,"a","BUSINESS","FIRST-GEN"],["N-668",1450,5.5,"d","BUSINESS","NONE"],["N-804",1450,5.0,"d","CS","NONE"],["N-838",1450,4.5,"d","CS","NONE"],["N-1630",1450,1.0,"w","","NONE"],["N-1812",1450,2.0,"d","CS","NONE"],["N-2226",1450,5.0,"d","BIO","NONE"],["N-40",1460,5.5,"d","CS","URM"],["N-146",1460,5.0,"a","CS","URM"],["N-345",1460,5.5,"a","POLISCI","FIRST-GEN"],["N-460",1460,5.0,"a","ENG","NONE"],["N-644",1460,1.0,"d","ENG","NONE"],["N-696",1440,5.5,"a","BIO","NONE"],["N-1038",1460,2.0,"d","POLISCI","NONE"],["N-1296",1440,2.0,"a","CS","FIRST-GEN"],["N-1453",1460,1.0,"d","CS","NONE"],["N-1902",1460,2.0,"d","CS","LEGACY"],["N-1960",1460,5.5,"d","CS","FIRST-GEN"],["N-2006",1460,1.0,"d","","NONE"],["N-2099",1460,3.5,"a","BUSINESS","NONE"],["N-37",1430,5.5,"d","BIO","NONE"],["N-150",1430,5.5,"a","","FIRST-GEN"],["N-223",1430,5.5,"a","","FIRST-GEN"],["N-233",1430,3.5,"d","POLISCI","URM"],["N-535",1430,1.5,"d","","LEGACY"],["N-541",1430,1.0,"a","PSYCH","NONE"],["N-579",1430,4.5,"d","CS","NONE"],["N-821",1470,4.5,"d","","LGBT"],["N-997",1430,5.5,"w","CS","NONE"],["N-1313",1430,4.5,"a","BIO","LEGACY"],["N-1599",1470,4.0,"d","CS","NONE"],["N-2213",1470,3.5,"a","ENG","NONE"],["N-115",1420,5.5,"a","CS","URM"],["N-127",1480,5.0,"d","CS","LEGACY"],["N-163",1480,5.5,"d","BUSINESS","FIRST-GEN"],["N-296",1480,5.5,"a","BIO","NONE"],["N-363",1480,4.0,"d","ENG","NONE"],["N-718",1480,3.0,"a","OTHER","NONE"],["N-924",1480,5.5,"d","CS","NONE"],["N-1294",1480,5.5,"d","CS","NONE"],["N-1344",1480,3.5,"d","CS","LEGACY"],["N-1451",1420,3.5,"a","ENG","FIRST-GEN"],["N-1990",1480,1.0,"w","CS","URM"],["N-540",1490,3.5,"a","CS","URM"],["N-583",1410,3.5,"d","CS","FIRST-GEN"],["N-747",1410,3.5,"a","BIO","NONE"],["N-825",1490,5.5,"d","CS","URM"],["N-866",1410,3.5,"d","CS","FIRST-GEN"],["N-901",1490,1.0,"a","CS","LEGACY"],["N-1200",1410,1.0,"d","CS","FIRST-GEN"],["N-1325",1490,2.5,"d","CS","NONE"],["N-1569",1490,2.5,"d","CS","NONE"],["N-1923",1490,5.5,"d","CS","NONE"],["N-88",1400,2.5,"a","BIO","URM"],["N-237",1400,5.0,"d","MATH","URM"],["N-772",1400,2.5,"d","CS","NONE"],["N-1709",1400,5.5,"d","BUSINESS","LEGACY"],["N-1018",1390,3.5,"d","ENG","LEGACY"],["N-792",1380,5.5,"d","OTHER","NONE"],["N-1526",1380,5.0,"d","BIO","LGBT"],["N-1901",1370,5.5,"d","BUSINESS","NONE"],["N-332",1360,2.0,"a","BIO","URM"],["N-843",1360,5.5,"a","OTHER","URM"],["N-1564",1350,5.5,"d","CS","URM"],["N-980",1340,5.0,"d","POLISCI","NONE"],["N-59",1330,2.5,"d","CS","NONE"],["N-155",1320,5.5,"w","ARTS","NONE"],["N-925",1320,2.5,"d","BUSINESS","LEGACY"],["N-822",1310,4.5,"d","CS","LEGACY"],["N-1825",1310,5.0,"d","BUSINESS","NONE"],["N-643",1300,5.0,"d","","URM"],["N-1280",1300,5.5,"w","POLISCI","FIRST-GEN"],["N-988",1280,3.5,"d","POLISCI","FIRST-GEN"],["N-1755",1280,5.5,"d","ENG","NONE"],["N-1465",1260,3.5,"d","POLISCI","URM"],["N-735",1240,5.0,"a","CS","NONE"],["N-1185",1240,2.5,"a","OTHER","URM"],["N-1263",1240,1.0,"a","OTHER","URM"],["N-1408",1210,3.5,"d","BUSINESS","NONE"],["N-340",1170,5.5,"d","HUMANITIES","NONE"],["N-2074",1140,5.5,"d","MATH","FIRST-GEN"],["N-175",1080,1.5,"d","BIO","URM"],["N-1463",890,5.0,"d","ENG","URM"]]},{"score_band":"inside","activities_band":"low","admitted":31,"waitlisted":16,"denied":51,"n":98,"state":"ok","is_student":false,"cases":[["N-240",1500,3.5,"a","ENG","FIRST-GEN"],["N-243",1500,5.5,"d","BUSINESS","NONE"],["N-269",1500,5.5,"d","CS","NONE"],["N-292",1500,5.5,"d","CS","FIRST-GEN"],["N-299",1500,5.5,"w","CS","NONE"],["N-316",1500,3.5,"d","BIO","URM"],["N-361",1500,5.5,"d","PREMED","LEGACY"],["N-386",1500,1.0,"a","CS","NONE"],["N-421",1500,5.0,"d","CS","NONE"],["N-682",1500,2.0,"d","POLISCI","NONE"],["N-683",1500,4.0,"d","OTHER","NONE"],["N-733",1500,3.5,"a","POLISCI","NONE"],["N-743",1500,5.5,"a","BIO","NONE"],["N-854",1500,2.5,"d","ENG","FIRST-GEN"],["N-862",1500,3.0,"d","CS","LEGACY"],["N-1398",1500,2.0,"d","CS","NONE"],["N-1494",1500,4.5,"a","CS","FIRST-GEN"],["N-1500",1500,1.5,"d","HUMANITIES","LEGACY"],["N-2122",1500,1.0,"a","BUSINESS","NONE"],["N-2175",1500,5.5,"a","ENG","NONE"],["N-2197",1500,5.0,"d","ENG","LGBT"],["N-2201",1500,5.5,"d","POLISCI","LEGACY"],["N-2212",1500,2.5,"a","BUSINESS","NONE"],["N-558",1510,5.5,"d","CS","NONE"],["N-773",1510,5.5,"a","ENG","NONE"],["N-803",1510,5.5,"w","CS","NONE"],["N-855",1510,5.0,"w","CS","LEGACY"],["N-1033",1510,5.5,"a","POLISCI","LEGACY"],["N-1352",1510,5.0,"w","CS","NONE"],["N-1490",1510,4.5,"d","ENG","URM"],["N-1786",1510,1.0,"d","CS","URM"],["N-2208",1510,5.5,"d","CS","NONE"],["N-27",1520,5.5,"d","BIO","URM"],["N-204",1520,5.5,"d","BIO","URM"],["N-420",1520,5.0,"a","ENG","NONE"],["N-756",1520,3.5,"w","CS","NONE"],["N-940",1520,1.0,"a","CS","LEGACY"],["N-1013",1520,5.5,"a","","LEGACY"],["N-1232",1520,3.5,"d","CS","NONE"],["N-1391",1520,5.5,"d","BIO","NONE"],["N-1473",1520,3.5,"d","PSYCH","NONE"],["N-1616",1520,5.5,"w","PHYSICS","URM"],["N-2131",1520,2.5,"d","CS","URM"],["N-139",1530,2.5,"d","BUSINESS","FIRST-GEN"],["N-717",1530,3.0,"a","ENG","LEGACY"],["N-877",1530,5.0,"a","POLISCI","NONE"],["N-948",1530,1.0,"a","POLISCI","URM"],["N-1288",1530,2.0,"d","ENG","NONE"],["N-1421",1530,5.5,"d","PSYCH","URM"],["N-1488",1530,4.0,"d","CS","NONE"],["N-1511",1530,4.0,"d","CS","NONE"],["N-199",1540,3.5,"a","CS","NONE"],["N-211",1540,3.5,"d","CS","NONE"],["N-274",1540,5.5,"w","ENG","NONE"],["N-463",1540,5.5,"d","CS","NONE"],["N-589",1540,5.5,"w","CS","NONE"],["N-701",1540,5.5,"w","CS","URM"],["N-709",1540,3.5,"w","ENG","NONE"],["N-797",1540,3.5,"w","CS","NONE"],["N-824",1540,3.5,"a","ENG","URM"],["N-874",1540,5.5,"d","CS","NONE"],["N-969",1540,4.5,"w","CS","NONE"],["N-1025",1540,4.5,"a","BUSINESS","NONE"],["N-1154",1540,5.5,"d","CS","NONE"],["N-1315",1540,5.5,"d","PHYSICS","NONE"],["N-1966",1540,4.0,"w","ENG","NONE"],["N-2116",1540,5.5,"d","CS","NONE"],["N-2216",1540,2.0,"d","CS","NONE"],["N-342",1550,5.5,"d","BUSINESS","NONE"],["N-440",1550,5.5,"a","CS","NONE"],["N-450",1550,4.5,"d","CS","NONE"],["N-592",1550,5.5,"w","CS","NONE"],["N-738",1550,0.0,"d","CS","NONE"],["N-783",1550,5.5,"a","CS","NONE"],["N-1049",1550,5.0,"a","CS","FIRST-GEN"],["N-1401",1550,3.5,"d","ENG","NONE"],["N-1469",1550,4.5,"d","CS","NONE"],["N-1520",1550,5.5,"a","BIO","NONE"],["N-1534",1550,5.0,"d","ENG","NONE"],["N-1845",1550,1.0,"d","CS","URM"],["N-2172",1550,3.5,"a","OTHER","NONE"],["N-206",1560,5.5,"d","CS","NONE"],["N-377",1560,5.0,"a","CS","NONE"],["N-1188",1560,5.5,"a","CS","NONE"],["N-1330",1560,1.0,"d","CS","NONE"],["N-1498",1560,5.0,"d","CS","NONE"],["N-1506",1560,5.5,"a","BIO","NONE"],["N-1548",1560,5.0,"d","CS","NONE"],["N-1853",1560,5.0,"d","BUSINESS","NONE"],["N-2053",1560,2.0,"d","","NONE"],["N-2117",1560,5.5,"a","POLISCI","NONE"],["N-2171",1560,5.5,"a","CS","NONE"],["N-474",1570,3.5,"w","BIO","NONE"],["N-891",1570,5.5,"a","CS","NONE"],["N-998",1570,5.5,"d","PHYSICS","NONE"],["N-1521",1570,5.5,"d","ENG","NONE"],["N-2002",1570,4.8,"a","CS","NONE"],["N-2056",1570,4.0,"w","","NONE"]]},{"score_band":"above","activities_band":"low","admitted":3,"waitlisted":7,"denied":9,"n":19,"state":"ok","is_student":false,"cases":[["N-890",1580,3.0,"w","POLISCI","NONE"],["N-949",1580,5.5,"d","ENG","LEGACY"],["N-1014",1580,4.5,"d","ENG","NONE"],["N-1340",1580,3.5,"d","CS","NONE"],["N-1514",1580,3.5,"a","CS","NONE"],["N-1632",1580,2.5,"w","CS","NONE"],["N-2054",1580,4.5,"w","PSYCH","NONE"],["N-2236",1580,5.0,"d","BIO","LGBT"],["N-334",1590,5.5,"w","ENG","LEGACY"],["N-343",1590,5.5,"d","CS","NONE"],["N-642",1590,2.5,"d","HUMANITIES","NONE"],["N-665",1590,5.0,"d","CS","NONE"],["N-713",1590,5.5,"w","ENG","LEGACY"],["N-812",1590,5.5,"d","MATH","URM"],["N-922",1590,3.5,"w","CS","NONE"],["N-1075",1590,4.5,"a","ENG","NONE"],["N-1462",1590,3.5,"w","POLISCI","FIRST-GEN"],["N-1745",1590,5.0,"d","CS","NONE"],["N-2041",1590,3.5,"a","CS","NONE"]]}],"caveat":"People who were admitted post far more often than people who were denied, so every cluster looks rosier than the real applicant pool."},"kinds_check":{"separation":0.319,"shuffled":0.148,"stability":0.191,"verdict":"none","text":"No clear kinds at this college.","needs":{"separation":0.51,"margin":0.05,"stability":0.75,"loose_separation":0.26,"loose_stability":0.6}},"d_admitted":0.07,"d_denied":0.059,"gap":-0.012,"lean":"in_between","text":"About as close to the people admitted as to the people denied.","steady":true,"flips":[],"parts":[{"part":"score","distance":0.062,"text":"close"},{"part":"activities","distance":0.107,"text":"close"},{"part":"major","distance":0.0,"text":"close"},{"part":"hooks","distance":0.143,"text":"close"}],"not_used":["GPA","essay","activity descriptions","residency (private college)"],"nearest_admitted":[{"case_id":"N-811","sat":null,"act":null,"major":"CS","hooks":"FIRST-GEN","home_state":"MA","activities_rating":4.5,"outcome":"admitted","invented":false,"distance":0.022,"parts":{"activities":0.05,"major":0.0,"hooks":0.0}},{"case_id":"N-150","sat":1430,"act":32,"major":null,"hooks":"FIRST-GEN","home_state":"CO","activities_rating":5.5,"outcome":"admitted","invented":false,"distance":0.043,"parts":{"score":0.05,"activities":0.05,"hooks":0.0}},{"case_id":"N-223","sat":1430,"act":32,"major":null,"hooks":"FIRST-GEN","home_state":"CO","activities_rating":5.5,"outcome":"admitted","invented":false,"distance":0.043,"parts":{"score":0.05,"activities":0.05,"hooks":0.0}}],"nearest_denied":[{"case_id":"N-1960","sat":1460,"act":null,"major":"CS","hooks":"FIRST-GEN","home_state":"FL","activities_rating":5.5,"outcome":"denied","invented":false,"distance":0.024,"parts":{"score":0.025,"activities":0.05,"major":0.0,"hooks":0.0}},{"case_id":"N-537","sat":1430,"act":null,"major":"CS","hooks":"FIRST-GEN","home_state":"NY","activities_rating":6.0,"outcome":"denied","invented":false,"distance":0.047,"parts":{"score":0.05,"activities":0.1,"major":0.0,"hooks":0.0}},{"case_id":"N-678","sat":1430,"act":null,"major":"CS","hooks":"FIRST-GEN","home_state":"NY","activities_rating":6.0,"outcome":"denied","invented":false,"distance":0.047,"parts":{"score":0.05,"activities":0.1,"major":0.0,"hooks":0.0}}],"kinds":[{"kind_id":"K1","name":"Mid score, CS, activities 6.5","size":113,"median_sat":1550,"median_activities":6.5,"top_major":"CS","medoid_case_id":"N-699","distance":0.219,"nearest":false},{"kind_id":"K2","name":"Lower score, CS, activities 6.5 (SAT 1460)","size":60,"median_sat":1460,"median_activities":6.5,"top_major":"CS","medoid_case_id":"N-194","distance":0.063,"nearest":true},{"kind_id":"K3","name":"Lower score, CS, activities 6.5 (SAT 1320)","size":11,"median_sat":1320,"median_activities":6.5,"top_major":"CS","medoid_case_id":"N-770","distance":0.271,"nearest":false}],"changes":[],"changes_note":"Nothing we can measure here would move this.","points":[{"case_id":"N-5","sat":1580,"activities":7.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-19","sat":1500,"activities":7.5,"outcome":"denied","kind_id":null},{"case_id":"N-37","sat":1430,"activities":5.5,"outcome":"denied","kind_id":null},{"case_id":"N-42","sat":1570,"activities":8.5,"outcome":"denied","kind_id":null},{"case_id":"N-46","sat":630,"activities":6.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-63","sat":1590,"activities":6.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-66","sat":1600,"activities":6.5,"outcome":"denied","kind_id":null},{"case_id":"N-87","sat":1460,"activities":7.5,"outcome":"waitlisted","kind_id":null},{"case_id":"N-93","sat":1540,"activities":6.5,"outcome":"denied","kind_id":null},{"case_id":"N-114","sat":1450,"activities":6.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-123","sat":1460,"activities":6.5,"outcome":"denied","kind_id":null},{"case_id":"N-127","sat":1480,"activities":5.0,"outcome":"denied","kind_id":null},{"case_id":"N-144","sat":1560,"activities":6.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-149","sat":1500,"activities":6.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-155","sat":1320,"activities":5.5,"outcome":"waitlisted","kind_id":null},{"case_id":"N-166","sat":1440,"activities":7.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-175","sat":1080,"activities":1.5,"outcome":"denied","kind_id":null},{"case_id":"N-189","sat":1450,"activities":6.5,"outcome":"denied","kind_id":null},{"case_id":"N-194","sat":1460,"activities":6.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-199","sat":1540,"activities":3.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-203","sat":1540,"activities":6.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-206","sat":1560,"activities":5.5,"outcome":"denied","kind_id":null},{"case_id":"N-209","sat":1540,"activities":6.5,"outcome":"waitlisted","kind_id":null},{"case_id":"N-212","sat":1550,"activities":7.5,"outcome":"denied","kind_id":null},{"case_id":"N-214","sat":1570,"activities":6.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-225","sat":1470,"activities":6.5,"outcome":"denied","kind_id":null},{"case_id":"N-234","sat":1530,"activities":6.5,"outcome":"waitlisted","kind_id":null},{"case_id":"N-237","sat":1400,"activities":5.0,"outcome":"denied","kind_id":null},{"case_id":"N-243","sat":1500,"activities":5.5,"outcome":"denied","kind_id":null},{"case_id":"N-251","sat":1560,"activities":6.5,"outcome":"waitlisted","kind_id":null},{"case_id":"N-260","sat":1540,"activities":6.5,"outcome":"waitlisted","kind_id":null},{"case_id":"N-268","sat":1540,"activities":8.5,"outcome":"waitlisted","kind_id":null},{"case_id":"N-272","sat":1430,"activities":6.5,"outcome":"denied","kind_id":null},{"case_id":"N-274","sat":1540,"activities":5.5,"outcome":"waitlisted","kind_id":null},{"case_id":"N-279","sat":1540,"activities":6.5,"outcome":"denied","kind_id":null},{"case_id":"N-284","sat":1590,"activities":6.5,"outcome":"denied","kind_id":null},{"case_id":"N-296","sat":1480,"activities":5.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-303","sat":1400,"activities":6.5,"outcome":"denied","kind_id":null},{"case_id":"N-312","sat":1520,"activities":7.5,"outcome":"denied","kind_id":null},{"case_id":"N-318","sat":1560,"activities":7.5,"outcome":"admitted","kind_id":"K1"}]},"own":{"source":"Invented demo school history (not real students)","verified":true,"status":"cant_say","n_admitted":0,"n_denied":2,"n_waitlisted":1,"groups":{"status":"cant_say","reason":"The school's own cases carry no activities rating, so they cannot be placed in these clusters.","sat25":null,"sat75":null,"act_mid":6,"act_high":8,"min_n":5,"few_n":15,"left_out":0,"capped":false,"student_note":"","cells":[],"caveat":"People who were admitted post far more often than people who were denied, so every cluster looks rosier than the real applicant pool."},"kinds_check":null,"text":"Not enough shared profile information to measure distance.","invented":true},"caveat":"Closeness compares this student with people who chose to post their results. It is not a forecast."},"says":[{"claim_id":"c7_essay","text":"Cornell rates the application essay Very Important.","field":"Common Data Set, section C7","year":"2025-26","source_url":"https://www.collegedata.fyi/schools/cornell/2025-26/cds.csv","numbers":[],"kb":{"text":"Application Essay: Very Important","score":0.83,"doc":"KB_doc1_college_admission_factors_C7.md"},"checked":true}],"myths":[{"belief":"Showing interest (visits, emails) improves the odds.","college_says":"Cornell's form rates level of applicant's interest Not Considered.","source_url":"https://www.collegedata.fyi/schools/cornell/2025-26/cds.csv","year":"2025-26"}],"cost_note":"Sticker cost is about $88,000 a year. What this family would actually pay is not known here.","flags":[]},{"id":"243780","name":"Purdue University-Main Campus","state":"IN","control":"public","admit_rate":0.4995,"sat25":1210,"sat75":1470,"act25":27,"act75":34,"cost_year":22812,"source":"US Department of Education, College Scorecard","in_data":true,"label":{"state":"target","text":"Target","rule_id":"R4","rule_text":"The score is inside the college's middle range (1210 to 1470).","score_used":1450,"score_kind":"SAT","inputs":{"sat25":1210,"sat75":1470,"admit_rate":0.4995},"not_used":["GPA","activities","essay"],"caveats":["The score range covers only students who sent scores.","Computer science at Purdue is harder to get into than the university as a whole; this label is for the university."],"steady":false,"flips":[{"cause":"score 30 points higher","to":"likely"}],"publishers":[{"name":"BigFuture","label":"target"},{"name":"Princeton Review","label":"target"},{"name":"Scoir","label":"likely"},{"name":"Appily","label":"target"},{"name":"CollegeVine","label":"target"}],"publishers_disagree":true},"cases":{"needed":15,"own":{"source":"Your school's own finished cases (SYNTHETIC demo data)","verified":true,"status":"none","n":0,"admitted":0,"denied":0,"waitlisted":0,"matched_on":[],"relaxed":[],"examples":[]},"national":{"source":"Self-reported public posts (r/collegeresults)","verified":false,"status":"ok","n":31,"admitted":22,"denied":6,"waitlisted":3,"matched_on":["SAT within 50 points","same major group","same hook status"],"relaxed":[],"examples":[{"case_id":"N-0","sat":1440,"act":null,"major":"CS","hooks":"NONE","home_state":"MI","activities_rating":2.0,"outcome":"admitted"},{"case_id":"N-918","sat":1460,"act":null,"major":"CS","hooks":"NONE","home_state":"IL","activities_rating":6.5,"outcome":"denied"}]},"official_admit_rate":0.4995,"pool_admit_share_all":0.687,"overcount":1.4,"caveat":"People who post their results are admitted far more often than applicants overall. Read these as examples, not odds."},"says":[],"myths":[],"cost_note":"Sticker cost is about $23,000 a year in-state; out-of-state students pay more. What this family would actually pay is not known here.","flags":[],"closeness":{"semantic":{"status":"off"},"essay_retrieval":[],"weights":{"score":0.45,"activities":0.2,"major":0.15,"hooks":0.1,"residency":0.1,"gpa":0.2,"essay":0.2,"activity_text":0.15},"needed":15,"neighbours":7,"student":{"score":1450,"converted":false,"activities":5.0,"activities_from":"estimated","activities_why":["1 activity listed","recognition beyond the school"],"activities_rule":"4 for one activity, +1 for each further activity up to 4, +1 for a leading role, +1 for recognition beyond the school, +1 for sustained commitment (years, or weekly hours); never over 10."},"national":{"source":"Public posts on Reddit (r/collegeresults), self-reported","verified":false,"status":"ok","n_admitted":250,"n_denied":62,"n_waitlisted":25,"groups":{"status":"ok","reason":"","sat25":1200,"sat75":1480,"act_mid":6,"act_high":8,"min_n":5,"few_n":15,"left_out":33,"capped":false,"student_note":"","cells":[{"score_band":"below","activities_band":"high","admitted":0,"waitlisted":0,"denied":0,"n":0,"state":"not_enough","is_student":false,"cases":[]},{"score_band":"inside","activities_band":"high","admitted":4,"waitlisted":2,"denied":0,"n":6,"state":"few","is_student":false,"cases":[["N-2100",1450,8.5,"a","OTHER","NONE"],["N-376",1440,8.5,"w","CS","NONE"],["N-80",1430,8.5,"a","BIO","NONE"],["N-1211",1470,8.5,"a","CS","NONE"],["N-191",1480,8.2,"w","CS","NONE"],["N-2093",1330,8.5,"a","ENG","NONE"]]},{"score_band":"above","activities_band":"high","admitted":29,"waitlisted":4,"denied":2,"n":35,"state":"ok","is_student":false,"cases":[["N-238",1490,8.5,"w","CS","NONE"],["N-816",1510,8.5,"a","ENG","URM"],["N-1798",1520,8.5,"d","CS","NONE"],["N-1801",1520,8.5,"a","CS","NONE"],["N-1922",1520,8.5,"a","CS","NONE"],["N-1308",1530,8.5,"a","CS","NONE"],["N-1796",1530,8.5,"a","CS","FIRST-GEN"],["N-254",1540,8.5,"a","CS","NONE"],["N-1470",1540,8.5,"a","CS","NONE"],["N-1861",1540,8.5,"a","CS","NONE"],["N-1991",1540,8.5,"a","ENG","NONE"],["N-2031",1540,8.2,"a","CS","NONE"],["N-389",1550,9.5,"w","ENG","LEGACY"],["N-1195",1550,8.5,"w","CS","NONE"],["N-1566",1550,8.5,"a","CS","LEGACY"],["N-507",1560,8.5,"a","CS","NONE"],["N-849",1560,8.5,"a","CS","NONE"],["N-1260",1560,8.5,"a","POLISCI","NONE"],["N-1287",1560,9.5,"w","","NONE"],["N-2244",1560,8.5,"a","CS","NONE"],["N-42",1570,8.5,"a","CS","NONE"],["N-1062",1570,8.5,"a","CS","NONE"],["N-1932",1570,8.5,"a","CS","NONE"],["N-1933",1570,8.5,"a","CS","NONE"],["N-1295",1580,8.5,"a","CS","NONE"],["N-1600",1580,8.5,"d","CS","NONE"],["N-1625",1580,8.5,"a","ENG","NONE"],["N-2040",1580,8.5,"a","CS","NONE"],["N-546",1590,8.5,"a","CS","FIRST-GEN"],["N-1019",1590,8.5,"a","MATH","NONE"],["N-1085",1590,8.5,"a","CS","NONE"],["N-1146",1590,8.5,"a","CS","NONE"],["N-1382",1590,8.5,"a","CS","NONE"],["N-911",1600,8.5,"a","CS","NONE"],["N-1449",1600,8.5,"a","CS","NONE"]]},{"score_band":"below","activities_band":"mid","admitted":0,"waitlisted":0,"denied":0,"n":0,"state":"not_enough","is_student":false,"cases":[]},{"score_band":"inside","activities_band":"mid","admitted":32,"waitlisted":2,"denied":12,"n":46,"state":"ok","is_student":false,"cases":[["N-290",1450,7.5,"a","","NONE"],["N-434",1450,6.5,"a","PSYCH","NONE"],["N-1602",1450,6.5,"d","CS","NONE"],["N-166",1440,7.5,"a","CS","NONE"],["N-1396",1460,6.5,"a","ENG","URM"],["N-1484",1460,6.5,"a","BIO","NONE"],["N-2144",1460,6.5,"a","CS","NONE"],["N-2156",1460,7.5,"w","CS","FIRST-GEN"],["N-272",1430,6.5,"a","ENG","NONE"],["N-834",1470,7.5,"a","CS","NONE"],["N-989",1470,7.5,"a","CS","NONE"],["N-1143",1470,7.5,"d","CS","NONE"],["N-1197",1430,7.5,"a","CS","NONE"],["N-1516",1430,6.5,"a","ENG","NONE"],["N-1610",1430,7.0,"a","ENG","NONE"],["N-1739",1470,6.0,"d","CS","FIRST-GEN"],["N-1740",1470,6.5,"d","CS","FIRST-GEN"],["N-1741",1470,6.0,"d","CS","FIRST-GEN"],["N-1851",1470,7.5,"a","PREMED","NONE"],["N-1936",1470,7.5,"a","PREMED","NONE"],["N-2085",1430,6.0,"d","CS","NONE"],["N-720",1480,6.5,"a","ENG","NONE"],["N-859",1480,6.0,"d","ENG","NONE"],["N-1541",1420,6.5,"d","CS","NONE"],["N-1821",1420,6.0,"a","ENG","NONE"],["N-2018",1480,6.5,"a","CS","NONE"],["N-2233",1480,6.5,"a","ENG","NONE"],["N-2134",1410,6.5,"a","","NONE"],["N-303",1400,6.5,"w","CS","URM"],["N-1608",1400,7.5,"a","POLISCI","URM"],["N-656",1390,6.5,"a","","NONE"],["N-1153",1390,7.5,"d","CS","NONE"],["N-1435",1390,6.5,"d","ENG","NONE"],["N-2110",1380,6.5,"a","ENG","URM"],["N-2111",1380,6.5,"a","ENG","URM"],["N-547",1370,6.5,"a","ENG","NONE"],["N-2161",1370,6.5,"a","CS","NONE"],["N-1908",1360,6.5,"a","ENG","NONE"],["N-1545",1350,6.5,"d","CS","NONE"],["N-2138",1350,6.5,"a","ENG","NONE"],["N-1778",1330,6.0,"a","CS","NONE"],["N-1208",1320,6.5,"a","POLISCI","NONE"],["N-1244",1320,7.5,"a","POLISCI","NONE"],["N-1480",1310,7.5,"a","ENG","LEGACY"],["N-975",1300,6.5,"a","CS","NONE"],["N-1865",1210,6.0,"d","CS","NONE"]]},{"score_band":"above","activities_band":"mid","admitted":102,"waitlisted":7,"denied":17,"n":126,"state":"ok","is_student":false,"cases":[["N-101",1490,6.5,"a","","NONE"],["N-1337",1490,6.5,"a","CS","URM"],["N-64",1500,6.5,"a","ENG","LEGACY"],["N-580",1500,6.5,"a","CS","NONE"],["N-677",1500,6.5,"a","CS","NONE"],["N-991",1500,7.5,"a","CS","NONE"],["N-1194",1500,7.5,"a","BUSINESS","NONE"],["N-1335",1500,6.5,"a","CS","NONE"],["N-1395",1500,7.5,"a","ENG","FIRST-GEN"],["N-1422",1500,7.5,"a","CS","NONE"],["N-1540",1500,7.5,"d","CS","NONE"],["N-1542",1500,6.5,"d","ENG","URM"],["N-1557",1500,6.5,"d","CS","NONE"],["N-1729",1500,7.5,"a","BIO","NONE"],["N-1760",1500,6.5,"a","CS","NONE"],["N-1863",1500,6.5,"a","CS","LEGACY"],["N-1919",1500,7.5,"a","CS","URM"],["N-1958",1500,6.5,"a","CS","LEGACY"],["N-1987",1500,6.5,"a","CS","LEGACY"],["N-2060",1500,6.5,"a","BUSINESS","NONE"],["N-359",1510,6.5,"a","CS","NONE"],["N-899",1510,7.0,"a","BUSINESS","NONE"],["N-959",1510,6.5,"a","","LEGACY"],["N-1199",1510,6.5,"d","ENG","NONE"],["N-1347",1510,6.5,"w","CS","NONE"],["N-1434",1510,6.5,"d","CS","NONE"],["N-1452",1510,7.5,"a","CS","NONE"],["N-790",1520,6.5,"a","CS","NONE"],["N-1178",1520,7.5,"d","ENG","NONE"],["N-1323",1520,6.5,"a","CS","NONE"],["N-1544",1520,6.5,"d","ENG","NONE"],["N-1763",1520,7.5,"a","CS","NONE"],["N-2005",1520,7.0,"a","CS","NONE"],["N-12",1530,7.5,"a","CS","LEGACY"],["N-262",1530,7.5,"a","CS","LEGACY"],["N-771",1530,6.5,"a","ENG","NONE"],["N-881",1530,6.5,"a","CS","NONE"],["N-1017",1530,6.5,"a","CS","NONE"],["N-1152",1530,6.5,"a","ENG","NONE"],["N-1189",1530,7.5,"w","CS","NONE"],["N-1343",1530,7.5,"a","CS","NONE"],["N-1696",1530,6.5,"d","ENG","LGBT"],["N-1979",1530,7.5,"d","CS","NONE"],["N-2086",1530,6.5,"a","CS","NONE"],["N-2094",1530,6.0,"a","CS","LEGACY"],["N-2125",1530,6.5,"d","CS","NONE"],["N-158",1540,6.5,"a","POLISCI","NONE"],["N-210",1540,7.5,"a","","NONE"],["N-279",1540,6.5,"a","CS","NONE"],["N-700",1540,7.5,"d","CS","LEGACY"],["N-712",1540,6.5,"a","ENG","NONE"],["N-1005",1540,7.5,"a","CS","NONE"],["N-1160",1540,6.5,"a","CS","NONE"],["N-1164",1540,6.5,"a","CS","NONE"],["N-1174",1540,6.5,"a","CS","NONE"],["N-1247",1540,6.5,"a","CS","NONE"],["N-1269",1540,7.5,"a","BIO","NONE"],["N-1321",1540,6.5,"a","BIO","NONE"],["N-1454",1540,7.5,"a","CS","NONE"],["N-1717",1540,6.5,"a","ENG","NONE"],["N-1718",1540,6.5,"a","ENG","NONE"],["N-1773",1540,6.5,"a","CS","NONE"],["N-1788",1540,7.5,"a","ENG","FIRST-GEN"],["N-1952",1540,7.5,"d","ENG","NONE"],["N-2048",1540,7.5,"a","CS","NONE"],["N-2096",1540,6.5,"a","BUSINESS","NONE"],["N-2097",1540,6.5,"a","BUSINESS","NONE"],["N-2199",1540,6.5,"d","CS","NONE"],["N-935",1550,6.5,"a","ENG","NONE"],["N-1051",1550,6.5,"d","CS","NONE"],["N-1162",1550,6.0,"a","CS","NONE"],["N-1577",1550,6.5,"d","CS","NONE"],["N-1579",1550,7.0,"a","POLISCI","NONE"],["N-1618",1550,6.5,"a","CS","NONE"],["N-1775",1550,7.5,"a","CS","NONE"],["N-1947",1550,7.5,"a","","NONE"],["N-1976",1550,7.5,"a","ENG","NONE"],["N-1988",1550,7.5,"a","CS","NONE"],["N-2073",1550,7.5,"a","ENG","NONE"],["N-2135",1550,7.5,"a","CS","NONE"],["N-2218",1550,6.5,"a","CS","NONE"],["N-104",1560,6.5,"a","PHYSICS","NONE"],["N-143",1560,6.5,"a","CS","NONE"],["N-318",1560,7.5,"a","CS","NONE"],["N-708",1560,6.5,"a","ENG","NONE"],["N-800",1560,7.5,"d","CS","NONE"],["N-906",1560,6.5,"a","","NONE"],["N-964",1560,6.5,"a","CS","NONE"],["N-1291",1560,6.5,"w","MATH","NONE"],["N-1785",1560,7.0,"a","CS","NONE"],["N-1935",1560,7.5,"a","CS","NONE"],["N-1942",1560,7.5,"a","CS","NONE"],["N-1980",1560,6.5,"a","CS","NONE"],["N-2061",1560,7.5,"a","ENG","NONE"],["N-2062",1560,7.5,"a","CS","NONE"],["N-571",1570,7.5,"w","CS","NONE"],["N-799",1570,7.5,"a","ENG","NONE"],["N-829",1570,7.0,"a","ENG","NONE"],["N-995",1570,6.5,"a","ENG","NONE"],["N-1158",1570,6.5,"a","CS","LEGACY"],["N-1161",1570,6.5,"a","CS","NONE"],["N-1581",1570,6.5,"a","CS","NONE"],["N-1779",1570,6.5,"a","CS","URM"],["N-1789",1570,7.5,"a","","NONE"],["N-2202",1570,7.5,"a","CS","NONE"],["N-8",1580,6.5,"d","","NONE"],["N-860",1580,6.5,"a","CS","NONE"],["N-917",1580,7.5,"a","CS","LEGACY"],["N-1060",1580,6.5,"w","CS","NONE"],["N-1300",1580,6.5,"a","CS","NONE"],["N-2128",1580,7.5,"a","CS","NONE"],["N-2200",1580,6.5,"w","CS","URM"],["N-2239",1580,6.5,"a","CS","NONE"],["N-514",1590,6.5,"a","CS","NONE"],["N-587",1590,7.5,"a","CS","NONE"],["N-690",1590,6.5,"a","CS","LEGACY"],["N-760",1590,7.5,"a","ENG","NONE"],["N-801",1590,6.5,"a","CS","NONE"],["N-1275",1590,6.5,"w","","NONE"],["N-1333",1590,6.5,"a","CS","NONE"],["N-1567",1590,7.5,"a","CS","NONE"],["N-1889",1590,6.5,"a","CS","NONE"],["N-2036",1590,7.5,"a","CS","NONE"],["N-2137",1590,7.5,"a","CS","NONE"],["N-1744",1600,7.5,"a","CS","NONE"],["N-1920",1600,6.5,"a","ENG","LEGACY"]]},{"score_band":"below","activities_band":"low","admitted":0,"waitlisted":0,"denied":1,"n":1,"state":"not_enough","is_student":false,"cases":[["N-610",1080,2.5,"d","ENG","NONE"]]},{"score_band":"inside","activities_band":"low","admitted":24,"waitlisted":2,"denied":8,"n":34,"state":"ok","is_student":true,"cases":[["N-905",1450,4.0,"a","ENG","NONE"],["N-1812",1450,2.0,"a","CS","NONE"],["N-0",1440,2.0,"a","CS","NONE"],["N-696",1440,5.5,"a","BIO","NONE"],["N-1224",1460,1.0,"w","MATH","NONE"],["N-1902",1460,2.0,"a","CS","LEGACY"],["N-2006",1460,1.0,"d","","NONE"],["N-2046",1440,4.5,"d","ENG","NONE"],["N-2104",1460,3.5,"a","CS","FIRST-GEN"],["N-2151",1440,1.0,"d","ENG","FIRST-GEN"],["N-579",1430,4.5,"a","CS","NONE"],["N-623",1430,3.5,"a","BIO","NONE"],["N-1599",1470,4.0,"a","CS","NONE"],["N-1769",1470,2.5,"a","CS","NONE"],["N-1898",1470,5.0,"a","ENG","NONE"],["N-2213",1470,3.5,"a","ENG","NONE"],["N-363",1480,4.0,"d","ENG","NONE"],["N-497",1420,5.5,"a","BIO","URM"],["N-1983",1480,5.5,"d","CS","NONE"],["N-81",1400,5.0,"a","ENG","NONE"],["N-772",1400,2.5,"a","CS","NONE"],["N-1255",1390,4.0,"a","CS","FIRST-GEN"],["N-1418",1370,5.5,"w","CS","NONE"],["N-1857",1370,5.0,"a","ENG","NONE"],["N-59",1330,2.5,"a","CS","NONE"],["N-725",1320,5.5,"d","CS","FIRST-GEN"],["N-822",1310,4.5,"d","CS","LEGACY"],["N-1928",1310,2.0,"d","ENG","NONE"],["N-480",1280,1.0,"a","","NONE"],["N-1834",1250,3.5,"a","ENG","NONE"],["N-2219",1250,2.0,"a","","LEGACY"],["N-1474",1240,2.0,"a","BUSINESS","NONE"],["N-1580",1240,2.0,"a","CS","NONE"],["N-1830",1210,5.0,"a","ENG","NONE"]]},{"score_band":"above","activities_band":"low","admitted":40,"waitlisted":4,"denied":12,"n":56,"state":"ok","is_student":false,"cases":[["N-1428",1490,4.5,"a","CS","FIRST-GEN"],["N-1923",1490,5.5,"a","CS","NONE"],["N-862",1500,3.0,"a","CS","LEGACY"],["N-1274",1500,1.0,"a","BUSINESS","LEGACY"],["N-1319",1500,5.5,"a","CS","NONE"],["N-1494",1500,4.5,"a","CS","FIRST-GEN"],["N-1967",1500,3.5,"d","ENG","NONE"],["N-1968",1500,3.5,"d","ENG","NONE"],["N-2197",1500,5.0,"w","ENG","LGBT"],["N-635",1510,5.0,"d","ENG","NONE"],["N-651",1510,3.0,"a","MATH","NONE"],["N-773",1510,5.5,"w","ENG","NONE"],["N-1568",1510,3.5,"a","PSYCH","LEGACY"],["N-1750",1510,1.0,"a","ENG","NONE"],["N-1765",1510,5.0,"a","CS","NONE"],["N-1786",1510,1.0,"a","CS","URM"],["N-1841",1510,5.5,"a","ENG","NONE"],["N-2070",1510,5.5,"a","","NONE"],["N-538",1520,5.5,"a","ENG","NONE"],["N-2220",1520,5.5,"d","CS","NONE"],["N-113",1530,5.0,"a","CS","NONE"],["N-1288",1530,2.0,"d","ENG","NONE"],["N-1329",1530,3.0,"a","BIO","NONE"],["N-1562",1530,5.5,"a","CS","NONE"],["N-1756",1530,5.5,"a","CS","NONE"],["N-1757",1530,5.5,"a","CS","NONE"],["N-258",1540,5.0,"a","BIO","NONE"],["N-311",1540,5.5,"a","ENG","NONE"],["N-544",1540,2.5,"a","CS","NONE"],["N-589",1540,5.5,"a","CS","NONE"],["N-1149",1540,5.5,"d","CS","NONE"],["N-1154",1540,5.5,"w","CS","NONE"],["N-1816",1540,5.5,"a","","NONE"],["N-307",1550,5.5,"d","ENG","LGBT"],["N-1469",1550,4.5,"a","CS","NONE"],["N-1534",1550,5.0,"a","ENG","NONE"],["N-1845",1550,1.0,"d","CS","URM"],["N-2115",1550,3.0,"d","CS","NONE"],["N-2147",1550,4.5,"d","CS","NONE"],["N-1733",1560,5.0,"d","ENG","NONE"],["N-337",1570,1.0,"a","ENG","NONE"],["N-550",1570,3.5,"a","","NONE"],["N-891",1570,5.5,"a","CS","NONE"],["N-2002",1570,4.8,"a","CS","NONE"],["N-949",1580,5.5,"a","ENG","LEGACY"],["N-1858",1580,2.5,"a","ENG","NONE"],["N-1917",1580,4.5,"a","MATH","NONE"],["N-2091",1580,3.5,"d","ENG","LEGACY"],["N-71",1590,2.5,"a","ENG","NONE"],["N-334",1590,5.5,"a","ENG","LEGACY"],["N-713",1590,5.5,"w","ENG","LEGACY"],["N-1745",1590,5.0,"a","CS","NONE"],["N-1774",1590,5.5,"a","ENG","NONE"],["N-1872",1590,5.5,"a","CS","NONE"],["N-2041",1590,3.5,"a","CS","NONE"],["N-636",1600,5.0,"a","CS","NONE"]]}],"caveat":"People who were admitted post far more often than people who were denied, so every cluster looks rosier than the real applicant pool."},"kinds_check":{"separation":0.235,"shuffled":0.273,"stability":0.604,"verdict":"none","text":"No clear kinds at this college.","needs":{"separation":0.51,"margin":0.05,"stability":0.75,"loose_separation":0.26,"loose_stability":0.6}},"d_admitted":0.061,"d_denied":0.106,"gap":0.045,"lean":"closer_to_admitted","text":"Looks more like the people admitted here than the people denied.","steady":true,"flips":[],"parts":[{"part":"score","distance":0.09,"text":"close"},{"part":"activities","distance":0.071,"text":"close"},{"part":"major","distance":0.0,"text":"close"},{"part":"hooks","distance":0.143,"text":"close"},{"part":"residency","distance":0.0,"text":"close"}],"not_used":["GPA","essay","activity descriptions"],"nearest_admitted":[{"case_id":"N-811","sat":null,"act":null,"major":"CS","hooks":"FIRST-GEN","home_state":"MA","activities_rating":4.5,"outcome":"admitted","invented":false,"distance":0.018,"parts":{"activities":0.05,"major":0.0,"hooks":0.0,"residency":0.0}},{"case_id":"N-51","sat":null,"act":null,"major":"CS","hooks":"FIRST-GEN","home_state":null,"activities_rating":5.5,"outcome":"admitted","invented":false,"distance":0.022,"parts":{"activities":0.05,"major":0.0,"hooks":0.0}},{"case_id":"N-2104","sat":1460,"act":null,"major":"CS","hooks":"FIRST-GEN","home_state":null,"activities_rating":3.5,"outcome":"admitted","invented":false,"distance":0.046,"parts":{"score":0.025,"activities":0.15,"major":0.0,"hooks":0.0}}],"nearest_denied":[{"case_id":"N-1739","sat":1470,"act":null,"major":"CS","hooks":"FIRST-GEN","home_state":"PA","activities_rating":6.0,"outcome":"denied","invented":false,"distance":0.043,"parts":{"score":0.05,"activities":0.1,"major":0.0,"hooks":0.0,"residency":0.0}},{"case_id":"N-1741","sat":1470,"act":null,"major":"CS","hooks":"FIRST-GEN","home_state":"PA","activities_rating":6.0,"outcome":"denied","invented":false,"distance":0.043,"parts":{"score":0.05,"activities":0.1,"major":0.0,"hooks":0.0,"residency":0.0}},{"case_id":"N-1740","sat":1470,"act":null,"major":"CS","hooks":"FIRST-GEN","home_state":"PA","activities_rating":6.5,"outcome":"denied","invented":false,"distance":0.053,"parts":{"score":0.05,"activities":0.15,"major":0.0,"hooks":0.0,"residency":0.0}}],"kinds":[{"kind_id":"K1","name":"High score, CS, activities 7.5","size":95,"median_sat":1570,"median_activities":7.5,"top_major":"CS","medoid_case_id":"N-1789","distance":0.285,"nearest":false},{"kind_id":"K2","name":"Mid score, CS, activities 6.5","size":93,"median_sat":1510,"median_activities":6.5,"top_major":"CS","medoid_case_id":"N-959","distance":0.15,"nearest":true},{"kind_id":"K3","name":"Lower score, ENG, activities 6.5","size":43,"median_sat":1390,"median_activities":6.5,"top_major":"ENG","medoid_case_id":"N-656","distance":0.15,"nearest":false}],"changes":[],"changes_note":"Nothing we can measure here would move this.","points":[{"case_id":"N-0","sat":1440,"activities":2.0,"outcome":"admitted","kind_id":"K3"},{"case_id":"N-8","sat":1580,"activities":6.5,"outcome":"denied","kind_id":null},{"case_id":"N-12","sat":1530,"activities":7.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-42","sat":1570,"activities":8.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-59","sat":1330,"activities":2.5,"outcome":"admitted","kind_id":"K3"},{"case_id":"N-64","sat":1500,"activities":6.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-71","sat":1590,"activities":2.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-80","sat":1430,"activities":8.5,"outcome":"admitted","kind_id":"K3"},{"case_id":"N-81","sat":1400,"activities":5.0,"outcome":"admitted","kind_id":"K3"},{"case_id":"N-101","sat":1490,"activities":6.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-104","sat":1560,"activities":6.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-113","sat":1530,"activities":5.0,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-143","sat":1560,"activities":6.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-158","sat":1540,"activities":6.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-166","sat":1440,"activities":7.5,"outcome":"admitted","kind_id":"K3"},{"case_id":"N-191","sat":1480,"activities":8.2,"outcome":"waitlisted","kind_id":null},{"case_id":"N-210","sat":1540,"activities":7.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-238","sat":1490,"activities":8.5,"outcome":"waitlisted","kind_id":null},{"case_id":"N-254","sat":1540,"activities":8.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-258","sat":1540,"activities":5.0,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-262","sat":1530,"activities":7.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-272","sat":1430,"activities":6.5,"outcome":"admitted","kind_id":"K3"},{"case_id":"N-279","sat":1540,"activities":6.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-290","sat":1450,"activities":7.5,"outcome":"admitted","kind_id":"K3"},{"case_id":"N-303","sat":1400,"activities":6.5,"outcome":"waitlisted","kind_id":null},{"case_id":"N-311","sat":1540,"activities":5.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-318","sat":1560,"activities":7.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-334","sat":1590,"activities":5.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-337","sat":1570,"activities":1.0,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-359","sat":1510,"activities":6.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-363","sat":1480,"activities":4.0,"outcome":"denied","kind_id":null},{"case_id":"N-376","sat":1440,"activities":8.5,"outcome":"waitlisted","kind_id":null},{"case_id":"N-389","sat":1550,"activities":9.5,"outcome":"waitlisted","kind_id":null},{"case_id":"N-434","sat":1450,"activities":6.5,"outcome":"admitted","kind_id":"K3"},{"case_id":"N-480","sat":1280,"activities":1.0,"outcome":"admitted","kind_id":"K3"},{"case_id":"N-497","sat":1420,"activities":5.5,"outcome":"admitted","kind_id":"K3"},{"case_id":"N-507","sat":1560,"activities":8.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-514","sat":1590,"activities":6.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-538","sat":1520,"activities":5.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-544","sat":1540,"activities":2.5,"outcome":"admitted","kind_id":"K2"}]},"own":{"source":"Invented demo school history (not real students)","verified":true,"status":"not_enough","n_admitted":1,"n_denied":5,"n_waitlisted":0,"groups":{"status":"cant_say","reason":"The school's own cases carry no activities rating, so they cannot be placed in these clusters.","sat25":null,"sat75":null,"act_mid":6,"act_high":8,"min_n":5,"few_n":15,"left_out":0,"capped":false,"student_note":"","cells":[],"caveat":"People who were admitted post far more often than people who were denied, so every cluster looks rosier than the real applicant pool."},"kinds_check":null,"d_admitted":0.315,"d_denied":0.517,"gap":0.202,"lean":null,"text":"Not enough finished cases in one of the two groups to say which the student is closer to.","steady":null,"flips":[],"parts":[{"part":"score","distance":0.1,"text":"close"},{"part":"major","distance":1.0,"text":"far"},{"part":"hooks","distance":1.0,"text":"far"},{"part":"residency","distance":0.0,"text":"close"},{"part":"gpa","distance":0.1,"text":"close"}],"not_used":["activities rating","essay","activity descriptions"],"nearest_admitted":[{"case_id":"S-106","sat":1490,"act":null,"major":"BIO","hooks":"NONE","home_state":"NJ","activities_rating":null,"outcome":"admitted","invented":true,"activities_note":"Family business helper; Summer research at a university lab","essay_theme":"service","distance":0.315,"parts":{"score":0.1,"major":1.0,"hooks":1.0,"residency":0.0,"gpa":0.1}}],"nearest_denied":[{"case_id":"S-5","sat":1380,"act":null,"major":"PSYCH","hooks":"URM","home_state":"NJ","activities_rating":null,"outcome":"denied","invented":true,"activities_note":"Model UN delegate","essay_theme":"mentorship","distance":0.357,"parts":{"score":0.175,"major":1.0,"hooks":1.0,"residency":0.0,"gpa":0.14}},{"case_id":"S-68","sat":null,"act":26,"major":"CS","hooks":"NONE","home_state":"NJ","activities_rating":null,"outcome":"denied","invented":true,"activities_note":"Art portfolio and school gallery show","essay_theme":"leadership","distance":0.404,"parts":{"score":0.525,"major":0.0,"hooks":1.0,"residency":0.0,"gpa":0.34}},{"case_id":"S-74","sat":1330,"act":null,"major":"ARTS","hooks":"NONE","home_state":"NJ","activities_rating":null,"outcome":"denied","invented":true,"activities_note":"Art portfolio and school gallery show","essay_theme":"community","distance":0.419,"parts":{"score":0.3,"major":1.0,"hooks":1.0,"residency":0.0,"gpa":0.17}}],"kinds":[],"changes":[],"changes_note":"","points":[{"case_id":"S-5","sat":1380,"activities":null,"outcome":"denied","kind_id":null},{"case_id":"S-45","sat":1010,"activities":null,"outcome":"denied","kind_id":null},{"case_id":"S-68","sat":1240,"activities":null,"outcome":"denied","kind_id":null},{"case_id":"S-74","sat":1330,"activities":null,"outcome":"denied","kind_id":null},{"case_id":"S-80","sat":1240,"activities":null,"outcome":"denied","kind_id":null},{"case_id":"S-106","sat":1490,"activities":null,"outcome":"admitted","kind_id":null}],"invented":true},"caveat":"Closeness compares this student with people who chose to post their results. It is not a forecast."}},{"id":"186380","name":"Rutgers University-New Brunswick","state":"NJ","control":"public","admit_rate":0.582,"sat25":1270,"sat75":1480,"act25":28,"act75":33,"cost_year":37000,"source":"US Department of Education, College Scorecard","in_data":true,"label":{"state":"target","text":"Target","rule_id":"R4","rule_text":"The score is inside the college's middle range (1270 to 1480).","score_used":1450,"score_kind":"SAT","inputs":{"sat25":1270,"sat75":1480,"admit_rate":0.582},"not_used":["GPA","activities","essay"],"caveats":["The score range covers only students who sent scores."],"steady":false,"flips":[{"cause":"score 30 points higher","to":"likely"}],"publishers":[{"name":"BigFuture","label":"target"},{"name":"Princeton Review","label":"target"},{"name":"Scoir","label":"likely"},{"name":"Appily","label":"target"},{"name":"CollegeVine","label":"target"}],"publishers_disagree":true},"cases":{"needed":15,"own":{"source":"Your school's own finished cases (SYNTHETIC demo data)","verified":true,"status":"ok","n":17,"admitted":13,"denied":3,"waitlisted":1,"matched_on":["SAT within 100 points"],"relaxed":["hook status","major group","SAT widened to 100"],"examples":[{"case_id":"S-3","sat":1430,"act":null,"major":"ENG","hooks":"none","home_state":"NJ","activities_note":"Varsity track; part-time job","essay_theme":"work","outcome":"admitted","cycle_year":2025}]},"national":{"source":"Self-reported public posts (r/collegeresults)","verified":false,"status":"not_enough","n":9,"admitted":7,"denied":1,"waitlisted":1,"matched_on":["SAT within 100 points"],"relaxed":["hook status","major group","SAT widened to 100"],"examples":[]},"official_admit_rate":0.582,"pool_admit_share_all":0.7,"overcount":1.2,"caveat":"People who post their results are admitted far more often than applicants overall. Read these as examples, not odds."},"says":[],"myths":[],"cost_note":"Sticker cost is about $37,000 a year in-state. What this family would actually pay is not known here.","flags":[],"closeness":{"semantic":{"status":"off"},"essay_retrieval":[],"weights":{"score":0.45,"activities":0.2,"major":0.15,"hooks":0.1,"residency":0.1,"gpa":0.2,"essay":0.2,"activity_text":0.15},"needed":15,"neighbours":7,"student":{"score":1450,"converted":false,"activities":5.0,"activities_from":"estimated","activities_why":["1 activity listed","recognition beyond the school"],"activities_rule":"4 for one activity, +1 for each further activity up to 4, +1 for a leading role, +1 for recognition beyond the school, +1 for sustained commitment (years, or weekly hours); never over 10."},"national":{"source":"Public posts on Reddit (r/collegeresults), self-reported","verified":false,"status":"not_enough","n_admitted":116,"n_denied":3,"n_waitlisted":1,"groups":{"status":"ok","reason":"","sat25":1310,"sat75":1500,"act_mid":6,"act_high":8,"min_n":5,"few_n":15,"left_out":22,"capped":false,"student_note":"","cells":[{"score_band":"below","activities_band":"high","admitted":0,"waitlisted":0,"denied":0,"n":0,"state":"not_enough","is_student":false,"cases":[]},{"score_band":"inside","activities_band":"high","admitted":2,"waitlisted":0,"denied":0,"n":2,"state":"not_enough","is_student":false,"cases":[["N-2019",1500,8.5,"a","CS","NONE"],["N-2093",1330,8.5,"a","ENG","NONE"]]},{"score_band":"above","activities_band":"high","admitted":6,"waitlisted":0,"denied":0,"n":6,"state":"few","is_student":false,"cases":[["N-221",1520,8.5,"a","CS","NONE"],["N-1470",1540,8.5,"a","CS","NONE"],["N-42",1570,8.5,"a","CS","NONE"],["N-358",1570,8.5,"a","BIO","NONE"],["N-1062",1570,8.5,"a","CS","NONE"],["N-722",1590,8.5,"a","BIO","NONE"]]},{"score_band":"below","activities_band":"mid","admitted":2,"waitlisted":0,"denied":0,"n":2,"state":"not_enough","is_student":false,"cases":[["N-2190",1280,6.5,"a","CS","NONE"],["N-1145",1180,6.5,"a","PREMED","URM"]]},{"score_band":"inside","activities_band":"mid","admitted":16,"waitlisted":0,"denied":1,"n":17,"state":"ok","is_student":false,"cases":[["N-194",1460,6.5,"a","","NONE"],["N-2012",1460,7.5,"a","CS","NONE"],["N-2144",1460,6.5,"a","CS","NONE"],["N-148",1430,6.5,"a","BUSINESS","URM"],["N-1143",1470,7.5,"a","CS","NONE"],["N-1256",1470,6.5,"a","CS","NONE"],["N-1439",1420,6.5,"a","PREMED","URM"],["N-1790",1420,7.5,"a","BUSINESS","NONE"],["N-1337",1490,6.5,"a","CS","URM"],["N-2134",1410,6.5,"a","","NONE"],["N-152",1500,6.5,"a","BIO","NONE"],["N-256",1500,6.5,"a","CS","NONE"],["N-612",1500,7.5,"a","BIO","NONE"],["N-1042",1500,6.5,"a","PHYSICS","URM"],["N-1335",1500,6.5,"a","CS","NONE"],["N-1729",1500,7.5,"d","BIO","NONE"],["N-1760",1500,6.5,"a","CS","NONE"]]},{"score_band":"above","activities_band":"mid","admitted":24,"waitlisted":0,"denied":0,"n":24,"state":"ok","is_student":false,"cases":[["N-1022",1510,6.5,"a","","FIRST-GEN"],["N-926",1530,6.5,"a","ENG","NONE"],["N-1189",1530,7.5,"a","CS","NONE"],["N-1640",1530,6.5,"a","CS","LEGACY"],["N-2003",1530,7.5,"a","PREMED","URM"],["N-158",1540,6.5,"a","POLISCI","NONE"],["N-208",1540,7.5,"a","BIO","NONE"],["N-712",1540,6.5,"a","ENG","NONE"],["N-914",1540,7.5,"a","ENG","LEGACY"],["N-1140",1540,7.5,"a","CS","NONE"],["N-1708",1540,6.5,"a","BIO","NONE"],["N-2087",1540,7.5,"a","BIO","NONE"],["N-2096",1540,6.5,"a","BUSINESS","NONE"],["N-2097",1540,6.5,"a","BUSINESS","NONE"],["N-1032",1550,6.5,"a","CS","NONE"],["N-1579",1550,7.0,"a","POLISCI","NONE"],["N-2030",1550,6.5,"a","CS","NONE"],["N-2073",1550,7.5,"a","ENG","NONE"],["N-2135",1550,7.5,"a","CS","NONE"],["N-883",1560,6.5,"a","CS","LEGACY"],["N-954",1560,7.5,"a","CS","LEGACY"],["N-5",1580,7.5,"a","CS","NONE"],["N-468",1580,6.5,"a","","NONE"],["N-1649",1580,6.5,"a","CS","NONE"]]},{"score_band":"below","activities_band":"low","admitted":6,"waitlisted":0,"denied":0,"n":6,"state":"few","is_student":false,"cases":[["N-643",1300,5.0,"a","","URM"],["N-1134",1300,5.0,"a","BUSINESS","NONE"],["N-1755",1280,5.5,"a","ENG","NONE"],["N-2043",1280,1.0,"a","BUSINESS","NONE"],["N-889",1230,4.5,"a","BUSINESS","LEGACY"],["N-1489",1180,1.0,"a","ENG","NONE"]]},{"score_band":"inside","activities_band":"low","admitted":23,"waitlisted":1,"denied":1,"n":25,"state":"ok","is_student":true,"cases":[["N-222",1450,2.5,"a","CS","URM"],["N-522",1450,4.5,"a","BUSINESS","FIRST-GEN"],["N-1749",1450,1.0,"w","","URM"],["N-40",1460,5.5,"a","CS","URM"],["N-921",1460,2.5,"a","BUSINESS","NONE"],["N-983",1440,1.0,"a","CS","NONE"],["N-1296",1440,2.0,"a","CS","FIRST-GEN"],["N-746",1470,5.0,"a","OTHER","LEGACY"],["N-650",1480,5.5,"a","BUSINESS","LEGACY"],["N-1874",1480,3.5,"a","PSYCH","NONE"],["N-1925",1480,3.5,"a","BIO","LGBT"],["N-2194",1480,2.5,"d","BUSINESS","FIRST-GEN"],["N-2205",1480,3.5,"a","CS","FIRST-GEN"],["N-2157",1410,5.0,"a","HUMANITIES","LEGACY"],["N-247",1500,5.5,"a","POLISCI","URM"],["N-448",1500,3.5,"a","CS","NONE"],["N-1906",1500,5.5,"a","ENG","LGBT"],["N-1967",1500,3.5,"a","ENG","NONE"],["N-1968",1500,3.5,"a","ENG","NONE"],["N-2153",1500,4.5,"a","CS","LEGACY"],["N-2163",1500,5.5,"a","","NONE"],["N-2164",1500,5.5,"a","","NONE"],["N-1962",1360,5.5,"a","CS","URM"],["N-59",1330,2.5,"a","CS","NONE"],["N-725",1320,5.5,"a","CS","FIRST-GEN"]]},{"score_band":"above","activities_band":"low","admitted":16,"waitlisted":0,"denied":0,"n":16,"state":"ok","is_student":false,"cases":[["N-1568",1510,3.5,"a","PSYCH","LEGACY"],["N-1894",1510,2.5,"a","HUMANITIES","URM"],["N-2070",1510,5.5,"a","","NONE"],["N-2098",1510,4.0,"a","POLISCI","NONE"],["N-591",1520,3.0,"a","PSYCH","NONE"],["N-2131",1520,2.5,"a","CS","URM"],["N-1562",1530,5.5,"a","CS","NONE"],["N-520",1540,3.5,"a","ENG","NONE"],["N-544",1540,2.5,"a","CS","NONE"],["N-1622",1540,5.5,"a","BUSINESS","NONE"],["N-2116",1540,5.5,"a","CS","NONE"],["N-307",1550,5.5,"a","ENG","LGBT"],["N-450",1550,4.5,"a","CS","NONE"],["N-206",1560,5.5,"a","CS","NONE"],["N-435",1570,5.5,"a","","NONE"],["N-1514",1580,3.5,"a","CS","NONE"]]}],"caveat":"People who were admitted post far more often than people who were denied, so every cluster looks rosier than the real applicant pool."},"kinds_check":{"separation":0.289,"shuffled":0.25,"stability":0.332,"verdict":"none","text":"No clear kinds at this college.","needs":{"separation":0.51,"margin":0.05,"stability":0.75,"loose_separation":0.26,"loose_stability":0.6}},"d_admitted":0.165,"d_denied":0.482,"gap":0.317,"lean":null,"text":"Not enough finished cases in one of the two groups to say which the student is closer to.","steady":null,"flips":[],"parts":[{"part":"score","distance":0.088,"text":"close"},{"part":"activities","distance":0.143,"text":"close"},{"part":"major","distance":0.0,"text":"close"},{"part":"hooks","distance":0.429,"text":"some way off"},{"part":"residency","distance":1.0,"text":"far"}],"not_used":["GPA","essay","activity descriptions"],"nearest_admitted":[{"case_id":"N-1296","sat":1440,"act":null,"major":"CS","hooks":"FIRST-GEN","home_state":null,"activities_rating":2.0,"outcome":"admitted","invented":false,"distance":0.079,"parts":{"score":0.025,"activities":0.3,"major":0.0,"hooks":0.0}},{"case_id":"N-1022","sat":1510,"act":null,"major":null,"hooks":"FIRST-GEN","home_state":null,"activities_rating":6.5,"outcome":"admitted","invented":false,"distance":0.13,"parts":{"score":0.15,"activities":0.15,"hooks":0.0}},{"case_id":"N-2205","sat":1480,"act":null,"major":"CS","hooks":"FIRST-GEN","home_state":"FL","activities_rating":3.5,"outcome":"admitted","invented":false,"distance":0.164,"parts":{"score":0.075,"activities":0.15,"major":0.0,"hooks":0.0,"residency":1.0}}],"nearest_denied":[{"case_id":"N-2194","sat":1480,"act":null,"major":"BUSINESS","hooks":"FIRST-GEN","home_state":"GA","activities_rating":2.5,"outcome":"denied","invented":false,"distance":0.334,"parts":{"score":0.075,"activities":0.25,"major":1.0,"hooks":0.0,"residency":1.0}},{"case_id":"N-1729","sat":1500,"act":null,"major":"BIO","hooks":"NONE","home_state":"WA","activities_rating":7.5,"outcome":"denied","invented":false,"distance":0.456,"parts":{"score":0.125,"activities":0.25,"major":1.0,"hooks":1.0,"residency":1.0}},{"case_id":"N-1846","sat":null,"act":null,"major":"ENG","hooks":"NONE","home_state":"CA","activities_rating":5.5,"outcome":"denied","invented":false,"distance":0.655,"parts":{"activities":0.05,"major":1.0,"hooks":1.0,"residency":1.0}}],"kinds":[{"kind_id":"K1","name":"High score, CS, activities 6.5","size":62,"median_sat":1540,"median_activities":6.5,"top_major":"CS","medoid_case_id":"N-1022","distance":0.15,"nearest":false},{"kind_id":"K2","name":"Lower score, CS, activities 5.5","size":21,"median_sat":1460,"median_activities":5.5,"top_major":"CS","medoid_case_id":"N-194","distance":0.063,"nearest":true},{"kind_id":"K3","name":"Lower score, CS, activities 5.2","size":12,"median_sat":1290,"median_activities":5.2,"top_major":"CS","medoid_case_id":"N-643","distance":0.26,"nearest":false}],"changes":[],"changes_note":"","points":[{"case_id":"N-5","sat":1580,"activities":7.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-40","sat":1460,"activities":5.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-42","sat":1570,"activities":8.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-59","sat":1330,"activities":2.5,"outcome":"admitted","kind_id":"K3"},{"case_id":"N-148","sat":1430,"activities":6.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-152","sat":1500,"activities":6.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-158","sat":1540,"activities":6.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-194","sat":1460,"activities":6.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-206","sat":1560,"activities":5.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-208","sat":1540,"activities":7.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-221","sat":1520,"activities":8.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-222","sat":1450,"activities":2.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-247","sat":1500,"activities":5.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-256","sat":1500,"activities":6.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-307","sat":1550,"activities":5.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-358","sat":1570,"activities":8.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-435","sat":1570,"activities":5.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-448","sat":1500,"activities":3.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-450","sat":1550,"activities":4.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-468","sat":1580,"activities":6.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-520","sat":1540,"activities":3.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-522","sat":1450,"activities":4.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-544","sat":1540,"activities":2.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-591","sat":1520,"activities":3.0,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-612","sat":1500,"activities":7.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-643","sat":1300,"activities":5.0,"outcome":"admitted","kind_id":"K3"},{"case_id":"N-650","sat":1480,"activities":5.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-712","sat":1540,"activities":6.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-722","sat":1590,"activities":8.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-725","sat":1320,"activities":5.5,"outcome":"admitted","kind_id":"K3"},{"case_id":"N-746","sat":1470,"activities":5.0,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-883","sat":1560,"activities":6.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-889","sat":1230,"activities":4.5,"outcome":"admitted","kind_id":"K3"},{"case_id":"N-914","sat":1540,"activities":7.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-921","sat":1460,"activities":2.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-926","sat":1530,"activities":6.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-954","sat":1560,"activities":7.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-983","sat":1440,"activities":1.0,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-1022","sat":1510,"activities":6.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-1032","sat":1550,"activities":6.5,"outcome":"admitted","kind_id":"K1"}]},"own":{"source":"Invented demo school history (not real students)","verified":true,"status":"not_enough","n_admitted":4,"n_denied":6,"n_waitlisted":0,"groups":{"status":"cant_say","reason":"The school's own cases carry no activities rating, so they cannot be placed in these clusters.","sat25":null,"sat75":null,"act_mid":6,"act_high":8,"min_n":5,"few_n":15,"left_out":0,"capped":false,"student_note":"","cells":[],"caveat":"People who were admitted post far more often than people who were denied, so every cluster looks rosier than the real applicant pool."},"kinds_check":null,"d_admitted":0.364,"d_denied":0.523,"gap":0.159,"lean":null,"text":"Not enough finished cases in one of the two groups to say which the student is closer to.","steady":null,"flips":[],"parts":[{"part":"score","distance":0.163,"text":"some way off"},{"part":"major","distance":1.0,"text":"far"},{"part":"hooks","distance":1.0,"text":"far"},{"part":"residency","distance":0.0,"text":"close"},{"part":"gpa","distance":0.205,"text":"some way off"}],"not_used":["activities rating","essay","activity descriptions"],"nearest_admitted":[{"case_id":"S-105","sat":1490,"act":null,"major":"BIO","hooks":"NONE","home_state":"NJ","activities_rating":null,"outcome":"admitted","invented":true,"activities_note":"Family business helper; Summer research at a university lab","essay_theme":"service","distance":0.315,"parts":{"score":0.1,"major":1.0,"hooks":1.0,"residency":0.0,"gpa":0.1}},{"case_id":"S-48","sat":1390,"act":null,"major":"POLISCI","hooks":"NONE","home_state":"NJ","activities_rating":null,"outcome":"admitted","invented":true,"activities_note":"Student newspaper editor; Robotics club captain","essay_theme":"curiosity","distance":0.349,"parts":{"score":0.15,"major":1.0,"hooks":1.0,"residency":0.0,"gpa":0.16}},{"case_id":"S-59","sat":1370,"act":null,"major":"BUSINESS","hooks":"NONE","home_state":"NJ","activities_rating":null,"outcome":"admitted","invented":true,"activities_note":"Family business helper; Summer research at a university lab","essay_theme":"mentorship","distance":0.362,"parts":{"score":0.2,"major":1.0,"hooks":1.0,"residency":0.0,"gpa":0.11}}],"nearest_denied":[{"case_id":"S-66","sat":1350,"act":null,"major":"CS","hooks":"NONE","home_state":"NJ","activities_rating":null,"outcome":"denied","invented":true,"activities_note":"Theater stage crew; Part-time job at a grocery store","essay_theme":"resilience","distance":0.217,"parts":{"score":0.25,"major":0.0,"hooks":1.0,"residency":0.0,"gpa":0.02}},{"case_id":"S-1","sat":1140,"act":null,"major":"CS","hooks":"FIRST-GEN","home_state":"NJ","activities_rating":null,"outcome":"denied","invented":true,"activities_note":"School orchestra first chair; Science Olympiad","essay_theme":"identity","distance":0.409,"parts":{"score":0.775,"major":0.0,"hooks":0.0,"residency":0.0,"gpa":0.3}},{"case_id":"S-42","sat":1340,"act":null,"major":"POLISCI","hooks":"NONE","home_state":"PA","activities_rating":null,"outcome":"denied","invented":true,"activities_note":"Hospital volunteer","essay_theme":"family","distance":0.544,"parts":{"score":0.275,"major":1.0,"hooks":1.0,"residency":1.0,"gpa":0.35}}],"kinds":[],"changes":[],"changes_note":"","points":[{"case_id":"S-1","sat":1140,"activities":null,"outcome":"denied","kind_id":null},{"case_id":"S-29","sat":1240,"activities":null,"outcome":"denied","kind_id":null},{"case_id":"S-37","sat":1080,"activities":null,"outcome":"denied","kind_id":null},{"case_id":"S-42","sat":1340,"activities":null,"outcome":"denied","kind_id":null},{"case_id":"S-48","sat":1390,"activities":null,"outcome":"admitted","kind_id":null},{"case_id":"S-59","sat":1370,"activities":null,"outcome":"admitted","kind_id":null},{"case_id":"S-61","sat":1330,"activities":null,"outcome":"denied","kind_id":null},{"case_id":"S-66","sat":1350,"activities":null,"outcome":"denied","kind_id":null},{"case_id":"S-105","sat":1490,"activities":null,"outcome":"admitted","kind_id":null},{"case_id":"S-116","sat":1370,"activities":null,"outcome":"admitted","kind_id":null}],"invented":true},"caveat":"Closeness compares this student with people who chose to post their results. It is not a forecast."}},{"id":"203535","name":"Kenyon College","state":"OH","control":"private","admit_rate":0.31,"sat25":null,"sat75":null,"act25":null,"act75":null,"cost_year":85000,"source":"US Department of Education, College Scorecard","in_data":true,"label":{"state":"cant_say","text":"Can't say","rule_id":"R2","rule_text":"This college publishes no test score range, so there is nothing to compare the student's score with.","score_used":1450,"score_kind":"SAT","inputs":{"sat25":null,"sat75":null,"admit_rate":0.31},"not_used":["GPA","activities","essay"],"caveats":[],"steady":true,"flips":[],"publishers":[],"publishers_disagree":false},"cases":{"needed":15,"own":{"source":"Your school's own finished cases (SYNTHETIC demo data)","verified":true,"status":"none","n":0,"admitted":0,"denied":0,"waitlisted":0,"matched_on":[],"relaxed":[],"examples":[]},"national":{"source":"Self-reported public posts (r/collegeresults)","verified":false,"status":"none","n":0,"admitted":0,"denied":0,"waitlisted":0,"matched_on":[],"relaxed":[],"examples":[]},"official_admit_rate":0.31,"pool_admit_share_all":null,"overcount":null,"caveat":"No finished cases for this college in either pool."},"says":[],"myths":[],"cost_note":"Sticker cost is about $85,000 a year. What this family would actually pay is not known here.","flags":[],"closeness":{"semantic":{"status":"off"},"essay_retrieval":[],"weights":{"score":0.45,"activities":0.2,"major":0.15,"hooks":0.1,"residency":0.1,"gpa":0.2,"essay":0.2,"activity_text":0.15},"needed":15,"neighbours":7,"student":{"score":1450,"converted":false,"activities":5.0,"activities_from":"estimated","activities_why":["1 activity listed","recognition beyond the school"],"activities_rule":"4 for one activity, +1 for each further activity up to 4, +1 for a leading role, +1 for recognition beyond the school, +1 for sustained commitment (years, or weekly hours); never over 10."},"national":{"source":"Public posts on Reddit (r/collegeresults), self-reported","verified":false,"status":"none","n_admitted":0,"n_denied":0,"n_waitlisted":0,"groups":{"status":"cant_say","reason":"No finished cases for this college in this pool.","sat25":null,"sat75":null,"act_mid":6,"act_high":8,"min_n":5,"few_n":15,"left_out":0,"capped":false,"student_note":"","cells":[],"caveat":"People who were admitted post far more often than people who were denied, so every cluster looks rosier than the real applicant pool."},"kinds_check":null,"text":"No finished cases for this college in this pool."},"own":{"source":"Your school's finished cases","verified":true,"status":"none","n_admitted":0,"n_denied":0,"n_waitlisted":0,"groups":{"status":"cant_say","reason":"The school's own cases carry no activities rating, so they cannot be placed in these clusters.","sat25":null,"sat75":null,"act_mid":6,"act_high":8,"min_n":5,"few_n":15,"left_out":0,"capped":false,"student_note":"","cells":[],"caveat":"People who were admitted post far more often than people who were denied, so every cluster looks rosier than the real applicant pool."},"kinds_check":null,"text":"No finished cases for this college in this pool.","invented":false},"caveat":"Closeness compares this student with people who chose to post their results. It is not a forecast."}},{"id":null,"name":"Some College Not In Our File","state":null,"control":null,"admit_rate":null,"sat25":null,"sat75":null,"act25":null,"act75":null,"cost_year":null,"source":null,"in_data":false,"label":{"state":"outside_data","text":"Outside our data","rule_id":"R0","rule_text":"This college is not in the 300-college file, so nothing is said about it.","score_used":null,"score_kind":null,"inputs":{},"not_used":[],"caveats":[],"steady":true,"flips":[],"publishers":[],"publishers_disagree":false},"cases":null,"closeness":null,"says":[],"myths":[],"cost_note":null,"flags":[]}],"balance":{"counts":{"reach":1,"target":2,"likely":0,"cant_say":1,"outside_data":1},"warnings":[{"id":"no_likely","text":"There is no likely college on this list."},{"id":"short_list","text":"Only 3 colleges on this list could be labelled."}],"suggestions":[{"id":"185828","name":"New Jersey Institute of Technology","would_be":"likely","admit_rate":0.66,"sat25":1180,"sat75":1400,"cost_year":36000,"tuition_note":"In-state tuition applies","why":"The score is at or above the 75th percentile and the college admits about two in three applicants."},{"id":"204796","name":"Ohio State University-Main Campus","would_be":"target","admit_rate":0.53,"sat25":1300,"sat75":1470,"cost_year":30000,"tuition_note":"Out-of-state tuition applies","why":"The score is inside the middle range and the college admits about half of applicants."}],"cost_notes":[{"name":"Cornell University","text":"Sticker cost is about $88,000 a year. What this family would actually pay is not known here."}]},"checks":{"sentences_shown":14,"sentences_hidden":1,"hidden_reasons":["A number in the sentence was not in its source row."]},"prism":{"status":"off","why":"No PRISM key is set, so nothing was recorded.","session_id":null,"records_sent":0,"guardrail":"local check only","evaluator":null,"kb":"off"},"refusals":["No personal chance of admission is given. The counts above are examples from finished cases, shown beside the official admit rate.","The essay is never rated and never changes a label."],"closeness_check":{"generated_at":"2026-10-10T13:57:58-04:00","sampled":400,"used":382,"skipped_small_groups":18,"seed":20261010,"neighbours":7,"lean_gap":0.03,"source":"Self-reported public posts (r/collegeresults)","rows":[{"lean":"closer_to_admitted","admitted":39,"denied":17,"n":56},{"lean":"in_between","admitted":75,"denied":125,"n":200},{"lean":"closer_to_denied","admitted":25,"denied":101,"n":126}],"caveat":"Counted on self-reported public posts, each person hidden before their own lean was computed. People who post are admitted far more often than applicants overall, so this says how the lean sorts posters, not applicants."},"closeness_method":{"parts":[{"part":"score","name":"score","weight":0.45,"distance":"score difference / 400 SAT points, capped at 1","student":"SAT, or ACT converted to the SAT scale","case":"SAT, or ACT converted","pools":"both","required":true},{"part":"activities","name":"activities rating","weight":0.2,"distance":"rating difference / 10","student":"the counselor's 0 to 10 rating (optional)","case":"self-rated activities and awards, 0 to 10","pools":"national only","required":false},{"part":"major","name":"major group","weight":0.15,"distance":"0 same group, 1 different","student":"intended major, or the essay reader's tag when both models agreed","case":"stated major","pools":"both","required":false},{"part":"hooks","name":"hook status","weight":0.1,"distance":"0 same set of hooks, 1 different","student":"first-gen, legacy, under-represented, athlete, or none","case":"the same set","pools":"both","required":false},{"part":"residency","name":"residency","weight":0.1,"distance":"0 if both in-state or both out-of-state for this college, else 1","student":"home state","case":"home state","pools":"both, public colleges only","required":false},{"part":"gpa","name":"GPA","weight":0.2,"distance":"GPA difference / 1 on a 4.0 scale, capped at 1","student":"GPA, converted to a 4.0 scale","case":"GPA in the school's own file","pools":"own only","required":false}],"never_used":["essay text","activity descriptions","race","gender","income","class rank","the essay/recommendation/interview self-rating"],"neighbours":7,"needed":15,"lean_gap":0.03,"change_gain":0.02,"max_changes":3,"score_steps":[30,60,100],"rating_steps":[1,2],"close":0.15,"far":0.5,"steady":{"neighbours":[5,10],"score":[-30,30]},"kinds":{"k":3,"min_admitted":30,"cap":300,"rounds":20,"seed":20261010,"parts":["score","activities","major"],"score_band":40,"rating_band":1.0},"points_cap":300,"check":{"n":400,"seed":20261010},"libraries":{"engine":["csv","json","functools.lru_cache","random","statistics","collections.Counter","pathlib"],"not_used":["numpy","scikit-learn","pandas","text embeddings","any model call"],"screen":["plain HTML, CSS and JavaScript","inline SVG drawn by hand","no chart library, no framework, no build step"]}}}/*FIXTURE_END*/;
/* A copy of docs/features.json, kept in step by tools/sync_features.py. The About page and the README both read that file. */
var FEATURES = /*FEATURES_START*/[{"id":"story","name":"One story in five sections","status":"works","when":"afternoon","what":"Who you are, where you stand, what is in your hands, your plan, and Essay Similarity Search. A waypoint bar links the five sections.","where":"The whole screen after \"Show where they stand\".","files":"web/app.js, web/index.html"},{"id":"label","name":"Reach / target / likely label","status":"works","when":"morning","what":"Each college gets a label from a written rule in code, from its published admit rate and middle score range. Never from a model.","where":"Chapter 2; tap a college, \"How we got this\".","files":"engine/labels.py"},{"id":"edge","name":"This one is close, and publishers disagree","status":"works","when":"morning","what":"Every label is rerun with the score 30 points either way and the admit rate 5 points lower; a label that flips is marked. Five published rulebooks are run on the same score and any disagreement is shown.","where":"Chapter 2 and \"How we got this\".","files":"engine/labels.py, data/colleges/rulebooks.json"},{"id":"picture","name":"Where you stand: the trail map","status":"works","when":"morning","what":"Every college's middle score band on one line, the distance to the student's score written on each bar, and a label beside it.","where":"Chapter 2.","files":"web/app.js"},{"id":"cases","name":"Example cases, two pools kept apart","status":"works","when":"morning","what":"Counts of admitted, not admitted and waitlisted among finished cases like this student, with n and the official admit rate beside them. The school's own cases and the public self-reported pool are never added together, and the public pool's over-count is stated.","where":"Tap a college, \"Who you resemble\".","files":"engine/cases.py, engine/caselog.py"},{"id":"closeness","name":"Who you resemble: closer to the admitted or the not admitted","status":"works","when":"afternoon","what":"Per college, the distance from the student to the 7 nearest admitted and the 7 nearest not-admitted cases, over score, activities rating, major group, hooks and residency. A lean, a steady test, the parts that are close or far, and the nearest cases of each. A distance, never a percentage; the label is untouched.","where":"Tap a college, \"Who you resemble\".","files":"engine/similarity.py"},{"id":"rings","name":"Rings picture","status":"works","when":"afternoon","what":"The student at the centre, one dot per college as far out as the student is from the people admitted there. Hollow when there are too few cases; on an outer ring when it cannot be placed.","where":"Chapter 2, \"Other pictures: Rings\".","files":"web/app.js"},{"id":"mindmap","name":"Map picture","status":"works","when":"afternoon","what":"The student in the middle, a branch per label, a node per college, and under each college its nearest kind of admitted student (only when the kinds pass their check) and its three nearest admitted cases.","where":"Chapter 2, \"Other pictures: Map\".","files":"web/app.js"},{"id":"groups","name":"Clusters picture","status":"works","when":"evening","what":"For one college, a 3 by 3 grid of rule-defined clusters of past applicants (score below, inside or above the published range; activities rating low, middle or high), each with its real finished cases as dots and counts, and the student's own cluster outlined. A cluster grows when pressed and lists its cases. Beside it, a three-number check on the computer-made kinds; kind names appear anywhere on the screen only when that check passes.","where":"Chapter 2, \"Other pictures: Clusters\".","files":"engine/similarity.py, web/app.js, docs/req/GROUPS_REQUIREMENTS.md"},{"id":"resemble","name":"Scatter, part bars, kinds and changes","status":"works","when":"afternoon","what":"A scatter of that college's cases by score and activities rating with the student as a star and the three kinds' medoids ringed; a bar per part; three kinds of admitted student found by k-medoids and named from counts, shown only when they pass a separation, shuffle and stability check; and what would bring the student closer (score, activities, a named major; never hooks, home state or GPA).","where":"Tap a college, \"Who you resemble\".","files":"engine/similarity.py, web/app.js"},{"id":"semantic","name":"Essay and activity text in closeness","status":"works with a key","when":"afternoon","what":"With a model key, masked essay and activity text are embedded and become two more parts of the distance, compared only where both profiles have text. Vectors stay in memory. Without a key the structured parts carry the comparison.","where":"Tap a college, \"Who you resemble\", with the working shown.","files":"engine/semantic.py, engine/similarity.py"},{"id":"rating","name":"Activities rating input","status":"works","when":"afternoon","what":"A 0 to 10 dial for the counselor's own rating of the student's activities, used only by closeness and the clusters. When the dial is not set, a written rule estimates a rating from the activities listed (count, a leading role, recognition beyond the school, sustained commitment) and the screen says so.","where":"Counselor tools, \"Change the details\".","files":"web/index.html, engine/similarity.py"},{"id":"says","name":"What the college says it weighs","status":"works","when":"morning","what":"Statements from each college's own Common Data Set form, each with its field, year and source link, checked in code and confirmed against a knowledge base. Common beliefs are checked against the form.","where":"Tap a college, \"What the college says\".","files":"engine/claims.py, data/cds/, data/kb/"},{"id":"fit","name":"What the college looks for, beside the profile","status":"works","when":"afternoon","what":"For each factor the college says it reads, whether it is in this profile, not yet, or cannot be seen here. Three neutral states and no total: it is not a score.","where":"Chapter 3.","files":"engine/pipeline.py"},{"id":"balance","name":"List balance and suggested fills","status":"works","when":"morning","what":"Warnings when a list is reach-heavy, has no likely or no target, piles onto very selective colleges, or is short. Suggested colleges that would be likely or target, preferring the home state.","where":"Chapter 2 headline and caution; chapter 3.","files":"engine/balance.py"},{"id":"whatif","name":"\"What if the score were…\" slider","status":"works","when":"morning","what":"Moves the student's score and re-labels the whole list as it moves, saying which colleges change at which score. Labels only; nothing else is re-run.","where":"Chapter 3.","files":"engine/pipeline.py, web/app.js"},{"id":"cost","name":"Cost: sticker price and what families paid","status":"works","when":"afternoon","what":"The published sticker cost beside the federal average paid after grants, by income band when given. One family's price can differ, and the screen says so.","where":"Chapter 3 and each college.","files":"engine/colleges.py"},{"id":"plan","name":"Your plan, and a sheet to print","status":"works","when":"afternoon","what":"Five things to do this month from the list and its gaps, and a one-page print layout for the family in plain words.","where":"Chapter 4.","files":"web/app.js, web/style.css"},{"id":"tracker","name":"Keep track, and pay it forward","status":"works","when":"afternoon","what":"A status for each college (considering, applying, submitted, result). When a result comes in it becomes a finished case for next year's students, with no names.","where":"Chapter 4.","files":"engine/tracker.py"},{"id":"essay","name":"Essay notes with quotes, after masking","status":"works with a key","when":"morning","what":"Names, addresses, phones and dates are masked, then one model reads the essay and returns observations with word-for-word quotes; code drops any note whose quote is not in the essay. A second model tags the major independently. An essay with instructions aimed at an AI is stopped twice.","where":"Chapter 1; Counselor tools, \"Questions to ask\".","files":"engine/privacy.py, engine/reader.py, engine/nicrron.py, engine/prism.py"},{"id":"working","name":"Show the working","status":"works","when":"afternoon","what":"One switch reveals every source, rule, check and step behind the screen: the five steps, what code did and what a model did, sentences hidden by checks, the privacy record, and the closeness check table.","where":"The switch in the header.","files":"web/app.js, engine/pipeline.py"},{"id":"about","name":"About, and How we worked this out","status":"works","when":"afternoon","what":"A tour with live buttons; the parts and weights, the algorithm as a diagram, the libraries, the choices made, every data source with what was taken from it, and this feature list. Weights and thresholds are read from the engine, not typed into the page.","where":"\"About\" in the header; Counselor tools, \"How we worked this out\".","files":"web/app.js, engine/similarity.py"},{"id":"addcase","name":"Add a finished case","status":"works","when":"morning","what":"A counselor records a finished case for the school's own pool. Anything that looks like a name, email, phone or date of birth is refused.","where":"Counselor tools, \"Add a finished case\".","files":"engine/caselog.py, server.py"},{"id":"refusal","name":"No personal chance of admission","status":"works","when":"morning","what":"The screen never shows a percentage for the student. Asking why gets the measured over-count of the public pool and a pointer to the evidence instead.","where":"\"Why there is no percentage\" in chapter 2; every count sits beside the official admit rate.","files":"engine/cases.py, web/app.js"},{"id":"check","name":"Holds-up check for closeness","status":"works","when":"afternoon","what":"400 past posters, each hidden in turn, their lean computed and their real outcome counted. Shown as counts with the caveat about self-reporting.","where":"Show the working; python -m engine.similarity --check","files":"engine/similarity.py, docs/closeness_check.json"},{"id":"evidence","name":"Applicant-evidence package","status":"works","when":"afternoon","what":"A store for applicant records with provenance and consent, intake from messy files, and a weighted similarity score that reports how much of a profile could be compared. Its scorer orders the example cases.","where":"Behind the example cases; admissions/README.md","files":"admissions/, engine/evidence_adapter.py"},{"id":"colleges","name":"1,339 colleges from the federal file","status":"works","when":"afternoon","what":"The full Scorecard institution file with cost and net price, and a \"did you mean\" for a college typed slightly wrong.","where":"Everywhere a college is named.","files":"engine/colleges.py, tools/build_college_file.py"},{"id":"static","name":"Shared preview with no server","status":"works","when":"morning","what":"Saved runs for the demo students, with the what-if scores, as plain files that open from a folder or a zip.","where":"python tools/make_static.py --zip","files":"tools/make_static.py"},{"id":"tests","name":"Tests and the acceptance sheet","status":"works","when":"both","what":"Automated tests with no network, including one that fails if the fixture or this feature list drifts from its copies. 60 labels worked out by hand from the published rows, separately from the label code: 60 of 60 match.","where":"python -m unittest discover -s tests -t . ; python tests/acceptance/run_acceptance.py","files":"tests/"},{"id":"parser","name":"Parser for raw public posts","status":"thin","when":"afternoon","what":"Turns raw r/collegeresults posts into a wider pool (654 colleges in our run). Not wired in; its output stays out of the repository because it holds snippets of people's posts.","where":"","files":"tools/parse_reddit_posts.py"},{"id":"evaluator","name":"PRISM Evaluator on the essay notes","status":"not done","when":"","what":"The run's score is read back in code instead.","where":"","files":"engine/prism.py"},{"id":"majors","name":"Several intended majors in the form","status":"not done","when":"","what":"Closeness can try another major the student named, but the form sends only one; the API accepts major_interests.","where":"","files":"web/index.html"},{"id":"text","name":"Essay baseline search and activity text comparison","status":"works","when":"afternoon","what":"A student draft searches a standalone reference bank using embeddings when available and local text similarity otherwise. Undergraduate samples are original synthetic essays; licensed graduate references come from OpenEssays with attribution. Missing applicant essay text is omitted from outcome comparisons.","where":"Section 5, Essay Similarity Search; input and similar references displayed side by side.","files":"engine/baseline.py, engine/semantic.py, data/essays/, web/app.js"}]/*FEATURES_END*/;

/* ====================================================================== */
/* Part 1: pure helpers                                                    */
/* ====================================================================== */

var ESC = {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'};
function esc(v) {
  if (v === null || v === undefined) return '';
  return String(v).replace(/[&<>"']/g, function (m) { return ESC[m]; });
}
function arr(v) { return Array.isArray(v) ? v : []; }
function obj(v) { return v && typeof v === 'object' && !Array.isArray(v) ? v : {}; }
function num(v) {
  if (v === null || v === undefined || v === '' || typeof v === 'boolean') return null;
  var n = Number(v);
  return isFinite(n) ? n : null;
}
function str(v) { return (v === null || v === undefined || typeof v === 'object') ? '' : String(v); }
function plural(n, one, many) { return n === 1 ? one : many; }
function cap(s) { s = str(s); return s ? s.charAt(0).toUpperCase() + s.slice(1) : ''; }
function safeUrl(u) { u = str(u).trim(); return /^https?:\/\//i.test(u) ? u : ''; }
function commas(n) { return Math.round(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ','); }
function clip(s, n) { s = str(s); return s.length > n ? s.slice(0, n - 1).replace(/[\s,-]+$/, '') + '…' : s; }
function shortName(n) { return str(n).replace(/-Main Campus$/i, '').replace(/-/g, ', '); }
function f1(v) { return (Math.round(v * 10) / 10).toString(); }
var WORDS = ['No', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten'];
function word(n) { return n >= 0 && n <= 10 ? WORDS[n] : String(n); }
function joinAnd(list) {
  list = arr(list).filter(Boolean);
  return list.length < 2 ? (list[0] || '') : list.slice(0, -1).join(', ') + ' and ' + list[list.length - 1];
}

/* "about 9 in 100": a published rate about the college, never about the student. */
function inHundred(rate) {
  var r = num(rate);
  if (r === null) return '';
  var n = Math.round(r * 100);
  if (n < 1) return 'fewer than 1 in 100';
  if (n > 99) return 'nearly all';
  return 'about ' + n + ' in 100';
}
function rateFull(rate) {
  var r = num(rate);
  if (r === null) return 'not published';
  return inHundred(r) + ' applicants (' + (Math.round(r * 1000) / 10) + '%)';
}
function moneyAbout(n) {
  var v = num(n);
  if (v === null) return '';
  return 'about $' + commas(Math.round(v / 1000) * 1000);
}
function costLine(n) { return num(n) === null ? '' : moneyAbout(n) + ' a year before aid'; }
function duration(ms) {
  var v = num(ms);
  if (v === null) return '';
  if (v < 1000) return Math.round(v) + ' ms';
  return (Math.round(v / 100) / 10) + ' seconds';
}

var STATES = {AL: 'Alabama', AK: 'Alaska', AZ: 'Arizona', AR: 'Arkansas', CA: 'California', CO: 'Colorado', CT: 'Connecticut',
  DE: 'Delaware', DC: 'District of Columbia', FL: 'Florida', GA: 'Georgia', HI: 'Hawaii', ID: 'Idaho', IL: 'Illinois', IN: 'Indiana',
  IA: 'Iowa', KS: 'Kansas', KY: 'Kentucky', LA: 'Louisiana', ME: 'Maine', MD: 'Maryland', MA: 'Massachusetts', MI: 'Michigan',
  MN: 'Minnesota', MS: 'Mississippi', MO: 'Missouri', MT: 'Montana', NE: 'Nebraska', NV: 'Nevada', NH: 'New Hampshire',
  NJ: 'New Jersey', NM: 'New Mexico', NY: 'New York', NC: 'North Carolina', ND: 'North Dakota', OH: 'Ohio', OK: 'Oklahoma',
  OR: 'Oregon', PA: 'Pennsylvania', RI: 'Rhode Island', SC: 'South Carolina', SD: 'South Dakota', TN: 'Tennessee', TX: 'Texas',
  UT: 'Utah', VT: 'Vermont', VA: 'Virginia', WA: 'Washington', WV: 'West Virginia', WI: 'Wisconsin', WY: 'Wyoming'};
var ORDER = ['reach', 'target', 'likely', 'cant_say', 'outside_data'];
/* The event's own words stay (Reach, Target, Likely); each is always paired with a plain gloss. */
var WORD = {reach: 'Reach', target: 'Target', likely: 'Likely', cant_say: "Can't say yet", outside_data: 'Not in our data'};
var GLOSS = {reach: 'ambitious', target: 'within range', likely: 'a safer choice', cant_say: 'the published numbers run out', outside_data: 'we say nothing about it'};
var GROUPS = [
  {key: 'reach', title: 'Reach · ambitious', always: true, empty: 'No ambitious college on this list yet.'},
  {key: 'target', title: 'Target · within range', always: true, empty: 'No college within range on this list yet.'},
  {key: 'likely', title: 'Likely · a safer choice', always: true, empty: 'No safer choice on this list yet.'},
  {key: 'cant_say', title: "Can't say yet", always: false},
  {key: 'outside_data', title: 'Not in our data', always: false}
];
function groupOf(state) {
  var s = str(state).toLowerCase().replace(/[\s']+/g, '_');
  if (s === 'reach' || s === 'reach_for_everyone') return 'reach';
  if (s === 'target' || s === 'likely' || s === 'outside_data') return s;
  return 'cant_say';
}
function isEveryone(label) { return str(obj(label).state) === 'reach_for_everyone'; }
function glossOf(label, brief) {
  if (isEveryone(label)) return brief ? 'hard for every applicant' : 'hard for every applicant, however strong';
  return GLOSS[groupOf(obj(label).state)];
}
function labelPhrase(label, brief) { return WORD[groupOf(obj(label).state)] + ' · ' + glossOf(label, brief); }
function pill(label, brief) {
  var g = groupOf(obj(label).state);
  return '<span class="pill p-' + g + '"><i class="dot" aria-hidden="true"></i><b>' + esc(WORD[g]) + '</b><span>' + esc(glossOf(label, brief)) + '</span></span>';
}
function pillFor(state) { return pill({state: groupOf(state)}, true); }

var HOOKS = {
  first_gen: 'First in family to attend college', 'first-gen': 'First in family to attend college',
  legacy: 'Legacy', urm: 'Under-represented background', recruited_athlete: 'Recruited athlete', none: 'None'
};
function hookText(h) {
  if (Array.isArray(h)) return h.length ? h.map(hookText).join(', ') : 'None';
  var s = str(h).trim();
  if (!s) return '';
  return HOOKS[s.toLowerCase()] || cap(s.toLowerCase().replace(/[_-]+/g, ' '));
}
var MAJORS = {
  CS: 'Computer science', ENG: 'Engineering', BIO: 'Biology', PREMED: 'Pre-medicine', BUSINESS: 'Business',
  POLISCI: 'Political science', PSYCH: 'Psychology', MATH: 'Mathematics', PHYSICS: 'Physics', ECON: 'Economics',
  HUMANITIES: 'Humanities', ARTS: 'Arts', OTHER: 'Other'
};
function majorText(m) { var s = str(m); return MAJORS[s] || s; }
function studentShort(label) { return str(label).split(/\s*[(:]/)[0].trim() || 'Student'; }
function studentTagline(label) { var s = str(label), i = s.indexOf(':'); return i === -1 ? '' : cap(s.slice(i + 1).trim()); }
function studentFacts(s) {
  s = obj(s);
  var bits = [num(s.sat) !== null ? 'SAT ' + num(s.sat) : (num(s.act) !== null ? 'ACT ' + num(s.act) : 'No test score')];
  if (str(s.home_state)) bits.push(STATES[str(s.home_state).toUpperCase()] || str(s.home_state));
  if (str(s.intended_major)) bits.push(str(s.intended_major));
  return bits;
}
/* The waypoint: a dot on a short stem. Filled = you are here; outline = could go. */
function waypoint(filled) {
  return '<svg class="wp' + (filled ? ' wp-on' : '') + '" viewBox="0 0 16 22" width="16" height="22" aria-hidden="true" focusable="false">' +
    '<line x1="8" y1="11" x2="8" y2="21"/><circle cx="8" cy="7" r="5.5"/></svg>';
}

/* ---------- top bar and the opening screen ---------- */
function renderTopChips(result, mode) {
  var h = '';
  if (obj(result).synthetic === true || mode === 'static' || mode === 'example') h += '<span class="chip" title="An invented student for this demo. No real person.">Example student</span>';
  if (mode === 'static') h += '<span class="chip">Shared preview</span>';
  return h;
}
function renderStudentCards(students, chosen) {
  var list = arr(students);
  if (!list.length) return '<p class="quiet">No example students could be loaded. Use Change the details to enter one.</p>';
  function card(s, i, small) {
    s = obj(s);
    return '<button type="button" class="scard' + (small ? ' scard-small' : '') + '" data-act="pick-student" data-i="' + i + '" aria-pressed="' + (i === chosen ? 'true' : 'false') + '">' +
      waypoint(i === chosen) + '<span class="scard-name">' + esc(studentShort(s.label)) + '</span>' +
      '<span class="scard-line">' + esc(studentTagline(s.label) || studentFacts(s).slice(1).join(' · ') || 'Example student') + '</span>' +
      (small ? '' : '<span class="scard-facts">' + esc(studentFacts(s)[0]) + '</span>') + '</button>';
  }
  var main = '', safety = '';
  list.forEach(function (s, i) {
    if (isSafetyDemo(obj(s).label)) safety += card(s, i, true); else main += card(s, i, false);
  });
  return '<div class="scards">' + main + '</div>' +
    (safety ? '<p class="mini">Two safety demonstrations</p><div class="scards scards-small">' + safety + '</div>' : '');
}
function isSafetyDemo(label) { return /hidden instruction|personal details/i.test(str(label)); }
function personGlyph(x, y) {
  return '<g class="pperson" transform="translate(' + x + ' ' + y + ')"><circle cx="0" cy="-12" r="8"/><path d="M-13 12a13 13 0 0 1 26 0z"/></g>';
}
function renderGhost() {
  var bars = [[560, 70, 150], [500, 122, 170], [330, 174, 250], [250, 226, 270], [210, 278, 240]], s = '';
  bars.forEach(function (b) { s += '<rect class="ghost-bar" x="' + b[0] + '" y="' + b[1] + '" width="' + b[2] + '" height="16" rx="8"/>'; });
  return '<svg class="ghost" viewBox="0 0 960 330" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false">' + s +
    '<line class="pline" x1="470" x2="470" y1="48" y2="322"/>' + personGlyph(470, 34) + '</svg>';
}
var CHAPTERS = [['ch1', 'Who you are'], ['ch2', 'Where you stand'], ['ch3', 'What is in your hands'], ['ch4', 'Your plan'], ['ch5', 'Essay Similarity Search']];
function renderWaypoints(current, ready) {
  return '<ol>' + CHAPTERS.map(function (c, i) {
    return '<li><button type="button" class="way" data-act="go" data-to="' + c[0] + '"' + (ready ? '' : ' disabled') +
      (ready && c[0] === current ? ' aria-current="step"' : '') + '>' + waypoint(ready && c[0] === current) + '<span>' + (i + 1) + ' ' + esc(c[1]) + '</span></button></li>';
  }).join('') + '</ol>';
}
function chapterHead(n, kicker, title) {
  return '<p class="kicker">' + waypoint(true) + '<span>' + n + ' · ' + esc(kicker) + '</span></p><h2 class="ch-title" tabindex="-1">' + esc(title) + '</h2>';
}
function nextButton(to, text) { return '<p class="next"><button type="button" class="btn primary big" data-act="go" data-to="' + to + '">' + esc(text) + '</button></p>'; }

/* ---------- Chapter 1: who you are ---------- */
function essayStopped(privacy, reader) {
  var pv = obj(privacy);
  return pv.blocked === true || str(obj(reader).status) === 'blocked' || arr(pv.verdicts).some(function (v) { return obj(v).blocked === true; });
}
function verdictMarks(privacy) {
  return arr(obj(privacy).verdicts).map(obj).filter(function (v) { return str(v.by); }).map(function (v) {
    var stopped = v.blocked === true, asked = v.blocked === true || v.blocked === false;
    return '<span class="verdict ' + (stopped ? 'v-stop' : (asked ? 'v-pass' : 'v-na')) + '"' + (!asked && str(v.detail) ? ' title="' + esc(v.detail) + '"' : '') + '>' +
      esc(str(v.by).replace(/\s*\(.*\)\s*$/, '')) + ': ' + (stopped ? 'stopped' : (asked ? 'passed' : 'not asked')) + '</span>';
  }).join('');
}
function renderStrengths(result) {
  var r = obj(result), st = obj(r.student), rd = obj(r.reader), pv = obj(r.privacy);
  var h = chapterHead(1, 'Who you are', 'What stands out in you');
  h += '<p class="you-line"><b>' + esc(studentShort(st.label)) + '</b><span class="sep" aria-hidden="true"> · </span>' +
    studentFacts(st).map(esc).join('<span class="sep" aria-hidden="true"> · </span>') + '</p>';
  var acts = arr(st.activities).map(obj).filter(function (a) { return str(a.type) || str(a.role) || str(a.description); }).slice(0, 3);
  if (acts.length) {
    h += '<ul class="acts">' + acts.map(function (a) {
      var lead = [str(a.type), str(a.role).toLowerCase()].filter(Boolean).join(', ');
      return '<li>' + waypoint(false) + '<span><b>' + esc(lead) + '</b>' + (lead && str(a.description) ? ': ' : '') + esc(a.description) + '</span></li>';
    }).join('') + '</ul>';
  }
  var stopped = essayStopped(pv, rd), status = str(rd.status);
  if (stopped) {
    var why = str(obj(arr(pv.verdicts).map(obj).filter(function (v) { return v.blocked === true; })[0]).detail) || str(pv.reason);
    h += '<div class="calm"><p><b>We did not read this essay.</b> It contains text written to steer an AI, so it was stopped before any model saw it. Your counselor can read it with you.</p>' +
      '<p class="working-only verdicts">' + verdictMarks(pv) + (why ? '<span class="quiet">' + esc(why) + '</span>' : '') + '</p></div>';
  } else if (status === 'ok') {
    var themes = arr(obj(rd.tags).essay_themes).map(str).filter(Boolean);
    if (themes.length) h += '<p class="themes"><span class="quiet">Your essay is about</span> ' + themes.map(function (t) { return '<span class="chip chip-theme">' + esc(t) + '</span>'; }).join('') + '</p>';
    var notes = arr(rd.notes).map(obj).filter(function (n) { return str(n.quote) && n.quote_found !== false; }).slice(0, 2);
    if (notes.length) {
      h += '<div class="words"><p class="label">In your words</p>' + notes.map(function (n) {
        return '<figure><blockquote>“' + esc(n.quote) + '”</blockquote>' + (str(n.observation) ? '<figcaption>' + esc(n.observation) + '</figcaption>' : '') + '</figure>';
      }).join('') + '</div>';
    }
    var d = num(rd.dropped) || 0;
    if (d > 0) h += '<p class="quiet small">' + d + ' ' + plural(d, 'note was', 'notes were') + ' left out because ' + plural(d, 'its quote was', 'their quotes were') + ' not in the essay.</p>';
    h += '<p class="quiet small">Personal details were hidden before any AI read this. Your counselor reads the essay; it never changes a label.</p>';
    var masked = arr(pv.masked).map(obj).filter(function (m) { return num(m.count); });
    if (masked.length || verdictMarks(pv)) {
      h += '<p class="working-only verdicts">' + verdictMarks(pv) + (masked.length ? '<span class="quiet">Hidden: ' + esc(masked.map(function (m) { return num(m.count) + ' ' + str(m.kind); }).join(', ')) + '</span>' : '') + '</p>';
    }
  } else if (status === 'error') {
    h += '<p class="quiet small">The essay could not be read this time. Nothing below depends on it.</p>';
  } else if (!acts.length) {
    h += '<p class="quiet">There is more to you than a score. Add activities or an essay under Counselor tools, Change the details, to see it here.</p>';
  }
  return h + nextButton('ch2', "Now let's look at where you stand");
}

/* ---------- Chapter 2: where you stand ---------- */
function listCounts(result) {
  var c = {reach: 0, target: 0, likely: 0, cant_say: 0, outside_data: 0, everyone: 0, names: {reach: [], target: [], likely: []}};
  arr(obj(result).colleges).map(obj).forEach(function (x) {
    var g = groupOf(obj(x.label).state);
    c[g]++;
    if (isEveryone(x.label)) c.everyone++;
    if (c.names[g]) c.names[g].push(shortName(x.name));
  });
  return c;
}
function headlineSentence(result) {
  var st = obj(obj(result).student), c = listCounts(result), r = c.reach, t = c.target, l = c.likely, n = r + t + l;
  if (num(st.sat) === null && num(st.act) === null) return "Without a test score we can't place you against these colleges yet. Here is what we can still say.";
  if (!n) return "We can't place you against these colleges yet. Here is what we can still say.";
  var hard = c.everyone === r && r > 0 ? 'hard to get into for every applicant, however strong' : 'ambitious choices';
  if (r && t && l) return 'This list has ambition, colleges within range, and safer choices.';
  if (r && !t && !l) return r === 1 ? 'This list has one college so far, and it is an ambitious choice. Keep the dream; give it a foundation.'
    : 'Every college here is an ambitious choice today. Keep the dreams; give them a foundation.';
  if (r >= 2 && t + l === 1) {
    return 'This list aims high. ' + word(r) + ' of these ' + word(n).toLowerCase() + ' are ' + hard + '. ' +
      (t ? c.names.target[0] + ' is within range.' : c.names.likely[0] + ' is a safer choice.');
  }
  if (!l && t) {
    return (r ? 'This list has ' + word(r).toLowerCase() + ' ambitious ' + plural(r, 'choice', 'choices') + ' and ' + word(t).toLowerCase() + ' within range.'
              : word(t) + ' of these ' + plural(t, 'colleges is', 'colleges are') + ' within range.') + ' It has room for a safer choice.';
  }
  if (!t && l && r) return 'This list has ambition and safer choices, with room for something in between.';
  if (!r) return 'This list stands on solid ground. It has room for a dream or two.';
  return 'Here is where you stand at each college.';
}
/* One block per college in its label colour, then a dashed slot for each missing group: room to fill, not an alarm. */
function renderBalanceBar(result) {
  var c = listCounts(result), h = '<div class="bbar" role="img" aria-label="' +
    esc(c.reach + ' reach, ' + c.target + ' target, ' + c.likely + ' likely' + (c.cant_say ? ', ' + c.cant_say + " can't say yet" : '')) + '">';
  ['reach', 'target', 'likely', 'cant_say'].forEach(function (g) {
    for (var i = 0; i < c[g]; i++) h += '<span class="bb bb-' + g + '"></span>';
    if (c[g] && g !== 'cant_say') h += '<span class="bb-word p-' + g + '"><b>' + c[g] + ' ' + WORD[g].toLowerCase() + '</b> ' + GLOSS[g] + '</span>';
    else if (c[g]) h += '<span class="bb-word">' + c[g] + " can't say yet</span>";
    else if (g !== 'cant_say' && (c.reach + c.target + c.likely) > 0) h += '<span class="bb bb-slot"></span><span class="bb-word bb-room">room for ' + (g === 'likely' ? 'a likely college, a safer choice' : (g === 'target' ? 'a target, within range' : 'a reach, a dream')) + '</span>';
  });
  return h + '</div>';
}
var CAUTION_RANK = ['all_cant_say', 'no_likely', 'reach_heavy', 'prestige_pile', 'no_target', 'short_list'];
var CAUTION = {
  all_cant_say: "We can't place these colleges yet. That is not a bad sign; it means the published numbers run out.",
  no_likely: 'This list has no safer choice yet. A plan needs one or two, and some colleges fit your numbers.',
  reach_heavy: 'Most of this list is ambition. That is a fine place to dream from, and a plan needs a few safer choices too.',
  prestige_pile: 'Most of this list is ambition. That is a fine place to dream from, and a plan needs a few safer choices too.',
  no_target: 'There is nothing in the middle yet. A college within range would steady this list.',
  short_list: 'This is a short list. Most plans have a few more colleges on them.'
};
function warningTexts(warnings) {
  return arr(warnings).map(function (x, i) {
    var id = str(obj(x).id), k = CAUTION_RANK.indexOf(id);
    return {t: CAUTION[id] || (typeof x === 'string' ? x : str(obj(x).text)), raw: typeof x === 'string' ? x : str(obj(x).text), k: k === -1 ? 50 + i : k, i: i};
  }).filter(function (w) { return w.t; }).sort(function (a, b) { return a.k - b.k || a.i - b.i; });
}
function cautionLine(result) {
  var c = listCounts(result), w = warningTexts(obj(obj(result).balance).warnings);
  if (!w.length) return '';
  if (c.reach && !c.target && !c.likely) return 'This list is all ambition. That is a fine place to dream from, and a plan needs a few safer choices too.';
  return w[0].t;
}
function renderHeadline(result, whatIfScore) {
  var caution = cautionLine(result), raw = warningTexts(obj(obj(result).balance).warnings);
  var notes = arr(obj(obj(result).student).input_notes).map(str).filter(Boolean);
  return chapterHead(2, 'Where you stand', 'Where you stand at each college') +
    (notes.length ? '<ul class="input-notes">' + notes.map(function (t) { return '<li>' + esc(t) + '</li>'; }).join('') + '</ul>' : '') +
    '<p class="hero">' + (num(whatIfScore) !== null ? '<span class="hero-if">If your score were ' + esc(whatIfScore) + ':</span> ' : '') + esc(headlineSentence(result)) + '</p>' +
    renderBalanceBar(result) +
    (raw.length ? '<ul class="working-only plain small">' + raw.map(function (x) { return '<li>' + esc(x.raw) + '</li>'; }).join('') + '</ul>' : '');
}
function renderCaution(result) {
  var caution = cautionLine(result);
  return (caution ? '<p class="caution">' + esc(caution) + ' <button type="button" class="linkbtn" data-act="go" data-to="ch3">See what you can do</button></p>' : '') +
    nextButton('ch3', 'See what you can do about it');
}

/* ---------- the trail map: the student stands on the trail; each college is ahead, nearby or behind ---------- */
function edgeLever(c) {
  var lv = arr(obj(c).levers).map(obj).filter(function (l) { return l.kind === 'score' && l.moves === true && num(l.points) !== null && str(l.to); })[0];
  return lv ? num(lv.points) + ' ' + plural(num(lv.points), 'point', 'points') + ' from ' + GLOSS[groupOf(lv.to)] : '';
}
function pictureModel(result, opts) {
  var o = obj(opts), r = obj(result), st = obj(r.student), cs = arr(r.colleges).map(obj);
  var sat = num(st.sat), act = num(st.act), useAct = o.kind ? o.kind === 'ACT' : (sat === null && act !== null);
  var own = useAct ? act : sat;
  var score = num(o.score) !== null ? num(o.score) : own, base = num(o.base) !== null ? num(o.base) : own;
  var rows = cs.map(function (c, i) {
    var L = obj(c.label), g = groupOf(L.state);
    var lo = num(useAct ? c.act25 : c.sat25), hi = num(useAct ? c.act75 : c.sat75), t;
    if (lo !== null && hi !== null && hi < lo) { t = lo; lo = hi; hi = t; }
    return {i: i, c: c, L: L, g: g, lo: lo, hi: hi, has: lo !== null && hi !== null && g !== 'outside_data'};
  });
  /* furthest ahead first; colleges we cannot place come last */
  rows.sort(function (a, b) {
    if (a.has !== b.has) return a.has ? -1 : 1;
    if (!a.has) return ORDER.indexOf(a.g) - ORDER.indexOf(b.g) || a.i - b.i;
    return ORDER.indexOf(a.g) - ORDER.indexOf(b.g) || (b.lo + b.hi) - (a.lo + a.hi) || a.i - b.i;
  });
  var vals = [useAct ? 18 : 1050];
  rows.forEach(function (x) { if (x.has) vals.push(x.lo, x.hi); });
  [score, base, num(o.scoreMin), num(o.scoreMax)].forEach(function (v) { if (v !== null) vals.push(v); });
  var lowest = Math.min.apply(null, vals);
  return {rows: rows, useAct: useAct, test: useAct ? 'ACT' : 'SAT', score: score, base: base, name: studentShort(st.label),
          min: useAct ? Math.max(1, lowest - 2) : Math.max(400, Math.floor((lowest - 50) / 100) * 100), max: useAct ? 36 : 1600};
}
function gapNote(x, score) {
  if (!x.has || score === null) return '';
  if (score < x.lo) return (x.lo - score) + ' ' + plural(x.lo - score, 'point', 'points') + ' above your score';
  if (score >= x.hi) return score === x.hi ? 'your score is at the top of this range' : 'your score is ' + (score - x.hi) + ' ' + plural(score - x.hi, 'point', 'points') + ' above this range';
  return 'your score is inside this range';
}
function renderPicture(result, opts) {
  var m = pictureModel(result, opts), o = obj(opts), c0 = listCounts(result);
  var W = 960, X0 = 28, X1 = 668, RX = 692, RH = 56, TOP = 70, n = m.rows.length;
  var emptyRow = n > 0 && !c0.likely && (c0.reach + c0.target) > 0 ? 1 : 0, nSug = arr(obj(obj(result).balance).suggestions).length;
  var H = TOP + Math.max(n + emptyRow, 1) * RH + 34;
  function sx(v) { return X0 + (Math.max(m.min, Math.min(m.max, v)) - m.min) / (m.max - m.min) * (X1 - X0); }
  function p(v) { return (Math.round(v * 10) / 10).toString(); }
  var who = m.name + (m.score !== null ? ', ' + m.score : '');
  var s = '<svg class="pic" viewBox="0 0 ' + W + ' ' + H + '" width="' + W + '" height="' + H + '" role="group" aria-label="' +
    esc('Where you stand: ' + n + ' ' + plural(n, 'college', 'colleges') + ' on one ' + m.test + ' score line' + (m.score !== null ? ', with ' + who : '') + '.') + '">';
  s += '<defs><pattern id="pichatch" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">' +
    '<rect class="ph-bg" width="8" height="8"/><rect class="ph-fg" width="3" height="8"/></pattern></defs>';
  (m.useAct ? [20, 26, 32] : [1100, 1300, 1500]).forEach(function (tv) {
    if (tv <= m.min || tv >= m.max) return;
    s += '<line class="pgrid" x1="' + p(sx(tv)) + '" x2="' + p(sx(tv)) + '" y1="' + (TOP - 6) + '" y2="' + (H - 26) + '"/>' +
      '<text class="ptick" x="' + p(sx(tv)) + '" y="' + (H - 8) + '" text-anchor="middle">' + (m.useAct ? 'ACT ' : 'SAT ') + tv + '</text>';
  });
  var lx = m.score !== null ? sx(m.score) : null;
  if (lx !== null) {
    if (lx - X0 > 250) s += '<text class="pcap" x="' + p(lx - 14) + '" y="' + (TOP - 12) + '" text-anchor="end">colleges asking for less than this</text>';
    if (X1 - lx > 180) s += '<text class="pcap" x="' + p(lx + 14) + '" y="' + (TOP - 12) + '">colleges asking for more</text>';
  }
  if (!n) s += '<text class="pnote" x="' + X0 + '" y="' + (TOP + 30) + '">No colleges on this list yet.</text>';
  m.rows.forEach(function (x, k) {
    var c = x.c, L = x.L, y = TOP + k * RH, by = y + 26, name = str(c.name) || 'Unnamed college', note = gapNote(x, m.score) || (x.has && x.g === 'cant_say' ? "we can't place you here yet" : ''), edge = edgeLever(c), cost = costLine(c.cost_year);
    var say = name + '. ' + labelPhrase(L) + '.' + (x.has ? ' Middle ' + m.test + ' range ' + x.lo + ' to ' + x.hi + '.' : ' No published range.') +
      (note ? ' ' + cap(note) + '.' : '') + (edge ? ' ' + cap(edge) + '.' : '') + (cost ? ' ' + cap(cost) + '.' : '') + ' See how we got this.';
    s += '<g class="prow pr-' + x.g + '" data-act="open-receipt" data-i="' + x.i + '" tabindex="0" role="button" aria-label="' + esc(say) + '">';
    s += '<title>' + esc(name + ': see how we got this') + '</title><rect class="phit" x="4" y="' + (y + 1) + '" width="' + (W - 8) + '" height="' + (RH - 2) + '" rx="10"/>';
    if (x.has) {
      var x0 = sx(x.lo), x1 = Math.max(sx(x.hi), x0 + 12), mid = (X0 + X1) / 2, nameW = Math.min(name.length, 44) * 8.3;
      var endAnchor = x0 + nameW > X1;
      s += '<text class="pname" x="' + p(endAnchor ? x1 : x0) + '" y="' + (y + 19) + '"' + (endAnchor ? ' text-anchor="end"' : '') + '>' + esc(clip(name, 44)) + '</text>';
      s += '<rect class="pbar" x="' + p(x0) + '" y="' + by + '" width="' + p(x1 - x0) + '" height="16" rx="8"/>';
      if (num(obj(obj(c.cases).own).n) > 0) s += '<circle class="pown" cx="' + p(x1 - 8) + '" cy="' + (by + 8) + '" r="4"/>';
      if (note) {
        var nw = note.length * 7 + 16, left = x0 - X0, right = X1 - x1, ahead = m.score !== null && m.score < x.lo;
        var side = (ahead && left >= nw) ? 'L' : (!ahead && right >= nw) ? 'R' : (right >= nw ? 'R' : (left >= nw ? 'L' : ((x1 - x0) >= nw ? 'IN' : (left > right ? 'L' : 'R'))));
        s += side === 'IN' ? '<text class="pnote pnote-in" x="' + p((x0 + x1) / 2) + '" y="' + (by + 12.5) + '" text-anchor="middle">' + esc(note) + '</text>'
          : '<text class="pnote" x="' + p(side === 'L' ? x0 - 8 : x1 + 8) + '" y="' + (by + 13) + '"' + (side === 'L' ? ' text-anchor="end"' : '') + '>' + esc(note) + '</text>';
      }
    } else {
      s += '<text class="pname" x="' + X0 + '" y="' + (y + 19) + '">' + esc(clip(name, 44)) + '</text>' +
        '<rect class="pband" x="' + X0 + '" y="' + by + '" width="' + (X1 - X0) + '" height="16" rx="8" fill="url(#pichatch)"/>' +
        '<text class="pnote pbandt" x="' + (X0 + 14) + '" y="' + (by + 12.5) + '">' +
        (x.g === 'outside_data' ? (str(c.suggestion) ? 'Not in our data. Did you mean ' + esc(c.suggestion) + '?' : 'Not in our data, so we say nothing about it.') : "No published " + (m.useAct ? 'ACT ' : '') + "range, so we can't place you. Not a bad sign.") + '</text>';
    }
    s += '<circle class="pdot" cx="' + (RX + 6) + '" cy="' + (y + 14) + '" r="6"/>' +
      '<text class="plab" x="' + (RX + 19) + '" y="' + (y + 19) + '"><tspan class="plab-w">' + esc(WORD[x.g]) + '</tspan>' +
      (x.g === 'cant_say' || x.g === 'outside_data' ? '' : '<tspan class="plab-g"> · ' + esc(glossOf(L, true)) + '</tspan>') + '</text>';
    if (cost) s += '<text class="pcost" x="' + (RX + 19) + '" y="' + (y + 36) + '">' + esc(cost) + '</text>';
    if (edge) s += '<text class="pedge" x="' + (RX + 19) + '" y="' + (y + 51) + '">' + esc(edge) + '</text>';
    s += '</g>';
  });
  if (emptyRow) {
    var ey = TOP + n * RH;
    s += '<g class="pempty"><rect x="' + X0 + '" y="' + (ey + 14) + '" width="' + (X1 - X0) + '" height="30" rx="15"/>' +
      '<text class="pnote" x="' + (X0 + 18) + '" y="' + (ey + 34) + '">Likely: none yet.' + (nSug ? ' Chapter 3 shows ' + nSug + ' that would be within range or safer.' : ' Chapter 3 is about what you can change.') + '</text></g>';
  }
  if (m.base !== null && m.score !== null && m.base !== m.score) {
    s += '<line class="pline-base" x1="' + p(sx(m.base)) + '" x2="' + p(sx(m.base)) + '" y1="' + (TOP - 6) + '" y2="' + (H - 26) + '"/>';
  }
  if (lx !== null) {
    var tag = o.whatIf ? 'If your score were ' + m.score : who, tw = tag.length * 9.2, right2 = lx + 22 + tw < W - 10;
    s += '<g class="pstudent" aria-hidden="true"><line class="pline" x1="' + p(lx) + '" x2="' + p(lx) + '" y1="42" y2="' + (H - 26) + '"/>' + personGlyph(p(lx), 30) +
      '<text class="pyou" x="' + p(right2 ? lx + 22 : lx - 22) + '" y="30"' + (right2 ? '' : ' text-anchor="end"') + '>' + esc(tag) + '</text></g>';
  }
  return s + '</svg>';
}
function didYouMean(c, canSwap) {
  c = obj(c);
  if (groupOf(obj(c.label).state) !== 'outside_data' || !str(c.suggestion)) return '';
  return '<p class="calm meant">“' + esc(c.name) + '” is not in our data. Did you mean <b>' + esc(c.suggestion) + '</b>? ' +
    (canSwap === false ? '' : '<button type="button" class="btn small" data-act="swap-college" data-from="' + esc(c.name) + '" data-name="' + esc(c.suggestion) + '">Use ' + esc(c.suggestion) + '</button>') + '</p>';
}
var PIC_VIEWS = [['trail', 'Trail map'], ['rings', 'Rings'], ['map', 'Map'], ['groups', 'Clusters']];
function renderPictureCard(result, opts) {
  var o = obj(opts), m = pictureModel(result, opts), canSwap = o.canSwap, from = o.closenessFrom || result, can = hasCloseness(from), grp = can && hasGroups(from);
  var view = ((o.view === 'rings' || o.view === 'map') && can) || (o.view === 'groups' && grp) ? o.view : 'trail';
  var toggle = can ? '<p class="pic-toggle quiet small" role="group" aria-label="Other pictures">Other pictures: ' + PIC_VIEWS.filter(function (v) { return v[0] !== 'groups' || grp; }).map(function (v) {
    return '<button type="button" class="linkbtn" data-act="pic-view" data-view="' + v[0] + '" aria-pressed="' + (v[0] === view ? 'true' : 'false') + '">' + v[1] + '</button>';
  }).join(' <span aria-hidden="true">·</span> ') + '</p>' : '';
  if (view === 'groups') {
    return '<div class="card pic-card">' + renderGroups(from, o) +
      '<p class="pic-foot"><span class="quiet">Clusters are set by a written rule, so you can recount them by hand. Every dot is one real finished case from the self-reported pool.' +
      (o.stale ? ' From the last full run.' : '') + '</span><span class="tap">Press a cluster to enlarge it and list its cases.</span></p>' + toggle + '</div>';
  }
  if (view !== 'trail') {
    return '<div class="card pic-card"><div class="pic-scroll">' + (view === 'rings' ? renderRings(from) : renderMindMap(from, o.focus)) + '</div>' +
      '<p class="pic-foot"><span class="quiet">' + (view === 'rings'
        ? 'You are at the centre. A college nearer the centre has admitted more students who look like you. Hollow: too few cases. Outer ring: cannot be placed. Distance is a resemblance, not the label and not a forecast.'
        : 'You are in the middle, with a branch for each label. Under each college: the kind of admitted student closest to you, when the kinds pass their check, and the nearest admitted cases.') +
      (o.stale ? ' From the last full run.' : '') + '</span><span class="tap">Tap a college to see how we got this.</span></p>' + toggle + '</div>';
  }
  return '<div class="card pic-card">' + arr(obj(result).colleges).map(function (c) { return didYouMean(c, canSwap); }).join('') +
    '<div class="pic-scroll">' + renderPicture(result, opts) + '</div>' +
    '<p class="pic-foot"><span class="quiet">Each bar is where the middle half of a college\'s students scored.' + (m.score === null ? ' There is no line for you, because no test score was entered.' : ' The line is you.') + '</span>' +
    '<span class="tap">Tap a college to see how we got this.</span></p>' + toggle + '</div>';
}

/* ---------- Chapter 3: what is in your hands ---------- */
function changesBetween(base, view) {
  var before = {}, out = [];
  arr(obj(base).colleges).map(obj).forEach(function (c) { before[str(c.name)] = groupOf(obj(c.label).state); });
  arr(obj(view).colleges).map(obj).forEach(function (c) {
    var g = groupOf(obj(c.label).state), b = before[str(c.name)];
    if (b && b !== g) out.push({name: str(c.name), from: b, to: g});
  });
  return out;
}
var NOT_A_PREDICTION = ' This shows how the rule works. It is not a prediction.';
function moveSentence(score, moves, would) {
  var mv = arr(moves).map(obj).filter(function (x) { return str(x.name); });
  if (!mv.length) return 'At ' + score + ', no college on this list changes label.' + NOT_A_PREDICTION;
  return 'At ' + score + ', ' + mv.slice(0, 3).map(function (x) {
    return shortName(x.name) + (would ? ' would move' : ' moves') + ' from ' + GLOSS[groupOf(x.from)] + ' to ' + GLOSS[groupOf(x.to)];
  }).join('; ') + (mv.length > 3 ? '; and ' + (mv.length - 3) + ' more change' : '') + '.' + NOT_A_PREDICTION;
}
/* The nearest score at which a label changes, from the server's ladder. */
function nearestMove(result) {
  var ladder = arr(obj(obj(result).levers).score_ladder).map(obj), maxPts = 0, hit = null;
  ladder.forEach(function (st) {
    if (num(st.points) !== null && num(st.points) > maxPts) maxPts = num(st.points);
    if (!hit && arr(st.moves).length && num(st.new_score) !== null) hit = st;
  });
  return {hit: hit, maxPts: maxPts, kind: str(obj(ladder[0]).kind) || 'SAT'};
}
function ladderSentence(result) {
  var nm = nearestMove(result);
  if (nm.hit) return moveSentence(num(nm.hit.new_score), nm.hit.moves, true);
  if (nm.maxPts) return 'Up to ' + nm.maxPts + ' more points changes no label on this list.' + NOT_A_PREDICTION;
  return 'Move the slider to see how the labels would change.' + NOT_A_PREDICTION;
}
function suggestionCard(s, canAdd, hidden) {
  s = obj(s);
  var g = groupOf(s.would_be), bits = [];
  if (num(s.admit_rate) !== null) bits.push(inHundred(s.admit_rate) + ' get in');
  if (costLine(s.cost_year)) bits.push(costLine(s.cost_year));
  return '<li class="sugg p-' + g + '"' + (hidden ? ' hidden data-more="1"' : '') + '><p class="sugg-name"><i class="dot" aria-hidden="true"></i>' + esc(str(s.name) || 'A college') + '</p>' +
    (s.would_be ? '<p class="sugg-would">would be ' + esc(GLOSS[g]) + ' <span class="quiet">(' + esc(WORD[g].toLowerCase()) + ')</span></p>' : '') +
    (str(s.why) ? '<p class="sugg-why">' + esc(s.why) + '</p>' : '') +
    (bits.length ? '<p class="quiet small">' + esc(cap(bits.join(' · '))) + (str(s.tuition_note) ? '<span class="working-only"> · ' + esc(s.tuition_note) + '</span>' : '') + '</p>' : '') +
    (canAdd !== false && str(s.name) ? '<button type="button" class="btn small" data-act="add-suggestion" data-name="' + esc(s.name) + '">Add to my list</button>' : '') + '</li>';
}
/* What a college says it reads, set beside what is in this profile. Three neutral marks; never a count or a score. */
var FIT_MARK = {in_profile: ['fit-in', 'in your profile'], not_yet: ['fit-not', 'not in this profile yet'], cant_see: ['fit-cant', "we can't see this here"]};
function fitRows(fit, max) {
  return arr(obj(fit).looks_for).map(obj).filter(function (f) { return str(f.factor); }).slice(0, max || 99).map(function (f) {
    var mk = FIT_MARK[str(f.state)] || FIT_MARK.cant_see;
    return '<li' + (str(f.note) ? ' title="' + esc(f.note) + '"' : '') + '><i class="fit-mark ' + mk[0] + '" aria-hidden="true"></i><span class="fit-factor">' + esc(cap(f.factor)) + '</span>' +
      (str(f.rating) ? '<span class="fit-rating">' + esc(f.rating) + '</span>' : '') + '<span class="sr">: ' + mk[1] + '</span></li>';
  }).join('');
}
function fitKey() {
  return '<p class="fit-key quiet small"><span><i class="fit-mark fit-in" aria-hidden="true"></i>in your profile</span><span><i class="fit-mark fit-not" aria-hidden="true"></i>not in this profile yet</span>' +
    '<span><i class="fit-mark fit-cant" aria-hidden="true"></i>we can\'t see this here</span></p>';
}
function fitDoesNot(fit) {
  var d = arr(obj(fit).does_not_consider).map(str).filter(Boolean);
  return d.length ? '<p class="fit-relief">This college says it does not consider: ' + esc(d.join('; ')) + '.</p>' : '';
}
function renderFit(fit) {
  fit = obj(fit);
  var rows = fitRows(fit);
  if (!rows && !fitDoesNot(fit)) return '';
  return '<div class="fit"><p class="label">What this college says it reads</p>' + (rows ? '<ul class="fit-list">' + rows + '</ul>' + fitKey() : '') + fitDoesNot(fit) +
    (str(fit.note) ? '<p class="quiet small">' + esc(fit.note) + '</p>' : '') +
    '<p class="working-only small quiet">' + [esc(str(fit.year)), sourceLink(fit.source_url)].filter(Boolean).join(' · ') + '</p></div>';
}
function fitColleges(result) {
  return arr(obj(result).colleges).map(obj).map(function (c, i) {
    return arr(obj(c.fit).looks_for).length ? {i: i, name: str(c.name), fit: obj(c.fit)} : null;
  }).filter(Boolean);
}
function coverageLine(result, counted) {
  var cov = obj(obj(obj(result).levers).fit_coverage), w = num(cov['with']), of = num(cov.of), n = arr(obj(result).colleges).length;
  if (w === null || of === null) { w = counted; of = n; }
  return w > 0 ? "We have each college's own statement for " + w + ' of your ' + of + ' ' + plural(of, 'college', 'colleges') + '.'
    : "We don't hold these colleges' own statements yet, so we say nothing here.";
}
function saysLevers(result) {
  return arr(obj(result).colleges).map(obj).map(function (c, i) {
    var lv = arr(c.levers).map(obj).filter(function (l) { return l.kind === 'says' && (arr(l.factors).length || str(l.text)); })[0];
    return lv ? {i: i, name: str(c.name), lv: lv} : null;
  }).filter(Boolean);
}
/* slider: {disabled, reason, min, max, step, value, shown} */
function renderHands(result, slider, canAdd) {
  var r = obj(result), sl = obj(slider), sug = arr(obj(r.balance).suggestions), says = saysLevers(r), fits = fitColleges(r);
  var h = chapterHead(3, 'What is in your hands', 'What is in your hands') + '<p class="ch-sub">Three things you can change. Try any of them.</p><div class="hands">';
  h += '<section class="card hand"><h3>' + waypoint(false) + 'Your list</h3><p class="hand-lead">The list is the biggest lever you have.</p>';
  if (sug.length) {
    h += '<ul class="suggs">' + sug.map(function (x, i) { return suggestionCard(x, canAdd, i >= 3); }).join('') + '</ul>';
    if (sug.length > 3) h += '<button type="button" class="linkbtn" data-act="more-suggestions" aria-expanded="false">See ' + (sug.length - 3) + ' more</button>';
    if (canAdd === false) h += '<p class="quiet small">Shared preview: adding colleges is switched off.</p>';
  } else h += '<p class="quiet">We have no colleges to suggest for this list.</p>';
  h += '</section>';
  h += '<section class="card hand"><h3>' + waypoint(false) + 'Your score</h3>';
  if (sl.disabled || num(sl.value) === null) {
    h += '<p class="hand-lead">' + esc(str(sl.reason) || 'No test score to vary.') + '</p><p class="quiet">Whether to take or send a test is a conversation for you and your counselor.</p>';
  } else {
    h += '<label class="hand-lead" for="whatif">If your score were different…</label><div class="whatif-row">' +
      '<input type="range" id="whatif" min="' + esc(sl.min) + '" max="' + esc(sl.max) + '" step="' + esc(sl.step) + '" value="' + esc(sl.value) + '">' +
      '<output id="whatif-out" for="whatif">' + esc(sl.shown) + '</output></div>' +
      '<p id="whatif-say" class="whatif-say" role="status">' + esc(ladderSentence(r)) + '</p>' +
      '<p class="hint" id="whatif-hint"></p>' +
      '<p class="hand-foot"><span class="quiet">Whether a retake is worth the effort is your call.</span> <button type="button" class="linkbtn" data-act="reset-score" id="whatif-reset" disabled>Back to your score</button></p>';
  }
  h += '</section>';
  h += '<section class="card hand"><h3>' + waypoint(false) + 'What they look for</h3><p class="hand-lead">What each college says it looks for.</p>';
  if (fits.length) {
    var fnotes = {};
    h += '<ul class="looks">' + fits.slice(0, 3).map(function (x) {
      if (str(x.fit.note)) fnotes[str(x.fit.note)] = 1;
      return '<li><button type="button" class="linkbtn" data-act="open-receipt" data-i="' + x.i + '" data-tab="says">' + esc(shortName(x.name)) + '</button>' +
        '<ul class="fit-list">' + fitRows(x.fit, 3) + '</ul></li>';
    }).join('') + '</ul>' + fitKey() + Object.keys(fnotes).map(function (t) { return '<p class="quiet small">' + esc(t) + '</p>'; }).join('');
  } else if (says.length) {
    h += '<ul class="looks">' + says.slice(0, 4).map(function (x) {
      var f = arr(x.lv.factors).map(str).filter(Boolean).slice(0, 4);
      return '<li><button type="button" class="linkbtn" data-act="open-receipt" data-i="' + x.i + '" data-tab="says">' + esc(shortName(x.name)) + '</button>' +
        (f.length ? '<p><span class="quiet small">' + esc(str(x.lv.rating) ? 'rates as ' + str(x.lv.rating) : 'looks for') + '</span> ' + f.map(function (t) { return '<span class="chip chip-theme">' + esc(t) + '</span>'; }).join('') + '</p>'
                  : '<p class="small">' + esc(x.lv.text) + '</p>') + '</li>';
    }).join('') + '</ul>';
  }
  h += '<p class="quiet small">' + esc(coverageLine(r, Math.max(fits.length, says.length))) + '</p></section></div>';
  if (str(obj(r.levers).note)) h += '<p class="quiet small working-only">' + esc(obj(r.levers).note) + '</p>';
  return h + nextButton('ch4', 'Put it into a plan');
}

/* ---------- Chapter 4: your plan ---------- */
function planLines(result) {
  var r = obj(result), st = obj(r.student), out = [];
  var sug = arr(obj(r.balance).suggestions).map(function (x) { return shortName(obj(x).name); }).filter(Boolean).slice(0, 3);
  if (sug.length) out.push({t: 'Widen the list.', x: 'Talk about adding one or two of these: ' + joinAnd(sug) + '.'});
  var sat = num(st.sat), act = num(st.act), nm = nearestMove(r), kind = sat !== null ? 'SAT' : 'ACT', score = sat !== null ? sat : act;
  if (score === null) out.push({t: 'Know your number.', x: 'No test score is on file. Talk about whether taking or sending one would help.'});
  else if (nm.hit) {
    var mv = arr(nm.hit.moves).map(obj), first = obj(mv[0]);
    out.push({t: 'Know your number.', x: 'Your ' + kind + ' is ' + score + '. At ' + num(nm.hit.new_score) + ', ' + shortName(first.name) + ' changes from ' + GLOSS[groupOf(first.from)] + ' to ' + GLOSS[groupOf(first.to)] +
      (mv.length > 1 ? ', and ' + (mv.length - 1) + ' more ' + plural(mv.length - 1, 'college changes', 'colleges change') + ' too' : '') + '. Whether a retake is worth the effort is your call.'});
  } else if (nm.maxPts) out.push({t: 'Know your number.', x: 'Your ' + kind + ' is ' + score + '. Up to ' + nm.maxPts + ' more points changes no label on this list, so the list matters more than the score here.'});
  var says = saysLevers(r).slice(0, 2).map(function (x) {
    var f = arr(x.lv.factors).map(str).filter(Boolean).slice(0, 3);
    return f.length ? shortName(x.name) + ' rates as ' + (str(x.lv.rating) || 'important') + ': ' + joinAnd(f) + '.' : '';
  }).filter(Boolean);
  if (!says.length) {
    says = fitColleges(r).slice(0, 2).map(function (x) {
      var top = arr(x.fit.looks_for).map(obj).filter(function (f) { return str(f.factor); }), rating = str(obj(top[0]).rating);
      var f = top.filter(function (y) { return str(y.rating) === rating; }).map(function (y) { return str(y.factor); }).slice(0, 3);
      return f.length ? shortName(x.name) + (rating ? ' rates as ' + rating + ': ' : ' reads: ') + joinAnd(f) + '.' : '';
    }).filter(Boolean);
  }
  if (says.length) out.push({t: 'Write to what they ask.', x: says.join(' ')});
  var withCases = arr(r.colleges).map(obj).map(function (c) {
    return {name: shortName(c.name), n: (num(obj(obj(c.cases).own).n) || 0) + (num(obj(obj(c.cases).national).n) || 0)};
  }).filter(function (x) { return x.n > 0; }).sort(function (a, b) { return b.n - a.n; }).slice(0, 2);
  if (withCases.length) out.push({t: 'Read the real cases.', x: 'Look at how it went for students like you at ' + joinAnd(withCases.map(function (x) { return x.name; })) + ', including students who were not admitted.'});
  var q = str(obj(arr(obj(r.reader).notes)[0]).question);
  if (q && !essayStopped(r.privacy, r.reader)) out.push({t: 'Bring a question.', x: q});
  return out;
}
var WHY_NO_PERCENT = 'No one can honestly give you a percentage. What we can show is real students and how it went for them.';
function renderPlan(result) {
  var lines = planLines(result);
  var h = chapterHead(4, 'Your plan', 'Your plan') + '<p class="ch-sub">For you and your counselor to decide together.</p><div class="card plan">';
  h += lines.length ? '<ol class="plan-list">' + lines.map(function (l) { return '<li><b>' + esc(l.t) + '</b> ' + esc(l.x) + '</li>'; }).join('') + '</ol>'
    : '<p class="quiet">Add a college or two and the plan will fill in.</p>';
  h += '<p class="plan-close">This plan is a starting point. Your counselor makes the final call with you.</p></div>';
  h += '<p class="next"><button type="button" class="btn primary big" data-act="print">Print your plan</button>' +
    '<button type="button" class="linkbtn" data-act="why-no-percent" aria-expanded="false" aria-controls="why-answer">Why no percentage?</button></p>' +
    '<div id="why-answer" class="calm" hidden><p>' + esc(WHY_NO_PERCENT) + '</p>' +
    '<button type="button" class="btn small" data-act="see-cases">See how it went for students like you</button></div>' +
    '<p class="quiet small checked">Everything here was checked against its source. <button type="button" class="linkbtn" data-act="toggle-working">Show the working</button></p>';
  return h;
}

/* ====== closeness: how much a student resembles the people admitted and the people not admitted ======
   The rendering below this line down to "end of lifted code" is yuri's, lifted from the earlier screen and adapted
   to this palette and wording. A lean is a resemblance, never a forecast. */
function stateText(label) { return labelPhrase(label, true); }
function shape(key, extra) {
  return '<svg class="shape sh-' + esc(key) + '" viewBox="0 0 16 16" width="16" height="16" aria-hidden="true" focusable="false"' + (extra || '') + '><circle cx="8" cy="8" r="6"/></svg>';
}
function closenessOf(c) {
  var n = obj(obj(obj(c).closeness).national);
  return str(n.status) ? n : null;
}
function f2(v) { return (Math.round(v * 100) / 100).toString(); }
function ringsModel(result) {
  var rows = arr(obj(result).colleges).map(function (c, i) {
    c = obj(c);
    var L = obj(c.label), g = groupOf(L.state), n = closenessOf(c), d = n ? num(n.d_admitted) : null;
    var placed = n !== null && d !== null && (n.status === 'ok' || n.status === 'not_enough');
    return {i: i, c: c, L: L, g: g, n: n, d: d, placed: placed, hollow: placed && n.status !== 'ok'};
  });
  rows.sort(function (a, b) { return ORDER.indexOf(a.g) - ORDER.indexOf(b.g) || str(a.c.name).localeCompare(str(b.c.name)); });
  return rows;
}
function renderRings(result) {
  var rows = ringsModel(result), st = obj(obj(result).student), score = num(st.sat) !== null ? num(st.sat) : num(st.act);
  var W = 880, H = 560, CX = 440, CY = 280, R0 = 40, R1 = 200, DMAX = 0.6, ROUT = R0 + R1 + 24;
  function rad(d) { return R0 + R1 * Math.min(Math.max(d, 0) / DMAX, 1); }
  function p(v) { return (Math.round(v * 10) / 10).toString(); }
  var n = rows.length, placed = rows.filter(function (x) { return x.placed; }).length;
  var s = '<svg class="pic rings" viewBox="0 0 ' + W + ' ' + H + '" width="' + W + '" height="' + H + '" role="group" aria-label="' +
    esc('Rings: ' + n + ' ' + plural(n, 'college', 'colleges') + ' around the student. Nearer the centre means more like the people admitted there. ' +
        placed + ' placed' + (n - placed > 0 ? '; ' + (n - placed) + ' on the outer ring with too few cases to place' : '') + '. Distance is not the label.') + '">';
  [0.2, 0.4, 0.6].forEach(function (d) { s += '<circle class="rguide" cx="' + CX + '" cy="' + CY + '" r="' + p(rad(d)) + '"/>'; });
  s += '<circle class="rguide router" cx="' + CX + '" cy="' + CY + '" r="' + ROUT + '"/>' +
    '<text class="rguidet" x="' + CX + '" y="' + (CY - ROUT - 5) + '" text-anchor="middle">not enough cases to place</text>';
  s += '<g class="rcentre" aria-hidden="true"><circle class="rme" cx="' + CX + '" cy="' + CY + '" r="9"/>' +
    '<text class="rmet" x="' + CX + '" y="' + (CY + 25) + '" text-anchor="middle">You' + (score !== null ? ', ' + score : '') + '</text></g>';
  if (!n) s += '<text class="pnone" x="' + CX + '" y="' + (CY - 30) + '" text-anchor="middle">No colleges on this list yet.</text>';
  rows.forEach(function (x, k) {
    var ang = -Math.PI / 2 + k * 2 * Math.PI / Math.max(n, 1), rr = x.placed ? rad(x.d) : ROUT;
    var cx = CX + rr * Math.cos(ang), cy = CY + rr * Math.sin(ang), right = Math.cos(ang) >= -0.01;
    var name = str(x.c.name) || 'Unnamed college', nn = x.n || {};
    var say = name + '. ' + stateText(x.L) + '. ' +
      (x.placed ? str(nn.text) + ' Distance to the nearest admitted ' + f2(x.d) + (num(nn.d_denied) !== null ? ', to the nearest denied ' + f2(num(nn.d_denied)) : '') + '.' +
                  (x.hollow ? ' Too few cases, so this is rough.' : '')
                : (x.n ? str(nn.text) : 'No closeness data for this college.')) + ' Open the details.';
    s += '<g class="rdot rd-' + x.g + (x.hollow ? ' rd-hollow' : '') + (x.placed ? '' : ' rd-out') + '" data-act="open-receipt" data-i="' + x.i +
      '" tabindex="0" role="button" aria-label="' + esc(say) + '"><title>' + esc(name) + '</title>' +
      '<circle class="rhit" cx="' + p(cx) + '" cy="' + p(cy) + '" r="15"/>' +
      shape(x.g, ' x="' + p(cx - 8) + '" y="' + p(cy - 8) + '"') +
      '<text class="rname" x="' + p(cx + (right ? 13 : -13)) + '" y="' + p(cy + 4.5) + '" text-anchor="' + (right ? 'start' : 'end') + '">' +
      esc(clip(shortName(name), 24)) + '</text></g>';
  });
  return s + '</svg>';
}
/* ---------- Level 1: mind map. Student in the middle, a branch per label, a node per college, leaves under each. ---------- */
var MAP_MAX_LEAVES = 12;   /* above this many colleges, leaves show only for the college last pressed */
function mindMapModel(result, focus) {
  var rows = ringsModel(result), groups = {reach: [], target: [], likely: [], other: []};
  rows.forEach(function (x) { groups[groups[x.g] ? x.g : 'other'].push(x); });
  var showLeaves = rows.length <= MAP_MAX_LEAVES;
  function leavesFor(x) {
    var out = [], n = x.n || {};
    if (!showLeaves && focus !== x.i) return out;
    var shown = kindsShown(n), kind = shown === 'none' ? null : arr(n.kinds).map(obj).filter(function (q) { return q.nearest === true; })[0];
    if (kind) out.push({text: (shown === 'loose' ? 'Loose kind: ' : 'Kind: ') + clip(str(kind.name), 30), kind: 'kind'});
    arr(n.nearest_admitted).map(obj).slice(0, 3).forEach(function (e) { if (str(e.case_id)) out.push({text: str(e.case_id) + ' admitted', kind: 'case'}); });
    return out;
  }
  /* reach down the left, target down the right, likely along the bottom, "can't say" along the top when present */
  var BX = 150, NX = 330, BY = 150, NY = 300, GAP = 205, LINE = 14, PAD = 28;
  var branches = [], nodes = [], lines = [];
  [['reach', 'left'], ['target', 'right'], ['likely', 'bottom'], ['other', 'top']].forEach(function (sp) {
    var k = sp[0], side = sp[1], items = groups[k];
    if (k === 'other' && !items.length) return;
    var bx = side === 'left' ? -BX : (side === 'right' ? BX : 0), by = side === 'bottom' ? BY : (side === 'top' ? -BY : 0);
    branches.push({key: k, x: bx, y: by, title: k === 'other' ? "Can't say" : cap(k), n: items.length});
    lines.push({x1: 0, y1: 0, x2: bx, y2: by, kind: 'trunk'});
    var q = items.map(function (x) { return {row: x, leaves: leavesFor(x)}; });
    if (side === 'left' || side === 'right') {
      var hs = q.map(function (e) { return PAD + LINE * e.leaves.length; }), total = hs.reduce(function (a, b) { return a + b; }, 0), y = -total / 2;
      q.forEach(function (e, j) {
        var nx = side === 'left' ? -NX : NX, ny = y + 12;
        nodes.push({x: nx, y: ny, right: side === 'right', row: e.row, leaves: e.leaves});
        lines.push({x1: bx, y1: by, x2: nx, y2: ny, kind: 'limb'});
        y += hs[j];
      });
    } else {
      var x0 = -(q.length - 1) * GAP / 2;
      q.forEach(function (e, j) {
        var nx = x0 + j * GAP, ny = side === 'bottom' ? NY : -NY;
        nodes.push({x: nx, y: ny, right: true, row: e.row, leaves: e.leaves});
        lines.push({x1: bx, y1: by, x2: nx, y2: ny, kind: 'limb'});
      });
    }
  });
  return {branches: branches, nodes: nodes, lines: lines, showLeaves: showLeaves, n: rows.length};
}
function renderMindMap(result, focus) {
  var m = mindMapModel(result, focus), st = obj(obj(result).student), score = num(st.sat) !== null ? num(st.sat) : num(st.act);
  function p(v) { return (Math.round(v * 10) / 10).toString(); }
  var xs = [-120, 120], ys = [-40, 40];
  m.branches.forEach(function (b) { xs.push(b.x - 70, b.x + 70); ys.push(b.y - 16, b.y + 16); });
  m.nodes.forEach(function (q) {
    xs.push(q.right ? q.x + 235 : q.x - 235, q.x);
    ys.push(q.y - 16, q.y + 24 + 14 * q.leaves.length);
  });
  var X0 = Math.min.apply(null, xs) - 12, X1 = Math.max.apply(null, xs) + 12, Y0 = Math.min.apply(null, ys) - 12, Y1 = Math.max.apply(null, ys) + 12;
  var W = X1 - X0, H = Y1 - Y0;
  var s = '<svg class="pic mindmap" viewBox="' + p(X0) + ' ' + p(Y0) + ' ' + p(W) + ' ' + p(H) + '" width="' + p(W) + '" height="' + p(H) + '" role="group" aria-label="' +
    esc('Mind map: the student in the middle, ' + m.branches.map(function (b) { return b.title.toLowerCase() + ' (' + b.n + ')'; }).join(', ') +
        ', a node per college' + (m.showLeaves ? ', and under each college its nearest kind of admitted student and its nearest admitted cases.' :
        '. With more than ' + MAP_MAX_LEAVES + ' colleges, the nearest kind and cases show only for the college last pressed.')) + '">';
  m.lines.forEach(function (l) { s += '<line class="mm-' + l.kind + '" x1="' + p(l.x1) + '" y1="' + p(l.y1) + '" x2="' + p(l.x2) + '" y2="' + p(l.y2) + '"/>'; });
  m.branches.forEach(function (b) {
    var t = b.title + ' (' + b.n + ')', w = t.length * 7.6 + 22;
    s += '<g class="mm-branch mm-' + b.key + '" aria-hidden="true"><rect x="' + p(b.x - w / 2) + '" y="' + p(b.y - 13) + '" width="' + p(w) + '" height="26" rx="13"/>' +
      '<text x="' + p(b.x) + '" y="' + p(b.y + 4.5) + '" text-anchor="middle">' + esc(t) + '</text></g>';
  });
  s += '<g class="rcentre" aria-hidden="true"><circle class="rme" cx="0" cy="0" r="11"/><text class="rmet" x="0" y="-19" text-anchor="middle">You' + (score !== null ? ', ' + score : '') + '</text></g>';
  if (!m.n) s += '<text class="pnone" x="0" y="-50" text-anchor="middle">No colleges on this list yet.</text>';
  m.nodes.forEach(function (q) {
    var x = q.row, name = str(x.c.name) || 'Unnamed college', nn = x.n || {}, dir = q.right ? 1 : -1, anchor = q.right ? 'start' : 'end';
    var kind = kindsShown(nn) === 'none' ? null : arr(nn.kinds).map(obj).filter(function (k) { return k.nearest === true; })[0];
    var say = name + '. ' + stateText(x.L) + '. ' + (x.n ? str(nn.text) + ' ' : '') +
      (kind ? 'Nearest kind of admitted student' + (kindsShown(nn) === 'loose' ? ' (loose grouping)' : '') + ': ' + str(kind.name) + '. ' : '') +
      (arr(nn.nearest_admitted).length ? 'Nearest admitted cases: ' + arr(nn.nearest_admitted).map(function (e) { return str(obj(e).case_id); }).join(', ') + '. ' : '') + 'Open the details.';
    s += '<g class="rdot mm-node rd-' + x.g + (x.hollow ? ' rd-hollow' : '') + '" data-act="open-receipt" data-i="' + x.i + '" tabindex="0" role="button" aria-label="' + esc(say) + '"><title>' + esc(name) + '</title>' +
      '<circle class="rhit" cx="' + p(q.x) + '" cy="' + p(q.y) + '" r="14"/>' + shape(x.g, ' x="' + p(q.x - 8) + '" y="' + p(q.y - 8) + '"') +
      '<text class="rname" x="' + p(q.x + 13 * dir) + '" y="' + p(q.y + 4.5) + '" text-anchor="' + anchor + '">' + esc(clip(shortName(name), 26)) + '</text>';
    q.leaves.forEach(function (l, k) {
      var ly = q.y + 20 + 14 * k;
      s += '<circle class="mm-leaf-dot mm-leaf-' + l.kind + '" cx="' + p(q.x + 17 * dir) + '" cy="' + p(ly - 3.5) + '" r="2.6"/>' +
        '<text class="mm-leaf" x="' + p(q.x + 24 * dir) + '" y="' + p(ly) + '" text-anchor="' + anchor + '">' + esc(l.text) + '</text>';
    });
    s += '</g>';
  });
  return s + '</svg>';
}
/* ---------- Level 1: clusters. One college, a 3 by 3 grid of rule-defined clusters (the contract's `groups`): score band by activities band. ---------- */
/* Groups are set by a written rule (the engine's ACT_MID, ACT_HIGH, GROUP_MIN, GROUP_FEW, read from the result), so a
   counselor can recount them by hand. Every dot is one real finished case. The pressed cell grows; its cases list below. */
var GROUP_COLS = [['below', 'Below the range'], ['inside', 'Inside the range'], ['above', 'Above the range']];
var GROUP_ROWS = [['high', 'High'], ['mid', 'Middle'], ['low', 'Low']];
var GROUP_PAGE = 12;
var OUTCOME_LETTER = {a: 'admitted', w: 'waitlisted', d: 'denied'};
function groupsOf(c) { var n = closenessOf(c); return n && Array.isArray(obj(n.groups).cells) ? obj(n.groups) : null; }
function hasGroups(result) { return arr(obj(result).colleges).some(function (c) { return !!groupsOf(c); }); }
function scoreBand(score, lo, hi) { return score < lo ? 'below' : (score > hi ? 'above' : 'inside'); }
function actBand(r, mid, high) { return r >= high ? 'high' : (r >= mid ? 'mid' : 'low'); }
/* Kinds are named on the screen only when the engine's check passes: 'clear' or 'loose'; a missing check counts as 'none'. */
function kindsShown(pool) { var v = str(obj(obj(pool).kinds_check).verdict); return v === 'clear' || v === 'loose' ? v : 'none'; }
function groupCase(k) { return {case_id: str(k[0]), sat: num(k[1]), activities_rating: num(k[2]), outcome: OUTCOME_LETTER[str(k[3])] || 'denied', major: str(k[4]), hooks: str(k[5])}; }
function groupsModel(result, opts) {
  var o = obj(opts), cs = arr(obj(result).colleges).map(obj);
  var rows = cs.map(function (c, i) {
    var g = groupsOf(c);
    return {i: i, c: c, L: obj(c.label), groups: g, ok: !!g && str(g.status) === 'ok'};
  }).filter(function (x) { return x.groups; });
  var pick = null, focus = num(o.focus);
  rows.forEach(function (x) { if (pick === null && x.i === focus && x.ok) pick = x; });   /* the college pressed in rings or the map, if it has a grid */
  if (!pick) rows.forEach(function (x) { if (!pick && x.ok) pick = x; });
  if (!pick) pick = rows[0] || null;
  var m = {rows: rows, pick: pick, cells: {}, majors: [], major: '', mine: null, note: '', actNote: ''};
  if (!pick) return m;
  var g = pick.groups, lo = num(g.sat25), hi = num(g.sat75), mid = num(g.act_mid) !== null ? num(g.act_mid) : 6, high = num(g.act_high) !== null ? num(g.act_high) : 8;
  var minN = num(g.min_n) !== null ? num(g.min_n) : 5, fewN = num(g.few_n) !== null ? num(g.few_n) : 15;
  m.lo = lo; m.hi = hi; m.mid = mid; m.high = high; m.minN = minN; m.fewN = fewN;
  var counts = {};
  arr(g.cells).map(obj).forEach(function (cell) {
    arr(cell.cases).filter(Array.isArray).forEach(function (k) { var mj = str(k[4]); if (mj) counts[mj] = (counts[mj] || 0) + 1; });
  });
  m.majors = Object.keys(counts).filter(function (mj) { return counts[mj] >= 30; }).sort();
  m.major = m.majors.indexOf(str(o.major)) !== -1 ? str(o.major) : '';
  arr(g.cells).map(obj).forEach(function (cell) {
    var key = str(cell.score_band) + '|' + str(cell.activities_band), cases = arr(cell.cases).filter(Array.isArray);
    var kept = m.major ? cases.filter(function (k) { return str(k[4]) === m.major; }) : cases, a = 0, w = 0, d = 0;
    if (m.major) kept.forEach(function (k) { if (k[3] === 'a') a++; else if (k[3] === 'w') w++; else d++; });
    else { a = num(cell.admitted) || 0; w = num(cell.waitlisted) || 0; d = num(cell.denied) || 0; }
    var n = m.major ? kept.length : (num(cell.n) !== null ? num(cell.n) : kept.length);
    m.cells[key] = {key: key, a: a, w: w, d: d, n: n, cases: kept, state: n < minN ? 'not_enough' : (n < fewN ? 'few' : 'ok')};
    if (cell.is_student === true) m.mine = key;
  });
  var st = obj(obj(obj(pick.c).closeness).student), act = num(st.activities), score = num(st.score);
  if (o.whatIf === true && num(o.score) !== null && pick.ok) {
    if (o.kind !== 'ACT') score = num(o.score);
    else m.actNote = 'The what-if score is on the ACT scale, so the outlined cluster stays where the real score put it.';
  }
  /* the column is known from the score alone; the one cell needs the activities rating too */
  m.score = score; m.act = act;
  m.myCol = pick.ok && score !== null && lo !== null && hi !== null ? scoreBand(score, lo, hi) : null;
  if (m.myCol && act !== null) m.mine = m.myCol + '|' + actBand(act, mid, high);
  m.estimate = '';
  if (m.mine && str(st.activities_from) === 'estimated') {
    var why = arr(st.activities_why).map(str).filter(Boolean);
    m.estimate = 'Activities rating ' + act + ', estimated from the activities listed by a written rule' + (why.length ? ' (' + why.join('; ') + ')' : '') +
      '. Your own rating under Counselor tools, Change the details, replaces it.' + (str(st.activities_rule) ? ' Rule: ' + str(st.activities_rule) : '');
  }
  if (m.mine) m.note = '';
  else if (m.myCol) m.note = 'Score ' + score + ' puts this student in the column "' + GROUP_COLS.filter(function (x) { return x[0] === m.myCol; })[0][1].toLowerCase() + '". Give an activities rating (Counselor tools, Change the details) to pick the row.';
  else m.note = str(g.student_note);
  return m;
}
function groupDots(cell) {
  var h = '';
  [['a', cell.a], ['w', cell.w], ['d', cell.d]].forEach(function (p) { for (var i = 0; i < p[1]; i++) h += '<i class="gd gd-' + p[0] + '"></i>'; });
  return '<span class="g-dots" aria-hidden="true">' + h + '</span>';
}
function groupWords(key) {
  var p = str(key).split('|'), c = GROUP_COLS.filter(function (x) { return x[0] === p[0]; })[0], r = GROUP_ROWS.filter(function (x) { return x[0] === p[1]; })[0];
  return {col: c ? c[1].toLowerCase() : '', row: r ? r[1].toLowerCase() : ''};
}
function renderGroups(result, opts) {
  var o = obj(opts), m = groupsModel(result, opts), h = '<div class="groups">';
  if (!m.rows.length) return h + '<p class="calm">No college on this list has clusters to show.</p></div>';
  h += '<div class="picks g-picks" role="group" aria-label="College">' + m.rows.map(function (x) {
    return '<button type="button" class="pick g-pick" data-act="groups-college" data-i="' + x.i + '" aria-pressed="' + (x === m.pick ? 'true' : 'false') + '">' +
      esc(shortName(x.c.name)) + ' <span class="g-pill p-' + groupOf(x.L.state) + '"><i class="dot" aria-hidden="true"></i>' + esc(WORD[groupOf(x.L.state)]) + '</span></button>';
  }).join('') + '</div>';
  var pk = m.pick, g = pk.groups, c = pk.c;
  h += '<h3 class="g-h">' + esc(shortName(c.name)) + ': finished cases by score and activities</h3>';
  if (!pk.ok) return h + '<p class="calm"><b>Can\'t say.</b> ' + esc(str(g.reason) || 'There is no grid for this college.') + '</p>' + renderKindsCheck(closenessOf(c)) + '</div>';
  var open = m.cells[str(o.cell)] ? str(o.cell) : '', openCol = open.split('|')[0];
  h += '<div class="g-head"><p class="quiet small">Published middle score range: <b>' + m.lo + ' to ' + m.hi + '</b>. Official admit rate: <b>' + esc(inHundred(c.admit_rate) || 'not published') + '</b>.</p>';
  if (m.majors.length) {
    h += '<label class="g-filter">Show only this major group <select id="groups-major"><option value=""' + (m.major ? '' : ' selected') + '>All majors</option>' + m.majors.map(function (mj) {
      return '<option value="' + esc(mj) + '"' + (mj === m.major ? ' selected' : '') + '>' + esc(majorText(mj)) + '</option>';
    }).join('') + '</select></label>';
  }
  h += '</div>';
  var cols = 'minmax(58px,auto) ' + GROUP_COLS.map(function (x) { return x[0] === openCol ? 'minmax(0,2fr)' : 'minmax(0,1fr)'; }).join(' ');
  h += '<div class="g-grid" style="grid-template-columns:' + cols + '" role="group" aria-label="Nine clusters of past applicants at ' + esc(shortName(c.name)) + (m.major ? ', ' + esc(majorText(m.major)) + ' only' : '') + '">';
  var colOnly = m.myCol && !m.mine;
  h += '<div></div>' + GROUP_COLS.map(function (x) {
    var meCol = colOnly && x[0] === m.myCol;   /* the column is tagged only until a rating picks the one cell */
    return '<div class="g-colh' + (meCol ? ' g-mecol' : '') + '">' + (meCol ? '<span class="g-tag">This student\'s score</span>' : '') + '<b>' + x[1] + '</b>' + (x[0] === 'below' ? 'under ' + m.lo : (x[0] === 'above' ? 'over ' + m.hi : m.lo + ' to ' + m.hi)) + '</div>';
  }).join('');
  GROUP_ROWS.forEach(function (r) {
    var range = r[0] === 'high' ? m.high + ' to 10' : (r[0] === 'mid' ? m.mid + ' to under ' + m.high : 'under ' + m.mid);
    h += '<div class="g-rowh"><b>' + r[1] + '</b>activities ' + esc(range) + '</div>';
    GROUP_COLS.forEach(function (x) {
      var key = x[0] + '|' + r[0], cell = m.cells[key] || {a: 0, w: 0, d: 0, n: 0, state: 'not_enough'}, me = key === m.mine, isOpen = key === open;
      var thin = cell.state === 'not_enough', inCol = colOnly && x[0] === m.myCol;
      var say = thin ? 'Not enough cases (' + cell.n + ')' : cell.a + ' admitted · ' + cell.w + ' waitlisted · ' + cell.d + ' denied (' + cell.n + (cell.state === 'few' ? ', few' : '') + ')';
      h += '<button type="button" class="g-cell' + (me ? ' g-me' : '') + (inCol ? ' g-mecol' : '') + (thin ? ' g-thin' : '') + (isOpen ? ' g-open' : '') + '" data-act="groups-cell" data-key="' + key + '" aria-pressed="' + (isOpen ? 'true' : 'false') +
        '" aria-label="' + esc(x[1] + ', ' + r[1].toLowerCase() + ' activities: ' + say + (me ? '. This student is here.' : (inCol ? '. This student\'s score column; the row needs an activities rating.' : '.')) + (isOpen ? ' Open; press again to shrink it.' : ' Press to enlarge this cluster and list its cases.')) + '">' +
        (me ? '<span class="g-tag">This student</span>' : '') + (thin ? '' : groupDots(cell)) +
        '<span class="g-counts">' + (thin ? esc(say) : cell.a + ' admitted · ' + cell.w + ' waitlisted · ' + cell.d + ' denied <em>(' + cell.n + (cell.state === 'few' ? ', few' : '') + ')</em>') + '</span></button>';
    });
  });
  h += '</div>';
  var left = num(g.left_out) || 0;
  h += '<p class="g-legend small"><span><i class="gd gd-a" aria-hidden="true"></i>admitted</span><span><i class="gd gd-w" aria-hidden="true"></i>waitlisted</span><span><i class="gd gd-d" aria-hidden="true"></i>denied</span>' +
    '<span class="quiet">Hatched: fewer than ' + m.minN + ' cases, so no counts. "Few": under ' + m.fewN + '.</span>' +
    (left ? '<span class="quiet">' + left + ' ' + plural(left, 'case', 'cases') + ' left out: no score or no activities rating reported.</span>' : '') +
    (g.capped === true ? '<span class="quiet">The list is capped, spread evenly through the file.</span>' : '') + '</p>';
  if (m.note) h += '<p class="calm">' + esc(m.note) + '</p>';
  if (m.estimate) h += '<p class="quiet small">' + esc(m.estimate) + '</p>';
  if (m.actNote) h += '<p class="quiet small">' + esc(m.actNote) + '</p>';
  if (open) {
    var oc = m.cells[open], words = groupWords(open), shown = Math.min(oc.cases.length, GROUP_PAGE * Math.max(1, num(o.more) || 1));
    h += '<div class="g-list" id="groups-list"><h4>' + (open === m.mine ? 'This student\'s cluster: ' : 'Cluster: ') + 'score ' + esc(words.col) + ', ' + esc(words.row) + ' activities. ' +
      oc.cases.length + ' ' + plural(oc.cases.length, 'case', 'cases') + (oc.cases.length ? ', closest score first' : '') + (m.major ? ' (' + esc(majorText(m.major)) + ' only)' : '') + '</h4>' +
      (oc.cases.length ? examplesTable(oc.cases.slice(0, shown).map(groupCase)) : '<p class="quiet">No finished cases in this cluster.</p>') +
      (oc.cases.length > shown ? '<p><button type="button" class="linkbtn" data-act="groups-more">Show ' + Math.min(GROUP_PAGE, oc.cases.length - shown) + ' more</button> <span class="quiet small">Showing ' + shown + ' of ' + oc.cases.length + '.</span></p>' : '') + '</div>';
  }
  h += '<p class="g-note">' + esc(str(g.caveat) || 'These are self-reported public posts. Read the dots as examples, not as a forecast for this student.') + '</p>';
  return h + renderKindsCheck(closenessOf(c)) + '</div>';
}
/* G4: did the computer find its own kinds here? Three numbers from the engine, each beside what it needs. */
function renderKindsCheck(pool) {
  var p = obj(pool), c = p.kinds_check ? obj(p.kinds_check) : null, h = '<div class="kcheck"><p class="label">Checked, not assumed</p><h4>Did the computer find its own kinds of admitted student here?</h4>';
  if (!c) return h + '<p class="k-verdict">No kinds were made here.</p><p class="quiet small">' + (arr(p.kinds).length ? 'This result carries no check, so the kinds are not named.' : 'Too few admitted cases to group, or no cases at all.') + '</p></div>';
  var needs = obj(c.needs), sep = num(c.separation), shu = num(c.shuffled), stab = num(c.stability);
  var needSep = num(needs.separation) !== null ? num(needs.separation) : 0.51, margin = num(needs.margin) !== null ? num(needs.margin) : 0.05, needStab = num(needs.stability) !== null ? num(needs.stability) : 0.75;
  var beats = sep !== null && shu !== null && sep - shu >= margin;
  function row(val, label, need, ok) { return '<div><b class="' + (ok ? 'pass' : 'fail') + '">' + (val === null ? '—' : f2(val)) + '</b>' + esc(label) + '<br><small>' + esc(need) + '</small></div>'; }
  h += '<p class="k-verdict k-' + esc(str(c.verdict)) + '">' + esc(str(c.text) || 'No clear kinds at this college.') + '</p><div class="kv3">' +
    row(sep, 'How separate the kinds are', 'needs ' + needSep + ' or more', sep !== null && sep >= needSep) +
    row(shu, 'Same test on shuffled data', 'real data must beat this by ' + margin, beats) +
    row(stab, 'Same kinds on 8 in 10 of the cases', 'needs ' + needStab + ' or more', stab !== null && stab >= needStab) + '</div>' +
    '<p class="quiet small">The grouping method always returns groups, even when none exist, so kinds are named on this screen only when they pass all three tests. The rule-based clusters above need no such test.</p></div>';
  return h;
}
var LEAN_WORD = {closer_to_admitted: 'Looks more like the students admitted', closer_to_denied: 'Looks more like the students not admitted', in_between: 'In between the two groups'};
var PART_NAME = {score: 'Score', activities: 'Activities', major: 'Major', hooks: 'Background', residency: 'Home state', gpa: 'GPA', essay: 'Essay content', activity_text: 'Activity descriptions'};
function leanWord(v) { return LEAN_WORD[str(v)] || str(v).replace(/_/g, ' '); }
function starPath(cx, cy, r) {
  var pts = [];
  for (var i = 0; i < 10; i++) {
    var a = -Math.PI / 2 + i * Math.PI / 5, rr = i % 2 ? r * 0.45 : r;
    pts.push((Math.round((cx + rr * Math.cos(a)) * 10) / 10) + ',' + (Math.round((cy + rr * Math.sin(a)) * 10) / 10));
  }
  return pts.join(' ');
}
/* score across, activities rating up; circle = admitted, cross = denied, diamond = waitlisted; kinds' medoids ringed; student = star */
function renderScatter(pool, student) {
  var n = obj(pool), st = obj(student), pts = arr(n.points).map(obj).filter(function (p) { return num(p.sat) !== null; });
  if (!pts.length) return '';
  var drawn = pts.filter(function (p) { return num(p.activities) !== null; }), skipped = pts.length - drawn.length;
  var sScore = num(st.score), sAct = num(st.activities);
  var W = 640, H = 300, L = 46, R = 14, T = 16, B = 36;
  var xs = drawn.map(function (p) { return num(p.sat); }); if (sScore !== null) xs.push(sScore);
  if (!xs.length) return '';
  var xmin = Math.max(400, Math.floor((Math.min.apply(null, xs) - 40) / 50) * 50), xmax = Math.min(1600, Math.ceil((Math.max.apply(null, xs) + 40) / 50) * 50);
  if (xmax - xmin < 100) { xmin = Math.max(400, xmin - 50); xmax = Math.min(1600, xmax + 50); }
  function sx(v) { return L + (v - xmin) / (xmax - xmin) * (W - L - R); }
  function sy(v) { return T + (10 - v) / 10 * (H - T - B); }
  function p(v) { return (Math.round(v * 10) / 10).toString(); }
  var medoid = {}, showKinds = kindsShown(n) !== 'none';
  if (showKinds) arr(n.kinds).map(obj).forEach(function (k) { if (str(k.medoid_case_id)) medoid[str(k.medoid_case_id)] = str(k.kind_id); });
  var counts = {admitted: 0, denied: 0, waitlisted: 0}; drawn.forEach(function (q) { if (counts[q.outcome] !== undefined) counts[q.outcome]++; });
  var say = 'Scatter of ' + drawn.length + ' ' + plural(drawn.length, 'case', 'cases') + ' at this college: score across, activities rating up. ' +
    counts.admitted + ' admitted as circles, ' + counts.denied + ' denied as crosses, ' + counts.waitlisted + ' waitlisted as diamonds. ' +
    (sScore !== null ? (sAct !== null ? 'The student is the star at score ' + sScore + ' and rating ' + sAct + '. ' : 'The student is the vertical line at score ' + sScore + '; no activities rating was given. ') : 'The student has no score, so is not drawn. ') +
    (showKinds && arr(n.kinds).length ? 'The medoid of each kind of admitted student is ringed and labelled. ' : '') +
    (skipped ? skipped + ' ' + plural(skipped, 'case has', 'cases have') + ' no activities rating and ' + plural(skipped, 'is', 'are') + ' not drawn.' : '');
  var s = '<svg class="scatter" viewBox="0 0 ' + W + ' ' + H + '" width="' + W + '" height="' + H + '" role="img" aria-label="' + esc(say) + '">';
  var step = (xmax - xmin) > 600 ? 200 : 100, t;
  for (t = Math.ceil(xmin / step) * step; t <= xmax; t += step) {
    s += '<line class="sc-grid" x1="' + p(sx(t)) + '" x2="' + p(sx(t)) + '" y1="' + T + '" y2="' + (H - B) + '"/>' +
      '<text class="sc-tick" x="' + p(sx(t)) + '" y="' + (H - B + 14) + '" text-anchor="middle">' + t + '</text>';
  }
  for (t = 0; t <= 10; t += 2) {
    s += '<line class="sc-grid" x1="' + L + '" x2="' + (W - R) + '" y1="' + p(sy(t)) + '" y2="' + p(sy(t)) + '"/>' +
      '<text class="sc-tick" x="' + (L - 6) + '" y="' + p(sy(t) + 4) + '" text-anchor="end">' + t + '</text>';
  }
  s += '<line class="sc-axis" x1="' + L + '" x2="' + (W - R) + '" y1="' + (H - B) + '" y2="' + (H - B) + '"/><line class="sc-axis" x1="' + L + '" x2="' + L + '" y1="' + T + '" y2="' + (H - B) + '"/>' +
    '<text class="sc-ax" x="' + (W - R) + '" y="' + (H - 6) + '" text-anchor="end">Score (SAT scale)</text>' +
    '<text class="sc-ax" x="' + (L + 4) + '" y="' + (T - 4) + '">Activities rating</text>';
  drawn.forEach(function (q) {
    var x = sx(num(q.sat)), y = sy(num(q.activities)), o = str(q.outcome);
    if (o === 'admitted') s += '<circle class="sc-a" cx="' + p(x) + '" cy="' + p(y) + '" r="4"/>';
    else if (o === 'denied') s += '<path class="sc-d" d="M' + p(x - 3.5) + ' ' + p(y - 3.5) + 'l7 7M' + p(x + 3.5) + ' ' + p(y - 3.5) + 'l-7 7"/>';
    else s += '<rect class="sc-w" x="' + p(x - 3) + '" y="' + p(y - 3) + '" width="6" height="6" transform="rotate(45 ' + p(x) + ' ' + p(y) + ')"/>';
    if (medoid[str(q.case_id)]) s += '<circle class="sc-medoid" cx="' + p(x) + '" cy="' + p(y) + '" r="9"/><text class="sc-mk" x="' + p(x + 11) + '" y="' + p(y - 8) + '">' + esc(medoid[str(q.case_id)]) + '</text>';
  });
  if (sScore !== null) {
    var lx = sx(sScore);
    if (sAct !== null) s += '<polygon class="sc-me" points="' + starPath(lx, sy(sAct), 9) + '"/>';
    else s += '<line class="sc-line" x1="' + p(lx) + '" x2="' + p(lx) + '" y1="' + T + '" y2="' + (H - B) + '"/>';
    s += '<text class="sc-mk" x="' + p(Math.min(lx + 8, W - R - 50)) + '" y="' + (T + 11) + '">Student</text>';
  }
  return s + '</svg>';
}
function renderPartBars(parts) {
  var ps = arr(parts).map(obj).filter(function (q) { return str(q.part) && num(q.distance) !== null; });
  if (!ps.length) return '<p class="quiet">No parts to compare.</p>';
  return '<ul class="pbars" aria-label="How close you are to the nearest admitted students, part by part">' + ps.map(function (q) {
    var d = Math.max(0, Math.min(1, num(q.distance)));
    return '<li><span class="pb-name">' + esc(PART_NAME[str(q.part)] || cap(q.part)) + '</span>' +
      '<span class="pb-track" aria-hidden="true"><span class="pb-fill" style="width:' + Math.round(d * 100) + '%"></span></span>' +
      '<span class="pb-word">' + esc(str(q.text)) + ' <span class="quiet working-only">(' + f2(d) + ')</span></span></li>';
  }).join('') + '</ul>';
}
function renderClosenessCheck(cc) {
  var c = obj(cc), rows = arr(c.rows).map(obj).filter(function (r) { return str(r.lean); });
  if (!rows.length) return '';
  return '<div class="ccheck"><p><b>Does the resemblance hold up? Checked on ' + (num(c.used) || 0) + ' past decisions.</b> Each person was hidden in turn, the resemblance worked out without them, and then their real result counted. These are counts of past posters, not odds for anyone.</p>' +
    '<table class="kv ccheck-t"><thead><tr><th scope="col">Resemblance</th><th scope="col">Were admitted</th><th scope="col">Were not admitted</th></tr></thead><tbody>' +
    rows.map(function (r) { return '<tr><th scope="row">' + esc(leanWord(r.lean)) + '</th><td>' + (num(r.admitted) || 0) + '</td><td>' + (num(r.denied) || 0) + '</td></tr>'; }).join('') +
    '</tbody></table>' + (str(c.caveat) ? '<p class="quiet small">' + esc(c.caveat) + '</p>' : '') + '</div>';
}
var METHOD_FALLBACK = {
  parts: [
    {part: 'score', name: 'score', weight: 0.45, distance: 'score difference / 400 SAT points, capped at 1', student: 'SAT, or ACT converted to the SAT scale', case: 'SAT, or ACT converted', pools: 'both', required: true},
    {part: 'activities', name: 'activities rating', weight: 0.2, distance: 'rating difference / 10', student: "the counselor's 0 to 10 rating (optional)", case: 'self-rated activities and awards, 0 to 10', pools: 'national only'},
    {part: 'major', name: 'major group', weight: 0.15, distance: '0 same group, 1 different', student: "intended major, or the essay reader's tag when both models agreed", case: 'stated major', pools: 'both'},
    {part: 'hooks', name: 'hook status', weight: 0.1, distance: '0 same set of hooks, 1 different', student: 'first-gen, legacy, under-represented, athlete, or none', case: 'the same set', pools: 'both'},
    {part: 'residency', name: 'residency', weight: 0.1, distance: '0 if both in-state or both out-of-state for this college, else 1', student: 'home state', case: 'home state', pools: 'both, public colleges only'},
    {part: 'gpa', name: 'GPA', weight: 0.2, distance: 'GPA difference / 1 on a 4.0 scale, capped at 1', student: 'GPA, converted to a 4.0 scale', case: "GPA in the school's own file", pools: 'own only'}
  ],
  never_used: ['essay text', 'activity descriptions', 'race', 'gender', 'income', 'class rank', 'the essay/recommendation/interview self-rating'],
  neighbours: 7, needed: 15, lean_gap: 0.03, change_gain: 0.02, max_changes: 3, score_steps: [30, 60, 100], rating_steps: [1, 2], close: 0.15, far: 0.5,
  steady: {neighbours: [5, 10], score: [-30, 30]},
  kinds: {k: 3, min_admitted: 30, cap: 300, rounds: 20, seed: 20261010, parts: ['score', 'activities', 'major'], score_band: 40, rating_band: 1},
  points_cap: 300, check: {n: 400, seed: 20261010},
  libraries: {engine: ['csv', 'json', 'functools.lru_cache', 'random', 'statistics', 'collections.Counter', 'pathlib'],
              not_used: ['numpy', 'scikit-learn', 'pandas', 'text embeddings', 'any model call'],
              screen: ['plain HTML, CSS and JavaScript', 'inline SVG drawn by hand', 'no chart library, no framework, no build step']}
};
function methodOf(result) { var m = obj(obj(result).closeness_method); return arr(m.parts).length ? m : METHOD_FALLBACK; }
function renderWeightsTable(m) {
  var parts = arr(m.parts).map(obj);
  var h = '<div class="table-wrap"><table class="cases-table weights" aria-label="Parts of the distance and their weights"><thead><tr>' +
    '<th scope="col">Part</th><th scope="col">Weight</th><th scope="col">Distance, 0 same to 1 far</th><th scope="col">Student side</th><th scope="col">Case side</th><th scope="col">Pools</th></tr></thead><tbody>';
  h += parts.map(function (p) {
    return '<tr><th scope="row">' + esc(cap(p.name)) + (p.required ? ' <span class="quiet">(required)</span>' : '') + '</th><td class="w-num">' + esc(f2(num(p.weight) || 0)) + '</td><td>' + esc(p.distance) + '</td>' +
      '<td>' + esc(p.student) + '</td><td>' + esc(p['case']) + '</td><td>' + esc(p.pools) + '</td></tr>';
  }).join('');
  h += '</tbody></table></div>';
  /* the shares that apply in practice, after renormalising over the parts present */
  function share(keys) {
    var tot = 0, out = [];
    parts.forEach(function (p) { if (keys.indexOf(p.part) !== -1) tot += num(p.weight) || 0; });
    parts.forEach(function (p) { if (keys.indexOf(p.part) !== -1) out.push(cap(p.name) + ' ' + Math.round((num(p.weight) || 0) / tot * 100) + '%'); });
    return out.join(', ');
  }
  h += '<p class="small">Only the parts both sides have are used, and the weights are renormalised over them. In practice:</p><ul class="plain small">' +
    '<li>National pool, private college, no activities rating entered: ' + esc(share(['score', 'major', 'hooks'])) + '.</li>' +
    '<li>National pool, public college, activities rating entered: ' + esc(share(['score', 'activities', 'major', 'hooks', 'residency'])) + '.</li>' +
    '<li>The school\'s own pool (no rating in that file), private college: ' + esc(share(['score', 'major', 'hooks', 'gpa'])) + '.</li></ul>';
  if (arr(m.never_used).length) h += '<p class="small"><b>Never used:</b> ' + esc(arr(m.never_used).map(str).join(', ')) + '.</p>';
  return h;
}
/* The algorithm as boxes and arrows. Text first: the aria-label says the same thing in one paragraph. */
function renderAlgorithmDiagram(m) {
  var k = num(m.neighbours) || 7, gap = num(m.lean_gap) || 0.03, kd = obj(m.kinds), gain = num(m.change_gain) || 0.02;
  var W = 760, H = 500;
  var say = 'How closeness is computed. The student input becomes a view: score, activities rating, major group, hooks, home state, GPA. ' +
    'One college\'s finished cases, from two pools kept apart, are split into admitted, denied and waitlisted. The distance to each case is the weighted mean of the parts both sides have. ' +
    'The mean distance to the ' + k + ' nearest admitted and to the ' + k + ' nearest denied gives a gap; a gap of ' + gap + ' or more leans to admitted, ' + (-gap) + ' or less to denied, else in between. ' +
    'Three side checks: the steady test reruns with ' + arr(obj(m.steady).neighbours).join(' and ') + ' nearest and the score 30 points either way; changes try a higher score, a higher activities rating or a named major and keep those that raise the gap by ' + gain + ' or more; ' +
    'kinds group the admitted cases into ' + (num(kd.k) || 3) + ' with k-medoids. No model is called anywhere.';
  var s = '<svg class="algo" viewBox="0 0 ' + W + ' ' + H + '" width="' + W + '" height="' + H + '" role="img" aria-label="' + esc(say) + '">' +
    '<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0 0L10 5 0 10z" class="al-arrhead"/></marker></defs>';
  function box(x, y, w, h, lines, cls) {
    var out = '<g class="al-box ' + (cls || '') + '"><rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '" rx="8"/>';
    lines.forEach(function (t, i) { out += '<text x="' + (x + 12) + '" y="' + (y + 20 + i * 16) + '"' + (i === 0 ? ' class="al-h"' : '') + '>' + esc(t) + '</text>'; });
    return out + '</g>';
  }
  function arrow(x1, y1, x2, y2) { return '<line class="al-arr" x1="' + x1 + '" y1="' + y1 + '" x2="' + x2 + '" y2="' + y2 + '" marker-end="url(#arr)"/>'; }
  s += box(10, 10, 220, 78, ['1. Student input', 'SAT or ACT, GPA, major, hooks,', 'home state, activities rating', '(the essay is never read here)'], 'al-in');
  s += arrow(230, 49, 268, 49);
  s += box(270, 10, 230, 78, ['2. Student view, built once', 'score (ACT converted), rating,', 'major group (or reader tag if', 'both models agreed), hooks, state'], 'al-in');
  s += box(520, 10, 230, 78, ['3. One college\'s cases', 'two pools, never merged:', 'national (self-reported) and', 'own (the school\'s, verified)'], 'al-data');
  s += arrow(635, 88, 635, 118);
  s += box(520, 120, 230, 62, ['4. Split, scored cases only', 'admitted | denied', 'waitlisted: counted, not compared'], 'al-data');
  s += arrow(385, 88, 385, 118);
  s += box(270, 120, 230, 62, ['5. Distance to each case', 'weighted mean of the parts', 'both sides have (table above)'], 'al-calc');
  s += arrow(520, 151, 502, 151);
  s += arrow(385, 182, 385, 212);
  s += box(270, 214, 230, 62, ['6. ' + k + ' nearest of each group', 'd_admitted = mean distance', 'd_denied = mean distance'], 'al-calc');
  s += arrow(385, 276, 385, 306);
  s += box(270, 308, 230, 78, ['7. gap = d_denied − d_admitted', 'lean: gap ≥ ' + gap + ' closer to admitted', 'gap ≤ ' + (-gap) + ' closer to denied', 'else in between'], 'al-out');
  s += arrow(500, 347, 518, 347);
  s += box(520, 308, 230, 78, ['8. Status gates', 'ok: both groups ≥ ' + (num(m.needed) || 15), 'not enough: either 1 to ' + ((num(m.needed) || 15) - 1) + ' (no lean given)', 'none / can\'t say (no score)'], 'al-out');
  s += arrow(270, 347, 252, 347);
  s += box(10, 120, 220, 266, ['Side checks, same maths', '', 'Steady test: rerun with', arr(obj(m.steady).neighbours).join(' and ') + ' nearest, score ±30', '', 'Changes: score +' + arr(m.score_steps).join('/+') + ',', 'rating +' + arr(m.rating_steps).join('/+') + ', a named major;', 'keep if gap rises ≥ ' + gain + ';', 'never hooks, state, GPA', '', 'Kinds: k-medoids, k = ' + (num(kd.k) || 3) + ',', 'admitted cases, seed ' + (num(kd.seed) || ''), '≤ ' + (num(kd.cap) || 300) + ' cases, ' + (num(kd.rounds) || 20) + ' rounds;', 'named from medians only'], 'al-side');
  s += box(10, 400, 740, 90, ['9. Output, all numbers set by code', 'lean + text, d_admitted, d_denied, gap, steady/flips, parts (close or far), not_used, 3 nearest admitted and 3 nearest denied with per-part', 'distances, kinds with the nearest marked, up to 3 changes, up to ' + (num(m.points_cap) || 300) + ' points for the scatter. The reach / target / likely label is untouched.', 'Holds-up check: ' + (num(obj(m.check).n) || 400) + ' past posters, each hidden in turn, counted by lean and real outcome.'], 'al-out');
  s += arrow(385, 386, 385, 398);
  return s + '</svg>';
}
function renderHowBuilt(m) {
  var lib = obj(m.libraries), kd = obj(m.kinds), h = '';
  h += '<h4>How closeness was built</h4>';
  h += '<p><b>The distance.</b> Two people are compared part by part. Each part gives a number from 0 (the same) to 1 (as far as it gets); the parts are combined as a weighted mean, ' +
    'and only the parts both people have count. A student with no test score has no distance at all, so the answer is "can\'t say", not a guess. ' +
    'The distance to a group is the mean distance to its ' + (num(m.neighbours) || 7) + ' nearest members, which is less jumpy than the single nearest and less blurred than the whole group.</p>';
  h += '<h4>Parts and weights</h4>' + renderWeightsTable(m);
  h += '<h4>The algorithm</h4><div class="pic-scroll">' + renderAlgorithmDiagram(m) + '</div>';
  h += '<h4>Libraries</h4><ul class="plain">' +
    '<li><b>Engine (Python, standard library only):</b> ' + esc(arr(lib.engine).map(str).join(', ')) + '. Not used: ' + esc(arr(lib.not_used).map(str).join(', ')) + '.</li>' +
    '<li><b>Screen:</b> ' + esc(arr(lib.screen).map(str).join('; ')) + '.</li>' +
    '<li><b>Kinds:</b> k-medoids written in plain Python: pick ' + (num(kd.k) || 3) + ' seeded starting cases, assign every admitted case to its nearest, move each medoid to the member with the least total distance, repeat up to ' + (num(kd.rounds) || 20) + ' rounds or until nothing moves. A medoid is a real case, so each kind is described by counting its members.</li></ul>';
  h += '<h4>Choices made, and why</h4><ul class="plain">' +
    '<li><b>A distance, not a probability.</b> The pool is people who chose to post; a percentage from it would be wrong twice over. A distance says "like" or "unlike" and nothing more.</li>' +
    '<li><b>Weights are starting values.</b> Score carries the most because it is the one part every case has and the one the labels already use; the rest are split by how often the data has them. Nothing was fitted.</li>' +
    '<li><b>' + (num(m.neighbours) || 7) + ' neighbours, ' + (num(m.needed) || 15) + ' needed.</b> The same "needed" as the cases tab, so "not enough" means the same thing everywhere.</li>' +
    '<li><b>Lean threshold ' + (num(m.lean_gap) || 0.03) + '.</b> Set by printing the gap for the six demo students: about half their colleges land clearly one way, the rest in between, and the direction matched their lists.</li>' +
    '<li><b>Steady test.</b> Copied from the label edge test: an answer that flips with 5 instead of 7 neighbours, or 30 score points, is shown as "on the edge" rather than hidden.</li>' +
    '<li><b>Residency only at public colleges,</b> and listed as not used at private ones, so the counselor sees it was considered.</li>' +
    '<li><b>Kinds named from medians,</b> "High / Mid / Lower score" relative to that college\'s own admitted median (±' + (num(kd.score_band) || 40) + ' points), so the words mean something at MIT and at Arizona State alike; two kinds that would read the same get their median score added.</li>' +
    '<li><b>Changes never touch who the student is.</b> Hooks, home state and GPA are matched on but never varied, and no wording suggests inventing or inflating anything.</li>' +
    '<li><b>Everything is deterministic:</b> fixed seeds, sorted inputs, ties broken by case number. The same student gives the same answer every time, and the holds-up table can be regenerated and compared.</li>' +
    '<li><b>Cut order under the two-hour budget:</b> the lean sentence, nearest cases, changes and rings were built first; the check table, kinds, mind-map leaves and the scatter were the things to drop if time ran out. None had to be.</li></ul>';
  return h;
}
/* ====== end of lifted code ====== */
function hasCloseness(result) { return arr(obj(result).colleges).some(function (c) { return !!obj(c).closeness; }); }
function nearList(cases, emptyText) {
  var cs = arr(cases).map(obj).slice(0, 3);
  if (!cs.length) return '<p class="quiet small">' + esc(emptyText) + '</p>';
  return '<ul class="near">' + cs.map(function (e) {
    var bits = [num(e.sat) !== null ? 'SAT ' + num(e.sat) : (num(e.act) !== null ? 'ACT ' + num(e.act) : ''), majorText(e.major || e.major_group),
      hookText(e.hooks) && hookText(e.hooks) !== 'None' ? hookText(e.hooks) : '', str(e.home_state), num(e.activities_rating) !== null ? 'activities ' + num(e.activities_rating) : ''].filter(Boolean);
    return '<li>' + esc(bits.join(' · ') || 'A past student') + '<span class="working-only quiet small"> ' + esc(str(e.case_id)) + (num(e.distance) !== null ? ', distance ' + f2(num(e.distance)) : '') + '</span></li>';
  }).join('') + '</ul>';
}
function renderResemblePool(pool, cl, which) {
  var q = obj(pool), st = str(q.status), ok = st === 'ok', k = num(obj(cl).neighbours) || 7;
  var h = '<div class="pool rpool pool-' + which + '"><h4>' + (which === 'own' ? 'Your school' : 'Students nationwide') + '</h4><p class="quiet small">' +
    (q.invented === true ? '<span class="tagx">Invented for this demo</span> Not real students.'
      : (which === 'own' ? (q.verified === true ? 'Past students, checked by a counselor.' : 'Not checked by a counselor.') : 'Students who posted their own results online. Not checked.')) + '</p>';
  if (!pool) return h + '<p class="calm">No past students to compare with here.</p></div>';
  if (ok) h += '<p class="reason">' + esc(str(q.text) || leanWord(q.lean) + '.') + '</p>';
  else if (st === 'not_enough') h += '<p class="calm">Too few cases here to compare yet. We would rather tell you that than guess.' + (str(q.text) ? ' <span class="quiet">' + esc(q.text) + '</span>' : '') + '</p>';
  else h += '<p class="calm">' + esc(str(q.text) || 'No past students to compare with here.') + '</p>';
  if (ok && q.steady === false) {
    var flips = arr(q.flips).map(obj).filter(function (f) { return str(f.cause); });
    h += '<p class="quiet small">This one is close to the line' + (flips.length ? ': ' + esc(flips.map(function (f) { return str(f.cause) + ' gives "' + leanWord(f.to).toLowerCase() + '"'; }).join('; ')) : '') + '.</p>';
  }
  if (ok || st === 'not_enough') {
    if (arr(q.parts).length) h += '<p class="label">Close or some way off, part by part</p>' + renderPartBars(q.parts);
    h += '<div class="near-two"><div><p class="label">Nearest who were admitted</p>' + nearList(q.nearest_admitted, 'None to show.') + '</div>' +
      '<div><p class="label">Nearest who were not admitted</p>' + nearList(q.nearest_denied, 'None to show.') + '</div></div>';
    var sc = which === 'national' ? renderScatter(q, obj(cl).student) : '';
    if (sc) h += '<details class="more"><summary>Every case here, as a picture</summary>' + sc +
      '<p class="quiet small">Circle: admitted. Cross: not admitted. Diamond: waitlisted. The star or line is you.</p></details>';
  }
  h += '<div class="working-only working-box">' + (str(q.source) ? '<p class="src">' + esc(q.source) + '</p>' : '') +
    '<p class="small">' + (num(q.n_admitted) || 0) + ' admitted, ' + (num(q.n_denied) || 0) + ' not admitted, ' + (num(q.n_waitlisted) || 0) + ' waitlisted with a score.' +
    (num(q.d_admitted) !== null && num(q.d_denied) !== null ? ' Distance to the ' + k + ' nearest admitted ' + f2(num(q.d_admitted)) + ', to the ' + k + ' nearest not admitted ' + f2(num(q.d_denied)) +
      (num(q.gap) !== null ? ' (gap ' + f2(num(q.gap)) + ')' : '') + '. 0 is the same person; 1 is as far as it gets.' : '') +
    (ok ? (q.steady === true ? ' Steady: the same answer with 5 or 10 nearest cases and with the score 30 points either way.' : '') : '') + '</p>' +
    (arr(q.not_used).length ? '<p class="small quiet">Not used: ' + esc(arr(q.not_used).map(str).join('; ')) + '.</p>' : '') + '</div>';
  return h + '</div>';
}
/* "Who you resemble": leads the tab. Both pools kept apart; then kinds; then what would bring you closer; the caveat always. */
function renderResemble(c) {
  c = obj(c);
  if (!c.closeness) return '';
  var cl = obj(c.closeness), n = obj(cl.national), o = obj(cl.own), h = '<div class="resemble">';
  h += '<h3 class="section">Who you resemble</h3>' + (c.closeness_stale === true ? '<p class="quiet small stale">From the last full run.</p>' : '');
  h += '<div class="pools">' + renderResemblePool(cl.own, cl, 'own') + renderResemblePool(cl.national, cl, 'national') + '</div>';
  var kinds = arr(n.kinds).map(obj).concat(arr(o.kinds).map(obj)).filter(function (q) { return str(q.name); }), shownKinds = kindsShown(n);
  if (kinds.length && shownKinds === 'none') {
    h += '<p class="label">Kinds of student admitted here</p><p class="calm">' + esc(str(obj(n.kinds_check).text) || 'No clear kinds at this college.') +
      ' <span class="quiet small">The computer-made kinds did not pass their check, so they are not named. See the Clusters picture for rule-based clusters.</span></p>';
  } else if (kinds.length) {
    h += '<p class="label">Kinds of student admitted here' + (shownKinds === 'loose' ? ' <span class="quiet">(loose grouping)</span>' : '') + '</p><ul class="kinds">' + kinds.map(function (q) {
      return '<li' + (q.nearest === true ? ' class="nearest"' : '') + '>' + esc(q.name) + ' <span class="quiet">(' + (num(q.size) || 0) + ' ' + plural(num(q.size) || 0, 'student', 'students') + ')</span>' +
        (q.nearest === true ? ' <span class="tagn">closest to you</span>' : '') +
        '<span class="working-only quiet small"> ' + esc(str(q.kind_id)) + (num(q.distance) !== null ? ', distance ' + f2(num(q.distance)) : '') + '</span></li>';
    }).join('') + '</ul>';
  }
  var ch = [];
  [[n, 'Students nationwide'], [o, 'Your school']].forEach(function (pp) {
    arr(pp[0].changes).map(obj).filter(function (q) { return str(q.change); }).forEach(function (q) { ch.push({q: q, pool: pp[1]}); });
  });
  h += '<p class="label">What would bring you closer</p>';
  if (ch.length) {
    h += '<ol class="changes">' + ch.slice(0, 4).map(function (x) {
      var q = x.q;
      return '<li><b>' + esc(q.change) + '.</b> ' + (str(q.lean_after) ? 'Then: ' + esc(leanWord(q.lean_after).toLowerCase()) + '. ' : '') + '<span class="quiet small">Compared with: ' + esc(x.pool.toLowerCase()) + '.</span>' +
        '<span class="working-only quiet small"> Gap ' + f2(num(q.gap_before) || 0) + ' to ' + f2(num(q.gap_after) || 0) + (arr(q.because).length ? '; nearest admitted would be ' + esc(arr(q.because).map(str).join(', ')) : '') + '.</span></li>';
    }).join('') + '</ol>';
  } else h += '<p class="calm">' + esc(str(n.changes_note) || str(o.changes_note) || 'Nothing we can measure here would move this.') + '</p>';
  h += '<p class="quiet small">Only the score, the activities rating and a named major are ever varied. Nothing about who you are.</p>';
  /* optional text comparison (only with a model key): its status, and the cases whose masked text came nearest */
  var sem = obj(cl.semantic), matches = arr(cl.essay_retrieval).map(obj).filter(function (q) { return str(q.case_id); });
  if (str(sem.status) && str(sem.status) !== 'off') {
    h += '<p class="working-only quiet small">Text comparison: ' + esc(sem.status) + (str(sem.note) ? '. ' + esc(sem.note) : '') + '</p>';
    if (matches.length) h += '<p class="label">Nearest in essay and activity text</p><ol class="plain small">' + matches.map(function (q) {
      return '<li>' + esc(q.case_id) + ', ' + (str(q.text_kind) === 'full_essay' ? 'full essay' : 'theme summary') + (num(q.distance) !== null ? ', text distance ' + f2(num(q.distance)) + ' (lower is closer)' : '') + '</li>';
    }).join('') + '</ol>';
  }
  h += '<p class="caveat-line">' + esc(str(cl.caveat) || 'Closeness is a distance to past cases. It is not a forecast.') + '</p>';
  return h + '</div>';
}
/* ---------- data sources: each one, what was taken from it, what was left out ---------- */
var DATA_SOURCES = [
  {name: 'College Scorecard, US Department of Education', kind: 'Real', files: 'data/colleges/',
   what: 'The federal institution file: 1,339 colleges with admit rate, score bands, sticker cost and what families paid after grants.',
   used: ['admit rate and 25th / 75th percentile SAT and ACT: the reach / target / likely label and the "what if" slider',
          'state and public / private: residency in closeness, in-state cost lines, suggestions near home',
          'sticker cost, tuition, and the federal average paid by income band: the cost line (one family\'s price can differ)',
          'graduation rate and size: ordering the suggested colleges'],
   left: ['nothing is modelled from it beyond those fields; no ranking or prestige score is derived']},
  {name: 'SAT / ACT concordance', kind: 'Real', files: 'data/colleges/sat_act_concordance.csv',
   what: 'The published concordance table.', used: ['converting an ACT composite to the SAT scale when a student or case has only an ACT'], left: []},
  {name: 'Five published rulebooks', kind: 'Real, transcribed', files: 'data/colleges/rulebooks.json',
   what: 'How five public sites turn a score into reach / target / likely.',
   used: ['run beside our own rule on the same score; "publishers disagree" when any of them lands elsewhere'], left: ['they never set our label']},
  {name: 'Common Data Set, through collegedata.fyi', kind: 'Real', files: 'data/cds/',
   what: 'What 24 colleges say they weigh (section C7) and related fields, for 2025-26.',
   used: ['"What the college says" statements, each with its field, year and source link', 'what the college looks for, beside what is in the profile', 'common beliefs checked against the form',
          'claim sentences are checked in code: every number and name must come from the row; nothing from the forbidden-phrases list'],
   left: ['fields that failed the file\'s own sanity flags are skipped', 'colleges without a row say so']},
  {name: 'Knowledge base notes', kind: 'Real, written by the builders from the sources above', files: 'data/kb/',
   what: 'Plain-language notes on admission factors, how labels are set, the UC and Texas systems, and 24 college pages.',
   used: ['uploaded to PRISM\'s Knowledge Base; each college statement is confirmed against it and a planted false one comes back "not confirmed"'], left: ['never shown as text on the screen; only the confirmed / not confirmed mark']},
  {name: 'Public case pool: r/collegeresults posts', kind: 'Real, self-reported, not verified', files: 'data/cases/',
   what: 'About 2,250 applicants and their results at 58 colleges, as compiled in the GitHub repository shreybirmiwal/college-predictor. No names. That repository states no licence; the files are here for the demo and can be removed.',
   used: ['SAT, ACT, major, hooks, home state: "Who you resemble" and the example cases', 'self-rated activities and awards (0 to 10): the activities part of closeness and the scatter',
          'outcome at each college: admitted / not admitted / waitlisted counts, the two groups closeness compares, the kinds, and the holds-up check'],
   left: ['gender, race, income, school type, class rank and the essay / recommendation / interview self-rating are read into memory and never used anywhere',
          'a second row for the same person at one college is merged (an offer held counts as admitted; a waitlist is superseded)',
          'the pool over-represents the admitted and skews to high scorers and computer science; the official admit rate sits beside every count']},
  {name: "The school's own finished cases", kind: 'Invented, stamped SYNTHETIC', files: 'data/synthetic/SYNTHETIC_school_cases.csv',
   what: 'Generated by a seeded script to stand in for a counselor\'s verified records, and labelled as invented on screen.',
   used: ['SAT, ACT, GPA, major group, hooks, home state, activities note, essay theme, outcome: the "Your school" pool, kept apart from the public one', 'GPA: the only place GPA enters closeness'],
   left: ['any field that looks like a name, email, phone or date of birth is refused when a case is added']},
  {name: 'Demo students and essays', kind: 'Invented, stamped SYNTHETIC', files: 'data/synthetic/',
   what: 'Invented students built to exercise the screen: strong scores, mid scores, ACT only, no score, a hidden instruction, personal details.',
   used: ['the student cards on the opening page; the saved runs in the shared preview'], left: ['no real student appears anywhere in this repository']},
  {name: 'Models, through the Nicrron gateway', kind: 'Service, only with a key', files: 'engine/reader.py, engine/nicrron.py, engine/semantic.py',
   what: 'One fast model reads the masked essay; a second model from a different maker tags the intended major independently. Optionally, a text-embedding model compares masked essay and activity text with past cases.',
   used: ['essay notes with word-for-word quotes (code drops any note whose quote is not in the essay)', 'a major group tag, used only when the two models agree and the student gave no major',
          'with a key: an essay and activity-text part in closeness, from masked text only'],
   left: ['no model sets a label, a count or a number', 'the essay is masked first; an essay with instructions aimed at an AI is stopped before any model sees it', 'vectors stay in memory and are never written to disk or sent to the browser']},
  {name: 'PRISM by Block Convey', kind: 'Service, only with a key', files: 'engine/prism.py',
   what: 'Guardrail, knowledge base and run record.', used: ['second guard on the essay', 'confirming college statements', 'recording each run and its five steps'], left: ['never delays or changes a label; with no key every call returns "off" at once']}
];
function renderDataSources(result) {
  var pools = obj(obj(result).pools), nat = obj(pools.national), own = obj(pools.own);
  var h = '<h4>Data sources, and what was taken from each</h4>';
  if (num(nat.cases) !== null) {
    h += '<p class="small">Counts in this run: ' + commas(num(nat.cases)) + ' people' + (num(nat.decisions) !== null ? ' and ' + commas(num(nat.decisions)) + ' decisions' : '') +
      (num(nat.colleges) !== null ? ' at ' + num(nat.colleges) + ' colleges' : '') + ' in the public pool' + (num(own.cases) !== null ? '; ' + num(own.cases) + ' invented cases in the school\'s own pool' : '') + '.</p>';
  }
  h += '<ul class="srcs">' + DATA_SOURCES.map(function (s) {
    return '<li class="src-card"><p class="src-name">' + esc(s.name) + ' <span class="tagn' + (/Invented/.test(s.kind) ? ' tagn-off' : '') + '">' + esc(s.kind) + '</span></p>' +
      '<p class="src-what">' + esc(s.what) + '</p><p class="src-files"><span class="quiet">Files:</span> ' + esc(s.files) + '</p>' +
      '<p class="src-h">Used for</p><ul class="plain small">' + arr(s.used).map(function (t) { return '<li>' + esc(t) + '</li>'; }).join('') + '</ul>' +
      (arr(s.left).length ? '<p class="src-h">Left out, or kept in check</p><ul class="plain small">' + arr(s.left).map(function (t) { return '<li>' + esc(t) + '</li>'; }).join('') + '</ul>' : '') + '</li>';
  }).join('') + '</ul>';
  return h;
}
/* ---------- the feature list, from docs/features.json ---------- */
var FEATURE_STATUS = {'works': 'Works', 'works with a key': 'Works with a key', 'thin': 'Thin', 'not done': 'Not done'};
function renderFeatures(features) {
  var fs = arr(features).map(obj).filter(function (f) { return str(f.name); });
  if (!fs.length) return '';
  var done = fs.filter(function (f) { return str(f.status).indexOf('works') === 0; }).length;
  var h = '<p class="small quiet">' + done + ' of ' + fs.length + ' work today. The same list is in the README; both come from docs/features.json.</p>';
  h += '<ul class="feats">' + fs.map(function (f) {
    var st = str(f.status), cls = st.indexOf('works') === 0 ? 'f-ok' : (st === 'not done' ? 'f-no' : 'f-thin');
    return '<li class="feat ' + cls + '"><p class="feat-name">' + esc(f.name) + (str(f.when) === 'afternoon' ? ' <span class="tagn">new today</span>' : '') +
      ' <span class="feat-st">' + esc(FEATURE_STATUS[st] || cap(st)) + '</span></p><p class="feat-what">' + esc(f.what) + '</p>' +
      (str(f.where) ? '<p class="feat-where"><span class="quiet">Where:</span> ' + esc(f.where) + '</p>' : '') + '</li>';
  }).join('') + '</ul>';
  return h;
}
/* ---------- about: what this is, a tour with live buttons, the rules it keeps ---------- */
function renderAboutPanel(result, mode) {
  var r = obj(result), cs = arr(r.colleges).map(obj), has = cs.length > 0, can = hasCloseness(r);
  var first = cs.filter(function (c) { return closenessOf(c) && closenessOf(c).status === 'ok'; })[0];
  function tourBtn(act, text, extra) { return '<button type="button" class="btn small" data-act="' + act + '"' + (extra || '') + '>' + esc(text) + '</button>'; }
  var h = panelHead('About this screen') + '<section class="rc-sec about">';
  h += '<p class="reason">A meeting tool for a college counselor and a family. Load one student and their list; the screen labels each college from published numbers, shows what happened to similar finished cases, and says plainly when it does not know. <b>It never gives a personal chance of admission.</b></p>';
  h += '<p class="label">A two-minute tour</p><ol class="tour">';
  h += '<li><b>Who you are.</b> Chapter 1: what stands out in the student, from their own activities and essay. Nothing here is scored.</li>';
  h += '<li><b>Where you stand.</b> Chapter 2: the student is a line; each college is a bar showing where its middle half scored, with a reach, target or likely label set by a written rule. ' +
    'The same list can be seen as <b>rings</b> (nearer the centre means more like the people admitted there) or as a <b>map</b> (a branch per label, and under each college its nearest kind of admitted student). ' +
    (has && can ? tourBtn('tour-pic', 'Show the rings', ' data-view="rings"') + ' ' + tourBtn('tour-pic', 'Show the map', ' data-view="map"') + ' ' + tourBtn('tour-pic', 'Back to the trail', ' data-view="trail"') : (has ? '<span class="quiet">Rings and the map need a full run.</span>' : '<span class="quiet">Choose a student first.</span>')) + '</li>';
  h += '<li><b>Tap a college.</b> How we got this (the rule and its inputs); who you resemble (closer to the people admitted or the people not admitted, part by part, with the nearest cases of each, two pools kept apart); what could change it; and what the college says in its own form. ' +
    (first ? tourBtn('tour-resemble', 'Open "' + shortName(first.name) + '": who you resemble', ' data-i="' + cs.indexOf(first) + '"') : '') + '</li>';
  h += '<li><b>What is in your hands.</b> Chapter 3: colleges that would balance the list, the "what if the score were…" slider, and what each college looks for beside what is in the profile.</li>';
  h += '<li><b>Your plan.</b> Chapter 4: five things to do this month, a sheet to print, and a status for each college that becomes a finished case for next year.</li>';
  h += '<li><b>Check the work.</b> The "Show the working" switch reveals every source, rule and step. "How we worked this out" has the method, the weights, a diagram, every data source and the full feature list. ' +
    tourBtn('tool-how', 'Open "How we worked this out"') + ' ' + tourBtn('toggle-working', 'Show the working') + '</li></ol>';
  h += '<p class="label">What closeness is, and is not</p><ul class="plain">' +
    '<li>For each college: does this student look more like the people admitted there, or the people not admitted? Measured as a <b>distance</b> over score, activities rating, major group, hooks and residency (and, only with a model key, masked essay and activity text).</li>' +
    '<li>It never changes a label and never becomes a percentage. "Too few cases" and "can\'t say" are normal answers.</li>' +
    '<li>"What would bring you closer" only ever tries a higher score, deeper involvement in the activities already listed, or another major the student named. Never hooks, home state or GPA.</li>' +
    '<li>Checked on 400 past posters with each one hidden in turn; the counts are under "How we worked this out", with the caveat that people who post are admitted far more often than applicants.</li></ul>';
  h += '<p class="label">What is real and what is invented</p><ul class="plain">' +
    '<li><b>Real:</b> 1,339 colleges\' admit rates, score bands and costs (US Department of Education); what 24 colleges say they weigh (their own Common Data Set); a public pool of self-reported results from posts, with no names.</li>' +
    '<li><b>Invented, stamped SYNTHETIC:</b> the demo students and essays, and the school\'s own cases.</li></ul>';
  h += '<p class="quiet small">Built on 10 October 2026 at a one-day hackathon. Python standard library and plain HTML, CSS and JavaScript; no build step. Source and tests sit beside this page.</p>';
  return h + '</section>';
}
function renderHowWorked(result) {
  var r = obj(result);
  return panelHead('How we worked this out') + '<section class="rc-sec howbuilt">' +
    '<p class="reason">Two things are worked out for each college, both by code, with no model deciding anything.</p>' +
    '<ul class="plain"><li><b>The label</b> (reach, target, likely) comes from your score against the college\'s published range and its admit rate.</li>' +
    '<li><b>Who you resemble</b> comes from how close you are to past students who were admitted and who were not. It is a resemblance, not a forecast.</li></ul>' +
    (renderClosenessCheck(r.closeness_check) || '') + renderHowBuilt(methodOf(r)) + renderDataSources(r) +
    '<h4>Everything it does, feature by feature</h4>' + renderFeatures(FEATURES) + '</section>';
}

/* ---------- keep track, and pay it forward ---------- */
var TRACK_STEPS = [['considering', 'Considering'], ['applying', 'Applying'], ['submitted', 'Submitted'], ['result', 'Result']];
var TRACK_OUT = [['admitted', 'Admitted'], ['denied', 'Not admitted'], ['waitlisted', 'Waitlisted']];
/* state: {college name: {status, outcome, asking}}; falls back to each college's own tracker */
function renderTracker(result, canPost, state, message) {
  var cs = arr(obj(result).colleges).map(obj).filter(function (c) { return str(c.name) && groupOf(obj(c.label).state) !== 'outside_data'; }), st = obj(state), msg = obj(message);
  if (!cs.length) return '';
  var h = '<div class="card tracker"><h3 class="section">Keep track, and pay it forward</h3>' +
    '<p class="quiet">When results come in, they go back into your school\'s cases, with no names.</p>';
  if (canPost === false) h += '<p class="quiet small">Shared preview: saved runs for six invented students. Run it on a laptop to edit.</p>';
  h += '<ul class="track-rows">' + cs.map(function (c) {
    var t = obj(st[str(c.name)] || c.tracker), status = str(t.status) || 'considering', outcome = str(t.outcome), off = canPost === false ? ' disabled' : '';
    var row = '<li><span class="track-name">' + esc(shortName(c.name)) + '</span><span class="track-steps" role="group" aria-label="Where this application is">' +
      TRACK_STEPS.map(function (s) {
        return '<button type="button" class="step" data-act="track" data-name="' + esc(c.name) + '" data-status="' + s[0] + '" aria-pressed="' + (s[0] === status ? 'true' : 'false') + '"' + off + '>' +
          s[1] + (s[0] === 'result' && status === 'result' && outcome ? ': ' + esc((TRACK_OUT.filter(function (o) { return o[0] === outcome; })[0] || ['', outcome])[1]).toLowerCase() : '') + '</button>';
      }).join('') + '</span>';
    if (t.asking === true && canPost !== false) {
      row += '<span class="track-ask">Which result? ' + TRACK_OUT.map(function (o) {
        return '<button type="button" class="btn small" data-act="track-outcome" data-name="' + esc(c.name) + '" data-outcome="' + o[0] + '">' + o[1] + '</button>';
      }).join('') + '</span>';
    }
    return row + '</li>';
  }).join('') + '</ul>';
  h += '<div id="tracker-msg" class="track-msg" role="status" aria-live="polite">' + (str(msg.note) ? '<p>' + esc(msg.note) + '</p>' : '') +
    (msg.case_added === true ? '<p class="calm paid"><b>This result is now one of your school\'s finished cases.</b> Next year\'s students will see it. ' +
      '<button type="button" class="btn small" data-act="build">Build the list again</button></p>' : '') + '</div>';
  if (canPost !== false) h += '<p><button type="button" class="linkbtn small" data-act="track-reset">Clear the demo results</button></p>';
  return h + '</div>';
}

/* ---------- pressing a college: the drill-in ---------- */
function rangeInfo(c) {
  c = obj(c);
  var L = obj(c.label), inp = obj(L.inputs), kind = str(L.score_kind);
  var useAct = /^act$/i.test(kind.trim());
  var lo = num(useAct ? (inp.act25 !== undefined ? inp.act25 : c.act25) : (inp.sat25 !== undefined ? inp.sat25 : c.sat25));
  var hi = num(useAct ? (inp.act75 !== undefined ? inp.act75 : c.act75) : (inp.sat75 !== undefined ? inp.sat75 : c.sat75));
  return {lo: lo, hi: hi, min: useAct ? 10 : 800, max: useAct ? 36 : 1600, score: num(L.score_used),
          kind: kind || (useAct ? 'ACT' : 'SAT'), test: useAct ? 'ACT' : 'SAT'};
}
function rangeBar(c) {
  var r = rangeInfo(c), g = groupOf(obj(obj(c).label).state);
  if (r.lo === null || r.hi === null) return '<span class="range none"><span class="range-cap">This college publishes no score range.</span></span>';
  function pc(v) { return Math.max(0, Math.min(100, (v - r.min) / (r.max - r.min) * 100)); }
  var where = '';
  if (r.score !== null) where = r.score < r.lo ? 'below the range' : (r.score >= r.hi ? 'at or above the top of the range' : 'inside the range');
  var aria = 'This college\'s middle ' + r.test + ' range is ' + r.lo + ' to ' + r.hi + '. ' + (r.score !== null ? 'Your score, ' + r.score + ', is ' + where + '.' : 'No score to mark.');
  var left = pc(r.lo), width = Math.max(1.5, pc(r.hi) - pc(r.lo));
  return '<span class="range p-' + g + '" role="img" aria-label="' + esc(aria) + '">' +
    '<span class="track"><span class="band" style="left:' + left.toFixed(1) + '%;width:' + width.toFixed(1) + '%"></span>' +
    (r.score !== null ? '<span class="me" style="left:' + pc(r.score).toFixed(1) + '%"></span>' : '') + '</span>' +
    '<span class="range-cap">Middle half of students: <b>' + r.lo + ' to ' + r.hi + '</b>' +
    (r.score !== null ? ' · you: <b>' + r.score + '</b>, ' + esc(where) : '') + (/converted/i.test(r.kind) ? ' (ACT converted to SAT)' : '') + '</span></span>';
}
function renderWhyWorking(c) {
  c = obj(c);
  var L = obj(c.label), g = groupOf(L.state), inp = obj(L.inputs), h = '<div class="working-only working-box">';
  var NAMES = {sat25: "College's 25th percentile SAT", sat75: "College's 75th percentile SAT",
               act25: "College's 25th percentile ACT", act75: "College's 75th percentile ACT", admit_rate: 'Official admit rate'};
  var rows = [['Rule', esc(str(L.rule_id) || 'not recorded')],
    ['Score used', num(L.score_used) !== null ? esc(num(L.score_used) + (str(L.score_kind) ? ' (' + str(L.score_kind) + ')' : '')) : 'No score to compare']];
  Object.keys(inp).forEach(function (k) {
    var v = inp[k];
    rows.push([esc(NAMES[k] || cap(k.replace(/_/g, ' '))), k === 'admit_rate' ? esc(rateFull(v)) : (v === null || v === undefined || typeof v === 'object' ? 'not published' : esc(v))]);
  });
  h += '<h4>The numbers used</h4><table class="kv"><tbody>' + rows.map(function (r) { return '<tr><th scope="row">' + r[0] + '</th><td>' + r[1] + '</td></tr>'; }).join('') + '</tbody></table>';
  if (str(c.source)) h += '<p class="src">Numbers from: ' + esc(c.source) + '</p>';
  var nu = arr(L.not_used).map(str).filter(Boolean);
  h += '<h4>What was not used</h4>' + (nu.length ? '<p>' + nu.map(function (x) { return '<span class="unused">' + esc(x) + '</span>'; }).join('') + '<span class="quiet"> None of these changed the label.</span></p>' : '<p class="quiet">Nothing was listed.</p>');
  var cv = arr(L.caveats).map(str).concat(arr(c.flags).map(function (f) { return typeof f === 'string' ? f : str(obj(f).text); })).filter(Boolean);
  if (cv.length) h += '<h4>Caveats</h4><ul class="plain">' + cv.map(function (x) { return '<li>' + esc(x) + '</li>'; }).join('') + '</ul>';
  var fl = arr(L.flips).map(obj);
  h += '<h4>What would change the label</h4>';
  if (fl.length) h += '<ul class="rows">' + fl.map(function (f) { return '<li><span>' + esc(cap(f.cause)) + '</span><span class="becomes">becomes ' + pillFor(f.to) + '</span></li>'; }).join('') + '</ul>';
  else if (isEveryone(L)) h += '<p class="quiet">Nothing in the profile changes it. The label comes from the college\'s admit rate, not from the score.</p>';
  else if (g === 'cant_say') h += '<p class="quiet">Not tested, because there is no label to test.</p>';
  else h += '<p class="quiet">Nothing small: a score 30 points lower or higher, or an admit rate 5 points lower, gives the same label.</p>';
  var pubs = arr(L.publishers).map(obj);
  h += '<h4>What each publisher would call it' + (L.publishers_disagree === true ? ' <span class="tagx">they differ</span>' : '') + '</h4>';
  if (pubs.length) {
    h += '<ul class="rows">' + pubs.map(function (p) {
      var same = p.label && groupOf(p.label) === g;
      return '<li><span class="pub-name">' + esc(p.name) + '</span>' + (p.label ? pillFor(p.label) : '<span class="quiet">could not label</span>') +
        (p.label ? '<span class="becomes ' + (same ? '' : 'differs') + '">' + (same ? 'same as ours' : 'differs from ours') + '</span>' : '') + '</li>';
    }).join('') + '</ul>';
  } else h += '<p class="quiet">No publisher\'s rulebook could label this one.</p>';
  return h + '</div>';
}
function renderWhyTab(c) {
  c = obj(c);
  var L = obj(c.label), g = groupOf(L.state), edge = edgeLever(c);
  var h = (g === 'outside_data' ? '' : '<div class="tab-pic">' + rangeBar(c) + '</div>') +
    '<p class="reason">' + esc(str(L.rule_text) || 'No reason was recorded for this label.') + '</p>';
  if (num(c.admit_rate) !== null) h += '<p class="quiet">' + esc(cap(inHundred(c.admit_rate))) + ' applicants get in' + (costLine(c.cost_year) ? ', and it costs ' + esc(costLine(c.cost_year)) : '') + '.</p>';
  if (edge) h += '<p class="close-one">' + waypoint(false) + 'This one is close: ' + esc(edge) + '.</p>';
  if (g !== 'outside_data') h += renderWhyWorking(c);
  return h;
}
function outcomeKind(o) {
  var s = str(o).toLowerCase();
  return s === 'admitted' || s === 'denied' || s === 'waitlisted' ? s : 'other';
}
var OUTCOME_WORD = {admitted: 'Admitted', denied: 'Not admitted', waitlisted: 'Waitlisted', other: 'Not recorded'};
function outcomeTag(o) { return '<span class="outcome"><i class="cd cd-' + outcomeKind(o) + '" aria-hidden="true"></i>' + OUTCOME_WORD[outcomeKind(o)] + '</span>'; }
function dotGrid(a, d, w) {
  var h = '', left = 150;
  [[a, 'admitted'], [d, 'denied'], [w, 'waitlisted']].forEach(function (q) {
    var k = Math.max(0, Math.min(num(q[0]) || 0, left));
    left -= k;
    for (var i = 0; i < k; i++) h += '<i class="cd cd-' + q[1] + '"></i>';
  });
  return '<div class="grid-dots" aria-hidden="true">' + h + '</div>';
}
function examplesTable(examples) {
  var ex = arr(examples).map(obj);
  if (!ex.length) return '<p class="quiet">No example cases to list.</p>';
  var cols = [
    ['Case', function (e) { return esc(e.case_id) + (e.shared ? ' <span class="tagx">shared</span>' : ''); }, function (e) { return str(e.case_id); }],
    ['Score', function (e) { return num(e.sat) !== null ? 'SAT ' + num(e.sat) : (num(e.act) !== null ? 'ACT ' + num(e.act) : 'none sent'); }, function () { return 'x'; }],
    ['Major', function (e) { return esc(majorText(e.major || e.major_group)); }, function (e) { return str(e.major || e.major_group); }],
    ['Background', function (e) { return esc(hookText(e.hooks)); }, function (e) { return hookText(e.hooks); }],
    ['Home', function (e) { return esc(e.home_state); }, function (e) { return str(e.home_state); }],
    ['Activities', function (e) { return str(e.activities_note) ? esc(e.activities_note) : (num(e.activities_rating) !== null ? 'rated ' + num(e.activities_rating) : ''); },
      function (e) { return str(e.activities_note) || (num(e.activities_rating) !== null ? 'x' : ''); }],
    ['Essay theme', function (e) { return esc(e.essay_theme); }, function (e) { return str(e.essay_theme); }],
    ['Year', function (e) { return esc(e.cycle_year); }, function (e) { return str(e.cycle_year); }],
    ['Result', function (e) { return outcomeTag(e.outcome); }, function () { return 'x'; }]
  ].filter(function (col) { return ex.some(function (e) { return col[2](e) !== ''; }); });
  return '<div class="table-wrap"><table class="cases-table"><thead><tr>' + cols.map(function (col) { return '<th scope="col">' + col[0] + '</th>'; }).join('') + '</tr></thead><tbody>' +
    ex.map(function (e) { return '<tr>' + cols.map(function (col) { return '<td>' + col[1](e) + '</td>'; }).join('') + '</tr>'; }).join('') + '</tbody></table></div>';
}
function renderPool(pool, cases, which) {
  var cs = obj(cases), p = obj(pool), need = num(cs.needed) || 15, n = num(p.n) || 0;
  var a = num(p.admitted) || 0, d = num(p.denied) || 0, w = num(p.waitlisted) || 0;
  var h = '<div class="pool pool-' + which + '"><h4>' + (which === 'own' ? 'Your school' : 'Students nationwide') + '</h4>' +
    '<p class="quiet small">' + (which === 'own'
      ? (p.invented === true ? '<span class="tagx">Invented for this demo</span> Not real students.' : (p.verified === true ? 'Past students, checked by a counselor.' : 'Not checked by a counselor.'))
      : (p.verified === true ? 'Checked results.' : 'Students who posted their own results online. Not checked.')) + '</p>';
  if (!pool || p.status === 'none' || n === 0) {
    h += '<p class="big-n zero">0</p><p class="calm">No past students with a known result here yet.</p>';
  } else {
    h += '<p class="big-n">' + n + '<span> ' + plural(n, 'student', 'students') + ' with similar scores</span></p>' + dotGrid(a, d, w) +
      '<p class="out-line"><span><i class="cd cd-admitted" aria-hidden="true"></i><b>' + a + '</b> admitted</span>' +
      '<span><i class="cd cd-denied" aria-hidden="true"></i><b>' + d + '</b> not admitted</span>' +
      '<span><i class="cd cd-waitlisted" aria-hidden="true"></i><b>' + w + '</b> waitlisted</span></p>';
    if (p.status === 'not_enough') h += '<p class="calm">Too few cases here to say anything yet. We would rather tell you that than guess. <span class="quiet">(' + n + ' of the ' + need + ' we look for.)</span></p>';
  }
  if (which === 'national' && str(p.note)) h += '<p class="beside">' + esc(p.note) + '</p>';
  if (which === 'national') {
    h += '<p class="beside">Across all applicants, ' + (num(cs.official_admit_rate) !== null ? '<b>' + esc(inHundred(cs.official_admit_rate)) + '</b> get in.' : 'the admit rate is not published.') +
      ' People who post their results are admitted more often than applicants overall' +
      (num(cs.overcount) !== null ? '<span class="working-only"> (about ' + esc(f1(num(cs.overcount))) + ' times as often at this college; official rate ' + esc(rateFull(cs.official_admit_rate)) + ')</span>' : '') + '.</p>';
  }
  if (pool) {
    var m = arr(p.matched_on).map(str).filter(Boolean), rx = arr(p.relaxed).map(str).filter(Boolean);
    h += '<div class="working-only working-box">' + (str(p.source) ? '<p class="src">' + esc(p.source) + '</p>' : '') +
      '<dl class="match"><dt>Matched on</dt><dd>' + (m.length ? esc(m.join('; ')) : 'nothing recorded') + '</dd>' +
      '<dt>Relaxed to find more</dt><dd>' + (rx.length ? esc(rx.join('; ')) : 'nothing') + '</dd></dl>' +
      (n > 0 ? examplesTable(p.examples) : '') + (which === 'national' && str(cs.caveat) ? '<p class="quiet small">' + esc(cs.caveat) + '</p>' : '') + '</div>';
  }
  return h + '</div>';
}
function renderBaselineResults(result) {
  var r = obj(result), matches = arr(r.matches);
  if (r.status === 'blocked') return '<p class="calm">This draft contains instructions aimed at an AI. Revise those passages before searching.</p>';
  if (r.status === 'empty') return '<p class="quiet">Paste an essay to find similar references.</p>';
  if (r.status === 'no_baseline') return '<p class="quiet">There are no reference essays for this essay type yet.</p>';
  if (!matches.length) return '<p class="quiet">No similar references found for this draft.</p>';
  var h = '<p class="quiet small">Compared with ' + esc(r.bank_size) + ' reference essays using ' +
    (r.method === 'embedding' ? 'semantic embeddings' : 'local text similarity') + '.</p>';
  if (r.method === 'local_text') h += '<p class="quiet small">Local comparison uses shared words; it may miss essays that express similar ideas differently.</p>';
  h += '<ol class="baseline-list">' + matches.map(function (m) {
    var school = str(m.school), program = str(m.program);
    var card = '<li class="baseline-match"><h4>' + esc(m.title) + '</h4>';
    card += '<p class="baseline-university"><b>University:</b> ' +
      (school.trim() && school.trim().toLowerCase() !== 'unknown' ? esc(school) :
        (m.synthetic ? 'Not associated with a university (original sample)' : 'Not provided by the source')) + '</p>';
    if (program.trim() && program.trim().toLowerCase() !== 'unknown') card += '<p><b>Program:</b> ' + esc(program) + '</p>';
    if (m.synthetic) card += '<p class="quiet small">Original sample · no admission outcome</p>';
    card += '<p><b>Content similarity: ' + esc(Math.round(num(m.similarity) * 100)) + '/100</b><span class="quiet small"> · not an essay grade</span></p>';
    if (arr(m.shared_terms).length) card += '<p class="quiet small">Shared words: ' + esc(arr(m.shared_terms).join(', ')) + '</p>';
    card += '<blockquote>' + esc(m.excerpt) + '</blockquote><details class="more"><summary>Read the reference essay</summary><div class="baseline-full">' + esc(m.text) + '</div></details>';
    // Only web links can be rendered, including when a saved response is loaded.
    function link(url, label) { return /^https?:\/\//i.test(str(url)) ? '<a href="' + esc(url) + '" target="_blank" rel="noopener noreferrer">' + label + '</a>' : ''; }
    var links = [link(m.source_url, 'OpenEssays source'), link(m.original_url, 'Original source'), link(m.license_url, 'License')].filter(Boolean);
    if (links.length) card += '<p class="baseline-links">' + links.join(' · ') + '</p>';
    if (str(m.attribution)) card += '<p class="quiet small">' + esc(m.attribution) + '</p>';
    if (!m.synthetic && str(m.license)) card += '<p class="quiet small">' + esc(m.license) + ' · text masked for privacy</p>';
    return card + '</li>';
  }).join('') + '</ol>';
  return h;
}

function renderHolistic(c) {
  var cl = obj(c.closeness);
  if (!c.closeness) return '';
  var names = {score: 'Test score', activities: 'Activities rating', major: 'Major', hooks: 'Hooks',
    residency: 'Residency', gpa: 'GPA', essay: 'Essay content', activity_text: 'Activity descriptions'};
  var h = '<h3>Whole profile comparison</h3><p class="quiet">' + esc(cl.caveat) + '</p>';
  ['own', 'national'].forEach(function (key) {
    var p = obj(cl[key]);
    h += '<h4>' + (key === 'own' ? 'Your school' : 'National') + '</h4><p>' + esc(p.text) + '</p>';
    if (arr(p.parts).length) {
      h += '<ul>' + arr(p.parts).map(function (part) {
        return '<li>' + esc(names[part.part] || part.part) + ': ' + esc(part.text) + '</li>';
      }).join('') + '</ul>';
      h += '<p class="quiet small">Not compared: ' + esc(arr(p.not_used).join(', ')) + '.</p>';
      h += '<details class="more"><summary>Nearest admitted and denied cases</summary><h4>Admitted</h4>' +
        examplesTable(p.nearest_admitted) + '<h4>Denied</h4>' + examplesTable(p.nearest_denied) + '</details>';
    }
  });
  var matches = arr(cl.essay_retrieval), report = obj(cl.semantic);
  var embeddingFailed = report.status === 'unavailable' || report.status === 'partial';
  if (!embeddingFailed) h += '<p class="quiet small">Essay comparison: ' + esc(report.status) +
    (str(report.note) ? '. ' + esc(report.note) : '') + '</p>';
  h += '<h4>Similar essay content</h4>';
  if (matches.length) h += '<ol>' + matches.map(function (r) {
    return '<li>' + esc(r.case_id) + ' — ' + (r.text_kind === 'full_essay' ? 'full essay' : 'theme summary') +
      ', content distance ' + esc(r.distance) + ' (lower is closer)</li>';
  }).join('') + '</ol>';
  else if (!embeddingFailed) {
    var reason;
    if (report.status === 'off') reason = 'Essay retrieval is disabled for this run.';
    else if (report.status === 'empty') reason = 'No eligible essay text was available. Enter an essay and rebuild the list.';
    else if (!str(report.status)) reason = 'This saved result has no essay retrieval data. Run a new comparison using the local server.';
    else reason = 'No essay matches for this college. Historical cases need a full essay or an essay theme summary, and the student needs an eligible essay.';
    h += '<p class="state-box">' + esc(reason) + '</p>';
  }
  return h;
}
function renderCasesTab(c) {
  c = obj(c);
  if (!c.cases) return renderResemble(c) + '<p class="calm">No past students with a known result here yet.</p>';
  var cs = obj(c.cases), res = renderResemble(c);
  return res + (res ? '<h3 class="section counts-h">The counts</h3>' : '') + '<p class="' + (res ? 'quiet' : 'reason') + '">Real students with scores like yours, and how it went for them.</p>' +
    '<div class="pools">' + renderPool(cs.own, cs, 'own') + renderPool(cs.national, cs, 'national') + '</div>' +
    '<p class="quiet small">Two separate groups, never added together. These are examples, not odds.</p>' + renderHolistic(c);
}
var LEVER_ICON = {
  score: '<path d="M8 1.5 12 6H9.3v4H12l-4 4.5L4 10h2.7V6H4z"/>',
  says: '<path d="M2 3h12v8H7.5L4 14v-3H2z"/>',
  sent_scores: '<path fill-rule="evenodd" d="M3 1.5h7l3 3v10H3zm2 5v1.4h6V6.5zm0 3v1.4h6V9.5z"/>',
  residency: '<path d="M8 1.5 14.5 7H13v7.5H9.5v-4h-3v4H3V7H1.5z"/>'
};
var LEVER_NAME = {score: 'Your score', says: 'What the college looks for', sent_scores: 'Who sent scores', residency: 'Where applicants live'};
function sourceLink(url, text) {
  var u = safeUrl(url);
  return u ? '<a class="working-only" href="' + esc(u) + '" target="_blank" rel="noopener noreferrer">' + esc(text || 'source') + '</a>' : '';
}
function renderLeversTab(c) {
  var lv = arr(obj(c).levers).map(obj).filter(function (l) { return str(l.text); });
  if (!lv.length) return '<p class="calm">We have nothing on file that would change this label.</p>';
  return '<ul class="clevers">' + lv.map(function (l) {
    var k = str(l.kind);
    return '<li><svg class="lv-icon" viewBox="0 0 16 16" width="22" height="22" aria-hidden="true" focusable="false">' + (LEVER_ICON[k] || LEVER_ICON.says) + '</svg>' +
      '<div><p class="label">' + esc(LEVER_NAME[k] || cap(k.replace(/_/g, ' '))) + '</p><p>' + esc(l.text) + ' ' + sourceLink(l.source_url) + '</p></div></li>';
  }).join('') + '</ul><p class="quiet small">The same written rule and the college\'s own published statements. Not predictions.</p>';
}
function sayLine(s) {
  s = obj(s);
  var kb = s.kb ? obj(s.kb) : null, st = kb ? str(kb.status).toLowerCase() : '';
  return '<li><p class="claim">' + esc(s.text) + (st === 'not confirmed' ? ' <span class="tagx">not confirmed</span>' : '') + '</p>' +
    '<p class="working-only small quiet">' + [esc(str(s.field)), esc(str(s.year)), sourceLink(s.source_url)].filter(Boolean).join(' · ') +
    (st === 'confirmed' ? ' · <span class="v-pass verdict">confirmed in the knowledge base</span>' : '') + (s.checked === true ? ' · <span class="v-pass verdict">checked against the source</span>' : '') + '</p></li>';
}
function renderSaysTab(c) {
  c = obj(c);
  var says = arr(c.says), myths = arr(c.myths).map(obj), h = renderFit(c.fit);
  if (!says.length && !myths.length && !h) h += "<p class=\"calm\">We don't hold this college's own statement yet, so we quote nothing.</p>";
  if (says.length) {
    h += '<p class="reason">In the college\'s own words, from the form it publishes each year.</p><ul class="claims">' + says.slice(0, 3).map(sayLine).join('') + '</ul>';
    if (says.length > 3) h += '<details class="more"><summary>' + (says.length - 3) + ' more</summary><ul class="claims">' + says.slice(3).map(sayLine).join('') + '</ul></details>';
  }
  if (myths.length) {
    h += '<details class="more"><summary>Things people say, checked (' + myths.length + ')</summary><ul class="claims">' + myths.map(function (m) {
      return '<li><p class="quiet">People say: ' + esc(m.belief) + '</p><p class="claim">' + esc(m.college_says) + '</p>' +
        '<p class="working-only small quiet">' + [esc(str(m.year)), sourceLink(m.source_url)].filter(Boolean).join(' · ') + '</p></li>';
    }).join('') + '</ul></details>';
  }
  if (str(c.cost_note)) h += '<p class="cost"><b>Cost.</b> ' + esc(c.cost_note) + '</p>';
  return h;
}
var TABS = [['why', 'How we got this'], ['cases', 'Who you resemble'], ['levers', 'What could change it'], ['says', 'What the college says']];
function renderDrill(c, tab) {
  c = obj(c);
  var L = obj(c.label), g = groupOf(L.state), active = TABS.some(function (t) { return t[0] === tab; }) ? tab : 'why';
  var h = '<header class="rc-head"><div><h2 id="receipt-title">' + esc(str(c.name) || 'Unnamed college') + '</h2>' + pill(L) + '</div>' +
    '<button type="button" class="btn" data-act="close-panel">Close</button></header>';
  if (g === 'outside_data') {
    return h + '<section class="rc-sec"><p class="reason">' + esc(str(L.rule_text) || 'This college is not in our data.') + '</p>' + didYouMean(c) +
      '<p class="calm">We hold no numbers for this college, so we say nothing about it. Check the spelling, or pick it from the search under Change the details.</p></section>';
  }
  var body = {why: renderWhyTab(c), cases: renderCasesTab(c), levers: renderLeversTab(c), says: renderSaysTab(c)};
  h += '<div class="tabs" role="tablist" aria-label="About this college">' + TABS.map(function (t) {
    return '<button type="button" role="tab" id="tab-' + t[0] + '" data-act="tab" data-tab="' + t[0] + '" aria-controls="pan-' + t[0] + '" aria-selected="' + (t[0] === active ? 'true' : 'false') + '">' + esc(t[1]) + '</button>';
  }).join('') + '</div>';
  h += TABS.map(function (t) {
    return '<section class="rc-sec tabpan" role="tabpanel" id="pan-' + t[0] + '" aria-labelledby="tab-' + t[0] + '"' + (t[0] === active ? '' : ' hidden') + '>' + body[t[0]] + '</section>';
  }).join('');
  return h + '<p class="quiet small checked"><button type="button" class="linkbtn" data-act="toggle-working">Show the working</button> for the numbers and sources behind this.</p>';
}
function panelHead(title) {
  return '<header class="rc-head"><div><h2 id="receipt-title">' + esc(title) + '</h2></div><button type="button" class="btn" data-act="close-panel">Close</button></header>';
}
/* Counselor tools: questions to ask, from the essay notes. */
function renderQuestions(result) {
  var r = obj(result), rd = obj(r.reader), st = str(rd.status), h = panelHead('Questions to ask') + '<section class="rc-sec">';
  if (essayStopped(r.privacy, rd)) return h + '<p class="calm"><b>We did not read this essay.</b> It contains text written to steer an AI, so it was stopped before any model saw it. Read it with the student.</p></section>';
  if (st === 'off') return h + '<p class="calm">The essay reader is switched off here, so there are no notes. Nothing was sent anywhere.</p></section>';
  if (st === 'empty' || !r.reader) return h + '<p class="calm">No essay was entered, so there are no notes.</p></section>';
  if (st === 'error') return h + '<p class="calm">The essay could not be read this time.</p></section>';
  var notes = arr(rd.notes).map(obj);
  h += '<p class="quiet">Here is what stood out in the essay. You read it; it never changes a label.</p>';
  h += notes.length ? '<ol class="notes">' + notes.map(function (n) {
    return '<li>' + (str(n.question) ? '<p class="note-q">' + esc(n.question) + '</p>' : '') + (str(n.quote) ? '<blockquote>“' + esc(n.quote) + '”</blockquote>' : '') +
      (str(n.observation) ? '<p class="quiet">' + esc(n.observation) + '</p>' : '') +
      (n.quote_found === true ? '<p class="working-only small"><span class="verdict v-pass">quote found word for word in the essay</span></p>' : '') + '</li>';
  }).join('') + '</ol>' : '<p class="quiet">The reader returned no notes.</p>';
  var d = num(rd.dropped) || 0;
  if (d > 0) h += '<p class="calm">' + d + ' ' + plural(d, 'note was', 'notes were') + ' left out because ' + plural(d, 'its quote was', 'their quotes were') + ' not in the essay.</p>';
  if (str(rd.model)) h += '<p class="working-only quiet small">Read by ' + esc(rd.model) + (str(rd.second_model) ? '; major checked separately by ' + esc(rd.second_model) : '') + '.</p>';
  return h + '</section>';
}
/* The working: the five steps, the checks, the privacy and guard record, the run record. */
function renderWorking(result) {
  var r = obj(result), ss = arr(r.steps).map(obj), ch = obj(r.checks), pr = obj(r.prism), pv = obj(r.privacy);
  var h = '<div class="card working-card"><h2 class="ch-title">The working</h2><p class="quiet">Labels are set by code from published numbers. A model only reads the essay and returns quotes, which code checks. The counselor decides.</p>';
  if (ss.length) {
    h += '<ol class="steps">' + ss.map(function (s, i) {
      var by = str(s.by);
      return '<li><span class="step-n">' + (i + 1) + '</span><span class="step-name">' + esc(cap(s.step)) + '</span><span class="step-what">' + esc(s.what) + '</span>' +
        '<span class="step-by">' + (by === 'code' || !by ? 'Done by code' : 'Done by the model ' + esc(by)) + (num(s.ms) !== null ? ' · ' + esc(duration(s.ms)) : '') + '</span></li>';
    }).join('') + '</ol>';
  } else h += '<p class="quiet">No steps were recorded for this run.</p>';
  var shown = num(ch.sentences_shown), hidden = num(ch.sentences_hidden);
  if (shown !== null || hidden !== null) {
    var reasons = arr(ch.hidden_reasons).map(str).filter(Boolean);
    h += '<p><b>' + (shown || 0) + ' ' + plural(shown || 0, 'sentence', 'sentences') + ' shown, ' + (hidden || 0) + ' hidden.</b>' + ((hidden || 0) > 0 && reasons.length ? ' Why hidden: ' + esc(reasons.join(' ')) : '') + '</p>';
  }
  if (r.privacy) {
    var masked = arr(pv.masked).map(obj).filter(function (m) { return num(m.count); });
    h += '<p><b>Privacy:</b> ' + (essayStopped(pv, r.reader) ? 'the essay was stopped and not read. ' + esc(pv.reason) : esc(str(pv.note) || 'nothing recorded.')) +
      (masked.length ? ' <span class="quiet">(' + esc(masked.map(function (m) { return num(m.count) + ' ' + str(m.kind); }).join(', ')) + ')</span>' : '') + '</p>';
    if (verdictMarks(pv)) h += '<p class="verdicts"><b>Essay guard:</b> ' + verdictMarks(pv) + '</p>';
  }
  if (r.prism) {
    h += '<p><b>Run record:</b> ' + esc(str(pr.status) || 'unknown') + (str(pr.why) ? '. ' + esc(pr.why) : '') +
      (num(pr.records_sent) ? ' ' + num(pr.records_sent) + ' ' + plural(num(pr.records_sent), 'record', 'records') + ' sent.' : '') + (str(pr.guardrail) ? ' Essay guard: ' + esc(pr.guardrail) + '.' : '') + '</p>';
  }
  h += renderClosenessCheck(r.closeness_check);
  if (r.closeness_check || r.closeness_method) h += '<p><button type="button" class="linkbtn" data-act="tool-how">How we worked this out</button></p>';
  arr(r.refusals).map(str).filter(Boolean).forEach(function (t) { h += '<p class="quiet small">' + esc(t) + '</p>'; });
  return h + '</div>';
}

/* ---------- the printed plan ---------- */
function familyLine(c) {
  c = obj(c);
  var L = obj(c.label), g = groupOf(L.state), bits = [];
  if (g === 'outside_data') return '<li><b>' + esc(c.name) + '.</b> Not in our data, so we say nothing about it.</li>';
  if (g === 'cant_say') bits.push(str(L.rule_text));
  else if (isEveryone(L)) bits.push('Hard for every applicant, however strong');
  if (num(c.admit_rate) !== null) bits.push(cap(inHundred(c.admit_rate)) + ' applicants get in');
  if (costLine(c.cost_year)) bits.push(cap(costLine(c.cost_year)));
  bits = bits.filter(Boolean);
  return '<li><b>' + esc(c.name) + '.</b> ' + esc(bits.map(function (b) { return b.replace(/\.$/, ''); }).join('. ')) + (bits.length ? '.' : '') + '</li>';
}
function renderFamily(result) {
  var r = obj(result), cs = arr(r.colleges).map(obj), st = obj(r.student), h = '';
  h += '<header class="fam-head"><h1>Your plan' + (str(st.label) ? ': ' + esc(studentShort(st.label)) : '') + '</h1>' +
    '<p>' + (r.synthetic === true ? 'Example student. ' : '') + 'For you and your counselor to decide together' + (str(r.generated_at) ? ' · ' + esc(str(r.generated_at).slice(0, 10)) : '') + '</p>' +
    '<p class="fam-hero">' + esc(headlineSentence(r)) + '</p></header>';
  GROUPS.forEach(function (G) {
    var items = cs.filter(function (c) { return groupOf(obj(c.label).state) === G.key; });
    if (!items.length && !G.always) return;
    h += '<section class="fam-group"><h2>' + esc(G.title) + ' (' + items.length + ')</h2>' + (items.length ? '<ul>' + items.map(familyLine).join('') + '</ul>' : '<p>' + esc(G.empty) + '</p>') + '</section>';
  });
  var lines = planLines(r);
  if (lines.length) h += '<section class="fam-group"><h2>The plan</h2><ol>' + lines.map(function (l) { return '<li><b>' + esc(l.t) + '</b> ' + esc(l.x) + '</li>'; }).join('') + '</ol></section>';
  var seen = {}, cav = [];
  function add(t) { t = str(t).trim(); if (t && !seen[t]) { seen[t] = 1; cav.push(t); } }
  add('This plan is a starting point. Your counselor makes the final call with you.');
  add('Reach, target and likely describe where your score sits against each college\'s published numbers. They are not odds of getting in. Grades, activities and the essay are not used for the labels.');
  cs.forEach(function (c) { arr(obj(c.label).caveats).forEach(add); });
  add('Cost is the published price before aid. What your family would actually pay is not known here.');
  h += '<section class="fam-group fam-caveats"><h2>Please read this with the plan</h2><ul>' + cav.map(function (t) { return '<li>' + esc(t) + '</li>'; }).join('') + '</ul></section>';
  return h;
}

/* ---------- small pieces of the student editor ---------- */
function renderCollegeChips(list, locked) {
  var l = arr(list);
  if (!l.length) return '<li class="quiet">No colleges yet. Press one below.</li>';
  return l.map(function (name, i) {
    return '<li><button type="button" class="chipbtn" data-act="remove-college" data-i="' + i + '" aria-label="Remove ' + esc(name) + '"' +
      (locked ? ' disabled' : '') + '>' + esc(name) + '<span aria-hidden="true"> ×</span></button></li>';
  }).join('');
}
function renderQuickAdds(names, list) {
  var have = arr(list).map(function (x) { return str(x).toLowerCase(); });
  return arr(names).map(str).filter(Boolean).map(function (n) {
    var on = have.indexOf(n.toLowerCase()) !== -1;
    return '<button type="button" class="pick" data-act="quick-add" data-name="' + esc(n) + '"' + (on ? ' disabled' : '') + '>' + (on ? '' : '+ ') + esc(shortName(n)) + '</button>';
  }).join('');
}
function renderEssayPicks(students, chosen) {
  var h = '<button type="button" class="pick" data-act="pick-essay" data-i="-1" aria-pressed="' + (chosen === -1 ? 'true' : 'false') + '">No essay</button>';
  arr(students).forEach(function (s, i) {
    if (!str(obj(s).essay).trim()) return;
    h += '<button type="button" class="pick" data-act="pick-essay" data-i="' + i + '" aria-pressed="' + (chosen === i ? 'true' : 'false') + '">Essay from ' + esc(studentShort(obj(s).label)) + '</button>';
  });
  return h;
}
function renderActivityRows(acts) {
  return arr(acts).map(function (a, i) {
    a = obj(a);
    return '<div class="act-row" data-i="' + i + '">' +
      '<input type="text" data-k="type" value="' + esc(a.type) + '" placeholder="Type (Research)" aria-label="Activity ' + (i + 1) + ' type">' +
      '<input type="text" data-k="role" value="' + esc(a.role) + '" placeholder="Role" aria-label="Activity ' + (i + 1) + ' role">' +
      '<input type="text" data-k="description" value="' + esc(a.description) + '" placeholder="What they did" aria-label="Activity ' + (i + 1) + ' description">' +
      '<button type="button" class="x" data-act="remove-activity" data-i="' + i + '" aria-label="Remove activity ' + (i + 1) + '">Remove</button></div>';
  }).join('');
}
function renderHits(names) {
  return arr(names).map(function (n, i) {
    return '<li role="option" id="hit-' + i + '"><button type="button" data-act="pick-hit" data-name="' + esc(n) + '">' + esc(n) + '</button></li>';
  }).join('');
}
/* Accepts a list, or an object that wraps one under any of the given keys. */
function listFrom(data, keys) {
  if (Array.isArray(data)) return data;
  var o = obj(data);
  for (var i = 0; i < keys.length; i++) if (Array.isArray(o[keys[i]])) return o[keys[i]];
  return [];
}
/* A demo student in the contract's shape, the raw profile file's shape, or a manifest entry. */
function normaliseStudent(s) {
  s = obj(s);
  function first() { for (var i = 0; i < arguments.length; i++) if (arguments[i] !== undefined && arguments[i] !== null) return arguments[i]; return null; }
  return {
    label: str(first(s.label, s.name, s.id)), index: num(s.index),
    sat: num(first(s.sat, s.sat_total)), act: num(first(s.act, s.act_composite)),
    gpa: num(first(s.gpa, s.gpa_value)), gpa_scale: num(first(s.gpa_scale, s.gpa_scale_max)), activities_rating: num(s.activities_rating),
    home_state: str(first(s.home_state, s.state)), intended_major: str(first(s.intended_major, s.major)),
    hooks: arr(s.hooks).map(str).filter(function (h) { return h && h.toLowerCase() !== 'none'; }),
    activities: arr(s.activities).map(function (a) {
      a = obj(a);
      return {type: str(first(a.type, a.activity_type)), role: str(first(a.role, a.position)), description: str(a.description)};
    }),
    essay: str(s.essay), essay_words: num(s.essay_words),
    college_list: arr(s.college_list).map(str).filter(Boolean)
  };
}
/* The what-if slider. Live: a range around the entered score. Shared preview: only the saved scores. */
function sliderSpec(result, saved) {
  var st = obj(obj(result).student), sat = num(st.sat), act = num(st.act), useAct = sat === null && act !== null, base = useAct ? act : sat;
  if (saved !== undefined) {
    var e = obj(saved), vals = arr(e.values).map(num).filter(function (v) { return v !== null; }).sort(function (a, b) { return a - b; });
    if (!saved || !vals.length) return {disabled: true, reason: 'No test score to vary.'};
    var b = num(e.base) !== null ? num(e.base) : base, idx = 0;
    vals.forEach(function (v, i) { if (b !== null && Math.abs(v - b) < Math.abs(vals[idx] - b)) idx = i; });
    return {disabled: false, min: 0, max: vals.length - 1, step: 1, value: idx, shown: vals[idx], values: vals, base: vals[idx],
            kind: str(e.kind) || (useAct ? 'ACT' : 'SAT'), lo: vals[0], hi: vals[vals.length - 1]};
  }
  if (base === null) return {disabled: true, reason: 'No test score to vary.'};
  var span = useAct ? 6 : 200, lo = Math.max(useAct ? 1 : 400, base - span), hi = Math.min(useAct ? 36 : 1600, base + span);
  return {disabled: false, min: lo, max: hi, step: useAct ? 1 : 10, value: base, shown: base, values: null, base: base, kind: useAct ? 'ACT' : 'SAT', lo: lo, hi: hi};
}


var api = {
  esc: esc, inHundred: inHundred, rateFull: rateFull, moneyAbout: moneyAbout, duration: duration, groupOf: groupOf, labelPhrase: labelPhrase, pill: pill,
  renderTopChips: renderTopChips, renderStudentCards: renderStudentCards, renderGhost: renderGhost, renderWaypoints: renderWaypoints,
  renderStrengths: renderStrengths, headlineSentence: headlineSentence, renderBalanceBar: renderBalanceBar, cautionLine: cautionLine,
  renderHeadline: renderHeadline, renderCaution: renderCaution, pictureModel: pictureModel, renderPicture: renderPicture, renderPictureCard: renderPictureCard,
  changesBetween: changesBetween, moveSentence: moveSentence, ladderSentence: ladderSentence, renderHands: renderHands,
  planLines: planLines, renderPlan: renderPlan, rangeBar: rangeBar, renderDrill: renderDrill, renderPool: renderPool,
  renderWhyTab: renderWhyTab, renderCasesTab: renderCasesTab, renderLeversTab: renderLeversTab, renderSaysTab: renderSaysTab,
  renderResemble: renderResemble, renderResemblePool: renderResemblePool, renderRings: renderRings, renderMindMap: renderMindMap,
  renderGroups: renderGroups, groupsModel: groupsModel, renderKindsCheck: renderKindsCheck, kindsShown: kindsShown, hasGroups: hasGroups,
  renderScatter: renderScatter, renderPartBars: renderPartBars, renderClosenessCheck: renderClosenessCheck, renderHowBuilt: renderHowBuilt,
  renderHowWorked: renderHowWorked, methodOf: methodOf, hasCloseness: hasCloseness, leanWord: leanWord,
  renderAboutPanel: renderAboutPanel, renderDataSources: renderDataSources, renderFeatures: renderFeatures, DATA_SOURCES: DATA_SOURCES, FEATURES: FEATURES,
  renderTracker: renderTracker, renderFit: renderFit, didYouMean: didYouMean, coverageLine: coverageLine,
  renderBaselineResults: renderBaselineResults,
  renderQuestions: renderQuestions, renderWorking: renderWorking, verdictMarks: verdictMarks, renderFamily: renderFamily,
  renderCollegeChips: renderCollegeChips, renderQuickAdds: renderQuickAdds, renderEssayPicks: renderEssayPicks,
  renderActivityRows: renderActivityRows, renderHits: renderHits, listFrom: listFrom, normaliseStudent: normaliseStudent,
  sliderSpec: sliderSpec, hookText: hookText, FIXTURE: FIXTURE
};
if (typeof module !== 'undefined' && module.exports) module.exports = api;
root.CounselorCopilot = api;
if (typeof document === 'undefined') return;

/* ====================================================================== */
/* Part 2: the page                                                        */
/* ====================================================================== */

var OFTEN = ['Rutgers University-New Brunswick', 'Purdue University-Main Campus', 'University of Michigan-Ann Arbor', 'Cornell University',
  'New York University', 'Boston University', 'Georgia Institute of Technology-Main Campus', 'University of California-Los Angeles'];
var PREVIEW_LINE = 'Shared preview: saved runs for six invented students. Run it on a laptop to edit.';
/* mode: 'live' (server answers), 'static' (shared preview from saved files), 'example' (the embedded example). */
var S = {mode: 'live', base: null, view: null, whatIf: null, slider: null, students: [], pick: 0, manifest: null, runIndex: null, example: null,
         list: [], acts: [], lastInput: null, essayPick: -2, lastFocus: null, openEl: null, seq: 0, timer: null, chapter: 'ch1',
         groupsCell: null, groupsMajor: '', groupsMore: 1};
function $(id) { return document.getElementById(id); }
function all(sel, el) { return Array.prototype.slice.call((el || document).querySelectorAll(sel)); }

function fetchJSON(url, opts, ms) {
  var ctl = typeof AbortController !== 'undefined' ? new AbortController() : null;
  var t = ctl ? setTimeout(function () { ctl.abort(); }, ms || 8000) : null;
  var o = opts || {};
  if (ctl) o.signal = ctl.signal;
  if (o.body) o.headers = {'Content-Type': 'application/json'};
  return fetch(url, o).then(function (res) {
    return res.text().then(function (txt) {
      var data = null;
      try { data = JSON.parse(txt); } catch (e) { data = null; }
      return {ok: res.ok, status: res.status, data: data};
    });
  }).finally(function () { if (t) clearTimeout(t); });
}

function notice(text) {
  var n = $('notice');
  if (!text) { n.hidden = true; n.textContent = ''; return; }
  n.hidden = false; n.textContent = text;
}

/* ---------- drawing the story ---------- */
function picOpts() {
  var sl = obj(S.slider);
  return {score: S.whatIf, base: num(sl.base), scoreMin: num(sl.lo), scoreMax: num(sl.hi), whatIf: S.whatIf !== null, kind: sl.disabled ? null : sl.kind, canSwap: S.mode !== 'static',
          view: S.picView || 'trail', focus: S.picFocus, closenessFrom: hasCloseness(S.view) ? S.view : S.base, stale: !hasCloseness(S.view) && S.view !== S.base,
          cell: S.groupsCell, major: S.groupsMajor, more: S.groupsMore};
}
function redrawPicture(focusSel, fallbackSel) {
  $('picture').innerHTML = renderPictureCard(S.view, picOpts());
  var f = (focusSel && $('picture').querySelector(focusSel)) || (fallbackSel && $('picture').querySelector(fallbackSel));
  if (f) { if (!f.hasAttribute('tabindex') && !/^(button|select|a|input)$/i.test(f.tagName)) f.setAttribute('tabindex', '-1'); f.focus(); }
}
/* A picture switch redraws the card and keeps the reader at its top, since the toggle sits under a card that can be tall. */
function showPictureTop() {
  var pic = $('picture');
  pic.innerHTML = renderPictureCard(S.view, picOpts());
  var btn = pic.querySelector('[data-view="' + S.picView + '"]');
  if (btn) { try { btn.focus({preventScroll: true}); } catch (e) { btn.focus(); } }
  if (pic.scrollIntoView) pic.scrollIntoView({block: 'start'});
}
function drawView() {
  $('headline').innerHTML = renderHeadline(S.view, S.whatIf);
  $('picture').innerHTML = renderPictureCard(S.view, picOpts());
  $('caution').innerHTML = renderCaution(S.view);
}
function drawWaypoints() { $('waypoints').innerHTML = renderWaypoints(S.chapter, !!S.base); }
function showResult(result) {
  S.base = S.view = result; S.whatIf = null; S.seq++;
  S.slider = S.mode === 'static' ? sliderSpec(result, obj(obj(S.manifest).scores)[String(S.runIndex)] || null) : sliderSpec(result);
  $('top-chips').innerHTML = renderTopChips(result, S.mode);
  $('opening').hidden = true; $('student-panel').hidden = true; $('results').hidden = false;
  $('ch1').innerHTML = renderStrengths(result);
  drawView();
  $('ch3').innerHTML = renderHands(result, S.slider, S.mode !== 'static');
  $('ch4').innerHTML = renderPlan(result) + '<div id="tracker"></div>' + nextButton('ch5', 'Compare your essay');
  S.track = {}; S.trackMsg = null; drawTracker();
  $('working').innerHTML = renderWorking(result);
  $('family').innerHTML = renderFamily(result);
  S.chapter = 'ch1'; drawWaypoints(); drawQuick();
  window.scrollTo(0, 0);
}
function go(id) {
  var el = $(id);
  if (!el || $('results').hidden) return;
  S.chapter = id; drawWaypoints();
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  el.scrollIntoView({behavior: reduce ? 'auto' : 'smooth', block: 'start'});
  var t = el.querySelector('.ch-title'); if (t) t.focus({preventScroll: true});
}
function inputFromStudent(st) {
  var s = normaliseStudent(st);
  return {label: s.label || 'Student', sat: s.sat, act: s.act, gpa: s.gpa, gpa_scale: s.gpa_scale, activities_rating: s.activities_rating, home_state: s.home_state || null,
          intended_major: s.intended_major || null, hooks: s.hooks.length ? s.hooks : ['none'], activities: s.activities, essay: '', college_list: s.college_list};
}

/* ---------- the tracker ---------- */
function drawTracker() { var el = $('tracker'); if (el) el.innerHTML = renderTracker(S.base, S.mode !== 'static', S.track, S.trackMsg); }
function trackOf(name) {
  var c = arr(obj(S.base).colleges).map(obj).filter(function (x) { return str(x.name) === name; })[0];
  return Object.assign({status: 'considering', outcome: null}, obj(obj(c).tracker), obj(S.track[name]));
}
function postTrack(body, name, next) {
  fetchJSON('api/tracker', {method: 'POST', body: JSON.stringify(body)}, 15000).then(function (r) {
    var d = obj(r.data);
    if (!r.ok || r.data === null || str(d.error)) { S.trackMsg = {note: str(d.error) || 'That could not be saved (' + r.status + ').'}; drawTracker(); return; }
    if (body.reset) S.track = {}; else S.track[name] = next;
    S.trackMsg = {note: str(d.note), case_added: d.case_added === true}; drawTracker();
    var b = $('tracker').querySelector('[data-name="' + (window.CSS && CSS.escape ? CSS.escape(name || '') : '') + '"][aria-pressed="true"]'); if (b) b.focus();
  }).catch(function () { S.trackMsg = {note: 'Keeping track needs the server, which could not be reached.'}; drawTracker(); });
}
function trackStep(name, status) {
  if (status === 'result') { S.track[name] = Object.assign(trackOf(name), {asking: true}); S.trackMsg = null; drawTracker(); var f = $('tracker').querySelector('[data-act="track-outcome"]'); if (f) f.focus(); return; }
  postTrack({student: obj(S.base).student_key || obj(obj(S.base).student).label, college: name, status: status}, name, {status: status, outcome: null});
}
function trackOutcome(name, outcome) {
  postTrack({student: obj(S.base).student_key || obj(obj(S.base).student).label, college: name, status: 'result', outcome: outcome}, name, {status: 'result', outcome: outcome});
}

/* ---------- the what-if score ---------- */
function onWhatIf(raw) {
  var sl = S.slider;
  if (!sl || sl.disabled) return;
  var v = sl.values ? sl.values[+raw] : +raw;
  if (num(v) === null) return;
  $('whatif-out').textContent = v;
  S.whatIf = v === sl.base ? null : v;
  $('whatif-reset').disabled = S.whatIf === null;
  $('whatif-hint').textContent = '';
  $('picture').innerHTML = renderPictureCard(S.view, picOpts());
  clearTimeout(S.timer);
  var seq = ++S.seq;
  S.timer = setTimeout(function () {
    if (S.whatIf === null) { S.view = S.base; drawView(); $('whatif-say').textContent = ladderSentence(S.base); return; }
    var req;
    if (S.mode === 'static') {
      req = fetchJSON('static/run-' + S.runIndex + '-' + v + '.json');
    } else {
      var inp = Object.assign({}, S.lastInput || inputFromStudent(obj(S.base).student), {use_model: false, essay: ''});
      if (sl.kind === 'ACT') inp.act = v; else inp.sat = v;
      req = fetchJSON('api/run', {method: 'POST', body: JSON.stringify(inp)}, 20000);
    }
    function failed() { if (seq === S.seq) $('whatif-hint').textContent = 'The labels could not be re-run here. The line has moved; the labels have not.'; }
    req.then(function (r) {
      if (seq !== S.seq) return;
      if (r.ok && r.data && Array.isArray(r.data.colleges)) { S.view = r.data; drawView(); $('whatif-say').textContent = moveSentence(v, changesBetween(S.base, S.view)); }
      else failed();
    }).catch(failed);
  }, 250);
}
function resetScore() {
  var sl = S.slider, el = $('whatif');
  if (!sl || !el) return;
  el.value = sl.value; onWhatIf(el.value); el.focus();
}

/* ---------- loading: server, then shared preview, then the embedded example ---------- */
function drawCards() { $('student-cards').innerHTML = renderStudentCards(S.students, S.pick); }
function setStudents(list) {
  S.students = list.map(normaliseStudent); S.pick = 0;
  if (S.students.length) fillForm(S.students[0]);
  drawCards(); drawEssayPicks();
}
function loadExample(why) {
  function use(data) {
    if (!data || !Array.isArray(data.colleges)) { notice('No example could be loaded.'); return; }
    S.mode = 'example'; S.example = data;
    if (why === 'runfail') { showResult(data); notice('The server could not be reached, so this is the example student, not the one you entered.'); return; }
    setStudents([data.student]); S.lastInput = null;
    $('top-chips').innerHTML = renderTopChips(data, 'example');
  }
  return fetchJSON('../docs/fixture_result.json').then(function (r) { use(r.ok && r.data ? r.data : FIXTURE); }).catch(function () { use(FIXTURE); });
}
function lockEditing() {
  $('more-fields').hidden = true; $('mode-line').hidden = false; $('mode-line').textContent = PREVIEW_LINE;
  all('[data-tool="edit"],[data-tool="case"]').forEach(function (b) { b.hidden = true; });
  $('change-link').hidden = true; $('preview-line').hidden = false; $('preview-line').textContent = PREVIEW_LINE;
}
function loadPreview() {
  return fetchJSON('static/manifest.json').then(function (r) {
    var list = listFrom(obj(r.data).students, []);
    if (!r.ok || !list.length) throw new Error('no manifest');
    S.mode = 'static'; S.manifest = r.data;
    setStudents(list); lockEditing();
    $('top-chips').innerHTML = renderTopChips(null, 'static');
  });
}

/* ---------- the student editor (Counselor tools, Change the details) ---------- */
function showOut(k) {
  var none = $('f-' + k + '-none').checked, el = $('f-' + k);
  el.disabled = none;
  $('o-' + k).textContent = none ? 'none' : (k === 'gpa' ? (+el.value).toFixed(1) : el.value);
}
function setSlider(k, v, dflt) {
  $('f-' + k + '-none').checked = v === null;
  $('f-' + k).value = v === null ? dflt : v;
  showOut(k);
}
function syncMajor() {
  var v = $('f-major').value.trim().toLowerCase();
  all('[data-act="pick-major"]').forEach(function (b) { b.setAttribute('aria-pressed', b.getAttribute('data-major').toLowerCase() === v ? 'true' : 'false'); });
}
function fillForm(s) {
  s = s || normaliseStudent({});
  $('f-label').value = s.label || '';
  setSlider('sat', s.sat, 1200); setSlider('act', s.act, 24); setSlider('gpa', s.gpa === null ? null : Math.min(4, s.gpa), 3.5);
  setSlider('actv', s.activities_rating === undefined ? null : s.activities_rating, 5);
  $('f-state').value = (s.home_state || '').toUpperCase();
  $('f-major').value = s.intended_major || ''; syncMajor();
  $('f-essay').value = s.essay || '';
  $('baseline-query').value = s.essay || ''; resetBaseline();
  S.essayPick = s.essay ? S.students.indexOf(s) : -1; drawEssayPicks();
  $('essay-hint').textContent = (!s.essay && s.essay_words) ? 'The example essay (' + s.essay_words + ' words) is not shown here.' : '';
  all('[data-act="toggle-hook"]').forEach(function (b) { b.setAttribute('aria-pressed', s.hooks.indexOf(b.getAttribute('data-hook')) !== -1 ? 'true' : 'false'); });
  S.acts = s.activities.map(function (a) { return Object.assign({}, a); }); S.list = s.college_list.slice();
  drawActs(); drawChips(); $('build-hint').textContent = '';
}
function syncActs() {
  all('#activities .act-row').forEach(function (row) {
    var i = +row.getAttribute('data-i');
    if (!S.acts[i]) return;
    all('input', row).forEach(function (inp) { S.acts[i][inp.getAttribute('data-k')] = inp.value.trim(); });
  });
}
var baselineSeq = 0;
function searchBaseline() {
  var seq = ++baselineSeq, button = $('baseline-search'), results = $('baseline-results');
  var input = {essay: $('baseline-query').value, degree_level: $('baseline-level').value};
  if (!input.essay.trim()) { results.innerHTML = renderBaselineResults({status: 'empty'}); return Promise.resolve(); }
  button.disabled = true; button.textContent = 'Finding similar essays…';
  results.setAttribute('aria-busy', 'true'); $('baseline-status').textContent = 'Comparing your draft with the essay bank…';
  return fetchJSON('api/essay-search', {method: 'POST', body: JSON.stringify(input)}, 120000).then(function (response) {
    if (seq !== baselineSeq) return;
    if (response.ok && response.data) {
      results.innerHTML = renderBaselineResults(response.data);
      $('baseline-status').textContent = response.data.matches && response.data.matches.length ? 'Reference essays found.' : '';
    } else {
      results.innerHTML = '<p class="quiet">Run the local server to search the essay bank.</p>';
      $('baseline-status').textContent = '';
    }
  }).catch(function () {
    if (seq !== baselineSeq) return;
    results.innerHTML = '<p class="quiet">Run the local server to search the essay bank.</p>'; $('baseline-status').textContent = '';
  }).finally(function () {
    if (seq !== baselineSeq) return;
    button.disabled = false; button.textContent = 'Find similar essays'; results.removeAttribute('aria-busy');
  });
}
function resetBaseline() {
  baselineSeq++;
  $('baseline-search').disabled = false; $('baseline-search').textContent = 'Find similar essays';
  $('baseline-results').removeAttribute('aria-busy');
  $('baseline-results').innerHTML = '<p class="quiet">Search this draft to see similar reference essays.</p>';
  $('baseline-status').textContent = '';
}
function drawActs() { $('activities').innerHTML = renderActivityRows(S.acts); }
function drawQuick() {
  $('often').innerHTML = renderQuickAdds(OFTEN, S.list);
  var sug = arr(obj(obj(S.base).balance).suggestions).map(function (x) { return str(obj(x).name); }).filter(Boolean);
  $('suggested-row').hidden = !sug.length;
  $('suggested').innerHTML = renderQuickAdds(sug, S.list);
}
function drawChips() { $('college-chips').innerHTML = renderCollegeChips(S.list, S.mode === 'static'); drawQuick(); }
function drawEssayPicks() { $('essay-picks').innerHTML = renderEssayPicks(S.students, S.essayPick); }
function readForm() {
  syncActs();
  function sv(k) { return $('f-' + k + '-none').checked ? null : num($('f-' + k).value); }
  var hooks = all('[data-act="toggle-hook"][aria-pressed="true"]').map(function (b) { return b.getAttribute('data-hook'); });
  return {
    label: $('f-label').value.trim() || 'Student', sat: sv('sat'), act: sv('act'), gpa: sv('gpa'), gpa_scale: 4.0, activities_rating: sv('actv'),
    home_state: $('f-state').value || null, intended_major: $('f-major').value.trim() || null,
    hooks: hooks.length ? hooks : ['none'],
    activities: S.acts.filter(function (a) { return a.type || a.role || a.description; }),
    essay: $('f-essay').value, college_list: S.list.slice()
  };
}
function changed(text) { S.edited = true; if (S.base) $('build-hint').textContent = text || 'Changed. Press Show where they stand to refresh.'; }
function addCollege(name) {
  name = str(name).trim();
  if (!name || S.mode === 'static') return false;
  var dup = S.list.some(function (x) { return x.toLowerCase() === name.toLowerCase(); });
  if (!dup) S.list.push(name);
  drawChips();
  $('college-q').value = ''; clearHits();
  changed(dup ? name + ' is already on the list.' : name + ' added. Press Show where they stand to see it.');
  return !dup;
}
function clearHits() { $('college-hits').innerHTML = ''; $('college-q').setAttribute('aria-expanded', 'false'); }

var searchTimer = null;
function searchColleges(q) {
  clearTimeout(searchTimer);
  if (q.trim().length < 2) { clearHits(); return; }
  searchTimer = setTimeout(function () {
    fetchJSON('api/colleges?q=' + encodeURIComponent(q.trim())).then(function (r) {
      if ($('college-q').value.trim() !== q.trim()) return;
      var names = listFrom(r.data, ['colleges', 'results', 'matches']).map(function (c) { return typeof c === 'string' ? c : str(obj(c).name); })
        .filter(Boolean).slice(0, 8);
      $('college-hits').innerHTML = renderHits(names);
      $('college-q').setAttribute('aria-expanded', names.length ? 'true' : 'false');
      $('search-hint').textContent = names.length ? '' : 'No match among the 300 colleges we hold numbers for. Press Add to list it anyway.';
      var dl = $('case-colleges'); if (dl && names.length) dl.innerHTML = names.map(function (n) { return '<option value="' + esc(n) + '">'; }).join('');
    }).catch(function () {
      $('search-hint').textContent = 'Search needs the server. Type the full name and press Add.';
    });
  }, 180);
}

function run() {
  var btns = all('[data-act="build"]');
  function busy(on) {
    btns.forEach(function (b) { b.disabled = on; b.textContent = on ? 'Getting ready…' : 'Show where they stand'; });
    if (on) $('results').setAttribute('aria-busy', 'true'); else $('results').removeAttribute('aria-busy');
  }
  if (S.mode === 'static') {
    var s = S.students[S.pick] || S.students[0], idx = s && s.index !== null ? s.index : S.pick;
    busy(true);
    return fetchJSON('static/run-' + idx + '.json').then(function (r) {
      if (r.ok && r.data && Array.isArray(r.data.colleges)) { S.runIndex = idx; notice(''); showResult(r.data); }
      else notice('That saved run could not be loaded.');
    }).catch(function () { notice('That saved run could not be loaded.'); }).finally(function () { busy(false); });
  }
  if (S.mode === 'example' && S.example && !S.edited) { showResult(S.example); notice(''); return Promise.resolve(); }
  var input = readForm();
  if (!input.college_list.length) { openEditor(); $('build-hint').textContent = 'Add at least one college first.'; return Promise.resolve(); }
  busy(true); $('build-hint').textContent = '';
  return fetchJSON('api/run', {method: 'POST', body: JSON.stringify(input)}, 120000).then(function (r) {
    if (r.ok && r.data && Array.isArray(r.data.colleges)) {
      S.mode = 'live'; S.lastInput = input; S.edited = false; notice(''); showResult(r.data);
    } else if (r.status === 404 || r.status === 405 || r.status === 501) {
      return loadExample('runfail');
    } else {
      notice('We could not get this ready: ' + (str(obj(r.data).error) || 'the server answered with an error (' + r.status + ').'));
    }
  }).catch(function () { return loadExample('runfail'); }).finally(function () { busy(false); });
}
function openEditor() {
  if (S.mode === 'static') { $('student-panel').hidden = false; return; }
  $('student-panel').hidden = false; $('more-fields').open = true;
  $('student-panel').scrollIntoView({block: 'start'});
  var f = $('student-panel').querySelector('input,button,select'); if (f) f.focus({preventScroll: true});
}
function setWorking(on) {
  document.body.classList.toggle('show-working', on);
  var b = $('working-switch'); b.setAttribute('aria-pressed', on ? 'true' : 'false');
  b.querySelector('span').textContent = on ? 'Hide the working' : 'Show the working';
  all('[data-act="toggle-working"]:not(#working-switch)').forEach(function (x) { x.textContent = on ? 'Hide the working' : 'Show the working'; });
}

/* ---------- drawers ---------- */
function openPanel(el, html, focusSel) {
  if (S.openEl && S.openEl !== el) S.openEl.hidden = true;
  else if (!S.openEl) S.lastFocus = document.activeElement;
  if (html !== null && html !== undefined) el.innerHTML = html;
  S.openEl = el; el.hidden = false; $('backdrop').hidden = false; document.body.classList.add('drawer-open');
  el.scrollTop = 0;
  var f = (focusSel && el.querySelector(focusSel)) || el.querySelector('[data-act="close-panel"]');
  if (f) f.focus();
  if (document.body.classList.contains('show-working')) setWorking(true);
}
function closePanel() {
  if (!S.openEl) return;
  S.openEl.hidden = true; S.openEl = null; $('backdrop').hidden = true; document.body.classList.remove('drawer-open');
  if (S.lastFocus && S.lastFocus.focus && document.contains(S.lastFocus)) S.lastFocus.focus();
}
function openCollege(i, tab) {
  var c = arr(obj(S.view).colleges)[i];
  if (!c) return;
  if (!obj(c).closeness && S.view !== S.base) {   /* a labels-only what-if run: keep the closeness from the last full run */
    var old = arr(obj(S.base).colleges).map(obj).filter(function (x) { return str(x.name) === str(obj(c).name); })[0];
    if (old && old.closeness) c = Object.assign({}, c, {closeness: old.closeness, closeness_stale: true});
  }
  S.picFocus = i;
  openPanel($('receipt'), renderDrill(c, tab), tab ? '#tab-' + tab : null);
}
function pickTab(name) {
  all('#receipt [role="tab"]').forEach(function (t) { t.setAttribute('aria-selected', t.getAttribute('data-tab') === name ? 'true' : 'false'); });
  all('#receipt .tabpan').forEach(function (p) { p.hidden = p.id !== 'pan-' + name; });
}
function trapTab(e) {
  var d = S.openEl;
  if (!d || e.key !== 'Tab') return;
  var f = all('a[href],button:not([disabled]),input:not([disabled]),select,textarea,summary,[tabindex]:not([tabindex="-1"])', d).filter(function (x) { return x.offsetParent !== null; });
  if (!f.length) return;
  var first = f[0], last = f[f.length - 1];
  if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
  else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
}

/* ---------- add a finished case ---------- */
function loadCaseCount() {
  fetchJSON('api/cases').then(function (r) {
    if (!r.ok) return;
    var n = listFrom(r.data, ['cases', 'results']).length;
    $('case-count').textContent = 'Your school has ' + n + ' finished ' + plural(n, 'case', 'cases') + ' on file.';
  }).catch(function () {});
}
function saveCase(form) {
  var msg = $('case-msg'), d = {};
  ['cycle_year', 'sat', 'act', 'gpa'].forEach(function (k) { var v = form.elements[k].value.trim(); d[k] = v === '' ? null : num(v); });
  ['major_group', 'hooks', 'home_state', 'college', 'outcome', 'activities_note', 'essay_theme'].forEach(function (k) { d[k] = form.elements[k].value.trim(); });
  d.home_state = d.home_state.toUpperCase();
  if (!d.college) { msg.className = 'case-msg refuse'; msg.textContent = 'Enter the college this case is about.'; form.elements.college.focus(); return; }
  msg.className = 'case-msg'; msg.textContent = 'Saving…';
  fetchJSON('api/cases', {method: 'POST', body: JSON.stringify(d)}, 15000).then(function (r) {
    var data = obj(r.data), err = str(data.error) || str(obj(data.case).error);
    if (err) { msg.className = 'case-msg refuse'; msg.textContent = 'Not saved. ' + err; return; }
    if (!r.ok || r.data === null) { msg.className = 'case-msg refuse'; msg.textContent = 'Not saved. The server did not accept the case (' + r.status + ').'; return; }
    var id = str(data.case_id) || str(obj(data.case).case_id);
    msg.className = 'case-msg ok'; msg.textContent = 'Saved' + (id ? ' as ' + id : '') + '. Names are never stored.';
    form.reset(); loadCaseCount();
  }).catch(function () { msg.className = 'case-msg refuse'; msg.textContent = 'Not saved. The server could not be reached.'; });
}

/* ---------- wiring ---------- */
function closeTools() { var t = $('tools'); if (t) t.open = false; }
function doAct(el) {
  var act = el.getAttribute('data-act'), i = +el.getAttribute('data-i'), name = el.getAttribute('data-name');
  if (act === 'open-receipt') openCollege(i, el.getAttribute('data-tab'));
  else if (act === 'close-panel') closePanel();
  else if (act === 'tab') pickTab(el.getAttribute('data-tab'));
  else if (act === 'print') window.print();
  else if (act === 'go') go(el.getAttribute('data-to'));
  else if (act === 'build') run();
  else if (act === 'toggle-working') setWorking(!document.body.classList.contains('show-working'));
  else if (act === 'pick-student') { S.pick = i; S.edited = false; fillForm(S.students[i]); drawCards(); var again = $('student-cards').querySelector('[data-i="' + i + '"]'); if (again) again.focus(); }
  else if (act === 'tool-questions') { closeTools(); if (S.base) openPanel($('receipt'), renderQuestions(S.base)); else notice('Choose a student first.'); }
  else if (act === 'tool-case') { closeTools(); openPanel($('case-panel'), null, 'input'); loadCaseCount(); }
  else if (act === 'tool-edit') { closeTools(); openEditor(); }
  else if (act === 'tool-start') { closeTools(); $('results').hidden = true; $('student-panel').hidden = true; $('opening').hidden = false; S.base = null; drawWaypoints(); notice(''); window.scrollTo(0, 0); }
  else if (act === 'hide-editor') { $('student-panel').hidden = true; }
  else if (act === 'more-suggestions') {
    var hid = all('#ch3 .sugg[data-more]'), show = hid.length && hid[0].hidden;
    hid.forEach(function (x) { x.hidden = !show; }); el.setAttribute('aria-expanded', show ? 'true' : 'false'); el.textContent = show ? 'See fewer' : 'See ' + hid.length + ' more';
  }
  else if (act === 'see-cases') {
    var cs = arr(obj(S.view).colleges), k = -1;
    cs.forEach(function (c, j) { var cc = obj(c); if (k === -1 && (num(obj(obj(cc.cases).own).n) || 0) + (num(obj(obj(cc.cases).national).n) || 0) > 0) k = j; });
    openCollege(k === -1 ? 0 : k, 'cases');
  }
  else if (act === 'why-no-percent') { var box = $('why-answer'); box.hidden = !box.hidden; el.setAttribute('aria-expanded', box.hidden ? 'false' : 'true'); }
  else if (act === 'reset-score') resetScore();
  else if (act === 'pic-view') { S.picView = el.getAttribute('data-view'); showPictureTop(); }
  else if (act === 'groups-college') { S.picFocus = i; S.groupsCell = null; S.groupsMore = 1; redrawPicture('[data-act="groups-college"][data-i="' + i + '"]'); }
  else if (act === 'groups-cell') { var key = el.getAttribute('data-key'); S.groupsCell = S.groupsCell === key ? null : key; S.groupsMore = 1; redrawPicture('[data-key="' + key + '"]'); }
  else if (act === 'groups-more') { S.groupsMore = (S.groupsMore || 1) + 1; redrawPicture('[data-act="groups-more"]', '#groups-list'); }
  else if (act === 'tool-how') { closeTools(); openPanel($('receipt'), renderHowWorked(S.base)); }
  else if (act === 'tool-about') { closeTools(); openPanel($('receipt'), renderAboutPanel(S.base, S.mode)); }
  else if (act === 'tour-pic') {
    S.picView = el.getAttribute('data-view'); closePanel();
    if (S.base) { go('ch2'); showPictureTop(); }
  }
  else if (act === 'tour-resemble') { closePanel(); if (S.base) openCollege(i, 'cases'); }
  else if (act === 'track') trackStep(name, el.getAttribute('data-status'));
  else if (act === 'track-outcome') trackOutcome(name, el.getAttribute('data-outcome'));
  else if (act === 'track-reset') postTrack({reset: true}, '', null);
  else if (act === 'swap-college') {
    var from = str(el.getAttribute('data-from')).toLowerCase(), at = -1;
    S.list.forEach(function (x, j) { if (x.toLowerCase() === from) at = j; });
    if (at === -1) S.list.push(name); else S.list[at] = name;
    drawChips(); S.edited = true; closePanel(); run();
  }
  else if (act === 'add-suggestion') { if (addCollege(name)) { el.textContent = 'Added'; el.disabled = true; run(); } }
  else if (act === 'quick-add' || act === 'pick-hit') { addCollege(name); }
  else if (act === 'add-typed') {
    var top = $('college-hits').querySelector('button'), typed = $('college-q').value.trim();
    addCollege(top && top.getAttribute('data-name').toLowerCase() === typed.toLowerCase() ? top.getAttribute('data-name') : typed);
  }
  else if (act === 'remove-college') { S.list.splice(i, 1); drawChips(); changed(); var nx = all('#college-chips button')[Math.min(i, S.list.length - 1)]; if (nx) nx.focus(); }
  else if (act === 'add-activity') { syncActs(); S.acts.push({type: '', role: '', description: ''}); drawActs(); var ins = all('#activities .act-row input'); if (ins.length) ins[ins.length - 3].focus(); changed(); }
  else if (act === 'remove-activity') { syncActs(); S.acts.splice(i, 1); drawActs(); changed(); }
  else if (act === 'toggle-hook') { el.setAttribute('aria-pressed', el.getAttribute('aria-pressed') === 'true' ? 'false' : 'true'); changed(); }
  else if (act === 'pick-major') { $('f-major').value = el.getAttribute('aria-pressed') === 'true' ? '' : el.getAttribute('data-major'); syncMajor(); changed(); }
  else if (act === 'pick-essay') {
    S.essayPick = i; $('f-essay').value = i === -1 ? '' : str(obj(S.students[i]).essay);
    $('baseline-query').value = $('f-essay').value; resetBaseline();
    var words = $('f-essay').value.trim() ? $('f-essay').value.trim().split(/\s+/).length : 0;
    $('essay-hint').textContent = i === -1 ? 'No essay will be read.' : 'Essay from ' + studentShort(obj(S.students[i]).label) + ' chosen (' + words + ' words).';
    drawEssayPicks(); changed();
    var ag = $('essay-picks').querySelector('[data-i="' + i + '"]'); if (ag) ag.focus();
  }
}
function boot() {
  $('f-state').innerHTML = '<option value="">Not given</option>' + Object.keys(STATES).map(function (k) { return '<option value="' + k + '">' + esc(STATES[k]) + '</option>'; }).join('');
  $('ghost').innerHTML = renderGhost();
  drawWaypoints();
  document.addEventListener('click', function (e) {
    var el = e.target.closest ? e.target.closest('[data-act]') : null;
    if (el && !el.disabled) doAct(el);
    var t = $('tools'); if (t && t.open && !t.contains(e.target)) t.open = false;
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') { closePanel(); closeTools(); }
    trapTab(e);
    var t = e.target;
    if ((e.key === 'Enter' || e.key === ' ') && t && t.getAttribute && t.getAttribute('role') === 'button' && t.getAttribute('data-act') && t.tagName.toLowerCase() === 'g') { e.preventDefault(); doAct(t); }
    if ((e.key === 'ArrowRight' || e.key === 'ArrowLeft') && t && t.getAttribute && t.getAttribute('role') === 'tab') {
      var tabs = all('#receipt [role="tab"]'), k = tabs.indexOf(t), nx = tabs[(k + (e.key === 'ArrowRight' ? 1 : tabs.length - 1)) % tabs.length];
      if (nx) { nx.focus(); pickTab(nx.getAttribute('data-tab')); }
    }
  });
  document.addEventListener('input', function (e) {
    var t = e.target;
    if (t.id === 'whatif') onWhatIf(t.value);
    else if (t.id === 'f-sat' || t.id === 'f-act' || t.id === 'f-gpa' || t.id === 'f-actv') { showOut(t.id.slice(2)); changed(); }
    else if (t.id === 'f-major') { syncMajor(); changed(); }
    else if (t.id === 'f-essay') { $('baseline-query').value = t.value; resetBaseline(); S.essayPick = -2; drawEssayPicks(); changed(); }
    else if (t.id === 'baseline-query') { $('f-essay').value = t.value; resetBaseline(); S.essayPick = -2; drawEssayPicks(); changed(); }
    else if (t.id === 'f-label') changed();
  });
  document.addEventListener('change', function (e) {
    var t = e.target;
    if (t.id === 'baseline-level') resetBaseline();
    else if (t.id === 'groups-major') { S.groupsMajor = t.value; S.groupsMore = 1; redrawPicture('#groups-major'); }
    else if (/^f-(sat|act|gpa|actv)-none$/.test(t.id)) { showOut(t.id.slice(2, -5)); changed(); }
    else if (t.id === 'f-state') changed();
  });
  $('baseline-form').addEventListener('submit', function (e) { e.preventDefault(); searchBaseline(); });
  $('student-form').addEventListener('submit', function (e) { e.preventDefault(); run(); });
  $('case-form').addEventListener('submit', function (e) { e.preventDefault(); saveCase(e.target); });
  var q = $('college-q');
  q.addEventListener('input', function () { $('search-hint').textContent = ''; searchColleges(q.value); });
  q.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') {
      e.preventDefault();
      var top = $('college-hits').querySelector('button');
      addCollege(top ? top.getAttribute('data-name') : q.value);
    } else if (e.key === 'ArrowDown') {
      var b = $('college-hits').querySelector('button'); if (b) { e.preventDefault(); b.focus(); }
    } else if (e.key === 'Escape') { clearHits(); }
  });
  if (typeof IntersectionObserver !== 'undefined') {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting && S.base && S.chapter !== en.target.id) { S.chapter = en.target.id; drawWaypoints(); } });
    }, {rootMargin: '-35% 0px -55% 0px'});
    CHAPTERS.forEach(function (c) { io.observe($(c[0])); });
  }
  fillForm(normaliseStudent({})); S.edited = false; drawCards();
  if (/[?&]about=1(&|$)/.test(location.search)) openPanel($('receipt'), renderAboutPanel(null, S.mode));

  if (/[?&]fixture=1(&|$)/.test(location.search)) { loadExample('asked'); return; }
  fetchJSON('api/students').then(function (r) {
    var list = listFrom(r.data, ['students', 'profiles']);
    if (!r.ok || !list.length) throw new Error('no students');
    S.mode = 'live'; setStudents(list); S.edited = false;
  }).catch(function () {
    return loadPreview().catch(function () { return loadExample('offline'); });
  });
}
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();

})(typeof window !== 'undefined' ? window : globalThis);
