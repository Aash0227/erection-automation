import sys, math, json, csv, hashlib, pathlib, textwrap
sys.path.insert(0, str(pathlib.Path(__file__).parent / 'python_libs'))
import pymupdf as F

ROOT=pathlib.Path(__file__).resolve().parent.parent
OUT=ROOT/'outputs'; WORK=ROOT/'work'
src=F.open(WORK/'permit.pdf'); ref=F.open(WORK/'reference.pdf')
ref.bake(annots=True, widgets=True)  # preserve the annotated snapshot in embedded PDF pages
for p in src: p.remove_rotation()
for p in ref: p.remove_rotation()
doc=F.open(); W,H=2592,1728
NAVY=(.08,.16,.23); RED=(.83,.19,.10); TEAL=(0,.43,.40); BLUE=(.06,.33,.73); PURPLE=(.43,.23,.64); GREY=(.40,.45,.49); LIGHT=(.94,.96,.97); AMBER=(.73,.39,.03)
pages=[]; checks=[]
def box(p,r,fill=None,color=None,width=1,dashes=None):
    p.draw_rect(F.Rect(r),color=color,fill=fill,width=width,dashes=dashes)
def text(p,r,s,size=20,bold=False,color=NAVY,align=0):
    z=p.insert_textbox(F.Rect(r),str(s),fontname='hebo' if bold else 'helv',fontsize=size,color=color,align=align,lineheight=1.23)
    if z < -.1: raise RuntimeError(f'TEXT OVERFLOW page {len(doc)} {r}: {str(s)[:100]} {z}')
def line(p,a,b,c=GREY,w=2,dashes=None): p.draw_line(a,b,color=c,width=w,dashes=dashes)
def arrow(p,pts,c=RED,w=4,dash=None):
    for a,b in zip(pts,pts[1:]): line(p,a,b,c,w,dash)
    a,b=pts[-2:]; dx=b[0]-a[0];dy=b[1]-a[1]; l=math.hypot(dx,dy)
    if not l:return
    ux,uy=dx/l,dy/l; sz=12+w
    q=[b,(b[0]-sz*ux+sz*.45*uy,b[1]-sz*uy-sz*.45*ux),(b[0]-sz*ux-sz*.45*uy,b[1]-sz*uy+sz*.45*ux)]
    sh=p.new_shape();sh.draw_polyline(q+[q[0]]);sh.finish(color=c,fill=c);sh.commit()
def badge(p,x,y,s,c=RED,r=27):
    p.draw_circle((x,y),r,color=(1,1,1),fill=c,width=3)
    text(p,(x-r,y-14,x+r,y+21),s,21,True,(1,1,1),1)
def tag(p,x,y,s,c=PURPLE,w=140):
    box(p,(x,y,x+w,y+42),fill=c)
    text(p,(x+5,y+8,x+w-5,y+40),s,20,True,(1,1,1),1)
def new(title,subtitle,code):
    p=doc.new_page(width=W,height=H);pages.append((code,title))
    box(p,(0,0,W,17),fill=NAVY)
    text(p,(62,44,1970,111),title,39,True)
    text(p,(64,116,1960,169),subtitle,20)
    text(p,(2020,54,2520,97),'LIVIO  /  ARON TERRACE',23,True,align=2)
    text(p,(2020,99,2520,151),'ERECTION COORDINATION CONCEPT',18,True,RED,2)
    line(p,(62,180),(2530,180),NAVY,2)
    line(p,(62,1655),(2530,1655),GREY,1)
    text(p,(64,1671,2110,1713),'REV B  |  29 SEP 2026  |  NOT FOR ERECTION - engineering and lift-plan release required  |  Overlays NTS; do not scale',16,False,GREY)
    text(p,(2190,1669,2528,1714),f'{code}  /  {len(doc):02d}',20,True,align=2)
    return p
def embed(p,n,r,crop=None,source=src):
    sp=source[n-1]; sr=sp.rect
    clip=F.Rect(sr.x0+crop[0]*sr.width,sr.y0+crop[1]*sr.height,sr.x0+crop[2]*sr.width,sr.y0+crop[3]*sr.height) if crop else sr
    r=F.Rect(r); scale=min(r.width/clip.width,r.height/clip.height)
    actual=F.Rect(r.x0+(r.width-clip.width*scale)/2,r.y0+(r.height-clip.height*scale)/2,r.x0+(r.width+clip.width*scale)/2,r.y0+(r.height+clip.height*scale)/2)
    p.show_pdf_page(actual,source,n-1,clip=clip)
    def xy(x,y): return (actual.x0+(x*sr.width-clip.x0)*scale,actual.y0+(y*sr.height-clip.y0)*scale)
    return xy,actual
def para(p,x,y,w,title,body,size=22,space=165):
    text(p,(x,y,x+w,y+42),title,26,True)
    text(p,(x,y+49,x+w,y+space),body,size)
def legend(p,y=1510,x=70):
    badge(p,x+25,y+24,'01',r=24);text(p,(x+61,y+5,x+310,y+53),'Sequence group',19)
    arrow(p,[(x+350,y+24),(x+470,y+24)]);text(p,(x+490,y+5,x+770,y+53),'Erection progression',19)
    arrow(p,[(x+840,y+24),(x+960,y+24)],TEAL,6);text(p,(x+980,y+5,x+1220,y+53),'Material transfer',19)
    arrow(p,[(x+1310,y+24),(x+1430,y+24)],BLUE,3,'[12 8]');text(p,(x+1450,y+5,x+1700,y+53),'Keep access open',19)
    tag(p,x+1810,y+3,'C',w=52);text(p,(x+1880,y+5,x+2130,y+53),'Candidate crane',19)
def no_go(p,r,label):
    rr=F.Rect(r);box(p,rr,color=GREY,width=2)
    for x in range(int(rr.x0)+10,int(rr.x1)-10,22): line(p,(x,rr.y0+5),(min(x+20,rr.x1-4),rr.y1-5),GREY,1)
    if label:text(p,(rr.x0,rr.y1+7,rr.x1,rr.y1+43),label,16,True,GREY,1)

rows=[]
def add(step,group,action,crane,material,reason,risk,after,nextcheck,source,status='ASSUMED'):
    rows.append(dict(step=f'{step:02}',group=group,action=action,crane=crane,material=material,reason=reason,risk=risk,after=after,next_check=nextcheck,source=source,status=status))
