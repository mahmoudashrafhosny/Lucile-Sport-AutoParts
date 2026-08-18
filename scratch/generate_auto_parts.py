import pandas as pd
import random

auto_parts = [
    # فلاتر وزيوت
    {
        "title": "زيت موتور شيل هيليكس الكس Ultra 5W-40 - 4 ليتر",
        "category": "فلاتر وزيوت",
        "product_description": "زيت تخليقي بالكامل يوفر أقصى حماية للمحرك في درجات الحرارة العالية الشديدة ومناسب لجميع السيارات الحديثة في مصر.",
        "rating": 4.9, "ratings_count": 340, "initial_price": 2200, "discount": 10, "final_price": 1980,
        "seller_name": "الفرسان لأوتو زيت", "what_customers_said": "زيت ممتاز وأصلي 100% صوت المحرك بقى أنعم كتير"
    },
    {
        "title": "زيت موتور موبيل 1Mobil 1 ESP 5W-30 - 4 ليتر",
        "category": "فلاتر وزيوت",
        "product_description": "زيت محرك تخليقي متطور موصى به لسيارات هيونداي وكيا وتويوتا ونيسان.",
        "rating": 4.8, "ratings_count": 290, "initial_price": 2400, "discount": 12, "final_price": 2112,
        "seller_name": "التوفيكية لأوتو", "what_customers_said": "أصلية وحافظت على حرارة الموتور ثابتة"
    },
    {
        "title": "فلتر زيت أصلي هيونداي / كيا (Hyundai Accent/Elantra/Cerato)",
        "category": "فلاتر وزيوت",
        "product_description": "فلتر زيت أصلي OEM هيونداي وكيا يحافظ على ضغط الزيت ونقاء المحرك من الشوائب.",
        "rating": 4.7, "ratings_count": 185, "initial_price": 450, "discount": 15, "final_price": 382,
        "seller_name": "الكوري لقطع الغيار", "what_customers_said": "فلتر كوري أصلي بالختم"
    },
    {
        "title": "فلتر هواء محرك تويوتا كورولا (Toyota Corolla 2014-2023)",
        "category": "فلاتر وزيوت",
        "product_description": "فلتر هواء عالي الكفاءة يضمن تدفق الهواء النقي للمحرك وتقليل استهلاك البنزين.",
        "rating": 4.6, "ratings_count": 120, "initial_price": 500, "discount": 20, "final_price": 400,
        "seller_name": "الياباني لقطع الغيار", "what_customers_said": "خامة الفلتر ممتازة وفرق في سحب العربية"
    },
    {
        "title": "فلتر تكييف كربون مضاد للبكتيريا نيسان صني N17",
        "category": "فلاتر وزيوت",
        "product_description": "فلتر تكييف كربون ينقي هواء الكابينة من الأتربة والروائح الكريهة ومناسب لنيسان صني N17.",
        "rating": 4.8, "ratings_count": 210, "initial_price": 350, "discount": 14, "final_price": 300,
        "seller_name": "نيسان جراج مصر", "what_customers_said": "قضى على رطوبة التكييف تماماً"
    },

    # فرامل وتيل
    {
        "title": "تيل فرامل أمامي بوش Bosch أصلي - تويوتا كورولا / هيونداي الجمل",
        "category": "فرامل وتيل",
        "product_description": "تيل فرامل أمامي ألماني بوش بدون صوت أو صفير، عمر افتراضي طويل وقوة فرملة عالية.",
        "rating": 4.9, "ratings_count": 410, "initial_price": 1600, "discount": 15, "final_price": 1360,
        "seller_name": "بوش أوتو سنتر مصر", "what_customers_said": "فرملة ناعمة ومفيش أي صفير أو سخونة"
    },
    {
        "title": "تيل فرامل خلفي بريمبو Brembo - كيا سيراتو / هيونداي النترا AD",
        "category": "فرامل وتيل",
        "product_description": "تيل فرامل رياضي سيراميك بريمبو إيطالي عالي الأداء لا يسبب تآكل الطنابير.",
        "rating": 4.9, "ratings_count": 310, "initial_price": 1850, "discount": 10, "final_price": 1665,
        "seller_name": "إيطاليانو قطع غيار", "what_customers_said": "أفضل تيل جربته في مصر أمان تام"
    },
    {
        "title": "طنابير فرامل أمامية طقم (زوج) TRW - فيات تيبو / رينو لوجان",
        "category": "فرامل وتيل",
        "product_description": "طنابير فرامل تهوية أمامية TRW أصلية تتحمل درجات الحرارة العالية في الصيف.",
        "rating": 4.7, "ratings_count": 145, "initial_price": 3800, "discount": 12, "final_price": 3344,
        "seller_name": "أوربي لقطع الغيار", "what_customers_said": "خامة محترمة جداً وقضت على الرجة عند الفرملة"
    },
    {
        "title": "طقم بوجيهات ليزر إيريديوم NGK Laser Iridium (4 بوجيه)",
        "category": "كهرباء ومحرك",
        "product_description": "بوجيهات إيريديوم ياباني NGK الأصلي تعيش حتى 100 ألف كم وتحسن استجابة الدواسة واستهلاك الوقود.",
        "rating": 4.9, "ratings_count": 520, "initial_price": 2200, "discount": 18, "final_price": 1804,
        "seller_name": "الياباني لقطع الغيار", "what_customers_said": "فرق شاسع في سحب العربية وصوت الموتور"
    },

    # عفشة وتعليق
    {
        "title": "طقم مساعدين أماميين غاز KYB Excel-G - هيونداي النترا MD / كيا K3",
        "category": "عفشة وتعليق",
        "product_description": "مساعدين غاز ونقطة زيت KYB ياباني أصلي توفر ثبات ممتاذ في المنحنيات وراحة على الحفر.",
        "rating": 4.8, "ratings_count": 270, "initial_price": 5500, "discount": 10, "final_price": 4950,
        "seller_name": "التوفيكية لأوتو", "what_customers_said": "العربية بقت ثابته جداً في السفر والغرز"
    },
    {
        "title": "طقم مساعدين خلفيين زاكس Sachs ألماني - شيفورليه أوبترا / افيو",
        "category": "عفشة وتعليق",
        "product_description": "مساعدين Sachs ألماني للسيارات الشيفورليه والدايو لامتصاص الصدمات على المطبات.",
        "rating": 4.7, "ratings_count": 190, "initial_price": 4200, "discount": 15, "final_price": 3570,
        "seller_name": "البرنس لقطع الغيار", "what_customers_said": "ناشفة وثابتة على الطرق السريعة"
    },
    {
        "title": "طقم مقصات كاملة بالبيض والجلب CTR كوري - هيونداي اكسبنت RB",
        "category": "عفشة وتعليق",
        "product_description": "مقصات CTR كوري أصلي مختومة للمطبات والظروف الصعبة على الطرق المصرية.",
        "rating": 4.8, "ratings_count": 160, "initial_price": 3200, "discount": 12, "final_price": 2816,
        "seller_name": "الكوري لقطع الغيار", "what_customers_said": "طقم تقيل وعفشة العربية رجعت زيرو"
    },
    {
        "title": "تيش ميزان أمامي طقم (زوج) 555 ياباني - تويوتا ياريس / كورولا",
        "category": "عفشة وتعليق",
        "product_description": "تيش ميزان 555 ياباني لمنع الخبط والأصوات في العفشة أثناء التوجيه والمطبات.",
        "rating": 4.6, "ratings_count": 115, "initial_price": 1400, "discount": 15, "final_price": 1190,
        "seller_name": "الياباني لقطع الغيار", "what_customers_said": "قضى على صوت التكتكة تماماً"
    },
    {
        "title": "كوبلن خارجي كامل C.V Joint HDK ياباني - نيسان صني / سنترا",
        "category": "عفشة وتعليق",
        "product_description": "كوبلن خارجيHD K ياباني مزود بشحم الأصلي وكاوتشة كوبلن عالية التحمل.",
        "rating": 4.7, "ratings_count": 130, "initial_price": 2100, "discount": 14, "final_price": 1806,
        "seller_name": "نيسان جراج مصر", "what_customers_said": "خامة ممتاز ومفيش طقطقة في الملفات"
    },

    # بطاريات وكهرباء
    {
        "title": "بطارية فارتا Varta ألماني Blue Dynamic 70 أمبير جافة",
        "category": "بطاريات وكهرباء",
        "product_description": "بطارية فارتا ألماني جافة بالكامل ضمان سنتين مناسبة لجميع السيارات الحديثة وتتحمل التشغيل الشاق.",
        "rating": 4.9, "ratings_count": 480, "initial_price": 4500, "discount": 10, "final_price": 4050,
        "seller_name": "مركز فورتكس للبطاريات", "what_customers_said": "ضمان حقيقي وتدوير سريع جداً في البرد"
    },
    {
        "title": "بطارية كلورايد Chloride مائية 60 أمبير مصرية بمواصفات ألمانية",
        "category": "بطاريات وكهرباء",
        "product_description": "بطارية كلورايد مصرية أصلية بضمان عام كامل وقوة تدوير عالية على البارد.",
        "rating": 4.5, "ratings_count": 310, "initial_price": 2900, "discount": 15, "final_price": 2465,
        "seller_name": "كلورايد مصر", "what_customers_said": "سعرها ممتاز وعايشة معايا بقالها سنة وزي الفل"
    },
    {
        "title": "طقم لمبات ليد LED أوسرام Osram LEDriving H7 للفاوانيس",
        "category": "بطاريات وكهرباء",
        "product_description": "لمبات ليد أوسرام ألماني H7 إضاءة بيضاء ثلجية 6000K بدون تداخل مع ضفيرة العربية.",
        "rating": 4.8, "ratings_count": 390, "initial_price": 3100, "discount": 20, "final_price": 2480,
        "seller_name": "أوسرام مصر للإضاءة", "what_customers_said": "نور قوي جداً في السفر ومبيعميش العربية اللي قدامك"
    },

    # سير ومحرك
    {
        "title": "طقم سير كاتينة مع بلية التوتر Gates ألماني - رينو لوجان / سانديرو",
        "category": "سير ومحرك",
        "product_description": "طقم سير كاتينة جيتس بلجيكي/ألماني أصلي يضمن حماية المحرك من انقطاع السير.",
        "rating": 4.9, "ratings_count": 220, "initial_price": 2800, "discount": 10, "final_price": 2520,
        "seller_name": "الفرنساوي لقطع الغيار", "what_customers_said": "سير أصلي ومطاط مقوى خامة نظيفة"
    },
    {
        "title": "طلمبة مياه GMB ياباني - تويوتا كورولا / ميتسوبيشي لانسر شارك",
        "category": "سير ومحرك",
        "product_description": "طلمبة مياه تبريد المحرك GMB ياباني لمنع ارتفاع حرارة المحرك.",
        "rating": 4.7, "ratings_count": 140, "initial_price": 1950, "discount": 12, "final_price": 1716,
        "seller_name": "الياباني لقطع الغيار", "what_customers_said": "الحرارة سبتت على النصف بالظبط"
    },
    {
        "title": "ترموستات كوع حرارة ردياتير أصلي هيونداي / كيا",
        "category": "سير ومحرك",
        "product_description": "ترموستات كوع حرارة مياه 82 درجة مئوية أصلي لتنظيم دورة التبريد بالموتور.",
        "rating": 4.8, "ratings_count": 175, "initial_price": 650, "discount": 15, "final_price": 552,
        "seller_name": "الكوري لقطع الغيار", "what_customers_said": "أصلي بالختم ورجّع دورة المية طبيعية"
    },

    # إكسسوارات ومساحات
    {
        "title": "طقم مساحات زجاج بوش Bosch Aerotwin مقاسات مختلفة",
        "category": "إكسسوارات ومساحات",
        "product_description": "مساحات بوش سيراميك سيليكون ناعمة تنظف الزجاج بدون خربشة أو صوت ريريرة.",
        "rating": 4.9, "ratings_count": 650, "initial_price": 750, "discount": 20, "final_price": 600,
        "seller_name": "بوش أوتو سنتر مصر", "what_customers_said": "أفضل مساحات للمطر والتراب في مصر"
    },
    {
        "title": "دواسات سيارة جلد ثعبان 5D خامة ثقيلة ضد الماء والتراب",
        "category": "إكسسوارات ومساحات",
        "product_description": "طقم دواسات أرضية 5D تفصيل ببروز حماية لجميع أنواع السيارات كيا وهيونداي وتويوتا ونيسان.",
        "rating": 4.7, "ratings_count": 280, "initial_price": 1200, "discount": 25, "final_price": 900,
        "seller_name": "أوتو كير مصر", "what_customers_said": "خامة تقيلة وسهلة الغسيل والتنظيف"
    },
    {
        "title": "غطاء سيارة ووتربروف مبطن شواكيش ضد الشمس والمطر والتراب",
        "category": "إكسسوارات ومساحات",
        "product_description": "غطاء سيارة ثقيل طبقتين مبطن قماش من الداخل لحماية دهان السيارة من الشمس والخدوش.",
        "rating": 4.6, "ratings_count": 310, "initial_price": 1500, "discount": 20, "final_price": 1200,
        "seller_name": "أوتو كير مصر", "what_customers_said": "خامة محترمة جداً وبيستحمل الشمس العالية"
    },
    {
        "title": "كومبريسور نفخ تائر سيارة جمل 2 بيستون مع شنطة وسلك لترانس البطارية",
        "category": "إكسسوارات ومساحات",
        "product_description": "منفاخ إطارات جمل 2 بستم سريع جداً ينفخ الكاوتش في دقيقة واحدة ومزود بمقياس ضغط воздуха.",
        "rating": 4.8, "ratings_count": 420, "initial_price": 1800, "discount": 15, "final_price": 1530,
        "seller_name": "التوفيكية لأوتو", "what_customers_said": "منقذ في السفر والزنقات ينفخ في ثواني"
    }
]

# Multiply dataset variations to make it rich (~100 items)
expanded = []
for i in range(4):
    for item in auto_parts:
        c = item.copy()
        c["product_id"] = f"auto_{len(expanded)+1}"
        c["currency"] = "EGP"
        c["is_active"] = 1
        c["delivery_options"] = "توصيل خلال 24-48 ساعة لجميع محافظات مصر - الدفع عند الاستلام"
        c["product_specifications"] = f"قطع غيار أصلي متوافقة مع السيارات في مصر | الضمان: 6 أشهر ضد عيوب التصنيع | الماركة: {c['seller_name']}"
        expanded.append(c)

df = pd.DataFrame(expanded)
df.to_csv("data/products_clean.csv", index=False)
print(f"Generated {len(df)} auto parts products in data/products_clean.csv successfully!")
