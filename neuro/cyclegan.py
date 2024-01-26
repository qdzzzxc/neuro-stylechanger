import functools
import logging

import numpy as np
import torch
from PIL import Image
from torch import nn
from torchvision.transforms import transforms

from res_net import ResnetGenerator
from singleton import Singleton


class CycleGan(Singleton):
    def init(self):
        self.device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')

        #нам нужен только генератор, который состоит из блоков ResNet
        norm_layer = functools.partial(nn.InstanceNorm2d, affine=False, track_running_stats=False)
        self.net = ResnetGenerator(3, 3, 64, norm_layer=norm_layer, use_dropout=False, n_blocks=9)
        self.net.to(self.device)

        self.mode = "Monet"

        self.set_mode(self.mode)

    def set_mode(self, mode):
        state_dict = torch.load(f'./weights/{mode}.pth',
                                map_location=str(self.device))

        if hasattr(state_dict, '_metadata'):
            del state_dict._metadata

        for key in list(state_dict.keys()):
            self._patch_instance_norm_state_dict(state_dict, self.net, key.split('.'))

        self.net.load_state_dict(state_dict)

        self.net.eval()
        self.mode = mode
        logging.info(f'CycleGan: the mode has been changed to {self.mode}')

    def __call__(self, image, mode):
        logging.info('CycleGan: start of processing')

        if mode != self.mode:
            logging.info('CycleGan: the operating mode does NOT match')
            self.set_mode(mode)
        else:
            logging.info('CycleGan: the mode is the same')

        transform = transforms.Compose([
            transforms.ToTensor()])
        data = transform(image).unsqueeze(0)
        data = data.to(self.device)

        with torch.no_grad():
            result = self.net.forward(data)

        img = Image.fromarray(self.tensor2im(result))

        logging.info('CycleGan: end of processing')
        return img, None

    def tensor2im(self, input_image, imtype=np.uint8):
        """"Представляем тензор в виде, удобном для pillow.
        (C x H x W) --> (H x W x C)

            input_image (tensor) --  the input image tensor array
            imtype (type)        --  the desired type of the converted numpy array
        """

        image_tensor = input_image.data

        image_numpy = image_tensor[0].cpu().float().numpy()
        if image_numpy.shape[0] == 1:  # чёрно-белое RGB
            image_numpy = np.tile(image_numpy, (3, 1, 1))

        # переводим из интервала (-1, 1) в (0, 1), а также переставляем каналы местами как и было у исходной картинки
        image_numpy = (np.transpose(image_numpy, (1, 2, 0)) + 1) / 2.0 * 255.0

        return image_numpy.astype(imtype)

    def _patch_instance_norm_state_dict(self, state_dict, module, keys, i=0):
        """Позволяет использовать сохранения весов с InstanceNorm.
        Нужен для версий сохранённых весов до 0.4"""
        key = keys[i]
        if i + 1 == len(keys):  # at the end, pointing to a parameter/buffer
            if module.__class__.__name__.startswith('InstanceNorm') and \
                    (key == 'running_mean' or key == 'running_var'):
                if getattr(module, key) is None:
                    state_dict.pop('.'.join(keys))
            if module.__class__.__name__.startswith('InstanceNorm') and \
                    (key == 'num_batches_tracked'):
                state_dict.pop('.'.join(keys))
        else:
            self._patch_instance_norm_state_dict(state_dict, getattr(module, key), keys, i + 1)