add(1,'Site controls','Survey boundaries, utilities and retained trees; install approved protection and access controls.','None','None','Prevent setup on an unverified support area or protected feature.','HOLD: tree identity, ROW rights, buried/overhead services and exclusion limits.','Protected limits and access are established.','Prove excavation and delivery access do not conflict.','A1.0 p15; C2.0 p75; ER-1 p90; L1.01 p98')
add(2,'Substructure','Complete engineered shoring, excavation, mat, basement walls and support system.','Separate plan','Separate schedule','Provide the designed support before superstructure erection.','HOLD: excavation surcharge; shoring design and staged removal.','Basement and mat exist; car-lift voids remain controlled openings.','Confirm embeds and support elevations against released drawings.','S0.1 p47; S1.0-S1.1 pp49-50; S1 p182')
add(3,'Equipment interfaces','Resolve automated-parking and electrical equipment installation routes before restricting openings.','Separate plan','Vendor packages','Large equipment cannot be assumed to pass through finished personnel openings.','HOLD: deferred parking equipment; delivery dimensions; transformer access.','Reserved vendor routes are documented and protected.','Confirm first-floor work will not trap equipment or close required access.','A1.1 p16; QA sheets pp177-181; joint trench p215')
add(4,'First-floor release','Accept supporting slab/frame, anchors, protected access and approved erection stability plan.','A candidate','First floor kits','Release only a checked working surface and a defined temporary load path.','HOLD: slab strength, storage loading, crane reactions and full lift envelope.','First-floor survey and staged support prerequisites are accepted.','Confirm first wall group can be landed, connected and braced.','S0.1 p47; S1.1-S1.2 pp50-51')

level_pages=[16,18,19,20,21,22,23,24]
locations=[
 ['Bike room / unit 105 side','Units 104-102 side','Units 107-108 side','Electrical / trash / 106 / stair 01','Unit 101 frontage','Lobby / public rooms / stair 02 / elevators'],
]+[[f'Units {l}06-{l}05 side',f'Units {l}04-{l}02 side',f'Units {l}09-{l}10 side',f'Units {l}07-{l}08 / stair 01',f'Unit {l}01 frontage',f'Unit {l}00 / stair 02 / elevators'] for l in range(2,9)]
names=['Neighbor-side rear','Neighbor-side middle','Jordan-side middle','Jordan-side rear','Neighbor-side frontage','Jordan-side frontage / core']
reasons=[
 'Start at the far rear with an approved stable corner and returns; no later low-level transfer behind it.',
 'Continue the far side while the overhead delivery route and central corridor are open.',
 'Complete the middle near side only after its far-side kit and internal large pieces are in place.',
 'Finish the rear sector before relocation; protect rear equipment routes and stair access.',
 'From the verified front setup, land the remaining far-side frontage group before the near front closes.',
 'Complete the front core interfaces and near-side returns last; lower trapped pieces before final closure.'
]
risks=[
 'High: far reach, adjacent property, initial stability and edge protection.',
 'High: large internal pieces can be trapped by top framing or completed near walls.',
 'High: connecting faces and long-panel rotation require a verified envelope.',
 'High: stair/equipment routes; local rear closure only after kit reconciliation.',
 'High: front reach, neighboring edge and public El Camino frontage.',
 'High: shaft/stair interfaces and final crane-delivered wall closure.'
]
afters=[
 'Far rear group is stabilized; middle/front and overhead receiving areas remain open.',
 'Far middle group is stabilized; near middle receiving slot remains open.',
 'Middle cell is bounded; rear near-side receiving slot remains open.',
 'Rear/middle sector is complete and stable for the planned crane move.',
 'Far front is complete; near front and core receiving space remain open.',
 'Crane-delivered wall groups are complete; no remaining large pieces may depend on closed side access.'
]
nexts=[
 'Check next group landing and rigging rotation clear of the new rear returns.',
 'Check all large middle-cell internals are installed before its near-side closure.',
 'Check the rear group arrives from above without passing through the completed middle cell.',
 'Verify B setup or A full coverage, public controls and forward cell stability before front lifts.',
 'Check shaft pieces, stair members and front internals fit before closing the near-front return.',
 'Reconcile every kit; any missing trapped item requires reordering before closure, not improvisation.'
]
for l,pn in enumerate(level_pages,1):
    base=5+(l-1)*8
    st=f'A1.{l} p{pn}; '+(f'S1.{l+1} p{50+l}' if l<8 else 'RFI-01: L8 structural mapping unresolved')
    for j in range(6):
        add(base+j,f'L{l} - {names[j]}: {locations[l-1][j]}','Erect required steel/supports and CFS as an approved stable cell; place large internals before its last enclosing return.','A' if j<4 else 'A or B',f'L{l}-G{j+1} kit; cube TBD',reasons[j],risks[j]+(' L8 HOLD RFI-01.' if l==8 else ''),afters[j],nexts[j],st)
    add(base+6,f'L{l} - Residual partitions / closure check','Complete remaining non-loadbearing partitions and connections; verify all lift-dependent components and access closures.','A or B as released',f'L{l}-G7 kit; cube TBD','Clear all items that would become trapped under the next deck.','High: shop-panel inventory, connection access and maintained egress.', 'All wall groups and pre-deck large internals are reconciled.','Verify no missing panel or connection face will be covered by joists/deck.',st)
    add(base+7,f'L{l} - Overhead framing / floor release','Complete required joists, blocking, diaphragms and inspections in approved cells; authorize the next working level.','A or B as released',f'L{l}-G8 framing kit; cube TBD','Close overhead receiving space only after that cell passes its pre-deck check.','HOLD: diaphragm/temporary bracing, support reactions, load capacity and deck-system RFI-02.', 'The receiving route from above is closed in released cells; next deck is an accepted work surface.','Reset crane coverage for the next level; do not advance an unreleased upper story.',st)
