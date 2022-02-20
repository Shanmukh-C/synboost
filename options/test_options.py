from .base_options import BaseOptions


class TestOptions(BaseOptions):
    def initialize(self, parser):
        BaseOptions.initialize(self, parser)
        parser.add_argument('--results_dir', type=str, default='/kaggle/working/results/', help='saves results here.')
        parser.add_argument('--which_epoch', type=str, default='latest', help='which epoch to load? set to latest to use latest cached model')
        parser.add_argument('--how_many', type=int, default=float("inf"), help='how many test images to run')
        parser.add_argument('--instances_og', type=str, default='/kaggle/input/instance', help='path to folder containing ground truth instances')
        parser.add_argument('--semantic_og', type=str, default='/kaggle/input/semantic', help='path to folder containing ground truth semantic maps')
        # General
        parser.add_argument('--demo-folder', type=str, default='/kaggle/input/original', help='path to the folder containing demo images/ original images',
                            required=False)
        parser.add_argument('--no-segmentation', action='store_true', help='if specified, do *not* segment images since they are already created')

        # Segmentation
        parser.add_argument('--snapshot', type=str, default='/kaggle/input/sdcnet-cityscapes-segmentation/cityscapes_best (1).pth',
                            help='pre-trained Segmentation checkpoint', required=False)
        parser.add_argument('--arch', type=str, default='network.deepv3.DeepWV3Plus',
                            help='Network architecture used for Segmentation inference')
        
        parser.set_defaults(preprocess_mode='scale_width_and_crop', crop_size=256, load_size=256, display_winsize=256)
        parser.set_defaults(serial_batches=True)
        parser.set_defaults(no_flip=True)
        parser.set_defaults(phase='test')
        parser.set_defaults(use_vae=True)
        parser.set_defaults(gpu=0)
        self.isTrain = False
        return parser
