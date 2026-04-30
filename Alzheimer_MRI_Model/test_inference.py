import torch
import yaml
from models.build_model import build_model
import numpy as np

config = yaml.safe_load(open('config.yaml'))
# We need to make sure 'pretrain' matches the downloaded filename 
# The build_model function does: best_model_dir+ config['training_parameters']['pretrain'] + '_model_low_loss.pth.tar'
config['training_parameters']['pretrain'] = '1007_pooling_age'

print("Building model...")
model = build_model(config)
model.eval()
print("Model built successfully!")

# Create a dummy 3D input tensor [batch_size, channels, D, H, W]
# Config says input_channel: 1. So [1, 1, 96, 96, 96]
dummy_input = torch.randn(1, 1, 96, 96, 96)
# Age input is needed? 
# The build_model.py says: AgeEncoding(512,0.1,feat_dim)
# And forward(self, x, age_id): if age_id is not None: z = self.age_encoder(z,age_id)
# So age_id can be None or a tensor. Let's try None.
try:
    print("Running inference...")
    output = model(dummy_input, age_id=None)
    print("Output shape:", output.shape)
    probs = torch.nn.functional.softmax(output, dim=1)
    print("Probs:", probs)
except Exception as e:
    import traceback
    traceback.print_exc()