roof=[
('Roof support and deck acceptance','Accept the L8-to-roof structure, falls, penetrations and storage limits.','None until accepted','Engineering release','The roof may only be used after structural and loading acceptance.','HOLD RFI-01 / RFI-02; elevations and support mapping.','Roof is released for the planned construction loads.','Confirm upstand and equipment supports match the coordinated roof layout.'),
('Rear stair 01 headhouse','Erect approved stair 01 upstand walls and overhead framing; keep the stair route protected.','A','Roof G2 kit','Complete the rear vertical termination before restricting its lifting access.','High: edge work and incomplete headhouse stability.','Rear headhouse is stable; equipment landing zones remain available.','Verify the front headhouse can be approached without crossing occupied areas.'),
('Front stair 02 / elevator headhouse','Erect the front headhouse and elevator overrun structure with vendor coordination.','A or B','Roof G3 kit','Respect the highest erection level and unresolved equipment interfaces.','High: maximum hook height and elevator steel/rigging interfaces.','Both vertical terminations are coordinated; roof equipment routes remain open.','Verify largest equipment package and the crane envelope at maximum height.'),
('Roof equipment / large assemblies','Land agreed large equipment and PV assemblies on approved supports in the vendor sequence.','A or B','Vendor packages','Avoid trapping roof equipment behind permanent screens or final crane demobilization.','HOLD: weights, supports, rigging and vendor lifting instructions.','Large roof deliveries are complete and secured.','Reconcile all equipment before screen and parapet closure.'),
('Final parapets / screens / canopies','Complete remaining parapets, screens and exterior canopy packages after route reconciliation.','A or B','Roof G5 kit','Make final closure only after all required large roof packages are in place.','High: wind area and edge lifts; do not defer required fall protection.','Final permanent closures are complete; protected personnel egress remains.','Verify every remaining lift, temporary support and access restoration obligation.'),
('Final release and demobilization','Inspect connections and weather protection; remove temporary works only under approved release; restore ROW.','Released demobilization','None','End crane use only when all scheduled lifts and dependent work are accepted.','HOLD: engineer/GC release; incomplete lifts or temporary support removal.','Erection coordination scope is closed after acceptance.','Record as-built deviations and hand over to follow-on trades.')]
for i,row in enumerate(roof,69):
    g,a,c,m,re,ri,af,ne=row;add(i,g,a,c,m,re,ri,af,ne,'A1.9-A1.10 pp25-26; A4.1 p33; S1.9 p58; M2.8 p128')

# 01 overview
p=new('4898 El Camino Real | Erection coordination','Aron Terrace, Los Altos, California  |  Document-based planning proposal  |  74 uniquely numbered coordination steps','EC-01')
img=WORK/'supplied-aerial.png'
p.insert_image(F.Rect(70,215,1475,1265),filename=img)
text(p,(80,1288,1450,1380),'Supplied aerial: post-demolition / pre-excavation context. Orange footprint and tree labels are user annotations, not surveyed geometry. Tree positions/IDs conflict with parts of the permit set: see EC-03.',22)
para(p,1550,220,960,'Proposed erection logic','Work one released level at a time. From Jordan Avenue, build stable far-side cells before their near-side returns. Complete rear/middle cells, then the frontage. Receive large pieces from above before closing their overhead framing.',25,220)
para(p,1550,475,960,'Primary crane strategy - ASSUMED','A: mid/rear Jordan Avenue candidate. B: forward Jordan Avenue relocation candidate only if A fails coverage or clearance. No verified crane capacity, radius, outrigger footprint or street occupation is available.',24,210)
para(p,1550,720,960,'Building facts - CONFIRMED','Eight stories plus basement, with roof terrace and headhouses (T1.1; A1.1-A1.10; A5.1). CFS bearing/nonbearing walls and steel framing are shown. The reference residence is not the target building.',24,190)
para(p,1550,945,960,'Release-critical gaps - FIELD VERIFY','Panel shop model, joints, weights and pick points; crane chart and 3D lift envelope; engineered temporary stability and deck loads; tree survey; L8 structural mapping; floor-system conflicts; parking equipment routes.',24,220)
text(p,(1550,1215,2500,1400),'This package is a coordination concept. It does not establish a safe lifting capacity or prove panel-by-panel constructability. The proposed sequence is conditional on the hold points and must be converted to a released erection/lift plan.',25,True,RED)
legend(p,1460)
text(p,(70,1530,2500,1575),'T = truck/container   |   S = inspect/rig staging   |   R = conditional crane relocation   |   ! = critical closure / verification hold   |   Hatching = restricted / no staging   |   Dashed red boxes = proposed work groups',20,True)
text(p,(70,1590,2500,1643),'All new sequence and crane selections are ASSUMED. Read: reference > site > substructure > vertical cycle > floors > roof > packing > replay > holds > sequence register.',20)

# 02 reference
p=new('Livio reference | What the drawing actually establishes','Reference PDF: one page, Sarkar Residence, 10510 Madera Drive, Cupertino  |  Source A-1.004 plus superimposed first-floor snapshot','EC-02')
xy,rr=embed(p,1,(70,220,1650,1450),(.02,.34,.42,.9),ref)
para(p,1730,225,790,'Observed sequence - CONFIRMED','01-04 trace the top and right perimeter. 05-14 move through bedroom/bathroom crosswalls, passage and the lower return. 15-17 wrap the pantry. 18-25 continue the left perimeter, garage/living interface and puja/foyer.',23,265)
para(p,1730,520,790,'Last groups - CONFIRMED','26 is repeated on three local segments. 27-33 complete the stair/entry/laundry/garage-side area. Red arrows indicate direction along wall runs; yellow tags label groups. The arrows are not a crane-radius or capacity diagram.',23,235)
para(p,1730,785,790,'Underlying logic - PROBABLE','Use a stable perimeter start; resolve returns and crosswalls before adjacent closures; work in local clusters; finish restricted entry/service areas after larger groups. Connection-face access may explain several turns. These reasons are inferred, not written on the reference.',23,275)
para(p,1730,1090,790,'Not established by the reference','No C/T/S symbols, crane setup, relocation schedule, packing manifest, bracing design or step-by-step access validation is shown. Do not claim those items were reverse-engineered as facts.',23,210)
text(p,(80,1472,2500,1570),'LIVIO ERECTION SEQUENCE LOGIC: group by constructible wall runs, show direction, place trapped pieces before closures, preserve connection and future delivery access, and test the changed condition after each group. Add a stability/diaphragm cycle for this multistory project.',26,True)
text(p,(80,1580,2500,1630),'Improved here: unique numbers, clean source crops, distinct access/material styles, documented assumptions, explicit closure and crane-move checks.',21)

# 03 site
p=new('Site logistics | Jordan Avenue crane candidates','Authority: civil C2.0 p75 + A1.0 p15, ER-1 p90, landscape L1.01 p98, joint trench p215  |  Symbols indicate candidate zones, not equipment footprints','EC-03')
xy,rr=embed(p,75,(65,245,1900,1360),(.03,.03,.90,.74))
for u,v,s in [(.39,.145,'C A'),(.56,.145,'C B?')]:
    x,y=xy(u,v);tag(p,x-55,y-20,s,w=110)
