import os
from dataclasses import dataclass, field

import torch
from torch import nn
from torch.nn import functional as F
from torch.utils.data import DataLoader
from torchvision import transforms
from torchvision.datasets import MNIST

from trainer import Trainer, TrainerArgs, TrainerConfig


@dataclass
class MnistModelConfig(TrainerConfig):
    optimizer: str = "Adam"
    lr: float = 0.001
    epochs: int = 5
    print_step: int = 500
    dashboard_logger: str = "clearml"
    project_name: str = "pytorch-mnist"
    logger_uri: str = "http://ec2-34-228-161-74.compute-1.amazonaws.com/"
    run_name: str = "test-run"


class MnistModel(nn.Module):
    def __init__(self):
        super().__init__()

        # mnist images are (1, 28, 28) (channels, height, width)
        self.layer_1 = nn.Linear(28 * 28, 128)
        self.layer_2 = nn.Linear(128, 256)
        self.layer_3 = nn.Linear(256, 10)

    def forward(self, x):
        batch_size, _, _, _ = x.size()

        # (b, 1, 28, 28) -> (b, 1*28*28)
        x = x.view(batch_size, -1)
        x = self.layer_1(x)
        x = F.relu(x)
        x = self.layer_2(x)
        x = F.relu(x)
        x = self.layer_3(x)

        x = F.log_softmax(x, dim=1)
        return x

    def train_step(self, batch, criterion):
        x, y = batch
        logits = self(x)
        loss = criterion(logits, y)
        return {"model_outputs": logits}, {"loss": loss}

    def eval_step(self, batch, criterion):
        x, y = batch
        logits = self(x)
        loss = criterion(logits, y)
        return {"model_outputs": logits}, {"loss": loss}

    def get_criterion(self):
        return torch.nn.NLLLoss()

    def get_data_loader(self, config, assets, is_eval, data_items, verbose, num_gpus, rank=0):
        transform = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.1307,), (0.3081,))])
        dataset = MNIST(os.getcwd(), train=not is_eval, download=True, transform=transform)
        mnist_train = DataLoader(dataset, batch_size=8)
        return mnist_train


def test_train_mnist():
    model = MnistModel()
    trainer = Trainer(TrainerArgs(), MnistModelConfig(), model=model, output_path=os.getcwd())
    trainer.fit()


if __name__ == "__main__":
    test_train_mnist()
