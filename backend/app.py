from flask import Flask, request, send_from_directory, session, jsonify
from flask_cors import CORS
import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.transforms as transforms
from torchvision import models
from PIL import Image
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'admin'
CORS(app)

# Database connection
import sqlite3
import os

# Create database file if it doesn't exist
db_path = 'users.db'
if not os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            address TEXT,
            mobile_number TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# Device configuration
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Image transformations for main model (no normalization)
image_transform_main = transforms.Compose([
    transforms.Resize(224),
    transforms.CenterCrop(224),
    transforms.ToTensor()
])

# Image transformations for normalization (irrelevant/relevant classification)
image_transform_normalization = transforms.Compose([
    transforms.Resize(224),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# Define the MobileNetModel class for relevance/irrelevance classification
class MobileNetModel(nn.Module):
    def __init__(self, num_classes):
        super(MobileNetModel, self).__init__()
        self.mobilenet = models.mobilenet_v2(pretrained=True)
        num_features = self.mobilenet.classifier[1].in_features
        self.mobilenet.classifier[1] = nn.Linear(num_features, num_classes)

    def forward(self, x):
        return self.mobilenet(x)

# Load the relevant/irrelevant model
irrelevant_model_path = 'mobilenet_irrelevent.pt'
irrelevant_model = MobileNetModel(num_classes=2)
irrelevant_model.load_state_dict(torch.load(irrelevant_model_path))
irrelevant_model = irrelevant_model.to(device)
irrelevant_model.eval()
# Define the DenseNet121 model for 40 class classification
class DenseNetPlantClassifier(nn.Module):
    def __init__(self, num_classes):
        super(DenseNetPlantClassifier, self).__init__()
        self.densenet = models.densenet121(weights=models.DenseNet121_Weights.DEFAULT)
        num_ftrs = self.densenet.classifier.in_features
        self.densenet.classifier = nn.Linear(num_ftrs, num_classes)
    
    def forward(self, x):
        return self.densenet(x)

# Load the model
num_classes = 40  # Adjust according to your number of classes
model = DenseNetPlantClassifier(num_classes=num_classes)
checkpoint = torch.load('backend/densenet121_pso_medicinal_plants.pth', map_location=device)
# Extract the model state dict if it's wrapped in a checkpoint
if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
    model.load_state_dict(checkpoint['model_state_dict'], strict=False)
else:
    model.load_state_dict(checkpoint, strict=False)
model = model.to(device)
model.eval()

# Load class names (hardcoded for development)
class_names = [
    'Wood_sorel', 'Brahmi', 'Basale', 'Lemon_grass', 'Lemon', 'Insulin', 'Amruta_Balli',
    'Betel', 'Castor', 'Ashoka', 'Aloevera', 'Tulasi', 'Henna', 'Curry_Leaf', 'Arali',
    'Hibiscus', 'Betel_Nut', 'Neem', 'Jasmine', 'Nithyapushpa', 'Mint', 'Nooni',
    'Pomegranate', 'Pepper', 'Geranium', 'Mango', 'Honge', 'Amla', 'Ekka', 'Raktachandini',
    'Rose', 'Ashwagandha', 'Gauva', 'Ganike', 'Avocado', 'Sapota', 'Doddapatre',
    'Nagadali', 'Pappaya', 'Bamboo'
]



# Helper functions
def predict_relevance(image_path):
    image = Image.open(image_path).convert('RGB')
    image = image_transform_normalization(image).unsqueeze(0).to(device)
    with torch.no_grad():
        output = irrelevant_model(image)
        _, predicted = torch.max(output, 1)
    return predicted.item()

def predict_classification(image_path):
    image = Image.open(image_path).convert('RGB')
    image = image_transform_main(image).unsqueeze(0).to(device)
    with torch.no_grad():
        outputs = model(image)
        probabilities = F.softmax(outputs, dim=1)
        top3_probs, top3_indices = torch.topk(probabilities, 3, dim=1)
    
    # Get top 3 predictions with confidence scores
    predictions = []
    for i in range(3):
        plant_idx = top3_indices[0][i].item()
        confidence = top3_probs[0][i].item()
        plant_name = class_names[plant_idx]
        predictions.append({
            'plant': plant_name,
            'confidence': round(confidence, 4)
        })
    
    # Get main prediction details (highest confidence)
    main_plant_name = predictions[0]['plant']
    description = "No description available"
    uses = "No uses available"

    # Provide details for each plant class
    if main_plant_name == 'Wood_sorel':
        description = "Wood sorrel is a wild herb with a sour taste, often used in salads. Wood sorrels are a terrific choice for beginner foragers, easy to identify and beloved by kiddos for its lemony flavor. Its signature heart-shaped leaves have led to one of its other nicknames, lemon hearts. You may also have heard it called sourgrass, common yellow oxalis, sheep’s clover, lemon clover, shamrock, or other regional variations."
        uses = "Used in salads, soups, and as a garnish. The old herbalists tell us that Wood Sorrel is more effectual than the true Sorrels as a blood cleanser, and will strengthen a weak stomach, produce an appetite, check vomiting, and remove obstructions of the viscera."
    elif main_plant_name == 'Brahmi':
        description = "Brahmi is an herb commonly used in Ayurvedic medicine for enhancing memory and reducing stress.Brahmi is non-aromatic soft, perennial, creeping herb with succulent leaves. It has numerous branches that grow especially in wet and marshy places. This edible plant can grow up to 6 inches in height, branches creep horizontally to cover the ground. Green leaves with small marks are coin shaped and grow in the cluster of two or three alternately placed on hairy stem. Flowers are small, actinomorphic, white and purplish in color and appear most of months in a year. It contains 4-5 petals. Due to its ability to grow in water it is also called water aquarium plant."
        uses = "Used as a memory enhancer, stress reliever, and general tonic. Brahmi is a powerful medicinal herb known for **enhancing memory, cognitive function, and reducing stress**. It helps manage **anxiety, depression, and insomnia** by promoting mental calmness. Its **anti-inflammatory and antioxidant properties** protect brain cells and support **nervous system health**, making it beneficial for conditions like **Alzheimer’s, ADHD, and epilepsy**. Brahmi also promotes **hair growth, improves skin health**, and aids in **digestion and liver detoxification**. Widely used in **Ayurveda**, it is consumed as **powder, capsules, tea, or oil** for overall **brain and body wellness**. "
    elif main_plant_name == 'Basale':
        description = "Basale, or basil, is an aromatic herb used in cooking and for medicinal purposes. Basale, also known as Malabar Spinach (Basella alba or Basella rubra), is a nutritious leafy vegetable found in tropical regions. It has thick, fleshy leaves, and grows as a climbing vine. Unlike regular spinach, it has a mucilaginous (slimy) texture, making it beneficial for digestion and gut health. It is rich in iron, calcium, vitamins A, C, and antioxidants, and is widely used in Indian, Southeast Asian, and African cuisines."
        uses = "Used in cooking, especially in Italian dishes, and for its medicinal properties such as aiding digestion. Basil provides numerous benefits, including antioxidant properties, anticancer activity, radioprotection, antimicrobial effects, anti-inflammatory actions, immunomodulation, adaptogenic properties, antidiabetic activity, and more. The wide-ranging uses of basil make it a valuable and versatile herb with potential health-promoting effects."
    elif main_plant_name == 'Lemon_grass':
        description = "Lemongrass is a tropical plant used for its citrus flavor and medicinal properties. Lemongrass is a tall, aromatic grass commonly used in Asian cuisine, herbal medicine, and aromatherapy. It has a fresh, citrusy scent and is known for its medicinal and therapeutic benefits. Native to India, Southeast Asia, and Africa, it is widely used in tea, soups, curries, and essential oils. Lemongrass is valued for its antibacterial, antifungal, anti-inflammatory, and digestive properties."
        uses = "Used in teas, soups, and as a flavoring in various dishes.Lemongrass is widely used for its medicinal, culinary, and therapeutic benefits. It aids in digestion, relieving bloating, stomach cramps, and indigestion, making it a common ingredient in herbal teas. Its antibacterial, antifungal, and immune-boosting properties help fight infections and colds. Lemongrass is also known for its calming effects, reducing stress, anxiety, and promoting restful sleep, especially when used in aromatherapy or herbal infusions. It supports heart health by lowering blood pressure and cholesterol levels while also acting as an anti-inflammatory agent to relieve pain and swelling, making it beneficial for arthritis and muscle soreness. Additionally, it promotes weight loss and detoxification by boosting metabolism and flushing out toxins. Lemongrass essential oil is a natural insect repellent, often used in candles, sprays, and skincare to ward off mosquitoes and bacteria. Its refreshing citrus aroma makes it a popular ingredient in soaps, perfumes, and spa treatments."
    elif main_plant_name == 'Lemon':
        description = "Lemon is a citrus fruit known for its tangy flavor and high vitamin C content. It is widely used in culinary, medicinal, and cosmetic applications. Native to South Asia, lemons are now cultivated worldwide and are essential in beverages, cooking, herbal remedies, and skincare. The fruit is packed with antioxidants, essential nutrients, and bioactive compounds, making it highly beneficial for health and wellness."
        uses = "Used in cooking, baking, and as a flavoring in drinks and foods. Lemon is rich in vitamin C, boosting immunity and fighting infections. It aids digestion, relieves bloating, and promotes heart health by lowering cholesterol and blood pressure. Lemon supports weight loss, prevents kidney stones, and enhances skin and hair health by reducing acne, dandruff, and pigmentation. Its antimicrobial properties make it useful for natural cleaning, food preservation, and oral care. Lemon essential oil relieves stress and fatigue, while lemon water keeps the body hydrated and detoxified."
    elif main_plant_name == 'Insulin':
        description = "Insulin is a hormone used in diabetes management. The Insulin Plant (Costus igneus) is a medicinal herb known for its ability to regulate blood sugar levels. It is native to Southeast Asia and India and is widely used in Ayurveda and traditional medicine. The plant has spiral-shaped leaves and orange-yellow flowers, making it both ornamental and medicinal. Consuming its leaves is believed to help manage diabetes, as it mimics the function of insulin in the body."
        uses = "Used in medical treatments for diabetes to regulate blood sugar levels. The insulin plant is mainly used for its anti-diabetic properties, as its leaves help lower blood sugar levels naturally. It also improves insulin sensitivity, benefiting people with type 2 diabetes. The plant has anti-inflammatory, antioxidant, and antibacterial effects, making it useful in treating wounds, infections, and digestive issues. It supports heart health by lowering cholesterol and blood pressure. Additionally, it enhances liver function, aids in detoxification, and promotes overall well-being."
    elif main_plant_name == 'Amruta_Balli':
        description = "Amruta Balli is a plant used in traditional medicine, known for its health benefits. Amruta Balli, also known as Giloy or Guduchi, is a powerful medicinal herb in Ayurveda, often referred to as the root of immortality due to its vast health benefits. It is a climbing shrub with heart-shaped leaves, commonly found in India, Sri Lanka, and Myanmar. Known for its immune-boosting, anti-inflammatory, and detoxifying properties, Amruta Balli is widely used for treating fevers, infections, diabetes, and digestive disorders."
        uses = "Used in traditional remedies to improve health and treat various ailments.Amruta Balli is widely used in Ayurvedic medicine for its immune-boosting properties, helping the body fight infections, fevers, and respiratory issues. It regulates blood sugar levels, making it beneficial for diabetes management. Its anti-inflammatory and antioxidant effects aid in joint pain relief, liver detoxification, and digestion. It is also known to improve mental clarity, reduce stress, and enhance overall well-being. Additionally, it helps in wound healing, skin health, and acts as a natural detoxifier for removing harmful toxins from the body."
    elif main_plant_name == 'Betel':
        description = "Betel is a plant whose leaves are used in chewing and for medicinal purposes.Betel, scientifically known as Piper betle, is a medicinal and aromatic plant widely used in Ayurveda and traditional medicine. It is a climbing vine with heart-shaped leaves, commonly found in India, Southeast Asia, and tropical regions. Betel leaves are chewed raw or used in herbal remedies due to their antibacterial, digestive, and stimulant properties. They are also used in religious and cultural practices across Asia."
        uses = "Used in chewing for its stimulant effects and in traditional medicine. Betel leaves are traditionally used for oral health, preventing bad breath, gum infections, and tooth decay. Their digestive properties help in reducing bloating, acidity, and indigestion. The leaves have antibacterial and antifungal effects, making them useful in wound healing, skin infections, and respiratory issues like cough and asthma. Betel also acts as a natural stimulant, improving mood and alertness. It is widely used in traditional medicine for detoxification, pain relief, and immune support. Additionally, its antioxidant and anti-inflammatory properties promote heart health and blood circulation."
    elif main_plant_name == 'Castor':
        description = "Castor is a plant known for its oil, which has various industrial and medicinal uses. Castor is a medicinal and industrial plant known for its oil-rich seeds and diverse therapeutic applications. It is a fast-growing shrub native to Africa and India and is widely cultivated in tropical and subtropical regions. Castor seeds are the primary source of castor oil, which is used in medicine, cosmetics, and industry. Despite its benefits, the raw seeds contain toxic compounds and should not be consumed directly."
        uses = "Used to produce castor oil for industrial applications and as a laxative. Castor oil is widely used as a natural laxative, relieving constipation and digestive issues. It is beneficial for skin and hair care, promoting hydration, reducing acne, and stimulating hair growth. Due to its anti-inflammatory properties, castor oil is applied to joint pain, muscle soreness, and wounds. In medicine, it is used in drug formulations, wound dressings, and antifungal treatments. Industrially, castor oil is used in lubricants, cosmetics, biofuels, and plastic manufacturing. Despite its many benefits, raw castor seeds should be avoided due to toxicity."
    elif main_plant_name == 'Ashoka':
        description = "Ashoka is a tree valued in traditional medicine for its therapeutic properties. Ashoka, scientifically known as Saraca asoca, is a sacred and medicinal tree widely used in Ayurveda and traditional medicine. Native to India and Southeast Asia, it is famous for its beautiful orange-red flowers and its role in women’s health remedies. The bark, flowers, and leaves of the Ashoka tree have therapeutic properties, particularly for gynecological disorders, skin health, and digestion."
        uses = "Used in traditional medicine to treat gynecological disorders and other conditions. Ashoka is highly valued for its women’s health benefits, helping regulate menstrual cycles, relieve cramps, and treat excessive bleeding (menorrhagia). It has anti-inflammatory and pain-relieving properties, making it useful for joint pain, ulcers, and wounds. Ashoka also supports digestive health, improving appetite and reducing bloating. It is beneficial for skin health, treating acne, pigmentation, and allergies. Additionally, Ashoka strengthens the heart, purifies the blood, and enhances mental well-being by reducing stress and anxiety."
    elif main_plant_name == 'Aloevera':
        description = "Aloe Vera is a succulent plant known for its soothing and healing properties. Aloe Vera is a succulent plant known for its medicinal and cosmetic benefits. Native to North Africa and the Arabian Peninsula, it is widely cultivated for its gel-filled leaves, which have soothing, healing, and hydrating properties. Aloe Vera is used in traditional medicine, skincare, hair care, and digestion remedies due to its cooling and anti-inflammatory effects."
        uses = "Used in skin care products and as a remedy for burns and wounds. Aloe Vera is widely used in skincare, helping to moisturize, heal wounds, treat acne, and soothe sunburns. It supports hair growth, reduces dandruff, and strengthens the scalp. In medicine, Aloe Vera is used to aid digestion, relieve constipation, and support gut health. It has anti-inflammatory properties, making it beneficial for arthritis, joint pain, and skin conditions like eczema and psoriasis. Aloe Vera also boosts immunity, hydrates the body, and detoxifies the liver. Its gel is a popular ingredient in cosmetics, health drinks, and herbal medicine."
    elif main_plant_name == 'Tulasi':
        description = "Tulasi, or Holy Basil, is a revered plant in Ayurveda with various health benefits. Native to India and Southeast Asia, it is known for its aromatic leaves and therapeutic properties. Tulasi is highly valued for its immune-boosting, anti-inflammatory, and stress-relieving benefits. It is commonly used in herbal teas, medicines, and religious rituals."
        uses = "Used in traditional medicine to boost immunity and as a general tonic. Tulasi is a natural immunity booster, helping the body fight infections, colds, and respiratory issues like asthma and bronchitis. It has adaptogenic properties, reducing stress, anxiety, and fatigue. Tulasi is also used for digestive health, relieving bloating, acidity, and indigestion. Its antibacterial and antifungal properties make it effective for oral health, skin infections, and wound healing. Tulasi helps regulate blood sugar levels, supports heart health, and detoxifies the liver and kidneys. It is commonly consumed as a herbal tea, extract, or fresh leaves for overall well-being."
    elif main_plant_name == 'Henna':
        description = "Henna is a plant known for its dyeing properties, used in body art and hair coloring. Henna, scientifically known as Lawsonia inermis, is a flowering shrub widely used for its natural dyeing and medicinal properties. Native to North Africa, the Middle East, and South Asia, henna leaves are ground into a paste and applied for hair and skin coloring, cooling effects, and wound healing. It has been used for centuries in cosmetics, traditional medicine, and cultural rituals."
        uses = "Used for creating temporary body art and coloring hair. Henna is primarily used as a natural hair dye, strengthening hair, reducing dandruff, and promoting hair growth. It is applied on skin (mehndi) for temporary body art and cooling effects. Henna has antibacterial and antifungal properties, making it effective for treating wounds, skin infections, and scalp conditions. It is also used in Ayurveda for fever, headaches, and arthritis pain relief. Additionally, henna leaves are known to soothe burns, improve nail health, and support oral hygiene."
    elif main_plant_name == 'Curry_Leaf':
        description = "Curry leaf (botanical name: Murraya koenigii) is a tropical to sub-tropical tree native to India and Sri Lanka. It is a small tree or shrub with aromatic, dark green leaves that are commonly used in Indian cooking for their distinct flavor and fragrance. The plant belongs to the Rutaceae family and thrives in well-drained soil with plenty of sunlight. Beyond its culinary appeal, curry leaf is valued in traditional medicine systems like Ayurveda and Siddha for its therapeutic properties."
        uses = "Curry leaves are widely recognized for their medicinal value in traditional Indian healing systems like Ayurveda. They are highly effective in aiding digestion by stimulating digestive enzymes and easing common issues like bloating, nausea, and diarrhea. The leaves play a supportive role in managing diabetes, as they help regulate blood sugar levels and improve insulin activity. Rich in antioxidants and vital nutrients, curry leaves are also used to promote hair health by reducing hair fall, delaying premature graying, and nourishing the scalp. Their antibacterial and anti-inflammatory properties help boost immunity and protect the body from infections. Additionally, curry leaves have been found to protect the liver from oxidativ"
    elif main_plant_name == 'Arali':
        description = "Arali, scientifically known as Nerium oleander, is an evergreen shrub or small tree found in tropical and subtropical regions. It is easily recognizable by its long, narrow leaves and beautiful, fragrant flowers that come in colors such as pink, white, red, and yellow. While Arali is often grown as an ornamental plant in gardens due to its attractive appearance, it is also known for its strong medicinal properties. However, it is important to note that all parts of the plant are highly toxic if ingested and should be used with caution under proper guidance."
        uses = "Despite its toxicity, Arali has been used in traditional medicine in carefully controlled forms. Extracts from the plant have been studied for their potential in treating skin conditions, heart ailments, and even certain types of cancer due to their anti-inflammatory, antimicrobial, and cardiotonic properties. In external applications, Arali leaves and flowers are sometimes used in poultices or oils to relieve joint pain, swelling, and inflammation. Some research has explored its potential in producing herbal formulations for heart failure and skin infections, although only under strict medical supervision. Due to its powerful effects and toxic nature, medicinal use of Arali should always be guided by trained professionals."
    elif main_plant_name == 'Hibiscus':
        description = "Hibiscus, scientifically known as Hibiscus rosa-sinensis, is a flowering plant commonly found in tropical and subtropical regions. It is well-known for its large, vibrant flowers that bloom in colors like red, pink, yellow, and white. Often grown as an ornamental plant, hibiscus also holds significant importance in traditional medicine systems such as Ayurveda and Unani. The plant's flowers and leaves are rich in antioxidants, vitamins, and minerals, making them beneficial for health and wellness."
        uses = "Hibiscus is widely used for its medicinal properties. One of its most popular uses is in the form of hibiscus tea, which is known to help lower blood pressure and cholesterol levels due to its rich antioxidant content. It also supports liver health and aids in weight management by promoting fat metabolism. The flower extract is used in hair care to strengthen roots, reduce dandruff, and encourage hair growth. In skincare, hibiscus is valued for its anti-aging and moisturizing properties, making it a natural remedy for healthy skin. Additionally, hibiscus is used to treat fevers, respiratory issues, and menstrual disorders in traditional medicine. Its gentle, natural healing properties make it a popular herb in many households."
    elif main_plant_name == 'Betel_Nut':
        description = "Betel nut, also known as Areca nut, comes from the Areca palm (Areca catechu), which is commonly found in tropical regions of Asia and the Pacific. The nut is typically chewed along with betel leaves, slaked lime, and other flavorings in many cultures, especially in India and Southeast Asia. The tree itself has a slender trunk and grows tall with a canopy of feather-like leaves. The nut is oval-shaped and reddish-brown when mature. Although widely consumed socially, betel nut also has a history of use in traditional medicine."
        uses = "In traditional medicine, betel nut has been used for its digestive and stimulant properties. It is believed to help with digestion, increase saliva production, and act as a mild stimulant that boosts alertness and energy. Some cultures have used it to treat intestinal worms, indigestion, and bad breath. In Ayurveda and folk medicine, betel nut has also been used as a tonic for the nervous system and for improving oral hygiene. However, it’s important to note that long-term and excessive consumption of betel nut is associated with serious health risks, including oral cancer and other diseases, and is classified as a carcinogen by the World Health Organization. Therefore, its medicinal use should be approached with great caution."
    elif main_plant_name == 'Neem':
        description = "Neem, scientifically known as Azadirachta indica, is a fast-growing evergreen tree native to the Indian subcontinent. It belongs to the mahogany family and is widely recognized for its small white flowers, bitter leaves, and green fruit. Almost every part of the neem tree—leaves, bark, seeds, and oil—is known for its potent medicinal properties. Neem has been used in Ayurveda, Siddha, and Unani systems of medicine for centuries and is often referred to as the “Village Pharmacy” due to its wide range of healing benefits."
        uses = "Neem is highly valued for its antibacterial, antifungal, antiviral, and anti-inflammatory properties. Neem leaves are commonly used to treat skin conditions like acne, eczema, and psoriasis, either in paste form or infused in water. Neem oil is applied to wounds, scalp infections, and fungal issues. It also plays a major role in oral health, often included in herbal toothpastes and mouthwashes to fight gum disease and bad breath. Neem is used internally as well—in small, controlled amounts—to help detoxify the body, support the immune system, and manage blood sugar levels in diabetic patients. It’s also an effective natural pesticide and insect repellent. Despite its many benefits, neem should be used with care, especially in high doses or during pregnancy."
    elif main_plant_name == 'Jasmine':
        description = "Jasmine is a beautiful, fragrant flowering plant belonging to the genus Jasminum in the olive family (Oleaceae). Native to tropical and warm temperate regions, jasmine is well-loved for its sweetly scented white or yellow blossoms that bloom especially at night. It is widely cultivated as an ornamental plant and holds cultural significance in many parts of the world. Beyond its pleasing aroma, jasmine has been used in traditional medicine systems like Ayurveda and Chinese medicine for its calming and healing properties."
        uses = "Jasmine is best known for its relaxing and mood-lifting qualities. The flowers are often used in aromatherapy to reduce stress, anxiety, and depression, thanks to their natural calming fragrance. Jasmine tea, made from dried flowers, is consumed to improve digestion, relieve menstrual cramps, and boost immunity. The essential oil extracted from jasmine flowers is used in massages and skin treatments due to its anti-inflammatory, antiseptic, and moisturizing effects. In traditional medicine, jasmine has also been used to treat fever, wounds, and cough. Its gentle, soothing nature makes it a popular ingredient in perfumes, oils, and herbal beauty products."
    elif main_plant_name == 'Nithyapushpa':
        description = "Nithyapushpa, also known as Periwinkle or Catharanthus roseus, is a small evergreen shrub with glossy green leaves and delicate flowers that bloom in pink, white, or purple. Native to Madagascar but widely grown in India and other tropical regions, this plant is often seen in home gardens and temple courtyards. Despite its ornamental appeal, Nithyapushpa is highly valued in traditional and modern medicine for its powerful bioactive compounds."
        uses = "Nithyapushpa holds great medicinal importance, especially in modern cancer treatment. The plant contains alkaloids such as vincristine and vinblastine, which are used in chemotherapy to treat cancers like leukemia and lymphoma. In traditional medicine, extracts of the leaves and roots are used to treat diabetes, high blood pressure, and infections. The plant also exhibits antibacterial, antifungal, and antioxidant properties. Some traditional remedies use it for managing skin diseases, toothache, and menstrual disorders. However, due to the presence of potent alkaloids, it should be used with caution and only under professional guidance."
    elif main_plant_name == 'Mint':
        description = "Mint, belonging to the genus Mentha, is a fast-growing, aromatic herb widely cultivated for its refreshing scent and flavor. It has bright green, serrated leaves and a cool, menthol-rich aroma that makes it a favorite in kitchens and gardens around the world. Mint thrives in moist, shaded areas and spreads quickly due to its creeping roots. Common varieties include peppermint (Mentha piperita) and spearmint (Mentha spicata). Aside from culinary use, mint has a long history in traditional medicine for its soothing and healing qualities."
        uses = "UMint is well-known for its ability to aid digestion and relieve stomach discomfort, including indigestion, bloating, and gas. It is often consumed as a tea or chewed raw for its cooling effect. The menthol in mint acts as a natural decongestant, making it useful in treating colds, sore throats, and sinus issues. It also has antibacterial and anti-inflammatory properties, making it beneficial for oral hygiene, skin irritation, and even headache relief when used as an essential oil. In addition, mint is widely used in cosmetics, toothpaste, balms, and herbal medicines for its fresh aroma and therapeutic benefits. Its versatility and pleasant flavor make it a popular herb for both medicinal and everyday use."
    elif main_plant_name == 'Nooni':
        description = "Nooni, commonly known as Noni, is a small evergreen tree native to Southeast Asia and the Pacific Islands. It belongs to the Rubiaceae (coffee) family and is scientifically named Morinda citrifolia. The tree bears a distinctive, bumpy, potato-like fruit that turns from green to yellowish-white when ripe. Although the fruit has a strong, pungent odor (often called “cheese fruit”), it is highly valued in traditional medicine systems such as Ayurveda, Polynesian, and Hawaiian healing practices for its wide range of health benefits."
        uses = "Nooni is best known for its immune-boosting, antioxidant, anti-inflammatory, and pain-relieving properties. The juice extracted from the Noni fruit is used to boost immunity, fight fatigue, and improve overall energy levels. It is also believed to help regulate blood pressure, manage diabetes, and support digestive health. In traditional medicine, Noni is used to treat joint pain, infections, skin problems, menstrual cramps, and fevers. The leaves are sometimes applied externally to relieve wounds, inflammation, and swelling. Rich in vitamins, minerals, and plant compounds like xeronine and scopoletin, Nooni has gained popularity as a natural health supplement—though it should be consumed in moderation due to its strong potency."
    elif main_plant_name == 'Pomegranate':
        description = "Pomegranate, scientifically known as Punica granatum, is a fruit-bearing shrub or small tree native to the Middle East and South Asia. It is well-known for its round, reddish fruit filled with juicy, ruby-red seeds called arils. The plant grows well in warm, dry climates and is often cultivated both for its ornamental beauty and nutritional value. Revered since ancient times, the pomegranate is a symbol of health, fertility, and longevity in many cultures and is extensively used in traditional medicine."
        uses = "Pomegranate is prized for its antioxidant, anti-inflammatory, and antibacterial properties. The juice is rich in vitamin C, potassium, and polyphenols, which help boost the immune system, improve heart health, and protect the body against oxidative stress. It is especially beneficial in lowering blood pressure, reducing cholesterol, and managing blood sugar levels. In Ayurveda, the fruit, rind, and even bark are used to treat digestive disorders, diarrhea, and intestinal parasites. Pomegranate is also known to support skin health, slow aging, and may help prevent certain types of cancer, particularly prostate and breast cancer. Its versatile medicinal benefits make it a powerful addition to both diet and natural remedies."
    elif main_plant_name == 'Pepper':
        description = "Pepper, scientifically known as Piper nigrum, is a flowering vine native to South India and widely cultivated for its fruit, which is dried and used as the popular spice known as black pepper. The plant climbs with the help of aerial roots and produces small, round berries that turn red when ripe. Depending on how it is processed, these berries give us black, white, or green pepper. Known as the King of Spices, pepper has been valued for centuries not only for its pungent flavor but also for its medicinal qualities."
        uses = "Pepper is widely used in traditional and modern medicine for its digestive, anti-inflammatory, and antioxidant properties. The active compound piperine enhances the absorption of nutrients and medicines in the body, making it a powerful bio-enhancer. Pepper stimulates the digestive system, relieving gas, bloating, and indigestion. It is also used to treat cold, cough, and respiratory issues, thanks to its expectorant and warming effects. In Ayurveda, black pepper is often combined with honey and turmeric for immune support. Its antibacterial and antioxidant properties contribute to better metabolism, and it may aid in weight management and blood sugar control. Pepper is a staple in herbal remedies due to its versatility and effectiveness."
    elif main_plant_name == 'Geranium':
        description = "Geranium, particularly the species from the Pelargonium genus, is a flowering plant known for its fragrant leaves and vibrant blooms in shades of pink, red, purple, or white. Although often grown for its ornamental value, certain varieties—like Pelargonium graveolens (commonly called rose-scented geranium)—are well-known for their medicinal properties. The plant is native to South Africa but is now cultivated around the world for use in herbal remedies, skincare, and essential oil production."
        uses = "Geranium is widely used in herbal and aromatherapy practices due to its antibacterial, anti-inflammatory, and astringent properties. The essential oil extracted from its leaves is used to treat skin conditions like acne, eczema, and dermatitis, and also helps in wound healing. Its soothing fragrance has calming effects on the nervous system, making it beneficial for reducing stress, anxiety, and mild depression. Geranium oil is also applied in massage to relieve muscle pain and improve circulation. In traditional medicine, geranium leaves have been used as a mild pain reliever, to stop bleeding, and to treat respiratory infections. Its natural astringent quality also makes it helpful in tightening and toning skin, hence its inclusion in many natural beauty products."
    elif main_plant_name == 'Mango':
        description = "Mango, scientifically known as Mangifera indica, is a large, evergreen tropical tree native to South Asia and widely cultivated in warm climates around the world. Known as the “King of Fruits,” mango is cherished not only for its sweet, juicy fruit but also for its significant medicinal value. The tree has dense, glossy leaves, small fragrant flowers, and produces fleshy stone fruits in various shapes and colors. In traditional systems like Ayurveda and Siddha, various parts of the mango tree—including the fruit, bark, leaves, and seeds—are used for healing purposes."
        uses = "Mango is packed with vitamins A, C, and E, making it great for boosting immunity, improving eye health, and promoting healthy skin. In traditional medicine, tender mango leaves are boiled and used to help manage diabetes by regulating insulin levels. The bark and seed kernel are used to treat diarrhea, dysentery, and intestinal worms. The fruit itself supports digestion, helps prevent constipation, and provides natural energy. Mango also has anti-inflammatory and antioxidant properties, which help fight free radicals and reduce the risk of chronic diseases. Additionally, mango pulp and seed oil are used in natural skincare to moisturize and rejuvenate the skin."
    elif main_plant_name == 'Honge':
        description = "Honge, scientifically known as Pongamia pinnata, is a medium-sized, fast-growing deciduous tree native to India and Southeast Asia. It thrives in tropical and subtropical climates and is commonly found along roadsides, riversides, and in wastelands. The tree has glossy, dark green leaves and produces clusters of fragrant pink, lavender, or white flowers, followed by flat brown seed pods. Honge is not only valued for its ability to grow in poor soil and improve soil fertility but also for its many medicinal and environmental benefits."
        uses = "Honge is highly regarded in traditional medicine for its antiseptic, anti-inflammatory, antifungal, and antiparasitic properties. The seeds are used to extract Karanja oil, which is applied externally to treat skin diseases, eczema, wounds, and ulcers. The leaves are used in poultices to reduce inflammation and pain, while bark and roots are used in decoctions for treating fever, diarrhea, and coughs. The oil is also a natural pesticide and insect repellent, often used in organic farming. Additionally, Honge is used for biofuel production due to its oil-rich seeds, making it beneficial for both health and the environment."
    elif main_plant_name == 'Amla':
        description = "Amla, scientifically known as Phyllanthus emblica, is a small deciduous tree native to India and Southeast Asia. It produces round, greenish-yellow fruits with a sour, tangy taste. This fruit has been a cornerstone of Ayurvedic medicine for thousands of years due to its incredible health-promoting properties. Amla trees are typically found in forest regions and are also cultivated in home gardens for their fruit and medicinal benefits."
        uses = "Amla is renowned for being one of the richest natural sources of Vitamin C, which helps boost immunity, combat infections, and promote glowing skin. It is a powerful antioxidant, helping to slow down aging and reduce oxidative stress. In Ayurveda, it is used to balance all three doshas—Vata, Pitta, and Kapha—and is included in many formulations like Triphala. Amla supports digestion, helps detoxify the liver, improves heart health, and aids in regulating blood sugar levels. It is also widely used in hair care, promoting hair growth, reducing dandruff, and preventing premature greying. Whether consumed raw, as juice, powder, or oil, Amla is a versatile and highly valued medicinal plant."
    elif main_plant_name == 'Ekka':
        description = "Ekka, scientifically known as Calotropis gigantea, is a large, hardy shrub commonly found in dry and sandy regions of India and Southeast Asia. It grows up to 2–4 meters in height and is easily recognizable by its thick, pale green leaves and striking star-shaped flowers, usually white or lavender. The plant exudes a milky latex when cut, and though parts of it are toxic in raw form, it holds great value in traditional medicine when used properly. Ekka is considered sacred in some cultures and is often associated with Lord Shiva in Indian tradition."
        uses = "Ekka is traditionally used for a variety of therapeutic and healing purposes. The leaves are warmed and applied to relieve joint pain, swelling, and inflammation. The latex from the plant, though toxic if consumed directly, is used externally in small, controlled amounts to treat skin conditions, warts, and wounds. The flowers and roots are used in Ayurvedic medicine to manage digestive disorders, asthma, cough, and fever. Ekka also acts as a vermifuge (expels intestinal worms) and helps in detoxifying the body. Due to its strong properties, it must be used with caution and preferably under guidance from a qualified practitioner."
    elif main_plant_name == 'Raktachandini':
        description = "Raktachandini, or Red Sandalwood, is a valuable medicinal tree native to southern India, especially found in the Eastern Ghats of Andhra Pradesh. Scientifically known as Pterocarpus santalinus, this tree is recognized for its deep red-colored heartwood, which is hard, heavy, and used extensively in traditional medicine and cosmetics. Unlike white sandalwood, red sandalwood does not have fragrance but is known for its cooling and healing properties. Due to its limited growing regions and overexploitation, it is now a protected species."
        uses = "Raktachandini is highly valued in Ayurveda for its ability to purify the blood and treat skin diseases such as acne, blemishes, and rashes. It has anti-inflammatory, antiseptic, and cooling properties that make it useful in the treatment of fever, headaches, and digestive disorders. Red sandalwood powder is commonly used in face packs to enhance skin glow and reduce pigmentation. Internally, it is used in decoctions to help manage diabetes, diarrhea, and ulcers. It is also used as a natural coloring agent in medicines and cosmetics."
    elif main_plant_name == 'Rose':
        description = "The Rose, belonging to the Rosa genus, is a woody perennial flowering plant known for its beauty, fragrance, and wide variety of colors. While admired for ornamental and symbolic purposes, roses—especially Damask rose (Rosa damascena) and Wild rose (Rosa canina)—also have important medicinal and therapeutic values. Rose petals, hips (the fruit of the rose), and essential oil are all used in traditional and modern herbal practices."
        uses = "Roses are widely used for their cooling, soothing, and anti-inflammatory properties. Rose water, made from petals, is used to tone and refresh the skin, reduce eye irritation, and soothe sunburns. Rose essential oil has antidepressant and anti-anxiety effects, often used in aromatherapy. Rose petals are used to prepare herbal teas that help with digestive issues, menstrual pain, and mild infections due to their antibacterial properties. Rose hips, rich in vitamin C and antioxidants, are used to boost immunity, promote skin health, and treat joint pain. In Ayurveda and Unani medicine, rose is also used as a mild laxative and heart tonic."
    elif main_plant_name == 'Ashwagandha':
        description = "Ashwagandha, also known as Indian Ginseng or Winter Cherry, is a small woody shrub native to India, the Middle East, and parts of Africa. Scientifically named Withania somnifera, this powerful adaptogenic herb has been a cornerstone of Ayurvedic medicine for over 3,000 years. The plant has oval leaves, yellow-green flowers, and red berry-like fruit. However, it is the roots and sometimes the leaves that are used for medicinal purposes. The name Ashwagandha means smell of a horse in Sanskrit, referring to its strong aroma and its traditional belief to impart the strength and vitality of a horse."
        uses = "Ashwagandha is best known as an adaptogen, helping the body cope with stress, anxiety, and fatigue. It is widely used to support mental clarity, focus, and emotional balance. Studies suggest it helps reduce cortisol levels, the stress hormone, and improves sleep quality. Ashwagandha also enhances stamina, boosts immunity, and supports thyroid function. It is used to strengthen the nervous system, improve sexual health and fertility, and manage blood sugar levels. In Ayurveda, it's commonly used as a rejuvenating tonic (Rasayana) for longevity and vitality."
    elif main_plant_name == 'Gauva':
        description = "Guava, scientifically known as Psidium guajava, is a tropical evergreen shrub or small tree native to Central America and widely cultivated in India and other tropical regions. It bears round or oval fruits with light green or yellow skin and sweet, fragrant white or pink flesh filled with tiny seeds. The leaves, fruits, and bark of the guava plant are all used in traditional medicine for their wide range of health benefits. Guava is known not only for its nutritional value but also for its healing properties."
        uses = "Guava is rich in Vitamin C, fiber, and antioxidants, which make it excellent for boosting immunity and promoting skin health. The leaves of the guava plant are widely used in herbal medicine to treat diarrhea, dysentery, and toothaches. Guava leaf tea helps control blood sugar levels, making it beneficial for people with diabetes. The fruit aids in digestion, relieves constipation, and supports weight loss due to its high fiber and low-calorie content. Additionally, guava has anti-inflammatory and antibacterial properties that help fight infections and support overall health."
    elif main_plant_name == 'Ganike':
        description = "Ganike, scientifically known as Clerodendrum inerme, is a hardy, evergreen shrub often found in coastal areas and tropical regions of India. It is commonly used as a hedge plant and is recognized for its small, glossy green leaves and white flowers. The plant is known by various regional names and holds an important place in traditional medicine, especially in Ayurveda and folk healing practices. It thrives in sandy and saline soils, making it a resilient plant in challenging environments."
        uses = "Ganike is known for its antibacterial, anti-inflammatory, and analgesic properties. The leaves are traditionally used to treat skin infections, wounds, and insect bites. A paste made from the leaves is applied externally to relieve swelling and joint pain. Decoctions of the leaves are also used to manage fever, asthma, and cough. In some traditional practices, it is used to treat epilepsy and nervous disorders due to its calming effects. The plant is also considered helpful in promoting hair health and controlling dandruff when used as a hair wash."
    elif main_plant_name == 'Avocado':
        description = "Avocado, scientifically known as Persea americana, is a nutrient-rich fruit-bearing tree native to Central America and now widely cultivated across tropical and subtropical regions, including parts of India. The tree is medium to large, with dark green, leathery leaves and pear-shaped fruits with a creamy green flesh and a single large seed. Avocado is not only valued as a delicious and healthy fruit but also has significant medicinal and therapeutic properties. Its pulp, seed, oil, and even leaves are used in traditional and modern health practices."
        uses = "Avocado is highly regarded for its heart-healthy fats, especially monounsaturated fatty acids, which help lower bad cholesterol levels. Rich in vitamin E, potassium, folate, and antioxidants, it supports skin health, improves brain function, and enhances immunity. Avocado oil is used to moisturize dry skin, heal wounds, and reduce inflammation. In traditional remedies, avocado leaves are used to make herbal teas that may help in managing high blood pressure, digestive issues, and kidney stones. The fruit is also beneficial for those with arthritis and joint pain due to its anti-inflammatory properties. Regular consumption supports eye health, weight management, and overall well-being."
    elif main_plant_name == 'Sapota':
        description = "Sapota, commonly known as Chikoo or Sapodilla, is a tropical fruit-bearing tree scientifically called Manilkara zapota. Native to Central America, it is widely grown in India for its sweet, brown, pulpy fruit. The tree is evergreen, with thick, glossy leaves and small, bell-shaped flowers. While the fruit is primarily known for its delicious taste, various parts of the tree—including the bark, seeds, and leaves—have medicinal properties that are used in traditional medicine."
        uses = "Sapota is rich in dietary fiber, vitamin C, iron, and antioxidants, making it excellent for boosting immunity and aiding digestion. The fruit pulp helps relieve constipation, reduce inflammation, and combat fatigue. Sapota seeds, when ground into a paste, are used as a natural remedy to treat kidney stones and urinary issues. The leaves of the tree are used in decoctions to treat coughs, cold, and diarrhea due to their antibacterial and anti-inflammatory properties. The bark has astringent qualities and is sometimes used to treat fevers and dysentery in traditional practices."
    elif main_plant_name == 'Doddapatre':
        description = "Doddapatre, scientifically known as Coleus amboinicus, is a fleshy, aromatic herb with thick, velvety leaves and a strong camphor-like scent. Commonly found in Indian households and known by various names such as Karpooravalli in Tamil and Ajwain Patta in Hindi, it belongs to the mint family. The plant grows easily in pots and gardens, making it a popular home remedy herb. Its leaves are packed with essential oils and bioactive compounds that give it strong medicinal properties."
        uses = "Doddapatre is widely used in traditional medicine for treating respiratory conditions like cough, cold, asthma, and bronchitis. The juice or decoction of the leaves acts as a natural expectorant and helps relieve chest congestion. It also aids in digestion, relieves bloating, and is commonly given to children for indigestion and colic pain. The leaves can be crushed and applied to insect bites or skin irritations to reduce itching and inflammation. It also possesses antibacterial, antifungal, and antioxidant properties, making it a versatile herb for various minor ailments."
    elif main_plant_name == 'Nagadali':
        description = "Nagadali, scientifically known as Vitex negundo, is a large aromatic shrub or small tree native to India and Southeast Asia. It is easily recognized by its compound leaves with five leaflets, hence the common name “Five-leaved chaste tree.” The plant has bluish-purple flowers and is often found growing near riverbanks or roadsides. In traditional medicine systems like Ayurveda, Siddha, and Unani, Nagadali is highly valued for its powerful anti-inflammatory, analgesic, and antibacterial properties."
        uses = "Nagadali is primarily used for treating joint pain, arthritis, and muscular inflammation. Its leaves are often made into a paste or oil to apply on swollen joints, sprains, and wounds to reduce pain and inflammation. Leaf decoctions are also taken internally to relieve fever, cold, and cough, as the plant acts as a natural expectorant. The roots and bark are used for their anti-asthmatic and antiseptic properties. Women traditionally use Nagadali to treat menstrual disorders and hormonal imbalances. It also serves as a natural insect repellent and is sometimes planted near homes for this purpose."
    elif main_plant_name == 'Pappaya':
        description = "Papaya, scientifically known as Carica papaya, is a tropical fruit-bearing plant widely cultivated in India and across the world. It has a soft trunk and large lobed leaves, and it produces sweet, orange-fleshed fruits. Every part of the papaya plant — including the fruit, leaves, seeds, and latex — holds medicinal value and has been used in traditional remedies for centuries. Papaya is known for its nutritional richness, especially in enzymes and vitamins."
        uses = "Papaya fruit is rich in vitamin C, vitamin A, and the digestive enzyme papain, which helps in digesting proteins and relieving constipation. It is commonly used to improve digestion, boost immunity, and support skin health. The leaves are famous in folk medicine for their ability to increase platelet count, especially in cases of dengue fever. Leaf extracts are also used to treat malaria, indigestion, and menstrual pain. Papaya seeds have antiparasitic properties and are used to treat intestinal worms. The latex of unripe papaya is sometimes used externally for treating skin warts and wounds."
    elif main_plant_name == 'Bamboo':
        description = "Bamboo is a fast-growing, woody grass belonging to the Poaceae family and is commonly found in tropical and subtropical regions, including India. It is known for its tall, hollow stems (culms) and is often associated with strength, flexibility, and resilience. While bamboo is widely used for construction, furniture, and crafts, it also holds important medicinal properties, especially in traditional medicine systems like Ayurveda, Chinese medicine, and folk remedies."
        uses = "Bamboo has various medicinal applications. The young shoots are edible and rich in dietary fiber, helping in digestion and weight management. They are also used to treat stomach disorders, diabetes, and high cholesterol. The leaves are brewed into teas to relieve fever, respiratory problems, and inflammation. Bamboo resin, also known as tabasheer, is a siliceous substance found in the internodes and is traditionally used to treat cough, asthma, urinary disorders, and even bone-related issues due to its high silica content. Additionally, bamboo extracts have antioxidant, antibacterial, and anti-inflammatory properties."

    return predictions, main_plant_name, description, uses


def map_prediction_to_label(prediction):
    label_mapping = {0: "relevant", 1: "irrelevant"}
    return label_mapping.get(prediction, "Unknown")

@app.route('/logout')
def logout():
    session.pop('user_email', None)
    return redirect('/')

# Routes
@app.route('/api/register', methods=["POST"])
def api_register():
    try:
        email = request.form.get('email')
        password = request.form.get('password')
        c_password = request.form.get('confirm_password')
        address = request.form.get('address')
        mobile_number = request.form.get('mobile_number')

        if not email or not password or not c_password or not address or not mobile_number:
            return jsonify({'error': 'All fields are required!'}), 400

        if password != c_password:
            return jsonify({'error': 'Confirm password does not match!'}), 400

        if len(mobile_number) != 10 or not mobile_number.isdigit():
            return jsonify({'error': 'Mobile number must be exactly 10 digits!'}), 400

        query = "SELECT email FROM users WHERE email = ?"
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, (email,))
        email_data = cursor.fetchone()
        conn.close()

        if email_data:
            return jsonify({'error': 'This email ID already exists!'}), 400

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        query = "INSERT INTO users (email, password, address, mobile_number) VALUES (?, ?, ?, ?)"
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, (email, hashed_password, address, mobile_number))
        conn.commit()
        conn.close()

        return jsonify({'message': 'Successfully Registered!'}), 201
    except sqlite3.IntegrityError as err:
        return jsonify({'error': 'Email already exists'}), 400
    except Exception as err:
        return jsonify({'error': 'Database error: ' + str(err)}), 500

