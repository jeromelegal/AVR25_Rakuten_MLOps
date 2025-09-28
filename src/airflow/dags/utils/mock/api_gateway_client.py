import logging
import random
from typing import Optional

# POSIBLE_CATEGORY = [10, 20, 30, 40, None]
POSIBLE_CATEGORY = [
    10,
    1140,
    1160,
    1180,
    1280,
    1281,
    1300,
    1301,
    1302,
    1320,
    1560,
    1920,
    1940,
    2060,
    2220,
    2280,
    2403,
    2462,
    2522,
    2582,
    2583,
    2585,
    2705,
    2905,
    40,
    50,
    60,
]

IMAGE_IN_10 = [
    "image_1311896972_product_4190489620.jpg",
    "image_1311911184_product_4121042776.jpg",
    "image_1311793245_product_433760371.jpg",
    "image_1311851792_product_1948118331.jpg",
    "image_1311862916_product_4190166918.jpg",
]
IMAGE_IN_1140 = [
    "image_1323017168_product_4232485249.jpg",
    "image_1323017051_product_4232485210.jpg",
    "image_1323104944_product_4232785242.jpg",
    "image_1323017101_product_4232485222.jpg",
    "image_1325888059_product_4243175322.jpg",
]
IMAGE_IN_1160 = [
    "image_1326011290_product_4241234833.jpg",
    "image_1326004978_product_4237034391.jpg",
    "image_1326007509_product_4056375396.jpg",
    "image_1326004965_product_4236945843.jpg",
    "image_1326004969_product_4236945847.jpg",
]
IMAGE_IN_1180 = [
    "image_1317473695_product_3392717846.jpg",
    "image_1325973862_product_4241243836.jpg",
    "image_1318071529_product_1410192005.jpg",
    "image_1325973842_product_4233761410.jpg",
    "image_1321802893_product_4227000861.jpg",
]
IMAGE_IN_1280 = [
    "image_1328821910_product_4252010799.jpg",
    "image_1328819447_product_4252010105.jpg",
    "image_1328823833_product_4252011401.jpg",
    "image_1328821943_product_4252010809.jpg",
    "image_1328810071_product_4251979116.jpg",
]
IMAGE_IN_1281 = [
    "image_1327702752_product_4248813554.jpg",
    "image_1325970741_product_4240154304.jpg",
    "image_1326711025_product_4243534589.jpg",
    "image_1325963360_product_4237034369.jpg",
    "image_1326438549_product_4245268902.jpg",
]
IMAGE_IN_1300 = [
    "image_1325958809_product_4234337337.jpg",
    "image_1325958808_product_4234337336.jpg",
    "image_1325966939_product_4239813041.jpg",
    "image_1327549698_product_4245331344.jpg",
    "image_1325099712_product_4240377375.jpg",
]
IMAGE_IN_1301 = [
    "image_1321336624_product_4225064269.jpg",
    "image_1318413041_product_4218867607.jpg",
    "image_1318413037_product_4218867605.jpg",
    "image_1320580409_product_4225145602.jpg",
    "image_1318473465_product_846184477.jpg",
]
IMAGE_IN_1302 = [
    "image_1327706770_product_4248815875.jpg",
    "image_1327454175_product_4248023458.jpg",
    "image_1327702675_product_4248813245.jpg",
    "image_1327085195_product_4246902397.jpg",
    "image_1327702721_product_4248813249.jpg",
]
IMAGE_IN_1320 = [
    "image_1326901422_product_4177075894.jpg",
    "image_1328373699_product_3732839975.jpg",
    "image_1326881090_product_4176506063.jpg",
    "image_1327085593_product_4197351303.jpg",
    "image_1326964668_product_4008640697.jpg",
]
IMAGE_IN_1560 = [
    "image_1324661046_product_4238024360.jpg",
    "image_1324632021_product_4237810153.jpg",
    "image_1324209600_product_4150899992.jpg",
    "image_1324249194_product_4236596965.jpg",
    "image_1324165816_product_4236353706.jpg",
]
IMAGE_IN_1920 = [
    "image_1323629988_product_4231864961.jpg",
    "image_1323629596_product_4231864921.jpg",
    "image_1323629115_product_4231864845.jpg",
    "image_1323628534_product_4231864781.jpg",
    "image_1323629684_product_4231864929.jpg",
]
IMAGE_IN_1940 = [
    "image_1314090820_product_4201687950.jpg",
    "image_1313198832_product_4198225225.jpg",
    "image_1317279654_product_4212610948.jpg",
    "image_1323315938_product_4233575174.jpg",
    "image_1313723394_product_4198035351.jpg",
]
IMAGE_IN_2060 = [
    "image_1324673133_product_4238135222.jpg",
    "image_1324681656_product_4238135918.jpg",
    "image_1324695510_product_4238137700.jpg",
    "image_1324700026_product_4238138124.jpg",
    "image_1324698535_product_4238137940.jpg",
]
IMAGE_IN_2220 = [
    "image_1324290202_product_4235890711.jpg",
    "image_1324302033_product_4235891353.jpg",
    "image_1324300142_product_4235891120.jpg",
    "image_1324302400_product_4235891366.jpg",
    "image_1324308052_product_4235891531.jpg",
]
IMAGE_IN_2280 = [
    "image_1307650044_product_4171534238.jpg",
    "image_1307245924_product_4169004705.jpg",
    "image_1311167007_product_4185723382.jpg",
    "image_1309166049_product_4175270605.jpg",
    "image_1309172914_product_4177916059.jpg",
]
IMAGE_IN_2403 = [
    "image_1311752450_product_4189542192.jpg",
    "image_1311709553_product_4189040604.jpg",
    "image_1311740748_product_4189029478.jpg",
    "image_1311873022_product_4190384754.jpg",
    "image_1311727350_product_4189542154.jpg",
]
IMAGE_IN_2462 = [
    "image_1326016835_product_4233820095.jpg",
    "image_1325927501_product_4242974256.jpg",
    "image_1326151938_product_4244021259.jpg",
    "image_1326151947_product_4244021263.jpg",
    "image_1325981766_product_3513322578.jpg",
]
IMAGE_IN_2522 = [
    ".DS_Store",
    "image_1311282268_product_4186852021.jpg",
    "image_1310936418_product_4185654159.jpg",
    "image_1311385418_product_4187377747.jpg",
    "image_1311388941_product_4187379595.jpg",
    "image_1309786432_product_4180459979.jpg",
]
IMAGE_IN_2582 = [
    "image_1323152359_product_4232954438.jpg",
    "image_1323542232_product_4234329056.jpg",
    "image_1323152464_product_4232954456.jpg",
    "image_1323153094_product_4232954624.jpg",
    "image_1323152715_product_4232954520.jpg",
]
IMAGE_IN_2583 = [
    "image_1324229325_product_4233625648.jpg",
    "image_1324254943_product_4233637820.jpg",
    "image_1324229304_product_4233625647.jpg",
    "image_1324239033_product_4233642435.jpg",
    "image_1324266545_product_4233651354.jpg",
]
IMAGE_IN_2585 = [
    "image_1323284537_product_4232535372.jpg",
    "image_1323616858_product_4234598026.jpg",
    "image_1323283760_product_4232535117.jpg",
    "image_1323802283_product_4234916545.jpg",
    "image_1323802489_product_4234921179.jpg",
]
IMAGE_IN_2705 = [
    "image_1311637836_product_974120305.jpg",
    "image_1311834880_product_1746715544.jpg",
    "image_1311459680_product_278517494.jpg",
    "image_1311637439_product_278681062.jpg",
    "image_1311637892_product_1192648725.jpg",
]
IMAGE_IN_2905 = [
    "image_1322071029_product_4230260492.jpg",
    "image_1322071023_product_4230260491.jpg",
    "image_1318031891_product_4216563333.jpg",
    "image_1323709980_product_4234905265.jpg",
    "image_1322071035_product_4230260493.jpg",
]
IMAGE_IN_40 = [
    "image_1323895136_product_4234091570.jpg",
    "image_1324384878_product_4237073471.jpg",
    "image_1324203522_product_4236143316.jpg",
    "image_1323894858_product_4234091564.jpg",
    "image_1323894622_product_4234091560.jpg",
]
IMAGE_IN_50 = [
    "image_1325976183_product_4236147267.jpg",
    "image_1325976184_product_4236085069.jpg",
    "image_1325276870_product_4240795440.jpg",
    "image_1325976203_product_4237481401.jpg",
    "image_1325976215_product_4238480169.jpg",
]
IMAGE_IN_60 = [
    "image_1318166506_product_109417906.jpg",
    "image_1321638214_product_4228447241.jpg",
    "image_1321405697_product_4227191850.jpg",
    "image_1316320754_product_4200885122.jpg",
    "image_1322862417_product_4229104564.jpg",
]


