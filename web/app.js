/* Counselor Copilot: the one screen.
   Part 1: pure helpers that take data and return HTML or SVG strings (no DOM; testable in Node).
   Part 2: the page wiring (runs only in a browser).
   Three levels: the first view (one picture, three levers), a drill-in with four tabs, and "Details" inside each tab.
   Every piece of data goes through esc() before it reaches HTML. */
(function (root) {
'use strict';

/* A copy of docs/fixture_result.json, used only when nothing else can be loaded. */
var FIXTURE = /*FIXTURE_START*/{"run_id":"fixture-0001","generated_at":"2026-10-10T12:30:00-04:00","synthetic":true,"student":{"label":"Student A (SYNTHETIC)","sat":1450,"act":null,"gpa":3.9,"gpa_scale":4.0,"home_state":"NJ","intended_major":"Computer Science","hooks":["first_gen"],"activities":[{"type":"Research","role":"Student researcher","description":"Summer lab program; co-author on a poster"}],"essay_words":612,"college_list":["Cornell University","Purdue University-Main Campus","Rutgers University-New Brunswick","Kenyon College","Some College Not In Our File"]},"steps":[{"step":"retrieve","what":"Looked up 5 colleges and 2,250 finished cases","ms":14,"by":"code"},{"step":"score","what":"Compared the student's SAT of 1450 with each college's published range","ms":2,"by":"code"},{"step":"bucket","what":"Labelled 4 colleges; 1 is outside our data","ms":1,"by":"code"},{"step":"explain","what":"Read the essay for themes and quotes; 3 notes kept, 1 dropped","ms":1840,"by":"anthropic/claude-haiku-4-5"},{"step":"log","what":"Recorded this run in PRISM","ms":220,"by":"code"}],"privacy":{"masked":[{"kind":"name","count":2},{"kind":"email","count":1}],"blocked":false,"reason":"","guard":"local, then PRISM","note":"3 personal details were masked before any model read the essay."},"reader":{"status":"ok","model":"anthropic/claude-haiku-4-5","second_model":"openai/gpt-5.5","tags":{"major_group":"CS","major_group_agreed":true,"activity_types":["research"],"essay_themes":["family","persistence"]},"notes":[{"observation":"The essay centres on translating for a parent at medical appointments.","quote":"I learned the word for kidney before I learned to drive","question":"Does the rest of the application show this responsibility anywhere else?","quote_found":true},{"observation":"It names a specific research task rather than a general interest in science.","quote":"I ran the same assay eleven times before it worked","question":"Can the research mentor's letter confirm this?","quote_found":true}],"dropped":1,"latency_ms":1840},"colleges":[{"id":"190415","name":"Cornell University","state":"NY","control":"private","admit_rate":0.0876,"sat25":1500,"sat75":1570,"act25":33,"act75":35,"cost_year":88140,"source":"US Department of Education, College Scorecard","in_data":true,"label":{"state":"reach_for_everyone","text":"Reach for everyone","rule_id":"R1","rule_text":"This college admits fewer than 15 in 100 applicants, so it is a reach for any student.","score_used":1450,"score_kind":"SAT","inputs":{"sat25":1500,"sat75":1570,"admit_rate":0.0876},"not_used":["GPA","activities","essay"],"caveats":["The score range covers only students who sent scores."],"steady":true,"flips":[],"publishers":[{"name":"BigFuture","label":"reach"},{"name":"Princeton Review","label":"reach"},{"name":"Scoir","label":"reach"},{"name":"Appily","label":"reach"},{"name":"CollegeVine","label":"reach"}],"publishers_disagree":false},"cases":{"needed":15,"own":{"source":"Your school's own finished cases (SYNTHETIC demo data)","verified":true,"status":"not_enough","n":4,"admitted":1,"denied":3,"waitlisted":0,"matched_on":["SAT within 100 points"],"relaxed":["hook status","major group","SAT widened to 100"],"examples":[{"case_id":"S-12","sat":1480,"act":null,"major":"CS","hooks":"first_gen","home_state":"NJ","activities_note":"Robotics captain; state finalist","essay_theme":"immigrant family","outcome":"denied","cycle_year":2025}]},"national":{"source":"Self-reported public posts (r/collegeresults)","verified":false,"status":"ok","n":23,"admitted":8,"denied":12,"waitlisted":3,"matched_on":["SAT within 50 points","same major group"],"relaxed":["hook status"],"examples":[{"case_id":"N-1042","sat":1460,"act":null,"major":"CS","hooks":"NONE","home_state":"CA","activities_rating":6.5,"outcome":"denied"},{"case_id":"N-377","sat":1440,"act":null,"major":"CS","hooks":"FIRST-GEN","home_state":"NY","activities_rating":7.5,"outcome":"admitted"},{"case_id":"N-1611","sat":1470,"act":null,"major":"CS","hooks":"NONE","home_state":"TX","activities_rating":5.5,"outcome":"waitlisted"}]},"official_admit_rate":0.0876,"pool_admit_share_all":0.251,"overcount":2.9,"caveat":"People who post their results are admitted far more often than applicants overall. Read these as examples, not odds."},"closeness":{"needed":15,"neighbours":7,"student":{"score":1450,"converted":false,"activities":null},"national":{"source":"Self-reported public posts (r/collegeresults)","verified":false,"status":"ok","n_admitted":184,"n_denied":381,"n_waitlisted":126,"d_admitted":0.08,"d_denied":0.039,"gap":-0.041,"lean":"closer_to_denied","text":"Looks more like the people denied here than the people admitted.","steady":false,"flips":[{"cause":"5 nearest instead of 7","to":"in_between"}],"parts":[{"part":"score","distance":0.057,"text":"close"},{"part":"major","distance":0.0,"text":"close"},{"part":"hooks","distance":0.286,"text":"some way off"}],"not_used":["activities rating","GPA","residency (private college)","essay","activity descriptions"],"nearest_admitted":[{"case_id":"N-1296","sat":1440,"act":null,"major":"CS","hooks":"FIRST-GEN","home_state":null,"activities_rating":2.0,"outcome":"admitted","distance":0.016,"parts":{"score":0.025,"major":0.0,"hooks":0.0}},{"case_id":"N-150","sat":1430,"act":32,"major":null,"hooks":"FIRST-GEN","home_state":"CO","activities_rating":5.5,"outcome":"admitted","distance":0.041,"parts":{"score":0.05,"hooks":0.0}},{"case_id":"N-223","sat":1430,"act":32,"major":null,"hooks":"FIRST-GEN","home_state":"CO","activities_rating":5.5,"outcome":"admitted","distance":0.041,"parts":{"score":0.05,"hooks":0.0}}],"nearest_denied":[{"case_id":"N-1960","sat":1460,"act":null,"major":"CS","hooks":"FIRST-GEN","home_state":"FL","activities_rating":5.5,"outcome":"denied","distance":0.016,"parts":{"score":0.025,"major":0.0,"hooks":0.0}},{"case_id":"N-2127","sat":1460,"act":null,"major":"CS","hooks":"FIRST-GEN","home_state":"FL","activities_rating":7.5,"outcome":"denied","distance":0.016,"parts":{"score":0.025,"major":0.0,"hooks":0.0}},{"case_id":"N-537","sat":1430,"act":null,"major":"CS","hooks":"FIRST-GEN","home_state":"NY","activities_rating":6.0,"outcome":"denied","distance":0.032,"parts":{"score":0.05,"major":0.0,"hooks":0.0}}],"kinds":[{"kind_id":"K1","name":"Mid score, CS, activities 6.5","size":113,"median_sat":1550,"median_activities":6.5,"top_major":"CS","medoid_case_id":"N-699","distance":0.25,"nearest":false},{"kind_id":"K2","name":"Lower score, CS, activities 6.5 (SAT 1460)","size":60,"median_sat":1460,"median_activities":6.5,"top_major":"CS","medoid_case_id":"N-194","distance":0.025,"nearest":true},{"kind_id":"K3","name":"Lower score, CS, activities 6.5 (SAT 1320)","size":11,"median_sat":1320,"median_activities":6.5,"top_major":"CS","medoid_case_id":"N-770","distance":0.325,"nearest":false}],"changes":[{"change":"Score 100 points higher","gap_before":-0.041,"gap_after":-0.004,"lean_after":"in_between","because":["N-559","N-1049","N-1487"]}],"changes_note":"","points":[{"case_id":"N-5","sat":1580,"activities":7.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-19","sat":1500,"activities":7.5,"outcome":"denied","kind_id":null},{"case_id":"N-37","sat":1430,"activities":5.5,"outcome":"denied","kind_id":null},{"case_id":"N-42","sat":1570,"activities":8.5,"outcome":"denied","kind_id":null},{"case_id":"N-46","sat":630,"activities":6.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-63","sat":1590,"activities":6.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-66","sat":1600,"activities":6.5,"outcome":"denied","kind_id":null},{"case_id":"N-87","sat":1460,"activities":7.5,"outcome":"waitlisted","kind_id":null},{"case_id":"N-93","sat":1540,"activities":6.5,"outcome":"denied","kind_id":null},{"case_id":"N-114","sat":1450,"activities":6.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-123","sat":1460,"activities":6.5,"outcome":"denied","kind_id":null},{"case_id":"N-127","sat":1480,"activities":5.0,"outcome":"denied","kind_id":null},{"case_id":"N-144","sat":1560,"activities":6.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-149","sat":1500,"activities":6.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-155","sat":1320,"activities":5.5,"outcome":"waitlisted","kind_id":null},{"case_id":"N-166","sat":1440,"activities":7.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-175","sat":1080,"activities":1.5,"outcome":"denied","kind_id":null},{"case_id":"N-189","sat":1450,"activities":6.5,"outcome":"denied","kind_id":null},{"case_id":"N-194","sat":1460,"activities":6.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-199","sat":1540,"activities":3.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-203","sat":1540,"activities":6.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-206","sat":1560,"activities":5.5,"outcome":"denied","kind_id":null},{"case_id":"N-209","sat":1540,"activities":6.5,"outcome":"waitlisted","kind_id":null},{"case_id":"N-212","sat":1550,"activities":7.5,"outcome":"denied","kind_id":null},{"case_id":"N-214","sat":1570,"activities":6.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-225","sat":1470,"activities":6.5,"outcome":"denied","kind_id":null},{"case_id":"N-234","sat":1530,"activities":6.5,"outcome":"waitlisted","kind_id":null},{"case_id":"N-237","sat":1400,"activities":5.0,"outcome":"denied","kind_id":null},{"case_id":"N-243","sat":1500,"activities":5.5,"outcome":"denied","kind_id":null},{"case_id":"N-251","sat":1560,"activities":6.5,"outcome":"waitlisted","kind_id":null},{"case_id":"N-260","sat":1540,"activities":6.5,"outcome":"waitlisted","kind_id":null},{"case_id":"N-268","sat":1540,"activities":8.5,"outcome":"waitlisted","kind_id":null},{"case_id":"N-272","sat":1430,"activities":6.5,"outcome":"denied","kind_id":null},{"case_id":"N-274","sat":1540,"activities":5.5,"outcome":"waitlisted","kind_id":null},{"case_id":"N-279","sat":1540,"activities":6.5,"outcome":"denied","kind_id":null},{"case_id":"N-284","sat":1590,"activities":6.5,"outcome":"denied","kind_id":null},{"case_id":"N-296","sat":1480,"activities":5.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-303","sat":1400,"activities":6.5,"outcome":"denied","kind_id":null},{"case_id":"N-312","sat":1520,"activities":7.5,"outcome":"denied","kind_id":null},{"case_id":"N-318","sat":1560,"activities":7.5,"outcome":"admitted","kind_id":"K1"}]},"own":{"source":"Your school's own finished cases","verified":true,"status":"none","n_admitted":0,"n_denied":2,"n_waitlisted":1,"text":"No finished cases for this college in this pool."},"caveat":"Closeness compares this student with people who chose to post their results. It is not a forecast."},"says":[{"claim_id":"c7_essay","text":"Cornell rates the application essay Very Important.","field":"Common Data Set, section C7","year":"2025-26","source_url":"https://www.collegedata.fyi/schools/cornell/2025-26/cds.csv","numbers":[],"kb":{"text":"Application Essay: Very Important","score":0.83,"doc":"KB_doc1_college_admission_factors_C7.md"},"checked":true}],"myths":[{"belief":"Showing interest (visits, emails) improves the odds.","college_says":"Cornell's form rates level of applicant's interest Not Considered.","source_url":"https://www.collegedata.fyi/schools/cornell/2025-26/cds.csv","year":"2025-26"}],"cost_note":"Sticker cost is about $88,000 a year. What this family would actually pay is not known here.","flags":[]},{"id":"243780","name":"Purdue University-Main Campus","state":"IN","control":"public","admit_rate":0.4995,"sat25":1210,"sat75":1470,"act25":27,"act75":34,"cost_year":22812,"source":"US Department of Education, College Scorecard","in_data":true,"label":{"state":"target","text":"Target","rule_id":"R4","rule_text":"The score is inside the college's middle range (1210 to 1470).","score_used":1450,"score_kind":"SAT","inputs":{"sat25":1210,"sat75":1470,"admit_rate":0.4995},"not_used":["GPA","activities","essay"],"caveats":["The score range covers only students who sent scores.","Computer science at Purdue is harder to get into than the university as a whole; this label is for the university."],"steady":false,"flips":[{"cause":"score 30 points higher","to":"likely"}],"publishers":[{"name":"BigFuture","label":"target"},{"name":"Princeton Review","label":"target"},{"name":"Scoir","label":"likely"},{"name":"Appily","label":"target"},{"name":"CollegeVine","label":"target"}],"publishers_disagree":true},"cases":{"needed":15,"own":{"source":"Your school's own finished cases (SYNTHETIC demo data)","verified":true,"status":"none","n":0,"admitted":0,"denied":0,"waitlisted":0,"matched_on":[],"relaxed":[],"examples":[]},"national":{"source":"Self-reported public posts (r/collegeresults)","verified":false,"status":"ok","n":31,"admitted":22,"denied":6,"waitlisted":3,"matched_on":["SAT within 50 points","same major group","same hook status"],"relaxed":[],"examples":[{"case_id":"N-0","sat":1440,"act":null,"major":"CS","hooks":"NONE","home_state":"MI","activities_rating":2.0,"outcome":"admitted"},{"case_id":"N-918","sat":1460,"act":null,"major":"CS","hooks":"NONE","home_state":"IL","activities_rating":6.5,"outcome":"denied"}]},"official_admit_rate":0.4995,"pool_admit_share_all":0.687,"overcount":1.4,"caveat":"People who post their results are admitted far more often than applicants overall. Read these as examples, not odds."},"says":[],"myths":[],"cost_note":"Sticker cost is about $23,000 a year in-state; out-of-state students pay more. What this family would actually pay is not known here.","flags":[],"closeness":{"needed":15,"neighbours":7,"student":{"score":1450,"converted":false,"activities":null},"national":{"source":"Self-reported public posts (r/collegeresults)","verified":false,"status":"ok","n_admitted":231,"n_denied":54,"n_waitlisted":21,"d_admitted":0.09,"d_denied":0.1,"gap":0.01,"lean":"in_between","text":"About as close to the people admitted as to the people denied.","steady":true,"flips":[],"parts":[{"part":"score","distance":0.064,"text":"close"},{"part":"major","distance":0.0,"text":"close"},{"part":"hooks","distance":0.429,"text":"some way off"},{"part":"residency","distance":0.0,"text":"close"}],"not_used":["activities rating","GPA","essay","activity descriptions"],"nearest_admitted":[{"case_id":"N-2104","sat":1460,"act":null,"major":"CS","hooks":"FIRST-GEN","home_state":null,"activities_rating":3.5,"outcome":"admitted","distance":0.016,"parts":{"score":0.025,"major":0.0,"hooks":0.0}},{"case_id":"N-1428","sat":1490,"act":null,"major":"CS","hooks":"FIRST-GEN","home_state":"WA","activities_rating":4.5,"outcome":"admitted","distance":0.056,"parts":{"score":0.1,"major":0.0,"hooks":0.0,"residency":0.0}},{"case_id":"N-1494","sat":1500,"act":31,"major":"CS","hooks":"FIRST-GEN","home_state":"MI","activities_rating":4.5,"outcome":"admitted","distance":0.07,"parts":{"score":0.125,"major":0.0,"hooks":0.0,"residency":0.0}}],"nearest_denied":[{"case_id":"N-1739","sat":1470,"act":null,"major":"CS","hooks":"FIRST-GEN","home_state":"PA","activities_rating":6.0,"outcome":"denied","distance":0.028,"parts":{"score":0.05,"major":0.0,"hooks":0.0,"residency":0.0}},{"case_id":"N-1740","sat":1470,"act":null,"major":"CS","hooks":"FIRST-GEN","home_state":"PA","activities_rating":6.5,"outcome":"denied","distance":0.028,"parts":{"score":0.05,"major":0.0,"hooks":0.0,"residency":0.0}},{"case_id":"N-1741","sat":1470,"act":null,"major":"CS","hooks":"FIRST-GEN","home_state":"PA","activities_rating":6.0,"outcome":"denied","distance":0.028,"parts":{"score":0.05,"major":0.0,"hooks":0.0,"residency":0.0}}],"kinds":[{"kind_id":"K1","name":"High score, CS, activities 7.5","size":95,"median_sat":1570,"median_activities":7.5,"top_major":"CS","medoid_case_id":"N-1789","distance":0.3,"nearest":false},{"kind_id":"K2","name":"Mid score, CS, activities 6.5","size":93,"median_sat":1510,"median_activities":6.5,"top_major":"CS","medoid_case_id":"N-959","distance":0.15,"nearest":true},{"kind_id":"K3","name":"Lower score, ENG, activities 6.5","size":43,"median_sat":1390,"median_activities":6.5,"top_major":"ENG","medoid_case_id":"N-656","distance":0.15,"nearest":false}],"changes":[],"changes_note":"Nothing we can measure here would move this.","points":[{"case_id":"N-0","sat":1440,"activities":2.0,"outcome":"admitted","kind_id":"K3"},{"case_id":"N-8","sat":1580,"activities":6.5,"outcome":"denied","kind_id":null},{"case_id":"N-12","sat":1530,"activities":7.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-42","sat":1570,"activities":8.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-59","sat":1330,"activities":2.5,"outcome":"admitted","kind_id":"K3"},{"case_id":"N-64","sat":1500,"activities":6.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-71","sat":1590,"activities":2.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-80","sat":1430,"activities":8.5,"outcome":"admitted","kind_id":"K3"},{"case_id":"N-81","sat":1400,"activities":5.0,"outcome":"admitted","kind_id":"K3"},{"case_id":"N-101","sat":1490,"activities":6.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-104","sat":1560,"activities":6.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-113","sat":1530,"activities":5.0,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-143","sat":1560,"activities":6.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-158","sat":1540,"activities":6.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-166","sat":1440,"activities":7.5,"outcome":"admitted","kind_id":"K3"},{"case_id":"N-191","sat":1480,"activities":8.2,"outcome":"waitlisted","kind_id":null},{"case_id":"N-210","sat":1540,"activities":7.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-238","sat":1490,"activities":8.5,"outcome":"waitlisted","kind_id":null},{"case_id":"N-254","sat":1540,"activities":8.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-258","sat":1540,"activities":5.0,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-262","sat":1530,"activities":7.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-272","sat":1430,"activities":6.5,"outcome":"admitted","kind_id":"K3"},{"case_id":"N-279","sat":1540,"activities":6.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-290","sat":1450,"activities":7.5,"outcome":"admitted","kind_id":"K3"},{"case_id":"N-303","sat":1400,"activities":6.5,"outcome":"waitlisted","kind_id":null},{"case_id":"N-311","sat":1540,"activities":5.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-318","sat":1560,"activities":7.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-334","sat":1590,"activities":5.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-337","sat":1570,"activities":1.0,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-359","sat":1510,"activities":6.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-363","sat":1480,"activities":4.0,"outcome":"denied","kind_id":null},{"case_id":"N-376","sat":1440,"activities":8.5,"outcome":"waitlisted","kind_id":null},{"case_id":"N-389","sat":1550,"activities":9.5,"outcome":"waitlisted","kind_id":null},{"case_id":"N-434","sat":1450,"activities":6.5,"outcome":"admitted","kind_id":"K3"},{"case_id":"N-480","sat":1280,"activities":1.0,"outcome":"admitted","kind_id":"K3"},{"case_id":"N-497","sat":1420,"activities":5.5,"outcome":"admitted","kind_id":"K3"},{"case_id":"N-507","sat":1560,"activities":8.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-514","sat":1590,"activities":6.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-538","sat":1520,"activities":5.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-544","sat":1540,"activities":2.5,"outcome":"admitted","kind_id":"K2"}]},"own":{"source":"Your school's own finished cases","verified":true,"status":"not_enough","n_admitted":1,"n_denied":5,"n_waitlisted":0,"d_admitted":0.315,"d_denied":0.517,"gap":0.202,"lean":null,"text":"Not enough finished cases in one of the two groups to say which the student is closer to.","steady":null,"flips":[],"parts":[{"part":"score","distance":0.1,"text":"close"},{"part":"major","distance":1.0,"text":"far"},{"part":"hooks","distance":1.0,"text":"far"},{"part":"residency","distance":0.0,"text":"close"},{"part":"gpa","distance":0.1,"text":"close"}],"not_used":["activities rating","essay","activity descriptions"],"nearest_admitted":[{"case_id":"S-106","sat":1490,"act":null,"major":"BIO","hooks":"NONE","home_state":"NJ","activities_rating":null,"outcome":"admitted","activities_note":"Family business helper; Summer research at a university lab","essay_theme":"service","distance":0.315,"parts":{"score":0.1,"major":1.0,"hooks":1.0,"residency":0.0,"gpa":0.1}}],"nearest_denied":[{"case_id":"S-5","sat":1380,"act":null,"major":"PSYCH","hooks":"URM","home_state":"NJ","activities_rating":null,"outcome":"denied","activities_note":"Model UN delegate","essay_theme":"mentorship","distance":0.357,"parts":{"score":0.175,"major":1.0,"hooks":1.0,"residency":0.0,"gpa":0.14}},{"case_id":"S-68","sat":null,"act":26,"major":"CS","hooks":"NONE","home_state":"NJ","activities_rating":null,"outcome":"denied","activities_note":"Art portfolio and school gallery show","essay_theme":"leadership","distance":0.404,"parts":{"score":0.525,"major":0.0,"hooks":1.0,"residency":0.0,"gpa":0.34}},{"case_id":"S-74","sat":1330,"act":null,"major":"ARTS","hooks":"NONE","home_state":"NJ","activities_rating":null,"outcome":"denied","activities_note":"Art portfolio and school gallery show","essay_theme":"community","distance":0.419,"parts":{"score":0.3,"major":1.0,"hooks":1.0,"residency":0.0,"gpa":0.17}}],"kinds":[],"changes":[],"changes_note":"","points":[{"case_id":"S-5","sat":1380,"activities":null,"outcome":"denied","kind_id":null},{"case_id":"S-45","sat":1010,"activities":null,"outcome":"denied","kind_id":null},{"case_id":"S-68","sat":1240,"activities":null,"outcome":"denied","kind_id":null},{"case_id":"S-74","sat":1330,"activities":null,"outcome":"denied","kind_id":null},{"case_id":"S-80","sat":1240,"activities":null,"outcome":"denied","kind_id":null},{"case_id":"S-106","sat":1490,"activities":null,"outcome":"admitted","kind_id":null}]},"caveat":"Closeness compares this student with people who chose to post their results. It is not a forecast."}},{"id":"186380","name":"Rutgers University-New Brunswick","state":"NJ","control":"public","admit_rate":0.582,"sat25":1270,"sat75":1480,"act25":28,"act75":33,"cost_year":37000,"source":"US Department of Education, College Scorecard","in_data":true,"label":{"state":"target","text":"Target","rule_id":"R4","rule_text":"The score is inside the college's middle range (1270 to 1480).","score_used":1450,"score_kind":"SAT","inputs":{"sat25":1270,"sat75":1480,"admit_rate":0.582},"not_used":["GPA","activities","essay"],"caveats":["The score range covers only students who sent scores."],"steady":false,"flips":[{"cause":"score 30 points higher","to":"likely"}],"publishers":[{"name":"BigFuture","label":"target"},{"name":"Princeton Review","label":"target"},{"name":"Scoir","label":"likely"},{"name":"Appily","label":"target"},{"name":"CollegeVine","label":"target"}],"publishers_disagree":true},"cases":{"needed":15,"own":{"source":"Your school's own finished cases (SYNTHETIC demo data)","verified":true,"status":"ok","n":17,"admitted":13,"denied":3,"waitlisted":1,"matched_on":["SAT within 100 points"],"relaxed":["hook status","major group","SAT widened to 100"],"examples":[{"case_id":"S-3","sat":1430,"act":null,"major":"ENG","hooks":"none","home_state":"NJ","activities_note":"Varsity track; part-time job","essay_theme":"work","outcome":"admitted","cycle_year":2025}]},"national":{"source":"Self-reported public posts (r/collegeresults)","verified":false,"status":"not_enough","n":9,"admitted":7,"denied":1,"waitlisted":1,"matched_on":["SAT within 100 points"],"relaxed":["hook status","major group","SAT widened to 100"],"examples":[]},"official_admit_rate":0.582,"pool_admit_share_all":0.7,"overcount":1.2,"caveat":"People who post their results are admitted far more often than applicants overall. Read these as examples, not odds."},"says":[],"myths":[],"cost_note":"Sticker cost is about $37,000 a year in-state. What this family would actually pay is not known here.","flags":[],"closeness":{"needed":15,"neighbours":7,"student":{"score":1450,"converted":false,"activities":null},"national":{"source":"Self-reported public posts (r/collegeresults)","verified":false,"status":"not_enough","n_admitted":95,"n_denied":2,"n_waitlisted":1,"d_admitted":0.168,"d_denied":0.431,"gap":0.263,"lean":null,"text":"Not enough finished cases in one of the two groups to say which the student is closer to.","steady":null,"flips":[],"parts":[{"part":"score","distance":0.093,"text":"close"},{"part":"major","distance":0.0,"text":"close"},{"part":"hooks","distance":0.571,"text":"far"},{"part":"residency","distance":1.0,"text":"far"}],"not_used":["activities rating","GPA","essay","activity descriptions"],"nearest_admitted":[{"case_id":"N-1296","sat":1440,"act":null,"major":"CS","hooks":"FIRST-GEN","home_state":null,"activities_rating":2.0,"outcome":"admitted","distance":0.016,"parts":{"score":0.025,"major":0.0,"hooks":0.0}},{"case_id":"N-1022","sat":1510,"act":null,"major":null,"hooks":"FIRST-GEN","home_state":null,"activities_rating":6.5,"outcome":"admitted","distance":0.123,"parts":{"score":0.15,"hooks":0.0}},{"case_id":"N-2205","sat":1480,"act":null,"major":"CS","hooks":"FIRST-GEN","home_state":"FL","activities_rating":3.5,"outcome":"admitted","distance":0.167,"parts":{"score":0.075,"major":0.0,"hooks":0.0,"residency":1.0}}],"nearest_denied":[{"case_id":"N-2194","sat":1480,"act":null,"major":"BUSINESS","hooks":"FIRST-GEN","home_state":"GA","activities_rating":2.5,"outcome":"denied","distance":0.355,"parts":{"score":0.075,"major":1.0,"hooks":0.0,"residency":1.0}},{"case_id":"N-1729","sat":1500,"act":null,"major":"BIO","hooks":"NONE","home_state":"WA","activities_rating":7.5,"outcome":"denied","distance":0.508,"parts":{"score":0.125,"major":1.0,"hooks":1.0,"residency":1.0}}],"kinds":[{"kind_id":"K1","name":"High score, CS, activities 6.5","size":62,"median_sat":1540,"median_activities":6.5,"top_major":"CS","medoid_case_id":"N-1022","distance":0.15,"nearest":false},{"kind_id":"K2","name":"Lower score, CS, activities 5.5","size":21,"median_sat":1460,"median_activities":5.5,"top_major":"CS","medoid_case_id":"N-194","distance":0.025,"nearest":true},{"kind_id":"K3","name":"Lower score, CS, activities 5.2","size":12,"median_sat":1290,"median_activities":5.2,"top_major":"CS","medoid_case_id":"N-643","distance":0.375,"nearest":false}],"changes":[],"changes_note":"","points":[{"case_id":"N-5","sat":1580,"activities":7.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-40","sat":1460,"activities":5.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-42","sat":1570,"activities":8.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-59","sat":1330,"activities":2.5,"outcome":"admitted","kind_id":"K3"},{"case_id":"N-148","sat":1430,"activities":6.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-152","sat":1500,"activities":6.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-158","sat":1540,"activities":6.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-194","sat":1460,"activities":6.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-206","sat":1560,"activities":5.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-208","sat":1540,"activities":7.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-221","sat":1520,"activities":8.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-222","sat":1450,"activities":2.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-247","sat":1500,"activities":5.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-256","sat":1500,"activities":6.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-307","sat":1550,"activities":5.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-358","sat":1570,"activities":8.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-435","sat":1570,"activities":5.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-448","sat":1500,"activities":3.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-450","sat":1550,"activities":4.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-468","sat":1580,"activities":6.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-520","sat":1540,"activities":3.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-522","sat":1450,"activities":4.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-544","sat":1540,"activities":2.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-591","sat":1520,"activities":3.0,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-612","sat":1500,"activities":7.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-643","sat":1300,"activities":5.0,"outcome":"admitted","kind_id":"K3"},{"case_id":"N-650","sat":1480,"activities":5.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-712","sat":1540,"activities":6.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-722","sat":1590,"activities":8.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-725","sat":1320,"activities":5.5,"outcome":"admitted","kind_id":"K3"},{"case_id":"N-746","sat":1470,"activities":5.0,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-883","sat":1560,"activities":6.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-889","sat":1230,"activities":4.5,"outcome":"admitted","kind_id":"K3"},{"case_id":"N-914","sat":1540,"activities":7.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-921","sat":1460,"activities":2.5,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-926","sat":1530,"activities":6.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-954","sat":1560,"activities":7.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-983","sat":1440,"activities":1.0,"outcome":"admitted","kind_id":"K2"},{"case_id":"N-1022","sat":1510,"activities":6.5,"outcome":"admitted","kind_id":"K1"},{"case_id":"N-1032","sat":1550,"activities":6.5,"outcome":"admitted","kind_id":"K1"}]},"own":{"source":"Your school's own finished cases","verified":true,"status":"not_enough","n_admitted":4,"n_denied":6,"n_waitlisted":0,"d_admitted":0.364,"d_denied":0.523,"gap":0.159,"lean":null,"text":"Not enough finished cases in one of the two groups to say which the student is closer to.","steady":null,"flips":[],"parts":[{"part":"score","distance":0.163,"text":"some way off"},{"part":"major","distance":1.0,"text":"far"},{"part":"hooks","distance":1.0,"text":"far"},{"part":"residency","distance":0.0,"text":"close"},{"part":"gpa","distance":0.205,"text":"some way off"}],"not_used":["activities rating","essay","activity descriptions"],"nearest_admitted":[{"case_id":"S-105","sat":1490,"act":null,"major":"BIO","hooks":"NONE","home_state":"NJ","activities_rating":null,"outcome":"admitted","activities_note":"Family business helper; Summer research at a university lab","essay_theme":"service","distance":0.315,"parts":{"score":0.1,"major":1.0,"hooks":1.0,"residency":0.0,"gpa":0.1}},{"case_id":"S-48","sat":1390,"act":null,"major":"POLISCI","hooks":"NONE","home_state":"NJ","activities_rating":null,"outcome":"admitted","activities_note":"Student newspaper editor; Robotics club captain","essay_theme":"curiosity","distance":0.349,"parts":{"score":0.15,"major":1.0,"hooks":1.0,"residency":0.0,"gpa":0.16}},{"case_id":"S-59","sat":1370,"act":null,"major":"BUSINESS","hooks":"NONE","home_state":"NJ","activities_rating":null,"outcome":"admitted","activities_note":"Family business helper; Summer research at a university lab","essay_theme":"mentorship","distance":0.362,"parts":{"score":0.2,"major":1.0,"hooks":1.0,"residency":0.0,"gpa":0.11}}],"nearest_denied":[{"case_id":"S-66","sat":1350,"act":null,"major":"CS","hooks":"NONE","home_state":"NJ","activities_rating":null,"outcome":"denied","activities_note":"Theater stage crew; Part-time job at a grocery store","essay_theme":"resilience","distance":0.217,"parts":{"score":0.25,"major":0.0,"hooks":1.0,"residency":0.0,"gpa":0.02}},{"case_id":"S-1","sat":1140,"act":null,"major":"CS","hooks":"FIRST-GEN","home_state":"NJ","activities_rating":null,"outcome":"denied","activities_note":"School orchestra first chair; Science Olympiad","essay_theme":"identity","distance":0.409,"parts":{"score":0.775,"major":0.0,"hooks":0.0,"residency":0.0,"gpa":0.3}},{"case_id":"S-42","sat":1340,"act":null,"major":"POLISCI","hooks":"NONE","home_state":"PA","activities_rating":null,"outcome":"denied","activities_note":"Hospital volunteer","essay_theme":"family","distance":0.544,"parts":{"score":0.275,"major":1.0,"hooks":1.0,"residency":1.0,"gpa":0.35}}],"kinds":[],"changes":[],"changes_note":"","points":[{"case_id":"S-1","sat":1140,"activities":null,"outcome":"denied","kind_id":null},{"case_id":"S-29","sat":1240,"activities":null,"outcome":"denied","kind_id":null},{"case_id":"S-37","sat":1080,"activities":null,"outcome":"denied","kind_id":null},{"case_id":"S-42","sat":1340,"activities":null,"outcome":"denied","kind_id":null},{"case_id":"S-48","sat":1390,"activities":null,"outcome":"admitted","kind_id":null},{"case_id":"S-59","sat":1370,"activities":null,"outcome":"admitted","kind_id":null},{"case_id":"S-61","sat":1330,"activities":null,"outcome":"denied","kind_id":null},{"case_id":"S-66","sat":1350,"activities":null,"outcome":"denied","kind_id":null},{"case_id":"S-105","sat":1490,"activities":null,"outcome":"admitted","kind_id":null},{"case_id":"S-116","sat":1370,"activities":null,"outcome":"admitted","kind_id":null}]},"caveat":"Closeness compares this student with people who chose to post their results. It is not a forecast."}},{"id":"203535","name":"Kenyon College","state":"OH","control":"private","admit_rate":0.31,"sat25":null,"sat75":null,"act25":null,"act75":null,"cost_year":85000,"source":"US Department of Education, College Scorecard","in_data":true,"label":{"state":"cant_say","text":"Can't say","rule_id":"R2","rule_text":"This college publishes no test score range, so there is nothing to compare the student's score with.","score_used":1450,"score_kind":"SAT","inputs":{"sat25":null,"sat75":null,"admit_rate":0.31},"not_used":["GPA","activities","essay"],"caveats":[],"steady":true,"flips":[],"publishers":[],"publishers_disagree":false},"cases":{"needed":15,"own":{"source":"Your school's own finished cases (SYNTHETIC demo data)","verified":true,"status":"none","n":0,"admitted":0,"denied":0,"waitlisted":0,"matched_on":[],"relaxed":[],"examples":[]},"national":{"source":"Self-reported public posts (r/collegeresults)","verified":false,"status":"none","n":0,"admitted":0,"denied":0,"waitlisted":0,"matched_on":[],"relaxed":[],"examples":[]},"official_admit_rate":0.31,"pool_admit_share_all":null,"overcount":null,"caveat":"No finished cases for this college in either pool."},"says":[],"myths":[],"cost_note":"Sticker cost is about $85,000 a year. What this family would actually pay is not known here.","flags":[],"closeness":{"needed":15,"neighbours":7,"student":{"score":1450,"converted":false,"activities":null},"national":{"source":"Self-reported public posts (r/collegeresults)","verified":false,"status":"none","n_admitted":0,"n_denied":0,"n_waitlisted":0,"text":"No finished cases for this college in this pool."},"own":{"source":"Your school's own finished cases","verified":true,"status":"none","n_admitted":0,"n_denied":0,"n_waitlisted":0,"text":"No finished cases for this college in this pool."},"caveat":"Closeness compares this student with people who chose to post their results. It is not a forecast."}},{"id":null,"name":"Some College Not In Our File","state":null,"control":null,"admit_rate":null,"sat25":null,"sat75":null,"act25":null,"act75":null,"cost_year":null,"source":null,"in_data":false,"label":{"state":"outside_data","text":"Outside our data","rule_id":"R0","rule_text":"This college is not in the 300-college file, so nothing is said about it.","score_used":null,"score_kind":null,"inputs":{},"not_used":[],"caveats":[],"steady":true,"flips":[],"publishers":[],"publishers_disagree":false},"cases":null,"closeness":null,"says":[],"myths":[],"cost_note":null,"flags":[]}],"balance":{"counts":{"reach":1,"target":2,"likely":0,"cant_say":1,"outside_data":1},"warnings":[{"id":"no_likely","text":"There is no likely college on this list."},{"id":"short_list","text":"Only 3 colleges on this list could be labelled."}],"suggestions":[{"id":"185828","name":"New Jersey Institute of Technology","would_be":"likely","admit_rate":0.66,"sat25":1180,"sat75":1400,"cost_year":36000,"tuition_note":"In-state tuition applies","why":"The score is at or above the 75th percentile and the college admits about two in three applicants."},{"id":"204796","name":"Ohio State University-Main Campus","would_be":"target","admit_rate":0.53,"sat25":1300,"sat75":1470,"cost_year":30000,"tuition_note":"Out-of-state tuition applies","why":"The score is inside the middle range and the college admits about half of applicants."}],"cost_notes":[{"name":"Cornell University","text":"Sticker cost is about $88,000 a year. What this family would actually pay is not known here."}]},"checks":{"sentences_shown":14,"sentences_hidden":1,"hidden_reasons":["A number in the sentence was not in its source row."]},"prism":{"status":"off","why":"No PRISM key is set, so nothing was recorded.","session_id":null,"records_sent":0,"guardrail":"local check only","evaluator":null,"kb":"off"},"refusals":["No personal chance of admission is given. The counts above are examples from finished cases, shown beside the official admit rate.","The essay is never rated and never changes a label."],"closeness_check":{"generated_at":"2026-10-10T13:57:58-04:00","sampled":400,"used":382,"skipped_small_groups":18,"seed":20261010,"neighbours":7,"lean_gap":0.03,"source":"Self-reported public posts (r/collegeresults)","rows":[{"lean":"closer_to_admitted","admitted":39,"denied":17,"n":56},{"lean":"in_between","admitted":75,"denied":125,"n":200},{"lean":"closer_to_denied","admitted":25,"denied":101,"n":126}],"caveat":"Counted on self-reported public posts, each person hidden before their own lean was computed. People who post are admitted far more often than applicants overall, so this says how the lean sorts posters, not applicants."},"closeness_method":{"parts":[{"part":"score","name":"score","weight":0.45,"distance":"score difference / 400 SAT points, capped at 1","student":"SAT, or ACT converted to the SAT scale","case":"SAT, or ACT converted","pools":"both","required":true},{"part":"activities","name":"activities rating","weight":0.2,"distance":"rating difference / 10","student":"the counselor's 0 to 10 rating (optional)","case":"self-rated activities and awards, 0 to 10","pools":"national only","required":false},{"part":"major","name":"major group","weight":0.15,"distance":"0 same group, 1 different","student":"intended major, or the essay reader's tag when both models agreed","case":"stated major","pools":"both","required":false},{"part":"hooks","name":"hook status","weight":0.1,"distance":"0 same set of hooks, 1 different","student":"first-gen, legacy, under-represented, athlete, or none","case":"the same set","pools":"both","required":false},{"part":"residency","name":"residency","weight":0.1,"distance":"0 if both in-state or both out-of-state for this college, else 1","student":"home state","case":"home state","pools":"both, public colleges only","required":false},{"part":"gpa","name":"GPA","weight":0.2,"distance":"GPA difference / 1 on a 4.0 scale, capped at 1","student":"GPA, converted to a 4.0 scale","case":"GPA in the school's own file","pools":"own only","required":false}],"never_used":["essay text","activity descriptions","race","gender","income","class rank","the essay/recommendation/interview self-rating"],"neighbours":7,"needed":15,"lean_gap":0.03,"change_gain":0.02,"max_changes":3,"score_steps":[30,60,100],"rating_steps":[1,2],"close":0.15,"far":0.5,"steady":{"neighbours":[5,10],"score":[-30,30]},"kinds":{"k":3,"min_admitted":30,"cap":300,"rounds":20,"seed":20261010,"parts":["score","activities","major"],"score_band":40,"rating_band":1.0},"points_cap":300,"check":{"n":400,"seed":20261010},"libraries":{"engine":["csv","json","functools.lru_cache","random","statistics","collections.Counter","pathlib"],"not_used":["numpy","scikit-learn","pandas","text embeddings","any model call"],"screen":["plain HTML, CSS and JavaScript","inline SVG drawn by hand","no chart library, no framework, no build step"]}}}/*FIXTURE_END*/;

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
var STATE_TEXT = {
  reach: 'Reach', reach_for_everyone: 'Reach for everyone', target: 'Target', likely: 'Likely',
  cant_say: "Can't say", outside_data: 'Outside our data'
};
var ORDER = ['reach', 'target', 'likely', 'cant_say', 'outside_data'];
var GROUPS = [
  {key: 'reach', title: 'Reach', always: true, empty: 'No reach college on this list.'},
  {key: 'target', title: 'Target', always: true, empty: 'No target college on this list.'},
  {key: 'likely', title: 'Likely', always: true, empty: 'No likely college on this list.'},
  {key: 'cant_say', title: "Can't say", always: false},
  {key: 'outside_data', title: 'Outside our data', always: false}
];
function groupOf(state) {
  var s = str(state).toLowerCase().replace(/[\s']+/g, '_');
  if (s === 'reach' || s === 'reach_for_everyone') return 'reach';
  if (s === 'target' || s === 'likely' || s === 'outside_data') return s;
  return 'cant_say';
}
function stateText(label) {
  var L = obj(label);
  return str(L.text) || STATE_TEXT[L.state] || cap(str(L.state)) || "Can't say";
}

/* Shape as well as colour: triangle = reach, circle = target, square = likely, dashed = no label. */
var SHAPES = {
  reach: '<path d="M8 2 15 14H1z"/>',
  target: '<circle cx="8" cy="8" r="6"/>',
  likely: '<rect x="2" y="2" width="12" height="12" rx="1"/>',
  cant_say: '<path d="M8 1.5 14.5 8 8 14.5 1.5 8z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-dasharray="2.4 1.6"/>',
  outside_data: '<circle cx="8" cy="8" r="6" fill="none" stroke="currentColor" stroke-width="1.6" stroke-dasharray="2 2"/>'
};
function shape(key, extra) {
  return '<svg class="shape sh-' + (SHAPES[key] ? key : 'cant_say') + '" viewBox="0 0 16 16" width="16" height="16" aria-hidden="true" focusable="false"' +
    (extra || '') + '>' + (SHAPES[key] || SHAPES.cant_say) + '</svg>';
}
function badge(label) {
  var g = groupOf(obj(label).state);
  return '<span class="badge b-' + g + '">' + shape(g) + '<span>' + esc(stateText(label)) + '</span></span>';
}
function badgeFor(state) { return badge({state: groupOf(state) === 'cant_say' ? 'cant_say' : str(state).toLowerCase().replace(/\s+/g, '_')}); }

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

/* ---------- Level 1: top chips, student line, counters ---------- */
function renderTopChips(result, mode) {
  var r = obj(result), h = '';
  if (r.synthetic === true || mode === 'static') h += '<span class="stamp" title="Invented demo data. No real student.">SYNTHETIC</span>';
  if (mode === 'example') h += '<span class="chip chip-example">Example data</span>';
  if (mode === 'static') h += '<span class="chip chip-example">Shared preview</span>';
  return h;
}
function renderStudentLine(student, open) {
  var s = obj(student), bits = [studentShort(s.label)];
  bits.push(num(s.sat) !== null ? 'SAT ' + num(s.sat) : (num(s.act) !== null ? 'ACT ' + num(s.act) : 'No test score'));
  if (str(s.home_state)) bits.push(STATES[str(s.home_state).toUpperCase()] || str(s.home_state));
  if (str(s.intended_major)) bits.push(str(s.intended_major));
  return '<p class="sline">' + bits.map(esc).join('<span class="sep" aria-hidden="true"> · </span>') + '</p>' +
    '<button type="button" class="btn small" data-act="edit-student" aria-expanded="' + (open ? 'true' : 'false') +
    '" aria-controls="student-panel">' + (open ? 'Hide' : 'Edit') + '</button>';
}
var WARN_RANK = ['all_cant_say', 'no_likely', 'reach_heavy', 'prestige_pile', 'no_target', 'short_list'];
function warningTexts(warnings) {
  return arr(warnings).map(function (x, i) {
    var id = str(obj(x).id), k = WARN_RANK.indexOf(id);
    return {t: typeof x === 'string' ? x : str(obj(x).text), k: k === -1 ? 50 + i : k, i: i};
  }).filter(function (w) { return w.t; }).sort(function (a, b) { return a.k - b.k || a.i - b.i; }).map(function (w) { return w.t; });
}
function renderCounters(balance, whatIf) {
  var b = obj(balance), c = obj(b.counts), tiles = [['reach', 'Reach'], ['target', 'Target'], ['likely', 'Likely']];
  if (num(c.cant_say)) tiles.push(['cant_say', "Can't say"]);
  if (num(c.outside_data)) tiles.push(['outside_data', 'Outside our data']);
  var h = '<ul class="tiles">' + tiles.map(function (t) {
    var n = num(c[t[0]]) || 0;
    return '<li class="tile t-' + t[0] + (n === 0 ? ' zero' : '') + '"><span class="tile-n">' + n + '</span>' +
      '<span class="tile-l">' + shape(t[0]) + esc(t[1]) + '</span></li>';
  }).join('') + '</ul>';
  var w = warningTexts(b.warnings);
  h += '<div class="warnbox">';
  if (whatIf) h += '<p class="whatif-tag">Showing the list as it would be labelled with a different score.</p>';
  else if (w.length) {
    h += '<p class="warn1">' + esc(w[0]) + (w.length > 1
      ? ' <button type="button" class="linkbtn" data-act="more-warnings" aria-expanded="false" aria-controls="more-warn">' + (w.length - 1) + ' more</button>' : '') + '</p>';
    if (w.length > 1) h += '<ul id="more-warn" class="more-warn" hidden>' + w.slice(1).map(function (x) { return '<li>' + esc(x) + '</li>'; }).join('') + '</ul>';
  } else h += '<p class="quiet">No warnings about the balance of this list.</p>';
  return h + '</div>';
}

/* ---------- Level 1: the picture. Every college on one score axis; the student is one line. ---------- */
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
  rows.sort(function (a, b) { return ORDER.indexOf(a.g) - ORDER.indexOf(b.g) || a.i - b.i; });
  var vals = [useAct ? 18 : 1050];
  rows.forEach(function (x) { if (x.has) vals.push(x.lo, x.hi); });
  [score, base, num(o.scoreMin), num(o.scoreMax)].forEach(function (v) { if (v !== null) vals.push(v); });
  var lowest = Math.min.apply(null, vals);
  return {rows: rows, useAct: useAct, test: useAct ? 'ACT' : 'SAT', score: score, base: base,
          min: useAct ? Math.max(1, lowest - 2) : Math.max(400, Math.floor((lowest - 50) / 100) * 100), max: useAct ? 36 : 1600};
}
function renderPicture(result, opts) {
  var m = pictureModel(result, opts), o = obj(opts);
  var W = 880, X0 = 268, X1 = 640, AX = 664, CX = 772, RH = 38, TOP = 42, n = m.rows.length, H = TOP + Math.max(n, 1) * RH + 8;
  function sx(v) { return X0 + (Math.max(m.min, Math.min(m.max, v)) - m.min) / (m.max - m.min) * (X1 - X0); }
  function p(v) { return (Math.round(v * 10) / 10).toString(); }
  var s = '<svg class="pic" viewBox="0 0 ' + W + ' ' + H + '" width="' + W + '" height="' + H + '" role="group" aria-label="' +
    esc('Where this student stands: ' + n + ' ' + plural(n, 'college', 'colleges') + ' on one ' + m.test + ' score axis' +
    (m.score !== null ? ', with the student at ' + m.score : '') + '.') + '">';
  s += '<defs><pattern id="pichatch" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">' +
    '<rect class="ph-bg" width="8" height="8"/><rect class="ph-fg" width="4" height="8"/></pattern></defs>';
  var step = m.useAct ? 4 : 100, ticks = [], t;
  for (t = Math.ceil(m.min / step) * step; t <= m.max; t += step) ticks.push(t);
  var every = ticks.length > 9 ? 2 : 1;
  ticks.forEach(function (tv, k) {
    s += '<line class="pgrid" x1="' + p(sx(tv)) + '" x2="' + p(sx(tv)) + '" y1="' + (TOP - 4) + '" y2="' + (H - 4) + '"/>';
    if ((ticks.length - 1 - k) % every === 0) s += '<text class="ptick" x="' + p(sx(tv)) + '" y="' + (TOP - 9) + '" text-anchor="middle">' + tv + '</text>';
  });
  s += '<text class="phead" x="8" y="' + (TOP - 9) + '">College</text>' +
    '<text class="phead" x="' + (X0 - 26) + '" y="' + (TOP - 9) + '" text-anchor="end">' + m.test + ' score</text>' +
    '<text class="phead" x="' + AX + '" y="' + (TOP - 9) + '">Admits, of 10</text>' +
    '<text class="phead" x="' + CX + '" y="' + (TOP - 9) + '">Cases</text>';
  if (!n) s += '<text class="pnone" x="' + X0 + '" y="' + (TOP + 22) + '">No colleges on this list yet.</text>';
  m.rows.forEach(function (x, k) {
    var c = x.c, L = x.L, y = TOP + k * RH, cy = y + RH / 2 - 1, name = str(c.name) || 'Unnamed college';
    var nat = obj(obj(c.cases).national), ownP = obj(obj(c.cases).own);
    var a = num(nat.admitted) || 0, d = num(nat.denied) || 0, w = num(nat.waitlisted) || 0, nn = num(nat.n) || 0, on = num(ownP.n) || 0;
    var rate = num(c.admit_rate);
    var say = name + '. ' + stateText(L) + '.' + (L.steady === false ? ' On the edge.' : '') +
      (x.has ? ' Middle ' + m.test + ' range ' + x.lo + ' to ' + x.hi + '.' : ' No published range.') +
      (rate !== null ? ' Admits ' + inHundred(rate) + '.' : '') +
      (c.cases ? ' National cases ' + nn + (nn ? ': ' + a + ' admitted, ' + d + ' denied, ' + w + ' waitlisted' : '') + '. Your school ' + on + '.' : '') + ' Open the details.';
    s += '<g class="prow pr-' + x.g + '" data-act="open-receipt" data-i="' + x.i + '" tabindex="0" role="button" aria-label="' + esc(say) + '">';
    s += '<title>' + esc(name) + '</title><rect class="phit" x="1" y="' + (y + 1) + '" width="' + (W - 2) + '" height="' + (RH - 2) + '" rx="7"/>';
    s += shape(x.g, ' x="8" y="' + (y + 5) + '"');
    s += '<text class="pname" x="32" y="' + (y + 17) + '">' + esc(clip(name, 27)) + '</text>';
    s += '<text class="plabel" x="32" y="' + (y + 31) + '">' + esc(stateText(L) + (L.steady === false ? ' · on the edge' : '')) + '</text>';
    if (x.has) {
      var x0 = sx(x.lo), x1 = Math.max(sx(x.hi), x0 + 8), top = cy - 8, bot = cy + 8;
      if (x.g === 'reach') {
        var e = Math.min(7, (x1 - x0) / 2);
        s += '<polygon class="pbar" points="' + [p(x0) + ',' + cy, p(x0 + e) + ',' + top, p(x1 - e) + ',' + top, p(x1) + ',' + cy, p(x1 - e) + ',' + bot, p(x0 + e) + ',' + bot].join(' ') + '"/>';
      } else {
        s += '<rect class="pbar' + (x.g === 'cant_say' ? ' pbar-open' : '') + '" x="' + p(x0) + '" y="' + top + '" width="' + p(x1 - x0) + '" height="16" rx="' + (x.g === 'target' ? 8 : 1) + '"/>';
      }
    } else {
      s += '<rect class="pband" x="' + X0 + '" y="' + (cy - 9) + '" width="' + (X1 - X0) + '" height="18" rx="3" fill="url(#pichatch)"/>' +
        '<text class="pbandt" x="' + ((X0 + X1) / 2) + '" y="' + (cy + 4) + '" text-anchor="middle">' +
        (x.g === 'outside_data' ? 'outside our data' : 'no published ' + (m.useAct ? 'ACT ' : '') + 'range') + '</text>';
    }
    if (rate !== null) {
      var fill = rate > 0 ? Math.max(1, Math.round(rate * 10)) : 0;
      for (var i = 0; i < 10; i++) s += '<circle class="' + (i < fill ? 'pd-on' : 'pd-off') + '" cx="' + (AX + 4 + i * 9.4) + '" cy="' + cy + '" r="3.3"/>';
    } else if (x.g !== 'outside_data') s += '<text class="pnone" x="' + AX + '" y="' + (cy + 4) + '">not published</text>';
    if (nn > 0) {
      [[a, 'a', -9], [d, 'd', 0], [w, 'w', 9]].forEach(function (q) {
        var k2 = Math.min(q[0], 11), yy = cy + q[2];
        for (var j = 0; j < k2; j++) {
          var xx = CX + 3 + j * 6.6;
          s += q[1] === 'w' ? '<rect class="pc-w" x="' + p(xx - 2.2) + '" y="' + p(yy - 2.2) + '" width="4.4" height="4.4" transform="rotate(45 ' + p(xx) + ' ' + yy + ')"/>'
            : '<circle class="pc-' + q[1] + '" cx="' + p(xx) + '" cy="' + yy + '" r="' + (q[1] === 'a' ? 2.7 : 2.2) + '"/>';
        }
        if (q[0] > 11) s += '<text class="pplus" x="' + p(CX + 3 + 11 * 6.6) + '" y="' + (yy + 3) + '">+</text>';
      });
    } else if (c.cases) s += '<text class="pnone" x="' + CX + '" y="' + (cy + 4) + '">none</text>';
    if (on > 0) s += '<circle class="pring" cx="' + (W - 14) + '" cy="' + cy + '" r="6"/>';
    s += '</g>';
  });
  if (m.base !== null && m.score !== null && m.base !== m.score) {
    s += '<line class="pline-base" x1="' + p(sx(m.base)) + '" x2="' + p(sx(m.base)) + '" y1="' + (TOP - 4) + '" y2="' + (H - 4) + '"/>';
  }
  if (m.score !== null) {
    var lx = sx(m.score), txt = (o.whatIf ? 'What if ' : 'Student ') + m.score, tw = txt.length * 7.4 + 14, tx = Math.max(X0 + tw / 2, Math.min(X1 - tw / 2 + 30, lx));
    s += '<g class="pstudent" aria-hidden="true"><line class="pline" x1="' + p(lx) + '" x2="' + p(lx) + '" y1="16" y2="' + (H - 4) + '"/>' +
      '<rect class="ptagbg" x="' + p(tx - tw / 2) + '" y="1" width="' + p(tw) + '" height="19" rx="9.5"/>' +
      '<text class="ptag" x="' + p(tx) + '" y="15" text-anchor="middle">' + esc(txt) + '</text></g>';
  }
  return s + '</svg>';
}
/* ---------- Level 1: rings. Distance from the centre = how far the student is from the people admitted there. ---------- */
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
    '<text class="rmet" x="' + CX + '" y="' + (CY + 25) + '" text-anchor="middle">Student' + (score !== null ? ' ' + score : '') + '</text></g>';
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
    var kind = arr(n.kinds).map(obj).filter(function (q) { return q.nearest === true; })[0];
    if (kind) out.push({text: 'Kind: ' + clip(str(kind.name), 30), kind: 'kind'});
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
  s += '<g class="rcentre" aria-hidden="true"><circle class="rme" cx="0" cy="0" r="11"/><text class="rmet" x="0" y="-19" text-anchor="middle">Student' + (score !== null ? ' ' + score : '') + '</text></g>';
  if (!m.n) s += '<text class="pnone" x="0" y="-50" text-anchor="middle">No colleges on this list yet.</text>';
  m.nodes.forEach(function (q) {
    var x = q.row, name = str(x.c.name) || 'Unnamed college', nn = x.n || {}, dir = q.right ? 1 : -1, anchor = q.right ? 'start' : 'end';
    var kind = arr(nn.kinds).map(obj).filter(function (k) { return k.nearest === true; })[0];
    var say = name + '. ' + stateText(x.L) + '. ' + (x.n ? str(nn.text) + ' ' : '') +
      (kind ? 'Nearest kind of admitted student: ' + str(kind.name) + '. ' : '') +
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
var PIC_VIEWS = [['ranges', 'Score ranges'], ['rings', 'Rings'], ['map', 'Mind map']];
function picView(opts) {
  var v = str(obj(opts).view);
  return PIC_VIEWS.some(function (x) { return x[0] === v; }) ? v : 'ranges';
}
function renderPictureCard(result, opts) {
  var m = pictureModel(result, opts), view = picView(opts), body, legend;
  var head = '<div class="pic-head"><h2>Where this student stands</h2>' +
    (m.score === null && view === 'ranges' ? '<span class="quiet">No test score entered, so there is no line.</span>' : '') +
    '<div class="pic-toggle" role="group" aria-label="Which picture">' + PIC_VIEWS.map(function (v) {
      return '<button type="button" class="pick small" data-act="pic-view" data-view="' + v[0] + '" aria-pressed="' + (v[0] === view ? 'true' : 'false') + '">' + esc(v[1]) + '</button>';
    }).join('') + '</div></div>';
  if (view === 'rings') {
    body = renderRings(result);
    legend = '<ul class="legend" aria-label="How to read the rings">' +
      '<li><span class="lg-centre"></span>the student, at the centre</li>' +
      '<li>nearer the centre: more like the people admitted there</li>' +
      '<li><span class="lg-hollow"></span>hollow: too few cases, rough</li>' +
      '<li><span class="lg-dashed"></span>outer ring: cannot be placed</li>' +
      '<li class="lg-tip">Press a dot to see why. Distance is not the label.</li></ul>';
  } else if (view === 'map') {
    body = renderMindMap(result, num(obj(opts).focus));
    legend = '<ul class="legend" aria-label="How to read the mind map">' +
      '<li><span class="lg-centre"></span>the student, in the middle</li>' +
      '<li>a branch per label, a node per college</li>' +
      '<li><span class="lg-leaf"></span>under each college: its nearest kind of admitted student and its nearest admitted cases</li>' +
      '<li class="lg-tip">Press a college to see why.</li></ul>';
  } else {
    body = renderPicture(result, opts);
    legend = '<ul class="legend" aria-label="How to read the picture">' +
      '<li><span class="lg-bar"></span>the college\'s middle score range</li>' +
      '<li><span class="lg-line"></span>the student\'s score</li>' +
      '<li><i class="cd cd-admitted"></i>admitted <i class="cd cd-denied"></i>denied <i class="cd cd-waitlisted"></i>waitlisted, national cases</li>' +
      '<li><span class="lg-ring"></span>your school has cases</li>' +
      '<li class="lg-tip">Press a row to see why.</li></ul>';
  }
  return '<div class="panel pic-card">' + head + '<div class="pic-scroll">' + body + '</div>' + legend + '</div>';
}

/* ---------- Level 1: the three levers ---------- */
function ladderLines(ladder) {
  var seen = {}, out = [], maxPts = 0, kind = 'SAT';
  arr(ladder).map(obj).forEach(function (st) {
    var moves = arr(st.moves).map(obj), pts = num(st.points);
    if (pts !== null && pts > maxPts) maxPts = pts;
    if (str(st.kind)) kind = str(st.kind);
    if (!moves.length || pts === null) return;
    var sig = moves.map(function (mv) { return str(mv.name) + '>' + str(mv.to); }).join('|');
    if (seen[sig]) return;
    seen[sig] = 1;
    out.push(pts + ' more ' + plural(pts, 'point', 'points') + ' moves ' + moves.length + ' ' + plural(moves.length, 'college', 'colleges') + ': ' +
      moves.slice(0, 3).map(function (mv) { return shortName(mv.name) + ', ' + str(mv.from) + ' to ' + str(mv.to); }).join('; ') +
      (moves.length > 3 ? '; and ' + (moves.length - 3) + ' more' : '') + '.');
  });
  if (!out.length && maxPts) out.push('Up to ' + maxPts + ' more ' + kind + ' points moves no college on this list.');
  return out.slice(0, 2);
}
/* slider: {disabled, reason, min, max, step, value, shown} */
function renderLeversCard(result, slider, canAdd) {
  var r = obj(result), lv = obj(r.levers), ll = obj(lv.list), sl = obj(slider);
  var nSug = arr(obj(r.balance).suggestions).length || num(ll.suggestions) || 0;
  var h = '<div class="panel levers"><h2>What could change this</h2><ol class="lever-list">';
  h += '<li><h3><span class="lv-n">1</span>The list</h3><p>' + esc(str(ll.text) || 'The first thing you can change is the list itself.') + '</p>' +
    (nSug ? '<button type="button" class="btn small" data-act="show-suggestions">Show ' + nSug + ' suggested ' + plural(nSug, 'college', 'colleges') + '</button>'
          : '<p class="quiet small">No suggested colleges for this list.</p>') + '</li>';
  h += '<li><h3><span class="lv-n">2</span>The score</h3>';
  if (sl.disabled || num(sl.value) === null) {
    h += '<p class="quiet">' + esc(str(sl.reason) || 'No test score to vary.') + '</p>';
  } else {
    h += '<label class="whatif-l" for="whatif">What if the score were…</label><div class="whatif-row">' +
      '<input type="range" id="whatif" min="' + esc(sl.min) + '" max="' + esc(sl.max) + '" step="' + esc(sl.step) + '" value="' + esc(sl.value) + '">' +
      '<output id="whatif-out" for="whatif">' + esc(sl.shown) + '</output>' +
      '<button type="button" class="btn small" data-act="reset-score" id="whatif-reset" disabled>Reset</button></div>' +
      '<p class="hint" id="whatif-hint" role="status"></p>';
    var lines = ladderLines(lv.score_ladder);
    if (lines.length) h += '<ul class="ladder">' + lines.map(function (t) { return '<li>' + esc(t) + '</li>'; }).join('') + '</ul>';
  }
  h += '</li>';
  h += '<li><h3><span class="lv-n">3</span>What each college says matters</h3>' +
    '<button type="button" class="btn small" data-act="open-says">See what the colleges say</button></li></ol>';
  if (str(lv.note)) h += '<p class="quiet small lv-note">' + esc(lv.note) + '</p>';
  return h + '</div>';
}
function suggestionCard(s, canAdd) {
  s = obj(s);
  var facts = [];
  if (num(s.admit_rate) !== null) facts.push('Admits ' + inHundred(s.admit_rate));
  if (num(s.sat25) !== null && num(s.sat75) !== null) facts.push('Middle score range ' + num(s.sat25) + ' to ' + num(s.sat75));
  if (num(s.cost_year) !== null) facts.push('Sticker cost ' + moneyAbout(s.cost_year) + ' a year');
  if (str(s.tuition_note)) facts.push(str(s.tuition_note));
  return '<li class="sugg"><div class="sugg-head"><span class="sugg-name">' + esc(str(s.name) || 'A college') + '</span>' +
    (s.would_be ? '<span class="sugg-would">Would be ' + badgeFor(s.would_be) + '</span>' : '') + '</div>' +
    (facts.length ? '<ul class="facts">' + facts.map(function (f) { return '<li>' + esc(f) + '</li>'; }).join('') + '</ul>' : '') +
    (str(s.why) ? '<p class="why"><b>Why:</b> ' + esc(s.why) + '</p>' : '') +
    (canAdd !== false && str(s.name) ? '<button type="button" class="btn small" data-act="add-suggestion" data-name="' + esc(s.name) + '">Add to list</button>' : '') + '</li>';
}
function panelHead(kicker, title) {
  return '<header class="rc-head"><div><p class="rc-kicker">' + esc(kicker) + '</p><h2 id="receipt-title">' + esc(title) + '</h2></div>' +
    '<button type="button" class="btn" data-act="close-panel">Close</button></header>';
}
function renderSuggestionsPanel(balance, canAdd) {
  var s = arr(obj(balance).suggestions), w = warningTexts(obj(balance).warnings);
  return panelHead('The list', 'Suggested colleges') + '<section class="rc-sec">' +
    (w.length ? '<ul class="more-warn open">' + w.map(function (x) { return '<li>' + esc(x) + '</li>'; }).join('') + '</ul>' : '') +
    (s.length ? '<ul class="suggs">' + s.map(function (x) { return suggestionCard(x, canAdd); }).join('') + '</ul>'
              : '<p class="state-box">No suggested colleges for this list.</p>') +
    (canAdd === false ? '<p class="quiet small">Shared preview: adding colleges is switched off.</p>' : '') + '</section>';
}
function renderFootLinks(result, mode) {
  var n = arr(obj(obj(result).reader).notes).length;
  var links = [['open-about', 'About this screen'], ['open-essay', 'Essay notes (' + n + ')'], ['open-how', 'How this was made']];
  if (mode !== 'static') links.push(['open-case', 'Add a finished case']);
  links.push(['print', 'Print for the family'], ['ask-chance', "What is the student's chance?"]);
  return links.map(function (l) {
    return '<button type="button" class="linkbtn" data-act="' + l[0] + '"' + (l[0] === 'ask-chance' ? ' aria-expanded="false" aria-controls="chance-answer"' : '') + '>' + esc(l[1]) + '</button>';
  }).join('<span class="sep" aria-hidden="true">·</span>');
}
function renderChanceAnswer(refusals) {
  return '<p><b>This screen does not give odds.</b> ' + esc(str(arr(refusals)[0]) || 'No personal odds of admission are given.') + '</p>' +
    '<p class="quiet">The picture shows where the score sits against each college. The finished cases show what happened to students like this one.</p>' +
    '<button type="button" class="btn small" data-act="see-cases">Show the finished cases</button>';
}

/* ---------- Level 2: the drill-in, four tabs ---------- */
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
  var r = rangeInfo(c);
  if (r.lo === null || r.hi === null) {
    return '<span class="range none"><span class="range-cap">No score range published</span></span>';
  }
  function pc(v) { return Math.max(0, Math.min(100, (v - r.min) / (r.max - r.min) * 100)); }
  var where = '';
  if (r.score !== null) where = r.score < r.lo ? 'below the range' : (r.score >= r.hi ? 'at or above the top of the range' : 'inside the range');
  var aria = 'College\'s middle ' + r.test + ' range ' + r.lo + ' to ' + r.hi + '. ' +
    (r.score !== null ? 'Student\'s score ' + r.score + ', ' + where + '.' : 'No student score to mark.');
  var left = pc(r.lo), width = Math.max(1.5, pc(r.hi) - pc(r.lo));
  return '<span class="range" role="img" aria-label="' + esc(aria) + '">' +
    '<span class="track"><span class="band" style="left:' + left.toFixed(1) + '%;width:' + width.toFixed(1) + '%"></span>' +
    (r.score !== null ? '<span class="me" style="left:' + pc(r.score).toFixed(1) + '%"></span>' : '') + '</span>' +
    '<span class="range-cap">Middle range <b>' + r.lo + ' to ' + r.hi + '</b>' +
    (r.score !== null ? ' · student <b>' + r.score + '</b>, ' + esc(where) : ' · no student score') +
    (/converted/i.test(r.kind) ? ' (ACT converted to SAT)' : '') + '</span></span>';
}
function renderWhyDetails(c) {
  c = obj(c);
  var L = obj(c.label), g = groupOf(L.state), inp = obj(L.inputs), h = '';
  var NAMES = {sat25: "College's 25th percentile SAT", sat75: "College's 75th percentile SAT",
               act25: "College's 25th percentile ACT", act75: "College's 75th percentile ACT", admit_rate: 'Official admit rate'};
  var rows = [['Student&#39;s score', num(L.score_used) !== null ? esc(num(L.score_used) + (str(L.score_kind) ? ' (' + str(L.score_kind) + ')' : '')) : 'No score to compare']];
  Object.keys(inp).forEach(function (k) {
    var v = inp[k];
    rows.push([esc(NAMES[k] || cap(k.replace(/_/g, ' '))),
      k === 'admit_rate' ? esc(rateFull(v)) : (v === null || v === undefined || typeof v === 'object' ? 'not published' : esc(v))]);
  });
  h += '<h4>The numbers used</h4><table class="kv"><tbody>' + rows.map(function (r) {
    return '<tr><th scope="row">' + r[0] + '</th><td>' + r[1] + '</td></tr>';
  }).join('') + '</tbody></table>';
  if (str(c.source)) h += '<p class="src">Numbers from: ' + esc(c.source) + '</p>';
  var nu = arr(L.not_used).map(str).filter(Boolean);
  h += '<h4>What was not used</h4>' + (nu.length
    ? '<p class="not-used">' + nu.map(function (x) { return '<span class="pill">' + esc(x) + '</span>'; }).join('') +
      '<span class="quiet"> None of these changed the label.</span></p>'
    : '<p class="quiet">Nothing was listed.</p>');
  var cv = arr(L.caveats).map(str).concat(arr(c.flags).map(function (f) { return typeof f === 'string' ? f : str(obj(f).text); })).filter(Boolean);
  h += '<h4>Caveats</h4>' + (cv.length
    ? '<ul class="plain">' + cv.map(function (x) { return '<li>' + esc(x) + '</li>'; }).join('') + '</ul>'
    : '<p class="quiet">None recorded for this college.</p>');
  var fl = arr(L.flips).map(obj);
  h += '<h4>What would flip it</h4>';
  if (fl.length) {
    h += '<ul class="flips">' + fl.map(function (f) {
      return '<li><span>' + esc(cap(f.cause)) + '</span><span class="becomes">becomes ' + badgeFor(f.to) + '</span></li>';
    }).join('') + '</ul>';
  } else if (L.state === 'reach_for_everyone') {
    h += '<p class="quiet">Nothing in this student\'s profile changes it. The label comes from the college\'s admit rate, not from the score.</p>';
  } else if (g === 'cant_say') {
    h += '<p class="quiet">Not tested, because there is no label to test.</p>';
  } else {
    h += '<p class="quiet">Nothing small changes it: a score 30 points lower or higher, or an admit rate 5 points lower, gives the same label.</p>';
  }
  var pubs = arr(L.publishers).map(obj);
  h += '<h4>What each publisher would call it</h4>';
  if (pubs.length) {
    h += '<ul class="pubs">' + pubs.map(function (p) {
      var same = p.label && groupOf(p.label) === g;
      return '<li><span class="pub-name">' + esc(p.name) + '</span>' +
        (p.label ? badgeFor(p.label) : '<span class="quiet">could not label</span>') +
        (p.label ? '<span class="pub-cmp ' + (same ? 'same' : 'differs') + '">' + (same ? 'same as ours' : 'differs from ours') + '</span>' : '') + '</li>';
    }).join('') + '</ul>';
  } else {
    h += '<p class="quiet">No publisher\'s rulebook could label this one.</p>';
  }
  return h;
}
function renderWhyTab(c) {
  c = obj(c);
  var L = obj(c.label), g = groupOf(L.state);
  var h = (g === 'outside_data' ? '' : '<div class="tab-pic">' + rangeBar(c) + '</div>') +
    '<p class="rule">' + badge(L) + '<span>' + esc(str(L.rule_text) || 'No rule text was recorded.') + '</span></p>';
  var marks = [];
  if (L.steady === false) marks.push('<span class="mark m-edge">On the edge</span>');
  if (L.publishers_disagree === true) marks.push('<span class="mark m-pub">Publishers disagree</span>');
  if (marks.length) h += '<p class="marks">' + marks.join('') + '</p>';
  if (g !== 'outside_data') h += '<details class="more"><summary>Details</summary>' + renderWhyDetails(c) + '</details>';
  return h;
}
function outcomeKind(o) {
  var s = str(o).toLowerCase();
  return s === 'admitted' || s === 'denied' || s === 'waitlisted' ? s : 'other';
}
function outcomeTag(o) {
  return '<span class="outcome"><i class="cd cd-' + outcomeKind(o) + '" aria-hidden="true"></i>' + esc(cap(str(o).toLowerCase()) || 'Not recorded') + '</span>';
}
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
    ['Case', function (e) { return esc(e.case_id) + (e.shared ? ' <span class="tag tag-self">shared</span>' : ''); }, function (e) { return str(e.case_id); }],
    ['Score', function (e) {
      return num(e.sat) !== null ? 'SAT ' + num(e.sat) : (num(e.act) !== null ? 'ACT ' + num(e.act) : 'none sent');
    }, function () { return 'x'; }],
    ['Major', function (e) { return esc(majorText(e.major || e.major_group)); }, function (e) { return str(e.major || e.major_group); }],
    ['Hooks', function (e) { return esc(hookText(e.hooks)); }, function (e) { return hookText(e.hooks); }],
    ['Home', function (e) { return esc(e.home_state); }, function (e) { return str(e.home_state); }],
    ['Activities', function (e) {
      if (str(e.activities_note)) return esc(e.activities_note);
      return num(e.activities_rating) !== null ? 'rated ' + num(e.activities_rating) : '';
    }, function (e) { return str(e.activities_note) || (num(e.activities_rating) !== null ? 'x' : ''); }],
    ['Essay theme', function (e) { return esc(e.essay_theme); }, function (e) { return str(e.essay_theme); }],
    ['Year', function (e) { return esc(e.cycle_year); }, function (e) { return str(e.cycle_year); }],
    ['Outcome', function (e) { return outcomeTag(e.outcome); }, function () { return 'x'; }],
    ['Distance', function (e) { return num(e.distance) !== null ? f2(num(e.distance)) : ''; }, function (e) { return num(e.distance) !== null ? 'x' : ''; }]
  ].filter(function (col) { return ex.some(function (e) { return col[2](e) !== ''; }); });
  return '<div class="table-wrap"><table class="cases-table"><thead><tr>' +
    cols.map(function (col) { return '<th scope="col">' + col[0] + '</th>'; }).join('') + '</tr></thead><tbody>' +
    ex.map(function (e) {
      return '<tr>' + cols.map(function (col) { return '<td>' + col[1](e) + '</td>'; }).join('') + '</tr>';
    }).join('') + '</tbody></table></div>';
}
function renderPool(pool, cases, which) {
  var cs = obj(cases), p = obj(pool), need = num(cs.needed) || 15, n = num(p.n) || 0;
  var a = num(p.admitted) || 0, d = num(p.denied) || 0, w = num(p.waitlisted) || 0;
  var h = '<div class="pool pool-' + which + '"><h4>' + (which === 'own' ? 'Your school' : 'National') + '</h4>' +
    (which === 'own' ? (p.verified === false ? '<span class="tag tag-self">Not verified</span>' : '<span class="tag tag-verified">Verified by a counselor</span>')
                     : (p.verified === true ? '<span class="tag tag-verified">Verified</span>' : '<span class="tag tag-self">Self-reported, not verified</span>'));
  if (!pool || p.status === 'none' || n === 0) {
    h += '<p class="big-n zero">0</p><p class="state-box">No finished cases.</p>';
  } else {
    h += '<p class="big-n">' + n + '<span> finished ' + plural(n, 'case', 'cases') + '</span></p>';
    if (p.status === 'not_enough') h += '<p class="state-box"><b>Not enough cases: ' + n + ' of the ' + need + ' needed.</b></p>';
    h += dotGrid(a, d, w) + '<p class="out-line"><span><i class="cd cd-admitted" aria-hidden="true"></i><b>' + a + '</b> admitted</span>' +
      '<span><i class="cd cd-denied" aria-hidden="true"></i><b>' + d + '</b> denied</span>' +
      '<span><i class="cd cd-waitlisted" aria-hidden="true"></i><b>' + w + '</b> waitlisted</span></p>';
  }
  if (which === 'national') {
    h += '<p class="beside">Official admit rate: <b>' + esc(rateFull(cs.official_admit_rate)) + '</b>.' +
      (num(cs.overcount) !== null ? ' People who post are admitted about <b>' + esc(f1(num(cs.overcount))) + ' times</b> as often as applicants overall.' : '') + '</p>';
  }
  if (pool) {
    var m = arr(p.matched_on).map(str).filter(Boolean), rx = arr(p.relaxed).map(str).filter(Boolean);
    h += '<details class="more"><summary>Details</summary>' +
      (str(p.source) ? '<p class="pool-src">' + esc(p.source) + '</p>' : '') +
      '<dl class="match"><dt>Matched on</dt><dd>' + (m.length ? esc(m.join('; ')) : 'nothing recorded') + '</dd>' +
      '<dt>Relaxed to find more</dt><dd>' + (rx.length ? esc(rx.join('; ')) : 'nothing') + '</dd></dl>' +
      (n > 0 ? examplesTable(p.examples) : '') +
      (which === 'national' && str(cs.caveat) ? '<p class="quiet small">' + esc(cs.caveat) + '</p>' : '') + '</details>';
  }
  return h + '</div>';
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
  h += '<p class="quiet small">Essay comparison: ' + esc(report.status) +
    (str(report.note) ? '. ' + esc(report.note) : '') + '</p>';
  if (matches.length) h += '<h4>Similar essay content</h4><ol>' + matches.map(function (r) {
    return '<li>' + esc(r.case_id) + ' — ' + (r.text_kind === 'full_essay' ? 'full essay' : 'theme summary') +
      ', content distance ' + esc(r.distance) + ' (lower is closer)</li>';
  }).join('') + '</ol>';
  return h;
}
function renderCasesTab(c) {
  c = obj(c);
  if (!c.cases) return '<p class="state-box">No finished cases.</p>';
  var cs = obj(c.cases);
  return '<div class="pools">' + renderPool(cs.own, cs, 'own') + renderPool(cs.national, cs, 'national') + '</div>' +
    '<p class="quiet small">Two separate pools, never added together. These are examples, not odds.</p>' + renderHolistic(c);
}
var LEVER_ICON = {
  score: '<path d="M8 1.5 12 6H9.3v4H12l-4 4.5L4 10h2.7V6H4z"/>',
  says: '<path d="M2 3h12v8H7.5L4 14v-3H2z"/>',
  sent_scores: '<path fill-rule="evenodd" d="M3 1.5h7l3 3v10H3zm2 5v1.4h6V6.5zm0 3v1.4h6V9.5z"/>',
  residency: '<path d="M8 1.5 14.5 7H13v7.5H9.5v-4h-3v4H3V7H1.5z"/>'
};
var LEVER_NAME = {score: 'Score', says: 'What the college weighs', sent_scores: 'Who sent scores', residency: 'Where applicants live'};
function sourceLink(url, text) {
  var u = safeUrl(url);
  return u ? '<a href="' + esc(u) + '" target="_blank" rel="noopener noreferrer">' + esc(text || 'Source') + '</a>' : '';
}
function renderLeversTab(c) {
  var lv = arr(obj(c).levers).map(obj).filter(function (l) { return str(l.text); });
  if (!lv.length) return '<p class="state-box">Nothing on file that would change this label.</p>';
  return '<ul class="clevers">' + lv.map(function (l) {
    var k = str(l.kind), link = sourceLink(l.source_url, 'source');
    return '<li><svg class="lv-icon" viewBox="0 0 16 16" width="22" height="22" aria-hidden="true" focusable="false">' + (LEVER_ICON[k] || LEVER_ICON.says) + '</svg>' +
      '<div><p class="lv-kind">' + esc(LEVER_NAME[k] || cap(k.replace(/_/g, ' '))) + '</p><p>' + esc(l.text) + (link ? ' <span class="claim-meta">' + link + '</span>' : '') + '</p></div></li>';
  }).join('') + '</ul><p class="quiet small">The same written rule and the college\'s own published statements. Not predictions.</p>';
}
function sayLine(s) {
  s = obj(s);
  var kb = s.kb ? obj(s.kb) : null, st = kb ? str(kb.status).toLowerCase() : '', link = sourceLink(s.source_url, 'source');
  var meta = [esc(str(s.year)), link].filter(Boolean).join(' · ');
  return '<li><p class="claim">' + esc(s.text) + '</p><p class="claim-meta">' + meta +
    (st === 'confirmed' ? ' <span class="kb kb-ok"><svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><path d="M6.2 11.3 2.9 8l-1.2 1.2 4.5 4.5L14.300 5.600 13.100 4.400z"/></svg>confirmed in the knowledge base</span>'
      : (st === 'not confirmed' ? ' <span class="kb kb-no">not confirmed</span>' : '')) + '</p></li>';
}
function renderSaysTab(c) {
  c = obj(c);
  var says = arr(c.says), myths = arr(c.myths).map(obj), h = '';
  if (!says.length && !myths.length) h += '<p class="state-box">We hold no form from this college, so nothing is quoted.</p>';
  if (says.length) {
    h += '<ul class="claims">' + says.slice(0, 3).map(sayLine).join('') + '</ul>';
    if (says.length > 3) h += '<details class="more"><summary>' + (says.length - 3) + ' more ' + plural(says.length - 3, 'statement', 'statements') + '</summary><ul class="claims">' + says.slice(3).map(sayLine).join('') + '</ul></details>';
  }
  if (myths.length) {
    h += '<details class="more"><summary>Common beliefs, checked (' + myths.length + ')</summary><ul class="claims">' + myths.map(function (m) {
      var link = sourceLink(m.source_url, 'source');
      return '<li><p class="belief">Belief: ' + esc(m.belief) + '</p><p class="claim">' + esc(m.college_says) + '</p>' +
        '<p class="claim-meta">' + esc(str(m.year)) + (str(m.year) && link ? ' · ' : '') + link + '</p></li>';
    }).join('') + '</ul></details>';
  }
  h += '<p class="cost"><b>Cost.</b> ' + (str(c.cost_note) ? esc(c.cost_note) : 'No cost figure is published for this college.') + '</p>';
  return h;
}
/* ---------- Level 2: who they resemble (closeness) ---------- */
var LEAN_WORD = {closer_to_admitted: 'Closer to the people admitted', closer_to_denied: 'Closer to the people denied', in_between: 'In between'};
var PART_NAME = {score: 'Score', activities: 'Activities rating', major: 'Major group', hooks: 'Hook status', residency: 'Residency', gpa: 'GPA'};
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
  var medoid = {}; arr(n.kinds).map(obj).forEach(function (k) { if (str(k.medoid_case_id)) medoid[str(k.medoid_case_id)] = str(k.kind_id); });
  var counts = {admitted: 0, denied: 0, waitlisted: 0}; drawn.forEach(function (q) { if (counts[q.outcome] !== undefined) counts[q.outcome]++; });
  var say = 'Scatter of ' + drawn.length + ' ' + plural(drawn.length, 'case', 'cases') + ' at this college: score across, activities rating up. ' +
    counts.admitted + ' admitted as circles, ' + counts.denied + ' denied as crosses, ' + counts.waitlisted + ' waitlisted as diamonds. ' +
    (sScore !== null ? (sAct !== null ? 'The student is the star at score ' + sScore + ' and rating ' + sAct + '. ' : 'The student is the vertical line at score ' + sScore + '; no activities rating was given. ') : 'The student has no score, so is not drawn. ') +
    (arr(n.kinds).length ? 'The medoid of each kind of admitted student is ringed and labelled. ' : '') +
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
  return '<ul class="pbars" aria-label="How close the student is to the nearest admitted, part by part">' + ps.map(function (q) {
    var d = Math.max(0, Math.min(1, num(q.distance)));
    return '<li><span class="pb-name">' + esc(PART_NAME[str(q.part)] || cap(q.part)) + '</span>' +
      '<span class="pb-track" aria-hidden="true"><span class="pb-fill" style="width:' + Math.round(d * 100) + '%"></span></span>' +
      '<span class="pb-word">' + esc(str(q.text)) + ' <span class="quiet">(' + f2(d) + ')</span></span></li>';
  }).join('') + '</ul>';
}
function renderResembleTab(c) {
  c = obj(c);
  if (!c.closeness) return '<p class="state-box">No closeness data for this college.</p>';
  var cl = obj(c.closeness), n = obj(cl.national), o = obj(cl.own), st = obj(cl.student), ok = n.status === 'ok', h = '';
  var lean = str(n.lean), k = num(cl.neighbours) || 7;
  var head = ok ? leanWord(lean) : (n.status === 'not_enough' ? 'Not enough cases to say' : (n.status === 'cant_say' ? "Can't say" : 'No cases'));
  h += '<div class="lean lean-' + esc(ok ? lean : str(n.status)) + '"><p class="lean-h">' + esc(head) + '</p>';
  if (str(n.text)) h += '<p>' + esc(n.text) + '</p>';
  if (num(n.n_admitted) !== null) {
    h += '<p class="out-line"><span><i class="cd cd-admitted" aria-hidden="true"></i><b>' + (num(n.n_admitted) || 0) + '</b> admitted</span>' +
      '<span><i class="cd cd-denied" aria-hidden="true"></i><b>' + (num(n.n_denied) || 0) + '</b> denied</span>' +
      '<span><i class="cd cd-waitlisted" aria-hidden="true"></i><b>' + (num(n.n_waitlisted) || 0) + '</b> waitlisted</span>' +
      '<span class="quiet">national, self-reported, with a score</span></p>';
  }
  if (num(n.d_admitted) !== null && num(n.d_denied) !== null) {
    h += '<p class="small">Distance to the ' + k + ' nearest admitted <b>' + f2(num(n.d_admitted)) + '</b>, to the ' + k + ' nearest denied <b>' + f2(num(n.d_denied)) + '</b>' +
      (num(n.gap) !== null ? ' (gap ' + f2(num(n.gap)) + ')' : '') + '. 0 is the same person; 1 is as far as it gets.</p>';
  }
  if (ok) {
    var flips = arr(n.flips).map(obj).filter(function (f) { return str(f.cause); });
    h += '<p class="small">' + (n.steady === true ? '<b>Steady.</b> The same answer with 5 or 10 nearest cases and with the score 30 points either way.'
      : '<b>On the edge.</b> ' + esc(flips.map(function (f) { return cap(f.cause) + ' gives "' + leanWord(f.to).toLowerCase() + '"'; }).join('; ')) + '.') + '</p>';
  }
  h += '</div>';
  if (ok || n.status === 'not_enough') {
    var sc = renderScatter(n, st);
    if (sc) {
      h += '<h4>Every case here, by score and activities rating</h4>' + sc +
        '<ul class="legend" aria-label="How to read the scatter"><li><i class="cd cd-admitted"></i>admitted</li><li><i class="cd cd-denied"></i>denied</li><li><i class="cd cd-waitlisted"></i>waitlisted</li>' +
        '<li><span class="lg-hollow"></span>a kind\'s medoid</li><li><span class="lg-star">★</span>the student</li></ul>';
    }
    h += '<h4>Close or far, part by part</h4>' + renderPartBars(n.parts);
    var nu = arr(n.not_used).map(str).filter(Boolean);
    if (nu.length) h += '<p class="quiet small">Not used: ' + esc(nu.join('; ')) + '.</p>';
    var kinds = arr(n.kinds).map(obj);
    if (kinds.length) {
      h += '<h4>Kinds of admitted student here</h4><ul class="kinds">' + kinds.map(function (q) {
        return '<li' + (q.nearest === true ? ' class="nearest"' : '') + '><b>' + esc(q.kind_id) + '</b> ' + esc(q.name) +
          ' <span class="quiet">(' + (num(q.size) || 0) + ' ' + plural(num(q.size) || 0, 'case', 'cases') + (num(q.distance) !== null ? ', distance ' + f2(num(q.distance)) : '') + ')</span>' +
          (q.nearest === true ? ' <span class="tag tag-verified">nearest</span>' : '') + '</li>';
      }).join('') + '</ul>';
    }
    h += '<h4>Nearest admitted</h4>' + examplesTable(n.nearest_admitted) + '<h4>Nearest denied</h4>' + examplesTable(n.nearest_denied);
  }
  if (ok) {
    var ch = arr(n.changes).map(obj).filter(function (q) { return str(q.change); });
    h += '<h4>What would bring the student closer</h4>';
    if (ch.length) {
      h += '<ol class="changes">' + ch.map(function (q) {
        return '<li><b>' + esc(q.change) + '.</b> Gap ' + f2(num(q.gap_before) || 0) + ' to ' + f2(num(q.gap_after) || 0) + ', ' + esc(leanWord(q.lean_after).toLowerCase()) + '.' +
          (arr(q.because).length ? '<span class="quiet">Nearest admitted would be ' + esc(arr(q.because).map(str).join(', ')) + '.</span>' : '') + '</li>';
      }).join('') + '</ol>';
    } else h += '<p class="state-box">' + esc(str(n.changes_note) || 'Nothing we can measure here would move this.') + '</p>';
    h += '<p class="quiet small">Only the score, the activities rating and a major the student named are ever varied. Nothing about who the student is.</p>';
  }
  h += '<h4>Your school</h4>';
  if (o.status === 'ok') h += '<p><b>' + esc(leanWord(o.lean)) + '.</b> ' + esc(str(o.text)) + '</p>';
  else h += '<p>' + esc(str(o.text) || 'No finished cases.') + (num(o.n_admitted) !== null ? ' <span class="quiet">(' + (num(o.n_admitted) || 0) + ' admitted, ' + (num(o.n_denied) || 0) + ' denied, ' + (num(o.n_waitlisted) || 0) + ' waitlisted)</span>' : '') + '</p>';
  h += '<p class="quiet small">' + esc(str(cl.caveat) || 'Closeness is a distance to past cases, not a forecast.') + '</p>';
  return h;
}
var TABS = [['why', 'Why this label'], ['cases', 'Cases like this student'], ['resemble', 'Who they resemble'], ['levers', 'What could change it'], ['says', 'What the college says']];
function renderDrill(c, tab) {
  c = obj(c);
  var L = obj(c.label), g = groupOf(L.state), active = TABS.some(function (t) { return t[0] === tab; }) ? tab : 'why';
  var h = '<header class="rc-head"><div><p class="rc-kicker">Check the work</p><h2 id="receipt-title">' + esc(str(c.name) || 'Unnamed college') + '</h2>' +
    badge(L) + '</div><button type="button" class="btn" data-act="close-panel">Close</button></header>';
  if (g === 'outside_data') {
    return h + '<section class="rc-sec">' + renderWhyTab(c) +
      '<p class="state-box">This college is outside our data, so there are no cases, statements or costs to show. Check the spelling, or pick it from the search.</p></section>';
  }
  var body = {why: renderWhyTab(c), cases: renderCasesTab(c), resemble: renderResembleTab(c), levers: renderLeversTab(c), says: renderSaysTab(c)};
  h += '<div class="tabs" role="tablist" aria-label="About this college">' + TABS.map(function (t) {
    return '<button type="button" role="tab" id="tab-' + t[0] + '" data-act="tab" data-tab="' + t[0] + '" aria-controls="pan-' + t[0] +
      '" aria-selected="' + (t[0] === active ? 'true' : 'false') + '">' + esc(t[1]) + '</button>';
  }).join('') + '</div>';
  h += TABS.map(function (t) {
    return '<section class="rc-sec tabpan" role="tabpanel" id="pan-' + t[0] + '" aria-labelledby="tab-' + t[0] + '"' + (t[0] === active ? '' : ' hidden') + '>' + body[t[0]] + '</section>';
  }).join('');
  return h;
}

/* ---------- panels opened from the footer ---------- */
function renderEssay(reader, privacy) {
  var r = obj(reader), pv = obj(privacy), st = str(r.status), h = '<div class="essay">';
  var masked = arr(pv.masked).map(obj).filter(function (m) { return num(m.count); });
  if (pv.blocked === true || st === 'blocked') {
    return h + '<p class="banner">The essay was not read. ' + esc(str(pv.reason) || str(r.reason) || 'It contains text written as instructions to the reader.') +
      ' The labels do not depend on the essay, so they are unchanged.</p></div>';
  }
  if (st === 'off') {
    return h + '<p class="banner">The essay reader is off' + (str(r.reason) ? ': ' + esc(r.reason) : ' (no key is set)') +
      '. Nothing was sent anywhere. The labels do not depend on the essay.</p></div>';
  }
  if (st === 'empty') return h + '<p class="state-box">No essay was entered, so there are no notes.</p></div>';
  if (st === 'error') {
    return h + '<p class="banner">The essay could not be read this time' + (str(r.error) || str(r.reason) ? ': ' + esc(str(r.error) || str(r.reason)) : '') +
      '. The labels do not depend on the essay.</p></div>';
  }
  if (!reader) return h + '<p class="state-box">No essay notes for this run.</p></div>';
  h += '<p class="quiet">Observations only. The essay is never rated and never changes a label.</p>';
  var notes = arr(r.notes).map(obj);
  if (notes.length) {
    h += '<ol class="notes">' + notes.map(function (n) {
      return '<li><p class="note-obs">' + esc(n.observation) + '</p>' +
        (str(n.quote) ? '<blockquote><mark>' + esc(n.quote) + '</mark>' +
          (n.quote_found === true ? '<span class="tag tag-verified">found word for word in the essay</span>' : '') + '</blockquote>' : '') +
        (str(n.question) ? '<p class="note-q"><b>To ask:</b> ' + esc(n.question) + '</p>' : '') + '</li>';
    }).join('') + '</ol>';
  } else {
    h += '<p class="quiet">The reader returned no notes.</p>';
  }
  var d = num(r.dropped) || 0;
  if (d > 0) {
    h += '<p class="dropped">' + d + ' ' + plural(d, 'note was', 'notes were') + ' dropped because ' +
      plural(d, 'its quote was', 'their quotes were') + ' not in the essay.</p>';
  }
  var t = obj(r.tags), themes = arr(t.essay_themes).map(str).filter(Boolean), meta = [];
  if (masked.length) meta.push('Masked before reading: ' + masked.map(function (m) { return num(m.count) + ' ' + str(m.kind) + plural(num(m.count), '', 's'); }).join(', '));
  if (themes.length) meta.push('Themes: ' + themes.join(', '));
  if (t.major_group_agreed === false) meta.push('The two readers disagreed about the major group, so it was not used');
  else if (str(t.major_group)) meta.push('Major group read as ' + majorText(t.major_group) + (t.major_group_agreed === true ? ' by both readers' : ''));
  if (str(r.model)) meta.push('Read by ' + str(r.model) + (str(r.second_model) ? '; major checked separately by ' + str(r.second_model) : ''));
  if (meta.length) h += '<details class="more"><summary>Details</summary><p class="quiet small">' + esc(meta.join('. ')) + '.</p></details>';
  return h + '</div>';
}
function renderClosenessCheck(cc) {
  var c = obj(cc), rows = arr(c.rows).map(obj).filter(function (r) { return str(r.lean); });
  if (!rows.length) return '';
  return '<div class="ccheck"><p><b>Closeness, checked on ' + (num(c.used) || 0) + ' past decisions.</b> Each person was hidden, their lean computed, and the real outcome counted.</p>' +
    '<table class="kv ccheck-t"><thead><tr><th scope="col">Lean</th><th scope="col">Admitted</th><th scope="col">Denied</th></tr></thead><tbody>' +
    rows.map(function (r) { return '<tr><th scope="row">' + esc(leanWord(r.lean)) + '</th><td>' + (num(r.admitted) || 0) + '</td><td>' + (num(r.denied) || 0) + '</td></tr>'; }).join('') +
    '</tbody></table>' + (str(c.caveat) ? '<p class="quiet small">' + esc(c.caveat) + '</p>' : '') + '</div>';
}
function renderHow(steps, checks, prism, privacy, closenessCheck) {
  var ss = arr(steps).map(obj), ch = obj(checks), pr = obj(prism), pv = obj(privacy), h = '<div class="how">';
  if (ss.length) {
    h += '<ol class="steps">' + ss.map(function (s, i) {
      var by = str(s.by);
      return '<li><span class="step-n">' + (i + 1) + '</span><span class="step-name">' + esc(cap(s.step)) + '</span>' +
        '<span class="step-what">' + esc(s.what) + '</span>' +
        '<span class="step-by">' + (by === 'code' || !by ? 'Done by code' : 'Done by the model ' + esc(by)) +
        (num(s.ms) !== null ? ' · ' + esc(duration(s.ms)) : '') + '</span></li>';
    }).join('') + '</ol>';
  } else {
    h += '<p class="quiet">No steps were recorded for this run.</p>';
  }
  var shown = num(ch.sentences_shown), hidden = num(ch.sentences_hidden);
  if (shown !== null || hidden !== null) {
    var reasons = arr(ch.hidden_reasons).map(str).filter(Boolean);
    h += '<p class="checks"><b>' + (shown || 0) + ' ' + plural(shown || 0, 'sentence', 'sentences') + ' shown, ' + (hidden || 0) + ' hidden.</b>' +
      ((hidden || 0) > 0 && reasons.length ? ' Why hidden: ' + esc(reasons.join(' ')) : '') + '</p>';
  }
  if (privacy) {
    var masked = arr(pv.masked).map(obj).filter(function (m) { return num(m.count); });
    h += '<p><b>Privacy:</b> ' + (pv.blocked === true ? 'the essay was held back and not read. ' + esc(pv.reason) : esc(str(pv.note) || 'nothing recorded.')) +
      (masked.length ? ' <span class="quiet">(' + esc(masked.map(function (m) { return num(m.count) + ' ' + str(m.kind); }).join(', ')) + ')</span>' : '') + '</p>';
  }
  if (privacy && verdictMarks(pv)) h += '<p class="verdicts"><b>Essay guard:</b> ' + verdictMarks(pv) + '</p>';
  if (prism) {
    h += '<p><b>Run record:</b> ' + esc(str(pr.status) || 'unknown') + (str(pr.why) ? '. ' + esc(pr.why) : '') +
      (num(pr.records_sent) ? ' ' + num(pr.records_sent) + ' ' + plural(num(pr.records_sent), 'record', 'records') + ' sent.' : '') +
      (str(pr.guardrail) ? ' Essay guard: ' + esc(pr.guardrail) + '.' : '') + '</p>';
  }
  h += renderClosenessCheck(closenessCheck);
  return h + '<p class="quiet small">Labels are set by code from published numbers. A model only reads the essay and returns quotes, which code checks. The counselor decides.</p></div>';
}
/* The essay guard's verdicts: a calm banner when the essay was stopped, small passed marks otherwise. */
function verdictMarks(privacy) {
  return arr(obj(privacy).verdicts).map(obj).filter(function (v) { return str(v.by); }).map(function (v) {
    var stopped = v.blocked === true;
    return '<span class="verdict ' + (stopped ? 'v-stop' : 'v-pass') + '">' + esc(str(v.by).replace(/\s*\(.*\)\s*$/, '')) + ': ' + (stopped ? 'stopped' : 'passed') + '</span>';
  }).join('');
}
function renderStopBanner(privacy, reader) {
  var pv = obj(privacy), vs = arr(pv.verdicts).map(obj);
  var stopped = pv.blocked === true || str(obj(reader).status) === 'blocked' || vs.some(function (v) { return v.blocked === true; });
  if (!stopped) return '';
  var why = str(obj(vs.filter(function (v) { return v.blocked === true; })[0]).detail) || str(obj(vs[0]).detail) || str(pv.reason);
  return '<div class="stopped"><p class="stopped-h">This essay was stopped before any model read it.</p>' +
    '<p class="verdicts">' + verdictMarks(pv) + '<span class="quiet">The labels below are set without the essay, as always.</span></p>' +
    (why ? '<details class="more"><summary>Why</summary><p>' + esc(why) + '</p></details>' : '') + '</div>';
}
/* ---------- about: what this is, a tour with live buttons, the rules it keeps, how it was built ---------- */
/* The method's numbers come from the engine (result.closeness_method); these are the same values, used only when a result predates it. */
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
  s += box(520, 308, 230, 78, ['8. Status gates', 'ok: both groups ≥ ' + (num(m.needed) || 15), 'not enough: either 1 to ' + ((num(m.needed) || 15) - 1) + ' (lean null)', 'none / can\'t say (no score)'], 'al-out');
  s += arrow(270, 347, 252, 347);
  s += box(10, 120, 220, 266, ['Side checks, same maths', '', 'Steady test: rerun with', arr(obj(m.steady).neighbours).join(' and ') + ' nearest, score ±30', '', 'Changes: score +' + arr(m.score_steps).join('/+') + ',', 'rating +' + arr(m.rating_steps).join('/+') + ', a named major;', 'keep if gap rises ≥ ' + gain + ';', 'never hooks, state, GPA', '', 'Kinds: k-medoids, k = ' + (num(kd.k) || 3) + ',', 'admitted cases, seed ' + (num(kd.seed) || ''), '≤ ' + (num(kd.cap) || 300) + ' cases, ' + (num(kd.rounds) || 20) + ' rounds;', 'named from medians only'], 'al-side');
  s += box(10, 400, 740, 90, ['9. Output, all numbers set by code', 'lean + text, d_admitted, d_denied, gap, steady/flips, parts (close or far), not_used, 3 nearest admitted and 3 nearest denied with per-part', 'distances, kinds with the nearest marked, up to 3 changes, up to ' + (num(m.points_cap) || 300) + ' points for the scatter. The reach / target / likely label is untouched.', 'Holds-up check: ' + (num(obj(m.check).n) || 400) + ' past posters, each hidden in turn, counted by lean and real outcome.'], 'al-out');
  s += arrow(385, 386, 385, 398);
  return s + '</svg>';
}
function renderHowBuilt(m) {
  var lib = obj(m.libraries), kd = obj(m.kinds), h = '';
  h += '<h4>How it was built</h4>';
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
function renderAboutPanel(result, mode) {
  var r = obj(result), cs = arr(r.colleges).map(obj), nIn = cs.filter(function (c) { return c.in_data; }).length;
  var withClose = cs.filter(function (c) { return closenessOf(c) && closenessOf(c).status === 'ok'; }).length;
  var first = cs.filter(function (c) { return closenessOf(c) && closenessOf(c).status === 'ok'; })[0];
  function tourBtn(act, text, extra) { return '<button type="button" class="btn small" data-act="' + act + '"' + (extra || '') + '>' + esc(text) + '</button>'; }
  var h = panelHead('Start here', 'About this screen') + '<section class="rc-sec about">';
  h += '<p class="about-lead">A screen for a college counselor in a meeting with a family. Enter one student and the colleges under discussion. ' +
    'Code sets every label, count and number from published data and finished cases. A model only reads the essay, and only after personal details are masked. ' +
    '<b>It never gives a personal chance of admission.</b></p>';
  h += '<h4>A two-minute tour</h4><ol class="tour">';
  h += '<li><b>The first view.</b> Three counters say how many colleges are reach, target and likely, and the one warning that matters most. ' +
    'The picture "Where this student stands" puts every college\'s middle score range on one line with the student\'s score drawn through them.' +
    (cs.length ? '' : ' <span class="quiet">Pick a demo student and press Build the list to see it.</span>') + '</li>';
  h += '<li><b>Rings and the mind map (new today).</b> Two more pictures of the same list. In the rings, the student is at the centre and each college sits as far out as the student is from the people admitted there. ' +
    'The mind map hangs the colleges off three branches and shows, under each, the kind of admitted student they are nearest to and the three nearest admitted cases. ' +
    (cs.length ? tourBtn('tour-rings', 'Show the rings') + ' ' + tourBtn('tour-map', 'Show the mind map') + ' ' + tourBtn('tour-ranges', 'Back to score ranges') : '') + '</li>';
  h += '<li><b>Press a college.</b> Five tabs: why this label (the written rule and its inputs), cases like this student (two pools, never merged), ' +
    'who they resemble (new today), what could change it, and what the college itself says it weighs. ' +
    (first ? tourBtn('tour-resemble', 'Open "' + shortName(first.name) + '", who they resemble', ' data-i="' + cs.indexOf(first) + '"') : '') + '</li>';
  h += '<li><b>The levers.</b> Beside the picture: the list itself (suggested fills), a "what if the score were…" slider that re-labels the list as it moves, and what each college says matters.</li>';
  h += '<li><b>Check the work.</b> "How this was made" lists the five steps, what code did and what a model did, the sentences hidden by checks, and the closeness check table. ' +
    tourBtn('open-how', 'Open "How this was made"') + '</li>';
  h += '<li><b>Ask the forbidden question.</b> "What is the student\'s chance?" in the footer explains why no percentage is given and points at the evidence instead.</li>';
  h += '</ol>';
  h += '<h4>What closeness is, and is not</h4><ul class="plain">' +
    '<li>For each college: does this student look more like the people admitted there, or the people denied? Measured as a <b>distance</b> over score, activities rating, major group, hooks and residency. Nothing else.</li>' +
    '<li>It never reads the essay or activity text, never changes a label, and never becomes a percentage. "Not enough cases" and "can\'t say" are normal answers.</li>' +
    '<li>"What would bring the student closer" only ever tries a higher score, deeper involvement in the activities already listed, or another major the student named. Never hooks, home state or GPA.</li>' +
    '<li>Checked on 400 past posters with each one hidden in turn; the counts are under "How this was made", with the caveat that people who post are admitted far more often than applicants.</li></ul>';
  h += '<h4>What is real and what is invented</h4><ul class="plain">' +
    '<li><b>Real:</b> 300 colleges\' admit rates, score ranges and costs (US Department of Education); what 24 colleges say they weigh (their own Common Data Set); a national pool of self-reported results from public posts, with no names.</li>' +
    '<li><b>Invented, stamped SYNTHETIC:</b> the six demo students and essays, and the school\'s own "verified" cases.</li></ul>';
  if (cs.length) {
    h += '<p class="quiet small">This run: ' + cs.length + ' ' + plural(cs.length, 'college', 'colleges') + ', ' + nIn + ' in our data, ' + withClose + ' with enough cases for closeness.' +
      (mode === 'static' ? ' Shared preview: saved runs, no server.' : '') + '</p>';
  }
  h += '<p>' + tourBtn('open-built', 'How it was built: distance, weights, algorithm, data sources') + '</p>';
  h += '<p class="quiet small">Built on 10 October 2026 at a one-day hackathon. Python standard library and plain HTML, CSS and JavaScript; no build step. Source and tests sit beside this page.</p>';
  return h + '</section>';
}
/* ---------- how it was built: method, libraries, choices, data sources. Not tied to a student. ---------- */
var DATA_SOURCES = [
  {name: 'College Scorecard, US Department of Education', kind: 'Real', files: 'data/colleges/scorecard_top300_admissions.csv',
   what: 'The most recent institution file, cut to 300 colleges.',
   used: ['admit rate, 25th and 75th percentile SAT and ACT: the reach / target / likely label and the "what if" slider',
          'state and public / private: residency in closeness, in-state cost notes, suggestions near home',
          'sticker cost of attendance, in-state and out-of-state tuition: cost notes (never what a family would pay)',
          'graduation rate and size: ordering the suggested colleges'],
   left: ['Pell share and the college URL are loaded but not used', 'nothing is modelled from it beyond those fields; no ranking or prestige score is derived']},
  {name: 'SAT / ACT concordance', kind: 'Real', files: 'data/colleges/sat_act_concordance.csv',
   what: 'The published concordance table.', used: ['converting an ACT composite to the SAT scale when a student or case has only an ACT'], left: []},
  {name: 'Five published rulebooks', kind: 'Real, transcribed', files: 'data/colleges/rulebooks.json',
   what: 'How five public sites (BigFuture, Princeton Review, Scoir, Appily, CollegeVine) turn a score into reach / target / likely.',
   used: ['run beside our own rule on the same score; "publishers disagree" when any of them lands elsewhere'], left: ['they never set our label']},
  {name: 'Common Data Set, through collegedata.fyi', kind: 'Real', files: 'data/cds/cds_outcomes_sample.csv, data/cds/claim_types.json, data/cds/forbidden_phrases.txt',
   what: 'What 24 colleges say they weigh (section C7) and related fields, for 2025-26.',
   used: ['"What the college says" statements, each with its field, year and source link', 'common beliefs checked against the form (interest, tests, essay, legacy)',
          'claim sentences are checked in code: every number and name must come from the row; nothing from the forbidden-phrases list'],
   left: ['fields that failed the file\'s own sanity flags are skipped', 'colleges without a row say "We hold no form from this college"']},
  {name: 'Knowledge base notes', kind: 'Real, written by the builders from the sources above', files: 'data/kb/*.md, data/kb/colleges/*.md',
   what: 'Plain-language notes on admission factors, how labels are set, the UC and Texas systems, and 24 college pages.',
   used: ['uploaded to PRISM\'s Knowledge Base; each college statement is confirmed against it and a planted false one comes back "not confirmed"'], left: ['never shown as text on the screen; only the confirmed / not confirmed mark']},
  {name: 'National case pool: public r/collegeresults posts', kind: 'Real, self-reported, no names', files: 'data/cases/applicants_wide.csv, data/cases/decisions_long.csv',
   what: 'As compiled in the GitHub repository shreybirmiwal/college-predictor. That repository states no licence; the files are included for the demo and can be removed.',
   used: ['SAT, ACT, major, hooks, home state: "Cases like this student" and closeness', 'self-rated activities and awards (0 to 10): the activities part of closeness and the scatter',
          'outcome at each college: admitted / denied / waitlisted counts, the two groups closeness compares, the kinds, and the holds-up check'],
   left: ['gender, race, income, school type, class rank and the essay / recommendation / interview self-rating are read into memory and never used anywhere',
          'a second row for the same person at one college is merged (an offer held counts as admitted; a waitlist is superseded)',
          'the pool over-represents admitted people; the official admit rate is shown beside every count and the over-count is stated']},
  {name: "The school's own finished cases", kind: 'Invented, stamped SYNTHETIC', files: 'data/synthetic/SYNTHETIC_school_cases.csv (copied to data/local/ on first use)',
   what: 'Generated by a seeded script to stand in for a counselor\'s verified records.',
   used: ['SAT, ACT, GPA, major group, hooks, home state, activities note, essay theme, outcome: the "Your school" pool, kept apart from the national one', 'GPA: the only place GPA enters closeness'],
   left: ['any field that looks like a name, email, phone or date of birth is refused when a case is added']},
  {name: 'Demo students and essays', kind: 'Invented, stamped SYNTHETIC', files: 'data/synthetic/SYNTHETIC_profiles.json, SYNTHETIC_essay_*.txt',
   what: 'Six students built to exercise the screen: strong scores, mid scores, ACT only, no score, a hidden instruction, personal details.',
   used: ['the picker on the first view; the saved runs in the shared preview'], left: ['no real student appears anywhere in this repository']},
  {name: 'Models, through the Nicrron gateway', kind: 'Service', files: 'engine/reader.py, engine/nicrron.py',
   what: 'One fast model reads the masked essay; a second model from a different maker tags the intended major independently.',
   used: ['essay notes with word-for-word quotes (code drops any note whose quote is not in the essay)', 'a major group tag, used only when the two models agree and the student gave no major'],
   left: ['no model sets a label, a count, a distance or a number of any kind', 'the essay is masked first; an essay with instructions aimed at an AI is stopped before any model sees it']},
  {name: 'PRISM by Block Convey', kind: 'Service', files: 'engine/prism.py',
   what: 'Guardrail, knowledge base and run record.', used: ['second guard on the essay', 'confirming college statements', 'recording each run and its five steps'], left: ['never delays or changes a label; with no key every call returns "off" at once']}
];
function renderDataSources(result) {
  var pools = obj(obj(result).pools), nat = obj(pools.national), own = obj(pools.own);
  var natN = num(nat.cases) !== null ? commas(num(nat.cases)) : '2,247', natC = num(nat.colleges) !== null ? num(nat.colleges) : 58;
  var natD = num(nat.decisions) !== null ? commas(num(nat.decisions)) : '20,966', ownN = num(own.cases) !== null ? num(own.cases) : 120;
  var h = '<h4>Data sources, and what was taken from each</h4>';
  h += '<p class="small">Counts today: ' + natN + ' people and ' + natD + ' decisions at ' + natC + ' colleges in the national pool; ' + ownN + ' invented cases in the school\'s own pool; 300 colleges in the Scorecard file; 24 colleges with a Common Data Set row.</p>';
  h += '<ul class="srcs">' + DATA_SOURCES.map(function (s) {
    return '<li class="src-card"><p class="src-name">' + esc(s.name) + ' <span class="tag ' + (/Invented/.test(s.kind) ? 'tag-self' : 'tag-verified') + '">' + esc(s.kind) + '</span></p>' +
      '<p class="src-what">' + esc(s.what) + '</p><p class="src-files"><span class="quiet">Files:</span> ' + esc(s.files) + '</p>' +
      '<p class="src-h">Used for</p><ul class="plain small">' + arr(s.used).map(function (t) { return '<li>' + esc(t) + '</li>'; }).join('') + '</ul>' +
      (arr(s.left).length ? '<p class="src-h">Left out, or kept in check</p><ul class="plain small">' + arr(s.left).map(function (t) { return '<li>' + esc(t) + '</li>'; }).join('') + '</ul>' : '') + '</li>';
  }).join('') + '</ul>';
  return h;
}
function renderBuiltPanel(result) {
  return panelHead('Check the work', 'How it was built') + '<section class="rc-sec about">' +
    '<p class="about-lead">The method behind closeness and the data behind the whole screen. None of it depends on which student is loaded.</p>' +
    renderHowBuilt(methodOf(result)) + renderDataSources(result) + '</section>';
}
function renderEssayPanel(result) { return panelHead('For the counselor', 'Essay notes') + '<section class="rc-sec">' + renderEssay(obj(result).reader, obj(result).privacy) + '</section>'; }
function renderHowPanel(result) {
  var r = obj(result);
  return panelHead('Check the work', 'How this was made') + '<section class="rc-sec">' + renderHow(r.steps, r.checks, r.prism, r.privacy, r.closeness_check) + '</section>';
}

/* ---------- family sheet (print only) ---------- */
function familyLine(c) {
  c = obj(c);
  var L = obj(c.label), g = groupOf(L.state), bits = [];
  if (g === 'outside_data') return '<li><b>' + esc(c.name) + '.</b> Not in our data, so nothing is said about it.</li>';
  if (g === 'cant_say') bits.push(str(L.rule_text));
  else if (L.state === 'reach_for_everyone') bits.push('A reach for every applicant');
  if (num(c.admit_rate) !== null) bits.push('Admits ' + inHundred(c.admit_rate) + ' applicants');
  if (num(c.cost_year) !== null) bits.push('Sticker cost ' + moneyAbout(c.cost_year) + ' a year');
  bits = bits.filter(Boolean);
  return '<li><b>' + esc(c.name) + '.</b> ' + esc(bits.map(function (b) { return b.replace(/\.$/, ''); }).join('. ')) + (bits.length ? '.' : '') + '</li>';
}
function renderFamily(result) {
  var r = obj(result), cs = arr(r.colleges).map(obj), b = obj(r.balance), st = obj(r.student), h = '';
  h += '<header class="fam-head"><h1>College list' + (str(st.label) ? ' for ' + esc(studentShort(st.label)) : '') + '</h1>' +
    '<p>' + (r.synthetic === true ? '<span class="stamp">SYNTHETIC</span> ' : '') + 'Prepared with the counselor' +
    (str(r.generated_at) ? ' on ' + esc(str(r.generated_at).slice(0, 10)) : '') + '</p></header>';
  GROUPS.forEach(function (G) {
    var items = cs.filter(function (c) { return groupOf(obj(c.label).state) === G.key; });
    if (!items.length && !G.always) return;
    h += '<section class="fam-group"><h2>' + shape(G.key) + esc(G.title) + ' (' + items.length + ')</h2>' +
      (items.length ? '<ul>' + items.map(familyLine).join('') + '</ul>' : '<p>' + esc(G.empty) + '</p>') + '</section>';
  });
  var w = warningTexts(b.warnings);
  if (w.length) {
    h += '<section class="fam-group"><h2>About the balance of this list</h2><ul>' + w.map(function (x) { return '<li>' + esc(x) + '</li>'; }).join('') + '</ul></section>';
  }
  var s = arr(b.suggestions).map(obj);
  if (s.length) {
    h += '<section class="fam-group"><h2>Colleges worth a look</h2><ul>' + s.map(function (x) {
      return '<li><b>' + esc(x.name) + '</b>' + (x.would_be ? ' (would be ' + esc((STATE_TEXT[x.would_be] || str(x.would_be)).toLowerCase()) + ')' : '') +
        '. ' + esc(x.why) + (num(x.cost_year) !== null ? ' Sticker cost ' + esc(moneyAbout(x.cost_year)) + ' a year.' : '') + '</li>';
    }).join('') + '</ul></section>';
  }
  var seen = {}, cav = [];
  function add(t) { t = str(t).trim(); if (t && !seen[t]) { seen[t] = 1; cav.push(t); } }
  add('Labels come from each college\'s published test score range and admit rate. Grades, activities and the essay are not used.');
  add('Reach, target and likely describe where the score sits against published numbers. They are not odds of getting in.');
  cs.forEach(function (c) { arr(obj(c.label).caveats).forEach(add); });
  add('Sticker cost is the published price. What this family would actually pay is not known here.');
  h += '<section class="fam-group fam-caveats"><h2>Please read this with the list</h2><ul>' +
    cav.map(function (t) { return '<li>' + esc(t) + '</li>'; }).join('') + '</ul></section>';
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
  esc: esc, inHundred: inHundred, rateFull: rateFull, moneyAbout: moneyAbout, duration: duration, groupOf: groupOf,
  renderTopChips: renderTopChips, renderStudentLine: renderStudentLine, renderCounters: renderCounters, warningTexts: warningTexts,
  pictureModel: pictureModel, renderPicture: renderPicture, renderPictureCard: renderPictureCard, ladderLines: ladderLines,
  closenessOf: closenessOf, ringsModel: ringsModel, renderRings: renderRings, picView: picView, PIC_VIEWS: PIC_VIEWS,
  mindMapModel: mindMapModel, renderMindMap: renderMindMap,
  renderLeversCard: renderLeversCard, renderSuggestionsPanel: renderSuggestionsPanel, renderFootLinks: renderFootLinks,
  renderChanceAnswer: renderChanceAnswer, rangeBar: rangeBar, renderDrill: renderDrill, renderPool: renderPool,
  renderWhyTab: renderWhyTab, renderCasesTab: renderCasesTab, renderLeversTab: renderLeversTab, renderSaysTab: renderSaysTab,
  renderResembleTab: renderResembleTab, renderScatter: renderScatter, renderPartBars: renderPartBars, TABS: TABS,
  renderEssay: renderEssay, renderHow: renderHow, renderStopBanner: renderStopBanner, verdictMarks: verdictMarks, renderEssayPanel: renderEssayPanel, renderHowPanel: renderHowPanel,
  renderAboutPanel: renderAboutPanel, renderWeightsTable: renderWeightsTable, renderAlgorithmDiagram: renderAlgorithmDiagram, renderHowBuilt: renderHowBuilt, methodOf: methodOf,
  renderBuiltPanel: renderBuiltPanel, renderDataSources: renderDataSources, DATA_SOURCES: DATA_SOURCES,
  renderFamily: renderFamily, renderCollegeChips: renderCollegeChips, renderQuickAdds: renderQuickAdds, renderEssayPicks: renderEssayPicks,
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
var S = {mode: 'live', base: null, view: null, whatIf: null, slider: null, students: [], manifest: null, runIndex: null,
         list: [], acts: [], lastInput: null, essayPick: -2, lastFocus: null, openEl: null, seq: 0, timer: null, picView: 'ranges', lastOpened: null,
         aboutOffered: false};
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

/* ---------- drawing the first view ---------- */
function picOpts() {
  var sl = obj(S.slider);
  return {score: S.whatIf, base: num(sl.base), scoreMin: num(sl.lo), scoreMax: num(sl.hi), whatIf: S.whatIf !== null, kind: sl.disabled ? null : sl.kind, view: S.picView, focus: S.lastOpened};
}
function drawView() {
  $('counters').innerHTML = renderCounters(obj(S.view).balance, S.whatIf !== null);
  $('picture').innerHTML = renderPictureCard(S.view, picOpts());
}
function drawStudentLine() {
  $('student-line').innerHTML = renderStudentLine(obj(S.base).student, !$('student-panel').hidden);
}
function showResult(result) {
  S.base = S.view = result; S.whatIf = null; S.seq++;
  S.slider = S.mode === 'static' ? sliderSpec(result, obj(obj(S.manifest).scores)[String(S.runIndex)] || null) : sliderSpec(result);
  $('top-chips').innerHTML = renderTopChips(result, S.mode);
  $('student-panel').hidden = true; $('student-line').hidden = false;
  drawStudentLine(); drawView();
  $('stopped').innerHTML = renderStopBanner(obj(result).privacy, obj(result).reader);
  $('levers').innerHTML = renderLeversCard(result, S.slider, S.mode !== 'static');
  $('footlinks').innerHTML = renderFootLinks(result, S.mode);
  $('chance-answer').hidden = true; $('chance-answer').innerHTML = renderChanceAnswer(obj(result).refusals);
  $('family').innerHTML = renderFamily(result);
  drawQuick();
  maybeOpenAbout();
}
function inputFromStudent(st) {
  var s = normaliseStudent(st);
  return {label: s.label || 'Student', sat: s.sat, act: s.act, gpa: s.gpa, gpa_scale: s.gpa_scale, activities_rating: s.activities_rating, home_state: s.home_state || null,
          intended_major: s.intended_major || null, hooks: s.hooks.length ? s.hooks : ['none'], activities: s.activities, essay: '', college_list: s.college_list};
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
    if (S.whatIf === null) { S.view = S.base; drawView(); return; }
    var req;
    if (S.mode === 'static') {
      req = fetchJSON('static/run-' + S.runIndex + '-' + v + '.json');
    } else {
      var inp = Object.assign({}, S.lastInput || inputFromStudent(obj(S.base).student), {use_model: false, essay: ''});
      if (sl.kind === 'ACT') inp.act = v; else inp.sat = v;
      req = fetchJSON('api/run', {method: 'POST', body: JSON.stringify(inp)}, 20000);
    }
    req.then(function (r) {
      if (seq !== S.seq) return;
      if (r.ok && r.data && Array.isArray(r.data.colleges)) { S.view = r.data; drawView(); }
      else $('whatif-hint').textContent = 'The labels could not be re-run here. The line has moved; the labels have not.';
    }).catch(function () {
      if (seq === S.seq) $('whatif-hint').textContent = 'The labels could not be re-run here. The line has moved; the labels have not.';
    });
  }, 250);
}
function resetScore() {
  var sl = S.slider, el = $('whatif');
  if (!sl || !el) return;
  el.value = sl.value; onWhatIf(el.value); el.focus();
}

/* ---------- loading: server, then shared preview, then the embedded example ---------- */
function setStudents(list) {
  S.students = list.map(normaliseStudent);
  $('student-pick').innerHTML = S.students.map(function (s, i) {
    return '<option value="' + i + '">' + esc(s.label || 'Demo student ' + (i + 1)) + '</option>';
  }).join('') + (S.mode === 'static' ? '' : '<option value="">New student (blank)</option>');
  if (S.students.length) fillForm(S.students[0]);
  drawEssayPicks();
}
function loadExample(why) {
  function use(data) {
    if (!data || !Array.isArray(data.colleges)) { notice('No example data could be loaded.'); return; }
    S.mode = 'example';
    if (why !== 'runfail') { setStudents([data.student]); S.lastInput = null; }
    showResult(data);
    notice(why === 'runfail' ? 'The server could not be reached, so this is example data, not the student you entered.'
      : (why === 'offline' ? 'The server could not be reached, so this is example data.' : 'Showing example data.'));
  }
  return fetchJSON('../docs/fixture_result.json').then(function (r) { use(r.ok && r.data ? r.data : FIXTURE); }).catch(function () { use(FIXTURE); });
}
function loadPreview() {
  return fetchJSON('static/manifest.json').then(function (r) {
    var list = listFrom(obj(r.data).students, []);
    if (!r.ok || !list.length) throw new Error('no manifest');
    S.mode = 'static'; S.manifest = r.data;
    setStudents(list);
    $('more-fields').hidden = true; $('mode-line').hidden = false; $('mode-line').textContent = PREVIEW_LINE;
    $('top-chips').innerHTML = renderTopChips(null, 'static');
    return run();
  });
}

/* ---------- the student editor ---------- */
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
  setSlider('actv', s.activities_rating, 5);
  $('f-state').value = (s.home_state || '').toUpperCase();
  $('f-major').value = s.intended_major || ''; syncMajor();
  $('f-essay').value = s.essay || '';
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
function changed(text) { if (S.base) $('build-hint').textContent = text || 'Changed. Press Build the list to refresh.'; }
function addCollege(name) {
  name = str(name).trim();
  if (!name || S.mode === 'static') return false;
  var dup = S.list.some(function (x) { return x.toLowerCase() === name.toLowerCase(); });
  if (!dup) S.list.push(name);
  drawChips();
  $('college-q').value = ''; clearHits();
  changed(dup ? name + ' is already on the list.' : name + ' added. Press Build the list to see it.');
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
  var btn = $('build-btn');
  function busy(on) { btn.disabled = on; btn.textContent = on ? 'Building the list…' : 'Build the list'; if (on) $('results').setAttribute('aria-busy', 'true'); else $('results').removeAttribute('aria-busy'); }
  if (S.mode === 'static') {
    var s = S.students[+$('student-pick').value] || S.students[0], idx = s && s.index !== null ? s.index : +$('student-pick').value;
    busy(true);
    return fetchJSON('static/run-' + idx + '.json').then(function (r) {
      if (r.ok && r.data && Array.isArray(r.data.colleges)) { S.runIndex = idx; notice(''); showResult(r.data); }
      else notice('That saved run could not be loaded.');
    }).catch(function () { notice('That saved run could not be loaded.'); }).finally(function () { busy(false); });
  }
  var input = readForm();
  if (!input.college_list.length) { $('more-fields').open = true; $('build-hint').textContent = 'Add at least one college first.'; return; }
  busy(true); $('build-hint').textContent = '';
  return fetchJSON('api/run', {method: 'POST', body: JSON.stringify(input)}, 120000).then(function (r) {
    if (r.ok && r.data && Array.isArray(r.data.colleges)) {
      S.mode = 'live'; S.lastInput = input; notice(''); showResult(r.data);
      $('results').focus();
    } else if (r.status === 404 || r.status === 405 || r.status === 501) {
      return loadExample('runfail');
    } else {
      notice('The list could not be built: ' + (str(obj(r.data).error) || 'the server answered with an error (' + r.status + ').'));
    }
  }).catch(function () { return loadExample('runfail'); }).finally(function () { busy(false); });
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
}
function closePanel() {
  if (!S.openEl) return;
  S.openEl.hidden = true; S.openEl = null; $('backdrop').hidden = true; document.body.classList.remove('drawer-open');
  if (S.lastFocus && S.lastFocus.focus && document.contains(S.lastFocus)) S.lastFocus.focus(); else $('results').focus();
}
function openAbout() {
  openPanel($('receipt'), renderAboutPanel(S.base, S.mode));
  try { localStorage.setItem('cc-about-seen', '1'); } catch (e) { /* private window or storage off: the page still works */ }
}
/* The about page opens by itself on a first visit, or whenever the address has ?about=1. */
function maybeOpenAbout() {
  if (S.aboutOffered) return;
  S.aboutOffered = true;
  var asked = /[?&]about=1(&|$)/.test(location.search), seen = false;
  try { seen = localStorage.getItem('cc-about-seen') === '1'; } catch (e) { seen = true; }
  if (asked || !seen) openAbout();
}
function openCollege(i, tab) {
  var c = arr(obj(S.view).colleges)[i];
  if (!c) return;
  S.lastOpened = i;
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
function doAct(el) {
  var act = el.getAttribute('data-act'), i = +el.getAttribute('data-i'), name = el.getAttribute('data-name');
  if (act === 'open-receipt') openCollege(i);
  else if (act === 'close-panel') closePanel();
  else if (act === 'tab') pickTab(el.getAttribute('data-tab'));
  else if (act === 'print') window.print();
  else if (act === 'edit-student') {
    var p = $('student-panel'); p.hidden = !p.hidden;
    if (!p.hidden && S.mode !== 'static') $('more-fields').open = true;
    drawStudentLine();
    var b = $('student-line').querySelector('button'); if (b) b.focus();
  }
  else if (act === 'more-warnings') { var mw = $('more-warn'); mw.hidden = !mw.hidden; el.setAttribute('aria-expanded', mw.hidden ? 'false' : 'true'); }
  else if (act === 'show-suggestions') openPanel($('receipt'), renderSuggestionsPanel(obj(S.base).balance, S.mode !== 'static'));
  else if (act === 'open-says' || act === 'see-cases') {
    var cs = arr(obj(S.view).colleges), k = -1;
    cs.forEach(function (c, j) {
      var cc = obj(c), hit = act === 'open-says' ? arr(cc.says).length > 0
        : (num(obj(obj(cc.cases).own).n) || 0) + (num(obj(obj(cc.cases).national).n) || 0) > 0;
      if (k === -1 && hit) k = j;
    });
    openCollege(k === -1 ? 0 : k, act === 'open-says' ? 'says' : 'cases');
  }
  else if (act === 'open-about') openAbout();
  else if (act === 'open-built') openPanel($('receipt'), renderBuiltPanel(S.base));
  else if (act === 'tour-rings' || act === 'tour-map' || act === 'tour-ranges') {
    S.picView = act === 'tour-rings' ? 'rings' : (act === 'tour-map' ? 'map' : 'ranges');
    closePanel();
    if (S.view) { $('picture').innerHTML = renderPictureCard(S.view, picOpts()); $('picture').scrollIntoView({block: 'start'}); var tb = $('picture').querySelector('[data-view="' + S.picView + '"]'); if (tb) tb.focus(); }
  }
  else if (act === 'tour-resemble') { closePanel(); openCollege(i, 'resemble'); }
  else if (act === 'open-essay') openPanel($('receipt'), renderEssayPanel(S.base));
  else if (act === 'open-how') openPanel($('receipt'), renderHowPanel(S.base));
  else if (act === 'open-case') { openPanel($('case-panel'), null, 'input'); loadCaseCount(); }
  else if (act === 'ask-chance') {
    var box = $('chance-answer'); box.hidden = !box.hidden; el.setAttribute('aria-expanded', box.hidden ? 'false' : 'true');
    if (!box.hidden) box.scrollIntoView({block: 'nearest'});
  }
  else if (act === 'reset-score') resetScore();
  else if (act === 'pic-view') {
    S.picView = picView({view: el.getAttribute('data-view')});
    $('picture').innerHTML = renderPictureCard(S.view, picOpts());
    var pb = $('picture').querySelector('[data-view="' + S.picView + '"]'); if (pb) pb.focus();
  }
  else if (act === 'add-suggestion') { if (addCollege(name)) { el.textContent = 'Added'; el.disabled = true; closePanel(); run(); } }
  else if (act === 'quick-add' || act === 'pick-hit') { addCollege(name); }
  else if (act === 'add-typed') {
    var top = $('college-hits').querySelector('button'), typed = $('college-q').value.trim();
    addCollege(top && top.getAttribute('data-name').toLowerCase() === typed.toLowerCase() ? top.getAttribute('data-name') : typed);
  }
  else if (act === 'remove-college') { S.list.splice(i, 1); drawChips(); changed(); var nx = all('#college-chips button')[Math.min(i, S.list.length - 1)]; if (nx) nx.focus(); }
  else if (act === 'add-activity') { syncActs(); S.acts.push({type: '', role: '', description: ''}); drawActs(); var ins = all('#activities .act-row input'); if (ins.length) ins[ins.length - 3].focus(); }
  else if (act === 'remove-activity') { syncActs(); S.acts.splice(i, 1); drawActs(); }
  else if (act === 'toggle-hook') { el.setAttribute('aria-pressed', el.getAttribute('aria-pressed') === 'true' ? 'false' : 'true'); changed(); }
  else if (act === 'pick-major') { $('f-major').value = el.getAttribute('aria-pressed') === 'true' ? '' : el.getAttribute('data-major'); syncMajor(); changed(); }
  else if (act === 'pick-essay') {
    S.essayPick = i; $('f-essay').value = i === -1 ? '' : str(obj(S.students[i]).essay);
    var words = $('f-essay').value.trim() ? $('f-essay').value.trim().split(/\s+/).length : 0;
    $('essay-hint').textContent = i === -1 ? 'No essay will be read.' : 'Essay from ' + studentShort(obj(S.students[i]).label) + ' chosen (' + words + ' words).';
    drawEssayPicks(); changed();
    var again = $('essay-picks').querySelector('[data-i="' + i + '"]'); if (again) again.focus();
  }
}
function boot() {
  $('f-state').innerHTML = '<option value="">Not given</option>' + Object.keys(STATES).map(function (k) { return '<option value="' + k + '">' + esc(STATES[k]) + '</option>'; }).join('');
  document.addEventListener('click', function (e) {
    var el = e.target.closest ? e.target.closest('[data-act]') : null;
    if (el && !el.disabled) doAct(el);
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closePanel();
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
    else if (t.id === 'f-essay') { S.essayPick = -2; drawEssayPicks(); }
  });
  document.addEventListener('change', function (e) {
    var t = e.target;
    if (/^f-(sat|act|gpa|actv)-none$/.test(t.id)) { showOut(t.id.slice(2, -5)); changed(); }
    else if (t.id === 'f-state') changed();
  });
  $('student-form').addEventListener('submit', function (e) { e.preventDefault(); run(); });
  $('case-form').addEventListener('submit', function (e) { e.preventDefault(); saveCase(e.target); });
  $('student-pick').addEventListener('change', function (e) {
    var v = e.target.value;
    fillForm(v === '' ? normaliseStudent({}) : S.students[+v]);
    if (v === '') $('more-fields').open = true;
    changed('Student changed. Press Build the list.');
  });
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
  fillForm(normaliseStudent({}));

  var asked = /[?&]fixture=1(&|$)/.test(location.search);
  if (asked) { loadExample('asked'); return; }
  fetchJSON('api/students').then(function (r) {
    var list = listFrom(r.data, ['students', 'profiles']);
    if (!r.ok || !list.length) throw new Error('no students');
    S.mode = 'live'; setStudents(list);
  }).catch(function () {
    return loadPreview().catch(function () { return loadExample('offline'); });
  });
}
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();

})(typeof window !== 'undefined' ? window : globalThis);