x,y=xy(.24,.145);tag(p,x-50,y-20,'T / S',TEAL,115)
arrow(p,[xy(.285,.145),xy(.35,.145)],TEAL,6)
arrow(p,[xy(.44,.145),xy(.515,.145)],PURPLE,4,'[12 7]')
text(p,(790,207,1450,242),'R: A to B only after a stable sector stop',18,True,PURPLE)
arrow(p,[xy(.165,.17),xy(.165,.34),xy(.18,.56)],BLUE,4,'[12 8]')
x,y=xy(.16,.30);badge(p,x,y,'01')
for u,v in [(.123,.553),(.697,.705)]:
    x,y=xy(u,v);p.draw_circle((x,y),42,color=AMBER,width=4,dashes='[8 5]')
    text(p,(x-70,y+45,x+100,y+108),'TREE HOLD\nTPZ TBD',16,True,AMBER)
no_go(p,(110,1385,1800,1415),'NO NEIGHBOR STAGING / OVER-SAIL RIGHTS UNVERIFIED')
para(p,1980,220,530,'A - primary candidate','Mid/rear Jordan frontage. Keep setup outside the excavation influence zone and clear of utilities, transformer access, drive apron and retained trees. Location and support system: FIELD VERIFY.',20,210)
para(p,1980,465,530,'B - conditional candidate','Forward Jordan frontage, away from the intersection. Use only if A cannot serve the front groups. B must pass the same ground, utility, traffic, tree and load-chart checks. No default El Camino lane setup.',20,225)
para(p,1980,725,530,'T / S - timed deliveries','Truck/container and inspection/rigging space share a permitted working zone by time, not by assumed simultaneous fit. No on-site stockyard is demonstrated. Use off-site holding and one called-off kit at a time.',20,225)
para(p,1980,985,530,'Tree conflict - FIELD VERIFY','C2.0 labels rear-side tree #5 and front-side tree #6 to remain. L1.01 uses #4 and #6. The aerial labels #6 at the street corner. Protect all candidate retained trees until survey/arborist reconciliation.',20,235)
text(p,(1980,1255,2510,1450),'Blue access is a proposed controlled route, not truck-turning proof. Existing rear ingress/egress easement and ER-1 construction entrance must remain coordinated with neighbors.',20,True,BLUE)
legend(p,1510)
text(p,(70,1590,2500,1635),'No reach circles are drawn: a circle without a crane model, load, height and configuration would imply unverified capacity. Tree circles are issue markers, not protection radii.',20)

# 03A aerial cross-check (Rev B)
p=new('Aerial site context | Independent imagery cross-check','SUPPORTING CONTEXT ONLY - Esri World Imagery retrieved 29 SEP 2026 at the project coordinate; capture date NOT verified  |  Permit drawings remain authoritative','EC-03A')
ax0,ay0,ax1,ay1=210,225,1230,1245
def A(u,v): return (ax0+(ax1-ax0)*u, ay0+(ay1-ay0)*v)
p.insert_image(F.Rect(ax0,ay0,ax1,ay1),filename=str(WORK/'aerial-site-z19.png'))
box(p,(ax0,ay0,ax1,ay1),color=NAVY,width=2)
sh=p.new_shape();sh.draw_circle((A(.5,.5)[0],A(.5,.5)[1]),95);sh.finish(color=RED,width=4,dashes='[10 6]');sh.commit()
text(p,(ax0+2,A(.5,.5)[1]+105,ax0+560,A(.5,.5)[1]+155),'4898 SITE (approx. - image center)',19,True,RED)
tag(p,ax0+8,ay0+12,'N',NAVY,48);text(p,(ax0+62,ay0+8,ax0+430,ay0+52),'IMAGERY IS NORTH-UP / NTS',18,True,NAVY)
text(p,(ax0,ay0-42,ax0+560,ay0-6),'EL CAMINO REAL (multi-lane arterial)',19,True,NAVY)
arrow(p,[(ax0+400,ay0+4),A(.42,.09)],NAVY,4)
text(p,(ax0+585,ay0+140,ax1-8,ay0+186),'JORDAN AVE',19,True,NAVY)
arrow(p,[(ax0+600,ay0+185),A(.53,.29)],NAVY,4)
arrow(p,[A(.30,.78),A(.26,.70)],AMBER,4);text(p,(ax0+2,A(.30,.78)[1]+8,ax0+640,A(.30,.78)[1]+56),'REAR: TREE CANOPY + NEIGHBOR STRUCTURES (approx.)',18,True,AMBER)
para(p,1330,225,1160,'Imagery source - PROBABLE','Esri World Imagery tile mosaic retrieved 29 SEP 2026 at the coordinate supplied with the prompt (37.3980, -122.1080). Direct Google Earth retrieval is unavailable to automation. Capture date is not verified; site conditions shown may pre- or post-date permit photos. Supporting context only - no dimension is taken from imagery.',21,300)
para(p,1330,540,1160,'Frontage check - CONSISTENT','Imagery shows the multi-lane El Camino Real arterial along the north and Jordan Avenue fronting the site, matching EC-03 crane candidates A/B and the T/S timed-delivery zone. No default El Camino lane setup is supported by either source.',21,235)
para(p,1330,800,1160,'Rear constraint - CONSISTENT','Dense mature tree canopy and neighboring structures close off the rear/southwest boundary; no rear staging corridor exists. Confirms the EC-03 NO NEIGHBOR STAGING band and the tree-hold TPZ items. Tree identity/numbering remains FIELD VERIFY.',21,235)
para(p,1330,1060,1160,'What this does NOT prove','Crane capacity, reach, outrigger bearing, street-closure permits, utility clearances, tree survey, or current site state. Candidate zones remain ASSUMED pending lift-plan release. Supplied annotated aerial (EC-01) remains the closer-in-time site reference.',21,260)
p.insert_image(F.Rect(1330,1395,1630,1640),filename=str(WORK/'aerial-context-z16.png'));box(p,(1330,1395,1630,1640),color=NAVY,width=1)
text(p,(1670,1400,2520,1445),'~1.4 km context',18,True,NAVY)
text(p,(1670,1455,2520,1635),'Same coordinate at 16x zoom: El Camino corridor, Jordan Ave approach and surrounding residential fabric. Use for orientation awareness only.',19)

# 04 enabling
p=new('01-04 | Substructure and equipment release','The building footprint is not a crane hardstand  |  Basement excavations, parking voids and utilities control what may carry temporary loads','EC-04')
embed(p,50,(70,270,1640,1200),(.19,.09,.90,.70))
badge(p,650,310,'02');badge(p,480,635,'03');badge(p,1260,960,'04')
tag(p,950,225,'C A / B: STREET CANDIDATES ONLY',w=530)
no_go(p,(125,1245,1580,1300),'NO CRANE OR CUBE STORAGE ON SLAB / EXCAVATION EDGE WITHOUT ENGINEERED RELEASE')
for j,row in enumerate(rows[:4]):
    yy=240+j*240;badge(p,1740,yy+20,row['step'])
    if j<3: arrow(p,[(1740,yy+65),(1740,yy+214)],RED,3)
    text(p,(1790,yy-4,2510,yy+52),row['group'],26,True)
    text(p,(1790,yy+55,2510,yy+205),row['action']+' '+row['risk'],22)