class MockAPIGatewayClient:
    _username: str
    _password: str
    _base_url: str
    _email: str

    def __init__(self, username: str, password: str, email: str, base_url: str):
        self._username = username
        self._password = password
        self._email = email
        self._base_url = base_url
        self._token = None

    def signup(self):
        logging.info("Signing up")

    def login(self):
        logging.info("Login")

    def get_category_from_image_id(self, image_id: str) -> Optional[int]:
        if image_id in IMAGE_IN_10:
            return 10
        if image_id in IMAGE_IN_1140:
            return 1140
        if image_id in IMAGE_IN_1160:
            return 1160
        if image_id in IMAGE_IN_1180:
            return 1180
        if image_id in IMAGE_IN_1280:
            return 1280
        if image_id in IMAGE_IN_1281:
            return 1281
        if image_id in IMAGE_IN_1300:
            return 1300
        if image_id in IMAGE_IN_1301:
            return 1301
        if image_id in IMAGE_IN_1302:
            return 1302
        if image_id in IMAGE_IN_1320:
            return 1320
        if image_id in IMAGE_IN_1560:
            return 1560
        if image_id in IMAGE_IN_1920:
            return 1920
        if image_id in IMAGE_IN_1940:
            return 1940
        if image_id in IMAGE_IN_2060:
            return 2060
        if image_id in IMAGE_IN_2220:
            return 2220
        if image_id in IMAGE_IN_2280:
            return 2280
        if image_id in IMAGE_IN_2403:
            return 2403
        if image_id in IMAGE_IN_2462:
            return 2462
        if image_id in IMAGE_IN_2522:
            return 2522
        if image_id in IMAGE_IN_2582:
            return 2582
        if image_id in IMAGE_IN_2583:
            return 2583
        if image_id in IMAGE_IN_2585:
            return 2585
        if image_id in IMAGE_IN_2705:
            return 2705
        if image_id in IMAGE_IN_2905:
            return 2905
        if image_id in IMAGE_IN_40:
            return 40
        if image_id in IMAGE_IN_50:
            return 50
        if image_id in IMAGE_IN_60:
            return 60
        return random.choice(POSIBLE_CATEGORY)
