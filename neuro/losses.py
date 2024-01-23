import torch
import torch.nn as nn
import torch.nn.functional as F


def gram_matrix(matrix):
    b, f, h, w = matrix.size()
    # батч, фичи, высота, ширина
    # здесь батч будет 1, у нас просто одна картинка

    features = matrix.view(b * f, h * w)  # resize F_XL into \hat F_XL

    gram = torch.mm(features, features.t())  # всевозможные скалярные произведения

    # нормируем, деля на количество элементов матрицы
    return gram.div(b * f * h * w)


#лоссы ниже, по факту просто обёртка над mse и матрицей грамма
class ContentLoss(nn.Module):
    def __init__(self, target, ):
        super(ContentLoss, self).__init__()
        self.target = target.detach()

    def forward(self, input):
        self.loss = F.mse_loss(input, self.target)
        return input


class StyleLoss(nn.Module):
    def __init__(self, target_feature):
        super(StyleLoss, self).__init__()
        self.target = gram_matrix(target_feature).detach()

    def forward(self, input):
        G = gram_matrix(input)
        self.loss = F.mse_loss(G, self.target)
        return input