text(p,(1700,1235,2510,1470),'CONFIRMED: S0.1 refers to excavation extending about 22 ft below grade; the separate S1 shoring concept depicts slab about 19 ft below grade. These describe different limits and do not authorize crane surcharge or a temporary support scheme.',23)
text(p,(80,1400,1600,1500),'Source shown: S1.1 basement framing, permit p50. Car-lift openings remain protected. Parking vendor plans are deferred/preliminary interfaces, not authorization to fill, bridge or load a void.',22)
legend(p,1530)

# 05 vertical cycle
p=new('Vertical cycle | Close each cell only after its last large delivery','Source A5.1 p38 and A4.1 p33  |  Eight floors plus roof terrace/headhouses  |  Height is not hook-height clearance','EC-05')
xy,rr=embed(p,38,(70,230,1730,1420),(.02,.1,.91,.94))
for l,v in enumerate([.69,.628,.565,.505,.445,.384,.322,.258],1):
    x,y=xy(.765,v);badge(p,x,y,str(l),r=24)
arrow(p,[(1665,1300),(1665,400)],RED,5)
text(p,(95,1460,1740,1560),'Published elevations: L1 0\'0\"; L2 12\'4\"; L3 23\'8\"; L4 34\'11\"; L5 46\'3\"; L6 57\'7\"; L7 68\'11\"; L8 80\'2\"; roof deck 92\'4\". A4.1 also labels top of elevator 109\'7 1/4\" and overall height 109\'9\"; reconcile datums for lifting.',22)
para(p,1830,230,690,'Repeat on every floor','1. Accept the working deck, anchors and approved temporary stability arrangement.\n2. Erect an approved steel/CFS cell. Land trapped internals while the receiving space is open.\n3. Connect, plumb and brace before release.\n4. Close only that cell\'s joists/deck after a pre-deck inventory check.\n5. Accept diaphragm and support capacity before advancing upward.',24,445)
para(p,1830,715,690,'Critical dependency','No blanket instruction to omit a beam, bearing wall, shear-wall return or diaphragm is given. If a support must precede a panel but blocks its delivery, resolve the panel split or engineered sequence before fabrication.',23,225)
para(p,1830,980,690,'Two structural holds','RFI-01: no separately named L8 framing sheet was found in S1.2-S1.9. Confirm how L8 and roof supports map to the plans.\nRFI-02: S0.1 describes composite deck/concrete diaphragms; floor plans call for Megaboard sheathing. Obtain the governing assembly and temporary load path.',23,320)
text(p,(1830,1350,2510,1585),'The numbered floor bubbles here identify levels, not erection steps. Every floor has its own globally unique step numbers on EC-06 through EC-13. Crane charts must cover actual pick and set positions at each elevation, including load and rigging height.',22,True)

# floor sheets
zone_rects=[(.06,.640,.40,.895),(.40,.640,.72,.895),(.40,.340,.635,.602),(.06,.340,.40,.602),(.72,.640,.883,.895),(.635,.320,.883,.602)]
badge_pts=[(.225,.937),(.525,.937),(.51,.286),(.22,.286),(.80,.937),(.80,.286)]
for l,pn in enumerate(level_pages,1):
    base=5+(l-1)*8; rrrows=rows[base-1:base+7]
    p=new(f'Level {l} | Steps {base:02}-{base+7:02}',f'Actual architectural plan A1.{l}, permit p{pn}  |  Rear/middle sector first, then El Camino frontage  |  Proposed groups; shop-panel mapping required',f'EC-{5+l:02}')
    xy,ar=embed(p,pn,(65,320,1935,1430),(.02,.23,.932,.970))
    # Equipment chain is outside the drawing, linked to the street-side orientation.
    tag(p,100,218,'T',TEAL,75);tag(p,290,218,'S',TEAL,75);tag(p,510,218,'C A',PURPLE,125);tag(p,1500,218,'C B?',PURPLE,140)
    arrow(p,[(185,239),(275,239)],TEAL,6);arrow(p,[(375,239),(492,239)],TEAL,6)
    text(p,(690,216,1440,276),'JORDAN AVENUE | candidate setup zones at grade',21,True)
    text(p,(85,279,1910,318),'Top landing only: crane-to-cell route must be checked in 3D. T/S are off-building staging symbols, not a deck storage allowance.',18,False,TEAL)
    hall=src[pn-1].search_for('HALLWAY')[0]; hv=(hall.y0+hall.y1)/2/src[pn-1].rect.height
    zrs=[(a,hv+.024,c,d) if j in [0,1,4] else (a,b,c,hv-.018) for j,(a,b,c,d) in enumerate(zone_rects)]
    for j,(zr,bp) in enumerate(zip(zrs,badge_pts)):
        a=xy(zr[0],zr[1]);b=xy(zr[2],zr[3]);box(p,(*a,*b),color=RED,width=2,dashes='[9 6]')
        bx,by=xy(*bp);badge(p,bx,by,f'{base+j:02}')
        if j in [3,5]: text(p,(bx+34,by-21,bx+82,by+35),'!',28,True,AMBER)
        cy=zr[1] if j in [2,3,5] else zr[3]
        line(p,(bx,by+(28 if j in [2,3,5] else -28)),xy(bp[0],cy),RED,2)
        # Short arrows trace exterior-edge progress without running through room notes.
        xx1,xx2=zr[0]+.015,zr[2]-.015
        yy=zr[3]+.006 if j in [0,1,4] else zr[1]-.006
        arrow(p,[xy(xx2,yy),xy(xx1,yy)] if j in [2,3] else [xy(xx1,yy),xy(xx2,yy)],RED,3)
    # Global transitions are explicit in the uncluttered flow strip below.
    arrow(p,[xy(.325,hv+.007),xy(.755,hv+.007)],BLUE,3,'[12 8]')
    text(p,(80,1436,1910,1473),'BLUE: preserve central corridor / stair routes for people and small items. Follow actual plan jogs. Group outlines are schematic; include all associated recesses and returns.',18,False,BLUE)
    for j in range(8):
        x=80+j*226;badge(p,x+28,1520,f'{base+j:02}',r=23)
        labels=['FAR REAR','FAR MIDDLE','NEAR MIDDLE','NEAR REAR','FAR FRONT','NEAR FRONT','KIT CHECK','DECK RELEASE']
        text(p,(x-18,1554,x+179,1597),labels[j],17,True,align=1)
        if j<7:arrow(p,[(x+61,1520),(x+185,1520)],PURPLE if j==3 else RED,3)
    text(p,(80,1604,1910,1643),'Transitions: far middle to near middle = change workface; near rear to far front = new sector / R if needed. Short plan arrows show local progression, not load-flight paths.',17)
    for j,row in enumerate(rrrows):
        yy=225+j*135
        badge(p,2020,yy+18,row['step'],r=22)
        short=names[j] if j<6 else ('Residual partitions / inventory' if j==6 else 'Joists / diaphragm / release')
        text(p,(2060,yy-5,2520,yy+53),short,22,True)
        desc=(locations[l-1][j]+'. '+(['Start stable; protect rear route.','Land all large far-side internals.','Close near side after far kit.','Complete rear sector; prepare R.','Verify A coverage or move to B.','Core interfaces first; last return closes.'][j])) if j<6 else ('All lift-dependent items installed before overhead closure.' if j==6 else 'Complete each cell only after pre-deck check; approve next level.')
        text(p,(2060,yy+53,2520,yy+120),desc,18)
    text(p,(1980,1340,2520,1480),f'CLOSURE: {base+3:02} rear-sector last return; {base+5:02} front-sector last return. Install cell internals first. Permanent door/stair routes stay usable.',20,True,RED)
    text(p,(1980,1500,2520,1635),'HOLD: floor-specific steel/CFS support, bracing and crane coverage. '+('L8 structural mapping unresolved: RFI-01. No repeat-floor assumption releases L8.' if l==8 else 'If A covers all groups, omit R. If not, stabilize rear/middle cells, then relocate A to B for front groups.'),19,True,PURPLE)

