"""Plant information database for medicinal plants"""

PLANT_INFO = {
    'Wood_sorel': {
        'description': 'Wood sorrel is a wild herb with a sour taste, often used in salads.',
        'uses': 'Used in salads, soups, and as a garnish. Blood cleanser.'
    },
    'Brahmi': {
        'description': 'Ayurvedic herb used for memory and stress.',
        'uses': 'Memory enhancer, reduces anxiety and insomnia.'
    },
    'Basale': {
        'description': 'Malabar spinach with thick leaves.',
        'uses': 'Rich in antioxidants, anti-inflammatory.'
    },
    'Lemon_grass': {
        'description': 'Aromatic citrus grass.',
        'uses': 'Aids digestion, boosts immunity.'
    },
    'Lemon': {
        'description': 'Citrus fruit rich in Vitamin C.',
        'uses': 'Improves immunity and digestion.'
    },
    'Insulin': {
        'description': 'Plant that regulates blood sugar.',
        'uses': 'Anti-diabetic properties.'
    },
    'Amruta_Balli': {
        'description': 'Giloy, immunity booster.',
        'uses': 'Anti-inflammatory, antioxidant.'
    },
    'Betel': {
        'description': 'Medicinal leaf used in Ayurveda.',
        'uses': 'Improves digestion, antibacterial.'
    },
    'Castor': {
        'description': 'Oil-rich medicinal plant.',
        'uses': 'Used for skin, hair, and joint pain.'
    },
    'Ashoka': {
        'description': 'Sacred medicinal tree.',
        'uses': 'Used for women’s health.'
    },
    'Aloevera': {
        'description': 'Healing succulent plant.',
        'uses': 'Skin care, digestion.'
    },
    'Tulasi': {
        'description': 'Holy basil plant.',
        'uses': 'Boosts immunity, reduces stress.'
    },
    'Henna': {
        'description': 'Natural dye plant.',
        'uses': 'Hair care and antibacterial.'
    },
    'Curry_Leaf': {
        'description': 'Common Indian cooking leaf.',
        'uses': 'Improves digestion and hair health.'
    },
    'Arali': {
        'description': 'Medicinal shrub (toxic).',
        'uses': 'Used carefully in traditional medicine.'
    },
    'Hibiscus': {
        'description': 'Flowering plant.',
        'uses': 'Supports heart and hair health.'
    },
    'Betel_Nut': {
        'description': 'Areca nut plant.',
        'uses': 'Digestive stimulant.'
    },
    'Neem': {
        'description': 'Powerful antibacterial tree.',
        'uses': 'Skin care and oral hygiene.'
    },
    'Jasmine': {
        'description': 'Fragrant flower.',
        'uses': 'Relaxation and mood boost.'
    },
    'Nithyapushpa': {
        'description': 'Periwinkle plant.',
        'uses': 'Used in cancer treatments.'
    },
    'Mint': {
        'description': 'Cooling herb.',
        'uses': 'Relieves digestion issues.'
    },
    'Nooni': {
        'description': 'Noni medicinal plant.',
        'uses': 'Boosts immunity.'
    },
    'Pomegranate': {
        'description': 'Antioxidant-rich fruit.',
        'uses': 'Heart and blood pressure health.'
    },
    'Pepper': {
        'description': 'Spice plant.',
        'uses': 'Improves digestion.'
    },
    'Geranium': {
        'description': 'Aromatic plant.',
        'uses': 'Skin and aromatherapy.'
    },
    'Mango': {
        'description': 'King of fruits.',
        'uses': 'Rich in vitamins.'
    },
    'Honge': {
        'description': 'Indian medicinal tree.',
        'uses': 'Antiseptic uses.'
    },
    'Amla': {
        'description': 'Vitamin C rich fruit.',
        'uses': 'Boosts immunity.'
    },
    'Ekka': {
        'description': 'Hardy shrub.',
        'uses': 'Used for joint pain.'
    },
    'Raktachandini': {
        'description': 'Red sandalwood.',
        'uses': 'Blood purifier.'
    },
    'Rose': {
        'description': 'Flowering plant.',
        'uses': 'Cooling and skin care.'
    },
    'Ashwagandha': {
        'description': 'Adaptogenic herb.',
        'uses': 'Reduces stress.'
    },
    'Gauva': {
        'description': 'Guava plant.',
        'uses': 'Rich in fiber and vitamin C.'
    },
    'Ganike': {
        'description': 'Medicinal shrub.',
        'uses': 'Used for infections.'
    },

    # ✅ FIXED
    'Avocado': {
        'description': 'Nutrient-rich fruit.',
        'uses': 'Heart and brain health.'
    },

    # ✅ ADD THIS (CRITICAL FIX)
    'Avacado': {
        'description': 'Nutrient-rich fruit.',
        'uses': 'Heart and brain health.'
    },

    'Sapota': {
        'description': 'Chikoo fruit.',
        'uses': 'Improves digestion.'
    },
    'Doddapatre': {
        'description': 'Aromatic herb.',
        'uses': 'Treats cough and digestion.'
    },
    'Nagadali': {
        'description': 'Medicinal shrub.',
        'uses': 'Used for joint pain.'
    },
    'Pappaya': {
        'description': 'Papaya plant.',
        'uses': 'Improves digestion.'
    },
    'Bamboo': {
        'description': 'Fast growing grass.',
        'uses': 'Helps digestion and respiratory health.'
    }
}


def get_plant_description_and_uses(plant_name):
    return PLANT_INFO.get(
        plant_name,
        {"description": "No description", "uses": "No uses"}
    )['description'], PLANT_INFO.get(
        plant_name,
        {"description": "No description", "uses": "No uses"}
    )['uses']