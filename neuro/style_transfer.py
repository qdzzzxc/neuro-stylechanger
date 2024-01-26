import logging
from io import BytesIO

import torch
import torch.nn as nn
import torch.optim as optim

from PIL import Image

import torchvision.transforms as transforms
from torchvision.models import vgg19, VGG19_Weights

from time import time

from losses import StyleLoss, ContentLoss
from singleton import Singleton

import warnings
warnings.filterwarnings("ignore", message="To copy construct from a tensor")
# возникает даже с clone detach как написать в warn'е. мозолит глаза


# класс для nn.Sequential
class Normalization(nn.Module):
    def __init__(self, mean, std):
        super(Normalization, self).__init__()
        #  [C x 1 x 1] --> [B x C x H x W].
        self.mean = torch.tensor(mean).view(-1, 1, 1)
        self.std = torch.tensor(std).view(-1, 1, 1)

    def forward(self, img):
        return (img - self.mean) / self.std


class StyleTransfer(Singleton):
    def init(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        torch.set_default_device(self.device)

        #загружаю предобученную на image net модель
        self.cnn = vgg19(weights=VGG19_Weights.DEFAULT).features.eval()

        self.cnn_normalization_mean = torch.tensor([0.485, 0.456, 0.406])
        self.cnn_normalization_std = torch.tensor([0.229, 0.224, 0.225])

        #определяет, после каких слоёв будут вставлены лосы:
        self.content_layers_default = ['conv_4']
        self.style_layers_default = ['conv_1', 'conv_2', 'conv_3', 'conv_4', 'conv_5']

        self.unloader = transforms.ToPILImage()

    def get_style_model_and_losses(self, style_img, content_img):
        content_layers = self.content_layers_default
        style_layers = self.style_layers_default
        normalization = Normalization(self.cnn_normalization_mean, self.cnn_normalization_std)

        # списки для лоссов с разных слоёв, чтобы оптимизировать потом по ним
        content_losses = []
        style_losses = []

        # поэтапно "собираем" модель. Первое - нормализация данных
        model = nn.Sequential(normalization)

        # поэтапно создаем сеть, добавляя слои и лоссы, если необходимо
        i = 0
        for layer in self.cnn.children():
            if isinstance(layer, nn.Conv2d):
                i += 1
                name = 'conv_{}'.format(i)
            elif isinstance(layer, nn.ReLU):
                name = 'relu_{}'.format(i)
                #ContentLoss и StyleLoss не работают с in-place relu, поэтому заменяем его
                layer = nn.ReLU(inplace=False)
            elif isinstance(layer, nn.MaxPool2d):
                name = 'pool_{}'.format(i)
            elif isinstance(layer, nn.BatchNorm2d):
                name = 'bn_{}'.format(i)
            else:
                raise RuntimeError('Unrecognized layer: {}'.format(layer.__class__.__name__))

            model.add_module(name, layer)

            #если слои обозначены как те, после которых вставим лоссы, то вставляем их)
            if name in content_layers:
                target = model(content_img).detach()
                content_loss = ContentLoss(target)
                model.add_module("content_loss_{}".format(i), content_loss)
                content_losses.append(content_loss)

            if name in style_layers:
                target_feature = model(style_img).detach()
                style_loss = StyleLoss(target_feature)
                model.add_module("style_loss_{}".format(i), style_loss)
                style_losses.append(style_loss)

        # обрезаем дальнейшие слои, на которых уже нейроны для разделения картинок на классы
        for i in range(len(model) - 1, -1, -1):
            if isinstance(model[i], ContentLoss) or isinstance(model[i], StyleLoss):
                break

        model = model[:(i + 1)]

        return model, style_losses, content_losses

    def get_input_optimizer(self, input_img):
        optimizer = optim.LBFGS([input_img])
        return optimizer

    def run_style_transfer(self, content_img, style_img, input_img, num_steps=300,
                           style_weight=1000000, content_weight=1):
        error = None

        logging.info('Style Transfer: creating a model')
        model, style_losses, content_losses = self.get_style_model_and_losses(style_img, content_img)

        # алгоритм изменяет входящую картинку, а не веса сети, поэтому
        # замораживаем веса сети, размораживаем градиент входной картинки
        input_img.requires_grad_(True)
        model.eval()
        model.requires_grad_(False)

        optimizer = self.get_input_optimizer(input_img)

        logging.info('StyleTransfer: the beginning of optimization')

        start_time = time()
        temp_time = time()
        for step in range(num_steps):
            if step % 50 == 0:
                logging.info(f'StyleTransfer: {step} processing step')

                # 180 - nats timeout
                if (time() - start_time) + (time() - temp_time) < 180:
                    temp_time = time()
                else:
                    logging.warning(
                        f'StyleTransfer: the images will not have time to be processed, premature completion')
                    error = 'inner_timeout'
                    break

            def closure():
                # изменяем значение входящей картинки!
                with torch.no_grad():
                    input_img.clamp_(0, 1)

                optimizer.zero_grad()
                model(input_img)
                style_score = 0
                content_score = 0

                for sl in style_losses:
                    style_score += sl.loss
                for cl in content_losses:
                    content_score += cl.loss

                style_score *= style_weight
                content_score *= content_weight

                loss = style_score + content_score
                loss.backward()

                return style_score + content_score

            optimizer.step(closure)

        # наша картинка нормализована, её значения для нормального отображения должны быть от 0 до 1 или от 0 до 255
        with torch.no_grad():
            input_img.clamp_(0, 1)

        return input_img, error

    def image_loader(self, image):
        image = Image.open(BytesIO(image))
        #добавляем канал батча
        image = self.loader(image).unsqueeze(0)
        return image.to(self.device, torch.float)

    def two_image_loader(self, content_img, style_img):
        images = [content_img, style_img]

        sizes = [*content_img.size, *style_img.size]
        min_size = min(sizes)
        if min_size > 500:
            logging.warning('StyleTransfer: the pictures are too big, the size is reduced')
            min_size = 500

        for i in range(len(images)):
            image_size = images[i].size
            ratio = max(image_size) / min(image_size)

            if images[i].size[0] < images[i].size[1]:
                loader = transforms.Compose([
                    transforms.Resize((round(min_size * ratio), min_size)),
                    transforms.CenterCrop((min_size, min_size)),
                    transforms.ToTensor()])
                images[i] = loader(images[i]).unsqueeze(0)

            else:
                loader = transforms.Compose([
                    transforms.Resize((min_size, round(min_size * ratio))),
                    transforms.CenterCrop((min_size, min_size)),
                    transforms.ToTensor()])
                images[i] = loader(images[i]).unsqueeze(0)

        return images[0].to(self.device, torch.float), images[1].to(self.device, torch.float)

    def to_pillow(self, tensor):
        image = tensor.cpu().detach()
        image = image.squeeze(0)
        image = self.unloader(image)
        return image

    def __call__(self, content_img, style_img, num_steps=100):
        logging.info('StyleTransfer: start of processing')

        content_img, style_img = self.two_image_loader(content_img, style_img)

        assert style_img.size() == content_img.size(), \
            "we need to import style and content images of the same size"

        input_img = content_img.clone()

        #путём изменения input_img минимиризуем его различия со content_img и style_img
        output, error = self.run_style_transfer(content_img, style_img, input_img, num_steps=num_steps)

        output = self.to_pillow(output)

        logging.info('StyleTransfer: end of processing')
        return output, error