# roof
p=new('Roof | Steps 69-74 and final closures','Source A1.9 p25 + A1.10 p26 + A4.1 p33 + S1.9 p58 + M2.8 p128  |  Roof framing and headhouse mapping require RFI-01','EC-14')
xy,ar=embed(p,25,(70,305,1930,1430),(.02,.23,.932,.967))
tag(p,350,218,'C A',w=140);tag(p,1550,218,'C B?',w=140);tag(p,120,218,'T / S',TEAL,160)
arrow(p,[(285,239),(340,239)],TEAL,6)
for n,pt in [(69,(.43,.76)),(70,(.295,.47)),(71,(.65,.32)),(72,(.475,.42)),(73,(.875,.76))]:
    x,y=xy(*pt);badge(p,x,y,str(n))
arrow(p,[xy(.31,.47),xy(.57,.47),xy(.62,.35)],RED,4)
arrow(p,[xy(.635,.37),xy(.56,.41)],RED,4)
arrow(p,[xy(.53,.44),xy(.80,.44),xy(.85,.72)],RED,4)
arrow(p,[xy(.295,.52),xy(.295,.59),xy(.64,.59),xy(.64,.44)],BLUE,3,'[12 8]')
text(p,(90,1450,1910,1515),'Keep a protected route between stair landings. Do not use the mechanical/PV layout as a temporary storage rating. Final screens and canopies must not trap equipment.',21,True,BLUE)
for j,row in enumerate(rows[68:]):
    yy=235+j*200;badge(p,2010,yy+16,row['step'],r=23)
    text(p,(2055,yy-7,2520,yy+63),row['group'],22,True)
    text(p,(2055,yy+66,2520,yy+177),row['action'],19)
for j,n in enumerate(range(69,75)):
    x=90+j*304;badge(p,x+24,1543,str(n),r=23)
    if j<5:arrow(p,[(x+62,1543),(x+257,1543)],RED,3)
text(p,(80,1600,1910,1640),'69 support > 70 rear headhouse > 71 front headhouse > 72 equipment > 73 final closures > 74 release / demobilize. ASSUMED stages.',18)

# packing
p=new('Container logistics | Sequence kits before cube numbers','Approximately 40 ft container; user-specified maximum cube length 39\'4\"  |  ASSUMPTION - PACKING TO BE VERIFIED','EC-15')
p.insert_image(F.Rect(90,250,1070,820),filename='C:/Users/aashd/AppData/Local/Temp/codex-clipboard-79400877-7a53-4b7b-8c04-7df9df1e948a.png')
p.insert_image(F.Rect(1170,250,2140,820),filename='C:/Users/aashd/AppData/Local/Temp/codex-clipboard-e33ec8e9-b79b-42f7-9cf4-5265980490a3.png')
text(p,(80,827,2470,906),'Supplied illustrations establish the intended container/cube concept only. They do not identify this building\'s packed panels, door clearance, cube weight, handling system or tie-down arrangement. Do not lift a complete cube as one load without a designed lifting method.',23)
stages=['OFF-SITE HOLD','T: CALL-OFF','S: INSPECT / RIG','C: DIRECT LIFT','RELEASED CELL']
for j,s in enumerate(stages):
    x=80+j*500;tag(p,x,955,s,TEAL,385)
    if j<4:arrow(p,[(x+395,976),(x+478,976)],TEAL,6)
para(p,90,1060,750,'Planning kits, not invented cubes','Each level has G1-G6 cell kits, G7 residual partitions and G8 overhead framing. A kit may span several cubes; a cube may contain multiple kits only if extraction remains compatible with the sequence.',23,245)
para(p,920,1060,750,'Extraction precedes erection','For an end-door container, verify the actual first-out item against the first-needed kit. Retain dunnage/restraints until the remaining pack is stable. Separate independent late closures if they would be buried behind earlier bundles.',23,245)
para(p,1750,1060,750,'39\'4\" is not a wall-panel length','The limit applies to the user\'s cube envelope. Check clear internal/door geometry, bracing and handling allowances. A 39\'4\" shear-wall label on a structural plan is not proof of one transportable panel.',23,245)
text(p,(90,1375,2490,1470),'Required manifest: cube ID > extraction position > floor/step > shop panel IDs > gross dimensions and weight > center of gravity/pick points > restraint release order > delivery orientation > receiving cell > special handling.',24,True)
text(p,(90,1510,2490,1610),'No container count, panel count, packed cube dimensions beyond the supplied length limit, lift weight, or assumed bulk deck-storage allowance is assigned. Field staging must fit alongside crane/traffic controls or move off-site.',24,True,RED)

