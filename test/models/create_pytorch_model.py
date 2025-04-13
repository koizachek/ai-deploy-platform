"""
Test script for creating and testing a PyTorch model for the AI model deployment platform.
"""

import os
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms

# Define a simple CNN model
class SimpleCNN(nn.Module):
    def __init__(self):
        super(SimpleCNN, self).__init__()
        self.conv1 = nn.Conv2d(1, 32, 3, 1)
        self.conv2 = nn.Conv2d(32, 64, 3, 1)
        self.dropout1 = nn.Dropout2d(0.25)
        self.dropout2 = nn.Dropout2d(0.5)
        self.fc1 = nn.Linear(9216, 128)
        self.fc2 = nn.Linear(128, 10)

    def forward(self, x):
        x = self.conv1(x)
        x = nn.functional.relu(x)
        x = self.conv2(x)
        x = nn.functional.relu(x)
        x = nn.functional.max_pool2d(x, 2)
        x = self.dropout1(x)
        x = torch.flatten(x, 1)
        x = self.fc1(x)
        x = nn.functional.relu(x)
        x = self.dropout2(x)
        x = self.fc2(x)
        output = nn.functional.log_softmax(x, dim=1)
        return output

# Create and train a simple model
def create_and_train_model():
    # Set device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # Load MNIST dataset
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))
    ])

    # Download training data
    train_dataset = torchvision.datasets.MNIST(
        root='./data', 
        train=True, 
        download=True, 
        transform=transform
    )
    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=64)

    # Create model
    model = SimpleCNN().to(device)
    optimizer = optim.Adam(model.parameters())
    criterion = nn.CrossEntropyLoss()

    # Train for just one epoch for testing purposes
    model.train()
    for batch_idx, (data, target) in enumerate(train_loader):
        data, target = data.to(device), target.to(device)
        optimizer.zero_grad()
        output = model(data)
        loss = criterion(output, target)
        loss.backward()
        optimizer.step()
        
        if batch_idx % 100 == 0:
            print(f'Batch {batch_idx}/{len(train_loader)}, Loss: {loss.item():.4f}')
        
        # Just train on a few batches for testing
        if batch_idx >= 300:
            break

    # Save the model
    model_path = os.path.join('/home/ubuntu/ai-deploy-platform/test/models', 'mnist_cnn.pt')
    torch.save(model.state_dict(), model_path)
    print(f"Model saved to {model_path}")
    
    # Create a TorchScript version for deployment
    model.eval()
    example = torch.rand(1, 1, 28, 28).to(device)
    traced_script_module = torch.jit.trace(model, example)
    script_model_path = os.path.join('/home/ubuntu/ai-deploy-platform/test/models', 'mnist_cnn_script.pt')
    traced_script_module.save(script_model_path)
    print(f"TorchScript model saved to {script_model_path}")
    
    return model_path, script_model_path

if __name__ == "__main__":
    create_and_train_model()
