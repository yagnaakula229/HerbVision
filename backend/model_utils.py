"""
Clean Model Utilities - Kaggle Aligned (FINAL)
"""

import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import os

# ================= DEVICE =================
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ================= TRANSFORM (EXACT SAME AS KAGGLE) =================
transform_for_prediction = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    ),
])

# ================= MODEL =================
class DenseNetPlantClassifier(nn.Module):
    def __init__(self, num_classes=40):
        super().__init__()

        # ✅ MUST match training (pretrained=True)
        self.densenet = models.densenet121(
            weights=models.DenseNet121_Weights.DEFAULT
        )

        num_ftrs = self.densenet.classifier.in_features
        self.densenet.classifier = nn.Linear(num_ftrs, num_classes)

    def forward(self, x):
        return self.densenet(x)


# ================= PREDICTOR =================
class PlantPredictor:
    def __init__(self, model_path='densenet121_pso_medicinal_plants.pth', num_classes=40):

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")

        checkpoint = torch.load(model_path, map_location=device)

        # ================= LOAD MODEL =================
        self.model = DenseNetPlantClassifier(num_classes=num_classes)

        # Handle state_dict key mismatch (checkpoint has 'features...' but model expects 'densenet.features...')
        state_dict = checkpoint['model_state_dict']
        new_state_dict = {}
        for k, v in state_dict.items():
            if k.startswith('features.') or k.startswith('classifier.'):
                new_state_dict['densenet.' + k] = v
            else:
                new_state_dict[k] = v

        self.model.load_state_dict(new_state_dict, strict=True)

        self.model.to(device)
        self.model.eval()

        # ================= LABEL MAPPING =================
        if 'label_to_idx' not in checkpoint:
            raise ValueError("label_to_idx missing in checkpoint")

        self.idx_to_label = {
            v: k for k, v in checkpoint['label_to_idx'].items()
        }

    # ================= PREDICT (KAGGLE SAME) =================
    def predict(self, image_path, top_k=3):
        try:
            image = Image.open(image_path).convert("RGB")
            image = transform_for_prediction(image).unsqueeze(0).to(device)

            with torch.no_grad():
                outputs = self.model(image)
                probs = torch.softmax(outputs, dim=1)
                top_probs, top_idxs = probs.topk(top_k, dim=1)

            results = []
            for p, idx in zip(top_probs[0], top_idxs[0]):
                label = self.idx_to_label[idx.item()]
                confidence = p.item() * 100

                results.append({
                    "plant": label,
                    "confidence": round(confidence, 2)
                })

            return results

        except Exception as e:
            print("Prediction error:", str(e))
            return []


# ================= SINGLETON =================
_predictor_instance = None


def get_predictor():
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = PlantPredictor()
    return _predictor_instance