# replay
p=new('Constructability replay | What changes after each group','Conditional qualitative replay of the proposed groups  |  Not a crane simulation, panel collision model or temporary-stability calculation','EC-16')
headers=['State reached','New obstruction / condition','What the next step must prove']
widths=[460,895,1085];x0=75; y=240
for j,h in enumerate(headers):
    x=x0+sum(widths[:j]);box(p,(x,y,x+widths[j],y+58),fill=NAVY);text(p,(x+16,y+14,x+widths[j]-16,y+56),h,23,True,(1,1,1))
replay=[
('01-04 complete','Excavation, structural supports, parking voids, access and equipment interfaces now govern the work surface.','Verify first cell support, anchors, crane envelope and vendor routes before lifting.'),
('Each floor G1','Rear far-side corner/returns now obstruct low-level rear transfer.','G2 arrives from above into the middle receiving cell; do not route it through the completed rear cell.'),
('Each floor G2','Far rear/middle walls and transverse pieces stand.','All large middle-cell internals are in before G3 closes the near side; check hook and rigging withdrawal.'),
('Each floor G3','Middle near-side wall group has reduced lateral maneuvering room.','G4 is independently top-delivered to the rear near cell; inspect connecting faces before the last return.'),
('Each floor G4 / R','Rear/middle work has reached a stable stop; B may be needed for frontage.','Secure all installed work; remove suspended loads, release travel route and re-establish B setup. Front cell remains open.'),
('Each floor G5','Far-front group now obstructs access from the neighbor edge.','G6 receives from the street side/top. Install large shaft, stair and front-cell pieces before closing its near return.'),
('Each floor G6 / G7','Final crane-delivered wall return and residual partitions are complete.','Full kit reconciliation and connection inspection. A missing trapped piece stops the pre-deck release.'),
('Each floor G8','Joists/diaphragm close overhead receiving space in the accepted cell.','No later large piece may depend on that route. Next level begins only after structural capacity and stability release.'),
('69-74 roof','Head-houses, equipment and final screens progressively remove roof maneuvering space.','Complete large deliveries before permanent screen closure; engineer releases temporary support removal and demobilization.')]
yy=298
for k,row in enumerate(replay):
    for j,s in enumerate(row):
        x=x0+sum(widths[:j]);box(p,(x,yy,x+widths[j],yy+132),fill=LIGHT if k%2==0 else (1,1,1),color=(.8,.83,.85));text(p,(x+16,yy+17,x+widths[j]-16,yy+125),s,21,j==0)
    yy+=132
text(p,(80,1522,2480,1625),'Reorder applied: the plan does not close the entire perimeter first and then attempt to feed large interior panels through finished openings. Interior large pieces are included in their cell before closure. Remaining geometric, lifting and stability checks are HOLD items, not claimed passes.',23,True,RED)

# holds
p=new('Release register | Resolve before fabrication or erection','FIELD VERIFY includes engineer/vendor verification and document reconciliation, not only a site measurement','EC-17')
holds=[
('RFI-01','L8 / roof structural mapping','EOR + architect','Provide the governing L8 framing and roof/headhouse support plans. S1.2-S1.8 name floors 1-7; S1.9 is named roof. Do not interpolate a structural story.'),
('RFI-02','Floor and lateral system','EOR','Reconcile S0.1 composite deck/concrete and moment-frame narrative with Megaboard, CFS bearing/shear walls and details on S1.x / S3.x. Issue the construction-stage stability sequence.'),
('RFI-03','Shop-panel and closure map','Livio + erector + EOR','Provide panel tags, joints, weights, pick points, loadbearing/shear status, connection access and approved local closure returns. Map every panel exactly once to a step.'),
('RFI-04','Crane A/B and ground support','Crane planner + geotech + shoring EOR','Prove actual gross lift loads, chart capacity at all radii/heights, boom/rigging clearance, reactions, mats, utilities and excavation surcharge. Verify B or demonstrate full A coverage.'),
('RFI-05','Trees and site constraints','Surveyor + arborist + GC','Reconcile aerial #5/#6 with civil #5/#6 and landscape #4/#6; set approved TPZs and canopy clearances. Do not size protection from the illustration circles.'),
('RFI-06','Truck / ROW / public routes','GC + traffic planner + authorities','Obtain working-zone permissions and approved traffic/pedestrian arrangements. Prove truck turning, queuing, offload fit and crane mobilization. Preserve easement and neighbor access.'),
('RFI-07','Parking, elevators and services','Vendors + MEP + GC','Resolve automated parking count/layout revisions, delivery openings and route timing; elevator overrun and stair numbering conflicts; transformer and joint-trench work.'),
('RFI-08','Packing / roof / weather','Livio + vendors + crane planner','Release extraction manifest, cube dimensions/weights and supports; roof equipment lift data; panel wind/handling limits; stop/recovery procedure. Do not assign numerical limits from this concept.')]
for i,(rid,topic,owner,body) in enumerate(holds):
    y=235+i*169;box(p,(75,y,2505,y+153),fill=LIGHT if i%2==0 else (1,1,1),color=(.8,.83,.85))
    text(p,(95,y+19,270,y+65),rid,26,True,RED);text(p,(295,y+16,945,y+66),topic,25,True)
    text(p,(295,y+80,945,y+137),owner,20,False,GREY);text(p,(975,y+18,2480,y+138),body,23)

