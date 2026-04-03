import torch
import torch.nn as nn
import torchvision.transforms as transforms
from torchvision import models
from PIL import Image
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Device configuration
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Image preprocessing transforms
preprocess = transforms.Compose([
    transforms.Resize(224),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# Plant class names (40 classes)
PLANT_CLASSES = [
    'Wood_sorel', 'Brahmi', 'Basale', 'Lemon_grass', 'Lemon', 'Insulin', 'Amruta_Balli',
    'Betel', 'Castor', 'Ashoka', 'Aloevera', 'Tulasi', 'Henna', 'Curry_Leaf', 'Arali',
    'Hibiscus', 'Betel_Nut', 'Neem', 'Jasmine', 'Nithyapushpa', 'Mint', 'Nooni',
    'Pomegranate', 'Pepper', 'Geranium', 'Mango', 'Honge', 'Amla', 'Ekka', 'Raktachandini',
    'Rose', 'Ashwagandha', 'Gauva', 'Ganike', 'Avocado', 'Sapota', 'Doddapatre',
    'Nagadali', 'Pappaya', 'Bamboo'
]

class MobileNetIrrelevant(nn.Module):
    """MobileNet model for irrelevant/relevant classification"""
    def __init__(self, num_classes=2):
        super(MobileNetIrrelevant, self).__init__()
        self.model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
        num_features = self.model.classifier[1].in_features
        self.model.classifier[1] = nn.Linear(num_features, num_classes)

    def forward(self, x):
        return self.model(x)

class DenseNetPlantClassifier(nn.Module):
    """DenseNet model for plant classification"""
    def __init__(self, num_classes=40):
        super(DenseNetPlantClassifier, self).__init__()
        self.model = models.densenet121(weights=models.DenseNet121_Weights.DEFAULT)
        num_features = self.model.classifier.in_features
        self.model.classifier = nn.Linear(num_features, num_classes)

    def forward(self, x):
        return self.model(x)

# Global model variables
mobilenet_model = None
densenet_model = None

def load_models():
    """Load both models at startup"""
    global mobilenet_model, densenet_model

    try:
        # Load MobileNet irrelevant filter
        logger.info("Loading MobileNet irrelevant filter model...")
        mobilenet_model = MobileNetIrrelevant()
        state_dict = torch.load('models/mobilenet_irrelevant.pth', map_location=device)

        # Handle potential key prefix mismatch
        new_state_dict = {}
        for k, v in state_dict.items():
            if k.startswith('mobilenet.'):
                new_state_dict[k.replace('mobilenet.', 'model.')] = v
            else:
                new_state_dict[k] = v

        mobilenet_model.load_state_dict(new_state_dict)
        mobilenet_model.to(device)
        mobilenet_model.eval()
        logger.info("MobileNet model loaded successfully")

        # Load DenseNet plant classifier
        logger.info("Loading DenseNet plant classifier model...")
        densenet_model = DenseNetPlantClassifier()
        checkpoint = torch.load('models/densenet_model.pth', map_location=device)
        densenet_model.model.load_state_dict(checkpoint['model_state_dict'])
        densenet_model.to(device)
        densenet_model.eval()
        logger.info("DenseNet model loaded successfully")

    except Exception as e:
        logger.error(f"Error loading models: {str(e)}")
        raise

def preprocess_image(image_path):
    """Preprocess image for model input"""
    try:
        image = Image.open(image_path).convert('RGB')
        image_tensor = preprocess(image).unsqueeze(0).to(device)
        return image_tensor
    except Exception as e:
        logger.error(f"Error preprocessing image: {str(e)}")
        raise

def predict_irrelevant(image_tensor):
    """Predict if image is relevant or irrelevant using MobileNet"""
    global mobilenet_model

    if mobilenet_model is None:
        raise RuntimeError("MobileNet model not loaded")

    with torch.no_grad():
        outputs = mobilenet_model(image_tensor)
        probabilities = torch.softmax(outputs, dim=1)
        confidence, predicted = torch.max(probabilities, 1)

        # 0 = irrelevant, 1 = relevant
        is_relevant = predicted.item() == 1
        confidence_score = confidence.item()

        return is_relevant, confidence_score

def predict_plant(image_tensor, top_k=3):
    """Predict plant type using DenseNet"""
    global densenet_model

    if densenet_model is None:
        raise RuntimeError("DenseNet model not loaded")

    with torch.no_grad():
        outputs = densenet_model(image_tensor)
        probabilities = torch.softmax(outputs, dim=1)

        # Get top-k predictions
        top_probabilities, top_class_indices = torch.topk(probabilities, top_k, dim=1)

        predictions = []
        for i in range(top_k):
            class_idx = top_class_indices[0][i].item()
            confidence = top_probabilities[0][i].item() * 100  # Convert to percentage
            plant_name = PLANT_CLASSES[class_idx]
            predictions.append({
                'plant_name': plant_name,
                'confidence': round(confidence, 2)
            })

        # Return top-1 prediction details
        top_prediction = predictions[0]
        return top_prediction['plant_name'], top_prediction['confidence'], predictions

def cleanup_file(file_path):
    """Delete uploaded file after processing"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up file: {file_path}")
    except Exception as e:
        logger.warning(f"Error cleaning up file {file_path}: {str(e)}")