@app.route('/api/login', methods=["POST"])
def api_login():
    try:
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required!'}), 400
        
        query = "SELECT email, password FROM users WHERE email = ?"
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, (email,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user[1], password):
            session['user_email'] = email
            return jsonify({'message': 'Login successful', 'user': email}), 200
        return jsonify({'error': 'Invalid email or password!'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logout', methods=["POST"])
def api_logout():
    session.pop('user_email', None)
    return jsonify({'message': 'Logged out successfully'}), 200

@app.route('/api/check-auth', methods=["GET"])
def check_auth():
    if 'user_email' in session:
        return jsonify({'authenticated': True, 'user': session['user_email']}), 200
    return jsonify({'authenticated': False}), 401

@app.route("/api/upload", methods=["POST"])
def api_upload():
    try:
        if 'user_email' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        myfile = request.files['file']
        fn = myfile.filename
        
        if not fn or '.' not in fn:
            return jsonify({'error': 'Invalid file'}), 400
        
        file_ext = fn.split('.')[-1].lower()
        if file_ext not in ['jpg', 'png', 'jpeg', 'jfif']:
            return jsonify({'error': 'Only image formats are accepted'}), 400
        
        # Create upload directory if it doesn't exist
        upload_dir = 'static/uploaded_images'
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        
        mypath = os.path.join(upload_dir, fn)
        myfile.save(mypath)
        
        relevance = predict_relevance(mypath)
        if relevance == 0:
            predictions, main_plant, description, uses = predict_classification(mypath)
            return jsonify({
                'predictions': predictions,
                'main_prediction': {
                    'plant': main_plant,
                    'description': description,
                    'uses': uses
                },
                'image': fn
            }), 200
        else:
            return jsonify({
                'prediction': 'This is not a medicinal plant image!',
                'image': fn
            }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/upload/<filename>')
def send_image(filename):
    return send_from_directory("static/uploaded_images", filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)