# source evidence
p=new('Evidence register | Scope, confidence and source limitations','Repository downloads verified against GitHub blob SHA-1 values  |  Page references are PDF page numbers, counted from 1','EC-18')
para(p,85,235,1170,'CONFIRMED drawing evidence','Reference: one annotated Cupertino sheet. Target: 215-page permit compilation. Reviewed relevant architectural plans, elevations and sections; structural plans/connection details; civil access/utilities; landscape trees; shoring and parking/elevator interfaces. MEP/energy material was indexed and consulted selectively, not subjected to a full discipline design review.',24,270)
para(p,1340,235,1170,'Confidence rules','CONFIRMED = directly visible in a supplied project document. PROBABLE = inference from the reference or converging evidence. ASSUMED = proposed sequencing, zoning or logistics. FIELD VERIFY = unresolved information requiring an accountable field, design or vendor decision. All 74 proposed steps are ASSUMED; holds remain open.',24,270)
para(p,85,560,1170,'Source precedence','Use permit dimensions and released coordinated drawings. Imagery supports adjacency and access awareness only. Rev B adds an independent Esri World Imagery cross-check (EC-03A) retrieved 29 SEP 2026; its capture date is not verified, so the supplied annotated aerial (EC-01) remains the closer-in-time site reference. Direct Google Earth access is unavailable to automation.',24,260)
para(p,1340,560,1170,'Other discrepancies affecting coordination','A1.0 stair numbering is reversed relative to A1.1/upper floor plans; use the floor-plan positions until reconciled. T1.1 parking summary differs from later vendor schedules. A4.1 overall height and elevator-top level are different labels/datums; verify actual lifting elevation. These items are not silently corrected in the source.',24,260)
text(p,(85,880,2490,942),'Key project sources',29,True)
sources=[
 'T1.1 p2: project scope. A1.0 p15: site. A1.1 p16: ground floor. A1.1A p17: basement. A1.2-A1.8 pp18-24: upper floors.',
 'A1.9-A1.10 pp25-26: roof. A4.1-A4.4 pp33-36: elevations. A5.1-A5.4 pp38-41: sections. A7.1-A7.3 pp42-44: assemblies/offsite system.',
 'S0.1-S0.2 pp47-48: structural notes. S1.0-S1.9 pp49-58: support and framing plans. S3.0-S6.1 pp61-71: framing and connection details.',
 'C2.0 p75: demolition/retained trees/utilities/easement. ER-1 p90: construction entrance. L1.01 p98 and L3.01 p110: site and trees.',
 'QA sheets pp177-181: parking interfaces. S1 p182: shoring concept. Elevator sheets pp183-214 marked preliminary. Joint trench p215.'
]
for i,s in enumerate(sources):text(p,(90,955+i*72,2490,1016+i*72),s,22)
text(p,(85,1337,2490,1385),'External practice references (not a project lift approval)',27,True)
urls=[('California DIR - load ratings / load handling','https://www.dir.ca.gov/title8/4923.html'),('California DIR - handling loads','https://www.dir.ca.gov/title8/4999.html'),('California DIR - power-line assessment','https://www.dir.ca.gov/title8/5003_1.html'),('Caltrans - encroachment permit manual','https://dot.ca.gov/programs/traffic-operations/ep/ep-manual')]
for i,(s,u) in enumerate(urls):
    y=1400+i*47;text(p,(90,y,2470,y+44),s+'  |  '+u,20)
    p.insert_link({'kind':F.LINK_URI,'from':F.Rect(90,y,2470,y+40),'uri':u})

# detailed 74-step register: all rows and full replay are supplied also as CSV.
colw=[75,340,480,140,220,580,615]
heads=['STEP','PANEL / GROUP','ACTION','CRANE','MATERIAL','WHY / CHANGED STATE','RISK / NEXT CHECK']
for start in range(0,len(rows),8):
    subset=rows[start:start+8];p=new(f'Sequence register | {subset[0]["step"]}-{subset[-1]["step"]}','Exact IDs match the annotated sheets  |  A/B are conditional candidates  |  All material cube assignments: ASSUMPTION - PACKING TO BE VERIFIED',f'SR-{start//8+1:02}')
    x=70;y=230
    for ww,hh in zip(colw,heads):box(p,(x,y,x+ww,y+62),fill=NAVY);text(p,(x+9,y+15,x+ww-9,y+60),hh,18,True,(1,1,1));x+=ww
    y+=62
    for k,r in enumerate(subset):
        vals=[r['step'],r['group'],r['action'],r['crane'],r['material'],r['reason']+'\nAFTER: '+r['after'],r['risk']+'\nNEXT: '+r['next_check']]
        x=70
        for j,(ww,ss) in enumerate(zip(colw,vals)):
            box(p,(x,y,x+ww,y+159),fill=LIGHT if k%2==0 else (1,1,1),color=(.80,.83,.85));text(p,(x+10,y+14,x+ww-10,y+151),ss,18,j==0);x+=ww
        y+=159
    if start==72:
        text(p,(80,690,2490,748),'Lift-plan handoff worksheet - complete outside this concept before release',29,True)
        text(p,(80,759,2480,842),'For every shop-panel or assembly pick, document the actual data below. Test both pick and set locations and the full swept route. Ground-level plan distance alone does not establish crane feasibility.',23)
        ww=[360,330,330,440,460,520]; hh=['CASE','GROSS LOAD / RIGGING','PICK / SET COORDS','MAX RADIUS / HOOK HEIGHT','OBSTACLES / SUPPORT','CHART / APPROVAL RECORD']
        xx=80
        for wi,hi in zip(ww,hh):
            box(p,(xx,890,xx+wi,952),fill=NAVY);text(p,(xx+12,905,xx+wi-12,949),hi,18,True,(1,1,1));xx+=wi
        for k,label in enumerate(['A: far rear at highest served level','A or B: far front at highest served level','Highest headhouse / roof equipment','Final closure and remaining lift']):
            xx=80;yy=952+k*112
            for j,wi in enumerate(ww):
                box(p,(xx,yy,xx+wi,yy+112),fill=LIGHT if k%2==0 else (1,1,1),color=(.8,.83,.85));text(p,(xx+12,yy+18,xx+wi-12,yy+100),label if j==0 else 'TO BE PROVIDED',19,j==0,color=NAVY if j==0 else GREY);xx+=wi
        text(p,(80,1440,2500,1553),'Release owners: Livio / fabricator, erection contractor, structural engineer, crane planner/operator, shoring/geotechnical engineer, GC and relevant road authority. The required sign-offs depend on the final means and methods; no approval is recorded by this worksheet.',22)
    text(p,(75,1602,2500,1643),'Source and status fields for every row, plus the full changed-state / next-step checks, are included in the companion CSV. A sequence group is not a single crane pick.',18)

assert [int(r['step']) for r in rows]==list(range(1,75))
doc.set_metadata({'title':'Livio 4898 El Camino Real Erection Coordination Rev B','author':'Prepared with Hermes Agent for Livio review','subject':'Conditional erection coordination concept; not for erection','keywords':'Livio, Aron Terrace, erection sequence, concept, 74 steps, aerial cross-check'})
doc.set_toc([[1,title,i+1] for i,(code,title) in enumerate(pages)])
path=OUT/'Livio_4898_El_Camino_Erection_Coordination_RevB.pdf'
doc.save(path,garbage=4,deflate=True)
with (OUT/'Livio_4898_El_Camino_Sequence_Register.csv').open('w',newline='',encoding='utf-8-sig') as f:
    cw=csv.DictWriter(f,fieldnames=list(rows[0]));cw.writeheader();cw.writerows(rows)
(WORK/'sequence-data.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
(WORK/'page-index.json').write_text(json.dumps(pages,indent=2),encoding='utf-8')
print('SAVED',path,'pages',len(doc),'steps',len(rows),'bytes',path.stat().st_size)
for i,p in enumerate(doc):
    p.get_pixmap(matrix=F.Matrix(.52,.52)).save(WORK/f'qa-{i+1:02}.png')
print('Rendered all pages for QA')
