BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "attachment" (
	"id"	INTEGER NOT NULL,
	"filename"	VARCHAR(255) NOT NULL,
	"item_id"	INTEGER,
	"created_at"	DATETIME,
	PRIMARY KEY("id"),
	FOREIGN KEY("item_id") REFERENCES "item"("id")
);
CREATE TABLE IF NOT EXISTS "category" (
	"id"	INTEGER NOT NULL,
	"name"	VARCHAR(50) NOT NULL,
	"icon"	VARCHAR(255) NOT NULL,
	PRIMARY KEY("id"),
	UNIQUE("name")
);
CREATE TABLE IF NOT EXISTS "item" (
	"id"	INTEGER NOT NULL,
	"name"	VARCHAR(80) NOT NULL,
	"description_hu"	TEXT,
	"description_en"	TEXT,
	"created_at"	DATETIME,
	"uploader_id"	INTEGER NOT NULL,
	"active"	BOOLEAN,
	"type"	VARCHAR(20),
	"category_id"	INTEGER,
	"location"	VARCHAR(200),
	"is_closed"	BOOLEAN,
	PRIMARY KEY("id"),
	FOREIGN KEY("category_id") REFERENCES "category"("id"),
	FOREIGN KEY("uploader_id") REFERENCES "user"("id")
);
CREATE TABLE IF NOT EXISTS "messages" (
	"id"	INTEGER NOT NULL,
	"sender_id"	INTEGER NOT NULL,
	"receiver_id"	INTEGER NOT NULL,
	"content"	TEXT,
	"created_at"	DATETIME,
	"seen"	BOOLEAN,
	"attachment_id"	INTEGER,
	PRIMARY KEY("id"),
	FOREIGN KEY("attachment_id") REFERENCES "attachment"("id"),
	FOREIGN KEY("receiver_id") REFERENCES "user"("id"),
	FOREIGN KEY("sender_id") REFERENCES "user"("id")
);
CREATE TABLE IF NOT EXISTS "password_reset_token" (
	"id"	INTEGER NOT NULL,
	"user_id"	INTEGER NOT NULL,
	"token"	VARCHAR(64) NOT NULL,
	"created_at"	DATETIME,
	"used"	BOOLEAN,
	PRIMARY KEY("id"),
	UNIQUE("token"),
	FOREIGN KEY("user_id") REFERENCES "user"("id")
);
CREATE TABLE IF NOT EXISTS "punishments" (
	"id"	INTEGER NOT NULL,
	"user_id"	INTEGER NOT NULL,
	"reason"	TEXT,
	"expires_at"	DATETIME,
	"created_at"	DATETIME,
	"is_ban"	BOOLEAN,
	"is_warning"	BOOLEAN,
	"is_suspension"	BOOLEAN,
	PRIMARY KEY("id"),
	FOREIGN KEY("user_id") REFERENCES "user"("id")
);
CREATE TABLE IF NOT EXISTS "reports" (
	"id"	INTEGER NOT NULL,
	"reporter_id"	INTEGER NOT NULL,
	"item_id"	INTEGER,
	"user_id"	INTEGER,
	"reason"	TEXT,
	"content"	TEXT,
	"created_at"	DATETIME,
	"pending"	BOOLEAN,
	PRIMARY KEY("id"),
	FOREIGN KEY("item_id") REFERENCES "item"("id"),
	FOREIGN KEY("reporter_id") REFERENCES "user"("id"),
	FOREIGN KEY("user_id") REFERENCES "user"("id")
);
CREATE TABLE IF NOT EXISTS "two_factor_auth" (
	"id"	INTEGER NOT NULL,
	"user_id"	INTEGER NOT NULL,
	"secret_key"	VARCHAR(32) NOT NULL,
	PRIMARY KEY("id"),
	FOREIGN KEY("user_id") REFERENCES "user"("id")
);
CREATE TABLE IF NOT EXISTS "user" (
	"id"	INTEGER NOT NULL,
	"username"	VARCHAR(80) NOT NULL,
	"password_hash"	VARCHAR(128) NOT NULL,
	"created_at"	DATETIME,
	"email"	VARCHAR(80),
	"profile_picture"	INTEGER,
	"name"	VARCHAR(80),
	"birthdate"	DATE,
	"phone_number"	VARCHAR(20),
	"phone_number_is_private"	BOOLEAN,
	"address"	VARCHAR(200),
	"address_is_private"	BOOLEAN,
	"_2fa_enabled"	BOOLEAN,
	"_2fa_id"	INTEGER,
	"role"	VARCHAR(20) NOT NULL,
	UNIQUE("email"),
	PRIMARY KEY("id"),
	UNIQUE("username"),
	FOREIGN KEY("_2fa_id") REFERENCES "two_factor_auth"("id"),
	FOREIGN KEY("profile_picture") REFERENCES "attachment"("id")
);
INSERT INTO "attachment" ("id","filename","item_id","created_at") VALUES (1,'1_1776959810.32385_1000027665.jpg',NULL,'2026-04-23 17:56:50.331941');
INSERT INTO "attachment" ("id","filename","item_id","created_at") VALUES (2,'2_1776960017.945802_1000026896.jpg',NULL,'2026-04-23 18:00:17.955953');
INSERT INTO "attachment" ("id","filename","item_id","created_at") VALUES (3,'a8c16cefc23b445ea0d4d17df7cc6467.jpg',1,'2026-04-23 18:04:53.695773');
INSERT INTO "attachment" ("id","filename","item_id","created_at") VALUES (4,'f3652724fff74345b0008c77c4caf11f.jpg',1,'2026-04-23 18:04:53.695773');
INSERT INTO "attachment" ("id","filename","item_id","created_at") VALUES (5,'d2dc1fa806ce4f138145cde43d2bd926.jpg',1,'2026-04-23 18:04:53.695773');
INSERT INTO "attachment" ("id","filename","item_id","created_at") VALUES (6,'7efb1835975a4192bf43472693889221.jpg',1,'2026-04-23 18:04:53.695773');
INSERT INTO "attachment" ("id","filename","item_id","created_at") VALUES (7,'55e8fbd8101f4f21a20fbb45aac13cc5.jpg',1,'2026-04-23 18:04:53.695773');
INSERT INTO "attachment" ("id","filename","item_id","created_at") VALUES (8,'44beeca9783c40ab97b5df61abc897cf.jpg',1,'2026-04-23 18:04:53.695773');
INSERT INTO "attachment" ("id","filename","item_id","created_at") VALUES (9,'333851a23c544153b609c15c4c449925.jpg',1,'2026-04-23 18:04:53.695773');
INSERT INTO "attachment" ("id","filename","item_id","created_at") VALUES (10,'875a2a431e0c46f9980709fe5e62aa29.jpg',1,'2026-04-23 18:04:53.695773');
INSERT INTO "attachment" ("id","filename","item_id","created_at") VALUES (11,'660d7f400cfa4a0a88cf961531496786.jpg',1,'2026-04-23 18:04:53.695773');
INSERT INTO "attachment" ("id","filename","item_id","created_at") VALUES (12,'563fd2275a2942d7acc44f091e225380.jpg',1,'2026-04-23 18:04:53.695773');
INSERT INTO "attachment" ("id","filename","item_id","created_at") VALUES (13,'6d6e8a4cc632450f9f1330c7c9c3539c.jpg',2,'2026-04-23 18:27:54.553711');
INSERT INTO "attachment" ("id","filename","item_id","created_at") VALUES (14,'4_1776962093.062482_nelli1.jpg',NULL,'2026-04-23 18:34:53.063480');
INSERT INTO "attachment" ("id","filename","item_id","created_at") VALUES (15,'d9ee4e4eca5c4d88a664c48e9777462c.jpg',3,'2026-04-23 18:38:39.743398');
INSERT INTO "attachment" ("id","filename","item_id","created_at") VALUES (16,'bc1070b99c4845ac972b9a2af9cbe6a9.jpg',3,'2026-04-23 18:38:39.743398');
INSERT INTO "attachment" ("id","filename","item_id","created_at") VALUES (17,'2359110e9af74186b6be3dd5ff2d47ec.jpg',3,'2026-04-23 18:38:39.743398');
INSERT INTO "attachment" ("id","filename","item_id","created_at") VALUES (18,'6383ab6568534815827d5c010df8fb32.jpg',3,'2026-04-23 18:38:39.743398');
INSERT INTO "attachment" ("id","filename","item_id","created_at") VALUES (19,'5_1776962676.757673_ceccc.png',NULL,'2026-04-23 18:44:36.758678');
INSERT INTO "attachment" ("id","filename","item_id","created_at") VALUES (20,'16dc89298adf4abcb2ffd5f7c7f43f8d.jpg',4,'2026-04-23 18:49:51.243958');
INSERT INTO "attachment" ("id","filename","item_id","created_at") VALUES (21,'bcc93f487b87494399e13976b379498e.jpg',4,'2026-04-23 18:49:51.243958');
INSERT INTO "attachment" ("id","filename","item_id","created_at") VALUES (22,'8ad980a3b4fc4d999b5db22a6a167937.jpg',4,'2026-04-23 18:49:51.243958');
INSERT INTO "attachment" ("id","filename","item_id","created_at") VALUES (31,'04096be5b5604fe9bb96046259e761eb.jpg',6,'2026-04-23 18:56:51.624336');
INSERT INTO "attachment" ("id","filename","item_id","created_at") VALUES (32,'cc58c6943d944fa19f8c1b5528a04e66.jpg',6,'2026-04-23 18:56:51.624336');
INSERT INTO "attachment" ("id","filename","item_id","created_at") VALUES (33,'8e81667f433d406689a9f44bb0b0227e.jpg',6,'2026-04-23 18:56:51.624336');
INSERT INTO "attachment" ("id","filename","item_id","created_at") VALUES (34,'24e0a912cb744183a4abf97ac4763363.jpg',5,'2026-04-23 18:58:35.444501');
INSERT INTO "attachment" ("id","filename","item_id","created_at") VALUES (35,'1c455ddb382a4f51a4d28d332a640621.jpg',5,'2026-04-23 18:58:35.444501');
INSERT INTO "attachment" ("id","filename","item_id","created_at") VALUES (36,'7f2024896d9e4e74925672a5b2936edb.jpg',5,'2026-04-23 18:58:35.444501');
INSERT INTO "attachment" ("id","filename","item_id","created_at") VALUES (37,'45b33da0544648218d2688024389e39f.jpg',5,'2026-04-23 18:58:35.444501');
INSERT INTO "attachment" ("id","filename","item_id","created_at") VALUES (38,'5afe3f91e2d2416fbe1b065deac47d91.jpg',9,'2026-04-23 19:14:34.261457');
INSERT INTO "attachment" ("id","filename","item_id","created_at") VALUES (39,'511b583a2b7a44d18b8198dd85eb3c1d.jpg',9,'2026-04-23 19:14:34.261457');
INSERT INTO "attachment" ("id","filename","item_id","created_at") VALUES (40,'dbd0a9f9efd047dab68bfccde4404508.jpg',10,'2026-04-23 19:15:50.526004');
INSERT INTO "attachment" ("id","filename","item_id","created_at") VALUES (41,'1c4e23cb761a4992a6faf4935db7d3c4.jpeg',11,'2026-04-23 19:26:46.451160');
INSERT INTO "attachment" ("id","filename","item_id","created_at") VALUES (42,'fd52288b8c56467b912473176be4ee6e.jpg',12,'2026-04-23 19:56:10.590753');
INSERT INTO "attachment" ("id","filename","item_id","created_at") VALUES (43,'7bd06997e4d541d1943b50293d84a2d5.jpg',12,'2026-04-23 19:56:10.590753');
INSERT INTO "attachment" ("id","filename","item_id","created_at") VALUES (44,'eb6ecd48540f4582be8b1c0ca91febe6.jpg',12,'2026-04-23 19:56:10.590753');
INSERT INTO "attachment" ("id","filename","item_id","created_at") VALUES (45,'ceccbf2a12ec4cc987e8aef3c8cb1e38.jpg',13,'2026-04-23 20:04:51.860750');
INSERT INTO "attachment" ("id","filename","item_id","created_at") VALUES (46,'5bdf2b46f758451a9f175e98d6703415.jpg',14,'2026-04-23 23:58:05.510304');
INSERT INTO "attachment" ("id","filename","item_id","created_at") VALUES (47,'87dd55b3ebc64043b56b9ffea9c78966.png',14,'2026-04-23 23:58:05.510304');
INSERT INTO "attachment" ("id","filename","item_id","created_at") VALUES (48,'77a87479d9c14c2b91c37fd619a9342b.png',14,'2026-04-23 23:58:05.510304');
INSERT INTO "category" ("id","name","icon") VALUES (1,'allat','fa-paw');
INSERT INTO "category" ("id","name","icon") VALUES (2,'dokumentum','fa-file-alt');
INSERT INTO "category" ("id","name","icon") VALUES (3,'ekszer','fa-gem');
INSERT INTO "item" ("id","name","description_hu","description_en","created_at","uploader_id","active","type","category_id","location","is_closed") VALUES (1,'Katze','Elvesztettem a macskámat 2 napja. A Katze névre hallgat. Egy Bengális cicus, 2 éves, éhenkórász. Kiszökött a lakásból és azóta nem találom. Segítség!','I lost my cat two days ago. His name is Katze. He''s a two‑year‑old Bengal, always starving. He escaped from the apartment and I haven’t been able to find him since. Help!','2026-04-23 18:04:53.657375',2,1,'lost',1,'Hajdú-Bihar, Egyek',0);
INSERT INTO "item" ("id","name","description_hu","description_en","created_at","uploader_id","active","type","category_id","location","is_closed") VALUES (2,'Bagó Ördög Csoki','Keszthelyről elszökött három kutyusunk: Bagó, Ördög és Csoki.
Nagyon hiányoznak, és minden perc számít!

Barátságosak, de ijedtek lehetnek, ezért kérjük, óvatosan közelítsetek hozzájuk.
Ha bárki látta őket, vagy bármilyen információval rendelkezik, kérjük, AZONNAL jelezze!','Our three dogs have escaped from Keszthely: Bagó, Ördög, and Csoki.  
They are greatly missed, and every minute counts!  

They are friendly but may be frightened, so please approach them carefully.  
If anyone has seen them or has any information, please report it IMMEDIATELY!','2026-04-23 18:27:54.550190',3,1,'lost',1,'Zala, Keszthely',0);
INSERT INTO "item" ("id","name","description_hu","description_en","created_at","uploader_id","active","type","category_id","location","is_closed") VALUES (3,'Szürki','Debrecenben eltűnt Szürki, a cicánk.
Nagyon hiányzik, minden segítség számít!

Szürki félénk, idegenek elől elbújhat (bokrok, pincék, lépcsőházak).
Kérjük, ha látjátok, ne üldözzétek, inkább jelezzétek!','Our cat Szürki disappeared in Debrecen.  
We miss him terribly; any help is appreciated!  

Szürki is shy and may hide from strangers (in bushes, basements, stairwells).  
Please, if you see him, do not chase him—just let us know.','2026-04-23 18:38:39.736378',4,1,'lost',1,'Hajdú-Bihar, Debrecen',0);
INSERT INTO "item" ("id","name","description_hu","description_en","created_at","uploader_id","active","type","category_id","location","is_closed") VALUES (4,'Molly','Az utcán találtuk ezt a kutyust, Mollyt a biléta alapján.
Úgy tűnik, elveszhetett, és biztosan nagyon hiányzik valakinek!

Barátságos, emberekhez szokott, ezért valószínűleg van gazdija.
Szeretnénk mielőbb visszajuttatni a családjához','We found this dog, Molly, on the street based on the note. It seems she got lost, and someone must be missing her a lot!

She’s friendly and used to people, so she probably has an owner. We’d like to get her back to her family as soon as possible.','2026-04-23 18:49:51.237435',5,1,'found',1,'Budapest, Budapest',0);
INSERT INTO "item" ("id","name","description_hu","description_en","created_at","uploader_id","active","type","category_id","location","is_closed") VALUES (5,'Mimi','Eltűnt Mimi, a nyuszink. 
Nagyon hiányzik a gazdijának, és aggódunk érte!
Kérjük, ha valaki látja, jelezze, mert valószínűleg félénk és elbújhat bokrokban, kertekben, bokros részeken.','Mimi, our rabbit, has disappeared. Its owner misses it greatly, and we are worried about it! Please, if anyone sees it, let us know, as it is probably shy and may be hiding in bushes, gardens, or thicketed areas.','2026-04-23 18:51:49.426091',5,1,'lost',1,'Tolna, Bogyiszló',0);
INSERT INTO "item" ("id","name","description_hu","description_en","created_at","uploader_id","active","type","category_id","location","is_closed") VALUES (6,'Garfield macska','Egy vörös színű macskát találtunk.
Barátságosnak tűnik, valószínűleg van gazdája, aki nagyon hiányolja!','We found a red-colored cat. It looks friendly, and it probably has an owner who misses it very much.','2026-04-23 18:56:51.615295',4,1,'found',1,'Hajdú-Bihar, Balmazújváros',0);
INSERT INTO "item" ("id","name","description_hu","description_en","created_at","uploader_id","active","type","category_id","location","is_closed") VALUES (7,'Személyi igazolvány','Elhagytam a személyimet a villamoson. a nevem xy, ha valaki megtalálja kérem jelezze','I left my ID card on the tram. My name is xy; if anyone finds it, please let me know.','2026-04-23 19:10:26.371459',4,1,'lost',2,'Győr-Moson-Sopron, Beled',0);
INSERT INTO "item" ("id","name","description_hu","description_en","created_at","uploader_id","active","type","category_id","location","is_closed") VALUES (8,'Gyűrű','Elhagytam a jeggyűrűmet! Egy aranygyűrű, gyémánttal a közepén, aki megtalálja pénzjutalomban részesül!!','I left my ring! It''s a gold ring with a diamond in the center—whoever finds it will receive a cash reward!!','2026-04-23 19:11:53.024439',4,1,'lost',3,'Csongrád, Balástya',0);
INSERT INTO "item" ("id","name","description_hu","description_en","created_at","uploader_id","active","type","category_id","location","is_closed") VALUES (9,'Pedro és Pabló','Eltűnt két kis termetű kutya, Pedro és Pablo. 
Nagyon hiányoznak a gazdijuknak, minden segítség számít!

Valószínűleg megijedhettek, ezért kérjük, ha látjátok őket, ne üldözzétek, inkább jelezzétek a megadott elérhetőségen!','Two small dogs, Pedro and Pablo, have disappeared.  
Their owners miss them terribly; any help counts!  

You may be startled, so if you see them, please don’t chase them—just report them using the contact information provided.','2026-04-23 19:14:34.255458',2,1,'lost',1,'Heves, Hatvan',0);
INSERT INTO "item" ("id","name","description_hu","description_en","created_at","uploader_id","active","type","category_id","location","is_closed") VALUES (10,'Putyin','Egy puli kutyát találtunk, Putyin névre hallgat, és biléta van a nyakában.
Valószínűleg elkóborolt, és szeretnénk mielőbb visszajuttatni a gazdájához!','We found a Puli dog named Putyin, with a tag around its neck. It has probably wandered off, and we would like to return it to its owner as soon as possible.','2026-04-23 19:15:50.515467',2,1,'found',1,'Tolna, Báta',0);
INSERT INTO "item" ("id","name","description_hu","description_en","created_at","uploader_id","active","type","category_id","location","is_closed") VALUES (11,'Foltos kutya','Foltos kutyát találtunk ma az utcán, keresi gazdáját sürgősen!','We found a spotted dog on the street today, urgently looking for its owner.','2026-04-23 19:26:46.451160',3,1,'found',1,'Csongrád, Domaszék',0);
INSERT INTO "item" ("id","name","description_hu","description_en","created_at","uploader_id","active","type","category_id","location","is_closed") VALUES (12,'Vattacukor','Eltűnt egy különleges kakas, akit Vattacukornak hívnak.

Vattacukor egy barátságos, enyhén bolondos természetű kakas, aki tollazatával könnyen felismerhető. Nagyon szelíd, nem támadó, inkább kíváncsi és szeret emberek közelében lenni.','A special rooster named Vattacukor has disappeared.

Vattacukor is a friendly rooster with a slightly goofy temperament, easily recognizable by his plumage. He is very gentle, not aggressive, rather curious, and enjoys being close to people.','2026-04-23 19:56:10.576047',3,1,'lost',1,'Heves, Bükkszentmárton',0);
INSERT INTO "item" ("id","name","description_hu","description_en","created_at","uploader_id","active","type","category_id","location","is_closed") VALUES (13,'Brúno meg spacc','Eltűnt két kutyusunk: Brúno és Spacc

Brúno: nyugodtabb, kicsit „főnök” karakter, emberekkel barátságos, de határozott jelenlétű.
Spacc: energikus, gyors, kíváncsi, valószínűleg már valami új kaland közepén van.','Eltűnt két kutyusunk: Brúno és Spacc 

 Brúno: nyugodtabb, kicsit „főnök” karakter, emberekkel barátságos, de határozott jelenlétű.
 Spacc: energikus, gyors, kíváncsi, valószínűleg már valami új kaland közepén van.','2026-04-23 20:04:51.844211',3,1,'lost',1,'Heves, Boldog',0);
INSERT INTO "item" ("id","name","description_hu","description_en","created_at","uploader_id","active","type","category_id","location","is_closed") VALUES (14,'Bogyó','Eltűnt a szeretett nyuszim, Bogyó. Kérlek, ha bárki látta vagy megtalálta, azonnal jelezzen! Nagyon barátságos','My beloved rabbit Bogyó is missing. Please, if anyone has seen or found him, let me know immediately! He''s very friendly.','2026-04-23 23:58:05.494137',5,1,'lost',1,'Fejér, Baracs',0);
INSERT INTO "two_factor_auth" ("id","user_id","secret_key") VALUES (1,4,'Y7IDV5YBJH7PLJ2T2HZIUPCFAGWVNNGY');
INSERT INTO "two_factor_auth" ("id","user_id","secret_key") VALUES (2,6,'XI2N4UWEBE6SQRNRZEPGTZ5ZGKYDF73L');
INSERT INTO "two_factor_auth" ("id","user_id","secret_key") VALUES (3,7,'XUUNKOOFA5VUCAZNJOLB7MSX6RXZMHTO');
INSERT INTO "two_factor_auth" ("id","user_id","secret_key") VALUES (4,8,'PQDACX53J2JFXGCMZUQNRWFEZOSM4IVL');
INSERT INTO "two_factor_auth" ("id","user_id","secret_key") VALUES (5,9,'2OQD6BPYT26X4JQRNX7KT4MWT6Y5NPJW');
INSERT INTO "two_factor_auth" ("id","user_id","secret_key") VALUES (6,10,'3MIYV7JCEPT23XVR6JSOZANCPKHM6TIY');
INSERT INTO "two_factor_auth" ("id","user_id","secret_key") VALUES (7,11,'KNVNWUGICFKR7CXDHA5VUBBAMA2BAAQR');
INSERT INTO "two_factor_auth" ("id","user_id","secret_key") VALUES (8,12,'XAJCID5QIL4HWFPIXFOB7EUSBXFRD5LG');
INSERT INTO "user" ("id","username","password_hash","created_at","email","profile_picture","name","birthdate","phone_number","phone_number_is_private","address","address_is_private","_2fa_enabled","_2fa_id","role") VALUES (1,'admin','$2b$12$9F1QdTltcrvB91ux8sUikecl0MJTnP8err0I1GSfw/ascDeckVRL2','2026-04-23 17:52:25.535588','admin@example.com',1,'Admin','1999-04-02','123456789',1,'Füzesabony',1,0,NULL,'admin');
INSERT INTO "user" ("id","username","password_hash","created_at","email","profile_picture","name","birthdate","phone_number","phone_number_is_private","address","address_is_private","_2fa_enabled","_2fa_id","role") VALUES (2,'Laura','$2b$12$Lsu8ovNZmJdRcNiCd2UDxu1KXqfVwGxNfZ1WlhzO4xdorFttPBwBO','2026-04-23 17:52:26.807284','nreka261@gmail.com',2,'Laura','2007-07-26','+36304583538',1,'Egyek',0,0,NULL,'user');
INSERT INTO "user" ("id","username","password_hash","created_at","email","profile_picture","name","birthdate","phone_number","phone_number_is_private","address","address_is_private","_2fa_enabled","_2fa_id","role") VALUES (3,'ZigZag','$2b$12$d1mEDqy0FzvmkGJ/LW16tOCkaBQmxUFJqx7oOnrL17IsLt6Min.oO','2026-04-23 17:52:26.807284','zigzag@gmail.com',NULL,'Dávid','2000-07-10','12345678',1,'Keszhely',0,0,NULL,'user');
INSERT INTO "user" ("id","username","password_hash","created_at","email","profile_picture","name","birthdate","phone_number","phone_number_is_private","address","address_is_private","_2fa_enabled","_2fa_id","role") VALUES (4,'szurkimissing','$2b$12$8u27017vwH51DIMfJcdNouEfCucDqQBcQaqkD4uzPpxMxM0r9GeQC','2026-04-23 17:52:26.807284','szurkihelp@gmail.com',14,'Nelli','2012-02-14','12304520',1,'Egyek',0,0,NULL,'user');
INSERT INTO "user" ("id","username","password_hash","created_at","email","profile_picture","name","birthdate","phone_number","phone_number_is_private","address","address_is_private","_2fa_enabled","_2fa_id","role") VALUES (5,'RicsiRich','$2b$12$wsQq.VfFHeCyKiLDNu4MjOMMoh5Jq7iwr42Hv1vrIkvYj0rVVUgRe','2026-04-23 17:52:26.807284','molly@gmail.com',19,'Richárd','2026-01-16','15786225',1,'Budapest',0,0,NULL,'user');
INSERT INTO "user" ("id","username","password_hash","created_at","email","profile_picture","name","birthdate","phone_number","phone_number_is_private","address","address_is_private","_2fa_enabled","_2fa_id","role") VALUES (6,'asdasd','$2b$12$H0mV8knn0lpFd6KsP2QesuMirkNcNseuvy6nfAefexGCsM7upgPf2','2026-04-23 20:25:35.820921','asd@asd.om',NULL,'asdsad','2026-03-05','12345678',1,'asd',0,1,2,'user');
INSERT INTO "user" ("id","username","password_hash","created_at","email","profile_picture","name","birthdate","phone_number","phone_number_is_private","address","address_is_private","_2fa_enabled","_2fa_id","role") VALUES (7,'Lauraasd','$2b$12$j.9ZZUAYieBfsf.AfpQcdum32rzkxbMeOPU1WFkAAJRbjSofremzC','2026-04-23 21:31:21.885970','nrekaasdasd261@gmail.com',NULL,NULL,NULL,NULL,1,NULL,0,0,NULL,'user');
INSERT INTO "user" ("id","username","password_hash","created_at","email","profile_picture","name","birthdate","phone_number","phone_number_is_private","address","address_is_private","_2fa_enabled","_2fa_id","role") VALUES (8,'LauraNagy','$2b$12$SEvFBD3dusrklH1nDsxWEuiMkRu8huoPr2J3yQLn5xQbP0.FWxX9u','2026-04-24 08:38:10.396847','laaura768@gmail.com',NULL,'Lau','2026-02-27','12642056',1,'Asd',0,1,4,'user');
INSERT INTO "user" ("id","username","password_hash","created_at","email","profile_picture","name","birthdate","phone_number","phone_number_is_private","address","address_is_private","_2fa_enabled","_2fa_id","role") VALUES (9,'LauraNagy23233','$2b$12$ZUe.30iVpYSuyiK0Pk7chO8H/aY7vG4O.ifncFPHlMpLSLWq41cwC','2026-04-24 08:38:10.396847','nglahura@gmail.com',NULL,NULL,NULL,NULL,1,NULL,0,1,5,'user');
INSERT INTO "user" ("id","username","password_hash","created_at","email","profile_picture","name","birthdate","phone_number","phone_number_is_private","address","address_is_private","_2fa_enabled","_2fa_id","role") VALUES (10,'LauraNagy23','$2b$12$o6stX4cZMZcHkum9JUL7g.BsHos/yoI9SqO2i0dHDOxHc4orIgGK2','2026-04-24 09:12:56.217545','asd@asd.com',NULL,'asdasd','2026-04-15','123123123',1,'Asd',0,0,NULL,'user');
INSERT INTO "user" ("id","username","password_hash","created_at","email","profile_picture","name","birthdate","phone_number","phone_number_is_private","address","address_is_private","_2fa_enabled","_2fa_id","role") VALUES (11,'test12','$2b$12$K6QUDamWAW0hLMMF7yRp5e6fZJKtPR8ohaAxkjT5UuHBX8BaG6d..','2026-04-24 09:12:56.217545','test@test.com',NULL,'asdasd','2026-04-07','8546579',1,'Asd',0,0,NULL,'user');
INSERT INTO "user" ("id","username","password_hash","created_at","email","profile_picture","name","birthdate","phone_number","phone_number_is_private","address","address_is_private","_2fa_enabled","_2fa_id","role") VALUES (12,'asd12','$2b$12$fdCKEn6pKGkg.pDdKDpse.bb016WysNiVf5NHkIZ/BevzrkeiI3u6','2026-04-24 09:12:56.217545','asd@asasdd.com',NULL,'wqe','2026-04-10','8685482',1,'asd',0,0,NULL,'user');
COMMIT;
