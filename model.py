from mxnet import nd, gluon


class ConvBlock(gluon.nn.HybridSequential):
    def __init__(self, num_filters):
        """
        :param num_filters: number of filters in convolutional block
        """
        super().__init__()
        with self.name_scope():
            self.add(gluon.nn.Conv1D(channels=num_filters, kernel_size=3, strides=1, padding=1, activation=None))
            self.add(gluon.nn.BatchNorm(axis=1))
            self.add(gluon.nn.Activation(activation='relu'))
            self.add(gluon.nn.Conv1D(channels=num_filters, kernel_size=3, strides=1, padding=1, activation=None))
            self.add(gluon.nn.BatchNorm(axis=1))
            self.add(gluon.nn.Activation(activation='relu'))


class MultiConvBlock(gluon.nn.HybridSequential):
    def __init__(self, num_filters, num_blocks):
        """
        :param num_filters: number of filters in each block
        :param num_blocks: number of blocks in sequence
        """
        super().__init__()
        with self.name_scope():
            for i in range(num_blocks):
                self.add(ConvBlock(num_filters))


class EmbedBlock(gluon.nn.HybridSequential):
    def __init__(self, input_dim, output_dim):
        """
        :param input_dim: number of rows in lookup table
        :param output_dim: number of columns in lookup table
        """
        super().__init__()
        with self.name_scope():
            self.embed = gluon.nn.Embedding(input_dim=input_dim, output_dim=output_dim)

    def forward(self, x):
        """
        :param x: mxnet ndarray of data
        :return: mxnet ndarray of data
        """
        return self.embed(x).transpose(axes=(0, 2, 1))


class CnnTextClassifier(gluon.nn.HybridSequential):
    """
    Deep convnet for text classification inspired by https://arxiv.org/pdf/1606.01781.pdf
    """
    def __init__(self, vocab_size, embed_size, dropout, num_label, filters, blocks):
        """
        :param vocab_size: number of rows in lookup table
        :param embed_size: number of columns in lookup table
        :param dropout: dropout probability for output from final conv layer
        :param num_label: number of neurons in final network layer
        :param filters: list of filter numbers per convolutional block
        :param blocks: list of block numbers between pooling stages
        """
        super().__init__()
        with self.name_scope():
            self.add(EmbedBlock(input_dim=vocab_size, output_dim=embed_size))
            self.add(gluon.nn.Conv1D(channels=64, kernel_size=3, strides=1, padding=1, activation=None))
            for i, n_blocks in enumerate(blocks):
                self.add(MultiConvBlock(num_filters=filters[i], num_blocks=n_blocks))
                if i != len(blocks) - 1:
                    self.add(gluon.nn.MaxPool1D(pool_size=3, strides=2, padding=1))

            self.add(gluon.nn.GlobalAvgPool1D())
            self.add(gluon.nn.Dropout(rate=dropout))
            self.add(gluon.nn.Dense(units=num_label))


if __name__ == "__main__":
    """
    Run unit-test
    """
    block = MultiConvBlock(num_filters=10, num_blocks=5)

    x = nd.random.uniform(shape=(128, 1, 1014))
    block.initialize()
    y = block(x)
    assert y.shape == (128, 10, 1014)
    nd.waitall()
    print("Conv Block Unit-test success!")

    net = CnnTextClassifier(vocab_size=100,
                            embed_size=16,
                            dropout=0.5,
                            num_label=5,
                            filters=[64, 128, 256, 512],
                            blocks=[2, 3, 2, 1])

    x = nd.random.uniform(shape=(128, 1024))
    net.initialize()
    y = net(x)
    assert y.shape == (128, 5)
    nd.waitall()
    print("Network Unit-test success!")
